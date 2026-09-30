## 1. Backend

- [x] 1.1 Implementar la función pura de resumen (duración, completadas/fallidas/salteadas, carga entregada, ventanas cumplidas) y verificar con tests unitarios de los casos de la spec
- [x] 1.2 Exponer `hora_fin_real` y `resumen` (solo si `completada`) en `RutaPublica` y verificar con test de API que es `null` en una ruta en curso
- [x] 1.3 Agregar el conteo de incidencias y resultado por día a `RutaHistorialItem` con una consulta agregada; verificar con test en `tests/test_rutas.py`

## 2. Frontend

- [x] 2.1 Actualizar `tipos/ruta.ts`; verificar con `npm run build`
- [x] 2.2 Extender `ResumenRuta` en `RutaDeHoyEscritorio.tsx` con la rama completada (KPIs del resumen y acciones "Armar otra ruta" / "Ver historial"); verificar manualmente completando una ruta
- [x] 2.3 Mostrar resumen y estado por parada (con motivo) en `PanelHistorial.tsx`; verificar manualmente con un día que tenga una parada fallida
- [x] 2.4 Mostrar resultado y marca de días con fallos en `Almanaque.tsx`; verificar visualmente

## 3. Cierre

- [x] 3.1 Correr `uv run pytest`, `uv run ruff check .` y `npm run build`; verificar que pasan
