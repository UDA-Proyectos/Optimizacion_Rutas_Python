import type { MotivoFalloParada, TipoIncidencia } from "../tipos/ruta";

export const ETIQUETA_MOTIVO: Record<TipoIncidencia, string> = {
  cliente_ausente: "Cliente ausente",
  rechazo_entrega: "Rechazó la entrega",
  direccion_incorrecta: "Dirección incorrecta",
  mercaderia_danada: "Mercadería dañada",
  problema_vehiculo: "Problema del vehículo",
  otro: "Otro motivo",
};

export const OPCIONES_MOTIVO_FALLO: MotivoFalloParada[] = [
  "cliente_ausente",
  "rechazo_entrega",
  "direccion_incorrecta",
  "mercaderia_danada",
  "otro",
];
