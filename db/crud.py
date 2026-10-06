import secrets
import string
import uuid
from datetime import UTC, date, datetime
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from db.modelos import (
    Cliente,
    CodigoInvitacion,
    Deposito,
    Duenio,
    Empresa,
    EntregaPendiente,
    EstadoEntregaPendiente,
    EstadoIncidencia,
    EstadoParada,
    EstadoRuta,
    Incidencia,
    ParadaRuta,
    PlanSuscripcion,
    ResolucionIncidencia,
    RolUsuario,
    Ruta,
    TipoIncidencia,
    TipoProblema,
    TipoVehiculo,
    Usuario,
    Vehiculo,
)
from db.sesion import guardar

ALFABETO_CODIGO = string.ascii_uppercase + string.digits


class DatosChofer(Protocol):
    """Forma estructural que necesita crear_chofer. Los schemas de registro de
    api/schemas_auth.py la cumplen sin que este módulo dependa de ellos."""

    email: str
    nombre_completo: str
    telefono: str
    tipo_vehiculo: TipoVehiculo
    patente: str
    capacidad_carga_kg: int


class DatosCliente(Protocol):
    """Forma estructural que necesita crear_cliente — cumplida por
    api/schemas_clientes.py.ClienteCrear sin acoplar este módulo a Pydantic."""

    nombre: str
    direccion: str
    latitud: float
    longitud: float
    telefono: str | None
    demanda_carga_default: int | None
    tiempo_servicio_default: int
    ventana_inicio_default: int | None
    ventana_fin_default: int | None


class DatosDeposito(Protocol):
    """Forma estructural que necesita crear_deposito — cumplida por
    api/schemas_depositos.py.DepositoCrear."""

    nombre: str
    latitud: float
    longitud: float
    ventana_inicio: int | None
    ventana_fin: int | None


class DatosParadaRuta(Protocol):
    """Forma estructural que necesita crear_ruta para cada parada — cumplida
    tal cual por routing.planificador.ParadaPlanificada, sin que este módulo
    dependa de esa capa."""

    cliente: Cliente
    orden: int
    carga_kg: int
    unidades: int
    distancia_acumulada_m: int
    ventana_inicio: int | None
    ventana_fin: int | None
    hora_estimada_llegada: int | None


def obtener_usuario_por_email(db: Session, email: str) -> Usuario | None:
    return db.execute(select(Usuario).where(Usuario.email == email)).scalar_one_or_none()


def obtener_usuario_por_email_sin_mayusculas(db: Session, email: str) -> Usuario | None:
    # Google devuelve el email en minúsculas; las cuentas viejas pueden tenerlo con mayúsculas.
    # Si dos cuentas difieren solo en mayúsculas, gana la más antigua.
    return (
        db.execute(
            select(Usuario)
            .where(func.lower(Usuario.email) == email.lower())
            .order_by(Usuario.fecha_creacion)
        )
        .scalars()
        .first()
    )


def obtener_usuario_por_google_sub(db: Session, google_sub: str) -> Usuario | None:
    return db.execute(select(Usuario).where(Usuario.google_sub == google_sub)).scalar_one_or_none()


def vincular_google(db: Session, usuario: Usuario, google_sub: str) -> Usuario:
    usuario.google_sub = google_sub
    return guardar(db, usuario)


def obtener_vehiculo_por_patente(db: Session, patente: str) -> Vehiculo | None:
    return db.execute(select(Vehiculo).where(Vehiculo.patente == patente)).scalar_one_or_none()


def actualizar_usuario(db: Session, usuario: Usuario, cambios: dict[str, object]) -> Usuario:
    for campo, valor in cambios.items():
        setattr(usuario, campo, valor)
    return guardar(db, usuario)


def actualizar_vehiculo(db: Session, vehiculo: Vehiculo, cambios: dict[str, object]) -> Vehiculo:
    for campo, valor in cambios.items():
        setattr(vehiculo, campo, valor)
    return guardar(db, vehiculo)


