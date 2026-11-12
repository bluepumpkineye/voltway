import { runShape } from './drive-beats';
import type { DriveFacts } from './drive-run';

/**
 * The Drive tab's curve: a corner in the road, a short, sharp arc to the left that the car drives into while it holds its speed, so that the run shows
 * the car going round a corner and not only down a straight. No React and no three.js; a pure function of the run, so a scrubbed run shows the same
 * road as a played one.
 *
 * The corner belongs to the road, not to the clock: it is an arc at a fixed distance along the road (`sa` to `sb`, in the run's scroll, the metres the
 * road has rolled under the car). It is drawn bent in the road's vertex shader (`withBend`, viewer/scenery/kit.ts), so it is seen from far up the road
 * long before the car gets there (it comes out of the haze, the road ahead already curving away), the car drives into it, the road already driven turns
 * back behind it, and past it the road runs straight again. The first version bent the whole road about the car as a function of time, and the road
 * curved all at once from nowhere.
 *
 * The run itself is unchanged (the car's speed, its power and its figures are the maker's published ones and the planner's): the corner is drawn on
 * top. The front wheels turn into it and the body leans out (TechDirector), as a car does through a corner at the speed it is going. What is drawn is
 * ours: a corner tighter than a street car could take at the speed (1.5 g at 100 km/h: a radius of 60 m, through about 105 degrees in 3.7 s), the
 * steering and the lean drawn larger than they are (as the S-curve's wheels are: they would not be seen at their real size). The road is two lanes
 * (drive-run.ts) so that the corner is seen against the car, not against empty asphalt.
 *
 * It goes where the car holds a steady speed (a cruise, or a coast) for long enough, never over the pull or the stop, and not at all on a run that
 * has manoeuvres of its own (an S-curve, a slalom, a crab walk: they turn the car already) or on a wet road (the rain's mirror is a flat sheet).
 */

const G = 9.81;
/** the lateral acceleration the corner is drawn at, in g (ours: a hard corner, so that it is seen from a camera beside the car) */
const LATERAL_G = 1.5;
/** the tightest and the widest the corner gets, m: at a low speed the road bends sharply, at 200 km/h it is a long, wide arc */
const R_MIN = 50;
const R_MAX = 220;
/** how far round the road turns, rad (about 105 degrees); a steady stretch too short for it gets a smaller corner, and under about 50 degrees none */
const ANGLE = 1.83;
const MIN_ANGLE = 0.9;
/** the most the lean and the steering follow, g (a faster run has a wide corner that would not be a g and more) */
const G_DRAWN_MAX = 1;
/** a corner is for a car at speed: the least speed at the middle of its stretch, km/h */
const MIN_KMH = 55;
/** the least stretch of steady speed worth a corner, s, and the steady speed kept either side of it, s */
const MIN_SPAN_S = 5;
const KEEP_S = 1.2;
/** the steering and the lean ease in over this many metres on each side of the arc's ends (the road itself has no such ease: the wheels do) */
const EASE_M = 8;

export interface Bend {
  /** where the arc begins and ends along the road, m (the run's scroll) */
  sa: number;
  sb: number;
  /** the arc's curvature, 1/m: negative bends to the left (toward -z in the viewer's axes) */
  k: number;
  /** the curvature the car steers at when it is `s` metres along the road: the arc's, eased in and out around its ends */
  kCar: (s: number) => number;
  /** the lateral acceleration the car feels at `s` going `v` m/s, g, at most the most the lean follows */
  gCar: (s: number, v: number) => number;
}

const smooth = (x: number) => {
  const t = Math.min(1, Math.max(0, x));
  return t * t * (3 - 2 * t);
};

/**
 * The corner for a run, or null when the run has no stretch for one (or turns on its own). `scroll` is the run's distance rolled by time
 * (DriveRun.scroll).
 */
export function bendFor(facts: DriveFacts, duration: number, scroll: (t: number) => number): Bend | null {
  if (facts.lateral || facts.env.wet) return null;
  const shape = runShape(facts, duration);
  const spans = [...(shape.spans.cruise ?? []), ...(shape.spans.coast ?? [])];
  let best: { from: number; to: number } | null = null;
  for (const s of spans) {
    const len = s.to - s.from;
    if (len < MIN_SPAN_S) continue;
    if (facts.telemetry((s.from + s.to) / 2).speed < MIN_KMH) continue;
    if (!best || len > best.to - best.from) best = s;
  }
  if (!best) return null;
  // the corner sits in the middle of the stretch; the radius follows from the speed there, and the arc is as long as the stretch allows
  const tc = (best.from + best.to) / 2;
  const v = Math.max(5, facts.telemetry(tc).speed / 3.6);
  const R = Math.min(R_MAX, Math.max(R_MIN, (v * v) / (LATERAL_G * G)));
  const room = best.to - best.from - 2 * KEEP_S;
  const angle = Math.min(ANGLE, (room * v) / R);
  if (angle < MIN_ANGLE) return null;
  const half = (R * angle) / 2;
  const sm = scroll(tc);
  const sa = sm - half;
  const sb = sm + half;
  const k = -1 / R;
  const kCar = (s: number) => k * smooth((s - (sa - EASE_M)) / (2 * EASE_M)) * smooth((sb + EASE_M - s) / (2 * EASE_M));
  return {
    sa,
    sb,
    k,
    kCar,
    gCar: (s, vMs) => Math.min(G_DRAWN_MAX, (vMs * vMs * Math.abs(kCar(s))) / G),
  };
}
