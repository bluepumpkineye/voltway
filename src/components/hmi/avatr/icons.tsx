import React from 'react';

/**
 * The Avatr skin's own line icons, drawn here in the car's style (thin round strokes on a 24 grid); the
 * rest come from the HarmonyOS skin's set. They are not the maker's artwork: the shapes follow the
 * photographs of the screen (blender/reference/avatr-06t/hmi), nothing is copied.
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

/* ---------------------------------------------------------------- status bar */
export const User = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="8.500" r="3.600" fill={F} stroke="none" />
    <path d="M4.800 20c.6-4 3.300-6 7.200-6s6.600 2 7.200 6z" fill={F} stroke="none" />
  </Svg>
);
export const WeatherAlert = (p: IconProps) => (
  <Svg {...p}>
    <path d="M7.500 18.500a4 4 0 0 1-.6-7.900A5.600 5.600 0 0 1 17.600 9a4.800 4.800 0 0 1-.1 9.500z" />
    <path d="M12 10.800v3M12 16.200h.01" strokeWidth={2.100} />
  </Svg>
);
export const LockOpen = (p: IconProps) => (
  <Svg {...p}>
    <rect x="5.500" y="10.500" width="13" height="9.500" rx="2.600" />
    <path d="M8.600 10.500V8a3.400 3.400 0 0 1 6.600-1.200" />
  </Svg>
);
export const LockShut = (p: IconProps) => (
  <Svg {...p}>
    <rect x="5.500" y="10.500" width="13" height="9.500" rx="2.600" />
    <path d="M8.600 10.500V8a3.400 3.400 0 0 1 6.800 0v2.500" />
  </Svg>
);
export const ShieldTick = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 3l7 3v5.200c0 4.700-3 7.800-7 9.800-4-2-7-5.100-7-9.800V6z" />
    <circle cx="12" cy="11.500" r="2" fill={F} stroke="none" />
  </Svg>
);
export const CamRing = (p: IconProps) => (
  <Svg {...p}>
    <path d="M20.500 12A8.500 8.500 0 1 1 15 4" />
    <circle cx="12" cy="12" r="2.800" />
    <circle cx="19" cy="5.500" r="1.600" fill={F} stroke="none" />
  </Svg>
);
export const WifiOff = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3 9.500a13 13 0 0 1 18 0M6 13a9 9 0 0 1 12 0M9.200 16.400a4.400 4.400 0 0 1 5.600 0" />
    <path d="M12 19.800h.01" strokeWidth={2.600} />
    <path d="M4 4l16 16" />
  </Svg>
);

