import { type FormEvent, useState } from "react";

import { actualizarPerfil } from "../../api/auth";
import { ErrorFormulario } from "../../api/cliente";
import { useEnvioFormulario } from "../../hooks/useEnvioFormulario";
import { useAuthStore } from "../../store/useAuthStore";
import type { UsuarioPublico } from "../../tipos/auth";
import { Boton } from "../ui/Boton";
import { Campo } from "../ui/Campo";
import { Formulario } from "../ui/Formulario";

interface Props {
  usuario: UsuarioPublico;
  onGuardado: () => void;
  onCancelar: () => void;
}

export function FormularioPerfil({ usuario, onGuardado, onCancelar }: Props) {
  const establecerUsuario = useAuthStore((estado) => estado.establecerUsuario);
  const { error, enviando, enviar } = useEnvioFormulario();
  const [nombre, setNombre] = useState(usuario.nombre_completo);
  const [telefono, setTelefono] = useState(usuario.telefono ?? "");

  function manejarSubmit(evento: FormEvent) {
    evento.preventDefault();
    enviar(async () => {
      if (nombre.trim().length < 2) {
        throw new ErrorFormulario("Ingresá tu nombre completo.");
      }
      // El backend no admite null en el teléfono: solo se envía si hay uno.
      const usuarioActualizado = await actualizarPerfil({
        nombre_completo: nombre.trim(),
        ...(telefono.trim() ? { telefono: telefono.trim() } : {}),
      });
      establecerUsuario(usuarioActualizado);
      onGuardado();
    }, "No se pudieron guardar tus datos.");
  }

  return (
    <Formulario onSubmit={manejarSubmit} error={error} className="flex flex-col">
      <Campo
        etiqueta="Nombre completo"
        required
        value={nombre}
        onChange={(e) => setNombre(e.target.value)}
      />
      <Campo
        etiqueta="Teléfono"
        type="tel"
        placeholder="+54 9 261 555-0100"
        value={telefono}
        onChange={(e) => setTelefono(e.target.value)}
      />
      <p className="mb-3 text-[11.5px] text-texto-mutado">El email no se puede cambiar.</p>
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
