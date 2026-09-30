## 1. Modelo y migración

- [x] 1.1 Agregar `estado`, `resolucion` y `fecha_resolucion` a `Incidencia` y el modelo `EntregaPendiente` en `db/modelos.py`, y generar la migración con las filas existentes como resueltas/cerradas; verificar con `alembic upgrade head`, `downgrade -1` y `upgrade head`

## 2. Backend

- [x] 2.1 Implementar en `db/crud.py` reprogramar una entrega (crea la pendiente, evita duplicados, resuelve la incidencia) y `fallar_parada` con la opción `reprogramar`; verificar con tests de los escenarios de la spec
- [x] 2.2 Agregar `estado` y `resolucion` a `IncidenciaPublica`, el filtro `?estado=` y `POST /incidencias/{id}/resolver` (404 ajena, 409 ya resuelta o sin parada fallida); verificar con tests en `tests/test_incidencias.py`
- [x] 2.3 Crear `api/routes_entregas_pendientes.py` con `GET /api/v1/entregas-pendientes` (propias y de lugares activos) y registrarlo en `main.py`; verificar con tests
- [x] 2.4 Dar por incluida la entrega pendiente al confirmar o editar una ruta que contiene el lugar, y devolverla a pendiente si esa ruta se cancela o se edita sin el lugar; verificar con tests de confirmar, editar, cancelar y desmarcar

## 3. Frontend

- [x] 3.1 Agregar tipos y funciones de API (resolver, filtro, entregas pendientes, `reprogramar` al fallar); verificar con `npm run build`
- [x] 3.2 Ofrecer "Reprogramar para la próxima ruta" o "Decidir después" tras elegir el motivo en `VistaEnCursoRuta.tsx`; verificar manualmente
- [x] 3.3 Filtro pendientes/resueltas y acciones reprogramar / marcar como resuelta en `PanelIncidencias.tsx`, con indicador de pendientes en el menú; verificar manualmente
- [x] 3.4 Precargar y rotular las entregas reprogramadas en `FlujoArmarRuta.tsx`; verificar manualmente con una ruta real

## 4. Cierre

- [x] 4.1 Correr `uv run pytest`, `uv run ruff check .`, `npm run build`, `npm run lint` y `npm test`; verificar que pasan
