'use client';

import React from 'react';

/* ------------------------------------------------------------------- clock */

const DAY = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** The time, ticking; empty until mounted (the HMI is also server-rendered). */
export function useNow(): { hm: string; date: string } {
  const [now, setNow] = React.useState<Date | null>(null);
  React.useEffect(() => {
    setNow(new Date());
    const id = window.setInterval(() => setNow(new Date()), 15_000);
    return () => window.clearInterval(id);
  }, []);
  if (!now) return { hm: '', date: '' };
  return {
    hm: `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`,
    date: `${MON[now.getMonth()]} ${now.getDate()} ${DAY[now.getDay()]}`,
  };
}

/* ------------------------------------------------- local switches and toasts */

interface ZkLocal {
  /** switches the showroom has no 3D or store state for (the charge flap, the mirrors ...) */
  on: Record<string, boolean>;
  toggle: (id: string) => void;
  set: (id: string, v: boolean) => void;
  /** a number or a choice a control keeps (seat levels, the sound field ...) */
  val: Record<string, number>;
  setVal: (id: string, v: number) => void;
  /** a small message at the bottom of the screen, for things a showroom car cannot do */
  notify: (msg: string) => void;
}

const Ctx = React.createContext<ZkLocal | null>(null);

const DEFAULTS: Record<string, boolean> = {
  autoHold: true,
  sentry: false,
  lyrics: true,
  hud: true,
  adaptiveBrightness: true,
  motionRelief: true, // Driving settings: on in c10_0036
  onePedal: false,
  parkComfort: false,
};

const VALUES: Record<string, number> = {
  seatFL: 0, // vent/heat AUTO states: 0 off, 1 auto
  seatFR: 0,
  seatRL: 0,
  seatRR: 0,
  ventFL: 0,
  ventFR: 0,
  ventRL: 0,
  ventRR: 0,
  wheelHeat: 0,
  seatTab: 0,
  setPage: 0,
  brightness: 100,
  regenLevel: 1, // Driving settings: 0 none, 1 low, 2 medium, 3 high
  brakeAssist: 0, // 0 comfort, 1 standard, 2 sport
  soundFx: 1,
  mediaSource: 0,
};

export function ZkProvider({ children }: { children: React.ReactNode }) {
  const [on, setOn] = React.useState<Record<string, boolean>>({});
  const [val, setValState] = React.useState<Record<string, number>>({});
  const [msg, setMsg] = React.useState<string | null>(null);
  const timer = React.useRef<number | undefined>(undefined);

  const api = React.useMemo<ZkLocal>(
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
          className="pointer-events-none absolute bottom-[84px] left-1/2 z-[60] -translate-x-1/2 rounded-full px-6 py-3 text-[17px] text-white"
          style={{ background: 'rgba(20,20,24,0.88)', backdropFilter: 'blur(16px)' }}
        >
          {msg}
        </div>
      )}
    </Ctx.Provider>
  );
}

export function useZkLocal(): ZkLocal {
  const v = React.useContext(Ctx);
  if (!v) throw new Error('ZkProvider missing');
  return v;
}
