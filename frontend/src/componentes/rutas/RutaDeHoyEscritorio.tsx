import { eliminarRuta, iniciarRuta } from "../../api/rutas";
import type { EjecutarAccionRuta } from "../../hooks/useRutaActiva";
import type { EstadoGps } from "../../hooks/useUbicacion";
import type { UsuarioPublico } from "../../tipos/auth";
import type { ClientePublico } from "../../tipos/cliente";
import type { RutaPublica } from "../../tipos/ruta";
import { Boton } from "../ui/Boton";
import { BannerError } from "../ui/Formulario";
import { CabeceraTarjeta, TituloTarjeta } from "../ui/TarjetaContenido";
import { TextoVacio } from "../ui/TextoVacio";
import { ResumenCierre } from "./ResumenCierre";
import { VistaEnCursoRuta } from "./VistaEnCursoRuta";

interface Props {
  ruta: RutaPublica | null;
  cargando: boolean;
  enviando: boolean;
  sinConexion: boolean;
  gps: EstadoGps;
  error: string | null;
  ejecutar: EjecutarAccionRuta;
  usuario: UsuarioPublico;
  clientePorId: Map<string, ClientePublico>;
  onIrAArmarRuta: () => void;
  onIrAHistorial: () => void;
  onEditar: () => void;
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

export function RutaDeHoyEscritorio({
  ruta,
  cargando,
  enviando,
  sinConexion,
  gps,
  error,
  ejecutar,
  usuario,
  clientePorId,
  onIrAArmarRuta,
  onIrAHistorial,
  onEditar,
}: Props) {
  if (cargando) {
    return (
      <div className="flex h-full items-center justify-center">
        <TextoVacio>Cargando…</TextoVacio>
      </div>
    );
  }

  if (!ruta) {
    return (
      <TarjetaCentrada>
        <div className="flex flex-col items-center text-center">
          <p className="mb-1.5 text-[15px] font-bold text-texto-fuerte">
            Todavía no armaste la ruta de hoy
          </p>
          <p className="mb-5 max-w-[280px] text-[13px] text-texto-mutado">
            Elegí los lugares que visitás y te armamos el mejor orden para recorrerlos.
          </p>
          <Boton tamanio="auto" onClick={onIrAArmarRuta}>
            Armar ruta de hoy
          </Boton>
        </div>
        {error && (
          <div className="mt-4">
            <BannerError>{error}</BannerError>
          </div>
        )}
      </TarjetaCentrada>
    );
  }

  if (ruta.estado === "completada" && ruta.resumen) {
    return (
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
    );
  }

  if (ruta.estado !== "en_curso") {
    return (
      <ResumenRuta
        ruta={ruta}
        enviando={enviando}
        sinConexion={sinConexion}
        error={error}
        ejecutar={ejecutar}
        onEditar={onEditar}
      />
    );
  }

  return (
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
  );
}

function ResumenRuta({
  ruta,
  enviando,
  sinConexion,
  error,
  ejecutar,
  onEditar,
}: {
  ruta: RutaPublica;
  enviando: boolean;
  sinConexion: boolean;
  error: string | null;
  ejecutar: Props["ejecutar"];
  onEditar: () => void;
}) {
  const cargaTotalKg = ruta.paradas.reduce((suma, p) => suma + p.demanda_carga_snapshot, 0);
  const cargaPct = Math.min(100, Math.round((cargaTotalKg / ruta.capacidad_vehiculo_kg) * 100));

  return (
    <TarjetaCentrada>
      <CabeceraTarjeta>
        <TituloTarjeta>
          {ruta.estado === "planificada" ? "Ruta lista para arrancar" : "¡Ruta completada!"}
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
            disabled={sinConexion}
            onClick={() => ejecutar(() => iniciarRuta(), "No se pudo iniciar la ruta.")}
          >
            Iniciar ruta
          </Boton>
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
                ejecutar(() => eliminarRuta().then(() => undefined), "No se pudo eliminar la ruta.")
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

