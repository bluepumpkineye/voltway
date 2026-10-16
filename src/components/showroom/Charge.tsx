'use client';

import React from 'react';
import type { Vehicle } from '@/data/vehicles/schema';
import { flagshipVariant } from '@/data/vehicles/schema';
import { pauseDemo, tapChargeFlap } from '@/lib/tech/actions';
import { techClock, useTechClock } from '@/lib/tech/clock';
import { chargeFacts } from '@/lib/tech/charging';
import { runPhase } from '@/lib/tech/phase';
import { useChargeReadout, useRuntime, type Runtime } from '@/lib/tech/session';
import { useVehicleStore } from '@/store/vehicle-store';
import { FOCUS, GLASS } from './Chrome';

const W = 600;
const H = 78;

const mmss = (s: number) => {
  const n = Math.round(s);
  return `${Math.floor(n / 60)}:${String(n % 60).padStart(2, '0')}`;
};

/** How wide the panel's column is, px, on a window wide enough to stand it beside the car. */
export const CHARGE_COLUMN_W = 392;

/**
 * The Charging tab's panel, the showroom's and not the car's: what the car charges at (the maker's figures, each tagged
 * published or derived), the run's own numbers (charge level, power, time, energy), the charging curve with where the
 * car is on it, and the button that starts it. The window and the minutes are the maker's (`Vehicle.charging`); a peak it
 * does not publish is derived, the curve between is ours, and the minutes play in fourteen seconds: the figures say
 * which is which, and the playback bar's Simulation button has the sources.
 *
 * `compact` is the panel in the dock of a narrow window: the specifications fold away behind a button.
 */
