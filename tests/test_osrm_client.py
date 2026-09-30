import pytest
import requests

from services import osrm_client
from services.osrm_client import (
    _formatear_coordenadas,
    obtener_geometria_osrm,
    obtener_matriz_osrm,
)

BASE_URL = "http://osrm.test"

# Depósito y un cliente, en el formato {latitud, longitud} que usa el resto del código.
COORDENADAS = [
    {"latitud": -32.8908, "longitud": -68.8272},
    {"latitud": -32.8850, "longitud": -68.8200},
]


class RespuestaFalsa:
    def __init__(self, cuerpo, status=200):
        self._cuerpo = cuerpo
        self._status = status

    def raise_for_status(self):
        if self._status >= 400:
            raise requests.exceptions.HTTPError(f"HTTP {self._status}")

    def json(self):
        return self._cuerpo


@pytest.fixture
def pedidos(monkeypatch):
    """Reemplaza `requests.get` del cliente y deja registradas las URLs pedidas."""
    monkeypatch.setattr(osrm_client.settings, "osrm_base_url", BASE_URL)
    registro = {"urls": [], "respuesta": None}

    def get_falso(url, timeout):
        registro["urls"].append(url)
        respuesta = registro["respuesta"]
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta

    monkeypatch.setattr(osrm_client.requests, "get", get_falso)
    return registro


def test_las_coordenadas_van_como_longitud_coma_latitud():
    # OSRM espera "lon,lat", al revés que la convención lat,lon de los schemas.
    assert _formatear_coordenadas(COORDENADAS) == "-68.8272,-32.8908;-68.82,-32.885"


def test_la_matriz_se_pide_a_table_con_distancia_y_duracion(pedidos):
    pedidos["respuesta"] = RespuestaFalsa(
        {"code": "Ok", "distances": [[0, 500.5], [510.5, 0]], "durations": [[0, 60.2], [61.7, 0]]}
    )

    obtener_matriz_osrm(COORDENADAS)

    assert pedidos["urls"] == [
        f"{BASE_URL}/table/v1/driving/-68.8272,-32.8908;-68.82,-32.885?annotations=distance,duration"
    ]


def test_la_matriz_devuelve_metros_y_segundos_sin_transformar(pedidos):
    pedidos["respuesta"] = RespuestaFalsa(
        {"code": "Ok", "distances": [[0, 500.5], [510.5, 0]], "durations": [[0, 60.2], [61.7, 0]]}
    )

    matrices = obtener_matriz_osrm(COORDENADAS)

    assert matrices == {
        "matriz_distancias_metros": [[0, 500.5], [510.5, 0]],
        "matriz_tiempos_segundos": [[0, 60.2], [61.7, 0]],
    }


def test_un_error_http_se_envuelve_como_falla_de_conexion(pedidos):
    pedidos["respuesta"] = RespuestaFalsa({}, status=429)

    with pytest.raises(Exception, match="Falla de conexión con la capa de tránsito"):
        obtener_matriz_osrm(COORDENADAS)


def test_un_error_de_red_se_envuelve_como_falla_de_conexion(pedidos):
    pedidos["respuesta"] = requests.exceptions.ConnectionError("sin ruta al host")

    with pytest.raises(Exception, match="Falla de conexión con la capa de tránsito"):
        obtener_matriz_osrm(COORDENADAS)


def test_un_code_distinto_de_ok_levanta_value_error_con_el_mensaje_de_osrm(pedidos):
    pedidos["respuesta"] = RespuestaFalsa({"code": "NoSegment", "message": "Coordenada sin calle"})

    with pytest.raises(ValueError, match="Coordenada sin calle"):
        obtener_matriz_osrm(COORDENADAS)


def test_la_geometria_se_pide_a_route_y_devuelve_lat_lon_por_tramo(pedidos):
    # OSRM devuelve GeoJSON: [lon, lat]. El cliente lo invierte a (lat, lon) para Leaflet.
    pedidos["respuesta"] = RespuestaFalsa(
        {
            "code": "Ok",
            "routes": [
                {
                    "legs": [
                        {
                            "steps": [
                                {
                                    "geometry": {
                                        "coordinates": [[-68.8272, -32.8908], [-68.826, -32.89]]
                                    }
                                },
                                {"geometry": {"coordinates": [[-68.82, -32.885]]}},
                            ]
                        }
                    ]
                }
            ],
        }
    )

    tramos = obtener_geometria_osrm(COORDENADAS)

    assert tramos == [[(-32.8908, -68.8272), (-32.89, -68.826), (-32.885, -68.82)]]
    assert pedidos["urls"] == [
        (
            f"{BASE_URL}/route/v1/driving/-68.8272,-32.8908;-68.82,-32.885"
            "?overview=full&geometries=geojson&steps=true"
        )
    ]
