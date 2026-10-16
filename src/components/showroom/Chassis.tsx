'use client';

import React from 'react';
import { pauseDemo, resetDemo } from '@/lib/tech/actions';
import { techClock, useTechClock } from '@/lib/tech/clock';
import { parkPhase } from '@/lib/tech/phase';
import { useChassisReadout, useRuntime } from '@/lib/tech/session';
import type { Pivot } from '@/lib/tech/street';
import { useVehicleStore } from '@/store/vehicle-store';
import { GLASS } from './Chrome';

const FOCUS = 'outline-none focus-visible:ring-2 focus-visible:ring-neutral-900/70 focus-visible:ring-offset-1';

const signed = (a: number) => {
  const r = Math.round(a);
  return (r > 0 ? '+' : r < 0 ? '−' : '') + Math.abs(r);
};

const PIVOTS: { id: Pivot; label: string }[] = [
  { id: 'FL', label: 'Left front wheel' },
  { id: 'FR', label: 'Right front wheel' },
];
const ANGLES = [90, 180, 360];

/**
 * The chassis demos' own panel, the showroom's and not the car's: the wheels' angles as the run sets them, the speed and
 * what the manoeuvre needed, with the compass turn's choices (which front wheel, how far). The car's own screen carries
 * the same numbers and the button that starts the run; this is what is left when that screen is put away.
 */
