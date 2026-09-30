from datetime import UTC, datetime

from sqlalchemy import select

from db.modelos import Incidencia, Ruta, TipoIncidencia
from tests.conftest import (
    PAYLOAD_CLIENTE_1,
    PAYLOAD_CLIENTE_2,
    PAYLOAD_DEPOSITO,
    armar_chofer_con_lugares,
    iniciar_ruta_con_paradas,
    registrar_chofer_independiente,
)

BASE_RUTAS = "/api/v1/rutas"
BASE_DEPOSITOS = "/api/v1/depositos"
BASE_CLIENTES = "/api/v1/clientes"


def test_optimizar_devuelve_preview_sin_persistir(client, osrm_falso):
    cliente1, cliente2 = armar_chofer_con_lugares(client)

    respuesta = client.post(
        f"{BASE_RUTAS}/optimizar",
        json={
            "paradas": [
                {"cliente_id": cliente1["id"], "carga_kg": 10},
                {"cliente_id": cliente2["id"], "carga_kg": 5},
            ]
        },
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo["paradas"]) == 2
    assert cuerpo["distancia_total_m"] > 0
    assert cuerpo["carga_total_kg"] == 15

    assert client.get(f"{BASE_RUTAS}/activa").json() is None


def test_confirmar_persiste_la_ruta(client, osrm_falso):
    cliente1, cliente2 = armar_chofer_con_lugares(client)
    paradas = {
        "paradas": [
            {"cliente_id": cliente1["id"], "carga_kg": 10},
            {"cliente_id": cliente2["id"], "carga_kg": 5},
        ]
    }

    respuesta = client.post(f"{BASE_RUTAS}/confirmar", json=paradas)
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "planificada"
    assert len(cuerpo["paradas"]) == 2
    assert "capacidad" in cuerpo["explicacion"].lower()

    activa = client.get(f"{BASE_RUTAS}/activa")
    assert activa.status_code == 200
    assert activa.json()["id"] == cuerpo["id"]
    # La explicación del preview se persiste, no solo se muestra una vez.
    assert activa.json()["explicacion"] == cuerpo["explicacion"]


def test_no_se_puede_confirmar_dos_rutas_el_mismo_dia(client, osrm_falso):
    cliente1, _ = armar_chofer_con_lugares(client)
    paradas = {"paradas": [{"cliente_id": cliente1["id"], "carga_kg": 10}]}

    assert client.post(f"{BASE_RUTAS}/confirmar", json=paradas).status_code == 201
    respuesta = client.post(f"{BASE_RUTAS}/confirmar", json=paradas)
    assert respuesta.status_code == 409


def test_optimizar_sin_deposito_da_400(client, osrm_falso):
    registrar_chofer_independiente(client)
    cliente = client.post(BASE_CLIENTES, json=PAYLOAD_CLIENTE_1).json()

    respuesta = client.post(
        f"{BASE_RUTAS}/optimizar",
        json={"paradas": [{"cliente_id": cliente["id"], "carga_kg": 10}]},
    )
    assert respuesta.status_code == 400


def test_optimizar_con_cliente_ajeno_da_400(client, osrm_falso):
    registrar_chofer_independiente(client, email="dueno@test.com", patente="AA111AA")
    client.post(BASE_DEPOSITOS, json=PAYLOAD_DEPOSITO)
    cliente_ajeno = client.post(BASE_CLIENTES, json=PAYLOAD_CLIENTE_1).json()
    client.cookies.clear()

    registrar_chofer_independiente(client, email="otro@test.com", patente="BB222BB")
    client.post(BASE_DEPOSITOS, json=PAYLOAD_DEPOSITO)
    respuesta = client.post(
        f"{BASE_RUTAS}/optimizar",
        json={"paradas": [{"cliente_id": cliente_ajeno["id"], "carga_kg": 10}]},
    )
    assert respuesta.status_code == 400


def test_chofer_de_empresa_no_puede_optimizar(client):
    respuesta_empresa = client.post(
        "/api/v1/auth/registro/empresa",
        json={
            "nombre_empresa": "Distribuidora Ruta",
            "email": "admin-ruta@test.com",
            "contrasena": "contrasenaSegura123",
            "confirmar_contrasena": "contrasenaSegura123",
            "nombre_completo": "Ana Admin",
        },
    )
    assert respuesta_empresa.status_code == 201

    respuesta = client.post(
        f"{BASE_RUTAS}/optimizar",
        json={
            "paradas": [
                {"cliente_id": "00000000-0000-0000-0000-000000000000", "carga_kg": 1},
            ]
        },
    )
    assert respuesta.status_code == 403


