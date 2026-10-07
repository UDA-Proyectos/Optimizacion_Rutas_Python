import type { EstadoRuta } from "../tipos/ruta";

export const ETIQUETA_ESTADO_RUTA: Record<EstadoRuta, string> = {
  planificada: "Planificada",
  en_curso: "En curso",
  completada: "Completada",
  cancelada: "Cancelada",
};

/** Clases de la pastilla de estado de una ruta. */
export const CHIP_ESTADO_RUTA: Record<EstadoRuta, string> = {
  planificada: "bg-primario/10 text-[#6428CC]",
  en_curso: "bg-exito-tint text-[#067647]",
  completada: "bg-fondo text-texto-cuerpo",
  cancelada: "bg-peligro-tint text-peligro",
};
