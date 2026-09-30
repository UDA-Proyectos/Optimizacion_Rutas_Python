import { type FormEvent, useState } from "react";

import { actualizarVehiculo } from "../../api/auth";
import { ErrorFormulario } from "../../api/cliente";
import { useEnvioFormulario } from "../../hooks/useEnvioFormulario";
import { useAuthStore } from "../../store/useAuthStore";
import type { TipoVehiculo, VehiculoPublico } from "../../tipos/auth";
import { OPCIONES_TIPO_VEHICULO } from "../formularios/opcionesVehiculo";
import { Boton } from "../ui/Boton";
import { Campo } from "../ui/Campo";
import { CampoSelect } from "../ui/CampoSelect";
import { Formulario } from "../ui/Formulario";

interface Props {
  vehiculo: VehiculoPublico;
  onGuardado: () => void;
  onCancelar: () => void;
}

export function FormularioVehiculo({ vehiculo, onGuardado, onCancelar }: Props) {
  const establecerUsuario = useAuthStore((estado) => estado.establecerUsuario);
  const { error, enviando, enviar } = useEnvioFormulario();
  const [tipo, setTipo] = useState<TipoVehiculo>(vehiculo.tipo_vehiculo);
  const [patente, setPatente] = useState(vehiculo.patente);
  const [capacidad, setCapacidad] = useState(String(vehiculo.capacidad_carga_kg));

  function manejarSubmit(evento: FormEvent) {
    evento.preventDefault();
    enviar(async () => {
      const capacidadKg = Number(capacidad);
      if (!Number.isInteger(capacidadKg) || capacidadKg <= 0) {
        throw new ErrorFormulario("La capacidad de carga tiene que ser un número entero mayor a 0.");
      }
      if (patente.trim().length < 4) {
        throw new ErrorFormulario("Ingresá la patente del vehículo.");
      }
      const usuario = await actualizarVehiculo({
        tipo_vehiculo: tipo,
        patente: patente.trim(),
        capacidad_carga_kg: capacidadKg,
      });
      establecerUsuario(usuario);
      onGuardado();
    }, "No se pudo guardar el vehículo.");
  }

  return (
    <Formulario onSubmit={manejarSubmit} error={error} className="flex flex-col">
      <CampoSelect
        etiqueta="Tipo de vehículo"
        opciones={OPCIONES_TIPO_VEHICULO}
        value={tipo}
        onChange={(e) => setTipo(e.target.value as TipoVehiculo)}
      />
      <Campo
        etiqueta="Patente"
        required
        value={patente}
        onChange={(e) => setPatente(e.target.value.toUpperCase())}
      />
      <Campo
        etiqueta="Capacidad de carga (kg)"
        type="number"
        min={1}
        required
        value={capacidad}
        onChange={(e) => setCapacidad(e.target.value)}
      />
      <div className="flex gap-2.5 [&>*]:flex-1">
        <Boton type="button" variante="secundario" onClick={onCancelar}>
          Cancelar
        </Boton>
        <Boton type="submit" cargando={enviando}>
          Guardar
        </Boton>
      </div>
    </Formulario>
  );
}
