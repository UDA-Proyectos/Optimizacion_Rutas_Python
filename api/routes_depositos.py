import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api import schemas_depositos as schemas
from api.dependencies import get_db, obtener_usuario_actual, requiere_planificador
from api.schemas_auth import MensajeResponse
from db import crud
from db.modelos import Deposito, Usuario

router = APIRouter(prefix="/api/v1/depositos", tags=["Depositos"])


def _obtener_deposito_propio(db: Session, deposito_id: uuid.UUID, usuario: Usuario) -> Deposito:
    deposito = crud.obtener_deposito_propio(db, deposito_id, usuario.ambito_dueño)
    if deposito is None:
        raise HTTPException(status_code=404, detail="Depósito no encontrado.")
    return deposito


@router.post("", response_model=schemas.DepositoPublico, status_code=201)
def crear_deposito(
    datos: schemas.DepositoCrear,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_planificador),
):
    return crud.crear_deposito(db, datos, usuario.ambito_dueño)


@router.get("", response_model=list[schemas.DepositoPublico])
def listar_depositos(
    db: Session = Depends(get_db), usuario: Usuario = Depends(obtener_usuario_actual)
):
    return crud.listar_depositos(db, usuario.ambito_dueño)


@router.patch("/{deposito_id}", response_model=schemas.DepositoPublico)
def actualizar_deposito(
    deposito_id: uuid.UUID,
    datos: schemas.DepositoActualizar,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_planificador),
):
    deposito = _obtener_deposito_propio(db, deposito_id, usuario)
    return crud.actualizar_deposito(db, deposito, datos.model_dump(exclude_unset=True))


@router.delete("/{deposito_id}", response_model=MensajeResponse)
def eliminar_deposito(
    deposito_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_planificador),
):
    deposito = _obtener_deposito_propio(db, deposito_id, usuario)
    crud.eliminar_deposito(db, deposito)
    return MensajeResponse(mensaje="Depósito eliminado.")
