import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api import schemas_clientes as schemas
from api.dependencies import get_db, obtener_usuario_actual, requiere_planificador
from api.schemas_auth import MensajeResponse
from db import crud
from db.modelos import Cliente, Usuario

router = APIRouter(prefix="/api/v1/clientes", tags=["Clientes"])


def _obtener_cliente_propio(db: Session, cliente_id: uuid.UUID, usuario: Usuario) -> Cliente:
    cliente = crud.obtener_cliente_propio(db, cliente_id, usuario.ambito_dueño)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")
    return cliente


@router.post("", response_model=schemas.ClientePublico, status_code=201)
def crear_cliente(
    datos: schemas.ClienteCrear,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_planificador),
):
    return crud.crear_cliente(db, datos, usuario.ambito_dueño)


@router.get("", response_model=list[schemas.ClientePublico])
def listar_clientes(
    db: Session = Depends(get_db), usuario: Usuario = Depends(obtener_usuario_actual)
):
    return crud.listar_clientes(db, usuario.ambito_dueño)


@router.patch("/{cliente_id}", response_model=schemas.ClientePublico)
def actualizar_cliente(
    cliente_id: uuid.UUID,
    datos: schemas.ClienteActualizar,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_planificador),
):
    cliente = _obtener_cliente_propio(db, cliente_id, usuario)
    return crud.actualizar_cliente(db, cliente, datos.model_dump(exclude_unset=True))


@router.delete("/{cliente_id}", response_model=MensajeResponse)
def eliminar_cliente(
    cliente_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_planificador),
):
    cliente = _obtener_cliente_propio(db, cliente_id, usuario)
    crud.eliminar_cliente(db, cliente)
    return MensajeResponse(mensaje="Cliente eliminado.")
