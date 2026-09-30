## Context

`frontend/public` solo tiene `favicon.svg` e `icons.svg`; `index.html` no enlaza manifest. `useRutaActiva` pide `GET /rutas/activa` y no tiene noción de red. `MapaRutaActiva` usa Leaflet con teselas de OpenStreetMap. La sesión vive en una cookie httpOnly y el CLAUDE.md prohíbe `localStorage` para la sesión. Ver proposal.md para la motivación.

## Goals / Non-Goals

**Goals:**
- Instalación y arranque offline con un service worker mantenible.
- Lectura offline de la ruta activa sin comprometer la seguridad de la sesión.
- GPS estrictamente local.

**Non-Goals:**
- Cola de escrituras offline con sincronización posterior (las acciones no son todas idempotentes; se bloquean sin conexión).
- Notificaciones push.
- Seguimiento continuo o historial de posiciones.
- Mapas offline completos (solo las teselas ya visitadas).

## Decisions

- **Service worker escrito a mano, sin dependencias nuevas** (`frontend/public/sw.js` + `manifest.webmanifest`). Se descartó `vite-plugin-pwa` (Workbox) porque el CLAUDE.md exige discutir cualquier librería nueva antes de sumarla. Como el build de Vite genera nombres con hash, no hay lista de precache: el shell se cachea en runtime (stale-while-revalidate para estáticos del mismo origen, network-first con fallback para la navegación), lo que alcanza tras una primera carga online. Se registra solo en producción (`import.meta.env.PROD`) para no cachear módulos de desarrollo.
- **Ruta activa cacheada en IndexedDB** (no `localStorage`), con marca de tiempo; se borra en el logout. Contiene datos operativos, no credenciales ni token.
- **Estrategia de red**: `GET /api/v1/rutas/activa` con network-first y fallback a la copia local; las demás llamadas a la API no se cachean. Teselas de OSM con stale-while-revalidate y tope de entradas.
- **Estado de conexión** en un hook (`navigator.onLine` + eventos `online/offline`), consumido por `useRutaActiva` y los botones de acción; las acciones se deshabilitan en vez de encolarse.
- **`useUbicacion`**: `watchPosition` activo solo mientras hay ruta en curso y con permiso concedido; la posición vive en estado de React, nunca en el store persistente ni en requests.
- **Origen de navegación**: `origenNavegacionParaParadaActual` (`utilidades/googleMaps.ts`) recibe la posición opcional y la prefiere.

## Risks / Trade-offs

- [Service worker sirve una versión vieja de la app] → el worker nuevo queda en espera (sin `skipWaiting` automático) y se ofrece un aviso "hay una versión nueva" y recarga controlada, no automática a mitad de una entrega.
- [Datos de ruta desactualizados offline] → aviso visible y marca de hora de la última sincronización.
- [Geolocalización imprecisa o lenta en interiores] → siempre hay fallback al origen del tramo.
- [Ruta cacheada permanece si el usuario no cierra sesión en un dispositivo compartido] → se limpia en logout y al recibir un 401.
- [HTTPS obligatorio para instalar] → en desarrollo `localhost` está exento; el despliegue debe cumplirlo.
