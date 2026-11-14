import type { PlannedRun, Sample } from './kinematics';

/**
 * The Avatr 06T's panoramic Star Ring demo (docs/tech-showcase.md section 29): the 35.4-inch 4K ring that runs across the foot of the
 * windscreen lights up from end to end, the car goes to D and the ring carries what the driver needs (speed, the power meter, the
 * range), a route set on the centre screen puts its next turn on the ring, and media plays on it. The two 6.7-inch mirror screens
 * at its ends show what is behind. The car stands still; the camera is in the driver's seat.
 *
 * Published: the screen's size and resolution, that it runs along the windscreen's foot, that it is mainly for speed, navigation and
 * battery information (ifanr, 2026-04-08), and that it forms a "four-screen linkage" with the 15.6-inch floating centre screen and the
 * two mirror screens (CarNewsChina). The zones and their content are read off Autohome's photographs of the ring (the car, range,
 * power meter and trip at the left; a media card; a trip-energy chart; weather and the time at the right). No page tells how the
 * screens hand content to one another, and no photograph shows the ring in drive, in navigation or the mirror screens lit: all of
 * that, and every number and the timing, is ours, and the panel says so. No value imports: it runs under plain Node.
 */

export interface RingState {
  /** 0 dark, 1 fully lit: the light goes from the left end to the right end */
  wake: number;
  gear: 'P' | 'D';
  /** the seat-belt and parking-brake warning lamps (red, as photographed) */
  belt: boolean;
  brake: boolean;
  /** km/h */
  speed: number;
  /** -1 recovering, 0 neutral, 1 full power */
  power: number;
  rangeKm: number;
  /** the next turn from the route the centre screen has set, or null */
  route: { dist: number; turn: 'right' | 'ahead'; road: string; then: string } | null;
  media: { title: string; artist: string; progress: number };
  /** the mirror screens show the road behind */
  mirrors: boolean;
  clock: string;
}

/** the centre screen's page at each time: the home page, the map while a route is set */
export type CentrePage = 'home' | 'nav';

export interface Beat {
  id: 'wake' | 'drive' | 'route' | 'media';
  label: string;
  t0: number;
  t1: number;
  line: string;
}

export const BEATS: Beat[] = [
  { id: 'wake', label: 'Wakes up', t0: 0.6, t1: 5.5, line: 'The ring lights from end to end: the car, its range and power, the gear' },
  { id: 'drive', label: 'Drives off', t0: 5.5, t1: 8.2, line: 'In D the ring carries the speed, the power meter and the range' },
  { id: 'route', label: 'Guides a turn', t0: 8.2, t1: 17.6, line: 'A route is set on the centre screen: its next turn appears on the ring, in front of the driver' },
  { id: 'media', label: 'Plays media', t0: 17.6, t1: 27.0, line: 'Media plays on the ring: the track changes' },
];

export const T_END = 28;

const clamp = (x: number, a: number, b: number) => Math.min(b, Math.max(a, x));
const smooth = (x: number) => {
  const u = clamp(x, 0, 1);
  return u * u * (3 - 2 * u);
};

/** the light's sweep along the ring, s */
export const WAKE = { from: 0.8, to: 3.4 } as const;
/** the lamps go out when the driver buckles and releases the brake; the car is in D from DRIVE */
const BELT_OFF = 4.4;
const BRAKE_OFF = 5.0;
const DRIVE = 5.6;
/** the speed the car settles at, km/h, and when it starts to slow and when it has stopped */
const CRUISE = 54;
const SLOW = 21.5;
const STOP = 26.0;
/** the route is set at ROUTE, with this far to the turn (m) */
const ROUTE = 8.4;
/** how far the route's first turn is when the route is set, m (the ring's bar counts it down) */
export const TURN_AT = 110;

