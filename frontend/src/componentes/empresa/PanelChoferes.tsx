import { useEffect, useState } from "react";

import { generarCodigoInvitacion, listarCodigosInvitacion } from "../../api/auth";
import { listarChoferes } from "../../api/empresa";
import type { CodigoInvitacionPublico } from "../../tipos/auth";
import type { ChoferDeEmpresa } from "../../tipos/empresa";
import { hoyLocal } from "../../utilidades/fechas";
import { OPCIONES_TIPO_VEHICULO } from "../formularios/opcionesVehiculo";
import { Boton } from "../ui/Boton";
import { BannerError } from "../ui/Formulario";
import { CabeceraTarjeta, TarjetaContenido, TituloTarjeta } from "../ui/TarjetaContenido";
import { TextoVacio } from "../ui/TextoVacio";

function etiquetaVehiculo(chofer: ChoferDeEmpresa): string {
  if (!chofer.vehiculo) return "Sin vehículo";
  const tipo = OPCIONES_TIPO_VEHICULO.find((op) => op.valor === chofer.vehiculo?.tipo_vehiculo);
  return `${tipo?.etiqueta ?? chofer.vehiculo.tipo_vehiculo} · ${chofer.vehiculo.patente} · ${chofer.vehiculo.capacidad_carga_kg} kg`;
}

function EstadoDelDia({ chofer }: { chofer: ChoferDeEmpresa }) {
  if (chofer.tiene_ruta_en_curso) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-pill bg-exito-tint px-2.5 py-1 text-[11px] font-semibold text-[#067647]">
        <span className="h-1.5 w-1.5 rounded-full bg-exito" />
        En ruta
      </span>
    );
  }
  return (
    <span className="rounded-pill bg-fondo px-2.5 py-1 text-[11px] font-semibold text-texto-cuerpo">
      {chofer.rutas_del_dia === 0
        ? "Sin rutas hoy"
        : `${chofer.rutas_del_dia} ruta${chofer.rutas_del_dia > 1 ? "s" : ""} hoy`}
    </span>
  );
}

/** Choferes de la empresa y códigos de invitación para sumar choferes nuevos. */
export function PanelChoferes() {
  const [choferes, setChoferes] = useState<ChoferDeEmpresa[] | null>(null);
  const [codigos, setCodigos] = useState<CodigoInvitacionPublico[]>([]);
  const [generando, setGenerando] = useState(false);
  const [copiado, setCopiado] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function recargar() {
    const [listaChoferes, listaCodigos] = await Promise.all([
      listarChoferes(hoyLocal()),
      listarCodigosInvitacion(),
    ]);
    setChoferes(listaChoferes);
    setCodigos(listaCodigos);
  }

  useEffect(() => {
    // Los setState ocurren después del await de recargar(), no en el cuerpo del efecto.
    // oxlint-disable-next-line react/set-state-in-effect
    recargar().catch(() => setError("No se pudieron cargar los choferes."));
  }, []);

  async function generar() {
    setGenerando(true);
    setError(null);
    try {
      const nuevo = await generarCodigoInvitacion();
      setCodigos((actuales) => [nuevo, ...actuales]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo generar el código.");
    } finally {
      setGenerando(false);
    }
  }

  async function copiar(codigo: string) {
    try {
      await navigator.clipboard.writeText(codigo);
      setCopiado(codigo);
      setTimeout(() => setCopiado((actual) => (actual === codigo ? null : actual)), 2000);
    } catch {
      setError("No se pudo copiar. Seleccioná el código y copialo a mano.");
    }
  }

  const disponibles = codigos.filter((c) => !c.usado);
  const usados = codigos.filter((c) => c.usado);

  return (
    <div className="flex flex-col gap-4 xl:grid xl:grid-cols-[minmax(0,1fr)_340px] xl:items-start">
      <TarjetaContenido>
        <CabeceraTarjeta>
          <TituloTarjeta>Choferes de la empresa</TituloTarjeta>
          {choferes && (
            <span className="font-mono text-[11px] text-texto-mutado">{choferes.length}</span>
          )}
        </CabeceraTarjeta>
        {choferes === null ? (
          <TextoVacio>Cargando…</TextoVacio>
        ) : choferes.length === 0 ? (
          <TextoVacio>
            Todavía no se sumó ningún chofer. Generá un código de invitación y compartilo: el chofer
            lo usa al registrarse.
          </TextoVacio>
        ) : (
          <ul className="mt-2 flex flex-col divide-y divide-borde">
            {choferes.map((chofer) => (
              <li key={chofer.id} className="flex items-start gap-3 py-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primario font-mono text-sm font-bold text-blanco">
                  {chofer.nombre_completo.charAt(0).toUpperCase()}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[13.5px] font-semibold text-texto-fuerte">
                    {chofer.nombre_completo}
                    {!chofer.activo && (
                      <span className="ml-2 text-[11px] font-medium text-peligro">Inactivo</span>
                    )}
                  </p>
                  <p className="truncate text-[12px] text-texto-mutado">
                    {chofer.email}
                    {chofer.telefono && ` · ${chofer.telefono}`}
                  </p>
                  <p className="truncate font-mono text-[11.5px] text-texto-cuerpo">
                    {etiquetaVehiculo(chofer)}
                  </p>
                </div>
                <EstadoDelDia chofer={chofer} />
              </li>
            ))}
          </ul>
        )}
      </TarjetaContenido>

      <TarjetaContenido>
        <TituloTarjeta>Invitar choferes</TituloTarjeta>
        <p className="mb-3 text-[12.5px]">
          Cada código sirve para un solo chofer. Lo ingresa en "Tengo un código de invitación" al
          crear su cuenta.
        </p>
        {error && <BannerError className="mb-3">{error}</BannerError>}
        <Boton onClick={generar} cargando={generando}>
          Generar código
        </Boton>

        {disponibles.length > 0 && (
          <ul className="mt-4 flex flex-col gap-2">
            {disponibles.map((c) => (
              <li
                key={c.id}
                className="flex items-center justify-between gap-2 rounded-lg border border-borde px-3 py-2"
              >
                <span className="font-mono text-[15px] font-bold tracking-[0.12em] text-texto-fuerte select-all">
                  {c.codigo}
                </span>
                <button
                  type="button"
                  onClick={() => copiar(c.codigo)}
                  className="h-8 rounded-md border border-borde-input bg-blanco px-3 text-[12px] font-semibold text-texto-cuerpo hover:bg-fondo"
                >
                  {copiado === c.codigo ? "¡Copiado!" : "Copiar"}
                </button>
              </li>
            ))}
          </ul>
        )}

        {usados.length > 0 && (
          <>
            <p className="mt-4 mb-1.5 text-[10px] font-bold tracking-[0.12em] text-texto-tenue uppercase">
              Ya usados
            </p>
            <ul className="flex flex-col gap-1">
              {usados.map((c) => (
                <li key={c.id} className="font-mono text-[12px] text-texto-tenue line-through">
                  {c.codigo}
                </li>
              ))}
            </ul>
          </>
        )}
      </TarjetaContenido>
    </div>
  );
}