export function ChargePanel({ vehicle, compact }: { vehicle: Vehicle; compact: boolean }) {
  const facts = React.useMemo(() => chargeFacts(vehicle), [vehicle]);
  const charge = useRuntime()?.charge;
  const r = useChargeReadout();
  const clock = useTechClock();
  const run = runPhase(clock);
  const soc = useVehicleStore((s) => s.soc);
  const [specs, setSpecs] = React.useState(false);
  const variant = flagshipVariant(vehicle);

  const profile = facts?.profile;
  const peakKw = profile?.peakKw ?? 1;
  const kwMax = peakKw * 1.08;
  const seconds = profile?.seconds ?? 1;

  const path = React.useMemo(() => {
    if (!charge) return { line: '', area: '' };
    const step = Math.max(1, Math.round(charge.curve.length / 120));
    const pts = charge.curve.filter((_, i) => i % step === 0 || i === charge.curve.length - 1);
    const xy = pts.map((p) => [(p.s / seconds) * W, H - 6 - (p.kw / kwMax) * (H - 10)] as const);
    const line = 'M' + xy.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join(' L');
    return { line, area: `${line} L${W} ${H} L0 ${H} Z` };
  }, [charge, seconds, kwMax]);

  if (!facts || !profile) return null;
  const { spec } = facts;

  const sim = r ? Math.min(seconds, r.elapsed) : 0;
  const x = (sim / seconds) * W;
  const y = r ? H - 6 - (Math.max(r.kw, curveKw(charge, sim)) / kwMax) * (H - 10) : H;
  const peakY = H - 6 - (peakKw / kwMax) * (H - 10);
  const shown = Math.round((r?.soc ?? soc) * 100);

  const action =
    run === 'driving'
      ? { label: 'Pause', run: pauseDemo }
      : run === 'done'
        ? { label: 'Charge again', run: () => techClock.play() }
        : r?.phase === 'charged'
          ? { label: 'Unplug', run: () => techClock.play() }
          : run === 'ready'
            ? { label: 'Start charging', run: tapChargeFlap }
            : { label: 'Resume', run: () => techClock.play() };

  const phaseLine = !r
    ? 'Loading the car…'
    : r.phase === 'ready'
      ? `Parked at the charger, at ${Math.round(profile.from * 100)} %`
      : r.phase === 'opening'
        ? 'The flap opens and the gun comes off its pedestal'
        : r.phase === 'connecting'
          ? 'The gun goes into the DC socket'
          : r.phase === 'charging'
            ? 'Charging'
            : r.phase === 'charged'
              ? `Charged to ${Math.round(profile.to * 100)} %`
              : r.phase === 'unplugging'
                ? 'The gun goes home and the flap shuts'
                : 'Unplugged';

  const peakTag = facts.peak.source === 'published' ? 'published' : facts.peak.source === 'c-rate' ? `${spec.cRate}C × pack` : 'derived';
  const rows: { label: string; value: string; tag?: string }[] = [
    { label: 'Peak power', value: `${facts.peak.kw} kW`, tag: peakTag },
    { label: `${spec.window.from}–${spec.window.to} %`, value: `${spec.window.minutes} min`, tag: 'published' },
    { label: 'Average over it', value: `${Math.round(facts.averageKw)} kW`, tag: 'derived' },
    { label: 'Pack', value: `${spec.packKwh} kWh ${variant.battery.chemistry}` },
    ...(spec.architectureV ? [{ label: 'Architecture', value: `${spec.architectureV} V` }] : []),
    { label: 'Connector', value: `${spec.connector} DC` },
    { label: 'Charge port', value: spec.port.where, tag: spec.port.published ? 'published' : 'ours' },
  ];

  return (
    <section aria-label="Fast charging" className={`pointer-events-auto w-full rounded-2xl px-4 py-3 ${GLASS}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-[13px] font-semibold text-neutral-900">Fast charging</h2>
          <p className="truncate text-[11px] text-neutral-500" aria-live="polite">
            {phaseLine}
          </p>
        </div>
        <button
          type="button"
          onClick={action.run}
          disabled={!r}
          className={`shrink-0 rounded-full bg-neutral-900 px-4 py-2 text-[12px] font-medium text-white transition-opacity disabled:opacity-40 ${FOCUS}`}
        >
          {action.label}
        </button>
      </div>

      <div className="mt-2 flex items-end justify-between gap-3">
        <div className="flex items-baseline gap-1.5">
          <span className="tnum text-[34px] font-semibold leading-none tracking-tight text-neutral-900">{shown}</span>
          <span className="text-[12px] text-neutral-500">% charged</span>
        </div>
        <div className="tnum flex items-baseline gap-1">
          <span className="text-[22px] font-medium leading-none text-neutral-900">{Math.round(r?.kw ?? 0)}</span>
          <span className="text-[12px] text-neutral-500">kW</span>
        </div>
        <div className="tnum text-right text-[12px] leading-tight text-neutral-600">
          <div>{r ? mmss(r.elapsed) : '0:00'} charging</div>
          <div className="text-neutral-400">{r ? r.kwh.toFixed(1) : '0.0'} kWh added</div>
        </div>
      </div>

      <figure className="mt-2">
        <svg viewBox={`0 0 ${W} ${H}`} className="block h-[56px] w-full" role="img" aria-label="Charging power against time">
          <line x1="0" x2={W} y1={peakY} y2={peakY} stroke="#c9ccd2" strokeWidth="1" strokeDasharray="3 4" vectorEffect="non-scaling-stroke" />
          <path d={path.area} fill="#2f6bff" opacity="0.08" />
          <path d={path.line} fill="none" stroke="#8a8f98" strokeWidth="1.4" strokeOpacity="0.7" vectorEffect="non-scaling-stroke" />
          <clipPath id="chargeDone">
            <rect x="0" y="0" width={x} height={H} />
          </clipPath>
          <path d={path.line} fill="none" stroke="#2f6bff" strokeWidth="2.4" strokeLinejoin="round" vectorEffect="non-scaling-stroke" clipPath="url(#chargeDone)" />
          {r && r.elapsed > 0 && <circle cx={x} cy={y} r="4" fill="#2f6bff" vectorEffect="non-scaling-stroke" />}
        </svg>
        <figcaption className="mt-0.5 flex justify-between text-[10.5px] text-neutral-500">
          <span>Power through the charge (simulated curve)</span>
          <span className="tnum">{mmss(seconds)}</span>
        </figcaption>
      </figure>

      {compact && (
        <button
          type="button"
          aria-expanded={specs}
          onClick={() => setSpecs((v) => !v)}
          className={`mt-2 flex w-full items-center justify-between border-t border-black/[0.06] pt-2 text-[12px] font-medium text-neutral-700 ${FOCUS}`}
        >
          Charging specifications
          <svg className={`transition-transform ${specs ? 'rotate-180' : ''}`} width="9" height="6" viewBox="0 0 9 6" aria-hidden>
            <path d="M1 1l3.5 3.5L8 1" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      )}
      {(!compact || specs) && (
        <dl className={`mt-2 grid grid-cols-2 gap-x-4 gap-y-2 ${compact ? '' : 'border-t border-black/[0.06] pt-3'}`}>
          {rows.map((row) => (
            <div key={row.label} className="min-w-0">
              <dt className="text-[11px] text-neutral-500">{row.label}</dt>
              <dd className="tnum text-[13px] leading-snug text-neutral-900">
                {row.value}
                {row.tag && <span className="ml-1.5 text-[10.5px] font-normal text-neutral-400">{row.tag}</span>}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  );
}

function curveKw(charge: NonNullable<Runtime['charge']> | null | undefined, sim: number): number {
  if (!charge) return 0;
  const c = charge.curve;
  return c[Math.min(c.length - 1, Math.max(0, Math.round(sim)))]?.kw ?? 0;
}
