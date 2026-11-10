import React from 'react';

/**
 * The DiLink skin's line icons for the Seal, drawn here in the car's style (thin round strokes on a 24 grid).
 * They are not the maker's artwork: the shapes follow the photographs of the screen
 * (blender/reference/byd-seal-ev/hmi), nothing is copied.
 */
export interface IconProps {
  size?: number;
  className?: string;
  style?: React.CSSProperties;
  sw?: number;
}

function Svg({ size = 24, sw = 1.7, fill = 'none', className, style, children }: IconProps & { fill?: string; children: React.ReactNode }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill={fill} stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" className={className} style={style} aria-hidden="true">
      {children}
    </svg>
  );
}
const F = 'currentColor';

/* ------------------------------------------------------------ the system bar */
export const Back = (p: IconProps) => (
  <Svg {...p}>
    <path d="M9 7L4.500 11.500 9 16M5 11.500h9.500a4.500 4.500 0 0 1 0 9H12" />
  </Svg>
);
export const Home = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 11.200L12 4l8 7.200M6.200 9.800V19.500h4.300v-5h3v5h4.300V9.800" />
  </Svg>
);
export const Hex = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 3.200l7.600 4.400v8.800L12 20.800l-7.600-4.400V7.600z" />
    <circle cx="12" cy="12" r="3" />
  </Svg>
);
export const FanAc = (p: IconProps) => (
  <Svg {...p} sw={0}>
    {[0, 120, 240].map((a) => (
      <path key={a} transform={`rotate(${a} 12 12)`} d="M12 12.200c-1.300-3.800-.7-7 2-8.900 1.700 3 1.100 6.400-2 8.900z" fill={F} />
    ))}
    <circle cx="12" cy="12" r="1.900" fill={F} />
  </Svg>
);
export const SeatHeat = (p: IconProps) => (
  <Svg {...p}>
    <path d="M8 3.500c2.600.5 3 3 3.400 6l.6 3.500h5.200a2.400 2.400 0 0 1 2.300 1.800l.5 2.200H9.300" />
    <path d="M3.600 19.200c.8-.6 1.500-.6 2.300 0s1.500.6 2.300 0M4 22.200c.8-.6 1.500-.6 2.300 0" strokeWidth={1.400} />
    <path d="M9 18.500H6.500c-.7-2.500-1.100-5-1.100-7.500" />
  </Svg>
);
export const DefrostFront = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 15.500c1.700-5.600 4.500-8 8-8s6.300 2.400 8 8z" />
    <path d="M8.500 18.800c.7-.8 1.300 0 2 0s1.300-.8 2 0 1.300 0 2 0" strokeWidth={1.400} />
    <path d="M9.300 13.500c0-1.700 1-3 2.700-3.400" strokeWidth={1.300} />
  </Svg>
);
export const Grid = (p: IconProps) => (
  <Svg {...p}>
    <rect x="4" y="4" width="6.500" height="6.500" rx="1.600" />
    <rect x="13.500" y="4" width="6.500" height="6.500" rx="1.600" />
    <rect x="4" y="13.500" width="6.500" height="6.500" rx="1.600" />
    <rect x="13.500" y="13.500" width="6.500" height="6.500" rx="1.600" />
  </Svg>
);
export const Split = (p: IconProps) => (
  <Svg {...p}>
    <rect x="3.500" y="5" width="17" height="14" rx="2.600" />
    <path d="M12 5v14" />
  </Svg>
);
export const Windows = (p: IconProps) => (
  <Svg {...p}>
    <rect x="3.500" y="8" width="13" height="11" rx="2.200" />
    <path d="M7.500 8V6.500a2 2 0 0 1 2-2H18a2 2 0 0 1 2 2V15a2 2 0 0 1-2 2h-1.500" />
  </Svg>
);

