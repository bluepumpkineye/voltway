'use client';

import React from 'react';
import type { DriveOverlay, Vehicle } from '@/data/vehicles/schema';
import { techClock } from '@/lib/tech/clock';
import { beatPlan, captionsOf, launchActs, openAt, runShape, type Caption, type CaptionTone } from '@/lib/tech/drive-beats';
import { driveAnchors, targetsOf } from '@/lib/tech/drive-anchors';
import { arrowTo, layoutCards, type Placed, type Slot } from '@/lib/tech/drive-layout';
import { clamp, countTo, Easing, fmt, progress, spring, SPRINGS } from '@/lib/tech/motion';
import { useRuntime } from '@/lib/tech/session';
import { useVehicleStore } from '@/store/vehicle-store';
import { BELOW_TOP } from './Chrome';
import { DRIVE_COLUMN_W, useDriveSetup } from './Drive';
import { ACCENT, AMBER, CYAN, RED, TILES, type TileCtx } from './driveTiles';

/**
 * The Drive tab's data, set in motion. The figures the instruments used to hold on a card at the side float beside the car, each next to
 * the part it explains and joined to it by an arrow that draws itself on and runs its dashes toward the part: the suspension's at the
 * tyre's arch, the brake's at the disc, the motors' at the hubs, the power's and the energy's at the pack under the floor, the drag's at the
 * roof (`targetsOf`, src/lib/tech/drive-anchors.ts; the viewer puts the points on the screen each frame, viewer/TechAnchors.tsx). Only the
 * cards the run has come to are there: when it reaches the moment of one (`beatPlan`, src/lib/tech/drive-beats.ts) it opens with its
 * arrow, and the one that opened first closes. Where each goes is a layout in pixels (src/lib/tech/drive-layout.ts): beside the car, not
 * over it, the gauges or the caption. Above them, when a run begins, the trim's published figures count up.
 *
 * What the cards show is a pure function of the playhead (src/lib/tech/motion.ts): scrub the run and they open and close with it, pause it
 * and they hold. Where they stand and the arrows' running dashes follow the camera and the wall clock, so that they stay alive when the
 * run is held. Inside the cabin camera, where there is nothing outside to point at, the open cards stand in a column at the left; on a
 * narrow window one line shows the card whose moment it is. The controls (mode, load, road, camera) stay on the card at the right.
 */

export const RAIL_W = 292;
const HEAD = 36;
const GAP = 6;
const INTRO_H = 72;

/**
 * The playhead and the wall clock, read every frame (not at the clock's ten a second): the cards are drawn from them. It renders again
 * when the playhead or the car's place on the screen (`driveAnchors`) has changed, and every frame while `live()` says something is
 * moving on its own (a card on its way to its place, an arrow's dashes).
 */
