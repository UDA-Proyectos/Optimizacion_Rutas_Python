import { useSyncExternalStore } from "react";

function suscribir(avisar: () => void) {
  window.addEventListener("online", avisar);
  window.addEventListener("offline", avisar);
  return () => {
    window.removeEventListener("online", avisar);
    window.removeEventListener("offline", avisar);
  };
}

/** `navigator.onLine`: solo sabe si el dispositivo tiene *una* red, no que el
 * servidor responda — por eso useRutaActiva también cuenta un pedido fallido
 * como "sin conexión". */
export function useEnLinea(): boolean {
  return useSyncExternalStore(
    suscribir,
    () => navigator.onLine,
    () => true,
  );
}
