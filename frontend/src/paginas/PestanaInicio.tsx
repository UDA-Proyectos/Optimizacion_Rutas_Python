import { completarParada, eliminarRuta, iniciarRuta } from "../api/rutas";
import { hoyLocal } from "../utilidades/fechas";
import { MapaRutaActiva } from "../componentes/rutas/MapaRutaActiva";
import { Boton } from "../componentes/ui/Boton";
import { BannerError } from "../componentes/ui/Formulario";
import { DatoNumerico } from "../componentes/ui/DatoNumerico";
import { CabeceraTarjeta, TarjetaContenido, TituloTarjeta } from "../componentes/ui/TarjetaContenido";
import { TarjetaLugar } from "../componentes/ui/TarjetaLugar";
import { TextoEyebrow } from "../componentes/ui/TextoEyebrow";
import { TextoVacio } from "../componentes/ui/TextoVacio";
import { combinarClases } from "../componentes/ui/combinarClases";
import { useRutaActiva } from "../hooks/useRutaActiva";
import type { EstadoRuta } from "../tipos/ruta";

const ETIQUETA_ESTADO: Record<EstadoRuta, string> = {
  planificada: "Planificada",
  en_curso: "En curso",
  completada: "Completada",
  cancelada: "Cancelada",
};

const CHIP_ESTADO: Record<EstadoRuta, string> = {
  planificada: "bg-primario/10 text-primario",
  en_curso: "bg-exito-tint text-exito",
  completada: "bg-exito-tint text-exito",
  cancelada: "bg-peligro-tint text-peligro",
};

interface Props {
  onEditar: () => void;
  /** undefined: este usuario no arma su propia ruta (chofer de empresa,
   * admin) — no hay a dónde mandarlo, así que el estado vacío no ofrece CTA. */
  onArmarRuta?: () => void;
}

