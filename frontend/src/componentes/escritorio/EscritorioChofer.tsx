import { useEffect, useState } from "react";

import { listarClientes } from "../../api/clientes";
import { listarIncidencias } from "../../api/incidencias";
import { useRutaActiva } from "../../hooks/useRutaActiva";
import { useUbicacion } from "../../hooks/useUbicacion";
import { type AccionPendiente, PestanaLugares } from "../../paginas/PestanaLugares";
import type { UsuarioPublico } from "../../tipos/auth";
import type { ClientePublico } from "../../tipos/cliente";
import type { IncidenciaPublica } from "../../tipos/incidencia";
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
import { ItemsNav, type Seccion } from "./NavSidebar";

const TITULOS: Record<Seccion, string> = {
  ruta: "Ruta de hoy",
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

export function EscritorioChofer({ usuario, onLogout }: Props) {
  const [seccion, setSeccion] = useState<Seccion>("ruta");
  const [menuAbierto, setMenuAbierto] = useState(false);
  const [accionPendiente, setAccionPendiente] = useState<AccionPendiente | undefined>(undefined);
  const [clientes, setClientes] = useState<ClientePublico[]>([]);
  const [incidencias, setIncidencias] = useState<IncidenciaPublica[]>([]);
  const [reportando, setReportando] = useState(false);
  const { ruta, cargando, enviando, error, sinConexion, copiaGuardadaEn, ejecutar, recargar } =
    useRutaActiva();
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

  function manejarIncidenciaReportada() {
    setReportando(false);
    listarIncidencias()
      .then(setIncidencias)
      .catch(() => {});
  }

  function irAEditarRuta() {
    setAccionPendiente({ tipo: "editar" });
    setSeccion("lugares");
  }

  function irAArmarRuta() {
    setSeccion("lugares");
  }

  // "Mis lugares" confirma/edita la ruta sobre su propia instancia de
  // FlujoArmarRuta, sin pasar por el useRutaActiva() de acá — hay que
  // refrescarlo a mano al volver, si no "Ruta de hoy" se queda mostrando el
  // estado vacío de cuando montó este componente.
  function manejarRutaConfirmada() {
    setSeccion("ruta");
    recargar();
  }

  function usarRutaDeNuevo(datos: { seleccion: Seleccion; usaVentanasHorarias: boolean }) {
    setAccionPendiente({ tipo: "copiar", ...datos });
    setSeccion("lugares");
  }

  const paradaActual = ruta?.paradas.find((p) => p.estado === "en_curso");
  const origenNavegacion = ruta
    ? origenNavegacionParaParadaActual(ruta.deposito, ruta.paradas, gps.ubicacion)
    : null;
  const clientePorId = new Map(clientes.map((c) => [c.id, c] as const));

  const subtitulo =
    seccion === "ruta"
      ? ruta
        ? `${ruta.paradas.length} paradas de hoy`
        : "Todavía no armaste tu ruta"
      : seccion === "lugares"
        ? `${clientes.length} lugares guardados`
        : seccion === "vehiculo"
          ? usuario.vehiculo?.patente
          : seccion === "incidencias"
            ? incidencias.length === 0
              ? "Sin incidencias registradas"
              : `${incidencias.length} incidencia${incidencias.length > 1 ? "s" : ""} reportada${incidencias.length > 1 ? "s" : ""}`
            : seccion === "cuenta"
              ? usuario.email
              : undefined;

  const estiloSidebar = {
    backgroundColor: "#2A1264",
    backgroundImage:
      "radial-gradient(420px 260px at 0% 0%, rgba(124,58,237,0.55), transparent 70%), linear-gradient(180deg, #35197A 0%, #1E0C4C 100%)",
  };

  return (
    <div className="flex h-dvh w-full flex-col lg:flex-row">
      {/* SIDEBAR de escritorio: columna fija a la izquierda desde lg, con el
          nav completo adentro. En mobile es solo la barra de marca — el
          nav completo vive en el drawer de abajo, no acá (nada de scroll
          horizontal). */}
      <aside className="flex shrink-0 flex-col text-blanco lg:w-[232px]" style={estiloSidebar}>
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
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-blanco">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6428CC" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="3 11 22 2 13 21 11 13 3 11" />
            </svg>
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-sm font-extrabold tracking-tight text-blanco">OptiRuta</div>
            <div className="hidden text-[9.5px] font-semibold tracking-[0.1em] text-white/60 uppercase lg:block">
              Vista del chofer
            </div>
          </div>
        </div>

        <nav className="hidden min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto p-3 lg:flex">
          <ItemsNav seccion={seccion} ruta={ruta} clientes={clientes} onSeleccionar={setSeccion} />
        </nav>
      </aside>

      {/* Drawer del menú en mobile — el mismo nav de arriba, ahora vertical
          y deslizable desde la izquierda, en vez de una tira horizontal
          que había que scrollear. */}
      {menuAbierto && (
        <div
          className="fixed inset-0 z-[900] animate-aparecer-fondo bg-[rgba(16,24,40,0.4)] lg:hidden"
          onClick={() => setMenuAbierto(false)}
        >
          <aside
            className="absolute top-0 left-0 flex h-full w-[min(280px,80vw)] animate-deslizar-panel-izq flex-col text-blanco"
            style={estiloSidebar}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex h-14 shrink-0 items-center justify-between gap-2.5 border-b border-white/12 px-4">
              <div className="flex min-w-0 items-center gap-2.5">
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-blanco">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6428CC" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="3 11 22 2 13 21 11 13 3 11" />
                  </svg>
                </div>
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
                seccion={seccion}
                ruta={ruta}
                clientes={clientes}
                onSeleccionar={(s) => {
                  setSeccion(s);
                  setMenuAbierto(false);
                }}
              />
            </nav>
          </aside>
        </div>
      )}

      {/* MAIN */}
      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <header className="flex shrink-0 flex-col gap-2.5 border-b border-borde bg-blanco px-4 py-3 lg:h-16 lg:flex-row lg:items-center lg:gap-4 lg:px-6 lg:py-0">
          <div className="min-w-0 flex-1">
            <div className="text-base font-bold tracking-tight text-texto-fuerte">
              {TITULOS[seccion]}
            </div>
            {subtitulo && <div className="text-[11.5px] text-texto-mutado">{subtitulo}</div>}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {ruta?.estado === "en_curso" && (
              <div className="flex items-center gap-2 rounded-pill border border-[#ABEFC6] bg-exito-tint px-3 py-1.5">
                <span className="h-[7px] w-[7px] shrink-0 rounded-full bg-exito" />
                <span className="text-[11.5px] font-semibold text-[#067647]">
                  En ruta
                  {ruta.hora_inicio_real &&
                    ` · desde ${new Date(ruta.hora_inicio_real).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`}
                </span>
              </div>
            )}

            <button
              type="button"
              disabled={ruta?.estado !== "en_curso" || sinConexion}
              title={
                sinConexion
                  ? "Necesitás conexión para reportar una incidencia"
                  : ruta?.estado === "en_curso"
                    ? undefined
                    : "Iniciá tu ruta para reportar una incidencia"
              }
              onClick={() => setReportando(true)}
              className="h-[38px] rounded-lg border border-borde-input bg-blanco px-3.5 text-[12.5px] font-semibold text-texto-cuerpo disabled:cursor-not-allowed disabled:opacity-60"
            >
              Reportar incidencia
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
              className={combinarClases(
                "flex h-[38px] items-center gap-1.5 rounded-lg bg-primario px-4 text-[12.5px] font-bold text-blanco shadow-boton-primario",
                !paradaActual && "pointer-events-none opacity-50",
              )}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="3 11 22 2 13 21 11 13 3 11" />
              </svg>
              Abrir navegación
            </a>
          </div>
        </header>

        {sinConexion && <BannerConexion copiaGuardadaEn={copiaGuardadaEn} />}

        <div
          className="min-h-0 flex-1 overflow-y-auto"
          style={{
            backgroundColor: "#EEEDF6",
            backgroundImage:
              "radial-gradient(900px 480px at 8% 0%, rgba(124,58,237,0.10), transparent 62%), radial-gradient(700px 420px at 96% 100%, rgba(15,118,110,0.07), transparent 60%), linear-gradient(160deg, #F7F6FC 0%, #EAEAF3 100%)",
          }}
        >
          {seccion === "ruta" && (
            <RutaDeHoyEscritorio
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
              <PanelHistorial clientes={clientes} onUsarDeNuevo={usarRutaDeNuevo} />
            </div>
          )}

          {seccion === "vehiculo" && (
            <div className="p-4 lg:p-6">
              <PanelVehiculo usuario={usuario} ruta={ruta} />
            </div>
          )}

          {seccion === "incidencias" && (
            <div className="p-4 lg:p-6">
              <PanelIncidencias incidencias={incidencias} />
            </div>
          )}

          {seccion === "cuenta" && <PanelCuenta usuario={usuario} onCerrarSesion={onLogout} />}
        </div>
      </div>

      {reportando && ruta && (
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
              paradas={ruta.paradas}
              onGuardada={manejarIncidenciaReportada}
              onCancelar={() => setReportando(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
