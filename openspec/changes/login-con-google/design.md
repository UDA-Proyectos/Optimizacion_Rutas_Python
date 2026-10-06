## Context

La autenticación actual (`api/routes_auth.py`, `core/seguridad.py`) emite un JWT propio en la cookie httpOnly `token_acceso` (`samesite=lax`), y `obtener_usuario_actual` lo revalida contra la DB en cada request. `Usuario.contrasena_hash` es `NOT NULL`. El registro de chofer independiente crea `Usuario` + `Vehiculo` juntos (`crud.crear_chofer`), y el resto de la app da por hecho que un chofer independiente tiene vehículo (planificación, `PATCH /me/vehiculo`).

En producción, front y API comparten origin (FastAPI sirve la PWA). En desarrollo, la API corre en `localhost:8000` y el front en `localhost:5174`. Las cookies se asocian al host y no al puerto, así que una cookie que pone la API en `localhost` también viaja en los pedidos del front.

Motivación y alcance: ver `proposal.md`. Comportamiento: ver `specs/login-con-google/spec.md`.

## Goals / Non-Goals

**Goals:**
- Que el resultado de entrar con Google sea exactamente la misma sesión (`token_acceso`) que el login con contraseña. Ni `obtener_usuario_actual` ni el frontend autenticado cambian.
- Que nunca exista un chofer independiente sin vehículo.
- Que no se sume ninguna dependencia al proyecto.

**Non-Goals:**
- Guardar tokens de acceso o refresh de Google. Solo se usa la identidad en el momento del ingreso; no se llama a ninguna API de Google después.
- Validar la firma del `id_token` con las claves públicas de Google (JWKS); ver la decisión 2.
- Cambiar la duración de la sesión ni agregar refresh tokens propios.

## Decisions

**1. Authorization code flow del lado del servidor, no Google Identity Services en el navegador.**
El botón es un link a `GET /api/v1/auth/google/iniciar`. La API redirige a `https://accounts.google.com/o/oauth2/v2/auth` (`scope=openid email profile`, `response_type=code`, `prompt=select_account`, `state`), y Google vuelve a `GET /api/v1/auth/google/callback`, que canjea el código en `https://oauth2.googleapis.com/token` con el `client_secret`.
- *Por qué:* no carga scripts de Google en la PWA (que ya tiene un service worker propio y CSP simple), el secreto no sale del servidor y la cookie de sesión se setea en la misma respuesta de redirección.
- *Alternativa descartada:* el botón de GIS en el front, que manda el `id_token` a la API. Obliga a cargar `accounts.google.com/gsi/client`, depende de cookies de terceros (One Tap) y exige validar la firma del token con JWKS.

**2. Leer el `id_token` sin verificar la firma, pero validando `iss`, `aud` y `exp`.**
El `id_token` llega en la respuesta del endpoint de tokens de Google, por TLS y autenticados con el `client_secret`. OIDC Core (§3.1.3.7) permite en ese caso usar la validación TLS del servidor en lugar de la firma. Se leen los claims con `jose.jwt.get_unverified_claims` y se exige: `iss` ∈ {`accounts.google.com`, `https://accounts.google.com`}, `aud == GOOGLE_CLIENT_ID`, `exp` futuro y `email_verified is True`. La validación vive en una función pura y testeable.
- *Alternativa descartada:* `google-auth` o `authlib` (dependencia nueva, el CLAUDE.md pide discutirlo) o JWKS a mano con `python-jose` (caché de claves y rotación, sin aportar seguridad en este flujo).

**3. `state` en una cookie corta, sin tabla en la DB.**
`iniciar` genera `secrets.token_urlsafe(32)` y lo guarda en la cookie `google_estado` (httpOnly, `samesite=lax`, `secure` en producción, `path=/api/v1/auth/google`, 10 minutos). El callback lo compara con `secrets.compare_digest` y la borra siempre. Con `samesite=lax` la cookie viaja igual, porque la vuelta desde Google es una navegación GET de primer nivel. No se usa `nonce`: el `state` ya ata la respuesta al navegador y el token llega por canal directo.

**4. Registro pendiente como JWT firmado en una cookie, no como fila "a medio crear".**
Si el email no existe, el callback emite un JWT con la misma `JWT_SECRET_KEY` y los claims `tipo="registro_google"`, `google_sub`, `email`, `nombre` y `exp` (15 minutos), en la cookie httpOnly `registro_google` (`path=/api/v1/auth/google`). Después redirige a `{FRONTEND_URL}/registro/google`. `GET /api/v1/auth/google/registro-pendiente` devuelve `{email, nombre_completo}` para precargar la pantalla. `POST /api/v1/auth/google/completar-registro` recibe `nombre_completo` + `DatosVehiculo` (teléfono, tipo, patente y capacidad, mismas validaciones), crea el chofer con `contrasena_hash=None` y `google_sub`, setea `token_acceso` y borra `registro_google`.
- La decodificación exige `tipo == "registro_google"`, y la de sesión no acepta ese `tipo`. Además son cookies distintas y el `sub` de sesión es un UUID de usuario, así que un token no se puede usar como el otro.
- *Alternativa descartada:* crear el usuario sin vehículo y forzar una pantalla de "completar perfil". Deja estados inválidos en la DB y obliga a cuidar cada endpoint que asume vehículo.

