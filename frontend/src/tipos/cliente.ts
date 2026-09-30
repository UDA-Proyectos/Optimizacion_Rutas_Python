export interface ClientePublico {
  id: string;
  nombre: string;
  direccion: string;
  latitud: number;
  longitud: number;
  telefono: string | null;
  demanda_carga_default: number | null;
  tiempo_servicio_default: number;
  ventana_inicio_default: number | null;
  ventana_fin_default: number | null;
  activo: boolean;
  fecha_creacion: string;
}

export interface DatosClienteCrear {
  nombre: string;
  direccion: string;
  latitud: number;
  longitud: number;
  telefono: string | null;
  demanda_carga_default: number | null;
  tiempo_servicio_default: number;
  ventana_inicio_default: number | null;
  ventana_fin_default: number | null;
}

export type DatosClienteActualizar = Partial<DatosClienteCrear>;
