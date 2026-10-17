'use client';

import React from 'react';
import { pauseDemo, resetDemo } from '@/lib/tech/actions';
import { techClock, useTechClock } from '@/lib/tech/clock';
import { parkPhase } from '@/lib/tech/phase';
import { useRuntime } from '@/lib/tech/session';
import { useVehicleStore } from '@/store/vehicle-store';
import { FOCUS, GLASS } from './Chrome';

/**
 * The SU7's parking assist panel, the showroom's and not the car's (the car's parking screen has not been photographed, so the
 * demo has no device): the button that starts the search, what the car is doing, and the least gap to the cars beside the bay.
 * The line follows the demo's clock against the times the plan found (park.ts: when the bay is seen, when the drive along
 * the row ends).
 */
export function ParkAssistTools() {
  const clock = useTechClock();
  const phase = parkPhase(clock);
  const stage = useRuntime()?.stage;
  const search = stage?.search;
  // this panel covers the foot of the window: the camera keeps the car clear of it
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
          ? { label: 'Pull out', run: () => techClock.play() }
          : phase === 'done'
            ? {
                label: 'Again',
                run: () => {
                  resetDemo();
                  techClock.play();
                },
              }
            : { label: 'Find a bay', run: () => techClock.play() };
  const inward = phase === 'parking' || phase === 'paused-in';
  const line =
    inward && search
      ? clock.t < search.found
        ? 'Along the row at a walking pace, looking for a bay'
        : clock.t < search.end
          ? 'Empty bay found: stopping to back in'
          : 'Reversing into the bay'
      : phase === 'leaving' || phase === 'paused-out'
        ? 'Pulling out'
        : phase === 'parked'
          ? 'Parked, nose to the lane'
          : phase === 'done'
            ? 'Out again, back in the lane'
            : 'At the start of a row of bays';
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
        <div className="min-w-0 flex-1 text-[12px] leading-snug text-neutral-700" aria-live="polite">
          {line}
        </div>
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
