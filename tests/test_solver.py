import pytest

from routing.solver import resolver_ruteo

# Depósito (0) y tres clientes sobre una recta, a 1000 m entre nodos vecinos:
# el mejor recorrido es 0 -> 1 -> 2 -> 3 -> 0 (6000 m) o su inverso.
DISTANCIAS = [[abs(i - j) * 1000.0 for j in range(4)] for i in range(4)]
# 60 s por cada 1000 m => 1 min entre nodos vecinos.
TIEMPOS = [[abs(i - j) * 60.0 for j in range(4)] for i in range(4)]


@pytest.fixture(autouse=True)
def solver_rapido(monkeypatch):
    # Los casos infactibles agotan el time_limit completo; con 1 s alcanza para
    # estas instancias de 4 nodos.
    monkeypatch.setattr("routing.solver.settings.solver_time_limit_segundos", 1)


def _nodos(ruta):
    return [parada["nodo_id"] for parada in ruta["ruta_secuencial_nodos"]]


def test_cvrp_resoluble_visita_a_todos_y_vuelve_al_deposito():
    resultado = resolver_ruteo(DISTANCIAS, [0, 5, 5, 5], [50])

    assert resultado["estado"] == "Exito"
    ruta = resultado["rutas"][0]
    nodos = _nodos(ruta)
    assert nodos[0] == 0 and nodos[-1] == 0
    assert sorted(nodos[1:-1]) == [1, 2, 3]
    assert ruta["carga_total"] == 15
    # Recorrido en línea recta ida y vuelta: 6000 m es el óptimo.
    assert ruta["distancia_recorrida_metros"] == 6000
    assert resultado["distancia_total_flota"] == 6000


def test_cvrp_con_dos_vehiculos_reparte_la_carga_sin_pasarse_de_la_capacidad():
    resultado = resolver_ruteo(DISTANCIAS, [0, 10, 10, 10], [20, 20])

    assert resultado["estado"] == "Exito"
    visitados = []
    for ruta in resultado["rutas"]:
        assert ruta["carga_total"] <= 20
        visitados += _nodos(ruta)[1:-1]
    assert sorted(visitados) == [1, 2, 3]


def test_cvrp_con_demanda_mayor_a_la_capacidad_devuelve_fallo():
    resultado = resolver_ruteo(DISTANCIAS, [0, 30, 30, 30], [50])

    assert resultado["estado"] == "Fallo"
    assert "solución factible" in resultado["mensaje"]


def test_los_costos_fraccionarios_de_osrm_no_rompen_el_solver():
    # OSRM devuelve floats (ej. 4538.5 m): el solver los trunca a int.
    distancias = [[abs(i - j) * 1000.5 for j in range(4)] for i in range(4)]
    resultado = resolver_ruteo(distancias, [0, 5, 5, 5], [50])
    assert resultado["estado"] == "Exito"


def test_vrptw_resoluble_devuelve_el_minuto_de_llegada_en_orden_creciente():
    ventanas = [(0, 1440)] + [(480, 900)] * 3
    resultado = resolver_ruteo(
        DISTANCIAS,
        [0, 5, 5, 5],
        [50],
        matriz_tiempos=TIEMPOS,
        tiempos_servicio=[0, 10, 10, 10],
        ventanas_horarias=ventanas,
        tipo_problema="VRPTW",
    )

    assert resultado["estado"] == "Exito"
    llegadas = [p["minuto_llegada"] for p in resultado["rutas"][0]["ruta_secuencial_nodos"]]
    assert llegadas == sorted(llegadas)
    # Ningún cliente se atiende antes de que abra su ventana.
    assert all(minuto >= 480 for minuto in llegadas[1:-1])
    # Entre dos paradas consecutivas pasa al menos el servicio de la primera (10 min).
    assert llegadas[2] - llegadas[1] >= 10


def test_vrptw_con_ventanas_imposibles_devuelve_fallo():
    # Llegar al cliente 1 toma 1 min pero su ventana cierra en el minuto 0, y el
    # depósito ya solo permite salir de 480 en adelante.
    ventanas = [(480, 1440), (0, 5), (480, 900), (480, 900)]
    resultado = resolver_ruteo(
        DISTANCIAS,
        [0, 5, 5, 5],
        [50],
        matriz_tiempos=TIEMPOS,
        tiempos_servicio=[0, 0, 0, 0],
        ventanas_horarias=ventanas,
        tipo_problema="VRPTW",
    )
    assert resultado["estado"] == "Fallo"


@pytest.mark.parametrize(
    "distancias, demandas",
    [
        ([], []),
        ([[0, 1], [1, 0], [2, 2]], [0, 1, 1]),  # no cuadrada
        ([[0, 1, 1], [1, 0]], [0, 1]),  # filas de distinto largo
        (DISTANCIAS, [0, 5, 5]),  # demandas de menos
    ],
)
def test_entradas_inconsistentes_levantan_value_error(distancias, demandas):
    with pytest.raises(ValueError):
        resolver_ruteo(distancias, demandas, [50])


def test_vrptw_sin_matriz_de_tiempos_levanta_value_error():
    with pytest.raises(ValueError, match="tiempos"):
        resolver_ruteo(
            DISTANCIAS,
            [0, 5, 5, 5],
            [50],
            matriz_tiempos=None,
            tiempos_servicio=[0] * 4,
            ventanas_horarias=[(0, 1440)] * 4,
            tipo_problema="VRPTW",
        )


def test_sin_vehiculos_levanta_value_error():
    with pytest.raises(ValueError, match="vehículo"):
        resolver_ruteo(DISTANCIAS, [0, 5, 5, 5], [])
