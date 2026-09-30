/** Espeja api/schemas_entregas_pendientes.py: una entrega reprogramada que se
 * ofrece ya cargada al armar la próxima ruta. */
export interface EntregaPendientePublica {
  id: string;
  cliente_id: string;
  cliente_nombre: string;
  cliente_direccion: string;
  carga_kg: number;
  unidades: number;
  ventana_inicio: number | null;
  ventana_fin: number | null;
  fecha_creacion: string;
  /** Día de la ruta en que no se pudo entregar (YYYY-MM-DD). */
  fecha_origen: string;
}
