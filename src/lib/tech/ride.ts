/**
 * The ride of a car over a rough road, for the showroom's Magic Carpet demo
 * (docs/tech-showcase.md, "Magic Carpet"). Pure maths, no three.js and no imports, so it can be run
 * and checked on its own.
 *
 * What is published and what is ours. The maker publishes that the 7X's Magic Carpet package is air
 * suspension, continuously controlled (CCD) electromagnetic dampers and a perception system (front
 * camera and lidar) that reads the road ahead; that it has five ride heights, about 70 mm of travel in
 * all and 230 mm of ground clearance at most. It publishes NO response curve. So the body's motion here
 * is a textbook model with our numbers: a half car (heave and pitch) on a spring and a damper per axle,
 * the wheels following the road. The passive car is that, and nothing else. The Magic Carpet car
 * is the same car with softer air springs, light axle dampers and an actuator that cancels the
 * force the road puts into the body (it "knows" the hump, because the cameras and the lidar saw it)
 * and holds the body still against the sky. The demo says all this on screen.
 *
 * Frames: heave up, pitch nose-up positive, distances along the road in metres from where the car's
 * rear axle starts.
 */

export type RideLevelId = 'very-low' | 'low' | 'standard' | 'high' | 'very-high';

export interface RideLevel {
  id: RideLevelId;
  /** the name on the car's own screen, in English */
  label: string;
  /** body height against Standard, mm: five equal steps over the maker's ~70 mm (the steps are ours) */
  mm: number;
}

/** Published: five levels with these names (the 7X's Quick settings) and about 70 mm in all. Ours: equal steps. */
export const RIDE_SPAN_MM = 70;
const NAMES: [RideLevelId, string][] = [
  ['very-low', 'Very low'],
  ['low', 'Low'],
  ['standard', 'Standard'],
  ['high', 'High'],
  ['very-high', 'Very high'],
];
/** Lowest first. */
export const RIDE_LEVELS: readonly RideLevel[] = NAMES.map(([id, label], i) => ({
  id,
  label,
  mm: (i - 2) * (RIDE_SPAN_MM / 4),
}));
export const STANDARD_LEVEL = 2;

// ---------------------------------------------------------------------------- the road

/** A rubber speed hump across the whole lane: where its middle is, how high and how long (base to base). */
export interface Hump {
  x: number;
  height: number;
  length: number;
}

/** The height of one hump at x: rounded shoulders on a short flat top. */
export function humpAt(h: Hump, x: number): number {
  const half = h.length / 2;
  const d = Math.abs(x - h.x);
  if (d >= half) return 0;
  const u = Math.min(1, (half - d) / (half * 0.8));
  return h.height * u * u * (3 - 2 * u);
}

export function roadAt(humps: readonly Hump[], x: number): number {
  let y = 0;
  for (const h of humps) if (Math.abs(x - h.x) < h.length / 2) y = Math.max(y, humpAt(h, x));
  return y;
}

/**
 * How far a wheel's hub is lifted when it stands at x: the tyre is a circle, so it rides up the shoulder
 * of a hump before its centre reaches it, and does not follow the hump's sharp corners.
 */
export function hubLift(humps: readonly Hump[], x: number, radius: number, step = 0.01): number {
  let lift = 0;
  for (const h of humps) {
    const reach = h.length / 2 + radius;
    if (Math.abs(x - h.x) > reach) continue;
    for (let s = x - radius; s <= x + radius + 1e-9; s += step) {
      const y = humpAt(h, s);
      if (y <= 0) continue;
      const u = y - radius + Math.sqrt(Math.max(0, radius * radius - (s - x) * (s - x)));
      if (u > lift) lift = u;
    }
  }
  return lift;
}

// ---------------------------------------------------------------------------- the car

/** What the ride needs of a car: from the rig's measured wheels. */
export interface RideCar {
  wheelbase: number;
  /** tyre rolling radius, front and rear, m */
  radiusF: number;
  radiusR: number;
}

/** Our numbers for a 2-tonne SUV (the 7X's kerb weight is about that); not the maker's. */
const BODY = { mass: 2000, gyration: 1.05, bounceHz: 1.25, bounceZeta: 0.22 };

export interface RideSetup {
  /** the Magic Carpet's control on (the car reads the road ahead) or a passive car */
  active: boolean;
  /** the drive mode's stiffness against Comfort (Sport 1.25 ...): ours, a visible difference */
  stiffness?: number;
}

export interface Chassis {
  /** the body's lift at its middle, m (the ride height is added by the viewer) */
  heave: number;
  /** nose-up positive, rad */
  pitch: number;
  /** each hub's lift over the road's level, m: FL, FR, RL, RR */
  lift: [number, number, number, number];
}

/** The two suspensions the demo compares: the Magic Carpet, and a plain passive one. */
export type RideMode = 'carpet' | 'passive';

export interface RideRun {
  duration: number;
  sample: (t: number) => Chassis;
  /** the largest motions of the run: body lift m, pitch rad, the largest hub lift m */
  peak: { heave: number; pitch: number; lift: number };
}

