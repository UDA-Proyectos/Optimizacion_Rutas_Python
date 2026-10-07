import uuid

from db.modelos import Ruta, Usuario
from tests.conftest import (
    PAYLOAD_CLIENTE_1,
    PAYLOAD_CLIENTE_2,
    PAYLOAD_DEPOSITO,
    iniciar_sesion,
    registrar_admin,
    registrar_chofer_de_empresa,
    registrar_chofer_independiente,
)

RUTAS = "/api/v1/rutas"
EMPRESA = "/api/v1/empresa"


def _flota(client):
    """Admin con depósito y dos lugares, y un chofer de empresa (moto, 50 kg).
    Deja logueado al admin."""
    registrar_admin(client)
    client.post("/api/v1/depositos", json=PAYLOAD_DEPOSITO)
    lugares = [
        client.post("/api/v1/clientes", json=PAYLOAD_CLIENTE_1).json(),
        client.post("/api/v1/clientes", json=PAYLOAD_CLIENTE_2).json(),
    ]
    beto = registrar_chofer_de_empresa(
        client, "admin@flota.com", "beto@flota.com", "BB111BB", "Beto"
    )
    iniciar_sesion(client, "admin@flota.com")
    return beto, lugares


def _paradas(lugares, carga=5):
    return [{"cliente_id": lugar["id"], "carga_kg": carga} for lugar in lugares]


def _asignar(client, chofer_id, lugares, carga=5, **extra):
    return client.post(
        f"{RUTAS}/confirmar",
        json={"chofer_id": chofer_id, "paradas": _paradas(lugares, carga), **extra},
    )


# --- Asignación de rutas -----------------------------------------------------


def test_admin_asigna_una_ruta_a_un_chofer_de_su_empresa(client, osrm_falso, db_session):
    beto, lugares = _flota(client)
    admin = client.get("/api/v1/auth/me").json()

    preview = client.post(
        f"{RUTAS}/optimizar", json={"chofer_id": beto["id"], "paradas": _paradas(lugares[:1])}
    )
    assert preview.status_code == 200
    respuesta = _asignar(client, beto["id"], lugares, nombre="Zona centro")
    assert respuesta.status_code == 201
    ruta = respuesta.json()
    assert ruta["chofer_id"] == beto["id"]
    assert ruta["chofer_nombre"] == "Beto"
    assert ruta["capacidad_vehiculo_kg"] == 50
    creada = db_session.get(Ruta, uuid.UUID(ruta["id"]))
    assert str(creada.creado_por_usuario_id) == admin["id"]

    [resumen] = client.get(f"{EMPRESA}/choferes").json()
    assert resumen["rutas_del_dia"] == 1


def test_asignar_respeta_la_capacidad_del_chofer_elegido(client, osrm_falso):
    beto, lugares = _flota(client)
    respuesta = _asignar(client, beto["id"], lugares, carga=30)
    assert respuesta.status_code == 400
    assert "capacidad" in respuesta.json()["detail"].lower()


def test_reglas_de_a_quien_se_asigna(client, osrm_falso):
    beto, lugares = _flota(client)
    paradas = _paradas(lugares[:1])
    assert client.post(f"{RUTAS}/confirmar", json={"paradas": paradas}).status_code == 422

    registrar_admin(client, email="otra@flota.com", nombre_empresa="Otra")
    ajeno = registrar_chofer_de_empresa(client, "otra@flota.com", "ajeno@flota.com", "ZZ111ZZ")
    iniciar_sesion(client, "admin@flota.com")
    assert _asignar(client, ajeno["id"], lugares[:1]).status_code == 404

    iniciar_sesion(client, "beto@flota.com")
    assert client.post(f"{RUTAS}/optimizar", json={"paradas": paradas}).status_code == 403
    assert client.post(f"{RUTAS}/confirmar", json={"paradas": paradas}).status_code == 403

    client.cookies.clear()
    registrar_chofer_independiente(client, email="solo@test.com", patente="SO111LO")
    respuesta = client.post(
        f"{RUTAS}/optimizar", json={"chofer_id": beto["id"], "paradas": paradas}
    )
    assert respuesta.status_code == 422


def test_chofer_inactivo_no_recibe_rutas(client, osrm_falso, db_session):
    beto, lugares = _flota(client)
    db_session.get(Usuario, uuid.UUID(beto["id"])).activo = False
    db_session.commit()
    assert _asignar(client, beto["id"], lugares).status_code == 409


