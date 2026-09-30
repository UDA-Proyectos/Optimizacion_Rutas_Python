from tests.conftest import payload_chofer

BASE = "/api/v1/depositos"

PAYLOAD_DEPOSITO = {
    "nombre": "Mi base",
    "latitud": -32.8908,
    "longitud": -68.8272,
}


def _registrar_chofer_independiente(client, email="chofer@test.com", patente="AB123CD"):
    return client.post(
        "/api/v1/auth/registro/chofer-independiente",
        json=payload_chofer(email, patente=patente),
    )


def test_crear_y_listar_deposito(client):
    _registrar_chofer_independiente(client)

    respuesta = client.post(BASE, json=PAYLOAD_DEPOSITO)
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["nombre"] == "Mi base"
    assert cuerpo["activo"] is True

    listado = client.get(BASE)
    assert listado.status_code == 200
    assert len(listado.json()) == 1


def test_crear_deposito_sin_sesion_da_401(client):
    respuesta = client.post(BASE, json=PAYLOAD_DEPOSITO)
    assert respuesta.status_code == 401


def test_actualizar_deposito(client):
    _registrar_chofer_independiente(client)
    creado = client.post(BASE, json=PAYLOAD_DEPOSITO).json()

    respuesta = client.patch(f"{BASE}/{creado['id']}", json={"nombre": "Base renombrada"})
    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Base renombrada"


def test_eliminar_deposito_es_soft_delete(client):
    _registrar_chofer_independiente(client)
    creado = client.post(BASE, json=PAYLOAD_DEPOSITO).json()

    respuesta = client.delete(f"{BASE}/{creado['id']}")
    assert respuesta.status_code == 200
    assert client.get(BASE).json() == []


def test_deposito_no_visible_ni_editable_para_otro_chofer(client):
    _registrar_chofer_independiente(client, email="chofer1@test.com", patente="AB123CD")
    creado = client.post(BASE, json=PAYLOAD_DEPOSITO).json()
    client.cookies.clear()

    _registrar_chofer_independiente(client, email="chofer2@test.com", patente="ZZ999XX")
    assert client.get(BASE).json() == []

    respuesta = client.patch(f"{BASE}/{creado['id']}", json={"nombre": "Intento ajeno"})
    assert respuesta.status_code == 404


def test_deposito_con_ventana_horaria(client):
    _registrar_chofer_independiente(client)

    creado = client.post(
        BASE, json={**PAYLOAD_DEPOSITO, "ventana_inicio": 480, "ventana_fin": 1080}
    ).json()
    assert creado["ventana_inicio"] == 480
    assert creado["ventana_fin"] == 1080


def test_deposito_con_ventana_invalida_da_422(client):
    _registrar_chofer_independiente(client)

    for inicio, fin in [(1080, 480), (480, 480), (480, None), (None, 480)]:
        respuesta = client.post(
            BASE, json={**PAYLOAD_DEPOSITO, "ventana_inicio": inicio, "ventana_fin": fin}
        )
        assert respuesta.status_code == 422, (inicio, fin)


def test_actualizar_deposito_con_ventana_invalida_da_422(client):
    _registrar_chofer_independiente(client)
    creado = client.post(BASE, json=PAYLOAD_DEPOSITO).json()

    respuesta = client.patch(
        f"{BASE}/{creado['id']}", json={"ventana_inicio": 900, "ventana_fin": 600}
    )
    assert respuesta.status_code == 422

    correcto = client.patch(
        f"{BASE}/{creado['id']}", json={"ventana_inicio": 480, "ventana_fin": 600}
    )
    assert correcto.status_code == 200
    assert correcto.json()["ventana_fin"] == 600
