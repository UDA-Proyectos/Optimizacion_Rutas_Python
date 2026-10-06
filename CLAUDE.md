# CLAUDE.md

Guía de arquitectura, stack y convenciones para trabajar en este repo. Léelo antes de tocar código.

## 1. Qué es este proyecto

Motor de optimización de rutas (VRP) para empresas de distribución del Gran Mendoza. Es el prototipo de software del paper *"Optimización de rutas para empresas de distribución: un enfoque computacional"* (CACIC 2026, Grupo 8 — Martinez, Sallenave, Quevedo, Fermentini, Méndez-Garabetti, Universidad del Aconcagua).

La idea central del paper: no reinventar el algoritmo de optimización, sino integrar librerías de alto rendimiento (Google OR-Tools) con datos de tránsito reales (OSRM) detrás de una API backend desacoplada, y evaluar esa integración contra las restricciones operativas y la topología real del Gran Mendoza. El aporte del proyecto no es el algoritmo en sí, sino su adaptación y validación empírica a ese contexto.

Resuelve dos variantes del problema:
- **CVRP** (Capacitated VRP): rutas respetando la capacidad de carga de cada vehículo.
- **VRPTW** (VRP with Time Windows): CVRP + ventanas horarias por cliente y depósito, con tiempo de servicio por parada.

**Evolución del alcance**: además del motor VRP (el aporte académico del paper), el proyecto es una app web PWA real para choferes de reparto — con cuentas de usuario, empresas de distribución que gestionan flotas de choferes, y (a futuro) planes de suscripción. El motor VRP y su validación empírica siguen siendo el núcleo del paper; la capa de cuentas/auth/frontend es la plataforma que lo pone en manos de usuarios reales. Ver §10 y §11.

**Estado actual**: el motor VRP (API + solver + benchmarks) es un prototipo funcional, con tests del solver y del cliente OSRM. Están implementados: las fundaciones (`uv`, `core/config.py`, Docker para Postgres, `pytest`, `ruff`), el sistema de autenticación, y el flujo completo del chofer independiente (libreta de lugares, armado de ruta CVRP/VRPTW, ejecución parada por parada con fallos/saltos/incidencias, resumen de cierre, historial, edición de perfil y vehículo, modo offline de solo lectura y ubicación del dispositivo) — ver §10 y §11. Sigue pendiente: generalizar el solver de benchmarks (ítem 5 del roadmap), PyVRP y el dataset del Gran Mendoza (ítems 8-9), y todo lo de empresa (§10, "Fuera de alcance").

**Especificaciones y cambios**: el trabajo nuevo se planifica con **OpenSpec** (`openspec/`) — ver §12.

## 2. Stack tecnológico

| Capa | Tecnología | Notas |
|---|---|---|
| Lenguaje | Python 3.12 | |
| Gestión de entorno/dependencias | **uv** | `pyproject.toml` + `uv.lock`. Reemplaza pip/venv sueltos. |
| API | **FastAPI** + Pydantic v2 | Único framework web del proyecto. |
| Servidor ASGI | uvicorn | |
| Optimización (core) | **Google OR-Tools** (`ortools.constraint_solver`) | Motor principal de ruteo. |
| Comparación empírica | **PyVRP** | Heurística constructiva de referencia para medir gap contra OR-Tools (pedido por el paper, Sección 4.3). Pendiente. |
| Datos de tránsito | **OSRM** (perfil `driving`) | Matriz de distancias (metros) y tiempos (segundos) reales, no euclidianas. Servidor demo público por defecto, o instancia propia en Docker (§7). |
| Contenedores | Docker + docker-compose | Postgres, y opcionalmente OSRM propio (profile `osrm`). |
| Config | **pydantic-settings** + `.env` | Nada de URLs o parámetros hardcodeados. |
| Tests (backend) | **pytest** | Contra una DB Postgres de test separada; `tests/test_solver.py` y `tests/test_osrm_client.py` no tocan la red. |
| Tests (frontend) | `node --test` | Sin framework: `frontend/pruebas/*.test.mjs` con el type stripping de Node, solo para utilidades puras. Hoy cubre `googleMaps.ts`. |
| Lint/formato | **ruff** (backend), **oxlint** (frontend) | Config de ruff en `pyproject.toml`. `alembic/versions/` excluido (migraciones autogeneradas). |
| Base de datos | **PostgreSQL** (vía Docker) | Cuentas, lugares, rutas, incidencias. El motor VRP puro (`/api/v1/optimizar`) sigue siendo stateless. |
| ORM / migraciones | **SQLAlchemy 2.0** (sync) + **Alembic** | Sync, no async — consistente con el resto del backend (OR-Tools/OSRM ya son sync). |
| Auth | **passlib[bcrypt]** + **python-jose** | Hash de contraseñas + JWT firmado en cookie httpOnly (no localStorage). |
| Frontend | **React 19 + Vite + TypeScript** + **Tailwind CSS v4** | Monorepo en `frontend/`. |
| Estado global (frontend) | **Zustand** | Sin `persist` — la sesión se re-hidrata siempre desde `GET /api/v1/auth/me` (única excepción: abrir la app sin red, §11). |
| Ruteo (frontend) | **react-router-dom** | |
| Mapas | **Leaflet** + OpenStreetMap | Sin API key. |
| PWA | Service worker propio (`frontend/public/sw.js`) + `manifest.webmanifest` | Sin `vite-plugin-pwa` ni Workbox: sumar una librería requiere discutirlo antes. |
| Especificaciones | **OpenSpec** | `openspec/` (specs, changes, config). |

