import type { RutaHistorialItem } from "../../tipos/ruta";
import { combinarClases } from "../ui/combinarClases";

const DIAS_SEMANA = ["L", "M", "M", "J", "V", "S", "D"];
const NOMBRES_MES = [
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre",
];

const COLOR_PUNTO: Record<RutaHistorialItem["estado"], string> = {
  completada: "bg-exito",
  cancelada: "bg-texto-tenue",
  planificada: "bg-primario",
  en_curso: "bg-primario",
};

function conFallos(ruta: RutaHistorialItem): boolean {
  return ruta.estado === "completada" && ruta.paradas_fallidas > 0;
}

interface Props {
  anio: number;
  mes: number; // 1-12
  rutas: RutaHistorialItem[];
  diaSeleccionado: string | null;
  onSeleccionarDia: (fecha: string) => void;
  onCambiarMes: (anio: number, mes: number) => void;
}

function aFechaIso(anio: number, mes: number, dia: number): string {
  return `${anio}-${String(mes).padStart(2, "0")}-${String(dia).padStart(2, "0")}`;
}

export function Almanaque({ anio, mes, rutas, diaSeleccionado, onSeleccionarDia, onCambiarMes }: Props) {
  // Puede haber más de una Ruta el mismo día (canceló y volvió a armar
  // otra) — `rutas` ya viene con la más reciente primero por fecha (ver
  // crud.listar_rutas_historial), así que la primera que aparece acá es la
  // que se muestra: la última palabra del día, misma que abre el detalle
  // (PanelHistorial.seleccionarDia usa el mismo criterio de "primera que
  // matchea").
  const rutaPorDia = new Map<string, RutaHistorialItem>();
  for (const r of rutas) {
    if (!rutaPorDia.has(r.fecha)) {
      rutaPorDia.set(r.fecha, r);
    }
  }

  const primerDiaSemana = (new Date(anio, mes - 1, 1).getDay() + 6) % 7; // 0 = lunes
  const diasEnMes = new Date(anio, mes, 0).getDate();
  const hoy = new Date();
  const hoyIso = aFechaIso(hoy.getFullYear(), hoy.getMonth() + 1, hoy.getDate());

  const celdas: (number | null)[] = [
    ...Array.from({ length: primerDiaSemana }, () => null),
    ...Array.from({ length: diasEnMes }, (_, i) => i + 1),
  ];
  while (celdas.length % 7 !== 0) {
    celdas.push(null);
  }

  function irMesAnterior() {
    onCambiarMes(mes === 1 ? anio - 1 : anio, mes === 1 ? 12 : mes - 1);
  }

  function irMesSiguiente() {
    onCambiarMes(mes === 12 ? anio + 1 : anio, mes === 12 ? 1 : mes + 1);
  }

  return (
    <div className="rounded-2xl border border-borde bg-blanco p-5 shadow-md">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm font-bold text-texto-fuerte">
          {NOMBRES_MES[mes - 1]} {anio}
        </p>
        <div className="flex gap-1.5">
          <button
            type="button"
            onClick={irMesAnterior}
            aria-label="Mes anterior"
            className="flex h-8 w-8 items-center justify-center rounded-md border border-borde text-texto-fuerte hover:bg-fondo"
          >
            ‹
          </button>
          <button
            type="button"
            onClick={irMesSiguiente}
            aria-label="Mes siguiente"
            className="flex h-8 w-8 items-center justify-center rounded-md border border-borde text-texto-fuerte hover:bg-fondo"
          >
            ›
          </button>
        </div>
      </div>

      <div className="grid grid-cols-7 gap-1 text-center">
        {DIAS_SEMANA.map((d, i) => (
          <div key={i} className="pb-1.5 text-[10.5px] font-semibold text-texto-tenue">
            {d}
          </div>
        ))}
        {celdas.map((dia, indice) => {
          if (dia == null) {
            return <div key={indice} />;
          }
          const fecha = aFechaIso(anio, mes, dia);
          const ruta = rutaPorDia.get(fecha);
          const seleccionado = fecha === diaSeleccionado;
          return (
            <button
              key={indice}
              type="button"
              disabled={!ruta}
              onClick={() => onSeleccionarDia(fecha)}
              className={combinarClases(
                "flex h-10 flex-col items-center justify-center gap-0.5 rounded-lg text-[12.5px]",
                seleccionado
                  ? "bg-primario font-bold text-blanco"
                  : ruta
                    ? "font-semibold text-texto-fuerte hover:bg-fondo"
                    : "text-texto-tenue",
                fecha === hoyIso && !seleccionado && "ring-1 ring-primario/40",
              )}
            >
              <span>{dia}</span>
              {ruta && (
                <span
                  className="flex items-center gap-0.5"
                  title={
                    ruta.estado === "cancelada"
                      ? "Ruta cancelada"
                      : `${ruta.paradas_completadas} de ${ruta.paradas_total} entregas` +
                        (ruta.paradas_fallidas > 0 ? ` · ${ruta.paradas_fallidas} sin entregar` : "")
                  }
                >
                  <span
                    className={combinarClases(
                      "h-1.5 w-1.5 rounded-full",
                      seleccionado
                        ? "bg-blanco"
                        : conFallos(ruta)
                          ? "bg-peligro"
                          : COLOR_PUNTO[ruta.estado],
                    )}
                  />
                  {ruta.estado !== "cancelada" && (
                    <span
                      className={combinarClases(
                        "font-mono text-[8.5px] leading-none",
                        seleccionado ? "text-blanco" : "text-texto-mutado",
                      )}
                    >
                      {ruta.paradas_completadas}/{ruta.paradas_total}
                    </span>
                  )}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="mt-4 flex flex-wrap gap-3 border-t border-borde pt-3 text-[10.5px] text-texto-mutado">
        <span className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-exito" /> Completada
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-peligro" /> Con paradas sin entregar
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-texto-tenue" /> Cancelada
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-primario" /> En curso / planificada
        </span>
      </div>
    </div>
  );
}
