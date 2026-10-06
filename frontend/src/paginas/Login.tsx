import { Link, useSearchParams } from "react-router-dom";

import { BotonGoogle } from "../componentes/formularios/BotonGoogle";
import { FormularioLogin } from "../componentes/formularios/FormularioLogin";
import { BannerError } from "../componentes/ui/Formulario";
import { PaginaAuth, claseEnlacePie } from "../componentes/ui/PaginaAuth";

/** Códigos que manda la API en `?error_google=` al volver de Google (api/routes_google.py). */
const MENSAJES_ERROR_GOOGLE: Record<string, string> = {
  no_disponible: "El ingreso con Google no está disponible en este momento.",
  cancelado: "Cancelaste el ingreso con Google.",
  estado_invalido: "El ingreso con Google se interrumpió. Probá de nuevo.",
  fallo_google: "No pudimos comunicarnos con Google. Probá de nuevo en un rato.",
  email_no_verificado: "Tu email de Google no está verificado.",
  cuenta_inactiva: "Cuenta inactiva.",
  cuenta_vinculada_otra: "Ese email ya está vinculado a otra cuenta de Google.",
  registro_vencido: "Pasó demasiado tiempo. Volvé a entrar con Google para crear tu cuenta.",
};

export function Login() {
  const [parametros] = useSearchParams();
  const codigoError = parametros.get("error_google");
  const errorGoogle = codigoError
    ? (MENSAJES_ERROR_GOOGLE[codigoError] ?? MENSAJES_ERROR_GOOGLE.fallo_google)
    : null;

  return (
    <PaginaAuth
      titulo="Iniciar sesión"
      subtitulo="Entrá con tu email y contraseña."
      pie={
        <>
          ¿No tenés cuenta?{" "}
          <Link to="/registro" className={claseEnlacePie}>
            Registrate
          </Link>
        </>
      }
    >
      {errorGoogle && <BannerError className="mb-4">{errorGoogle}</BannerError>}
      <FormularioLogin />
      <BotonGoogle />
    </PaginaAuth>
  );
}
