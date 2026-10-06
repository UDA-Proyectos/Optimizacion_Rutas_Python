import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from api import schemas_auth as schemas
from api.dependencies import get_db
from api.routes_auth import (
    MENSAJE_EMAIL_DUPLICADO,
    crear_cuenta,
    setear_cookie_sesion,
    verificar_patente_disponible,
)
from core.config import settings
from core.seguridad import (
    MINUTOS_REGISTRO_GOOGLE,
    crear_token_registro_google,
    decodificar_token_registro_google,
)
from db import crud
from db.modelos import Usuario
from services.google_oauth import (
    ErrorGoogle,
    IdentidadGoogle,
    construir_url_autorizacion,
    intercambiar_codigo,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación con Google"])

# Cookies del flujo: cortas y limitadas a las rutas de Google.
COOKIE_ESTADO = "google_estado"
COOKIE_REGISTRO = "registro_google"
RUTA_COOKIES = "/api/v1/auth/google"
MINUTOS_ESTADO = 10


def _setear_cookie(response: Response, nombre: str, valor: str, minutos: int) -> None:
    response.set_cookie(
        key=nombre,
        value=valor,
        httponly=True,
        secure=settings.entorno == "produccion",
        # lax alcanza: la vuelta desde Google es una navegación GET de primer nivel.
        samesite="lax",
        max_age=minutos * 60,
        path=RUTA_COOKIES,
    )


def _redirigir_al_frontend(ruta: str) -> RedirectResponse:
    respuesta = RedirectResponse(f"{settings.frontend_url}{ruta}", status_code=302)
    respuesta.delete_cookie(COOKIE_ESTADO, path=RUTA_COOKIES)
    return respuesta


def _validar_vuelta(
    request: Request, code: str | None, state: str | None, error: str | None
) -> str:
    """Devuelve el código de autorización si la vuelta desde Google es legítima."""
    if not settings.google_habilitado:
        raise ErrorGoogle("no_disponible")
    if error:
        raise ErrorGoogle("cancelado" if error == "access_denied" else "fallo_google", error)
    estado_cookie = request.cookies.get(COOKIE_ESTADO)
    if not (state and estado_cookie and secrets.compare_digest(state, estado_cookie)):
        raise ErrorGoogle("estado_invalido")
    if not code:
        raise ErrorGoogle("fallo_google", "Google volvió sin código.")
    return code


def _resolver_usuario(db: Session, identidad: IdentidadGoogle) -> Usuario | None:
    """El usuario con el que entra esta identidad (vinculándolo si hace falta), o None si
    el email es nuevo y hay que completar el registro."""
    usuario = crud.obtener_usuario_por_google_sub(db, identidad.sub)
    if usuario is None:
        usuario = crud.obtener_usuario_por_email_sin_mayusculas(db, identidad.email)
        if usuario is None:
            return None
        if usuario.google_sub is not None:
            raise ErrorGoogle("cuenta_vinculada_otra")
    if not usuario.activo:
        raise ErrorGoogle("cuenta_inactiva")
    if usuario.google_sub is None:
        crud.vincular_google(db, usuario, identidad.sub)
    return usuario


@router.get("/proveedores", response_model=schemas.ProveedoresAuth)
def proveedores_disponibles():
    return schemas.ProveedoresAuth(google=settings.google_habilitado)


@router.get("/google/iniciar", include_in_schema=False)
def iniciar_google() -> RedirectResponse:
    if not settings.google_habilitado:
        return _redirigir_al_frontend("/login?error_google=no_disponible")
    estado = secrets.token_urlsafe(32)
    respuesta = RedirectResponse(construir_url_autorizacion(estado), status_code=302)
    _setear_cookie(respuesta, COOKIE_ESTADO, estado, MINUTOS_ESTADO)
    return respuesta


@router.get("/google/callback", include_in_schema=False)
def callback_google(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    try:
        identidad = intercambiar_codigo(_validar_vuelta(request, code, state, error))
        usuario = _resolver_usuario(db, identidad)
    except ErrorGoogle as e:
        if e.codigo == "fallo_google":
            logger.exception("Falló el ingreso con Google")
        return _redirigir_al_frontend(f"/login?error_google={e.codigo}")

    if usuario is None:
        respuesta = _redirigir_al_frontend("/registro/google")
        token = crear_token_registro_google(identidad.sub, identidad.email, identidad.nombre)
        _setear_cookie(respuesta, COOKIE_REGISTRO, token, MINUTOS_REGISTRO_GOOGLE)
        return respuesta

    respuesta = _redirigir_al_frontend("/")
    setear_cookie_sesion(respuesta, usuario)
    return respuesta


def _registro_pendiente(request: Request) -> dict:
    token = request.cookies.get(COOKIE_REGISTRO)
    if not token:
        raise HTTPException(status_code=401, detail="No hay un registro con Google pendiente.")
    try:
        return decodificar_token_registro_google(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="El registro con Google venció.")


@router.get("/google/registro-pendiente", response_model=schemas.RegistroGooglePendiente)
def obtener_registro_pendiente(request: Request):
    pendiente = _registro_pendiente(request)
    return schemas.RegistroGooglePendiente(
        email=pendiente["email"], nombre_completo=pendiente["nombre"]
    )


@router.post("/google/completar-registro", response_model=schemas.UsuarioPublico, status_code=201)
def completar_registro(
    datos: schemas.CompletarRegistroGoogle,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    pendiente = _registro_pendiente(request)
    # Mismo criterio que el callback: sin distinguir mayúsculas, para no duplicar una cuenta
    # que se registró con email mientras este registro estaba pendiente.
    if crud.obtener_usuario_por_email_sin_mayusculas(db, pendiente["email"]):
        raise HTTPException(status_code=409, detail=MENSAJE_EMAIL_DUPLICADO)
    verificar_patente_disponible(db, datos.patente)
    datos_chofer = schemas.DatosChoferGoogle(email=pendiente["email"], **datos.model_dump())
    usuario = crear_cuenta(
        db,
        datos_chofer.email,
        lambda: crud.crear_chofer(
            db, datos_chofer, contrasena_hash=None, google_sub=pendiente["google_sub"]
        ),
    )
    response.delete_cookie(COOKIE_REGISTRO, path=RUTA_COOKIES)
    setear_cookie_sesion(response, usuario)
    return usuario
