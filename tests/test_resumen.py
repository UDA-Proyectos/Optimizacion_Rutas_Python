from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from api.schemas_rutas import calcular_resumen
from db.modelos import EstadoParada
from tests.conftest import (
    armar_chofer_con_lugares,
    cancelar_unica_ruta,
    iniciar_ruta_con_paradas,
    iniciar_unica_ruta,
)

BASE_RUTAS = "/api/v1/rutas"


def _parada(estado, carga=5, salteos=0, ventana_cumplida=None):
    return SimpleNamespace(
        estado=estado,
        demanda_carga_snapshot=carga,
        veces_salteada=salteos,
        ventana_cumplida=ventana_cumplida,
    )


def _resumen(paradas, usa_ventanas=False, incidencias=0, duracion_min=95):
    inicio = datetime(2026, 9, 30, 9, 0, tzinfo=UTC)
    return calcular_resumen(
        hora_inicio_real=inicio,
        hora_fin_real=inicio + timedelta(minutes=duracion_min),
        paradas=paradas,
        usa_ventanas_horarias=usa_ventanas,
        distancia_total_m=12345,
        incidencias=incidencias,
    )


def test_resumen_cuenta_estados_y_suma_solo_lo_entregado():
    resumen = _resumen(
        [
            _parada(EstadoParada.COMPLETADA, carga=10),
            _parada(EstadoParada.COMPLETADA, carga=7, salteos=1),
            _parada(EstadoParada.COMPLETADA, carga=3),
            _parada(EstadoParada.FALLIDA, carga=50),
        ],
        incidencias=2,
    )
    assert resumen.paradas_completadas == 3
    assert resumen.paradas_fallidas == 1
    assert resumen.paradas_salteadas == 1
    assert resumen.carga_entregada_kg == 20
    assert resumen.incidencias == 2
    assert resumen.duracion_min == 95
    assert resumen.distancia_planificada_m == 12345


def test_resumen_sin_ventanas_no_incluye_metricas_de_ventanas():
    resumen = _resumen([_parada(EstadoParada.COMPLETADA, ventana_cumplida=True)])
    assert resumen.ventanas_cumplidas is None
    assert resumen.ventanas_evaluadas is None
    assert resumen.ventanas_cumplidas_pct is None


def test_resumen_con_ventanas_redondea_el_porcentaje():
    resumen = _resumen(
        [
            _parada(EstadoParada.COMPLETADA, ventana_cumplida=True),
            _parada(EstadoParada.COMPLETADA, ventana_cumplida=True),
            _parada(EstadoParada.COMPLETADA, ventana_cumplida=False),
            _parada(EstadoParada.FALLIDA),
        ],
        usa_ventanas=True,
    )
    assert resumen.ventanas_evaluadas == 3
    assert resumen.ventanas_cumplidas == 2
    assert resumen.ventanas_cumplidas_pct == 67


def test_resumen_con_ventanas_pero_ninguna_evaluable_no_inventa_un_porcentaje():
    resumen = _resumen([_parada(EstadoParada.FALLIDA)], usa_ventanas=True)
    assert resumen.ventanas_cumplidas_pct is None
    assert resumen.ventanas_evaluadas is None


def test_ruta_completada_devuelve_resumen_con_fallidas_y_salteadas(client, osrm_falso):
    paradas = iniciar_ruta_con_paradas(client, cantidad=3)
    primera, segunda, tercera = (p["id"] for p in paradas)

    client.post(f"{BASE_RUTAS}/activa/paradas/{primera}/saltear")
    client.post(f"{BASE_RUTAS}/activa/paradas/{segunda}/completar")
    client.post(f"{BASE_RUTAS}/activa/paradas/{tercera}/fallar", json={"motivo": "cliente_ausente"})
    final = client.post(f"{BASE_RUTAS}/activa/paradas/{primera}/completar").json()

    assert final["estado"] == "completada"
    resumen = final["resumen"]
    assert resumen["paradas_completadas"] == 2
    assert resumen["paradas_fallidas"] == 1
    assert resumen["paradas_salteadas"] == 1
    assert resumen["carga_entregada_kg"] == 10
    assert resumen["incidencias"] == 1
    assert resumen["duracion_min"] is not None
    assert resumen["distancia_planificada_m"] == final["distancia_total_m"]
    assert resumen["ventanas_cumplidas_pct"] is None
    assert final["hora_fin_real"] is not None


