'use client';

import React from 'react';
import type { TechDemoSpec, Variant, Vehicle } from '@/data/vehicles/schema';
import { useNow } from '@/components/hmi/harmonyos/shared';
import { effectiveRange } from '@/lib/performance';
import { pauseDemo, resetDemo, startDemo } from '@/lib/tech/actions';
import { useTechClock } from '@/lib/tech/clock';
import type { ParkSpeed } from '@/lib/tech/park';
import { parkPhase, parkProgress } from '@/lib/tech/phase';
import { useRuntime } from '@/lib/tech/session';
import { useVehicleStore } from '@/store/vehicle-store';
import { ParkTopView } from '../ParkTopView';
import * as Ic from './icons';
import { PHONE_H, PHONE_W } from './PhoneFrame';

/**
 * The maker's phone app as the Tech tab shows it: the vehicle page of the Huawei HIMA app (the car, its
 * range and charge, the quick controls, climate, and the list of functions with "Remote parking" in it),
 * and the remote-parking screen the demo runs on. Rebuilt in code from the maker's published screens
 * (blender/reference/luxeed-rx/tech): our own icons and art, text in English. The remote-parking screen is
 * drawn from the documented steps in the style of the vehicle page, as no still of it was found.
 *
 * What the app shows of the car is the demo's state, read from the clock: nothing here is a separate
 * simulation, so the phone, the car's screen and the 3D scene always agree.
 */

const BLUE = '#0a59f7';
const INK = '#14161a';
const MUTED = '#7c808a';
const BG = '#f2f2f4';

export type AppScreen = 'home' | 'remote';

export function HimaApp({
  vehicle,
  variant,
  demo,
  screen,
  setScreen,
}: {
  vehicle: Vehicle;
  variant: Variant;
  demo: TechDemoSpec;
  /** held by the showroom, so the guidance beside the phone knows which screen it is on */
  screen: AppScreen;
  setScreen: (s: AppScreen) => void;
}) {
  const [toast, setToast] = React.useState<string | null>(null);
  const timer = React.useRef<number | undefined>(undefined);
  const { hm } = useNow();
  const clock = useTechClock();
  const phase = parkPhase(clock);

  // the car's own settings and readouts, which this app shows too
  const soc = useVehicleStore((s) => s.soc);
  const driveMode = useVehicleStore((s) => s.driveMode);
  const climate = useVehicleStore((s) => s.climate);
  const rpa = useVehicleStore((s) => s.rpaEnabled);
  const speed = useVehicleStore((s) => s.parkSpeed);
  const status = useVehicleStore((s) => s.techStatus);
  const range = effectiveRange(variant, driveMode, soc, climate);

  const say = React.useCallback((msg: string) => {
    setToast(msg);
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setToast(null), 1900);
  }, []);
  const notDemo = () => say('Not part of the showroom demo');

  // leaving the screen stops a car that is moving, as the real app does
  const back = () => {
    if (phase === 'parking' || phase === 'leaving') {
      pauseDemo();
      say('Paused: remote parking stops when you leave the screen');
    }
    setScreen('home');
  };

  return (
    <div
      className="relative overflow-hidden text-[14px] leading-tight"
      style={{ width: PHONE_W, height: PHONE_H, background: BG, color: INK, fontFamily: "'HarmonyOS Sans', 'Inter', system-ui, sans-serif" }}
    >
      <StatusBar time={hm} />
      {screen === 'home' ? (
        <Home
          vehicle={vehicle}
          rangeKm={range?.km ?? null}
          soc={soc}
          tempC={climate.driverTempC}
          notDemo={notDemo}
          hint={phase === 'ready'}
          onRemote={() => setScreen('remote')}
          phase={phase}
        />
      ) : (
        <Remote
          vehicle={vehicle}
          demo={demo}
          phase={phase}
          progress={parkProgress(clock)}
          rpa={rpa}
          speed={speed}
          ready={status === 'ready'}
          back={back}
          notDemo={notDemo}
          done={() => setScreen('home')}
        />
      )}
      {toast && (
        <div
          role="status"
          className="pointer-events-none absolute bottom-[84px] left-1/2 z-40 max-w-[300px] -translate-x-1/2 rounded-full bg-[#1a1c21]/90 px-4 py-2.5 text-center text-[13px] text-white"
        >
          {toast}
        </div>
      )}
    </div>
  );
}

