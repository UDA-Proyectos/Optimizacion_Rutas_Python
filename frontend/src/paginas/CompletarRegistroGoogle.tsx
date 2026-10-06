import { Link } from "react-router-dom";

import { FormularioRegistroGoogle } from "../componentes/formularios/FormularioRegistroGoogle";
import { PaginaAuth, claseEnlacePie } from "../componentes/ui/PaginaAuth";

export function CompletarRegistroGoogle() {
  return (
    <PaginaAuth
      titulo="Completá tu cuenta"
      subtitulo="Entraste con Google. Solo faltan los datos de tu vehículo."
      pie={
        <>
          ¿No sos vos?{" "}
          <Link to="/login" className={claseEnlacePie}>
            Volver al inicio de sesión
          </Link>
        </>
      }
    >
      <FormularioRegistroGoogle />
    </PaginaAuth>
  );
}