/* ------------------------------------------------------------ the bottom bar */
export const Home = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3.600 11.200L12 4l8.400 7.200V19a1 1 0 0 1-1 1h-4.200v-5.400H8.800V20H4.600a1 1 0 0 1-1-1z" fill={F} />
  </Svg>
);
export const Grid = (p: IconProps) => (
  <Svg {...p} sw={1.8}>
    <rect x="4" y="4" width="6.500" height="6.500" rx="1.800" />
    <rect x="13.500" y="4" width="6.500" height="6.500" rx="1.800" />
    <rect x="4" y="13.500" width="6.500" height="6.500" rx="1.800" />
    <rect x="13.500" y="13.500" width="6.500" height="6.500" rx="1.800" />
  </Svg>
);
export const Gear = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="3" />
    <path d="M12 3.500l1.500 2.200 2.600-.7.700 2.600 2.600.9-.9 2.600 1.400 2.300-2.200 1.600-.2 2.700-2.700.2-1.500 2.200-2.500-1-2.500 1-1.500-2.200-2.700-.2-.2-2.700-2.200-1.600 1.400-2.300-.9-2.600 2.600-.9.7-2.600 2.600.7z" strokeWidth={1.500} />
  </Svg>
);
export const Ads = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 6.800l4.600 8.400H7.400z" />
    <circle cx="12" cy="12.600" r="1.100" fill={F} stroke="none" />
  </Svg>
);
export const Cam360 = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4.500 8.200A9 4 0 0 1 12 5.500c4.900 0 8.800 1.200 8.800 3.700" />
    <path d="M19.200 6.300l1.700 2.700-3 .6" />
    <text x="12" y="19.200" textAnchor="middle" fontSize="9.500" fontWeight="700" fill={F} stroke="none" fontFamily="inherit">360</text>
  </Svg>
);
export const CarOutline = (p: IconProps) => (
  <Svg {...p} sw={1.6}>
    <path d="M2.600 14.800c0-1.300.8-2 2-2.300l2.400-.6 2.700-3a3 3 0 0 1 2.100-1h5.300c1.400 0 2.600.8 3.100 2.100l.5 1.400c1.300.4 2.100 1.300 2.100 2.600v1.400h-2.500a2.700 2.700 0 0 0-5.300 0H9.800a2.700 2.700 0 0 0-5.300 0H2.600z" />
    <circle cx="7.100" cy="16.100" r="1.600" />
    <circle cx="17.200" cy="16.100" r="1.600" />
    <path d="M9.400 9h4.400l1 2.900h-6z" />
  </Svg>
);
export const DefrostRear = (p: IconProps) => (
  <Svg {...p}>
    <path d="M5 18l1.200-9a2 2 0 0 1 2-1.600h7.600a2 2 0 0 1 2 1.600L19 18z" />
    <path d="M9 11.200c1-.8 1 1 2 .2s1-1 2-.2 1-.8 2 .2M9 14.200c1-.8 1 1 2 .2s1-1 2-.2 1-.8 2 .2" strokeWidth={1.400} />
  </Svg>
);
export const WheelHeat = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="13" r="7.400" />
    <path d="M4.800 12.200c2 .8 4 1.100 7.200 1.100s5.200-.3 7.200-1.100M12 13.300v7" />
    <path d="M9.600 3.200c-.8.8-.8 1.500 0 2.200M12 2.600c-.8.9-.8 1.700 0 2.600M14.400 3.200c-.8.8-.8 1.500 0 2.200" strokeWidth={1.300} />
  </Svg>
);
export const WheelHeatOn = WheelHeat;