/** km/h at time t: eases up to the cruise speed, holds it with a little drift, eases to a stop */
export function speedAt(t: number): number {
  if (t < DRIVE) return 0;
  if (t < 12.8) return CRUISE * smooth((t - DRIVE) / (12.8 - DRIVE));
  if (t < SLOW) return CRUISE + 1.4 * Math.sin((t - 12.8) * 0.9);
  return t < STOP ? speedAt(SLOW - 1e-6) * (1 - smooth((t - SLOW) / (STOP - SLOW))) : 0;
}

/** metres driven by time t (the speed's integral, by the trapezoid rule at 0.1 s) */
export function distanceAt(t: number): number {
  let d = 0;
  const dt = 0.1;
  for (let u = 0; u < t; u += dt) {
    const a = Math.min(dt, t - u);
    d += ((speedAt(u) + speedAt(u + a)) / 2 / 3.6) * a;
  }
  return d;
}

export function centreAt(t: number): CentrePage {
  return t >= 7.8 && t < 17.4 ? 'nav' : 'home';
}

const TRACKS = [
  { title: 'Chop chop chop top', artist: 'Tapa Tapa · Aykut Closer' },
  { title: 'Evening on the ring road', artist: 'Voltway sessions' },
];
const TRACK_LENGTH = 34;

export function stateAt(t: number): RingState {
  const speed = speedAt(t);
  const a = (speedAt(t + 0.25) - speedAt(Math.max(0, t - 0.25))) / 0.5;
  // power: pull while it accelerates, a light draw at a steady speed, recovery as it slows
  const power = speed < 0.5 && a <= 0.01 ? 0 : clamp(a / 7 + (speed > 2 ? 0.1 : 0), -1, 1);
  const driven = distanceAt(t);
  const toTurn = TURN_AT - (driven - distanceAt(ROUTE));
  const route =
    t >= ROUTE + 0.4 && toTurn > -22
      ? toTurn > 0
        ? { dist: toTurn, turn: 'right' as const, road: 'Ring Road East', then: 'Then keep ahead for 2.1 km' }
        : null
      : null;
  const track = t < 21.2 ? 0 : 1;
  const since = track === 0 ? t : t - 21.2;
  return {
    wake: smooth((t - WAKE.from) / (WAKE.to - WAKE.from)),
    gear: t >= DRIVE && t < STOP + 0.3 ? 'D' : 'P',
    belt: t >= WAKE.to && t < BELT_OFF,
    brake: t >= WAKE.to && t < BRAKE_OFF,
    speed,
    power,
    rangeKm: Math.round(448 - (driven * 1.3) / 1000),
    route,
    media: { ...TRACKS[track], progress: clamp(0.18 + since / TRACK_LENGTH, 0, 1) },
    mirrors: t >= DRIVE - 0.2 && t < STOP + 0.3,
    clock: `02:${String(21 + Math.floor(t / 60)).padStart(2, '0')}`,
  };
}

export function beatAt(t: number): Beat | null {
  return BEATS.find((b) => t >= b.t0 && t < b.t1) ?? null;
}

export interface StarRingRun {
  /** the car stands still */
  track: PlannedRun;
  state: (t: number) => RingState;
  centre: (t: number) => CentrePage;
  beat: (t: number) => Beat | null;
}

export function planStarRing(start: { x: number; y: number; yaw: number }): StarRingRun {
  const track: PlannedRun = {
    duration: T_END,
    stats: { maxSteer: 0, bounds: { min: { x: start.x, y: start.y }, max: { x: start.x, y: start.y } } },
    sample: (): Sample => ({ ...start, steer: [0, 0, 0, 0], spin: [0, 0, 0, 0], speed: 0, segment: 0, phase: 'dwell' }),
    trace: () => [],
  };
  return { track, state: stateAt, centre: centreAt, beat: beatAt };
}

// ------------------------------------------------------------------ the run on show

/** The demo that is playing, for the ring's driver in the viewer (the director sets it when the demo is built and clears it when it goes). */
let active: StarRingRun | null = null;
export const setStarRingRun = (run: StarRingRun | null) => {
  active = run;
};
export const getStarRingRun = () => active;
