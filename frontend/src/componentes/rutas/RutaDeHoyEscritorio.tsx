import { eliminarRuta, iniciarRuta } from "../../api/rutas";
import type { EjecutarAccionRuta } from "../../hooks/useRutaActiva";
import type { EstadoGps } from "../../hooks/useUbicacion";
import type { UsuarioPublico } from "../../tipos/auth";
import type { ClientePublico } from "../../tipos/cliente";
import type { EstadoRuta, RutaPublica } from "../../tipos/ruta";
import { etiquetaDia, fechaLarga, hoyLocal } from "../../utilidades/fechas";
import { Boton } from "../ui/Boton";
import { combinarClases } from "../ui/combinarClases";
import { BannerError } from "../ui/Formulario";
import { CabeceraTarjeta, TituloTarjeta } from "../ui/TarjetaContenido";
import { TextoVacio } from "../ui/TextoVacio";
import { ResumenCierre } from "./ResumenCierre";
import { VistaEnCursoRuta } from "./VistaEnCursoRuta";

const ETIQUETA_ESTADO: Record<EstadoRuta, string> = {
  planificada: "Planificada",
  en_curso: "En curso",
  completada: "Completada",
  cancelada: "Cancelada",
};

const CHIP_ESTADO: Record<EstadoRuta, string> = {
  planificada: "bg-primario/10 text-[#6428CC]",
  en_curso: "bg-exito-tint text-[#067647]",
  completada: "bg-fondo text-texto-cuerpo",
  cancelada: "bg-peligro-tint text-peligro",
};

interface Props {
  fecha: string;
  rutas: RutaPublica[];
  enCurso: RutaPublica | null;
  ruta: RutaPublica | null;
  cargando: boolean;
  enviando: boolean;
  sinConexion: boolean;
  gps: EstadoGps;
  error: string | null;
  ejecutar: EjecutarAccionRuta;
  usuario: UsuarioPublico;
  clientePorId: Map<string, ClientePublico>;
  onMoverDia: (dias: number) => void;
  onIrAHoy: () => void;
  onSeleccionarRuta: (rutaId: string) => void;
  onIrARuta: (fecha: string, rutaId: string) => void;
  /** Arma una ruta nueva para el día que se está viendo. */
  onIrAArmarRuta: () => void;
  onIrAHistorial: () => void;
  onEditar: (ruta: RutaPublica) => void;
}

function TarjetaCentrada({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-full items-center justify-center p-4 sm:p-10">
      <div className="w-full max-w-[440px] rounded-2xl border border-borde bg-white/90 px-5 py-6 shadow-md backdrop-blur-[10px] sm:px-7 sm:py-8">
        {children}
      </div>
    </div>
  );
}

function nombreDeRuta(ruta: RutaPublica, indice: number): string {
  return ruta.nombre ?? `Ruta ${indice + 1}`;
}

