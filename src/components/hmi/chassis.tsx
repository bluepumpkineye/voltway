'use client';

import React from 'react';
import type { Variant, Vehicle } from '@/data/vehicles/schema';
import { pauseDemo, startDemo } from '@/lib/tech/actions';
import { CHASSIS, chassisAction, isChassisDriver } from '@/lib/tech/chassis';
import { useTechClock } from '@/lib/tech/clock';
import { useChassisReadout, useRuntime } from '@/lib/tech/session';
import { useVehicleStore } from '@/store/vehicle-store';
import { Card, CardTitle } from './ui';

/**
 * The chassis page of the generic skin, for the cars whose own screens have not been photographed (the Denza Z9, the
 * Xpeng G9L): the wheels from above with the angle each is set to, live, the figure the manoeuvre is about, and the
 * button that starts it. The Z9's hands-on reports say its centre screen shows a numeric indicator during the crab walk
 * (km77); the page is that idea drawn for the showroom, not the maker's screen, and says so.
 */

/** the chassis demo on show: the one the Tech tab is running, or else the car's first of them */
function useChassisDemo(vehicle: Vehicle) {
  const runtime = useRuntime();
  const chosen = useVehicleStore((s) => s.techDemoId);
  const mine = (vehicle.tech ?? []).filter((d) => isChassisDriver(d.driver));
  const spec = mine.find((d) => d.id === (runtime?.chassis ? runtime.demoId : chosen)) ?? mine[0];
  return { runtime, spec, copy: spec ? CHASSIS[spec.driver] : undefined };
}

export function ChassisScreen({ vehicle, accent }: { vehicle: Vehicle; variant: Variant; accent: string }) {
  const { runtime, spec, copy } = useChassisDemo(vehicle);
  const readout = useChassisReadout();
  const clock = useTechClock();
  const available = useVehicleStore((s) => s.techAvailable);
  const live = Boolean(runtime?.chassis && spec);

  if (!spec || !copy) {
    return (
      <Card className="flex h-full items-center justify-center px-16 text-center text-[17px] leading-relaxed text-white/45">
        The chassis page belongs to the showroom&rsquo;s Tech tab. Open it from there to see the wheels.
      </Card>
    );
  }

  const action = chassisAction(spec.driver, clock, () => startDemo(spec.id, 'dashboard'), pauseDemo);
  const steer = readout?.steer ?? [0, 0, 0, 0];
  // the crab angle is the angle the front wheels are set to (held at the end of the slide); the others show how far the car has turned
  const figure = spec.driver === 'crab' ? Math.abs(steer[0]) : Math.abs(readout?.turned ?? 0);
  const chosen = runtime?.chassis?.facts.pivot ?? null;

  return (
    <div className="grid h-full grid-cols-[1.15fr_1fr] gap-3">
      <Card className="relative flex flex-col overflow-hidden">
        <CardTitle>{copy.title}</CardTitle>
        <div className="relative flex min-h-0 flex-1 items-center justify-center">
          <TopView
            vehicle={vehicle}
            steer={steer}
            travel={readout?.travel ?? null}
            pivot={readout?.held ?? null}
            chosen={chosen}
            accent={accent}
          />
        </div>
        <p className="px-5 pb-4 text-[13px] leading-relaxed text-white/40">{copy.hint}</p>
      </Card>

      <div className="flex flex-col gap-3">
        <Card className="flex flex-col justify-center px-6 py-5">
          <span className="text-[13px] uppercase tracking-[0.16em] text-white/40">{copy.figure}</span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="tnum text-[84px] font-light leading-none text-white">{Math.round(figure)}</span>
            <span className="text-[28px] text-white/45">°</span>
          </div>
          <div className="mt-4 flex items-baseline gap-2 text-white/60">
            <span className="tnum text-[30px] font-light text-white/85">{Math.round(readout?.speed ?? 0)}</span>
            <span className="text-[14px]">km/h</span>
            <span className="ml-3 text-[12px] text-white/30">fastest wheel</span>
          </div>
        </Card>

        <Card className="grid grid-cols-2 gap-x-6 gap-y-3 px-6 py-5">
          {(['FL', 'FR', 'RL', 'RR'] as const).map((k, i) => (
            <div key={k} className="flex items-baseline justify-between border-b border-white/[0.06] pb-2">
              <span className="text-[14px] text-white/50">{LABEL[k]}</span>
              <span className="tnum text-[22px] font-light text-white/90">{signed(steer[i])}°</span>
            </div>
          ))}
        </Card>

        <button
          type="button"
          disabled={!live || !available}
          onClick={action.run}
          className="mt-auto flex h-[84px] items-center justify-center rounded-[22px] text-[24px] font-medium text-[#08090b] transition-opacity disabled:opacity-40"
          style={{ background: accent }}
        >
          {action.label}
        </button>
        <p className="px-2 text-[12px] leading-relaxed text-white/30">
          Drawn for this showroom from the maker&rsquo;s published figures; the car&rsquo;s own screen is not photographed.
        </p>
      </div>
    </div>
  );
}

