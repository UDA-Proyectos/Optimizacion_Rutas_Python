## 1. Bug del 400/500

- [x] 1.1 Escribir un test en `tests/` que envía un problema infactible a `/api/v1/optimizar` y espera 400 (debe fallar hoy con 500)
- [x] 1.2 Corregir en `api/routes.py` que el `HTTPException` de un problema sin solución no pase por el `except Exception` (sacar el chequeo del `try`) y verificar que el test anterior pasa

## 2. Tests del motor

- [x] 2.1 Crear `tests/test_solver.py` con casos CVRP resoluble, capacidad excedida, VRPTW resoluble y VRPTW infactible; verificar con `uv run pytest tests/test_solver.py`
- [x] 2.2 Crear `tests/test_osrm_client.py` con la red mockeada: orden `lon,lat`, parseo de matrices y error HTTP; verificar con `uv run pytest tests/test_osrm_client.py`

## 3. OSRM self-hosted

- [x] 3.1 Crear `scripts/preparar_osrm.py` que baja las calles del Gran Mendoza de Overpass (por teselas; el extracto de Argentina no entra en los ~3 GB de Docker) y corre `osrm-extract`, `osrm-partition` y `osrm-customize`; verificar que genera los archivos `.osrm*` en el volumen
- [x] 3.2 Descomentar y completar el servicio `osrm` en `docker-compose.yml` con versión de imagen fija (`ghcr.io`) y en un profile; verificar con `docker compose --profile osrm up -d osrm` y una consulta `route` de prueba
- [x] 3.3 Actualizar `.env.example` y `README.md` con la nueva `OSRM_BASE_URL` y los requisitos de disco y RAM; verificar que un checkout limpio puede seguir las instrucciones
- [x] 3.4 Correr un flujo real de armar ruta contra el OSRM local; verificar que devuelve matriz y geometría

## 4. Documentación

- [x] 4.1 Actualizar `CLAUDE.md` (estado, arquitectura, roadmap y gaps: VRPTW, historial, búsqueda, panel de escritorio, OpenSpec, bug corregido); verificar que no quedan afirmaciones desactualizadas contra el código

## 5. Cierre

- [x] 5.1 Correr `uv run pytest` y `uv run ruff check . && uv run ruff format --check .`; verificar que pasan
