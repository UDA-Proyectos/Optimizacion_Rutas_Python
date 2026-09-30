import type { InputHTMLAttributes } from "react";
import { useEffect, useState } from "react";

import { listarDepositos } from "../../api/depositos";
import { listarEntregasPendientes } from "../../api/entregasPendientes";
import { confirmarRuta, editarRuta, obtenerRutaActiva, optimizarRuta } from "../../api/rutas";
import { useEnvioFormulario } from "../../hooks/useEnvioFormulario";
import type { ClientePublico } from "../../tipos/cliente";
import type { DepositoPublico } from "../../tipos/deposito";
import type { EntregaPendientePublica } from "../../tipos/entregaPendiente";
import type { OptimizarRutaRequest, RutaPreview } from "../../tipos/ruta";
import { hhMmAMinutos, minutosAHhMm } from "../../utilidades/horario";
import { FormularioDeposito } from "../formularios/FormularioDeposito";
import { Boton } from "../ui/Boton";
import { CampoSelect } from "../ui/CampoSelect";
import { DatoNumerico } from "../ui/DatoNumerico";
import { BannerError } from "../ui/Formulario";
import { TarjetaContenido } from "../ui/TarjetaContenido";
import { TarjetaLugar } from "../ui/TarjetaLugar";
import { TextoVacio } from "../ui/TextoVacio";

interface DatosParada {
  carga_kg: number;
  unidades: number;
  ventana_inicio: number | null;
  ventana_fin: number | null;
}

// cliente_id -> lo que se lleva/necesita ahí hoy. La clave de presencia en
// este objeto ES la selección (agregar/sacar una clave marca o desmarca el
// checkbox), evita duplicar el estado en dos lugares distintos.
export type Seleccion = Record<string, DatosParada>;

export interface SeleccionInicial {
  seleccion: Seleccion;
  usaVentanasHorarias: boolean;
}

interface Props {
  clientes: ClientePublico[];
  /** true: reabre la ruta planificada de hoy con su selección precargada y
   * al confirmar la reemplaza (PUT), en vez de crear una nueva (POST). */
  modoEdicion?: boolean;
  /** Prellena la selección (ej. "usar de nuevo" desde el historial) sin
   * abrir el modo edición — arma una ruta nueva, no reemplaza ninguna. */
  seleccionInicial?: SeleccionInicial;
  onConfirmada: () => void;
  onCancelar: () => void;
}

type Vista = "cargando" | "deposito" | "seleccion" | "preview";

const DATOS_VACIOS: DatosParada = {
  carga_kg: 0,
  unidades: 0,
  ventana_inicio: null,
  ventana_fin: null,
};

/** Lo que se precarga al marcar un lugar: sus datos habituales (editables por
 * ruta sin tocar el lugar); sin datos habituales arranca vacío como siempre. */
function datosHabituales(cliente: ClientePublico): DatosParada {
  return {
    carga_kg: cliente.demanda_carga_default ?? 0,
    unidades: 0,
    ventana_inicio: cliente.ventana_inicio_default,
    ventana_fin: cliente.ventana_fin_default,
  };
}

/** Los datos de una entrega reprogramada son los de esa entrega puntual, así que
 * pisan a los habituales del lugar. */
function datosDeEntrega(entrega: EntregaPendientePublica): DatosParada {
  return {
    carga_kg: entrega.carga_kg,
    unidades: entrega.unidades,
    ventana_inicio: entrega.ventana_inicio,
    ventana_fin: entrega.ventana_fin,
  };
}

const CLASE_INPUT_CHICO =
  "h-9 w-[68px] shrink-0 rounded-md border border-borde-input bg-blanco px-2 text-right font-mono text-[13px] text-texto-fuerte outline-none transition-[border-color,box-shadow] duration-150 focus:border-primario focus:shadow-[0_0_0_3px_rgba(124,58,237,0.15)] focus-visible:outline-none";

/** Input chico con su etiqueta siempre visible arriba — el placeholder no
 * alcanza acá porque el valor nunca queda vacío (arranca en 0), así que
 * "kg"/"unid." nunca se llegaban a ver: quedaban 4 casilleros con "0" sin
 * ninguna pista de qué era cada uno. */
