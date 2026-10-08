import React from 'react';

/**
 * The HarmonyOS skin's line icons, drawn here in the car's style (thin round
 * strokes on a 24 grid). They are not the maker's artwork: the shapes follow the
 * photographs of the screens, nothing is copied.
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
  sw = 1.7,
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

/* ---------------------------------------------------------------- status bar */
export const Message = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 5.5h16v10.5H10.5L6.5 19.5V16H4z" />
    <path d="M8.5 10.7h.01M12 10.7h.01M15.5 10.7h.01" strokeWidth={2.4} />
  </Svg>
);
export const Shield = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 3l7 3v5.2c0 4.7-3 7.8-7 9.8-4-2-7-5.100-7-9.800V6z" />
  </Svg>
);
export const RingGear = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8" />
    <circle cx="12" cy="12" r="2.6" />
  </Svg>
);
export const Dashcam = (p: IconProps) => (
  <Svg {...p}>
    <rect x="3" y="6" width="14" height="12" rx="2.5" />
    <path d="M17 10.2l4-2v7.600l-4-2" />
    <path d="M10 9.500v3.500M10 15.200h.01" />
  </Svg>
);
export const Vibrate = (p: IconProps) => (
  <Svg {...p}>
    <rect x="8.500" y="5" width="7" height="14" rx="2" />
    <path d="M5.500 8.500v7M3 10.500v3M18.500 8.500v7M21 10.500v3" />
  </Svg>
);
export const Bluetooth = (p: IconProps) => (
  <Svg {...p}>
    <path d="M7 7.500l10 9-5 4.500V3l5 4.500-10 9" />
  </Svg>
);
export const Signal = (p: IconProps) => (
  <Svg {...p} sw={2.2}>
    <path d="M5 19v-2.500M9.500 19v-6M14 19v-9M18.500 19V5" />
  </Svg>
);
export const Cloud = (p: IconProps) => (
  <Svg {...p}>
    <path d="M7.500 18.500a4 4 0 0 1-.6-7.900A5.600 5.600 0 0 1 17.600 9a4.800 4.800 0 0 1-.1 9.500z" />
  </Svg>
);

