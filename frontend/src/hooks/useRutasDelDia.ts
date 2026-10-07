import { useEffect, useRef, useState } from "react";

import { obtenerRutaActiva, obtenerRutasDelDia } from "../api/rutas";
import type { RutaPublica } from "../tipos/ruta";
import { guardarRutasCache, leerRutasCache } from "../utilidades/almacenRuta";
import { hoyLocal, sumarDias } from "../utilidades/fechas";
import { useEnLinea } from "./useEnLinea";

/** Firma de `ejecutar` — la reciben por prop RutaDeHoyEscritorio y VistaEnCursoRuta. */
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

/** Reemplaza (o agrega) una ruta en la lista del día, conservando el orden. */
function conRuta(rutas: RutaPublica[], ruta: RutaPublica): RutaPublica[] {
  return rutas.some((r) => r.id === ruta.id)
    ? rutas.map((r) => (r.id === ruta.id ? ruta : r))
    : [...rutas, ruta];
}

/** Las rutas de un día (con un selector de día) y cuál de ellas se está viendo.
 *
 * - `ruta` es la seleccionada: la en curso si existe, y si no la primera del día.
 * - `enCurso` es la única ruta en curso del chofer, sea del día que sea: una
 *   iniciada ayer y sin terminar sigue siendo la actual hoy.
 *
 * Sin conexión muestra la última copia guardada de hoy y bloquea las acciones
 * que escriben — no se encolan: no todas son idempotentes. */
