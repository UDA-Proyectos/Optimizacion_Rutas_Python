import { useEffect, useState } from "react";
import { BrowserRouter } from "react-router-dom";

import { AppRouter } from "./router";
import { useAuthStore } from "./store/useAuthStore";
import { registrarServiceWorker } from "./utilidades/registrarServiceWorker";

export default function App() {
  const cargarSesion = useAuthStore((estado) => estado.cargarSesion);
  const cargando = useAuthStore((estado) => estado.cargando);
  // Función que aplica la versión nueva del service worker, si hay una esperando.
  const [aplicarActualizacion, setAplicarActualizacion] = useState<(() => void) | null>(null);

  useEffect(() => {
    cargarSesion();
  }, [cargarSesion]);

  useEffect(() => {
    // Un `useState` con una función como valor la ejecutaría al setearla.
    registrarServiceWorker((aplicar) => setAplicarActualizacion(() => aplicar));
  }, []);

  if (cargando) {
    return null;
  }

  return (
    <BrowserRouter>
      <AppRouter />
      {aplicarActualizacion && (
        <div
          role="status"
          className="fixed right-4 bottom-4 left-4 z-[1000] mx-auto flex max-w-[420px] items-center gap-3 rounded-xl border border-borde bg-blanco px-4 py-3 shadow-md"
        >
          <p className="min-w-0 flex-1 text-[12.5px] text-texto-cuerpo">
            Hay una versión nueva de la app.
          </p>
          <button
            type="button"
            onClick={aplicarActualizacion}
            className="h-9 shrink-0 rounded-lg bg-primario px-3.5 text-[12.5px] font-bold text-blanco"
          >
            Actualizar
          </button>
        </div>
      )}
    </BrowserRouter>
  );
}
