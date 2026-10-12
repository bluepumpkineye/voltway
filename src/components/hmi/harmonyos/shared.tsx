'use client';

import React from 'react';
import { LIGHT_MODES } from '@/lib/lights';
import { useVehicleStore } from '@/store/vehicle-store';

/* ------------------------------------------------------------------- clock */

export interface Now {
  hm: string;
  /** "Wed, Aug 19" */
  date: string;
}

const DAY = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/**
 * The time, ticking. Empty until mounted: the HMI is also server-rendered (the
 * capture route) and a server clock would not match the browser's.
 */
export function useNow(): Now {
  const [now, setNow] = React.useState<Date | null>(null);
  React.useEffect(() => {
    setNow(new Date());
    const id = window.setInterval(() => setNow(new Date()), 15_000);
    return () => window.clearInterval(id);
  }, []);
  if (!now) return { hm: '', date: '' };
  return {
    hm: `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`,
    date: `${DAY[now.getDay()]}, ${MON[now.getMonth()]} ${now.getDate()}`,
  };
}

/* ------------------------------------------------- local switches and toasts */

interface HaLocal {
  /** switches the showroom has no 3D or store state for (child lock, sentry mode ...) */
  on: Record<string, boolean>;
  toggle: (id: string, fallback?: boolean) => void;
  set: (id: string, v: boolean) => void;
  /** a number or a choice a control keeps (brightness, seat level ...) */
  val: Record<string, number>;
  setVal: (id: string, v: number) => void;
  /** a small message at the bottom of the screen, for things a showroom car cannot do */
  notify: (msg: string) => void;
}

const Ctx = React.createContext<HaLocal | null>(null);

const DEFAULTS: Record<string, boolean> = {
  autoHold: true,
  headrest: true,
  passengerScreen: true,
  hud: true,
  autoHighBeam: true,
  autoLowBeam: true,
  turnSignalOff: true,
  adaptiveBrightness: true,
  adaptiveBrightnessCluster: true,
  lyrics: true,
  batteryHealth: true,
};

const VALUES: Record<string, number> = {
  brightness: 100,
  clusterBrightness: 54,
  headlamp: 0, // 0 off, 1 position, 2 low beam, 3 auto: the store's lamp switch holds it (HaProvider)
  screenAim: 1, // 0 driver, 1 centre, 2 passenger
  wallpaper: -1, // the theme's own until the visitor switches it
  media: 0, // 0 music, 1 radio
  rideHeight: 2, // standard
  soundFx: 1, // concert hall
  dispMode: 1, // dark (the store's default)
  carrier: 0,
  rearL: 24,
  rearR: 24,
  station: 0,
};

export function HaProvider({ children }: { children: React.ReactNode }) {
  const [on, setOn] = React.useState<Record<string, boolean>>({});
  const [val, setValState] = React.useState<Record<string, number>>({});
  const [msg, setMsg] = React.useState<string | null>(null);
  const timer = React.useRef<number | undefined>(undefined);
  // the headlamp selector is the car's own lamp switch: the 3D car's lamps (and the Dashboard tab) follow it
  const lightMode = useVehicleStore((s) => s.lightMode);
  const setLightMode = useVehicleStore((s) => s.setLightMode);
  const lamp = Math.max(0, LIGHT_MODES.indexOf(lightMode));

  const api = React.useMemo<HaLocal>(
    () => ({
      on: new Proxy(on, { get: (t, k: string) => (k in t ? t[k] : DEFAULTS[k] ?? false) }),
      toggle: (id, fallback) =>
        setOn((s) => ({ ...s, [id]: !(id in s ? s[id] : fallback ?? DEFAULTS[id] ?? false) })),
      set: (id, v) => setOn((s) => ({ ...s, [id]: v })),
      val: new Proxy(val, { get: (t, k: string) => (k === 'headlamp' ? lamp : k in t ? t[k] : VALUES[k] ?? 0) }),
      setVal: (id, v) => (id === 'headlamp' ? setLightMode(LIGHT_MODES[v] ?? 'off') : setValState((s) => ({ ...s, [id]: v }))),
      notify: (m) => {
        setMsg(m);
        window.clearTimeout(timer.current);
        timer.current = window.setTimeout(() => setMsg(null), 1800);
      },
    }),
    [on, val, lamp, setLightMode],
  );

  return (
    <Ctx.Provider value={api}>
      {children}
      {msg && (
        <div
          role="status"
          className="pointer-events-none absolute bottom-[92px] left-1/2 z-[60] -translate-x-1/2 rounded-full px-6 py-3 text-[17px] text-white"
          style={{ background: 'rgba(20,20,24,0.88)', backdropFilter: 'blur(16px)' }}
        >
          {msg}
        </div>
      )}
    </Ctx.Provider>
  );
}

export function useHaLocal(): HaLocal {
  const v = React.useContext(Ctx);
  if (!v) throw new Error('HaProvider missing');
  return v;
}

/* --------------------------------------------------------------- wallpapers */

export type WallpaperId = 'sunset' | 'lake' | 'aurora';
export const WALLPAPERS: { id: WallpaperId; label: string }[] = [
  { id: 'sunset', label: 'Sunset road' },
  { id: 'lake', label: 'Mountain lake' },
  { id: 'aurora', label: 'Aurora' },
];

/**
 * The desktop's wallpapers, drawn here (the car's own are photographs we do not
 * ship): a dusk road under a red sky, an alpine lake, an aurora.
 */
