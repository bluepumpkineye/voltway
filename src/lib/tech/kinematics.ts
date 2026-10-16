/**
 * The kinematics of a car on a flat floor, for the showroom's tech demos
 * (docs/tech-showcase.md). Pure maths, no three.js, so it can be checked
 * against analytic values.
 *
 * A demo's motion is a PLAN: a list of segments, each a rigid motion of the whole
 * car, either a translation (a straight line, or a diagonal crab walk) or a
 * rotation about a point (an arc, a pivot, a four-wheel-steer turn). A wheel that
 * rolls without sliding points along its own contact velocity, so the steering
 * angles of every mode fall out of one rule instead of one formula per mode:
 *
 *     v_wheel = omega x (p_wheel - C)        rotation about C
 *     v_wheel = d                            translation
 *     steer   = atan2(v_y, v_x), folded to (-90, 90] degrees
 *
 * Front-wheel steering is a rotation about a point on the rear axle's line (the
 * Ackermann angles fall out), a crab walk a translation at an angle, a "compass
 * turn" a rotation about a front wheel's contact patch.
 *
 * Frames: x forward, y LEFT (the viewer's z is -y), angles counter-clockwise
 * from above, so a positive steer angle turns the wheel to the left. The car's
 * origin is the middle of its rear axle.
 */

export type Corner = 'FL' | 'FR' | 'RL' | 'RR';
export const CORNERS: readonly Corner[] = ['FL', 'FR', 'RL', 'RR'];

export interface Vec2 {
  x: number;
  y: number;
}

/** The car's wheels: contact centres relative to the middle of the rear axle, and tyre radii. */
export interface Layout {
  wheels: Record<Corner, Vec2>;
  radius: Record<Corner, number>;
  wheelbase: number;
}

/** A layout from wheel centres measured in any frame with x forward and y left. */
export function layoutFrom(centres: Record<Corner, Vec2>, radius: Record<Corner, number>): Layout {
  const rx = (centres.RL.x + centres.RR.x) / 2;
  const ry = (centres.RL.y + centres.RR.y) / 2;
  const wheels = {} as Record<Corner, Vec2>;
  for (const c of CORNERS) wheels[c] = { x: centres[c].x - rx, y: centres[c].y - ry };
  const front = (wheels.FL.x + wheels.FR.x) / 2;
  return { wheels, radius, wheelbase: front };
}

export type Segment =
  | {
      kind: 'move';
      /** metres travelled along the heading below; negative reverses */
      distance: number;
      /** the direction of travel in the car's frame, rad (0 straight ahead; a crab walk is a small angle) */
      angle?: number;
      /**
       * The angles the wheels are really set to, per corner (FL, FR, RL, RR), rad, when they are not all the direction of
       * travel: a car whose rear wheels turn less than its fronts (the Z9's crab walk: rear wheels at most 10 degrees, the
       * crab angle up to 15). A wheel off its own velocity rolls the part of it that lies along its plane and scrubs the rest.
       */
      steer?: readonly number[];
      label?: string;
    }
  | {
      kind: 'turn';
      /** the centre of rotation in the car's frame at the start of the segment, m */
      about: Vec2;
      /** signed, rad: positive is counter-clockwise from above (the car swings left) */
      angle: number;
      /**
       * The angles the wheels are really set to, when they cannot take the direction a no-slip turn asks of them: a
       * compass turn about a front wheel asks the rear wheels to point sideways, and the Z9 splays them 10 degrees
       * instead and lets the tyres scrub. The pivot wheel (no velocity) keeps its angle.
       */
      steer?: readonly number[];
      label?: string;
    };

/** Front-wheel steering round a circle of this radius at the rear axle: forward is positive, a reverse negative. */
export function arc(radius: number, deg: number, side: 'left' | 'right', reverse = false): Segment {
  const s = (side === 'left' ? 1 : -1) * (reverse ? -1 : 1);
  return { kind: 'turn', about: { x: 0, y: side === 'left' ? radius : -radius }, angle: (s * deg * Math.PI) / 180 };
}

export interface Motion {
  /** top speed of the fastest wheel, m/s */
  vmax: number;
  /** acceleration and braking, m/s^2 */
  accel: number;
  /** how fast the wheels steer while the car waits, rad/s (steering at rest) */
  steerRate: number;
  /** a pause at the end of every segment (a gear change), s */
  dwell: number;
  /** the least time steering takes when it has to move, s */
  steerMin: number;
}

