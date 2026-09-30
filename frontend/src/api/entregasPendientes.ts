import type { EntregaPendientePublica } from "../tipos/entregaPendiente";
import { fetchApi } from "./cliente";

export function listarEntregasPendientes() {
  return fetchApi<EntregaPendientePublica[]>("/api/v1/entregas-pendientes");
}
