import uuid
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api import schemas_rutas as schemas
from api.dependencies import get_db, obtener_usuario_actual, requiere_chofer_independiente
from api.schemas_auth import MensajeResponse
from db import crud
from db.modelos import EstadoParada, EstadoRuta, ParadaRuta, Ruta, TipoProblema, Usuario
from routing.planificador import (
    ErrorPlanificacion,
    ResultadoPlanificacion,
    SeleccionParada,
    planificar_ruta,
)
from services.osrm_client import obtener_geometria_osrm

router = APIRouter(prefix="/api/v1/rutas", tags=["Rutas"])


def _hoy():
    return datetime.now(UTC).date()


def _selecciones(datos: schemas.OptimizarRutaRequest) -> list[SeleccionParada]:
    return [
        SeleccionParada(
            cliente_id=parada.cliente_id,
            carga_kg=parada.carga_kg,
            unidades=parada.unidades,
            ventana_inicio=parada.ventana_inicio,
            ventana_fin=parada.ventana_fin,
        )
        for parada in datos.paradas
    ]


def _planificar(db: Session, usuario: Usuario, datos: schemas.OptimizarRutaRequest):
    try:
        return planificar_ruta(
            db,
            usuario,
            _selecciones(datos),
            usa_ventanas_horarias=datos.usa_ventanas_horarias,
            deposito_id=datos.deposito_id,
        )
    except ErrorPlanificacion as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


def _preview(resultado: ResultadoPlanificacion) -> schemas.RutaPreview:
    return schemas.RutaPreview(
        paradas=[
            schemas.ParadaPreview(
                cliente_id=parada.cliente.id,
                nombre=parada.cliente.nombre,
                direccion=parada.cliente.direccion,
                orden=parada.orden,
                carga_kg=parada.carga_kg,
                unidades=parada.unidades,
                distancia_acumulada_m=parada.distancia_acumulada_m,
                ventana_inicio=parada.ventana_inicio,
                ventana_fin=parada.ventana_fin,
                hora_estimada_llegada=parada.hora_estimada_llegada,
            )
            for parada in resultado.paradas
        ],
        distancia_total_m=resultado.distancia_total_m,
        carga_total_kg=resultado.carga_total_kg,
        distancia_sin_optimizar_m=resultado.distancia_sin_optimizar_m,
        ahorro_m=resultado.distancia_sin_optimizar_m - resultado.distancia_total_m,
        explicacion=resultado.explicacion,
        usa_ventanas_horarias=resultado.usa_ventanas_horarias,
        hora_fin_estimada_min=resultado.hora_fin_estimada_min,
    )


def _crear_ruta_desde_resultado(
    db: Session, usuario: Usuario, resultado: ResultadoPlanificacion
) -> Ruta:
    return crud.crear_ruta(
        db,
        chofer=usuario,
        vehiculo=resultado.vehiculo,
        deposito=resultado.deposito,
        fecha=_hoy(),
        tipo_problema=TipoProblema.VRPTW if resultado.usa_ventanas_horarias else TipoProblema.CVRP,
        distancia_total_m=resultado.distancia_total_m,
        explicacion=resultado.explicacion,
        hora_fin_estimada_min=resultado.hora_fin_estimada_min,
        paradas=resultado.paradas,
    )


def _ruta_activa_o_404(db: Session, usuario: Usuario) -> Ruta:
    ruta = crud.obtener_ruta_activa(db, usuario.id, _hoy())
    if ruta is None:
        raise HTTPException(status_code=404, detail="No tenés una ruta activa hoy.")
    return ruta


@router.post("/optimizar", response_model=schemas.RutaPreview)
def optimizar_ruta(
    datos: schemas.OptimizarRutaRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_chofer_independiente),
):
    resultado = _planificar(db, usuario, datos)
    return _preview(resultado)


@router.post("/confirmar", response_model=schemas.RutaPublica, status_code=201)
def confirmar_ruta(
    datos: schemas.OptimizarRutaRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_chofer_independiente),
):
    if crud.obtener_ruta_activa(db, usuario.id, _hoy()) is not None:
        raise HTTPException(status_code=409, detail="Ya tenés una ruta activa para hoy.")
    resultado = _planificar(db, usuario, datos)
    return _crear_ruta_desde_resultado(db, usuario, resultado)


@router.put("/activa", response_model=schemas.RutaPublica)
def editar_ruta_activa(
    datos: schemas.OptimizarRutaRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_chofer_independiente),
):
    """Reemplaza la ruta planificada de hoy por una nueva selección — la
    vieja queda cancelada (no se borra) y se crea una ruta nueva, igual que
    confirmar. Solo antes de iniciarla: una vez en curso no tiene sentido
    editar el plan del día."""
    ruta_actual = _ruta_activa_o_404(db, usuario)
    if ruta_actual.estado != EstadoRuta.PLANIFICADA:
        raise HTTPException(status_code=409, detail="Esta ruta ya arrancó, no se puede editar.")

    resultado = _planificar(db, usuario, datos)

    crud.cancelar_ruta(db, ruta_actual)
    return _crear_ruta_desde_resultado(db, usuario, resultado)


@router.delete("/activa", response_model=MensajeResponse)
def eliminar_ruta_activa(
    db: Session = Depends(get_db), usuario: Usuario = Depends(requiere_chofer_independiente)
):
    ruta = _ruta_activa_o_404(db, usuario)
    crud.cancelar_ruta(db, ruta)
    return MensajeResponse(mensaje="Ruta eliminada.")


