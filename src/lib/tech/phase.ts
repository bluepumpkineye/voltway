/**
 * Where the parking demonstration is, as a visitor would say it. The demo is one clock with one stop (the
 * car parked): the stretch before the stop is the way in, the stretch after it the way out. The devices
 * (the phone's app, the car's parking page) show the same state because they read it from the clock.
 */
import { legOf, type ClockSnapshot } from './clock';

export type ParkPhase =
  /** the car stands where it began, waiting for a device to start it */
  | 'ready'
  | 'parking'
  | 'paused-in'
  /** parked in the bay, waiting for the way out */
  | 'parked'
  | 'leaving'
  | 'paused-out'
  /** out again, where it began */
  | 'done';

export function parkPhase(c: ClockSnapshot): ParkPhase {
  const leg = legOf(c);
  // running: before the stop is the way in (the stop itself belongs to the way out, which a press of play starts)
  if (c.playing) return c.t < (c.stops[0] ?? Infinity) - 1e-3 ? 'parking' : 'leaving';
  if (leg.atEnd) return 'done';
  if (leg.atStart) return leg.index === 0 ? 'ready' : 'parked';
  return leg.index === 0 ? 'paused-in' : 'paused-out';
}

/**
 * Where a demonstration with no stops is (the Magic Carpet's run): standing at the top, driving, paused on the way,
 * or at the end.
 */
export type RunPhase = 'ready' | 'driving' | 'paused' | 'done';

export function runPhase(c: ClockSnapshot): RunPhase {
  if (c.playing) return 'driving';
  if (c.duration > 0 && c.t >= c.duration - 0.02) return 'done';
  return c.t < 0.02 ? 'ready' : 'paused';
}

/** How far through the current way (in or out), 0 to 1. */
export function parkProgress(c: ClockSnapshot): number {
  return legOf(c).frac;
}
