'use client';

import React from 'react';
import type { DriveOverlay, Vehicle } from '@/data/vehicles/schema';
import { techClock } from '@/lib/tech/clock';
import { beatPlan, captionsOf, launchActs, openAt, runShape, type Caption, type CaptionTone } from '@/lib/tech/drive-beats';
import { clamp, countTo, Easing, fmt, progress, spring, SPRINGS } from '@/lib/tech/motion';
import { useRuntime } from '@/lib/tech/session';
import { BELOW_TOP } from './Chrome';
import { DRIVE_COLUMN_W, useDriveSetup } from './Drive';
import { ACCENT, AMBER, CYAN, RED, TILES, type TileCtx } from './driveTiles';

/**
 * The Drive tab's data, set in motion. The figures the instruments used to hold on a card at the side are a column of tiles over
 * the left of the stage, one for each instrument the car's scenario lists. A tile is a line of live figures; when the run comes to
 * its moment (the launch for the power and the motors, the S-curve for the steering, the stop for the brakes: `beatPlan`,
 * src/lib/tech/drive-beats.ts) it opens into its own animation and the one that opened first closes. Above them, when a run
 * begins, the trim's published figures count up.
 *
 * Everything on screen is a pure function of the playhead (src/lib/tech/motion.ts): scrub the run and the tiles open and close
 * with it, pause it and they hold. The controls (mode, load, road, camera) stay on the card at the right.
 */

export const RAIL_W = 292;
const HEAD = 36;
const GAP = 6;
const INTRO_H = 72;

