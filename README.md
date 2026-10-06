# Optimización de Rutas — Gran Mendoza

Motor de optimización de rutas (VRP) para empresas de distribución del Gran
Mendoza, con una app web (PWA) para que un chofer arme, confirme y ejecute
su ruta del día. Prototipo del paper *"Optimización de rutas para empresas
de distribución: un enfoque computacional"* (CACIC 2026, Grupo 8).

## Stack

Backend: Python 3.12 + **uv** + FastAPI + Google OR-Tools (motor VRP) +
PostgreSQL (SQLAlchemy + Alembic) + OSRM (matriz de distancias/tiempos
reales). Frontend: React 19 + Vite + TypeScript + Tailwind CSS.

Arquitectura completa, convenciones y roadmap: [CLAUDE.md](CLAUDE.md).
Flujo de trabajo del equipo (ramas, PRs, CI): [CONTRIBUTING.md](CONTRIBUTING.md).

## Requisitos

- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** (instala
  y gestiona Python por vos — no hace falta instalar Python 3.12 aparte).
- **Docker Desktop** (levanta Postgres local).
- **Node.js 22+** y npm (frontend).
- **Git**.

## Instalación

```bash
git clone https://github.com/lauti-martinez1/Optimizacion_Rutas_Python.git
cd Optimizacion_Rutas_Python
```

### 1. Backend

```bash
uv sync                                  # instala Python 3.12 (si falta) + dependencias
cp .env.example .env                     # reemplazá JWT_SECRET_KEY y POSTGRES_PASSWORD por los tuyos
docker compose up -d postgres            # levanta Postgres en background
uv run alembic upgrade head              # crea las tablas
uv run pytest                            # opcional: confirma que todo compila y conecta bien
uv run uvicorn main:app --reload         # http://localhost:8000 (docs en /docs)
```

`JWT_SECRET_KEY` no tiene default (la app no arranca sin uno propio) —
generá el tuyo con:

```bash
uv run python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 2. Frontend

En otra terminal, con el backend ya corriendo:

```bash
cd frontend
npm install
cp .env.example .env                     # ya viene con el valor correcto, no hace falta tocarlo
npm run dev                              # http://localhost:5174
```

El puerto del frontend está fijo en `5174` (`vite.config.ts`, `strictPort: true`)
porque el backend solo acepta pedidos desde ese origen (`FRONTEND_URL` en tu
`.env` de la raíz) — si algo más ya está usando ese puerto, Vite va a fallar
al arrancar en vez de saltar a otro puerto en silencio.

### 3. OSRM propio (opcional)

Por defecto el backend usa el servidor demo público de OSRM
(`router.project-osrm.org`): anda sin instalar nada, pero tiene rate-limiting.
Para tener tu propio OSRM con el mapa del Gran Mendoza:

```bash
uv run python scripts/preparar_osrm.py    # una sola vez: baja las calles y las procesa
docker compose --profile osrm up -d osrm  # levanta OSRM en http://localhost:5001
```

y en tu `.env`: `OSRM_BASE_URL=http://localhost:5001` (reiniciá la API).

- **Qué hace el script**: pide a Overpass las calles del recuadro del Gran Mendoza
  (por teselas chicas, dividiendo las densas; una consulta grande da 504), las
  fusiona en `data/osrm/mendoza.osm` y corre `osrm-extract`, `osrm-partition` y
  `osrm-customize` dentro de la imagen oficial (`ghcr.io/project-osrm/osrm-backend`).
- **Requisitos**: Docker con **≥ 2 GB de RAM** asignados (el procesamiento de la
  zona por defecto usó muy poca, el pico del último paso fue de ~60 MB) y ~**60 MB**
  de disco en `data/osrm/` (mapa de ~15 MB + ~45 MB ya procesados). Lo lento es
  bajar el mapa: depende de servidores públicos (Overpass) y en la corrida de
  referencia tardó bastante por reintentos (minutos hasta ~1 hora según la
  carga). Si se corta, volvé a correr el script: reutiliza lo ya bajado.
- **No baja Argentina completa** a propósito: son cientos de MB y `osrm-extract`
  necesita varios GB de RAM. Con una máquina holgada, `--extracto ruta/al.osm.pbf`
  usa un extracto propio, y `--bbox min_lon,min_lat,max_lon,max_lat` cambia la zona.
