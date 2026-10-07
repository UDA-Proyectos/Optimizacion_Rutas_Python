import { useCallback, useEffect, useState } from "react";

import { listarRutasDeLaFlota, obtenerGeometriaRutaDeLaFlota } from "../../api/empresa";
import { eliminarRuta } from "../../api/rutas";
import type { EstadoParada, RutaPublica } from "../../tipos/ruta";
import { CHIP_ESTADO_RUTA, ETIQUETA_ESTADO_RUTA } from "../../utilidades/estadosRuta";
import { hoyLocal, sumarDias } from "../../utilidades/fechas";
import { minutosAHhMm } from "../../utilidades/horario";
import { MapaRutaActiva } from "../rutas/MapaRutaActiva";
import { NavegadorDia } from "../rutas/NavegadorDia";
import { ResumenCierre } from "../rutas/ResumenCierre";
import { Boton } from "../ui/Boton";
import { combinarClases } from "../ui/combinarClases";
import { BannerError } from "../ui/Formulario";
import { TextoVacio } from "../ui/TextoVacio";

// El avance de la flota se refresca solo mientras la pestaña está a la vista (sin
// tiempo real: polling simple).
const REFRESCO_MS = 30_000;

const ESTADO_PARADA: Record<EstadoParada, { etiqueta: string; clase: string }> = {
  pendiente: { etiqueta: "Pendiente", clase: "bg-fondo text-texto-cuerpo" },
  en_curso: { etiqueta: "En curso", clase: "bg-primario/10 text-[#6428CC]" },
  completada: { etiqueta: "Entregada", clase: "bg-exito-tint text-[#079455]" },
  fallida: { etiqueta: "No entregada", clase: "bg-peligro-tint text-peligro" },
};

function avance(ruta: RutaPublica) {
  const hechas = ruta.paradas.filter((p) => p.estado === "completada").length;
  const fallidas = ruta.paradas.filter((p) => p.estado === "fallida").length;
  const actual = ruta.paradas.find((p) => p.estado === "en_curso");
  return { hechas, fallidas, actual, total: ruta.paradas.length };
}

