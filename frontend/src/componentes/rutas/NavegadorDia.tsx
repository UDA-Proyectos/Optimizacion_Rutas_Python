import { etiquetaDia, fechaLarga, hoyLocal } from "../../utilidades/fechas";

/** ‹ Hoy › y el día que se está viendo — "Mis rutas" del chofer y "Hoy" del admin. */
export function NavegadorDia({
  fecha,
  onMoverDia,
  onIrAHoy,
}: {
  fecha: string;
  onMoverDia: (dias: number) => void;
  onIrAHoy: () => void;
}) {
  return (
    <>
      <div className="flex items-center gap-1" role="group" aria-label="Día">
        <button
          type="button"
          onClick={() => onMoverDia(-1)}
          aria-label="Día anterior"
          className="flex h-8 w-8 items-center justify-center rounded-md border border-borde text-texto-fuerte hover:bg-fondo"
        >
          ‹
        </button>
        <button
          type="button"
          onClick={onIrAHoy}
          disabled={fecha === hoyLocal()}
          className="h-8 rounded-md border border-borde px-2.5 text-[12px] font-semibold text-texto-fuerte hover:bg-fondo disabled:opacity-50"
        >
          Hoy
        </button>
        <button
          type="button"
          onClick={() => onMoverDia(1)}
          aria-label="Día siguiente"
          className="flex h-8 w-8 items-center justify-center rounded-md border border-borde text-texto-fuerte hover:bg-fondo"
        >
          ›
        </button>
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-[13px] font-bold text-texto-fuerte">{etiquetaDia(fecha)}</p>
        <p className="truncate text-[11px] text-texto-mutado first-letter:uppercase">
          {fechaLarga(fecha)}
        </p>
      </div>
    </>
  );
}