**5. Modelo: `contrasena_hash` nullable + `google_sub` único.**
`Usuario.google_sub: str | None` (`String(255)`, `unique=True`, índice) y `contrasena_hash: str | None`. No se agrega una tabla de identidades externas porque hay un solo proveedor. Si algún día se suma otro, se migra. `crud.crear_chofer` pasa a aceptar `contrasena_hash: str | None` y `google_sub: str | None = None`. Se agregan `crud.obtener_usuario_por_google_sub` y `crud.vincular_google`.

**6. Búsqueda y vínculo en el callback.**
Primero se busca por `google_sub`, después por email sin distinguir mayúsculas (`func.lower(Usuario.email) == email.lower()`; Google devuelve el email en minúsculas y las cuentas viejas pueden tener mayúsculas). Si el usuario encontrado por email ya tiene un `google_sub` distinto, se rechaza (`cuenta_vinculada_otra`). Si está `activo=False`, se rechaza (`cuenta_inactiva`). Solo se vincula con `email_verified`.

**7. Errores como redirección con código, no como JSON.** El flujo vive en su propio router (`api/routes_google.py`) y cada falla levanta `ErrorGoogle(codigo)`, que el callback traduce en un único lugar.
El callback es una navegación del navegador, así que todo error termina en `302 → {FRONTEND_URL}/login?error_google=<codigo>`, con códigos `no_disponible`, `cancelado`, `estado_invalido`, `fallo_google`, `email_no_verificado`, `cuenta_inactiva` y `cuenta_vinculada_otra`. El frontend los traduce a mensajes en español. Los fallos de red o de Google se loguean con `logger.exception` y nunca se exponen. Los endpoints JSON (`registro-pendiente` y `completar-registro`) siguen la convención del proyecto: 401 sin registro pendiente válido, y 409 o 422 como el registro con email.

**8. Configuración.**
En `Settings`: `google_client_id: str | None = None`, `google_client_secret: str | None = None`, `google_redirect_uri: str | None = None` (si falta, se usa `f"{frontend_url}/api/v1/auth/google/callback"`, que es correcto en producción por el mismo origin; en desarrollo hay que poner `http://localhost:8000/api/v1/auth/google/callback`) y `google_timeout_segundos: float = 10`. Google está habilitado si `client_id` y `client_secret` están presentes. `GET /api/v1/auth/proveedores` → `{"google": bool}`. Las URLs de autorización y tokens de Google son constantes del módulo `services/google_oauth.py`: son endpoints fijos del proveedor, no algo que se configure por entorno.

**9. Frontend.**
El botón "Continuar con Google" es un `<a href={`${BASE_URL}/api/v1/auth/google/iniciar`}>` (navegación completa, no `fetch`), y se muestra en `Login` y en `Registro` solo si `GET /auth/proveedores` dice `google: true`. Página nueva `CompletarRegistroGoogle` en la ruta pública `/registro/google`: precarga con `registro-pendiente`, reusa `CamposVehiculo` y, si recibe 401, vuelve a `/login?error_google=registro_vencido`. `Login` lee `error_google` de la query y muestra el mensaje. `UsuarioPublico.tiene_contrasena` (propiedad del modelo) se espeja en `tipos/auth.ts`, y `PanelCuenta` oculta `FormularioCambiarContrasena` cuando es `false`.

## Risks / Trade-offs

- [Vincular por email le da acceso a la cuenta a quien controle ese email en Google] → Solo se vincula con `email_verified=true`, que Google garantiza. Es el mismo modelo de confianza que una recuperación de contraseña por email, que es la práctica estándar.
- [Una cuenta creada con Google no puede entrar si pierde el acceso a Google, y no puede definir contraseña] → Aceptado por ahora (fuera de alcance, ver proposal). Queda documentado en CLAUDE.md §9 como gap.
- [La pantalla de consentimiento de Google en modo "Testing" solo deja entrar a usuarios de prueba cargados a mano] → Paso operativo: publicar la app OAuth en Google Cloud (con scopes básicos no requiere verificación de Google). Va en las instrucciones de despliegue.
- [El `redirect_uri` tiene que coincidir carácter por carácter con el registrado en Google] → `GOOGLE_REDIRECT_URI` explícito para desarrollo y el fallback derivado de `FRONTEND_URL` para producción, documentados en `.env.example` y README.
- [La cookie de registro pendiente podría robarse si hay XSS] → Es httpOnly, de 15 minutos y con path restringido, y solo permite crear una cuenta para ese email, no entrar a una existente.
- [No verificar la firma del `id_token`] → Válido solo porque el token llega directo del endpoint de tokens por TLS. Si en el futuro llegara un `id_token` desde el navegador, habría que verificar la firma con JWKS. Se deja un comentario en el código.

## Migration Plan

1. Migración de Alembic: `ALTER usuarios.contrasena_hash DROP NOT NULL` y columna `google_sub` + unique constraint (nombre según la naming convention de `db/base.py`). No toca datos existentes. El downgrade elimina `google_sub` y solo puede restaurar `NOT NULL` si no hay usuarios sin contraseña; si los hay, el downgrade falla de forma explícita.
2. El deploy en Railway corre `alembic upgrade head` al arrancar (ya está así en el `Dockerfile`).
3. Mientras no se carguen `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET`, el botón no aparece y todo sigue igual. Activar la función consiste solo en cargar esas dos variables (y opcionalmente `GOOGLE_REDIRECT_URI`) en Railway.
4. Rollback funcional: borrar las variables. Las cuentas creadas con Google quedan sin poder entrar hasta que se reactive.