function useFrameClock(live: () => boolean): { t: number; now: number } {
  const [state, setState] = React.useState(() => ({ t: techClock.t, now: performance.now() }));
  React.useEffect(() => {
    let raf = 0;
    let lastT = Number.NaN;
    let lastV = -1;
    const loop = (now: number) => {
      const v = driveAnchors.frame?.version ?? -1;
      if (techClock.t !== lastT || v !== lastV || live()) {
        lastT = techClock.t;
        lastV = v;
        setState({ t: lastT, now });
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [live]);
  return state;
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
      style={{ bottom: column ? 348 : Math.round(vh * 0.34), right: column ? DRIVE_COLUMN_W + 28 : 0 }}
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

// ------------------------------------------------------------------------------------------- the cards

/** One card: a line of live figures that opens into its animation. `x` and `y` are its top left in its container. */
function Tile({ id, c, x, y, chip = false }: { id: DriveOverlay; c: TileCtx; x: number; y: number; chip?: boolean }) {
  const def = TILES[id];
  const info = def.chip(c);
  const h = HEAD + (chip ? 0 : def.body * c.open);
  const Body = def.Body;
  const appear = chip ? 1 : clamp(c.open * 2.5);
  return (
    <section
      aria-label={def.title(c)}
      className="absolute left-0 top-0 overflow-hidden rounded-2xl bg-neutral-950/60 text-white shadow-lg ring-1 ring-white/12 backdrop-blur-md"
      style={{ width: RAIL_W, height: h, opacity: appear, transform: `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) scale(${chip ? 1 : 0.94 + 0.06 * c.open})` }}
    >
      <div className="absolute left-0 top-0 h-0.5" style={{ width: `${(chip ? 1 : c.open) * 100}%`, background: ACCENT[id] }} />
      <header className="flex items-center justify-between px-3" style={{ height: HEAD }}>
        <div className="flex min-w-0 items-center gap-2">
          <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: ACCENT[id] }} />
          <h3 className="truncate text-[10px] font-semibold uppercase tracking-[0.1em] text-white/75">{def.title(c)}</h3>
        </div>
        <div className="tnum shrink-0 text-[13px] font-semibold" style={{ color: info.color }}>
          {info.value}
          {info.unit && <span className="ml-0.5 text-[9px] font-normal text-white/55">{info.unit}</span>}
        </div>
      </header>
      {!chip && c.open > 0.01 && (
        <div aria-hidden className="px-3" style={{ opacity: clamp((c.open - 0.12) / 0.7), transform: `translateY(${(1 - c.open) * 10}px)` }}>
          <Body c={c} />
        </div>
      )}
    </section>
  );
}

/**
 * An arrow from a card to the part of the car it explains. It draws itself on (the line grows from the card to the part as the card opens),
 * then a bright dash train runs along it toward the part, a head sits at its end and a ring pulses on the part. The dashes and the ring
 * run on the wall clock (they are alive while the run is held); `still` freezes them (reduced motion).
 */
function Arrow({ id, rect, target, open, now, still }: { id: DriveOverlay; rect: { x: number; y: number; w: number; h: number }; target: { x: number; y: number }; open: number; now: number; still: boolean }) {
  const a = arrowTo(rect, target);
  const col = ACCENT[id];
  const draw = Easing.outCubic(clamp((open - 0.12) / 0.6));
  const ring = Easing.outCubic(clamp((open - 0.55) / 0.35));
  const phase = still ? 0.4 : (now / 1500) % 1;
  const flow = still ? 0 : -((now / 1000) * 26) % 14;
  const head = clamp((draw - 0.85) / 0.15);
  return (
    <g>
      {/* a dark underlay keeps the line readable on the studio's pale floor, the white dashes on the dark road */}
      <path d={a.d} pathLength={100} fill="none" stroke="#0a0a0a" strokeWidth={4.2} strokeLinecap="round" strokeOpacity={0.22} strokeDasharray={`${draw * 100} 100`} />
      <path d={a.d} pathLength={100} fill="none" stroke={col} strokeWidth={1.8} strokeLinecap="round" strokeOpacity={0.9} strokeDasharray={`${draw * 100} 100`} />
      <path d={a.d} fill="none" stroke="#fff" strokeWidth={2.2} strokeLinecap="round" strokeDasharray="3 11" strokeDashoffset={flow} strokeOpacity={0.9 * draw} />
      <g transform={`translate(${a.tip.x.toFixed(1)} ${a.tip.y.toFixed(1)}) rotate(${((a.angle * 180) / Math.PI).toFixed(1)}) scale(${head})`}>
        <path d="M2 0 L-9 -5.5 L-9 5.5 Z" fill={col} stroke="#0a0a0a" strokeOpacity={0.35} strokeWidth={0.8} />
      </g>
      <g opacity={ring}>
        <circle cx={target.x} cy={target.y} r={3.2} fill={col} stroke="#fff" strokeWidth={1.2} />
        {[0, 0.5].map((o) => {
          const p = (phase + o) % 1;
          return <circle key={o} cx={target.x} cy={target.y} r={5 + 13 * p} fill="none" stroke={col} strokeWidth={1.6} strokeOpacity={0.8 * (1 - p)} />;
        })}
      </g>
    </g>
  );
}

/**
 * The cards. `column` is a window wide enough for the card at the right: the open cards then float beside the car with their arrows
 * (their places from `layoutCards`, eased toward each frame so that they glide when the camera moves). In the cabin camera they stand
 * in a column at the left; on a narrow window one line shows the card whose moment it is.
 */
export function DriveMotion({ vehicle, column }: { vehicle: Vehicle; column: boolean }) {
  const setup = useDriveSetup(vehicle);
  const facts = useRuntime()?.launch?.drive ?? null;
  const cam = useVehicleStore((s) => s.drive.cam) ?? setup.camera;
  const reduced = useReducedMotion();
  const vh = useViewportHeight();
  const duration = techClock.duration;
  const live = React.useRef(false);
  const isLive = React.useCallback(() => live.current, []);
  const { t, now } = useFrameClock(isLive);
  // where each card is on screen now (they glide to their places) and the place each had last, which the layout favours
  const pos = React.useRef<Record<string, { x: number; y: number }>>({});
  const slots = React.useRef<Record<string, Slot>>({});
  const lastNow = React.useRef(now);

  const overlays = React.useMemo(() => setup.spec.overlays.filter((o, i, all) => all.indexOf(o) === i), [setup.spec.overlays]);
  const shape = React.useMemo(() => (facts ? runShape(facts, duration) : null), [facts, duration]);
  const acts = React.useMemo(() => (facts && shape ? launchActs(facts, shape.launch) : []), [facts, shape]);
  // two cards open at once where the window is tall enough for them above the gauges
  const max = column && vh >= 800 ? 2 : 1;
  const plan = React.useMemo(() => (facts && shape ? beatPlan(overlays, facts, shape, max) : []), [overlays, facts, shape, max]);
  const caps = React.useMemo(() => (facts && shape ? captionsOf(facts, shape, acts) : []), [facts, shape, acts]);
  const intro = useRealAge(facts, 3);

  if (!facts || !shape || !overlays.length) {
    live.current = false;
    return null;
  }

  const raw = openAt(plan, overlays, t);
  // reduced motion: a card is open or shut, with no in-between to watch
  const open = (o: DriveOverlay) => (reduced ? (raw[o] > 0.5 ? 1 : 0) : raw[o]);
  const tel = facts.telemetry(t);
  const cap = caps.find((x) => t >= x.from && t < x.to);

  const introExit = column && vh >= 800 ? Easing.inOutQuad(progress(t, shape.launch + 2.4, 0.5)) : 1;
  const introShown = introExit < 1;
  const shown = overlays.filter((o) => open(o) > 0.02);

  const frame = driveAnchors.frame;
  const floating = column && cam !== 'cabin' && frame !== null;
  const rightPad = column ? DRIVE_COLUMN_W + 28 : 0;

  // ---- floating: the cards beside the car, each with its arrow
  let floatingCards: { id: DriveOverlay; x: number; y: number; ctx: TileCtx; arrows: { x: number; y: number }[] }[] = [];
  if (floating && frame) {
    const W = frame.width;
    const H = frame.height;
    // above the caption, which stands over the road just above the gauges
    const safe = { x: 10, y: 70, w: W - rightPad - 20, h: H * 0.5 - 78 };
    const avoid = [] as { x: number; y: number; w: number; h: number }[];
    if (cap) avoid.push({ x: (W - rightPad) / 2 - 260, y: H - 348 - 126, w: 520, h: 130 });
    if (introShown) avoid.push({ x: 8, y: 62, w: RAIL_W + 8, h: INTRO_H + 8 });
    const specs = shown.map((o) => {
      const pts = targetsOf(o, facts, tel)
        .map((name) => frame.pts[name])
        .filter((p) => p.ok);
      return { id: o as string, w: RAIL_W, h: HEAD + TILES[o].body, targets: pts.length ? pts : [{ x: frame.box.x + frame.box.w / 2, y: frame.box.y + frame.box.h / 2 }] };
    });
    const placed: Placed[] = layoutCards(specs, { safe, car: frame.box, avoid }, slots.current);
    // glide to the place: a card that has just opened starts there
    const dt = Math.min(0.1, Math.max(0, (now - lastNow.current) / 1000));
    lastNow.current = now;
    const k = 1 - Math.exp(-dt * 10);
    let moving = false;
    const seen = new Set<string>();
    floatingCards = placed.map((p) => {
      seen.add(p.id);
      slots.current[p.id] = p.slot;
      const cur = pos.current[p.id] ?? { x: p.rect.x, y: p.rect.y };
      cur.x += (p.rect.x - cur.x) * k;
      cur.y += (p.rect.y - cur.y) * k;
      if (Math.abs(p.rect.x - cur.x) + Math.abs(p.rect.y - cur.y) > 0.6) moving = true;
      pos.current[p.id] = cur;
      const o = p.id as DriveOverlay;
      return {
        id: o,
        x: cur.x,
        y: cur.y,
        ctx: { t, tel, facts, setup, shape, acts, open: open(o) },
        arrows: specs.find((sp) => sp.id === p.id)?.targets ?? [],
      };
    });
    for (const key of Object.keys(pos.current)) if (!seen.has(key)) delete pos.current[key];
    live.current = !reduced && (moving || shown.length > 0);
  } else {
    live.current = false;
  }

  // ---- the column: the cabin camera (the open cards) and a narrow window (one line)
  const focus = column ? null : overlays.reduce((best, o) => (raw[o] > raw[best] ? o : best), overlays[0]);
  const rail: { id: DriveOverlay; y: number; ctx: TileCtx; chip: boolean }[] = [];
  if (!floating) {
    let y = introShown ? (INTRO_H + GAP) * (1 - introExit) : 0;
    for (const o of overlays) {
      if (focus !== null ? o !== focus : open(o) < 0.02) continue;
      const ctx: TileCtx = { t, tel, facts, setup, shape, acts, open: column ? open(o) : 0 };
      rail.push({ id: o, y, ctx, chip: !column });
      y += HEAD + (column ? TILES[o].body * open(o) : 0) + GAP;
    }
  }

  return (
    <>
      {cap && <StageCaption cap={cap} t={t} column={column} still={reduced} vh={vh} />}
      {floating && frame && (
        <div className="pointer-events-none absolute inset-0 z-10" role="group" aria-label="Live data from the run">
          <svg className="absolute inset-0 h-full w-full" aria-hidden>
            {floatingCards.map((f) =>
              f.arrows.map((tg, i) => (
                <Arrow
                  key={`${f.id}-${i}`}
                  id={f.id}
                  rect={{ x: f.x, y: f.y, w: RAIL_W, h: HEAD + TILES[f.id].body * f.ctx.open }}
                  target={tg}
                  open={f.ctx.open}
                  now={now}
                  still={reduced}
                />
              )),
            )}
          </svg>
          {floatingCards.map((f) => (
            <Tile key={f.id} id={f.id} c={f.ctx} x={f.x} y={f.y} />
          ))}
          {introShown && (
            <div className={`absolute left-3 ${BELOW_TOP}`} style={{ width: RAIL_W, opacity: 1 - introExit, transform: `translateY(${-introExit * 14}px)` }}>
              <Intro vehicle={vehicle} age={reduced ? 9 : intro} />
            </div>
          )}
        </div>
      )}
      {!floating && (
        <div role="group" aria-label="Live data from the run" className={`pointer-events-none absolute left-3 z-10 ${BELOW_TOP}`} style={{ width: RAIL_W, marginTop: column ? 0 : 44 }}>
          {introShown && (
            <div style={{ opacity: 1 - introExit, transform: `translateY(${-introExit * 14}px)` }}>
              <Intro vehicle={vehicle} age={reduced ? 9 : intro} />
            </div>
          )}
          {rail.map((r) => (
            <Tile key={r.id} id={r.id} c={r.ctx} x={0} y={r.y} chip={r.chip} />
          ))}
        </div>
      )}
    </>
  );
}
