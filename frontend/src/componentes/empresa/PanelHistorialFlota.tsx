import { useEffect, useState } from "react";

import { listarChoferes } from "../../api/empresa";
import type { ChoferDeEmpresa } from "../../tipos/empresa";
import { hoyLocal } from "../../utilidades/fechas";
import { PanelHistorial } from "../historial/PanelHistorial";
import { CampoSelect } from "../ui/CampoSelect";

/** Historial de toda la flota (admin), filtrable por chofer. */
export function PanelHistorialFlota() {
  const [choferes, setChoferes] = useState<ChoferDeEmpresa[]>([]);
  const [choferId, setChoferId] = useState("");

  useEffect(() => {
    listarChoferes(hoyLocal())
      .then(setChoferes)
      .catch(() => {});
  }, []);

  return (
    <div className="flex flex-col gap-4">
      <div className="mx-auto w-full max-w-[900px] sm:max-w-[340px] sm:self-start lg:mx-0">
        <CampoSelect
          etiqueta="Chofer"
          opciones={[
            { valor: "", etiqueta: "Todos los choferes" },
            ...choferes.map((c) => ({ valor: c.id, etiqueta: c.nombre_completo })),
          ]}
          value={choferId}
          onChange={(e) => setChoferId(e.target.value)}
        />
      </div>
      {/* PanelHistorial no reacciona a cambios de `flota`: se remonta al cambiar de chofer. */}
      <PanelHistorial
        key={choferId || "todos"}
        clientes={[]}
        flota={{ choferId: choferId || undefined }}
      />
    </div>
  );
}
