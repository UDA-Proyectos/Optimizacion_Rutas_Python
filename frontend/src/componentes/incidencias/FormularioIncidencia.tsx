import { type FormEvent, useState } from "react";

import { reportarIncidencia } from "../../api/incidencias";
import { useEnvioFormulario } from "../../hooks/useEnvioFormulario";
import type { ParadaRutaPublica, TipoIncidencia } from "../../tipos/ruta";
import { ETIQUETA_MOTIVO } from "../../utilidades/motivosFallo";
import { Boton } from "../ui/Boton";
import { Campo } from "../ui/Campo";
import { CampoSelect } from "../ui/CampoSelect";
import { Formulario } from "../ui/Formulario";

const OPCIONES_TIPO = (Object.keys(ETIQUETA_MOTIVO) as TipoIncidencia[]).map((tipo) => ({
  valor: tipo,
  etiqueta: ETIQUETA_MOTIVO[tipo],
}));

interface Props {
  paradas: ParadaRutaPublica[];
  onGuardada: () => void;
  onCancelar: () => void;
}

export function FormularioIncidencia({ paradas, onGuardada, onCancelar }: Props) {
  const { error, enviando, enviar } = useEnvioFormulario();
  const [tipo, setTipo] = useState<TipoIncidencia>("problema_vehiculo");
  const [paradaId, setParadaId] = useState("");
  const [descripcion, setDescripcion] = useState("");

  const opcionesParada = [
    { valor: "", etiqueta: "Toda la ruta" },
    ...paradas.map((parada) => ({ valor: parada.id, etiqueta: parada.nombre_snapshot })),
  ];

  function manejarSubmit(evento: FormEvent) {
    evento.preventDefault();
    enviar(async () => {
      await reportarIncidencia({
        tipo,
        descripcion: descripcion.trim() || null,
        parada_id: paradaId || null,
      });
      onGuardada();
    }, "No se pudo reportar la incidencia.");
  }

  return (
    <Formulario onSubmit={manejarSubmit} error={error} className="flex flex-col">
      <CampoSelect
        etiqueta="Tipo de incidencia"
        opciones={OPCIONES_TIPO}
        value={tipo}
        onChange={(e) => setTipo(e.target.value as TipoIncidencia)}
      />
      <CampoSelect
        etiqueta="¿Sobre qué parada?"
        opciones={opcionesParada}
        value={paradaId}
        onChange={(e) => setParadaId(e.target.value)}
      />
      <Campo
        etiqueta="Detalle (opcional)"
        placeholder="Contanos qué pasó"
        maxLength={500}
        value={descripcion}
        onChange={(e) => setDescripcion(e.target.value)}
      />
      <div className="flex gap-2.5 [&>*]:flex-1">
        <Boton type="button" variante="secundario" onClick={onCancelar}>
          Cancelar
        </Boton>
        <Boton type="submit" cargando={enviando}>
          Reportar
        </Boton>
      </div>
    </Formulario>
  );
}
