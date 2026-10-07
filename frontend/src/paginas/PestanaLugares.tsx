import { useEffect, useState } from "react";

import { eliminarCliente, listarClientes } from "../api/clientes";
import { listarDepositos } from "../api/depositos";
import { FormularioCliente } from "../componentes/formularios/FormularioCliente";
import { FormularioDeposito } from "../componentes/formularios/FormularioDeposito";
import { FlujoArmarRuta, type SeleccionInicial } from "../componentes/rutas/FlujoArmarRuta";
import { Boton } from "../componentes/ui/Boton";
import { Enlace } from "../componentes/ui/Enlace";
import { CabeceraTarjeta, TarjetaContenido, TituloTarjeta } from "../componentes/ui/TarjetaContenido";
import { TarjetaLugar } from "../componentes/ui/TarjetaLugar";
import { TextoVacio } from "../componentes/ui/TextoVacio";
import type { ClientePublico } from "../tipos/cliente";
import type { DepositoPublico } from "../tipos/deposito";
import type { RutaPublica } from "../tipos/ruta";
import { resumenHabituales } from "../utilidades/habituales";

type Vista = "lista" | "formulario" | "ruta" | "deposito";

/** Señal externa para saltar directo a "armar ruta" con una acción ya
 * decidida — desde EscritorioChofer, nunca derivada de un valor local. Las
 * dos variantes comparten la misma forma de "acción pendiente que se
 * consume una vez y se limpia" en vez de vivir como dos pares de props
 * paralelos con el mismo ciclo de vida. */
export type AccionPendiente =
  | { tipo: "editar"; ruta: RutaPublica }
  | { tipo: "nueva"; fecha: string }
  | ({ tipo: "copiar" } & SeleccionInicial);

interface Props {
  /** Se llama con la ruta guardada, para que "Mis rutas" se ubique en su día. */
  onRutaConfirmada?: (ruta: RutaPublica) => void;
  accionPendiente?: AccionPendiente;
  onAccionPendienteConsumida?: () => void;
  /** Libreta compartida de una empresa (la gestiona el admin): las rutas se arman desde
   * su propia sección, no desde acá. */
  deEmpresa?: boolean;
}