/* ------------------------------------------------------------ the bottom bar */
export const Voice = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="9.200" fill={F} stroke="none" />
    <path d="M8.200 10.500v3M10.700 8.500v7M13.300 9.500v5M15.800 10.800v2.400" stroke="var(--ha-voice-bars, #0d0e12)" strokeWidth={1.900} />
  </Svg>
);
export const CarFront = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4.500 15.500l1.800-5.200A3 3 0 0 1 9.100 8.200h5.800a3 3 0 0 1 2.800 2.100l1.800 5.200" />
    <path d="M3.500 15.500h17v3.500h-3.200v-1.800H6.700V19H3.500z" fill={F} />
    <path d="M7.800 12.600h.01M16.200 12.600h.01" strokeWidth={2.600} />
  </Svg>
);
export const Apps = (p: IconProps) => (
  <Svg {...p} sw={0}>
    <rect x="4" y="4" width="7" height="7" rx="2.200" fill={F} />
    <rect x="13" y="4" width="7" height="7" rx="2.200" fill={F} />
    <rect x="4" y="13" width="7" height="7" rx="2.200" fill={F} />
    <rect x="13" y="13" width="7" height="7" rx="2.200" fill={F} />
  </Svg>
);
export const NavRing = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="9.500" />
    <path d="M12 5.800l4.600 11-4.600-2.600-4.600 2.600z" />
  </Svg>
);
export const Fan = (p: IconProps) => (
  <Svg {...p} sw={0}>
    {[0, 120, 240].map((a) => (
      <path key={a} transform={`rotate(${a} 12 12)`} d="M12 12.200c-1.200-3.600-.6-6.800 2-8.700 1.600 2.900 1 6.200-2 8.700z" fill={F} />
    ))}
    <circle cx="12" cy="12" r="1.800" fill={F} />
  </Svg>
);
export const SeatHeat = (p: IconProps) => (
  <Svg {...p}>
    <path d="M7.500 3.500l1.700 11.500H18a2.500 2.500 0 0 1 2.500 2.500v1.500H8.500" />
    <path d="M5.500 20h15" />
  </Svg>
);
export const SeatHeatR = (p: IconProps) => (
  <Svg {...p} style={{ transform: 'scaleX(-1)', ...p.style }}>
    <path d="M7.500 3.500l1.700 11.500H18a2.500 2.500 0 0 1 2.500 2.500v1.500H8.500" />
    <path d="M5.500 20h15" />
  </Svg>
);
export const Music = (p: IconProps) => (
  <Svg {...p}>
    <path d="M9 17.500V6l10-2v11.500" />
    <circle cx="6.500" cy="17.500" r="2.600" fill={F} />
    <circle cx="16.500" cy="15.500" r="2.600" fill={F} />
  </Svg>
);
export const CarSide = (p: IconProps) => (
  <Svg {...p}>
    <path d="M2.500 15c0-2 1.100-3.100 3.200-3.500L9 8.500h6l3.300 3c2 .4 3.200 1.500 3.200 3.500v2h-2.600a2.600 2.600 0 0 0-5.200 0H10.300a2.600 2.600 0 0 0-5.200 0H2.500z" fill={F} />
  </Svg>
);
export const CarBeam = (p: IconProps) => (
  <Svg {...p}>
    <path d="M9.500 15c0-1.600.8-2.600 2.300-2.900l2.200-2.400h4.200l2.300 2.400c1.500.3 2.300 1.300 2.300 2.900v1.600h-1.800a1.900 1.900 0 0 0-3.800 0h-3.800a1.900 1.900 0 0 0-3.800 0H9.500z" fill={F} />
    <path d="M2 10.200l5 1M2 13.600h5M2 17l5-1" />
  </Svg>
);
export const Defrost = (p: IconProps) => (
  <Svg {...p}>
    <path d="M5 6.500h14l2 9.500H3z" />
    <path d="M8.500 9c1.300 1.100-1.300 2.100 0 3.200s-1.300 2.100 0 3.200M12 9c1.300 1.100-1.300 2.100 0 3.200s-1.300 2.100 0 3.200M15.500 9c1.300 1.100-1.300 2.100 0 3.200s-1.300 2.100 0 3.200" />
  </Svg>
);
export const Volume = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 9.500h3.600L13 5v14l-5.400-4.500H4z" fill={F} />
    <path d="M16 9.200c1.700 1.700 1.700 4.900 0 6.600M18.800 6.600c3.200 3.200 3.200 8.600 0 11.800" />
  </Svg>
);
export const Chev = ({ dir = 'r', ...p }: IconProps & { dir?: 'l' | 'r' | 'u' | 'd' }) => {
  const d = { l: 'M15 5.500L8.500 12l6.500 6.500z', r: 'M9 5.500l6.500 6.500L9 18.500z', u: 'M5.500 15L12 8.500l6.500 6.500z', d: 'M5.500 9L12 15.500 18.500 9z' }[dir];
  return (
    <Svg {...p} sw={0}>
      <path d={d} fill={F} />
    </Svg>
  );
};
export const ChevThin = ({ dir = 'r', ...p }: IconProps & { dir?: 'l' | 'r' | 'u' | 'd' }) => {
  const d = { l: 'M15 5l-7 7 7 7', r: 'M9 5l7 7-7 7', u: 'M5 15l7-7 7 7', d: 'M5 9l7 7 7-7' }[dir];
  return (
    <Svg {...p} sw={p.sw ?? 2}>
      <path d={d} />
    </Svg>
  );
};
export const Close = (p: IconProps) => (
  <Svg {...p} sw={p.sw ?? 1.9}>
    <path d="M6 6l12 12M18 6L6 18" />
  </Svg>
);

