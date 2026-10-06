## 1. Modelo y migración

- [x] 1.1 En `db/modelos.py`, hacer `Usuario.contrasena_hash` nullable, agregar `google_sub` (`String(255)`, único, indexado) y la propiedad `tiene_contrasena`; verificar que `uv run ruff check .` pasa
- [x] 1.2 Generar la migración con `uv run alembic revision --autogenerate -m "login con google"`, revisarla a mano (unique constraint con la naming convention, downgrade que falle de forma explícita si hay usuarios sin contraseña) y verificar con `uv run alembic upgrade head` seguido de `uv run alembic downgrade -1` y `upgrade head` en la DB local
- [x] 1.3 En `db/crud.py`, aceptar `contrasena_hash: str | None` y `google_sub` en `crear_chofer`, y agregar `obtener_usuario_por_google_sub`, `obtener_usuario_por_email_sin_mayusculas` y `vincular_google`; verificar con los tests del grupo 4

## 2. Configuración y servicio de Google

- [x] 2.1 Agregar a `core/config.py` `google_client_id`, `google_client_secret`, `google_redirect_uri` (con el fallback derivado de `frontend_url`) y `google_timeout_segundos`, más una propiedad `google_habilitado`; documentarlos en `.env.example`; verificar que la app arranca sin esas variables
- [x] 2.2 Crear `services/google_oauth.py` con `construir_url_autorizacion(estado)`, `intercambiar_codigo(codigo) -> IdentidadGoogle` (requests, timeout desde settings) y la función pura `validar_claims_id_token(claims, client_id, ahora)` (`iss`, `aud`, `exp`, `email_verified`); verificar con tests unitarios de la validación (emisor inválido, audiencia distinta, vencido, email no verificado, caso válido) sin red
- [x] 2.3 En `core/seguridad.py`, agregar `crear_token_registro_google` y `decodificar_token_registro_google` (claim `tipo="registro_google"`, 15 minutos) y hacer que el token de sesión rechace ese `tipo`; verificar con un test de que un token no se acepta como el otro

## 3. Endpoints

- [x] 3.1 Agregar `GET /api/v1/auth/proveedores` y `GET /api/v1/auth/google/iniciar` (cookie `google_estado`, redirección a Google, o `no_disponible` si está deshabilitado); verificar con tests de ambos estados de configuración
- [x] 3.2 Agregar `GET /api/v1/auth/google/callback` según las decisiones 6 y 7 del diseño (estado, cancelación, fallo de Google, email no verificado, vínculo existente, vínculo por email, cuenta vinculada a otra identidad, inactiva, email nuevo → cookie `registro_google`); verificar con un test por escenario del spec mockeando `intercambiar_codigo`
- [x] 3.3 Agregar `GET /api/v1/auth/google/registro-pendiente` y `POST /api/v1/auth/google/completar-registro` (schema con `nombre_completo` + `DatosVehiculo`, reusando `_verificar_patente_disponible` y `_crear_cuenta`); verificar con tests de alta correcta (crea chofer con vehículo, sesión iniciada, cookie pendiente borrada), 401 sin cookie o vencida, 409 por patente o email y 422
- [x] 3.4 En `POST /login`, rechazar con 401 a los usuarios sin contraseña; en `POST /cambiar-contrasena`, responder 400 con el mensaje de cuenta de Google; agregar `tiene_contrasena` a `UsuarioPublico`; verificar con tests (en `test_google_auth.py`, más `tiene_contrasena` en `test_auth.py`)

## 4. Tests del backend

- [x] 4.1 Crear `tests/test_google_auth.py` con fixtures que activen Google en `settings` y mockeen `intercambiar_codigo`, cubriendo todos los escenarios de `specs/login-con-google/spec.md`; verificar que `uv run pytest tests/test_google_auth.py` pasa sin acceso a la red

## 5. Frontend

- [x] 5.1 Actualizar `tipos/auth.ts` (`tiene_contrasena`, proveedores, registro pendiente, completar registro) y `api/auth.ts` (`obtenerProveedores`, `obtenerRegistroGooglePendiente`, `completarRegistroGoogle`) y exportar `BASE_URL` desde `api/cliente.ts`; verificar con `npm run build`
- [x] 5.2 Crear el componente `BotonGoogle` (link a `/api/v1/auth/google/iniciar`, visible solo si `google: true`) y sumarlo a `Login.tsx` y `Registro.tsx`; mostrar en `Login` el mensaje en español de cada `error_google`; verificar con `npm run build` y manualmente con y sin las variables de Google
- [x] 5.3 Crear la página `CompletarRegistroGoogle` en la ruta pública `/registro/google` (precarga nombre y email, email no editable, reusa `CamposVehiculo`, y con 401 vuelve a `/login?error_google=registro_vencido`); verificar manualmente el alta completa en desarrollo
- [x] 5.4 En `PanelCuenta.tsx`, ocultar `FormularioCambiarContrasena` cuando `tiene_contrasena` es `false`; verificar manualmente con una cuenta creada con Google

## 6. Documentación y cierre

- [x] 6.1 Actualizar README (sección de deploy: crear el cliente OAuth en Google Cloud, URI de redirección de producción y desarrollo, publicar la pantalla de consentimiento, variables en Railway) y CLAUDE.md (§6 configuración, §10 endpoints y modelo, §9 gap "cuentas de Google sin contraseña"); verificar releyendo que coinciden con lo implementado
- [x] 6.2 Correr `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, y en `frontend/` `npm run build`, `npm run lint` y `npm test`; verificar que todo pasa
- [ ] 6.3 Probar de punta a punta en desarrollo con un cliente OAuth real (alta nueva, segundo ingreso, vínculo con una cuenta de email existente y cancelación en Google); verificar que cada caso termina como dice el spec
