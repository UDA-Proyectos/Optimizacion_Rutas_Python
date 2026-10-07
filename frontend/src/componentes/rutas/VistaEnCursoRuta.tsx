import { useState } from "react";

import {
  completarParada,
  fallarParada,
  registrarLlegada,
  saltearParada,
} from "../../api/rutas";
import type { EjecutarAccionRuta } from "../../hooks/useRutasDelDia";
import type { EstadoGps } from "../../hooks/useUbicacion";
import type { UsuarioPublico } from "../../tipos/auth";
import type { ClientePublico } from "../../tipos/cliente";
import type {
  MotivoFalloParada,
  ParadaRutaPublica,
  RutaPublica,
} from "../../tipos/ruta";
import { minutosAHhMm } from "../../utilidades/horario";
import {
  ETIQUETA_MOTIVO,
  OPCIONES_MOTIVO_FALLO,
} from "../../utilidades/motivosFallo";
import { combinarClases } from "../ui/combinarClases";
import { BannerError } from "../ui/Formulario";
import { MapaRutaActiva } from "./MapaRutaActiva";

interface KpiProps {
  label: string;
  value: string;
  unit: string;
  delta: string;
  deltaColor?: string;
}

// Compactas a propósito: son el dato secundario de la pantalla, el mapa y
// la parada actual son lo que realmente importa mientras se maneja.
function TarjetaKpi({
  label,
  value,
  unit,
  delta,
  deltaColor = "#667085",
}: KpiProps) {
  return (
    <div className="rounded-lg border border-borde bg-blanco px-3 py-2 shadow-sm">
      <div className="mb-0.5 truncate text-[8px] font-bold tracking-[0.08em] text-texto-mutado uppercase">
        {label}
      </div>
      <div className="flex items-baseline gap-1">
        <div className="font-mono text-base leading-none font-bold text-texto-fuerte">
          {value}
        </div>
        <div className="truncate text-[10px] font-medium text-texto-mutado">
          {unit}
        </div>
      </div>
      {delta && (
        <div
          className="mt-0.5 truncate text-[9.5px] font-medium"
          style={{ color: deltaColor }}
        >
          {delta}
        </div>
      )}
    </div>
  );
}

const ETIQUETA_UBICACION: Record<EstadoGps["estado"], string> = {
  inactiva: "Usar mi ubicación",
  buscando: "Buscando…",
  activa: "Ubicación activa",
  denegada: "Ubicación bloqueada",
  no_disponible: "Sin GPS",
};

/** Activa/apaga la posición del dispositivo. El permiso del navegador se pide
 * recién al tocarlo; la posición nunca sale del dispositivo. */
function BotonUbicacion({ gps }: { gps: EstadoGps }) {
  const activa = gps.estado === "activa" || gps.estado === "buscando";
  return (
    <button
      type="button"
      disabled={gps.estado === "denegada" || gps.estado === "no_disponible"}
      onClick={activa ? gps.desactivar : gps.activar}
      title={
        gps.estado === "denegada"
          ? "Habilitá la ubicación para este sitio desde los permisos del navegador"
          : undefined
      }
      className={combinarClases(
        "h-9 flex-1 rounded-lg border px-2 text-[12px] font-semibold disabled:opacity-50",
        gps.estado === "activa"
          ? "border-[#2E5CFF] bg-[#2E5CFF]/10 text-[#2E5CFF]"
          : "border-borde-input bg-blanco text-texto-cuerpo",
      )}
    >
      {ETIQUETA_UBICACION[gps.estado]}
    </button>
  );
}

const TITULO_SECCION =
  "text-[9.5px] font-bold tracking-[0.12em] text-texto-mutado uppercase";

/** Dos pasos: el motivo del fallo y, con el motivo elegido, qué hacer con la entrega
 * (el chofer de empresa solo confirma: la decisión es de su empresa). */
