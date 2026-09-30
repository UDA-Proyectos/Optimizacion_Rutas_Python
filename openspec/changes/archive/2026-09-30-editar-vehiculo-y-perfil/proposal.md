## Why

"Mi vehículo" y "Mi cuenta" son solo lectura: el propio texto de la pantalla dice "escribinos, todavía no hay una pantalla de edición". Un chofer que cambia de vehículo, corrige un teléfono o quiere cambiar su contraseña no puede hacerlo sin ayuda.

## What Changes

- Endpoint para editar el perfil propio (nombre completo y teléfono).
- Endpoint para editar el vehículo propio (tipo, patente, capacidad de carga), con patente única.
- Endpoint para cambiar la contraseña, exigiendo la actual.
- Restricción: no se puede modificar la capacidad ni la patente mientras haya una ruta planificada o en curso.
- UI: formularios de edición en `PanelVehiculo` y `PanelCuenta`, y formulario de cambio de contraseña.

## Capabilities

### New Capabilities
- `perfil-y-vehiculo`: edición del perfil, del vehículo propio y cambio de contraseña del chofer independiente.

### Modified Capabilities

## Impact

- Backend: `api/schemas_auth.py`, `api/routes_auth.py`, nuevo `api/routes_vehiculo.py` o equivalente, `db/crud.py`, `core/seguridad.py` (reuso de hash/verificación). Sin migración.
- Frontend: `PanelVehiculo.tsx`, `PanelCuenta.tsx`, `api/auth.ts`, `tipos/auth.ts` (espejo manual de `schemas_auth.py`), `useAuthStore.ts` (actualizar el usuario tras editar).
- No incluye recuperación de contraseña por email (fuera de alcance: no hay verificación de email).
