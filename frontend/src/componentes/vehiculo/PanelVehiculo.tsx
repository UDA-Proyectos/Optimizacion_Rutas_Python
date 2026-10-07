import { useState } from "react";

import type { UsuarioPublico } from "../../tipos/auth";
import type { RutaPublica } from "../../tipos/ruta";
import { OPCIONES_TIPO_VEHICULO } from "../formularios/opcionesVehiculo";
import { Boton } from "../ui/Boton";
import { combinarClases } from "../ui/combinarClases";
import { FormularioVehiculo } from "./FormularioVehiculo";

interface Props {
  usuario: UsuarioPublico;
  ruta: RutaPublica | null;
  /** El chofer de empresa ve su vehículo pero no lo edita. */
  editable: boolean;
}

/** Muestra los datos reales que carga el registro (ver usuario.vehiculo) y
 * permite editarlos, sin inventar campos que la app no trackea (VTV, seguro,
 * mantenimiento). */
export function PanelVehiculo({ usuario, ruta, editable }: Props) {
  const vehiculo = usuario.vehiculo;
  const [editando, setEditando] = useState(false);

  if (!vehiculo) {
    return (
      <p className="text-[13px] text-texto-mutado">No tenés un vehículo registrado todavía.</p>
    );
  }

  if (editando) {
    return (
      <div className="mx-auto max-w-[520px] rounded-2xl border border-borde bg-blanco px-6 py-7 shadow-md">
        <p className="mb-4 text-[15px] font-bold text-texto-fuerte">Editar mi vehículo</p>
        <p className="mb-4 text-[12px] text-texto-mutado">
          Mientras tengas rutas planificadas (de hoy o de otro día) o en curso no se puede cambiar
          la patente ni la capacidad: terminalas o cancelalas primero.
        </p>
        <FormularioVehiculo
          vehiculo={vehiculo}
          onGuardado={() => setEditando(false)}
          onCancelar={() => setEditando(false)}
        />
      </div>
    );
  }

  const etiquetaTipo =
    OPCIONES_TIPO_VEHICULO.find((op) => op.valor === vehiculo.tipo_vehiculo)?.etiqueta ??
    vehiculo.tipo_vehiculo;

  const cargaHoyKg = ruta
    ? ruta.paradas
        .filter((p) => p.estado !== "completada")
        .reduce((suma, p) => suma + p.demanda_carga_snapshot, 0)
    : null;
  const usoHoyPct =
    cargaHoyKg != null ? Math.min(100, Math.round((cargaHoyKg / vehiculo.capacidad_carga_kg) * 100)) : null;

  return (
    <div className="mx-auto flex max-w-[520px] flex-col gap-4">
      <div className="rounded-2xl border border-borde bg-blanco px-6 py-7 shadow-md">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-primario/10 text-[#6428CC]">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10 17h4V5H2v12h3" />
              <path d="M20 17h2v-3.34a4 4 0 0 0-1.17-2.83L19 9h-5v8h1" />
              <circle cx="7.5" cy="17.5" r="2.5" />
              <circle cx="17.5" cy="17.5" r="2.5" />
            </svg>
          </div>
          <div className="min-w-0 flex-1">
            <div className="font-mono text-xl font-bold tracking-wide text-texto-fuerte">
              {vehiculo.patente}
            </div>
            <div className="text-[12.5px] text-texto-mutado">{etiquetaTipo}</div>
          </div>
          <span
            className={combinarClases(
              "shrink-0 rounded-pill px-2.5 py-1 text-[11px] font-semibold",
              vehiculo.activo ? "bg-exito-tint text-exito" : "bg-peligro-tint text-peligro",
            )}
          >
            {vehiculo.activo ? "Activo" : "Inactivo"}
          </span>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-4 border-t border-borde pt-5">
          <div>
            <div className="text-[9.5px] font-bold tracking-[0.1em] text-texto-mutado uppercase">
              Capacidad de carga
            </div>
            <div className="mt-1 font-mono text-lg font-bold text-texto-fuerte">
              {vehiculo.capacidad_carga_kg} kg
            </div>
          </div>
          {usoHoyPct != null && (
            <div>
              <div className="text-[9.5px] font-bold tracking-[0.1em] text-texto-mutado uppercase">
                Uso de hoy
              </div>
              <div className="mt-1 font-mono text-lg font-bold text-texto-fuerte">
                {usoHoyPct}%{" "}
                <span className="text-[11px] font-medium text-texto-mutado">
                  ({cargaHoyKg} kg a bordo)
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {editable && (
        <Boton variante="secundario" onClick={() => setEditando(true)}>
          Editar vehículo
        </Boton>
      )}
    </div>
  );
}
