## 1. Decisión de dependencia

- [x] 1.1 Resolver el service worker sin dependencias nuevas (`sw.js` propio, ver design) en vez de `vite-plugin-pwa`, que el CLAUDE.md pide discutir antes de sumar; verificar que `package.json` no cambia y que el design lo registra

## 2. PWA instalable

- [x] 2.1 Crear `manifest.webmanifest` e iconos (192/512 y maskable) y enlazarlos en `index.html`; verificar en DevTools > Application que el manifest es válido y "installable"
- [x] 2.2 Crear `sw.js` con caché en runtime del shell y registrarlo solo en producción; verificar con el servidor detenido que la app abre tras una primera carga
- [x] 2.3 Agregar el aviso de nueva versión disponible; verificar publicando un cambio y comprobando que se ofrece recargar

## 3. Offline de solo lectura

- [x] 3.1 Implementar el hook de estado de conexión y mostrar el banner "sin conexión"; verificar cortando la red en DevTools
- [x] 3.2 Cachear en IndexedDB la última ruta activa en `useRutaActiva.ts` con marca de hora y usarla como fallback; verificar que se ve la lista de paradas sin red
- [x] 3.3 Deshabilitar llegada, entrega, fallo, salto e iniciar sin conexión con mensaje; verificar manualmente que no se envía ningún request
- [x] 3.4 Borrar la ruta cacheada al cerrar sesión y ante un 401; verificar que IndexedDB queda vacío tras el logout
- [x] 3.5 Configurar el cache de teselas de OSM con tope; verificar que las teselas ya vistas cargan sin red

## 4. Ubicación

- [x] 4.1 Crear `useUbicacion` con permiso explícito y manejo de denegación; verificar con permiso denegado que la app funciona igual
- [x] 4.2 Mostrar el marcador de posición actual en `MapaRutaActiva.tsx`; verificar manualmente con ubicación simulada en DevTools
- [x] 4.3 Pasar la posición como origen preferido en `utilidades/googleMaps.ts`; verificar con un test unitario de las dos ramas (con y sin posición)
- [x] 4.4 Verificar en la pestaña Network que ningún request al backend incluye la posición del chofer

## 5. Cierre

- [x] 5.1 Correr `npm run build`, `npm run lint` y `npm test`; verificar que pasan y que se cumplen los criterios de instalabilidad (manifest con nombre, `start_url` y `display`, iconos PNG 192 y 512, service worker con manejador `fetch` sirviendo la página)