const LABEL = { FL: 'Front left', FR: 'Front right', RL: 'Rear left', RR: 'Rear right' } as const;

const signed = (a: number) => {
  const r = Math.round(a * 10) / 10;
  return (r > 0 ? '+' : r < 0 ? '−' : '') + Math.abs(r).toFixed(1);
};

/** The car from above, nose up, with the wheels turned as the car's own are. */
function TopView({
  vehicle,
  steer,
  travel,
  pivot,
  chosen,
  accent,
}: {
  vehicle: Vehicle;
  steer: readonly number[];
  travel: number | null;
  /** the wheel held still now */
  pivot: 'FL' | 'FR' | null;
  /** the wheel the demo will pivot about, picked but not yet held */
  chosen: 'FL' | 'FR' | null;
  accent: string;
}) {
  const d = vehicle.dimensions;
  const S = 0.088; // px per mm
  const L = d.lengthMm * S;
  const W = d.widthMm * S * 0.93;
  const wb = d.wheelbaseMm * S;
  const track = 1.7e3 * S;
  const cx = 230;
  const cy = 235;
  const wheelW = 0.25e3 * S;
  const wheelL = 0.72e3 * S;
  const pos = {
    FL: [cx - track / 2, cy - wb / 2],
    FR: [cx + track / 2, cy - wb / 2],
    RL: [cx - track / 2, cy + wb / 2],
    RR: [cx + track / 2, cy + wb / 2],
  } as const;
  // front left of the car is the left of the picture with the nose up
  const idx = { FL: 0, FR: 1, RL: 2, RR: 3 } as const;
  return (
    <svg viewBox="0 0 460 470" className="h-full max-h-full w-full" role="img" aria-label="The wheels seen from above">
      {/* the body */}
      <rect x={cx - W / 2} y={cy - L / 2 + 6} width={W} height={L - 12} rx={W * 0.32} fill="rgba(255,255,255,0.07)" stroke="rgba(255,255,255,0.22)" strokeWidth={2} />
      <rect x={cx - W * 0.36} y={cy - L * 0.2} width={W * 0.72} height={L * 0.36} rx={W * 0.16} fill="rgba(255,255,255,0.05)" />
      {/* the way it travels */}
      {travel !== null && (
        <g transform={`translate(${cx} ${cy}) rotate(${-travel})`}>
          <line x1={0} y1={-L * 0.3} x2={0} y2={-L * 0.62} stroke={accent} strokeWidth={5} strokeDasharray="10 8" strokeLinecap="round" />
          <path d={`M -14 ${-L * 0.62 + 6} L 0 ${-L * 0.62 - 14} L 14 ${-L * 0.62 + 6} Z`} fill={accent} />
        </g>
      )}
      {(['FL', 'FR', 'RL', 'RR'] as const).map((k) => {
        const [x, y] = pos[k];
        const held = pivot === k;
        const picked = !held && chosen === k;
        return (
          <g key={k} transform={`translate(${x} ${y}) rotate(${-steer[idx[k]]})`}>
            <rect x={-wheelW / 2} y={-wheelL / 2} width={wheelW} height={wheelL} rx={5} fill={held ? accent : '#0c0d10'} stroke="rgba(255,255,255,0.55)" strokeWidth={2} />
            {(held || picked) && <circle r={wheelW * 1.5} fill="none" stroke={accent} strokeWidth={2} strokeDasharray="4 5" />}
          </g>
        );
      })}
      <text x={cx} y={30} textAnchor="middle" fill="rgba(255,255,255,0.35)" fontSize={13} letterSpacing={2}>
        FRONT
      </text>
    </svg>
  );
}