/* ----------------------------------------------------------- control panel */
export const Charge = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12.800 6.500L8.600 12.800h3l-.6 4.700 4.400-6.600h-3.200z" fill={F} stroke="none" />
  </Svg>
);
export const WindowVent = (p: IconProps) => (
  <Svg {...p}>
    <path d="M5 18V8.500a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2V18z" />
    <path d="M5 11h14M9 14.400c1-.8 1 .8 2 0s1-.8 2 0 1 .8 2 0" strokeWidth={1.400} />
  </Svg>
);
export const FogRear = (p: IconProps) => (
  <Svg {...p}>
    <path d="M10 7.500a5 5 0 0 1 0 9" />
    <path d="M4.500 8.500h4M4 12h4.500M4.500 15.500h4M14.200 8.500h5M14.200 12h5.800M14.200 15.500h5" />
  </Svg>
);
export const ScreenClean = (p: IconProps) => (
  <Svg {...p}>
    <rect x="4" y="5" width="16" height="11.500" rx="2" />
    <path d="M9 19.500h6M14.500 8l.8 1.600 1.700.4-1.300 1.200.3 1.800-1.500-.9-1.500.9.300-1.800L12 10l1.700-.4z" strokeWidth={1.300} />
  </Svg>
);
export const PowerOff = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 3.800v8M7.200 7.500a7.400 7.400 0 1 0 9.600 0" />
  </Svg>
);
export const AutoHoldA = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8.200" />
    <path d="M8.800 15.500L12 8l3.200 7.500M9.900 13.200h4.200" strokeWidth={1.800} />
  </Svg>
);
export const ParkP = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8.200" />
    <path d="M10 16.500V8h2.800a2.400 2.400 0 0 1 0 4.800H10" strokeWidth={1.800} />
  </Svg>
);
export const Trunk = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3.800 15.500l1.400-4.600a2 2 0 0 1 1.900-1.400h9.600l3.500 2.400v3.600z" />
    <circle cx="7.800" cy="16.700" r="1.500" />
    <circle cx="16.800" cy="16.700" r="1.500" />
    <path d="M7.600 6.200l5.600-1.700" />
  </Svg>
);
export const Brightness = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="4.200" fill={F} stroke="none" />
    <path d="M12 3v2.400M12 18.600V21M3 12h2.400M18.600 12H21M5.600 5.600l1.700 1.700M16.700 16.700l1.700 1.700M18.400 5.600l-1.700 1.700M7.300 16.700l-1.700 1.700" />
  </Svg>
);
export const Headlamp = (p: IconProps) => (
  <Svg {...p}>
    <path d="M10.500 6.500a6 6 0 0 0 0 11 2 2 0 0 0 2.500-2V8.500a2 2 0 0 0-2.500-2z" />
    <path d="M16 8.500h4.500M16 12h4.500M16 15.500h4.500" />
  </Svg>
);
export const HeadrestMode = (p: IconProps) => (
  <Svg {...p}>
    <path d="M8 4h8a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2h-1.500v3H9.500v-3H8a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z" />
    <path d="M9.500 6.800v4.200M12 6.800v4.200M14.500 6.800v4.200" strokeWidth={1.300} />
  </Svg>
);
export const AlertTone = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="9.500" cy="9" r="3.200" />
    <path d="M3.600 19c.6-3.400 2.600-5 5.900-5s5.300 1.600 5.900 5z" />
    <path d="M16.500 7.200v2.800M16.500 12.600h.01" strokeWidth={2} />
  </Svg>
);
export const DoorGlyph = (p: IconProps) => (
  <Svg {...p}>
    <path d="M8 3.500h6.500a2 2 0 0 1 2 2V19a1.500 1.500 0 0 1-1.500 1.500H8z" />
    <path d="M8 3.500v17M13.800 12.500h1.200" />
  </Svg>
);
export const SmartLife = (p: IconProps) => (
  <Svg {...p} sw={1.8}>
    <path d="M6.500 4.500v15M17.500 4.500v15M6.500 12h11" />
  </Svg>
);

