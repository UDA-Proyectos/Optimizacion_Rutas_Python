from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

# Estos archivos no pueden quedar cacheados: apuntan a los assets con hash de cada build
# y el navegador tiene que ver enseguida un service worker nuevo.
_SIN_CACHE = {"Cache-Control": "no-cache"}
_ARCHIVOS_SIN_CACHE = {"index.html", "sw.js", "manifest.webmanifest"}


def montar_frontend(app: FastAPI, directorio: Path) -> None:
    """Sirve el build de la PWA desde la misma origin que la API (la cookie de sesión es samesite=lax)."""
    if not (directorio / "index.html").is_file():
        return

    raiz = directorio.resolve()

    @app.get("/{ruta:path}", include_in_schema=False)
    def servir_frontend(ruta: str) -> FileResponse:
        if ruta.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        archivo = (raiz / ruta).resolve()
        if not (archivo.is_relative_to(raiz) and archivo.is_file()):
            archivo = raiz / "index.html"  # fallback de la SPA (react-router)
        headers = _SIN_CACHE if archivo.name in _ARCHIVOS_SIN_CACHE else None
        return FileResponse(archivo, headers=headers)
