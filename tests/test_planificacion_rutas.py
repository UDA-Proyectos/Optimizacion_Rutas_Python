from datetime import UTC, datetime, timedelta

from tests.conftest import armar_chofer_con_lugares, registrar_chofer_independiente

BASE = "/api/v1/rutas"


def _hoy():
    return datetime.now(UTC).date()


def _dia(dias):
    return (_hoy() + timedelta(days=dias)).isoformat()


def _confirmar(client, cliente, **extra):
    return client.post(
        f"{BASE}/confirmar",
        json={"paradas": [{"cliente_id": cliente["id"], "carga_kg": 5}], **extra},
    )


def _ids(client, **params):
    return [r["id"] for r in client.get(BASE, params=params).json()]


def test_planificar_para_mañana_queda_en_esa_fecha(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)

    respuesta = _confirmar(client, cliente, fecha=_dia(1))
    assert respuesta.status_code == 201
    assert respuesta.json()["fecha"] == _dia(1)
    assert respuesta.json()["estado"] == "planificada"

    assert _ids(client, fecha=_dia(1)) == [respuesta.json()["id"]]
    assert _ids(client) == []  # hoy no tiene nada


def test_sin_fecha_se_planifica_para_hoy(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)
    respuesta = _confirmar(client, cliente)
    assert respuesta.json()["fecha"] == _dia(0)


def test_una_fecha_pasada_o_muy_lejana_da_400(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)

    assert _confirmar(client, cliente, fecha=_dia(-3)).status_code == 400
    assert _confirmar(client, cliente, fecha=_dia(61)).status_code == 400
    assert _confirmar(client, cliente, fecha=_dia(60)).status_code == 201
    assert client.get(BASE, params={"fecha": _dia(-3)}).json() == []


def test_se_tolera_un_dia_atras_por_el_huso_horario(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)
    # De noche en Argentina el "hoy" del chofer ya es el "ayer" del servidor (UTC).
    assert _confirmar(client, cliente, fecha=_dia(-1)).status_code == 201


def test_el_nombre_se_guarda_se_limpia_y_tiene_un_maximo(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)

    assert _confirmar(client, cliente, nombre="  Mañana  ").json()["nombre"] == "Mañana"
    assert _confirmar(client, cliente, nombre="   ").json()["nombre"] is None
    assert _confirmar(client, cliente).json()["nombre"] is None
    assert _confirmar(client, cliente, nombre="x" * 61).status_code == 422


def test_rutas_del_dia_en_orden_de_creacion_y_sin_canceladas(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)
    primera = _confirmar(client, cliente, nombre="Mañana").json()
    segunda = _confirmar(client, cliente, nombre="Tarde").json()
    tercera = _confirmar(client, cliente, nombre="Sobrante").json()
    client.delete(f"{BASE}/{tercera['id']}")

    del_dia = client.get(BASE).json()
    assert [r["id"] for r in del_dia] == [primera["id"], segunda["id"]]
    assert [r["nombre"] for r in del_dia] == ["Mañana", "Tarde"]
    assert client.get(BASE, params={"fecha": _dia(5)}).json() == []


def test_se_elige_cual_iniciar_y_la_otra_sigue_planificada(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)
    primera = _confirmar(client, cliente, nombre="Mañana").json()
    segunda = _confirmar(client, cliente, nombre="Tarde").json()

    iniciada = client.post(f"{BASE}/{segunda['id']}/iniciar")
    assert iniciada.status_code == 200
    assert iniciada.json()["estado"] == "en_curso"
    assert iniciada.json()["paradas"][0]["estado"] == "en_curso"

    estados = {r["id"]: r["estado"] for r in client.get(BASE).json()}
    assert estados == {primera["id"]: "planificada", segunda["id"]: "en_curso"}
    assert client.get(f"{BASE}/activa").json()["id"] == segunda["id"]


def test_no_se_puede_iniciar_una_ruta_ajena(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)
    ruta = _confirmar(client, cliente).json()
    client.cookies.clear()

    registrar_chofer_independiente(client, email="otro-plan@test.com", patente="OT111OT")
    assert client.post(f"{BASE}/{ruta['id']}/iniciar").status_code == 404
    assert client.put(f"{BASE}/{ruta['id']}", json={"paradas": []}).status_code in (404, 422)
    assert client.delete(f"{BASE}/{ruta['id']}").status_code == 404


def test_una_sola_ruta_en_curso_a_la_vez(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)
    primera = _confirmar(client, cliente).json()
    segunda = _confirmar(client, cliente).json()

    assert client.post(f"{BASE}/{primera['id']}/iniciar").status_code == 200
    respuesta = client.post(f"{BASE}/{segunda['id']}/iniciar")
    assert respuesta.status_code == 409
    assert "en curso" in respuesta.json()["detail"]

    estados = {r["id"]: r["estado"] for r in client.get(BASE).json()}
    assert estados[segunda["id"]] == "planificada"


def test_despues_de_terminar_la_primera_se_puede_iniciar_la_segunda(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)
    primera = _confirmar(client, cliente).json()
    segunda = _confirmar(client, cliente).json()

    en_curso = client.post(f"{BASE}/{primera['id']}/iniciar").json()
    client.post(f"{BASE}/activa/paradas/{en_curso['paradas'][0]['id']}/completar")
    assert client.get(f"{BASE}/activa").json() is None

    assert client.post(f"{BASE}/{segunda['id']}/iniciar").status_code == 200


