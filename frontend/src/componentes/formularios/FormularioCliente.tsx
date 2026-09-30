import { type FormEvent, useState } from "react";

import { actualizarCliente, crearCliente } from "../../api/clientes";
import { ErrorFormulario } from "../../api/cliente";
import { useEnvioFormulario } from "../../hooks/useEnvioFormulario";
import type { ClientePublico } from "../../tipos/cliente";
import { hhMmAMinutos, minutosAHhMm } from "../../utilidades/horario";
import { SelectorUbicacion } from "../mapa/SelectorUbicacion";
import { Boton } from "../ui/Boton";
import { Campo } from "../ui/Campo";
import { Formulario } from "../ui/Formulario";
import { TextoEyebrow } from "../ui/TextoEyebrow";

interface Props {
  cliente: ClientePublico | null;
  onGuardado: () => void;
  onCancelar: () => void;
}

export function FormularioCliente({ cliente, onGuardado, onCancelar }: Props) {
  const { error, enviando, enviar } = useEnvioFormulario();
  const [nombre, setNombre] = useState(cliente?.nombre ?? "");
  const [direccion, setDireccion] = useState(cliente?.direccion ?? "");
  const [telefono, setTelefono] = useState(cliente?.telefono ?? "");
  const [latitud, setLatitud] = useState<number | null>(cliente?.latitud ?? null);
  const [longitud, setLongitud] = useState<number | null>(cliente?.longitud ?? null);
  const [cargaHabitual, setCargaHabitual] = useState(
    cliente?.demanda_carga_default != null ? String(cliente.demanda_carga_default) : "",
  );
  const [tiempoServicio, setTiempoServicio] = useState(
    String(cliente?.tiempo_servicio_default ?? 0),
  );
  const [ventanaDesde, setVentanaDesde] = useState(
    cliente?.ventana_inicio_default != null ? minutosAHhMm(cliente.ventana_inicio_default) : "",
  );
  const [ventanaHasta, setVentanaHasta] = useState(
    cliente?.ventana_fin_default != null ? minutosAHhMm(cliente.ventana_fin_default) : "",
  );

  function manejarSubmit(evento: FormEvent) {
    evento.preventDefault();
    enviar(async () => {
      if (latitud == null || longitud == null) {
        throw new ErrorFormulario("Marcá la ubicación en el mapa antes de guardar.");
      }
      if (direccion.trim().length < 3) {
        throw new ErrorFormulario("Ingresá o buscá una dirección antes de guardar.");
      }
      const servicio = Number(tiempoServicio || 0);
      if (!Number.isInteger(servicio) || servicio < 0 || servicio > 240) {
        throw new ErrorFormulario("El tiempo de servicio va de 0 a 240 minutos.");
      }
      const carga = cargaHabitual === "" ? null : Number(cargaHabitual);
      if (carga != null && (!Number.isInteger(carga) || carga < 0)) {
        throw new ErrorFormulario("La carga habitual tiene que ser un número entero de kg.");
      }
      const desde = ventanaDesde ? hhMmAMinutos(ventanaDesde) : null;
      const hasta = ventanaHasta ? hhMmAMinutos(ventanaHasta) : null;
      if ((desde == null) !== (hasta == null)) {
        throw new ErrorFormulario("Completá el horario habitual: desde y hasta.");
      }
      if (desde != null && hasta != null && hasta <= desde) {
        throw new ErrorFormulario("El horario habitual tiene que terminar después de empezar.");
      }
      const datos = {
        nombre,
        direccion,
        telefono: telefono || null,
        latitud,
        longitud,
        demanda_carga_default: carga,
        tiempo_servicio_default: servicio,
        ventana_inicio_default: desde,
        ventana_fin_default: hasta,
      };
      if (cliente) {
        await actualizarCliente(cliente.id, datos);
      } else {
        await crearCliente(datos);
      }
      onGuardado();
    }, "No se pudo guardar el lugar.");
  }

  return (
    <Formulario onSubmit={manejarSubmit} error={error} className="flex flex-col">
      <Campo
        etiqueta="Nombre"
        placeholder="Ej: Kiosco Don José"
        required
        value={nombre}
        onChange={(e) => setNombre(e.target.value)}
      />
      <Campo
        etiqueta="Teléfono (opcional)"
        type="tel"
        placeholder="+54 9 261 555-0100"
        value={telefono}
        onChange={(e) => setTelefono(e.target.value)}
      />
      <SelectorUbicacion
        latitud={latitud}
        longitud={longitud}
        onCambiar={(lat, lon) => {
          setLatitud(lat);
          setLongitud(lon);
        }}
        direccion={direccion}
        onCambiarDireccion={setDireccion}
      />
      <TextoEyebrow>Datos habituales (opcional)</TextoEyebrow>
      <p className="mb-3 text-[12px] text-texto-mutado">
        Se precargan al armar una ruta; los podés cambiar cada día sin tocar el lugar.
      </p>
      <div className="flex gap-2.5">
        <Campo
          etiqueta="Carga habitual (kg)"
          type="number"
          min={0}
          inputMode="numeric"
          value={cargaHabitual}
          onChange={(e) => setCargaHabitual(e.target.value)}
        />
        <Campo
          etiqueta="Servicio (min)"
          type="number"
          min={0}
          max={240}
          inputMode="numeric"
          value={tiempoServicio}
          onChange={(e) => setTiempoServicio(e.target.value)}
        />
      </div>
      <div className="flex gap-2.5">
        <Campo
          etiqueta="Atiende desde"
          type="time"
          value={ventanaDesde}
          onChange={(e) => setVentanaDesde(e.target.value)}
        />
        <Campo
          etiqueta="Hasta"
          type="time"
          value={ventanaHasta}
          onChange={(e) => setVentanaHasta(e.target.value)}
        />
      </div>
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