export function RutaDeHoyEscritorio({
  fecha,
  rutas,
  enCurso,
  ruta,
  cargando,
  enviando,
  sinConexion,
  gps,
  error,
  ejecutar,
  usuario,
  clientePorId,
  onMoverDia,
  onIrAHoy,
  onSeleccionarRuta,
  onIrARuta,
  onIrAArmarRuta,
  onIrAHistorial,
  onEditar,
}: Props) {
  // Una ruta en curso de otro día no se pierde de vista: se ofrece volver a ella.
  const enCursoEnOtroDia = enCurso && enCurso.fecha !== fecha ? enCurso : null;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex shrink-0 flex-col gap-2 border-b border-borde bg-blanco/80 px-4 py-2.5 backdrop-blur-[10px] lg:px-6">
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1" role="group" aria-label="Día">
            <button
              type="button"
              onClick={() => onMoverDia(-1)}
              aria-label="Día anterior"
              className="flex h-8 w-8 items-center justify-center rounded-md border border-borde text-texto-fuerte hover:bg-fondo"
            >
              ‹
            </button>
            <button
              type="button"
              onClick={onIrAHoy}
              disabled={fecha === hoyLocal()}
              className="h-8 rounded-md border border-borde px-2.5 text-[12px] font-semibold text-texto-fuerte hover:bg-fondo disabled:opacity-50"
            >
              Hoy
            </button>
            <button
              type="button"
              onClick={() => onMoverDia(1)}
              aria-label="Día siguiente"
              className="flex h-8 w-8 items-center justify-center rounded-md border border-borde text-texto-fuerte hover:bg-fondo"
            >
              ›
            </button>
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-[13px] font-bold text-texto-fuerte">{etiquetaDia(fecha)}</p>
            <p className="truncate text-[11px] text-texto-mutado first-letter:uppercase">
              {fechaLarga(fecha)}
            </p>
          </div>
          <button
            type="button"
            onClick={onIrAArmarRuta}
            className="h-8 rounded-md bg-primario px-3 text-[12px] font-bold text-blanco"
          >
            + Armar ruta
          </button>
        </div>

        {rutas.length > 1 && (
          <div className="flex gap-1.5 overflow-x-auto" role="tablist" aria-label="Rutas del día">
            {rutas.map((r, indice) => (
              <button
                key={r.id}
                type="button"
                role="tab"
                aria-selected={ruta?.id === r.id}
                onClick={() => onSeleccionarRuta(r.id)}
                className={combinarClases(
                  "flex shrink-0 items-center gap-2 rounded-lg border px-3 py-1.5 text-left",
                  ruta?.id === r.id
                    ? "border-primario bg-primario/10"
                    : "border-borde bg-blanco hover:bg-fondo",
                )}
              >
                <span className="text-[12px] font-semibold text-texto-fuerte">
                  {nombreDeRuta(r, indice)}
                </span>
                <span className="font-mono text-[10.5px] text-texto-mutado">
                  {r.paradas.length} paradas
                </span>
                <span
                  className={combinarClases(
                    "rounded-pill px-2 py-0.5 text-[10px] font-semibold",
                    CHIP_ESTADO[r.estado],
                  )}
                >
                  {ETIQUETA_ESTADO[r.estado]}
                </span>
              </button>
            ))}
          </div>
        )}

        {enCursoEnOtroDia && (
          <div className="flex items-center justify-between gap-3 rounded-lg border border-[#ABEFC6] bg-exito-tint px-3 py-2">
            <p className="text-[12px] text-[#067647]">
              Tenés una ruta en curso del {etiquetaDia(enCursoEnOtroDia.fecha).toLowerCase()}
              {enCursoEnOtroDia.nombre ? ` (${enCursoEnOtroDia.nombre})` : ""}.
            </p>
            <button
              type="button"
              onClick={() => onIrARuta(enCursoEnOtroDia.fecha, enCursoEnOtroDia.id)}
              className="h-8 shrink-0 rounded-md bg-exito px-3 text-[12px] font-bold text-blanco"
            >
              Ir a la ruta
            </button>
          </div>
        )}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {cargando ? (
          <div className="flex h-full items-center justify-center">
            <TextoVacio>Cargando…</TextoVacio>
          </div>
        ) : !ruta ? (
          <TarjetaCentrada>
            <div className="flex flex-col items-center text-center">
              <p className="mb-1.5 text-[15px] font-bold text-texto-fuerte">
                {fecha === hoyLocal()
                  ? "Todavía no armaste ninguna ruta para hoy"
                  : `No tenés rutas para ${etiquetaDia(fecha).toLowerCase()}`}
              </p>
              <p className="mb-5 max-w-[280px] text-[13px] text-texto-mutado">
                Elegí los lugares que visitás y te armamos el mejor orden para recorrerlos.
              </p>
              <Boton tamanio="auto" onClick={onIrAArmarRuta}>
                Armar ruta
              </Boton>
            </div>
            {error && (
              <div className="mt-4">
                <BannerError>{error}</BannerError>
              </div>
            )}
          </TarjetaCentrada>
        ) : ruta.estado === "completada" && ruta.resumen ? (
          <TarjetaCentrada>
            <CabeceraTarjeta>
              <TituloTarjeta>¡Ruta completada!</TituloTarjeta>
            </CabeceraTarjeta>
            <div className="mb-4">
              <ResumenCierre resumen={ruta.resumen} totalParadas={ruta.paradas.length} />
            </div>
            <div className="flex gap-2.5 [&>*]:flex-1">
              <Boton variante="secundario" onClick={onIrAHistorial}>
                Ver historial
              </Boton>
              <Boton onClick={onIrAArmarRuta}>Armar otra ruta</Boton>
            </div>
          </TarjetaCentrada>
        ) : ruta.estado !== "en_curso" ? (
          <ResumenRuta
            ruta={ruta}
            fecha={fecha}
            hayOtraEnCurso={enCurso != null && enCurso.id !== ruta.id}
            enviando={enviando}
            sinConexion={sinConexion}
            error={error}
            ejecutar={ejecutar}
            onEditar={() => onEditar(ruta)}
          />
        ) : (
          <VistaEnCursoRuta
            ruta={ruta}
            enviando={enviando}
            sinConexion={sinConexion}
            gps={gps}
            error={error}
            ejecutar={ejecutar}
            usuario={usuario}
            clientePorId={clientePorId}
          />
        )}
      </div>
    </div>
  );
}