/* --------------------------------------------------------------- card icons */
export const ChargePort = (p: IconProps) => (
  <Svg {...p}>
    <path d="M7.500 3.500v4M12 3.500v4M5.500 7.500h8.200v2.600a4.100 4.100 0 0 1-4.100 4.100H9.600a4.100 4.100 0 0 1-4.100-4.100z" />
    <path d="M9.600 14.200V17a3 3 0 0 0 3 3h5.400" />
  </Svg>
);
export const WindowOpen = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3 15.500c0-3.500 2.200-6 5.500-6h7l5 4v4H3z" />
    <path d="M8.500 9.500v4.200h11" />
  </Svg>
);
export const TrunkRear = (p: IconProps) => (
  <Svg {...p}>
    <path d="M6 18v-5.500l1.800-3h8.400l1.800 3V18M4.500 18h15M7 9.500L5.500 5.500h13L17 9.500" />
    <path d="M8 14h8" />
  </Svg>
);
export const TrunkFront = (p: IconProps) => (
  <Svg {...p}>
    <path d="M5 18v-4l2.200-3.500a3 3 0 0 1 2.500-1.500h4.600a3 3 0 0 1 2.500 1.500L19 14v4zM4 18h16" />
    <path d="M8 11.500l-3-5h14l-3 5" />
  </Svg>
);
export const MirrorFold = (p: IconProps) => (
  <Svg {...p}>
    <path d="M5 8.500h9l3 3.500-3 3.500H5z" />
    <path d="M17.500 6l3 3-3 3" />
    <path d="M9 12h3" />
  </Svg>
);
export const MirrorAdj = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 9a2 2 0 0 1 2-2h8a4 4 0 0 1 4 4v1a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z" />
    <path d="M10 15v4h6" />
  </Svg>
);
export const HeatUp = (p: IconProps) => (
  <Svg {...p} sw={p.sw ?? 2}>
    <path d="M6 19V9.500M3.500 12L6 9.500 8.500 12M12 19V5M9.500 7.500L12 5l2.500 2.500M18 19V9.500M15.500 12L18 9.500 20.500 12" />
  </Svg>
);
export const HeatWave = (p: IconProps) => (
  <Svg {...p} sw={p.sw ?? 2}>
    <path d="M6.500 4c-2.200 2.300 2.200 4.700 0 8.200s2.200 4.200 0 7.800M12 4c-2.200 2.300 2.200 4.700 0 8.200s2.200 4.200 0 7.800M17.500 4c-2.200 2.300 2.200 4.700 0 8.200s2.200 4.200 0 7.800" />
  </Svg>
);