function TarjetaRutaFlota({
  ruta,
  seleccionada,
  onSeleccionar,
}: {
  ruta: RutaPublica;
  seleccionada: boolean;
  onSeleccionar: () => void;
}) {
  const { hechas, fallidas, actual, total } = avance(ruta);
  const porcentaje = total === 0 ? 0 : Math.round((100 * (hechas + fallidas)) / total);
  return (
    <button
      type="button"
      onClick={onSeleccionar}
      className={combinarClases(
        "flex w-full flex-col gap-2 rounded-xl border bg-blanco px-4 py-3.5 text-left shadow-sm",
        seleccionada ? "border-primario ring-2 ring-primario/20" : "border-borde hover:border-primario/50",
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-[13.5px] font-bold text-texto-fuerte">{ruta.chofer_nombre}</span>
        <span
          className={combinarClases(
            "shrink-0 rounded-pill px-2 py-0.5 text-[10.5px] font-semibold",
            CHIP_ESTADO_RUTA[ruta.estado],
          )}
        >
          {ETIQUETA_ESTADO_RUTA[ruta.estado]}
        </span>
      </div>
      <p className="truncate text-[12px] text-texto-mutado">
        {ruta.nombre ?? "Ruta sin nombre"} · {total} paradas
      </p>
      <div className="h-2 overflow-hidden rounded-pill bg-superficie-hundida">
        <div className="h-full bg-exito" style={{ width: `${porcentaje}%` }} />
      </div>
      <p className="font-mono text-[11px] text-texto-cuerpo">
        {hechas}/{total} entregadas{fallidas > 0 && ` · ${fallidas} sin entregar`}
        {actual && ` · ahora: ${actual.nombre_snapshot}`}
      </p>
    </button>
  );
}

function DetalleRutaFlota({
  ruta,
  onEditar,
  onCancelada,
}: {
  ruta: RutaPublica;
  onEditar: (ruta: RutaPublica) => void;
  onCancelada: () => void;
}) {
  const [cancelando, setCancelando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function cancelar() {
    setCancelando(true);
    setError(null);
    try {
      await eliminarRuta(ruta.id);
      onCancelada();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo cancelar la ruta.");
    } finally {
      setCancelando(false);
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-borde bg-blanco p-4 shadow-md sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-[15px] font-bold text-texto-fuerte">
            {ruta.chofer_nombre}
            {ruta.nombre && ` · ${ruta.nombre}`}
          </p>
          <p className="font-mono text-[12px] text-texto-cuerpo">
            {ruta.paradas.length} paradas
            {ruta.distancia_total_m != null && ` · ${(ruta.distancia_total_m / 1000).toFixed(1)} km`}
            {ruta.hora_inicio_real &&
              ` · arrancó ${new Date(ruta.hora_inicio_real).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`}
          </p>
        </div>
        <div className="flex gap-2">
          {ruta.estado === "planificada" && (
            <Boton variante="secundario" tamanio="chica" onClick={() => onEditar(ruta)}>
              Editar
            </Boton>
          )}
          {(ruta.estado === "planificada" || ruta.estado === "en_curso") && (
            <Boton variante="peligro" tamanio="chica" cargando={cancelando} onClick={cancelar}>
              Cancelar ruta
            </Boton>
          )}
        </div>
      </div>
      {error && <BannerError>{error}</BannerError>}

      {ruta.estado === "completada" && ruta.resumen && (
        <ResumenCierre resumen={ruta.resumen} totalParadas={ruta.paradas.length} />
      )}

      <div className="h-[300px] sm:h-[360px]">
        <MapaRutaActiva
          deposito={ruta.deposito}
          paradas={ruta.paradas}
          overlaySimple={false}
          cargarGeometria={() => obtenerGeometriaRutaDeLaFlota(ruta.id)}
        />
      </div>

      <ol className="flex flex-col divide-y divide-borde">
        {ruta.paradas.map((parada, indice) => (
          <li key={parada.id} className="flex items-center gap-3 py-2.5">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-fondo font-mono text-[11px] font-bold text-texto-cuerpo">
              {indice + 1}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px] font-semibold text-texto-fuerte">
                {parada.nombre_snapshot}
              </p>
              <p className="truncate text-[11.5px] text-texto-mutado">
                {parada.direccion_snapshot}
                {parada.hora_estimada_llegada != null &&
                  ` · llega ${minutosAHhMm(parada.hora_estimada_llegada)}`}
              </p>
            </div>
            <span
              className={combinarClases(
                "shrink-0 rounded-pill px-2 py-0.5 text-[10.5px] font-semibold",
                ESTADO_PARADA[parada.estado].clase,
              )}
            >
              {ESTADO_PARADA[parada.estado].etiqueta}
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}

/** Avance del día de toda la flota (admin). */
export function PanelFlotaHoy({
  fechaInicial,
  onEditar,
}: {
  fechaInicial?: string;
  onEditar: (ruta: RutaPublica) => void;
}) {
  const [fecha, setFecha] = useState(fechaInicial ?? hoyLocal());
  const [rutas, setRutas] = useState<RutaPublica[] | null>(null);
  const [seleccionadaId, setSeleccionadaId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const recargar = useCallback(() => {
    listarRutasDeLaFlota(fecha)
      .then((lista) => {
        setRutas(lista);
        setError(null);
      })
      .catch(() => setError("No se pudo actualizar el avance de la flota."));
  }, [fecha]);

  useEffect(() => {
    // Al cambiar de día se muestra "cargando" hasta tener las rutas de ese día.
    // oxlint-disable-next-line react/set-state-in-effect
    setRutas(null);
    recargar();
    const intervalo = setInterval(() => {
      if (document.visibilityState === "visible") recargar();
    }, REFRESCO_MS);
    // Al volver a la pestaña se actualiza enseguida, sin esperar al próximo ciclo.
    const alVolver = () => {
      if (document.visibilityState === "visible") recargar();
    };
    document.addEventListener("visibilitychange", alVolver);
    return () => {
      clearInterval(intervalo);
      document.removeEventListener("visibilitychange", alVolver);
    };
  }, [recargar]);

  const seleccionada = rutas?.find((r) => r.id === seleccionadaId) ?? null;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2 rounded-xl border border-borde bg-blanco/80 px-4 py-2.5">
        <NavegadorDia
          fecha={fecha}
          onMoverDia={(dias) => setFecha((actual) => sumarDias(actual, dias))}
          onIrAHoy={() => setFecha(hoyLocal())}
        />
      </div>
      {error && <BannerError>{error}</BannerError>}

      {rutas === null ? (
        <TextoVacio>Cargando…</TextoVacio>
      ) : rutas.length === 0 ? (
        <TextoVacio>No hay rutas de la flota para este día. Armá una desde "Armar ruta".</TextoVacio>
      ) : (
        <div className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)] xl:items-start">
          <div className="flex flex-col gap-2.5">
            {rutas.map((ruta) => (
              <TarjetaRutaFlota
                key={ruta.id}
                ruta={ruta}
                seleccionada={ruta.id === seleccionadaId}
                onSeleccionar={() => setSeleccionadaId(ruta.id)}
              />
            ))}
          </div>
          {seleccionada ? (
            <DetalleRutaFlota
              key={seleccionada.id}
              ruta={seleccionada}
              onEditar={onEditar}
              onCancelada={() => {
                setSeleccionadaId(null);
                recargar();
              }}
            />
          ) : (
            <p className="hidden text-center text-[13px] text-texto-mutado xl:block xl:pt-10">
              Elegí una ruta para ver sus paradas y el mapa.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
