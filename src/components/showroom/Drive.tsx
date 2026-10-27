'use client';

import React from 'react';
import Link from 'next/link';
import type { DriveOverlay, Vehicle } from '@/data/vehicles/schema';
import { vehicles } from '@/data/vehicles';
import { techClock, useTechClock } from '@/lib/tech/clock';
import { soundOn, subscribeSound } from '@/lib/sound/engine';
import { useRuntime } from '@/lib/tech/session';
import { DRIVE_CAMERAS, camerasOf, driveSetup, type DriveSetup } from '@/lib/tech/drive-setup';
import { HOLD, pullCurve, type DriveFacts, type DriveTelemetry } from '@/lib/tech/drive-run';
import { rivalEnv, rivalOf, rivalTrack } from '@/lib/tech/drive-rival';
import { useVehicleStore } from '@/store/vehicle-store';
import { BELOW_TOP, FOCUS, GLASS, PANEL } from './Chrome';

/** How wide the Drive tab's panel is in a column at the right of a wide window, px. */
export const DRIVE_COLUMN_W = 340;

const f0 = (x: number) => Math.round(x).toString();
const f1 = (x: number) => x.toFixed(1);
const f2 = (x: number) => x.toFixed(2);
const clamp = (x: number, a: number, b: number) => Math.min(b, Math.max(a, x));

// ------------------------------------------------------------------------------------------- small parts

