import { useEffect, useState } from "react";

import { listarClientes } from "../../api/clientes";
import { listarIncidencias } from "../../api/incidencias";
import { useRutasDelDia } from "../../hooks/useRutasDelDia";
import { useUbicacion } from "../../hooks/useUbicacion";
import { type AccionPendiente, PestanaLugares } from "../../paginas/PestanaLugares";
import type { UsuarioPublico } from "../../tipos/auth";
import type { ClientePublico } from "../../tipos/cliente";
import type { IncidenciaPublica } from "../../tipos/incidencia";
import type { RutaPublica } from "../../tipos/ruta";
import { etiquetaDia } from "../../utilidades/fechas";
import {
  construirUrlGoogleMaps,
  origenNavegacionParaParadaActual,
} from "../../utilidades/googleMaps";
import { PanelCuenta } from "../cuenta/PanelCuenta";
import { FormularioIncidencia } from "../incidencias/FormularioIncidencia";
import { PanelIncidencias } from "../incidencias/PanelIncidencias";
import { PanelHistorial } from "../historial/PanelHistorial";
import type { Seleccion } from "../rutas/FlujoArmarRuta";
import { RutaDeHoyEscritorio } from "../rutas/RutaDeHoyEscritorio";
import { BannerConexion } from "../ui/BannerConexion";
import { combinarClases } from "../ui/combinarClases";
import { PanelVehiculo } from "../vehiculo/PanelVehiculo";
import {
  IconoCuenta,
  IconoHistorial,
  IconoIncidencias,
  IconoLugares,
  IconoRuta,
  IconoVehiculo,
} from "./iconosNav";
import type { GrupoNav } from "./NavSidebar";
import { ShellEscritorio } from "./ShellEscritorio";

type Seccion = "ruta" | "lugares" | "historial" | "vehiculo" | "incidencias" | "cuenta";

const TITULOS: Record<Seccion, string> = {
  ruta: "Mis rutas",
  lugares: "Mis lugares",
  historial: "Historial de rutas",
  vehiculo: "Mi vehículo",
  incidencias: "Incidencias",
  cuenta: "Mi cuenta",
};

interface Props {
  usuario: UsuarioPublico;
  onLogout: () => void;
}

/** Escritorio de cualquier chofer. El independiente arma sus rutas y edita su vehículo;
 * el de empresa ejecuta las rutas que le asignan y consulta lo demás. */