No uses otras librerías de optimización, otro framework web, otro ORM, ni otro gestor de paquetes (backend o frontend) sin discutirlo antes — el stack ya está decidido.

## 3. Arquitectura (estado real)

```
main.py                       # entrypoint: crea la app FastAPI, CORS, monta routers
core/
  config.py                   # Settings (pydantic-settings): OSRM, solver, DATABASE_URL, JWT_*, frontend_url
  seguridad.py                 # hash de contraseñas (passlib) + crear/decodificar JWT (python-jose)
db/
  base.py                      # Base declarativa SQLAlchemy + naming convention (constraints estables en Alembic)
  sesion.py                    # engine, SessionLocal, get_db()
  modelos.py                   # Empresa, Usuario, CodigoInvitacion, Vehiculo, Deposito, Cliente, Ruta, ParadaRuta,
                                # PruebaEntrega, Incidencia (+ DuenioMixin/Duenio — dueño = empresa o chofer indep.)
  crud.py                      # funciones de acceso a datos (crear_*, obtener_*, listar_*), scoping por Duenio
api/
  schemas.py                   # Cliente, Deposito, Vehiculo, VentanaHoraria, Coordenada, PeticionRutas (VRP, stateless)
  routes.py                    # POST /api/v1/optimizar (motor VRP puro, sin persistencia — ver §5)
  validaciones.py               # reglas compartidas por varios schemas (ej. ventana horaria completa y ordenada)
  schemas_auth.py / routes_auth.py     # registro/login/me/invitaciones/perfil/vehículo/contraseña (ver §10)
  routes_google.py               # login con Google: iniciar/callback/registro pendiente (ver §10)
  schemas_clientes.py / routes_clientes.py     # CRUD de Cliente ("lugares" guardados) — ver §11 (`GET /rutas?fecha=`, `/rutas/{id}`)
  schemas_depositos.py / routes_depositos.py   # CRUD de Deposito — ver §11
  schemas_rutas.py / routes_rutas.py           # optimizar/confirmar/activa/paradas/historial — ver §11
  schemas_incidencias.py / routes_incidencias.py   # reporte, listado, filtro por estado y resolución — ver §11
  schemas_entregas_pendientes.py / routes_entregas_pendientes.py   # entregas reprogramadas — ver §11
  schemas_geocoding.py / routes_geocoding.py   # proxy de geocoding (Nominatim): inverso y búsqueda — ver §11
  dependencies.py                # get_db, obtener_usuario_actual, requiere_admin, requiere_chofer_independiente
routing/
  solver.py                    # resolver_ruteo(): el modelo OR-Tools (lee settings.solver_time_limit_segundos);
                                # valida entradas y levanta ValueError si son inconsistentes entre sí
  planificador.py              # planificar_ruta(): arma el problema desde Cliente/Vehiculo/Deposito de un usuario
                                # y llama a resolver_ruteo — compartido por /rutas/optimizar y /rutas/confirmar
services/
  osrm_client.py                # obtener_matriz_osrm() / obtener_geometria_osrm(): URL desde settings.osrm_base_url
  nominatim_client.py           # geocodificar_inverso() y búsqueda: URL desde settings.nominatim_base_url
  google_oauth.py               # login con Google: URL de autorización, canje del código y validación del id_token
scripts/
  preparar_osrm.py              # baja las calles del Gran Mendoza (Overpass, por teselas) y prepara los datos de OSRM
  benchmark_solomon.py          # benchmark VRPTW — TODAVÍA duplica lógica de routing/solver.py (ver §9)
  benchmark_uchoa.py            # benchmark CVRP — ídem
  compare_pyvrp.py              # comparación OR-Tools vs PyVRP (planificado, roadmap ítem 8)
  generar_dataset_mendoza.py    # dataset sintético georreferenciado (planificado, roadmap ítem 9)
data/
  solomon/                      # instancias VRPTW (Solomon), ya existe
  uchoa/                        # instancias CVRP (Uchoa et al.), ya existe
  osrm/                         # datos preparados de OSRM (gitignored, regenerables)
  mendoza/                      # dataset sintético del Gran Mendoza (planificado)
alembic/
  env.py                        # configurado con settings.database_url + metadata de db.modelos
  versions/                     # migraciones — excluidas de ruff, no reescribir su estilo a mano
tests/
  conftest.py                   # DB Postgres de test separada (sufijo _test), TestClient con get_db overrideado,
                                 # payload_chofer(), y helpers/fixtures compartidos para armar choferes, lugares y
                                 # rutas (osrm_falso, armar_chofer_con_lugares, iniciar_ruta_con_paradas, ...)
  test_auth.py / test_perfil.py / test_clientes.py / test_depositos.py / test_rutas.py / test_resumen.py /
  test_incidencias.py / test_entregas_pendientes.py / test_geocoding.py / test_optimizar_vrp.py /
  test_google_auth.py (canje con Google mockeado) /
  test_solver.py / test_osrm_client.py
                                 # los que arman rutas mockean OSRM con una matriz sintética con floats — no
                                 # dependen del servidor OSRM real
frontend/                       # PWA React+Vite+TS — ver §10, §11
openspec/                       # specs, changes y config de OpenSpec — ver §12
docker-compose.yml              # servicio postgres, y osrm (profile `osrm`, ver §7)
pyproject.toml / uv.lock
.env.example / .env             # .env gitignored
```

