import type { DepositoResumen, ParadaRutaPublica } from "../tipos/ruta";

export interface Coordenada {
  latitud: number;
  longitud: number;
}

export function construirUrlGoogleMaps(origen: Coordenada, destino: Coordenada): string {
  return `https://www.google.com/maps/dir/?api=1&origin=${origen.latitud},${origen.longitud}&destination=${destino.latitud},${destino.longitud}`;
}

/** De dónde sale la navegación hacia la parada en_curso: de la posición actual
 * del dispositivo si el chofer activó su ubicación; si no, del depósito (si es
 * la primera del día) o de la parada anterior. `null` si no hay ninguna parada
 * en_curso. Única fuente de esta regla — antes vivía por separado en
 * MapaRutaActiva.tsx y en el header de EscritorioChofer.tsx. */
export function origenNavegacionParaParadaActual(
  deposito: DepositoResumen,
  paradas: ParadaRutaPublica[],
  ubicacion?: Coordenada | null,
): Coordenada | null {
  const indiceActual = paradas.findIndex((parada) => parada.estado === "en_curso");
  if (indiceActual === -1) return null;
  if (ubicacion) return ubicacion;
  if (indiceActual === 0) return { latitud: deposito.latitud, longitud: deposito.longitud };
  const anterior = paradas[indiceActual - 1];
  return { latitud: anterior.latitud_snapshot, longitud: anterior.longitud_snapshot };
}