def test_admin_edita_y_cancela_rutas_de_su_flota(client, osrm_falso):
    beto, lugares = _flota(client)
    ruta = _asignar(client, beto["id"], lugares, nombre="Mañana").json()

    editada = client.put(f"{RUTAS}/{ruta['id']}", json={"paradas": _paradas(lugares[:1])})
    assert editada.status_code == 200
    assert editada.json()["chofer_id"] == beto["id"]
    assert editada.json()["nombre"] == "Mañana"
    assert len(editada.json()["paradas"]) == 1

    cambio_de_chofer = client.put(
        f"{RUTAS}/{editada.json()['id']}",
        json={"chofer_id": str(uuid.uuid4()), "paradas": _paradas(lugares[:1])},
    )
    assert cambio_de_chofer.status_code == 422

    assert client.delete(f"{RUTAS}/{editada.json()['id']}").status_code == 200


def test_admin_no_toca_rutas_de_otra_empresa(client, osrm_falso):
    beto, lugares = _flota(client)
    ruta = _asignar(client, beto["id"], lugares).json()

    registrar_admin(client, email="otra@flota.com", nombre_empresa="Otra")
    assert client.delete(f"{RUTAS}/{ruta['id']}").status_code == 404
    editar = client.put(f"{RUTAS}/{ruta['id']}", json={"paradas": _paradas(lugares[:1])})
    assert editar.status_code == 404
    assert client.get(f"{EMPRESA}/rutas/{ruta['id']}").status_code == 404


# --- Ejecución por el chofer de empresa --------------------------------------


def test_chofer_de_empresa_ejecuta_su_ruta_asignada(client, osrm_falso):
    beto, lugares = _flota(client)
    ruta = _asignar(client, beto["id"], lugares).json()

    iniciar_sesion(client, "beto@flota.com")
    assert [r["id"] for r in client.get(RUTAS).json()] == [ruta["id"]]
    editar = client.put(f"{RUTAS}/{ruta['id']}", json={"paradas": _paradas(lugares[:1])})
    assert editar.status_code == 403
    assert client.delete(f"{RUTAS}/{ruta['id']}").status_code == 403

    en_curso = client.post(f"{RUTAS}/{ruta['id']}/iniciar").json()
    primera, segunda = sorted(en_curso["paradas"], key=lambda p: p["orden"])
    assert client.post(f"{RUTAS}/activa/paradas/{primera['id']}/llegada").status_code == 200
    assert client.post(f"{RUTAS}/activa/paradas/{primera['id']}/completar").status_code == 200

    reprogramando = client.post(
        f"{RUTAS}/activa/paradas/{segunda['id']}/fallar",
        json={"motivo": "cliente_ausente", "reprogramar": True},
    )
    assert reprogramando.status_code == 403
    cerrada = client.post(
        f"{RUTAS}/activa/paradas/{segunda['id']}/fallar", json={"motivo": "cliente_ausente"}
    ).json()
    assert cerrada["estado"] == "completada"
    assert cerrada["resumen"]["paradas_completadas"] == 1

    hoy = cerrada["fecha"]
    [item] = client.get(f"{RUTAS}/historial", params={"desde": hoy, "hasta": hoy}).json()
    assert item["paradas_fallidas"] == 1
    assert client.get(f"{RUTAS}/historial/{ruta['id']}").status_code == 200


def test_chofer_de_empresa_no_ve_rutas_de_otros_choferes(client, osrm_falso):
    _, lugares = _flota(client)
    ana = registrar_chofer_de_empresa(client, "admin@flota.com", "ana@flota.com", "AA111AA", "Ana")
    iniciar_sesion(client, "admin@flota.com")
    de_ana = _asignar(client, ana["id"], lugares).json()

    iniciar_sesion(client, "beto@flota.com")
    assert client.get(RUTAS).json() == []
    assert client.get(f"{RUTAS}/historial/{de_ana['id']}").status_code == 404


# --- Incidencias y entregas reprogramadas de la empresa ----------------------


def _beto_falla_una_parada(client, beto, lugares):
    """Beto ejecuta una ruta de una parada y no la puede entregar. Deja logueado a Beto."""
    ruta = _asignar(client, beto["id"], lugares[:1]).json()
    iniciar_sesion(client, "beto@flota.com")
    [parada] = client.post(f"{RUTAS}/{ruta['id']}/iniciar").json()["paradas"]
    fallo = client.post(
        f"{RUTAS}/activa/paradas/{parada['id']}/fallar", json={"motivo": "rechazo_entrega"}
    )
    assert fallo.status_code == 200, fallo.text
    return ruta


