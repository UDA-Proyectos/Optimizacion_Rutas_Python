import type { ReactNode } from "react";

import { combinarClases } from "../ui/combinarClases";

export interface ItemNav<S extends string> {
  id: S;
  etiqueta: string;
  icono: ReactNode;
  badge?: string;
}

export interface GrupoNav<S extends string> {
  titulo: string;
  items: ItemNav<S>[];
}

/** El mismo nav se usa tal cual en el sidebar fijo de escritorio y en el
 * drawer de mobile (ShellEscritorio.tsx); cada escritorio declara sus grupos
 * de secciones como datos. */
export function ItemsNav<S extends string>({
  grupos,
  seccion,
  onSeleccionar,
}: {
  grupos: GrupoNav<S>[];
  seccion: S;
  onSeleccionar: (seccion: S) => void;
}) {
  return (
    <>
      {grupos.map((grupo, indice) => (
        <div key={grupo.titulo} className="flex flex-col gap-0.5">
          <p
            className={combinarClases(
              "px-2.5 pb-2 text-[9.5px] font-bold tracking-[0.12em] text-white/58 uppercase",
              indice === 0 ? "pt-1.5" : "pt-4.5",
            )}
          >
            {grupo.titulo}
          </p>
          {grupo.items.map((item) => (
            <BotonNav
              key={item.id}
              activo={seccion === item.id}
              onClick={() => onSeleccionar(item.id)}
              icono={item.icono}
              etiqueta={item.etiqueta}
              badge={item.badge}
            />
          ))}
        </div>
      ))}
    </>
  );
}

function BotonNav({
  activo,
  onClick,
  icono,
  etiqueta,
  badge,
}: {
  activo: boolean;
  onClick: () => void;
  icono: ReactNode;
  etiqueta: string;
  badge?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={combinarClases(
        "flex h-10 w-full items-center gap-2.5 rounded-lg px-2.5 text-left text-[13px]",
        activo ? "bg-white/16 font-semibold text-blanco" : "font-medium text-white/78 hover:bg-white/8",
      )}
    >
      {icono}
      <span className="flex-1">{etiqueta}</span>
      {badge && (
        <span className="rounded-pill bg-white/16 px-1.5 py-0.5 font-mono text-[10.5px] font-semibold text-blanco">
          {badge}
        </span>
      )}
    </button>
  );
}
