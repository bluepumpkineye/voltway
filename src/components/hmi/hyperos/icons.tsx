import React from 'react';

/* HyperOS-style line icons: 1.7 stroke, round caps, drawn on a 24 grid. */

type P = { size?: number; className?: string; style?: React.CSSProperties };
const L = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.7, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };

function I({ size = 22, className, style, children }: P & { children: React.ReactNode }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} style={style} aria-hidden="true">
      {children}
    </svg>
  );
}

export const Home = (p: P) => (
  <I {...p}><g {...L}><path d="M4 10.2 12 4l8 6.2" /><path d="M6.2 9v10.4h11.6V9" /></g></I>
);
export const ChevronL = (p: P) => (
  <I {...p}><path {...L} d="m14.5 6-6 6 6 6" /></I>
);
export const ChevronR = (p: P) => (
  <I {...p}><path {...L} d="m9.5 6 6 6-6 6" /></I>
);
export const ChevronDown = (p: P) => (
  <I {...p}><path {...L} d="m6 9.5 6 6 6-6" /></I>
);
export const Volume = (p: P) => (
  <I {...p}><g {...L}><path d="M4.5 9.5h3.2L12 6v12l-4.3-3.5H4.5z" /><path d="M15.5 9.2a4 4 0 0 1 0 5.6M18 6.8a7.4 7.4 0 0 1 0 10.4" /></g></I>
);
export const Play = (p: P) => (
  <I {...p}><path fill="currentColor" d="M8 5.6v12.8L18.6 12Z" /></I>
);
export const Pause = (p: P) => (
  <I {...p}><path fill="currentColor" d="M7.5 5.5h3v13h-3zM13.5 5.5h3v13h-3z" /></I>
);
export const Next = (p: P) => (
  <I {...p}><path fill="currentColor" d="M6 6v12l8.6-6Z M16 6h2.4v12H16z" /></I>
);
export const Prev = (p: P) => (
  <I {...p}><path fill="currentColor" d="M18 6v12l-8.6-6Z M8 6H5.6v12H8z" /></I>
);
export const Message = (p: P) => (
  <I {...p}><path {...L} d="M5 6.5h14v9.2H10l-4 3v-3H5z" /></I>
);
export const Dashcam = (p: P) => (
  <I {...p}><g {...L}><rect x="3.5" y="7" width="12" height="10" rx="2" /><path d="m15.5 11 5-3v8l-5-3" /></g></I>
);
export const Link = (p: P) => (
  <I {...p}><g {...L}><path d="M10 14a3.5 3.5 0 0 0 5 0l3-3a3.5 3.5 0 0 0-5-5l-1 1" /><path d="M14 10a3.5 3.5 0 0 0-5 0l-3 3a3.5 3.5 0 0 0 5 5l1-1" /></g></I>
);
export const Signal = (p: P) => (
  <I {...p}>
    <g fill="currentColor">
      <rect x="4" y="15" width="2.6" height="4" rx="0.8" />
      <rect x="8.4" y="12" width="2.6" height="7" rx="0.8" />
      <rect x="12.8" y="9" width="2.6" height="10" rx="0.8" />
      <rect x="17.2" y="5.5" width="2.6" height="13.5" rx="0.8" />
    </g>
  </I>
);
/** The car-status glyph beside the range pill. */
export const CarGlyph = (p: P) => (
  <I {...p}><g {...L}><path d="M5 15.5v-3l1.6-4.2A2 2 0 0 1 8.5 7h7a2 2 0 0 1 1.9 1.3l1.6 4.2v3" /><path d="M4 15.5h16v2.2H4z" /><circle cx="8" cy="13" r=".6" fill="currentColor" /><circle cx="16" cy="13" r=".6" fill="currentColor" /></g></I>
);
/** Low-beam tell-tale (green on HyperOS when the lamps are on). */
export const LowBeam = (p: P) => (
  <I {...p}><g {...L}><path d="M13 6.5c3.2 0 5.5 2.4 5.5 5.5s-2.3 5.5-5.5 5.5Z" /><path d="M9.5 8 4.5 9.5M9.5 11 4.5 12.5M9.5 14 4.5 15.5" /></g></I>
);
export const Fan = (p: P) => (
  <I {...p}><g {...L}><circle cx="12" cy="12" r="1.6" /><path d="M12 10.4C12 6 15.8 5 16.6 7.6c.6 2-2.4 3-4.6 2.8M13.6 12c4.4 0 5.4 3.8 2.8 4.6-2 .6-3-2.4-2.8-4.6M12 13.6c0 4.4-3.8 5.4-4.6 2.8-.6-2 2.4-3 4.6-2.8M10.4 12C6 12 5 8.2 7.6 7.4c2-.6 3 2.4 2.8 4.6" /></g></I>
);
export const SeatHeat = (p: P) => (
  <I {...p}><g {...L}><path d="M8 4.5c-1 1.6 1 2.4 0 4M11.5 4.5c-1 1.6 1 2.4 0 4M15 4.5c-1 1.6 1 2.4 0 4" /><path d="M6 11.5h12M7 11.5 8 19h8l1-7.5" /></g></I>
);
export const Defrost = (p: P) => (
  <I {...p}><g {...L}><path d="M4.5 16.5c2.5-6 12.5-6 15 0" /><path d="M8.5 13.5c-1 1.6 1 2.4 0 4M12 13c-1 1.6 1 2.4 0 4M15.5 13.5c-1 1.6 1 2.4 0 4" /></g></I>
);
export const Recirc = (p: P) => (
  <I {...p}><g {...L}><path d="M5 15.5c1.5 2.6 4 4 7 4a7.5 7.5 0 1 0-6.5-11.2" /><path d="M5 4.8v4h4" /></g></I>
);
export const Close = (p: P) => (
  <I {...p}><path {...L} d="m6.5 6.5 11 11M17.5 6.5l-11 11" /></I>
);
export const Info = (p: P) => (
  <I {...p}><g {...L}><circle cx="12" cy="12" r="8" /><path d="M12 11v5M12 8v.2" /></g></I>
);
export const Rocket = (p: P) => (
  <I {...p}><g {...L}><path d="M9.5 14.5c-2-.4-3-2-3-2l6.5-7c3-3 6.5-2.5 6.5-2.5s.5 3.5-2.5 6.5l-7 6.5s-1.6-1-2-3" /><path d="m7 17-2.5 2.5M6 13.5 4.5 15M10.5 18 9 19.5" /></g></I>
);
export const Leaf = (p: P) => (
  <I {...p}><g {...L}><path d="M5 19c0-8 5-13 14-14 0 9-5 14-13 14" /><path d="M5 19c3-4.5 6-7 9-8.5" /></g></I>
);
export const Flag = (p: P) => (
  <I {...p}><g {...L}><path d="M6 20V4.5" /><path d="M6 5h12l-2.5 4L18 13H6" /></g></I>
);
export const Boost = (p: P) => (
  <I {...p}><path {...L} d="M13 3.5 5.5 13.5h6L10.5 20.5 18.5 10h-6Z" /></I>
);
export const Pin = (p: P) => (
  <I {...p}><g {...L}><path d="M12 20.5s6.5-5.6 6.5-10.5a6.5 6.5 0 1 0-13 0c0 4.9 6.5 10.5 6.5 10.5Z" /><circle cx="12" cy="10" r="2.3" /></g></I>
);
export const Heart = (p: P) => (
  <I {...p}><path {...L} d="M12 19s-7-4.4-7-9.2A3.8 3.8 0 0 1 12 8a3.8 3.8 0 0 1 7 1.8C19 14.6 12 19 12 19Z" /></I>
);
export const ListIcon = (p: P) => (
  <I {...p}><path {...L} d="M5 7h14M5 12h14M5 17h9" /></I>
);
export const Repeat = (p: P) => (
  <I {...p}><g {...L}><path d="M5 11V9.5A2.5 2.5 0 0 1 7.5 7H18l-2.5-2.5M19 13v1.5a2.5 2.5 0 0 1-2.5 2.5H6l2.5 2.5" /></g></I>
);
export const Lyrics = (p: P) => (
  <I {...p}><g {...L}><path d="M5 6.5h14M5 11h9M5 15.5h6" /><circle cx="17" cy="16.5" r="2" /><path d="M19 16.5V10" /></g></I>
);
export const Exit = (p: P) => (
  <I {...p}><g {...L}><path d="M10 5.5H6.5v13H10" /><path d="M14 8.5 17.5 12 14 15.5M17.5 12H9" /></g></I>
);