Todo lo de arriba existe y funciona (`uv sync && docker compose up -d postgres && uv run alembic upgrade head && uv run pytest` corre en verde). Lo que falta del roadmap original: generalizar el solver para benchmarks (ítem 5), `pyvrp`/dataset Mendoza (ítems 8-9).

## 4. Convenciones de código

- **Idioma: español en todo.** Nombres de funciones, variables, campos de modelos Pydantic, claves de los JSON de request/response, y comentarios van en español (ej. `resolver_ruteo`, `matriz_distancias`, `carga_total`, `demanda_carga`). Es el estado actual del código y se mantiene así — no migres a inglés ni mezcles.
- **snake_case** para funciones/variables, **PascalCase** para modelos Pydantic.
- **Type hints completos** en código nuevo: preferí `list[list[int]]` / `List[int]` en vez de `list` a secas (el código viejo usa hints laxos; no hace falta reescribirlo retroactivamente, pero el código nuevo sí debe llevarlos).
- **Comentarios**: solo cuando expliquen un *por qué* no obvio (una convención OSRM rara, un valor mágico, una restricción del solver). No documentes *qué* hace el código si el nombre ya lo dice. Nada de docstrings largos — una línea si aporta.
- **ruff** es la única herramienta de lint/formato del backend (§8). No introduzcas black/flake8/isort en paralelo.
- Los benchmarks y el solver de producción deben compartir la misma lógica de modelado OR-Tools (ver gap en §9) — no dupliques el armado del `RoutingModel` en un script nuevo si `routing/solver.py` ya lo resuelve.
- **Errores HTTP**: un problema sin solución o una entrada inválida es 400/422; el 500 es solo para fallos inesperados y **no** expone el detalle de la excepción (va al log). No metas un `HTTPException` intencional dentro de un `try` con `except Exception`: se convierte en 500.
- **Frontend (`frontend/`)**: mismo idioma español en nombres de carpetas, componentes, funciones y variables (`FormularioLogin`, `useAuthStore`, `registrarChoferIndependiente`, `cargarSesion`). PascalCase para componentes React, camelCase para el resto — igual que el backend, no mezclar inglés salvo términos propios de la librería (`props`, `state`, hooks de React/Zustand). TypeScript con tipos completos (`tipos/*.ts` espeja los schemas Pydantic — si cambia uno, actualizar el otro a mano, no hay generación automática todavía).

## 5. Dominio del problema (semántica ya establecida en el código)

Para no reinventar convenciones al tocar `routing/solver.py` o `services/osrm_client.py`:

- **Nodo 0 = depósito**, siempre. El resto de los índices son clientes en el orden en que llegan en `clientes`.
- OSRM espera coordenadas como `"longitud,latitud"` (al revés que la convención `lat,lon` usada en los schemas Pydantic) — ver `services/osrm_client.py`.
- La **matriz de distancias** que devuelve OSRM está en **metros**; es la que se usa directamente como costo de arco en OR-Tools (`SetArcCostEvaluatorOfAllVehicles`).
- La **matriz de tiempos** que devuelve OSRM está en **segundos**; el solver la convierte a **minutos** para la dimensión de tiempo.
- **Ventanas horarias** (`VentanaHoraria.inicio` / `.fin`) se expresan en **minuto del día** (ej. 480 = 8:00 AM), no en formato hora. Una ventana es completa (inicio y fin) y el fin es posterior al inicio (`api/validaciones.py`).
- Dimensión `'Capacidad'`: sin holgura (slack=0), capacidad por vehículo tomada de `Vehiculo.capacidad`.
- Dimensión `'Tiempo'` (solo VRPTW): holgura de 120 min (tiempo máximo de espera si el vehículo llega antes de que abra el cliente), tope de 1440 min por vehículo (24 hs). El tiempo de servicio de cada nodo se suma al traslado. El depósito le impone su ventana horaria a la salida y el regreso de cada vehículo.
- Búsqueda: `PATH_CHEAPEST_ARC` como estrategia inicial + `GUIDED_LOCAL_SEARCH` como metaheurística, con `time_limit.seconds` tomado de `settings.solver_time_limit_segundos` (5s por defecto en el solver de producción; los benchmarks siguen con 60s propios — ver §9).
- `resolver_ruteo` valida que matrices, demandas, tiempos y ventanas sean coherentes entre sí (`ValueError` si no). Si el solver no encuentra solución factible devuelve `{"estado": "Fallo", "mensaje": ...}` en vez de tirar una excepción — el endpoint lo traduce a HTTP 400.

