import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { CompletarRegistroGoogle } from "./paginas/CompletarRegistroGoogle";
import { Inicio } from "./paginas/Inicio";
import { Login } from "./paginas/Login";
import { Registro } from "./paginas/Registro";
import { useAuthStore } from "./store/useAuthStore";

function RutaProtegida({ children }: { children: ReactNode }) {
  const estaAutenticado = useAuthStore((estado) => estado.estaAutenticado);
  return estaAutenticado ? <>{children}</> : <Navigate to="/login" replace />;
}

function RutaPublica({ children }: { children: ReactNode }) {
  const estaAutenticado = useAuthStore((estado) => estado.estaAutenticado);
  return estaAutenticado ? <Navigate to="/" replace /> : <>{children}</>;
}

export function AppRouter() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <RutaProtegida>
            <Inicio />
          </RutaProtegida>
        }
      />
      <Route
        path="/login"
        element={
          <RutaPublica>
            <Login />
          </RutaPublica>
        }
      />
      <Route
        path="/registro"
        element={
          <RutaPublica>
            <Registro />
          </RutaPublica>
        }
      />
      <Route
        path="/registro/google"
        element={
          <RutaPublica>
            <CompletarRegistroGoogle />
          </RutaPublica>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
