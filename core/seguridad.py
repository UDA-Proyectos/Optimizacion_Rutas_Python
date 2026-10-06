import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings

contexto_hash = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hashear_contrasena(contrasena: str) -> str:
    return contexto_hash.hash(contrasena)


def verificar_contrasena(contrasena_plana: str, contrasena_hash: str | None) -> bool:
    if contrasena_hash is None:  # cuenta creada con Google
        return False
    return contexto_hash.verify(contrasena_plana, contrasena_hash)


def crear_token_acceso(usuario_id: uuid.UUID, rol: str, empresa_id: uuid.UUID | None) -> str:
    ahora = datetime.now(UTC)
    payload = {
        "sub": str(usuario_id),
        "rol": rol,
        "empresa_id": str(empresa_id) if empresa_id else None,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


TIPO_REGISTRO_GOOGLE = "registro_google"
MINUTOS_REGISTRO_GOOGLE = 15


def _decodificar(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise ValueError(f"Token inválido o expirado: {e}")


def decodificar_token(token: str) -> dict:
    payload = _decodificar(token)
    # Los tokens de sesión no llevan "tipo": así uno de registro pendiente nunca sirve como sesión.
    if "tipo" in payload:
        raise ValueError("El token no es de sesión.")
    return payload


def crear_token_registro_google(google_sub: str, email: str, nombre: str) -> str:
    ahora = datetime.now(UTC)
    payload = {
        "tipo": TIPO_REGISTRO_GOOGLE,
        "google_sub": google_sub,
        "email": email,
        "nombre": nombre,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=MINUTOS_REGISTRO_GOOGLE),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decodificar_token_registro_google(token: str) -> dict:
    payload = _decodificar(token)
    if payload.get("tipo") != TIPO_REGISTRO_GOOGLE:
        raise ValueError("El token no es de registro con Google.")
    return payload