/* ------------------------------------------------------------------- status */
export const Orb = ({ size = 28 }: { size?: number }) => (
  <span
    className="block shrink-0 rounded-full"
    style={{ width: size, height: size, background: 'radial-gradient(circle at 32% 30%, #fff 0%, #cdd6ff 25%, #8a97ee 55%, #3b3f9c 100%)', boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.4)' }}
    aria-hidden
  />
);
export const Hotspot = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="1.600" fill={F} stroke="none" />
    <path d="M8.200 8.200a5.400 5.400 0 0 0 0 7.600M15.800 8.200a5.400 5.400 0 0 1 0 7.600M5.400 5.400a9.400 9.400 0 0 0 0 13.200M18.600 5.400a9.400 9.400 0 0 1 0 13.200" />
  </Svg>
);
export const Wifi = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3 9.500a13 13 0 0 1 18 0M6 13a9 9 0 0 1 12 0M9.200 16.400a4.400 4.400 0 0 1 5.600 0" />
    <path d="M12 19.800h.01" strokeWidth={2.600} />
  </Svg>
);
export const Pin = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 21s6.500-5.800 6.500-11A6.500 6.500 0 0 0 5.500 10C5.500 15.200 12 21 12 21z" />
    <circle cx="12" cy="10" r="2.200" />
  </Svg>
);
export const Battery = (p: IconProps) => (
  <Svg {...p}>
    <rect x="3" y="7.500" width="16" height="9" rx="2.200" />
    <path d="M21 10.500v3" strokeWidth={2.200} />
  </Svg>
);
export const Note = (p: IconProps) => (
  <Svg {...p}>
    <path d="M9 17.500V6.200l9-2v11.300" />
    <circle cx="6.800" cy="17.500" r="2.200" fill={F} stroke="none" />
    <circle cx="15.800" cy="15.500" r="2.200" fill={F} stroke="none" />
  </Svg>
);
export const Sun = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 3v2.400M12 18.600V21M3 12h2.400M18.600 12H21M5.600 5.600l1.700 1.700M16.700 16.700l1.700 1.700M18.400 5.600l-1.700 1.700M7.300 16.700l-1.700 1.700" />
  </Svg>
);

/* ------------------------------------------------------------------- home */
export const NavArrow = (p: IconProps) => (
  <Svg {...p}>
    <path d="M21 3L3.600 10.400l7 2.400 2.400 7z" fill={F} />
  </Svg>
);
export const ChargeStation = (p: IconProps) => (
  <Svg {...p}>
    <rect x="4.500" y="3.500" width="9" height="17" rx="2" />
    <path d="M13.500 9H17a1.500 1.500 0 0 1 1.500 1.500v6a1.500 1.500 0 0 0 3 0V8l-2-2.500M9.300 8.800L7.600 12h3l-.9 3.400" />
  </Svg>
);
export const CarSide = (p: IconProps) => (
  <Svg {...p} sw={1.5}>
    <path d="M2.400 14.600c0-1.300.8-2 2-2.300l2.400-.6 2.600-3a3 3 0 0 1 2.100-1h5.300c1.400 0 2.600.8 3.100 2.100l.5 1.400c1.300.4 2.100 1.300 2.100 2.600v1.600h-2.500a2.700 2.700 0 0 0-5.300 0H9.600a2.700 2.700 0 0 0-5.300 0H2.400z" />
    <circle cx="7" cy="16" r="1.500" />
    <circle cx="17" cy="16" r="1.500" />
  </Svg>
);
export const Lock = (p: IconProps) => (
  <Svg {...p}>
    <rect x="5.500" y="10.500" width="13" height="9.500" rx="2.600" />
    <path d="M8.600 10.500V8a3.400 3.400 0 0 1 6.800 0v2.500" />
  </Svg>
);
export const Unlock = (p: IconProps) => (
  <Svg {...p}>
    <rect x="5.500" y="10.500" width="13" height="9.500" rx="2.600" />
    <path d="M8.600 10.500V8a3.400 3.400 0 0 1 6.600-1.200" />
  </Svg>
);
export const Trunk = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3.800 15.500l1.400-4.600a2 2 0 0 1 1.900-1.400h9.600l3.500 2.400v3.600z" />
    <circle cx="7.800" cy="16.700" r="1.500" />
    <circle cx="16.800" cy="16.700" r="1.500" />
  </Svg>
);
export const PhoneHandset = (p: IconProps) => (
  <Svg {...p}>
    <path d="M6.600 4.200l2.700-.7 1.700 4-1.800 1.600a11 11 0 0 0 5.700 5.700l1.600-1.800 4 1.700-.7 2.700a2.600 2.600 0 0 1-2.700 1.900A15.600 15.600 0 0 1 4.700 6.900a2.600 2.600 0 0 1 1.900-2.700z" fill={F} stroke="none" />
  </Svg>
);
export const Clock = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8.500" />
    <path d="M12 7.500V12l3 2" />
  </Svg>
);
export const MissedCall = (p: IconProps) => (
  <Svg {...p}>
    <path d="M6.600 4.200l2.700-.7 1.700 4-1.800 1.600a11 11 0 0 0 5.700 5.700l1.600-1.800 4 1.700-.7 2.700a2.600 2.600 0 0 1-2.700 1.900A15.600 15.600 0 0 1 4.700 6.900a2.600 2.600 0 0 1 1.900-2.700z" />
    <path d="M15 4l5 5M20 4.500V9h-4.500" strokeWidth={1.500} />
  </Svg>
);
export const Star = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 3.500l2.600 5.400 5.900.8-4.300 4.100 1 5.800L12 16.800l-5.200 2.800 1-5.800-4.300-4.100 5.900-.8z" />
  </Svg>
);