/* --------------------------------------------------------------------- bars */

function StatusBar({ time }: { time: string }) {
  return (
    <div className="absolute inset-x-0 top-0 z-30 flex h-[34px] items-center justify-between px-6 pt-1 text-[12px] font-medium" style={{ color: INK }}>
      <span className="tnum w-12">{time}</span>
      <span className="flex items-center gap-1.5">
        <Ic.Signal size={14} />
        <span className="tnum text-[11px]">5G</span>
        <span className="relative h-[11px] w-[20px] rounded-[3px] border border-current opacity-80">
          <span className="absolute inset-[1.5px] right-[5px] rounded-[1.5px] bg-current" />
        </span>
      </span>
    </div>
  );
}

const NAV = [
  { id: 'discover', label: 'Discover', icon: <Ic.Compass size={22} /> },
  { id: 'featured', label: 'Featured', icon: <Ic.Bag size={22} /> },
  { id: 'car', label: 'My car', icon: <Ic.CarSide size={22} /> },
  { id: 'services', label: 'Services', icon: <Ic.Heart size={22} /> },
  { id: 'me', label: 'Me', icon: <Ic.Person size={22} /> },
];

function TabBar({ notDemo }: { notDemo: () => void }) {
  return (
    <nav className="absolute inset-x-0 bottom-0 z-20 flex h-[62px] items-start justify-around border-t border-black/[0.06] bg-[#f8f8fa]/95 pt-2 backdrop-blur" aria-label="App">
      {NAV.map((n) => {
        const on = n.id === 'car';
        return (
          <button key={n.id} type="button" onClick={on ? undefined : notDemo} className="flex w-[64px] flex-col items-center gap-0.5 text-[10.5px] outline-none" style={{ color: on ? BLUE : MUTED }} aria-current={on ? 'page' : undefined}>
            {n.icon}
            {n.label}
          </button>
        );
      })}
    </nav>
  );
}

/* --------------------------------------------------------------------- home */

const QUICK = [
  { id: 'lock', label: 'Lock', icon: <Ic.Lock size={24} />, on: true },
  { id: 'boot', label: 'Boot', icon: <Ic.Boot size={24} /> },
  { id: 'windows', label: 'Windows', icon: <Ic.Window size={24} /> },
  { id: 'horn', label: 'Flash & horn', icon: <Ic.Horn size={24} /> },
  { id: 'frunk', label: 'Frunk', icon: <Ic.Frunk size={24} /> },
];

