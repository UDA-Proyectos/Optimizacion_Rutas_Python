import { useNavigate } from "react-router-dom";

import { EscritorioChofer } from "../componentes/escritorio/EscritorioChofer";
import { EscritorioEmpresa } from "../componentes/escritorio/EscritorioEmpresa";
import { useAuthStore } from "../store/useAuthStore";

/** Cada rol tiene su escritorio, todos sobre el mismo ShellEscritorio. */
export function Inicio() {
  const navigate = useNavigate();
  const usuario = useAuthStore((estado) => estado.usuario);
  const cerrarSesion = useAuthStore((estado) => estado.cerrarSesion);

  async function manejarLogout() {
    await cerrarSesion();
    navigate("/login");
  }

  if (!usuario) return null;
  if (usuario.rol === "admin") {
    return <EscritorioEmpresa usuario={usuario} onLogout={manejarLogout} />;
  }
  return <EscritorioChofer usuario={usuario} onLogout={manejarLogout} />;
}
