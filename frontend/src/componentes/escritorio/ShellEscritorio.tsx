import { type ReactNode, useState } from "react";

import { LogoOptiRuta } from "../ui/LogoOptiRuta";
import { type GrupoNav, ItemsNav } from "./NavSidebar";

const ESTILO_SIDEBAR = {
  backgroundColor: "#2A1264",
  backgroundImage:
    "radial-gradient(420px 260px at 0% 0%, rgba(124,58,237,0.55), transparent 70%), linear-gradient(180deg, #35197A 0%, #1E0C4C 100%)",
};

const ESTILO_CONTENIDO = {
  backgroundColor: "#EEEDF6",
  backgroundImage:
    "radial-gradient(900px 480px at 8% 0%, rgba(124,58,237,0.10), transparent 62%), radial-gradient(700px 420px at 96% 100%, rgba(15,118,110,0.07), transparent 60%), linear-gradient(160deg, #F7F6FC 0%, #EAEAF3 100%)",
};

interface Props<S extends string> {
  /** Debajo de "OptiRuta" en el sidebar de escritorio, ej. "Vista del chofer". */
  rol: string;
  grupos: GrupoNav<S>[];
  seccion: S;
  onSeleccionar: (seccion: S) => void;
  titulo: string;
  subtitulo?: ReactNode;
  /** Botones del encabezado, a la derecha del título. */
  acciones?: ReactNode;
  /** Franja entre el encabezado y el contenido (ej. el aviso de sin conexión). */
  banner?: ReactNode;
  children: ReactNode;
}

/** Layout compartido por todos los escritorios: sidebar violeta fijo desde lg y,
 * en pantallas chicas, barra de marca + drawer con el mismo nav (nada de scroll
 * horizontal). Cada escritorio aporta sus secciones, encabezado y contenido. */
export function ShellEscritorio<S extends string>({
  rol,
  grupos,
  seccion,
  onSeleccionar,
  titulo,
  subtitulo,
  acciones,
  banner,
  children,
}: Props<S>) {
  const [menuAbierto, setMenuAbierto] = useState(false);

  return (
    <div className="flex h-dvh w-full flex-col lg:flex-row">
      <aside className="flex shrink-0 flex-col text-blanco lg:w-[232px]" style={ESTILO_SIDEBAR}>
        <div className="flex h-14 shrink-0 items-center gap-2.5 border-b border-white/12 px-4 lg:h-16 lg:px-5">
          <button
            type="button"
            onClick={() => setMenuAbierto(true)}
            aria-label="Abrir menú"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-blanco hover:bg-white/10 lg:hidden"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
          <LogoOptiRuta />
          <div className="min-w-0 flex-1">
            <div className="text-sm font-extrabold tracking-tight text-blanco">OptiRuta</div>
            <div className="hidden text-[9.5px] font-semibold tracking-[0.1em] text-white/60 uppercase lg:block">
              {rol}
            </div>
          </div>
        </div>

        <nav className="hidden min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto p-3 lg:flex">
          <ItemsNav grupos={grupos} seccion={seccion} onSeleccionar={onSeleccionar} />
        </nav>
      </aside>

      {menuAbierto && (
        <div
          className="fixed inset-0 z-[900] animate-aparecer-fondo bg-[rgba(16,24,40,0.4)] lg:hidden"
          onClick={() => setMenuAbierto(false)}
        >
          <aside
            className="absolute top-0 left-0 flex h-full w-[min(280px,80vw)] animate-deslizar-panel-izq flex-col text-blanco"
            style={ESTILO_SIDEBAR}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex h-14 shrink-0 items-center justify-between gap-2.5 border-b border-white/12 px-4">
              <div className="flex min-w-0 items-center gap-2.5">
                <LogoOptiRuta />
                <span className="text-sm font-extrabold tracking-tight text-blanco">OptiRuta</span>
              </div>
              <button
                type="button"
                onClick={() => setMenuAbierto(false)}
                aria-label="Cerrar menú"
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-white/80 hover:bg-white/10"
              >
                ✕
              </button>
            </div>
            <nav className="flex min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto p-3">
              <ItemsNav
                grupos={grupos}
                seccion={seccion}
                onSeleccionar={(s) => {
                  onSeleccionar(s);
                  setMenuAbierto(false);
                }}
              />
            </nav>
          </aside>
        </div>
      )}

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        {/* En el celular todo entra en un renglón (acciones como íconos) para dejarle
            la pantalla al contenido; desde lg los escritorios pueden mostrar texto. */}
        <header className="flex shrink-0 items-center gap-3 border-b border-borde bg-blanco px-4 py-2.5 lg:h-16 lg:gap-4 lg:px-6 lg:py-0">
          <div className="min-w-0 flex-1">
            <div className="truncate text-base font-bold tracking-tight text-texto-fuerte">{titulo}</div>
            {subtitulo}
          </div>
          {acciones && <div className="flex shrink-0 items-center gap-2">{acciones}</div>}
        </header>

        {banner}

        <div className="min-h-0 flex-1 overflow-y-auto" style={ESTILO_CONTENIDO}>
          {children}
        </div>
      </div>
    </div>
  );
}