/* -------------------------------------------------------------- settings menu */
export const MenuVehicle = (p: IconProps) => (
  <Svg {...p}>
    <rect x="3.500" y="5" width="17" height="5.200" rx="2.600" fill={F} stroke="none" />
    <rect x="3.500" y="13.800" width="17" height="5.200" rx="2.600" fill={F} stroke="none" />
    <circle cx="16.800" cy="7.600" r="1.100" fill="#fff" stroke="none" />
  </Svg>
);
export const MenuDriving = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3 15.500l1.600-5a2.600 2.600 0 0 1 2.500-1.800h9.800a2.600 2.600 0 0 1 2.500 1.800l1.600 5V19H18v-1.700H6V19H3z" fill={F} stroke="none" />
    <circle cx="7.300" cy="13.400" r="1.200" fill="#fff" stroke="none" />
    <circle cx="16.700" cy="13.400" r="1.200" fill="#fff" stroke="none" />
  </Svg>
);
export const MenuSound = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 9.500h3.200L11.500 6v12L7.200 14.500H4z" fill={F} stroke="none" />
    <path d="M14.500 9a4.400 4.400 0 0 1 0 6M17 6.600a8 8 0 0 1 0 10.800" />
  </Svg>
);
export const MenuLights = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="3.800" fill={F} stroke="none" />
    <path d="M12 3.500v2.600M12 17.900v2.600M3.500 12h2.600M17.900 12h2.600M6 6l1.800 1.800M16.200 16.200L18 18M18 6l-1.800 1.800M7.800 16.200L6 18" />
  </Svg>
);
export const MenuEnergy = (p: IconProps) => (
  <Svg {...p}>
    <rect x="2.800" y="7.500" width="16" height="9" rx="2.600" fill={F} stroke="none" />
    <path d="M20.600 10.500v3" strokeWidth={2.200} />
  </Svg>
);
export const MenuAssist = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 6.800l4.600 8.400H7.400z" />
    <circle cx="12" cy="12.600" r="1.100" fill={F} stroke="none" />
  </Svg>
);
export const MenuScenes = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 3.500l7.500 4.200v8.600L12 20.500l-7.500-4.200V7.700z" fill={F} stroke="none" />
    <path d="M4.500 7.700L12 12l7.500-4.300M12 12v8.500" stroke="#fff" strokeWidth={1.200} />
  </Svg>
);
export const MenuDisplay = (p: IconProps) => (
  <Svg {...p}>
    <rect x="3.500" y="4.500" width="17" height="15" rx="3.200" fill={F} stroke="none" />
    <path d="M8.500 15l3-5 2 3 1.500-2" stroke="#fff" strokeWidth={1.400} />
  </Svg>
);
export const MenuLink = (p: IconProps) => (
  <Svg {...p}>
    <path d="M10 14a4 4 0 0 0 5.700 0l3-3a4 4 0 0 0-5.700-5.700l-1 1M14 10a4 4 0 0 0-5.700 0l-3 3a4 4 0 0 0 5.700 5.700l1-1" />
  </Svg>
);
export const MenuAssistant = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="9" fill={F} stroke="none" />
    <path d="M7.200 12a4.800 4.800 0 0 1 9.600 0" stroke="#fff" strokeWidth={1.500} />
    <circle cx="9.200" cy="13" r="1" fill="#fff" stroke="none" />
    <circle cx="14.800" cy="13" r="1" fill="#fff" stroke="none" />
  </Svg>
);
export const MenuStatus = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8.800" />
    <path d="M3 12h4l2-4 3.500 8 2-4H21" />
  </Svg>
);
export const MenuSystem = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="3.200" fill={F} stroke="none" />
    <path d="M12 2.800l1.800 2.400 2.900-.7.800 2.900 2.900.9-1 2.800 1.600 2.500-2.400 1.700-.2 3-3 .2-1.700 2.400L12 19.800l-2.800 1.100-1.700-2.400-3-.2-.2-3L2 13.600l1.600-2.500-1-2.800 2.900-.9.800-2.900 2.900.7z" strokeWidth={1.300} />
  </Svg>
);

/* ------------------------------------------------------------------- misc */
export const Leaf = (p: IconProps) => (
  <Svg {...p}>
    <path d="M5 19c0-8 4-13 14-14 0 9-4 13-12 13M5 19c2-4 5-7 9-9" />
  </Svg>
);
export const Compare = (p: IconProps) => (
  <Svg {...p}>
    <rect x="4" y="6" width="7" height="12" rx="1.800" />
    <rect x="13" y="6" width="7" height="12" rx="1.800" />
  </Svg>
);
export const Bulb = (p: IconProps) => (
  <Svg {...p}>
    <path d="M9 17.500h6M10 20h4M12 3.800a5.600 5.600 0 0 0-3.400 10c.6.500.9 1.100.9 1.700h5c0-.6.300-1.200.9-1.700a5.600 5.600 0 0 0-3.400-10z" />
  </Svg>
);
export const Phone = (p: IconProps) => (
  <Svg {...p}>
    <path d="M6.600 4.200l2.700-.7 1.700 4-1.800 1.600a11 11 0 0 0 5.700 5.700l1.600-1.800 4 1.700-.7 2.700a2.600 2.600 0 0 1-2.700 1.900A15.600 15.600 0 0 1 4.700 6.900a2.600 2.600 0 0 1 1.900-2.700z" fill={F} stroke="none" />
  </Svg>
);
