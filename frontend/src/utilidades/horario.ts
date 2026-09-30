/** Minuto del día (0-1440, ej. 480 = 8:00) ↔ "HH:MM" de <input type="time">
 * — misma convención que ya usa el backend (ver CLAUDE.md §5). */
export function minutosAHhMm(minutos: number): string {
  const h = Math.floor(minutos / 60)
    .toString()
    .padStart(2, "0");
  const m = Math.floor(minutos % 60)
    .toString()
    .padStart(2, "0");
  return `${h}:${m}`;
}

/** 95 -> "1 h 35 min", 40 -> "40 min". */
export function formatearDuracion(minutos: number): string {
  const horas = Math.floor(minutos / 60);
  const resto = minutos % 60;
  if (horas === 0) {
    return `${resto} min`;
  }
  return resto === 0 ? `${horas} h` : `${horas} h ${resto} min`;
}

export function hhMmAMinutos(valor: string): number | null {
  const coincidencia = /^(\d{1,2}):(\d{2})$/.exec(valor);
  if (!coincidencia) {
    return null;
  }
  const horas = Number(coincidencia[1]);
  const minutos = Number(coincidencia[2]);
  return horas * 60 + minutos;
}
