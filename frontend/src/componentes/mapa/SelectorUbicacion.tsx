import L from "leaflet";
import "leaflet/dist/leaflet.css";
import marcadorIcono from "leaflet/dist/images/marker-icon.png";
import marcadorIcono2x from "leaflet/dist/images/marker-icon-2x.png";
import marcadorSombra from "leaflet/dist/images/marker-shadow.png";
import { useEffect, useState } from "react";
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from "react-leaflet";

import { type ResultadoBusquedaDireccion, buscarDireccion, geocodificarInverso } from "../../api/geocoding";
import { CampoContenedor } from "../ui/CampoContenedor";
import { GestosTactiles } from "./GestosTactiles";

// El bundler no resuelve las rutas relativas que Leaflet usa por defecto
// para el ícono del pin — hay que apuntarlas a mano a los assets importados.
const iconoMarcador = L.icon({
  iconUrl: marcadorIcono,
  iconRetinaUrl: marcadorIcono2x,
  shadowUrl: marcadorSombra,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

// Centro del Gran Mendoza — punto de partida del mapa cuando todavía no hay
// ninguna ubicación marcada.
const CENTRO_MENDOZA: [number, number] = [-32.8908, -68.8272];

interface Props {
  latitud: number | null;
  longitud: number | null;
  onCambiar: (latitud: number, longitud: number) => void;
  /** El texto de dirección es responsabilidad del caller (Cliente lo persiste,
   * Depósito lo usa solo como confirmación visual) — este componente lo
   * mantiene actualizado solo, ya sea por click en el mapa (reversa) o por
   * un resultado de búsqueda elegido, y lo deja editable a mano debajo del
   * mapa. Nunca lo pisa con un resultado vacío: si Nominatim no resuelve
   * nada, lo que el usuario ya haya escrito queda como está. */
  direccion: string;
  onCambiarDireccion: (direccion: string) => void;
}

function ManejadorClicksMapa({ onClick }: { onClick: (lat: number, lon: number) => void }) {
  useMapEvents({
    click(evento) {
      onClick(evento.latlng.lat, evento.latlng.lng);
    },
  });
  return null;
}

/** Centra el mapa cada vez que cambia la ubicación marcada — necesario para
 * el resultado de una búsqueda, que puede caer bien afuera de lo que se ve
 * hoy (a diferencia de un click en el mapa, donde ya se está mirando ese
 * punto). Mismo patrón que AjustarVista en MapaRutaActiva.tsx.
 *
 * Depende de latitud/longitud como números sueltos, no de un array
 * [lat, lon]: ese array se recrearía en cada render de SelectorUbicacion
 * (aunque los valores no cambien) y con eso como dependencia el efecto
 * dispararía en cada tecla que se escribe en el buscador, no solo cuando
 * la ubicación cambia de verdad. */
function CentrarMapa({ latitud, longitud }: { latitud: number | null; longitud: number | null }) {
  const mapa = useMap();
  useEffect(() => {
    if (latitud != null && longitud != null) {
      mapa.setView([latitud, longitud], 15);
    }
  }, [mapa, latitud, longitud]);
  return null;
}

export function SelectorUbicacion({
  latitud,
  longitud,
  onCambiar,
  direccion,
  onCambiarDireccion,
}: Props) {
  const [buscando, setBuscando] = useState(false);
  const [busqueda, setBusqueda] = useState("");
  const [resultadosBusqueda, setResultadosBusqueda] = useState<ResultadoBusquedaDireccion[]>([]);
  const [buscandoTexto, setBuscandoTexto] = useState(false);
  const hayUbicacion = latitud != null && longitud != null;
  const posicion: [number, number] | null = hayUbicacion ? [latitud, longitud] : null;

  useEffect(() => {
    if (busqueda.trim().length < 3) {
      // oxlint no distingue el "no hay nada que buscar todavía" del resto
      // del efecto — sigue siendo la misma sincronización con la búsqueda
      // externa (acá, "no consultar y limpiar lo que había"), no un
      // segundo efecto disfrazado.
      // oxlint-disable-next-line react/set-state-in-effect
      setResultadosBusqueda([]);
      setBuscandoTexto(false);
      return;
    }
    setBuscandoTexto(true);
    const idTimeout = setTimeout(() => {
      buscarDireccion(busqueda).then((resultados) => {
        setResultadosBusqueda(resultados);
        setBuscandoTexto(false);
      });
    }, 400);
    return () => clearTimeout(idTimeout);
  }, [busqueda]);

  function limpiarBusqueda() {
    setBusqueda("");
    setResultadosBusqueda([]);
  }

  function manejarClickMapa(lat: number, lon: number) {
    limpiarBusqueda();
    onCambiar(lat, lon);
    setBuscando(true);
    geocodificarInverso(lat, lon).then((resuelta) => {
      setBuscando(false);
      if (resuelta) onCambiarDireccion(resuelta);
    });
  }

  function seleccionarResultadoBusqueda(resultado: ResultadoBusquedaDireccion) {
    limpiarBusqueda();
    onCambiar(resultado.latitud, resultado.longitud);
    onCambiarDireccion(resultado.direccion);
  }

  return (
    <CampoContenedor etiqueta="Ubicación — buscá una dirección o tocá el mapa para marcarla">
      <div className="relative mb-2">
        <input
          type="text"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          placeholder="Buscar dirección…"
          className="h-[46px] w-full rounded-md border border-borde-input bg-blanco px-3.5 text-sm text-texto-fuerte outline-none transition-[border-color,box-shadow] duration-150 focus:border-primario focus:shadow-[0_0_0_3px_rgba(124,58,237,0.15)] focus-visible:outline-none"
        />
        {busqueda.trim().length >= 3 && (
          <ul className="absolute z-[1100] mt-1 max-h-56 w-full overflow-y-auto rounded-md border border-borde bg-blanco shadow-md">
            {buscandoTexto ? (
              <li className="px-3 py-2 text-[12.5px] text-texto-mutado">Buscando…</li>
            ) : resultadosBusqueda.length > 0 ? (
              resultadosBusqueda.map((resultado, indice) => (
                <li key={indice}>
                  <button
                    type="button"
                    className="block w-full px-3 py-2 text-left text-[12.5px] text-texto-cuerpo hover:bg-fondo"
                    onClick={() => seleccionarResultadoBusqueda(resultado)}
                  >
                    {resultado.direccion}
                  </button>
                </li>
              ))
            ) : (
              <li className="px-3 py-2 text-[12.5px] text-texto-mutado">
                No encontramos esa dirección — probá tocar el mapa.
              </li>
            )}
          </ul>
        )}
      </div>
      <div className="overflow-hidden rounded-md border border-borde-input">
        <MapContainer center={posicion ?? CENTRO_MENDOZA} zoom={hayUbicacion ? 15 : 12} style={{ height: "220px" }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {hayUbicacion && <Marker position={[latitud, longitud]} icon={iconoMarcador} />}
          <ManejadorClicksMapa onClick={manejarClickMapa} />
          <CentrarMapa latitud={latitud} longitud={longitud} />
          <GestosTactiles />
        </MapContainer>
      </div>
      {buscando && <span className="mt-1.5 block text-xs text-texto-mutado">Buscando dirección…</span>}
      {!buscando && (
        <input
          type="text"
          value={direccion}
          onChange={(e) => onCambiarDireccion(e.target.value)}
          placeholder="Dirección"
          className="mt-1.5 h-[42px] w-full rounded-md border border-borde-input bg-blanco px-3.5 text-[12.5px] text-texto-fuerte outline-none transition-[border-color,box-shadow] duration-150 focus:border-primario focus:shadow-[0_0_0_3px_rgba(124,58,237,0.15)] focus-visible:outline-none"
        />
      )}
      {!hayUbicacion && !buscando && (
        <span className="text-[11.5px] text-peligro">Todavía no marcaste la ubicación.</span>
      )}
    </CampoContenedor>
  );
}