/* ------------------------------------------------------------ control centre */
export const Hill = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3 18.500l17-6.500M7 13.500l1.600-3.500h5.400l2.200 3" />
    <circle cx="8" cy="15.500" r="1.200" />
    <circle cx="14.500" cy="13.200" r="1.200" />
  </Svg>
);
export const BrightnessA = (p: IconProps) => (
  <Svg {...p} sw={p.sw ?? 1.5}>
    <circle cx="12" cy="12" r="5" />
    <path d="M12 2.500v2.300M12 19.200v2.300M2.500 12h2.300M19.200 12h2.300M5.300 5.300l1.600 1.600M17.100 17.100l1.600 1.600M18.700 5.300l-1.600 1.600M6.900 17.100l-1.600 1.600" />
    <path d="M10.200 14.300l1.800-4.700 1.800 4.700M10.800 12.900h2.400" strokeWidth={1.400} />
  </Svg>
);
export const ContrastMode = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8" />
    <path d="M12 4a8 8 0 0 1 0 16z" fill={F} />
  </Svg>
);
export const Headrest = (p: IconProps) => (
  <Svg {...p}>
    <path d="M9.500 3.500h5l1.500 6.500H8z" />
    <path d="M7 10l2 4.500h6L17 10M10.500 14.500V20M13.500 14.500V20" />
    <path d="M18 5.500c1 1 1 2.500 0 3.500" />
  </Svg>
);
export const Power = (p: IconProps) => (
  <Svg {...p} sw={p.sw ?? 1.9}>
    <path d="M12 3v8.500" />
    <path d="M7 6.200a8 8 0 1 0 10 0" />
  </Svg>
);
export const AutoHold = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8.500" />
    <circle cx="12" cy="12" r="5.200" />
    <path d="M10.200 14.500L12 9.500l1.800 5M10.800 13.200h2.400" strokeWidth={1.400} />
  </Svg>
);
export const LampPos = (p: IconProps) => (
  <Svg {...p}>
    <path d="M10 7h1.500a5 5 0 0 1 0 10H10z" />
    <path d="M4.500 8.800l3.500.5M4.500 12H8M4.500 15.200l3.500-.5" />
  </Svg>
);
export const LampLow = (p: IconProps) => (
  <Svg {...p}>
    <path d="M10 7h1.500a5 5 0 0 1 0 10H10z" />
    <path d="M4.500 8.800l3.800 1.600M4.500 12.200l3.800 1.200M4.500 15.600l3.800.8" />
  </Svg>
);
export const CarWash = (p: IconProps) => (
  <Svg {...p}>
    <path d="M5 16l1.600-4.600A2.600 2.600 0 0 1 9 9.500h6a2.600 2.600 0 0 1 2.400 1.900L19 16v3h-2.600v-1.500H7.600V19H5z" />
    <path d="M7 5.500h.01M12 4.500h.01M17 5.500h.01M9.500 7h.01M14.500 7h.01" strokeWidth={2.200} />
  </Svg>
);
export const Sentry = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 3l7 3v5.200c0 4.700-3 7.800-7 9.800-4-2-7-5.100-7-9.800V6z" />
    <circle cx="12" cy="11.500" r="2.800" />
    <circle cx="12" cy="11.500" r=".6" fill={F} />
  </Svg>
);
export const ChildLock = (p: IconProps) => (
  <Svg {...p}>
    <path d="M8.500 10.500V7.800a3.500 3.500 0 0 1 7 0v2.700" />
    <rect x="5.500" y="10.500" width="13" height="9.500" rx="2.200" />
    <path d="M12 14.200v2.400" />
  </Svg>
);
export const ParkAssist = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8.500" />
    <path d="M10 17V7.500h3.100a2.600 2.600 0 0 1 0 5.200H10" />
    <path d="M16.500 15.800l1.200-3 1.200 3M16.900 15h1.600" strokeWidth={1.100} />
  </Svg>
);
export const DoorLock = (p: IconProps) => (
  <Svg {...p}>
    <path d="M8.500 10.800V8a3.500 3.500 0 0 1 6.800-1.200" />
    <rect x="5.500" y="10.800" width="13" height="9.200" rx="2.200" />
    <path d="M12 14.400v2.400" />
  </Svg>
);
export const Nap = (p: IconProps) => (
  <Svg {...p}>
    <path d="M6 11.500A2.500 2.500 0 0 1 8.500 9h7a2.500 2.500 0 0 1 2.500 2.500V16H6z" />
    <path d="M3.500 12.500H6V17H3.500zM18 12.500h2.500V17H18zM7 17v2.500M17 17v2.500" />
  </Svg>
);
export const SeatPose = ({ n, ...p }: IconProps & { n: number }) => (
  <Svg {...p}>
    <path d="M7 3.500l1.800 10.500h7a2.700 2.700 0 0 1 2.700 2.700V19H8" />
    <path d="M5.500 19.500h14" />
    <path d={n === 1 ? 'M18.500 5.500v5' : n === 2 ? 'M17 6.500h3l-3 4h3' : 'M17 6h3l-1.500 2.200A1.700 1.700 0 1 1 17 10.800'} strokeWidth={1.500} />
  </Svg>
);
export const Sunshade = (p: IconProps) => (
  <Svg {...p}>
    <rect x="4.500" y="4" width="15" height="16" rx="2" />
    <path d="M4.500 10h15M12 10v4.500" />
  </Svg>
);
export const PassengerScreen = (p: IconProps) => (
  <Svg {...p}>
    <rect x="3.500" y="5" width="17" height="11" rx="2" />
    <path d="M9 19.500h6M12 16v3.500" />
    <path d="M12 8v3.500" strokeWidth={1.600} />
    <path d="M9.800 9.300a3 3 0 1 0 4.400 0" strokeWidth={1.400} />
  </Svg>
);
export const Leaf = (p: IconProps) => (
  <Svg {...p}>
    <path d="M5 19C5 10.500 10 5 19 5c0 9-5 14-14 14z" fill={F} />
    <path d="M5 19l8.500-8.500" stroke="var(--ha-leaf-vein, #0d0e12)" />
  </Svg>
);
export const Flag = (p: IconProps) => (
  <Svg {...p}>
    <path d="M6 21V4" />
    <path d="M6 5h12v8.500H6" />
    <path d="M10 5v8.500M14 5v8.500M6 9.200h12" />
  </Svg>
);
export const Rocket = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 3c3.200 2 4.700 5.200 4.200 9.200L14.200 15h-4.400l-2-2.800C7.300 8.200 8.800 5 12 3z" fill={F} />
    <path d="M9.800 15L8 19.500M14.200 15l1.800 4.500" />
    <circle cx="12" cy="8.800" r="1.100" stroke="var(--ha-leaf-vein, #0d0e12)" />
  </Svg>
);
export const Armchair = Nap;