def test_admin_resuelve_y_la_entrega_queda_para_la_empresa(client, osrm_falso):
    beto, lugares = _flota(client)
    _beto_falla_una_parada(client, beto, lugares)
    [propia] = client.get("/api/v1/incidencias").json()
    assert propia["chofer_nombre"] == "Beto"
    resolver = f"/api/v1/incidencias/{propia['id']}/resolver"
    assert client.post(resolver, json={"resolucion": "cerrada"}).status_code == 403
    assert client.get("/api/v1/entregas-pendientes").status_code == 403

    ana = registrar_chofer_de_empresa(client, "admin@flota.com", "ana@flota.com", "AA111AA", "Ana")
    iniciar_sesion(client, "admin@flota.com")
    [incidencia] = client.get("/api/v1/incidencias", params={"estado": "pendiente"}).json()
    assert incidencia["puede_reprogramarse"] is True
    assert client.post(resolver, json={"resolucion": "reprogramada"}).status_code == 200
    [entrega] = client.get("/api/v1/entregas-pendientes").json()
    assert entrega["cliente_id"] == lugares[0]["id"]

    # La entrega la termina haciendo otra chofer de la flota.
    assert _asignar(client, ana["id"], lugares[:1]).status_code == 201
    assert client.get("/api/v1/entregas-pendientes").json() == []


def test_chofer_de_empresa_reporta_incidencias(client, osrm_falso):
    beto, lugares = _flota(client)
    ruta = _asignar(client, beto["id"], lugares).json()
    iniciar_sesion(client, "beto@flota.com")
    client.post(f"{RUTAS}/{ruta['id']}/iniciar")
    respuesta = client.post(
        "/api/v1/incidencias", json={"tipo": "otro", "descripcion": "Pinchadura"}
    )
    assert respuesta.status_code == 201

    iniciar_sesion(client, "admin@flota.com")
    assert [i["descripcion"] for i in client.get("/api/v1/incidencias").json()] == ["Pinchadura"]


def test_incidencias_de_otra_empresa_no_se_ven_ni_se_resuelven(client, osrm_falso):
    beto, lugares = _flota(client)
    _beto_falla_una_parada(client, beto, lugares)
    [incidencia] = client.get("/api/v1/incidencias").json()

    registrar_admin(client, email="otra@flota.com", nombre_empresa="Otra")
    assert client.get("/api/v1/incidencias").json() == []
    respuesta = client.post(
        f"/api/v1/incidencias/{incidencia['id']}/resolver", json={"resolucion": "cerrada"}
    )
    assert respuesta.status_code == 404


# --- Seguimiento de la flota -------------------------------------------------


def test_avance_del_dia_de_la_flota(client, osrm_falso):
    beto, lugares = _flota(client)
    ruta = _asignar(client, beto["id"], lugares).json()
    iniciar_sesion(client, "beto@flota.com")
    en_curso = client.post(f"{RUTAS}/{ruta['id']}/iniciar").json()
    primera = min(en_curso["paradas"], key=lambda p: p["orden"])
    client.post(f"{RUTAS}/activa/paradas/{primera['id']}/completar")

    iniciar_sesion(client, "admin@flota.com")
    [del_dia] = client.get(f"{EMPRESA}/rutas", params={"fecha": ruta["fecha"]}).json()
    assert del_dia["chofer_nombre"] == "Beto"
    assert del_dia["estado"] == "en_curso"
    assert sorted(p["estado"] for p in del_dia["paradas"]) == ["completada", "en_curso"]
    assert [c["tiene_ruta_en_curso"] for c in client.get(f"{EMPRESA}/choferes").json()] == [True]
    assert client.get(f"{EMPRESA}/rutas/{ruta['id']}").json()["id"] == ruta["id"]


def test_traza_de_una_ruta_de_la_flota(client, osrm_falso, osrm_geometria_falsa):
    beto, lugares = _flota(client)
    ruta = _asignar(client, beto["id"], lugares).json()
    respuesta = client.get(f"{EMPRESA}/rutas/{ruta['id']}/geometria")
    assert respuesta.status_code == 200
    assert len(respuesta.json()["tramos"]) == 3


def test_historial_de_la_flota_filtrado_por_chofer(client, osrm_falso):
    beto, lugares = _flota(client)
    ana = registrar_chofer_de_empresa(client, "admin@flota.com", "ana@flota.com", "AA111AA", "Ana")
    iniciar_sesion(client, "admin@flota.com")
    hoy = _asignar(client, beto["id"], lugares).json()["fecha"]
    _asignar(client, ana["id"], lugares[:1])

    rango = {"desde": hoy, "hasta": hoy}
    todas = client.get(f"{EMPRESA}/historial", params=rango).json()
    assert sorted(r["chofer_nombre"] for r in todas) == ["Ana", "Beto"]
    solo_ana = client.get(f"{EMPRESA}/historial", params={**rango, "chofer_id": ana["id"]}).json()
    assert [r["chofer_nombre"] for r in solo_ana] == ["Ana"]

    iniciar_sesion(client, "beto@flota.com")
    assert client.get(f"{EMPRESA}/historial", params=rango).status_code == 403
