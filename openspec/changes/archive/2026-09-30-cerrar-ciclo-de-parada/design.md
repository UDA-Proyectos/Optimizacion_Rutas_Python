## Context

`crud.completar_parada` (`db/crud.py`) marca la parada como completada, avanza la siguiente por `orden` y cierra la ruta si no hay más. `ParadaRuta` ya tiene `hora_real_llegada` y `hora_real_salida`, y existe el enum `EstadoParada.FALLIDA` y el modelo `Incidencia` (con `parada_id`), pero nada los usa. En el frontend, `VistaEnCursoRuta` guarda `arribado` en `useState`. Ver proposal.md para la motivación.

## Goals / Non-Goals

**Goals:**
- Que llegada, fallo y salto sean estado persistido en el backend, fuente única de verdad.
- Reutilizar `Incidencia` para los fallos, sin duplicar el concepto.

**Non-Goals:**
- UI de listado/reporte libre de incidencias (change `incidencias-chofer`).
- Prueba de entrega (foto/firma).
- Reoptimizar el orden restante al saltear.

## Decisions

- **Motivo de fallo en `ParadaRuta.motivo_fallo`** (enum `TipoIncidencia`, nullable) además de la `Incidencia` creada. Alternativa: solo la incidencia. Se duplica el dato a propósito: el historial y la timeline leen la parada sin joins, y la incidencia queda como registro de auditoría.
- **Saltear = renumerar `orden`** de la parada al final de las pendientes (no un estado nuevo). Alternativa: estado `salteada`. Renumerar mantiene el modelo y `UniqueConstraint(ruta_id, orden)`; requiere reasignar órdenes en una sola transacción para no violar la restricción.
- **Cierre por "sin pendientes"**: el criterio pasa de "no hay `orden` mayor" a "no hay paradas pendientes o en curso", porque el salto rompe la relación entre orden y avance.
- **Endpoints bajo `/activa/paradas/{id}/`**: `llegada`, `completar` (existente), `fallar`, `saltear`; todos con `requiere_chofer_independiente` y validando que la parada sea la `en_curso`, igual que `completar`.
- **Botón "Llegué"** llama a `llegada`; ya no hay estado local `arribado` (se deriva de `hora_real_llegada`).

## Risks / Trade-offs

- [Renumerar `orden` puede chocar con `UniqueConstraint`] → hacerlo con un `orden` temporal negativo o desplazando en orden descendente dentro de la misma transacción.
- [Fallo duplica el motivo en dos tablas] → un único helper en `crud` crea ambos; tests que verifican consistencia.
- [Rutas históricas sin `motivo_fallo`] → columna nullable, sin backfill.

## Migration Plan

Migración Alembic que agrega `paradas_ruta.motivo_fallo` nullable (revisar el autogenerado a mano por el enum `native_enum=False`). Rollback: `alembic downgrade -1`; sin pérdida de datos previos.