/** The playhead, read every frame it changes (not at the clock's ten a second): the tiles are drawn from it. */
function useFrameT(): number {
  const [t, setT] = React.useState(() => techClock.t);
  React.useEffect(() => {
    let raf = 0;
    let last = Number.NaN;
    const loop = () => {
      if (techClock.t !== last) {
        last = techClock.t;
        setT(last);
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);
  return t;
}

/** Seconds since `key` last changed, on the wall clock, until `dur` has passed: for what plays once however the run is held. */
function useRealAge(key: unknown, dur: number): number {
  const [age, setAge] = React.useState(0);
  React.useEffect(() => {
    const t0 = performance.now();
    let raf = 0;
    const loop = () => {
      const a = (performance.now() - t0) / 1000;
      setAge(a);
      if (a < dur) raf = requestAnimationFrame(loop);
    };
    setAge(0);
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [key, dur]);
  return age;
}

function useReducedMotion(): boolean {
  const [reduced, setReduced] = React.useState(false);
  React.useEffect(() => {
    const q = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReduced(q.matches);
    const on = () => setReduced(q.matches);
    q.addEventListener('change', on);
    return () => q.removeEventListener('change', on);
  }, []);
  return reduced;
}

function useViewportHeight(): number {
  const [h, setH] = React.useState(900);
  React.useEffect(() => {
    const on = () => setH(window.innerHeight);
    on();
    window.addEventListener('resize', on);
    return () => window.removeEventListener('resize', on);
  }, []);
  return h;
}

// ------------------------------------------------------------------------------------------- the trim's figures

/** The trim's published figures, counting up when a run begins and leaving as the car gets going. */
function Intro({ vehicle, age }: { vehicle: Vehicle; age: number }) {
  const setup = useDriveSetup(vehicle);
  const perf = setup.variant.performance;
  const stats: { label: string; value: number; unit: string; digits: number }[] = [
    { label: 'Power', value: perf.powerKw, unit: 'kW', digits: 0 },
    ...(perf.torqueNm !== undefined ? [{ label: 'Torque', value: perf.torqueNm, unit: 'Nm', digits: 0 }] : []),
    ...(perf.zeroTo100S !== undefined ? [{ label: '0–100', value: perf.zeroTo100S, unit: 's', digits: 2 }] : []),
    { label: 'Battery', value: setup.variant.battery.capacityKwh, unit: 'kWh', digits: setup.variant.battery.capacityKwh % 1 ? 1 : 0 },
  ];
  const line = clamp(progress(age, 0, 0.7));
  return (
    <div className="absolute left-0 top-0 overflow-hidden rounded-2xl bg-neutral-950/60 px-3 py-2.5 text-white shadow-lg ring-1 ring-white/12 backdrop-blur-md" style={{ width: RAIL_W, height: INTRO_H }}>
      <div className="mb-1.5 flex items-center justify-between">
        <span className="min-w-0 flex-1 truncate text-[9px] font-semibold uppercase tracking-[0.1em] text-white/65">{setup.variant.name}</span>
        <span className="shrink-0 pl-2 text-[8.5px] uppercase tracking-[0.1em] text-white/40">published</span>
      </div>
      <div className="mb-1.5 h-px bg-white/15">
        <div className="h-full" style={{ width: `${line * 100}%`, background: ACCENT.power }} />
      </div>
      <div className="grid gap-1" style={{ gridTemplateColumns: `repeat(${stats.length}, minmax(0, 1fr))` }}>
        {stats.map((s, i) => {
          const at = 0.12 + i * 0.1;
          const enter = spring(age - at, SPRINGS.pop);
          const n = countTo(s.value, progress(age, at, 1.1));
          return (
            <div key={s.label} style={{ opacity: clamp(enter * 1.4), transform: `translateY(${(1 - Math.min(enter, 1)) * 12}px)` }}>
              <div className="truncate text-[8.5px] font-semibold uppercase tracking-[0.08em] text-white/55">{s.label}</div>
              <div className="tnum whitespace-nowrap text-[16px] font-semibold leading-tight">
                {fmt(n, s.digits)}
                <span className="ml-0.5 text-[9px] font-normal text-white/55">{s.unit}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ------------------------------------------------------------------------------------------- the stage's captions

const TONE: Record<CaptionTone, string> = { front: CYAN, rear: AMBER, all: '#ffffff', peak: AMBER, turn: AMBER, stop: RED };

/**
 * One line of the run set large over the stage, in kinetic type: a small label slides up, the headline's words rise one after
 * another out of their own masks, a rule draws under them, the line fades in. Each of those is a spring on the seconds since the
 * caption's start, so it plays the same from any scrub.
 */
function StageCaption({ cap, t, column, still, vh }: { cap: Caption; t: number; column: boolean; still: boolean; vh: number }) {
  // reduced motion: the caption comes and goes, with nothing to watch in between
  const age = still ? 9 : t - cap.from;
  const out = Easing.inOutQuad(progress(t, cap.to - 0.35, 0.35));
  const plate = spring(age, SPRINGS.firm);
  const tone = TONE[cap.tone];
  const words = cap.title.split(' ');
  const size = (cap.title.length <= 14 ? 32 : cap.title.length <= 30 ? 24 : 20) - (column ? 0 : 4);
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute left-0 z-10 flex justify-center px-3"
      // a wide window: over the road between the car and the gauges; a phone: above the gauges, under the car
      style={{ bottom: column ? 392 : Math.round(vh * 0.34), right: column ? DRIVE_COLUMN_W + 28 : 0 }}
    >
      <div
        className="flex max-w-[520px] flex-col items-center rounded-2xl bg-neutral-950/65 px-5 pb-3 pt-2.5 text-center text-white shadow-xl ring-1 ring-white/12 backdrop-blur-md"
        style={{ opacity: clamp(plate * 1.3) * (1 - out), transform: `translateY(${(1 - Math.min(plate, 1)) * 16 - out * 10}px) scale(${0.94 + 0.06 * Math.min(plate, 1.04)})` }}
      >
        <div className="flex items-center gap-1.5 text-[9.5px] font-semibold uppercase tracking-[0.18em]" style={{ color: tone, opacity: clamp(spring(age - 0.05, SPRINGS.soft) * 1.4), transform: `translateY(${(1 - Math.min(spring(age - 0.05, SPRINGS.soft), 1)) * 8}px)` }}>
          <span className="inline-block h-1.5 w-1.5 rounded-full" style={{ background: tone }} />
          {cap.kicker}
        </div>
        <div className="mt-1 flex flex-wrap justify-center gap-x-[0.3em] font-bold leading-[1.12] tracking-[-0.01em]" style={{ fontSize: size }}>
          {words.map((w, i) => {
            const k = Math.min(spring(age - 0.1 - i * 0.06, SPRINGS.rise), 1);
            return (
              // the mask has room under the line for the descenders (y, g, p), and gives it back so that the lines do not drift apart
              <span key={i} className="-mb-[0.14em] inline-block overflow-hidden pb-[0.14em]" style={{ lineHeight: 1.12 }}>
                <span className="inline-block" style={{ transform: `translateY(${(1 - k) * 115}%)`, opacity: clamp(k * 2) }}>
                  {w}
                </span>
              </span>
            );
          })}
        </div>
        <div className="mt-1 h-0.5 rounded-full" style={{ width: `${Math.round(clamp(spring(age - 0.2, SPRINGS.soft)) * 64)}px`, background: tone }} />
        {cap.line && (
          <p className="mt-1.5 text-[12px] leading-snug text-white/80" style={{ opacity: clamp((age - 0.35) / 0.35) }}>
            {cap.line}
          </p>
        )}
      </div>
    </div>
  );
}

// ------------------------------------------------------------------------------------------- the rail

function Tile({ id, c, top }: { id: DriveOverlay; c: TileCtx; top: number }) {
  const def = TILES[id];
  const chip = def.chip(c);
  const h = HEAD + def.body * c.open;
  const Body = def.Body;
  return (
    <section
      aria-label={def.title(c)}
      className="absolute left-0 overflow-hidden rounded-2xl bg-neutral-950/60 text-white shadow-lg ring-1 ring-white/12 backdrop-blur-md"
      style={{ top, width: RAIL_W, height: h }}
    >
      <div className="absolute left-0 top-0 h-0.5" style={{ width: `${c.open * 100}%`, background: ACCENT[id] }} />
      <header className="flex items-center justify-between px-3" style={{ height: HEAD }}>
        <div className="flex min-w-0 items-center gap-2">
          <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: ACCENT[id] }} />
          <h3 className="truncate text-[10px] font-semibold uppercase tracking-[0.1em] text-white/75">{def.title(c)}</h3>
        </div>
        <div className="tnum shrink-0 text-[13px] font-semibold" style={{ color: chip.color }}>
          {chip.value}
          {chip.unit && <span className="ml-0.5 text-[9px] font-normal text-white/55">{chip.unit}</span>}
        </div>
      </header>
      {c.open > 0.01 && (
        <div aria-hidden className="px-3" style={{ opacity: clamp((c.open - 0.12) / 0.7), transform: `translateY(${(1 - c.open) * 10}px)` }}>
          <Body c={c} />
        </div>
      )}
    </section>
  );
}

/**
 * The column of tiles. `column` is a window wide enough for the card at the right: the tiles then keep a line each, the open ones
 * taller. On a narrower one only the open tiles are drawn, under the scenario bar.
 */
export function DriveMotion({ vehicle, column }: { vehicle: Vehicle; column: boolean }) {
  const setup = useDriveSetup(vehicle);
  const facts = useRuntime()?.launch?.drive ?? null;
  const t = useFrameT();
  const reduced = useReducedMotion();
  const vh = useViewportHeight();
  const duration = techClock.duration;

  const overlays = React.useMemo(() => setup.spec.overlays.filter((o, i, all) => all.indexOf(o) === i), [setup.spec.overlays]);
  const shape = React.useMemo(() => (facts ? runShape(facts, duration) : null), [facts, duration]);
  const acts = React.useMemo(() => (facts && shape ? launchActs(facts, shape.launch) : []), [facts, shape]);
  // two tiles open at once where the window is tall enough for them above the gauges
  const max = column && vh >= 800 ? 2 : 1;
  const plan = React.useMemo(() => (facts && shape ? beatPlan(overlays, facts, shape, max) : []), [overlays, facts, shape, max]);
  const caps = React.useMemo(() => (facts && shape ? captionsOf(facts, shape, acts) : []), [facts, shape, acts]);
  const intro = useRealAge(facts, 3);

  if (!facts || !shape || !overlays.length) return null;

  const raw = openAt(plan, overlays, t);
  // reduced motion: a tile is open or shut, with no in-between to watch
  const open = (o: DriveOverlay) => (reduced ? (raw[o] > 0.5 ? 1 : 0) : raw[o]);
  const tel = facts.telemetry(t);

  const introExit = column && vh >= 800 ? Easing.inOutQuad(progress(t, shape.launch + 2.4, 0.5)) : 1;
  let y = 0;
  const introShown = introExit < 1;
  if (introShown) y += (INTRO_H + GAP) * (1 - introExit);
  // a narrow window has no room for a tile to open over the car: it shows the line of the tile whose moment it is
  const focus = column ? null : overlays.reduce((best, o) => (raw[o] > raw[best] ? o : best), overlays[0]);
  const tops: Record<string, number> = {};
  for (const o of overlays) {
    if (focus !== null && o !== focus) continue;
    tops[o] = y;
    y += HEAD + (column ? TILES[o].body * open(o) : 0) + GAP;
  }

  const cap = caps.find((x) => t >= x.from && t < x.to);

  return (
    <>
      {cap && <StageCaption cap={cap} t={t} column={column} still={reduced} vh={vh} />}
      <div
        role="group"
        aria-label="Live data from the run"
        className={`pointer-events-none absolute left-3 z-10 ${BELOW_TOP}`}
        style={{ width: RAIL_W, marginTop: column ? 0 : 44 }}
      >
        {introShown && (
          <div style={{ opacity: 1 - introExit, transform: `translateY(${-introExit * 14}px)` }}>
            <Intro vehicle={vehicle} age={reduced ? 9 : intro} />
          </div>
        )}
        {overlays.map((o) => {
          if (tops[o] === undefined) return null;
          const c: TileCtx = { t, tel, facts, setup, shape, acts, open: column ? open(o) : 0 };
          return <Tile key={o} id={o} c={c} top={tops[o]} />;
        })}
      </div>
    </>
  );
}