export function Wallpaper({ id, className }: { id: WallpaperId; className?: string }) {
  const uid = React.useId().replace(/:/g, '');
  const common = {
    viewBox: '0 0 1280 800',
    preserveAspectRatio: 'xMidYMid slice' as const,
    className,
    'aria-hidden': true as const,
  };
  if (id === 'lake') {
    return (
      <svg {...common}>
        <defs>
          <linearGradient id={`${uid}s`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#5f95dc" />
            <stop offset="0.55" stopColor="#a9cdee" />
            <stop offset="1" stopColor="#e6d3d0" />
          </linearGradient>
          <linearGradient id={`${uid}l`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#35568f" />
            <stop offset="0.5" stopColor="#1d3568" />
            <stop offset="1" stopColor="#0b1634" />
          </linearGradient>
          <linearGradient id={`${uid}m`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#2a3768" />
            <stop offset="1" stopColor="#141c40" />
          </linearGradient>
          <filter id={`${uid}b`}><feGaussianBlur stdDeviation="5" /></filter>
        </defs>
        <rect width="1280" height="800" fill={`url(#${uid}s)`} />
        {/* far range, lit pink on its left faces */}
        <path d="M0 470 L90 330 L150 390 L215 300 L300 400 L360 360 L470 440 L560 470 Z" fill="#7d6f9b" opacity="0.75" />
        <path d="M0 470 L90 330 L130 380 L110 470 Z" fill="#efb199" opacity="0.9" />
        <path d="M150 390 L215 300 L240 340 L215 420 Z" fill="#f0b9a2" opacity="0.85" />
        <path d="M720 470 L850 420 L960 330 L1060 400 L1150 380 L1280 440 L1280 480 Z" fill="#2a3566" />
        <path d="M0 480 L120 400 L260 470 L420 440 L620 480 L860 455 L1010 410 L1130 430 L1280 400 L1280 520 L0 520 Z" fill={`url(#${uid}m)`} />
        <path d="M960 330 L985 365 L1005 345 L1040 385 L1060 400 L960 400 Z" fill="#cfd5ea" opacity="0.5" />
        {/* the lake and the mountains in it */}
        <rect y="500" width="1280" height="300" fill={`url(#${uid}l)`} />
        <g filter={`url(#${uid}b)`} opacity="0.55" transform="translate(0 1000) scale(1 -1)">
          <path d="M0 470 L90 330 L150 390 L215 300 L300 400 L360 360 L470 440 L560 470 Z" fill="#c78c86" opacity="0.7" />
          <path d="M720 470 L850 420 L960 330 L1060 400 L1150 380 L1280 440 L1280 480 Z" fill="#26325f" />
        </g>
        <ellipse cx="640" cy="735" rx="70" ry="22" fill="#241b2c" opacity="0.85" />
      </svg>
    );
  }
  if (id === 'aurora') {
    return (
      <svg {...common}>
        <defs>
          <linearGradient id={`${uid}s`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#050a1c" />
            <stop offset="0.6" stopColor="#0c2236" />
            <stop offset="1" stopColor="#04080f" />
          </linearGradient>
          <filter id={`${uid}b`}><feGaussianBlur stdDeviation="38" /></filter>
        </defs>
        <rect width="1280" height="800" fill={`url(#${uid}s)`} />
        <g filter={`url(#${uid}b)`}>
          <ellipse cx="420" cy="330" rx="420" ry="120" fill="#27d6a0" opacity="0.55" transform="rotate(-12 420 330)" />
          <ellipse cx="860" cy="270" rx="360" ry="90" fill="#7a5cff" opacity="0.5" transform="rotate(8 860 270)" />
          <ellipse cx="640" cy="420" rx="520" ry="70" fill="#1fb6ff" opacity="0.3" />
        </g>
        <path d="M0 640 L180 560 L330 620 L520 540 L700 630 L900 560 L1100 620 L1280 570 L1280 800 L0 800 Z" fill="#03070d" />
      </svg>
    );
  }
  // sunset road
  return (
    <svg {...common}>
      <defs>
        <linearGradient id={`${uid}s`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#150912" />
          <stop offset="0.3" stopColor="#3b1321" />
          <stop offset="0.52" stopColor="#8d2c2b" />
          <stop offset="0.64" stopColor="#d96b30" />
          <stop offset="0.7" stopColor="#6b2020" />
          <stop offset="1" stopColor="#10060a" />
        </linearGradient>
        <radialGradient id={`${uid}g`} cx="0.5" cy="0.64" r="0.55">
          <stop offset="0" stopColor="#ffb36b" stopOpacity="0.55" />
          <stop offset="1" stopColor="#ffb36b" stopOpacity="0" />
        </radialGradient>
        <linearGradient id={`${uid}r`} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#fff" stopOpacity="0" />
          <stop offset="0.5" stopColor="#ffd9b8" stopOpacity="0.55" />
          <stop offset="1" stopColor="#fff" stopOpacity="0" />
        </linearGradient>
        <filter id={`${uid}b`}><feGaussianBlur stdDeviation="6" /></filter>
      </defs>
      <rect width="1280" height="800" fill={`url(#${uid}s)`} />
      <rect width="1280" height="800" fill={`url(#${uid}g)`} />
      {/* the swept highlight of a body line, as the car's own wallpaper draws it */}
      <path d="M-40 560 C 260 470, 520 430, 760 470 S 1140 560, 1340 500" fill="none" stroke={`url(#${uid}r)`} strokeWidth="26" filter={`url(#${uid}b)`} />
      <path d="M-40 600 C 300 520, 560 490, 800 520 S 1160 600, 1340 560" fill="none" stroke={`url(#${uid}r)`} strokeWidth="6" opacity="0.7" />
    </svg>
  );
}
