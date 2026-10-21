'use client';

import React from 'react';
import type { SensorSpec, Vehicle } from '@/data/vehicles/schema';
import { pauseDemo } from '@/lib/tech/actions';
import { techClock, useTechClock } from '@/lib/tech/clock';
import { toggleLayer, useLayers, type LayerId } from '@/lib/tech/layers';
import { runPhase } from '@/lib/tech/phase';
import { useSensorsReadout } from '@/lib/tech/session';
import { useVehicleStore } from '@/store/vehicle-store';
import { FOCUS, GLASS } from './Chrome';

/** The groups of sensors the demo draws: the colour in the scene, what it is, and the car's own count where the maker gives one. */
const GROUPS: { id: LayerId; label: string; note: string; color: string; has: (s: SensorSpec) => boolean }[] = [
  { id: 'lidar', label: 'Roof lidar', note: 'The forward lidar', color: '#2f6bff', has: (s) => !!s.lidar },
  { id: 'side', label: 'Side lidars', note: 'Solid-state, one on each side', color: '#0fa594', has: (s) => !!s.sideLidar },
  { id: 'rear', label: 'Rear lidar', note: 'Solid-state, at the tail', color: '#8b5cf6', has: (s) => !!s.rearLidar },
  { id: 'surround', label: 'Surround cameras', note: 'Drawn as four diagonal beams', color: '#38a8ff', has: (s) => !!s.surround },
  { id: 'vision', label: 'Camera views', note: 'What the cameras see, drawn from where each sits', color: '#4aa3ff', has: (s) => !!s.views?.length },
  { id: 'ultrasonic', label: 'Ultrasonic', note: 'Close-range sensors round the bumpers', color: '#f59e0b', has: (s) => s.ultrasonic.length > 0 },
  { id: 'cameras', label: 'Cameras', note: 'As photographed', color: '#9aa0a9', has: (s) => s.cameras.length > 0 },
];

/**
 * Autonomous Drive's own panel, the showroom's and not the car's (the car's screen has no photographed page for it): the
 * button that starts the run, what the car is doing now, and a switch for each group of sensors the car has. The counts
 * are the makers' and Autohome's (a tooltip on each switch); the scenario, the cones and their reach are ours, and the
 * demo's facts say so.
 */
export function SensorsTools({ vehicle }: { vehicle: Vehicle }) {
  const clock = useTechClock();
  const run = runPhase(clock);
  const r = useSensorsReadout();
  const layers = useLayers();
  const spec = vehicle.sensors;
  // this panel covers the foot of the window: the camera keeps the car clear of it
  const setInset = useVehicleStore((s) => s.setDeviceInset);
  React.useEffect(() => {
    setInset({ right: 0, bottom: 0.2 });
    return () => setInset({ right: 0, bottom: 0 });
  }, [setInset]);

  const action =
    run === 'driving'
      ? { label: 'Pause', run: pauseDemo }
      : run === 'paused'
        ? { label: 'Resume', run: () => techClock.play() }
        : run === 'done'
          ? { label: 'Again', run: () => techClock.play() }
          : { label: 'Start', run: () => techClock.play() };

  return (
    <div className={`pointer-events-auto w-full max-w-[620px] rounded-2xl px-3.5 py-2.5 ${GLASS}`}>
      <div className="flex items-center gap-3">
        <button type="button" onClick={action.run} disabled={!r} className={`shrink-0 rounded-full bg-neutral-900 px-4 py-2 text-[12px] font-medium text-white transition-opacity disabled:opacity-40 ${FOCUS}`}>
          {action.label}
        </button>
        <div className="min-w-0 flex-1" aria-live="polite">
          <div className="flex items-center gap-1.5 truncate text-[13px] font-medium text-neutral-900">
            {r?.indicator ? <span className="text-[#f59e0b]" aria-hidden>{r.indicator > 0 ? '◀' : '▶'}</span> : null}
            <span className="truncate">{r ? r.message : 'Loading the car…'}</span>
          </div>
          <div className="tnum truncate text-[11px] text-neutral-500">
            {r
              ? `${Math.round(r.speed)} km/h${r.gap !== null ? ` · ${Math.max(0, r.gap).toFixed(0)} m to the car ahead` : ''} · ${r.tracked} tracked${r.note ? ` · ${r.note}` : ''}`
              : ' '}
          </div>
        </div>
      </div>
      {spec && (
        <div className="mt-2 flex flex-wrap gap-1.5" role="group" aria-label="Sensors drawn">
          {GROUPS.filter((g) => g.has(spec)).map((g) => (
            <button
              key={g.id}
              type="button"
              aria-pressed={layers[g.id]}
              onClick={() => toggleLayer(g.id)}
              title={`${g.label}: ${spec.notes?.[g.id] ?? g.note}`}
              className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] transition-opacity ${FOCUS} ${
                layers[g.id] ? 'bg-black/[0.07] text-neutral-800' : 'bg-black/[0.03] text-neutral-400'
              }`}
            >
              <span className="h-[8px] w-[8px] shrink-0 rounded-full" style={{ background: layers[g.id] ? g.color : '#c9ccd2' }} aria-hidden />
              {g.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