export function PestanaInicio({ onEditar, onArmarRuta }: Props) {
  const { ruta, cargando, enviando, error, ejecutar } = useRutaActiva();

  if (cargando) {
    return <TextoVacio>Cargando…</TextoVacio>;
  }

  if (!ruta) {
    return (
      <div className="flex flex-col items-center gap-1 px-5 pt-12 pb-8 text-center">
        <svg className="mb-3 h-12 w-12" viewBox="0 0 48 48" fill="none" aria-hidden="true">
          <path
            d="M8 34c6-10 10-14 16-14s10 4 16 14"
            stroke="var(--color-borde-input)"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeDasharray="1 7"
          />
          <circle cx="8" cy="34" r="4" fill="var(--color-texto-fuerte)" />
          <circle cx="40" cy="34" r="4" fill="var(--color-primario)" />
        </svg>
        <p className="text-[15px] font-bold text-texto-fuerte">Todavía no armaste la ruta de hoy</p>
        <p className="mb-5 max-w-[280px] text-[13px] text-texto-mutado">
          Elegí los lugares que visitás y te armamos el mejor orden para recorrerlos.
        </p>
        {onArmarRuta && (
          <Boton tamanio="auto" onClick={onArmarRuta}>
            Armar ruta de hoy
          </Boton>
        )}
      </div>
    );
  }

  const paradasCompletadas = ruta.paradas.filter((parada) => parada.estado === "completada").length;
  const cargaTotalKg = ruta.paradas.reduce((suma, parada) => suma + parada.demanda_carga_snapshot, 0);
  const cargaUsadaPct = Math.min(100, Math.round((cargaTotalKg / ruta.capacidad_vehiculo_kg) * 100));
  const conMapa = ruta.estado === "en_curso";

  return (
    <div className="flex flex-col gap-4">
      <TarjetaContenido>
        <CabeceraTarjeta>
          <TituloTarjeta>Ruta de hoy</TituloTarjeta>
          <span
            className={combinarClases(
              "inline-flex items-center gap-1.5 whitespace-nowrap rounded-pill px-2.5 py-1 text-[11px] font-semibold tracking-[0.02em]",
              CHIP_ESTADO[ruta.estado],
            )}
          >
            <span
              className={combinarClases(
                "h-1.5 w-1.5 shrink-0 rounded-full bg-current",
                ruta.estado === "en_curso" && "animate-pulso-chip motion-reduce:animate-none",
              )}
            />
            {ETIQUETA_ESTADO[ruta.estado]}
          </span>
        </CabeceraTarjeta>
        <DatoNumerico as="p">
          {ruta.paradas.length} paradas
          {ruta.distancia_total_m != null && ` · ${(ruta.distancia_total_m / 1000).toFixed(1)} km`}
        </DatoNumerico>
        {ruta.explicacion && <p className="text-[12.5px] text-texto-mutado">{ruta.explicacion}</p>}
        {(ruta.estado === "planificada" || ruta.estado === "en_curso") && (
          <>
            <TextoEyebrow>Progreso del día</TextoEyebrow>
            <div className="flex items-end justify-between gap-3 border-t border-borde pt-3">
              <div className="flex flex-col gap-[3px]">
                <span className="font-mono text-[28px] leading-none font-bold text-primario">
                  {paradasCompletadas}
                  <span className="text-[19px] text-texto-tenue">/{ruta.paradas.length}</span>
                </span>
                <span className="text-[11.5px] font-medium text-texto-mutado">entregas completadas</span>
              </div>
              <div className="flex flex-col items-end gap-[3px]">
                <span className="text-[15px] font-semibold text-texto-fuerte">{cargaUsadaPct}%</span>
                <span className="text-[10.5px] text-texto-tenue">carga</span>
              </div>
            </div>
          </>
        )}
      </TarjetaContenido>

      {error && <BannerError>{error}</BannerError>}

      <div className={conMapa ? "xl:grid xl:grid-cols-[1fr_380px] xl:items-start xl:gap-5" : undefined}>
        {conMapa && (
          <div className="h-[280px] xl:h-[520px]">
            <MapaRutaActiva deposito={ruta.deposito} paradas={ruta.paradas} />
          </div>
        )}

        <ol className={combinarClases("flex flex-col gap-2.5", conMapa && "xl:max-h-[520px] xl:overflow-y-auto")}>
          {ruta.paradas.map((parada) => (
            <TarjetaLugar
              key={parada.id}
              numero={parada.orden + 1}
              nombre={parada.nombre_snapshot}
              direccion={parada.direccion_snapshot}
              estado={parada.estado}
              trailing={
                parada.estado === "en_curso" ? (
                  <Boton
                    variante="exito"
                    tamanio="chica"
                    cargando={enviando}
                    onClick={() =>
                      ejecutar(() => completarParada(parada.id), "No se pudo marcar la parada.")
                    }
                  >
                    Marcar visitada
                  </Boton>
                ) : (
                  <DatoNumerico>{parada.demanda_carga_snapshot} kg</DatoNumerico>
                )
              }
            />
          ))}
        </ol>
      </div>

      {ruta.estado === "planificada" && (
        <>
          <Boton
            variante="exito"
            cargando={enviando}
            onClick={() => ejecutar(() => iniciarRuta(ruta.id, hoyLocal()), "No se pudo iniciar la ruta.")}
          >
            Iniciar ruta
          </Boton>
          <div className="mt-2 flex gap-2.5 [&>*]:flex-1">
            <Boton variante="secundario" onClick={onEditar}>
              Editar
            </Boton>
            <Boton
              variante="peligro"
              cargando={enviando}
              onClick={() =>
                ejecutar(() => eliminarRuta(ruta.id).then(() => undefined), "No se pudo eliminar la ruta.")
              }
            >
              Eliminar
            </Boton>
          </div>
        </>
      )}

      {ruta.estado === "en_curso" && (
        <Boton
          variante="peligro"
          cargando={enviando}
          onClick={() =>
            ejecutar(() => eliminarRuta(ruta.id).then(() => undefined), "No se pudo cancelar la ruta.")
          }
        >
          Cancelar ruta
        </Boton>
      )}

      {ruta.estado === "completada" && (
        <TarjetaContenido>
          <p>
            ¡Ruta completada
            {ruta.distancia_total_m != null &&
              ` — recorriste ${(ruta.distancia_total_m / 1000).toFixed(1)} km`}
            !
          </p>
        </TarjetaContenido>
      )}
    </div>
  );
}
