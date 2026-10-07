import type { VehiculoPublico } from "./auth";

/** Espeja api/schemas_empresa.py (ChoferDeEmpresa). */
export interface ChoferDeEmpresa {
  id: string;
  nombre_completo: string;
  email: string;
  telefono: string | null;
  activo: boolean;
  vehiculo: VehiculoPublico | null;
  rutas_del_dia: number;
  tiene_ruta_en_curso: boolean;
}