export const MOTION: Motion = { vmax: 1.3, accel: 0.9, steerRate: 1.1, dwell: 0.35, steerMin: 0.4 };

export interface Sample {
  /** the middle of the rear axle in the floor frame (x forward at the start, y left), and its heading */
  x: number;
  y: number;
  yaw: number;
  /** per corner, rad, positive turns the wheel left */
  steer: [number, number, number, number];
  /** per corner, rad rolled forward (cumulative) */
  spin: [number, number, number, number];
  /** speed of the fastest wheel, m/s (0 while waiting or steering) */
  speed: number;
  /** index of the plan's segment */
  segment: number;
  phase: 'steer' | 'move' | 'dwell';
}

interface Phase {
  t0: number;
  t1: number;
  seg: number;
  phase: Sample['phase'];
  /** pose and spin at the start of the segment (the end, after its move) */
  pose0: { x: number; y: number; yaw: number };
  spin0: number[];
  steer0: number[];
  steer1: number[];
  /** wheel path length of the move, m */
  length: number;
  /** per-wheel rolled distance at the end of the move, signed, m */
  rolled: number[];
  segment: Segment;
  profile: Profile | null;
}

/** A trapezoidal speed profile over a path length. */
class Profile {
  readonly length: number;
  readonly accel: number;
  readonly tAcc: number;
  readonly tCruise: number;
  readonly vPeak: number;
  readonly duration: number;
  constructor(length: number, vmax: number, accel: number) {
    this.length = length;
    this.accel = accel;
    let v = vmax;
    let ta = v / accel;
    const dAcc = 0.5 * accel * ta * ta;
    if (length < 2 * dAcc) {
      // too short to reach top speed: accelerate to the middle, then brake
      v = Math.sqrt(length * accel);
      ta = v / accel;
      this.tCruise = 0;
    } else {
      this.tCruise = (length - 2 * dAcc) / v;
    }
    this.tAcc = ta;
    this.vPeak = v;
    this.duration = 2 * ta + this.tCruise;
  }
  /** distance covered after tau seconds */
  at(tau: number): number {
    const { tAcc, tCruise, vPeak, accel, length } = this;
    if (tau <= 0) return 0;
    if (tau >= this.duration) return length;
    if (tau < tAcc) return 0.5 * accel * tau * tau;
    if (tau < tAcc + tCruise) return 0.5 * accel * tAcc * tAcc + vPeak * (tau - tAcc);
    const r = this.duration - tau;
    return length - 0.5 * accel * r * r;
  }
  /** speed after tau seconds */
  speed(tau: number): number {
    const { tAcc, tCruise, vPeak, accel } = this;
    if (tau <= 0 || tau >= this.duration) return 0;
    if (tau < tAcc) return accel * tau;
    if (tau < tAcc + tCruise) return vPeak;
    return accel * (this.duration - tau);
  }
}

const TAU = Math.PI * 2;
const wrapPi = (a: number) => a - TAU * Math.round(a / TAU);
const smooth = (t: number) => t * t * (3 - 2 * t);

/** Fold a wheel direction to (-90, 90] degrees: a wheel rolls either way along its plane. */
function fold(a: number): number {
  let d = wrapPi(a);
  if (d > Math.PI / 2 + 1e-9) d -= Math.PI;
  else if (d <= -Math.PI / 2 + 1e-9) d += Math.PI;
  return d;
}

/**
 * The steering angle each wheel needs for a segment, and how far each rolls per
 * unit of the segment's parameter (m of travel for a move, rad for a turn).
 * `hold` is returned for a wheel that does not move (a pivot's centre).
 */
export function segmentWheels(
  layout: Layout,
  seg: Segment,
  hold: readonly number[] = [0, 0, 0, 0],
): { steer: number[]; roll: number[]; reach: number } {
  const steer: number[] = [];
  const roll: number[] = [];
  let reach = 0;
  CORNERS.forEach((c, i) => {
    const w = layout.wheels[c];
    if (seg.kind === 'move') {
      const beta = seg.angle ?? 0;
      const set = seg.steer?.[i] ?? beta;
      steer.push(set);
      // a wheel set off the direction of travel rolls only the part of the path that lies along its plane
      roll.push((Math.sign(seg.distance) || 1) * Math.cos(beta - set));
      reach = 1;
    } else {
      const rx = w.x - seg.about.x;
      const ry = w.y - seg.about.y;
      const r = Math.hypot(rx, ry);
      const omega = Math.sign(seg.angle) || 1;
      if (r < 1e-6) {
        steer.push(seg.steer?.[i] ?? hold[i] ?? 0);
        roll.push(0);
        return;
      }
      // contact velocity of a point turning counter-clockwise about the centre
      const vx = -omega * ry;
      const vy = omega * rx;
      const set = seg.steer?.[i];
      const d = set ?? fold(Math.atan2(vy, vx));
      steer.push(d);
      // rolling forward along the wheel's own heading, or backward; with the wheel set by hand, the
      // velocity's component along its plane (the rest is scrub)
      const along = vx * Math.cos(d) + vy * Math.sin(d);
      roll.push(set === undefined ? Math.sign(along) * r : along);
      reach = Math.max(reach, r);
    }
  });
  return { steer, roll, reach };
}