## 6. Configuración (`core/config.py`, implementado)

Clase `Settings` (`pydantic-settings`), leída desde `.env` (ver `.env.example` versionado). Variables actuales:

- `OSRM_BASE_URL` — por defecto el servidor demo público de OSRM (`http://router.project-osrm.org`, con rate-limiting); para usar una instancia propia, `http://localhost:5001` (ver §7). `OSRM_PORT` solo lo lee `docker-compose.yml`.
- `SOLVER_TIME_LIMIT_SEGUNDOS` — default 5. Los benchmarks siguen con su propio valor hardcodeado en 60 (no leen `Settings` — ver gap en §9, roadmap ítem 5 sin resolver).
- `DATABASE_URL` — sin default, la app falla al arrancar si falta (fail-fast). Formato `postgresql+psycopg://...`.
- `JWT_SECRET_KEY` — sin default, ídem. `JWT_ALGORITHM` (default `HS256`), `JWT_EXPIRE_MINUTES` (default 10080 = 7 días).
- `ENTORNO` (`desarrollo` | `produccion`) — controla el flag `secure` de la cookie de sesión.
- `FRONTEND_URL` — usado en `CORSMiddleware` (`allow_origins`), debe matchear el origin real del frontend (`http://localhost:5174`).
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — opcionales; sin ambos el login con Google queda deshabilitado (`GET /api/v1/auth/proveedores` → `google: false` y el botón no aparece). `GOOGLE_REDIRECT_URI` tiene que coincidir con una URI autorizada en Google Cloud; si falta se usa `FRONTEND_URL` + `/api/v1/auth/google/callback` (correcto en producción, donde la API sirve el frontend; en desarrollo va `http://localhost:8000/...`). `GOOGLE_TIMEOUT_SEGUNDOS` (default 10).
- `NOMINATIM_BASE_URL` — default `https://nominatim.openstreetmap.org` (servidor público, sin API key). Usado solo para geocoding (pin del mapa → texto de dirección, y búsqueda de direcciones) en el alta de `Cliente`/`Deposito`; nunca para el motor VRP en sí.

No hardcodees URLs, timeouts ni límites nuevos — si es un valor que alguien podría querer cambiar sin tocar código, va en `Settings`.

## 7. Cómo correr el proyecto

```bash
# --- Backend ---
uv sync                                  # instala dependencias desde pyproject.toml/uv.lock
docker compose up -d postgres            # levanta Postgres
uv run alembic upgrade head              # aplica las migraciones
uv run uvicorn main:app --reload         # levanta la API en http://localhost:8000
uv run pytest                            # corre la suite de tests
uv run ruff check . && uv run ruff format .   # lint + formato
uv run python scripts/benchmark_solomon.py    # benchmark VRPTW
uv run python scripts/benchmark_uchoa.py      # benchmark CVRP
uv run python scripts/compare_pyvrp.py        # comparación OR-Tools vs PyVRP (planificado)

# --- OSRM propio (opcional; por defecto se usa el servidor demo público) ---
uv run python scripts/preparar_osrm.py   # una sola vez: baja las calles del Gran Mendoza y las procesa
docker compose --profile osrm up -d osrm # http://localhost:5001 — apuntá OSRM_BASE_URL ahí en tu .env

# --- Frontend ---
cd frontend
npm install
npm run dev                              # http://localhost:5174 (puerto fijo, ver vite.config.ts)
npm run build && npm run lint && npm test
```

El service worker solo se registra en el build de producción (`npm run build` + `npx vite preview --port 5174 --strictPort`); en desarrollo la app desregistra cualquier worker previo del mismo origen para que el hot reload no sirva módulos viejos desde la caché.

Nueva migración tras cambiar `db/modelos.py`: `uv run alembic revision --autogenerate -m "descripción"` y revisar el archivo generado a mano antes de `alembic upgrade head` (Alembic no siempre detecta bien cambios de tipo/constraint).

## 8. Roadmap accionable (motor VRP / paper)

Basado en las secciones 4.3 y 5 del paper (dataset, validación, métricas empíricas) más la deuda técnica actual.