- `data/osrm/` está en `.gitignore`: es pesado y se regenera con el script.

## Verificar que quedó todo andando

1. Abrí `http://localhost:5174/registro` y creá una cuenta de chofer independiente.
2. Deberías caer en la pantalla de Inicio, ya logueado.
3. `http://localhost:8000/docs` tiene que responder con la documentación interactiva de la API.

Si algo falla, `uv run pytest` y `cd frontend && npx tsc -b && npm run lint`
corren exactamente lo mismo que el CI (`.github/workflows/ci.yml`) — sirven
para aislar si el problema es de setup local o de código.

## Notas

- El `.env` de cada uno es local y **nunca se commitea** (está en `.gitignore`).
- OSRM (el servicio que calcula distancias/tiempos reales) apunta por defecto al
  servidor demo público (`router.project-osrm.org`) — tiene rate-limiting, no hace
  falta instalar nada aparte para desarrollo local. Para uno propio, ver
  [OSRM propio](#3-osrm-propio-opcional).
- El frontend es una PWA: el service worker solo se registra en el build de
  producción (`npm run build` + `npx vite preview --port 5174 --strictPort`).
  Tests del frontend: `npm test` (utilidades puras, sin dependencias extra).
- Antes de abrir un PR, revisá los checks de [CONTRIBUTING.md](CONTRIBUTING.md#antes-de-abrir-un-pr).

## Deploy en Railway

La app se despliega como **un solo servicio** (el `Dockerfile` compila la PWA y FastAPI la sirve junto a la API, así la cookie de sesión funciona sin dominio propio) más un Postgres.

1. Subí el repo a GitHub. En Railway: **New Project → Deploy from GitHub repo** (toma `railway.json` y el `Dockerfile`).
2. En el mismo proyecto: **New → Database → PostgreSQL**.
3. En el servicio de la app, pestaña **Variables**:
   - `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` (se corrige solo a `postgresql+psycopg://`)
   - `JWT_SECRET_KEY` = salida de `python -c "import secrets;print(secrets.token_urlsafe(64))"`
   - `ENTORNO` = `produccion`
   - `FRONTEND_URL` = la URL pública del servicio (ej. `https://mi-app.up.railway.app`)
4. **Settings → Networking → Generate Domain**.

Las migraciones (`alembic upgrade head`) corren en cada arranque. `OSRM_BASE_URL` queda en el demo público; para un OSRM propio hace falta otro servicio con los datos de `scripts/preparar_osrm.py`.

### Login con Google (opcional)

Sin estas variables la app funciona igual, solo que sin el botón "Continuar con Google".

1. En [Google Cloud Console](https://console.cloud.google.com/) creá un proyecto (o usá uno existente) y entrá a **APIs y servicios → Pantalla de consentimiento de OAuth**: tipo **Externo**, nombre de la app, email de soporte y los scopes básicos (`openid`, `email`, `profile`). Cuando termines de probar, **publicala** (botón "Publicar app"); mientras esté en modo "Prueba" solo pueden entrar los usuarios de prueba que cargues ahí. Con solo esos scopes básicos, Google no pide verificación.
2. **APIs y servicios → Credenciales → Crear credenciales → ID de cliente de OAuth**, tipo **Aplicación web**. En **URI de redireccionamiento autorizados** agregá:
   - `https://<tu-dominio>/api/v1/auth/google/callback` (producción, ej. `https://optirutas.up.railway.app/api/v1/auth/google/callback`)
   - `http://localhost:8000/api/v1/auth/google/callback` (desarrollo)
3. Copiá el ID y el secreto. En Railway, en las variables del servicio de la app: `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET`. `GOOGLE_REDIRECT_URI` puede quedar sin definir en producción (se usa `FRONTEND_URL` + `/api/v1/auth/google/callback`, así que `FRONTEND_URL` tiene que ser exactamente el dominio público). En tu `.env` local, cargá las tres (ver `.env.example`).

Si alguien entra con Google con un email que ya tiene cuenta, se vincula a esa cuenta. Si el email es nuevo, se le piden los datos del vehículo y se crea como chofer independiente sin contraseña.