def cambiar_contrasena(db: Session, usuario: Usuario, contrasena_hash: str) -> None:
    usuario.contrasena_hash = contrasena_hash
    guardar(db, usuario)


def crear_empresa(db: Session, nombre: str) -> Empresa:
    return guardar(db, Empresa(nombre=nombre, plan=PlanSuscripcion.PRUEBA))


def crear_chofer(
    db: Session,
    datos: DatosChofer,
    contrasena_hash: str | None,
    empresa_id: uuid.UUID | None = None,
    google_sub: str | None = None,
) -> Usuario:
    """Chofer independiente (empresa_id=None) o chofer vinculado a una empresa.
    Crea también su Vehiculo — el registro sigue pidiendo esos datos juntos,
    aunque ahora vivan en tablas separadas."""
    usuario = guardar(
        db,
        Usuario(
            email=datos.email,
            contrasena_hash=contrasena_hash,
            google_sub=google_sub,
            nombre_completo=datos.nombre_completo,
            rol=RolUsuario.CHOFER,
            empresa_id=empresa_id,
            telefono=datos.telefono,
            plan=PlanSuscripcion.PRUEBA,
        ),
    )
    guardar(
        db,
        Vehiculo(
            empresa_id=empresa_id,
            usuario_id=usuario.id,
            tipo_vehiculo=datos.tipo_vehiculo,
            patente=datos.patente,
            capacidad_carga_kg=datos.capacidad_carga_kg,
        ),
    )
    return usuario


def crear_admin(
    db: Session,
    email: str,
    contrasena_hash: str,
    nombre_completo: str,
    empresa_id: uuid.UUID,
) -> Usuario:
    """Único camino para crear un admin — empresa_id no-opcional a propósito:
    un admin sin empresa es un estado inválido que no debe poder construirse."""
    return guardar(
        db,
        Usuario(
            email=email,
            contrasena_hash=contrasena_hash,
            nombre_completo=nombre_completo,
            rol=RolUsuario.ADMIN,
            empresa_id=empresa_id,
            plan=PlanSuscripcion.PRUEBA,
        ),
    )


def obtener_codigo_invitacion(db: Session, codigo: str) -> CodigoInvitacion | None:
    return db.execute(
        select(CodigoInvitacion).where(CodigoInvitacion.codigo == codigo)
    ).scalar_one_or_none()


def _generar_codigo_unico(db: Session) -> str:
    while True:
        candidato = "".join(secrets.choice(ALFABETO_CODIGO) for _ in range(8))
        if obtener_codigo_invitacion(db, candidato) is None:
            return candidato


def crear_codigo_invitacion(
    db: Session, empresa_id: uuid.UUID, creado_por_usuario_id: uuid.UUID
) -> CodigoInvitacion:
    return guardar(
        db,
        CodigoInvitacion(
            codigo=_generar_codigo_unico(db),
            empresa_id=empresa_id,
            creado_por_usuario_id=creado_por_usuario_id,
        ),
    )


def listar_codigos_invitacion(db: Session, empresa_id: uuid.UUID) -> list[CodigoInvitacion]:
    return list(
        db.execute(
            select(CodigoInvitacion)
            .where(CodigoInvitacion.empresa_id == empresa_id)
            .order_by(CodigoInvitacion.fecha_creacion.desc())
        ).scalars()
    )


def marcar_codigo_usado(db: Session, invitacion: CodigoInvitacion, usuario_id: uuid.UUID) -> None:
    invitacion.usado = True
    invitacion.usado_por_usuario_id = usuario_id
    invitacion.fecha_uso = datetime.now(UTC)
    guardar(db, invitacion)


def _condicion_dueño(modelo: type[Cliente] | type[Deposito], duenio: Duenio):
    """Condición SQL de dueño, compartida por cualquier modelo con
    DuenioMixin (hoy Cliente y Deposito) — un solo lugar donde vive el
    filtro, en vez de repetirlo por modelo."""
    return (
        modelo.empresa_id == duenio.empresa_id
        if duenio.empresa_id
        else modelo.usuario_id == duenio.usuario_id
    )


