# --- Frontend: build de la PWA ---
FROM node:22-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# API en la misma origin que el frontend: rutas relativas (/api/v1/...)
ENV VITE_API_URL=""
RUN npm run build

# --- Backend + frontend estático ---
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH="/app/.venv/bin:$PATH"
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY main.py alembic.ini ./
COPY alembic/ alembic/
COPY api/ api/
COPY core/ core/
COPY db/ db/
COPY routing/ routing/
COPY services/ services/
COPY --from=frontend /frontend/dist frontend/dist
RUN useradd --system --no-create-home app && chown -R app /app
USER app
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
