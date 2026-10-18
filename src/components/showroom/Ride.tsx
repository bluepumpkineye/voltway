'use client';

import React from 'react';
import type { Vehicle } from '@/data/vehicles/schema';
import { useTechClock } from '@/lib/tech/clock';
import { rideLevelsOf, RIDE_SPAN_MM, type RideMode, type RideRun } from '@/lib/tech/ride';
import { useRuntime } from '@/lib/tech/session';
import { useVehicleStore } from '@/store/vehicle-store';
import { GLASS } from './Chrome';

const FOCUS = 'outline-none focus-visible:ring-2 focus-visible:ring-neutral-900/70 focus-visible:ring-offset-1';

const W = 600;
const H = 74;
/** how far the chart reaches up and down from the body's resting height, cm */
const SPAN_CM = 3.5;

/**
 * The Magic Carpet / PrimeRide demo's own controls, the showroom's and not the car's (the car has no such switch): which
 * suspension the body rides on, the ride height when no screen offers it, and the body's height through the
 * run, both suspensions drawn together so the difference is seen and not only felt. It is a simulation
 * (src/lib/tech/ride.ts); the chart says so.
 */
export function RideTools({ vehicle, showHeights }: { vehicle?: Vehicle; showHeights: boolean }) {
  const isNio = vehicle?.slug === 'nio-es8';
  const modes: { id: RideMode; label: string }[] = [
    { id: 'carpet', label: isNio ? 'PrimeRide 4D' : 'Magic Carpet' },
    { id: 'passive', label: isNio ? 'Passive Suspension' : 'Passive' },
  ];
  const spanMm = isNio ? 100 : RIDE_SPAN_MM;
  const levels = React.useMemo(() => rideLevelsOf(spanMm), [spanMm]);
  const activeColor = isNio ? '#00C2A8' : '#2f6bff';
  const carpetOn = useVehicleStore((s) => s.carpetOn);
  const setCarpetOn = useVehicleStore((s) => s.setCarpetOn);
  const level = useVehicleStore((s) => s.rideLevel);
  const setLevel = useVehicleStore((s) => s.setRideLevel);
  const ride = useRuntime()?.ride;
  const easyEntry = useVehicleStore((s) => s.easyEntry);
  const beltOn = useVehicleStore((s) => s.beltOn);
  const setBeltOn = useVehicleStore((s) => s.setBeltOn);
  const moving = useTechClock().playing;
  // the car buckles up by itself once it drives
  React.useEffect(() => {
    if (moving) setBeltOn(true);
  }, [moving, setBeltOn]);
  const mode: RideMode = carpetOn ? 'carpet' : 'passive';
  // with no device standing beside the stage, this panel is what covers the foot of the window: the camera
  // keeps the wheels (what the demo is about) clear of it
  const setInset = useVehicleStore((s) => s.setDeviceInset);
  React.useEffect(() => {
    if (!showHeights) return;
    setInset({ right: 0, bottom: 0.27 });
    return () => setInset({ right: 0, bottom: 0 });
  }, [showHeights, setInset]);

  return (
    <div className={`pointer-events-auto w-full max-w-[620px] rounded-2xl px-3.5 py-2 ${GLASS}`}>
      <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1.5">
        <div role="group" aria-label="Suspension" className="flex rounded-full bg-black/[0.04] p-0.5">
          {modes.map((m) => (
            <button
              key={m.id}
              type="button"
              aria-pressed={m.id === mode}
              onClick={() => setCarpetOn(m.id === 'carpet')}
              className={`rounded-full px-3 py-1 text-[11px] font-medium transition-colors ${FOCUS} ${
                m.id === mode ? 'bg-white text-neutral-900 shadow-sm' : 'text-neutral-500 hover:text-neutral-800'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
        {showHeights && (
          <div role="group" aria-label="Ride height" className="flex min-w-0 overflow-x-auto rounded-full bg-black/[0.04] p-0.5">
            {levels.map((l, i) => (
              <button
                key={l.id}
                type="button"
                aria-pressed={i === level}
                onClick={() => setLevel(i)}
                className={`shrink-0 whitespace-nowrap rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors ${FOCUS} ${
                  i === level ? 'bg-white text-neutral-900 shadow-sm' : 'text-neutral-500 hover:text-neutral-800'
                }`}
              >
                {l.label}
              </button>
            ))}
          </div>
        )}
      </div>
      {easyEntry && !moving && (
        <div className="mt-1.5 flex items-center justify-between gap-3 border-t border-black/[0.06] pt-1.5">
          <span className="text-[11px] leading-snug text-neutral-500">
            {beltOn
              ? isNio
                ? 'Suspension Easy Entry: unbuckle a belt and the ES8 lowers by 50 mm.'
                : 'Suspension easy entry: unbuckle a belt and the parked car lowers.'
              : isNio
                ? 'Belt unbuckled: the ES8 has lowered by 50 mm for effortless exit.'
                : 'Belt unbuckled: the parked car has lowered to let you out.'}
          </span>
          <button
            type="button"
            aria-pressed={!beltOn}
            onClick={() => setBeltOn(!beltOn)}
            className={`shrink-0 rounded-full px-3 py-1 text-[11px] font-medium transition-colors ${FOCUS} ${
              beltOn ? 'bg-black/[0.04] text-neutral-700 hover:text-neutral-900' : 'bg-neutral-900 text-white'
            }`}
          >
            {beltOn ? 'Unbuckle belt' : 'Buckle belt'}
          </button>
        </div>
      )}
      {ride && <BodyChart modes={ride.modes} mode={mode} activeLabel={isNio ? 'PrimeRide 4D' : 'Magic Carpet'} activeColor={activeColor} />}
    </div>
  );
}

/** The body's height through the run, both suspensions, and where the playhead is. */
function BodyChart({
  modes,
  mode,
  activeLabel = 'Magic Carpet',
  activeColor = '#2f6bff',
}: {
  modes: Record<RideMode, RideRun>;
  mode: RideMode;
  activeLabel?: string;
  activeColor?: string;
}) {
  const clock = useTechClock();
  const dur = modes.carpet.duration || 1;
  const colour: Record<RideMode, string> = { carpet: activeColor, passive: '#8a8f98' };
  const paths = React.useMemo(() => {
    const out = {} as Record<RideMode, string>;
    for (const m of ['passive', 'carpet'] as const) {
      const pts: string[] = [];
      for (let t = 0; t <= dur + 1e-6; t += 0.05) {
        const cm = modes[m].sample(t).heave * 100;
        pts.push(`${((t / dur) * W).toFixed(1)} ${(H / 2 - (cm / SPAN_CM) * (H / 2 - 4)).toFixed(1)}`);
      }
      out[m] = 'M' + pts.join(' L');
    }
    return out;
  }, [modes, dur]);
  const x = Math.min(1, clock.t / dur) * W;
  const cm = (m: RideMode) => (modes[m].peak.heave * 100).toFixed(1);
  const other: RideMode = mode === 'carpet' ? 'passive' : 'carpet';
  return (
    <figure className="mt-1.5">
      <svg viewBox={`0 0 ${W} ${H}`} className="block h-[46px] w-full" role="img" aria-label="Body height through the run, both suspensions">
        <line x1="0" x2={W} y1={H / 2} y2={H / 2} stroke="#c9ccd2" strokeWidth="1" strokeDasharray="3 4" />
        <path d={paths[other]} fill="none" stroke={colour[other]} strokeOpacity="0.55" strokeWidth="1.4" vectorEffect="non-scaling-stroke" />
        <path d={paths[mode]} fill="none" stroke={colour[mode]} strokeWidth="2.2" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
        <line x1={x} x2={x} y1="0" y2={H} stroke="#17181b" strokeWidth="1" vectorEffect="non-scaling-stroke" />
      </svg>
      <figcaption className="mt-0.5 flex flex-wrap justify-between gap-x-3 text-[10.5px] leading-snug text-neutral-500">
        <span>Body height over the humps (simulated)</span>
        <span className="tnum">
          <span style={{ color: activeColor }}>{activeLabel} ±{cm('carpet')} cm</span>
          {' · '}
          <span style={{ color: '#6b7078' }}>Passive ±{cm('passive')} cm</span>
        </span>
      </figcaption>
    </figure>
  );
}