def test_ruta_activa_sin_ruta_devuelve_null(client):
    registrar_chofer_independiente(client)
    respuesta = client.get(f"{BASE_RUTAS}/activa")
    assert respuesta.status_code == 200
    assert respuesta.json() is None


def test_optimizar_incluye_ahorro_y_explicacion(client, osrm_falso):
    cliente1, cliente2 = armar_chofer_con_lugares(client)
    respuesta = client.post(
        f"{BASE_RUTAS}/optimizar",
        json={
            "paradas": [
                {"cliente_id": cliente1["id"], "carga_kg": 10},
                {"cliente_id": cliente2["id"], "carga_kg": 5},
            ]
        },
    )
    cuerpo = respuesta.json()
    # El óptimo nunca puede ser peor que el orden pedido — es la garantía
    # que hace honesto mostrar el ahorro.
    assert cuerpo["ahorro_m"] >= 0
    assert cuerpo["distancia_sin_optimizar_m"] >= cuerpo["distancia_total_m"]
    assert "capacidad" in cuerpo["explicacion"].lower()


def test_editar_ruta_reemplaza_la_planificada(client, osrm_falso):
    cliente1, cliente2 = armar_chofer_con_lugares(client)
    original = client.post(
        f"{BASE_RUTAS}/confirmar",
        json={"paradas": [{"cliente_id": cliente1["id"], "carga_kg": 10}]},
    ).json()

    editada = client.put(
        f"{BASE_RUTAS}/activa",
        json={
            "paradas": [
                {"cliente_id": cliente1["id"], "carga_kg": 10},
                {"cliente_id": cliente2["id"], "carga_kg": 5},
            ]
        },
    )
    assert editada.status_code == 200
    cuerpo = editada.json()
    assert cuerpo["id"] != original["id"]
    assert len(cuerpo["paradas"]) == 2

    activa = client.get(f"{BASE_RUTAS}/activa").json()
    assert activa["id"] == cuerpo["id"]


def test_editar_sin_ruta_da_404(client):
    registrar_chofer_independiente(client)
    respuesta = client.put(
        f"{BASE_RUTAS}/activa",
        json={"paradas": [{"cliente_id": "00000000-0000-0000-0000-000000000000", "carga_kg": 1}]},
    )
    assert respuesta.status_code == 404


def test_eliminar_ruta_activa(client, osrm_falso):
    cliente1, _ = armar_chofer_con_lugares(client)
    client.post(
        f"{BASE_RUTAS}/confirmar",
        json={"paradas": [{"cliente_id": cliente1["id"], "carga_kg": 10}]},
    )

    respuesta = client.delete(f"{BASE_RUTAS}/activa")
    assert respuesta.status_code == 200
    assert client.get(f"{BASE_RUTAS}/activa").json() is None


def test_iniciar_sin_ruta_da_404(client):
    registrar_chofer_independiente(client)
    assert client.post(f"{BASE_RUTAS}/activa/iniciar").status_code == 404


def test_iniciar_y_completar_paradas_cierra_la_ruta(client, osrm_falso):
    cliente1, cliente2 = armar_chofer_con_lugares(client)
    client.post(
        f"{BASE_RUTAS}/confirmar",
        json={
            "paradas": [
                {"cliente_id": cliente1["id"], "carga_kg": 10},
                {"cliente_id": cliente2["id"], "carga_kg": 5},
            ]
        },
    )

    iniciada = client.post(f"{BASE_RUTAS}/activa/iniciar")
    assert iniciada.status_code == 200
    cuerpo = iniciada.json()
    assert cuerpo["estado"] == "en_curso"
    paradas_ordenadas = sorted(cuerpo["paradas"], key=lambda p: p["orden"])
    assert paradas_ordenadas[0]["estado"] == "en_curso"
    assert paradas_ordenadas[1]["estado"] == "pendiente"

    primera_id = paradas_ordenadas[0]["id"]
    segunda_id = paradas_ordenadas[1]["id"]

    despues_primera = client.post(f"{BASE_RUTAS}/activa/paradas/{primera_id}/completar")
    assert despues_primera.status_code == 200
    estados = {p["id"]: p["estado"] for p in despues_primera.json()["paradas"]}
    assert estados[primera_id] == "completada"
    assert estados[segunda_id] == "en_curso"

    despues_segunda = client.post(f"{BASE_RUTAS}/activa/paradas/{segunda_id}/completar")
    assert despues_segunda.status_code == 200
    assert despues_segunda.json()["estado"] == "completada"

    # Ni planificada ni en_curso: ya no es "la ruta activa".
    assert client.get(f"{BASE_RUTAS}/activa").json() is None