function SelectorFallo({
  bloqueado,
  onFallar,
  puedeReprogramar,
}: {
  bloqueado: boolean;
  onFallar: (motivo: MotivoFalloParada, reprogramar: boolean) => void;
  puedeReprogramar: boolean;
}) {
  const [motivoElegido, setMotivoElegido] = useState<MotivoFalloParada | null>(
    null,
  );

  if (!motivoElegido) {
    return (
      <div className="mt-2.5">
        <div className={combinarClases("mb-1.5", TITULO_SECCION)}>
          ¿Por qué no pudiste entregar?
        </div>
        <div className="flex flex-wrap gap-1.5">
          {OPCIONES_MOTIVO_FALLO.map((motivo) => (
            <button
              key={motivo}
              type="button"
              disabled={bloqueado}
              onClick={() => setMotivoElegido(motivo)}
              className="h-8 rounded-lg border border-borde-input bg-blanco px-2.5 text-[11.5px] font-semibold text-texto-cuerpo disabled:opacity-60"
            >
              {ETIQUETA_MOTIVO[motivo]}
            </button>
          ))}
        </div>
      </div>
    );
  }

  if (!puedeReprogramar) {
    return (
      <div className="mt-2.5">
        <div className={combinarClases("mb-1.5", TITULO_SECCION)}>
          {ETIQUETA_MOTIVO[motivoElegido]}
        </div>
        <div className="flex gap-1.5">
          <button
            type="button"
            disabled={bloqueado}
            onClick={() => onFallar(motivoElegido, false)}
            className="h-9 flex-1 rounded-lg bg-primario px-3 text-[12px] font-bold text-blanco disabled:opacity-60"
          >
            Confirmar
          </button>
          <button
            type="button"
            disabled={bloqueado}
            onClick={() => setMotivoElegido(null)}
            className="h-9 rounded-lg px-3 text-[12px] font-semibold text-texto-mutado disabled:opacity-60"
          >
            Volver
          </button>
        </div>
        <p className="mt-1.5 text-[10.5px] text-texto-mutado">
          Tu empresa decide si la entrega se reprograma.
        </p>
      </div>
    );
  }

  return (
    <div className="mt-2.5">
      <div className={combinarClases("mb-1.5", TITULO_SECCION)}>
        {ETIQUETA_MOTIVO[motivoElegido]} · ¿Qué hacemos con esta entrega?
      </div>
      <div className="flex flex-col gap-1.5">
        <button
          type="button"
          disabled={bloqueado}
          onClick={() => onFallar(motivoElegido, true)}
          className="h-9 rounded-lg bg-primario px-3 text-[12px] font-bold text-blanco disabled:opacity-60"
        >
          Reprogramar para la próxima ruta
        </button>
        <div className="flex gap-1.5">
          <button
            type="button"
            disabled={bloqueado}
            onClick={() => onFallar(motivoElegido, false)}
            className="h-9 flex-1 rounded-lg border border-borde-input bg-blanco px-2 text-[12px] font-semibold text-texto-cuerpo disabled:opacity-60"
          >
            Decidir después
          </button>
          <button
            type="button"
            disabled={bloqueado}
            onClick={() => setMotivoElegido(null)}
            className="h-9 rounded-lg px-3 text-[12px] font-semibold text-texto-mutado disabled:opacity-60"
          >
            Volver
          </button>
        </div>
        <p className="text-[10.5px] text-texto-mutado">
          Si decidís después, la ves en Incidencias y la podés reprogramar desde
          ahí.
        </p>
      </div>
    </div>
  );
}

/** Overlay del mapa mientras hay una parada en curso: tarjeta con los datos
 * de esa parada arriba, y la barra de acciones (confirmar llegada, llamar
 * al cliente) abajo — separado de VistaEnCursoRuta para que esa función no
 * cargue con este bloque de JSX además del resto del dashboard. */
