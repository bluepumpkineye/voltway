/**
 * The tech demo's clock: where the playhead is, and whether it runs.
 *
 * It lives outside React and outside the zustand store on purpose. The viewer
 * advances it every frame while a demo plays, and a store write per frame would
 * wake every subscriber; the panel only needs the time about ten times a second,
 * and at once when the visitor presses play or drags the scrubber. The panel
 * reads it with `useTechClock()` (a snapshot that changes at that rate); the
 * viewer reads `clock.t` directly.
 *
 * A demo can have STOPS: times where a running clock halts and waits for the
 * visitor, such as the car sitting parked until they ask for the way out. Pressing
 * play at a stop goes on; scrubbing past one does not trigger it.
 */
import React from 'react';

export interface ClockSnapshot {
  /** seconds into the demo */
  t: number;
  /** length of the demo's motion, s (0 when there is none) */
  duration: number;
  playing: boolean;
  /** the times a running clock stops at, s (ascending) */
  stops: readonly number[];
}

type Listener = () => void;

/** How often a running clock tells the panel, ms. */
const EMIT_EVERY = 100;

const NONE: readonly number[] = [];

class TechClock {
  /** authoritative time, advanced by the viewer every frame */
  t = 0;
  duration = 0;
  playing = false;
  private stops: readonly number[] = NONE;
  private snap: ClockSnapshot = { t: 0, duration: 0, playing: false, stops: NONE };
  private subs = new Set<Listener>();
  private lastEmit = 0;

  /**
   * Start a demo of this length from the top: running, unless `play` is false (it then waits
   * for a press of play, or of a device in the showroom that starts it).
   */
  load(duration: number, opts: boolean | { play?: boolean; stops?: readonly number[] } = true) {
    const o = typeof opts === 'boolean' ? { play: opts } : opts;
    this.t = 0;
    this.duration = duration;
    this.stops = o.stops ? [...o.stops].sort((a, b) => a - b) : NONE;
    this.playing = (o.play ?? true) && duration > 0;
    this.emit();
  }

  play() {
    // pressing play at the end plays it again
    if (this.t >= this.duration) this.t = 0;
    this.playing = this.duration > 0;
    this.emit();
  }

  pause() {
    this.playing = false;
    this.emit();
  }

  seek(t: number) {
    this.t = Math.min(Math.max(t, 0), this.duration);
    this.emit();
  }

  /** Move the playhead from the frame loop; halts at a stop, and tells the panel at its own pace. */
  advance(t: number, now: number) {
    if (this.playing) {
      const stop = this.stops.find((s) => s > this.t + 1e-6 && s <= t + 1e-9);
      if (stop !== undefined) {
        this.t = stop;
        this.playing = false;
        this.emit(now);
        return;
      }
    }
    this.t = t;
    if (t >= this.duration && this.playing) {
      this.playing = false;
      this.emit(now);
    } else if (now - this.lastEmit >= EMIT_EVERY) {
      this.emit(now);
    }
  }

  private emit(now = performance.now()) {
    this.lastEmit = now;
    this.snap = { t: this.t, duration: this.duration, playing: this.playing, stops: this.stops };
    for (const fn of this.subs) fn();
  }

  subscribe = (fn: Listener) => {
    this.subs.add(fn);
    return () => {
      this.subs.delete(fn);
    };
  };

  snapshot = () => this.snap;
}

export const techClock = new TechClock();

const serverSnapshot: ClockSnapshot = { t: 0, duration: 0, playing: false, stops: NONE };

/** The clock as the panel sees it. */
export function useTechClock(): ClockSnapshot {
  return React.useSyncExternalStore(techClock.subscribe, techClock.snapshot, () => serverSnapshot);
}

/**
 * Where a clock with stops is, as a visitor would put it: which leg of the demo (the stretches between
 * its stops), how far through it, and whether it stands at one end of it.
 */
export interface Leg {
  /** 0 is the stretch up to the first stop */
  index: number;
  /** how many stretches the demo has */
  of: number;
  /** progress through this stretch, 0..1 */
  frac: number;
  /** waiting at the start of the stretch (the top of the demo, or a stop) */
  atStart: boolean;
  /** waiting at the end of the whole demo */
  atEnd: boolean;
}

const EPS = 0.02;

export function legOf(s: ClockSnapshot): Leg {
  const edges = [0, ...s.stops, s.duration];
  const of = edges.length - 1;
  let index = 0;
  // the stretch the playhead is in; standing exactly on a stop is the start of the next one
  for (let i = 0; i < of; i++) if (s.t >= edges[i] - EPS) index = i;
  const a = edges[index];
  const b = edges[index + 1];
  const frac = b > a ? Math.min(1, Math.max(0, (s.t - a) / (b - a))) : 0;
  const atEnd = s.duration > 0 && s.t >= s.duration - EPS;
  return { index: atEnd ? of - 1 : index, of, frac: atEnd ? 1 : frac, atStart: !atEnd && Math.abs(s.t - a) < EPS, atEnd };
}
