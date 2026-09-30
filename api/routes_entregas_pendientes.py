from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api import schemas_entregas_pendientes as schemas
from api.dependencies import get_db, requiere_chofer_independiente
from db import crud
from db.modelos import Usuario

router = APIRouter(prefix="/api/v1/entregas-pendientes", tags=["Entregas pendientes"])


@router.get("", response_model=list[schemas.EntregaPendientePublica])
def listar_entregas_pendientes(
    db: Session = Depends(get_db), usuario: Usuario = Depends(requiere_chofer_independiente)
):
    return [
        schemas.EntregaPendientePublica(
            id=entrega.id,
            cliente_id=entrega.cliente_id,
            cliente_nombre=entrega.cliente.nombre,
            cliente_direccion=entrega.cliente.direccion,
            carga_kg=entrega.carga_kg,
            unidades=entrega.unidades,
            ventana_inicio=entrega.ventana_inicio,
            ventana_fin=entrega.ventana_fin,
            fecha_creacion=entrega.fecha_creacion,
            fecha_origen=entrega.parada_origen.ruta.fecha,
        )
        for entrega in crud.listar_entregas_pendientes(db, usuario.id)
    ]
