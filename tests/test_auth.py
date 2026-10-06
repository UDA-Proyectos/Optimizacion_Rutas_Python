from tests.conftest import payload_chofer as _payload_chofer

BASE = "/api/v1/auth"


def _registrar_empresa(client, email="admin@sur.com"):
    return client.post(
        f"{BASE}/registro/empresa",
        json={
            "nombre_empresa": "Distribuidora Sur",
            "email": email,
            "contrasena": "contrasenaSegura123",
            "confirmar_contrasena": "contrasenaSegura123",
            "nombre_completo": "Ana Admin",
        },
    )


def test_registro_chofer_independiente(client):
    respuesta = client.post(
        f"{BASE}/registro/chofer-independiente",
        json=_payload_chofer("indep@gmail.com"),
    )
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["rol"] == "chofer"
    assert cuerpo["empresa_id"] is None
    assert cuerpo["vehiculo"]["tipo_vehiculo"] == "moto"
    assert cuerpo["vehiculo"]["capacidad_carga_kg"] == 50
    assert cuerpo["tiene_contrasena"] is True
    assert "token_acceso" in respuesta.cookies


def test_registro_contrasenas_no_coinciden_da_422(client):
    payload = _payload_chofer("nomatch@test.com", contrasena="claveUnoValida1")
    payload["confirmar_contrasena"] = "claveDosDistinta2"
    respuesta = client.post(f"{BASE}/registro/chofer-independiente", json=payload)
    assert respuesta.status_code == 422


def test_registro_chofer_independiente_email_duplicado(client):
    client.post(f"{BASE}/registro/chofer-independiente", json=_payload_chofer("dup@gmail.com"))
    respuesta = client.post(
        f"{BASE}/registro/chofer-independiente",
        json=_payload_chofer("dup@gmail.com", contrasena="otraClave123"),
    )
    assert respuesta.status_code == 409


def test_registro_chofer_patente_duplicada_da_409_no_email_duplicado(client):
    """La patente vive en Vehiculo, no en Usuario — un choque de patente no
    debe confundirse con MENSAJE_EMAIL_DUPLICADO (dos choferes distintos,
    emails distintos, misma patente por error de tipeo)."""
    client.post(f"{BASE}/registro/chofer-independiente", json=_payload_chofer("patente1@gmail.com"))
    respuesta = client.post(
        f"{BASE}/registro/chofer-independiente",
        json=_payload_chofer("patente2@gmail.com", contrasena="otraClave123"),
    )
    assert respuesta.status_code == 409
    assert "patente" in respuesta.json()["detail"].lower()


def test_registro_empresa_crea_usuario_admin(client):
    respuesta = _registrar_empresa(client)
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["usuario"]["rol"] == "admin"
    assert cuerpo["usuario"]["empresa_id"] == cuerpo["empresa"]["id"]
    assert cuerpo["usuario"]["vehiculo"] is None
    assert cuerpo["empresa"]["nombre"] == "Distribuidora Sur"


def test_flujo_invitacion_completo(client):
    respuesta_empresa = _registrar_empresa(client)
    empresa_id = respuesta_empresa.json()["empresa"]["id"]

    respuesta_codigo = client.post(f"{BASE}/invitaciones")
    assert respuesta_codigo.status_code == 201
    codigo = respuesta_codigo.json()["codigo"]

    respuesta_chofer = client.post(
        f"{BASE}/registro/chofer-invitado",
        json=_payload_chofer(
            "chofer1@sur.com",
            contrasena="otraSegura123",
            nombre_completo="Beto Chofer",
            codigo_invitacion=codigo,
        ),
    )
    assert respuesta_chofer.status_code == 201
    assert respuesta_chofer.json()["empresa_id"] == empresa_id

    # el mismo código no se puede reutilizar
    respuesta_reuso = client.post(
        f"{BASE}/registro/chofer-invitado",
        json=_payload_chofer(
            "chofer2@sur.com",
            contrasena="otraSegura123",
            nombre_completo="Otro Chofer",
            codigo_invitacion=codigo,
        ),
    )
    assert respuesta_reuso.status_code == 409


