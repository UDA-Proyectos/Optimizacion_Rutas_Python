## Context

`crud.obtener_ruta_activa(db, chofer_id, fecha)` devuelve la ruta `planificada` o `en_curso` de hoy y es la base de casi todo: `/rutas/activa*`, reportar incidencias, bloquear la edición del vehículo y el 409 de `confirmar`. `Ruta.fecha` ya existe y el historial ya lista por rango de fechas. El frontend modela "la ruta de hoy" como una sola ruta (`useRutaActiva`). Ver proposal.md para la motivación.

## Goals / Non-Goals

**Goals:**
- Planificar para una fecha, varias rutas por día, elegir y iniciar una concreta.
- Mantener intactas las acciones sobre la ruta en curso.

**Non-Goals:**
- Reordenar o fusionar rutas, o repartir lugares entre rutas automáticamente.
- Varios vehículos o varias rutas en curso a la vez.
- Recordatorios o notificaciones de rutas futuras.
- Rutas recurrentes.

## Decisions

- **Dos conceptos en lugar de uno**: "ruta en curso" (una sola por chofer, sin importar la fecha, con `GET /rutas/activa` y las acciones de parada) y "rutas de un día" (`GET /rutas?fecha=`). `obtener_ruta_activa` se reemplaza por `obtener_ruta_en_curso` y `listar_rutas_del_dia`. Una ruta iniciada un día y sin terminar sigue siendo la en curso al día siguiente, en vez de quedar huérfana.
- **Rutas identificadas por id** para editar, cancelar e iniciar (`/rutas/{id}`), porque ya no hay "la" ruta. Se descartó mantener `/activa` como alias de "la única ruta abierta": deja de tener sentido con varias.
- **La fecha la manda el cliente** (su día local), no el servidor: la fecha de una ruta es un día calendario del chofer, y el servidor en UTC daría el día equivocado de noche en Argentina. El servidor acepta hasta un día de tolerancia respecto de su propio "hoy" para no rechazar fechas locales válidas, y limita el futuro a 60 días. Sin fecha se usa el "hoy" del servidor, como hasta ahora.
- **Iniciar solo desde su día**: `POST /rutas/{id}/iniciar` acepta opcionalmente `fecha_hoy` (el día local del cliente, con el mismo control de tolerancia) y responde 409 si la ruta es de una fecha posterior. Una ruta de un día ya pasado que nunca se inició se puede iniciar igual: es decisión del chofer.
- **Nombre opcional** (`Ruta.nombre`, hasta 60 caracteres) en vez de numerarlas automáticamente: el número ("Ruta 2") se puede derivar en la pantalla por orden de creación, pero un nombre propio ("Zona norte") es lo que el chofer realmente usa para distinguirlas.
- **Bloqueo del vehículo** con un chequeo de "cualquier ruta planificada o en curso, de cualquier fecha" (`hay_ruta_abierta`), porque las rutas futuras ya se planificaron con la capacidad actual.
- **Frontend**: `useRutaActiva` pasa a manejar la fecha visible, la lista de rutas del día y la ruta seleccionada; expone `ruta` (la seleccionada) para que el resto de la pantalla cambie lo menos posible. La ruta en curso se selecciona sola si existe.
- **Copia offline**: se guarda la lista de rutas de hoy (y la en curso) en lugar de "la ruta activa".

## Risks / Trade-offs

- [Romper clientes de la API que usen `/rutas/activa`] → el único cliente es este frontend; los tests se migran y se documenta como BREAKING.
- [Fecha local distinta a la del servidor] → tolerancia de un día y fecha enviada por el cliente.
- [Varias rutas con los mismos lugares] → no se valida: el chofer puede querer repetir un lugar. Las entregas reprogramadas se dan por incluidas en la primera ruta que las confirma.
- [El selector de rutas agrega una pantalla más] → solo aparece cuando hay más de una ruta ese día.

## Migration Plan

Migración Alembic: columna `rutas.nombre` nullable. Las rutas existentes no cambian. Rollback con `alembic downgrade -1`.