export function EscritorioChofer({ usuario, onLogout }: Props) {
  const esIndependiente = usuario.empresa_id === null;
  const [seccion, setSeccion] = useState<Seccion>("ruta");
  const [accionPendiente, setAccionPendiente] = useState<AccionPendiente | undefined>(undefined);
  const [clientes, setClientes] = useState<ClientePublico[]>([]);
  const [incidencias, setIncidencias] = useState<IncidenciaPublica[]>([]);
  const [reportando, setReportando] = useState(false);
  const {
    fecha,
    moverDia,
    irAHoy,
    irARuta,
    rutas,
    enCurso,
    ruta,
    seleccionarRuta,
    cargando,
    enviando,
    error,
    sinConexion,
    copiaGuardadaEn,
    ejecutar,
  } = useRutasDelDia();
  const gps = useUbicacion();

  useEffect(() => {
    // Se dispara con cada cambio de sección (no solo al montar) para que el
    // badge de "Mis lugares" y el teléfono usado en "Llamar al cliente" no
    // queden desactualizados después de agregar/editar/eliminar un lugar.
    // Sin conexión estos pedidos fallan: se ignora, se conserva lo último visto.
    listarClientes()
      .then(setClientes)
      .catch(() => {});
    // Las incidencias también nacen fuera de esta sección (al marcar una
    // parada como no entregada), así que se refrescan igual.
    listarIncidencias()
      .then(setIncidencias)
      .catch(() => {});
  }, [seccion, ruta]);

  function recargarIncidencias() {
    listarIncidencias()
      .then(setIncidencias)
      .catch(() => {});
  }

  function manejarIncidenciaReportada() {
    setReportando(false);
    recargarIncidencias();
  }

  function irAEditarRuta(rutaAEditar: RutaPublica) {
    setAccionPendiente({ tipo: "editar", ruta: rutaAEditar });
    setSeccion("lugares");
  }

  // Arma una ruta nueva para el día que se está viendo.
  function irAArmarRuta() {
    setAccionPendiente({ tipo: "nueva", fecha });
    setSeccion("lugares");
  }

  // "Mis lugares" confirma/edita la ruta sobre su propia instancia de
  // FlujoArmarRuta, sin pasar por el hook de acá — hay que ubicarse en el día
  // de la ruta guardada y volver a pedirlo, si no "Mis rutas" mostraría lo de
  // antes de armarla.
  function manejarRutaConfirmada(guardada: RutaPublica) {
    setSeccion("ruta");
    irARuta(guardada.fecha, guardada.id);
  }

  function usarRutaDeNuevo(datos: { seleccion: Seleccion; usaVentanasHorarias: boolean }) {
    setAccionPendiente({ tipo: "copiar", ...datos });
    setSeccion("lugares");
  }

  const paradaActual = enCurso?.paradas.find((p) => p.estado === "en_curso");
  const origenNavegacion = enCurso
    ? origenNavegacionParaParadaActual(enCurso.deposito, enCurso.paradas, gps.ubicacion)
    : null;
  const clientePorId = new Map(clientes.map((c) => [c.id, c] as const));
  const incidenciasPendientes = incidencias.filter((i) => i.estado === "pendiente").length;

  const horaInicioEnCurso = enCurso?.hora_inicio_real
    ? new Date(enCurso.hora_inicio_real).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : null;

  const subtitulo =
    seccion === "ruta"
      ? ruta
        ? `${etiquetaDia(fecha)} · ${ruta.paradas.length} paradas`
        : `${etiquetaDia(fecha)} · sin rutas`
      : seccion === "lugares"
        ? `${clientes.length} lugares guardados`
        : seccion === "vehiculo"
          ? usuario.vehiculo?.patente
          : seccion === "incidencias"
            ? incidencias.length === 0
              ? "Sin incidencias registradas"
              : incidenciasPendientes === 0
                ? "No tenés incidencias pendientes"
                : `${incidenciasPendientes} incidencia${incidenciasPendientes > 1 ? "s" : ""} pendiente${incidenciasPendientes > 1 ? "s" : ""}`
            : seccion === "cuenta"
              ? usuario.email
              : undefined;

  const grupos: GrupoNav<Seccion>[] = [
    {
      titulo: "Mi jornada",
      items: [
        {
          id: "ruta",
          etiqueta: "Mis rutas",
          icono: <IconoRuta />,
          badge: ruta ? String(ruta.paradas.length) : undefined,
        },
        ...(esIndependiente
          ? [
              {
                id: "lugares" as const,
                etiqueta: "Mis lugares",
                icono: <IconoLugares />,
                badge: clientes.length > 0 ? String(clientes.length) : undefined,
              },
            ]
          : []),
      ],
    },
    {
      titulo: "Mi operación",
      items: [
        { id: "historial", etiqueta: "Historial de rutas", icono: <IconoHistorial /> },
        { id: "vehiculo", etiqueta: "Mi vehículo", icono: <IconoVehiculo /> },
        {
          id: "incidencias",
          etiqueta: "Incidencias",
          icono: <IconoIncidencias />,
          badge: incidenciasPendientes > 0 ? String(incidenciasPendientes) : undefined,
        },
      ],
    },
    { titulo: "Cuenta", items: [{ id: "cuenta", etiqueta: "Mi cuenta", icono: <IconoCuenta /> }] },
  ];

  return (
    <ShellEscritorio
      rol="Vista del chofer"
      grupos={grupos}
      seccion={seccion}
      onSeleccionar={setSeccion}
      titulo={TITULOS[seccion]}
      subtitulo={
        <>
          {enCurso && seccion === "ruta" ? (
            <div className="flex items-center gap-1.5 truncate text-[11.5px] font-semibold text-[#067647] lg:hidden">
              <span className="h-[7px] w-[7px] shrink-0 rounded-full bg-exito" />
              En ruta{horaInicioEnCurso && ` · desde ${horaInicioEnCurso}`}
            </div>
          ) : (
            subtitulo && <div className="truncate text-[11.5px] text-texto-mutado lg:hidden">{subtitulo}</div>
          )}
          {subtitulo && (
            <div className="hidden truncate text-[11.5px] text-texto-mutado lg:block">{subtitulo}</div>
          )}
        </>
      }
      acciones={
        <>
          {enCurso && (
            <div className="hidden items-center gap-2 rounded-pill border border-[#ABEFC6] bg-exito-tint px-3 py-1.5 lg:flex">
              <span className="h-[7px] w-[7px] shrink-0 rounded-full bg-exito" />
              <span className="text-[11.5px] font-semibold text-[#067647]">
                En ruta{horaInicioEnCurso && ` · desde ${horaInicioEnCurso}`}
              </span>
            </div>
          )}

          <button
            type="button"
            disabled={!enCurso || sinConexion}
            title={
              sinConexion
                ? "Necesitás conexión para reportar una incidencia"
                : enCurso
                  ? undefined
                  : "Iniciá tu ruta para reportar una incidencia"
            }
            onClick={() => setReportando(true)}
            aria-label="Reportar incidencia"
            className="flex h-[38px] w-[38px] items-center justify-center rounded-lg border border-borde-input bg-blanco text-[12.5px] font-semibold text-texto-cuerpo disabled:cursor-not-allowed disabled:opacity-60 lg:w-auto lg:px-3.5"
          >
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lg:hidden">
              <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            <span className="hidden lg:inline">Reportar incidencia</span>
          </button>

          <a
            href={
              paradaActual && origenNavegacion
                ? construirUrlGoogleMaps(origenNavegacion, {
                    latitud: paradaActual.latitud_snapshot,
                    longitud: paradaActual.longitud_snapshot,
                  })
                : undefined
            }
            target="_blank"
            rel="noopener noreferrer"
            aria-disabled={!paradaActual}
            aria-label="Abrir navegación"
            className={combinarClases(
              "flex h-[38px] items-center justify-center gap-1.5 rounded-lg bg-primario px-3 text-[12.5px] font-bold text-blanco shadow-boton-primario lg:px-4",
              !paradaActual && "pointer-events-none opacity-50",
            )}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="3 11 22 2 13 21 11 13 3 11" />
            </svg>
            <span className="lg:hidden">Ir</span>
            <span className="hidden lg:inline">Abrir navegación</span>
          </a>
        </>
      }
      banner={sinConexion && <BannerConexion copiaGuardadaEn={copiaGuardadaEn} />}
    >
      {seccion === "ruta" && (
        <RutaDeHoyEscritorio
          fecha={fecha}
          rutas={rutas}
          enCurso={enCurso}
          onMoverDia={moverDia}
          onIrAHoy={irAHoy}
          onSeleccionarRuta={seleccionarRuta}
          onIrARuta={irARuta}
          ruta={ruta}
          cargando={cargando}
          enviando={enviando}
          sinConexion={sinConexion}
          gps={gps}
          error={error}
          ejecutar={ejecutar}
          usuario={usuario}
          clientePorId={clientePorId}
          onIrAArmarRuta={irAArmarRuta}
          onIrAHistorial={() => setSeccion("historial")}
          onEditar={irAEditarRuta}
          puedePlanificar={esIndependiente}
        />
      )}

      {seccion === "lugares" && (
        <div className="p-4 lg:p-6">
          <PestanaLugares
            onRutaConfirmada={manejarRutaConfirmada}
            accionPendiente={accionPendiente}
            onAccionPendienteConsumida={() => setAccionPendiente(undefined)}
          />
        </div>
      )}

      {seccion === "historial" && (
        <div className="p-4 lg:p-6">
          <PanelHistorial
            clientes={clientes}
            onUsarDeNuevo={esIndependiente ? usarRutaDeNuevo : undefined}
          />
        </div>
      )}

      {seccion === "vehiculo" && (
        <div className="p-4 lg:p-6">
          <PanelVehiculo usuario={usuario} ruta={enCurso} editable={esIndependiente} />
        </div>
      )}

      {seccion === "incidencias" && (
        <div className="p-4 lg:p-6">
          <PanelIncidencias
            incidencias={incidencias}
            sinConexion={sinConexion}
            onActualizar={recargarIncidencias}
            alcance={esIndependiente ? "propias" : "deEmpresa"}
          />
        </div>
      )}

      {seccion === "cuenta" && <PanelCuenta usuario={usuario} onCerrarSesion={onLogout} />}

      {reportando && enCurso && (
        <div
          className="fixed inset-0 z-[900] flex items-center justify-center bg-[rgba(16,24,40,0.4)] p-4"
          onClick={() => setReportando(false)}
        >
          <div
            className="w-full max-w-[420px] rounded-2xl border border-borde bg-blanco px-5 py-5 shadow-md"
            onClick={(e) => e.stopPropagation()}
          >
            <p className="mb-4 text-[15px] font-bold text-texto-fuerte">Reportar incidencia</p>
            <FormularioIncidencia
              paradas={enCurso.paradas}
              onGuardada={manejarIncidenciaReportada}
              onCancelar={() => setReportando(false)}
            />
          </div>
        </div>
      )}
    </ShellEscritorio>
  );
}
