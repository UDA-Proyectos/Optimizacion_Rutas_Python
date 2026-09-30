import { useEffect, useState } from "react";

import { obtenerHistorialRutas, obtenerRutaHistorial } from "../../api/rutas";
import type { ClientePublico } from "../../tipos/cliente";
import type { RutaHistorialItem, RutaPublica } from "../../tipos/ruta";
import { minutosAHhMm } from "../../utilidades/horario";
import { ETIQUETA_MOTIVO } from "../../utilidades/motivosFallo";
import type { Seleccion } from "../rutas/FlujoArmarRuta";
import { ResumenCierre } from "../rutas/ResumenCierre";
import { Boton } from "../ui/Boton";
import { BannerError } from "../ui/Formulario";
import { TextoVacio } from "../ui/TextoVacio";
import { Almanaque } from "./Almanaque";

const ETIQUETA_ESTADO: Record<RutaHistorialItem["estado"], string> = {
  planificada: "Planificada",
  en_curso: "En curso",
  completada: "Completada",
  cancelada: "Cancelada",
};

interface Props {
  clientes: ClientePublico[];
  onUsarDeNuevo: (datos: { seleccion: Seleccion; usaVentanasHorarias: boolean }) => void;
}

function primerYUltimoDia(anio: number, mes: number): [string, string] {
  const pad = (n: number) => String(n).padStart(2, "0");
  const ultimoDia = new Date(anio, mes, 0).getDate();
  return [`${anio}-${pad(mes)}-01`, `${anio}-${pad(mes)}-${pad(ultimoDia)}`];
}

