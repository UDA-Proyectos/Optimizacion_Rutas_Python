import type { TipoIncidencia } from "./ruta";

export type EstadoIncidencia = "pendiente" | "resuelta";
export type ResolucionIncidencia = "reprogramada" | "cerrada";

/** Espeja api/schemas_incidencias.py — si cambia uno, actualizar el otro a mano. */
export interface IncidenciaPublica {
  id: string;
  tipo: TipoIncidencia;
  descripcion: string | null;
  fecha_hora: string;
  ruta_id: string;
  ruta_fecha: string;
  parada_id: string | null;
  parada_nombre: string | null;
  estado: EstadoIncidencia;
  resolucion: ResolucionIncidencia | null;
  fecha_resolucion: string | null;
  /** Solo la de una parada fallida que todavía no se reprogramó. */
  puede_reprogramarse: boolean;
}

export interface IncidenciaCrear {
  tipo: TipoIncidencia;
  descripcion: string | null;
  parada_id: string | null;
}
