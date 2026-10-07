import type { ChoferDeEmpresa } from "../tipos/empresa";
import type { GeometriaRuta, RutaHistorialItem, RutaPublica } from "../tipos/ruta";
import { fetchApi } from "./cliente";

const BASE = "/api/v1/empresa";

/** `fecha` es el día local (YYYY-MM-DD) para el resumen de rutas de cada chofer. */
export function listarChoferes(fecha: string) {
  return fetchApi<ChoferDeEmpresa[]>(`${BASE}/choferes?fecha=${fecha}`);
}

/** Rutas no canceladas de toda la flota en un día (YYYY-MM-DD), con sus paradas. */
export function listarRutasDeLaFlota(fecha: string) {
  return fetchApi<RutaPublica[]>(`${BASE}/rutas?fecha=${fecha}`);
}

export function obtenerRutaDeLaFlota(id: string) {
  return fetchApi<RutaPublica>(`${BASE}/rutas/${id}`);
}

export function obtenerGeometriaRutaDeLaFlota(id: string) {
  return fetchApi<GeometriaRuta>(`${BASE}/rutas/${id}/geometria`);
}

export function obtenerHistorialDeLaFlota(desde: string, hasta: string, choferId?: string) {
  const filtro = choferId ? `&chofer_id=${choferId}` : "";
  return fetchApi<RutaHistorialItem[]>(`${BASE}/historial?desde=${desde}&hasta=${hasta}${filtro}`);
}
