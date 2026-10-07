import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { type ReactNode, useEffect, useState } from "react";
import { MapContainer, Marker, Polyline, TileLayer, ZoomControl, useMap } from "react-leaflet";

import { obtenerGeometriaRutaActiva } from "../../api/rutas";
import type { DepositoResumen, GeometriaRuta, ParadaRutaPublica } from "../../tipos/ruta";
import {
  type Coordenada,
  construirUrlGoogleMaps,
  origenNavegacionParaParadaActual,
} from "../../utilidades/googleMaps";
import { GestosTactiles } from "../mapa/GestosTactiles";
import { combinarClases } from "../ui/combinarClases";

const CENTRO_MENDOZA: [number, number] = [-32.8908, -68.8272];

// Marcadores dibujados en CSS (DivIcon), no imágenes — así el color sale de
// los tokens del sistema y sigue el mismo código de estado que las tarjetas
// (mismo verde que el anillo de "en curso" en la lista y el chip de estado
// de la Ruta). Una vez completada, la parada se saca del mapa — salvo la
// que dio origen al tramo que se está recorriendo ahora mismo (ver
// `paradasVisibles` más abajo): sacarla de inmediato borraba de dónde salía
// el trayecto actual, y quedaba una línea sin punto de partida visible.
//
// El HTML de estos íconos lo consume Leaflet directamente (fuera del árbol
// de React), pero las clases de Tailwind siguen siendo literales completas
// acá abajo — el scanner de Tailwind las encuentra igual, solo la selección
// de cuál usar pasa en runtime, nunca la construcción del string de clases.
const CLASE_MARCADOR: Record<ParadaRutaPublica["estado"], string> = {
  pendiente:
    "h-4 w-4 rounded-full border-[2.5px] border-blanco bg-texto-tenue shadow-[0_1px_4px_rgba(16,24,40,0.4)]",
  en_curso:
    "h-6 w-6 animate-pulso-marcador rounded-full border-[3px] border-blanco bg-exito " +
    "shadow-[0_1px_4px_rgba(16,24,40,0.4)] motion-reduce:animate-none",
  completada:
    "h-4 w-4 rounded-full border-[2.5px] border-blanco bg-exito shadow-[0_1px_4px_rgba(16,24,40,0.4)]",
  fallida:
    "h-4 w-4 rounded-full border-[2.5px] border-blanco bg-peligro shadow-[0_1px_4px_rgba(16,24,40,0.4)]",
};

function iconoParada(estado: ParadaRutaPublica["estado"]) {
  const tamanio = estado === "en_curso" ? 24 : 16;
  return L.divIcon({
    className: "",
    html: `<div class="${CLASE_MARCADOR[estado]}"></div>`,
    iconSize: [tamanio, tamanio],
    iconAnchor: [tamanio / 2, tamanio / 2],
  });
}

const iconoDeposito = L.divIcon({
  className: "",
  html: '<div class="h-[18px] w-[18px] rounded-full border-[2.5px] border-blanco bg-texto-fuerte shadow-[0_1px_4px_rgba(16,24,40,0.45)]"></div>',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
});

