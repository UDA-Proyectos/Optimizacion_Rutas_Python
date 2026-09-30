from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api import schemas_incidencias as schemas
from api.dependencies import get_db, requiere_chofer_independiente
from db import crud
from db.modelos import EstadoRuta, Incidencia, Usuario

router = APIRouter(prefix="/api/v1/incidencias", tags=["Incidencias"])


def _publica(incidencia: Incidencia) -> schemas.IncidenciaPublica:
    return schemas.IncidenciaPublica(
        id=incidencia.id,
        tipo=incidencia.tipo,
        descripcion=incidencia.descripcion,
        fecha_hora=incidencia.fecha_hora,
        ruta_id=incidencia.ruta_id,
        ruta_fecha=incidencia.ruta.fecha,
        parada_id=incidencia.parada_id,
        parada_nombre=incidencia.parada.nombre_snapshot if incidencia.parada else None,
    )


@router.post("", response_model=schemas.IncidenciaPublica, status_code=201)
def reportar_incidencia(
    datos: schemas.IncidenciaCrear,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_chofer_independiente),
):
    ruta = crud.obtener_ruta_activa(db, usuario.id, datetime.now(UTC).date())
    if ruta is None or ruta.estado != EstadoRuta.EN_CURSO:
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
    return _publica(incidencia)


@router.get("", response_model=list[schemas.IncidenciaPublica])
def listar_incidencias(
    limite: int = Query(100, ge=1, le=200),
    desplazamiento: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_chofer_independiente),
):
    incidencias = crud.listar_incidencias_de_chofer(db, usuario.id, limite, desplazamiento)
    return [_publica(incidencia) for incidencia in incidencias]