export function PanelHistorial({ clientes, onUsarDeNuevo }: Props) {
  const hoy = new Date();
  const [anio, setAnio] = useState(hoy.getFullYear());
  const [mes, setMes] = useState(hoy.getMonth() + 1);
  const [rutas, setRutas] = useState<RutaHistorialItem[]>([]);
  const [cargandoMes, setCargandoMes] = useState(true);
  const [diaSeleccionado, setDiaSeleccionado] = useState<string | null>(null);
  const [detalle, setDetalle] = useState<RutaPublica | null>(null);
  const [rutaIdSeleccionada, setRutaIdSeleccionada] = useState<string | null>(null);
  const [cargandoDetalle, setCargandoDetalle] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Sincroniza con el mes visible cambiando (señal externa real: el
    // usuario navegó el calendario) — el mes anterior deja de mostrarse como
    // cargado y su selección/detalle ya no aplican mientras carga el nuevo.
    // oxlint-disable-next-line react/set-state-in-effect
    setCargandoMes(true);
    const [desde, hasta] = primerYUltimoDia(anio, mes);
    obtenerHistorialRutas(desde, hasta)
      .then(setRutas)
      .finally(() => setCargandoMes(false));
    setDiaSeleccionado(null);
    setDetalle(null);
    setRutaIdSeleccionada(null);
  }, [anio, mes]);

  function abrirRuta(id: string) {
    setRutaIdSeleccionada(id);
    setCargandoDetalle(true);
    setError(null);
    obtenerRutaHistorial(id)
      .then(setDetalle)
      .catch(() => setError("No se pudo abrir esa ruta."))
      .finally(() => setCargandoDetalle(false));
  }

  function seleccionarDia(fecha: string) {
    const primera = rutas.find((r) => r.fecha === fecha);
    if (!primera) return;
    setDiaSeleccionado(fecha);
    abrirRuta(primera.id);
  }

  // Un día puede tener varias rutas (ahora se pueden planificar dos o más).
  const rutasDelDiaSeleccionado = diaSeleccionado
    ? rutas.filter((r) => r.fecha === diaSeleccionado && r.estado !== "cancelada")
    : [];

  function usarDeNuevo() {
    if (!detalle) return;
    const idsVigentes = new Set(clientes.map((c) => c.id));
    const paradasVigentes = detalle.paradas.filter((p) => idsVigentes.has(p.cliente_id));

    const seleccion: Seleccion = {};
    for (const parada of paradasVigentes) {
      seleccion[parada.cliente_id] = {
        carga_kg: parada.demanda_carga_snapshot,
        unidades: parada.unidades_snapshot,
        ventana_inicio: parada.ventana_inicio_snapshot,
        ventana_fin: parada.ventana_fin_snapshot,
      };
    }

    onUsarDeNuevo({ seleccion, usaVentanasHorarias: detalle.usa_ventanas_horarias });
  }

  const excluidos = detalle
    ? detalle.paradas.length -
      detalle.paradas.filter((p) => clientes.some((c) => c.id === p.cliente_id)).length
    : 0;

  return (
    <div className="mx-auto grid max-w-[900px] gap-5 lg:grid-cols-[340px_1fr]">
      <Almanaque
        anio={anio}
        mes={mes}
        rutas={rutas}
        diaSeleccionado={diaSeleccionado}
        onSeleccionarDia={seleccionarDia}
        onCambiarMes={(a, m) => {
          setAnio(a);
          setMes(m);
        }}
      />

      <div className="min-w-0 rounded-2xl border border-borde bg-blanco p-5 shadow-md">
        {cargandoMes ? (
          <TextoVacio>Cargando…</TextoVacio>
        ) : !diaSeleccionado ? (
          <TextoVacio>
            {rutas.length === 0
              ? "No hiciste ninguna ruta este mes."
              : "Elegí un día del calendario para ver esa ruta."}
          </TextoVacio>
        ) : cargandoDetalle ? (
          <TextoVacio>Cargando…</TextoVacio>
        ) : error ? (
          <BannerError>{error}</BannerError>
        ) : (
          detalle && (
            <div className="flex flex-col gap-4">
              {rutasDelDiaSeleccionado.length > 1 && (
                <div className="flex flex-wrap gap-1.5" role="tablist" aria-label="Rutas del día">
                  {rutasDelDiaSeleccionado.map((r, indice) => (
                    <button
                      key={r.id}
                      type="button"
                      role="tab"
                      aria-selected={r.id === rutaIdSeleccionada}
                      onClick={() => abrirRuta(r.id)}
                      className={
                        r.id === rutaIdSeleccionada
                          ? "rounded-pill bg-primario px-3 py-1.5 text-[12px] font-semibold text-blanco"
                          : "rounded-pill border border-borde-input bg-blanco px-3 py-1.5 text-[12px] font-semibold text-texto-cuerpo"
                      }
                    >
                      {r.nombre ?? `Ruta ${indice + 1}`} · {ETIQUETA_ESTADO[r.estado]}
                    </button>
                  ))}
                </div>
              )}
              <div>
                <div className="mb-1 flex items-center justify-between gap-3">
                  <p className="text-sm font-bold text-texto-fuerte">
                    {detalle.fecha}
                    {detalle.nombre && ` · ${detalle.nombre}`}
                  </p>
                  <span className="rounded-pill bg-fondo px-2.5 py-1 text-[11px] font-semibold text-texto-cuerpo">
                    {ETIQUETA_ESTADO[detalle.estado]}
                  </span>
                </div>
                <p className="font-mono text-[12.5px] text-texto-cuerpo">
                  {detalle.paradas.length} paradas
                  {detalle.distancia_total_m != null &&
                    ` · ${(detalle.distancia_total_m / 1000).toFixed(1)} km`}
                  {detalle.usa_ventanas_horarias && " · con ventanas horarias"}
                </p>
                {detalle.explicacion && (
                  <p className="mt-1.5 text-[12.5px] text-texto-mutado">{detalle.explicacion}</p>
                )}
              </div>

              {detalle.resumen && (
                <ResumenCierre resumen={detalle.resumen} totalParadas={detalle.paradas.length} />
              )}

              <ol className="flex flex-col gap-2">
                {detalle.paradas.map((parada) => (
                  <li
                    key={parada.id}
                    className="flex items-baseline justify-between gap-3 rounded-lg bg-superficie px-3.5 py-2.5"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[12.5px] font-semibold text-texto-fuerte">
                        {parada.orden + 1}. {parada.nombre_snapshot}
                      </p>
                      <p className="truncate text-[11px] text-texto-mutado">
                        {parada.direccion_snapshot}
                      </p>
                      {parada.estado === "fallida" && (
                        <p className="mt-0.5 text-[11px] font-semibold text-peligro">
                          No entregada
                          {parada.motivo_fallo && ` · ${ETIQUETA_MOTIVO[parada.motivo_fallo]}`}
                        </p>
                      )}
                    </div>
                    <span className="shrink-0 font-mono text-[11px] text-texto-mutado">
                      {parada.demanda_carga_snapshot} kg
                      {detalle.usa_ventanas_horarias &&
                        parada.ventana_inicio_snapshot != null &&
                        ` · ${minutosAHhMm(parada.ventana_inicio_snapshot)}–${minutosAHhMm(parada.ventana_fin_snapshot ?? 0)}`}
                    </span>
                  </li>
                ))}
              </ol>

              {excluidos > 0 && (
                <p className="text-[11.5px] text-texto-tenue">
                  {excluidos} lugar{excluidos > 1 ? "es" : ""} de esa ruta ya no existe
                  {excluidos > 1 ? "n" : ""} en tu libreta — no se incluir
                  {excluidos > 1 ? "án" : "á"} al copiarla.
                </p>
              )}

              <Boton
                tamanio="auto"
                disabled={detalle.paradas.length - excluidos === 0}
                onClick={usarDeNuevo}
              >
                Usar esta ruta de nuevo
              </Boton>
            </div>
          )
        )}
      </div>
    </div>
  );
}
