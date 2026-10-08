import React from 'react';

/**
 * The ZEEKR OS skin's glyphs: bold, solid black pictograms on a 24 grid, as the 7X's screen
 * draws them (blender/reference/zeekr-7x/hmi). They are not the maker's artwork: the shapes
 * follow the photographs, nothing is copied.
 */
export interface IconProps {
  size?: number;
  className?: string;
  style?: React.CSSProperties;
  /** stroke weight on the 24 grid */
  sw?: number;
}

function Svg({
  size = 24,
  sw = 2,
  fill = 'none',
  className,
  style,
  children,
}: IconProps & { fill?: string; children: React.ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={fill}
      stroke="currentColor"
      strokeWidth={sw}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      style={style}
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

const F = 'currentColor';

/* --------------------------------------------------------------- bottom bar */
export const Home = (p: IconProps) => (
  <Svg {...p} fill={F} sw={1.2}>
    <path d="M3 12.5 12 3.5l9 9v8h-6.200v-5.200H9.200v5.200H3z" />
    <path d="M12 3.500v6.400l-4.600 4.600" stroke="#fff" strokeWidth={1.100} fill="none" opacity="0.7" />
  </Svg>
);
export const CarFront = (p: IconProps) => (
  <Svg {...p} fill={F} sw={1.1}>
    <path d="M5.200 6.800C5.600 5.700 6.400 5 7.500 5h9c1.100 0 1.900.7 2.300 1.800l1.200 3.200c.9.300 1.500 1.100 1.500 2.100v5.400c0 .6-.4 1-1 1h-1.300c-.6 0-1-.4-1-1v-1H6.800v1c0 .6-.4 1-1 1H4.500c-.6 0-1-.4-1-1v-5.400c0-1 .6-1.800 1.500-2.100z" />
    <path d="M7.300 7.200h9.400l.8 2.300H6.500z" fill="#fff" stroke="none" opacity="0.92" />
  </Svg>
);
export const Cam360 = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3 5.500h10.500a1.500 1.500 0 0 1 1.500 1.500v5a1.500 1.500 0 0 1-1.500 1.500H3z" fill={F} stroke="none" />
    <path d="M15 8.200l5-2.200v7l-5-2.200z" fill={F} stroke="none" />
    <text x="11.500" y="22" fontSize="7.800" fontWeight="800" textAnchor="middle" fill={F} stroke="none" fontFamily="Arial, sans-serif">360°</text>
  </Svg>
);
export const DefrostFront = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4.500 4.500h15l2 11.500h-19z" />
    <path d="M8 8.200v3.800M12 8.200v3.800M16 8.200v3.800" />
    <path d="M6 19.200c1.200-1 2.400 1 3.600 0s2.400 1 3.600 0 2.400 1 3.600 0" />
  </Svg>
);
export const SeatHeat = (p: IconProps) => (
  <Svg {...p} sw={1.800}>
    <path d="M6.500 3.500c1.500 0 2.200.9 2.400 2.300l1 8.700h8.600c1.300 0 2.100.9 2.100 2.100v2.400H8.200c-1.100 0-1.900-.7-2.100-1.700L4.300 7c-.2-1.900.6-3.500 2.200-3.500z" fill={F} />
    <path d="M3 21h18" />
  </Svg>
);
export const SeatAuto = (p: IconProps) => (
  <Svg {...p} sw={1.800}>
    <path d="M10.500 3.500c1.500 0 2.200.9 2.400 2.300l1 8.700h6c1.300 0 2.100.9 2.100 2.100v2.400H12.200c-1.100 0-1.900-.7-2.100-1.700L8.300 7c-.2-1.900.6-3.500 2.200-3.500z" fill={F} />
    <text x="4.500" y="9.500" fontSize="8.500" fontWeight="800" fill="#d4182a" stroke="none" fontFamily="Arial, sans-serif">A</text>
    <path d="M3 21h18" />
  </Svg>
);
export const Chev = ({ dir = 'l', ...p }: IconProps & { dir?: 'l' | 'r' | 'u' | 'd' }) => (
  <Svg {...p} sw={p.sw ?? 2.400}>
    <path d={dir === 'l' ? 'M15 5l-7 7 7 7' : dir === 'r' ? 'M9 5l7 7-7 7' : dir === 'u' ? 'M5 15l7-7 7 7' : 'M5 9l7 7 7-7'} />
  </Svg>
);
export const Fan = (p: IconProps) => (
  <Svg {...p} fill={F} sw={0.8}>
    <path d="M12 12.500c-1.800-.4-3.300-2-3.300-4 0-2 1.300-3.800 3.300-3.800 1.500 0 2.200 1.100 2.100 2.200-.1 1.500-.9 2.900-2.100 5.600z" />
    <path d="M11.500 12c.4-1.800 2-3.300 4-3.300 2 0 3.800 1.300 3.800 3.300 0 1.500-1.100 2.200-2.200 2.100-1.500-.1-2.900-.9-5.600-2.100z" />
    <path d="M12 11.500c1.800.4 3.300 2 3.300 4 0 2-1.300 3.800-3.300 3.800-1.500 0-2.200-1.100-2.100-2.200.1-1.500.9-2.900 2.100-5.600z" />
    <path d="M12.500 12c-.4 1.800-2 3.300-4 3.300-2 0-3.800-1.300-3.800-3.300 0-1.500 1.100-2.200 2.200-2.100 1.500.1 2.900.9 5.600 2.100z" />
    <circle cx="12" cy="12" r="1.600" fill="#fff" stroke="none" />
  </Svg>
);
export const DefrostRear = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3.500 6h17l-1.500 11h-14z" />
    <path d="M7.500 9.500c1-.9 2 .9 3 0s2 .9 3 0 2 .9 3 0M7.500 13c1-.9 2 .9 3 0s2 .9 3 0 2 .9 3 0" />
  </Svg>
);
export const Music = (p: IconProps) => (
  <Svg {...p} fill={F} sw={1.600}>
    <path d="M9 4.500l11-2v14.200" fill="none" />
    <path d="M9 4.500v13.500" fill="none" />
    <ellipse cx="6.200" cy="18" rx="3" ry="2.500" />
    <ellipse cx="17.200" cy="16.300" rx="3" ry="2.500" />
    <path d="M9 4.500l11-2v3.300L9 7.800z" />
  </Svg>
);
export const Apps = (p: IconProps) => (
  <Svg {...p} fill={F} sw={1.200}>
    <rect x="3.500" y="3.500" width="7" height="7" rx="1.300" />
    <rect x="13.500" y="3.500" width="7" height="7" rx="1.300" />
    <rect x="3.500" y="13.500" width="7" height="7" rx="1.300" />
    <path d="M17 13l3.800 3.800L17 20.600l-3.800-3.800z" />
  </Svg>
);
export const Volume = (p: IconProps) => (
  <Svg {...p} fill={F} sw={1.600}>
    <path d="M3.500 9.500h3.200L11.500 5v14l-4.800-4.500H3.500z" />
    <path d="M15 8.800c1.600 1.800 1.600 4.600 0 6.400M18 6.200c2.800 3.200 2.800 8.400 0 11.600" fill="none" />
  </Svg>
);

