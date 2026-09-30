/** Registra el service worker (solo en producción: en desarrollo cachearía
 * módulos de Vite y confundiría cualquier cambio). Cuando hay una versión nueva
 * esperando, llama a `onActualizacion` con la función que la aplica — la app
 * la ofrece con un aviso en vez de recargarse sola a mitad de una entrega. */
export function registrarServiceWorker(onActualizacion: (aplicar: () => void) => void) {
  if (!("serviceWorker" in navigator)) {
    return;
  }

  if (!import.meta.env.PROD) {
    // En desarrollo se limpia cualquier worker que haya dejado un `vite preview`
    // (o un build anterior) en este mismo origen: si no, serviría módulos viejos
    // desde su caché y el hot reload dejaría de funcionar.
    void navigator.serviceWorker
      .getRegistrations()
      .then((registros) => registros.forEach((registro) => void registro.unregister()));
    void caches
      .keys()
      .then((nombres) =>
        nombres.filter((n) => n.startsWith("optiruta-")).forEach((n) => void caches.delete(n)),
      );
    return;
  }

  // controllerchange también dispara la primera vez que el worker toma el
  // control (clients.claim): solo se recarga si el chofer aceptó actualizar.
  let aplicando = false;
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    if (aplicando) {
      window.location.reload();
    }
  });

  function avisar(worker: ServiceWorker) {
    onActualizacion(() => {
      aplicando = true;
      worker.postMessage("SKIP_WAITING");
    });
  }

  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js")
      .then((registro) => {
        if (registro.waiting && navigator.serviceWorker.controller) {
          avisar(registro.waiting);
        }
        registro.addEventListener("updatefound", () => {
          const nuevo = registro.installing;
          nuevo?.addEventListener("statechange", () => {
            if (nuevo.state === "installed" && navigator.serviceWorker.controller) {
              avisar(nuevo);
            }
          });
        });
      })
      .catch(() => {
        // Sin service worker la app funciona igual, solo que sin modo offline.
      });
  });
}
