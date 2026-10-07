import uuid

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from core.seguridad import decodificar_token
from db.modelos import RolUsuario, Usuario
from db.sesion import get_db

__all__ = [
    "get_db",
    "obtener_usuario_actual",
    "requiere_admin",
    "requiere_chofer",
    "requiere_chofer_independiente",
    "requiere_planificador",
]


def obtener_usuario_actual(request: Request, db: Session = Depends(get_db)) -> Usuario:
    token = request.cookies.get("token_acceso")
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado.")
    try:
        payload = decodificar_token(token)
        usuario_id = uuid.UUID(payload["sub"])
    except (ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada.")

    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo.")
    return usuario


def requiere_admin(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
    if usuario.rol != RolUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Se requiere rol de administrador.")
    if usuario.empresa_id is None:
        # No debería poder pasar — db.crear_admin() es el único camino para crear un
        # ADMIN y exige empresa_id. Si igual pasa (dato corrupto, código futuro que
        # se salte crear_admin), fallar acá con un mensaje claro en vez de dejar que
        # un endpoint downstream (ej. generar_invitacion) reviente con un
        # IntegrityError sin manejar contra codigos_invitacion.empresa_id.
        raise HTTPException(status_code=500, detail="Cuenta admin sin empresa asociada.")
    return usuario


def requiere_chofer_independiente(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
    """Armar y confirmar la propia ruta es autoservicio del chofer sin
    empresa — un chofer de empresa la recibe asignada por su admin (todavía
    sin implementar), no la arma él mismo."""
    if usuario.empresa_id is not None:
        raise HTTPException(
            status_code=403,
            detail="Los choferes de empresa reciben la ruta asignada por su empresa.",
        )
    return usuario


def requiere_chofer(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
    """Cualquier chofer, independiente o de empresa: ejecutar rutas, consultar las propias."""
    if usuario.rol != RolUsuario.CHOFER:
        raise HTTPException(status_code=403, detail="Esta acción es para choferes.")
    return usuario


def requiere_planificador(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
    """Quien arma rutas y gestiona la libreta (lugares, depósitos, entregas reprogramadas):
    el chofer independiente para sí mismo y el admin para su empresa. El chofer de
    empresa ejecuta lo que le asignan y solo consulta."""
    if usuario.rol == RolUsuario.CHOFER and usuario.empresa_id is not None:
        raise HTTPException(status_code=403, detail="Esto lo gestiona tu empresa.")
    return usuario
