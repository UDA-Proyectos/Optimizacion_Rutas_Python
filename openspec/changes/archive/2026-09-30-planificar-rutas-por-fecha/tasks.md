## 1. Modelo y migración

- [x] 1.1 Agregar `Ruta.nombre` (nullable, 60) y su migración; verificar con `alembic upgrade head`, `downgrade -1` y `upgrade head`

## 2. Backend

- [x] 2.1 En `db/crud.py` reemplazar `obtener_ruta_activa` por `obtener_ruta_en_curso`, `listar_rutas_del_dia` y `hay_ruta_abierta`, y aceptar `nombre` en `crear_ruta`; verificar con `uv run ruff check .` y los tests de las tareas siguientes
- [x] 2.2 `POST /rutas/confirmar` con `fecha` y `nombre` (400 fecha pasada o a más de 60 días, sin 409 por otra ruta) y `GET /rutas?fecha=`; verificar con tests de fecha, de dos rutas el mismo día y del listado
- [x] 2.3 `POST /rutas/{id}/iniciar` (elige cuál, una sola en curso, solo desde su día), `PUT /rutas/{id}` y `DELETE /rutas/{id}`, y `GET /rutas/activa` como ruta en curso; verificar con tests de cada escenario de la spec
- [x] 2.4 Adaptar el reporte de incidencias y el bloqueo de edición del vehículo a la ruta en curso y a `hay_ruta_abierta`; verificar con tests, incluida una ruta planificada para otro día
- [x] 2.5 Migrar los tests y helpers que usaban `/rutas/activa` para confirmar, editar, cancelar e iniciar; verificar que toda la suite pasa

## 3. Frontend

- [x] 3.1 Actualizar tipos y `api/rutas.ts` (listar por fecha, iniciar/editar/eliminar por id, fecha y nombre al confirmar); verificar con `npm run build`
- [x] 3.2 Hacer que `useRutaActiva` maneje la fecha visible, las rutas del día y la ruta seleccionada, con copia offline; verificar con `npm run build` y manualmente
- [x] 3.3 Selector de fecha y de ruta en la pantalla de rutas, con la ruta en curso seleccionada sola; verificar manualmente con dos rutas el mismo día
- [x] 3.4 Fecha y nombre al armar la ruta, botón "Armar ruta" siempre disponible y edición por id; verificar manualmente armando una ruta para mañana y una segunda para hoy
- [x] 3.5 Ajustar historial y "usar de nuevo" a las rutas por id; verificar manualmente

## 4. Cierre

- [x] 4.1 Correr `uv run pytest`, `uv run ruff check .`, `npm run build`, `npm run lint` y `npm test`; verificar que pasan