export function PestanaLugares({
  onRutaConfirmada,
  accionPendiente,
  onAccionPendienteConsumida,
  deEmpresa = false,
}: Props) {
  const [clientes, setClientes] = useState<ClientePublico[]>([]);
  const [deposito, setDeposito] = useState<DepositoPublico | null>(null);
  const [cargando, setCargando] = useState(true);
  const [vista, setVista] = useState<Vista>("lista");
  // Ruta que se está editando (null: armando una nueva) y día con el que arranca una nueva.
  const [rutaEnEdicion, setRutaEnEdicion] = useState<RutaPublica | null>(null);
  const [fechaNueva, setFechaNueva] = useState<string | undefined>(undefined);
  // Snapshot local de la selección a copiar, tomado en el mismo efecto que
  // consume accionPendiente — leer accionPendiente de nuevo en el render de
  // "ruta" no alcanza: onAccionPendienteConsumida limpia esa prop en el
  // mismo tick en que este efecto cambia `vista`, así que para cuando
  // FlujoArmarRuta llega a montarse la prop ya volvió a estar vacía.
  const [seleccionInicial, setSeleccionInicial] = useState<SeleccionInicial | undefined>(
    undefined,
  );
  const [clienteEditando, setClienteEditando] = useState<ClientePublico | null>(null);

  async function recargar() {
    const [listaClientes, listaDepositos] = await Promise.all([listarClientes(), listarDepositos()]);
    setClientes(listaClientes);
    setDeposito(listaDepositos[0] ?? null);
  }

  useEffect(() => {
    // oxlint no distingue que los setState ocurren después de un await
    // dentro de recargar() — no hay setState síncrono ni loop de renders acá.
    // oxlint-disable-next-line react/set-state-in-effect
    recargar().finally(() => setCargando(false));
  }, []);

  useEffect(() => {
    // Sincroniza con una señal externa real (EscritorioChofer pidiendo
    // saltar a "armar ruta" con una acción ya decidida), no un valor
    // derivable en el render.
    if (!accionPendiente) return;
    // oxlint-disable-next-line react/set-state-in-effect
    setRutaEnEdicion(accionPendiente.tipo === "editar" ? accionPendiente.ruta : null);
    setFechaNueva(accionPendiente.tipo === "nueva" ? accionPendiente.fecha : undefined);
    setSeleccionInicial(
      accionPendiente.tipo === "copiar"
        ? {
            seleccion: accionPendiente.seleccion,
            usaVentanasHorarias: accionPendiente.usaVentanasHorarias,
          }
        : undefined,
    );
    setVista("ruta");
    onAccionPendienteConsumida?.();
  }, [accionPendiente, onAccionPendienteConsumida]);

  function abrirNuevo() {
    setClienteEditando(null);
    setVista("formulario");
  }

  function abrirEdicionLugar(cliente: ClientePublico) {
    setClienteEditando(cliente);
    setVista("formulario");
  }

  function abrirArmarRutaNueva() {
    setRutaEnEdicion(null);
    setFechaNueva(undefined);
    setSeleccionInicial(undefined);
    setVista("ruta");
  }

  function abrirDeposito() {
    setVista("deposito");
  }

  async function manejarGuardadoLugar() {
    setVista("lista");
    await recargar();
  }

  async function manejarGuardadoDeposito() {
    setVista("lista");
    await recargar();
  }

  async function manejarEliminarLugar(id: string) {
    await eliminarCliente(id);
    await recargar();
  }

  async function manejarRutaGuardada(ruta: RutaPublica) {
    setVista("lista");
    await recargar();
    onRutaConfirmada?.(ruta);
  }

  if (vista === "formulario") {
    return (
      <FormularioCliente
        cliente={clienteEditando}
        onGuardado={manejarGuardadoLugar}
        onCancelar={() => setVista("lista")}
      />
    );
  }

  if (vista === "ruta") {
    return (
      <FlujoArmarRuta
        clientes={clientes}
        rutaEdicion={rutaEnEdicion}
        fechaInicial={fechaNueva}
        seleccionInicial={rutaEnEdicion ? undefined : seleccionInicial}
        onConfirmada={manejarRutaGuardada}
        onCancelar={() => setVista("lista")}
      />
    );
  }

  if (vista === "deposito") {
    return (
      <FormularioDeposito
        deposito={deposito}
        onGuardado={manejarGuardadoDeposito}
        onCancelar={() => setVista("lista")}
      />
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {!cargando && (
        <TarjetaContenido>
          <CabeceraTarjeta>
            <TituloTarjeta>{deEmpresa ? "Depósito de la empresa" : "Mi depósito"}</TituloTarjeta>
            <Enlace onClick={abrirDeposito}>{deposito ? "Editar" : "+ Agregar"}</Enlace>
          </CabeceraTarjeta>
          <p className="text-[12.5px] text-texto-mutado">
            {deposito
              ? `${deposito.nombre} — de acá parten y a acá vuelven ${deEmpresa ? "las rutas de la flota" : "tus rutas"}.`
              : deEmpresa
                ? "Todavía no marcaste de dónde salen y a dónde vuelven los choferes."
                : "Todavía no marcaste de dónde salís y a dónde volvés cada día."}
          </p>
        </TarjetaContenido>
      )}

      <div className="mt-2 flex gap-2.5 [&>*]:flex-1">
        <Boton variante="secundario" onClick={abrirNuevo}>
          + Agregar lugar
        </Boton>
        {!deEmpresa && (
          <Boton onClick={abrirArmarRutaNueva} disabled={clientes.length === 0}>
            Armar ruta
          </Boton>
        )}
      </div>

      {cargando ? (
        <TextoVacio>Cargando…</TextoVacio>
      ) : clientes.length === 0 ? (
        <TextoVacio>
          {deEmpresa
            ? "Todavía no hay lugares cargados. Agregá los clientes que visita la flota y quedan disponibles para armar las rutas de cualquier chofer."
            : "Todavía no guardaste ningún lugar. Agregá las direcciones que visitás seguido para no tener que cargarlas cada vez."}
        </TextoVacio>
      ) : (
        <ul className="flex flex-col gap-2.5 xl:grid xl:grid-cols-2 xl:gap-3">
          {clientes.map((cliente) => (
            <TarjetaLugar
              key={cliente.id}
              nombre={cliente.nombre}
              direccion={cliente.direccion}
              telefono={cliente.telefono}
              detalle={resumenHabituales(cliente)}
              trailing={
                <div className="flex shrink-0 flex-col items-end gap-1.5">
                  <Enlace onClick={() => abrirEdicionLugar(cliente)}>Editar</Enlace>
                  <Enlace peligro onClick={() => manejarEliminarLugar(cliente.id)}>
                    Eliminar
                  </Enlace>
                </div>
              }
            />
          ))}
        </ul>
      )}
    </div>
  );
}
