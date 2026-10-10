'use client';

import React from 'react';
import type { TechDemoSpec } from '@/data/vehicles/schema';
import { techClock, useTechClock } from '@/lib/tech/clock';
import { GLASS } from './Chrome';

const FOCUS =
  'outline-none focus-visible:ring-2 focus-visible:ring-neutral-900/70 focus-visible:ring-offset-1';

const SPEEDS = [0.5, 1, 2];

const mmss = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;

/** The car's demonstrations, as chips like the wheel designs. */
export function TechChips({
  demos,
  selected,
  onSelect,
}: {
  demos: TechDemoSpec[];
  selected: string;
  onSelect: (id: string) => void;
}) {
  const cur = demos.find((d) => d.id === selected) ?? demos[0];
  return (
    <div role="group" aria-label="Demonstration" className={`pointer-events-auto flex w-fit max-w-full overflow-x-auto rounded-full p-1 ${GLASS}`}>
      {demos.map((d) => (
        <button
          key={d.id}
          type="button"
          aria-pressed={d.id === cur.id}
          onClick={() => onSelect(d.id)}
          className={`shrink-0 whitespace-nowrap rounded-full px-4 py-1.5 text-[12px] font-medium transition-colors ${FOCUS} ${
            d.id === cur.id ? 'bg-neutral-900 text-white' : 'text-neutral-600 hover:text-neutral-900'
          }`}
        >
          {d.title}
        </button>
      ))}
    </div>
  );
}

function Icon({ d, label }: { d: string; label: string }) {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor" aria-label={label} role="img">
      <path d={d} />
    </svg>
  );
}

const PLAY = 'M3.5 2.2v9.6a.6.6 0 0 0 .92.5l7.4-4.8a.6.6 0 0 0 0-1L4.42 1.7a.6.6 0 0 0-.92.5z';
const PAUSE = 'M3 2h2.6v10H3zM8.4 2H11v10H8.4z';
const REPLAY =
  'M7 2.2a4.8 4.8 0 1 0 4.5 6.4.7.7 0 1 0-1.3-.5A3.4 3.4 0 1 1 7 3.6h.7L6.6 4.7a.7.7 0 1 0 1 1l2.4-2.4a.7.7 0 0 0 0-1L7.6.4a.7.7 0 0 0-1 1l.9.8z';

/** Play and pause, replay, the playhead and its speed. */
export function TechControls({
  speed,
  onSpeed,
  disabled,
}: {
  speed: number;
  onSpeed: (s: number) => void;
  disabled?: string;
}) {
  const clock = useTechClock();
  const resume = React.useRef(false);
  const off = Boolean(disabled) || clock.duration <= 0;
  return (
    <div
      className={`pointer-events-auto flex w-full max-w-[620px] items-center gap-2 rounded-full px-2 py-1.5 ${GLASS}`}
      title={disabled}
    >
      <button
        type="button"
        disabled={off}
        aria-label={clock.playing ? 'Pause' : 'Play'}
        onClick={() => (clock.playing ? techClock.pause() : techClock.play())}
        className={`grid h-8 w-8 shrink-0 place-items-center rounded-full bg-neutral-900 text-white transition-opacity disabled:opacity-35 ${FOCUS}`}
      >
        <Icon d={clock.playing ? PAUSE : PLAY} label={clock.playing ? 'Pause' : 'Play'} />
      </button>
      <button
        type="button"
        disabled={off}
        aria-label="Replay from the start"
        onClick={() => {
          techClock.seek(0);
          techClock.play();
        }}
        className={`grid h-8 w-8 shrink-0 place-items-center rounded-full text-neutral-600 hover:text-neutral-900 disabled:opacity-35 ${FOCUS}`}
      >
        <Icon d={REPLAY} label="Replay" />
      </button>
      <div className="relative flex min-w-0 flex-1 items-center">
        <input
          type="range"
          aria-label="Position in the demonstration"
          min={0}
          max={Math.max(clock.duration, 0.01)}
          step={0.01}
          value={Math.min(clock.t, clock.duration)}
          disabled={off}
          onPointerDown={() => {
            resume.current = techClock.playing;
            techClock.pause();
          }}
          onPointerUp={() => {
            if (resume.current) techClock.play();
          }}
          onChange={(e) => techClock.seek(Number(e.target.value))}
          className="h-1 w-full min-w-0 cursor-pointer accent-neutral-900 disabled:cursor-default disabled:opacity-35"
        />
        {/* where the demonstration waits for the visitor (the car parked, until they ask for the way out) */}
        {clock.duration > 0 &&
          clock.stops.map((s) => (
            <span
              key={s}
              className="pointer-events-none absolute top-1/2 h-3 w-[2px] -translate-y-1/2 rounded bg-neutral-400"
              style={{ left: `calc(${(s / clock.duration) * 100}% * 0.96 + 2%)` }}
              aria-hidden
            />
          ))}
      </div>
      <span className="tnum w-[76px] shrink-0 text-right text-[11px] text-neutral-500">
        {mmss(clock.t)} / {mmss(clock.duration)}
      </span>
      <div role="group" aria-label="Speed" className="flex shrink-0 rounded-full bg-black/[0.04] p-0.5">
        {SPEEDS.map((s) => (
          <button
            key={s}
            type="button"
            aria-pressed={speed === s}
            onClick={() => onSpeed(s)}
            className={`tnum rounded-full px-2 py-1 text-[11px] font-medium transition-colors ${FOCUS} ${
              speed === s ? 'bg-white text-neutral-900 shadow-sm' : 'text-neutral-500 hover:text-neutral-800'
            }`}
          >
            {s}×
          </button>
        ))}
      </div>
    </div>
  );
}

/**
 * What the demonstration is, the published facts behind it and what in it is simulated. One line until
 * opened, so the stage and the devices keep the screen; the line already says it is a simulation.
 */
export function TechFacts({ spec }: { spec: TechDemoSpec }) {
  const [open, setOpen] = React.useState(false);
  return (
    <div className={`pointer-events-auto w-full max-w-[620px] rounded-2xl px-3.5 py-2 text-[11px] leading-snug text-neutral-600 ${GLASS}`}>
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className={`flex w-full items-center justify-between gap-3 text-left ${FOCUS}`}
      >
        <span className="min-w-0 truncate">
          <span className="font-semibold text-neutral-900">{spec.title}</span>
          <span className="text-neutral-500"> · a simulation from the maker’s published figures</span>
        </span>
        <span className="shrink-0 text-neutral-500">
          {open ? 'Hide' : 'Facts and sources'}
          <svg className={`ml-1 inline transition-transform ${open ? 'rotate-180' : ''}`} width="9" height="6" viewBox="0 0 9 6" aria-hidden>
            <path d="M1 1l3.5 3.5L8 1" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
      </button>
      {open && (
        <div className="mt-1.5">
          <p>{spec.blurb}</p>
          {spec.claims.length > 0 && (
            <ul className="mt-1 list-disc space-y-0.5 pl-4">
              {spec.claims.map((c) => (
                <li key={c.text}>
                  {c.text}{' '}
                  <a
                    href={c.source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="underline decoration-neutral-300 underline-offset-2 hover:text-neutral-900"
                  >
                    {c.source.label}
                  </a>
                </li>
              ))}
            </ul>
          )}
          <p className="mt-1 italic text-neutral-500">{spec.simulated}</p>
        </div>
      )}
    </div>
  );
}
