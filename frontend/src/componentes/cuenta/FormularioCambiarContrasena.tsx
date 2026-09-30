import { type FormEvent, useState } from "react";

import { cambiarContrasena } from "../../api/auth";
import { ErrorFormulario } from "../../api/cliente";
import { useEnvioFormulario } from "../../hooks/useEnvioFormulario";
import { Boton } from "../ui/Boton";
import { Campo } from "../ui/Campo";
import { Formulario } from "../ui/Formulario";

interface Props {
  onGuardado: () => void;
  onCancelar: () => void;
}

export function FormularioCambiarContrasena({ onGuardado, onCancelar }: Props) {
  const { error, enviando, enviar } = useEnvioFormulario();
  const [actual, setActual] = useState("");
  const [nueva, setNueva] = useState("");
  const [confirmacion, setConfirmacion] = useState("");

  function manejarSubmit(evento: FormEvent) {
    evento.preventDefault();
    enviar(async () => {
      if (nueva !== confirmacion) {
        throw new ErrorFormulario("Las contraseñas no coinciden.");
      }
      await cambiarContrasena({
        contrasena_actual: actual,
        contrasena_nueva: nueva,
        confirmar_contrasena_nueva: confirmacion,
      });
      onGuardado();
    }, "No se pudo cambiar la contraseña.");
  }

  return (
    <Formulario onSubmit={manejarSubmit} error={error} className="flex flex-col">
      <Campo
        etiqueta="Contraseña actual"
        type="password"
        autoComplete="current-password"
        required
        value={actual}
        onChange={(e) => setActual(e.target.value)}
      />
      <Campo
        etiqueta="Contraseña nueva"
        type="password"
        autoComplete="new-password"
        minLength={8}
        required
        value={nueva}
        onChange={(e) => setNueva(e.target.value)}
      />
      <Campo
        etiqueta="Confirmar contraseña nueva"
        type="password"
        autoComplete="new-password"
        minLength={8}
        required
        value={confirmacion}
        onChange={(e) => setConfirmacion(e.target.value)}
      />
      <div className="flex gap-2.5 [&>*]:flex-1">
        <Boton type="button" variante="secundario" onClick={onCancelar}>
          Cancelar
        </Boton>
        <Boton type="submit" cargando={enviando}>
          Cambiar contraseña
        </Boton>
      </div>
    </Formulario>
  );
}