def crear_cliente(db: Session, datos: DatosCliente, duenio: Duenio) -> Cliente:
    return guardar(
        db,
        Cliente(
            empresa_id=duenio.empresa_id,
            usuario_id=duenio.usuario_id,
            nombre=datos.nombre,
            direccion=datos.direccion,
            latitud=datos.latitud,
            longitud=datos.longitud,
            telefono=datos.telefono,
            demanda_carga_default=datos.demanda_carga_default,
            tiempo_servicio_default=datos.tiempo_servicio_default,
            ventana_inicio_default=datos.ventana_inicio_default,
            ventana_fin_default=datos.ventana_fin_default,
        ),
    )


def listar_clientes(db: Session, duenio: Duenio) -> list[Cliente]:
    return list(
        db.execute(
            select(Cliente)
            .where(_condicion_dueño(Cliente, duenio), Cliente.activo.is_(True))
            .order_by(Cliente.nombre)
        ).scalars()
    )


def obtener_cliente_propio(db: Session, cliente_id: uuid.UUID, duenio: Duenio) -> Cliente | None:
    """Trae el Cliente solo si pertenece a `duenio` — el scoping vive en la
    query, no queda a cargo de que el caller lo verifique después de un
    fetch sin restricción (eso sería fácil de olvidar en un endpoint nuevo)."""
    return db.execute(
        select(Cliente).where(Cliente.id == cliente_id, _condicion_dueño(Cliente, duenio))
    ).scalar_one_or_none()


def obtener_clientes_propios(
    db: Session, cliente_ids: list[uuid.UUID], duenio: Duenio
) -> list[Cliente]:
    """Trae varios Cliente por id, filtrados por dueño — usado al armar una
    ruta a partir de una selección. Si algún id no pertenece a `duenio`
    (ajeno o inexistente), simplemente no aparece en el resultado; el
    caller es responsable de comparar la cantidad devuelta contra la
    pedida si necesita detectarlo."""
    return list(
        db.execute(
            select(Cliente).where(Cliente.id.in_(cliente_ids), _condicion_dueño(Cliente, duenio))
        ).scalars()
    )


def actualizar_cliente(db: Session, cliente: Cliente, cambios: dict[str, object]) -> Cliente:
    for campo, valor in cambios.items():
        setattr(cliente, campo, valor)
    return guardar(db, cliente)


def eliminar_cliente(db: Session, cliente: Cliente) -> None:
    """Soft delete — activo=False, para no romper el snapshot de ParadaRuta
    de rutas ya confirmadas que referencien este cliente."""
    cliente.activo = False
    guardar(db, cliente)


def crear_deposito(db: Session, datos: DatosDeposito, duenio: Duenio) -> Deposito:
    return guardar(
        db,
        Deposito(
            empresa_id=duenio.empresa_id,
            usuario_id=duenio.usuario_id,
            nombre=datos.nombre,
            latitud=datos.latitud,
            longitud=datos.longitud,
            ventana_inicio=datos.ventana_inicio,
            ventana_fin=datos.ventana_fin,
        ),
    )


def listar_depositos(db: Session, duenio: Duenio) -> list[Deposito]:
    return list(
        db.execute(
            select(Deposito)
            .where(_condicion_dueño(Deposito, duenio), Deposito.activo.is_(True))
            .order_by(Deposito.nombre)
        ).scalars()
    )


def obtener_deposito_propio(db: Session, deposito_id: uuid.UUID, duenio: Duenio) -> Deposito | None:
    return db.execute(
        select(Deposito).where(Deposito.id == deposito_id, _condicion_dueño(Deposito, duenio))
    ).scalar_one_or_none()


def actualizar_deposito(db: Session, deposito: Deposito, cambios: dict[str, object]) -> Deposito:
    for campo, valor in cambios.items():
        setattr(deposito, campo, valor)
    return guardar(db, deposito)