function ResumenRuta({
  ruta,
  fecha,
  hayOtraEnCurso,
  enviando,
  sinConexion,
  error,
  ejecutar,
  onEditar,
}: {
  ruta: RutaPublica;
  fecha: string;
  hayOtraEnCurso: boolean;
  enviando: boolean;
  sinConexion: boolean;
  error: string | null;
  ejecutar: Props["ejecutar"];
  onEditar: () => void;
}) {
  const cargaTotalKg = ruta.paradas.reduce((suma, p) => suma + p.demanda_carga_snapshot, 0);
  const cargaPct = Math.min(100, Math.round((cargaTotalKg / ruta.capacidad_vehiculo_kg) * 100));
  // Solo se inicia desde su día; las rutas de días futuros se preparan y esperan.
  const esDeUnDiaFuturo = ruta.fecha > hoyLocal();

  return (
    <TarjetaCentrada>
      <CabeceraTarjeta>
        <TituloTarjeta>
          {ruta.nombre ? `${ruta.nombre} · ` : ""}
          {ruta.estado === "planificada"
            ? esDeUnDiaFuturo
              ? `Ruta planificada para ${etiquetaDia(fecha).toLowerCase()}`
              : "Ruta lista para arrancar"
            : "¡Ruta completada!"}
        </TituloTarjeta>
      </CabeceraTarjeta>
      <p className="mb-2 font-mono text-[13px] text-texto-cuerpo">
        {ruta.paradas.length} paradas
        {ruta.distancia_total_m != null && ` · ${(ruta.distancia_total_m / 1000).toFixed(1)} km`}
        {` · ${cargaTotalKg}/${ruta.capacidad_vehiculo_kg} kg (${cargaPct}%)`}
      </p>
      {ruta.explicacion && <p className="mb-4 text-[12.5px] text-texto-mutado">{ruta.explicacion}</p>}

      {error && (
        <div className="mb-3">
          <BannerError>{error}</BannerError>
        </div>
      )}

      {ruta.estado === "planificada" && (
        <div className="flex flex-col gap-2.5">
          <Boton
            variante="exito"
            cargando={enviando}
            disabled={sinConexion || esDeUnDiaFuturo || hayOtraEnCurso}
            onClick={() =>
              ejecutar(() => iniciarRuta(ruta.id, hoyLocal()), "No se pudo iniciar la ruta.")
            }
          >
            Iniciar ruta
          </Boton>
          {esDeUnDiaFuturo && (
            <p className="text-center text-[11.5px] text-texto-mutado">
              Se puede iniciar el día de la ruta. Mientras tanto la podés editar o cancelar.
            </p>
          )}
          {hayOtraEnCurso && !esDeUnDiaFuturo && (
            <p className="text-center text-[11.5px] text-texto-mutado">
              Ya tenés otra ruta en curso: terminala o cancelala para iniciar esta.
            </p>
          )}
          {sinConexion && (
            <p className="text-center text-[11.5px] text-peligro">
              Sin conexión: la ruta se puede iniciar o cambiar cuando vuelva la señal.
            </p>
          )}
          <div className="flex gap-2.5 [&>*]:flex-1">
            <Boton variante="secundario" disabled={sinConexion} onClick={onEditar}>
              Editar
            </Boton>
            <Boton
              variante="peligro"
              cargando={enviando}
              disabled={sinConexion}
              onClick={() =>
                ejecutar(
                  () => eliminarRuta(ruta.id).then(() => undefined),
                  "No se pudo eliminar la ruta.",
                )
              }
            >
              Eliminar
            </Boton>
          </div>
        </div>
      )}
    </TarjetaCentrada>
  );
}