def test_registro_chofer_invitado_codigo_inexistente(client):
    respuesta = client.post(
        f"{BASE}/registro/chofer-invitado",
        json=_payload_chofer(
            "nuevo@sur.com", nombre_completo="Nuevo", codigo_invitacion="NOEXISTE"
        ),
    )
    assert respuesta.status_code == 404


def test_invitaciones_requiere_rol_admin(client):
    client.post(f"{BASE}/registro/chofer-independiente", json=_payload_chofer("indep2@gmail.com"))
    respuesta = client.post(f"{BASE}/invitaciones")
    assert respuesta.status_code == 403


def test_login_exitoso_y_me(client):
    _registrar_empresa(client)
    client.cookies.clear()

    respuesta_login = client.post(
        f"{BASE}/login", json={"email": "admin@sur.com", "contrasena": "contrasenaSegura123"}
    )
    assert respuesta_login.status_code == 200

    respuesta_me = client.get(f"{BASE}/me")
    assert respuesta_me.status_code == 200
    assert respuesta_me.json()["email"] == "admin@sur.com"


def test_login_credenciales_invalidas(client):
    _registrar_empresa(client)
    client.cookies.clear()

    respuesta = client.post(
        f"{BASE}/login", json={"email": "admin@sur.com", "contrasena": "incorrecta"}
    )
    assert respuesta.status_code == 401


def test_me_sin_sesion(client):
    respuesta = client.get(f"{BASE}/me")
    assert respuesta.status_code == 401


def test_logout_invalida_sesion(client):
    client.post(f"{BASE}/registro/chofer-independiente", json=_payload_chofer("indep3@gmail.com"))
    respuesta_logout = client.post(f"{BASE}/logout")
    assert respuesta_logout.status_code == 200

    respuesta_me = client.get(f"{BASE}/me")
    assert respuesta_me.status_code == 401


def test_registro_race_email_duplicado_da_409_no_500(client, monkeypatch):
    """Si el pre-chequeo de email no ve la carrera (dos requests concurrentes),
    el INSERT igual choca contra la unicidad de la columna — eso debe traducirse
    a 409, no escapar como 500."""
    client.post(f"{BASE}/registro/chofer-independiente", json=_payload_chofer("race@test.com"))
    client.cookies.clear()

    from api import routes_auth

    monkeypatch.setattr(routes_auth.crud, "obtener_usuario_por_email", lambda db, email: None)

    respuesta = client.post(
        f"{BASE}/registro/chofer-independiente",
        json=_payload_chofer("race@test.com", contrasena="otraClave123"),
    )
    assert respuesta.status_code == 409


def test_admin_sin_empresa_id_falla_claro_en_requiere_admin(client, db_session):
    """crear_admin() exige empresa_id, pero eso es un contrato de tipos, no una
    garantía en runtime. Si igual se cuela un ADMIN sin empresa (bypaseando
    crear_admin), requiere_admin debe frenarlo con un 500 explícito en vez de
    dejar que reviente más abajo contra el NOT NULL de codigos_invitacion."""
    from core.seguridad import hashear_contrasena
    from db.modelos import RolUsuario, Usuario

    admin_corrupto = Usuario(
        email="corrupto@test.com",
        contrasena_hash=hashear_contrasena("claveValida123"),
        nombre_completo="Admin Corrupto",
        rol=RolUsuario.ADMIN,
        empresa_id=None,
    )
    db_session.add(admin_corrupto)
    db_session.flush()

    respuesta_login = client.post(
        f"{BASE}/login", json={"email": "corrupto@test.com", "contrasena": "claveValida123"}
    )
    assert respuesta_login.status_code == 200

    respuesta = client.post(f"{BASE}/invitaciones")
    assert respuesta.status_code == 500
    assert "empresa" in respuesta.json()["detail"].lower()
