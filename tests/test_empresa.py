from tests.conftest import (
    PAYLOAD_CLIENTE_1,
    PAYLOAD_CLIENTE_2,
    PAYLOAD_DEPOSITO,
    iniciar_sesion,
    registrar_admin,
    registrar_chofer_de_empresa,
    registrar_chofer_independiente,
)

BASE = "/api/v1/empresa"


def test_admin_lista_sus_choferes_con_vehiculo_y_resumen(client):
    registrar_admin(client)
    registrar_chofer_de_empresa(client, "admin@flota.com", "beto@flota.com", "BB111BB", "Beto")
    registrar_chofer_de_empresa(client, "admin@flota.com", "ana@flota.com", "AA111AA", "Ana")
    iniciar_sesion(client, "admin@flota.com")

    respuesta = client.get(f"{BASE}/choferes")
    assert respuesta.status_code == 200
    choferes = respuesta.json()
    assert [c["nombre_completo"] for c in choferes] == ["Ana", "Beto"]
    assert choferes[0]["vehiculo"]["patente"] == "AA111AA"
    assert choferes[0]["rutas_del_dia"] == 0
    assert choferes[0]["tiene_ruta_en_curso"] is False


def test_no_incluye_choferes_de_otra_empresa_ni_independientes(client):
    registrar_admin(client, email="otra@flota.com", nombre_empresa="Otra")
    registrar_chofer_de_empresa(client, "otra@flota.com", "ajeno@flota.com", "ZZ111ZZ")
    client.cookies.clear()
    registrar_chofer_independiente(client, email="solo@test.com", patente="SO111LO")
    registrar_admin(client)

    assert client.get(f"{BASE}/choferes").json() == []


def test_choferes_no_pueden_listar_la_flota(client):
    registrar_admin(client)
    registrar_chofer_de_empresa(client, "admin@flota.com", "beto@flota.com", "BB111BB")
    assert client.get(f"{BASE}/choferes").status_code == 403

    client.cookies.clear()
    registrar_chofer_independiente(client, email="solo@test.com", patente="SO111LO")
    assert client.get(f"{BASE}/choferes").status_code == 403


# --- Libreta de la empresa ---------------------------------------------------


def test_admin_gestiona_la_libreta_y_la_flota_la_ve(client):
    registrar_admin(client)
    deposito = client.post("/api/v1/depositos", json=PAYLOAD_DEPOSITO)
    lugar = client.post("/api/v1/clientes", json=PAYLOAD_CLIENTE_1)
    assert deposito.status_code == 201 and lugar.status_code == 201
    assert (
        client.patch(
            f"/api/v1/clientes/{lugar.json()['id']}", json={"nombre": "Kiosco renovado"}
        ).status_code
        == 200
    )

    registrar_chofer_de_empresa(client, "admin@flota.com", "beto@flota.com", "BB111BB")
    assert [c["nombre"] for c in client.get("/api/v1/clientes").json()] == ["Kiosco renovado"]
    assert len(client.get("/api/v1/depositos").json()) == 1


def test_chofer_de_empresa_no_escribe_la_libreta(client):
    registrar_admin(client)
    lugar = client.post("/api/v1/clientes", json=PAYLOAD_CLIENTE_1).json()
    deposito = client.post("/api/v1/depositos", json=PAYLOAD_DEPOSITO).json()
    registrar_chofer_de_empresa(client, "admin@flota.com", "beto@flota.com", "BB111BB")

    assert client.post("/api/v1/clientes", json=PAYLOAD_CLIENTE_2).status_code == 403
    assert client.patch(f"/api/v1/clientes/{lugar['id']}", json={"nombre": "X"}).status_code == 403
    assert client.delete(f"/api/v1/clientes/{lugar['id']}").status_code == 403
    assert client.post("/api/v1/depositos", json=PAYLOAD_DEPOSITO).status_code == 403
    assert client.delete(f"/api/v1/depositos/{deposito['id']}").status_code == 403
    assert len(client.get("/api/v1/clientes").json()) == 1