def test_la_ruta_activa_es_nula_sin_ruta_en_curso(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)
    _confirmar(client, cliente)  # planificada, sin iniciar
    assert client.get(f"{BASE}/activa").json() is None


def test_una_ruta_de_mañana_no_se_inicia_hoy(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)
    ruta = _confirmar(client, cliente, fecha=_dia(2)).json()

    respuesta = client.post(f"{BASE}/{ruta['id']}/iniciar")
    assert respuesta.status_code == 409
    assert _dia(2) in respuesta.json()["detail"]
    assert client.get(f"{BASE}/activa").json() is None


def test_iniciar_usa_el_dia_local_que_manda_el_cliente(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)
    ruta = _confirmar(client, cliente, fecha=_dia(1)).json()

    # Para el chofer ya es "mañana" (otro huso): la ruta de ese día se puede iniciar.
    assert (
        client.post(f"{BASE}/{ruta['id']}/iniciar", json={"fecha_hoy": _dia(1)}).status_code == 200
    )


def test_un_dia_local_absurdo_da_400(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)
    ruta = _confirmar(client, cliente).json()
    respuesta = client.post(f"{BASE}/{ruta['id']}/iniciar", json={"fecha_hoy": _dia(10)})
    assert respuesta.status_code == 400


def test_editar_una_de_dos_no_toca_la_otra(client, osrm_falso):
    cliente, otro = armar_chofer_con_lugares(client)
    primera = _confirmar(client, cliente, nombre="Mañana").json()
    segunda = _confirmar(client, cliente, nombre="Tarde").json()

    editada = client.put(
        f"{BASE}/{primera['id']}",
        json={"paradas": [{"cliente_id": otro["id"], "carga_kg": 7}]},
    )
    assert editada.status_code == 200
    assert editada.json()["id"] != primera["id"]
    # Conserva fecha y nombre al no indicarse otros.
    assert editada.json()["fecha"] == _dia(0)
    assert editada.json()["nombre"] == "Mañana"

    del_dia = client.get(BASE).json()
    assert {r["id"] for r in del_dia} == {editada.json()["id"], segunda["id"]}
    assert (
        next(r for r in del_dia if r["id"] == segunda["id"])["paradas"][0]["cliente_id"]
        == (cliente["id"])
    )


def test_editar_puede_cambiar_fecha_y_nombre(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)
    ruta = _confirmar(client, cliente, nombre="Mañana").json()

    editada = client.put(
        f"{BASE}/{ruta['id']}",
        json={
            "paradas": [{"cliente_id": cliente["id"], "carga_kg": 5}],
            "fecha": _dia(3),
            "nombre": "Jueves",
        },
    ).json()
    assert editada["fecha"] == _dia(3)
    assert editada["nombre"] == "Jueves"
    assert _ids(client) == []
    assert _ids(client, fecha=_dia(3)) == [editada["id"]]


def test_no_se_edita_una_ruta_en_curso_ni_se_cancela_una_terminada(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)
    ruta = _confirmar(client, cliente).json()
    en_curso = client.post(f"{BASE}/{ruta['id']}/iniciar").json()

    cuerpo = {"paradas": [{"cliente_id": cliente["id"], "carga_kg": 5}]}
    assert client.put(f"{BASE}/{ruta['id']}", json=cuerpo).status_code == 409

    client.post(f"{BASE}/activa/paradas/{en_curso['paradas'][0]['id']}/completar")
    assert client.delete(f"{BASE}/{ruta['id']}").status_code == 409


def test_se_puede_cancelar_una_ruta_en_curso(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)
    ruta = _confirmar(client, cliente).json()
    client.post(f"{BASE}/{ruta['id']}/iniciar")

    assert client.delete(f"{BASE}/{ruta['id']}").status_code == 200
    assert client.get(f"{BASE}/activa").json() is None


def test_las_acciones_de_parada_sin_ruta_en_curso_dan_409(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)
    ruta = _confirmar(client, cliente).json()  # planificada, sin iniciar

    respuesta = client.post(f"{BASE}/activa/paradas/{ruta['paradas'][0]['id']}/completar")
    assert respuesta.status_code == 409


def test_una_ruta_planificada_para_otro_dia_bloquea_editar_la_capacidad(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)
    assert (
        client.patch("/api/v1/auth/me/vehiculo", json={"capacidad_carga_kg": 300}).status_code
        == 200
    )

    ruta = _confirmar(client, cliente, fecha=_dia(4)).json()
    assert (
        client.patch("/api/v1/auth/me/vehiculo", json={"capacidad_carga_kg": 400}).status_code
        == 409
    )

    client.delete(f"{BASE}/{ruta['id']}")
    assert (
        client.patch("/api/v1/auth/me/vehiculo", json={"capacidad_carga_kg": 400}).status_code
        == 200
    )


def test_las_rutas_de_otro_chofer_no_aparecen_en_la_lista(client, osrm_falso):
    cliente, _ = armar_chofer_con_lugares(client)
    _confirmar(client, cliente)
    client.cookies.clear()

    registrar_chofer_independiente(client, email="vacio-plan@test.com", patente="VP111VP")
    assert client.get(BASE).json() == []


def test_el_listado_requiere_sesion(client):
    assert client.get(BASE).status_code == 401