def test_no_se_puede_completar_parada_fuera_de_orden(client, osrm_falso):
    cliente1, cliente2 = armar_chofer_con_lugares(client)
    ruta = client.post(
        f"{BASE_RUTAS}/confirmar",
        json={
            "paradas": [
                {"cliente_id": cliente1["id"], "carga_kg": 10},
                {"cliente_id": cliente2["id"], "carga_kg": 5},
            ]
        },
    ).json()
    client.post(f"{BASE_RUTAS}/activa/iniciar")

    segunda_id = sorted(ruta["paradas"], key=lambda p: p["orden"])[1]["id"]
    respuesta = client.post(f"{BASE_RUTAS}/activa/paradas/{segunda_id}/completar")
    assert respuesta.status_code == 409


def test_geometria_ruta_activa(client, osrm_falso, osrm_geometria_falsa):
    cliente1, _ = armar_chofer_con_lugares(client)
    client.post(
        f"{BASE_RUTAS}/confirmar",
        json={"paradas": [{"cliente_id": cliente1["id"], "carga_kg": 10}]},
    )

    respuesta = client.get(f"{BASE_RUTAS}/activa/geometria")
    assert respuesta.status_code == 200
    tramos = respuesta.json()["tramos"]
    # depósito→parada→depósito: 2 tramos.
    assert len(tramos) == 2
    assert all(len(tramo) >= 2 for tramo in tramos)


def test_confirmar_con_ventanas_horarias_calcula_llegada(client, osrm_falso):
    cliente1, cliente2 = armar_chofer_con_lugares(client)

    respuesta = client.post(
        f"{BASE_RUTAS}/confirmar",
        json={
            "paradas": [
                {
                    "cliente_id": cliente1["id"],
                    "carga_kg": 10,
                    "unidades": 3,
                    "ventana_inicio": 480,
                    "ventana_fin": 600,
                },
                {
                    "cliente_id": cliente2["id"],
                    "carga_kg": 5,
                    "unidades": 7,
                    "ventana_inicio": 500,
                    "ventana_fin": 700,
                },
            ],
            "usa_ventanas_horarias": True,
        },
    )
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["usa_ventanas_horarias"] is True
    assert cuerpo["tipo_problema"] == "VRPTW"
    for parada in cuerpo["paradas"]:
        assert parada["hora_estimada_llegada"] is not None
        assert parada["ventana_inicio_snapshot"] is not None
        assert parada["ventana_fin_snapshot"] is not None


def test_ventanas_horarias_sin_completar_todas_da_400(client, osrm_falso):
    cliente1, cliente2 = armar_chofer_con_lugares(client)

    respuesta = client.post(
        f"{BASE_RUTAS}/optimizar",
        json={
            "paradas": [
                {
                    "cliente_id": cliente1["id"],
                    "carga_kg": 10,
                    "ventana_inicio": 480,
                    "ventana_fin": 600,
                },
                {"cliente_id": cliente2["id"], "carga_kg": 5},
            ],
            "usa_ventanas_horarias": True,
        },
    )
    assert respuesta.status_code == 400
    assert "ventana" in respuesta.json()["detail"].lower()


def test_unidades_y_distancia_acumulada_persisten(client, osrm_falso):
    cliente1, cliente2 = armar_chofer_con_lugares(client)

    respuesta = client.post(
        f"{BASE_RUTAS}/confirmar",
        json={
            "paradas": [
                {"cliente_id": cliente1["id"], "carga_kg": 10, "unidades": 4},
                {"cliente_id": cliente2["id"], "carga_kg": 5, "unidades": 9},
            ]
        },
    )
    assert respuesta.status_code == 201

    activa = client.get(f"{BASE_RUTAS}/activa").json()
    unidades_por_parada = {p["unidades_snapshot"] for p in activa["paradas"]}
    assert unidades_por_parada == {4, 9}
    assert all(p["distancia_acumulada_m"] > 0 for p in activa["paradas"])


