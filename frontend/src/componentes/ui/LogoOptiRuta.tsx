import { useId } from "react";

/** Mismo dibujo que public/favicon.svg y los íconos de la PWA. */
export function LogoOptiRuta({ tamanio = 28 }: { tamanio?: number }) {
  // El gradiente necesita un id único: el logo puede estar dos veces en pantalla (sidebar y drawer).
  const idGradiente = useId();

  return (
    <svg
      width={tamanio}
      height={tamanio}
      viewBox="0 0 64 64"
      aria-hidden="true"
      className="shrink-0 rounded-[7px] ring-1 ring-white/25"
    >
      <defs>
        <linearGradient id={idGradiente} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#7c3aed" />
          <stop offset="1" stopColor="#4c1d95" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="15" fill={`url(#${idGradiente})`} />
      <polyline
        points="17,45 28,31 38,38 47,19"
        fill="none"
        stroke="#fff"
        strokeWidth="5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="17" cy="45" r="5.5" fill="#fff" />
      <circle cx="47" cy="19" r="7" fill="#22c55e" stroke="#fff" strokeWidth="3" />
    </svg>
  );
}
