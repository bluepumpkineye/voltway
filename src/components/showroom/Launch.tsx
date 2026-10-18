'use client';

import React from 'react';
import type { Vehicle } from '@/data/vehicles/schema';
import { techClock, useTechClock } from '@/lib/tech/clock';
import { pauseDemo } from '@/lib/tech/actions';
import { runPhase } from '@/lib/tech/phase';
import { useRuntime } from '@/lib/tech/session';
import { useVehicleStore } from '@/store/vehicle-store';
import { GLASS } from './Chrome';

const FOCUS = 'outline-none focus-visible:ring-2 focus-visible:ring-neutral-900/70 focus-visible:ring-offset-1';

/** how far the g bar reaches, g */
const G_SPAN = 1.8;

/**
 * The launch demo's own panel, the showroom's and not the car's (no photograph or screen of a launch exists, so
 * the demo starts here and on the playback bar): the button that starts it, the speed, the pull in g and the
 * stopwatch checked against the two published times. The speed and the bar are written straight to the page every
 * frame while the car runs, so they are as smooth as the car; the readout is a simulation (src/lib/tech/launch.ts)
 * and the panel says which times are the maker's.
 */
export function LaunchTools({ vehicle }: { vehicle?: Vehicle } = {}) {
  const isNio = vehicle?.slug === 'nio-es8';
  const accent = isNio ? '#00C2A8' : '#2f6bff';
  const launch = useRuntime()?.launch;
  const clock = useTechClock();
  const run = runPhase(clock);
  const speed = React.useRef<HTMLSpanElement>(null);
  const gText = React.useRef<HTMLSpanElement>(null);
  const gFill = React.useRef<HTMLSpanElement>(null);
  const watch = React.useRef<HTMLSpanElement>(null);
  const marks = React.useRef<(HTMLLIElement | null)[]>([]);
  const playing = clock.playing;
  // this panel is what covers the foot of the window (no device stands beside the stage): the camera keeps the car clear of it
  const setInset = useVehicleStore((s) => s.setDeviceInset);
  React.useEffect(() => {
    setInset({ right: 0, bottom: 0.22 });
    return () => setInset({ right: 0, bottom: 0 });
  }, [setInset]);
  // while the clock is not running the panel follows its snapshots (a scrub, a pause)
  const still = playing ? 0 : clock.t;

  React.useEffect(() => {
    if (!launch) return;
    const paint = () => {
      const r = launch.readout(techClock.t);
      if (speed.current) speed.current.textContent = String(Math.round(r.speed));
      if (gText.current) gText.current.textContent = `${Math.max(0, r.g).toFixed(2)} g`;
      if (gFill.current) gFill.current.style.width = `${Math.min(100, Math.max(0, (r.g / G_SPAN) * 100))}%`;
      if (watch.current) watch.current.textContent = `${r.elapsed.toFixed(2)} s`;
      launch.marks.forEach((m, i) => {
        marks.current[i]?.setAttribute('data-reached', r.elapsed >= m.time - 1e-3 ? 'true' : 'false');
      });
    };
    paint();
    if (!playing) return;
    let raf = requestAnimationFrame(function loop() {
      paint();
      raf = requestAnimationFrame(loop);
    });
    return () => cancelAnimationFrame(raf);
  }, [launch, playing, still]);

  const action =
    run === 'driving'
      ? { label: 'Pause', run: pauseDemo }
      : run === 'paused'
        ? { label: 'Resume', run: () => techClock.play() }
        : run === 'done'
          ? { label: 'Launch again', run: () => techClock.play() }
          : { label: 'Launch', run: () => techClock.play() };

  return (
    <div className={`pointer-events-auto w-full max-w-[620px] rounded-2xl px-3.5 py-2.5 ${GLASS}`}>
      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={action.run}
          disabled={!launch}
          className={`shrink-0 rounded-full bg-neutral-900 px-4 py-2 text-[12px] font-medium text-white transition-opacity disabled:opacity-40 ${FOCUS}`}
        >
          {action.label}
        </button>
        <div className="flex min-w-0 flex-1 items-baseline gap-1.5" aria-live="off">
          <span ref={speed} className="tnum text-[34px] font-semibold leading-none tracking-tight text-neutral-900">
            0
          </span>
          <span className="text-[12px] text-neutral-500">km/h</span>
        </div>
        <div className="shrink-0 text-right">
          <span ref={watch} className="tnum text-[17px] font-medium leading-none text-neutral-900">
            0.00 s
          </span>
        </div>
      </div>
      <div className="mt-2 flex items-center gap-2.5">
        <span className="w-[26px] text-[10.5px] text-neutral-500">Pull</span>
        <span className="relative h-[6px] min-w-0 flex-1 overflow-hidden rounded-full bg-black/[0.07]">
          <span ref={gFill} className="absolute inset-y-0 left-0 rounded-full" style={{ width: '0%', backgroundColor: accent }} />
        </span>
        <span ref={gText} className="tnum w-[52px] text-right text-[11px] text-neutral-700">
          0.00 g
        </span>
      </div>
      <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-neutral-500">
        {(launch?.marks ?? []).map((m, i) => (
          <li
            key={m.speed}
            ref={(el) => {
              marks.current[i] = el;
            }}
            data-reached="false"
            className="group tnum transition-colors data-[reached=true]:font-medium data-[reached=true]:text-neutral-900"
          >
            0–{m.speed} km/h <span className="group-data-[reached=true]:font-semibold" style={{ color: accent }}>{m.time.toFixed(2)} s</span>
            <span className="ml-1 text-neutral-400">published</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