def test_historial_lista_rutas_del_rango_con_contadores(client, osrm_falso):
    cliente1, _ = armar_chofer_con_lugares(client)

    client.post(
        f"{BASE_RUTAS}/confirmar",
        json={"paradas": [{"cliente_id": cliente1["id"], "carga_kg": 10}]},
    )
    client.post(f"{BASE_RUTAS}/activa/iniciar")
    parada_id = client.get(f"{BASE_RUTAS}/activa").json()["paradas"][0]["id"]
    client.post(f"{BASE_RUTAS}/activa/paradas/{parada_id}/completar")

    hoy = datetime.now(UTC).date().isoformat()
    respuesta = client.get(f"{BASE_RUTAS}/historial", params={"desde": hoy, "hasta": hoy})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 1
    assert cuerpo[0]["estado"] == "completada"
    assert cuerpo[0]["paradas_total"] == 1
    assert cuerpo[0]["paradas_completadas"] == 1

    detalle = client.get(f"{BASE_RUTAS}/historial/{cuerpo[0]['id']}")
    assert detalle.status_code == 200
    assert detalle.json()["id"] == cuerpo[0]["id"]


def test_historial_de_ruta_ajena_da_404(client, osrm_falso):
    registrar_chofer_independiente(client, email="dueno-hist@test.com", patente="HI111HI")
    client.post(BASE_DEPOSITOS, json=PAYLOAD_DEPOSITO)
    cliente = client.post(BASE_CLIENTES, json=PAYLOAD_CLIENTE_1).json()
    ruta = client.post(
        f"{BASE_RUTAS}/confirmar",
        json={"paradas": [{"cliente_id": cliente["id"], "carga_kg": 10}]},
    ).json()
    client.cookies.clear()

    registrar_chofer_independiente(client, email="otro-hist@test.com", patente="HI222HI")
    respuesta = client.get(f"{BASE_RUTAS}/historial/{ruta['id']}")
    assert respuesta.status_code == 404


def test_optimizar_excede_capacidad_da_mensaje_especifico(client, osrm_falso):
    cliente1, cliente2 = armar_chofer_con_lugares(client)

    respuesta = client.post(
        f"{BASE_RUTAS}/optimizar",
        json={
            "paradas": [
                {"cliente_id": cliente1["id"], "carga_kg": 300},
                {"cliente_id": cliente2["id"], "carga_kg": 300},
            ]
        },
    )
    assert respuesta.status_code == 400
    mensaje = respuesta.json()["detail"].lower()
    assert "capacidad" in mensaje
    assert "600" in mensaje


def _por_id(ruta_json):
    return {p["id"]: p for p in ruta_json["paradas"]}


def test_registrar_llegada_persiste_y_es_idempotente(client, osrm_falso):
    paradas = iniciar_ruta_con_paradas(client)
    primera_id = paradas[0]["id"]
    assert paradas[0]["hora_real_llegada"] is None

    respuesta = client.post(f"{BASE_RUTAS}/activa/paradas/{primera_id}/llegada")
    assert respuesta.status_code == 200
    llegada = _por_id(respuesta.json())[primera_id]["hora_real_llegada"]
    assert llegada is not None

    repetida = client.post(f"{BASE_RUTAS}/activa/paradas/{primera_id}/llegada")
    assert repetida.status_code == 200
    assert _por_id(repetida.json())[primera_id]["hora_real_llegada"] == llegada

    # Sobrevive a recargar: viene del servidor, no del estado local.
    activa = client.get(f"{BASE_RUTAS}/activa").json()
    assert _por_id(activa)[primera_id]["hora_real_llegada"] == llegada


def test_registrar_llegada_en_parada_que_no_es_la_actual_da_409(client, osrm_falso):
    paradas = iniciar_ruta_con_paradas(client)
    segunda_id = paradas[1]["id"]

    respuesta = client.post(f"{BASE_RUTAS}/activa/paradas/{segunda_id}/llegada")
    assert respuesta.status_code == 409

    activa = client.get(f"{BASE_RUTAS}/activa").json()
    assert _por_id(activa)[segunda_id]["hora_real_llegada"] is None