/* ------------------------------------------------ Settings side menu */
export const MenuVehicle = (p: P) => (
  <I {...p}><g {...L}><rect x="4" y="8" width="16" height="8" rx="4" /><circle cx="8" cy="12" r="2.2" /></g></I>
);
export const MenuLights = (p: P) => (
  <I {...p}><g {...L}><circle cx="12" cy="12" r="3.5" /><path d="M12 3.5V5.5M12 18.5v2M3.5 12h2M18.5 12h2M6 6l1.4 1.4M16.6 16.6 18 18M6 18l1.4-1.4M16.6 7.4 18 6" /></g></I>
);
export const MenuDoors = (p: P) => (
  <I {...p}><g {...L}><path d="M5.5 18.5V9.5l4-4H18.5v13Z" /><path d="M5.5 11.5h13M14.5 14.5h2" /></g></I>
);
export const MenuDriving = (p: P) => (
  <I {...p}><g {...L}><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="2" /><path d="M4.5 10.5c4.5-1.5 10.5-1.5 15 0M12 14v5.8" /></g></I>
);
export const MenuAssist = (p: P) => (
  <I {...p}><g {...L}><path d="M12 3.5 5 6.5v5c0 4.3 3 7.4 7 8.8 4-1.4 7-4.5 7-8.8v-5Z" /><path d="m9.5 15 2.5-6.5 2.5 6.5M10.3 13h3.4" /></g></I>
);
export const MenuCharging = (p: P) => (
  <I {...p}><g {...L}><rect x="6" y="4.5" width="9" height="15" rx="2" /><path d="M15 9h2.5a1.5 1.5 0 0 1 1.5 1.5V16M11 8.5 9 12h3l-2 3.5" /></g></I>
);
export const MenuConnection = (p: P) => (
  <I {...p}><g {...L}><path d="M4.5 9.5a11 11 0 0 1 15 0M7.2 12.4a7 7 0 0 1 9.6 0M9.8 15.2a3 3 0 0 1 4.4 0" /><circle cx="12" cy="18" r=".6" fill="currentColor" /></g></I>
);
export const MenuDisplay = (p: P) => (
  <I {...p}><g {...L}><rect x="3.5" y="5" width="17" height="11" rx="2" /><path d="M9 19.5h6M12 16v3.5" /></g></I>
);

