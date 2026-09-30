import { fetchApi } from "./cliente";
import type {
  CodigoInvitacionPublico,
  DatosCambiarContrasena,
  DatosLogin,
  DatosPerfilActualizar,
  DatosRegistroChoferIndependiente,
  DatosRegistroChoferInvitado,
  DatosRegistroEmpresa,
  DatosVehiculoActualizar,
  RegistroEmpresaResponse,
  UsuarioPublico,
} from "../tipos/auth";

const BASE = "/api/v1/auth";

export function registrarChoferIndependiente(datos: DatosRegistroChoferIndependiente) {
  return fetchApi<UsuarioPublico>(`${BASE}/registro/chofer-independiente`, {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

export function registrarEmpresa(datos: DatosRegistroEmpresa) {
  return fetchApi<RegistroEmpresaResponse>(`${BASE}/registro/empresa`, {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

export function registrarChoferInvitado(datos: DatosRegistroChoferInvitado) {
  return fetchApi<UsuarioPublico>(`${BASE}/registro/chofer-invitado`, {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

export function iniciarSesion(datos: DatosLogin) {
  return fetchApi<UsuarioPublico>(`${BASE}/login`, {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

export function cerrarSesion() {
  return fetchApi<{ mensaje: string }>(`${BASE}/logout`, { method: "POST" });
}

export function obtenerUsuarioActual() {
  return fetchApi<UsuarioPublico>(`${BASE}/me`);
}

export function actualizarPerfil(datos: DatosPerfilActualizar) {
  return fetchApi<UsuarioPublico>(`${BASE}/me`, { method: "PATCH", body: JSON.stringify(datos) });
}

export function actualizarVehiculo(datos: DatosVehiculoActualizar) {
  return fetchApi<UsuarioPublico>(`${BASE}/me/vehiculo`, {
    method: "PATCH",
    body: JSON.stringify(datos),
  });
}

export function cambiarContrasena(datos: DatosCambiarContrasena) {
  return fetchApi<{ mensaje: string }>(`${BASE}/cambiar-contrasena`, {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

export function generarCodigoInvitacion() {
  return fetchApi<CodigoInvitacionPublico>(`${BASE}/invitaciones`, { method: "POST" });
}

export function listarCodigosInvitacion() {
  return fetchApi<CodigoInvitacionPublico[]>(`${BASE}/invitaciones`);
}
