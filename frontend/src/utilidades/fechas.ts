/** Fechas como "YYYY-MM-DD" del calendario *local* del chofer — el mismo formato
 * que usa la API. Se evita `toISOString()` a propósito: convierte a UTC y de
 * noche en Argentina daría el día siguiente. */

function aIso(fecha: Date): string {
  const mes = String(fecha.getMonth() + 1).padStart(2, "0");
  const dia = String(fecha.getDate()).padStart(2, "0");
  return `${fecha.getFullYear()}-${mes}-${dia}`;
}

function desdeIso(iso: string): Date {
  const [anio, mes, dia] = iso.split("-").map(Number);
  return new Date(anio, mes - 1, dia);
}

export function hoyLocal(): string {
  return aIso(new Date());
}

export function sumarDias(iso: string, dias: number): string {
  const fecha = desdeIso(iso);
  fecha.setDate(fecha.getDate() + dias);
  return aIso(fecha);
}

/** "Hoy", "Mañana", "Ayer" o "lun 5 oct". */
export function etiquetaDia(iso: string): string {
  const hoy = hoyLocal();
  if (iso === hoy) return "Hoy";
  if (iso === sumarDias(hoy, 1)) return "Mañana";
  if (iso === sumarDias(hoy, -1)) return "Ayer";
  return desdeIso(iso).toLocaleDateString("es-AR", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}

/** "lunes 5 de octubre". */
export function fechaLarga(iso: string): string {
  return desdeIso(iso).toLocaleDateString("es-AR", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}
