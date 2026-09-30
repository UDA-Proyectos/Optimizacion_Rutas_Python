## Why

Marcar "No pude entregar" hoy solo guarda una incidencia: el chofer no puede hacer nada con esa entrega (volver a intentarla otro día) y la sección "Incidencias" es un registro estático donde no se puede actuar ni distinguir lo que sigue abierto de lo ya resuelto. La mercadería queda sin dueño y el chofer tiene que acordarse solo de agregarla a la próxima ruta.

## What Changes

- Al marcar una parada como no entregada se ofrece **reprogramarla para la próxima ruta** en el momento, o dejar la decisión para después.
- Una entrega reprogramada queda guardada (con su carga, bultos y horario) y **aparece ya marcada** la próxima vez que el chofer arma una ruta, con su etiqueta "Reprogramada". Se da por cumplida al confirmar una ruta que incluye ese lugar.
- Las incidencias pasan a tener **estado** (pendiente o resuelta) y resolución. Las de una entrega fallida nacen pendientes; el resto, las generales o informativas, se cierran con "Marcar como resuelta".
- En "Incidencias" el chofer **filtra** por pendientes, resueltas o todas, y desde cada pendiente puede **reprogramar** la entrega o **marcarla como resuelta**.
- Un indicador muestra cuántas incidencias están pendientes.

## Capabilities

### New Capabilities
- `entregas-reprogramadas`: entregas no realizadas que el chofer reprograma, y cómo se precargan y se dan por cumplidas en la próxima ruta.

### Modified Capabilities
- `ejecucion-de-ruta`: al marcar una parada como fallida se puede pedir reprogramarla en el mismo paso.
- `incidencias`: estado y resolución de cada incidencia, filtro por estado y acción de resolver.

## Impact

- Backend: `db/modelos.py` (estado y resolución en `Incidencia`, nuevo `EntregaPendiente`) y migración Alembic, `db/crud.py`, `api/routes_incidencias.py`, nuevo `api/routes_entregas_pendientes.py`, `api/routes_rutas.py` (opción al fallar y cierre al confirmar/editar).
- Frontend: `VistaEnCursoRuta.tsx` (elección tras el motivo), `PanelIncidencias.tsx` (filtro y acciones), `FlujoArmarRuta.tsx` (precarga de reprogramadas), `NavSidebar.tsx` (indicador), tipos y APIs.
- Sin dependencias nuevas.
- Queda fuera, y se puede sumar después: "lo retira el cliente en el depósito", cancelar la entrega, notas de seguimiento y reabrir una incidencia.