function Home({
  vehicle,
  rangeKm,
  soc,
  tempC,
  notDemo,
  hint,
  onRemote,
  phase,
}: {
  vehicle: Vehicle;
  rangeKm: number | null;
  soc: number;
  tempC: number;
  notDemo: () => void;
  hint: boolean;
  onRemote: () => void;
  phase: ReturnType<typeof parkPhase>;
}) {
  const patchClimate = useVehicleStore((s) => s.patchClimate);
  const [cool, setCool] = React.useState(true);
  const scroller = React.useRef<HTMLDivElement>(null);
  const remoteRow = React.useRef<HTMLLIElement>(null);
  // the list is below the fold on the maker's page too: once the page is up, scroll it into view
  React.useEffect(() => {
    if (!hint) return;
    const id = window.setTimeout(() => {
      const box = scroller.current;
      const row = remoteRow.current;
      if (box && row) box.scrollTo({ top: Math.max(0, row.offsetTop - 300), behavior: 'smooth' });
    }, 700);
    return () => window.clearTimeout(id);
    // once, when the page opens; `hint` is true at that moment
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const pct = Math.round(soc * 100);
  const moving = phase === 'parking' || phase === 'leaving';
  const rows = [
    { id: 'key', icon: <Ic.Key size={22} />, title: 'Digital key', sub: 'Not set up' },
    { id: 'remote', icon: <Ic.ParkCar size={22} />, title: 'Remote parking' },
    { id: 'valet', icon: <Ic.Valet size={22} />, title: 'Valet parking', beta: true },
    { id: 'sentry', icon: <Ic.Eye size={22} />, title: 'Sentry mode', sub: 'Off' },
    { id: 'prep', icon: <Ic.Power size={22} />, title: 'Pre-trip prep' },
    { id: 'cooler', icon: <Ic.Cooler size={22} />, title: 'Cooler box' },
    { id: 'status', icon: <Ic.CarCheck size={22} />, title: 'Vehicle status' },
  ];
  return (
    <>
      <div ref={scroller} className="absolute inset-x-0 bottom-[62px] top-[34px] overflow-y-auto overflow-x-hidden pb-6 [scrollbar-width:none]">
        <header className="flex h-[48px] items-center justify-between px-5">
          <button type="button" onClick={notDemo} className="flex items-center gap-1 text-[19px] font-semibold outline-none">
            {vehicle.brand} {vehicle.model}
            <svg width="10" height="6" viewBox="0 0 10 6" aria-hidden>
              <path d="M1 1l4 4 4-4" stroke="currentColor" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
          <button type="button" onClick={notDemo} aria-label="Notifications" className="relative grid h-9 w-9 place-items-center rounded-full outline-none">
            <Ic.Bell size={22} />
            <span className="absolute right-[7px] top-[6px] h-[7px] w-[7px] rounded-full bg-[#ff3b30]" />
          </button>
        </header>

        <div className="flex items-center justify-between px-5">
          <span className="flex h-7 items-center gap-1.5 rounded-full bg-black/[0.05] px-3 text-[12px]">
            <span className={`h-[6px] w-[6px] rounded-full ${moving ? 'bg-[#0a59f7]' : 'bg-[#34c759]'}`} />
            {moving ? 'Moving by remote parking' : 'Parked and locked'}
          </span>
          <button type="button" onClick={notDemo} className="flex h-7 items-center gap-1 rounded-full bg-white px-3 text-[12px] text-[#1f9d55] outline-none">
            <Ic.Bolt size={13} />
            Charging service
            <Ic.Chevron size={11} />
          </button>
        </div>

        <div className="px-5 pt-3">
          <div className="flex items-end gap-1.5">
            <span className="tnum text-[46px] font-semibold leading-none tracking-tight">{rangeKm ?? '--'}</span>
            <span className="pb-1 text-[14px]" style={{ color: MUTED }}>km</span>
          </div>
          <div className="mt-1.5 text-[12px]" style={{ color: MUTED }}>Battery {pct}%</div>
          <div className="mt-1.5 h-[4px] w-[112px] overflow-hidden rounded-full bg-black/[0.08]">
            <div className="h-full rounded-full bg-[#34c759]" style={{ width: `${pct}%` }} />
          </div>
        </div>

        <div className="relative -mt-2 h-[158px]">
          <div className="absolute bottom-[10px] left-1/2 h-[16px] w-[250px] -translate-x-1/2 rounded-[50%] bg-black/[0.14] blur-[8px]" aria-hidden />
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={`/hmi/${vehicle.slug}/car34.webp`} alt={`${vehicle.brand} ${vehicle.model}`} draggable={false} className="absolute left-1/2 top-[6px] w-[318px] -translate-x-1/2" />
        </div>
        <p className="mt-0.5 text-center text-[10.5px]" style={{ color: MUTED }}>{moving ? 'Moving' : 'Parked'} · updated just now</p>

        <div className="mt-3 flex justify-between px-4">
          {QUICK.map((q) => (
            <button key={q.id} type="button" onClick={notDemo} className="flex w-[62px] flex-col items-center gap-1.5 text-[10.5px] outline-none">
              <span className="grid h-[52px] w-[52px] place-items-center rounded-full" style={q.on ? { background: BLUE, color: '#fff' } : { background: '#fff', color: INK }}>
                {q.icon}
              </span>
              <span className="whitespace-nowrap" style={{ color: MUTED }}>{q.label}</span>
            </button>
          ))}
        </div>

        <div className="mt-4 grid grid-cols-2 gap-2.5 px-4">
          <div className="row-span-2 rounded-[18px] bg-white p-3.5">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-[13px] font-medium" style={{ color: BLUE }}>
                <Ic.Fan size={17} />
                Climate
              </span>
              <button type="button" aria-label={cool ? 'Switch the climate off' : 'Switch the climate on'} aria-pressed={cool} onClick={() => setCool((v) => !v)} className="grid h-7 w-7 place-items-center rounded-full outline-none" style={cool ? { background: '#e8f0ff', color: BLUE } : { background: '#eeeeef', color: MUTED }}>
                <Ic.Power size={15} />
              </button>
            </div>
            <div className="mt-5 flex items-center justify-between">
              <button type="button" aria-label="Cooler" onClick={() => patchClimate({ driverTempC: Math.max(16, tempC - 0.5) })} className="grid h-8 w-8 place-items-center rounded-full bg-black/[0.05] text-[18px] outline-none">−</button>
              <span className="tnum text-[26px] font-semibold" style={{ opacity: cool ? 1 : 0.35 }}>{tempC.toFixed(1)}</span>
              <button type="button" aria-label="Warmer" onClick={() => patchClimate({ driverTempC: Math.min(30, tempC + 0.5) })} className="grid h-8 w-8 place-items-center rounded-full bg-black/[0.05] text-[18px] outline-none">+</button>
            </div>
            <div className="mt-3 text-[11px]" style={{ color: MUTED }}>Cabin 18.4 °C</div>
          </div>
          <button type="button" onClick={notDemo} className="rounded-[18px] bg-white p-3.5 text-left outline-none">
            <span className="flex items-center gap-1.5 text-[13px] font-medium"><Ic.Pin size={16} style={{ color: '#ff9a3d' }} />Location</span>
            <span className="mt-2 block text-[11px]" style={{ color: MUTED }}>49 m · parked</span>
          </button>
          <button type="button" onClick={notDemo} className="rounded-[18px] bg-white p-3.5 text-left outline-none">
            <span className="flex items-center gap-1.5 text-[13px] font-medium"><Ic.Bolt size={16} style={{ color: '#1f9d55' }} />Battery</span>
            <span className="mt-2 block text-[11px]" style={{ color: MUTED }}>{pct}% · not charging</span>
          </button>
        </div>

        <ul className="mx-4 mt-3 overflow-hidden rounded-[18px] bg-white">
          {rows.map((r, i) => {
            const demoRow = r.id === 'remote';
            return (
              <li key={r.id} ref={demoRow ? remoteRow : undefined} className={i ? 'border-t border-black/[0.06]' : ''}>
                <button type="button" onClick={demoRow ? onRemote : notDemo} className="relative flex h-[54px] w-full items-center gap-3 px-4 text-left outline-none">
                  <span style={{ color: demoRow ? BLUE : INK }}>{r.icon}</span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-center gap-1.5 text-[14.5px]">
                      {r.title}
                      {r.beta && <span className="rounded-[4px] border border-black/20 px-1 text-[9px] leading-[13px]" style={{ color: MUTED }}>beta</span>}
                    </span>
                    {r.sub && <span className="block text-[11px]" style={{ color: MUTED }}>{r.sub}</span>}
                  </span>
                  {demoRow && hint && <span className="mr-1 rounded-full bg-[#0a59f7] px-2.5 py-1 text-[10.5px] font-medium text-white">Tap to begin</span>}
                  <Ic.Chevron size={16} style={{ color: '#b3b6bd' }} />
                  {demoRow && hint && <span className="pointer-events-none absolute inset-x-1.5 inset-y-1 animate-pulse rounded-[12px] ring-2 ring-[#0a59f7]/50" aria-hidden />}
                </button>
              </li>
            );
          })}
        </ul>
      </div>
      <TabBar notDemo={notDemo} />
    </>
  );
}

/* ------------------------------------------------------------------- remote */

function Remote({
  vehicle,
  demo,
  phase,
  progress,
  rpa,
  speed,
  ready,
  back,
  notDemo,
  done,
}: {
  vehicle: Vehicle;
  demo: TechDemoSpec;
  phase: ReturnType<typeof parkPhase>;
  progress: number;
  rpa: boolean;
  speed: ParkSpeed;
  ready: boolean;
  back: () => void;
  notDemo: () => void;
  done: () => void;
}) {
  const runtime = useRuntime();
  const setTechDevice = useVehicleStore((s) => s.setTechDevice);
  const openSettings = useVehicleStore((s) => s.openSettings);
  const [mode, setMode] = React.useState<'park' | 'straight'>('park');

  // the system check, each time the screen opens
  const [check, setCheck] = React.useState<'running' | 'ok'>('running');
  React.useEffect(() => {
    const id = window.setTimeout(() => setCheck('ok'), 1300);
    return () => window.clearTimeout(id);
  }, []);
  const checked = check === 'ok' || phase !== 'ready';

  const moving = phase === 'parking' || phase === 'leaving';
  const paused = phase === 'paused-in' || phase === 'paused-out';
  const pct = Math.round(progress * 100);
  const go = () => startDemo(demo.id, 'phone');
  const showOnCar = () => {
    setTechDevice('dashboard');
    openSettings('assist');
  };

  const clock = useTechClock();
  const search = runtime?.stage?.search;
  const isScanning = Boolean(search && phase === 'parking' && clock.t < search.found);
  const isBayFound = Boolean(search && phase === 'parking' && clock.t >= search.found && clock.t < search.end);

  const isCrab = demo.driver === 'crab';
  const isE3Park = demo.driver === 'e3park';

  const title =
    isCrab
      ? moving
        ? `Crab sliding to kerb… ${pct}%`
        : paused
          ? 'Crab walk paused'
          : phase === 'parked' || phase === 'done'
            ? 'Parked flush by the kerb'
            : 'Intelligent Crab Walk'
      : isE3Park
        ? moving
          ? clock.t >= (clock.stops[0] ?? Infinity)
            ? `Pivoting tail in… ${pct}%`
            : `Pulling into space… ${pct}%`
          : paused
            ? Math.abs(clock.t - (clock.stops[0] ?? 0)) < 0.2
              ? 'Ready to Pivot'
              : 'Paused'
            : phase === 'parked' || phase === 'done'
              ? 'Parked in parallel bay'
              : 'e³ Parallel Smart Parking'
        : isScanning
          ? 'Screening for bay…'
          : isBayFound
            ? 'Target slot identified'
            : phase === 'parking'
              ? `Parking in… ${pct}%`
              : phase === 'leaving'
                ? `Parking out… ${pct}%`
                : paused
                  ? 'Paused'
                  : phase === 'parked'
                    ? 'Parked in the bay'
                    : phase === 'done'
                      ? 'Back where it started'
                      : 'Rear-in, bay on your right';

  const sub =
    isCrab
      ? phase === 'ready'
        ? 'All four wheels steer diagonally into kerbside bay.'
        : moving
          ? 'Four-wheel diagonal slide active. 15° crab angle.'
          : paused
            ? 'The car has stopped where it is.'
            : 'Diagonal docking completed.'
      : isE3Park
        ? phase === 'ready'
          ? 'Autonomous parallel parking into tight 1 m margin gap.'
          : Math.abs(clock.t - (clock.stops[0] ?? 0)) < 0.2
            ? 'Nose in bay. Tap Pivot to swing tail into the space.'
            : moving
              ? clock.t >= (clock.stops[0] ?? Infinity)
                ? 'Front wheel locked. Counter-rotating rear wheels swing tail in.'
                : 'Approaching target bay with nose-in angle.'
              : paused
                ? 'The car has stopped where it is.'
                : 'e³ parallel docking completed.'
        : phase === 'ready'
          ? 'Stand clear of the car and its path, and keep it in sight.'
          : isScanning
            ? 'Sensors screening parking bays along the lane.'
            : isBayFound
              ? 'Target bay locked. Stopping to reverse in.'
              : moving
                ? 'The car is steering itself. Pause at any time.'
                : paused
                  ? 'The car has stopped where it is.'
                  : phase === 'parked'
                    ? 'Ready to drive out again whenever you are.'
                    : 'Remote parking finished.';

  return (
    <div className="absolute inset-x-0 bottom-0 top-[34px] flex flex-col">
      <header className="flex h-[48px] shrink-0 items-center justify-between px-3">
        <button type="button" onClick={back} aria-label="Back" className="grid h-9 w-9 place-items-center rounded-full outline-none">
          <Ic.Back size={22} />
        </button>
        <h2 className="text-[17px] font-semibold">{demo.driver === 'crab' ? 'Crab walk' : demo.driver === 'e3park' ? 'e³ parking' : 'Remote parking'}</h2>
        <button type="button" onClick={notDemo} aria-label="About remote parking" className="grid h-9 w-9 place-items-center rounded-full outline-none">
          <Ic.Info size={20} />
        </button>
      </header>

      <div className="mx-4 flex h-[38px] shrink-0 rounded-full bg-black/[0.06] p-[3px] text-[13px]" role="tablist" aria-label="Mode">
        {([['park', 'Remote parking'], ['straight', 'Remote straight']] as const).map(([id, label]) => (
          <button key={id} type="button" role="tab" aria-selected={mode === id} onClick={() => (id === 'straight' ? notDemo() : setMode(id))} className="flex-1 rounded-full outline-none" style={mode === id ? { background: '#fff', fontWeight: 600, boxShadow: '0 1px 4px rgba(0,0,0,0.12)' } : { color: MUTED }}>
            {label}
          </button>
        ))}
      </div>

      {!rpa ? (
        <div className="mx-4 mt-3 rounded-[18px] bg-white p-4">
          <div className="text-[15px] font-semibold">Remote parking assist is off</div>
          <p className="mt-1.5 text-[12.5px] leading-snug" style={{ color: MUTED }}>
            Switch it on in the car: Settings › Assisted driving › Parking assist.
          </p>
          <button type="button" onClick={showOnCar} className="mt-3 h-[42px] w-full rounded-full text-[14px] font-medium text-white outline-none" style={{ background: BLUE }}>
            Show it on the car screen
          </button>
        </div>
      ) : (
        <div className="mx-4 mt-3 rounded-[18px] bg-white px-4 py-1">
          <Check label="Bluetooth" value="Connected" state="ok" />
          <Check label="System check" value={checked ? 'Passed' : 'Checking…'} state={checked ? 'ok' : 'running'} />
          <Check label="Parking speed" value={speed === 'slow' ? 'Slower' : speed === 'fast' ? 'Faster' : 'Medium'} state="plain" />
        </div>
      )}

      <div className="mx-4 mt-3 overflow-hidden rounded-[18px] bg-white">
        <div className="relative">
          {runtime?.stage ? (
            <ParkTopView theme="light" className="block h-auto w-full" sprite={{ src: `/hmi/${vehicle.slug}/car-top.webp`, aspect: 420 / 969 }} />
          ) : runtime?.chassis?.stage ? (
            <div className="flex h-[200px] flex-col items-center justify-center gap-2 bg-gradient-to-b from-[#e7edf6] to-[#cfd9e8] p-4 text-center">
              <span className="flex h-[36px] w-[36px] items-center justify-center rounded-[10px] text-[17px] font-bold text-white shadow-md" style={{ background: 'linear-gradient(145deg,#e0243c,#a30f2a)' }}>
                e³
              </span>
              <div className="text-[15px] font-semibold text-[#34405a]">
                {isCrab ? 'Intelligent Crab Walk' : isE3Park ? 'e³ Smart Parking' : 'Chassis Maneuver'}
              </div>
              <div className="text-[12px] text-[#52607c]">
                {isCrab ? 'Diagonal kerb docking · 15° steer' : isE3Park ? 'Front pivot · Rear swing parallel' : 'e³ Platform Telemetry'}
              </div>
            </div>
          ) : (
            <div className="grid h-[200px] place-items-center text-[12px]" style={{ color: MUTED }}>{ready ? 'Loading the lot…' : 'Loading the car…'}</div>
          )}
        </div>
        <div className="px-4 pb-3 pt-2.5">
          <div className="text-[14.5px] font-semibold">{title}</div>
          <div className="mt-0.5 text-[11.5px] leading-snug" style={{ color: MUTED }}>{sub}</div>
          {(moving || paused) && (
            <div className="mt-2 h-[4px] overflow-hidden rounded-full bg-black/[0.08]">
              <div className="h-full rounded-full" style={{ width: `${pct}%`, background: BLUE }} />
            </div>
          )}
        </div>
      </div>

      <div className="mt-auto flex shrink-0 gap-2.5 px-4 pb-5 pt-3">
        {phase === 'ready' && (
          <Primary disabled={!rpa || !checked || !ready} onClick={go}>{isCrab ? 'Start crab walk' : isE3Park ? 'Start pull in' : 'Start parking in'}</Primary>
        )}
        {moving && (
          <Primary outline onClick={pauseDemo}>
            <Ic.Pause size={16} /> Pause
          </Primary>
        )}
        {paused && (
          <>
            <button type="button" onClick={resetDemo} className="h-[48px] w-[110px] rounded-full bg-black/[0.06] text-[14px] outline-none">Start over</button>
            <Primary onClick={go}>{isE3Park && Math.abs(clock.t - (clock.stops[0] ?? 0)) < 0.2 ? 'Pivot' : <><Ic.Play size={15} /> Resume</>}</Primary>
          </>
        )}
        {phase === 'parked' && (
          <>
            <button type="button" onClick={done} className="h-[48px] w-[110px] rounded-full bg-black/[0.06] text-[14px] outline-none">Done</button>
            <Primary onClick={go}>Start parking out</Primary>
          </>
        )}
        {phase === 'done' && (
          <>
            <button type="button" onClick={() => { resetDemo(); done(); }} className="h-[48px] flex-1 rounded-full bg-black/[0.06] text-[14px] outline-none">Done</button>
            <Primary onClick={resetDemo}>Park again</Primary>
          </>
        )}
      </div>
    </div>
  );
}

function Check({ label, value, state }: { label: string; value: string; state: 'ok' | 'running' | 'plain' }) {
  return (
    <div className="flex h-[38px] items-center justify-between border-b border-black/[0.06] text-[13.5px] last:border-b-0">
      <span>{label}</span>
      <span className="flex items-center gap-1.5" style={{ color: state === 'ok' ? '#1f9d55' : MUTED }}>
        {state === 'ok' && <Ic.Check size={15} />}
        {state === 'running' && <Ic.Spinner size={14} />}
        {value}
      </span>
    </div>
  );
}

function Primary({
  children,
  onClick,
  disabled,
  outline,
}: {
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  outline?: boolean;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="flex h-[48px] flex-1 items-center justify-center gap-2 rounded-full text-[15px] font-medium outline-none transition-opacity disabled:opacity-40"
      style={outline ? { background: '#fff', color: BLUE, boxShadow: `inset 0 0 0 1.5px ${BLUE}` } : { background: BLUE, color: '#fff' }}
    >
      {children}
    </button>
  );
}
