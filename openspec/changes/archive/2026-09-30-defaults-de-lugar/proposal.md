## Why

`Cliente` ya guarda `demanda_carga_default`, `tiempo_servicio_default` y `ventana_inicio/fin_default`, pero ni el formulario de lugares ni el flujo de armar ruta los usan. El chofer retipea carga y horarios de cada parada todos los días, y el tiempo de servicio queda siempre en 0, lo que vuelve irreales los ETA y la detección de riesgo en VRPTW. Además el depósito tiene ventana horaria en el modelo pero no se puede configurar, y el solver toma siempre el primer depósito.

## What Changes

- `FormularioCliente` permite cargar carga habitual, tiempo de servicio (minutos) y ventana horaria habitual.
- `FlujoArmarRuta` precarga carga y ventana de cada lugar seleccionado con esos valores (editables por día).
- Tiempo de servicio real: el backend lo toma del cliente (ya lo hace) y la UI lo muestra en la tarjeta del lugar.
- `FormularioDeposito` permite configurar la ventana horaria del depósito.
- Si el chofer tiene más de un depósito, elige desde cuál sale la ruta (por defecto el primero).

## Capabilities

### New Capabilities
- `libreta-de-lugares`: datos habituales de un lugar (carga, servicio, ventana), ventana del depósito y selección de depósito de salida.

### Modified Capabilities

## Impact

- Backend: `api/schemas_clientes.py`, `api/schemas_depositos.py`, `api/schemas_rutas.py` (depósito elegido opcional), `routing/planificador.py`. Sin migración: las columnas existen.
- Frontend: `FormularioCliente.tsx`, `FormularioDeposito.tsx`, `FlujoArmarRuta.tsx`, `TarjetaLugar.tsx`, `tipos/cliente.ts`, `tipos/deposito.ts`.
