import { create } from "zustand";

import { cerrarSesion as apiCerrarSesion, iniciarSesion as apiIniciarSesion, obtenerUsuarioActual } from "../api/auth";
import { registrarManejadorSesionExpirada } from "../api/cliente";
import type { UsuarioPublico } from "../tipos/auth";
import {
  borrarCacheOffline,
  guardarUsuarioCache,
  leerUsuarioCache,
} from "../utilidades/almacenRuta";

interface EstadoAuth {
  usuario: UsuarioPublico | null;
  cargando: boolean;
  estaAutenticado: boolean;
  cargarSesion: () => Promise<void>;
  iniciarSesion: (email: string, contrasena: string) => Promise<void>;
  cerrarSesion: () => Promise<void>;
  establecerUsuario: (usuario: UsuarioPublico) => void;
}

// Sin middleware `persist`: la sesión SIEMPRE se re-hidrata desde el backend
// (cookie httpOnly + GET /me), nunca desde localStorage. La única excepción es
// abrir la app sin red (ver cargarSesion): ahí se usa la copia del perfil en
// IndexedDB solo para mostrar la ruta guardada, en modo lectura.
export const useAuthStore = create<EstadoAuth>((set) => ({
  usuario: null,
  cargando: true,
  estaAutenticado: false,

  cargarSesion: async () => {
    try {
      const usuario = await obtenerUsuarioActual();
      set({ usuario, estaAutenticado: true, cargando: false });
      void guardarUsuarioCache(usuario);
    } catch (error) {
      // fetch rechaza con TypeError cuando no hay red: no significa que la
      // sesión se perdió (eso es un 401, que ya limpia todo en fetchApi).
      const copia = error instanceof TypeError ? await leerUsuarioCache() : null;
      if (copia) {
        set({ usuario: copia, estaAutenticado: true, cargando: false });
      } else {
        set({ usuario: null, estaAutenticado: false, cargando: false });
      }
    }
  },

  iniciarSesion: async (email, contrasena) => {
    const usuario = await apiIniciarSesion({ email, contrasena });
    set({ usuario, estaAutenticado: true });
    void guardarUsuarioCache(usuario);
  },

  cerrarSesion: async () => {
    // La copia local es de este usuario: se borra siempre, aunque el pedido de
    // logout falle (ej. sin conexión).
    await borrarCacheOffline();
    await apiCerrarSesion();
    set({ usuario: null, estaAutenticado: false });
  },

  establecerUsuario: (usuario) => {
    set({ usuario, estaAutenticado: true });
    void guardarUsuarioCache(usuario);
  },
}));

// Cualquier 401 (sesión vencida o cookie perdida) limpia el store acá mismo
// — RutaProtegida ya redirige solo a /login apenas estaAutenticado es false.
registrarManejadorSesionExpirada(() => {
  void borrarCacheOffline();
  useAuthStore.setState({ usuario: null, estaAutenticado: false });
});
