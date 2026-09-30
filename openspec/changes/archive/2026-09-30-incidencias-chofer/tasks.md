## 1. Backend

- [x] 1.1 Crear `api/schemas_incidencias.py` (`IncidenciaCrear`, `IncidenciaPublica`) y verificar que el tipo inválido devuelve 422 en un test
- [x] 1.2 Agregar `crear_incidencia` y `listar_incidencias_de_chofer` en `db/crud.py` y verificar con tests que el listado solo devuelve las del chofer
- [x] 1.3 Crear `api/routes_incidencias.py` con `POST` y `GET` (404 parada ajena, 409 sin ruta en curso) y registrarlo en `main.py`; verificar con `tests/test_incidencias.py`

## 2. Frontend

- [x] 2.1 Agregar `tipos/incidencia.ts` y `api/incidencias.ts`; verificar con `npm run build`
- [x] 2.2 Crear el formulario modal de incidencia en `componentes/incidencias/` y habilitar el botón "Reportar incidencia" del header solo con ruta en curso; verificar manualmente que se crea y aparece en el listado
- [x] 2.3 Reemplazar `PlaceholderSeccion` de "Incidencias" por la lista real con estado vacío, y usar el conteo real en el subtítulo; verificar visualmente en el navegador

## 3. Cierre

- [x] 3.1 Correr `uv run pytest` y `uv run ruff check .`; verificar que pasan
