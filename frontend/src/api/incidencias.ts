import type { IncidenciaCrear, IncidenciaPublica } from "../tipos/incidencia";
import { fetchApi } from "./cliente";

const BASE = "/api/v1/incidencias";

export function reportarIncidencia(datos: IncidenciaCrear) {
  return fetchApi<IncidenciaPublica>(BASE, { method: "POST", body: JSON.stringify(datos) });
}

export function listarIncidencias() {
  return fetchApi<IncidenciaPublica[]>(BASE);
}
