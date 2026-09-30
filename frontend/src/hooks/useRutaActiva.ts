import { useEffect, useState } from "react";

import { obtenerRutaActiva } from "../api/rutas";
import type { RutaPublica } from "../tipos/ruta";
import { borrarRutaCache, guardarRutaCache, leerRutaCache } from "../utilidades/almacenRuta";
import { useEnLinea } from "./useEnLinea";

/** Firma de `ejecutar` — compartida por los componentes de escritorio
 * (RutaDeHoyEscritorio.tsx, VistaEnCursoRuta.tsx) que la reciben por prop
 * desde acá, para no redeclarar el tipo en cada uno. */
export type EjecutarAccionRuta = (
  accion: () => Promise<RutaPublica | void>,
  mensajeError: string,
) => Promise<void>;

const MENSAJE_SIN_CONEXION = "Necesitás conexión para hacer esto. Se habilita cuando vuelva la señal.";
const REINTENTO_SIN_CONEXION_MS = 10_000;

/** `fetch` rechaza con TypeError ante un fallo de red (a diferencia de un error
 * HTTP, que fetchApi convierte en ErrorFormulario). */
function esFalloDeRed(error: unknown): boolean {
  return error instanceof TypeError;
}

/** Solo una ruta que todavía se puede operar vale la pena tener offline. */
async function sincronizarCache(ruta: RutaPublica | null): Promise<void> {
  if (ruta && (ruta.estado === "planificada" || ruta.estado === "en_curso")) {
    await guardarRutaCache(ruta);
  } else {
    await borrarRutaCache();
  }
}

/** Estado + acciones sobre "la ruta activa de hoy" — compartido por la vista
 * mobile (PestanaInicio.tsx) y el panel de escritorio del chofer
 * independiente (RutaDeHoyEscritorio.tsx), mismo comportamiento en ambos.
 *
 * Sin conexión (dispositivo offline o servidor inalcanzable) muestra la última
 * copia guardada de la ruta en modo lectura y bloquea las acciones que
 * escriben — no se encolan: no todas son idempotentes. */
export function useRutaActiva() {
  const enLinea = useEnLinea();
  const [ruta, setRuta] = useState<RutaPublica | null>(null);
  const [cargando, setCargando] = useState(true);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [falloRed, setFalloRed] = useState(false);
  // Cuándo se guardó la copia local que se está mostrando (null: es la ruta en vivo).
  const [copiaGuardadaEn, setCopiaGuardadaEn] = useState<number | null>(null);

  const sinConexion = !enLinea || falloRed;

  async function recargar() {
    try {
      const nueva = await obtenerRutaActiva();
      setFalloRed(false);
      setCopiaGuardadaEn(null);
      setRuta(nueva);
      await sincronizarCache(nueva);
    } catch (e) {
      if (!esFalloDeRed(e)) {
        throw e;
      }
      setFalloRed(true);
      const copia = await leerRutaCache();
      if (copia) {
        setRuta(copia.ruta);
        setCopiaGuardadaEn(copia.guardadaEn);
      }
    }
  }

  useEffect(() => {
    // oxlint no distingue que setRuta ocurre después de un await dentro de
    // recargar() — no hay setState síncrono ni loop de renders acá.
    // oxlint-disable-next-line react/set-state-in-effect
    recargar().finally(() => setCargando(false));
  }, []);

  useEffect(() => {
    // Mientras no hay conexión, reintenta solo: al volver la señal la ruta se
    // refresca desde el servidor y las acciones se habilitan sin tocar nada.
    if (!sinConexion) return;
    const id = setInterval(() => {
      recargar().catch(() => {});
    }, REINTENTO_SIN_CONEXION_MS);
    const alVolver = () => recargar().catch(() => {});
    window.addEventListener("online", alVolver);
    return () => {
      clearInterval(id);
      window.removeEventListener("online", alVolver);
    };
  }, [sinConexion]);

  /** Iniciar/completar devuelven la Ruta actualizada — la usamos tal cual en
   * vez de recargar vía GET /activa, que ya no encuentra una ruta recién
   * completada (esa deja de contar como "activa") y pisaría el resumen
   * final con el estado vacío antes de que el chofer llegue a verlo.
   * Eliminar no devuelve una Ruta (queda cancelada, deja de ser "activa"),
   * así que su acción se pasa sin valor de retorno y siempre recarga. */
  async function ejecutar(accion: () => Promise<RutaPublica | void>, mensajeError: string) {
    setError(null);
    if (sinConexion) {
      setError(MENSAJE_SIN_CONEXION);
      return;
    }
    setEnviando(true);
    try {
      const resultado = await accion();
      if (resultado) {
        setRuta(resultado);
        await sincronizarCache(resultado);
      } else {
        await recargar();
      }
    } catch (e) {
      if (esFalloDeRed(e)) {
        setFalloRed(true);
        setError(MENSAJE_SIN_CONEXION);
      } else {
        setError(mensajeError);
      }
    } finally {
      setEnviando(false);
    }
  }

  return { ruta, cargando, enviando, error, sinConexion, copiaGuardadaEn, recargar, ejecutar };
}
