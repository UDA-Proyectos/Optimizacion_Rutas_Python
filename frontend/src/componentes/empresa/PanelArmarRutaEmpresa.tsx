import { useEffect, useState } from "react";

import { listarClientes } from "../../api/clientes";
import { listarChoferes } from "../../api/empresa";
import type { ClientePublico } from "../../tipos/cliente";
import type { ChoferDeEmpresa } from "../../tipos/empresa";
import type { RutaPublica } from "../../tipos/ruta";
import { hoyLocal } from "../../utilidades/fechas";
import { FlujoArmarRuta } from "../rutas/FlujoArmarRuta";
import { CampoSelect } from "../ui/CampoSelect";
import { TarjetaContenido, TituloTarjeta } from "../ui/TarjetaContenido";
import { TextoVacio } from "../ui/TextoVacio";

interface Props {
  /** Ruta planificada de la flota a editar: conserva su chofer. */
  rutaEdicion?: RutaPublica | null;
  fechaInicial?: string;
  onConfirmada: (ruta: RutaPublica) => void;
  onCancelar: () => void;
}

/** Armado de rutas del admin: el mismo flujo que el chofer independiente, eligiendo
 * antes a qué chofer de la flota se le asigna. */
export function PanelArmarRutaEmpresa({
  rutaEdicion = null,
  fechaInicial,
  onConfirmada,
  onCancelar,
}: Props) {
  const [choferes, setChoferes] = useState<ChoferDeEmpresa[] | null>(null);
  const [clientes, setClientes] = useState<ClientePublico[]>([]);
  const [choferId, setChoferId] = useState(rutaEdicion?.chofer_id ?? "");

  useEffect(() => {
    Promise.all([listarChoferes(hoyLocal()), listarClientes()])
      .then(([listaChoferes, listaClientes]) => {
        setChoferes(listaChoferes);
        setClientes(listaClientes);
      })
      .catch(() => setChoferes([]));
  }, []);

  if (choferes === null) {
    return <TextoVacio>Cargando…</TextoVacio>;
  }

  // Solo se le puede asignar una ruta a quien tiene con qué hacerla.
  const disponibles = choferes.filter((c) => c.activo && c.vehiculo);
  const elegido = choferes.find((c) => c.id === choferId);

  return (
    <div className="flex flex-col gap-4">
      <TarjetaContenido>
        <TituloTarjeta>{rutaEdicion ? "Chofer de la ruta" : "¿A quién se la asignás?"}</TituloTarjeta>
        {rutaEdicion ? (
          <p className="text-[13px] font-semibold text-texto-fuerte">{rutaEdicion.chofer_nombre}</p>
        ) : disponibles.length === 0 ? (
          <p className="text-[12.5px]">
            Todavía no hay choferes con vehículo en la flota. Invitá choferes desde la sección
            Choferes.
          </p>
        ) : (
          <CampoSelect
            etiqueta="Chofer"
            placeholder="Elegí un chofer"
            opciones={disponibles.map((c) => ({
              valor: c.id,
              etiqueta: `${c.nombre_completo} · ${c.vehiculo?.patente} · ${c.vehiculo?.capacidad_carga_kg} kg`,
            }))}
            value={choferId}
            onChange={(e) => setChoferId(e.target.value)}
          />
        )}
      </TarjetaContenido>

      {choferId && (rutaEdicion || elegido) && (
        <FlujoArmarRuta
          clientes={clientes}
          rutaEdicion={rutaEdicion}
          fechaInicial={fechaInicial}
          choferId={choferId}
          onConfirmada={onConfirmada}
          onCancelar={onCancelar}
        />
      )}
    </div>
  );
}
