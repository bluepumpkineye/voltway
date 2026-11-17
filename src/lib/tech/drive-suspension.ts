/**
 * The suspension at work: what a car's body does on its springs while it drives, for the Drive tab, the X-ray tab's Play, the launch demo and the
 * Autonomous Drive scenes. No React and no three.js; a pure function of the run, so a scrubbed run shows the same ride as a played one.
 *
 * Until now the body moved for the pedal and the steering only (the squat and the dive, the lean in a corner: drive-run.ts, drive-bend.ts); between
 * them, at a steady speed, it stood dead still on a road that rolled under it. A real car never does: the road is never flat, and the body, which
 * is a mass on four springs and four dampers, answers every swell and every joint in it. This file is that answer.
 *
 * Why here and not in Blender. The same thing can be keyed by hand on a bone per car (a few frames looped, Bezier between them) and baked into
 * every export; it would be one fixed loop that does not know the speed, the mode or the load, and nine cars to key and re-export. The rig
 * (rig.ts) already splits every car into a sprung body and four unsprung wheels, so the body is moved here, from a model: one
 * file for every car, the road's pace follows the speed (a hump comes faster at 200 km/h than at 60), the front axle meets a joint before the rear
 * one and the body rocks between them, Sport is firmer than Comfort, a full car sinks and floats lower. Layered looping cycles of different lengths are
 * what the hand-keyed version stands in for: three swells that never fall into step, with the joints on top.
 *
 * The model is a half-car-and-roll model: the body (heave, pitch, roll) on four springs and dampers, the four wheels following the road (their
 * heights are the road's, so the tyres stay on it and it is the BODY that is seen to move against them). A road is a sum of swells of 1.5 to 31 m
 * (a rough power law, the way ISO 8608 describes a real surface: long swells are tall, short ones low), a left and a right profile that
 * differ a little (the roll), and an expansion joint every 16 to 40 m (the front wheels hit it, then the rear ones: the thump-thump of a real car).
 *
 * What is published and what is ours. Nothing of this is published: no maker gives its car's ride frequencies. The numbers are textbook ones for a
 * saloon or an SUV on steel or air springs (a bounce of about 1.25 Hz, pitch and roll a little higher, a damping ratio about 0.3), and the whole
 * motion is DRAWN LARGER than a real one (`DRAWN`: about twice, after the first, three-and-a-half-times version was called exaggerated), the way the S-curve's wheels and the corner's lean are: at its real
 * size it would be a few millimetres, which no camera beside the car sees. The Drive tab says its pitch and roll are ours.
 *
 * Frames: heave up (m), pitch nose-up positive (rad), roll leaning right positive (rad), as the rig's `Chassis` (ride.ts). The values are the
 * body's motion against its wheels, to be added to the squat and the lean that are already there.
 */

export interface SuspensionCar {
  /** m */
  wheelbase: number;
  /** m, centre to centre of the tyres on one axle */
  track: number;
}

export interface SuspensionTune {
  /** the body's natural frequencies: up and down, nose and tail, side to side (Hz) */
  bounceHz: number;
  pitchHz: number;
  rollHz: number;
  /** damping ratio of all three */
  zeta: number;
}

export interface Motion {
  heave: number;
  pitch: number;
  roll: number;
}

export interface Suspension {
  sample: (t: number) => Motion;
  /** the largest the run draws: heave m, pitch and roll rad */
  peak: Motion;
  /** the root mean square of the heave while the car moves, m (what the figures are tuned against) */
  rms: Motion;
}

/** How much larger the motion is drawn than the model's own (the road is a motorway's; this is how much the picture exaggerates it). */
export const DRAWN = 2.0;
/**
 * The most a corner of the body is shown to move against its wheel, m: down into the arch (the bump stop: a tyre never goes into its arch) and up away from it.
 * Past these the travel is eased (tanh), so that a joint taken at speed on a body that is already low does not go into the tyre.
 */
const COMPRESS_MAX = 0.018;
const EXTEND_MAX = 0.032;
const limit = (c: number) => (c < 0 ? -COMPRESS_MAX * Math.tanh(-c / COMPRESS_MAX) : EXTEND_MAX * Math.tanh(c / EXTEND_MAX));

/** The squat scale of Comfort (drive-setup.ts `SQUAT_BY_MODE`): the tune below is for it, and a stiffer mode has a smaller scale. */
const COMFORT_SQUAT = 1.1;

/**
 * The tune for a mode and a load: `squatScale` is the mode's (Eco 1.15, Comfort 1.1, Sport 0.85, Track 0.75: drive-setup.ts), `massRatio` the car's mass
 * over its reference (a full car is above 1). A firmer mode lifts the frequencies and the damping; a heavier car rides lower on the same springs.
 */