function OverlayParadaActual({
  paradaActual,
  indiceActual,
  totalParadas,
  usaVentanasHorarias,
  enviando,
  sinConexion,
  gps,
  onLlegue,
  onFallar,
  onSaltear,
  puedeSaltear,
  clienteActual,
  puedeReprogramar,
}: {
  paradaActual: ParadaRutaPublica;
  indiceActual: number;
  totalParadas: number;
  usaVentanasHorarias: boolean;
  enviando: boolean;
  /** Sin conexión las acciones que escriben se bloquean (no se encolan). */
  sinConexion: boolean;
  gps: EstadoGps;
  onLlegue: () => void;
  onFallar: (motivo: MotivoFalloParada, reprogramar: boolean) => void;
  onSaltear: () => void;
  puedeSaltear: boolean;
  clienteActual: ClientePublico | undefined;
  puedeReprogramar: boolean;
}) {
  // Estado puramente visual (el selector abierto/cerrado). Se reinicia solo al
  // cambiar de parada porque el padre monta este componente con `key`.
  const [eligiendoMotivo, setEligiendoMotivo] = useState(false);
  // En el celular la tarjeta arranca compacta (nombre y dirección) para no tapar el mapa;
  // desde lg siempre se muestra completa.
  const [detallesAbiertos, setDetallesAbiertos] = useState(false);
  const arribado = paradaActual.hora_real_llegada != null;
  const bloqueado = enviando || sinConexion;

  return (
    <>
      <div className="absolute top-2 right-2 left-2 z-[500] rounded-xl border border-borde bg-white/95 px-3 py-2.5 shadow-md backdrop-blur-[10px] sm:top-3 sm:right-3 sm:left-3 sm:px-3.5 sm:py-3">
        <div className="mb-1 flex items-center gap-2 lg:mb-1.5">
          <span className="h-2 w-2 rounded-full bg-primario" />
          <span className="flex-1 text-[9.5px] font-bold tracking-[0.12em] text-texto-mutado uppercase">
            Parada actual · {indiceActual + 1} de {totalParadas}
          </span>
          <button
            type="button"
            onClick={() => setDetallesAbiertos((abiertos) => !abiertos)}
            aria-expanded={detallesAbiertos}
            className="-my-1 flex h-7 items-center gap-1 rounded-md px-2 text-[11px] font-semibold text-primario hover:bg-primario/10 lg:hidden"
          >
            {detallesAbiertos ? "Menos" : "Opciones"}
            <span aria-hidden="true" className={combinarClases("transition-transform", detallesAbiertos && "rotate-180")}>
              ▾
            </span>
          </button>
        </div>
        <div className="truncate text-[15px] font-bold tracking-tight text-texto-fuerte lg:mb-0.5 lg:whitespace-normal">
          {paradaActual.nombre_snapshot}
        </div>
        <div className="truncate text-[12px] text-texto-mutado lg:mb-1.5">
          {paradaActual.direccion_snapshot}
        </div>

        <div className={combinarClases(detallesAbiertos ? "block" : "hidden", "mt-1.5 lg:mt-0 lg:block")}>
          <div className="flex flex-wrap items-center gap-3">
            <div>
              <div className="font-mono text-sm font-bold text-texto-fuerte">
                {paradaActual.demanda_carga_snapshot} kg
              </div>
              <div className="text-[10px] text-texto-mutado">carga</div>
            </div>
            {usaVentanasHorarias &&
              paradaActual.ventana_inicio_snapshot != null && (
                <>
                  <div className="h-6.5 w-px bg-borde" />
                  <div>
                    <div className="font-mono text-sm font-bold text-texto-fuerte">
                      {minutosAHhMm(paradaActual.ventana_inicio_snapshot)}–
                      {minutosAHhMm(paradaActual.ventana_fin_snapshot ?? 0)}
                    </div>
                    <div className="text-[10px] text-texto-mutado">ventana</div>
                  </div>
                </>
              )}
            {paradaActual.hora_estimada_llegada != null && (
              <span
                className={combinarClases(
                  "inline-flex items-center gap-1.5 rounded-pill px-2.5 py-1",
                  paradaActual.en_riesgo ? "bg-peligro-tint" : "bg-primario/10",
                )}
              >
                <span
                  className={combinarClases(
                    "h-1.5 w-1.5 rounded-full",
                    paradaActual.en_riesgo ? "bg-peligro" : "bg-primario",
                  )}
                />
                <span
                  className={combinarClases(
                    "font-mono text-[10.5px] font-semibold whitespace-nowrap",
                    paradaActual.en_riesgo ? "text-peligro" : "text-[#6428CC]",
                  )}
                >
                  {paradaActual.en_riesgo ? "Riesgo · " : "Llega "}
                  {minutosAHhMm(paradaActual.hora_estimada_llegada)}
                </span>
              </span>
            )}
          </div>

          <div className="mt-2.5 flex gap-2 border-t border-borde pt-2.5">
            <button
              type="button"
              disabled={bloqueado}
              onClick={() => setEligiendoMotivo((abierto) => !abierto)}
              className="h-9 flex-1 rounded-lg border border-peligro-borde bg-peligro-tint px-2 text-[12px] font-semibold text-peligro disabled:opacity-60"
            >
              No pude entregar
            </button>
            <button
              type="button"
              disabled={bloqueado || !puedeSaltear}
              onClick={onSaltear}
              title={puedeSaltear ? undefined : "Es la única parada que queda"}
              className="h-9 flex-1 rounded-lg border border-borde-input bg-blanco px-2 text-[12px] font-semibold text-texto-cuerpo disabled:opacity-50"
            >
              Saltear
            </button>
            <BotonUbicacion gps={gps} />
          </div>

          {eligiendoMotivo && (
            <SelectorFallo
              bloqueado={bloqueado}
              onFallar={onFallar}
              puedeReprogramar={puedeReprogramar}
            />
          )}
        </div>

        {sinConexion && (
          <p className="mt-2 text-[11px] text-peligro">
            Sin conexión: solo podés mirar la ruta. Las acciones se habilitan al
            volver la señal.
          </p>
        )}
      </div>

      <div className="absolute right-3.5 bottom-3 left-3.5 z-[500] flex gap-2 sm:gap-2.5">
        <button
          type="button"
          disabled={bloqueado}
          onClick={onLlegue}
          className="h-[52px] flex-1 rounded-xl bg-exito px-2 text-[12px] font-bold text-blanco shadow-[0_4px_12px_rgba(18,183,106,0.32)] disabled:opacity-60 sm:text-[13.5px]"
        >
          {enviando
            ? "Un momento…"
            : arribado
              ? "Confirmar entrega y seguir"
              : "Llegué al destino"}
        </button>
        {clienteActual?.telefono ? (
          <a
            href={`tel:${clienteActual.telefono}`}
            aria-label="Llamar al cliente"
            className="flex h-[52px] w-[52px] shrink-0 items-center justify-center rounded-xl border border-borde-input bg-white/95 text-[12.5px] font-semibold text-texto-cuerpo shadow-sm backdrop-blur-[8px] sm:w-[190px]"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="sm:hidden"
            >
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.362 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.338 1.85.573 2.81.7A2 2 0 0 1 22 16.92z" />
            </svg>
            <span className="hidden sm:inline">Llamar al cliente</span>
          </a>
        ) : null}
      </div>
    </>
  );
}