export function useRutasDelDia() {
  const enLinea = useEnLinea();
  const [fecha, setFecha] = useState(hoyLocal);
  const [rutas, setRutas] = useState<RutaPublica[]>([]);
  const [enCurso, setEnCurso] = useState<RutaPublica | null>(null);
  const [seleccionadaId, setSeleccionadaId] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [falloRed, setFalloRed] = useState(false);
  // Cuándo se guardó la copia local que se está mostrando (null: es lo actual).
  const [copiaGuardadaEn, setCopiaGuardadaEn] = useState<number | null>(null);
  // Ruta a seleccionar al terminar de cargar el próximo día (ver irARuta).
  const preferidaAlCargar = useRef<string | null>(null);

  const sinConexion = !enLinea || falloRed;

  /** Elige qué ruta mostrar: la pedida si sigue en el día, si no la en curso
   * que esté en el día, si no la primera. */
  function elegirSeleccion(
    delDia: RutaPublica[],
    enCursoActual: RutaPublica | null,
    preferida: string | null,
  ): string | null {
    if (preferida && delDia.some((r) => r.id === preferida)) return preferida;
    if (enCursoActual && delDia.some((r) => r.id === enCursoActual.id)) return enCursoActual.id;
    if (enCursoActual && delDia.length === 0) return enCursoActual.id;
    return delDia[0]?.id ?? null;
  }

  async function cargar(dia: string, preferida: string | null = null) {
    try {
      const [delDia, actual] = await Promise.all([obtenerRutasDelDia(dia), obtenerRutaActiva()]);
      setFalloRed(false);
      setCopiaGuardadaEn(null);
      setRutas(delDia);
      setEnCurso(actual);
      setSeleccionadaId(elegirSeleccion(delDia, actual, preferida));
      if (dia === hoyLocal()) {
        await guardarRutasCache({ fecha: dia, rutas: delDia, enCurso: actual });
      }
    } catch (e) {
      if (!esFalloDeRed(e)) {
        throw e;
      }
      setFalloRed(true);
      const copia = await leerRutasCache();
      if (copia && copia.fecha === dia) {
        setRutas(copia.rutas);
        setEnCurso(copia.enCurso);
        setSeleccionadaId(elegirSeleccion(copia.rutas, copia.enCurso, preferida));
        setCopiaGuardadaEn(copia.guardadaEn);
      }
    }
  }

  useEffect(() => {
    const preferida = preferidaAlCargar.current;
    preferidaAlCargar.current = null;
    // oxlint no distingue que los setState ocurren después de un await dentro
    // de cargar() — no hay setState síncrono ni loop de renders acá.
    // oxlint-disable-next-line react/set-state-in-effect
    cargar(fecha, preferida).finally(() => setCargando(false));
    // Se vuelve a pedir al cambiar de día; `cargar` es estable para este fin.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fecha]);

  useEffect(() => {
    // Mientras no hay conexión, reintenta solo: al volver la señal se refresca
    // desde el servidor y las acciones se habilitan sin tocar nada.
    if (!sinConexion) return;
    const reintentar = () => cargar(fecha, seleccionadaId).catch(() => {});
    const id = setInterval(reintentar, REINTENTO_SIN_CONEXION_MS);
    window.addEventListener("online", reintentar);
    return () => {
      clearInterval(id);
      window.removeEventListener("online", reintentar);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sinConexion, fecha, seleccionadaId]);

  const ruta =
    rutas.find((r) => r.id === seleccionadaId) ??
    (enCurso && enCurso.id === seleccionadaId ? enCurso : null);

  function moverDia(dias: number) {
    setFecha((actual) => sumarDias(actual, dias));
  }

  /** Va a un día concreto, lo vuelve a pedir y deja seleccionada esa ruta (ej.
   * tras guardar una ruta nueva, o para "ir a la ruta en curso"). */
  function irARuta(dia: string, rutaId: string) {
    preferidaAlCargar.current = rutaId;
    if (dia === fecha) {
      preferidaAlCargar.current = null;
      void cargar(dia, rutaId).catch(() => {});
    } else {
      // El efecto de `fecha` recarga y selecciona la ruta pedida.
      setFecha(dia);
    }
  }

  /** Volver a pedir lo visible, p. ej. tras armar o editar una ruta en otra pantalla. */
  async function recargar(preferida: string | null = seleccionadaId) {
    await cargar(fecha, preferida);
  }

  /** Iniciar/completar devuelven la Ruta actualizada — se usa tal cual en vez de
   * recargar, porque una ruta recién completada ya no es "la en curso" y un GET
   * pisaría el resumen final antes de que el chofer llegue a verlo. Cancelar no
   * devuelve una Ruta (queda cancelada y sale de la lista), así que siempre
   * recarga. */
  const ejecutar: EjecutarAccionRuta = async (accion, mensajeError) => {
    setError(null);
    if (sinConexion) {
      setError(MENSAJE_SIN_CONEXION);
      return;
    }
    setEnviando(true);
    try {
      const resultado = await accion();
      if (resultado) {
        setRutas((actuales) => (resultado.fecha === fecha ? conRuta(actuales, resultado) : actuales));
        setEnCurso((actual) => {
          if (resultado.estado === "en_curso") return resultado;
          return actual?.id === resultado.id ? null : actual;
        });
        setSeleccionadaId(resultado.id);
      } else {
        await cargar(fecha);
      }
      if (fecha === hoyLocal()) {
        // Mantiene la copia offline al día tras cada acción.
        void (async () => {
          const copia = await leerRutasCache();
          if (copia?.fecha === fecha) {
            const nuevas = resultado ? conRuta(copia.rutas, resultado) : copia.rutas;
            await guardarRutasCache({
              fecha,
              rutas: nuevas,
              enCurso: resultado?.estado === "en_curso" ? resultado : copia.enCurso,
            });
          }
        })();
      }
    } catch (e) {
      if (esFalloDeRed(e)) {
        setFalloRed(true);
        setError(MENSAJE_SIN_CONEXION);
      } else {
        setError(e instanceof Error && e.message ? e.message : mensajeError);
      }
    } finally {
      setEnviando(false);
    }
  };

  return {
    fecha,
    moverDia,
    irAHoy: () => setFecha(hoyLocal()),
    irARuta,
    rutas,
    enCurso,
    ruta,
    seleccionadaId,
    seleccionarRuta: setSeleccionadaId,
    cargando,
    enviando,
    error,
    sinConexion,
    copiaGuardadaEn,
    recargar,
    ejecutar,
  };
}

