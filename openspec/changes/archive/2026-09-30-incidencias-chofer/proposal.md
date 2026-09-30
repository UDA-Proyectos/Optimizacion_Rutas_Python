## Why

El modelo `Incidencia` existe, pero no hay endpoint ni pantalla: el botón "Reportar incidencia" del header está deshabilitado y la sección "Incidencias" es un placeholder. El chofer no puede avisar de un problema del vehículo o de una parada durante la ruta, ni consultar después qué reportó.

## What Changes

- Endpoint para reportar una incidencia sobre la ruta en curso, opcionalmente asociada a una parada (problema general como falla del vehículo, o específico de una parada).
- Endpoint para listar las incidencias del chofer (incluidas las que se crean automáticamente al marcar una parada como fallida).
- UI: el botón "Reportar incidencia" del header abre un formulario (tipo, parada opcional, descripción) y la sección "Incidencias" muestra el historial real en lugar del placeholder.
- El badge/subtítulo de la sección deja de decir "Sin incidencias registradas" fijo y usa el conteo real.

## Capabilities

### New Capabilities
- `incidencias`: reporte y consulta de incidencias del chofer independiente sobre su ruta.

### Modified Capabilities

## Impact

- Backend: nuevos `api/schemas_incidencias.py` y `api/routes_incidencias.py`, funciones en `db/crud.py`, registro del router en `main.py`. Sin migración (el modelo ya existe).
- Frontend: `EscritorioChofer.tsx`, nuevo `componentes/incidencias/`, `api/incidencias.ts`, `tipos/incidencia.ts`.
- Depende de `cerrar-ciclo-de-parada` (las incidencias por fallo se crean ahí).
