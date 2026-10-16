import React from 'react';

/**
 * DiLink's line icons, drawn here (nothing of the maker's artwork is shipped). 24 x 24, 1.8 stroke.
 */
export interface IconProps {
  size?: number;
  sw?: number;
  style?: React.CSSProperties;
}

function Svg({ size = 24, sw = 1.8, style, children }: IconProps & { children: React.ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth={sw}
      strokeLinecap="round"
      strokeLinejoin="round"
      style={style}
      aria-hidden
    >
      {children}
    </svg>
  );
}

export const Back = (p: IconProps) => (
  <Svg {...p}>
    <path d="M9 7 4 12l5 5" />
    <path d="M4 12h9a6 6 0 0 1 6 6" />
  </Svg>
);
export const Home = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 11.500 12 4l8 7.500" />
    <path d="M6 10v10h4.500v-5.500h3V20H18V10" />
  </Svg>
);
export const Chev = ({ dir = 'l', ...p }: IconProps & { dir?: 'l' | 'r' | 'u' | 'd' }) => (
  <Svg {...p}>
    <path d={{ l: 'M15 5l-7 7 7 7', r: 'M9 5l7 7-7 7', u: 'M5 15l7-7 7 7', d: 'M5 9l7 7 7-7' }[dir]} />
  </Svg>
);
export const Gear = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="3" />
    <path d="M12 2.500v3M12 18.500v3M2.500 12h3M18.500 12h3M5.300 5.300l2.100 2.100M16.600 16.600l2.100 2.100M5.300 18.700l2.100-2.100M16.600 7.400l2.100-2.100" />
  </Svg>
);
export const SeatHeat = (p: IconProps) => (
  <Svg {...p}>
    <path d="M7 4c1 3 3 5 3 9v4h7" />
    <path d="M7 4c-1 0-2 1-1.500 3l1 5" />
    <path d="M11 20h7" />
    <path d="M14 3c.8.9.8 1.800 0 2.700M17 3c.8.9.8 1.800 0 2.700M20 3c.8.9.8 1.800 0 2.700" />
  </Svg>
);
export const SeatVent = (p: IconProps) => (
  <Svg {...p}>
    <path d="M7 4c1 3 3 5 3 9v4h7" />
    <path d="M7 4c-1 0-2 1-1.500 3l1 5" />
    <path d="M11 20h7" />
    <path d="M14 4c1.500 0 3 1 3 2.500S16 8 15 8M14 4v7" />
  </Svg>
);
export const DefrostFront = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3 18c2-6 5-9 9-9s7 3 9 9z" />
    <path d="M8 4c.8.9.8 1.800 0 2.700M12 3c.8.9.8 1.800 0 2.700M16 4c.8.9.8 1.800 0 2.700" />
  </Svg>
);
export const DefrostRear = (p: IconProps) => (
  <Svg {...p}>
    <rect x="4" y="9" width="16" height="9" rx="2" />
    <path d="M8 4c.8.9.8 1.800 0 2.700M12 3c.8.9.8 1.800 0 2.700M16 4c.8.9.8 1.800 0 2.700" />
    <path d="M7 12.500h10M7 15.500h10" />
  </Svg>
);
export const Sun = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2.500v2.500M12 19v2.500M2.500 12H5M19 12h2.500M5.300 5.300l1.800 1.800M16.900 16.900l1.800 1.800M5.300 18.700l1.800-1.800M16.900 7.100l1.800-1.800" />
  </Svg>
);
export const Camera = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 8h3l1.500-2.500h7L17 8h3v11H4z" />
    <circle cx="12" cy="13" r="3.500" />
  </Svg>
);
export const Grid = (p: IconProps) => (
  <Svg {...p}>
    <rect x="4" y="4" width="6" height="6" rx="1.200" />
    <rect x="14" y="4" width="6" height="6" rx="1.200" />
    <rect x="4" y="14" width="6" height="6" rx="1.200" />
    <rect x="14" y="14" width="6" height="6" rx="1.200" />
  </Svg>
);
export const Search = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="11" cy="11" r="6" />
    <path d="m16 16 4.500 4.500" />
  </Svg>
);
export const Phone = (p: IconProps) => (
  <Svg {...p}>
    <path d="M6 3.500h3l1.500 4-2 1.500a11 11 0 0 0 6.500 6.500l1.500-2 4 1.500v3a2 2 0 0 1-2 2A16 16 0 0 1 4 5.500a2 2 0 0 1 2-2Z" />
  </Svg>
);
export const Music = (p: IconProps) => (
  <Svg {...p}>
    <path d="M9 18V6l10-2v12" />
    <circle cx="6.500" cy="18" r="2.500" />
    <circle cx="16.500" cy="16" r="2.500" />
  </Svg>
);
export const Bluetooth = (p: IconProps) => (
  <Svg {...p}>
    <path d="m7 7 10 10-5 4V3l5 4L7 17" />
  </Svg>
);
export const Wifi = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3 9a14 14 0 0 1 18 0M6 12.500a10 10 0 0 1 12 0M9 16a5.500 5.500 0 0 1 6 0" />
    <circle cx="12" cy="19" r="1" fill="currentColor" />
  </Svg>
);
export const Pin = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 21s6-5.500 6-11a6 6 0 0 0-12 0c0 5.500 6 11 6 11Z" />
    <circle cx="12" cy="10" r="2.200" />
  </Svg>
);
export const User = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="8" r="3.500" />
    <path d="M5 20c.8-4 3.500-6 7-6s6.200 2 7 6" />
  </Svg>
);
export const Fan = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="1.800" />
    <path d="M12 10.200C12 6 10 3.500 7.500 4c-2 .5-1.500 3.500 1 5.500M13.800 12c4.200 0 6.700 2 6.200 4.500-.5 2-3.500 1.500-5.500-1M12 13.800c0 4.200 2 6.700 4.500 6.200 2-.5 1.500-3.500-1-5.500M10.200 12c-4.200 0-6.700-2-6.200-4.500.5-2 3.500-1.500 5.500 1" />
  </Svg>
);
export const Snow = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 3v18M4.200 7.500l15.600 9M4.200 16.500l15.600-9" />
    <path d="m9.500 4.500 2.500 2 2.500-2M9.500 19.500l2.500-2 2.500 2" />
  </Svg>
);
export const Recirc = (p: IconProps) => (
  <Svg {...p}>
    <path d="M5 12a7 7 0 0 1 12-5l2 2M19 12a7 7 0 0 1-12 5l-2-2" />
    <path d="M19 4v5h-5M5 20v-5h5" />
  </Svg>
);
export const AirFace = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="8" cy="6.500" r="2.200" />
    <path d="M5.500 12.500c0-2 1.200-3 2.500-3s2.500 1 2.500 3v4" />
    <path d="M13 8h8M13 11h7M13 14h6" />
  </Svg>
);
export const AirFeet = (p: IconProps) => (
  <Svg {...p}>
    <path d="M7 4v9l-3 5h5l2-3" />
    <path d="M14 12l3 3M17 12l3 3M14 16l3 3" />
  </Svg>
);
export const Play = (p: IconProps) => (
  <Svg {...p}>
    <path d="M7 4.500v15l12-7.500z" fill="currentColor" />
  </Svg>
);
export const Pause = (p: IconProps) => (
  <Svg {...p}>
    <rect x="6" y="5" width="4" height="14" rx="1" fill="currentColor" />
    <rect x="14" y="5" width="4" height="14" rx="1" fill="currentColor" />
  </Svg>
);
export const Prev = (p: IconProps) => (
  <Svg {...p}>
    <path d="M18 5v14L8 12z" fill="currentColor" />
    <path d="M6 5v14" />
  </Svg>
);
export const Next = (p: IconProps) => (
  <Svg {...p}>
    <path d="M6 5v14l10-7z" fill="currentColor" />
    <path d="M18 5v14" />
  </Svg>
);
export const Volume = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 9.500h3.500L12 5.500v13l-4.500-4H4z" />
    <path d="M15.500 9a4 4 0 0 1 0 6M18 6.500a8 8 0 0 1 0 11" />
  </Svg>
);
export const Mute = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 9.500h3.500L12 5.500v13l-4.500-4H4z" />
    <path d="m16 9.500 5 5M21 9.500l-5 5" />
  </Svg>
);
export const CarSide = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3 15v-3l2-4.500h9.500l4 4.500 2.500.8V15" />
    <circle cx="7.500" cy="16" r="2" />
    <circle cx="16.500" cy="16" r="2" />
    <path d="M9.500 16h5" />
  </Svg>
);
export const Lock = (p: IconProps) => (
  <Svg {...p}>
    <rect x="5" y="10.500" width="14" height="9.500" rx="2" />
    <path d="M8 10.500V8a4 4 0 0 1 8 0v2.500" />
  </Svg>
);
export const Unlock = (p: IconProps) => (
  <Svg {...p}>
    <rect x="5" y="10.500" width="14" height="9.500" rx="2" />
    <path d="M8 10.500V8a4 4 0 0 1 7.500-1.500" />
  </Svg>
);
export const Bolt = (p: IconProps) => (
  <Svg {...p}>
    <path d="M13 3 5 13.500h6L10 21l8-10.500h-6z" />
  </Svg>
);
export const Power = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 3.500v8" />
    <path d="M6.500 6.800a8 8 0 1 0 11 0" />
  </Svg>
);
export const Check = (p: IconProps) => (
  <Svg {...p}>
    <path d="m5 12.500 4.500 4.500L19 7.500" />
  </Svg>
);
export const Close = (p: IconProps) => (
  <Svg {...p}>
    <path d="M6 6l12 12M18 6 6 18" />
  </Svg>
);
export const Wheel = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8" />
    <circle cx="12" cy="12" r="2" />
    <path d="M4 12h6M14 12h6M12 14v6" />
  </Svg>
);
export const Bulb = (p: IconProps) => (
  <Svg {...p}>
    <path d="M9 18h6M10 21h4" />
    <path d="M8.500 14.500A6 6 0 1 1 15.500 14.500c-.8.7-1.300 1.500-1.500 2.500h-4c-.2-1-.7-1.800-1.500-2.500Z" />
  </Svg>
);
export const Doc = (p: IconProps) => (
  <Svg {...p}>
    <path d="M7 3.500h7l4 4V20.500H7z" />
    <path d="M14 3.500v4h4M9.500 12h6M9.500 15.500h6" />
  </Svg>
);
export const Shield = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 3.500 5 6v6c0 4 3 7 7 8.500 4-1.500 7-4.500 7-8.500V6z" />
    <path d="m9 12 2.200 2.200L15.500 10" />
  </Svg>
);
export const Link = (p: IconProps) => (
  <Svg {...p}>
    <path d="M10 14a4 4 0 0 0 5.600 0l3-3a4 4 0 0 0-5.600-5.600l-1 1M14 10a4 4 0 0 0-5.600 0l-3 3a4 4 0 0 0 5.600 5.600l1-1" />
  </Svg>
);
export const Radio = (p: IconProps) => (
  <Svg {...p}>
    <rect x="3.500" y="8" width="17" height="11.500" rx="2" />
    <path d="M7 8 17 3M7.500 13.500h4M15 13.500h2" />
  </Svg>
);
export const Map = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 6.500 9 4.500l6 2 5-2V17.500l-5 2-6-2-5 2z" />
    <path d="M9 4.500v13M15 6.500v13" />
  </Svg>
);
export const Leaf = (p: IconProps) => (
  <Svg {...p}>
    <path d="M5 19c0-8 5-13 14-14 0 9-5 14-13 14" />
    <path d="M5 19c3-5 6-8 10-10" />
  </Svg>
);
