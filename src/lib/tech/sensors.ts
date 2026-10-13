import type { Layout, PlannedRun, Sample } from './kinematics';
import type { RoadStage } from './carpet';
import type { Chassis } from './ride';

/**
 * The Luxeed RX's sensor demo, "what the car sees" (docs/tech-showcase.md section 12): the car cruises at 50 km/h, the
 * sensors' coverage is drawn from where each one sits, a pedestrian steps off the kerb ahead, and the car brakes to a
 * stop short of them.
 *
 * Published (the maker, Autohome's configuration table, Huawei): 38 sensors; the Ultra trims have four lidars, ONE
 * forward 896-line dual-optical-path (wide and tele) in the roof housing and THREE solid-state (two at the sides, one
 * at the rear), five millimetre-wave radars and twelve ultrasonic sensors; a 14 cm box is recognised at 120 m; the car
 * has the CAS 5.0 anti-collision system. Ours, said on the panel: the scenario itself (the pedestrian, the speeds, the
 * braking), every cone's angle and the reach it is drawn to (no field of view is published; the real reach is longer
 * than the drawing), where the solid-state lidars are drawn from (reported, not photographed) and the speed of the
 * sweep. Like the launch the car stays on the spot and the road rolls under it. No value imports: it runs under Node.
 */

/** the cruise, m/s (50 km/h) */
export const CRUISE = 50 / 3.6;
/** the braking, m/s^2: hard, short of a full stop on dry tarmac */
export const DECEL = 8;
const G = 9.81;
/** nose dip per g of braking, rad (about 1.1 degrees; ours) */
const DIP_PER_G = (1.1 * Math.PI) / 180;
const PITCH_OMEGA = 2 * Math.PI * 1.6;
const PITCH_ZETA = 0.38;

/** the seconds of the run at which each thing happens */
export const TIMES = {
  /** the pedestrian steps off the kerb */
  step: 1.6,
  /** the system decides that they are in the car's way, and then brakes */
  risk: 1.95,
  brake: 2.2,
  end: 8.0,
} as const;

/** the pedestrian: walking speed across the road, m/s, where they start (m from the road's middle, + toward the passenger side) */
const WALK = 1.4;
const KERB_Z = 3.0;
/** how far ahead of the car's front the pedestrian is when they step off, m */
const GAP_AT_STEP = 24;
/** the width the car's path is taken to have, half, m */
const PATH_HALF = 1.15;
/** the drawn reach of the sensors (illustrative: the real ones see further), m */
export const REACH = { wide: 18, tele: 45, side: 14, rear: 12, ultrasonic: 2.4 } as const;

export type SensorsState = 'scanning' | 'tracking' | 'risk' | 'braking' | 'stopped' | 'clear';

export interface SensorsReadout {
  state: SensorsState;
  /** km/h */
  speed: number;
  /** the distance from the car's front to the pedestrian's line, m */
  gap: number;
  /** the time to reach the pedestrian's line at this speed, s; null while the car is not moving */
  ttc: number | null;
  /** the pedestrian is in the car's path */
  inPath: boolean;
  braking: boolean;
}

export interface Pedestrian {
  /** m ahead of the car's front */
  ahead: number;
  /** m from the road's middle, + toward the passenger side */
  z: number;
  /** the walk cycle, radians, 0 while standing */
  stride: number;
  walking: boolean;
}

export interface SensorsRun {
  track: PlannedRun;
  /** the car's nose, x in the viewer's frame, where the pedestrian's distance is measured from */
  frontX: number;
  road: RoadStage;
  scroll: (t: number) => number;
  chassis: (t: number) => Chassis;
  scenario: {
    pedestrian: (t: number) => Pedestrian;
    readout: (t: number) => SensorsReadout;
    /** where the car stops, m before the pedestrian's line */
    stopGap: number;
    /** the pedestrian's line on the road, as a run distance from where the rear axle started (the road's own x) */
    pedX: number;
  };
  frame: { cx: number; cz: number; radius: number; camera: { az: number; el: number } };
}

