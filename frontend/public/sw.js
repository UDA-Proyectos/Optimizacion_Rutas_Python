// Service worker de OptiRuta. Sin dependencias: el build de Vite genera nombres
// con hash, así que en vez de una lista de precache el shell se guarda en
// runtime la primera vez que se carga online. Nunca cachea la API (vive en otro
// origen y lleva la sesión): la ruta activa offline la guarda la propia app.

const VERSION = "v1";
const CACHE_APP = `optiruta-app-${VERSION}`;
const CACHE_TESELAS = `optiruta-teselas-${VERSION}`;
const MAX_TESELAS = 400;

self.addEventListener("install", () => {
  // Sin skipWaiting() automático: una versión nueva queda "en espera" hasta que
  // el chofer acepta el aviso, para no recargar la app a mitad de una entrega.
});

self.addEventListener("message", (evento) => {
  if (evento.data === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    (async () => {
      const nombres = await caches.keys();
      await Promise.all(
        nombres
          .filter((n) => n.startsWith("optiruta-") && n !== CACHE_APP && n !== CACHE_TESELAS)
          .map((n) => caches.delete(n)),
      );
      await self.clients.claim();
    })(),
  );
});

async function recortarCache(nombre, maximo) {
  const cache = await caches.open(nombre);
  const claves = await cache.keys();
  // keys() devuelve en orden de inserción: se descartan las más viejas.
  await Promise.all(claves.slice(0, Math.max(0, claves.length - maximo)).map((c) => cache.delete(c)));
}

async function staleWhileRevalidate(request, nombreCache, maximo) {
  const cache = await caches.open(nombreCache);
  const guardada = await cache.match(request);
  const red = fetch(request)
    .then(async (respuesta) => {
      // Las teselas (<img> cross-origin) llegan "opaque" (status 0) y sirven igual.
      if (respuesta.ok || respuesta.type === "opaque") {
        await cache.put(request, respuesta.clone());
        if (maximo) await recortarCache(nombreCache, maximo);
      }
      return respuesta;
    })
    .catch(() => null);
  return guardada ?? (await red) ?? Response.error();
}

async function navegacion(request) {
  const cache = await caches.open(CACHE_APP);
  try {
    const respuesta = await fetch(request);
    if (respuesta.ok) {
      // Toda ruta del SPA sirve el mismo index.html.
      await cache.put("/", respuesta.clone());
    }
    return respuesta;
  } catch {
    return (await cache.match("/")) ?? Response.error();
  }
}

self.addEventListener("fetch", (evento) => {
  const { request } = evento;
  if (request.method !== "GET") return;
  const url = new URL(request.url);

  if (request.mode === "navigate") {
    evento.respondWith(navegacion(request));
    return;
  }

  if (/^[a-c]\.tile\.openstreetmap\.org$/.test(url.hostname)) {
    evento.respondWith(staleWhileRevalidate(request, CACHE_TESELAS, MAX_TESELAS));
    return;
  }

  // Estáticos propios (bundle con hash, iconos, manifest). La API (aunque algún
  // día se sirva desde este mismo origen) y cualquier otro origen pasan de largo.
  if (
    url.origin === self.location.origin &&
    url.pathname !== "/sw.js" &&
    !url.pathname.startsWith("/api/")
  ) {
    evento.respondWith(staleWhileRevalidate(request, CACHE_APP));
  }
});