/* ------------------------------------------------ dock app tiles */
/** A HyperOS app icon: a rounded square with a gradient and a white glyph. */
export function AppTile({
  from,
  to,
  size = 44,
  children,
}: {
  from: string;
  to: string;
  size?: number;
  children: React.ReactNode;
}) {
  return (
    <span
      className="flex items-center justify-center text-white shadow-[0_4px_14px_-6px_rgba(0,0,0,0.8)]"
      style={{
        width: size,
        height: size,
        borderRadius: size * 0.27,
        background: `linear-gradient(145deg, ${from}, ${to})`,
      }}
    >
      {children}
    </span>
  );
}

export const AppVehicle = () => (
  <AppTile from="#6b7280" to="#2f3339">
    <CarGlyph size={26} />
  </AppTile>
);
export const AppNav = () => (
  <AppTile from="#33d18f" to="#1a7fe0">
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#fff" d="M12 3.5 19 20l-7-3.6L5 20Z" />
    </svg>
  </AppTile>
);
export const AppMusic = () => (
  <AppTile from="#ff5f6d" to="#c2185b">
    <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#fff" d="M9 17.5V6.2l10-2.2v11.3a2.6 2.6 0 1 1-1.6-2.4V7.6L10.6 9v8.9A2.6 2.6 0 1 1 9 17.5Z" />
    </svg>
  </AppTile>
);
export const AppTrack = () => (
  <AppTile from="#2b2b2b" to="#0d0d0d">
    <svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true">
      <path fill="none" stroke="#f5c518" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" d="M4.5 16.5c0-5 3-9 7.5-9 3 0 3.5 2.5 6 2.5M7 16.5h12.5" />
      <circle cx="18.5" cy="10" r="1.4" fill="#f5c518" />
    </svg>
  </AppTile>
);
export const AppApps = () => (
  <AppTile from="#3a3b40" to="#1f2024">
    <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
      <rect x="4" y="4" width="7" height="7" rx="2" fill="#ffb020" />
      <rect x="13" y="4" width="7" height="7" rx="2" fill="#2c7bff" />
      <rect x="4" y="13" width="7" height="7" rx="2" fill="#34c46b" />
      <rect x="13" y="13" width="7" height="7" rx="2" fill="#ff4b6e" />
    </svg>
  </AppTile>
);
