## Context

`Incidencia` no tiene estado; `crud.fallar_parada` la crea junto con el fallo. `ParadaRuta` guarda un snapshot del lugar, la carga, los bultos y la ventana, y su `cliente_id`. `FlujoArmarRuta.tsx` arma una `Seleccion` (cliente -> carga, bultos, ventana) precargada desde los datos habituales del lugar. Ver proposal.md para la motivación.

## Goals / Non-Goals

**Goals:**
- Que una entrega fallida se pueda reprogramar en el momento o después, sin perderla.
- Que la sección Incidencias sirva para hacer seguimiento.

**Non-Goals:**
- "Retira el cliente en el depósito", cancelar la entrega, notas y reabrir (se pueden sumar sobre esta base).
- Asignar la reprogramada a una fecha concreta: siempre es "la próxima ruta".
- Choferes de empresa.

## Decisions

- **Tabla `EntregaPendiente` propia** (usuario, cliente, parada de origen, incidencia, carga, bultos, ventana, estado pendiente/incluida, fechas) en vez de marcar la `ParadaRuta` vieja: la parada es el historial de un día y debe quedar inmutable; la entrega pendiente es un compromiso a futuro con su propio ciclo de vida. Un índice único sobre `parada_origen_id` evita duplicados.
- **Estado y resolución en `Incidencia`** (`estado`, `resolucion`, `fecha_resolucion`). `estado` es un enum de dos valores; `resolucion` (reprogramada | cerrada) es nullable. Se descartó derivar el estado de la existencia de una entrega pendiente: no cubre "cerrada" ni las incidencias generales.
- **Una sola operación al fallar** (`reprogramar` en `FallarParadaRequest`): evita exponer el id de la incidencia en `RutaPublica` solo para encadenar un segundo pedido, y deja fallo + reprogramación en una transacción.
- **Resolver en `POST /api/v1/incidencias/{id}/resolver`** con la resolución en el cuerpo; el listado acepta `?estado=`. El cierre de una entrega pendiente al confirmar o editar una ruta ocurre en el backend (`crud`), no en el frontend, para que no dependa de que la pantalla lo pida.
- **Entregas pendientes en `GET /api/v1/entregas-pendientes`**, filtradas por dueño y por lugar activo. Sin endpoint de baja: para no entregarla en la próxima ruta alcanza con desmarcarla; sigue pendiente.
- **Precarga**: los datos de la entrega pendiente pisan a los datos habituales del lugar, porque son los de esa entrega concreta.
- **Indicador de pendientes** calculado en el frontend a partir del listado ya cargado, sin un endpoint de conteo.

## Risks / Trade-offs

- [Una entrega pendiente puede acumularse si el chofer nunca la incluye] → queda visible como reprogramada en cada ruta nueva hasta que se incluya; cancelarla queda para un cambio futuro.
- [Incidencias antiguas sin estado] → la migración las crea como pendientes, salvo que se quiera lo contrario; se ponen como resueltas cerradas para no generar ruido histórico.
- [El lugar se da de baja con una entrega pendiente] → se omite en el listado y se conserva el registro.

## Migration Plan

Migración Alembic: columnas `estado` (default resuelta para las filas existentes), `resolucion` y `fecha_resolucion` en `incidencias`, y la tabla `entregas_pendientes`. Las filas existentes quedan como resueltas/cerradas. Rollback con `alembic downgrade -1`; se pierden solo los datos del nuevo flujo.