def eliminar_deposito(db: Session, deposito: Deposito) -> None:
    deposito.activo = False
    guardar(db, deposito)


def obtener_ruta_en_curso(db: Session, chofer_id: uuid.UUID) -> Ruta | None:
    """La única ruta en curso del chofer, sin importar su fecha: una ruta
    iniciada un día y sin terminar sigue siendo la actual al día siguiente."""
    return (
        db.execute(
            select(Ruta).where(Ruta.chofer_id == chofer_id, Ruta.estado == EstadoRuta.EN_CURSO)
        )
        .scalars()
        .first()
    )


def listar_rutas_del_dia(db: Session, chofer_id: uuid.UUID, fecha: date) -> list[Ruta]:
    """Planificadas, en curso y completadas de un día, en el orden en que se
    crearon. Las canceladas quedan fuera (siguen en el historial)."""
    return list(
        db.execute(
            select(Ruta)
            .where(
                Ruta.chofer_id == chofer_id,
                Ruta.fecha == fecha,
                Ruta.estado != EstadoRuta.CANCELADA,
            )
            .order_by(Ruta.fecha_creacion)
        ).scalars()
    )


def hay_ruta_abierta(db: Session, chofer_id: uuid.UUID) -> bool:
    """Alguna ruta planificada o en curso, de cualquier fecha."""
    return (
        db.execute(
            select(Ruta.id)
            .where(
                Ruta.chofer_id == chofer_id,
                Ruta.estado.in_([EstadoRuta.PLANIFICADA, EstadoRuta.EN_CURSO]),
            )
            .limit(1)
        ).first()
        is not None
    )


def crear_ruta(
    db: Session,
    chofer: Usuario,
    vehiculo: Vehiculo,
    deposito: Deposito,
    fecha: date,
    tipo_problema: TipoProblema,
    distancia_total_m: int,
    explicacion: str,
    hora_fin_estimada_min: int | None,
    paradas: list[DatosParadaRuta],
    nombre: str | None = None,
) -> Ruta:
    """`paradas` ya viene en el orden que resolvió el solver (ver
    routing/planificador.py)."""
    ruta = guardar(
        db,
        Ruta(
            chofer_id=chofer.id,
            vehiculo_id=vehiculo.id,
            deposito_id=deposito.id,
            creado_por_usuario_id=chofer.id,
            fecha=fecha,
            nombre=nombre,
            tipo_problema=tipo_problema,
            estado=EstadoRuta.PLANIFICADA,
            distancia_total_m=distancia_total_m,
            explicacion=explicacion,
            hora_fin_estimada_min=hora_fin_estimada_min,
        ),
    )
    for item in paradas:
        cliente = item.cliente
        guardar(
            db,
            ParadaRuta(
                ruta_id=ruta.id,
                cliente_id=cliente.id,
                orden=item.orden,
                nombre_snapshot=cliente.nombre,
                direccion_snapshot=cliente.direccion,
                latitud_snapshot=cliente.latitud,
                longitud_snapshot=cliente.longitud,
                demanda_carga_snapshot=item.carga_kg,
                unidades_snapshot=item.unidades,
                distancia_acumulada_m=item.distancia_acumulada_m,
                ventana_inicio_snapshot=item.ventana_inicio,
                ventana_fin_snapshot=item.ventana_fin,
                hora_estimada_llegada=item.hora_estimada_llegada,
            ),
        )
    return ruta


