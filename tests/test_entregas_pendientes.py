from tests.conftest import (
    iniciar_ruta_con_paradas,
    registrar_chofer_independiente,
)

BASE_RUTAS = "/api/v1/rutas"
BASE_INCIDENCIAS = "/api/v1/incidencias"
BASE_PENDIENTES = "/api/v1/entregas-pendientes"


def _ruta_con_una_parada_fallida(client, reprogramar):
    """Ruta de 2 paradas: la primera falla (opcionalmente reprogramada) y la
    segunda se entrega. Devuelve las paradas originales por `orden`."""
    paradas = iniciar_ruta_con_paradas(client)
    respuesta = client.post(
        f"{BASE_RUTAS}/activa/paradas/{paradas[0]['id']}/fallar",
        json={"motivo": "cliente_ausente", "reprogramar": reprogramar},
    )
    assert respuesta.status_code == 200
    client.post(f"{BASE_RUTAS}/activa/paradas/{paradas[1]['id']}/completar")
    return paradas


def _incidencias(client, **params):
    return client.get(BASE_INCIDENCIAS, params=params).json()


def _ruta_nueva(client, cliente_ids, cargas=None):
    paradas = [
        {"cliente_id": cliente_id, "carga_kg": (cargas or {}).get(cliente_id, 5)}
        for cliente_id in cliente_ids
    ]
    return client.post(f"{BASE_RUTAS}/confirmar", json={"paradas": paradas})


def test_fallar_y_reprogramar_en_un_paso(client, osrm_falso):
    paradas = _ruta_con_una_parada_fallida(client, reprogramar=True)

    pendientes = client.get(BASE_PENDIENTES).json()
    assert len(pendientes) == 1
    assert pendientes[0]["cliente_id"] == paradas[0]["cliente_id"]
    assert pendientes[0]["cliente_nombre"] == paradas[0]["nombre_snapshot"]
    assert pendientes[0]["carga_kg"] == paradas[0]["demanda_carga_snapshot"]

    incidencia = _incidencias(client)[0]
    assert incidencia["estado"] == "resuelta"
    assert incidencia["resolucion"] == "reprogramada"
    assert incidencia["fecha_resolucion"] is not None
    assert incidencia["puede_reprogramarse"] is False


def test_fallar_sin_decidir_deja_la_incidencia_pendiente(client, osrm_falso):
    _ruta_con_una_parada_fallida(client, reprogramar=False)

    assert client.get(BASE_PENDIENTES).json() == []
    incidencia = _incidencias(client)[0]
    assert incidencia["estado"] == "pendiente"
    assert incidencia["resolucion"] is None
    assert incidencia["puede_reprogramarse"] is True


def test_una_incidencia_nueva_nace_pendiente(client, osrm_falso):
    iniciar_ruta_con_paradas(client)
    creada = client.post(BASE_INCIDENCIAS, json={"tipo": "problema_vehiculo"}).json()
    assert creada["estado"] == "pendiente"
    assert creada["puede_reprogramarse"] is False


