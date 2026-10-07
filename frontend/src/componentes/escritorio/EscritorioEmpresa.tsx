import { useEffect, useState } from "react";

import { listarIncidencias } from "../../api/incidencias";
import { useEnLinea } from "../../hooks/useEnLinea";
import { PestanaLugares } from "../../paginas/PestanaLugares";
import type { UsuarioPublico } from "../../tipos/auth";
import type { IncidenciaPublica } from "../../tipos/incidencia";
import type { RutaPublica } from "../../tipos/ruta";
import { hoyLocal } from "../../utilidades/fechas";
import { PanelCuenta } from "../cuenta/PanelCuenta";
import { PanelArmarRutaEmpresa } from "../empresa/PanelArmarRutaEmpresa";
import { PanelChoferes } from "../empresa/PanelChoferes";
import { PanelFlotaHoy } from "../empresa/PanelFlotaHoy";
import { PanelHistorialFlota } from "../empresa/PanelHistorialFlota";
import { PanelIncidencias } from "../incidencias/PanelIncidencias";
import { BannerConexion } from "../ui/BannerConexion";
import {
  IconoArmarRuta,
  IconoChoferes,
  IconoCuenta,
  IconoHistorial,
  IconoHoy,
  IconoIncidencias,
  IconoLugares,
} from "./iconosNav";
import type { GrupoNav } from "./NavSidebar";
import { ShellEscritorio } from "./ShellEscritorio";

type Seccion = "hoy" | "armar" | "choferes" | "lugares" | "historial" | "incidencias" | "cuenta";

const TITULOS: Record<Seccion, string> = {
  hoy: "Hoy",
  armar: "Armar ruta",
  choferes: "Choferes",
  lugares: "Lugares",
  historial: "Historial de la flota",
  incidencias: "Incidencias",
  cuenta: "Mi cuenta",
};

interface Props {
  usuario: UsuarioPublico;
  onLogout: () => void;
}

/** Escritorio del admin de empresa: planifica y sigue a su flota con el mismo shell
 * que el chofer. */
export function EscritorioEmpresa({ usuario, onLogout }: Props) {
  const enLinea = useEnLinea();
  const [seccion, setSeccion] = useState<Seccion>("hoy");
  // Día que muestra "Hoy" (después de armar una ruta, el de esa ruta).
  const [fechaHoy, setFechaHoy] = useState(hoyLocal());
  const [rutaEdicion, setRutaEdicion] = useState<RutaPublica | null>(null);
  const [incidencias, setIncidencias] = useState<IncidenciaPublica[]>([]);

  function recargarIncidencias() {
    listarIncidencias()
      .then(setIncidencias)
      .catch(() => {});
  }

  useEffect(() => {
    // Las incidencias nacen en las rutas de los choferes: se refrescan al navegar.
    recargarIncidencias();
  }, [seccion]);

  function seleccionar(nueva: Seccion) {
    if (nueva === "armar") setRutaEdicion(null);
    setSeccion(nueva);
  }

  function editarRuta(ruta: RutaPublica) {
    setRutaEdicion(ruta);
    setSeccion("armar");
  }

  function manejarRutaGuardada(ruta: RutaPublica) {
    setRutaEdicion(null);
    setFechaHoy(ruta.fecha);
    setSeccion("hoy");
  }

  const incidenciasPendientes = incidencias.filter((i) => i.estado === "pendiente").length;

  const grupos: GrupoNav<Seccion>[] = [
    {
      titulo: "Mi jornada",
      items: [
        { id: "hoy", etiqueta: "Hoy", icono: <IconoHoy /> },
        { id: "armar", etiqueta: "Armar ruta", icono: <IconoArmarRuta /> },
      ],
    },
    {
      titulo: "Mi flota",
      items: [
        { id: "choferes", etiqueta: "Choferes", icono: <IconoChoferes /> },
        { id: "lugares", etiqueta: "Lugares", icono: <IconoLugares /> },
        { id: "historial", etiqueta: "Historial", icono: <IconoHistorial /> },
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
      rol="Vista de empresa"
      grupos={grupos}
      seccion={seccion}
      onSeleccionar={seleccionar}
      titulo={rutaEdicion && seccion === "armar" ? "Editar ruta" : TITULOS[seccion]}
      subtitulo={
        <div className="truncate text-[11.5px] text-texto-mutado">
          {usuario.nombre_completo} · Administrador
        </div>
      }
      banner={!enLinea && <BannerConexion copiaGuardadaEn={null} />}
    >
      <div className="p-4 lg:p-6">
        {seccion === "hoy" && (
          <PanelFlotaHoy key={fechaHoy} fechaInicial={fechaHoy} onEditar={editarRuta} />
        )}
        {seccion === "armar" && (
          <PanelArmarRutaEmpresa
            key={rutaEdicion?.id ?? "nueva"}
            rutaEdicion={rutaEdicion}
            onConfirmada={manejarRutaGuardada}
            onCancelar={() => seleccionar("hoy")}
          />
        )}
        {seccion === "choferes" && <PanelChoferes />}
        {seccion === "lugares" && <PestanaLugares deEmpresa />}
        {seccion === "historial" && <PanelHistorialFlota />}
        {seccion === "incidencias" && (
          <PanelIncidencias
            incidencias={incidencias}
            sinConexion={!enLinea}
            onActualizar={recargarIncidencias}
            alcance="flota"
          />
        )}
      </div>
      {seccion === "cuenta" && <PanelCuenta usuario={usuario} onCerrarSesion={onLogout} />}
    </ShellEscritorio>
  );
}
