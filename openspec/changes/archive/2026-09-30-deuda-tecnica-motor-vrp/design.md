## Context

En `api/routes.py` el `HTTPException(400)` por `{"estado": "Fallo"}` se lanza dentro del mismo `try` que tiene `except Exception`, y termina como 500 (gap documentado en CLAUDE.md §9). `routing/solver.py` no tiene tests; `services/osrm_client.py` usa `settings.osrm_base_url`, hoy el demo público. `docker-compose.yml` solo levanta Postgres, con el servicio `osrm` comentado. Ver proposal.md para la motivación.

## Goals / Non-Goals

**Goals:**
- Corregir el mapeo de errores con el cambio mínimo.
- Cubrir con tests el solver y el cliente OSRM sin red real.
- Un OSRM local reproducible con un solo comando documentado.

**Non-Goals:**
- Generalizar el solver para los benchmarks (ítem 5 del roadmap).
- `response_model` tipado de `/optimizar`.
- PyVRP y dataset del Gran Mendoza (ítems 8-9).

## Decisions

- **Bug**: se saca el chequeo de `estado == "Fallo"` del `try` que capturaba todo, en vez de agregar `except HTTPException: raise`: arregla la causa (un `HTTPException` intencional no debe pasar por un `except Exception`) y no depende de acordarse del parche en cada `try` nuevo. Además el `except Exception` deja el detalle en el log y responde un mensaje genérico, y un `ValueError` del solver (entradas inconsistentes) se traduce a 400.
- **Tests del solver** con matrices sintéticas pequeñas (sin OSRM), incluyendo un caso infactible que espera `estado == "Fallo"`. Se usa un `time_limit` bajo vía `settings` en el test para no ralentizar la suite.
- **Tests de `osrm_client`** con `httpx`/`requests` mockeado (según lo que use el cliente hoy), verificando que las coordenadas van como `lon,lat`, el parseo a metros y segundos y el manejo de errores HTTP.
- **OSRM self-hosted, con el mapa recortado**: imagen `ghcr.io/project-osrm/osrm-backend:v5.27.1` (Docker Hub quedó en la v5.25 de 2021) con perfil `driving` y algoritmo MLD. El servicio `osrm` va en un *profile* de compose (`docker compose --profile osrm up -d osrm`) para que un `up` sin datos preparados no deje un contenedor reiniciándose. `scripts/preparar_osrm.py` baja las calles del Gran Mendoza de Overpass por teselas (una consulta grande da 504), las fusiona y corre `osrm-extract`/`osrm-partition`/`osrm-customize`. Se descartó el extracto de Argentina completo de Geofabrik: cientos de MB y varios GB de RAM en `osrm-extract`, y el Docker Desktop de desarrollo tiene ~3 GB. `--extracto` permite usar un `.pbf` propio en máquinas con más memoria.
- **Config**: `OSRM_BASE_URL` sigue en `Settings`. `.env.example` mantiene el servidor demo público como default (anda sin preparar nada; un checkout nuevo no tiene los datos de OSRM) y documenta `http://localhost:5001` como opción.
- **CLAUDE.md**: actualizar §1, §3, §8-§11 con el estado real; no cambia código.

## Risks / Trade-offs

- [Overpass es un servicio público con límites y a veces responde 504] → teselas chicas con reintentos y un servidor espejo; si aun así falla, `--extracto` con un `.pbf` propio.
- [Diferencias entre OSRM local y demo (versión, perfil)] → fijar la versión de la imagen en `docker-compose.yml`.
- [Los tests con mocks pueden divergir del OSRM real] → un test de integración opcional marcado y excluido por defecto.

## Migration Plan

1. Preparar los datos de OSRM una vez con el script; levantar `docker compose --profile osrm up -d osrm`.
2. Cambiar `OSRM_BASE_URL` en `.env` a `http://localhost:5001`.
3. Rollback: volver `OSRM_BASE_URL` al demo público; no hay cambios de esquema.