/* ---------------------------------------------------------------- settings menu */
export const MenuVehicle = (p: IconProps) => (
  <Svg {...p} sw={0}>
    <rect x="4" y="5" width="16" height="6" rx="3" fill={F} />
    <rect x="4" y="13" width="16" height="6" rx="3" fill={F} />
    <circle cx="8" cy="8" r="1.700" fill="var(--ha-menu-knob, #e9e7ea)" />
    <circle cx="16" cy="16" r="1.700" fill="var(--ha-menu-knob, #e9e7ea)" />
  </Svg>
);
export const MenuLights = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="3.800" fill={F} />
    <path d="M12 3v2.600M12 18.400V21M3 12h2.600M18.400 12H21M5.600 5.600l1.800 1.800M16.600 16.600l1.800 1.800M18.400 5.600l-1.800 1.800M7.400 16.600l-1.800 1.800" />
  </Svg>
);
export const MenuEnergy = (p: IconProps) => (
  <Svg {...p} sw={0}>
    <rect x="3" y="7.500" width="16" height="9" rx="2.600" fill={F} />
    <rect x="19.500" y="10.500" width="2" height="3" rx="1" fill={F} />
  </Svg>
);
export const MenuDriving = (p: IconProps) => <CarFront {...p} />;
export const MenuAssist = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="9" />
    <circle cx="12" cy="11" r="3.300" />
    <path d="M7.500 17.500c1.200-2 2.800-2.800 4.500-2.800s3.300.8 4.500 2.800M12 7.700V6" />
  </Svg>
);
export const MenuStatus = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M5.500 12.500h3l1.700-3.500 2.600 7 1.800-3.500h3.400" />
  </Svg>
);
export const MenuScenes = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 3l8 4.500v9L12 21l-8-4.500v-9z" fill={F} />
    <path d="M12 12l8-4.500M12 12v9M12 12L4 7.500" stroke="var(--ha-menu-knob, #e9e7ea)" />
  </Svg>
);
export const MenuPersonal = (p: IconProps) => (
  <Svg {...p}>
    <rect x="3.500" y="4.500" width="17" height="15" rx="2.600" fill={F} />
    <path d="M4 16.500l5-5 4 4 3-3 4.500 4.500" stroke="var(--ha-menu-knob, #e9e7ea)" />
  </Svg>
);
export const MenuDisplay = (p: IconProps) => (
  <Svg {...p}>
    <rect x="3" y="4.500" width="18" height="12.500" rx="2.600" fill={F} />
    <path d="M9 20.500h6" />
    <path d="M9 13l2.200-2.700L13 12.300l2-2.300" stroke="var(--ha-menu-knob, #e9e7ea)" />
  </Svg>
);
export const MenuLink = (p: IconProps) => (
  <Svg {...p}>
    <path d="M10.200 13.800a3.800 3.800 0 0 0 5.400 0l3-3a3.800 3.800 0 0 0-5.400-5.400l-1 1" />
    <path d="M13.800 10.200a3.800 3.800 0 0 0-5.400 0l-3 3a3.800 3.800 0 0 0 5.400 5.400l1-1" />
  </Svg>
);
export const MenuSound = (p: IconProps) => <Volume {...p} />;
export const MenuAssistant = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="9" fill={F} />
    <path d="M8.300 10.800c1.800-1.500 5.600-1.500 7.400 0M8.800 14.400c1.500 1 4 1 5.400 0" stroke="var(--ha-menu-knob, #e9e7ea)" />
  </Svg>
);
export const MenuSystem = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="3.300" fill={F} />
    <path d="M12 2.500v3M12 18.500v3M2.500 12h3M18.500 12h3M5.200 5.200l2.100 2.100M16.700 16.700l2.100 2.100M18.800 5.200l-2.100 2.100M7.300 16.700l-2.100 2.100" />
    <circle cx="12" cy="12" r="6.500" />
  </Svg>
);