export function planSensors(
  layout: Layout,
  body: { rear: number; front: number; halfWidth: number },
  start: { x: number; y: number; yaw: number },
): SensorsRun {
  const tEnd = TIMES.end;
  const tStop = TIMES.brake + CRUISE / DECEL;
  const STEP = 1 / 240;
  const SAVE = 4;
  const n = Math.ceil(tEnd / STEP) + 1;
  const kept = Math.floor(n / SAVE) + 2;
  const V = new Float32Array(kept);
  const S = new Float32Array(kept);
  const A = new Float32Array(kept);
  const P = new Float32Array(kept);
  const W = [0, 1, 2, 3].map(() => new Float32Array(kept));
  const radius = [layout.radius.FL, layout.radius.FR, layout.radius.RL, layout.radius.RR];
  let v = CRUISE;
  let s = 0;
  let pitch = 0;
  let pitchRate = 0;
  const spin = [0, 0, 0, 0];
  let k = 0;
  for (let i = 0; i < n; i++) {
    const t = i * STEP;
    // brake hard from the decision and ease off the pedal as the car comes to rest
    const a = t >= TIMES.brake && v > 0 ? -DECEL * (v < 1.2 ? Math.max(0.2, v / 1.2) : 1) : 0;
    if (i % SAVE === 0) {
      V[k] = v;
      S[k] = s;
      A[k] = a;
      P[k] = pitch;
      for (let j = 0; j < 4; j++) W[j][k] = spin[j];
      k++;
    }
    for (let j = 0; j < 4; j++) spin[j] += (v / radius[j]) * STEP;
    v = Math.max(0, v + a * STEP);
    s += v * STEP;
    // the body dips under braking on its springs and rocks back as the car stops
    const target = (a / G) * DIP_PER_G;
    pitchRate += (-2 * PITCH_ZETA * PITCH_OMEGA * pitchRate - PITCH_OMEGA * PITCH_OMEGA * (pitch - target)) * STEP;
    pitch += pitchRate * STEP;
  }
  for (const arr of [V, S, A, P, ...W]) arr.fill(arr[k - 1], k);
  const dt = STEP * SAVE;
  const at = (arr: Float32Array, t: number) => {
    const f = Math.min(Math.max(t, 0) / dt, kept - 2);
    const i = Math.floor(f);
    return arr[i] + (arr[i + 1] - arr[i]) * (f - i);
  };
  const length = at(S, tEnd);

  // the pedestrian's line, in the road's frame measured from the car's front at t = 0
  const lineAt = GAP_AT_STEP + at(S, TIMES.step);
  const ahead = (t: number) => lineAt - at(S, t);
  const pedZ = (t: number) => {
    const u = Math.max(0, t - TIMES.step);
    // a step off the kerb: a short ramp to walking pace
    const ramp = u < 0.35 ? (u * u) / (2 * 0.35) : u - 0.175;
    return Math.max(-KERB_Z, KERB_Z - WALK * ramp);
  };
  const tIn = TIMES.step + (KERB_Z - PATH_HALF) / WALK + 0.175;
  const tOut = TIMES.step + (KERB_Z + PATH_HALF) / WALK + 0.175;
  const tAcross = TIMES.step + (2 * KERB_Z) / WALK + 0.175;

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

  const pedestrian = (t: number): Pedestrian => {
    const walking = t >= TIMES.step && t < tAcross;
    return { ahead: ahead(t), z: pedZ(t), stride: walking ? (t - TIMES.step) * Math.PI * 2 * 1.7 : 0, walking };
  };

  const readout = (t: number): SensorsReadout => {
    const speed = at(V, t);
    const gap = ahead(t);
    const inPath = t >= tIn && t < tOut;
    let state: SensorsState = 'scanning';
    if (t >= tAcross - 0.4) state = 'clear';
    else if (t >= tStop - 1e-3) state = 'stopped';
    else if (t >= TIMES.brake) state = 'braking';
    else if (t >= TIMES.risk) state = 'risk';
    else if (gap < 45) state = 'tracking';
    return { state, speed: speed * 3.6, gap, ttc: speed > 0.3 ? gap / speed : null, inPath, braking: t >= TIMES.brake && speed > 0.05 };
  };

  return {
    track,
    frontX: start.x + body.front,
    // a plain road, long enough for the run; the tar joints and the broken edge lines stream by at the car's speed
    road: { humps: [], from: -10, to: length + 70, width: 5.2, markings: { period: 9, length: 3.2, joint: 12.5 } },
    scroll: (t) => at(S, t),
    chassis: (t) => ({ heave: 0, pitch: at(P, t), lift: [0, 0, 0, 0] }),
    scenario: { pedestrian, readout, stopGap: ahead(tStop), pedX: body.front + lineAt },
    frame: {
      // the car, and the road ahead of it that the sensors cover: the camera stands behind and above
      cx: start.x + (body.front - body.rear) / 2 + 7,
      cz: -start.y,
      radius: 12,
      camera: { az: 150, el: 20 },
    },
  };
}
