'use client';

import React from 'react';
import { pauseDemo } from '@/lib/tech/actions';
import { techClock, useTechClock } from '@/lib/tech/clock';
import { BEATS as NOMI_BEATS, beatAt as nomiBeatAt, SWEEP } from '@/lib/tech/nomi';
import { runPhase } from '@/lib/tech/phase';
import { BEATS as RING_BEATS, beatAt as ringBeatAt } from '@/lib/tech/starring';
import { useVehicleStore } from '@/store/vehicle-store';
import { FOCUS, GLASS } from './Chrome';

interface BeatLike {
  id: string;
  label: string;
  t0: number;
  line: string;
}

/**
 * The panel of a demo that plays a few things in turn from the driver's seat (NOMI, the Star Ring), the showroom's and not the car's:
 * the button that runs the demo, what is happening now, and a chip for each of the things it plays (a press jumps there and plays on).
 * What the car does is published or photographed; the order, the timing and the poses are ours, and each demo's facts say so.
 */
function BeatTools({
  beats,
  beatAt,
  idle,
  waiting,
  note,
  label,
}: {
  beats: readonly BeatLike[];
  beatAt: (t: number) => BeatLike | null;
  idle: string;
  waiting: string;
  note?: React.ReactNode;
  label: string;
}) {
  const clock = useTechClock();
  const run = runPhase(clock);
  const beat = beatAt(clock.t);
  // the demo is not built until the car's wheels and cabin have loaded (the clock has no length until then): a press before that would be
  // ignored, and only the next one would play. The controls wait for it, as the sensors' panel's do.
  const ready = clock.duration > 0;
  // the subject is the top of the dashboard: the picture is not lifted clear of this panel, as the others' are (it would take the subject up
  // under the menu); the foot of the dash goes behind the panel instead
  const setInset = useVehicleStore((s) => s.setDeviceInset);
  React.useEffect(() => {
    setInset({ right: 0, bottom: 0 });
  }, [setInset]);

  const action =
    run === 'driving'
      ? { label: 'Pause', run: pauseDemo }
      : run === 'paused'
        ? { label: 'Resume', run: () => techClock.play() }
        : run === 'done'
          ? { label: 'Again', run: () => techClock.play() }
          : { label: 'Start', run: () => techClock.play() };

  const go = (t: number) => {
    techClock.seek(t);
    techClock.play();
  };

  return (
    <div className={`pointer-events-auto w-full max-w-[620px] rounded-2xl px-3.5 py-2.5 ${GLASS}`}>
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={action.run}
          disabled={!ready}
          className={`shrink-0 rounded-full bg-neutral-900 px-4 py-2 text-[12px] font-medium text-white transition-opacity disabled:opacity-40 ${FOCUS}`}
        >
          {ready ? action.label : 'Loading…'}
        </button>
        <div className="min-w-0 flex-1 text-[12px] leading-snug text-neutral-700" aria-live="polite">
          <span className="font-medium text-neutral-900">{!ready ? 'Loading the car…' : beat ? beat.line : run === 'ready' ? waiting : idle}</span>
        </div>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-1.5" role="group" aria-label={label}>
        {beats.map((b) => (
          <button
            key={b.id}
            type="button"
            aria-pressed={beat?.id === b.id}
            onClick={() => go(b.t0)}
            disabled={!ready}
            className={`rounded-full px-3 py-1 text-[11px] transition-colors disabled:opacity-40 ${FOCUS} ${
              beat?.id === b.id ? 'bg-neutral-900 text-white' : 'bg-black/[0.06] text-neutral-700 hover:bg-black/[0.1]'
            }`}
          >
            {b.label}
          </button>
        ))}
        {note ? <span className="ml-1 text-[10.5px] text-neutral-400">{note}</span> : null}
      </div>
    </div>
  );
}

/** The ES8's NOMI: a door, a voice, music. The head's travel is one source's; the rest of the demo is ours. */
export function NomiTools() {
  return (
    <BeatTools
      beats={NOMI_BEATS}
      beatAt={nomiBeatAt}
      idle="NOMI is idle"
      waiting="NOMI on the dashboard, waiting"
      label="What NOMI does"
      note={`head travel about ${SWEEP.yaw}° across and ${SWEEP.pitch}° up and down (one source)`}
    />
  );
}

/** The 06T's Star Ring: it wakes, the car drives off, a turn is set on the centre screen, media plays. The layout is photographed; the run is ours. */
export function StarRingTools() {
  return (
    <BeatTools
      beats={RING_BEATS}
      beatAt={ringBeatAt}
      idle="The ring is dark"
      waiting="The 35.4-inch ring across the foot of the windscreen, dark"
      label="What the ring shows"
      note="layout read from photographs; the run is ours"
    />
  );
}