function Seg<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: { id: T; label: string; hint?: string }[];
  value: T;
  onChange: (id: T) => void;
}) {
  return (
    <div>
      <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.08em] text-neutral-500">{label}</div>
      <div role="group" aria-label={label} className="flex flex-wrap gap-1">
        {options.map((o) => (
          <button
            key={o.id}
            type="button"
            aria-pressed={o.id === value}
            title={o.hint}
            onClick={() => onChange(o.id)}
            className={`rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors ${FOCUS} ${
              o.id === value ? 'bg-neutral-900 text-white' : 'bg-black/[0.05] text-neutral-600 hover:bg-black/10 hover:text-neutral-900'
            }`}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function Card({ title, lead, children }: { title: string; lead?: boolean; children: React.ReactNode }) {
  return (
    <section className={`rounded-xl px-3 py-2.5 ${lead ? 'bg-neutral-900 text-white' : 'bg-black/[0.04] text-neutral-800'}`}>
      <h3 className={`mb-1.5 text-[10px] font-semibold uppercase tracking-[0.08em] ${lead ? 'text-neutral-400' : 'text-neutral-500'}`}>{title}</h3>
      {children}
    </section>
  );
}

/** A horizontal bar from 0 (or from the middle, if signed) with a fill that follows the value. */
function Bar({ value, max, color = 'bg-cyan-500', signed = false, dark = false }: { value: number; max: number; color?: string; signed?: boolean; dark?: boolean }) {
  const x = clamp(value / max, signed ? -1 : 0, 1);
  return (
    <div className={`relative h-1.5 w-full overflow-hidden rounded-full ${dark ? 'bg-white/15' : 'bg-black/10'}`}>
      {signed && <span className={`absolute left-1/2 top-0 h-full w-px ${dark ? 'bg-white/40' : 'bg-black/30'}`} />}
      <span
        className={`absolute top-0 h-full rounded-full transition-[width,left] duration-100 ease-linear ${color}`}
        style={signed ? { left: `${50 + Math.min(0, x) * 50}%`, width: `${Math.abs(x) * 50}%` } : { left: 0, width: `${x * 100}%` }}
      />
    </div>
  );
}

function Stat({ label, value, unit, dark = false }: { label: string; value: string; unit?: string; dark?: boolean }) {
  return (
    <div className="min-w-0">
      <div className={`text-[10px] ${dark ? 'text-neutral-400' : 'text-neutral-500'}`}>{label}</div>
      <div className="tnum text-[17px] font-semibold leading-tight">
        {value}
        {unit && <span className={`ml-0.5 text-[11px] font-normal ${dark ? 'text-neutral-400' : 'text-neutral-500'}`}>{unit}</span>}
      </div>
    </div>
  );
}

/** The car from above: four wheels, each turned by its angle and shaded by how hard it is driven. */
function TopCar({ steer, drive, dark = false }: { steer: [number, number, number, number]; drive: [number, number, number, number]; dark?: boolean }) {
  const L = 62;
  const track = 30;
  const spots: [number, number][] = [
    [-track / 2, -L / 2],
    [track / 2, -L / 2],
    [-track / 2, L / 2],
    [track / 2, L / 2],
  ];
  return (
    <svg viewBox="-34 -48 68 96" className="h-[88px] w-[62px] shrink-0" aria-hidden>
      <rect x={-12} y={-L / 2 - 6} width={24} height={L + 12} rx={9} fill={dark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.07)'} stroke={dark ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.25)'} />
      <line x1={0} y1={-L / 2} x2={0} y2={L / 2} stroke={dark ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.12)'} strokeDasharray="2 3" />
      {spots.map(([x, y], i) => (
        <g key={i} transform={`translate(${x} ${y}) rotate(${steer[i]})`}>
          <rect
            x={-3.4}
            y={-8}
            width={6.8}
            height={16}
            rx={2}
            fill={`rgba(245,158,11,${0.12 + 0.88 * clamp(drive[i], 0, 1)})`}
            stroke={dark ? 'rgba(255,255,255,0.75)' : 'rgba(0,0,0,0.55)'}
            strokeWidth={0.8}
          />
        </g>
      ))}
    </svg>
  );
}

// ------------------------------------------------------------------------------------------- the instruments

interface Ctx {
  tel: DriveTelemetry;
  facts: DriveFacts;
  setup: DriveSetup;
  peakKw: number;
}

function PowerCard({ c, lead }: { c: Ctx; lead: boolean }) {
  const { tel, peakKw, setup } = c;
  const peakNm = setup.input.peakNm;
  const regen = tel.powerKw < 0;
  return (
    <Card title="Power & torque" lead={lead}>
      <div className="grid grid-cols-3 gap-2">
        <Stat dark={lead} label={regen ? 'Recovered' : 'Power'} value={f0(Math.abs(tel.powerKw))} unit="kW" />
        <Stat dark={lead} label="Torque" value={tel.torqueNm === null ? '–' : f0(Math.abs(tel.torqueNm))} unit={tel.torqueNm === null ? undefined : 'Nm'} />
        <Stat dark={lead} label="Accel" value={f2(tel.g)} unit="g" />
      </div>
      <div className="mt-2 space-y-1.5">
        <Bar dark={lead} value={Math.abs(tel.powerKw)} max={peakKw} color={regen ? 'bg-emerald-500' : 'bg-amber-400'} />
        {peakNm !== undefined && <Bar dark={lead} value={Math.abs(tel.torqueNm ?? 0)} max={peakNm} color={tel.torqueNm !== null && tel.torqueNm < 0 ? 'bg-emerald-500' : 'bg-cyan-400'} />}
        <Bar dark={lead} value={tel.g} max={1.6} signed color={tel.g < 0 ? 'bg-rose-500' : 'bg-cyan-400'} />
      </div>
      <p className={`mt-1.5 text-[10px] ${lead ? 'text-neutral-400' : 'text-neutral-500'}`}>
        Bars: power of {f0(peakKw)} kW, torque of {peakNm ?? '–'} Nm, acceleration.
      </p>
    </Card>
  );
}

function WeightCard({ c, lead }: { c: Ctx; lead: boolean }) {
  const { tel } = c;
  const rear = tel.axleRear * 100;
  const squat = (tel.corner[2] + tel.corner[3]) / 2;
  return (
    <Card title="Weight transfer & squat" lead={lead}>
      <div className="flex items-center gap-3">
        <svg viewBox="-60 -26 120 52" className="h-[52px] w-[110px] shrink-0" aria-hidden>
          <line x1={-58} y1={20} x2={58} y2={20} stroke={lead ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.25)'} />
          <g transform={`rotate(${-tel.pitchDeg * 6} 0 6)`}>
            <path
              d="M-48 12 L-46 0 Q-40 -10 -22 -12 L8 -13 Q30 -12 42 -2 L50 6 L50 12 Z"
              fill={lead ? 'rgba(255,255,255,0.14)' : 'rgba(0,0,0,0.08)'}
              stroke={lead ? 'rgba(255,255,255,0.6)' : 'rgba(0,0,0,0.5)'}
              strokeWidth={1.2}
            />
          </g>
          <circle cx={-32} cy={14} r={6} fill="none" stroke={lead ? '#fff' : '#111'} strokeWidth={1.4} />
          <circle cx={34} cy={14} r={6} fill="none" stroke={lead ? '#fff' : '#111'} strokeWidth={1.4} />
        </svg>
        <div className="grid flex-1 grid-cols-2 gap-x-2">
          <Stat dark={lead} label="Pitch" value={`${tel.pitchDeg >= 0 ? '+' : ''}${f1(tel.pitchDeg)}`} unit="°" />
          <Stat dark={lead} label="Rear squat" value={f0(squat)} unit="mm" />
        </div>
      </div>
      <div className="mt-2">
        <div className={`mb-0.5 flex justify-between text-[10px] ${lead ? 'text-neutral-400' : 'text-neutral-500'}`}>
          <span className="tnum">Front {f0(100 - rear)} %</span>
          <span className="tnum">Rear {f0(rear)} %</span>
        </div>
        <div className={`flex h-1.5 overflow-hidden rounded-full ${lead ? 'bg-white/15' : 'bg-black/10'}`}>
          <span className="h-full bg-sky-400 transition-[width] duration-100 ease-linear" style={{ width: `${100 - rear}%` }} />
          <span className="h-full bg-amber-400 transition-[width] duration-100 ease-linear" style={{ width: `${rear}%` }} />
        </div>
      </div>
    </Card>
  );
}

function MotorsCard({ c, lead }: { c: Ctx; lead: boolean }) {
  const { tel, facts, peakKw, setup } = c;
  const ms = facts.motors;
  const modePeak = peakKw * setup.input.powerFrac;
  const level = (id: string) => {
    const j = ms.findIndex((m) => m.id === id);
    return j < 0 ? 0 : clamp(tel.motorKw[j] / Math.max(modePeak * 0.55, 1), 0, 1);
  };
  const wheel = (corner: 0 | 1 | 2 | 3) => {
    const front = corner < 2;
    const left = corner % 2 === 0;
    if (front) return level('front');
    return Math.max(level(left ? 'rear-left' : 'rear-right'), level('rear'));
  };
  const rl = ms.findIndex((m) => m.id === 'rear-left');
  const rr = ms.findIndex((m) => m.id === 'rear-right');
  const showSplit = rl >= 0 && rr >= 0;
  return (
    <Card title={ms.length > 2 ? 'Tri-motor torque flow' : ms.length === 2 ? 'Dual-motor torque flow' : 'Motor'} lead={lead}>
      <div className="flex items-center gap-3">
        <TopCar dark={lead} steer={[0, 0, 0, 0]} drive={[wheel(0), wheel(1), wheel(2), wheel(3)]} />
        <div className="min-w-0 flex-1 space-y-1.5">
          {ms.map((m, j) => (
            <div key={m.id}>
              <div className={`flex justify-between text-[10px] ${lead ? 'text-neutral-300' : 'text-neutral-600'}`}>
                <span>{m.label}</span>
                <span className="tnum">
                  {f0(tel.motorShare[j] * 100)} % · {f0(tel.motorKw[j])} kW
                </span>
              </div>
              <Bar dark={lead} value={tel.motorShare[j]} max={1} color="bg-amber-400" />
            </div>
          ))}
        </div>
      </div>
      {showSplit && (
        <p className={`mt-1.5 text-[10px] ${lead ? 'text-neutral-400' : 'text-neutral-500'}`}>
          {tel.phase === 'crab'
            ? 'The rear motors turn the two wheels at different rates, a differential that holds the crab angle.'
            : Math.abs(tel.vectoring) > 0.04
              ? `Torque vectoring: the rear motors favour the ${tel.vectoring > 0 ? 'right' : 'left'} wheel, ${f0(50 + Math.abs(tel.vectoring) * 50)} to ${f0(50 - Math.abs(tel.vectoring) * 50)}.`
              : 'Driving straight, the rear motors share equally.'}
        </p>
      )}
    </Card>
  );
}

function SuspensionCard({ c, lead }: { c: Ctx; lead: boolean }) {
  const { tel, setup } = c;
  const names = ['Front left', 'Front right', 'Rear left', 'Rear right'];
  return (
    <Card title="Suspension" lead={lead}>
      <div className="grid grid-cols-2 gap-x-3 gap-y-1.5">
        {tel.corner.map((mm, i) => (
          <div key={names[i]}>
            <div className={`flex justify-between text-[10px] ${lead ? 'text-neutral-300' : 'text-neutral-600'}`}>
              <span>{names[i]}</span>
              <span className="tnum">
                {mm >= 0 ? '+' : ''}
                {f0(mm)} mm
              </span>
            </div>
            <Bar dark={lead} value={mm} max={45} signed color={mm >= 0 ? 'bg-amber-400' : 'bg-sky-400'} />
          </div>
        ))}
      </div>
      <p className={`mt-1.5 text-[10px] ${lead ? 'text-neutral-400' : 'text-neutral-500'}`}>
        {setup.spec.chassis?.airSuspension ? 'Air suspension. ' : ''}+ compressed, − extended. Body roll {tel.rollDeg >= 0 ? '+' : ''}
        {f1(tel.rollDeg)}°.
      </p>
    </Card>
  );
}

function BrakeCard({ c, lead }: { c: Ctx; lead: boolean }) {
  const { tel, facts } = c;
  const braking = tel.g < -0.05 && tel.speed > 0.5;
  const regen = braking ? tel.regenFrac : 0;
  const sum = facts.summary;
  return (
    <Card title="Braking" lead={lead}>
      <div className="grid grid-cols-3 gap-2">
        <Stat dark={lead} label="Decel" value={braking ? f2(-tel.g) : '0.00'} unit="g" />
        <Stat dark={lead} label="Distance" value={f1(tel.brakeDistM)} unit="m" />
        <Stat dark={lead} label="Motors" value={f0(regen * 100)} unit="%" />
      </div>
      <div className="mt-2">
        <div className={`mb-0.5 flex justify-between text-[10px] ${lead ? 'text-neutral-400' : 'text-neutral-500'}`}>
          <span>Regeneration</span>
          <span>Friction brakes</span>
        </div>
        <div className={`flex h-1.5 overflow-hidden rounded-full ${lead ? 'bg-white/15' : 'bg-black/10'}`}>
          <span className="h-full bg-emerald-500 transition-[width] duration-100 ease-linear" style={{ width: `${regen * 100}%` }} />
          <span className="h-full bg-rose-500 transition-[width] duration-100 ease-linear" style={{ width: braking ? `${(1 - regen) * 100}%` : '0%' }} />
        </div>
      </div>
      <p className={`mt-1.5 text-[10px] ${lead ? 'text-neutral-400' : 'text-neutral-500'}`}>
        {sum.brakeM === null
          ? 'Switch on “Then stop” to see a full stop.'
          : `Stop from ${f0(sum.brakeFromKmh ?? 0)} km/h: ${f1(sum.brakeM)} m in ${f1(sum.brakeS ?? 0)} s.`}
      </p>
    </Card>
  );
}

function EnergyCard({ c, lead }: { c: Ctx; lead: boolean }) {
  const { tel, setup } = c;
  const net = tel.energyWh - tel.regenWh;
  return (
    <Card title="Energy & range" lead={lead}>
      <div className="grid grid-cols-3 gap-2">
        <Stat dark={lead} label="Used" value={f0(tel.energyWh)} unit="Wh" />
        <Stat dark={lead} label="Recovered" value={f0(tel.regenWh)} unit="Wh" />
        <Stat dark={lead} label="Range cost" value={tel.rangeKm === null ? '–' : f2(tel.rangeKm)} unit={tel.rangeKm === null ? undefined : 'km'} />
      </div>
      <div className="mt-2">
        <Bar dark={lead} value={Math.max(net, 0)} max={Math.max(setup.variant.battery.capacityKwh * 5, 1)} color="bg-amber-400" />
      </div>
      <p className={`mt-1.5 text-[10px] ${lead ? 'text-neutral-400' : 'text-neutral-500'}`}>
        Of a {f0(setup.variant.battery.capacityKwh)} kWh pack; the range is what the same energy drives at the car’s ordinary consumption.
      </p>
    </Card>
  );
}

function AeroCard({ c, lead }: { c: Ctx; lead: boolean }) {
  const { tel, setup } = c;
  const total = Math.max(Math.abs(tel.powerKw), 1);
  const share = tel.powerKw > 1 ? clamp(tel.dragKw / total, 0, 1) : 0;
  return (
    <Card title="Aero drag" lead={lead}>
      <div className="grid grid-cols-3 gap-2">
        <Stat dark={lead} label="Drag force" value={f0(tel.dragN)} unit="N" />
        <Stat dark={lead} label="Drag power" value={f0(tel.dragKw)} unit="kW" />
        <Stat dark={lead} label="Speed" value={f0(tel.speed)} unit="km/h" />
      </div>
      <div className="mt-2">
        <Bar dark={lead} value={tel.dragN} max={1500} color="bg-sky-400" />
      </div>
      <p className={`mt-1.5 text-[10px] ${lead ? 'text-neutral-400' : 'text-neutral-500'}`}>
        {setup.spec.aero ? `Cd ${setup.spec.aero.cd}. ` : ''}Drag grows with the square of the speed; now it takes {f0(share * 100)} % of the power.
      </p>
    </Card>
  );
}

function SteeringCard({ c, lead }: { c: Ctx; lead: boolean }) {
  const { tel, facts } = c;
  const hasRear = facts.rearSteerMaxDeg > 0;
  const crab = tel.phase === 'crab';
  // the axle angles are enough for the drawing (the car's own wheels take the planner's per-corner angles)
  const steer: [number, number, number, number] = [tel.steerFront, tel.steerFront, tel.steerRear, tel.steerRear];
  const active = tel.phase === 'slalom' || tel.phase === 'crab';
  return (
    <Card title={hasRear ? 'Rear-wheel steering' : 'Steering'} lead={lead}>
      <div className="flex items-center gap-3">
        <TopCar dark={lead} steer={steer} drive={[0, 0, 0, 0]} />
        <div className="grid flex-1 grid-cols-2 gap-x-2 gap-y-1">
          <Stat dark={lead} label="Front" value={`${tel.steerFront >= 0 ? '+' : ''}${f1(tel.steerFront)}`} unit="°" />
          <Stat dark={lead} label="Rear" value={hasRear ? `${tel.steerRear >= 0 ? '+' : ''}${f1(tel.steerRear)}` : '0.0'} unit="°" />
          {crab ? (
            <Stat dark={lead} label="Crab angle" value={f1(Math.abs(tel.crabDeg))} unit="°" />
          ) : (
            <Stat dark={lead} label="Curve radius" value={tel.radius === null || tel.radius > 150 ? '–' : f1(tel.radius)} unit={tel.radius === null || tel.radius > 150 ? undefined : 'm'} />
          )}
          {hasRear && !crab && <Stat dark={lead} label="Front alone" value={f1(Math.abs(tel.frontOnly))} unit="°" />}
        </div>
      </div>
      <p className={`mt-1.5 text-[10px] ${lead ? 'text-neutral-400' : 'text-neutral-500'}`}>
        {tel.steerScale > 1
          ? `The wheels turn this little in a gentle curve at speed; the car draws them ${tel.steerScale} times wider so that it shows.`
          : hasRear
          ? active
            ? crab
              ? 'All four wheels turn the same way: the car slides sideways without turning.'
              : `The rear wheels turn against the front: the fronts need ${f1(Math.abs(tel.frontOnly) - Math.abs(tel.steerFront))}° less than they would alone.`
            : `Rear wheels turn up to ${facts.rearSteerMaxDeg}°; they come into play in the slow manoeuvres.`
          : 'Front wheels steer the car.'}
      </p>
    </Card>
  );
}

const CARDS: Record<DriveOverlay, (p: { c: Ctx; lead: boolean }) => React.JSX.Element> = {
  power: PowerCard,
  weight: WeightCard,
  motors: MotorsCard,
  suspension: SuspensionCard,
  brake: BrakeCard,
  energy: EnergyCard,
  aero: AeroCard,
  steering: SteeringCard,
};

// ------------------------------------------------------------------------------------------- the chart

/** How far ahead or behind the rival is at the clock's time, in metres, while its stand-in is drawn beside the car. */
function RivalGap({ setup, facts, rival }: { setup: DriveSetup; facts: DriveFacts; rival: ReturnType<typeof rivalOf> }) {
  const clock = useTechClock();
  const track = React.useMemo(() => (rival ? rivalTrack(rival, setup.run.from, setup.run.to, setup.input.env) : null), [rival, setup.run.from, setup.run.to, setup.input.env]);
  if (!rival || !track) return null;
  const gap = track(clock.t) - facts.telemetry(clock.t).distance;
  const ahead = gap > 0.05;
  return (
    <p className="tnum mt-1 text-[11px] text-neutral-700" aria-live="off">
      {rival.car.brand} {rival.car.model}: {Math.abs(gap) < 0.05 ? 'level' : `${f1(Math.abs(gap))} m ${ahead ? 'ahead' : 'behind'}`}
    </p>
  );
}

/** Speed against time: the car's own run and, behind it, a rival's published pull on the same stopwatch. */
function SpeedChart({
  vehicle,
  setup,
  facts,
  ghostSlug,
  onGhost,
  beside,
}: {
  vehicle: Vehicle;
  setup: DriveSetup;
  facts: DriveFacts;
  ghostSlug: string;
  onGhost: (slug: string) => void;
  /** the rival's stand-in is drawn beside the car */
  beside: boolean;
}) {
  const clock = useTechClock();
  const W = 300;
  const H = 96;
  const pad = { l: 24, r: 6, t: 6, b: 14 };
  const T = Math.max(clock.duration, 1);
  const own = facts.curve;
  const rival = React.useMemo(() => rivalOf(vehicles, vehicle, setup.spec, ghostSlug), [vehicle, setup.spec, ghostSlug]);
  const { from, to } = setup.run;
  const road = setup.input.env;
  const ghost = React.useMemo(
    () =>
      rival
        ? {
            curve: pullCurve(rival.t100, rival.t200, from, to, 0.1, rivalEnv(rival, road)),
            // the maker's figure is dry and level
            published: from === 0 && !road?.wet && !road?.gradePct && (to === 100 || (to === 200 && rival.published200)),
          }
        : null,
    [rival, from, to, road],
  );

  const vMax = Math.max(50, Math.ceil(Math.max(...own.v, ...(ghost?.curve.v ?? [0])) / 50) * 50);
  const x = (t: number) => pad.l + (t / T) * (W - pad.l - pad.r);
  const y = (v: number) => pad.t + (1 - v / vMax) * (H - pad.t - pad.b);
  const line = (vs: number[], dt: number, t0: number) => vs.map((v, i) => `${i ? 'L' : 'M'}${x(t0 + i * dt).toFixed(1)} ${y(v).toFixed(1)}`).join(' ');
  const ownPath = line(own.v, own.dt, 0);
  const ghostPath = ghost ? line(ghost.curve.v, ghost.curve.dt, HOLD) : '';
  const ticks = [0, 0.5, 1].map((k) => Math.round((vMax * k) / 50) * 50);
  const brake = facts.events.find((e) => e.cue === 'brake');

  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Speed against time, with a rival's pull behind">
        {ticks.map((v) => (
          <g key={v}>
            <line x1={pad.l} x2={W - pad.r} y1={y(v)} y2={y(v)} stroke="rgba(0,0,0,0.1)" />
            <text x={pad.l - 3} y={y(v) + 3} textAnchor="end" fontSize={8} fill="#737373">
              {v}
            </text>
          </g>
        ))}
        {facts.events
          .filter((e) => e.cue !== 'pull')
          .map((e) => (
            <line key={e.cue} x1={x(e.t)} x2={x(e.t)} y1={pad.t} y2={H - pad.b} stroke="rgba(0,0,0,0.12)" strokeDasharray="2 2" />
          ))}
        {ghost && <path d={ghostPath} fill="none" stroke="#a3a3a3" strokeWidth={1.6} strokeDasharray="4 3" />}
        <path d={ownPath} fill="none" stroke="#0891b2" strokeWidth={2} />
        <line x1={x(clock.t)} x2={x(clock.t)} y1={pad.t} y2={H - pad.b} stroke="#171717" strokeWidth={1} />
        <text x={pad.l} y={H - 3} fontSize={8} fill="#737373">
          0 s
        </text>
        <text x={W - pad.r} y={H - 3} textAnchor="end" fontSize={8} fill="#737373">
          {Math.round(T)} s
        </text>
        {brake && (
          <text x={x(brake.t) + 2} y={pad.t + 8} fontSize={8} fill="#737373">
            brake
          </text>
        )}
      </svg>
      <div className="mt-1 flex items-center justify-between gap-2 text-[10px] text-neutral-600">
        <span className="flex items-center gap-1">
          <span className="inline-block h-0.5 w-3 bg-cyan-600" />
          <span className="tnum">
            {setup.run.label}: {f2(setup.run.time)} s
          </span>
        </span>
        <label className="flex min-w-0 items-center gap-1">
          <span className="inline-block h-0.5 w-3 border-t-2 border-dashed border-neutral-400" />
          <select
            aria-label="Rival on the chart"
            value={ghostSlug}
            onChange={(e) => onGhost(e.target.value)}
            className={`max-w-[130px] truncate rounded bg-transparent text-[10px] ${FOCUS}`}
          >
            <option value="">No rival</option>
            {vehicles.map((v) => (
              <option key={v.slug} value={v.slug}>
                {v.brand} {v.model}
                {v.slug === vehicle.slug ? ' (base trim)' : ''}
              </option>
            ))}
          </select>
          {ghost && (
            <span className="tnum whitespace-nowrap">
              {f2(ghost.curve.time)} s{ghost.published ? '' : '*'}
            </span>
          )}
        </label>
      </div>
      {ghost && !ghost.published && <p className="mt-0.5 text-[10px] text-neutral-400">* modelled from the rival’s own 0–100 time (and our estimate of its 0–200), not a published figure.</p>}
      {beside && <RivalGap setup={setup} facts={facts} rival={rival} />}
    </div>
  );
}

// ------------------------------------------------------------------------------------------- the panel

/** What the run is saying now: the callout pinned to the latest moment passed. */
function calloutNow(setup: DriveSetup, facts: DriveFacts, t: number): { index: number; text: string } | null {
  const at = (cue: string) => facts.events.find((e) => e.cue === cue)?.t;
  let best: { t: number; index: number; text: string } | null = null;
  setup.spec.callouts.forEach((c, index) => {
    const when = at(c.cue);
    if (when !== undefined && when <= t + 1e-3 && (!best || when >= best.t)) best = { t: when, index, text: c.text };
  });
  return best;
}

function calloutAt(setup: DriveSetup, facts: DriveFacts, t: number): string {
  return calloutNow(setup, facts, t)?.text ?? 'Ready. Choose a drive mode, then press Launch; the playback bar steps through the run.';
}

/** What the voice says of a callout: its first full sentence (the label before it, "Launch.", is left out), so that it is done before the next. */
export function spokenForm(text: string): string {
  const parts = text.split(/(?<=[.:;])\s+/);
  const full = parts.find((p) => p.trim().split(/\s+/).length >= 4) ?? text;
  return full.replace(/[.:;]$/, '').replace(/°/g, ' degrees').replace(/\bkm\/h\b/g, 'kilometres per hour');
}

/**
 * The callouts spoken as the run reaches them, when the visitor asks and the site's sound is on (the browser's own speech
 * synthesis: nothing is sent anywhere). A pause, a scrub or a new run stops what is being said.
 */
function useVoice(setup: DriveSetup, facts: DriveFacts | null, on: boolean) {
  const clock = useTechClock();
  const speed = useVehicleStore((s) => s.techSpeed);
  const spoken = React.useRef(-1);
  const lastT = React.useRef(0);
  const synth = typeof window !== 'undefined' && 'speechSynthesis' in window ? window.speechSynthesis : null;
  const [sound, setSound] = React.useState(true);
  React.useEffect(() => {
    setSound(soundOn());
    return subscribeSound(() => setSound(soundOn()));
  }, []);

  React.useEffect(() => {
    if (!synth) return;
    const live = on && sound && facts !== null;
    if (!live || !clock.playing) {
      synth.cancel();
      // a pause keeps its place; a scrub back or a replay starts the callouts again
      if (clock.t < lastT.current - 0.3 || clock.t < 0.2) spoken.current = -1;
      lastT.current = clock.t;
      return;
    }
    if (clock.t < lastT.current - 0.3) spoken.current = -1;
    lastT.current = clock.t;
    const now = calloutNow(setup, facts, clock.t);
    if (!now || now.index === spoken.current) return;
    spoken.current = now.index;
    synth.cancel();
    const u = new SpeechSynthesisUtterance(spokenForm(now.text));
    u.lang = 'en-GB';
    u.rate = clamp(1 + (speed - 1) * 0.4, 0.8, 1.4);
    synth.speak(u);
  }, [synth, on, sound, facts, setup, clock.t, clock.playing, speed]);

  // a new run, a new car or leaving the tab: nothing is left talking
  React.useEffect(() => {
    spoken.current = -1;
    return () => synth?.cancel();
  }, [synth, setup.run.id, setup.mode.id, setup.load.id, setup.variant.id]);

  return Boolean(synth);
}

function PostRun({ vehicle, setup, facts, ghostSlug, onClose }: { vehicle: Vehicle; setup: DriveSetup; facts: DriveFacts; ghostSlug: string; onClose: () => void }) {
  const s = facts.summary;
  const rival = ghostSlug ? vehicles.find((v) => v.slug === ghostSlug) : undefined;
  const next = rival && rival.slug !== vehicle.slug ? rival : vehicles.find((v) => v.slug !== vehicle.slug && v.drive);
  const rows: [string, string][] = [];
  if (s.runTime !== null) rows.push([setup.run.label, `${f2(s.runTime)} s${facts.nominal && setup.run.published ? ' (published)' : ' (modelled)'}`]);
  rows.push(['Top speed', `${f0(s.topKmh)} km/h`], ['Peak acceleration', `${f2(s.peakG)} g`]);
  rows.push(['Energy used', `${f0(s.energyWh)} Wh${s.regenWh > 1 ? ` (${f0(s.regenWh)} recovered)` : ''}`]);
  if (s.rangeKm !== null) rows.push(['Range cost', `${f2(s.rangeKm)} km`]);
  if (s.brakeM !== null) rows.push([`${f0(s.brakeFromKmh ?? 0)}–0 km/h`, `${f1(s.brakeM)} m in ${f1(s.brakeS ?? 0)} s`]);
  if (s.peakLatG > 0.05) rows.push(['Lateral', `${f2(s.peakLatG)} g, roll ${f1(s.peakRollDeg)}°`]);
  if (s.maxRearDeg > 0.5) rows.push(['Rear wheels', `up to ${f1(s.maxRearDeg)}°`]);
  return (
    <section className="rounded-xl bg-neutral-900 px-3 py-3 text-white" aria-label="Run summary">
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-[13px] font-semibold">Run complete</h3>
        <button type="button" onClick={onClose} className={`rounded-full px-2 text-[11px] text-neutral-400 hover:text-white ${FOCUS}`}>
          Hide
        </button>
      </div>
      <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-[11px]">
        {rows.map(([k, v]) => (
          <React.Fragment key={k}>
            <dt className="text-neutral-400">{k}</dt>
            <dd className="tnum text-right">{v}</dd>
          </React.Fragment>
        ))}
      </dl>
      {s.rangeKm !== null && (
        <p className="mt-2 text-[11px] leading-snug text-neutral-300">
          In real life: that run uses about {f0(s.energyWh)} Wh, the energy for {f1(s.rangeKm)} km of ordinary driving.
        </p>
      )}
      <div className="mt-2.5 flex flex-wrap gap-2">
        <button type="button" onClick={() => { techClock.seek(0); techClock.play(); }} className={`rounded-full bg-white px-3 py-1 text-[11px] font-medium text-neutral-900 ${FOCUS}`}>
          Run again
        </button>
        {next && (
          <Link href={`/showroom/${next.slug}?tab=drive`} className={`rounded-full bg-white/15 px-3 py-1 text-[11px] font-medium text-white hover:bg-white/25 ${FOCUS}`}>
            Drive the {next.brand} {next.model}
          </Link>
        )}
      </div>
    </section>
  );
}

function PanelBody({ vehicle }: { vehicle: Vehicle }) {
  const choice = useVehicleStore((s) => s.drive);
  const variantId = useVehicleStore((s) => s.variantId);
  const setDrive = useVehicleStore((s) => s.setDrive);
  const setVariant = useVehicleStore((s) => s.setVariant);
  const clock = useTechClock();
  const facts = useRuntime()?.launch?.drive ?? null;
  const [hidden, setHidden] = React.useState(false);

  const setup = React.useMemo(
    () => driveSetup(vehicle, { variantId, runId: choice.run, modeId: choice.mode, loadId: choice.load, brake: choice.brake }),
    [vehicle, variantId, choice.run, choice.mode, choice.load, choice.brake],
  );
  const { spec } = setup;
  const ghostSlug = choice.ghost ?? spec.ghost?.slug ?? '';
  const tel = facts ? facts.telemetry(clock.t) : null;
  const canSpeak = useVoice(setup, facts, Boolean(choice.voice));
  const rivalCar = React.useMemo(() => rivalOf(vehicles, vehicle, spec, ghostSlug), [vehicle, spec, ghostSlug]);
  const canBeside = Boolean(rivalCar?.car.assets.proxyUrl);
  const done = clock.duration > 0 && clock.t >= clock.duration - 0.05 && !clock.playing;
  // a new run shows its summary again
  React.useEffect(() => setHidden(false), [setup.run.id, setup.mode.id, setup.load.id, variantId, setup.brake]);

  const ctx: Ctx | null = facts && tel ? { tel, facts, setup, peakKw: setup.variant.performance.powerKw } : null;
  const cards = spec.overlays.filter((o, i, all) => all.indexOf(o) === i);
  const trims = vehicle.variants.filter((v) => v.performance.zeroTo100S !== undefined);

  return (
    <div className="space-y-3">
      <header>
        <h2 className="text-[15px] font-semibold leading-tight text-neutral-900">{spec.title}</h2>
        <p className="mt-1 text-[11px] leading-snug text-neutral-600">{spec.blurb}</p>
      </header>

      <div className="space-y-2.5">
        {trims.length > 1 && (
          <Seg
            label="Trim"
            value={setup.variant.id}
            onChange={(id) => setVariant(id)}
            options={trims.map((v) => ({ id: v.id, label: `${v.name.replace(/\s*\(.*\)/, '')} · ${f2(v.performance.zeroTo100S ?? 0)} s`, hint: `${v.performance.powerKw} kW` }))}
          />
        )}
        {setup.modes.length > 1 && (
          <Seg
            label="Drive mode"
            value={setup.mode.id}
            onChange={(id) => setDrive({ mode: id })}
            options={setup.modes.map((m) => ({ id: m.id, label: m.label, hint: m.native }))}
          />
        )}
        {setup.loads.length > 1 && (
          <Seg label="Load" value={setup.load.id} onChange={(id) => setDrive({ load: id })} options={setup.loads.map((l) => ({ id: l.id, label: l.label, hint: `${l.payloadKg} kg` }))} />
        )}
        {setup.canBrake && (
          <Seg
            label="After the run"
            value={setup.brake ? 'stop' : 'go'}
            onChange={(id) => setDrive({ brake: id === 'stop' })}
            options={[
              { id: 'go', label: spec.finish === 'cruise' ? 'Cruise' : 'Coast' },
              { id: 'stop', label: 'Then stop' },
            ]}
          />
        )}
        <div className="grid grid-cols-[auto_1fr] gap-x-4">
          <Seg
            label="Road"
            value={choice.surface ?? 'dry'}
            onChange={(id) => setDrive({ surface: id })}
            options={[
              { id: 'dry', label: 'Dry', hint: 'The maker’s own run is dry and level' },
              { id: 'wet', label: 'Wet', hint: 'The tyres hold about 0.7 g; ours' },
            ]}
          />
          <Seg
            label="Hill"
            value={String(choice.grade ?? 0)}
            onChange={(id) => setDrive({ grade: Number(id) })}
            options={[
              { id: '-6', label: '−6 %', hint: 'Downhill' },
              { id: '0', label: 'Level' },
              { id: '6', label: '+6 %', hint: 'Uphill' },
            ]}
          />
        </div>
        {canBeside && (
          <Seg
            label="Rival car"
            value={choice.rival ? 'beside' : 'none'}
            onChange={(id) => setDrive({ rival: id === 'beside' })}
            options={[
              { id: 'none', label: 'Off' },
              { id: 'beside', label: `Beside: ${rivalCar?.car.brand} ${rivalCar?.car.model}`, hint: 'Its stand-in drives beside you on its own published pull' },
            ]}
          />
        )}
        {canSpeak && (
          <Seg
            label="Voice"
            value={choice.voice ? 'on' : 'off'}
            onChange={(id) => setDrive({ voice: id === 'on' })}
            options={[
              { id: 'off', label: 'Off' },
              { id: 'on', label: 'Read the callouts', hint: 'The browser’s own speech; follows the site’s sound switch' },
            ]}
          />
        )}
        <Seg
          label="Camera"
          value={choice.cam ?? setup.camera}
          onChange={(id) => setDrive({ cam: id })}
          options={camerasOf(vehicle).map((id) => ({ id, label: DRIVE_CAMERAS[id].label }))}
        />
      </div>

      <div className="rounded-xl bg-cyan-50 px-3 py-2 text-[12px] leading-snug text-cyan-950 ring-1 ring-cyan-900/10" aria-live="polite">
        {facts ? calloutAt(setup, facts, clock.t) : 'Loading the car…'}
      </div>

      {done && facts && !hidden && <PostRun vehicle={vehicle} setup={setup} facts={facts} ghostSlug={ghostSlug} onClose={() => setHidden(true)} />}

      {ctx && (
        <div className="space-y-2">
          {cards.map((o, i) => {
            const Card = CARDS[o];
            return <Card key={o} c={ctx} lead={i === 0} />;
          })}
        </div>
      )}

      {facts && (
        <section className="rounded-xl bg-black/[0.04] px-3 py-2.5">
          <h3 className="mb-1 text-[10px] font-semibold uppercase tracking-[0.08em] text-neutral-500">Speed against time</h3>
          <SpeedChart vehicle={vehicle} setup={setup} facts={facts} ghostSlug={ghostSlug} onGhost={(slug) => setDrive({ ghost: slug })} beside={Boolean(choice.rival)} />
        </section>
      )}
    </div>
  );
}

/**
 * The Drive tab's panel: the car's own scenario (Vehicle.drive) with its modes, loads and instruments, the speed chart
 * with a rival behind it, and the run's summary. A column at the right of a wide window; on a narrower one a bar under the
 * menu that opens over the car.
 */
export function DrivePanel({ vehicle, column }: { vehicle: Vehicle; column: boolean }) {
  const [open, setOpen] = React.useState(false);
  const title = vehicle.drive?.title ?? 'Drive & Launch';
  if (column) {
    return (
      <aside
        aria-label="Drive scenario"
        className={`hy-scroll pointer-events-auto absolute right-3 bottom-3 z-20 overflow-y-auto rounded-2xl p-3 ${BELOW_TOP} ${PANEL}`}
        style={{ width: DRIVE_COLUMN_W }}
      >
        <PanelBody vehicle={vehicle} />
      </aside>
    );
  }
  return (
    <div className={`pointer-events-none absolute inset-x-3 z-20 ${BELOW_TOP}`}>
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className={`pointer-events-auto flex w-full items-center justify-between rounded-full px-4 py-2 text-left text-[12px] font-medium text-neutral-800 ${GLASS} ${FOCUS}`}
      >
        <span className="truncate">{title}</span>
        <span className="ml-2 shrink-0 text-neutral-500">{open ? 'Close ▴' : 'Scenario ▾'}</span>
      </button>
      {open && (
        <div className={`hy-scroll pointer-events-auto mt-2 max-h-[62vh] overflow-y-auto rounded-2xl p-3 ${PANEL}`}>
          <PanelBody vehicle={vehicle} />
        </div>
      )}
    </div>
  );
}
