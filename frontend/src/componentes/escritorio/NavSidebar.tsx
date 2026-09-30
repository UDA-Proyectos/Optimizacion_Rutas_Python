import type { ClientePublico } from "../../tipos/cliente";
import type { RutaPublica } from "../../tipos/ruta";
import { combinarClases } from "../ui/combinarClases";
import {
  IconoCuenta,
  IconoHistorial,
  IconoIncidencias,
  IconoLugares,
  IconoRuta,
  IconoVehiculo,
} from "./iconosNav";

export type Seccion = "ruta" | "lugares" | "historial" | "vehiculo" | "incidencias" | "cuenta";

/** El mismo nav se usa tal cual en el sidebar fijo de escritorio y en el
 * drawer de mobile (EscritorioChofer.tsx) — un solo lugar donde vive la
 * lista, en vez de dos copias que se puedan desincronizar. */
export function ItemsNav({
  seccion,
  ruta,
  clientes,
  incidenciasPendientes,
  onSeleccionar,
}: {
  seccion: Seccion;
  ruta: RutaPublica | null;
  clientes: ClientePublico[];
  incidenciasPendientes: number;
  onSeleccionar: (seccion: Seccion) => void;
}) {
  return (
    <>
      <p className="px-2.5 pt-1.5 pb-2 text-[9.5px] font-bold tracking-[0.12em] text-white/58 uppercase">
        Mi jornada
      </p>
      <BotonNav
        activo={seccion === "ruta"}
        onClick={() => onSeleccionar("ruta")}
        icono={<IconoRuta />}
        etiqueta="Ruta de hoy"
        badge={ruta ? String(ruta.paradas.length) : undefined}
      />
      <BotonNav
        activo={seccion === "lugares"}
        onClick={() => onSeleccionar("lugares")}
        icono={<IconoLugares />}
        etiqueta="Mis lugares"
        badge={clientes.length > 0 ? String(clientes.length) : undefined}
      />

      <p className="px-2.5 pt-4.5 pb-2 text-[9.5px] font-bold tracking-[0.12em] text-white/58 uppercase">
        Mi operación
      </p>
      <BotonNav
        activo={seccion === "historial"}
        onClick={() => onSeleccionar("historial")}
        icono={<IconoHistorial />}
        etiqueta="Historial de rutas"
      />
      <BotonNav
        activo={seccion === "vehiculo"}
        onClick={() => onSeleccionar("vehiculo")}
        icono={<IconoVehiculo />}
        etiqueta="Mi vehículo"
      />
      <BotonNav
        activo={seccion === "incidencias"}
        onClick={() => onSeleccionar("incidencias")}
        icono={<IconoIncidencias />}
        etiqueta="Incidencias"
        badge={incidenciasPendientes > 0 ? String(incidenciasPendientes) : undefined}
      />

      <p className="px-2.5 pt-4.5 pb-2 text-[9.5px] font-bold tracking-[0.12em] text-white/58 uppercase">
        Cuenta
      </p>
      <BotonNav
        activo={seccion === "cuenta"}
        onClick={() => onSeleccionar("cuenta")}
        icono={<IconoCuenta />}
        etiqueta="Mi cuenta"
      />
    </>
  );
}

function BotonNav({
  activo,
  onClick,
  icono,
  etiqueta,
  badge,
}: {
  activo: boolean;
  onClick: () => void;
  icono: React.ReactNode;
  etiqueta: string;
  badge?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={combinarClases(
        "flex h-10 w-full items-center gap-2.5 rounded-lg px-2.5 text-left text-[13px]",
        activo ? "bg-white/16 font-semibold text-blanco" : "font-medium text-white/78 hover:bg-white/8",
      )}
    >
      {icono}
      <span className="flex-1">{etiqueta}</span>
      {badge && (
        <span className="rounded-pill bg-white/16 px-1.5 py-0.5 font-mono text-[10.5px] font-semibold text-blanco">
          {badge}
        </span>
      )}
    </button>
  );
}
