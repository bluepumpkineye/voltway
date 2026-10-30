'use client';

import React from 'react';
import type { DriveOverlay } from '@/data/vehicles/schema';
import { spotlight, wheelLook, wheelsOf, type Act, type RunShape } from '@/lib/tech/drive-beats';
import type { DriveFacts, DriveTelemetry } from '@/lib/tech/drive-run';
import type { DriveSetup } from '@/lib/tech/drive-setup';
import { clamp, countTo, Easing, flash, fmt, interpolate, spring, SPRINGS } from '@/lib/tech/motion';

/**
 * The eight instruments of the Drive tab as moving pictures, one tile each (the rail of tiles is DriveMotion.tsx). A tile is a
 * line of live figures when it is shut and its own animation when it is open: what it draws is a function of the run's playhead
 * and of how open it is, nothing more, so a scrub or a pause is drawn exactly (src/lib/tech/motion.ts: no CSS transitions).
 * Every figure is the run's own readout (`DriveTelemetry`, drive-run.ts); the pictures only show it.
 */

export const AMBER = '#fbbf24';
export const CYAN = '#38bdf8';
export const GREEN = '#34d399';
export const RED = '#ff5a5a';
const INK = 'rgba(255,255,255,0.94)';
const DIM = 'rgba(255,255,255,0.58)';
const FAINT = 'rgba(255,255,255,0.14)';

export interface TileCtx {
  t: number;
  tel: DriveTelemetry;
  facts: DriveFacts;
  setup: DriveSetup;
  shape: RunShape;
  acts: Act[];
  /** how open the tile is, 0..1 */
  open: number;
}

export interface TileDef {
  id: DriveOverlay;
  title: (c: Pick<TileCtx, 'facts'>) => string;
  /** the open body's height, px (the tile is `HEAD` taller than that, shut or open) */
  body: number;
  /** the live figure of the shut tile */
  chip: (c: TileCtx) => { value: string; unit?: string; color?: string };
  Body: (p: { c: TileCtx }) => React.JSX.Element;
}

/** The inner width of a tile's body, px. */
export const BODY_W = 268;

/** The progress of an inner part of an open tile: 0 until `a`, 1 from `b` of the tile's opening. */
const sub = (open: number, a: number, b: number) => interpolate(open, [a, b], [0, 1], { easing: Easing.outCubic });

const polar = (cx: number, cy: number, r: number, deg: number): [number, number] => [cx + r * Math.cos((deg * Math.PI) / 180), cy + r * Math.sin((deg * Math.PI) / 180)];
const arc = (cx: number, cy: number, r: number, a0: number, a1: number) => {
  const [x0, y0] = polar(cx, cy, r, a0);
  const [x1, y1] = polar(cx, cy, r, a1);
  return `M${x0.toFixed(2)} ${y0.toFixed(2)} A${r} ${r} 0 ${Math.abs(a1 - a0) > 180 ? 1 : 0} ${a1 > a0 ? 1 : 0} ${x1.toFixed(2)} ${y1.toFixed(2)}`;
};

const mix = (a: string, b: string, k: number) => {
  const p = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const [r1, g1, b1] = p(a);
  const [r2, g2, b2] = p(b);
  const m = (x: number, y: number) => Math.round(x + (y - x) * k);
  return `rgb(${m(r1, r2)},${m(g1, g2)},${m(b1, b2)})`;
};

// ------------------------------------------------------------------------------------------- small parts

function Read({ label, value, unit, color, size = 17 }: { label: string; value: string; unit?: string; color?: string; size?: number }) {
  return (
    <div className="min-w-0">
      <div className="text-[9px] font-semibold uppercase tracking-[0.1em] text-white/55">{label}</div>
      <div className="tnum font-semibold leading-tight" style={{ fontSize: size, color }}>
        {value}
        {unit && <span className="ml-0.5 text-[10px] font-normal text-white/55">{unit}</span>}
      </div>
    </div>
  );
}

