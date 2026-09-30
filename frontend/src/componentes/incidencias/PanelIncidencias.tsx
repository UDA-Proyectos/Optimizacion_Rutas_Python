import { useState } from "react";

import { resolverIncidencia } from "../../api/incidencias";
import type { IncidenciaPublica, ResolucionIncidencia } from "../../tipos/incidencia";
import { ETIQUETA_MOTIVO } from "../../utilidades/motivosFallo";
import { combinarClases } from "../ui/combinarClases";
import { BannerError } from "../ui/Formulario";
import { TextoVacio } from "../ui/TextoVacio";

type Filtro = "pendiente" | "resuelta" | "todas";

const ETIQUETA_FILTRO: Record<Filtro, string> = {
  pendiente: "Pendientes",
  resuelta: "Resueltas",
  todas: "Todas",
};

const TEXTO_VACIO: Record<Filtro, string> = {
  pendiente: "No tenés incidencias pendientes.",
  resuelta: "Todavía no resolviste ninguna incidencia.",
  todas: "No reportaste ninguna incidencia todavía.",
};

const ETIQUETA_RESOLUCION: Record<ResolucionIncidencia, string> = {
  reprogramada: "Reprogramada para la próxima ruta",
  cerrada: "Cerrada",
};

function formatearFechaHora(marca: string): string {
  return new Date(marca).toLocaleString([], {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

interface Props {
  incidencias: IncidenciaPublica[];
  /** Sin conexión las acciones que escriben se bloquean. */
  sinConexion: boolean;
  /** Se llama tras resolver una incidencia, para volver a pedir el listado. */
  onActualizar: () => void;
}

export function PanelIncidencias({ incidencias, sinConexion, onActualizar }: Props) {
  const [filtro, setFiltro] = useState<Filtro>("pendiente");
  const [resolviendoId, setResolviendoId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const cuentas: Record<Filtro, number> = {
    pendiente: incidencias.filter((i) => i.estado === "pendiente").length,
    resuelta: incidencias.filter((i) => i.estado === "resuelta").length,
    todas: incidencias.length,
  };
  const visibles = incidencias.filter((i) => filtro === "todas" || i.estado === filtro);

  async function resolver(incidencia: IncidenciaPublica, resolucion: ResolucionIncidencia) {
    setError(null);
    setResolviendoId(incidencia.id);
    try {
      await resolverIncidencia(incidencia.id, resolucion);
      onActualizar();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo resolver la incidencia.");
    } finally {
      setResolviendoId(null);
    }
  }

  return (
    <div className="mx-auto flex max-w-[720px] flex-col gap-3">
      <div className="flex gap-1.5" role="tablist" aria-label="Filtrar incidencias">
        {(Object.keys(ETIQUETA_FILTRO) as Filtro[]).map((clave) => (
          <button
            key={clave}
            type="button"
            role="tab"
            aria-selected={filtro === clave}
            onClick={() => setFiltro(clave)}
            className={combinarClases(
              "h-9 rounded-pill px-3.5 text-[12.5px] font-semibold",
              filtro === clave
                ? "bg-primario text-blanco"
                : "border border-borde-input bg-blanco text-texto-cuerpo",
            )}
          >
            {ETIQUETA_FILTRO[clave]} · {cuentas[clave]}
          </button>
        ))}
      </div>

      {error && <BannerError>{error}</BannerError>}

      {visibles.length === 0 ? (
        <TextoVacio>{TEXTO_VACIO[filtro]}</TextoVacio>
      ) : (
        <ul className="flex flex-col gap-2.5">
          {visibles.map((incidencia) => (
            <li
              key={incidencia.id}
              className="rounded-xl border border-borde bg-blanco px-4 py-3.5 shadow-sm"
            >
              <div className="flex items-baseline justify-between gap-3">
                <p className="text-[13.5px] font-bold text-texto-fuerte">
                  {ETIQUETA_MOTIVO[incidencia.tipo]}
                </p>
                <span className="shrink-0 font-mono text-[11px] text-texto-mutado">
                  {formatearFechaHora(incidencia.fecha_hora)}
                </span>
              </div>
              <p className="mt-0.5 text-[12px] text-texto-mutado">
                {incidencia.parada_nombre ? `Parada: ${incidencia.parada_nombre}` : "Ruta completa"}
                {` · ruta del ${incidencia.ruta_fecha}`}
              </p>
              {incidencia.descripcion && (
                <p className="mt-1.5 text-[12.5px] text-texto-cuerpo">{incidencia.descripcion}</p>
              )}

              {incidencia.estado === "resuelta" ? (
                <p className="mt-2 inline-flex items-center gap-1.5 rounded-pill bg-exito-tint px-2.5 py-1 text-[11px] font-semibold text-[#067647]">
                  Resuelta
                  {incidencia.resolucion && ` · ${ETIQUETA_RESOLUCION[incidencia.resolucion]}`}
                  {incidencia.fecha_resolucion &&
                    ` · ${formatearFechaHora(incidencia.fecha_resolucion)}`}
                </p>
              ) : (
                <div className="mt-2.5 flex flex-wrap gap-2">
                  {incidencia.puede_reprogramarse && (
                    <button
                      type="button"
                      disabled={sinConexion || resolviendoId === incidencia.id}
                      onClick={() => resolver(incidencia, "reprogramada")}
                      className="h-9 rounded-lg bg-primario px-3.5 text-[12px] font-bold text-blanco disabled:opacity-60"
                    >
                      Reprogramar para la próxima ruta
                    </button>
                  )}
                  <button
                    type="button"
                    disabled={sinConexion || resolviendoId === incidencia.id}
                    onClick={() => resolver(incidencia, "cerrada")}
                    className="h-9 rounded-lg border border-borde-input bg-blanco px-3.5 text-[12px] font-semibold text-texto-cuerpo disabled:opacity-60"
                  >
                    Marcar como resuelta
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
