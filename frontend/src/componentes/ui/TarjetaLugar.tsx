import type { ReactNode } from "react";

import { combinarClases } from "./combinarClases";

interface Props {
  /** Badge circular con el número de orden — omitido en listas sin secuencia
   * (ej. "Mis lugares"). */
  numero?: number;
  nombre: string;
  direccion: string;
  telefono?: string | null;
  /** Línea extra de detalle bajo la dirección (ej. datos habituales del lugar). */
  detalle?: string | null;
  /** El mismo EstadoParada del dominio (sin importar el tipo acá para no
   * atarle a esta app UI genérica una dependencia de tipos/ruta.ts) — solo
   * en_curso/completada tienen tratamiento visual propio, pendiente/fallida
   * quedan con el aspecto normal. Tiparlo completo evita que el caller tenga
   * que filtrar el estado real de la parada antes de pasarlo. */
  estado?: "pendiente" | "en_curso" | "completada" | "fallida";
  /** Modo checkbox de selección (armar ruta): envuelve el bloque de info en
   * un <label> con su propio input, en vez de mostrarlo como texto plano. */
  seleccionable?: { marcado: boolean; onCambiar: (marcado: boolean) => void };
  /** Slot derecho: un botón, un dato en kg, una columna de acciones, o nada. */
  trailing?: ReactNode;
  className?: string;
}

const ESTADO_LI: Record<"pendiente" | "en_curso" | "completada" | "fallida", string> = {
  pendiente: "shadow-sm",
  en_curso: "shadow-[0_0_0_1.5px_#12B76A,0_2px_6px_rgba(16,24,40,0.08)]",
  completada: "opacity-60",
  fallida: "shadow-sm",
};

export function TarjetaLugar({
  numero,
  nombre,
  direccion,
  telefono,
  detalle,
  estado,
  seleccionable,
  trailing,
  className,
}: Props) {
  const info = (
    <div className="min-w-0 flex-1">
      <p className="mb-0.5 text-[13.5px] font-semibold text-texto-fuerte">{nombre}</p>
      <p className="mb-0.5 text-[12.5px] text-texto-cuerpo">{direccion}</p>
      {telefono && <p className="text-xs text-texto-mutado">{telefono}</p>}
      {detalle && <p className="mt-0.5 font-mono text-[11px] text-texto-tenue">{detalle}</p>}
    </div>
  );

  return (
    <li
      className={combinarClases(
        // flex-wrap: cuando el trailing no entra al lado de la info en
        // pantallas angostas (ej. los 4 campitos de armar ruta con ventana
        // horaria), baja a su propia fila en vez de desbordar el card.
        "flex flex-wrap items-start justify-between gap-3 rounded-lg bg-blanco px-4 py-3.5",
        ESTADO_LI[estado ?? "pendiente"],
        className,
      )}
    >
      {numero != null && (
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-borde bg-superficie font-mono text-[11.5px] font-bold text-texto-fuerte">
          {numero}
        </span>
      )}
      {seleccionable ? (
        <label className="flex flex-1 cursor-pointer items-start gap-2.5">
          <input
            type="checkbox"
            checked={seleccionable.marcado}
            onChange={(e) => seleccionable.onCambiar(e.target.checked)}
            className="mt-0.5 h-[18px] w-[18px] shrink-0 cursor-pointer accent-primario"
          />
          {info}
        </label>
      ) : (
        info
      )}
      {trailing}
    </li>
  );
}
