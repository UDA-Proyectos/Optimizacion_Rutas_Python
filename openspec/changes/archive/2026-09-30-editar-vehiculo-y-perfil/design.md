## Context

`Usuario.vehiculo` devuelve el primer elemento de `usuario.vehiculos`; `Vehiculo.patente` es única a nivel de base. El registro ya valida contraseña y patente (`schemas_auth.py`, `routes_auth.py`). Hay un espejo manual de esos schemas en `frontend/src/tipos/auth.ts`. Ver proposal.md para la motivación.

## Goals / Non-Goals

**Goals:**
- Edición parcial (PATCH) reutilizando validaciones del registro.
- Bloquear cambios que invaliden una ruta ya planificada.

**Non-Goals:**
- Recuperación de contraseña por email, verificación de email, cambio de email.
- Historial de vehículos o múltiples vehículos por chofer.
- Cerrar otras sesiones al cambiar la contraseña (no hay refresh tokens ni lista de sesiones).

## Decisions

- **Rutas**: `PATCH /api/v1/auth/me` (perfil), `PATCH /api/v1/auth/me/vehiculo` (vehículo), `POST /api/v1/auth/cambiar-contrasena`. Alternativa: router `/vehiculos`; se prefiere colgarlo de `/me` porque el chofer solo tiene un vehículo y no hay id que exponer.
- **Reutilizar los validadores del registro** (extraer a funciones/tipos compartidos en `schemas_auth.py`) para no duplicar reglas de patente y contraseña.
- **Bloqueo por ruta activa** con `crud.obtener_ruta_activa` (planificada/en_curso); solo cambian capacidad y patente. Tipo de vehículo y datos de perfil se pueden editar siempre, porque no alteran el plan.
- **Patente duplicada**: capturar `IntegrityError`/consulta previa y traducir a 409, igual que el registro.
- **Frontend**: tras un PATCH exitoso se actualiza `useAuthStore` con el usuario devuelto (sin `localStorage`), y `tipos/auth.ts` se actualiza a mano junto con los schemas.

## Risks / Trade-offs

- [Carrera entre validar patente y guardar] → confiar en la restricción única de la base y manejar el `IntegrityError`.
- [Cambiar contraseña no invalida el JWT vigente] → se documenta como limitación conocida; el token expira a los 7 días.