def test_ruta_no_terminada_no_tiene_resumen(client, osrm_falso):
    cliente1, _ = armar_chofer_con_lugares(client)
    planificada = client.post(
        f"{BASE_RUTAS}/confirmar", json={"paradas": [{"cliente_id": cliente1["id"], "carga_kg": 5}]}
    ).json()
    assert planificada["resumen"] is None

    en_curso = iniciar_unica_ruta(client).json()
    assert en_curso["resumen"] is None
    assert client.get(f"{BASE_RUTAS}/activa").json()["resumen"] is None


def test_ruta_con_ventanas_horarias_informa_ventanas_cumplidas(client, osrm_falso):
    cliente1, cliente2 = armar_chofer_con_lugares(client)
    client.post(
        f"{BASE_RUTAS}/confirmar",
        json={
            "paradas": [
                # Todo el día: siempre se cumple, sin depender de la hora en que corra el test.
                {"cliente_id": c["id"], "carga_kg": 5, "ventana_inicio": 0, "ventana_fin": 1440}
                for c in (cliente1, cliente2)
            ],
            "usa_ventanas_horarias": True,
        },
    )
    ruta = iniciar_unica_ruta(client).json()
    for parada in sorted(ruta["paradas"], key=lambda p: p["orden"]):
        ruta = client.post(f"{BASE_RUTAS}/activa/paradas/{parada['id']}/completar").json()

    resumen = ruta["resumen"]
    assert resumen["ventanas_evaluadas"] == 2
    assert resumen["ventanas_cumplidas"] == 2
    assert resumen["ventanas_cumplidas_pct"] == 100


def test_historial_expone_fallidas_e_incidencias_y_el_detalle_trae_el_resumen(client, osrm_falso):
    paradas = iniciar_ruta_con_paradas(client)
    client.post(
        f"{BASE_RUTAS}/activa/paradas/{paradas[0]['id']}/fallar", json={"motivo": "rechazo_entrega"}
    )
    client.post(f"{BASE_RUTAS}/activa/paradas/{paradas[1]['id']}/completar")

    hoy = datetime.now(UTC).date().isoformat()
    listado = client.get(f"{BASE_RUTAS}/historial", params={"desde": hoy, "hasta": hoy}).json()
    assert len(listado) == 1
    assert listado[0]["paradas_total"] == 2
    assert listado[0]["paradas_completadas"] == 1
    assert listado[0]["paradas_fallidas"] == 1
    assert listado[0]["incidencias_total"] == 1

    detalle = client.get(f"{BASE_RUTAS}/historial/{listado[0]['id']}").json()
    assert detalle["resumen"]["paradas_fallidas"] == 1
    fallida = next(p for p in detalle["paradas"] if p["estado"] == "fallida")
    assert fallida["motivo_fallo"] == "rechazo_entrega"


def test_ruta_cancelada_no_tiene_resumen(client, osrm_falso):
    cliente1, _ = armar_chofer_con_lugares(client)
    client.post(
        f"{BASE_RUTAS}/confirmar", json={"paradas": [{"cliente_id": cliente1["id"], "carga_kg": 5}]}
    )
    cancelar_unica_ruta(client)

    hoy = datetime.now(UTC).date().isoformat()
    listado = client.get(f"{BASE_RUTAS}/historial", params={"desde": hoy, "hasta": hoy}).json()
    assert listado[0]["estado"] == "cancelada"
    detalle = client.get(f"{BASE_RUTAS}/historial/{listado[0]['id']}").json()
    assert detalle["resumen"] is None
