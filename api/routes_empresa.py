import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api import schemas_empresa as schemas
from api import schemas_rutas
from api.dependencies import get_db, requiere_admin
from api.routes_rutas import geometria_de_ruta, hoy_servidor, item_historial
from db import crud
from db.modelos import Ruta, Usuario

router = APIRouter(prefix="/api/v1/empresa", tags=["Empresa"])


@router.get("/choferes", response_model=list[schemas.ChoferDeEmpresa])
def listar_choferes(
    fecha: date | None = None,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(requiere_admin),
):
    # `fecha` es el día local del navegador; sin ella, el del servidor (como en /rutas).
    resumenes = crud.listar_choferes_de_empresa(db, admin.empresa_id, fecha or hoy_servidor())
    return [
        schemas.ChoferDeEmpresa(
            id=r.chofer.id,
            nombre_completo=r.chofer.nombre_completo,
            email=r.chofer.email,
            telefono=r.chofer.telefono,
            activo=r.chofer.activo,
            vehiculo=r.chofer.vehiculo,
            rutas_del_dia=r.rutas_del_dia,
            tiene_ruta_en_curso=r.tiene_ruta_en_curso,
        )
        for r in resumenes
    ]


def _ruta_de_la_flota_o_404(db: Session, admin: Usuario, ruta_id: uuid.UUID) -> Ruta:
    ruta = crud.obtener_ruta_de_empresa(db, admin.empresa_id, ruta_id)
    if ruta is None:
        raise HTTPException(status_code=404, detail="No encontramos esa ruta.")
    return ruta


@router.get("/rutas", response_model=list[schemas_rutas.RutaPublica])
def rutas_de_la_flota(
    fecha: date | None = None,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(requiere_admin),
):
    """Las rutas del día de todos los choferes, con sus paradas: el avance se lee de ahí."""
    return crud.listar_rutas_de_empresa(db, admin.empresa_id, fecha or hoy_servidor())


@router.get("/rutas/{ruta_id}", response_model=schemas_rutas.RutaPublica)
def detalle_ruta_de_la_flota(
    ruta_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(requiere_admin),
):
    return _ruta_de_la_flota_o_404(db, admin, ruta_id)


@router.get("/rutas/{ruta_id}/geometria", response_model=schemas_rutas.GeometriaRuta)
def geometria_ruta_de_la_flota(
    ruta_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(requiere_admin),
):
    return geometria_de_ruta(_ruta_de_la_flota_o_404(db, admin, ruta_id))


@router.get("/historial", response_model=list[schemas_rutas.RutaHistorialItem])
def historial_de_la_flota(
    desde: date = Query(...),
    hasta: date = Query(...),
    chofer_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(requiere_admin),
):
    rutas = crud.listar_historial_de_empresa(db, admin.empresa_id, desde, hasta, chofer_id)
    return [item_historial(ruta) for ruta in rutas]
