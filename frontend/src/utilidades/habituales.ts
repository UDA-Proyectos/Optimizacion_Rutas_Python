import type { ClientePublico } from "../tipos/cliente";
import { minutosAHhMm } from "./horario";

/** Una línea con los datos habituales de un lugar ("20 kg · servicio 10 min ·
 * 09:00–12:00"), o null si no tiene ninguno cargado. */
export function resumenHabituales(cliente: ClientePublico): string | null {
  const partes: string[] = [];
  if (cliente.demanda_carga_default != null) {
    partes.push(`${cliente.demanda_carga_default} kg`);
  }
  if (cliente.tiempo_servicio_default > 0) {
    partes.push(`servicio ${cliente.tiempo_servicio_default} min`);
  }
  if (cliente.ventana_inicio_default != null && cliente.ventana_fin_default != null) {
    partes.push(
      `${minutosAHhMm(cliente.ventana_inicio_default)}–${minutosAHhMm(cliente.ventana_fin_default)}`,
    );
  }
  return partes.length > 0 ? partes.join(" · ") : null;
}
