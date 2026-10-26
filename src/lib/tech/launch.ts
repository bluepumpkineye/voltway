import type { Layout, PlannedRun, Sample } from './kinematics';
import type { RoadStage } from './carpet';
import type { Chassis } from './ride';

/**
 * The launch demo's run (docs/tech-showcase.md section 10): a standing start to 100 km/h and on to 200, then off
 * the power.
 *
 * Published (the vehicle's data): the time to 100 km/h and, when it has one, to 200 km/h. The maker's page words the
 * first as "2 seconds to 100" with a footnote saying it excludes rollout and needs Pirelli P Zero Trofeo RS tyres.
 * Ours, said on screen: everything between (the shape of the pull, the squat of the tail, the wheels' slip),
 * because the maker publishes none of it.
 *
 * Like the Magic Carpet's run the car stays on the spot and the road rolls under it (`RigState.scroll`).
 * No imports of values: it runs under plain Node, as ride.ts does.
 */

/** the car stands on the line before it goes, s */
export const HOLD = 0.6;
/** how long the pull takes to build to its full strength, s */
const BUILD = 0.15;
/** off the power at the end: the pull eases away over this, s */
const EASE = 0.5;
/** and the car holds what it has for this long, so the body is seen to settle, s */
const COAST = 5.9;
export const V100 = 100 / 3.6;
export const V200 = 200 / 3.6;

/** the body's nose-up pitch per g of acceleration, rad: about 0.9 degrees, ours (a soft-sprung sedan with some anti-squat) */
const SQUAT_PER_G = (0.9 * Math.PI) / 180;
/** the body's pitch response: 1.5 Hz, damping ratio 0.35 */
const PITCH_OMEGA = 2 * Math.PI * 1.5;
const PITCH_ZETA = 0.35;
const G = 9.81;

const STEP = 1 / 480;
/**
 * The most the wheels are drawn turning, rad/s (about 3 turns a second): a screen cannot show them any faster, and a
 * wheel turning at the road's speed strobes at 60 frames a second. Below it the wheels turn as the road and the slip say.
 */
const SPIN_SHOWN = 20;

export interface LaunchReadout {
  /** km/h */
  speed: number;
  /** longitudinal acceleration in g */
  g: number;
  /** the stopwatch from the moment the car goes, s */
  elapsed: number;
  /** the wheels' surface speed over the road's, 0.12 = 12 % */
  slip: number;
}

/** The published times the stopwatch is checked against. */
export interface LaunchMark {
  /** km/h */
  speed: number;
  /** s */
  time: number;
}

export interface LaunchRun {
  track: PlannedRun;
  road: RoadStage;
  scroll: (t: number) => number;
  chassis: (t: number) => Chassis;
  /** what the readout shows at time t, and the published times it is checked against */
  launch: { readout: (t: number) => LaunchReadout; marks: LaunchMark[]; target?: number };
  frame: { cx: number; cz: number; radius: number; camera: { az: number; el: number } };
}

const smooth = (x: number) => {
  const t = Math.min(1, Math.max(0, x));
  return t * t * (3 - 2 * t);
};

/** Tyre slip by speed: a launch holds the tyres a little past their grip, and the slip fades as the car gets going. */
const slipAt = (v: number) => 0.16 * Math.exp(-v / 15);

/**
 * Past 100 km/h the pull falls with speed, a = a0 (V100 / v)^p, as a power-limited car's does. The exponent that
 * takes the car from 100 to 200 km/h in the published time.
 */
function falloff(a0: number, span: number): number {
  const time = (p: number) => {
    // integral of dv / a(v) from 100 to 200 km/h, by the midpoint rule
    const n = 2000;
    const dv = (V200 - V100) / n;
    let t = 0;
    for (let i = 0; i < n; i++) {
      const v = V100 + (i + 0.5) * dv;
      t += dv / (a0 * Math.pow(V100 / v, p));
    }
    return t;
  };
  let lo = 0;
  let hi = 4;
  for (let i = 0; i < 40; i++) {
    const mid = (lo + hi) / 2;
    if (time(mid) < span) lo = mid;
    else hi = mid;
  }
  return (lo + hi) / 2;
}

