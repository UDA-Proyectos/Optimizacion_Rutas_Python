from tests.conftest import payload_chofer

BASE = "/api/v1/clientes"

PAYLOAD_CLIENTE = {
    "nombre": "Kiosco Don José",
    "direccion": "San Martín 123, Mendoza",
    "latitud": -32.8908,
    "longitud": -68.8272,
    "telefono": "+54 9 261 555-1234",
}


def _registrar_chofer_independiente(client, email="chofer@test.com", patente="AB123CD"):
    return client.post(
        "/api/v1/auth/registro/chofer-independiente",
        json=payload_chofer(email, patente=patente),
    )


def test_crear_y_listar_cliente(client):
    _registrar_chofer_independiente(client)

    respuesta = client.post(BASE, json=PAYLOAD_CLIENTE)
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["nombre"] == "Kiosco Don José"
    assert cuerpo["activo"] is True

    listado = client.get(BASE)
    assert listado.status_code == 200
    assert len(listado.json()) == 1
    assert listado.json()[0]["direccion"] == "San Martín 123, Mendoza"


def test_crear_cliente_sin_sesion_da_401(client):
    respuesta = client.post(BASE, json=PAYLOAD_CLIENTE)
    assert respuesta.status_code == 401


def test_actualizar_cliente(client):
    _registrar_chofer_independiente(client)
    creado = client.post(BASE, json=PAYLOAD_CLIENTE).json()

    respuesta = client.patch(f"{BASE}/{creado['id']}", json={"nombre": "Kiosco Renombrado"})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["nombre"] == "Kiosco Renombrado"
    # Los campos no enviados no se tocan.
    assert cuerpo["direccion"] == PAYLOAD_CLIENTE["direccion"]


def test_eliminar_cliente_es_soft_delete_y_desaparece_del_listado(client):
    _registrar_chofer_independiente(client)
    creado = client.post(BASE, json=PAYLOAD_CLIENTE).json()

    respuesta = client.delete(f"{BASE}/{creado['id']}")
    assert respuesta.status_code == 200

    assert client.get(BASE).json() == []


def test_cliente_no_visible_ni_editable_para_otro_chofer(client):
    _registrar_chofer_independiente(client, email="chofer1@test.com", patente="AB123CD")
    creado = client.post(BASE, json=PAYLOAD_CLIENTE).json()
    client.cookies.clear()

    _registrar_chofer_independiente(client, email="chofer2@test.com", patente="ZZ999XX")
    assert client.get(BASE).json() == []

    respuesta = client.patch(f"{BASE}/{creado['id']}", json={"nombre": "Intento ajeno"})
    assert respuesta.status_code == 404


def test_choferes_de_la_misma_empresa_comparten_clientes(client):
    respuesta_empresa = client.post(
        "/api/v1/auth/registro/empresa",
        json={
            "nombre_empresa": "Distribuidora Sur",
            "email": "admin@sur.com",
            "contrasena": "contrasenaSegura123",
            "confirmar_contrasena": "contrasenaSegura123",
            "nombre_completo": "Ana Admin",
        },
    )
    assert respuesta_empresa.status_code == 201
    client.post(BASE, json=PAYLOAD_CLIENTE)
    codigo = client.post("/api/v1/auth/invitaciones").json()["codigo"]
    client.cookies.clear()

    client.post(
        "/api/v1/auth/registro/chofer-invitado",
        json={
            "email": "chofer-sur@sur.com",
            "contrasena": "otraSegura123",
            "confirmar_contrasena": "otraSegura123",
            "nombre_completo": "Beto Chofer",
            "telefono": "+54 9 261 555-0200",
            "tipo_vehiculo": "furgon",
            "patente": "XY987ZW",
            "capacidad_carga_kg": 300,
            "codigo_invitacion": codigo,
        },
    )
    listado = client.get(BASE)
    assert listado.status_code == 200
    assert len(listado.json()) == 1


PAYLOAD_CON_HABITUALES = {
    **PAYLOAD_CLIENTE,
    "demanda_carga_default": 20,
    "tiempo_servicio_default": 10,
    "ventana_inicio_default": 540,
    "ventana_fin_default": 720,
}


def test_crear_cliente_con_datos_habituales(client):
    _registrar_chofer_independiente(client)

    respuesta = client.post(BASE, json=PAYLOAD_CON_HABITUALES)
    assert respuesta.status_code == 201

    listado = client.get(BASE).json()[0]
    assert listado["demanda_carga_default"] == 20
    assert listado["tiempo_servicio_default"] == 10
    assert listado["ventana_inicio_default"] == 540
    assert listado["ventana_fin_default"] == 720


def test_cliente_sin_datos_habituales_usa_valores_neutros(client):
    _registrar_chofer_independiente(client)
    creado = client.post(BASE, json=PAYLOAD_CLIENTE).json()

    assert creado["demanda_carga_default"] is None
    assert creado["tiempo_servicio_default"] == 0
    assert creado["ventana_inicio_default"] is None
    assert creado["ventana_fin_default"] is None


def test_cliente_con_ventana_invalida_da_422(client):
    _registrar_chofer_independiente(client)

    for inicio, fin in [(720, 540), (600, 600), (600, None), (None, 600)]:
        respuesta = client.post(
            BASE,
            json={**PAYLOAD_CLIENTE, "ventana_inicio_default": inicio, "ventana_fin_default": fin},
        )
        assert respuesta.status_code == 422, (inicio, fin)

    assert client.get(BASE).json() == []


def test_cliente_con_tiempo_de_servicio_fuera_de_rango_da_422(client):
    _registrar_chofer_independiente(client)

    for minutos in (-1, 241):
        respuesta = client.post(BASE, json={**PAYLOAD_CLIENTE, "tiempo_servicio_default": minutos})
        assert respuesta.status_code == 422, minutos


def test_actualizar_datos_habituales_del_cliente(client):
    _registrar_chofer_independiente(client)
    creado = client.post(BASE, json=PAYLOAD_CON_HABITUALES).json()

    respuesta = client.patch(
        f"{BASE}/{creado['id']}",
        json={
            "tiempo_servicio_default": 25,
            "ventana_inicio_default": None,
            "ventana_fin_default": None,
        },
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["tiempo_servicio_default"] == 25
    assert cuerpo["ventana_inicio_default"] is None
    assert cuerpo["ventana_fin_default"] is None
    # Lo que no se mandó no cambia.
    assert cuerpo["demanda_carga_default"] == 20


def test_actualizar_con_ventana_invalida_o_servicio_nulo_da_422(client):
    _registrar_chofer_independiente(client)
    creado = client.post(BASE, json=PAYLOAD_CON_HABITUALES).json()

    invalidos = [
        {"ventana_inicio_default": 800, "ventana_fin_default": 700},
        {"ventana_inicio_default": 800},
        {"tiempo_servicio_default": None},
    ]
    for cambios in invalidos:
        assert client.patch(f"{BASE}/{creado['id']}", json=cambios).status_code == 422, cambios
