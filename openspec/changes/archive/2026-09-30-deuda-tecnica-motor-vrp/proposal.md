## Why

El motor VRP arrastra deuda ya identificada en el CLAUDE.md: `/api/v1/optimizar` devuelve 500 en vez de 400 cuando el solver no encuentra solución (el `HTTPException` queda capturado por el `except Exception`), no hay tests de `routing/solver.py` ni de `services/osrm_client.py`, OSRM apunta al servidor demo público con rate limiting, y el propio `CLAUDE.md` quedó desactualizado respecto de lo implementado (VRPTW, historial, búsqueda de direcciones).

## What Changes

- Corregir `/api/v1/optimizar` para que una falla del solver responda 400 con el mensaje del solver.
- Agregar `tests/test_solver.py` (CVRP, VRPTW, caso infactible, capacidad excedida) y `tests/test_osrm_client.py` (formato `lon,lat`, parseo de matrices, errores HTTP) con la red mockeada.
- Self-hostear OSRM: servicio `osrm` en `docker-compose.yml` con un extracto de Argentina/Mendoza, y `OSRM_BASE_URL` apuntando a la instancia local por defecto en desarrollo.
- Actualizar `CLAUDE.md` para reflejar el estado real (VRPTW en producción, historial, búsqueda de direcciones, panel de escritorio, OpenSpec) y el roadmap restante.

## Capabilities

### New Capabilities
- `optimizacion-vrp`: contrato de errores del endpoint de optimización pura del motor VRP.

### Modified Capabilities

## Impact

- Backend: `api/routes.py`, nuevos `tests/test_solver.py` y `tests/test_osrm_client.py`.
- Infra: `docker-compose.yml`, nuevo `scripts/preparar_osrm.*`, `.env.example`, `README.md`.
- Documentación: `CLAUDE.md`.
- OSRM local exige descargar y procesar un extracto `.osm.pbf` y más memoria de disco/RAM en la máquina de desarrollo.
