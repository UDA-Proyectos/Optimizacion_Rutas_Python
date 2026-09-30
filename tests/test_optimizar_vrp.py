import pytest

from tests.conftest import _matriz_sintetica

URL = "/api/v1/optimizar"

DEPOSITO = {"ubicacion": {"latitud": -32.8908, "longitud": -68.8272}}
CLIENTE_A = {"id_cliente": "A", "ubicacion": {"latitud": -32.885, "longitud": -68.82}}
CLIENTE_B = {"id_cliente": "B", "ubicacion": {"latitud": -32.895, "longitud": -68.835}}


def _pedido(clientes, capacidad=50, tipo="CVRP", deposito=DEPOSITO):
    return {
        "tipo_problema": tipo,
        "deposito": deposito,
        "clientes": clientes,
        "vehiculos": [{"id_vehiculo": "V1", "capacidad": capacidad}],
    }


@pytest.fixture
def osrm_falso_api(monkeypatch):
    """Este endpoint importa `obtener_matriz_osrm` en su propio módulo (no pasa
    por el planificador), así que se reemplaza ahí."""
    monkeypatch.setattr("api.routes.obtener_matriz_osrm", _matriz_sintetica)


@pytest.fixture
def solver_rapido(monkeypatch):
    # Un problema infactible agota el time_limit completo: se acorta para no
    # frenar la suite.
    monkeypatch.setattr("routing.solver.settings.solver_time_limit_segundos", 1)


def test_problema_sin_solucion_responde_400_con_el_mensaje_del_solver(
    client, osrm_falso_api, solver_rapido
):
    # Demanda total (60) mayor que la única capacidad disponible (50).
    respuesta = client.post(
        URL,
        json=_pedido(
            [
                {**CLIENTE_A, "demanda_carga": 30},
                {**CLIENTE_B, "demanda_carga": 30},
            ]
        ),
    )
    assert respuesta.status_code == 400
    assert "solución factible" in respuesta.json()["detail"]


def test_vrptw_con_ventanas_imposibles_responde_400(client, osrm_falso_api, solver_rapido):
    deposito = {**DEPOSITO, "ventana_horaria": {"inicio": 480, "fin": 481}}
    cliente = {
        **CLIENTE_A,
        "demanda_carga": 5,
        "ventana_horaria": {"inicio": 600, "fin": 700},
    }
    respuesta = client.post(URL, json=_pedido([cliente], tipo="VRPTW", deposito=deposito))
    assert respuesta.status_code == 400


def test_problema_resoluble_responde_200_y_vuelve_al_deposito(client, osrm_falso_api):
    respuesta = client.post(
        URL,
        json=_pedido(
            [
                {**CLIENTE_A, "demanda_carga": 10},
                {**CLIENTE_B, "demanda_carga": 5},
            ]
        ),
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["distancia_total_flota_metros"] > 0
    ruta = cuerpo["rutas"][0]
    assert ruta["ruta_secuencial"][0] == "Depósito"
    assert ruta["ruta_secuencial"][-1] == "Depósito"
    assert sorted(ruta["ruta_secuencial"][1:-1]) == ["A", "B"]
    assert ruta["carga_total"] == 15


def test_error_inesperado_responde_500_sin_exponer_el_detalle(client, osrm_falso_api, monkeypatch):
    def explotar(*_args, **_kwargs):
        raise RuntimeError("detalle-interno-secreto")

    monkeypatch.setattr("api.routes.resolver_ruteo", explotar)

    respuesta = client.post(URL, json=_pedido([{**CLIENTE_A, "demanda_carga": 5}]))
    assert respuesta.status_code == 500
    assert "detalle-interno-secreto" not in respuesta.text


def test_matriz_de_tamano_incorrecto_es_rechazada_con_400(client, monkeypatch):
    def matriz_de_2x2(_coordenadas):
        return {
            "matriz_distancias_metros": [[0, 1], [1, 0]],
            "matriz_tiempos_segundos": [[0, 1], [1, 0]],
        }

    monkeypatch.setattr("api.routes.obtener_matriz_osrm", matriz_de_2x2)

    # Deposito + 2 clientes = 3 nodos, pero la matriz es de 2x2.
    respuesta = client.post(
        URL,
        json=_pedido(
            [
                {**CLIENTE_A, "demanda_carga": 1},
                {**CLIENTE_B, "demanda_carga": 1},
            ]
        ),
    )
    assert respuesta.status_code == 400
    assert "matriz" in respuesta.json()["detail"].lower()


def test_ventana_horaria_invertida_es_rechazada_con_422(client, osrm_falso_api):
    cliente = {
        **CLIENTE_A,
        "demanda_carga": 5,
        "ventana_horaria": {"inicio": 700, "fin": 600},
    }
    respuesta = client.post(URL, json=_pedido([cliente]))
    assert respuesta.status_code == 422


def test_sin_clientes_responde_400(client):
    respuesta = client.post(URL, json=_pedido([]))
    assert respuesta.status_code == 400
