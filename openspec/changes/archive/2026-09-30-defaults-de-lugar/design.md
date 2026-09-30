## Context

Las columnas `Cliente.demanda_carga_default`, `tiempo_servicio_default`, `ventana_inicio_default`, `ventana_fin_default` y `Deposito.ventana_inicio/fin` ya existen. `routing/planificador.py` ya usa `tiempo_servicio_default` y la ventana del depósito (cae en `VENTANA_COMPLETA` si es `None`) pero el frontend nunca los carga. `planificar_ruta` toma `depositos[0]`. Ver proposal.md para la motivación.

## Goals / Non-Goals

**Goals:**
- Exponer los campos existentes en schemas y formularios, con validación.
- Elegir depósito de salida sin romper el comportamiento actual (default = primero).

**Non-Goals:**
- Importación masiva de lugares (CSV).
- Múltiples vehículos o rutas por día.
- Ventanas horarias múltiples por lugar.

## Decisions

- **Sin migración**: solo se agregan campos a `ClienteCrear/Actualizar/Publico` y `DepositoCrear/Actualizar/Publico`. Se valida `fin > inicio` y `0 <= servicio <= 240` con validadores Pydantic.
- **Precarga en el frontend**, no en el backend: `FlujoArmarRuta` ya arma `Seleccion` por cliente; se inicializa con los defaults del `ClientePublico`. El backend sigue recibiendo valores explícitos por parada (contrato de `/rutas/optimizar` sin cambios).
- **Depósito elegido = campo opcional `deposito_id`** en `OptimizarRutaRequest`. Alternativa: marcar un depósito "principal" en el modelo; se descarta por requerir migración y un concepto extra. Se valida con `crud` filtrando por `Duenio` (mismo patrón que `obtener_clientes_propios`).
- **Selector de depósito solo visible si hay más de uno**, para no agregar ruido al caso común.
- **Ventana en minuto del día** y campos `HH:MM` en la UI, reutilizando `utilidades/horario.ts`.

## Risks / Trade-offs

- [Ventana habitual precargada obliga a VRPTW innecesariamente] → la precarga solo llena los campos; el modo VRPTW sigue siendo un toggle explícito del chofer.
- [Un tiempo de servicio alto vuelve infactibles rutas antes factibles] → el mensaje de fallo ya sugiere revisar ventanas; la UI muestra el servicio en la tarjeta del lugar.