@router.post("/activa/iniciar", response_model=schemas.RutaPublica)
def iniciar_ruta_activa(
    db: Session = Depends(get_db), usuario: Usuario = Depends(requiere_chofer_independiente)
):
    ruta = _ruta_activa_o_404(db, usuario)
    if ruta.estado != EstadoRuta.PLANIFICADA:
        raise HTTPException(status_code=409, detail="Esta ruta ya está iniciada o cerrada.")
    return crud.iniciar_ruta(db, ruta)


def _parada_en_curso_o_error(
    db: Session, usuario: Usuario, parada_id: uuid.UUID
) -> tuple[Ruta, ParadaRuta]:
    """Validación común de las acciones sobre la parada actual: ruta en curso,
    parada de esa ruta y que sea justo la próxima a visitar."""
    ruta = _ruta_activa_o_404(db, usuario)
    if ruta.estado != EstadoRuta.EN_CURSO:
        raise HTTPException(status_code=409, detail="Iniciá la ruta antes de marcar paradas.")
    parada = crud.obtener_parada_de_ruta(db, ruta, parada_id)
    if parada is None:
        raise HTTPException(status_code=404, detail="Esa parada no pertenece a tu ruta de hoy.")
    if parada.estado != EstadoParada.EN_CURSO:
        raise HTTPException(status_code=409, detail="Esa no es la próxima parada a visitar.")
    return ruta, parada


@router.post("/activa/paradas/{parada_id}/llegada", response_model=schemas.RutaPublica)
def registrar_llegada_activa(
    parada_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_chofer_independiente),
):
    ruta, parada = _parada_en_curso_o_error(db, usuario, parada_id)
    crud.registrar_llegada(db, parada)
    return ruta


@router.post("/activa/paradas/{parada_id}/completar", response_model=schemas.RutaPublica)
def completar_parada_activa(
    parada_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_chofer_independiente),
):
    ruta, parada = _parada_en_curso_o_error(db, usuario, parada_id)
    return crud.completar_parada(db, ruta, parada)


@router.post("/activa/paradas/{parada_id}/fallar", response_model=schemas.RutaPublica)
def fallar_parada_activa(
    parada_id: uuid.UUID,
    datos: schemas.FallarParadaRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_chofer_independiente),
):
    ruta, parada = _parada_en_curso_o_error(db, usuario, parada_id)
    return crud.fallar_parada(db, ruta, parada, usuario, datos.motivo, datos.descripcion)


@router.post("/activa/paradas/{parada_id}/saltear", response_model=schemas.RutaPublica)
def saltear_parada_activa(
    parada_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_chofer_independiente),
):
    ruta, parada = _parada_en_curso_o_error(db, usuario, parada_id)
    if not crud.hay_otras_paradas_pendientes(ruta, parada):
        raise HTTPException(
            status_code=409,
            detail="Es la única parada que queda: entregala o marcala como no entregada.",
        )
    return crud.saltear_parada(db, ruta, parada)


@router.get("/activa", response_model=schemas.RutaPublica | None)
def ruta_activa(db: Session = Depends(get_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return crud.obtener_ruta_activa(db, usuario.id, _hoy())


@router.get("/activa/geometria", response_model=schemas.GeometriaRuta)
def geometria_ruta_activa(
    db: Session = Depends(get_db), usuario: Usuario = Depends(obtener_usuario_actual)
):
    ruta = _ruta_activa_o_404(db, usuario)
    coordenadas = (
        [{"latitud": ruta.deposito.latitud, "longitud": ruta.deposito.longitud}]
        + [
            {"latitud": parada.latitud_snapshot, "longitud": parada.longitud_snapshot}
            for parada in ruta.paradas
        ]
        + [{"latitud": ruta.deposito.latitud, "longitud": ruta.deposito.longitud}]
    )
    try:
        tramos = obtener_geometria_osrm(coordenadas)
    except Exception as error:
        raise HTTPException(
            status_code=502, detail=f"No se pudo trazar el camino: {error}"
        ) from error
    return schemas.GeometriaRuta(tramos=tramos)


@router.get("/historial", response_model=list[schemas.RutaHistorialItem])
def historial_rutas(
    desde: date = Query(...),
    hasta: date = Query(...),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_chofer_independiente),
):
    rutas = crud.listar_rutas_historial(db, usuario.id, desde, hasta)
    return [
        schemas.RutaHistorialItem(
            id=ruta.id,
            fecha=ruta.fecha,
            estado=ruta.estado,
            tipo_problema=ruta.tipo_problema,
            distancia_total_m=ruta.distancia_total_m,
            paradas_total=len(ruta.paradas),
            paradas_completadas=sum(
                1 for parada in ruta.paradas if parada.estado == EstadoParada.COMPLETADA
            ),
            paradas_fallidas=sum(
                1 for parada in ruta.paradas if parada.estado == EstadoParada.FALLIDA
            ),
            incidencias_total=ruta.incidencias_total,
        )
        for ruta in rutas
    ]


@router.get("/historial/{ruta_id}", response_model=schemas.RutaPublica)
def detalle_ruta_historial(
    ruta_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_chofer_independiente),
):
    ruta = crud.obtener_ruta_historial(db, usuario.id, ruta_id)
    if ruta is None:
        raise HTTPException(status_code=404, detail="No encontramos esa ruta en tu historial.")
    return ruta
