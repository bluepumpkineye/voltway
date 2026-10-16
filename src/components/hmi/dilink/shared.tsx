'use client';

import React from 'react';

/* ------------------------------------------------------------------- clock */

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

/* ------------------------------------------------- local switches and toasts */

interface DlLocal {
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

const Ctx = React.createContext<DlLocal | null>(null);

const DEFAULTS: Record<string, boolean> = {
  smartLowBeam: true,
  smartLogo: true,
  autoHold: true,
  hud: true,
  rainClose: true,
  autoLock: true,
  mirrorsFold: true,
};

const VALUES: Record<string, number> = {
  setPage: 1, // settings menu: 0 search, 1 common ...
  lightTab: 0,
  seatTab: 0,
  climateTab: 0,
  flow: 1,
  brightness: 80,
  regen: 0, // 0 standard, 1 large
  steering: 1,
  ride: 1,
  mediaSource: 0,
  radioGroup: 0,
};

export function DlProvider({ children }: { children: React.ReactNode }) {
  const [on, setOn] = React.useState<Record<string, boolean>>({});
  const [val, setValState] = React.useState<Record<string, number>>({});
  const [msg, setMsg] = React.useState<string | null>(null);
  const timer = React.useRef<number | undefined>(undefined);

  const api = React.useMemo<DlLocal>(
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
          style={{ background: 'rgba(8,12,24,0.9)', backdropFilter: 'blur(16px)', boxShadow: '0 0 0 1px rgba(255,255,255,0.14)' }}
        >
          {msg}
        </div>
      )}
    </Ctx.Provider>
  );
}

export function useDl(): DlLocal {
  const v = React.useContext(Ctx);
  if (!v) throw new Error('DlProvider missing');
  return v;
}