// La posición del chofer: punto azul con halo, distinto de los pines de
// parada (verde/gris/rojo) y del depósito (oscuro).
const iconoUbicacion = L.divIcon({
  className: "",
  html: '<div class="h-[18px] w-[18px] rounded-full border-[3px] border-blanco bg-[#2E5CFF] shadow-[0_0_0_6px_rgba(46,92,255,0.22)]"></div>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

function AjustarVista({ puntos }: { puntos: [number, number][] }) {
  const mapa = useMap();
  useEffect(() => {
    if (puntos.length > 0) {
      mapa.fitBounds(puntos, { padding: [28, 28] });
    }
  }, [mapa, puntos]);
  return null;
}

interface Props {
  deposito: DepositoResumen;
  paradas: ParadaRutaPublica[];
  /** false: no dibuja la pill "Ir con Maps" ni la barra inferior propias —
   * el llamador provee su propio overlay via `children`, encimado sobre el
   * mismo contenedor `relative` que envuelve el mapa (uso: escritorio, ver
   * RutaDeHoyEscritorio.tsx). Default true: comportamiento actual, sin
   * cambios para quien no pase estas props (uso: mobile). */
  overlaySimple?: boolean;
  /** Posición actual del chofer, solo si activó su ubicación. */
  ubicacion?: Coordenada | null;
  /** De dónde sale la traza; por defecto, la ruta en curso del chofer. El admin pasa la
   * de una ruta de su flota. */
  cargarGeometria?: () => Promise<GeometriaRuta>;
  children?: ReactNode;
}

export function MapaRutaActiva({
  deposito,
  paradas,
  overlaySimple = true,
  ubicacion = null,
  cargarGeometria = obtenerGeometriaRutaActiva,
  children,
}: Props) {
  const [tramos, setTramos] = useState<[number, number][][]>([]);

  // Saltear una parada reordena el recorrido: la traza se vuelve a pedir
  // cuando cambia la secuencia de paradas, no solo al montar.
  const secuenciaParadas = paradas.map((parada) => parada.id).join(",");
  useEffect(() => {
    cargarGeometria()
      .then((geometria) => setTramos(geometria.tramos))
      .catch(() => setTramos([]));
    // cargarGeometria suele ser una función nueva en cada render: la traza depende de la
    // secuencia de paradas, no de su identidad.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [secuenciaParadas]);

  const indiceProxima = paradas.findIndex((parada) => parada.estado === "en_curso");
  const proximaParada = indiceProxima === -1 ? undefined : paradas[indiceProxima];

  // Una parada completada se saca del mapa — salvo la que dio origen al
  // tramo en curso (la inmediatamente anterior a la próxima parada), que se
  // mantiene visible hasta que ese tramo también se complete. Ver el
  // comentario sobre CLASE_MARCADOR más arriba.
  const paradasVisibles = paradas.filter(
    (parada, indice) => parada.estado !== "completada" || indice === indiceProxima - 1,
  );

  const puntosVisibles: [number, number][] = [
    [deposito.latitud, deposito.longitud],
    ...paradasVisibles.map((parada): [number, number] => [
      parada.latitud_snapshot,
      parada.longitud_snapshot,
    ]),
  ];

  // tramos[i] es el tramo que llega a paradas[i] (depósito→paradas[0],
  // paradas[0]→paradas[1], …). El que llega a la próxima parada es el que
  // se está recorriendo ahora — se dibuja aparte, en otro color, para que
  // se distinga del resto de la ruta (ver el render más abajo). El resto de
  // los tramos ya completados se ocultan a medida que avanza el día; el
  // último tramo (vuelta al depósito) no tiene parada asociada y queda
  // siempre entre los restantes.
  const tramoActual = indiceProxima === -1 ? undefined : tramos[indiceProxima];
  const tramosRestantes = tramos.filter((_, indice) => {
    const estado = paradas[indice]?.estado;
    return indice !== indiceProxima && estado !== "completada" && estado !== "fallida";
  });

  const origenNavegacion = origenNavegacionParaParadaActual(deposito, paradas, ubicacion);
  const overlayPropio = children != null;

  return (
    <div className="relative h-full overflow-hidden rounded-lg border border-borde bg-superficie-hundida shadow-sm">
      {/* Con overlay propio (tarjeta arriba, botones abajo) el zoom va abajo a la derecha,
          por encima de los botones; en pantallas chicas se oculta: ahí se hace zoom con los dedos. */}
      <div
        className={combinarClases(
          "h-full",
          overlayPropio &&
            "[&_.leaflet-bottom.leaflet-right]:mb-[68px] max-lg:[&_.leaflet-control-zoom]:hidden",
        )}
      >
        <MapContainer
          center={CENTRO_MENDOZA}
          zoom={13}
          zoomControl={!overlayPropio}
          style={{ height: "100%" }}
        >
          {overlayPropio && <ZoomControl position="bottomright" />}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {tramosRestantes.length > 0 && (
            <Polyline
              positions={tramosRestantes}
              pathOptions={{ color: "#7C3AED", weight: 3, opacity: 0.55 }}
            />
          )}
          {tramoActual && tramoActual.length > 0 && (
            <Polyline
              positions={tramoActual}
              pathOptions={{ color: "#12B76A", weight: 4, opacity: 0.85 }}
            />
          )}
          <Marker position={[deposito.latitud, deposito.longitud]} icon={iconoDeposito} />
          {paradasVisibles.map((parada) => (
            <Marker
              key={parada.id}
              position={[parada.latitud_snapshot, parada.longitud_snapshot]}
              icon={iconoParada(parada.estado)}
            />
          ))}
          {ubicacion && (
            <Marker
              position={[ubicacion.latitud, ubicacion.longitud]}
              icon={iconoUbicacion}
              zIndexOffset={1000}
            />
          )}
          {/* La vista se ajusta solo a la ruta: si incluyera la posición, el
              mapa saltaría en cada actualización del GPS. */}
          <AjustarVista puntos={puntosVisibles} />
          <GestosTactiles />
        </MapContainer>
      </div>

      {overlaySimple && proximaParada && origenNavegacion && (
        <a
          className="absolute top-3 right-3 z-[500] flex h-[34px] items-center rounded-pill border border-borde bg-[rgba(255,255,255,0.92)] px-[13px] text-[10.5px] font-semibold text-texto-fuerte shadow-sm backdrop-blur-[8px]"
          href={construirUrlGoogleMaps(origenNavegacion, {
            latitud: proximaParada.latitud_snapshot,
            longitud: proximaParada.longitud_snapshot,
          })}
          target="_blank"
          rel="noopener noreferrer"
        >
          Ir con Maps
        </a>
      )}

      {overlaySimple && proximaParada && (
        <div className="absolute right-3 bottom-2.5 left-3 z-[500] flex items-center gap-2.5 rounded-md border border-borde bg-[rgba(255,255,255,0.94)] px-3 py-2.5 shadow-md backdrop-blur-[8px]">
          <span className="h-2 w-2 shrink-0 rounded-full bg-exito" />
          <p className="min-w-0 flex-1 truncate text-[11.5px] font-semibold text-texto-fuerte">
            {proximaParada.direccion_snapshot}
          </p>
        </div>
      )}

      {children}
    </div>
  );
}