def test_registrar_llegada_con_ruta_sin_iniciar_da_409(client, osrm_falso):
    cliente1, _ = armar_chofer_con_lugares(client)
    ruta = client.post(
        f"{BASE_RUTAS}/confirmar",
        json={"paradas": [{"cliente_id": cliente1["id"], "carga_kg": 5}]},
    ).json()

    parada_id = ruta["paradas"][0]["id"]
    assert client.post(f"{BASE_RUTAS}/activa/paradas/{parada_id}/llegada").status_code == 409


def test_completar_sin_llegada_previa_completa_la_hora_de_llegada(client, osrm_falso):
    paradas = iniciar_ruta_con_paradas(client)
    primera_id = paradas[0]["id"]

    respuesta = client.post(f"{BASE_RUTAS}/activa/paradas/{primera_id}/completar")
    parada = _por_id(respuesta.json())[primera_id]
    assert parada["estado"] == "completada"
    assert parada["hora_real_llegada"] is not None
    assert parada["hora_real_salida"] is not None


def test_completar_conserva_la_llegada_ya_registrada(client, osrm_falso):
    paradas = iniciar_ruta_con_paradas(client)
    primera_id = paradas[0]["id"]
    llegada = _por_id(client.post(f"{BASE_RUTAS}/activa/paradas/{primera_id}/llegada").json())[
        primera_id
    ]["hora_real_llegada"]

    respuesta = client.post(f"{BASE_RUTAS}/activa/paradas/{primera_id}/completar")
    assert _por_id(respuesta.json())[primera_id]["hora_real_llegada"] == llegada


def test_fallar_parada_registra_motivo_incidencia_y_avanza(client, db_session, osrm_falso):
    paradas = iniciar_ruta_con_paradas(client)
    primera_id, segunda_id = paradas[0]["id"], paradas[1]["id"]

    respuesta = client.post(
        f"{BASE_RUTAS}/activa/paradas/{primera_id}/fallar",
        json={"motivo": "cliente_ausente", "descripcion": "Persiana baja"},
    )
    assert respuesta.status_code == 200
    por_id = _por_id(respuesta.json())
    assert por_id[primera_id]["estado"] == "fallida"
    assert por_id[primera_id]["motivo_fallo"] == "cliente_ausente"
    assert por_id[segunda_id]["estado"] == "en_curso"

    incidencias = db_session.execute(select(Incidencia)).scalars().all()
    assert len(incidencias) == 1
    assert incidencias[0].tipo == TipoIncidencia.CLIENTE_AUSENTE
    assert str(incidencias[0].parada_id) == primera_id
    assert incidencias[0].descripcion == "Persiana baja"


def test_fallar_parada_sin_motivo_da_422(client, db_session, osrm_falso):
    paradas = iniciar_ruta_con_paradas(client)
    primera_id = paradas[0]["id"]

    respuesta = client.post(f"{BASE_RUTAS}/activa/paradas/{primera_id}/fallar", json={})
    assert respuesta.status_code == 422

    activa = client.get(f"{BASE_RUTAS}/activa").json()
    assert _por_id(activa)[primera_id]["estado"] == "en_curso"
    assert db_session.execute(select(Incidencia)).scalars().all() == []


def test_fallar_con_motivo_invalido_da_422(client, osrm_falso):
    paradas = iniciar_ruta_con_paradas(client)
    respuesta = client.post(
        f"{BASE_RUTAS}/activa/paradas/{paradas[0]['id']}/fallar", json={"motivo": "inventado"}
    )
    assert respuesta.status_code == 422


def test_fallar_con_problema_de_vehiculo_da_422(client, osrm_falso):
    paradas = iniciar_ruta_con_paradas(client)
    respuesta = client.post(
        f"{BASE_RUTAS}/activa/paradas/{paradas[0]['id']}/fallar",
        json={"motivo": "problema_vehiculo"},
    )
    assert respuesta.status_code == 422