export function tuneOf(squatScale = COMFORT_SQUAT, massRatio = 1): SuspensionTune {
  const stiff = COMFORT_SQUAT / Math.max(0.5, squatScale);
  const load = 1 / Math.sqrt(Math.max(0.6, massRatio));
  return {
    bounceHz: 1.25 * Math.sqrt(stiff) * load,
    pitchHz: 1.55 * Math.sqrt(stiff) * load,
    rollHz: 1.75 * Math.sqrt(stiff) * load,
    zeta: 0.28 * Math.pow(stiff, 0.45),
  };
}

// ----------------------------------------------------------------------------------------------- the road

/** One swell of the road: its wavelength (m) and where it starts for the common profile and for the left-right difference. */
const SWELLS: readonly { lambda: number; common: number; diff: number }[] = [
  { lambda: 31, common: 0.3, diff: 2.1 },
  { lambda: 19, common: 1.7, diff: 0.4 },
  { lambda: 12.5, common: 4.1, diff: 5.0 },
  { lambda: 8.3, common: 2.6, diff: 3.3 },
  { lambda: 5.4, common: 0.9, diff: 1.2 },
  { lambda: 3.6, common: 5.5, diff: 4.4 },
  { lambda: 2.3, common: 3.4, diff: 2.8 },
  { lambda: 1.5, common: 1.1, diff: 5.9 },
];
/** the height of a 10 m swell, m: a good road (the others follow a power law: amplitude grows with the root of the wavelength) */
const SWELL_M = 0.0024;
/** how much of each swell differs between the left and the right wheel track */
const SIDE_SHARE = 0.55;
/** an expansion joint is a bump of this length (m), 6 to 13 mm tall, one in every 16 to 40 m of road */
const JOINT_LEN = 0.45;

const frac = (n: number) => {
  const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

interface Joint {
  x: number;
  h: number;
  skew: number;
}

/** The road's height under a wheel track (`side` -1 left, +1 right) at `x` metres along it; the same road every time. */
export function roadFor(maxS: number): (x: number, side: number) => number {
  const joints: Joint[] = [];
  let at = 11;
  for (let j = 0; at < maxS + 40; j++) {
    joints.push({ x: at, h: 0.006 + 0.007 * frac(j + 1), skew: (frac(j + 7) - 0.5) * 1.2 });
    at += 16 + 24 * frac(j + 3);
  }
  const amp = SWELLS.map((s) => SWELL_M * Math.sqrt(s.lambda / 10));
  return (x, side) => {
    let y = 0;
    for (let k = 0; k < SWELLS.length; k++) {
      const s = SWELLS[k];
      const w = (2 * Math.PI * x) / s.lambda;
      y += amp[k] * (Math.sin(w + s.common) + side * SIDE_SHARE * Math.sin(w * 1.07 + s.diff));
    }
    // the joints are in order along the road: only the ones within a metre of this wheel can be under it
    let lo = 0;
    let hi = joints.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (joints[mid].x < x - 1) lo = mid + 1;
      else hi = mid;
    }
    for (let i = lo; i < joints.length && joints[i].x < x + 1; i++) {
      const j = joints[i];
      const u = (x - j.x - side * j.skew * 0.5) / JOINT_LEN;
      if (u > 0 && u < 1) y += j.h * Math.sin(Math.PI * u) ** 2;
    }
    return y;
  };
}

// ----------------------------------------------------------------------------------------------- the body

const DT = 1 / 600;
const SAVE = 10; // every tenth step is kept: 60 Hz
/** the body is run this long before the clock starts, at the speed it has then, so that a run that begins rolling begins with the body already moving */
const PRE_S = 2.5;

/**
 * Integrate the body over a run. `distance(t)` is how far the car has gone along the road at `t` (the run's scroll, and the exit's metres after it); the
 * road is read at that distance for the front axle (`wheelbase` ahead) and for the rear one, on the left and on the right. Deterministic.
 */
