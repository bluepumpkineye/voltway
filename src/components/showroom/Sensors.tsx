'use client';

import React from 'react';
import { pauseDemo } from '@/lib/tech/actions';
import { techClock, useTechClock } from '@/lib/tech/clock';
import { LAYERS, toggleLayer, useLayers, type LayerId } from '@/lib/tech/layers';
import { runPhase } from '@/lib/tech/phase';
import type { SensorsState } from '@/lib/tech/sensors';
import { useSensorsReadout } from '@/lib/tech/session';
import { useVehicleStore } from '@/store/vehicle-store';
import { FOCUS, GLASS } from './Chrome';

/** The groups of sensors the demo draws: the colour in the scene, what it is, and the maker's count where there is one. */
const GROUPS: { id: LayerId; label: string; note: string; color: string }[] = [
  { id: 'lidar', label: 'Roof lidar', note: '896 lines, wide and tele paths', color: '#2f6bff' },
  { id: 'side', label: 'Side lidars', note: '2, solid-state', color: '#0fa594' },
  { id: 'rear', label: 'Rear lidar', note: '1, solid-state', color: '#8b5cf6' },
  { id: 'ultrasonic', label: 'Ultrasonic', note: '12', color: '#f59e0b' },
  { id: 'cameras', label: 'Cameras', note: 'as photographed', color: '#9aa0a9' },
];

const SAYS: Record<SensorsState, string> = {
  scanning: 'Scanning ahead',
  tracking: 'Pedestrian at the kerb: tracked',
  risk: 'Pedestrian stepping into the car’s path',
  braking: 'Collision risk: braking',
  stopped: 'Stopped short of the pedestrian',
  clear: 'Path clear',
};

/**
 * The sensor demo's own panel, the showroom's and not the car's (the car's screen has no photographed page for it): the
 * button that starts the run, what the car is doing now, and a switch for each group of sensors. The counts are the
 * maker's and Autohome's (a tooltip on each switch), the cones and the scenario are ours; the demo's facts say so.
 */
export function SensorsTools() {
  const clock = useTechClock();
  const run = runPhase(clock);
  const r = useSensorsReadout();
  const layers = useLayers();
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
          <div className="truncate text-[13px] font-medium text-neutral-900">{r ? SAYS[r.state] : 'Loading the car…'}</div>
          <div className="tnum truncate text-[11px] text-neutral-500">
            {r ? `${Math.round(r.speed)} km/h · ${Math.max(0, r.gap).toFixed(1)} m to the crossing${r.ttc !== null && r.ttc < 6 ? ` · ${r.ttc.toFixed(1)} s` : ''}` : ' '}
          </div>
        </div>
      </div>
      <div className="mt-2 flex flex-wrap gap-1.5" role="group" aria-label="Sensors drawn">
        {GROUPS.filter((g) => LAYERS.includes(g.id)).map((g) => (
          <button
            key={g.id}
            type="button"
            aria-pressed={layers[g.id]}
            onClick={() => toggleLayer(g.id)}
            title={`${g.label}: ${g.note}`}
            className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] transition-opacity ${FOCUS} ${
              layers[g.id] ? 'bg-black/[0.07] text-neutral-800' : 'bg-black/[0.03] text-neutral-400'
            }`}
          >
            <span className="h-[8px] w-[8px] shrink-0 rounded-full" style={{ background: layers[g.id] ? g.color : '#c9ccd2' }} aria-hidden />
            {g.label}
          </button>
        ))}
      </div>
    </div>
  );
}
