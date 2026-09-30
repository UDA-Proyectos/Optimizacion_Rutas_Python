export type EstadoRuta = "planificada" | "en_curso" | "completada" | "cancelada";
export type EstadoParada = "pendiente" | "en_curso" | "completada" | "fallida";
export type TipoProblema = "CVRP" | "VRPTW";
export type TipoIncidencia =
  | "cliente_ausente"
  | "rechazo_entrega"
  | "direccion_incorrecta"
  | "mercaderia_danada"
  | "problema_vehiculo"
  | "otro";

/** Motivos válidos para marcar *una parada* como no entregada — un problema
 * del vehículo no entra, se reporta como incidencia general (ver
 * api/schemas_rutas.py:FallarParadaRequest). */
export type MotivoFalloParada = Exclude<TipoIncidencia, "problema_vehiculo">;

export interface ParadaSeleccionada {
  cliente_id: string;
  carga_kg: number;
  unidades: number;
  ventana_inicio: number | null;
  ventana_fin: number | null;
}

export interface OptimizarRutaRequest {
  paradas: ParadaSeleccionada[];
  usa_ventanas_horarias: boolean;
  /** null/omitido: el primer depósito del chofer. */
  deposito_id?: string | null;
  /** Día (YYYY-MM-DD, calendario del chofer) de la ruta; omitido: hoy. */
  fecha?: string | null;
  /** Para distinguir varias rutas del mismo día. */
  nombre?: string | null;
}

export interface ParadaPreview {
  cliente_id: string;
  nombre: string;
  direccion: string;
  orden: number;
  carga_kg: number;
  unidades: number;
  distancia_acumulada_m: number;
  ventana_inicio: number | null;
  ventana_fin: number | null;
  hora_estimada_llegada: number | null;
}

export interface RutaPreview {
  paradas: ParadaPreview[];
  distancia_total_m: number;
  carga_total_kg: number;
  distancia_sin_optimizar_m: number;
  ahorro_m: number;
  explicacion: string;
  usa_ventanas_horarias: boolean;
  hora_fin_estimada_min: number | null;
}

export interface GeometriaRuta {
  tramos: [number, number][][];
}

export interface ParadaRutaPublica {
  id: string;
  cliente_id: string;
  orden: number;
  estado: EstadoParada;
  nombre_snapshot: string;
  direccion_snapshot: string;
  latitud_snapshot: number;
  longitud_snapshot: number;
  demanda_carga_snapshot: number;
  unidades_snapshot: number;
  distancia_acumulada_m: number;
  ventana_inicio_snapshot: number | null;
  ventana_fin_snapshot: number | null;
  hora_estimada_llegada: number | null;
  hora_real_llegada: string | null;
  hora_real_salida: string | null;
  veces_salteada: number;
  motivo_fallo: TipoIncidencia | null;
  en_riesgo: boolean;
  ventana_cumplida: boolean | null;
}

export interface DepositoResumen {
  latitud: number;
  longitud: number;
}

/** Espeja api/schemas_rutas.py:ResumenRuta. La distancia es la planificada:
 * no se registra el recorrido real del vehículo. */
export interface ResumenRutaDatos {
  duracion_min: number | null;
  paradas_completadas: number;
  paradas_fallidas: number;
  paradas_salteadas: number;
  carga_entregada_kg: number;
  incidencias: number;
  distancia_planificada_m: number | null;
  ventanas_cumplidas: number | null;
  ventanas_evaluadas: number | null;
  ventanas_cumplidas_pct: number | null;
}

export interface RutaPublica {
  id: string;
  fecha: string;
  nombre: string | null;
  estado: EstadoRuta;
  tipo_problema: TipoProblema;
  distancia_total_m: number | null;
  hora_inicio_real: string | null;
  hora_fin_real: string | null;
  hora_fin_estimada_min: number | null;
  fecha_creacion: string;
  deposito: DepositoResumen;
  capacidad_vehiculo_kg: number;
  explicacion: string | null;
  incidencias_total: number;
  paradas: ParadaRutaPublica[];
  usa_ventanas_horarias: boolean;
  /** null salvo en una ruta completada. */
  resumen: ResumenRutaDatos | null;
}

export interface RutaHistorialItem {
  id: string;
  fecha: string;
  nombre: string | null;
  estado: EstadoRuta;
  tipo_problema: TipoProblema;
  distancia_total_m: number | null;
  paradas_total: number;
  paradas_completadas: number;
  paradas_fallidas: number;
  incidencias_total: number;
  usa_ventanas_horarias: boolean;
}
