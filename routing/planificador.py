import uuid
from dataclasses import dataclass
from itertools import pairwise

from sqlalchemy.orm import Session

from db import crud
from db.modelos import Cliente, Deposito, Usuario, Vehiculo
from routing.solver import resolver_ruteo
from services.osrm_client import obtener_matriz_osrm

# "Todo el día" — usado como ventana horaria del depósito cuando no configuró
# una propia (hoy el caso de todos los depósitos existentes, ver
# Deposito.ventana_inicio/fin en db/modelos.py) y como ventana por defecto
# para cualquier nodo sin una específica.
VENTANA_COMPLETA = (0, 1440)


class ErrorPlanificacion(Exception):
    """Error de negocio al planificar una ruta (falta vehículo/depósito,
    clientes inválidos, o el solver no encontró solución) — el router lo
    traduce a un 400 con el mensaje tal cual."""


@dataclass
class SeleccionParada:
    """Lo que el chofer eligió para un cliente al armar la ruta de hoy —
    versión desacoplada de api.schemas_rutas.ParadaSeleccionada (este
    módulo no depende de la capa de API, mismo criterio que ya regía acá)."""

    cliente_id: uuid.UUID
    carga_kg: int
    unidades: int = 0
    ventana_inicio: int | None = None
    ventana_fin: int | None = None


@dataclass
class ParadaPlanificada:
    cliente: Cliente
    carga_kg: int
    unidades: int
    orden: int
    distancia_acumulada_m: int
    ventana_inicio: int | None
    ventana_fin: int | None
    hora_estimada_llegada: int | None


@dataclass
class ResultadoPlanificacion:
    vehiculo: Vehiculo
    deposito: Deposito
    paradas: list[ParadaPlanificada]
    distancia_total_m: int
    carga_total_kg: int
    distancia_sin_optimizar_m: int
    explicacion: str
    usa_ventanas_horarias: bool
    hora_fin_estimada_min: int | None


def _distancia_recorrido(matriz_distancias: list, secuencia_nodos: list[int]) -> int:
    return sum(int(matriz_distancias[a][b]) for a, b in pairwise(secuencia_nodos))


