import { fetchApi } from "./cliente";
import type {
  GeometriaRuta,
  MotivoFalloParada,
  OptimizarRutaRequest,
  RutaHistorialItem,
  RutaPreview,
  RutaPublica,
} from "../tipos/ruta";

const BASE = "/api/v1/rutas";

export function optimizarRuta(datos: OptimizarRutaRequest) {
  return fetchApi<RutaPreview>(`${BASE}/optimizar`, {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

export function confirmarRuta(datos: OptimizarRutaRequest) {
  return fetchApi<RutaPublica>(`${BASE}/confirmar`, {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

export function editarRuta(datos: OptimizarRutaRequest) {
  return fetchApi<RutaPublica>(`${BASE}/activa`, {
    method: "PUT",
    body: JSON.stringify(datos),
  });
}

export function eliminarRuta() {
  return fetchApi<{ mensaje: string }>(`${BASE}/activa`, { method: "DELETE" });
}

export function iniciarRuta() {
  return fetchApi<RutaPublica>(`${BASE}/activa/iniciar`, { method: "POST" });
}

export function registrarLlegada(paradaId: string) {
  return fetchApi<RutaPublica>(`${BASE}/activa/paradas/${paradaId}/llegada`, {
    method: "POST",
  });
}

export function completarParada(paradaId: string) {
  return fetchApi<RutaPublica>(`${BASE}/activa/paradas/${paradaId}/completar`, {
    method: "POST",
  });
}

/** `reprogramar`: dejar la entrega guardada para la próxima ruta en el mismo paso. */
export function fallarParada(paradaId: string, motivo: MotivoFalloParada, reprogramar = false) {
  return fetchApi<RutaPublica>(`${BASE}/activa/paradas/${paradaId}/fallar`, {
    method: "POST",
    body: JSON.stringify({ motivo, reprogramar }),
  });
}

export function saltearParada(paradaId: string) {
  return fetchApi<RutaPublica>(`${BASE}/activa/paradas/${paradaId}/saltear`, {
    method: "POST",
  });
}

export function obtenerRutaActiva() {
  return fetchApi<RutaPublica | null>(`${BASE}/activa`);
}

export function obtenerGeometriaRutaActiva() {
  return fetchApi<GeometriaRuta>(`${BASE}/activa/geometria`);
}

export function obtenerHistorialRutas(desde: string, hasta: string) {
  return fetchApi<RutaHistorialItem[]>(
    `${BASE}/historial?desde=${desde}&hasta=${hasta}`,
  );
}

export function obtenerRutaHistorial(id: string) {
  return fetchApi<RutaPublica>(`${BASE}/historial/${id}`);
}