export function VistaEnCursoRuta({
  ruta,
  enviando,
  sinConexion,
  gps,
  error,
  ejecutar,
  usuario,
  clientePorId,
  puedeReprogramar,
}: {
  ruta: RutaPublica;
  enviando: boolean;
  sinConexion: boolean;
  gps: EstadoGps;
  error: string | null;
  ejecutar: EjecutarAccionRuta;
  usuario: UsuarioPublico;
  clientePorId: Map<string, ClientePublico>;
  /** El chofer de empresa informa el fallo; reprogramar lo decide su empresa. */
  puedeReprogramar: boolean;
}) {
  const paradas = ruta.paradas;
  const completadas = paradas.filter((p) => p.estado === "completada");
  const doneCount = completadas.length;
  const fallidasCount = paradas.filter((p) => p.estado === "fallida").length;
  const indiceActual = paradas.findIndex((p) => p.estado === "en_curso");
  const paradaActual = indiceActual === -1 ? undefined : paradas[indiceActual];

  // Solo un chofer con vehículo llega hasta acá: hace falta uno para planificar
  // cualquier ruta, propia o asignada (ver routing/planificador.py).
  const vehiculo = usuario.vehiculo!;

  const kgTotal = paradas.reduce((a, p) => a + p.demanda_carga_snapshot, 0);
  const kgEntregado = completadas.reduce(
    (a, p) => a + p.demanda_carga_snapshot,
    0,
  );
  const kgPendiente = kgTotal - kgEntregado;
  const cargaPendientePct = Math.round(
    (kgPendiente / vehiculo.capacidad_carga_kg) * 100,
  );

  const ultimaCompletada = [...completadas].sort(
    (a, b) => b.orden - a.orden,
  )[0];
  const kmRecorridos = ultimaCompletada
    ? ultimaCompletada.distancia_acumulada_m / 1000
    : 0;
  const kmPlanificados = (ruta.distancia_total_m ?? 0) / 1000;

  const ventanasCumplidas = completadas.filter(
    (p) => p.ventana_cumplida === true,
  ).length;
  const ventanasPct =
    doneCount > 0 ? Math.round((100 * ventanasCumplidas) / doneCount) : 0;

  const kpis: KpiProps[] = [
    {
      label: "Entregas de hoy",
      value: String(doneCount),
      unit: `de ${paradas.length}`,
      delta: `${Math.round((doneCount / paradas.length) * 100)}% completado${
        fallidasCount > 0 ? ` · ${fallidasCount} sin entregar` : ""
      }`,
      deltaColor: "#079455",
    },
    {
      label: "Carga entregada",
      value: String(kgEntregado),
      unit: `de ${kgTotal} kg`,
      delta: `${kgPendiente} kg a bordo`,
    },
    {
      label: "Km recorridos",
      value: kmRecorridos.toFixed(1),
      unit: "km",
      delta:
        kmPlanificados > 0
          ? `de ${kmPlanificados.toFixed(1)} km planificados`
          : "",
    },
    ruta.usa_ventanas_horarias
      ? {
          label: "Ventanas cumplidas",
          value: String(ventanasPct),
          unit: "%",
          delta: paradaActual?.en_riesgo
            ? "1 parada en riesgo ahora"
            : "sin riesgos activos",
          deltaColor: paradaActual?.en_riesgo ? "#B42318" : "#667085",
        }
      : {
          label: "Carga a bordo",
          value: String(kgPendiente),
          unit: "kg",
          delta: `${cargaPendientePct}% de la capacidad`,
        },
  ];

  const pendientesCount = paradas.filter(
    (p) => p.estado === "pendiente" || p.estado === "en_curso",
  ).length;

  // El "llegué" vive en el servidor (hora_real_llegada): recargar la página no
  // lo pierde. El primer toque registra la llegada, el segundo completa.
  async function manejarLlegue() {
    if (!paradaActual) return;
    if (paradaActual.hora_real_llegada == null) {
      await ejecutar(
        () => registrarLlegada(paradaActual.id),
        "No se pudo registrar la llegada.",
      );
      return;
    }
    await ejecutar(
      () => completarParada(paradaActual.id),
      "No se pudo marcar la parada.",
    );
  }

  async function manejarFallar(
    motivo: MotivoFalloParada,
    reprogramar: boolean,
  ) {
    if (!paradaActual) return;
    await ejecutar(
      () => fallarParada(paradaActual.id, motivo, reprogramar),
      "No se pudo registrar el problema.",
    );
  }

  async function manejarSaltear() {
    if (!paradaActual) return;
    await ejecutar(
      () => saltearParada(paradaActual.id),
      "No se pudo saltear la parada.",
    );
  }

  const puedeSaltear = paradas.some((p) => p.estado === "pendiente");

  const clienteActual = paradaActual
    ? clientePorId.get(paradaActual.cliente_id)
    : undefined;

  return (
    <div className="flex min-h-0 flex-col overflow-y-auto lg:h-full lg:flex-row lg:overflow-hidden">
      {/* En el celular el mapa va primero y ocupa casi toda la pantalla; los indicadores
          quedan debajo (order-*). Desde lg vuelve el orden del dashboard. */}
      <div className="flex min-w-0 flex-col gap-2.5 p-2.5 sm:p-5 lg:flex-1 lg:overflow-y-auto">
        {error && <BannerError>{error}</BannerError>}

        <div className="order-2 grid shrink-0 grid-cols-2 gap-2 lg:order-none lg:grid-cols-4">
          {kpis.map((kpi) => (
            <TarjetaKpi key={kpi.label} {...kpi} />
          ))}
        </div>

        <div className="order-1 h-[calc(100dvh-12rem)] min-h-[380px] shrink-0 sm:h-[480px] lg:order-none lg:min-h-[420px] lg:flex-1">
          <MapaRutaActiva
            deposito={ruta.deposito}
            paradas={ruta.paradas}
            overlaySimple={false}
            ubicacion={gps.ubicacion}
          >
            {paradaActual && (
              <OverlayParadaActual
                key={paradaActual.id}
                paradaActual={paradaActual}
                indiceActual={indiceActual}
                totalParadas={paradas.length}
                usaVentanasHorarias={ruta.usa_ventanas_horarias}
                enviando={enviando}
                sinConexion={sinConexion}
                gps={gps}
                onLlegue={manejarLlegue}
                onFallar={manejarFallar}
                onSaltear={manejarSaltear}
                puedeSaltear={puedeSaltear}
                clienteActual={clienteActual}
                puedeReprogramar={puedeReprogramar}
              />
            )}
          </MapaRutaActiva>
        </div>
      </div>

      <aside className="flex w-full shrink-0 flex-col border-t border-borde bg-white/86 backdrop-blur-[10px] lg:w-[372px] lg:overflow-y-auto lg:border-t-0 lg:border-l">
        <div className="shrink-0 border-b border-borde px-5 pt-4.5 pb-4">
          <div className="mb-2.5 text-[9.5px] font-bold tracking-[0.12em] text-texto-mutado uppercase">
            Mi carga
          </div>
          <div className="mb-2 h-2.5 overflow-hidden rounded-pill bg-superficie-hundida">
            <div
              className="h-full bg-primario"
              style={{ width: `${Math.min(100, cargaPendientePct)}%` }}
            />
          </div>
          <div className="flex justify-between font-mono text-xs text-texto-cuerpo">
            <span>
              {kgPendiente} kg / {vehiculo.capacidad_carga_kg} kg
            </span>
            <span>{cargaPendientePct}%</span>
          </div>
          <div className="mt-2 text-[11.5px] text-texto-mutado">
            {vehiculo.patente} · {vehiculo.capacidad_carga_kg} kg máx.
          </div>
        </div>

        {paradaActual?.en_riesgo && (
          <div className="mx-5 mt-3.5 rounded-[10px] border border-peligro-borde bg-peligro-tint px-3.5 py-3">
            <div className="mb-0.5 text-[11.5px] font-bold text-[#B42318]">
              Ventana horaria ajustada
            </div>
            <div className="text-[11.5px] leading-snug text-[#912018]">
              Llegás cerca del límite de{" "}
              {paradaActual.ventana_inicio_snapshot != null &&
                paradaActual.ventana_fin_snapshot != null &&
                `${minutosAHhMm(paradaActual.ventana_inicio_snapshot)}–${minutosAHhMm(paradaActual.ventana_fin_snapshot)}`}
              . Si no alcanzás, avisale al cliente desde "Llamar al cliente".
            </div>
          </div>
        )}

        <div className="flex shrink-0 items-baseline justify-between gap-2.5 px-5 pt-4 pb-2.5">
          <div className="text-[9.5px] font-bold tracking-[0.12em] text-texto-mutado uppercase">
            Mis paradas
          </div>
          <div className="font-mono text-[10.5px] text-texto-mutado">
            {doneCount}/{paradas.length} hechas
          </div>
        </div>

        <div className="min-h-0 flex-1 px-5 pb-4">
          {paradas.map((parada, indice) => (
            <FilaTimeline
              key={parada.id}
              parada={parada}
              indice={indice}
              usaVentanas={ruta.usa_ventanas_horarias}
              esUltima={indice === paradas.length - 1}
            />
          ))}
        </div>

        <div className="shrink-0 border-t border-borde bg-white/60 px-5 pt-3.5 pb-4.5">
          <div className="mb-1 flex items-baseline justify-between">
            <div className="text-[11.5px] font-semibold text-texto-mutado">
              Cierre estimado
            </div>
            {ruta.usa_ventanas_horarias &&
              ruta.hora_fin_estimada_min != null && (
                <div className="font-mono text-lg font-bold text-texto-fuerte">
                  {minutosAHhMm(ruta.hora_fin_estimada_min)}
                </div>
              )}
          </div>
          <div className="text-[10.5px] text-texto-mutado">
            {pendientesCount > 0
              ? `${pendientesCount} paradas pendientes`
              : "Todas las paradas entregadas — registrá el cierre en el depósito"}
          </div>
        </div>
      </aside>
    </div>
  );
}

