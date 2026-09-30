## Context

`Incidencia` (`db/modelos.py`) ya tiene `ruta_id`, `parada_id` nullable, `tipo`, `descripcion`, `reportado_por_usuario_id`. El header de `EscritorioChofer.tsx` tiene un botón deshabilitado y la sección "incidencias" usa `PlaceholderSeccion`. Ver proposal.md para la motivación.

## Goals / Non-Goals

**Goals:**
- Alta y listado de incidencias con el modelo existente.
- Reutilizar el helper de creación que usa `cerrar-ciclo-de-parada` al fallar una parada.

**Non-Goals:**
- Resolución/estado de la incidencia por un dador de carga (el placeholder actual lo menciona; no hay empresa que la resuelva todavía).
- Adjuntos (fotos) y reputación del chofer.
- Incidencias de choferes de empresa.

## Decisions

- **Router propio `/api/v1/incidencias`** (`POST` y `GET`) en vez de anidarlo en `/rutas`: el listado no depende de la ruta activa. Alternativa: sub-ruta de rutas; se descarta porque el historial cruza rutas.
- **Reportar exige ruta `en_curso`**: evita incidencias huérfanas de un plan que no arrancó; una ruta planificada se edita o cancela.
- **Listado con límite y orden por `fecha_hora desc`** (paginación simple `limite`/`desplazamiento`); volumen esperado bajo.
- **Nombre de la parada** se resuelve desde `nombre_snapshot`, para que sobreviva si el cliente se borra.
- **Formulario en modal** reutilizando `Formulario`/`Campo*` de `componentes/ui`; la parada es un select con las paradas de la ruta activa.

## Risks / Trade-offs

- [Incidencias sin resolución pueden parecer "abiertas" para siempre] → la UI las muestra como registro, no como tickets con estado.
- [Depende de que `cerrar-ciclo-de-parada` esté implementado] → aplicar en ese orden; los tests de listado crean incidencias directo por CRUD.