function CampoChico({
  etiqueta,
  ...inputProps
}: { etiqueta: string } & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="flex flex-col items-center gap-1">
      <span className="text-[9px] font-bold tracking-wide text-texto-tenue uppercase">
        {etiqueta}
      </span>
      <input className={CLASE_INPUT_CHICO} {...inputProps} />
    </label>
  );
}

export function FlujoArmarRuta({
  clientes,
  modoEdicion = false,
  seleccionInicial,
  onConfirmada,
  onCancelar,
}: Props) {
  const [vista, setVista] = useState<Vista>("cargando");
  const [seleccion, setSeleccion] = useState<Seleccion>({});
  const [usaVentanasHorarias, setUsaVentanasHorarias] = useState(false);
  const [preview, setPreview] = useState<RutaPreview | null>(null);
  const [depositos, setDepositos] = useState<DepositoPublico[]>([]);
  // cliente_id -> entrega reprogramada pendiente de ese lugar.
  const [reprogramadas, setReprogramadas] = useState<Record<string, EntregaPendientePublica>>({});
  // "" = sin elegir: el backend usa el primer depósito.
  const [depositoId, setDepositoId] = useState("");
  const { error, enviando, enviar } = useEnvioFormulario();

  useEffect(() => {
    if (modoEdicion) {
      // Si ya hay una ruta hoy, su depósito ya existe — no hace falta el
      // chequeo de depósito, directo a precargar la selección actual.
      Promise.all([obtenerRutaActiva(), listarDepositos()]).then(([ruta, listaDepositos]) => {
        const seleccionActual: Seleccion = {};
        for (const parada of ruta?.paradas ?? []) {
          seleccionActual[parada.cliente_id] = {
            carga_kg: parada.demanda_carga_snapshot,
            unidades: parada.unidades_snapshot,
            ventana_inicio: parada.ventana_inicio_snapshot,
            ventana_fin: parada.ventana_fin_snapshot,
          };
        }
        setSeleccion(seleccionActual);
        setUsaVentanasHorarias(ruta?.usa_ventanas_horarias ?? false);
        setDepositos(listaDepositos);
        // La ruta solo trae las coordenadas de su depósito: se reconoce por
        // ahí para no reasignarla al primero al guardar los cambios.
        const deDeLaRuta = listaDepositos.find(
          (d) => d.latitud === ruta?.deposito.latitud && d.longitud === ruta?.deposito.longitud,
        );
        setDepositoId(deDeLaRuta?.id ?? "");
        setVista("seleccion");
      });
      return;
    }
    if (seleccionInicial) {
      setSeleccion(seleccionInicial.seleccion);
      setUsaVentanasHorarias(seleccionInicial.usaVentanasHorarias);
    }
    listarDepositos().then((listaDepositos) => {
      setDepositos(listaDepositos);
      setVista(listaDepositos.length > 0 ? "seleccion" : "deposito");
    });
    // Las entregas reprogramadas se ofrecen ya marcadas y con sus datos; lo que
    // el chofer ya eligió (ej. "usar de nuevo") no se pisa. Sin conexión o ante
    // un error se sigue sin ellas: armar la ruta no depende de esto.
    listarEntregasPendientes()
      .then((entregas) => {
        setReprogramadas(Object.fromEntries(entregas.map((e) => [e.cliente_id, e])));
        const idsDeLugares = new Set(clientes.map((c) => c.id));
        setSeleccion((actual) => {
          const siguiente = { ...actual };
          for (const entrega of entregas) {
            if (idsDeLugares.has(entrega.cliente_id) && !(entrega.cliente_id in siguiente)) {
              siguiente[entrega.cliente_id] = datosDeEntrega(entrega);
            }
          }
          return siguiente;
        });
      })
      .catch(() => {});
    // seleccionInicial es un valor de una sola vez al montar (viene de "usar
    // de nuevo" en el historial) — no hace falta reaccionar a que cambie.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modoEdicion]);

  function alternarSeleccion(cliente: ClientePublico, marcado: boolean) {
    setSeleccion((actual) => {
      const siguiente = { ...actual };
      if (marcado) {
        const reprogramada = reprogramadas[cliente.id];
        siguiente[cliente.id] =
          actual[cliente.id] ??
          (reprogramada ? datosDeEntrega(reprogramada) : datosHabituales(cliente));
      } else {
        delete siguiente[cliente.id];
      }
      return siguiente;
    });
  }

  function cambiarDatos(clienteId: string, cambios: Partial<DatosParada>) {
    setSeleccion((actual) => ({
      ...actual,
      [clienteId]: { ...(actual[clienteId] ?? DATOS_VACIOS), ...cambios },
    }));
  }

  function pedido(): OptimizarRutaRequest {
    return {
      // Sin ventanas horarias se mandan en null aunque el lugar tenga un
      // horario habitual precargado: si no, quedarían guardadas en la ruta y
      // marcarían paradas "en riesgo" en una ruta que no las usa.
      paradas: Object.entries(seleccion).map(([cliente_id, datos]) => ({
        cliente_id,
        ...datos,
        ventana_inicio: usaVentanasHorarias ? datos.ventana_inicio : null,
        ventana_fin: usaVentanasHorarias ? datos.ventana_fin : null,
      })),
      usa_ventanas_horarias: usaVentanasHorarias,
      deposito_id: depositoId || null,
    };
  }

  function manejarOptimizar() {
    enviar(async () => {
      const resultado = await optimizarRuta(pedido());
      setPreview(resultado);
      setVista("preview");
    }, "No se pudo optimizar la ruta.");
  }

  function manejarConfirmar() {
    enviar(async () => {
      const guardar = modoEdicion ? editarRuta : confirmarRuta;
      await guardar(pedido());
      onConfirmada();
    }, "No se pudo guardar la ruta.");
  }

  if (vista === "cargando") {
    return <TextoVacio>Cargando…</TextoVacio>;
  }

  if (vista === "deposito") {
    return <FormularioDeposito onGuardado={() => setVista("seleccion")} onCancelar={onCancelar} />;
  }

  if (vista === "preview" && preview) {
    return (
      <div className="flex flex-col gap-4">
        <TarjetaContenido>
          <p className="mb-1.5 text-sm font-bold text-texto-fuerte">
            {preview.paradas.length} paradas · {(preview.distancia_total_m / 1000).toFixed(1)} km ·{" "}
            {preview.carga_total_kg} kg
          </p>
          <p className="text-[12.5px] text-texto-mutado">{preview.explicacion}</p>
          {preview.ahorro_m > 0 && (
            <p className="mt-2 text-[12.5px] font-semibold text-exito">
              Te ahorrás {(preview.ahorro_m / 1000).toFixed(1)} km recorridos comparado con
              visitarlos en el orden en que los elegiste.
            </p>
          )}
        </TarjetaContenido>
        {error && <BannerError>{error}</BannerError>}
        <ol className="flex flex-col gap-2.5">
          {preview.paradas.map((parada) => (
            <li
              key={parada.cliente_id}
              className="flex items-start justify-between gap-3 rounded-lg bg-blanco px-4 py-3.5 shadow-sm"
            >
              <div className="min-w-0 flex-1">
                <p className="mb-0.5 text-[13.5px] font-semibold text-texto-fuerte">
                  {parada.orden + 1}. {parada.nombre}
                </p>
                <p className="text-[12.5px] text-texto-cuerpo">{parada.direccion}</p>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-0.5">
                <DatoNumerico>{(parada.distancia_acumulada_m / 1000).toFixed(1)} km</DatoNumerico>
                {usaVentanasHorarias && parada.hora_estimada_llegada != null && (
                  <DatoNumerico className="text-texto-tenue">
                    llega {minutosAHhMm(parada.hora_estimada_llegada)}
                  </DatoNumerico>
                )}
              </div>
            </li>
          ))}
        </ol>
        <div className="flex gap-2.5 [&>*]:flex-1">
          <Boton type="button" variante="secundario" onClick={() => setVista("seleccion")}>
            Volver
          </Boton>
          <Boton type="button" variante="exito" cargando={enviando} onClick={manejarConfirmar}>
            {modoEdicion ? "Guardar cambios" : "Confirmar ruta"}
          </Boton>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <p className="text-[12.5px] text-texto-mutado">
        Elegí los lugares que visitás hoy y cuánto llevás a cada uno.
      </p>
      {Object.keys(reprogramadas).length > 0 && (
        <p className="rounded-md border border-primario/30 bg-primario/10 px-3 py-2.5 text-[12.5px] text-[#6428CC]">
          Tenés {Object.keys(reprogramadas).length} entrega
          {Object.keys(reprogramadas).length > 1 ? "s" : ""} reprogramada
          {Object.keys(reprogramadas).length > 1 ? "s" : ""}: ya las marcamos por vos. Podés
          desmarcarlas si hoy no las llevás; siguen pendientes.
        </p>
      )}
      <label className="flex cursor-pointer items-center gap-2.5 rounded-lg bg-blanco px-4 py-3 shadow-sm">
        <input
          type="checkbox"
          checked={usaVentanasHorarias}
          onChange={(e) => setUsaVentanasHorarias(e.target.checked)}
          className="h-[18px] w-[18px] shrink-0 cursor-pointer accent-primario"
        />
        <span className="text-[13px] font-semibold text-texto-fuerte">
          Usar ventanas horarias para esta ruta
        </span>
      </label>
      {depositos.length > 1 && (
        <CampoSelect
          etiqueta="Depósito de salida"
          opciones={depositos.map((d) => ({ valor: d.id, etiqueta: d.nombre }))}
          value={depositoId || depositos[0].id}
          onChange={(e) => setDepositoId(e.target.value)}
        />
      )}
      {error && <BannerError>{error}</BannerError>}
      <ul className="flex flex-col gap-2.5 xl:grid xl:grid-cols-2 xl:gap-3">
        {clientes.map((cliente) => {
          const marcado = cliente.id in seleccion;
          const datos = seleccion[cliente.id] ?? DATOS_VACIOS;
          return (
            <TarjetaLugar
              key={cliente.id}
              nombre={cliente.nombre}
              direccion={cliente.direccion}
              detalle={
                reprogramadas[cliente.id]
                  ? `Reprogramada · no se pudo entregar el ${reprogramadas[cliente.id].fecha_origen}`
                  : undefined
              }
              seleccionable={{
                marcado,
                onCambiar: (valor) => alternarSeleccion(cliente, valor),
              }}
              trailing={
                marcado && (
                  <div className="flex shrink-0 flex-wrap items-start justify-end gap-x-3 gap-y-2">
                    <div className="flex gap-1.5">
                      <CampoChico
                        etiqueta="Kg"
                        type="number"
                        min={0}
                        inputMode="numeric"
                        aria-label={`Carga en kg para ${cliente.nombre}`}
                        value={datos.carga_kg}
                        onChange={(e) => cambiarDatos(cliente.id, { carga_kg: Number(e.target.value) })}
                      />
                      <CampoChico
                        etiqueta="Bultos"
                        type="number"
                        min={0}
                        inputMode="numeric"
                        aria-label={`Unidades para ${cliente.nombre}`}
                        value={datos.unidades}
                        onChange={(e) => cambiarDatos(cliente.id, { unidades: Number(e.target.value) })}
                      />
                    </div>
                    {usaVentanasHorarias && (
                      <div className="flex gap-1.5">
                        <CampoChico
                          etiqueta="Desde"
                          type="time"
                          aria-label={`Hora desde para ${cliente.nombre}`}
                          value={datos.ventana_inicio != null ? minutosAHhMm(datos.ventana_inicio) : ""}
                          onChange={(e) =>
                            cambiarDatos(cliente.id, { ventana_inicio: hhMmAMinutos(e.target.value) })
                          }
                        />
                        <CampoChico
                          etiqueta="Hasta"
                          type="time"
                          aria-label={`Hora hasta para ${cliente.nombre}`}
                          value={datos.ventana_fin != null ? minutosAHhMm(datos.ventana_fin) : ""}
                          onChange={(e) =>
                            cambiarDatos(cliente.id, { ventana_fin: hhMmAMinutos(e.target.value) })
                          }
                        />
                      </div>
                    )}
                  </div>
                )
              }
            />
          );
        })}
      </ul>
      <div className="flex gap-2.5 [&>*]:flex-1">
        <Boton type="button" variante="secundario" onClick={onCancelar}>
          Cancelar
        </Boton>
        <Boton
          type="button"
          cargando={enviando}
          disabled={Object.keys(seleccion).length === 0}
          onClick={manejarOptimizar}
        >
          Optimizar ruta
        </Boton>
      </div>
    </div>
  );
}
