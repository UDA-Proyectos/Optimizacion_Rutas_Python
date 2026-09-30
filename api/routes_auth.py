from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api import schemas_auth as schemas
from api.dependencies import (
    get_db,
    obtener_usuario_actual,
    requiere_admin,
    requiere_chofer_independiente,
)
from core.config import settings
from core.seguridad import crear_token_acceso, hashear_contrasena, verificar_contrasena
from db import crud
from db.modelos import Usuario

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])

NOMBRE_COOKIE = "token_acceso"

MENSAJE_EMAIL_DUPLICADO = "El email ya está registrado."
MENSAJE_PATENTE_DUPLICADA = "La patente ya está registrada."


def _setear_cookie_sesion(response: Response, usuario: Usuario) -> None:
    token = crear_token_acceso(usuario.id, usuario.rol.value, usuario.empresa_id)
    response.set_cookie(
        key=NOMBRE_COOKIE,
        value=token,
        httponly=True,
        secure=settings.entorno == "produccion",
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )


def _crear_cuenta(db: Session, email: str, crear: Callable[[], Usuario]) -> Usuario:
    """Verifica email único y ejecuta `crear`. Si dos requests concurrentes pasan
    ambas el chequeo previo, la unicidad a nivel de columna igual las separa —
    acá se traduce ese IntegrityError a un 409 limpio en vez de dejarlo escapar
    como 500."""
    if crud.obtener_usuario_por_email(db, email):
        raise HTTPException(status_code=409, detail=MENSAJE_EMAIL_DUPLICADO)
    try:
        return crear()
    except IntegrityError:
        # Tras un IntegrityError, SQLAlchemy deja la sesión en estado "pending
        # rollback" — cualquier uso posterior (incluso fuera de este request)
        # revienta con PendingRollbackError si no se limpia acá mismo.
        db.rollback()
        raise HTTPException(status_code=409, detail=MENSAJE_EMAIL_DUPLICADO)


def _verificar_patente_disponible(db: Session, patente: str) -> None:
    """Chequeo dedicado (no delegado a _crear_cuenta, que es genérico para
    empresa+chofer): una patente duplicada no es un conflicto de email, y sin
    esto el IntegrityError de la unique constraint de Vehiculo.patente se
    traduciría erróneamente en MENSAJE_EMAIL_DUPLICADO."""
    if crud.obtener_vehiculo_por_patente(db, patente):
        raise HTTPException(status_code=409, detail=MENSAJE_PATENTE_DUPLICADA)


@router.post(
    "/registro/chofer-independiente", response_model=schemas.UsuarioPublico, status_code=201
)
def registrar_chofer_independiente(
    datos: schemas.RegistroChoferIndependiente, response: Response, db: Session = Depends(get_db)
):
    _verificar_patente_disponible(db, datos.patente)
    usuario = _crear_cuenta(
        db,
        datos.email,
        lambda: crud.crear_chofer(db, datos, contrasena_hash=hashear_contrasena(datos.contrasena)),
    )
    _setear_cookie_sesion(response, usuario)
    return usuario


@router.post("/registro/empresa", response_model=schemas.RegistroEmpresaResponse, status_code=201)
def registrar_empresa(
    datos: schemas.RegistroEmpresa, response: Response, db: Session = Depends(get_db)
):
    empresa = crud.crear_empresa(db, nombre=datos.nombre_empresa)
    usuario = _crear_cuenta(
        db,
        datos.email,
        lambda: crud.crear_admin(
            db,
            email=datos.email,
            contrasena_hash=hashear_contrasena(datos.contrasena),
            nombre_completo=datos.nombre_completo,
            empresa_id=empresa.id,
        ),
    )
    _setear_cookie_sesion(response, usuario)
    return schemas.RegistroEmpresaResponse(usuario=usuario, empresa=empresa)


@router.post("/registro/chofer-invitado", response_model=schemas.UsuarioPublico, status_code=201)
def registrar_chofer_invitado(
    datos: schemas.RegistroChoferInvitado, response: Response, db: Session = Depends(get_db)
):
    invitacion = crud.obtener_codigo_invitacion(db, datos.codigo_invitacion)
    if invitacion is None:
        raise HTTPException(status_code=404, detail="Código de invitación inexistente.")
    if invitacion.usado:
        raise HTTPException(status_code=409, detail="El código de invitación ya fue utilizado.")
    _verificar_patente_disponible(db, datos.patente)

    usuario = _crear_cuenta(
        db,
        datos.email,
        lambda: crud.crear_chofer(
            db,
            datos,
            contrasena_hash=hashear_contrasena(datos.contrasena),
            empresa_id=invitacion.empresa_id,
        ),
    )
    crud.marcar_codigo_usado(db, invitacion, usuario.id)
    _setear_cookie_sesion(response, usuario)
    return usuario


