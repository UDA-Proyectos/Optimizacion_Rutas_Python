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

/** Las rutas de un día (YYYY-MM-DD): planificadas, en curso y completadas. */
export function obtenerRutasDelDia(fecha: string) {
  return fetchApi<RutaPublica[]>(`${BASE}?fecha=${fecha}`);
}

export function editarRuta(rutaId: string, datos: OptimizarRutaRequest) {
  return fetchApi<RutaPublica>(`${BASE}/${rutaId}`, {
    method: "PUT",
    body: JSON.stringify(datos),
  });
}

export function eliminarRuta(rutaId: string) {
  return fetchApi<{ mensaje: string }>(`${BASE}/${rutaId}`, { method: "DELETE" });
}

/** `fechaHoy`: el día local del chofer, porque el servidor no sabe en qué huso está. */
export function iniciarRuta(rutaId: string, fechaHoy: string) {
  return fetchApi<RutaPublica>(`${BASE}/${rutaId}/iniciar`, {
    method: "POST",
    body: JSON.stringify({ fecha_hoy: fechaHoy }),
  });
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