def test_fallar_la_ultima_parada_cierra_la_ruta(client, db_session, osrm_falso):
    paradas = iniciar_ruta_con_paradas(client)
    client.post(f"{BASE_RUTAS}/activa/paradas/{paradas[0]['id']}/completar")

    respuesta = client.post(
        f"{BASE_RUTAS}/activa/paradas/{paradas[1]['id']}/fallar",
        json={"motivo": "rechazo_entrega"},
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "completada"
    assert client.get(f"{BASE_RUTAS}/activa").json() is None

    ruta = db_session.execute(select(Ruta)).scalars().one()
    assert ruta.hora_fin_real is not None
    assert len(db_session.execute(select(Incidencia)).scalars().all()) == 1


def test_saltear_manda_la_parada_al_final_y_avanza(client, osrm_falso):
    paradas = iniciar_ruta_con_paradas(client, cantidad=3)
    primera_id, segunda_id, tercera_id = (p["id"] for p in paradas)
    client.post(f"{BASE_RUTAS}/activa/paradas/{primera_id}/llegada")

    respuesta = client.post(f"{BASE_RUTAS}/activa/paradas/{primera_id}/saltear")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    por_id = _por_id(cuerpo)

    assert por_id[primera_id]["estado"] == "pendiente"
    assert por_id[primera_id]["orden"] == 2
    assert por_id[segunda_id]["estado"] == "en_curso"
    assert por_id[tercera_id]["estado"] == "pendiente"
    # Órdenes contiguos y la respuesta ya viene en ese orden.
    assert [p["orden"] for p in cuerpo["paradas"]] == [0, 1, 2]
    # La llegada avisada antes de irse no vale para el próximo intento.
    assert por_id[primera_id]["hora_real_llegada"] is None


def test_parada_salteada_se_visita_al_final_y_cierra_la_ruta(client, osrm_falso):
    paradas = iniciar_ruta_con_paradas(client, cantidad=3)
    primera_id, segunda_id, tercera_id = (p["id"] for p in paradas)

    client.post(f"{BASE_RUTAS}/activa/paradas/{primera_id}/saltear")
    client.post(f"{BASE_RUTAS}/activa/paradas/{segunda_id}/completar")
    despues = client.post(f"{BASE_RUTAS}/activa/paradas/{tercera_id}/completar").json()

    assert _por_id(despues)[primera_id]["estado"] == "en_curso"
    assert despues["estado"] == "en_curso"

    final = client.post(f"{BASE_RUTAS}/activa/paradas/{primera_id}/completar").json()
    assert final["estado"] == "completada"


def test_saltear_la_unica_parada_restante_da_409(client, osrm_falso):
    paradas = iniciar_ruta_con_paradas(client)
    client.post(f"{BASE_RUTAS}/activa/paradas/{paradas[0]['id']}/completar")

    respuesta = client.post(f"{BASE_RUTAS}/activa/paradas/{paradas[1]['id']}/saltear")
    assert respuesta.status_code == 409

    activa = client.get(f"{BASE_RUTAS}/activa").json()
    assert _por_id(activa)[paradas[1]["id"]]["estado"] == "en_curso"


def test_saltear_no_cuenta_una_parada_fallida_como_pendiente(client, osrm_falso):
    paradas = iniciar_ruta_con_paradas(client, cantidad=3)
    client.post(
        f"{BASE_RUTAS}/activa/paradas/{paradas[0]['id']}/fallar",
        json={"motivo": "direccion_incorrecta"},
    )
    client.post(f"{BASE_RUTAS}/activa/paradas/{paradas[1]['id']}/completar")

    # Queda solo la tercera: la fallida no es candidata a "otra pendiente".
    respuesta = client.post(f"{BASE_RUTAS}/activa/paradas/{paradas[2]['id']}/saltear")
    assert respuesta.status_code == 409


def _registrar_con_dos_depositos(client):
    registrar_chofer_independiente(client)
    primero = client.post(BASE_DEPOSITOS, json=PAYLOAD_DEPOSITO).json()
    segundo = client.post(
        BASE_DEPOSITOS, json={"nombre": "Zeta base", "latitud": -32.9000, "longitud": -68.8000}
    ).json()
    cliente = client.post(BASE_CLIENTES, json=PAYLOAD_CLIENTE_1).json()
    return primero, segundo, cliente


def test_sin_deposito_elegido_se_usa_el_primero(client, osrm_falso):
    primero, _, cliente = _registrar_con_dos_depositos(client)

    ruta = client.post(
        f"{BASE_RUTAS}/confirmar", json={"paradas": [{"cliente_id": cliente["id"], "carga_kg": 5}]}
    ).json()
    assert ruta["deposito"]["latitud"] == primero["latitud"]
    assert ruta["deposito"]["longitud"] == primero["longitud"]


def test_deposito_elegido_es_el_punto_de_partida(client, osrm_falso):
    _, segundo, cliente = _registrar_con_dos_depositos(client)

    ruta = client.post(
        f"{BASE_RUTAS}/confirmar",
        json={
            "paradas": [{"cliente_id": cliente["id"], "carga_kg": 5}],
            "deposito_id": segundo["id"],
        },
    ).json()
    assert ruta["deposito"]["latitud"] == segundo["latitud"]
    assert ruta["deposito"]["longitud"] == segundo["longitud"]


def test_deposito_ajeno_o_inexistente_da_400(client, osrm_falso):
    registrar_chofer_independiente(client, email="dueno-dep@test.com", patente="DP111DP")
    deposito_ajeno = client.post(BASE_DEPOSITOS, json=PAYLOAD_DEPOSITO).json()
    client.cookies.clear()

    _, _, cliente = _registrar_con_dos_depositos_de_otro(client)
    for deposito_id in (deposito_ajeno["id"], "00000000-0000-0000-0000-000000000000"):
        respuesta = client.post(
            f"{BASE_RUTAS}/optimizar",
            json={
                "paradas": [{"cliente_id": cliente["id"], "carga_kg": 5}],
                "deposito_id": deposito_id,
            },
        )
        assert respuesta.status_code == 400, deposito_id
        assert "depósito" in respuesta.json()["detail"].lower()


def _registrar_con_dos_depositos_de_otro(client):
    registrar_chofer_independiente(client, email="otro-dep@test.com", patente="DP222DP")
    primero = client.post(BASE_DEPOSITOS, json=PAYLOAD_DEPOSITO).json()
    segundo = client.post(
        BASE_DEPOSITOS, json={"nombre": "Zeta base", "latitud": -32.9000, "longitud": -68.8000}
    ).json()
    cliente = client.post(BASE_CLIENTES, json=PAYLOAD_CLIENTE_1).json()
    return primero, segundo, cliente


def test_eta_incluye_el_tiempo_de_servicio_del_lugar(client, osrm_falso):
    registrar_chofer_independiente(client)
    client.post(BASE_DEPOSITOS, json=PAYLOAD_DEPOSITO)
    ids = [
        client.post(payload_url, json={**payload, "tiempo_servicio_default": 15}).json()["id"]
        for payload_url, payload in (
            (BASE_CLIENTES, PAYLOAD_CLIENTE_1),
            (BASE_CLIENTES, PAYLOAD_CLIENTE_2),
        )
    ]

    ruta = client.post(
        f"{BASE_RUTAS}/confirmar",
        json={
            "paradas": [
                {"cliente_id": i, "carga_kg": 5, "ventana_inicio": 480, "ventana_fin": 900}
                for i in ids
            ],
            "usa_ventanas_horarias": True,
        },
    ).json()
    llegadas = [
        p["hora_estimada_llegada"] for p in sorted(ruta["paradas"], key=lambda p: p["orden"])
    ]

    # Entre dos paradas consecutivas hay al menos los 15 min de servicio de la
    # primera (el traslado sintético entre lugares vecinos es de ~1-2 min).
    assert llegadas[1] - llegadas[0] >= 15


def test_ventana_del_deposito_acota_la_ruta_con_ventanas(client, osrm_falso):
    registrar_chofer_independiente(client)
    # El depósito cierra a las 08:01: ninguna parada con ventana 10:00-11:40 es alcanzable.
    client.post(
        BASE_DEPOSITOS, json={**PAYLOAD_DEPOSITO, "ventana_inicio": 480, "ventana_fin": 481}
    )
    cliente = client.post(BASE_CLIENTES, json=PAYLOAD_CLIENTE_1).json()

    respuesta = client.post(
        f"{BASE_RUTAS}/optimizar",
        json={
            "paradas": [
                {
                    "cliente_id": cliente["id"],
                    "carga_kg": 5,
                    "ventana_inicio": 600,
                    "ventana_fin": 700,
                }
            ],
            "usa_ventanas_horarias": True,
        },
    )
    assert respuesta.status_code == 400
    assert "ventanas horarias" in respuesta.json()["detail"].lower()
