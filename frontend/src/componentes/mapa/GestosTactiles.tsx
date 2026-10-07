import { useEffect, useState } from "react";
import { useMap } from "react-leaflet";

const MS_AVISO = 1500;

// En pantallas táctiles el mapa grande se "come" el scroll de la página: un dedo
// arrastra el mapa en vez de bajar o subir. Con el arrastre de un dedo apagado
// Leaflet deja `touch-action: pan-x pan-y` y la página scrollea normal; el mapa se
// mueve y se acerca con dos dedos (el pinch de Leaflet también desplaza).
export function GestosTactiles() {
  const mapa = useMap();
  const [mostrarAviso, setMostrarAviso] = useState(false);

  useEffect(() => {
    if (!window.matchMedia("(pointer: coarse)").matches) return;

    mapa.dragging.disable();
    const contenedor = mapa.getContainer();
    let temporizador: number | undefined;

    function alMoverUnDedo(evento: TouchEvent) {
      if (evento.touches.length !== 1) return;
      setMostrarAviso(true);
      window.clearTimeout(temporizador);
      temporizador = window.setTimeout(() => setMostrarAviso(false), MS_AVISO);
    }

    contenedor.addEventListener("touchmove", alMoverUnDedo, { passive: true });
    return () => {
      contenedor.removeEventListener("touchmove", alMoverUnDedo);
      window.clearTimeout(temporizador);
      mapa.dragging.enable();
    };
  }, [mapa]);

  if (!mostrarAviso) return null;
  return (
    <div className="pointer-events-none absolute inset-0 z-[1000] flex items-center justify-center bg-texto-fuerte/35">
      <p className="rounded-pill bg-texto-fuerte/85 px-4 py-2 text-[12.5px] font-semibold text-blanco">
        Usá dos dedos para mover el mapa
      </p>
    </div>
  );
}
