export type RolUsuario = "chofer" | "admin";
export type PlanSuscripcion = "prueba" | "basico" | "premium";
export type TipoVehiculo = "moto" | "auto" | "camioneta" | "furgon" | "camion";

export interface EmpresaPublica {
  id: string;
  nombre: string;
  plan: PlanSuscripcion;
  fecha_fin_prueba: string | null;
  fecha_creacion: string;
}

export interface VehiculoPublico {
  id: string;
  tipo_vehiculo: TipoVehiculo;
  patente: string;
  capacidad_carga_kg: number;
  activo: boolean;
}

export interface UsuarioPublico {
  id: string;
  email: string;
  nombre_completo: string;
  rol: RolUsuario;
  empresa_id: string | null;
  telefono: string | null;
  vehiculo: VehiculoPublico | null;
  tiene_contrasena: boolean;
  plan: PlanSuscripcion;
  fecha_fin_prueba: string | null;
  fecha_creacion: string;
}

export interface RegistroEmpresaResponse {
  usuario: UsuarioPublico;
  empresa: EmpresaPublica;
}

export interface CodigoInvitacionPublico {
  id: string;
  codigo: string;
  usado: boolean;
  fecha_creacion: string;
  fecha_uso: string | null;
}

interface DatosPersonaBase {
  email: string;
  contrasena: string;
  confirmar_contrasena: string;
  nombre_completo: string;
}

interface DatosVehiculo {
  telefono: string;
  tipo_vehiculo: TipoVehiculo;
  patente: string;
  capacidad_carga_kg: number;
}

/** Espeja api/schemas_auth.py (ProveedoresAuth, RegistroGooglePendiente,
 * CompletarRegistroGoogle). */
export interface ProveedoresAuth {
  google: boolean;
}

export interface RegistroGooglePendiente {
  email: string;
  nombre_completo: string;
}

export type DatosCompletarRegistroGoogle = DatosVehiculo & { nombre_completo: string };

export type DatosRegistroChoferIndependiente = DatosPersonaBase & DatosVehiculo;

export interface DatosRegistroEmpresa extends DatosPersonaBase {
  nombre_empresa: string;
}

export type DatosRegistroChoferInvitado = DatosPersonaBase &
  DatosVehiculo & {
    codigo_invitacion: string;
  };

/** Espeja api/schemas_auth.py (PerfilActualizar, VehiculoActualizar,
 * CambiarContrasena) — si cambia uno, actualizar el otro a mano. */
export interface DatosPerfilActualizar {
  nombre_completo?: string;
  telefono?: string;
}

export interface DatosVehiculoActualizar {
  tipo_vehiculo?: TipoVehiculo;
  patente?: string;
  capacidad_carga_kg?: number;
}

export interface DatosCambiarContrasena {
  contrasena_actual: string;
  contrasena_nueva: string;
  confirmar_contrasena_nueva: string;
}

export interface DatosLogin {
  email: string;
  contrasena: string;
}