1. ~~Migrar a `uv`~~ ✅ hecho.
2. ~~Reestructurar `main.py` en `api/`/`core/`~~ ✅ hecho.
3. ~~Introducir `core/config.py`~~ ✅ hecho (ver §6).
4. ~~Self-hostear OSRM~~ ✅ hecho: servicio `osrm` (profile) + `scripts/preparar_osrm.py`, con el mapa recortado al Gran Mendoza. El default de `OSRM_BASE_URL` sigue siendo el demo público; la instancia propia es opt-in (ver §7).
5. Generalizar `routing/solver.py` para que reciba matrices de cualquier origen (OSRM real o distancias euclidianas de benchmarks) sin duplicar el armado del `RoutingModel`; migrar `scripts/benchmark_solomon.py` y `scripts/benchmark_uchoa.py` para que lo importen en vez de reimplementarlo. **Pendiente**, sigue siendo el gap original.
6. ~~Agregar `pytest`~~ ✅ hecho: auth, perfil, lugares, depósitos, rutas, resumen, incidencias, geocoding, `/optimizar`, solver y cliente OSRM.
7. ~~Adoptar `ruff`~~ ✅ hecho, configurado en `pyproject.toml` (excluye `alembic/versions/`, ignora `B008` por el patrón `Depends()` de FastAPI).
8. Agregar `pyvrp` y `scripts/compare_pyvrp.py`. **Pendiente**.
9. Generar el dataset sintético georreferenciado del Gran Mendoza (`scripts/generar_dataset_mendoza.py`). **Pendiente**.
10. Recolectar métricas empíricas exhaustivas (Uchoa, Solomon/Homberger, Mendoza sintético) documentando hardware. **Pendiente**.

## 9. Gaps conocidos (no "arreglar" por sorpresa sin avisar)

- `scripts/benchmark_solomon.py` y `scripts/benchmark_uchoa.py` **duplican** la lógica de modelado de `routing/solver.py` con parámetros de búsqueda propios (estrategias iniciales distintas, `time_limit` de 60s vs 5s, escalado de distancias por separado) y **no leen `core/config.py`**. Se resuelve en el ítem 5 del roadmap — no es un bug, es deuda técnica ya identificada.
- `OSRM_BASE_URL` apunta por defecto al **servidor demo público** de OSRM, que tiene rate-limiting y no está pensado para uso intensivo/producción. La alternativa (OSRM propio) existe pero cubre solo el recuadro del Gran Mendoza y hay que prepararla a mano (§7).
- No hay dataset del Gran Mendoza todavía — el título de la API ("Gran Mendoza") es aspiracional hasta el ítem 9 del roadmap.
- No hay `response_model` tipado en el endpoint `/api/v1/optimizar` (devuelve un `dict` plano). No es prioritario resolverlo fuera del roadmap salvo que se decida explícitamente.
- `frontend/src/paginas/PestanaInicio.tsx` (pestaña "Inicio" de la vista clásica, usada por admin y choferes de empresa) es anterior al panel de escritorio del chofer independiente: solo sabe completar paradas, no registra llegada, ni falla/saltea, ni tiene resumen de cierre.
- El modo offline es de **solo lectura**: las acciones que escriben se bloquean sin conexión (no se encolan, no todas son idempotentes). Solo la ruta activa y el perfil se guardan localmente; "Mis lugares", historial e incidencias no.
- `en_riesgo` (ventana por vencer) se calcula sobre el plan y la hora del reloj, no se recalcula con la llegada real, y el resumen informa la distancia *planificada*: no se registra el recorrido real del vehículo.
- Las cuentas creadas con Google no tienen contraseña (`contrasena_hash` NULL): no pueden definir una ni desvincular Google, y si pierden el acceso a esa cuenta de Google no tienen otra forma de entrar. El registro con Google solo crea choferes independientes (no empresas ni choferes invitados).
- La sesión no invalida el JWT vigente al cambiar la contraseña (no hay refresh tokens ni lista de sesiones); expira a los 7 días.
- No hay tests automáticos de componentes de React (solo `npm run build`, `oxlint` y las pruebas de utilidades puras).

## 10. Sistema de cuentas / autenticación (implementado)

Capa para soportar la app PWA (más allá del motor VRP puro). Backend: `db/modelos.py`, `api/routes_auth.py`, `core/seguridad.py`. Frontend: `frontend/src/store/useAuthStore.ts`, `frontend/src/paginas/{Login,Registro}.tsx`.

**Modelo de cuentas**:
- `Empresa` (1) —N— `Usuario` vía `Usuario.empresa_id` (nullable). Un `Usuario` es o bien **chofer independiente** (`rol=chofer`, `empresa_id=NULL`) o **chofer de una empresa** (`rol=chofer`, `empresa_id` seteado) o **admin de una empresa** (`rol=admin`, siempre con `empresa_id`).
- Vínculo chofer↔empresa: **código de invitación de un solo uso** (`CodigoInvitacion`, 8 caracteres alfanuméricos). Lo genera un admin (`POST /api/v1/auth/invitaciones`), lo consume un chofer al registrarse (`POST /api/v1/auth/registro/chofer-invitado`); una vez usado (`usado=True`) no se puede reutilizar.
- `plan`/`fecha_fin_prueba` existen en `Empresa` y `Usuario` (modelo freemium futuro) pero **sin enforcement real todavía** — no hay billing (Stripe/MercadoPago) implementado ni planificado para esta etapa.