const ESTILO_PARADA: Record<
  string,
  { nodo: string; linea: string; badge: string }
> = {
  completada: {
    nodo: "bg-exito border-exito text-blanco",
    linea: "bg-[#D3F2E0]",
    badge: "bg-exito-tint text-[#079455]",
  },
  fallida: {
    nodo: "bg-peligro border-peligro text-blanco",
    linea: "bg-borde",
    badge: "bg-peligro-tint text-peligro",
  },
  riesgo: {
    nodo: "bg-peligro border-peligro text-blanco",
    linea: "bg-borde",
    badge: "bg-peligro-tint text-peligro",
  },
  en_curso: {
    nodo: "bg-primario border-primario text-blanco",
    linea: "bg-borde",
    badge: "bg-primario/10 text-[#6428CC]",
  },
  pendiente: {
    nodo: "bg-blanco border-borde-input text-texto-mutado",
    linea: "bg-borde",
    badge: "bg-fondo text-texto-cuerpo",
  },
};

function FilaTimeline({
  parada,
  indice,
  usaVentanas,
  esUltima,
}: {
  parada: ParadaRutaPublica;
  indice: number;
  usaVentanas: boolean;
  esUltima: boolean;
}) {
  const enRiesgo = parada.estado === "en_curso" && parada.en_riesgo;
  const clave = enRiesgo ? "riesgo" : parada.estado;
  const estilo = ESTILO_PARADA[clave] ?? ESTILO_PARADA.pendiente;

  const ventana =
    usaVentanas &&
    parada.ventana_inicio_snapshot != null &&
    parada.ventana_fin_snapshot != null
      ? `${minutosAHhMm(parada.ventana_inicio_snapshot)}–${minutosAHhMm(parada.ventana_fin_snapshot)}`
      : null;
  const llegada =
    usaVentanas && parada.hora_estimada_llegada != null
      ? `${enRiesgo ? "Riesgo · " : "Llega "}${minutosAHhMm(parada.hora_estimada_llegada)}`
      : null;
  const etiquetas: Record<string, string> = {
    completada: "Entregada",
    fallida: `No entregada${parada.motivo_fallo ? ` · ${ETIQUETA_MOTIVO[parada.motivo_fallo]}` : ""}`,
    en_curso: llegada ?? "En curso",
    pendiente: ventana ?? "Pendiente",
  };
  const badgeLabel = etiquetas[parada.estado];

  return (
    <div className="grid grid-cols-[24px_1fr] gap-3">
      <div className="flex flex-col items-center">
        <div
          className={combinarClases(
            "flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-full border-2 font-mono text-[9.5px] font-bold",
            estilo.nodo,
          )}
        >
          {parada.estado === "completada"
            ? "✓"
            : parada.estado === "fallida"
              ? "✕"
              : indice + 1}
        </div>
        {!esUltima && (
          <div
            className={combinarClases("min-h-3.5 w-0.5 flex-1", estilo.linea)}
          />
        )}
      </div>
      <div className="min-w-0 pb-3.5">
        <div className="flex items-baseline justify-between gap-2">
          <div
            className={combinarClases(
              "truncate text-[12.5px] font-semibold",
              parada.estado === "completada"
                ? "text-texto-mutado"
                : "text-texto-fuerte",
            )}
          >
            {parada.nombre_snapshot}
          </div>
          <div className="shrink-0 font-mono text-[10.5px] text-texto-mutado">
            {parada.unidades_snapshot > 0
              ? `${parada.unidades_snapshot} u · `
              : ""}
            {parada.demanda_carga_snapshot} kg
          </div>
        </div>
        <div className="my-0.5 truncate text-[10.5px] text-texto-mutado">
          {parada.direccion_snapshot}
        </div>
        <span
          className={combinarClases(
            "inline-flex items-center gap-1.5 rounded-pill px-2 py-0.5 font-mono text-[9.5px] font-semibold whitespace-nowrap",
            estilo.badge,
          )}
        >
          {badgeLabel}
        </span>
      </div>
    </div>
  );
}
