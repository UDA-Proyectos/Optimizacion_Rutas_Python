## 1. Modelo y migración

- [x] 1.1 Agregar `ParadaRuta.motivo_fallo` (enum `TipoIncidencia`, nullable) en `db/modelos.py` y generar la migración con `alembic revision --autogenerate`; verificar con `uv run alembic upgrade head` y `downgrade -1` sin errores
- [x] 1.2 Exponer `hora_real_llegada` y `motivo_fallo` en `ParadaRutaPublica` (`api/schemas_rutas.py`) y verificar que aparecen en `GET /rutas/activa`

## 2. Lógica de negocio

- [x] 2.1 Implementar en `db/crud.py` `registrar_llegada` (idempotente) y verificar con test que conserva la hora original
- [x] 2.2 Ajustar `completar_parada` para completar `hora_real_llegada` si falta y cerrar la ruta por "sin pendientes/en curso"; verificar con test de ruta con salto previo
- [x] 2.3 Implementar `fallar_parada` (estado fallida, `motivo_fallo`, `Incidencia` con `parada_id`, avance/cierre) y verificar con test que crea una sola incidencia
- [x] 2.4 Implementar `saltear_parada` con renumeración de `orden` en una transacción y verificar con test que no viola `UniqueConstraint` y que rechaza la única parada restante

## 3. API

- [x] 3.1 Agregar `POST /activa/paradas/{id}/llegada`, `/fallar` y `/saltear` en `api/routes_rutas.py` con las validaciones 404/409/422 de la spec; verificar con tests en `tests/test_rutas.py`

## 4. Frontend

- [x] 4.1 Agregar funciones `registrarLlegada`, `fallarParada`, `saltearParada` en `api/rutas.ts` y tipos en `tipos/ruta.ts`; verificar con `npm run build` sin errores de tipos
- [x] 4.2 Reemplazar el estado local `arribado` de `VistaEnCursoRuta.tsx` por `hora_real_llegada` y agregar botones "No pude entregar" (selector de motivo) y "Saltear"; verificar manualmente que recargar la página conserva la llegada
- [x] 4.3 Mostrar paradas fallidas en `FilaTimeline` y en el detalle del historial; verificar visualmente en el navegador

## 5. Cierre

- [x] 5.1 Correr `uv run pytest` y `uv run ruff check . && uv run ruff format --check .`; verificar que todo pasa
