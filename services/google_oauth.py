from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlencode

import requests
from jose import JWTError, jwt

from core.config import settings

# Endpoints fijos del proveedor (no dependen del entorno).
_URL_AUTORIZACION = "https://accounts.google.com/o/oauth2/v2/auth"
_URL_TOKEN = "https://oauth2.googleapis.com/token"
_EMISORES_VALIDOS = {"accounts.google.com", "https://accounts.google.com"}


class ErrorGoogle(Exception):
    """El ingreso con Google no pudo completarse. `codigo` es lo que ve el frontend en
    `/login?error_google=`; el detalle queda solo para el log."""

    def __init__(self, codigo: str, detalle: str = ""):
        super().__init__(detalle or codigo)
        self.codigo = codigo


@dataclass(frozen=True)
class IdentidadGoogle:
    sub: str
    email: str
    nombre: str


def construir_url_autorizacion(estado: str) -> str:
    parametros = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": estado,
        "prompt": "select_account",
    }
    return f"{_URL_AUTORIZACION}?{urlencode(parametros)}"


def validar_claims_id_token(claims: dict, client_id: str, ahora: datetime) -> IdentidadGoogle:
    if claims.get("iss") not in _EMISORES_VALIDOS:
        raise ErrorGoogle("fallo_google", "Emisor del id_token inválido.")
    audiencia = claims.get("aud")
    if audiencia != client_id and not (isinstance(audiencia, list) and client_id in audiencia):
        raise ErrorGoogle("fallo_google", "El id_token no fue emitido para esta aplicación.")
    exp = claims.get("exp")
    if not isinstance(exp, int | float) or exp <= ahora.timestamp():
        raise ErrorGoogle("fallo_google", "El id_token está vencido.")
    if not claims.get("sub") or not claims.get("email"):
        raise ErrorGoogle("fallo_google", "El id_token no trae sub o email.")
    if claims.get("email_verified") is not True:
        raise ErrorGoogle("email_no_verificado")
    return IdentidadGoogle(
        sub=str(claims["sub"]),
        email=str(claims["email"]),
        nombre=str(claims.get("name") or claims["email"].split("@")[0]),
    )


def intercambiar_codigo(codigo: str) -> IdentidadGoogle:
    try:
        respuesta = requests.post(
            _URL_TOKEN,
            data={
                "code": codigo,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=settings.google_timeout_segundos,
        )
        respuesta.raise_for_status()
        id_token = respuesta.json()["id_token"]
        # Sin verificar la firma: el token llega directo del endpoint de tokens de Google por TLS
        # y autenticado con el client_secret (OIDC Core §3.1.3.7). Si alguna vez llega desde el
        # navegador, hay que verificar la firma contra las claves públicas de Google.
        claims = jwt.get_unverified_claims(id_token)
    except (requests.exceptions.RequestException, KeyError, ValueError, JWTError) as e:
        raise ErrorGoogle("fallo_google", f"No se pudo canjear el código con Google: {e}") from e
    return validar_claims_id_token(claims, settings.google_client_id or "", datetime.now(UTC))