export interface TrackStats {
  /** the widest steering angle any wheel reaches, rad */
  maxSteer: number;
  /** floor extents of the middle of the rear axle (x, y), m */
  bounds: { min: Vec2; max: Vec2 };
}

/** A planned motion, sampled at any time. */
export class Track {
  readonly duration: number;
  readonly stats: TrackStats;
  private readonly phases: Phase[];
  private readonly layout: Layout;
  private readonly start: { x: number; y: number; yaw: number };

  /**
   * `start` is where the middle of the rear axle stands at t = 0 (the car's
   * rest pose in the floor frame); `motion` is how briskly it moves.
   */
  constructor(
    layout: Layout,
    plan: Segment[],
    motion: Motion = MOTION,
    start: { x: number; y: number; yaw: number } = { x: 0, y: 0, yaw: 0 },
  ) {
    this.layout = layout;
    this.phases = [];
    this.start = start;
    let t = 0;
    let pose = { ...start };
    let spin = [0, 0, 0, 0];
    let steer = [0, 0, 0, 0];
    let maxSteer = 0;
    const min = { x: start.x, y: start.y };
    const max = { x: start.x, y: start.y };

    plan.forEach((seg, k) => {
      const w = segmentWheels(layout, seg, steer);
      const dSteer = Math.max(...w.steer.map((a, i) => Math.abs(a - steer[i])));
      if (dSteer > 1e-4) {
        const dur = Math.max(motion.steerMin, dSteer / motion.steerRate);
        this.phases.push(this.stay('steer', t, t + dur, k, pose, spin, steer, w.steer, seg));
        t += dur;
      }
      for (const a of w.steer) maxSteer = Math.max(maxSteer, Math.abs(a));

      // how far the fastest wheel travels, and each wheel's rolled distance
      const span = seg.kind === 'move' ? Math.abs(seg.distance) : Math.abs(seg.angle);
      const length = seg.kind === 'move' ? span : span * w.reach;
      const rolled = w.roll.map((r) => r * span);
      if (length > 1e-6) {
        const profile = new Profile(length, motion.vmax, motion.accel);
        this.phases.push({
          t0: t, t1: t + profile.duration, seg: k, phase: 'move', pose0: pose, spin0: spin,
          steer0: w.steer, steer1: w.steer, length, rolled, segment: seg, profile,
        });
        t += profile.duration;
        const end = poseAt(pose, seg, 1);
        pose = end;
        spin = spin.map((s, i) => s + rolled[i] / layout.radius[CORNERS[i]]);
        // coarse extents: the path between is bounded by the ends and, for a turn, a few samples
        for (let j = 0; j <= 16; j++) {
          const p = poseAt(this.phases[this.phases.length - 1].pose0, seg, j / 16);
          min.x = Math.min(min.x, p.x); min.y = Math.min(min.y, p.y);
          max.x = Math.max(max.x, p.x); max.y = Math.max(max.y, p.y);
        }
      }
      steer = w.steer;
      if (motion.dwell > 0 && k < plan.length - 1) {
        this.phases.push(this.stay('dwell', t, t + motion.dwell, k, pose, spin, steer, steer, seg));
        t += motion.dwell;
      }
    });
    this.duration = t;
    this.stats = { maxSteer, bounds: { min, max } };
  }

  private stay(
    phase: 'steer' | 'dwell', t0: number, t1: number, seg: number,
    pose: Phase['pose0'], spin: number[], from: number[], to: number[], segment: Segment,
  ): Phase {
    return {
      t0, t1, seg, phase, pose0: pose, spin0: spin, steer0: from, steer1: to, length: 0,
      rolled: [0, 0, 0, 0], segment, profile: null,
    };
  }

