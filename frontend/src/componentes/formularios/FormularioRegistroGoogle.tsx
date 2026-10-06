import { type FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { completarRegistroGoogle, obtenerRegistroGooglePendiente } from "../../api/auth";
import { ErrorFormulario } from "../../api/cliente";
import { useEnvioFormulario } from "../../hooks/useEnvioFormulario";
import { useAuthStore } from "../../store/useAuthStore";
import type { TipoVehiculo } from "../../tipos/auth";
import { Boton } from "../ui/Boton";
import { Campo } from "../ui/Campo";
import { Formulario } from "../ui/Formulario";
import { CamposVehiculo } from "./CamposVehiculo";
import { VALORES_VEHICULO_INICIALES, capacidadCargaValidaKg } from "./datosRegistro";

const RUTA_REGISTRO_VENCIDO = "/login?error_google=registro_vencido";

export function FormularioRegistroGoogle() {
  const navigate = useNavigate();
  const establecerUsuario = useAuthStore((estado) => estado.establecerUsuario);
  const { error, enviando, enviar } = useEnvioFormulario();

  const [email, setEmail] = useState<string | null>(null);
  const [nombreCompleto, setNombreCompleto] = useState("");
  const [vehiculo, setVehiculo] = useState(VALORES_VEHICULO_INICIALES);

  useEffect(() => {
    obtenerRegistroGooglePendiente()
      .then((pendiente) => {
        setEmail(pendiente.email);
        setNombreCompleto(pendiente.nombre_completo);
      })
      // Sin registro pendiente (vencido o se entró directo a la URL) hay que empezar de nuevo.
      .catch(() => navigate(RUTA_REGISTRO_VENCIDO, { replace: true }));
  }, [navigate]);

  function manejarSubmit(evento: FormEvent) {
    evento.preventDefault();
    enviar(async () => {
      try {
        const usuario = await completarRegistroGoogle({
          nombre_completo: nombreCompleto,
          telefono: vehiculo.telefono,
          tipo_vehiculo: vehiculo.tipoVehiculo as TipoVehiculo,
          patente: vehiculo.patente,
          capacidad_carga_kg: capacidadCargaValidaKg(vehiculo),
        });
        establecerUsuario(usuario);
        navigate("/");
      } catch (e) {
        if (e instanceof ErrorFormulario && e.estado === 401) {
          navigate(RUTA_REGISTRO_VENCIDO, { replace: true });
          return;
        }
        throw e;
      }
    }, "No se pudo completar el registro.");
  }

  if (email === null) {
    return <p className="text-center text-[13px] text-texto-mutado">Cargando…</p>;
  }

  return (
    <Formulario onSubmit={manejarSubmit} error={error}>
      <Campo etiqueta="Email" type="email" value={email} readOnly disabled />
      <Campo
        etiqueta="Nombre completo"
        type="text"
        required
        value={nombreCompleto}
        onChange={(e) => setNombreCompleto(e.target.value)}
      />
      <CamposVehiculo
        valores={vehiculo}
        onCambiar={(campo, valor) => setVehiculo((v) => ({ ...v, [campo]: valor }))}
      />
      <Boton type="submit" cargando={enviando}>
        Crear cuenta
      </Boton>
    </Formulario>
  );
}