def listar_rutas_historial(
    db: Session, chofer_id: uuid.UUID, desde: date, hasta: date
) -> list[Ruta]:
    """Historial de rutas de un chofer en un rango de fechas, cualquier
    estado (a diferencia de listar_rutas_del_dia, acá interesan también las
    completadas/canceladas) — alimenta el almanaque de "Historial de rutas".
    Puede haber más de una Ruta para el mismo día (el chofer canceló y
    volvió a armar otra) — se ordena con la más reciente primero dentro de
    cada fecha para que el caller pueda quedarse con "la última palabra"
    del día sin tener que ordenar de nuevo."""
    return list(
        db.execute(
            select(Ruta)
            .where(Ruta.chofer_id == chofer_id, Ruta.fecha.between(desde, hasta))
            .order_by(Ruta.fecha.desc(), Ruta.fecha_creacion.desc())
            # Paradas e incidencias de todo el mes en una consulta cada una, en
            # vez de una por ruta al armar cada RutaHistorialItem.
            .options(selectinload(Ruta.paradas), selectinload(Ruta.incidencias))
        ).scalars()
    )


def obtener_ruta_propia(db: Session, chofer_id: uuid.UUID, ruta_id: uuid.UUID) -> Ruta | None:
    return db.execute(
        select(Ruta).where(Ruta.id == ruta_id, Ruta.chofer_id == chofer_id)
    ).scalar_one_or_none()


def cancelar_ruta(db: Session, ruta: Ruta) -> None:
    ruta.estado = EstadoRuta.CANCELADA
    guardar(db, ruta)
    # Las entregas reprogramadas que esta ruta había incluido vuelven a estar
    # pendientes: si no, cancelar la ruta las haría desaparecer.
    _liberar_entregas_de_ruta(db, ruta.id)


def iniciar_ruta(db: Session, ruta: Ruta) -> Ruta:
    """Arranca el día: la ruta pasa a en_curso y la primera parada (orden=0)
    pasa a ser el objetivo actual — ver EstadoParada.EN_CURSO."""
    ruta.estado = EstadoRuta.EN_CURSO
    ruta.hora_inicio_real = datetime.now(UTC)
    guardar(db, ruta)
    if ruta.paradas:
        ruta.paradas[0].estado = EstadoParada.EN_CURSO
        guardar(db, ruta.paradas[0])
    return ruta


def _avanzar_ruta(db: Session, ruta: Ruta) -> None:
    """Pasa a en_curso la próxima parada pendiente (por `orden`), o cierra la
    ruta si no queda ninguna — criterio por estado y no por `orden`, porque
    saltear una parada la manda al final y rompe esa relación."""
    pendientes = [p for p in ruta.paradas if p.estado == EstadoParada.PENDIENTE]
    if pendientes:
        siguiente = min(pendientes, key=lambda p: p.orden)
        siguiente.estado = EstadoParada.EN_CURSO
        guardar(db, siguiente)
    else:
        ruta.estado = EstadoRuta.COMPLETADA
        ruta.hora_fin_real = datetime.now(UTC)
        guardar(db, ruta)


def registrar_llegada(db: Session, parada: ParadaRuta) -> ParadaRuta:
    """Idempotente: una segunda llamada conserva la hora original."""
    if parada.hora_real_llegada is None:
        parada.hora_real_llegada = datetime.now(UTC)
        guardar(db, parada)
    return parada


def completar_parada(db: Session, ruta: Ruta, parada: ParadaRuta) -> Ruta:
    """Marca `parada` como visitada y avanza a la siguiente pendiente. Si no
    queda ninguna, cierra la ruta entera."""
    ahora = datetime.now(UTC)
    parada.estado = EstadoParada.COMPLETADA
    parada.hora_real_salida = ahora
    if parada.hora_real_llegada is None:
        parada.hora_real_llegada = ahora
    guardar(db, parada)

    _avanzar_ruta(db, ruta)
    return ruta


def crear_incidencia(
    db: Session,
    *,
    ruta: Ruta,
    reportado_por: Usuario,
    tipo: TipoIncidencia,
    descripcion: str | None = None,
    parada: ParadaRuta | None = None,
) -> Incidencia:
    return guardar(
        db,
        Incidencia(
            ruta_id=ruta.id,
            parada_id=parada.id if parada else None,
            tipo=tipo,
            descripcion=descripcion,
            reportado_por_usuario_id=reportado_por.id,
        ),
    )