def planificar_ruta(
    db: Session,
    usuario: Usuario,
    selecciones: list[SeleccionParada],
    usa_ventanas_horarias: bool = False,
    deposito_id: uuid.UUID | None = None,
) -> ResultadoPlanificacion:
    """Arma y resuelve el problema (CVRP, o VRPTW si `usa_ventanas_horarias`)
    para los clientes seleccionados por `usuario`, usando su vehículo y
    depósito ya configurados. Compartida por /rutas/optimizar (preview, no
    persiste) y /rutas/confirmar (persiste el mismo resultado) para no
    recalcular ni duplicar el armado del problema."""
    vehiculo = usuario.vehiculo
    if vehiculo is None:
        raise ErrorPlanificacion("No tenés un vehículo registrado.")

    duenio = usuario.ambito_dueño
    depositos = crud.listar_depositos(db, duenio)
    if not depositos:
        raise ErrorPlanificacion("Todavía no configuraste tu depósito de partida.")
    if deposito_id is None:
        deposito = depositos[0]
    else:
        # Solo entre los depósitos activos del propio dueño: uno ajeno o dado
        # de baja se trata igual que uno inexistente.
        deposito = next((d for d in depositos if d.id == deposito_id), None)
        if deposito is None:
            raise ErrorPlanificacion("El depósito elegido no existe.")

    cargas_por_cliente = {s.cliente_id: s for s in selecciones}
    clientes = crud.obtener_clientes_propios(db, list(cargas_por_cliente), duenio)
    if len(clientes) != len(cargas_por_cliente):
        raise ErrorPlanificacion("Alguno de los lugares seleccionados ya no existe.")

    if usa_ventanas_horarias and any(
        s.ventana_inicio is None or s.ventana_fin is None for s in selecciones
    ):
        raise ErrorPlanificacion(
            "Elegiste usar ventanas horarias para esta ruta: completá el horario "
            "de cada parada antes de optimizar."
        )

    coordenadas = [{"latitud": deposito.latitud, "longitud": deposito.longitud}] + [
        {"latitud": cliente.latitud, "longitud": cliente.longitud} for cliente in clientes
    ]
    try:
        matrices = obtener_matriz_osrm(coordenadas)
    except Exception as error:
        raise ErrorPlanificacion(f"No se pudo calcular la ruta: {error}") from error

    matriz_distancias = matrices["matriz_distancias_metros"]
    demandas = [0] + [cargas_por_cliente[cliente.id].carga_kg for cliente in clientes]

    # Un solo vehículo — si el solver falla, la causa casi siempre es esta y
    # no una traza genérica de OR-Tools ayuda al chofer a entender qué hacer.
    # Se chequea antes de llamar al solver para no depender de que agote el
    # time_limit en un problema ya sin salida.
    carga_total = sum(demandas)
    if carga_total > vehiculo.capacidad_carga_kg:
        raise ErrorPlanificacion(
            f"La carga total de tu selección ({carga_total} kg) supera la capacidad "
            f"de tu vehículo ({vehiculo.capacidad_carga_kg} kg) — sacá algún bulto o "
            f"repartilo en más de una ruta."
        )

    kwargs_solver = {}
    if usa_ventanas_horarias:
        kwargs_solver["matriz_tiempos"] = matrices["matriz_tiempos_segundos"]
        kwargs_solver["tiempos_servicio"] = [0] + [
            cliente.tiempo_servicio_default for cliente in clientes
        ]
        if deposito.ventana_inicio is not None and deposito.ventana_fin is not None:
            ventana_deposito = (deposito.ventana_inicio, deposito.ventana_fin)
        else:
            ventana_deposito = VENTANA_COMPLETA
        kwargs_solver["ventanas_horarias"] = [ventana_deposito] + [
            (
                cargas_por_cliente[cliente.id].ventana_inicio,
                cargas_por_cliente[cliente.id].ventana_fin,
            )
            for cliente in clientes
        ]
        kwargs_solver["tipo_problema"] = "VRPTW"

    resultado = resolver_ruteo(
        matriz_distancias, demandas, [vehiculo.capacidad_carga_kg], **kwargs_solver
    )
    if resultado["estado"] == "Fallo":
        mensaje = resultado["mensaje"]
        if usa_ventanas_horarias:
            mensaje += " Revisá que las ventanas horarias sean alcanzables entre sí."
        raise ErrorPlanificacion(mensaje)

    ruta_nodos = resultado["rutas"][0]["ruta_secuencial_nodos"]
    minuto_llegada_por_nodo = (
        {info["nodo_id"]: info["minuto_llegada"] for info in ruta_nodos}
        if usa_ventanas_horarias
        else {}
    )

    # Nodo 0 = depósito (no es una parada), nodo i = clientes[i - 1] — mismo
    # orden en que se armaron `coordenadas` y `demandas` arriba.
    secuencia_nodos = [info["nodo_id"] for info in ruta_nodos]
    paradas = []
    distancia_acumulada = 0
    orden = 0
    for nodo_previo, nodo_actual in pairwise(secuencia_nodos):
        # OSRM devuelve metros como float — el solver ya trunca a int para
        # los costos de arco (routing/solver.py:callback_distancia), acá
        # hay que hacer lo mismo para que sea consistente con esos valores.
        distancia_acumulada += int(matriz_distancias[nodo_previo][nodo_actual])
        if nodo_actual == 0:
            continue
        cliente = clientes[nodo_actual - 1]
        seleccion = cargas_por_cliente[cliente.id]
        paradas.append(
            ParadaPlanificada(
                cliente=cliente,
                carga_kg=seleccion.carga_kg,
                unidades=seleccion.unidades,
                orden=orden,
                distancia_acumulada_m=distancia_acumulada,
                ventana_inicio=seleccion.ventana_inicio,
                ventana_fin=seleccion.ventana_fin,
                hora_estimada_llegada=minuto_llegada_por_nodo.get(nodo_actual),
            )
        )
        orden += 1

    # Comparación honesta: mismas distancias reales de OSRM, orden pedido
    # (tal como el chofer fue marcando los lugares) vs. orden que resolvió
    # el solver — así el ahorro es un dato real, no una estimación.
    indice_por_cliente = {cliente.id: i + 1 for i, cliente in enumerate(clientes)}
    secuencia_sin_optimizar = [0] + [indice_por_cliente[id_] for id_ in cargas_por_cliente] + [0]
    distancia_sin_optimizar_m = _distancia_recorrido(matriz_distancias, secuencia_sin_optimizar)
    distancia_total_m = resultado["rutas"][0]["distancia_recorrida_metros"]

    porcentaje_carga = round(
        100 * resultado["rutas"][0]["carga_total"] / vehiculo.capacidad_carga_kg
    )
    explicacion = (
        f"Elegimos este orden para recorrer la menor distancia posible entre las "
        f"{len(paradas)} paradas, respetando la capacidad de tu vehículo "
        f"({resultado['rutas'][0]['carga_total']}/{vehiculo.capacidad_carga_kg} kg, "
        f"{porcentaje_carga}%)."
    )
    if usa_ventanas_horarias:
        explicacion += " También respeta la ventana horaria que le pusiste a cada parada."

    hora_fin_estimada_min = (
        minuto_llegada_por_nodo.get(secuencia_nodos[-1]) if usa_ventanas_horarias else None
    )

    return ResultadoPlanificacion(
        vehiculo=vehiculo,
        deposito=deposito,
        paradas=paradas,
        distancia_total_m=distancia_total_m,
        carga_total_kg=resultado["rutas"][0]["carga_total"],
        distancia_sin_optimizar_m=distancia_sin_optimizar_m,
        explicacion=explicacion,
        usa_ventanas_horarias=usa_ventanas_horarias,
        hora_fin_estimada_min=hora_fin_estimada_min,
    )