/* ------------------------------------------------------------ settings menu */
export const MenuDilink = (p: IconProps) => (
  <Svg {...p}>
    <path d="M6 7.500h8a4.500 4.500 0 0 1 0 9H8" />
    <path d="M9 4.500L6 7.500l3 3" />
  </Svg>
);
export const MenuPilot = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8.500" />
    <path d="M7.500 15.500l4.500-8 4.500 8M9.500 12.800h5" />
  </Svg>
);
export const MenuEnergy = (p: IconProps) => (
  <Svg {...p}>
    <rect x="3" y="7" width="15.500" height="10" rx="2.200" />
    <path d="M20.500 10.500v3M8 12h4M10 10v4" />
  </Svg>
);
export const MenuCar = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3 15.500l1.500-4.800A2.600 2.600 0 0 1 7 8.800h10a2.600 2.600 0 0 1 2.500 1.900L21 15.500V19h-3.500v-1.600h-11V19H3z" />
    <path d="M7.200 13.200h.01M16.800 13.200h.01" strokeWidth={2.600} />
  </Svg>
);
export const MenuHealth = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 20s-8-4.800-8-10.800A4.500 4.500 0 0 1 12 6.800 4.500 4.500 0 0 1 20 9.200C20 15.200 12 20 12 20z" />
    <path d="M8 11.500h2l1.200-2 1.600 3.500 1.200-1.500H16" strokeWidth={1.400} />
  </Svg>
);
export const MenuSearch = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="11" cy="11" r="6.500" />
    <path d="M16 16l4.500 4.500" />
  </Svg>
);

/* ----------------------------------------------------------------- misc */
export const Mic = (p: IconProps) => (
  <Svg {...p}>
    <rect x="9" y="3.500" width="6" height="11" rx="3" />
    <path d="M5.500 11.500a6.500 6.500 0 0 0 13 0M12 18v3" />
  </Svg>
);
export const Close = (p: IconProps) => (
  <Svg {...p}>
    <path d="M6 6l12 12M18 6L6 18" />
  </Svg>
);
export const Plus = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 5v14M5 12h14" />
  </Svg>
);
export const Dots = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="6" cy="12" r="1.500" fill={F} stroke="none" />
    <circle cx="12" cy="12" r="1.500" fill={F} stroke="none" />
    <circle cx="18" cy="12" r="1.500" fill={F} stroke="none" />
  </Svg>
);
export const Windows4 = (p: IconProps) => (
  <Svg {...p}>
    <rect x="3.500" y="6" width="17" height="12" rx="2.400" />
    <path d="M12 6v12M3.500 12h17" />
  </Svg>
);
export const Bulb = (p: IconProps) => (
  <Svg {...p}>
    <path d="M9 17.500h6M10 20h4M12 3.800a5.600 5.600 0 0 0-3.400 10c.6.500.9 1.100.9 1.700h5c0-.6.300-1.200.9-1.700a5.600 5.600 0 0 0-3.400-10z" />
  </Svg>
);
export const SeatSilhouette = (p: IconProps) => (
  <Svg {...p}>
    <path d="M9 3.500c1.800 0 2.800 1.200 3.100 3L14 14.500h5a2.200 2.200 0 0 1 2.200 2V19H8.500" />
    <path d="M6.500 19.500h14" />
  </Svg>
);
