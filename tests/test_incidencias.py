from tests.conftest import (
    armar_chofer_con_lugares,
    iniciar_ruta_con_paradas,
    registrar_chofer_independiente,
)

BASE = "/api/v1/incidencias"
BASE_RUTAS = "/api/v1/rutas"


def test_reportar_incidencia_general_de_la_ruta(client, osrm_falso):
    iniciar_ruta_con_paradas(client)

    respuesta = client.post(
        BASE, json={"tipo": "problema_vehiculo", "descripcion": "Pinché una rueda"}
    )
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["tipo"] == "problema_vehiculo"
    assert cuerpo["descripcion"] == "Pinché una rueda"
    assert cuerpo["parada_id"] is None
    assert cuerpo["parada_nombre"] is None
    assert cuerpo["fecha_hora"]


def test_reportar_incidencia_sobre_una_parada(client, osrm_falso):
    paradas = iniciar_ruta_con_paradas(client)

    respuesta = client.post(
        BASE, json={"tipo": "direccion_incorrecta", "parada_id": paradas[0]["id"]}
    )
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["parada_id"] == paradas[0]["id"]
    assert cuerpo["parada_nombre"] == paradas[0]["nombre_snapshot"]


def test_reportar_incidencia_de_parada_ajena_da_404(client, osrm_falso):
    paradas_ajenas = iniciar_ruta_con_paradas(client)
    client.cookies.clear()

    registrar_chofer_independiente(client, email="otro-inc@test.com", patente="IN222IN")
    client.post("/api/v1/depositos", json={"nombre": "Base", "latitud": -32.89, "longitud": -68.82})
    cliente = client.post(
        "/api/v1/clientes",
        json={"nombre": "Otro", "direccion": "X 1", "latitud": -32.88, "longitud": -68.83},
    ).json()
    client.post(
        f"{BASE_RUTAS}/confirmar", json={"paradas": [{"cliente_id": cliente["id"], "carga_kg": 1}]}
    )
    client.post(f"{BASE_RUTAS}/activa/iniciar")

    respuesta = client.post(BASE, json={"tipo": "otro", "parada_id": paradas_ajenas[0]["id"]})
    assert respuesta.status_code == 404
    assert client.get(BASE).json() == []


def test_reportar_incidencia_sin_ruta_en_curso_da_409(client, osrm_falso):
    cliente1, _ = armar_chofer_con_lugares(client)

    # Sin ninguna ruta.
    assert client.post(BASE, json={"tipo": "otro"}).status_code == 409

    # Ruta planificada pero sin iniciar.
    client.post(
        f"{BASE_RUTAS}/confirmar", json={"paradas": [{"cliente_id": cliente1["id"], "carga_kg": 5}]}
    )
    assert client.post(BASE, json={"tipo": "otro"}).status_code == 409


def test_reportar_incidencia_con_tipo_invalido_da_422(client, osrm_falso):
    iniciar_ruta_con_paradas(client)
    assert client.post(BASE, json={"tipo": "inventado"}).status_code == 422
    assert client.post(BASE, json={}).status_code == 422


def test_listar_incidencias_solo_devuelve_las_propias_mas_recientes_primero(client, osrm_falso):
    paradas = iniciar_ruta_con_paradas(client)
    client.post(BASE, json={"tipo": "problema_vehiculo"})
    client.post(BASE, json={"tipo": "otro", "parada_id": paradas[1]["id"]})

    listado = client.get(BASE)
    assert listado.status_code == 200
    tipos = [i["tipo"] for i in listado.json()]
    assert tipos == ["otro", "problema_vehiculo"]

    client.cookies.clear()
    registrar_chofer_independiente(client, email="vacio-inc@test.com", patente="VA333VA")
    assert client.get(BASE).json() == []


def test_listar_incluye_las_incidencias_creadas_al_fallar_una_parada(client, osrm_falso):
    paradas = iniciar_ruta_con_paradas(client)
    client.post(
        f"{BASE_RUTAS}/activa/paradas/{paradas[0]['id']}/fallar", json={"motivo": "cliente_ausente"}
    )

    incidencias = client.get(BASE).json()
    assert len(incidencias) == 1
    assert incidencias[0]["tipo"] == "cliente_ausente"
    assert incidencias[0]["parada_nombre"] == paradas[0]["nombre_snapshot"]


def test_incidencias_requieren_sesion_y_chofer_independiente(client):
    assert client.get(BASE).status_code == 401
    assert client.post(BASE, json={"tipo": "otro"}).status_code == 401