/* ----------------------------------------------------------- climate and media */
export const Recirc = (p: IconProps) => (
  <Svg {...p}>
    <path d="M3 15c0-2.200 1.200-3.500 3.200-3.800L9 8.500h6l3 2.700c1.800.3 3 1.600 3 3.800v2h-2.600" />
    <path d="M7 19l-2.800-2.200L7 14.600M4.300 16.800H11" />
  </Svg>
);
export const AirFace = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="9" cy="6" r="2.200" />
    <path d="M7 10.200l2 1.800v4.500M6 19l3-2.500M11 12.800l2.500.2M14 9.500c2 1 3.500 1 5 0M14.500 12.500c2 .7 3.500.7 4.500 0" />
  </Svg>
);
export const AirFeet = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="9" cy="5.500" r="2.200" />
    <path d="M7 9.500l2 1.800v4.200l-3 3.500M11 12.300l3 3.500M15 18.500l1.200-2M12.500 19l1.200-2M17.500 18l1.200-2" />
  </Svg>
);
export const AirBoth = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="8.500" cy="5.500" r="2.200" />
    <path d="M6.500 9.500l2 1.800v4.200l-3 3.500M10.500 12.300l2.500.5M13.500 9.300c2 .8 3.500.8 5 0M14 12c2 .6 3.500.6 4.500 0M13 16.500l1.400 2M16.500 16.500l1.400 2" />
  </Svg>
);
export const AirDefrost = (p: IconProps) => <Defrost {...p} />;
export const AcMax = (p: IconProps) => (
  <Svg {...p} sw={1.5}>
    <path d="M12 3v12M5.500 6.500l13 7M5.500 13.500l13-7" />
    <path d="M10 4.800L12 6.500l2-1.700M10 14.200L12 12.500l2 1.700" />
    <path d="M6 20v-2.600l1.400 1.400L8.800 17.400V20" strokeWidth={1.200} />
  </Svg>
);
export const SunMax = (p: IconProps) => (
  <Svg {...p} sw={1.5}>
    <circle cx="12" cy="10" r="3.600" />
    <path d="M12 3v1.800M12 15.200V17M5 10h1.800M17.200 10H19M7 5l1.300 1.300M15.700 13.700L17 15M17 5l-1.300 1.300M8.300 13.700L7 15" />
    <path d="M6 21v-3.200l1.700 1.900 1.700-1.900V21M12 21v-3h2a1.300 1.300 0 0 1 0 2.600H12M17 21l1.800-3 1.800 3" strokeWidth={1} />
  </Svg>
);
export const Heart = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 20s-8-4.800-8-10.800A4.500 4.500 0 0 1 12 6.800 4.500 4.500 0 0 1 20 9.200C20 15.200 12 20 12 20z" />
  </Svg>
);
export const Prev = (p: IconProps) => (
  <Svg {...p} sw={0}>
    <path d="M5 5h2.200v14H5zM19 5.500v13L9 12z" fill={F} />
  </Svg>
);
export const Next = (p: IconProps) => (
  <Svg {...p} sw={0}>
    <path d="M16.800 5H19v14h-2.200zM5 5.500v13L15 12z" fill={F} />
  </Svg>
);
export const Play = (p: IconProps) => (
  <Svg {...p} sw={0}>
    <path d="M7 4.500v15l13-7.500z" fill={F} />
  </Svg>
);
export const Pause = (p: IconProps) => (
  <Svg {...p} sw={0}>
    <rect x="6" y="4.500" width="4.400" height="15" rx="1.200" fill={F} />
    <rect x="13.600" y="4.500" width="4.400" height="15" rx="1.200" fill={F} />
  </Svg>
);
export const Timer = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="13" r="7.500" />
    <path d="M12 8.500V13l3 1.800M10 3.500h4" />
  </Svg>
);
export const MoreV = (p: IconProps) => (
  <Svg {...p} sw={0}>
    <circle cx="12" cy="5.500" r="1.700" fill={F} />
    <circle cx="12" cy="12" r="1.700" fill={F} />
    <circle cx="12" cy="18.500" r="1.700" fill={F} />
  </Svg>
);
export const Search = (p: IconProps) => (
  <Svg {...p} sw={p.sw ?? 1.9}>
    <circle cx="10.500" cy="10.500" r="6.500" />
    <path d="M15.500 15.500L20.500 20.500" />
  </Svg>
);
export const Shuffle = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 7h3.500c4 0 5 10 9 10H20M4 17h3.500c1.500 0 2.500-1.500 3.500-3M13 10c1-1.600 2-3 3.500-3H20M17.500 4.500L20 7l-2.500 2.500M17.500 14.500L20 17l-2.500 2.500" />
  </Svg>
);
export const Repeat = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 11V9.500A2.500 2.500 0 0 1 6.500 7H19M16.500 4l2.500 3-2.500 3M20 13v1.500a2.500 2.500 0 0 1-2.500 2.500H5M7.500 14L5 17l2.500 3" />
  </Svg>
);
export const Info = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8.500" />
    <path d="M12 11v5.500M12 7.800h.01" strokeWidth={2} />
  </Svg>
);
export const Pin = (p: IconProps) => (
  <Svg {...p}>
    <path d="M12 21s-6.500-5.800-6.500-11a6.500 6.500 0 0 1 13 0c0 5.200-6.500 11-6.500 11z" />
    <circle cx="12" cy="10" r="2.400" />
  </Svg>
);
export const Plus = (p: IconProps) => (
  <Svg {...p} sw={p.sw ?? 2}>
    <path d="M12 5v14M5 12h14" />
  </Svg>
);
export const Minus = (p: IconProps) => (
  <Svg {...p} sw={p.sw ?? 2}>
    <path d="M5 12h14" />
  </Svg>
);
export const Locate = (p: IconProps) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="6" />
    <circle cx="12" cy="12" r="1.800" fill={F} />
    <path d="M12 2.500v3M12 18.500v3M2.500 12h3M18.500 12h3" />
  </Svg>
);
export const Camera = (p: IconProps) => (
  <Svg {...p}>
    <path d="M4 8.500h3.200l1.600-2.500h6.400l1.600 2.500H20v10.500H4z" />
    <circle cx="12" cy="13.500" r="3.600" />
  </Svg>
);
export const Wallet = (p: IconProps) => (
  <Svg {...p}>
    <rect x="3" y="6" width="18" height="13" rx="2.500" />
    <path d="M3 10h18" />
  </Svg>
);
export const Check = (p: IconProps) => (
  <Svg {...p} sw={p.sw ?? 2.200}>
    <path d="M5 12.500l4.500 4.500L19 7.500" />
  </Svg>
);
