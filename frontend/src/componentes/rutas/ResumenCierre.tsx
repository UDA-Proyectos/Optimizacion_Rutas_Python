import type { ResumenRutaDatos } from "../../tipos/ruta";
import { formatearDuracion } from "../../utilidades/horario";

interface Dato {
  etiqueta: string;
  valor: string;
  detalle?: string;
  alerta?: boolean;
}

function datosDelResumen(resumen: ResumenRutaDatos, totalParadas: number): Dato[] {
  const datos: Dato[] = [
    {
      etiqueta: "Entregas",
      valor: `${resumen.paradas_completadas} de ${totalParadas}`,
    },
    {
      etiqueta: "Duración",
      valor: resumen.duracion_min != null ? formatearDuracion(resumen.duracion_min) : "—",
    },
    { etiqueta: "Carga entregada", valor: `${resumen.carga_entregada_kg} kg` },
    {
      etiqueta: "Distancia planificada",
      valor:
        resumen.distancia_planificada_m != null
          ? `${(resumen.distancia_planificada_m / 1000).toFixed(1)} km`
          : "—",
      detalle: "no es el recorrido real",
    },
  ];
  if (resumen.paradas_fallidas > 0) {
    datos.push({ etiqueta: "Sin entregar", valor: String(resumen.paradas_fallidas), alerta: true });
  }
  if (resumen.paradas_salteadas > 0) {
    datos.push({ etiqueta: "Salteadas", valor: String(resumen.paradas_salteadas) });
  }
  if (resumen.incidencias > 0) {
    datos.push({ etiqueta: "Incidencias", valor: String(resumen.incidencias) });
  }
  // Solo si la ruta usó ventanas y alguna parada entregada tenía una.
  if (resumen.ventanas_cumplidas_pct != null) {
    datos.push({
      etiqueta: "Ventanas cumplidas",
      valor: `${resumen.ventanas_cumplidas}/${resumen.ventanas_evaluadas}`,
      detalle: `${resumen.ventanas_cumplidas_pct}%`,
    });
  }
  return datos;
}

/** Cómo resultó realmente una ruta terminada — compartido por la pantalla de
 * cierre de "Ruta de hoy" y por el detalle de un día en el historial. */
export function ResumenCierre({
  resumen,
  totalParadas,
}: {
  resumen: ResumenRutaDatos;
  totalParadas: number;
}) {
  return (
    <dl className="grid grid-cols-2 gap-2.5">
      {datosDelResumen(resumen, totalParadas).map((dato) => (
        <div key={dato.etiqueta} className="rounded-lg border border-borde bg-superficie px-3 py-2.5">
          <dt className="text-[9px] font-bold tracking-[0.08em] text-texto-mutado uppercase">
            {dato.etiqueta}
          </dt>
          <dd
            className={
              dato.alerta
                ? "font-mono text-base font-bold text-peligro"
                : "font-mono text-base font-bold text-texto-fuerte"
            }
          >
            {dato.valor}
          </dd>
          {dato.detalle && <dd className="text-[10px] text-texto-mutado">{dato.detalle}</dd>}
        </div>
      ))}
    </dl>
  );
}
