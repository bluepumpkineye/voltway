import React from 'react';

/**
 * The line icons of the phone app, drawn here on a 24 grid (the maker's own are its artwork):
 * round caps and joins, a 1.7 stroke, the colour of the text they sit in.
 */
type P = { size?: number; className?: string; style?: React.CSSProperties };

function Svg({ size = 22, className, style, children, fill = 'none' }: P & { children: React.ReactNode; fill?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={fill}
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      style={style}
      aria-hidden
    >
      {children}
    </svg>
  );
}

export const Back = (p: P) => (
  <Svg {...p}>
    <path d="M15 5l-7 7 7 7" />
  </Svg>
);
export const Chevron = (p: P) => (
  <Svg {...p}>
    <path d="M9 5l7 7-7 7" />
  </Svg>
);
export const Bell = (p: P) => (
  <Svg {...p}>
    <path d="M6 16v-5a6 6 0 0 1 12 0v5l1.6 2H4.4z" />
    <path d="M10 21a2 2 0 0 0 4 0" />
  </Svg>
);
export const Info = (p: P) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 11v5M12 7.6v.1" />
  </Svg>
);
export const Lock = (p: P) => (
  <Svg {...p}>
    <rect x="5" y="11" width="14" height="9" rx="2.4" />
    <path d="M8 11V8a4 4 0 0 1 8 0v3M12 15v2" />
  </Svg>
);
export const Boot = (p: P) => (
  <Svg {...p}>
    <path d="M3.5 17v-5l2.4-4.6h12.2L20.5 12v5z" />
    <path d="M3.5 12h17M7 17v2M17 17v2" />
  </Svg>
);
export const Window = (p: P) => (
  <Svg {...p}>
    <rect x="4" y="4.5" width="16" height="15" rx="2.4" />
    <path d="M12 8.5v6M9.2 12.2L12 15l2.8-2.8" />
  </Svg>
);
export const Horn = (p: P) => (
  <Svg {...p}>
    <path d="M4 10v4h3l5 4V6L7 10z" />
    <path d="M16 9.2a4 4 0 0 1 0 5.6M18.6 6.6a8 8 0 0 1 0 10.8" />
  </Svg>
);
export const Frunk = (p: P) => (
  <Svg {...p}>
    <path d="M3.5 17v-4l2-3.6h13l2 3.6v4z" />
    <path d="M7.5 9.4L10 5h5.6M3.5 13h17M7 17v2M17 17v2" />
  </Svg>
);
export const Fan = (p: P) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="1.8" />
    <path d="M12 10.2C11 6 12.5 3.6 15 4.4c2 .8 1 4-3 5.8zM13.8 12.9c4.3.6 5.7 3 4.2 5-1.2 1.6-4 .4-5.2-4zM10.2 12.9C9.4 17 7 18.2 5.2 16.5c-1.5-1.5.3-4 5-3.6z" />
  </Svg>
);
export const Pin = (p: P) => (
  <Svg {...p}>
    <path d="M12 21s-6-5.4-6-10.2a6 6 0 0 1 12 0C18 15.600 12 21 12 21z" />
    <circle cx="12" cy="10.8" r="2.2" />
  </Svg>
);
export const Bolt = (p: P) => (
  <Svg {...p}>
    <path d="M13 3L6 13h5l-1 8 7-10h-5z" />
  </Svg>
);
export const Key = (p: P) => (
  <Svg {...p}>
    <circle cx="7.600" cy="14.400" r="3.600" />
    <path d="M10.200 11.800L19 3M16 6l2.400 2.400M13.200 8.800l2 2" />
  </Svg>
);
/** remote parking: a car from above, in its bay, with the arrow that takes it there */
export const ParkCar = (p: P) => (
  <Svg {...p}>
    <rect x="9" y="3.500" width="6.400" height="11" rx="2.600" />
    <path d="M10.400 6.600h3.600M10.400 12h3.600" />
    <path d="M4 20h16M7 17.200v2.800M17.400 17.200v2.800" />
  </Svg>
);
export const Valet = (p: P) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8.500" />
    <circle cx="12" cy="12" r="2.200" />
    <path d="M12 9.800V3.600M9.900 13.100L4 15.200M14.100 13.100L20 15.200" />
  </Svg>
);
export const Eye = (p: P) => (
  <Svg {...p}>
    <path d="M2.500 12s3.700-6.500 9.500-6.500S21.500 12 21.500 12s-3.700 6.500-9.500 6.500S2.500 12 2.500 12z" />
    <circle cx="12" cy="12" r="2.800" />
  </Svg>
);
export const Power = (p: P) => (
  <Svg {...p}>
    <path d="M12 3.500v7.600M7.200 6.600a7.400 7.400 0 1 0 9.600 0" />
  </Svg>
);
export const Cooler = (p: P) => (
  <Svg {...p}>
    <rect x="5" y="4" width="14" height="16.500" rx="2.400" />
    <path d="M5 10h14M9.200 6.800v1M9.200 13v3" />
  </Svg>
);
export const CarCheck = (p: P) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8.800" />
    <path d="M8 12.200l2.800 2.800L16.400 9.200" />
  </Svg>
);
export const Check = (p: P) => (
  <Svg {...p}>
    <path d="M5 12.500l4.500 4.500L19 7.500" />
  </Svg>
);
export const Pause = (p: P) => (
  <Svg {...p} fill="currentColor">
    <path d="M7 5h3.400v14H7zM13.600 5H17v14h-3.400z" stroke="none" />
  </Svg>
);
export const Play = (p: P) => (
  <Svg {...p} fill="currentColor">
    <path d="M7.500 4.800v14.400a.8.8 0 0 0 1.200.7l11.500-7.200a.8.8 0 0 0 0-1.400L8.700 4.100a.8.8 0 0 0-1.200.7z" stroke="none" />
  </Svg>
);
export const Compass = (p: P) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8.500" />
    <path d="M15.600 8.400l-2 5.200-5.200 2 2-5.200z" />
  </Svg>
);
export const Bag = (p: P) => (
  <Svg {...p}>
    <path d="M5 8h14l-1 12H6z" />
    <path d="M9 8V6.600a3 3 0 0 1 6 0V8" />
  </Svg>
);
export const CarSide = (p: P) => (
  <Svg {...p}>
    <path d="M3 16.500v-3.200l2.200-4.100h9.600l3.600 3.600 2.600.9v2.800z" />
    <circle cx="7.800" cy="16.800" r="1.700" />
    <circle cx="16.800" cy="16.800" r="1.700" />
  </Svg>
);
export const Heart = (p: P) => (
  <Svg {...p}>
    <path d="M12 20S4 15 4 9.400C4 6.800 6 5 8.200 5c1.600 0 2.900.9 3.800 2.300C12.900 5.900 14.200 5 15.800 5 18 5 20 6.800 20 9.400 20 15 12 20 12 20z" />
  </Svg>
);
export const Person = (p: P) => (
  <Svg {...p}>
    <circle cx="12" cy="8.400" r="3.600" />
    <path d="M5 20c.8-3.800 3.700-5.800 7-5.800s6.200 2 7 5.800" />
  </Svg>
);
export const Signal = ({ size = 14 }: P) => (
  <svg width={size} height={size} viewBox="0 0 18 14" aria-hidden>
    {[0, 1, 2, 3].map((i) => (
      <rect key={i} x={i * 4.600} y={13 - (i + 1) * 3.100} width="3" height={(i + 1) * 3.100} rx="1" fill="currentColor" />
    ))}
  </svg>
);
export const Spinner = ({ size = 18 }: P) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden className="animate-spin">
    <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeOpacity="0.2" strokeWidth="3" />
    <path d="M21 12a9 9 0 0 0-9-9" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
  </svg>
);