def listar_incidencias_de_chofer(
    db: Session,
    chofer_id: uuid.UUID,
    limite: int = 100,
    desplazamiento: int = 0,
    estado: EstadoIncidencia | None = None,
) -> list[Incidencia]:
    consulta = select(Incidencia).where(Incidencia.reportado_por_usuario_id == chofer_id)
    if estado is not None:
        consulta = consulta.where(Incidencia.estado == estado)
    return list(
        db.execute(
            consulta.options(joinedload(Incidencia.ruta), joinedload(Incidencia.parada))
            .order_by(Incidencia.fecha_hora.desc())
            .limit(limite)
            .offset(desplazamiento)
        ).scalars()
    )


def obtener_incidencia_propia(
    db: Session, incidencia_id: uuid.UUID, chofer_id: uuid.UUID
) -> Incidencia | None:
    return db.execute(
        select(Incidencia).where(
            Incidencia.id == incidencia_id, Incidencia.reportado_por_usuario_id == chofer_id
        )
    ).scalar_one_or_none()


def paradas_ya_reprogramadas(db: Session, parada_ids: list[uuid.UUID]) -> set[uuid.UUID]:
    """Cuáles de estas paradas ya tienen una entrega reprogramada (una sola consulta)."""
    return set(
        db.execute(
            select(EntregaPendiente.parada_origen_id).where(
                EntregaPendiente.parada_origen_id.in_(parada_ids)
            )
        ).scalars()
    )


def incidencia_es_reprogramable(incidencia: Incidencia, reprogramadas: set[uuid.UUID]) -> bool:
    """Solo la de una parada fallida que todavía no se reprogramó; `reprogramadas`
    sale de `paradas_ya_reprogramadas`."""
    parada = incidencia.parada
    return (
        incidencia.estado == EstadoIncidencia.PENDIENTE
        and parada is not None
        and parada.estado == EstadoParada.FALLIDA
        and parada.id not in reprogramadas
    )


def _resolver(db: Session, incidencia: Incidencia, resolucion: ResolucionIncidencia) -> None:
    incidencia.estado = EstadoIncidencia.RESUELTA
    incidencia.resolucion = resolucion
    incidencia.fecha_resolucion = datetime.now(UTC)
    guardar(db, incidencia)


def reprogramar_entrega(
    db: Session, usuario: Usuario, parada: ParadaRuta, incidencia: Incidencia
) -> EntregaPendiente:
    """Guarda la entrega de una parada fallida para la próxima ruta (con un
    snapshot de lo que había que entregar) y resuelve la incidencia."""
    entrega = guardar(
        db,
        EntregaPendiente(
            usuario_id=usuario.id,
            cliente_id=parada.cliente_id,
            parada_origen_id=parada.id,
            incidencia_id=incidencia.id,
            carga_kg=parada.demanda_carga_snapshot,
            unidades=parada.unidades_snapshot,
            ventana_inicio=parada.ventana_inicio_snapshot,
            ventana_fin=parada.ventana_fin_snapshot,
        ),
    )
    _resolver(db, incidencia, ResolucionIncidencia.REPROGRAMADA)
    return entrega


def cerrar_incidencia(db: Session, incidencia: Incidencia) -> Incidencia:
    _resolver(db, incidencia, ResolucionIncidencia.CERRADA)
    return incidencia


def listar_entregas_pendientes(db: Session, usuario_id: uuid.UUID) -> list[EntregaPendiente]:
    """Las del chofer todavía sin cumplir, de lugares que siguen en su libreta."""
    return list(
        db.execute(
            select(EntregaPendiente)
            .join(Cliente, Cliente.id == EntregaPendiente.cliente_id)
            .where(
                EntregaPendiente.usuario_id == usuario_id,
                EntregaPendiente.estado == EstadoEntregaPendiente.PENDIENTE,
                Cliente.activo.is_(True),
            )
            .order_by(EntregaPendiente.fecha_creacion)
        ).scalars()
    )


