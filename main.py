from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as router_ruteo
from api.routes_auth import router as router_auth
from api.routes_clientes import router as router_clientes
from api.routes_depositos import router as router_depositos
from api.routes_entregas_pendientes import router as router_entregas_pendientes
from api.routes_geocoding import router as router_geocoding
from api.routes_incidencias import router as router_incidencias
from api.routes_rutas import router as router_rutas
from core.config import settings

app = FastAPI(
    title="API de Optimización de Rutas - Gran Mendoza",
    description="Motor de optimización VRPTW basado en Google OR-Tools",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_ruteo)
app.include_router(router_auth)
app.include_router(router_clientes)
app.include_router(router_depositos)
app.include_router(router_geocoding)
app.include_router(router_rutas)
app.include_router(router_incidencias)
app.include_router(router_entregas_pendientes)
