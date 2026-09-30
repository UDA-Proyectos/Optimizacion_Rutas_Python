## Why

El proyecto se define como PWA para choferes, pero hoy solo es una web responsive: no tiene `manifest`, service worker ni instalación, y si el chofer pierde señal en plena ruta la app se queda sin la ruta cargada. Tampoco usa la ubicación del dispositivo: el origen de cada tramo es siempre el depósito o la parada anterior, no donde está realmente el chofer.

## What Changes

- La app es instalable (manifest, iconos, `display: standalone`, tema violeta).
- Service worker que cachea el shell de la app y permite abrir la app sin conexión.
- La última ruta activa consultada queda disponible en modo lectura sin conexión, con un aviso visible de "sin conexión".
- Las acciones que escriben (llegué, entregada, fallar, saltear) se bloquean sin conexión con un mensaje claro, en vez de fallar en silencio.
- Ubicación del dispositivo (Geolocation API, con permiso explícito): el mapa muestra la posición actual y "Ir con Maps" usa esa posición como origen cuando está disponible.
- La posición nunca se envía ni se guarda en el servidor.

## Capabilities

### New Capabilities
- `pwa-offline`: instalación de la app y acceso sin conexión al shell y a la ruta activa en modo lectura.
- `ubicacion-gps`: uso de la posición del dispositivo, solo en el cliente, para el mapa y la navegación.

### Modified Capabilities

## Impact

- Frontend: `frontend/public/manifest.webmanifest`, iconos PWA, service worker (vía `vite-plugin-pwa` o equivalente), `useRutaActiva.ts`, `MapaRutaActiva.tsx`, `utilidades/googleMaps.ts`, un hook `useUbicacion`, `index.html`.
- Dependencia nueva de frontend (plugin PWA): hay que discutirla antes de instalarla, según el CLAUDE.md.
- Backend: sin cambios.
- Producción: requiere HTTPS para service worker y geolocalización (localhost funciona en desarrollo).
