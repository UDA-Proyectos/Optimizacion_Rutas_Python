import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api import schemas_incidencias as schemas
from api.dependencies import (
    get_db,
    obtener_usuario_actual,
    requiere_chofer,
    requiere_planificador,
)
from db import crud
from db.modelos import (
    EstadoIncidencia,
    Incidencia,
    ResolucionIncidencia,
    Usuario,
)

router = APIRouter(prefix="/api/v1/incidencias", tags=["Incidencias"])


def _publicas(db: Session, incidencias: list[Incidencia]) -> list[schemas.IncidenciaPublica]:
    reprogramadas = crud.paradas_ya_reprogramadas(
        db, [i.parada_id for i in incidencias if i.parada_id is not None]
    )
    return [
        schemas.IncidenciaPublica(
            id=incidencia.id,
            tipo=incidencia.tipo,
            descripcion=incidencia.descripcion,
            fecha_hora=incidencia.fecha_hora,
            ruta_id=incidencia.ruta_id,
            ruta_fecha=incidencia.ruta.fecha,
            chofer_nombre=incidencia.ruta.chofer.nombre_completo,
            parada_id=incidencia.parada_id,
            parada_nombre=incidencia.parada.nombre_snapshot if incidencia.parada else None,
            estado=incidencia.estado,
            resolucion=incidencia.resolucion,
            fecha_resolucion=incidencia.fecha_resolucion,
            puede_reprogramarse=crud.incidencia_es_reprogramable(incidencia, reprogramadas),
        )
        for incidencia in incidencias
    ]


@router.post("", response_model=schemas.IncidenciaPublica, status_code=201)
def reportar_incidencia(
    datos: schemas.IncidenciaCrear,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_chofer),
):
    ruta = crud.obtener_ruta_en_curso(db, usuario.id)
    if ruta is None:
        raise HTTPException(
            status_code=409,
            detail="Necesitás tener una ruta en curso para reportar una incidencia.",
        )

    parada = None
    if datos.parada_id is not None:
        parada = crud.obtener_parada_de_ruta(db, ruta, datos.parada_id)
        if parada is None:
            raise HTTPException(status_code=404, detail="Esa parada no pertenece a tu ruta de hoy.")

    incidencia = crud.crear_incidencia(
        db,
        ruta=ruta,
        reportado_por=usuario,
        tipo=datos.tipo,
        descripcion=datos.descripcion,
        parada=parada,
    )
    return _publicas(db, [incidencia])[0]


@router.get("", response_model=list[schemas.IncidenciaPublica])
def listar_incidencias(
    estado: EstadoIncidencia | None = Query(None),
    limite: int = Query(100, ge=1, le=200),
    desplazamiento: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    incidencias = crud.listar_incidencias(db, usuario, limite, desplazamiento, estado)
    return _publicas(db, incidencias)


@router.post("/{incidencia_id}/resolver", response_model=schemas.IncidenciaPublica)
def resolver_incidencia(
    incidencia_id: uuid.UUID,
    datos: schemas.ResolverIncidencia,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_planificador),
):
    # En una empresa las resuelve el admin (el chofer de empresa queda afuera en la dependencia).
    incidencia = crud.obtener_incidencia_visible(db, usuario, incidencia_id)
    if incidencia is None:
        raise HTTPException(status_code=404, detail="No encontramos esa incidencia.")
    if incidencia.estado == EstadoIncidencia.RESUELTA:
        raise HTTPException(status_code=409, detail="Esa incidencia ya está resuelta.")

    if datos.resolucion == ResolucionIncidencia.REPROGRAMADA:
        reprogramadas = crud.paradas_ya_reprogramadas(db, [incidencia.parada_id])
        if not crud.incidencia_es_reprogramable(incidencia, reprogramadas):
            raise HTTPException(
                status_code=409,
                detail="Solo se puede reprogramar la entrega de una parada que no se pudo entregar.",
            )
        crud.reprogramar_entrega(db, incidencia.parada, incidencia)
    else:
        crud.cerrar_incidencia(db, incidencia)
    return _publicas(db, [incidencia])[0]
