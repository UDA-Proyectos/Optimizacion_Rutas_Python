## 1. Backend

- [x] 1.1 Extraer los validadores de contraseña y patente de `api/schemas_auth.py` a piezas reutilizables y verificar que `tests/test_auth.py` sigue pasando
- [x] 1.2 Agregar schemas `PerfilActualizar`, `VehiculoActualizar` y `CambiarContrasena`; verificar con tests de 422 (nombre vacío, capacidad <= 0, confirmación distinta)
- [x] 1.3 Implementar `PATCH /auth/me` ignorando el email y verificar con test que el email no cambia
- [x] 1.4 Implementar `PATCH /auth/me/vehiculo` con bloqueo 409 por ruta activa y patente duplicada; verificar con tests de ambos casos y del caso feliz
- [x] 1.5 Implementar `POST /auth/cambiar-contrasena` (400 si la actual es incorrecta) y verificar con test de login con la contraseña nueva

## 2. Frontend

- [x] 2.1 Actualizar `tipos/auth.ts` (espejo de los schemas) y `api/auth.ts`; verificar con `npm run build`
- [x] 2.2 Agregar edición de vehículo a `PanelVehiculo.tsx`, quitando el texto "todavía no hay una pantalla de edición"; verificar manualmente incluido el error 409 con ruta activa
- [x] 2.3 Agregar edición de perfil y cambio de contraseña a `PanelCuenta.tsx` y refrescar `useAuthStore` con el usuario devuelto; verificar manualmente

## 3. Cierre

- [x] 3.1 Correr `uv run pytest`, `uv run ruff check .` y `npm run build`; verificar que pasan