@router.post("/login", response_model=schemas.UsuarioPublico)
def iniciar_sesion(datos: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)):
    usuario = crud.obtener_usuario_por_email(db, datos.email)
    if usuario is None or not verificar_contrasena(datos.contrasena, usuario.contrasena_hash):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos.")
    if not usuario.activo:
        raise HTTPException(status_code=401, detail="Cuenta inactiva.")

    _setear_cookie_sesion(response, usuario)
    return usuario


@router.post("/logout", response_model=schemas.MensajeResponse)
def cerrar_sesion(response: Response):
    response.delete_cookie(key=NOMBRE_COOKIE, path="/")
    return schemas.MensajeResponse(mensaje="Sesión cerrada.")


@router.get("/me", response_model=schemas.UsuarioPublico)
def usuario_actual(usuario: Usuario = Depends(obtener_usuario_actual)):
    return usuario


@router.patch("/me", response_model=schemas.UsuarioPublico)
def actualizar_perfil(
    datos: schemas.PerfilActualizar,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return crud.actualizar_usuario(db, usuario, datos.model_dump(exclude_unset=True))


@router.patch("/me/vehiculo", response_model=schemas.UsuarioPublico)
def actualizar_vehiculo_propio(
    datos: schemas.VehiculoActualizar,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_chofer_independiente),
):
    vehiculo = usuario.vehiculo
    if vehiculo is None:
        raise HTTPException(status_code=404, detail="No tenés un vehículo registrado.")
    cambios = datos.model_dump(exclude_unset=True)

    # Capacidad y patente entran en la planificación de cualquier ruta (también
    # las de días futuros, que ya se planificaron con la capacidad actual):
    # cambiar alguna con una ruta planificada o en curso la dejaría inconsistente.
    cambia_capacidad = cambios.get("capacidad_carga_kg", vehiculo.capacidad_carga_kg) != (
        vehiculo.capacidad_carga_kg
    )
    cambia_patente = cambios.get("patente", vehiculo.patente) != vehiculo.patente
    if (cambia_capacidad or cambia_patente) and crud.hay_ruta_abierta(db, usuario.id):
        raise HTTPException(
            status_code=409,
            detail=(
                "Terminá o cancelá tus rutas planificadas o en curso antes de cambiar "
                "la patente o la capacidad."
            ),
        )

    if cambia_patente:
        existente = crud.obtener_vehiculo_por_patente(db, cambios["patente"])
        if existente is not None and existente.id != vehiculo.id:
            raise HTTPException(status_code=409, detail=MENSAJE_PATENTE_DUPLICADA)

    try:
        crud.actualizar_vehiculo(db, vehiculo, cambios)
    except IntegrityError:
        # Carrera entre el chequeo de arriba y el UPDATE: la unique constraint
        # de Vehiculo.patente decide.
        db.rollback()
        raise HTTPException(status_code=409, detail=MENSAJE_PATENTE_DUPLICADA)
    return usuario


@router.post("/cambiar-contrasena", response_model=schemas.MensajeResponse)
def cambiar_contrasena(
    datos: schemas.CambiarContrasena,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    if not verificar_contrasena(datos.contrasena_actual, usuario.contrasena_hash):
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta.")
    crud.cambiar_contrasena(db, usuario, hashear_contrasena(datos.contrasena_nueva))
    return schemas.MensajeResponse(mensaje="Contraseña actualizada.")


@router.post("/invitaciones", response_model=schemas.CodigoInvitacionPublico, status_code=201)
def generar_invitacion(db: Session = Depends(get_db), admin: Usuario = Depends(requiere_admin)):
    return crud.crear_codigo_invitacion(
        db, empresa_id=admin.empresa_id, creado_por_usuario_id=admin.id
    )


@router.get("/invitaciones", response_model=list[schemas.CodigoInvitacionPublico])
def listar_invitaciones(db: Session = Depends(get_db), admin: Usuario = Depends(requiere_admin)):
    return crud.listar_codigos_invitacion(db, empresa_id=admin.empresa_id)