def test_reprogramar_mas_tarde_desde_la_incidencia(client, osrm_falso):
    paradas = _ruta_con_una_parada_fallida(client, reprogramar=False)
    incidencia = _incidencias(client)[0]

    respuesta = client.post(
        f"{BASE_INCIDENCIAS}/{incidencia['id']}/resolver", json={"resolucion": "reprogramada"}
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "resuelta"
    assert respuesta.json()["resolucion"] == "reprogramada"

    pendientes = client.get(BASE_PENDIENTES).json()
    assert [p["cliente_id"] for p in pendientes] == [paradas[0]["cliente_id"]]


def test_no_se_puede_reprogramar_dos_veces(client, osrm_falso):
    _ruta_con_una_parada_fallida(client, reprogramar=True)
    incidencia = _incidencias(client)[0]

    respuesta = client.post(
        f"{BASE_INCIDENCIAS}/{incidencia['id']}/resolver", json={"resolucion": "reprogramada"}
    )
    assert respuesta.status_code == 409
    assert len(client.get(BASE_PENDIENTES).json()) == 1


def test_reprogramar_una_incidencia_general_da_409(client, osrm_falso):
    iniciar_ruta_con_paradas(client)
    general = client.post(BASE_INCIDENCIAS, json={"tipo": "problema_vehiculo"}).json()

    respuesta = client.post(
        f"{BASE_INCIDENCIAS}/{general['id']}/resolver", json={"resolucion": "reprogramada"}
    )
    assert respuesta.status_code == 409
    assert client.get(BASE_PENDIENTES).json() == []
    assert _incidencias(client, estado="pendiente")[0]["id"] == general["id"]


def test_cerrar_sin_accion_no_crea_entrega(client, osrm_falso):
    _ruta_con_una_parada_fallida(client, reprogramar=False)
    incidencia = _incidencias(client)[0]

    respuesta = client.post(
        f"{BASE_INCIDENCIAS}/{incidencia['id']}/resolver", json={"resolucion": "cerrada"}
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["resolucion"] == "cerrada"
    assert client.get(BASE_PENDIENTES).json() == []


def test_resolver_una_incidencia_ya_resuelta_da_409(client, osrm_falso):
    _ruta_con_una_parada_fallida(client, reprogramar=False)
    incidencia = _incidencias(client)[0]
    url = f"{BASE_INCIDENCIAS}/{incidencia['id']}/resolver"

    assert client.post(url, json={"resolucion": "cerrada"}).status_code == 200
    assert client.post(url, json={"resolucion": "cerrada"}).status_code == 409


def test_resolver_una_incidencia_ajena_da_404(client, osrm_falso):
    _ruta_con_una_parada_fallida(client, reprogramar=False)
    incidencia = _incidencias(client)[0]
    client.cookies.clear()

    registrar_chofer_independiente(client, email="ajeno-inc@test.com", patente="AJ111AJ")
    respuesta = client.post(
        f"{BASE_INCIDENCIAS}/{incidencia['id']}/resolver", json={"resolucion": "cerrada"}
    )
    assert respuesta.status_code == 404
    assert client.get(BASE_PENDIENTES).json() == []


def test_resolucion_invalida_da_422(client, osrm_falso):
    _ruta_con_una_parada_fallida(client, reprogramar=False)
    incidencia = _incidencias(client)[0]
    respuesta = client.post(
        f"{BASE_INCIDENCIAS}/{incidencia['id']}/resolver", json={"resolucion": "inventada"}
    )
    assert respuesta.status_code == 422


def test_filtrar_incidencias_por_estado(client, osrm_falso):
    paradas = iniciar_ruta_con_paradas(client)
    client.post(
        f"{BASE_RUTAS}/activa/paradas/{paradas[0]['id']}/fallar",
        json={"motivo": "cliente_ausente", "reprogramar": True},
    )
    client.post(
        f"{BASE_RUTAS}/activa/paradas/{paradas[1]['id']}/fallar",
        json={"motivo": "rechazo_entrega"},
    )

    assert len(_incidencias(client)) == 2
    pendientes = _incidencias(client, estado="pendiente")
    resueltas = _incidencias(client, estado="resuelta")
    assert [i["tipo"] for i in pendientes] == ["rechazo_entrega"]
    assert [i["tipo"] for i in resueltas] == ["cliente_ausente"]
    assert client.get(BASE_INCIDENCIAS, params={"estado": "otro"}).status_code == 422


def test_las_entregas_pendientes_son_solo_las_propias(client, osrm_falso):
    _ruta_con_una_parada_fallida(client, reprogramar=True)
    client.cookies.clear()

    registrar_chofer_independiente(client, email="otro-pend@test.com", patente="OP111OP")
    assert client.get(BASE_PENDIENTES).json() == []


def test_un_lugar_dado_de_baja_no_aparece_como_pendiente(client, osrm_falso):
    paradas = _ruta_con_una_parada_fallida(client, reprogramar=True)
    assert len(client.get(BASE_PENDIENTES).json()) == 1

    client.delete(f"/api/v1/clientes/{paradas[0]['cliente_id']}")
    assert client.get(BASE_PENDIENTES).json() == []


def test_confirmar_una_ruta_con_el_lugar_da_por_cumplida_la_entrega(client, osrm_falso):
    paradas = _ruta_con_una_parada_fallida(client, reprogramar=True)

    assert _ruta_nueva(client, [paradas[0]["cliente_id"]]).status_code == 201
    assert client.get(BASE_PENDIENTES).json() == []


def test_una_ruta_sin_el_lugar_deja_la_entrega_pendiente(client, osrm_falso):
    paradas = _ruta_con_una_parada_fallida(client, reprogramar=True)

    assert _ruta_nueva(client, [paradas[1]["cliente_id"]]).status_code == 201
    assert len(client.get(BASE_PENDIENTES).json()) == 1


def test_cancelar_la_ruta_devuelve_la_entrega_a_pendiente(client, osrm_falso):
    paradas = _ruta_con_una_parada_fallida(client, reprogramar=True)
    _ruta_nueva(client, [paradas[0]["cliente_id"]])
    assert client.get(BASE_PENDIENTES).json() == []

    assert client.delete(f"{BASE_RUTAS}/activa").status_code == 200
    assert [p["cliente_id"] for p in client.get(BASE_PENDIENTES).json()] == [
        paradas[0]["cliente_id"]
    ]


def test_editar_la_ruta_sin_el_lugar_devuelve_la_entrega_a_pendiente(client, osrm_falso):
    paradas = _ruta_con_una_parada_fallida(client, reprogramar=True)
    ambos = [paradas[0]["cliente_id"], paradas[1]["cliente_id"]]
    _ruta_nueva(client, ambos)
    assert client.get(BASE_PENDIENTES).json() == []

    solo_el_otro = [{"cliente_id": paradas[1]["cliente_id"], "carga_kg": 5}]
    assert client.put(f"{BASE_RUTAS}/activa", json={"paradas": solo_el_otro}).status_code == 200
    assert len(client.get(BASE_PENDIENTES).json()) == 1


def test_editar_la_ruta_conservando_el_lugar_mantiene_la_entrega_cumplida(client, osrm_falso):
    paradas = _ruta_con_una_parada_fallida(client, reprogramar=True)
    ambos = [paradas[0]["cliente_id"], paradas[1]["cliente_id"]]
    _ruta_nueva(client, ambos)

    con_ambos = [{"cliente_id": cliente_id, "carga_kg": 7} for cliente_id in ambos]
    assert client.put(f"{BASE_RUTAS}/activa", json={"paradas": con_ambos}).status_code == 200
    assert client.get(BASE_PENDIENTES).json() == []


def test_estos_endpoints_requieren_sesion(client):
    assert client.get(BASE_PENDIENTES).status_code == 401
    url = f"{BASE_INCIDENCIAS}/00000000-0000-0000-0000-000000000000/resolver"
    assert client.post(url, json={"resolucion": "cerrada"}).status_code == 401