def marcar_entregas_incluidas(
    db: Session, usuario_id: uuid.UUID, ruta: Ruta, cliente_ids: list[uuid.UUID]
) -> None:
    """Da por cumplidas las entregas pendientes de los lugares que la ruta
    confirmada contiene."""
    pendientes = db.execute(
        select(EntregaPendiente).where(
            EntregaPendiente.usuario_id == usuario_id,
            EntregaPendiente.estado == EstadoEntregaPendiente.PENDIENTE,
            EntregaPendiente.cliente_id.in_(cliente_ids),
        )
    ).scalars()
    for entrega in pendientes:
        entrega.estado = EstadoEntregaPendiente.INCLUIDA
        entrega.ruta_id = ruta.id
        entrega.fecha_inclusion = datetime.now(UTC)
        guardar(db, entrega)


def _liberar_entregas_de_ruta(db: Session, ruta_id: uuid.UUID) -> None:
    incluidas = db.execute(
        select(EntregaPendiente).where(
            EntregaPendiente.ruta_id == ruta_id,
            EntregaPendiente.estado == EstadoEntregaPendiente.INCLUIDA,
        )
    ).scalars()
    for entrega in incluidas:
        entrega.estado = EstadoEntregaPendiente.PENDIENTE
        entrega.ruta_id = None
        entrega.fecha_inclusion = None
        guardar(db, entrega)


def fallar_parada(
    db: Session,
    ruta: Ruta,
    parada: ParadaRuta,
    reportado_por: Usuario,
    motivo: TipoIncidencia,
    descripcion: str | None,
    reprogramar: bool = False,
) -> Ruta:
    """Marca `parada` como no entregada, deja registrada la incidencia (y, si se
    pidió, la entrega reprogramada para la próxima ruta) y avanza igual que al
    completar."""
    parada.estado = EstadoParada.FALLIDA
    parada.motivo_fallo = motivo
    guardar(db, parada)
    incidencia = crear_incidencia(
        db,
        ruta=ruta,
        reportado_por=reportado_por,
        tipo=motivo,
        descripcion=descripcion,
        parada=parada,
    )
    if reprogramar:
        reprogramar_entrega(db, reportado_por, parada, incidencia)

    _avanzar_ruta(db, ruta)
    return ruta


def hay_otras_paradas_pendientes(ruta: Ruta, parada: ParadaRuta) -> bool:
    return any(p.estado == EstadoParada.PENDIENTE and p.id != parada.id for p in ruta.paradas)


def saltear_parada(db: Session, ruta: Ruta, parada: ParadaRuta) -> Ruta:
    """Manda `parada` al final del recorrido pendiente y pasa a la siguiente.
    Quien llama ya verificó que quedan otras pendientes."""
    parada.estado = EstadoParada.PENDIENTE
    parada.veces_salteada += 1
    # Si había avisado que llegó y se va sin entregar, esa llegada ya no vale
    # para el próximo intento.
    parada.hora_real_llegada = None

    ordenadas = sorted(ruta.paradas, key=lambda p: p.orden)
    nuevo_orden = [p for p in ordenadas if p.id != parada.id] + [parada]

    # UniqueConstraint(ruta_id, orden): SQLAlchemy emite un UPDATE por fila, así
    # que renumerar directo puede chocar a mitad de camino. Primero se pasan
    # todas a órdenes negativos (libres), después a los definitivos.
    for indice, p in enumerate(nuevo_orden):
        p.orden = -(indice + 1)
    db.flush()
    for indice, p in enumerate(nuevo_orden):
        p.orden = indice
    db.flush()
    # El relationship `paradas` quedó en el orden viejo en memoria.
    db.refresh(ruta)

    _avanzar_ruta(db, ruta)
    return ruta


def obtener_parada_de_ruta(db: Session, ruta: Ruta, parada_id: uuid.UUID) -> ParadaRuta | None:
    return next((p for p in ruta.paradas if p.id == parada_id), None)
