## Why

Hoy el chofer solo puede armar la ruta de **hoy**, y una sola a la vez: mientras tenga una planificada o en curso, el sistema rechaza armar otra. No puede preparar la ruta de mañana ni tener dos rutas para el mismo día (por ejemplo mañana y tarde) y decidir cuál hace.

## What Changes

- Al armar una ruta se elige la **fecha**: hoy o un día futuro (hasta 60 días), con un **nombre opcional** ("Mañana", "Zona norte") para distinguirla.
- Se pueden tener **varias rutas planificadas el mismo día**; ya no se rechaza armar otra.
- La pantalla de rutas pasa a mostrar **un día a la vez**, con un selector de fecha (anterior, hoy, siguiente) y, si hay más de una ruta ese día, un selector para elegir con cuál trabajar.
- Cada ruta se **inicia, edita o cancela por su identificador**. Solo una puede estar **en curso a la vez**, y solo se inicia el día que le corresponde.
- Las acciones sobre las paradas (llegada, entrega, fallo, salto), el mapa y las incidencias siguen operando sobre la ruta **en curso**.
- El vehículo no se puede modificar (capacidad o patente) mientras haya cualquier ruta planificada o en curso, de cualquier día.
- **BREAKING (API)**: desaparecen `PUT`, `DELETE` y `POST …/iniciar` sobre `/api/v1/rutas/activa`; pasan a `/api/v1/rutas/{id}`. `GET /rutas/activa` devuelve la ruta en curso (antes, la planificada o en curso de hoy). `POST /rutas/confirmar` ya no responde 409 por tener otra ruta.

## Capabilities

### New Capabilities
- `planificacion-de-rutas`: planificar rutas para una fecha, varias por día, elegir cuál iniciar, una sola en curso y reglas de fecha.

### Modified Capabilities
- `perfil-y-vehiculo`: el bloqueo al editar capacidad o patente considera cualquier ruta planificada o en curso, no solo la de hoy.

## Impact

- Backend: `db/modelos.py` (`Ruta.nombre`) y migración, `db/crud.py`, `api/routes_rutas.py`, `api/schemas_rutas.py`, `api/routes_incidencias.py`, `api/routes_auth.py`.
- Frontend: `useRutaActiva` (pasa a manejar las rutas de un día), `RutaDeHoyEscritorio.tsx`, `FlujoArmarRuta.tsx` (fecha y nombre), `PestanaLugares.tsx`, `EscritorioChofer.tsx`, `PanelHistorial.tsx`, `api/rutas.ts`, tipos y la copia offline.
- Tests: se migran los que usaban `/rutas/activa`.
- Sin dependencias nuevas.