export function planLaunch(
  layout: Layout,
  body: { rear: number; front: number; halfWidth: number },
  start: { x: number; y: number; yaw: number },
  opts: { zeroTo100: number; zeroTo200?: number; targetSpeed?: number },
): LaunchRun {
  const t100 = opts.zeroTo100;
  const t200 = opts.zeroTo200 && opts.zeroTo200 > t100 + 0.5 ? opts.zeroTo200 : null;
  // the pull's strength up to 100: a plateau, with the build-up at the start, that reaches 100 km/h exactly at t100
  const a0 = V100 / (t100 - BUILD / 2);
  const p = t200 ? falloff(a0, t200 - t100) : 0;
  // the pull goes on to 200 km/h when the car has a published time for it and not capped to 100, else it eases off at 100
  const target = opts.targetSpeed === 100 ? 100 : (t200 ? 200 : 100);
  const tPull = target === 100 ? t100 : (t200 ?? t100);
  // for 200 km/h: passes 200 at t200 (6.09s), shifts 4th->5th at 204 km/h, climbs to ~212 km/h
  const tPeak = target === 200 ? tPull + 1.2 : tPull;
  const tEnd = HOLD + tPeak + EASE + COAST;

  let aEase = a0;
  // the longitudinal acceleration (m/s^2) at a time and speed
  const accel = (t: number, v: number): number => {
    const tau = t - HOLD;
    if (tau <= 0) return 0;
    if (tau < t100) return a0 * smooth(tau / BUILD);
    if (tau < tPull) {
      aEase = a0 * Math.pow(V100 / Math.max(v, V100), p);
      return aEase;
    }
    if (tau < tPeak) {
      return aEase * 0.85 * (1 - 0.5 * smooth((tau - tPull) / (tPeak - tPull)));
    }
    return aEase * 0.42 * (1 - smooth((tau - tPeak) / EASE));
  };

  // integrate speed, distance, the wheels' angle, and the body's pitch on its springs; keep every 1/60 s
  const SAVE = 8;
  const n = Math.ceil(tEnd / STEP) + 1;
  const kept = Math.floor(n / SAVE) + 2;
  const V = new Float32Array(kept);
  const S = new Float32Array(kept);
  const A = new Float32Array(kept);
  const P = new Float32Array(kept);
  const Q = new Float32Array(kept);
  const W = [0, 1, 2, 3].map(() => new Float32Array(kept));
  const radius = [layout.radius.FL, layout.radius.FR, layout.radius.RL, layout.radius.RR];
  let v = 0;
  let s = 0;
  let pitch = 0;
  let pitchRate = 0;
  const spin = [0, 0, 0, 0];
  let k = 0;
  for (let i = 0; i < n; i++) {
    const t = i * STEP;
    const a = accel(t, v);
    if (i % SAVE === 0) {
      V[k] = v;
      S[k] = s;
      A[k] = a;
      P[k] = pitch;
      Q[k] = slipAt(v);
      for (let j = 0; j < 4; j++) W[j][k] = spin[j];
      k++;
    }
    // the wheels spin a touch ahead of the road, and at the very start spin up before the car has moved
    const lead = t >= HOLD ? 1.2 * Math.exp(-(t - HOLD) / 0.18) : 0;
    const roll = v * (1 + slipAt(v)) + lead;
    for (let j = 0; j < 4; j++) {
      const w = roll / radius[j];
      spin[j] += SPIN_SHOWN * Math.tanh(w / SPIN_SHOWN) * STEP;
    }
    v += a * STEP;
    s += v * STEP;
    const target = (a / G) * SQUAT_PER_G;
    pitchRate += (-2 * PITCH_ZETA * PITCH_OMEGA * pitchRate - PITCH_OMEGA * PITCH_OMEGA * (pitch - target)) * STEP;
    pitch += pitchRate * STEP;
  }
  // hold the last values to the end of the arrays, so a read at the very end does not run into zeros
  for (const arr of [V, S, A, P, Q, ...W]) arr.fill(arr[k - 1], k);
  const dt = STEP * SAVE;
  const at = (arr: Float32Array, t: number) => {
    const f = Math.min(Math.max(t, 0) / dt, kept - 2);
    const i = Math.floor(f);
    return arr[i] + (arr[i + 1] - arr[i]) * (f - i);
  };
  const length = at(S, tEnd);

  const track: PlannedRun = {
    duration: tEnd,
    stats: { maxSteer: 0, bounds: { min: { x: start.x, y: start.y }, max: { x: start.x + length, y: start.y } } },
    sample: (t: number): Sample => ({
      x: start.x + at(S, t),
      y: start.y,
      yaw: start.yaw,
      steer: [0, 0, 0, 0],
      spin: [at(W[0], t), at(W[1], t), at(W[2], t), at(W[3], t)],
      speed: at(V, t),
      segment: 0,
      phase: 'move',
    }),
    trace: () => [],
  };

  const marks: LaunchMark[] = [{ speed: 100, time: t100 }];
  if (t200) marks.push({ speed: 200, time: t200 });
  return {
    track,
    // the strip is a long one, with broad dashes: what streams past is the speed
    road: { humps: [], from: -10, to: length + 30, width: 5.2, markings: { period: 9, length: 3.2, joint: 12.5 } },
    scroll: (t) => at(S, t),
    chassis: (t) => ({ heave: 0, pitch: at(P, t), lift: [0, 0, 0, 0] }),
    launch: {
      readout: (t) => ({ speed: at(V, t) * 3.6, g: at(A, t) / G, elapsed: Math.max(0, t - HOLD), slip: at(Q, t) }),
      marks,
      target,
    },
    frame: {
      cx: start.x + (body.front - body.rear) / 2,
      cz: -start.y,
      radius: (body.rear + body.front) * 0.62,
      camera: { az: 72, el: 8 },
    },
  };
}
