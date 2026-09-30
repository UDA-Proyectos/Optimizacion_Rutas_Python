import type { IncidenciaPublica } from "../../tipos/incidencia";
import { ETIQUETA_MOTIVO } from "../../utilidades/motivosFallo";
import { TextoVacio } from "../ui/TextoVacio";

interface Props {
  incidencias: IncidenciaPublica[];
}

export function PanelIncidencias({ incidencias }: Props) {
  if (incidencias.length === 0) {
    return <TextoVacio>No reportaste ninguna incidencia todavía.</TextoVacio>;
  }

  return (
    <ul className="mx-auto flex max-w-[720px] flex-col gap-2.5">
      {incidencias.map((incidencia) => (
        <li
          key={incidencia.id}
          className="rounded-xl border border-borde bg-blanco px-4 py-3.5 shadow-sm"
        >
          <div className="flex items-baseline justify-between gap-3">
            <p className="text-[13.5px] font-bold text-texto-fuerte">
              {ETIQUETA_MOTIVO[incidencia.tipo]}
            </p>
            <span className="shrink-0 font-mono text-[11px] text-texto-mutado">
              {new Date(incidencia.fecha_hora).toLocaleString([], {
                day: "2-digit",
                month: "2-digit",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
          </div>
          <p className="mt-0.5 text-[12px] text-texto-mutado">
            {incidencia.parada_nombre ? `Parada: ${incidencia.parada_nombre}` : "Ruta completa"}
            {` · ruta del ${incidencia.ruta_fecha}`}
          </p>
          {incidencia.descripcion && (
            <p className="mt-1.5 text-[12.5px] text-texto-cuerpo">{incidencia.descripcion}</p>
          )}
        </li>
      ))}
    </ul>
  );
}