**Auth/sesión**: JWT (claims `sub`, `rol`, `empresa_id`, `iat`, `exp`) en cookie `httponly` + `samesite=lax`, expira a los 7 días (`JWT_EXPIRE_MINUTES`). `obtener_usuario_actual` (en `api/dependencies.py`) decodifica el token y **siempre revalida contra la DB** (no confía ciegamente en los claims), así un `activo=False` surte efecto inmediato. No hay refresh token — al expirar, re-login manual. No hay rate limiting ni bloqueo de cuenta tras intentos fallidos de login todavía, ni recuperación de contraseña por email.

**Login con Google** (`api/routes_google.py` + `services/google_oauth.py`, sin dependencias nuevas): authorization code flow del lado del servidor. `GET /google/iniciar` deja un `state` en la cookie `google_estado` y redirige a Google; `GET /google/callback` valida el `state`, canjea el código (`requests`) y lee los claims del `id_token` sin verificar firma (llega directo del endpoint de tokens por TLS; se validan `iss`, `aud`, `exp` y `email_verified`). Busca primero por `Usuario.google_sub` y después por email sin distinguir mayúsculas (vincula la cuenta existente, de cualquier rol). Si el email es nuevo **no crea el usuario**: deja un JWT corto (`tipo="registro_google"`, 15 min) en la cookie `registro_google` y redirige a `/registro/google`, donde el chofer completa teléfono y vehículo (`GET /google/registro-pendiente`, `POST /google/completar-registro`). Cada falla del callback es un `ErrorGoogle(codigo)` y vuelve a `/login?error_google=<código>`. `decodificar_token` rechaza cualquier token con `tipo`, así uno de registro nunca sirve como sesión. `UsuarioPublico.tiene_contrasena` indica si la cuenta tiene contraseña.

**Endpoints** (`/api/v1/auth`, prefijo): `POST /registro/chofer-independiente`, `POST /registro/empresa`, `POST /registro/chofer-invitado`, `POST /login`, `POST /logout`, `GET /me`, `PATCH /me` (nombre y teléfono; el email no se edita), `PATCH /me/vehiculo` (solo chofer independiente; capacidad y patente se bloquean con una ruta planificada o en curso), `POST /cambiar-contrasena` (exige la actual; 400 en cuentas de Google), `GET /proveedores`, `GET /google/iniciar`, `GET /google/callback`, `GET /google/registro-pendiente`, `POST /google/completar-registro`, `POST /invitaciones` (rol admin), `GET /invitaciones` (rol admin).

**Frontend**: `frontend/` es un proyecto Vite+React+TS separado (propio `package.json`/`node_modules`, no gestionado por `uv`). Sin `localStorage` para la sesión — el store de Zustand (`useAuthStore`) siempre re-hidrata vía `GET /me` al montar la app; **la única excepción** es abrir la app sin red: si `/me` falla por un error de red (no un 401), se usa la copia del perfil guardada en IndexedDB solo para mostrar la ruta en modo lectura (§11). Estilos: `frontend/src/estilos/` (Tailwind v4 con tokens propios) — colores/tipografía extraídos de un mockup `Active Route View.dc.html` diseñado en Claude Design. El mockup trae azul `#2E5CFF` por defecto, con violeta `#7C3AED` como una de sus 3 opciones de color de acento — esta app usa esa opción violeta como identidad (violeta primario `#7C3AED`, verde éxito `#12B76A` — constante en las 3 opciones del mockup —, `Inter`+`JetBrains Mono`). **Importante**: ese mismo proyecto de Claude Design tiene un design system separado ("Trazo", tema oscuro/verde lima, terminología de levantamiento olímpico) que **no tiene relación con esta app** — no confundirlos ni usar esos tokens.

Cualquier 401 de `fetchApi` (sesión vencida o cookie perdida) limpia `useAuthStore` y la copia local offline automáticamente — `registrarManejadorSesionExpirada` en `api/cliente.ts` evita el import circular hacia el store; `RutaProtegida` (`router.tsx`) ya redirige sola a `/login` cuando `estaAutenticado` pasa a `false`, así una sesión perdida se hace visible en vez de fallar en silencio pedido por pedido.

**Fuera de alcance todavía** (no construir por sorpresa sin que se pida explícitamente):
- Dashboard de empresa (ver/listar choferes, copiar códigos de invitación desde la UI — hoy solo existe el endpoint, se prueba por API).
- Asignación de rutas por parte de la empresa a un chofer específico (el chofer independiente ya arma y ejecuta la suya solo — ver §11 — pero un chofer de empresa todavía no recibe nada, ni de un admin ni de sí mismo).
- Prueba de Entrega (POD — el modelo `PruebaEntrega` ya existe pero sin UI ni endpoint), Mi Flota.
- Billing/suscripciones reales, verificación de email.