  /** The car at time t (clamped to the plan). */
  sample(t: number): Sample {
    const ph = this.phases;
    if (!ph.length) {
      return { ...this.start, steer: [0, 0, 0, 0], spin: [0, 0, 0, 0], speed: 0, segment: 0, phase: 'dwell' };
    }
    const tt = Math.min(Math.max(t, 0), this.duration);
    // phases are few: a linear scan from the end is plenty
    let i = ph.length - 1;
    while (i > 0 && ph[i].t0 > tt) i--;
    const p = ph[i];
    const tau = tt - p.t0;
    if (p.phase === 'move' && p.profile) {
      const f = p.profile.at(tau) / p.length;
      const pose = poseAt(p.pose0, p.segment, f);
      const spin = p.spin0.map((s, j) => s + (p.rolled[j] * f) / this.layout.radius[CORNERS[j]]);
      return {
        x: pose.x, y: pose.y, yaw: pose.yaw,
        steer: p.steer1 as Sample['steer'], spin: spin as Sample['spin'],
        speed: p.profile.speed(tau), segment: p.seg, phase: 'move',
      };
    }
    const k = p.t1 > p.t0 ? smooth(Math.min(1, tau / (p.t1 - p.t0))) : 1;
    const steer = p.steer0.map((a, j) => a + (p.steer1[j] - a) * k);
    return {
      x: p.pose0.x, y: p.pose0.y, yaw: p.pose0.yaw,
      steer: steer as Sample['steer'], spin: p.spin0 as Sample['spin'],
      speed: 0, segment: p.seg, phase: p.phase,
    };
  }

  /** When segment k begins (its steering at rest included) and when its move ends, s. */
  span(k: number): { t0: number; tEnd: number } | null {
    const mine = this.phases.filter((p) => p.seg === k);
    if (!mine.length) return null;
    const moves = mine.filter((p) => p.phase === 'move');
    return { t0: mine[0].t0, tEnd: (moves.length ? moves[moves.length - 1] : mine[mine.length - 1]).t1 };
  }

  /** The path of the middle of the rear axle, for drawing on the floor; up to time `until` if given. */
  trace(step = 0.1, until = Infinity): Vec2[] {
    const out: Vec2[] = [];
    for (const p of this.phases) {
      if (p.phase !== 'move' || p.t1 > until + 1e-9) continue;
      const n = Math.max(2, Math.ceil(p.length / step));
      for (let j = 0; j <= n; j++) {
        const q = poseAt(p.pose0, p.segment, j / n);
        out.push({ x: q.x, y: q.y });
      }
    }
    return out;
  }

  /** How many segments the plan has. */
  segments(): number {
    return this.phases.reduce((m, p) => Math.max(m, p.seg + 1), 0);
  }
}

/** What the director needs of a run: a `Track`, or any other plan with its own speed profile (the launch's). */
export type PlannedRun = Pick<Track, 'duration' | 'stats' | 'sample' | 'trace'>;

/** The pose of the rear axle's middle after the fraction f of a segment that began at `p0`. */
export function poseAt(p0: { x: number; y: number; yaw: number }, seg: Segment, f: number) {
  const c0 = Math.cos(p0.yaw);
  const s0 = Math.sin(p0.yaw);
  if (seg.kind === 'move') {
    const beta = seg.angle ?? 0;
    const d = seg.distance * f;
    const lx = Math.cos(beta) * d;
    const ly = Math.sin(beta) * d;
    return { x: p0.x + c0 * lx - s0 * ly, y: p0.y + s0 * lx + c0 * ly, yaw: p0.yaw };
  }
  // rotation about `about` (in the frame at the start): pos = p0 + R(yaw0) c - R(yaw0 + theta) c
  const th = seg.angle * f;
  const c1 = Math.cos(p0.yaw + th);
  const s1 = Math.sin(p0.yaw + th);
  const { x: cx, y: cy } = seg.about;
  return {
    x: p0.x + (c0 * cx - s0 * cy) - (c1 * cx - s1 * cy),
    y: p0.y + (s0 * cx + c0 * cy) - (s1 * cx + c1 * cy),
    yaw: p0.yaw + th,
  };
}

/** Ackermann angles (rad) for a car steering round a circle of radius R at the rear axle's middle. */
export function ackermann(wheelbase: number, trackFront: number, radius: number) {
  return {
    inner: Math.atan(wheelbase / (radius - trackFront / 2)),
    outer: Math.atan(wheelbase / (radius + trackFront / 2)),
  };
}