const DT = 1 / 600;
const SAVE = 10; // every tenth step is kept: 60 Hz

/**
 * Integrate the half car over a run. `xRear(t)` is how far the rear axle has travelled at t (the
 * track's own profile), `humps` the road in the same distances. Deterministic: scrubbing the clock
 * back and forth shows the same ride.
 */
export function simulateRide(
  car: RideCar,
  humps: readonly Hump[],
  xRear: (t: number) => number,
  duration: number,
  setup: RideSetup,
): RideRun {
  const stiff = setup.stiffness ?? 1;
  const L = car.wheelbase;
  const a = L / 2; // the centre of mass is mid-wheelbase, where the rig pitches the body from
  const b = L / 2;
  const M = BODY.mass;
  const I = M * BODY.gyration * BODY.gyration;
  const w0 = 2 * Math.PI * BODY.bounceHz;
  // passive springs and dampers per axle; the carpet's air springs are softer and its axle dampers light
  const kAxle = (0.5 * M * w0 * w0 * stiff) * (setup.active ? 0.72 : 1);
  const cAxle = (0.5 * 2 * BODY.bounceZeta * Math.sqrt(2 * kAxle * M)) * (setup.active ? 0.5 : 1);
  const cSkyHeave = setup.active ? 2 * 0.6 * Math.sqrt(2 * kAxle * M) : 0;
  const cSkyPitch = setup.active ? 2 * 0.6 * Math.sqrt(2 * kAxle * 0.5 * (a * a + b * b) * I) : 0;
  const ffGain = setup.active ? 0.62 : 0;
  // one axle's actuator can only push so hard: a big hump is not entirely ironed out
  const fMax = 4000;

  const wheel = (t: number) => {
    const xr = xRear(t);
    return {
      f: hubLift(humps, xr + L, car.radiusF),
      r: hubLift(humps, xr, car.radiusR),
    };
  };

  const n = Math.ceil(duration / DT);
  const saved = Math.floor(n / SAVE) + 2;
  const hz = new Float32Array(saved);
  const hp = new Float32Array(saved);
  const hf = new Float32Array(saved);
  const hr = new Float32Array(saved);

  let z = 0;
  let zd = 0;
  let th = 0;
  let thd = 0;
  let w = wheel(0);
  let peakZ = 0;
  let peakTh = 0;
  let peakLift = 0;
  let k = 0;
  for (let i = 0; i <= n; i++) {
    const t = i * DT;
    const w1 = wheel(t + DT);
    const wfd = (w1.f - w.f) / DT;
    const wrd = (w1.r - w.r) / DT;
    const df = z + a * th - w.f;
    const dfd = zd + a * thd - wfd;
    const dr = z - b * th - w.r;
    const drd = zd - b * thd - wrd;
    let Ff = -kAxle * df - cAxle * dfd;
    let Fr = -kAxle * dr - cAxle * drd;
    if (setup.active) {
      // cancel what the road puts in through the spring and the damper (the part that does not
      // depend on the body) ...
      const cf = ffGain * (kAxle * w.f + cAxle * wfd);
      const cr = ffGain * (kAxle * w.r + cAxle * wrd);
      // ... and hold the body still against the sky
      const sf = -(cSkyHeave * 0.5) * (zd + a * thd);
      const sr = -(cSkyHeave * 0.5) * (zd - b * thd);
      const clamp = (v: number) => Math.max(-fMax, Math.min(fMax, v));
      Ff += clamp(-cf + sf);
      Fr += clamp(-cr + sr);
      // extra pitch damping from the same actuators
      Ff += (-cSkyPitch * thd) / (2 * a);
      Fr += (cSkyPitch * thd) / (2 * b);
    }
    const zdd = (Ff + Fr) / M;
    const thdd = (a * Ff - b * Fr) / I;
    zd += zdd * DT;
    thd += thdd * DT;
    z += zd * DT;
    th += thd * DT;
    w = w1;
    peakZ = Math.max(peakZ, Math.abs(z));
    peakTh = Math.max(peakTh, Math.abs(th));
    peakLift = Math.max(peakLift, w.f, w.r);
    if (i % SAVE === 0 && k < saved) {
      hz[k] = z;
      hp[k] = th;
      hf[k] = w.f;
      hr[k] = w.r;
      k++;
    }
  }
  const frames = k;
  const dt = DT * SAVE;
  const at = (arr: Float32Array, t: number) => {
    const u = Math.min(Math.max(t / dt, 0), frames - 1);
    const i = Math.floor(u);
    const j = Math.min(i + 1, frames - 1);
    return arr[i] + (arr[j] - arr[i]) * (u - i);
  };
  return {
    duration,
    sample: (t) => {
      const f = at(hf, t);
      const r = at(hr, t);
      return { heave: at(hz, t), pitch: at(hp, t), lift: [f, f, r, r] };
    },
    peak: { heave: peakZ, pitch: peakTh, lift: peakLift },
  };
}
