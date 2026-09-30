## Context

`RutaPublica` no expone `hora_fin_real` ni un resumen; el frontend calcula KPIs sueltos en `VistaEnCursoRuta` y `ResumenRuta`. `RutaHistorialItem` trae `paradas_total`/`paradas_completadas`. Una ruta completada deja de ser "la ruta activa" (ver `crud.obtener_ruta_activa`), por eso `useRutaActiva` usa la ruta devuelta por la última acción. Ver proposal.md para la motivación.

## Goals / Non-Goals

**Goals:**
- Una sola fuente de cálculo (backend) para el resumen, usada en cierre e historial.
- No inventar datos: nada de km reales ni combustible.

**Non-Goals:**
- Seguimiento GPS del recorrido real (ver `pwa-y-gps`).
- Exportar/compartir el resumen (PDF, mail).
- Estadísticas agregadas por semana o mes.

## Decisions

- **Campo calculado `resumen` en `RutaPublica`** (`computed_field`, mismo patrón que `en_riesgo` y `ventana_cumplida`), `None` si la ruta no está completada. Alternativa: endpoint separado; se descarta para evitar un request extra y porque las paradas ya vienen en la respuesta.
- **Resumen calculado en una función pura** de `schemas_rutas`/`crud` a partir de paradas e incidencias, testeable sin base.
- **Conteo de incidencias** con una consulta agregada en el listado del historial para no cargar N rutas con todas sus incidencias.
- **Distancia siempre "planificada"**: es lo único que se mide; queda explícito en la spec para que un futuro seguimiento GPS lo cambie de forma consciente.
- **Cierre en `ResumenRuta`**: se extiende el componente existente con la rama `completada`, en vez de crear una pantalla nueva, reutilizando `TarjetaKpi`.

## Risks / Trade-offs

- [Rutas antiguas sin `hora_real_llegada`/`motivo_fallo`] → el resumen tolera `None` y omite lo que no puede calcular.
- [`ventana_cumplida` se basa en la hora de salida, no de llegada] → se mantiene el criterio existente; queda documentado en el schema.
