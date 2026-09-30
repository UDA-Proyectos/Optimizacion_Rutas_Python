import type { TipoIncidencia } from "./ruta";

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
}

export interface IncidenciaCrear {
  tipo: TipoIncidencia;
  descripcion: string | null;
  parada_id: string | null;
}