function Meter({ v, max, color, signed = false }: { v: number; max: number; color: string; signed?: boolean }) {
  const x = clamp(v / Math.max(max, 1e-6), signed ? -1 : 0, 1);
  return (
    <div className="relative h-1 w-full overflow-hidden rounded-full bg-white/15">
      {signed && <span className="absolute left-1/2 top-0 h-full w-px bg-white/40" />}
      <span
        className="absolute top-0 h-full rounded-full"
        style={signed ? { left: `${50 + Math.min(0, x) * 50}%`, width: `${Math.abs(x) * 50}%`, background: color } : { left: 0, width: `${x * 100}%`, background: color }}
      />
    </div>
  );
}

function Note({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <p className="text-[10px] leading-snug text-white/60" style={style}>
      {children}
    </p>
  );
}

const sgn = (x: number, digits = 1) => `${x >= 0 ? '+' : '−'}${fmt(Math.abs(x), digits)}`;

// ------------------------------------------------------------------------------------------- power

const peakOf = (c: TileCtx) => Math.max(c.facts.modePeakKw, 1);

function PowerBody({ c }: { c: TileCtx }) {
  const { tel, facts, setup, shape, t, open } = c;
  const peakKw = peakOf(c);
  const peakNm = setup.input.peakNm;
  const regen = tel.powerKw < 0;
  const colour = regen ? GREEN : AMBER;
  const roll = sub(open, 0.15, 1);
  const frac = clamp(Math.abs(tel.powerKw) / peakKw) * roll;
  const reached = shape.peakKw.kw > peakKw * 0.9 && t >= shape.peakKw.t;
  const burst = reached ? flash(t, shape.peakKw.t, 0.9) : 0;
  const pop = reached ? spring(t - shape.peakKw.t, SPRINGS.pop) : 0;
  const CX = 54;
  const CY = 52;
  const [mx, my] = polar(CX, CY, 40, 135 + 270 * clamp(shape.peakKw.kw / peakKw));
  const full = arc(CX, CY, 40, 135, 405);
  const ticks = Array.from({ length: 11 }, (_, i) => {
    const a = 135 + 27 * i;
    const [x0, y0] = polar(CX, CY, 31, a);
    const [x1, y1] = polar(CX, CY, i % 5 === 0 ? 26 : 28, a);
    return <line key={i} x1={x0} y1={y0} x2={x1} y2={y1} stroke={FAINT} strokeWidth={1} />;
  });
  return (
    <div className="relative" style={{ height: 104 }}>
      <svg width={108} height={104} viewBox="0 0 108 104" className="absolute left-0 top-0" aria-hidden>
        {ticks}
        <path d={full} fill="none" stroke={FAINT} strokeWidth={7} strokeLinecap="round" />
        <path d={full} pathLength={100} fill="none" stroke={colour} strokeWidth={7} strokeLinecap="round" strokeDasharray={`${frac * 100} 100`} strokeOpacity={frac > 0.003 ? 1 : 0} />
        {burst > 0 && <circle cx={CX} cy={CY} r={40 + burst * 12} fill="none" stroke={colour} strokeWidth={2} strokeOpacity={burst * 0.8} />}
        {reached && <rect x={mx - 3} y={my - 3} width={6} height={6} fill={INK} transform={`rotate(45 ${mx} ${my}) translate(${mx} ${my}) scale(${0.4 + 0.6 * pop}) translate(${-mx} ${-my})`} />}
        <text x={CX} y={CY + 7} textAnchor="middle" fontSize={26} fontWeight={600} fill={INK} className="tnum">
          {fmt(Math.abs(tel.powerKw))}
        </text>
        <text x={CX} y={CY + 20} textAnchor="middle" fontSize={8.5} fill={DIM} letterSpacing={1}>
          {regen ? 'KW BACK IN' : 'KW'}
        </text>
        <text x={CX} y={CY + 46} textAnchor="middle" fontSize={8.5} fill={reached ? AMBER : DIM} className="tnum">
          {reached ? `PEAK ${fmt(shape.peakKw.kw)}` : `OF ${fmt(countTo(facts.modePeakKw, sub(open, 0.3, 1)))}`}
        </text>
      </svg>
      <div className="absolute top-0 grid gap-2.5" style={{ left: 120, width: BODY_W - 120 }}>
        {peakNm !== undefined && (
          <div>
            <Read label="Torque" value={tel.torqueNm === null ? '–' : fmt(Math.abs(tel.torqueNm))} unit={tel.torqueNm === null ? undefined : `Nm of ${fmt(peakNm)}`} size={15} />
            <div className="mt-0.5">
              <Meter v={Math.abs(tel.torqueNm ?? 0) * roll} max={peakNm} color={tel.torqueNm !== null && tel.torqueNm < 0 ? GREEN : CYAN} />
            </div>
          </div>
        )}
        <div>
          <Read label="Acceleration" value={sgn(tel.g, 2)} unit="g" size={15} />
          <div className="mt-0.5">
            <Meter v={tel.g * roll} max={1.6} signed color={tel.g < 0 ? RED : CYAN} />
          </div>
        </div>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------------------------------- motors

const WHEEL_AT: [number, number][] = [
  [3, 14],
  [52, 14],
  [3, 86],
  [52, 86],
];

/** Where a motor of the run stands on the little car from above (front is up), and the wheels it turns. */
function motorAt(m: DriveFacts['motors'][number]): { x: number; y: number } {
  const y = m.axle === 'front' ? 24 : 98;
  return { x: m.side === 'left' ? 21 : m.side === 'right' ? 43 : 32, y };
}

function MotorsBody({ c }: { c: TileCtx }) {
  const { tel, facts, t, open, acts } = c;
  const ms = facts.motors;
  const look = wheelLook(facts, tel, acts, t);
  const hasRear = ms.some((m) => m.axle === 'rear');
  const regen = tel.powerKw < 0;
  const peak = peakOf(c);
  const level = clamp(Math.abs(tel.powerKw) / peak);
  const cycle = (tel.energyWh - tel.regenWh) / 14;
  const frontColour = hasRear ? CYAN : AMBER;
  const wheelColour = (i: number) => {
    let col: string = i < 2 ? frontColour : AMBER;
    if (look.regen[i] > 0) col = mix(i < 2 ? frontColour : AMBER, GREEN, look.regen[i]);
    if (look.brake[i] > 0) col = mix(i < 2 ? frontColour : AMBER, RED, look.brake[i]);
    return col;
  };
  const draw = sub(open, 0.1, 0.8);
  const spotted = spotlight(acts, t);

  return (
    <div className="relative" style={{ height: 122 }}>
      <svg width={64} height={120} viewBox="0 0 64 120" className="absolute left-0 top-0" aria-hidden>
        <rect x={10} y={4} width={44} height={112} rx={16} fill="rgba(255,255,255,0.05)" stroke={FAINT} />
        <rect x={20} y={36} width={24} height={46} rx={4} fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.28)" />
        <rect x={20} y={36} width={24} height={46} rx={4} fill={regen ? GREEN : AMBER} opacity={0.08 + 0.55 * level * draw} />
        {[0, 1, 2].map((k) => (
          <line key={k} x1={20} x2={44} y1={51 + k * 15} y2={51 + k * 15} stroke="rgba(255,255,255,0.14)" />
        ))}
        {ms.map((m, j) => {
          const p = motorAt(m);
          const share = tel.motorShare[j] ?? 0;
          const on = clamp(Math.abs(tel.motorKw[j] ?? 0) / Math.max(peak * 0.45, 1));
          const front = m.axle === 'front';
          const col = front && hasRear ? CYAN : AMBER;
          const batt = front ? 36 : 82;
          const targets = front ? [7.5, 56.5] : m.side === 'left' ? [7.5] : m.side === 'right' ? [56.5] : [7.5, 56.5];
          const wy = front ? 25 : 97;
          const lineProps = {
            stroke: regen ? GREEN : col,
            strokeDasharray: '3 4',
            strokeDashoffset: (regen ? 1 : -1) * cycle * 28,
            strokeLinecap: 'round' as const,
            strokeOpacity: (0.12 + 0.88 * on) * draw,
            strokeWidth: 0.9 + 2.4 * clamp(share * 1.6) * (0.4 + 0.6 * on),
          };
          return (
            <g key={m.id}>
              <line x1={p.x} y1={batt} x2={p.x} y2={p.y + (front ? 6 : -6)} {...lineProps} />
              {targets.map((x) => (
                <line key={x} x1={p.x} y1={p.y} x2={x} y2={wy} {...lineProps} />
              ))}
              <circle cx={p.x} cy={p.y} r={m.side ? 5 : 6.5} fill="rgba(15,18,24,0.9)" stroke={col} strokeWidth={1.2} strokeOpacity={0.5 + 0.5 * on} />
              <circle cx={p.x} cy={p.y} r={(m.side ? 5 : 6.5) * (0.35 + 0.65 * on)} fill={regen ? GREEN : col} opacity={0.85 * draw} />
            </g>
          );
        })}
        {WHEEL_AT.map(([x, y], i) => {
          const lit = look.lit[i];
          return (
            <g key={i}>
              <rect x={x - 1.5 * lit} y={y - 1.5 * lit} width={9 + 3 * lit} height={22 + 3 * lit} rx={3} fill={wheelColour(i)} opacity={(0.1 + 0.9 * lit) * draw} />
              <rect x={x} y={y} width={9} height={22} rx={2.5} fill="none" stroke="rgba(255,255,255,0.65)" strokeWidth={0.8} />
            </g>
          );
        })}
      </svg>
      <div className="absolute top-0 grid gap-2" style={{ left: 78, width: BODY_W - 78 }}>
        {ms.map((m, j) => {
          const share = tel.motorShare[j] ?? 0;
          const col = m.axle === 'front' && hasRear ? CYAN : AMBER;
          // the row of a motor whose wheels an act is not showing fades with them
          const spot = Math.max(...wheelsOf(m).map((i) => spotted[i]));
          return (
            <div key={m.id} style={{ opacity: sub(open, 0.1 + 0.08 * j, 0.6 + 0.08 * j) * (0.35 + 0.65 * clamp((spot - 0.16) / 0.84)) }}>
              <div className="flex items-baseline justify-between text-[10px] text-white/80">
                <span>{m.label}</span>
                <span className="tnum">
                  {fmt(share * 100)} % · {fmt(tel.motorKw[j] ?? 0)} kW
                </span>
              </div>
              <div className="mt-0.5">
                <Meter v={share} max={1} color={col} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const CAR_SIDE = 'M-48 12 L-46 0 Q-40 -10 -22 -12 L8 -13 Q30 -12 42 -2 L50 6 L50 12 Z';

// ------------------------------------------------------------------------------------------- suspension

function SuspensionBody({ c }: { c: TileCtx }) {
  const { tel, open, setup } = c;
  const names = ['FL', 'FR', 'RL', 'RR'];
  const draw = sub(open, 0.1, 0.8);
  return (
    <div className="relative" style={{ height: 104 }}>
      <div className="grid grid-cols-4 gap-1.5">
        {tel.corner.map((mm, i) => {
          const L = clamp(44 - mm * 0.4, 22, 54);
          const turns = 8;
          const pts = Array.from({ length: turns + 1 }, (_, k) => `${k === 0 || k === turns ? 20 : 20 + (k % 2 ? 9 : -9)} ${(5 + (L * k) / turns).toFixed(1)}`).join(' L');
          const col = mm >= 0 ? AMBER : CYAN;
          return (
            <div key={names[i]} className="flex flex-col items-center" style={{ opacity: draw }}>
              <div className="text-[9px] font-semibold tracking-[0.1em] text-white/55">{names[i]}</div>
              <svg width={40} height={64} viewBox="0 0 40 64" aria-hidden>
                <rect x={10} y={0} width={20} height={4} rx={1.5} fill="rgba(255,255,255,0.45)" />
                <path d={`M${pts}`} fill="none" stroke={col} strokeWidth={2} strokeLinejoin="round" />
                <rect x={8} y={5 + L} width={24} height={6} rx={2} fill={col} opacity={0.9} />
              </svg>
              <div className="tnum text-[11px] font-semibold leading-none" style={{ color: col }}>
                {sgn(mm, 0)}
                <span className="text-[9px] font-normal text-white/55"> mm</span>
              </div>
            </div>
          );
        })}
      </div>
      <Note style={{ position: 'absolute', bottom: 0, left: 0 }}>
        {setup.spec.chassis?.airSuspension ? 'Air springs · ' : ''}roll {sgn(tel.rollDeg, 1)}° · + compressed, − extended
      </Note>
    </div>
  );
}

// ------------------------------------------------------------------------------------------- brake

function BrakeBody({ c }: { c: TileCtx }) {
  const { tel, facts, open, shape, t } = c;
  const sum = facts.summary;
  const braking = tel.g < -0.05 && tel.speed > 0.5;
  const regen = braking ? clamp(tel.regenFrac) : 0;
  const stopM = sum.brakeM;
  const scaleM = Math.max(10, Math.ceil(((stopM ?? 40) * 1.12) / 5) * 5);
  const draw = sub(open, 0.1, 0.8);
  const x = (m: number) => 4 + clamp(m / scaleM) * 150 * draw;
  // the stop is stamped when the car comes to rest: the figure springs in and goes amber
  const stopT = shape.spans.stop?.[0]?.from;
  const stopped = stopM !== null && stopT !== undefined && t >= stopT;
  const pop = stopped ? spring(t - stopT, SPRINGS.pop) : 1;
  const R = 22;
  const donut = arc(228, 36, R, -90, 269.9);
  return (
    <div className="relative" style={{ height: 108 }}>
      <div className="absolute left-0 top-0" style={{ transform: `scale(${0.82 + 0.18 * pop})`, transformOrigin: 'left center' }}>
        <Read label="Brake distance" value={fmt(tel.brakeDistM, 1)} unit="m" size={26} color={stopped ? AMBER : braking ? RED : INK} />
      </div>
      <svg width={166} height={34} viewBox="0 0 166 34" className="absolute left-0" style={{ top: 46 }} aria-hidden>
        <line x1={4} y1={12} x2={154} y2={12} stroke={FAINT} strokeWidth={3} strokeLinecap="round" />
        {Array.from({ length: Math.floor(scaleM / 5) + 1 }, (_, k) => (
          <g key={k}>
            <line x1={x(k * 5)} y1={7} x2={x(k * 5)} y2={17} stroke="rgba(255,255,255,0.3)" />
            {k % 2 === 0 && (
              <text x={x(k * 5)} y={29} textAnchor="middle" fontSize={8} fill={DIM}>
                {k * 5}
              </text>
            )}
          </g>
        ))}
        <line x1={4} y1={12} x2={x(tel.brakeDistM)} y2={12} stroke={RED} strokeWidth={3} strokeLinecap="round" />
        <circle cx={x(tel.brakeDistM)} cy={12} r={4.5} fill={INK} />
        {stopM !== null && <line x1={x(stopM)} y1={3} x2={x(stopM)} y2={21} stroke={AMBER} strokeWidth={1.4} strokeDasharray="2 2" opacity={draw} />}
      </svg>
      <svg width={86} height={74} viewBox="186 0 86 74" className="absolute right-0 top-0" aria-hidden>
        <path d={donut} fill="none" stroke={FAINT} strokeWidth={6} />
        <path d={donut} pathLength={100} fill="none" stroke={GREEN} strokeWidth={6} strokeDasharray={`${regen * 100 * draw} 100`} strokeOpacity={regen > 0.003 ? 1 : 0} />
        <path d={donut} pathLength={100} fill="none" stroke={RED} strokeWidth={6} strokeDasharray={`${braking ? (1 - regen) * 100 * draw : 0} 100`} strokeDashoffset={-regen * 100 * draw} strokeOpacity={braking ? 1 : 0} />
        <text x={228} y={40} textAnchor="middle" fontSize={13} fontWeight={600} fill={INK} className="tnum">
          {fmt(regen * 100)}%
        </text>
        <text x={228} y={70} textAnchor="middle" fontSize={8} fill={DIM}>
          by the motors
        </text>
      </svg>
      <div className="absolute bottom-0 w-full">
        <Note>{stopM === null ? 'Switch on “Then stop” to see a full stop.' : `Stop from ${fmt(sum.brakeFromKmh ?? 0)} km/h: ${fmt(stopM, 1)} m in ${fmt(sum.brakeS ?? 0, 1)} s`}</Note>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------------------------------- energy

function EnergyBody({ c }: { c: TileCtx }) {
  const { tel, setup, open } = c;
  const capWh = setup.variant.battery.capacityKwh * 1000;
  const net = Math.max(tel.energyWh - tel.regenWh, 0);
  const lens = 0.02 * capWh;
  const draw = sub(open, 0.1, 0.8);
  const fill = clamp(net / lens) * draw;
  return (
    <div className="relative" style={{ height: 92 }}>
      <div className="grid grid-cols-3 gap-2">
        <Read label="Used" value={fmt(tel.energyWh)} unit="Wh" />
        <Read label="Recovered" value={fmt(tel.regenWh)} unit="Wh" color={tel.regenWh > 1 ? GREEN : undefined} />
        <Read label="Range cost" value={tel.rangeKm === null ? '–' : fmt(tel.rangeKm, 2)} unit={tel.rangeKm === null ? undefined : 'km'} />
      </div>
      <div className="mt-3" style={{ opacity: draw }}>
        <div className="mb-1 flex justify-between text-[9px] font-semibold uppercase tracking-[0.1em] text-white/55">
          <span>Top 2 % of the pack, magnified</span>
          <span className="tnum">{fmt((net / capWh) * 100, 2)} % used</span>
        </div>
        <div className="relative h-3 overflow-hidden rounded-md bg-white/12 ring-1 ring-white/20">
          <span className="absolute left-0 top-0 h-full rounded-md" style={{ width: `${(1 - fill) * 100}%`, background: `linear-gradient(90deg, ${AMBER}, #fde68a)` }} />
          <span className="absolute top-0 h-full w-px bg-white/70" style={{ left: `${(1 - fill) * 100}%` }} />
        </div>
        <Note style={{ marginTop: 4 }}>
          Of a {fmt(setup.variant.battery.capacityKwh)} kWh pack. Range at ordinary consumption.
        </Note>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------------------------------- aero

function AeroBody({ c }: { c: TileCtx }) {
  const { tel, setup, open } = c;
  const total = Math.max(Math.abs(tel.powerKw), 1);
  const share = tel.powerKw > 1 ? clamp(tel.dragKw / total) : 0;
  const draw = sub(open, 0.1, 0.8);
  const v = clamp(tel.speed / 220);
  // the streamlines run past the car as the road does: by the distance driven
  const flow = tel.distance * 1.6;
  const lines = [
    'M0 22 C40 22 56 4 110 4 C160 4 176 22 268 22',
    'M0 32 C40 32 62 14 112 14 C158 14 180 30 268 30',
    'M0 44 C60 44 90 44 134 44 L268 44',
    'M0 54 C60 56 100 58 140 58 C190 58 220 52 268 52',
  ];
  return (
    <div className="relative" style={{ height: 104 }}>
      <svg width={BODY_W} height={66} viewBox="0 0 268 70" className="absolute left-0 top-0" aria-hidden>
        {lines.map((d, k) => (
          <path key={k} d={d} fill="none" stroke={CYAN} strokeWidth={1.4} strokeLinecap="round" strokeDasharray="14 18" strokeDashoffset={-(flow + k * 9) % 32} strokeOpacity={(0.2 + 0.7 * v) * draw} />
        ))}
        <g transform="translate(70 12) scale(1.7)">
          <path d={CAR_SIDE} transform="translate(48 30)" fill="rgba(255,255,255,0.14)" stroke="rgba(255,255,255,0.75)" strokeWidth={0.8} />
        </g>
        <g opacity={draw}>
          <line x1={232} y1={36} x2={232 + clamp(tel.dragN / 1500) * 30} y2={36} stroke={RED} strokeWidth={3} strokeLinecap="round" />
          <path d={`M${232 + clamp(tel.dragN / 1500) * 30 - 5} 31 L${232 + clamp(tel.dragN / 1500) * 30 + 2} 36 L${232 + clamp(tel.dragN / 1500) * 30 - 5} 41`} fill="none" stroke={RED} strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" />
        </g>
      </svg>
      <div className="absolute bottom-0 grid w-full grid-cols-3 gap-2">
        <Read label="Drag force" value={fmt(tel.dragN)} unit="N" size={15} />
        <Read label="Drag power" value={fmt(tel.dragKw)} unit="kW" size={15} />
        <Read label="Of the power" value={fmt(share * 100)} unit="%" size={15} />
      </div>
      <div className="absolute right-0 top-0 text-right">
        <Note>{setup.spec.aero ? `Cd ${setup.spec.aero.cd}` : 'Drag'}</Note>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------------------------------- steering

function SteeringBody({ c }: { c: TileCtx }) {
  const { tel, facts, open } = c;
  const hasRear = facts.rearSteerMaxDeg > 0;
  const crab = tel.phase === 'crab';
  const draw = sub(open, 0.1, 0.8);
  const scale = Math.max(tel.steerScale, 1);
  const front = tel.steerFront * scale;
  const rear = tel.steerRear * scale;
  const L = 62;
  const track = 30;
  const wheels: [number, number, number][] = [
    [-track / 2, -L / 2, front],
    [track / 2, -L / 2, front],
    [-track / 2, L / 2, rear],
    [track / 2, L / 2, rear],
  ];
  // the curve being driven, as an arc ahead of the car (clamped so that a gentle one does not leave the picture)
  const rad = tel.radius !== null && tel.radius <= 150 ? clamp(tel.radius * 1.4, 26, 120) : null;
  const dir = tel.steerFront >= 0 ? 1 : -1;
  const far = tel.radius === null || tel.radius > 150;
  return (
    <div className="relative" style={{ height: 112 }}>
      <svg width={104} height={108} viewBox="-52 -54 104 108" className="absolute left-0 top-0" aria-hidden>
        {rad !== null && !crab && <path d={arc(dir * rad, -L / 2, rad, dir > 0 ? 180 : 0, dir > 0 ? 180 + 52 : -52)} fill="none" stroke={AMBER} strokeWidth={1.6} strokeDasharray="3 3" opacity={draw} />}
        <rect x={-12} y={-L / 2 - 6} width={24} height={L + 12} rx={9} fill="rgba(255,255,255,0.08)" stroke="rgba(255,255,255,0.55)" />
        <line x1={0} y1={-L / 2} x2={0} y2={L / 2} stroke={FAINT} strokeDasharray="2 3" />
        {wheels.map(([x, y, a], i) => (
          <g key={i} transform={`translate(${x} ${y}) rotate(${a * draw})`}>
            <rect x={-3.6} y={-8.5} width={7.2} height={17} rx={2} fill={i < 2 ? CYAN : AMBER} opacity={0.35 + 0.65 * draw} stroke="rgba(255,255,255,0.85)" strokeWidth={0.8} />
          </g>
        ))}
        {crab && (
          <g stroke={INK} strokeWidth={1.6} strokeLinecap="round" fill="none" opacity={draw}>
            <path d="M22 -2 L40 -2 M35 -7 L40 -2 L35 3" />
          </g>
        )}
      </svg>
      <div className="absolute top-0 grid grid-cols-2 gap-x-3 gap-y-1.5" style={{ left: 112, width: BODY_W - 112 }}>
        <Read label="Front" value={sgn(tel.steerFront, 1)} unit="°" size={15} />
        <Read label="Rear" value={hasRear ? sgn(tel.steerRear, 1) : '0.0'} unit="°" size={15} />
        {crab ? <Read label="Crab" value={fmt(Math.abs(tel.crabDeg), 1)} unit="°" size={15} /> : <Read label="Radius" value={far ? '–' : fmt(tel.radius ?? 0, 1)} unit={far ? undefined : 'm'} size={15} />}
        {hasRear && !crab && <Read label="Front only" value={fmt(Math.abs(tel.frontOnly), 1)} unit="°" size={15} />}
      </div>
      <div className="absolute bottom-0" style={{ left: 112, width: BODY_W - 112 }}>
        <Note>{scale > 1 ? `Drawn ${scale} times wider than they turn, so that it shows.` : hasRear ? (crab ? 'All four wheels turn the same way.' : `Rear wheels turn up to ${facts.rearSteerMaxDeg}°.`) : 'Front wheels steer the car.'}</Note>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------------------------------- the set

const frontShare = (c: TileCtx) => c.facts.motors.reduce((a, m, j) => a + (m.axle === 'front' ? (c.tel.motorShare[j] ?? 0) : 0), 0);

export const TILES: Record<DriveOverlay, TileDef> = {
  power: {
    id: 'power',
    title: () => 'Power & torque',
    body: 104,
    chip: (c) => ({ value: fmt(Math.abs(c.tel.powerKw)), unit: c.tel.powerKw < 0 ? 'kW back' : 'kW', color: c.tel.powerKw < 0 ? GREEN : undefined }),
    Body: PowerBody,
  },
  motors: {
    id: 'motors',
    title: ({ facts }) => (facts.motors.length > 2 ? 'Tri-motor torque flow' : facts.motors.length === 2 ? 'Dual-motor torque flow' : 'Motor'),
    body: 122,
    chip: (c) => (c.facts.motors.length > 1 ? { value: `F ${fmt(frontShare(c) * 100)} · R ${fmt((1 - frontShare(c)) * 100)}`, unit: '%' } : { value: fmt(Math.abs(c.tel.powerKw)), unit: 'kW' }),
    Body: MotorsBody,
  },
  suspension: {
    id: 'suspension',
    title: () => 'Suspension',
    body: 104,
    chip: (c) => ({ value: `±${fmt(Math.max(...c.tel.corner.map(Math.abs)))}`, unit: 'mm' }),
    Body: SuspensionBody,
  },
  brake: {
    id: 'brake',
    title: () => 'Braking',
    body: 108,
    chip: (c) => ({ value: fmt(Math.max(0, -c.tel.g), 2), unit: 'g', color: c.tel.g < -0.05 ? RED : undefined }),
    Body: BrakeBody,
  },
  energy: {
    id: 'energy',
    title: () => 'Energy & range',
    body: 92,
    chip: (c) => ({ value: fmt(c.tel.energyWh), unit: 'Wh' }),
    Body: EnergyBody,
  },
  aero: {
    id: 'aero',
    title: () => 'Aero drag',
    body: 104,
    chip: (c) => ({ value: fmt(c.tel.dragN), unit: 'N' }),
    Body: AeroBody,
  },
  steering: {
    id: 'steering',
    title: ({ facts }) => (facts.rearSteerMaxDeg > 0 ? 'Rear-wheel steering' : 'Steering'),
    body: 112,
    chip: (c) => ({ value: sgn(c.tel.steerFront, 1), unit: '°' }),
    Body: SteeringBody,
  },
};

/** The colour that stands for each tile in its header. */
export const ACCENT: Record<DriveOverlay, string> = {
  power: AMBER,
  motors: AMBER,
  suspension: CYAN,
  brake: RED,
  energy: GREEN,
  aero: CYAN,
  steering: AMBER,
};