## 11. Libreta de direcciones, armado y ejecución de rutas (chofer independiente, implementado)

Un chofer sin empresa arma, confirma, ejecuta y cierra su propia ruta del día, sin intervención de un admin. Backend: `db/modelos.py` (`Cliente`, `Deposito`, `Ruta`, `ParadaRuta`, `Incidencia`), `api/routes_{clientes,depositos,rutas,incidencias}.py`, `routing/planificador.py`. Frontend: `frontend/src/componentes/escritorio/EscritorioChofer.tsx` (shell responsive: sidebar en escritorio, drawer en mobile), `paginas/PestanaLugares.tsx`, `componentes/rutas/*`, `componentes/historial/*`, `componentes/incidencias/*`, `componentes/vehiculo/*`, `componentes/cuenta/*`, `componentes/mapa/SelectorUbicacion.tsx`.

**Dueño de un recurso compartido** (`Cliente`, `Deposito`, y a futuro cualquier cosa con `DuenioMixin`): `Usuario.ambito_dueño` (propiedad en `db/modelos.py`, devuelve un `Duenio` — `NamedTuple` con `empresa_id`/`usuario_id`) es el único lugar que decide si un recurso nuevo pertenece a la empresa del usuario (compartido entre toda su flota) o al usuario mismo (independiente). `db/crud._condicion_dueño(modelo, duenio)` aplica ese mismo filtro como `WHERE` — nunca se trae una fila por id sin la condición de dueño adentro de la query (evita el típico bug de "traer y comparar después").

**Lugares** (`Cliente`): además de nombre, dirección y coordenadas guardan **datos habituales** — carga (kg), tiempo de servicio (0–240 min) y ventana horaria — que se precargan al armar una ruta (editables por día sin tocar el lugar). El `Deposito` puede tener ventana horaria; el chofer puede tener más de un depósito y elegir de cuál sale (por defecto, el primero).

**Selector de ubicación** (`SelectorUbicacion.tsx`, reusado por `FormularioCliente` y `FormularioDeposito`): Leaflet + tiles de OpenStreetMap (sin API key) para marcar el pin; al tocar el mapa dispara geocoding inverso contra Nominatim (`api/routes_geocoding.py` → `services/nominatim_client.py`), y también hay búsqueda de direcciones — best-effort, si Nominatim falla el chofer igual puede escribirla a mano. No confundir con el motor VRP: esto es puramente para cargar datos.

**Flujo de "armar ruta"** (`FlujoArmarRuta.tsx`):
1. Si el chofer todavía no tiene `Deposito`, primero se lo pide (`FormularioDeposito`) — es su punto de partida/llegada.
2. Selecciona qué `Cliente` visita hoy, cuánta carga (kg) y bultos lleva a cada uno, y si usa **ventanas horarias** (VRPTW) o no (CVRP). Sin ventanas horarias se mandan en `null` aunque el lugar tenga un horario habitual.
3. `POST /api/v1/rutas/optimizar` arma el problema (`routing/planificador.planificar_ruta`, que reusa `resolver_ruteo`/`obtener_matriz_osrm`) y devuelve un preview **sin persistir**: orden, distancia acumulada, ahorro contra el orden elegido, explicación y, con ventanas, la hora estimada de llegada.
4. El chofer confirma o cancela. `POST /api/v1/rutas/confirmar` vuelve a resolver el mismo problema (no persiste el preview del frontend tal cual — la única fuente de verdad es el solver) y crea `Ruta` + `ParadaRuta` (con snapshot de cada `Cliente` en ese momento).
5. Un chofer puede planificar **varias rutas por día y para otros días** (`fecha` del día local, hasta +60 días; el servidor tolera 1 día atrás por zona horaria; `nombre` opcional). Solo **una** puede estar `en_curso` a la vez (`crud.obtener_ruta_en_curso`); iniciar otra da 409, y iniciar una de un día futuro también.

**Ciclo de vida de una `Ruta`** (`api/routes_rutas.py`, bajo `/api/v1/rutas`, todo requiere `requiere_chofer_independiente` salvo donde se aclara):
- `GET /rutas?fecha=` — rutas del día (no canceladas). `PUT /rutas/{id}` — editar (solo `planificada`): vuelve a planificar, cancela la vieja (`estado=cancelada`, no se borra) y crea una nueva conservando fecha/nombre. `DELETE /rutas/{id}` — cancela (`planificada`/`en_curso`).
- `POST /rutas/{id}/iniciar` — `planificada` → `en_curso`; la primera parada pasa a `EstadoParada.en_curso`.
- Sobre la parada en curso (`/activa/paradas/{id}/…`): `llegada` (guarda `hora_real_llegada`, idempotente), `completar`, `fallar` (motivo obligatorio: cliente ausente, rechazo, dirección incorrecta, mercadería dañada u otro; crea una `Incidencia` asociada), `saltear` (manda la parada al final del recorrido y suma `veces_salteada`; 409 si es la única que queda). La ruta pasa a `completada` cuando no quedan paradas pendientes ni en curso, aunque alguna haya fallado. Ojo: una `Ruta` completada deja de ser "la ruta activa" (`obtener_ruta_en_curso` solo mira `en_curso`) — por eso el frontend usa la `Ruta` que devuelve la propia llamada en vez de volver a pedir `GET /activa`.
- `GET /activa` — la ruta `en_curso` o `null` (genérico, cualquier usuario autenticado). `GET /activa/geometria` — traza real (calles) para el mapa, vía `services/osrm_client.obtener_geometria_osrm`.
- `GET /historial` y `GET /historial/{id}` — rutas de un rango de fechas y su detalle.
- `RutaPublica.resumen` (solo si `completada`): duración real, paradas completadas/fallidas/salteadas, carga entregada, incidencias y, con ventanas, ventanas cumplidas. La distancia es la *planificada*.

