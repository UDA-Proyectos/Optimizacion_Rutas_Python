## Why

Hoy una parada solo puede pasar de pendiente a completada. El botón "Llegué al destino" es puro estado local del frontend (se pierde al recargar y `hora_real_llegada` nunca se guarda), no existe salida cuando el cliente está ausente o rechaza la entrega (`EstadoParada.FALLIDA` está en el modelo pero nunca se usa) y el chofer no puede saltear una parada. Sin esto la ejecución de la ruta no refleja la realidad y no se pueden medir tiempos de servicio ni ventanas cumplidas.

## What Changes

- Nuevo endpoint para registrar la llegada a la parada en curso (persiste `hora_real_llegada`); el frontend deja de guardar "arribado" solo en estado local.
- Nuevo endpoint para marcar una parada como **fallida** con un motivo (`TipoIncidencia`), que avanza a la siguiente igual que completar y crea una `Incidencia` asociada a la parada.
- Nuevo endpoint para **saltear** una parada en curso: pasa al final del recorrido pendiente sin perderse.
- La ruta se cierra (`completada`) cuando no quedan paradas pendientes ni en curso, aunque alguna haya quedado fallida.
- UI de la parada actual: botones "Llegué", "Entregada", "No pude entregar" (con selector de motivo) y "Saltear".
- La timeline y el historial distinguen paradas fallidas y salteadas.

## Capabilities

### New Capabilities
- `ejecucion-de-ruta`: ciclo de vida de una parada durante la ruta en curso (llegada, entrega, fallo con motivo, salto) y cierre de la ruta.

### Modified Capabilities

## Impact

- Backend: `db/modelos.py` (`ParadaRuta.motivo_fallo` opcional + migración Alembic), `db/crud.py`, `api/routes_rutas.py`, `api/schemas_rutas.py`.
- Frontend: `VistaEnCursoRuta.tsx`, `api/rutas.ts`, `tipos/ruta.ts`.
- Tests: `tests/test_rutas.py`.
- Sin dependencias nuevas. Es prerrequisito de `incidencias-chofer` y `resumen-de-cierre`.
