from tests.conftest import (
    armar_chofer_con_lugares,
    payload_chofer,
    registrar_chofer_independiente,
)

BASE = "/api/v1/auth"
BASE_RUTAS = "/api/v1/rutas"
CONTRASENA = "soloYoManejo1"


def test_editar_perfil_cambia_nombre_y_telefono(client):
    registrar_chofer_independiente(client)

    respuesta = client.patch(
        f"{BASE}/me",
        json={"nombre_completo": "Carlos Renombrado", "telefono": "+54 9 261 555-9999"},
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["nombre_completo"] == "Carlos Renombrado"

    me = client.get(f"{BASE}/me").json()
    assert me["nombre_completo"] == "Carlos Renombrado"
    assert me["telefono"] == "+54 9 261 555-9999"


def test_editar_perfil_es_parcial(client):
    registrar_chofer_independiente(client)
    antes = client.get(f"{BASE}/me").json()

    client.patch(f"{BASE}/me", json={"telefono": "+54 9 261 555-1111"})

    despues = client.get(f"{BASE}/me").json()
    assert despues["nombre_completo"] == antes["nombre_completo"]
    assert despues["telefono"] == "+54 9 261 555-1111"


def test_editar_perfil_con_datos_invalidos_da_422(client):
    registrar_chofer_independiente(client)

    for cuerpo in ({"nombre_completo": ""}, {"nombre_completo": None}, {"telefono": "123"}):
        assert client.patch(f"{BASE}/me", json=cuerpo).status_code == 422, cuerpo


def test_editar_perfil_ignora_el_email(client):
    registrar_chofer_independiente(client, email="original@test.com")

    respuesta = client.patch(
        f"{BASE}/me", json={"nombre_completo": "Otro Nombre", "email": "hackeado@test.com"}
    )
    assert respuesta.status_code == 200
    assert client.get(f"{BASE}/me").json()["email"] == "original@test.com"


def test_editar_vehiculo_sin_ruta_activa(client):
    registrar_chofer_independiente(client)

    respuesta = client.patch(
        f"{BASE}/me/vehiculo",
        json={"tipo_vehiculo": "camioneta", "patente": "zz999xx", "capacidad_carga_kg": 300},
    )
    assert respuesta.status_code == 200
    vehiculo = respuesta.json()["vehiculo"]
    assert vehiculo["tipo_vehiculo"] == "camioneta"
    assert vehiculo["patente"] == "ZZ999XX"
    assert vehiculo["capacidad_carga_kg"] == 300
    assert client.get(f"{BASE}/me").json()["vehiculo"]["capacidad_carga_kg"] == 300


def test_la_nueva_capacidad_se_usa_al_planificar(client, osrm_falso):
    cliente1, _ = armar_chofer_con_lugares(client)
    pedido = {"paradas": [{"cliente_id": cliente1["id"], "carga_kg": 100}]}
    assert client.post(f"{BASE_RUTAS}/optimizar", json=pedido).status_code == 400

    client.patch(f"{BASE}/me/vehiculo", json={"capacidad_carga_kg": 300})

    assert client.post(f"{BASE_RUTAS}/optimizar", json=pedido).status_code == 200


def test_editar_vehiculo_con_patente_de_otro_da_409(client):
    registrar_chofer_independiente(client, email="a@test.com", patente="AA111AA")
    client.cookies.clear()
    registrar_chofer_independiente(client, email="b@test.com", patente="BB222BB")

    respuesta = client.patch(f"{BASE}/me/vehiculo", json={"patente": "AA111AA"})
    assert respuesta.status_code == 409
    assert client.get(f"{BASE}/me").json()["vehiculo"]["patente"] == "BB222BB"


def test_editar_vehiculo_con_su_propia_patente_no_es_conflicto(client):
    registrar_chofer_independiente(client, patente="MI111MI")

    respuesta = client.patch(
        f"{BASE}/me/vehiculo", json={"patente": "mi111mi", "tipo_vehiculo": "furgon"}
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["vehiculo"]["tipo_vehiculo"] == "furgon"


def test_no_se_cambia_capacidad_ni_patente_con_ruta_activa(client, osrm_falso):
    cliente1, _ = armar_chofer_con_lugares(client)
    client.post(
        f"{BASE_RUTAS}/confirmar", json={"paradas": [{"cliente_id": cliente1["id"], "carga_kg": 5}]}
    )
    antes = client.get(f"{BASE}/me").json()["vehiculo"]

    for cuerpo in ({"capacidad_carga_kg": 300}, {"patente": "NU999EV"}):
        assert client.patch(f"{BASE}/me/vehiculo", json=cuerpo).status_code == 409, cuerpo

    assert client.get(f"{BASE}/me").json()["vehiculo"] == antes

    # El tipo de vehículo no altera el plan: se puede cambiar igual.
    assert client.patch(f"{BASE}/me/vehiculo", json={"tipo_vehiculo": "auto"}).status_code == 200
    # Y reenviar la capacidad actual no es un cambio.
    mismo = client.patch(
        f"{BASE}/me/vehiculo", json={"capacidad_carga_kg": antes["capacidad_carga_kg"]}
    )
    assert mismo.status_code == 200


def test_editar_vehiculo_con_datos_invalidos_da_422(client):
    registrar_chofer_independiente(client)

    invalidos = [
        {"capacidad_carga_kg": 0},
        {"capacidad_carga_kg": -5},
        {"capacidad_carga_kg": None},
        {"patente": "AB"},
        {"tipo_vehiculo": "nave"},
    ]
    for cuerpo in invalidos:
        assert client.patch(f"{BASE}/me/vehiculo", json=cuerpo).status_code == 422, cuerpo


def test_admin_de_empresa_no_edita_vehiculo(client):
    client.post(
        f"{BASE}/registro/empresa",
        json={
            "nombre_empresa": "Distribuidora Perfil",
            "email": "admin-perfil@test.com",
            "contrasena": "contrasenaSegura123",
            "confirmar_contrasena": "contrasenaSegura123",
            "nombre_completo": "Ana Admin",
        },
    )
    assert client.patch(f"{BASE}/me/vehiculo", json={"tipo_vehiculo": "auto"}).status_code == 403


def test_cambiar_contrasena(client):
    registrar_chofer_independiente(client, email="cambio@test.com")

    respuesta = client.post(
        f"{BASE}/cambiar-contrasena",
        json={
            "contrasena_actual": CONTRASENA,
            "contrasena_nueva": "nuevaClave456",
            "confirmar_contrasena_nueva": "nuevaClave456",
        },
    )
    assert respuesta.status_code == 200

    client.cookies.clear()
    vieja = client.post(
        f"{BASE}/login", json={"email": "cambio@test.com", "contrasena": CONTRASENA}
    )
    assert vieja.status_code == 401
    nueva = client.post(
        f"{BASE}/login", json={"email": "cambio@test.com", "contrasena": "nuevaClave456"}
    )
    assert nueva.status_code == 200


def test_cambiar_contrasena_con_la_actual_incorrecta_da_400(client):
    registrar_chofer_independiente(client, email="mala@test.com")

    respuesta = client.post(
        f"{BASE}/cambiar-contrasena",
        json={
            "contrasena_actual": "no-es-esa",
            "contrasena_nueva": "nuevaClave456",
            "confirmar_contrasena_nueva": "nuevaClave456",
        },
    )
    assert respuesta.status_code == 400

    client.cookies.clear()
    intento = client.post(
        f"{BASE}/login", json={"email": "mala@test.com", "contrasena": CONTRASENA}
    )
    assert intento.status_code == 200


def test_cambiar_contrasena_con_datos_invalidos_da_422(client):
    registrar_chofer_independiente(client)

    invalidos = [
        {"contrasena_nueva": "nuevaClave456", "confirmar_contrasena_nueva": "otraDistinta1"},
        {"contrasena_nueva": "corta", "confirmar_contrasena_nueva": "corta"},
    ]
    for cuerpo in invalidos:
        respuesta = client.post(
            f"{BASE}/cambiar-contrasena", json={"contrasena_actual": CONTRASENA, **cuerpo}
        )
        assert respuesta.status_code == 422, cuerpo


def test_estos_endpoints_requieren_sesion(client):
    assert client.patch(f"{BASE}/me", json={"telefono": "+54 9 261 555-0000"}).status_code == 401
    assert client.patch(f"{BASE}/me/vehiculo", json={"tipo_vehiculo": "auto"}).status_code == 401
    cambio = {
        "contrasena_actual": "x",
        "contrasena_nueva": "nuevaClave456",
        "confirmar_contrasena_nueva": "nuevaClave456",
    }
    assert client.post(f"{BASE}/cambiar-contrasena", json=cambio).status_code == 401


def test_payload_de_registro_sigue_siendo_valido_tras_compartir_reglas(client):
    """El registro y la edición comparten las reglas de contraseña y patente:
    esto asegura que extraerlas no rompió el registro."""
    assert (
        client.post(
            f"{BASE}/registro/chofer-independiente", json=payload_chofer("reg-ok@test.com")
        ).status_code
        == 201
    )
