function formatearHora(marca: number): string {
  return new Date(marca).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

/** Aviso de que no hay conexión y lo que se está viendo es la última copia
 * guardada de la ruta (solo lectura). Desaparece solo al volver la señal. */
export function BannerConexion({ copiaGuardadaEn }: { copiaGuardadaEn: number | null }) {
  return (
    <div
      role="status"
      className="flex shrink-0 items-center gap-2 border-b border-peligro-borde bg-peligro-tint px-4 py-2 text-[12px] text-peligro lg:px-6"
    >
      <span className="h-2 w-2 shrink-0 rounded-full bg-peligro" />
      <span className="font-semibold">Sin conexión.</span>
      <span>
        {copiaGuardadaEn != null
          ? `Estás viendo tu ruta guardada a las ${formatearHora(copiaGuardadaEn)}; puede estar desactualizada.`
          : "Las acciones se habilitan cuando vuelva la señal."}
      </span>
    </div>
  );
}