/* --------------------------------------------------------------- status bar */
export const Leaf = (p: IconProps) => (
  <Svg {...p} fill={F} sw={0.8}>
    <path d="M5 19C4 11 8.500 5 20 4.500 19.500 14 14 19.500 7 19.200L9.500 14" fill={F} />
    <path d="M5 19l7-7" stroke="#fff" strokeWidth={1.100} fill="none" opacity="0.6" />
  </Svg>
);
export const LockOpen = (p: IconProps) => (
  <Svg {...p} sw={1.800}>
    <rect x="5.500" y="11" width="13" height="9.500" rx="1.800" fill={F} />
    <path d="M8.500 11V8a3.500 3.500 0 0 1 6.800-1.200" />
  </Svg>
);
export const LockShut = (p: IconProps) => (
  <Svg {...p} sw={1.800}>
    <rect x="5.500" y="11" width="13" height="9.500" rx="1.800" fill={F} />
    <path d="M8.500 11V8a3.500 3.500 0 0 1 7 0v3" />
  </Svg>
);
export const DashcamSb = (p: IconProps) => (
  <Svg {...p} fill={F} sw={1}>
    <rect x="3" y="7" width="13" height="10" rx="2.200" />
    <path d="M16.500 10l4.500-2.500v9L16.500 14z" />
  </Svg>
);
export const Siren = (p: IconProps) => (
  <Svg {...p} sw={1.800}>
    <path d="M6.500 18.500v-5a5.500 5.500 0 0 1 11 0v5" fill={F} />
    <path d="M4 18.500h16M12 3.500v2M4.500 7l1.500 1.300M19.500 7L18 8.300" />
  </Svg>
);
export const ShieldSb = (p: IconProps) => (
  <Svg {...p} sw={1.800}>
    <path d="M12 3l7.500 3v5.500c0 4.600-3.200 7.800-7.500 9.500-4.300-1.700-7.500-4.900-7.500-9.500V6z" fill={F} />
  </Svg>
);
export const PhoneLink = (p: IconProps) => (
  <Svg {...p} sw={1.800}>
    <path d="M15 5.500c2.200 1.100 3.500 3.100 3.500 5.500M12.200 7.600c1.100.6 1.800 1.600 1.800 2.900" />
    <path d="M6 11a8 8 0 0 0 8 8l1.600-1.200c.6-.4.700-1.300.1-1.700l-1.800-1.300c-.4-.3-1-.2-1.400.2l-.5.600a8 8 0 0 1-2.800-2.800l.6-.5c.4-.4.500-1 .2-1.400L8.700 8.200c-.4-.6-1.300-.5-1.700.1z" fill={F} />
  </Svg>
);
export const Bluetooth = (p: IconProps) => (
  <Svg {...p} sw={1.800}>
    <path d="M7 7.500l10 9-5 4.500V3l5 4.500-10 9" />
  </Svg>
);
export const Broadcast = (p: IconProps) => (
  <Svg {...p} sw={1.700}>
    <circle cx="12" cy="12" r="2" fill={F} />
    <path d="M7.800 8.200a6 6 0 0 0 0 7.600M16.200 8.200a6 6 0 0 1 0 7.600M5 5.500a10 10 0 0 0 0 13M19 5.500a10 10 0 0 1 0 13" />
  </Svg>
);
export const Signal5G = (p: IconProps) => (
  <Svg {...p} fill={F} sw={0.6}>
    <rect x="4" y="14" width="2.400" height="5" rx="0.6" />
    <rect x="8" y="11" width="2.400" height="8" rx="0.6" />
    <rect x="12" y="8" width="2.400" height="11" rx="0.6" />
    <rect x="16" y="5" width="2.400" height="14" rx="0.6" opacity="0.4" />
    <text x="4" y="10" fontSize="6" fontWeight="800" stroke="none" fontFamily="Arial, sans-serif">5G</text>
  </Svg>
);
export const Mascot = ({ size = 38 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden="true">
    <defs>
      <linearGradient id="zkm" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stopColor="#7d8bff" />
        <stop offset="1" stopColor="#b266e6" />
      </linearGradient>
    </defs>
    <path d="M7 15 5 5l9 5.500h12L35 5l-2 10c1.800 2 2.800 4.500 2.800 7.200 0 6-6.500 10.300-15.800 10.300S4.200 28.200 4.200 22.200C4.200 19.500 5.200 17 7 15z" fill="url(#zkm)" />
    <rect x="9" y="17" width="22" height="12" rx="6" fill="#fff" opacity="0.95" />
    <circle cx="15.500" cy="23" r="2.200" fill="#3b2a8f" />
    <circle cx="24.500" cy="23" r="2.200" fill="#3b2a8f" />
  </svg>
);

/* --------------------------------------------------------------- the left rail */
export const NavArrow = ({ size = 30 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 30 30" aria-hidden="true">
    <circle cx="15" cy="15" r="14" fill="#fff" opacity="0.85" />
    <path d="M15 5.500 22 22.500 15 19 8 22.500z" fill="#2f6fe4" />
  </svg>
);
export const Scan = (p: IconProps) => (
  <Svg {...p} sw={2}>
    <path d="M4 8V6.200C4 5 5 4 6.200 4H8M16 4h1.800C19 4 20 5 20 6.200V8M20 16v1.800c0 1.200-1 2.200-2.200 2.200H16M8 20H6.200C5 20 4 19 4 17.800V16" />
    <circle cx="12" cy="12" r="3" />
  </Svg>
);
export const DashcamRail = (p: IconProps) => (
  <Svg {...p} fill={F} sw={1}>
    <path d="M3 13c0-4 2.500-7 9-7s9 3 9 7v4H3z" />
    <circle cx="12" cy="13" r="3.200" fill="#fff" stroke="none" />
    <circle cx="12" cy="13" r="1.500" />
  </Svg>
);
export const Hud = (p: IconProps) => (
  <Svg {...p} fill={F} sw={1}>
    <path d="M4 6h16a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1z" />
    <text x="12" y="13.500" fontSize="6.500" fontWeight="800" textAnchor="middle" fill="#fff" stroke="none" fontFamily="Arial, sans-serif">HUD</text>
    <path d="M9 19.500 12 17l3 2.500" fill="none" strokeWidth={1.500} />
  </Svg>
);
export const WheelP = (p: IconProps) => (
  <Svg {...p} sw={2}>
    <circle cx="11" cy="11.500" r="7.500" />
    <circle cx="11" cy="11.500" r="2.200" fill={F} />
    <path d="M4 10.500h4.500M13.500 10.500H18M11 14v5" />
    <circle cx="18.500" cy="18.500" r="3.300" fill={F} stroke="none" />
    <text x="18.500" y="20.300" fontSize="5" fontWeight="800" textAnchor="middle" fill="#fff" stroke="none" fontFamily="Arial, sans-serif">P</text>
  </Svg>
);
export const SeatRail = (p: IconProps) => (
  <Svg {...p} sw={1.800}>
    <path d="M7 3.500c1.600 0 2.300 1 2.500 2.400l.8 7.100h7c1.300 0 2 .8 2 2v2.200H9.400c-1.100 0-1.800-.6-2-1.600L5.600 7C5.300 5 6 3.500 7 3.500z" fill={F} />
    <rect x="3.500" y="20.300" width="9" height="2" rx="1" fill="#e5412d" stroke="none" />
  </Svg>
);
export const Bulb = (p: IconProps) => (
  <Svg {...p} sw={1.800}>
    <path d="M12 4a5.500 5.500 0 0 0-3 10.100V16.500h6V14.100A5.500 5.500 0 0 0 12 4z" fill={F} />
    <path d="M9.500 19h5M10.500 21.500h3" />
    <path d="M3 9.500h2M19 9.500h2M5 4.500l1.500 1.500M19 4.500 17.500 6" />
  </Svg>
);
export const Dots = (p: IconProps) => (
  <Svg {...p} fill={F} sw={0}>
    <circle cx="5.500" cy="12" r="2" />
    <circle cx="12" cy="12" r="2" />
    <circle cx="18.500" cy="12" r="2" />
  </Svg>
);

/* ----------------------------------------------------------- the car's hotspots */
export const HsFrunk = (p: IconProps) => (
  <Svg {...p} fill={F} sw={1}>
    <path d="M3 15.500v-2c0-1 .6-1.800 1.600-2.100L8 10.500 10.500 6c.3-.6.9-1 1.600-1H20l-2 5.500H8.500l-3 .8V15.500z" opacity="0.95" />
    <path d="M3 15.500h18v2.500a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z" />
  </Svg>
);
export const HsDoor = (p: IconProps) => (
  <Svg {...p} fill={F} sw={1}>
    <path d="M4 10.500c0-1.700 1.300-3 3-3h8.500l4.500 3.800V17a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z" />
    <path d="M6.500 12.800h8" stroke="#fff" strokeWidth={1.500} />
  </Svg>
);
export const HsDoorRear = (p: IconProps) => (
  <Svg {...p} fill={F} sw={1}>
    <path d="M5 8.500h11c1.700 0 3 1.300 3 3v5.500a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2z" />
    <path d="M8 12.500h6" stroke="#fff" strokeWidth={1.500} />
  </Svg>
);
export const HsBoot = (p: IconProps) => (
  <Svg {...p} fill={F} sw={1}>
    <path d="M3.500 17.500V12c0-.7.300-1.200.9-1.500l3.800-2 2-2.700c.3-.4.700-.6 1.200-.6H19l1.500 2.500v10.300a1 1 0 0 1-1 1H4.500a1 1 0 0 1-1-1z" />
    <path d="M13 9.200h5.200v4H13z" fill="#fff" stroke="none" opacity="0.9" />
  </Svg>
);
export const HsCharge = (p: IconProps) => (
  <Svg {...p} sw={1.800}>
    <path d="M13.500 3 6.500 13.500h5l-1 7.500 7-10.500h-5z" fill={F} />
  </Svg>
);
export const HsMirror = (p: IconProps) => (
  <Svg {...p} fill={F} sw={1}>
    <path d="M6 9c0-1.700 1.300-3 3-3h6c2.800 0 5 2.200 5 5v2.500c0 1.700-1.300 3-3 3H11c-2.800 0-5-2.200-5-5z" />
    <path d="M9 17.500h7l1.500 2.500H8z" />
  </Svg>
);

/* ------------------------------------------------------------------ pages */
export const SeatComfort = (p: IconProps) => (
  <Svg {...p} sw={1.800}>
    <path d="M7 3.500c1.600 0 2.300 1 2.500 2.400l.8 7.100h7c1.300 0 2 .8 2 2v2.200H9.400c-1.100 0-1.800-.6-2-1.600L5.600 7C5.300 5 6 3.500 7 3.500z" fill={F} />
    <path d="M16.500 3c1.500.5 2.500 2 2.500 3.500-1.800-.2-3.300-1.200-3.800-2.800z" fill="#2c8f56" stroke="none" />
    <path d="M3.500 21.500h14" />
  </Svg>
);
export const SeatAdjust = (p: IconProps) => (
  <Svg {...p} sw={1.800}>
    <path d="M7 4c1.600 0 2.300 1 2.500 2.400l.8 7.100h7c1.300 0 2 .8 2 2v2H9.400c-1.100 0-1.800-.6-2-1.600L5.600 7.500C5.300 5.500 6 4 7 4z" fill={F} />
    <path d="M17 7.500l3 2.500-3 2.500M4 20.500l2.500 1.500" />
  </Svg>
);
export const Gear = (p: IconProps) => (
  <Svg {...p} sw={0.6}>
    <path fillRule="evenodd" fill={F} d="M19.45 10.52 L19.56 11.23 L22.20 11.76 L22.13 13.20 L19.45 13.48 L18.32 16.22 L17.89 16.80 L19.38 19.04 L18.31 20.01 L16.22 18.32 L13.48 19.45 L12.77 19.56 L12.24 22.20 L10.80 22.13 L10.52 19.45 L7.78 18.32 L7.20 17.89 L4.96 19.38 L3.99 18.31 L5.68 16.22 L4.55 13.48 L4.44 12.77 L1.80 12.24 L1.87 10.80 L4.55 10.52 L5.68 7.78 L6.11 7.20 L4.62 4.96 L5.69 3.99 L7.78 5.68 L10.52 4.55 L11.23 4.44 L11.76 1.80 L13.20 1.87 L13.48 4.55 L16.22 5.68 L16.80 6.11 L19.04 4.62 L20.01 5.69 L18.32 7.78Z M12 8.6a3.4 3.4 0 1 0 0.01 0Z" />
  </Svg>
);
export const Check = (p: IconProps) => (
  <Svg {...p} sw={2.600}>
    <path d="M4.500 12.500 10 18 20 6.500" />
  </Svg>
);
export const Play = (p: IconProps) => (
  <Svg {...p} fill={F} sw={0.8}>
    <path d="M7 4.500v15L19.500 12z" />
  </Svg>
);
export const Pause = (p: IconProps) => (
  <Svg {...p} fill={F} sw={0.8}>
    <rect x="6" y="4.500" width="4" height="15" rx="1" />
    <rect x="14" y="4.500" width="4" height="15" rx="1" />
  </Svg>
);
export const Prev = (p: IconProps) => (
  <Svg {...p} fill={F} sw={1}>
    <path d="M18 5v14L8 12zM5.500 5v14" />
  </Svg>
);
export const Next = (p: IconProps) => (
  <Svg {...p} fill={F} sw={1}>
    <path d="M6 5v14l10-7zM18.500 5v14" />
  </Svg>
);
export const Snow = (p: IconProps) => (
  <Svg {...p} sw={1.800}>
    <path d="M12 3v18M4.200 7.500l15.600 9M4.200 16.500l15.600-9M9.500 4.500 12 7l2.500-2.500M9.500 19.500 12 17l2.500 2.500" />
  </Svg>
);
export const Sync = (p: IconProps) => (
  <Svg {...p} sw={1.900}>
    <path d="M4 12a8 8 0 0 1 13.500-5.800L20 8.500M20 4v4.500h-4.500M20 12a8 8 0 0 1-13.500 5.800L4 15.500M4 20v-4.500h4.500" />
  </Svg>
);
export const Recirc = (p: IconProps) => (
  <Svg {...p} sw={1.900}>
    <path d="M5 10h11M5 14h11M5 18h11" opacity="0" />
    <path d="M4.500 13.500c0-3.500 3-6 7-6h7.500M16 4.500 19 7.500 16 10.500M19.500 10.500c0 3.500-3 6-7 6H5M8 19.500 5 16.500 8 13.500" />
  </Svg>
);
export const AirFace = (p: IconProps) => (
  <Svg {...p} fill={F} sw={1.500}>
    <circle cx="9" cy="6.500" r="2.500" />
    <path d="M5 21v-6c0-1.700 1.300-3 3-3h2c1.700 0 3 1.300 3 3v6" />
    <path d="M16 8.500h5M16 12h4M16 15.500h3" fill="none" />
  </Svg>
);
export const AirFeet = (p: IconProps) => (
  <Svg {...p} fill={F} sw={1.500}>
    <circle cx="9" cy="5.500" r="2.500" />
    <path d="M6 9h6v7l1.500 5h-3.800L8 16.500 6.500 21H3z" />
    <path d="M16 18.500h5M16 21h4" fill="none" />
  </Svg>
);