**Incidencias y entregas reprogramadas** (`/api/v1/incidencias`, `/api/v1/entregas-pendientes`): el chofer reporta una incidencia (general de la ruta o sobre una parada) solo con una ruta en curso; el listado (filtrable con `?estado=pendiente|resuelta`) incluye las que se crean solas al fallar una parada. Toda incidencia nace `pendiente` y se resuelve con `POST /incidencias/{id}/resolver`: `reprogramada` (solo si viene de una parada fallida que todavía no se reprogramó) o `cerrada` (sin más acción). Reprogramar crea una `EntregaPendiente` (snapshot de lugar, carga, bultos y ventana; única por `parada_origen_id`) que `FlujoArmarRuta` ofrece **ya marcada** al armar la próxima ruta, rotulada "Reprogramada". Al confirmar o editar una ruta que contiene ese lugar pasa a `incluida` (con `ruta_id`); si esa ruta se cancela o se edita sin el lugar, vuelve a `pendiente` (`crud.cancelar_ruta`). Al marcar "No pude entregar" el frontend ofrece, tras el motivo, "Reprogramar para la próxima ruta" o "Decidir después" (`fallar` acepta `reprogramar`); desde "Incidencias" se puede hacer luego. Las incidencias anteriores al seguimiento quedaron resueltas/cerradas por la migración. Todavía no hay "retira el cliente en el depósito", cancelar la entrega, notas ni reabrir.

**Mapa de ruta activa** (`MapaRutaActiva.tsx`): traza violeta fina para el resto de la ruta y verde para el tramo en curso, un pin por parada coloreado por `estado` (gris pendiente, verde en curso —más grande y pulsante—, verde completada, rojo fallida), y —solo si el chofer lo activó— un punto azul con su posición. "Abrir navegación"/"Ir con Maps" abre `google.com/maps/dir` con coordenadas reales (sin API key ni billing); usa como origen la posición del dispositivo si está activa, y si no el depósito o la parada anterior.

**PWA, modo offline y ubicación** (`frontend/public/{sw.js,manifest.webmanifest}`, `utilidades/{registrarServiceWorker,almacenRuta}.ts`, `hooks/{useRutasDelDia,useRutaActiva,useEnLinea,useUbicacion}.ts`): la app es instalable; el service worker guarda el shell en runtime y las teselas de OSM, y nunca cachea la API. Sin conexión (dispositivo offline o servidor inalcanzable) `useRutaActiva` muestra la última ruta guardada en IndexedDB (con la hora de guardado y un aviso) y **bloquea** las acciones que escriben; al volver la señal reintenta solo. La copia local (ruta activa + perfil, sin credenciales) se borra al cerrar sesión y ante un 401. Una versión nueva del service worker queda en espera hasta que el chofer acepta el aviso "Hay una versión nueva". La posición del dispositivo se pide solo cuando el chofer toca "Usar mi ubicación", vive en el estado de React y **nunca** se envía al backend.

**Solo chofer independiente**: `api/dependencies.requiere_chofer_independiente` (403 si `usuario.empresa_id` no es `None`) protege el armado, la ejecución y el historial de rutas, las incidencias y la edición del vehículo — un chofer de empresa no puede auto-asignarse una ruta todavía (ver §10, fuera de alcance).

## 12. Flujo de trabajo con OpenSpec

El trabajo nuevo se planifica con OpenSpec: `openspec/config.yaml` resume el stack y las convenciones para que las propuestas los respeten, `openspec/changes/` tiene los cambios en curso y `openspec/specs/` las especificaciones ya consolidadas. Comandos del proyecto (Claude Code): `/opsx:propose` (crea propuesta, specs, diseño y tareas — solo planifica), `/opsx:apply <cambio>` (implementa las tareas y las va tildando), `/opsx:archive` (archiva un cambio terminado), más `/opsx:explore`, `/opsx:update` y `/opsx:sync`. `openspec validate --changes --strict` valida los artefactos. Un cambio no se considera terminado hasta que sus tareas están implementadas **y verificadas** como dice cada una.
