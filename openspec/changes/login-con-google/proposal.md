## Why

Hoy la única forma de entrar a la app es con email y contraseña. Para un chofer que la abre desde el celular, crear y recordar otra contraseña es fricción en el alta y una causa frecuente de "no puedo entrar". Con la app ya desplegada en Railway (`optirutas.up.railway.app`), sumar "Continuar con Google" baja esa barrera sin cambiar el modelo de cuentas.

## What Changes

- Nuevo flujo OAuth 2.0 / OpenID Connect con Google (authorization code, del lado del servidor): `GET /api/v1/auth/google/iniciar` redirige a Google y `GET /api/v1/auth/google/callback` recibe el código, lo canjea y deja la misma cookie de sesión JWT que el login actual.
- Si la cuenta de Google ya está vinculada, o si su email (verificado por Google) coincide con un usuario existente, se inicia sesión con ese usuario. En el segundo caso la cuenta queda vinculada a Google. Vale para cualquier rol (chofer independiente, chofer de empresa, admin).
- Si el email no existe, no se crea la cuenta enseguida: el chofer completa teléfono y vehículo en una pantalla nueva (`/registro/google`) y recién ahí se crea como **chofer independiente** (`POST /api/v1/auth/google/completar-registro`). Así nunca queda un chofer sin vehículo.
- Las cuentas creadas con Google no tienen contraseña: `Usuario.contrasena_hash` pasa a aceptar nulo y se agrega `Usuario.google_sub` (único). Con esas cuentas, el login con contraseña responde 401 igual que con datos incorrectos, y cambiar la contraseña responde 400 con un mensaje claro.
- `UsuarioPublico` suma `tiene_contrasena`, para que "Mi cuenta" oculte el formulario de cambio de contraseña cuando no aplica.
- `GET /api/v1/auth/proveedores` informa si Google está configurado. El frontend muestra el botón solo en ese caso.
- Configuración nueva en `core/config.py`: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` (opcionales: si faltan, la función queda deshabilitada) y `GOOGLE_REDIRECT_URI`.
- Frontend: botón "Continuar con Google" en Login y Registro, página `/registro/google`, mensajes de error de Google en Login, y el formulario de contraseña condicionado en "Mi cuenta".
- Sin dependencias nuevas: el canje se hace con `requests` (ya lo usan los clientes de OSRM y Nominatim) y los claims del `id_token` se leen con `python-jose`.

## Capabilities

### New Capabilities
- `login-con-google`: iniciar sesión y registrarse como chofer independiente con una cuenta de Google, vincular cuentas existentes por email verificado, y habilitar o deshabilitar la función por configuración.

### Modified Capabilities
- `perfil-y-vehiculo`: "Cambiar contraseña" contempla las cuentas sin contraseña (creadas con Google), que no pueden usar ese flujo.

## Impact

- **Backend:** `api/routes_auth.py` (rutas de Google, login y cambio de contraseña con hash nulo), `api/schemas_auth.py` (`tiene_contrasena`, schema de completar registro, proveedores), servicio nuevo `services/google_oauth.py`, `core/config.py`, `core/seguridad.py` (token corto de registro pendiente), `db/modelos.py` y `db/crud.py`.
- **Base de datos:** migración de Alembic: `usuarios.contrasena_hash` nullable y columna `usuarios.google_sub` única y nullable. Compatible con los datos actuales.
- **Frontend:** `paginas/Login.tsx`, `paginas/Registro.tsx`, página nueva de completar registro, `router.tsx`, `api/auth.ts`, `tipos/auth.ts`, `componentes/cuenta/PanelCuenta.tsx`.
- **Tests:** `tests/test_google_auth.py` nuevo, con el canje contra Google mockeado (sin red); ajustes en `test_auth.py` y `test_perfil.py`.
- **Operación (lo hace el dueño del proyecto):** crear el cliente OAuth en Google Cloud Console con las URI de redirección autorizadas (producción y `http://localhost:8000/...` en desarrollo) y cargar las variables en Railway. Hasta que no esté cargado, la app funciona igual que hoy, sin el botón.
- **Fuera de alcance:** registro de choferes invitados o de empresas con Google, desvincular Google, definir una contraseña para una cuenta creada con Google, Google One Tap y otros proveedores (Apple, Microsoft).
