import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from jose import jwt

from api import routes_google
from core.config import settings
from core.seguridad import (
    crear_token_acceso,
    crear_token_registro_google,
    decodificar_token,
    decodificar_token_registro_google,
)
from db import crud
from services import google_oauth
from services.google_oauth import IdentidadGoogle
from tests.conftest import DATOS_VEHICULO
from tests.conftest import payload_chofer as _payload_chofer

BASE = "/api/v1/auth"
CLIENT_ID = "cliente-test.apps.googleusercontent.com"
RUTA_COOKIES = "/api/v1/auth/google"


@pytest.fixture
def google_activo(monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", CLIENT_ID)
    monkeypatch.setattr(settings, "google_client_secret", "secreto-test")
    monkeypatch.setattr(
        settings, "google_redirect_uri", "http://testserver/api/v1/auth/google/callback"
    )


@pytest.fixture
def identidad_google(monkeypatch, google_activo):
    """Reemplaza el canje con Google; el test cambia `actual` para elegir la identidad."""
    estado = {"actual": IdentidadGoogle(sub="sub-123", email="nuevo@gmail.com", nombre="Nuevo")}

    def _intercambiar(codigo: str) -> IdentidadGoogle:
        resultado = estado["actual"]
        if isinstance(resultado, Exception):
            raise resultado
        return resultado

    monkeypatch.setattr(routes_google, "intercambiar_codigo", _intercambiar)
    return estado


def _iniciar(client) -> str:
    respuesta = client.get(f"{BASE}/google/iniciar", follow_redirects=False)
    assert respuesta.status_code == 302
    return parse_qs(urlparse(respuesta.headers["location"]).query)["state"][0]


def _volver_de_google(client, **parametros):
    estado = _iniciar(client)
    parametros.setdefault("state", estado)
    parametros.setdefault("code", "codigo-test")
    return client.get(f"{BASE}/google/callback", params=parametros, follow_redirects=False)


def _ruta_de_redireccion(respuesta) -> str:
    destino = urlparse(respuesta.headers["location"])
    return destino.path + (f"?{destino.query}" if destino.query else "")


def _registrar_con_contrasena(client, email="existente@gmail.com", patente="EX123AA"):
    respuesta = client.post(
        f"{BASE}/registro/chofer-independiente",
        json=_payload_chofer(email, patente=patente),
    )
    assert respuesta.status_code == 201
    client.cookies.clear()
    return respuesta.json()


def _completar(client, **cambios):
    cuerpo = {"nombre_completo": "Nuevo Chofer", **DATOS_VEHICULO, **cambios}
    return client.post(f"{BASE}/google/completar-registro", json=cuerpo)


# --- Disponibilidad --------------------------------------------------------


def test_proveedores_sin_configurar(client, monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", None)
    assert client.get(f"{BASE}/proveedores").json() == {"google": False}


def test_proveedores_con_google(client, google_activo):
    assert client.get(f"{BASE}/proveedores").json() == {"google": True}


def test_iniciar_sin_configurar_vuelve_al_login(client, monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", None)
    respuesta = client.get(f"{BASE}/google/iniciar", follow_redirects=False)
    assert respuesta.status_code == 302
    assert _ruta_de_redireccion(respuesta) == "/login?error_google=no_disponible"


def test_iniciar_redirige_a_google_con_estado(client, google_activo):
    respuesta = client.get(f"{BASE}/google/iniciar", follow_redirects=False)
    destino = urlparse(respuesta.headers["location"])
    parametros = parse_qs(destino.query)
    assert destino.netloc == "accounts.google.com"
    assert parametros["client_id"] == [CLIENT_ID]
    assert parametros["scope"] == ["openid email profile"]
    assert parametros["state"][0] == client.cookies.get("google_estado", path=RUTA_COOKIES)


# --- Validación de la vuelta -----------------------------------------------


def test_estado_distinto_no_inicia_sesion(client, identidad_google):
    respuesta = _volver_de_google(client, state="otro-estado")
    assert _ruta_de_redireccion(respuesta) == "/login?error_google=estado_invalido"
    assert "token_acceso" not in respuesta.cookies


def test_sin_cookie_de_estado_no_inicia_sesion(client, identidad_google):
    respuesta = client.get(
        f"{BASE}/google/callback",
        params={"state": "x", "code": "c"},
        follow_redirects=False,
    )
    assert _ruta_de_redireccion(respuesta) == "/login?error_google=estado_invalido"


def test_usuario_cancela_en_google(client, identidad_google):
    respuesta = _volver_de_google(client, error="access_denied", code=None)
    assert _ruta_de_redireccion(respuesta) == "/login?error_google=cancelado"


def test_fallo_del_canje(client, identidad_google):
    identidad_google["actual"] = google_oauth.ErrorGoogle("fallo_google", "timeout")
    respuesta = _volver_de_google(client)
    assert _ruta_de_redireccion(respuesta) == "/login?error_google=fallo_google"
    assert "timeout" not in respuesta.headers["location"]


def test_email_no_verificado(client, identidad_google):
    identidad_google["actual"] = google_oauth.ErrorGoogle("email_no_verificado")
    respuesta = _volver_de_google(client)
    assert _ruta_de_redireccion(respuesta) == "/login?error_google=email_no_verificado"


# --- Cuenta existente ------------------------------------------------------


def test_vincula_por_email_y_permite_seguir_con_contrasena(client, identidad_google, db_session):
    _registrar_con_contrasena(client, email="Existente@gmail.com")
    identidad_google["actual"] = IdentidadGoogle("sub-ex", "existente@gmail.com", "Ex")

    respuesta = _volver_de_google(client)
    assert _ruta_de_redireccion(respuesta) == "/"
    assert "token_acceso" in respuesta.cookies
    usuario = crud.obtener_usuario_por_google_sub(db_session, "sub-ex")
    assert usuario is not None and usuario.email == "Existente@gmail.com"

    client.cookies.clear()
    login = client.post(
        f"{BASE}/login", json={"email": "Existente@gmail.com", "contrasena": "soloYoManejo1"}
    )
    assert login.status_code == 200


def test_cuenta_ya_vinculada_inicia_sesion(client, identidad_google):
    _registrar_con_contrasena(client)
    identidad_google["actual"] = IdentidadGoogle("sub-ex", "existente@gmail.com", "Ex")
    _volver_de_google(client)
    client.cookies.clear()

    # Aunque el email de Google haya cambiado, el sub identifica la cuenta.
    identidad_google["actual"] = IdentidadGoogle("sub-ex", "otro-email@gmail.com", "Ex")
    respuesta = _volver_de_google(client)
    assert _ruta_de_redireccion(respuesta) == "/"
    me = client.get(f"{BASE}/me").json()
    assert me["email"] == "existente@gmail.com"


def test_usuario_inactivo_no_entra_ni_se_vincula(client, identidad_google, db_session):
    _registrar_con_contrasena(client)
    usuario = crud.obtener_usuario_por_email(db_session, "existente@gmail.com")
    usuario.activo = False
    db_session.commit()
    identidad_google["actual"] = IdentidadGoogle("sub-ex", "existente@gmail.com", "Ex")

    respuesta = _volver_de_google(client)
    assert _ruta_de_redireccion(respuesta) == "/login?error_google=cuenta_inactiva"
    assert "token_acceso" not in respuesta.cookies
    db_session.refresh(usuario)
    assert usuario.google_sub is None


def test_cuenta_vinculada_a_otra_identidad(client, identidad_google, db_session):
    _registrar_con_contrasena(client)
    usuario = crud.obtener_usuario_por_email(db_session, "existente@gmail.com")
    crud.vincular_google(db_session, usuario, "sub-original")
    db_session.commit()
    identidad_google["actual"] = IdentidadGoogle("sub-intruso", "existente@gmail.com", "Ex")

    respuesta = _volver_de_google(client)
    assert _ruta_de_redireccion(respuesta) == "/login?error_google=cuenta_vinculada_otra"
    db_session.refresh(usuario)
    assert usuario.google_sub == "sub-original"


# --- Registro nuevo --------------------------------------------------------


def test_primer_ingreso_no_crea_cuenta_y_deja_registro_pendiente(
    client, identidad_google, db_session
):
    respuesta = _volver_de_google(client)
    assert _ruta_de_redireccion(respuesta) == "/registro/google"
    assert "token_acceso" not in respuesta.cookies
    assert crud.obtener_usuario_por_email(db_session, "nuevo@gmail.com") is None

    pendiente = client.get(f"{BASE}/google/registro-pendiente")
    assert pendiente.status_code == 200
    assert pendiente.json() == {"email": "nuevo@gmail.com", "nombre_completo": "Nuevo"}


def test_completar_registro_crea_chofer_sin_contrasena(client, identidad_google):
    _volver_de_google(client)
    respuesta = _completar(client)
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["email"] == "nuevo@gmail.com"
    assert cuerpo["nombre_completo"] == "Nuevo Chofer"
    assert cuerpo["rol"] == "chofer" and cuerpo["empresa_id"] is None
    assert cuerpo["vehiculo"]["patente"] == DATOS_VEHICULO["patente"]
    assert cuerpo["tiene_contrasena"] is False
    assert "token_acceso" in respuesta.cookies

    # El registro pendiente se descarta.
    assert client.get(f"{BASE}/google/registro-pendiente").status_code == 401
    # Y el próximo ingreso con Google entra directo.
    client.cookies.clear()
    assert _ruta_de_redireccion(_volver_de_google(client)) == "/"


def test_completar_registro_con_datos_invalidos_da_422(client, identidad_google):
    _volver_de_google(client)
    assert _completar(client, capacidad_carga_kg=0).status_code == 422


def test_completar_registro_con_patente_duplicada_da_409(client, identidad_google):
    _registrar_con_contrasena(client, patente=DATOS_VEHICULO["patente"])
    _volver_de_google(client)
    respuesta = _completar(client)
    assert respuesta.status_code == 409
    assert "patente" in respuesta.json()["detail"].lower()


def test_completar_registro_si_el_email_se_registro_mientras_tanto(client, identidad_google):
    _volver_de_google(client)
    pendiente = client.cookies.get("registro_google", path=RUTA_COOKIES)
    # Con otras mayúsculas: igual es el mismo email y no se crea una segunda cuenta.
    _registrar_con_contrasena(client, email="Nuevo@gmail.com")
    client.cookies.set("registro_google", pendiente, path=RUTA_COOKIES)
    assert _completar(client, patente="OTRA123").status_code == 409


def test_completar_registro_sin_pendiente_da_401(client, google_activo):
    assert _completar(client).status_code == 401
    assert client.get(f"{BASE}/google/registro-pendiente").status_code == 401


def test_registro_pendiente_vencido_da_401(client, google_activo):
    vencido = jwt.encode(
        {
            "tipo": "registro_google",
            "google_sub": "s",
            "email": "v@gmail.com",
            "nombre": "V",
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    client.cookies.set("registro_google", vencido, path=RUTA_COOKIES)
    assert _completar(client).status_code == 401


# --- Cuentas sin contraseña ------------------------------------------------


def test_login_con_contrasena_en_cuenta_de_google_da_401(client, identidad_google):
    _volver_de_google(client)
    _completar(client)
    client.cookies.clear()
    respuesta = client.post(
        f"{BASE}/login", json={"email": "nuevo@gmail.com", "contrasena": "cualquiera123"}
    )
    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == "Email o contraseña incorrectos."


def test_cambiar_contrasena_en_cuenta_de_google_da_400(client, identidad_google, db_session):
    _volver_de_google(client)
    _completar(client)
    respuesta = client.post(
        f"{BASE}/cambiar-contrasena",
        json={
            "contrasena_actual": "x",
            "contrasena_nueva": "nuevaClave456",
            "confirmar_contrasena_nueva": "nuevaClave456",
        },
    )
    assert respuesta.status_code == 400
    assert "Google" in respuesta.json()["detail"]
    assert crud.obtener_usuario_por_email(db_session, "nuevo@gmail.com").contrasena_hash is None


# --- Tokens y validación del id_token (sin red) ----------------------------


def test_token_de_registro_no_sirve_como_sesion_ni_al_reves():
    registro = crear_token_registro_google("sub", "a@gmail.com", "A")
    with pytest.raises(ValueError):
        decodificar_token(registro)
    sesion = crear_token_acceso(uuid.uuid4(), "chofer", None)
    with pytest.raises(ValueError):
        decodificar_token_registro_google(sesion)


AHORA = datetime(2026, 10, 6, 12, 0, tzinfo=UTC)


def _claims(**cambios):
    claims = {
        "iss": "https://accounts.google.com",
        "aud": CLIENT_ID,
        "exp": AHORA.timestamp() + 600,
        "sub": "sub-1",
        "email": "a@gmail.com",
        "email_verified": True,
        "name": "Ana",
    }
    claims.update(cambios)
    return claims


def test_claims_validos():
    identidad = google_oauth.validar_claims_id_token(_claims(), CLIENT_ID, AHORA)
    assert identidad == IdentidadGoogle(sub="sub-1", email="a@gmail.com", nombre="Ana")


@pytest.mark.parametrize(
    "cambios",
    [
        {"iss": "https://otro.com"},
        {"aud": "otra-app"},
        {"exp": AHORA.timestamp() - 1},
        {"sub": None},
    ],
)
def test_claims_invalidos(cambios):
    with pytest.raises(google_oauth.ErrorGoogle):
        google_oauth.validar_claims_id_token(_claims(**cambios), CLIENT_ID, AHORA)


def test_claims_email_no_verificado():
    with pytest.raises(google_oauth.ErrorGoogle) as error:
        google_oauth.validar_claims_id_token(_claims(email_verified=False), CLIENT_ID, AHORA)
    assert error.value.codigo == "email_no_verificado"
