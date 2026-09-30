## Why

Cuando la ruta se completa, "Ruta de hoy" solo muestra "¡Ruta completada!" con los números del plan, y el historial muestra únicamente el plan (paradas, kilómetros planificados). Se guardan `hora_fin_real`, `hora_real_salida` y (tras `cerrar-ciclo-de-parada`) llegadas, fallos e incidencias, pero el chofer nunca ve cómo le fue realmente el día.

## What Changes

- Pantalla de resumen de cierre al completar la ruta: duración real, entregas completadas / fallidas / salteadas, carga entregada, ventanas cumplidas (en VRPTW), incidencias del día y distancia planificada.
- El detalle de un día en el historial muestra las mismas métricas reales y el estado de cada parada (completada, fallida con motivo).
- El listado mensual del historial incorpora resultado (completadas/total) y marca los días con paradas fallidas.
- Las métricas se calculan en el backend y se exponen en `RutaPublica`; el frontend solo las presenta.

## Capabilities

### New Capabilities
- `resumen-y-historial-de-ruta`: métricas reales de una ruta terminada y su presentación en el cierre y en el historial.

### Modified Capabilities

## Impact

- Backend: `api/schemas_rutas.py` (campos `hora_fin_real`, `resumen`), `db/crud.py`, `api/routes_rutas.py`. Sin migración.
- Frontend: `RutaDeHoyEscritorio.tsx` (`ResumenRuta`), `PanelHistorial.tsx`, `Almanaque.tsx`, `tipos/ruta.ts`.
- Depende de `cerrar-ciclo-de-parada` (fallos, llegadas) y usa el conteo de `incidencias-chofer`.
