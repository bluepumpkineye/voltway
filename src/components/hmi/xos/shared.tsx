'use client';

import React from 'react';

/** The time, ticking; empty until mounted (the HMI is also server-rendered). */
export function useNow(): string {
  const [now, setNow] = React.useState<Date | null>(null);
  React.useEffect(() => {
    setNow(new Date());
    const id = window.setInterval(() => setNow(new Date()), 15_000);
    return () => window.clearInterval(id);
  }, []);
  if (!now) return '';
  return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
}

const MON = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const DAY = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

/** The date card's figures: the day, the month and the weekday. */
export function useDate(): { d: string; m: string; w: string } {
  const [now, setNow] = React.useState<Date | null>(null);
  React.useEffect(() => setNow(new Date()), []);
  if (!now) return { d: '', m: '', w: '' };
  return { d: String(now.getDate()), m: MON[now.getMonth()], w: DAY[now.getDay()] };
}

interface XoLocal {
  /** switches the showroom has no 3D or store state for */
  on: Record<string, boolean>;
  toggle: (id: string) => void;
  set: (id: string, v: boolean) => void;
  /** a number or a choice a control keeps */
  val: Record<string, number>;
  setVal: (id: string, v: number) => void;
  /** a small message at the bottom of the screen, for things a showroom car cannot do */
  notify: (msg: string) => void;
}

const Ctx = React.createContext<XoLocal | null>(null);

const DEFAULTS: Record<string, boolean> = {
  mirrorsOut: true,
  trunkClosed: true,
  hud: true,
  sentry: false,
  nap: false,
};

const VALUES: Record<string, number> = {
  sheetTab: 0, // quick panel: 0 common, 1 AC, 2 seats
  seatMenu: 0,
  setPage: 0,
  subPage: 0,
  fan: 4,
  headlamp: 0, // 0 off, 1 position, 2 low beam, 3 auto, 4 fog
  brightness: 100,
  power: 1, // power response: 0 eco, 1 comfort, 2 sport
  steer: 1,
  brake: 1,
  ambMode: 0,
  mediaSource: 0,
  mapDetail: 0,
};

export function XoProvider({ children }: { children: React.ReactNode }) {
  const [on, setOn] = React.useState<Record<string, boolean>>({});
  const [val, setValState] = React.useState<Record<string, number>>({});
  const [msg, setMsg] = React.useState<string | null>(null);
  const timer = React.useRef<number | undefined>(undefined);

  const api = React.useMemo<XoLocal>(
    () => ({
      on: new Proxy(on, { get: (t, k: string) => (k in t ? t[k] : DEFAULTS[k] ?? false) }),
      toggle: (id) => setOn((s) => ({ ...s, [id]: !(id in s ? s[id] : DEFAULTS[id] ?? false) })),
      set: (id, v) => setOn((s) => ({ ...s, [id]: v })),
      val: new Proxy(val, { get: (t, k: string) => (k in t ? t[k] : VALUES[k] ?? 0) }),
      setVal: (id, v) => setValState((s) => ({ ...s, [id]: v })),
      notify: (m) => {
        setMsg(m);
        window.clearTimeout(timer.current);
        timer.current = window.setTimeout(() => setMsg(null), 1800);
      },
    }),
    [on, val],
  );

  return (
    <Ctx.Provider value={api}>
      {children}
      {msg && (
        <div
          role="status"
          className="pointer-events-none absolute bottom-[86px] left-1/2 z-[60] -translate-x-1/2 rounded-full px-6 py-3 text-[17px] text-white"
          style={{ background: 'rgba(24,24,36,0.9)', backdropFilter: 'blur(16px)' }}
        >
          {msg}
        </div>
      )}
    </Ctx.Provider>
  );
}

export function useXo(): XoLocal {
  const v = React.useContext(Ctx);
  if (!v) throw new Error('XoProvider missing');
  return v;
}
