export const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

/** Error con mensaje seguro para mostrar en un formulario, ya sea que venga
 * del backend (detail de una respuesta no-2xx) o de una validación de cliente. */
export class ErrorFormulario extends Error {
  /** Código HTTP si el error vino del backend; undefined si es una validación de cliente. */
  estado?: number;

  constructor(mensaje: string, estado?: number) {
    super(mensaje);
    this.estado = estado;
  }
}

/** useAuthStore se registra acá al inicializarse para limpiar la sesión ante
 * un 401 de cualquier pedido — evita un import circular (fetchApi -> store ->
 * api/auth -> fetchApi) y hace visible una sesión vencida/perdida en vez de
 * fallar en silencio pedido por pedido (ej. el autocompletado de geocoding,
 * que traga sus propios errores). */
let manejarSesionExpirada: (() => void) | null = null;
export function registrarManejadorSesionExpirada(fn: () => void) {
  manejarSesionExpirada = fn;
}

export async function fetchApi<T>(path: string, opciones: RequestInit = {}): Promise<T> {
  const respuesta = await fetch(`${BASE_URL}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...opciones.headers },
    ...opciones,
  });

  if (!respuesta.ok) {
    if (respuesta.status === 401) {
      manejarSesionExpirada?.();
    }
    const cuerpo = await respuesta.json().catch(() => null);
    throw new ErrorFormulario(cuerpo?.detail ?? "Error de red inesperado.", respuesta.status);
  }

  return respuesta.status === 204 ? (undefined as T) : respuesta.json();
}
