## 1. Backend

- [x] 1.1 Agregar los campos habituales con validación (`fin > inicio`, servicio 0–240) a `api/schemas_clientes.py` y verificar con tests de 422 y de round-trip en `tests/test_clientes.py`
- [x] 1.2 Agregar `ventana_inicio`/`ventana_fin` con validación a `api/schemas_depositos.py` y verificar con tests en `tests/test_depositos.py`
- [x] 1.3 Agregar `deposito_id` opcional a `OptimizarRutaRequest` y resolverlo en `routing/planificador.py` filtrando por dueño (400 si es ajeno); verificar con tests en `tests/test_rutas.py` de depósito elegido, ajeno y por defecto
- [x] 1.4 Verificar con un test que el ETA VRPTW incluye el tiempo de servicio del cliente anterior

## 2. Frontend

- [x] 2.1 Actualizar `tipos/cliente.ts` y `tipos/deposito.ts`; verificar con `npm run build`
- [x] 2.2 Agregar carga habitual, servicio y ventana a `FormularioCliente.tsx` y mostrarlos en `TarjetaLugar.tsx`; verificar manualmente que se guardan y se muestran
- [x] 2.3 Agregar la ventana horaria a `FormularioDeposito.tsx`; verificar manualmente
- [x] 2.4 Precargar carga y ventana desde el lugar en `FlujoArmarRuta.tsx` y agregar el selector de depósito cuando hay más de uno; verificar manualmente que el cambio puntual no altera el lugar

## 3. Cierre

- [x] 3.1 Correr `uv run pytest`, `uv run ruff check .` y `npm run build`; verificar que pasan