export function simulateSuspension(car: SuspensionCar, distance: (t: number) => number, duration: number, tune: SuspensionTune = tuneOf()): Suspension {
  const L = car.wheelbase;
  const a = L / 2;
  const hw = car.track / 2;
  // the four corners: FL, FR, RL, RR, with where they stand from the body's middle (x forward, z to the right) and which wheel track they ride on
  const cx = [a, a, -a, -a];
  const cz = [-hw, hw, -hw, hw];
  const cs = [-1, 1, -1, 1];
  const off = [L, L, 0, 0];

  const w0 = 2 * Math.PI * tune.bounceHz;
  const kc = (w0 * w0) / 4; // each corner carries a quarter of the body: the body's mass is 1
  const cc = (2 * tune.zeta * w0) / 4;
  // the radii of gyration that give the pitch and the roll their own frequencies
  const rp = (a * tune.bounceHz) / tune.pitchHz;
  const rr = (hw * tune.bounceHz) / tune.rollHz;
  const ip = 1 / (rp * rp);
  const ir = 1 / (rr * rr);

  const total = Math.max(distance(duration), distance(0)) + 2;
  const road = roadFor(Math.max(total, 60));
  // before the clock starts the car goes on at the speed it has at its start
  const s0 = distance(0);
  const v0 = Math.max(0, (distance(0.05) - s0) / 0.05);
  const dist = (t: number) => (t < 0 ? s0 + v0 * t : distance(t));
  const sxz = cx.reduce((sum, x) => sum + x * x, 0);
  const szz = cz.reduce((sum, z) => sum + z * z, 0);

  const wheels = (t: number, out: Float64Array) => {
    const s = dist(t);
    for (let k = 0; k < 4; k++) out[k] = road(s + off[k], cs[k]);
  };

  const t0 = -PRE_S;
  const n = Math.ceil((duration - t0) / DT);
  const frames = Math.floor((duration - t0) / (DT * SAVE)) + 2;
  const H = new Float32Array(frames);
  const P = new Float32Array(frames);
  const R = new Float32Array(frames);

  let w = new Float64Array(4);
  let w1 = new Float64Array(4);
  wheels(t0, w);
  // the body starts level on its wheels
  let z = (w[0] + w[1] + w[2] + w[3]) / 4;
  let th = 0;
  let ph = 0;
  for (let k = 0; k < 4; k++) {
    th += (cx[k] * w[k]) / sxz;
    ph -= (cz[k] * w[k]) / szz;
  }
  let zd = 0;
  let thd = 0;
  let phd = 0;
  const d = new Float64Array(4);
  let saved = 0;
  let peakH = 0;
  let peakP = 0;
  let peakR = 0;
  let sumH = 0;
  let sumP = 0;
  let sumR = 0;
  let count = 0;
  for (let i = 0; i <= n; i++) {
    const t = t0 + i * DT;
    wheels(t + DT, w1);
    let fz = 0;
    let ft = 0;
    let fp = 0;
    for (let k = 0; k < 4; k++) {
      d[k] = z + cx[k] * th - cz[k] * ph - w[k];
      const dd = zd + cx[k] * thd - cz[k] * phd - (w1[k] - w[k]) / DT;
      const f = -kc * d[k] - cc * dd;
      fz += f;
      ft += cx[k] * f;
      fp -= cz[k] * f;
    }
    zd += fz * DT;
    thd += ft * ip * DT;
    phd += fp * ir * DT;
    z += zd * DT;
    th += thd * DT;
    ph += phd * DT;
    // what is drawn: the lift, pitch and roll of the plane that fits the four corners' travel against their wheels (the twist of the body between the
    // axles is not drawn), larger than the model's own, and held between the bump stops: the plane is scaled down, all three together, until no corner
    // of it is past them
    if (i % SAVE === 0 && saved < frames) {
      let hh = 0;
      let pp = 0;
      let rrr = 0;
      for (let k = 0; k < 4; k++) {
        hh += (d[k] * DRAWN) / 4;
        pp += (cx[k] * d[k] * DRAWN) / sxz;
        rrr -= (cz[k] * d[k] * DRAWN) / szz;
      }
      let low = 0;
      let high = 0;
      for (let k = 0; k < 4; k++) {
        const c = hh + cx[k] * pp - cz[k] * rrr;
        low = Math.min(low, c);
        high = Math.max(high, c);
      }
      const scale = Math.min(low < 0 ? limit(low) / low : 1, high > 0 ? limit(high) / high : 1);
      hh *= scale;
      pp *= scale;
      rrr *= scale;
      H[saved] = hh;
      P[saved] = pp;
      R[saved] = rrr;
      saved++;
      if (t >= 0) {
        peakH = Math.max(peakH, Math.abs(hh));
        peakP = Math.max(peakP, Math.abs(pp));
        peakR = Math.max(peakR, Math.abs(rrr));
        sumH += hh * hh;
        sumP += pp * pp;
        sumR += rrr * rrr;
        count++;
      }
    }
    [w, w1] = [w1, w];
  }
  const dt = DT * SAVE;
  const first = Math.round(PRE_S / dt);
  const at = (arr: Float32Array, t: number) => {
    const u = Math.min(Math.max(t / dt + first, 0), saved - 1);
    const i = Math.floor(u);
    const j = Math.min(i + 1, saved - 1);
    return arr[i] + (arr[j] - arr[i]) * (u - i);
  };
  const mean = (sum: number) => Math.sqrt(sum / Math.max(1, count));
  return {
    sample: (t) => ({ heave: at(H, t), pitch: at(P, t), roll: at(R, t) }),
    peak: { heave: peakH, pitch: peakP, roll: peakR },
    rms: { heave: mean(sumH), pitch: mean(sumP), roll: mean(sumR) },
  };
}
