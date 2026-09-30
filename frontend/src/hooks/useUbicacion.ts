import { useEffect, useRef, useState } from "react";

import type { Coordenada } from "../utilidades/googleMaps";

export type EstadoUbicacion = "inactiva" | "buscando" | "activa" | "denegada" | "no_disponible";

/** Posición del dispositivo, solo en el cliente: vive en el estado de React y
 * jamás se envía al backend ni se guarda. No se pide nada al montar — el
 * permiso del navegador aparece únicamente cuando el chofer toca `activar()`. */
export function useUbicacion() {
  const [estado, setEstado] = useState<EstadoUbicacion>("inactiva");
  const [ubicacion, setUbicacion] = useState<Coordenada | null>(null);
  const idSeguimiento = useRef<number | null>(null);

  function detener() {
    if (idSeguimiento.current != null) {
      navigator.geolocation.clearWatch(idSeguimiento.current);
      idSeguimiento.current = null;
    }
  }

  function activar() {
    if (!("geolocation" in navigator)) {
      setEstado("no_disponible");
      return;
    }
    detener();
    setEstado("buscando");
    idSeguimiento.current = navigator.geolocation.watchPosition(
      (posicion) => {
        setUbicacion({
          latitud: posicion.coords.latitude,
          longitud: posicion.coords.longitude,
        });
        setEstado("activa");
      },
      (error) => {
        if (error.code === error.PERMISSION_DENIED) {
          detener();
          setUbicacion(null);
          setEstado("denegada");
        }
        // Otros errores (sin señal, timeout): sigue buscando; la navegación
        // usa mientras tanto el origen del tramo.
      },
      { enableHighAccuracy: true, maximumAge: 10_000, timeout: 20_000 },
    );
  }

  function desactivar() {
    detener();
    setUbicacion(null);
    setEstado("inactiva");
  }

  useEffect(() => detener, []);

  return { estado, ubicacion, activar, desactivar };
}

export type EstadoGps = ReturnType<typeof useUbicacion>;
