import type {
  EstadoIncidencia,
  IncidenciaCrear,
  IncidenciaPublica,
  ResolucionIncidencia,
} from "../tipos/incidencia";
import { fetchApi } from "./cliente";

const BASE = "/api/v1/incidencias";

export function reportarIncidencia(datos: IncidenciaCrear) {
  return fetchApi<IncidenciaPublica>(BASE, { method: "POST", body: JSON.stringify(datos) });
}

/** Sin `estado` devuelve todas; la pantalla filtra del lado del cliente, pero la
 * API también lo admite. */
export function listarIncidencias(estado?: EstadoIncidencia) {
  return fetchApi<IncidenciaPublica[]>(estado ? `${BASE}?estado=${estado}` : BASE);
}

export function resolverIncidencia(id: string, resolucion: ResolucionIncidencia) {
  return fetchApi<IncidenciaPublica>(`${BASE}/${id}/resolver`, {
    method: "POST",
    body: JSON.stringify({ resolucion }),
  });
}