export function ChassisTools({ driver }: { driver: string }) {
  const r = useChassisReadout();
  const facts = useRuntime()?.chassis?.facts;
  const pivot = useVehicleStore((s) => s.compassPivot);
  const angle = useVehicleStore((s) => s.compassAngle);
  const setCompass = useVehicleStore((s) => s.setCompass);
  const steer = r?.steer ?? [0, 0, 0, 0];

  return (
    <div className={`pointer-events-auto w-full max-w-[620px] rounded-2xl px-3.5 py-2.5 ${GLASS}`}>
      <div className="flex items-center gap-4">
        <div className="flex items-baseline gap-1">
          <span className="tnum text-[28px] font-semibold leading-none tracking-tight text-neutral-900">{Math.round(r?.speed ?? 0)}</span>
          <span className="text-[12px] text-neutral-500">km/h</span>
        </div>
        <div className="tnum grid flex-1 grid-cols-4 gap-1.5 text-center text-[11px] leading-tight text-neutral-500">
          {(['FL', 'FR', 'RL', 'RR'] as const).map((k, i) => (
            <div key={k}>
              <div className="text-[17px] font-medium text-neutral-900">{signed(steer[i])}°</div>
              {k === 'FL' ? 'Front left' : k === 'FR' ? 'Front right' : k === 'RL' ? 'Rear left' : 'Rear right'}
            </div>
          ))}
        </div>
        {facts && (
          <div className="tnum shrink-0 text-right text-[11px] leading-tight text-neutral-500">
            <div className="text-[15px] font-medium text-neutral-900">{facts.roadWidth.toFixed(1)} m</div>
            street
          </div>
        )}
      </div>
      {driver === 'compass' && (
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <div role="group" aria-label="Pivot wheel" className="flex rounded-full bg-black/[0.04] p-0.5">
            {PIVOTS.map((p) => (
              <button
                key={p.id}
                type="button"
                aria-pressed={pivot === p.id}
                onClick={() => setCompass(p.id, useVehicleStore.getState().compassAngle)}
                className={`rounded-full px-3 py-1 text-[11px] font-medium transition-colors ${FOCUS} ${
                  pivot === p.id ? 'bg-white text-neutral-900 shadow-sm' : 'text-neutral-500 hover:text-neutral-800'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
          <div role="group" aria-label="Angle" className="flex rounded-full bg-black/[0.04] p-0.5">
            {ANGLES.map((a) => (
              <button
                key={a}
                type="button"
                aria-pressed={angle === a}
                onClick={() => setCompass(useVehicleStore.getState().compassPivot, a)}
                className={`tnum rounded-full px-3 py-1 text-[11px] font-medium transition-colors ${FOCUS} ${
                  angle === a ? 'bg-white text-neutral-900 shadow-sm' : 'text-neutral-500 hover:text-neutral-800'
                }`}
              >
                {a}°
              </button>
            ))}
          </div>
          <span className="text-[10.5px] text-neutral-400">any angle to 360° is published</span>
        </div>
      )}
      {driver === 'crab' && (
        <p className="mt-1.5 text-[10.5px] leading-snug text-neutral-500">
          Front wheels up to 15° and rear wheels up to ±10°, below 20 km/h <span className="text-neutral-400">published</span>
          <span className="mx-1 text-neutral-300">·</span>
          the car slides {facts?.shift?.toFixed(2) ?? '2.25'} m at 7 km/h <span className="text-neutral-400">ours</span>
        </p>
      )}
      {driver === 'e3park' && (
        <p className="mt-1.5 text-[10.5px] leading-snug text-neutral-500">
          Nose in, pivot about a front wheel, tail swings in <span className="text-neutral-400">published</span>
          <span className="mx-1 text-neutral-300">·</span>
          the gap is {facts?.gap?.toFixed(1) ?? '6.1'} m, the car’s length and a metre <span className="text-neutral-400">ours</span>
        </p>
      )}
      {driver === 'uturn' && (
        <p className="mt-1.5 text-[10.5px] leading-snug text-neutral-500">
          5.4 m turning radius, rear wheels up to 15° against the fronts <span className="text-neutral-400">published</span>
          <span className="mx-1 text-neutral-300">·</span>
          front angles from the geometry <span className="text-neutral-400">ours</span>
        </p>
      )}
    </div>
  );
}

/**
 * The G9L's nose-in parking has no device of its own (no screen or app of the maker's is photographed), so it starts from
 * this panel: the button stands for the voice command the maker says can start parking from outside the car.
 */
export function NoseInTools() {
  const clock = useTechClock();
  const phase = parkPhase(clock);
  const stage = useRuntime()?.stage;
  // this panel is what covers the foot of the window (no device stands beside the stage): the camera keeps the car clear of it
  const setInset = useVehicleStore((s) => s.setDeviceInset);
  React.useEffect(() => {
    setInset({ right: 0, bottom: 0.2 });
    return () => setInset({ right: 0, bottom: 0 });
  }, [setInset]);

  const action =
    phase === 'parking' || phase === 'leaving'
      ? { label: 'Pause', run: pauseDemo }
      : phase === 'paused-in' || phase === 'paused-out'
        ? { label: 'Resume', run: () => techClock.play() }
        : phase === 'parked'
          ? { label: 'Voice command · park out', run: () => techClock.play() }
          : phase === 'done'
            ? { label: 'Again', run: () => { resetDemo(); techClock.play(); } }
            : { label: 'Voice command · park', run: () => techClock.play() };
  const line =
    phase === 'parking'
      ? 'Turning in on the rear-wheel steering.'
      : phase === 'leaving'
        ? 'Backing out.'
        : phase === 'parked'
          ? 'Parked nose first: the boot is at the lane.'
          : phase === 'done'
            ? 'Out again, where it began.'
            : phase === 'ready'
              ? 'Standing in the lane beside an empty bay.'
              : 'Paused.';
  return (
    <div className={`pointer-events-auto w-full max-w-[620px] rounded-2xl px-3.5 py-2.5 ${GLASS}`}>
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={action.run}
          disabled={!stage}
          className={`shrink-0 rounded-full bg-neutral-900 px-4 py-2 text-[12px] font-medium text-white transition-opacity disabled:opacity-40 ${FOCUS}`}
        >
          {action.label}
        </button>
        <div className="min-w-0 flex-1 text-[12px] leading-snug text-neutral-700">{line}</div>
        {stage && (
          <div className="tnum shrink-0 text-right text-[11px] leading-tight text-neutral-500">
            <div className="text-[15px] font-medium text-neutral-900">{stage.clearance.toFixed(2)} m</div>
            least gap
          </div>
        )}
      </div>
    </div>
  );
}
