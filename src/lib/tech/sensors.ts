import type { Layout, PlannedRun, Sample } from './kinematics';
import type { RoadStage } from './carpet';
import type { Chassis } from './ride';

/**
 * Autonomous Drive (docs/tech-showcase.md section 12), the sensor demo of the Luxeed RX, the Xiaomi SU7 Ultra and the Avatr
 * 06T: the car cruises at 100 km/h in the middle lane of a three-lane road with other cars in every lane, its sensors' coverage
 * is drawn from where each one sits, the car ahead brakes, the car follows it, waits for a car coming up fast in the left lane
 * to go by, changes lane when the lane is clear and overtakes.
 *
 * Published (the makers, Autohome's configuration tables, Huawei, Hesai): how many of each sensor a car has, the 120 by 25.4
 * degree field of view of the SU7's Hesai AT128, that the RX's lidar recognises a 14 cm box at 120 m, that the SU7 Ultra has
 * automatic lane change assist. Ours, said on each car's panel: the whole scenario (the traffic, the speeds, the braking, the
 * decisions and when they come), every cone's angle and the reach it is drawn to (the real sensors see much further), the
 * sweep's speed. The cars are other models' stand-ins in neutral paint. Like the launch the car stays on the spot and the road
 * rolls under it. No value imports: it runs under Node.
 */

/** the lane's width, m (a Chinese expressway's lanes are 3.75 m) */
export const LANE = 3.75;
/** the set speed, m/s (100 km/h) */
export const CRUISE = 100 / 3.6;
/** the set speed while the car is overtaking, m/s (112 km/h) */
const OVERTAKE = 112 / 3.6;
const G = 9.81;
/** nose dip per g of braking, rad (about 1.1 degrees; ours) */
const DIP_PER_G = (1.1 * Math.PI) / 180;
const PITCH_OMEGA = 2 * Math.PI * 1.6;
const PITCH_ZETA = 0.38;

/** the seconds of the run at which each thing is decided (the rest follows from the traffic) */
export const TIMES = {
  /** the car ahead starts to brake, and the car has finished doing so */
  leadBrake: 2.6,
  leadSlow: 6.0,
  /** the car does not think of changing lane before this */
  minDecide: 3.0,
  /** a lane change takes this long */
  lane: 4.0,
  end: 19.0,
} as const;

/** the drawn reach of the sensors (illustrative: the real ones see further), m */
export const REACH = { wide: 26, tele: 62, side: 18, rear: 30, ultrasonic: 2.4, surround: 22, scan: 34 } as const;

export type SensorsState = 'cruising' | 'following' | 'waiting' | 'changing' | 'passing' | 'done';

export interface SensorsReadout {
  state: SensorsState;
  /** km/h */
  speed: number;
  /** the distance from the car's nose to the tail of the car it is following, m; null while nothing is ahead in its lane */
  gap: number | null;
  /** the lane change's indicator: +1 left */
  indicator: 0 | 1;
  /** the left lane is clear to move into (null when the car is not thinking of it) */
  leftClear: boolean | null;
  /** how many of the other cars the sensors have within their drawn reach */
  tracked: number;
  braking: boolean;
}

/** What the sensors make of one car: it is in reach, it is the one being followed, or it is in the way of the lane change. */
export type Track = 'out' | 'tracked' | 'lead' | 'warn';

export interface TrafficCar {
  id: string;
  /** which car's stand-in is drawn (a vehicle slug) */
  slug: string;
  /** which lane it starts in: +1 left, 0 the car's own, -1 right */
  lane: -1 | 0 | 1;
  length: number;
  width: number;
  /** the middle of the car in the road's frame (x: run distance, the rear axle's start is 0), y: left of the road's middle, m */
  x: (t: number) => number;
  y: (t: number) => number;
  /** its brake lamps are lit */
  braking: (t: number) => boolean;
  /** how the sensors see it */
  track: (t: number) => Track;
}

export interface SensorsRun {
  track: PlannedRun;
  road: RoadStage;
  scroll: (t: number) => number;
  chassis: (t: number) => Chassis;
  scenario: {
    traffic: TrafficCar[];
    /** the car's middle in the road's frame (x: run distance, y: left of the road's middle), its heading, and its length */
    ego: (t: number) => { x: number; y: number; yaw: number };
    egoLength: number;
    readout: (t: number) => SensorsReadout;
  };
  frame: { cx: number; cz: number; radius: number; camera: { az: number; el: number } };
}

export interface SensorsOptions {
  /** the size of each car the traffic is drawn with, in the order of ROLES (the other modelled cars' stand-ins) */
  traffic?: { slug: string; length: number; width: number }[];
}

interface Role {
  id: string;
  lane: -1 | 0 | 1;
  /** where its middle is at the start, m ahead of the car's middle */
  gap: number;
  kmh: number;
  /** it brakes to this speed (km/h) between the two times */
  slows?: { to: number; from: number; until: number };
}

/**
 * The traffic, in the order the stand-ins are given: the car ahead (it brakes), one that comes up from behind in the left
 * lane, one that goes by the car's left early on, one that is passed on the right, one that follows on the right, and one far
 * ahead. Where each stands and how fast it goes is ours; the lane change's timing comes out of them.
 */
export const ROLES: Role[] = [
  { id: 'lead', lane: 0, gap: 62, kmh: 100, slows: { to: 74, from: TIMES.leadBrake, until: TIMES.leadSlow } },
  { id: 'fast', lane: 1, gap: -66, kmh: 130 },
  { id: 'early', lane: 1, gap: -22, kmh: 118 },
  { id: 'slow', lane: -1, gap: 30, kmh: 84 },
  { id: 'follow', lane: -1, gap: -30, kmh: 95 },
  { id: 'far', lane: -1, gap: 82, kmh: 90 },
];

const clamp = (x: number, a: number, b: number) => Math.min(b, Math.max(a, x));

/**
 * Is a car in the lane beside in the way of a lane change? `d` is where its middle is from ours (negative: behind), `half` the
 * two cars' half lengths added, `vc` and `ve` its speed and ours. One behind must not close within three seconds, and one
 * ahead must be well clear.
 */
function inTheWay(d: number, half: number, vc: number, ve: number): boolean {
  return d < 0 ? -d - half - Math.max(0, vc - ve) * 3.2 < 9 : d - half < 12 + Math.max(0, ve - vc) * 2.2;
}

export function planSensors(
  layout: Layout,
  body: { rear: number; front: number; halfWidth: number },
  start: { x: number; y: number; yaw: number },
  opts: SensorsOptions = {},
): SensorsRun {
  const tEnd = TIMES.end;
  const STEP = 1 / 120;
  const SAVE = 2;
  const n = Math.ceil(tEnd / STEP) + 1;
  const kept = Math.floor(n / SAVE) + 2;
  const mid = (body.front - body.rear) / 2;
  const egoLen = body.front + body.rear;
  const radius = [layout.radius.FL, layout.radius.FR, layout.radius.RL, layout.radius.RR];

  const cars = ROLES.map((r, i) => {
    const size = opts.traffic?.[i] ?? { slug: '', length: 4.9, width: 1.95 };
    const v0 = r.kmh / 3.6;
    return {
      role: r,
      slug: size.slug,
      length: size.length,
      width: size.width,
      v0,
      // the speed at time t: constant, or a linear ramp down while it brakes
      speed: (t: number) => {
        if (!r.slows) return v0;
        const { from, until, to } = r.slows;
        const v1 = to / 3.6;
        return t <= from ? v0 : t >= until ? v1 : v0 + ((v1 - v0) * (t - from)) / (until - from);
      },
      brakes: (t: number) => !!r.slows && t >= r.slows.from && t < r.slows.until + 0.5,
      x: mid + r.gap,
      X: new Float32Array(kept),
      V: new Float32Array(kept),
    };
  });

  // what the ego car does, one array per quantity, saved at 60 Hz
  const V = new Float32Array(kept);
  const S = new Float32Array(kept);
  const A = new Float32Array(kept);
  const P = new Float32Array(kept);
  const E = new Float32Array(kept);
  const YAW = new Float32Array(kept);
  const STR = new Float32Array(kept);
  const PH = new Uint8Array(kept);
  const LEAD = new Int8Array(kept);
  const CLEAR = new Int8Array(kept);
  const W = [0, 1, 2, 3].map(() => new Float32Array(kept));

  let v = CRUISE;
  let s = 0;
  let a = 0;
  let pitch = 0;
  let pitchRate = 0;
  const spin = [0, 0, 0, 0];
  let phase = 0; // 0 cruising, 1 following, 2 waiting, 3 changing, 4 passing, 5 done
  let t0 = -1; // when the lane change began
  let k = 0;

  /** is the left lane clear to move into now? Cars behind must not close within three seconds, cars ahead must be far enough. */
  const leftClear = (xe: number, ve: number, t: number) =>
    !cars.some((c) => c.role.lane === 1 && inTheWay(c.x - xe, (c.length + egoLen) / 2, c.speed(t), ve));

  for (let i = 0; i < n; i++) {
    const t = i * STEP;
    const xe = s + mid;
    // the lateral offset of the car (left positive) and its rate: a raised cosine over the lane change
    let e = 0;
    let de = 0;
    if (t0 >= 0) {
      const u = clamp((t - t0) / TIMES.lane, 0, 1);
      e = (LANE * (1 - Math.cos(Math.PI * u))) / 2;
      de = u > 0 && u < 1 ? (LANE * Math.PI * Math.sin(Math.PI * u)) / (2 * TIMES.lane) : 0;
    }

    // the car ahead: the nearest one whose lane the car overlaps
    let lead = -1;
    let leadGap = Infinity;
    cars.forEach((c, j) => {
      const yc = c.role.lane * LANE;
      if (Math.abs(yc - e) > 2.3) return;
      const g = c.x - xe - (c.length + egoLen) / 2;
      if (g > -1 && g < leadGap) {
        leadGap = g;
        lead = j;
      }
    });
    const vLead = lead >= 0 ? cars[lead].speed(t) : 0;

    // the longitudinal control: hold the set speed, or follow the car ahead at about one and a half seconds
    const vSet = phase >= 3 ? OVERTAKE : CRUISE;
    const aMax = phase >= 3 ? 1.9 : 1.2;
    let aCmd = clamp(0.5 * (vSet - v), -2, aMax);
    if (lead >= 0 && leadGap < 140) {
      const want = 8 + 1.55 * v;
      const aLead = 0.45 * (vLead - v) + 0.1 * (leadGap - want);
      aCmd = Math.min(aCmd, clamp(aLead, -3.4, aMax));
    }
    // a jerk limit: the pedal is not slammed
    a += clamp(aCmd - a, -2.6 * STEP, 2.4 * STEP);

    // the decisions
    if (phase <= 1) {
      phase = lead >= 0 && leadGap < 70 && vLead < v - 0.4 ? 1 : 0;
      if (t >= TIMES.minDecide && lead >= 0 && vLead < v - 2.5 && leadGap < 52 && cars[lead].role.lane === 0) phase = 2;
    }
    let clear = -1;
    if (phase === 2) {
      const ok = leftClear(xe, v, t);
      clear = ok ? 1 : 0;
      if (ok) {
        phase = 3;
        t0 = t;
      }
    }
    if (phase === 3 && t >= t0 + TIMES.lane) phase = 4;
    if (phase === 4) {
      const L = cars.find((c) => c.role.id === 'lead')!;
      if (xe - L.x > (L.length + egoLen) / 2 + 3) phase = 5;
    }

    if (i % SAVE === 0) {
      V[k] = v;
      S[k] = s;
      A[k] = a;
      P[k] = pitch;
      E[k] = e;
      YAW[k] = Math.atan2(de, Math.max(v, 1));
      // the front wheels' angle for the path's curvature (bicycle model); the rear wheels stay straight
      const u = t0 >= 0 ? clamp((t - t0) / TIMES.lane, 0, 1) : 0;
      const kappa = u > 0 && u < 1 ? (LANE * Math.PI ** 2 * Math.cos(Math.PI * u)) / (2 * TIMES.lane ** 2 * Math.max(v, 1) ** 2) : 0;
      STR[k] = Math.atan(layout.wheelbase * kappa);
      PH[k] = phase;
      LEAD[k] = lead;
      CLEAR[k] = clear;
      for (let j = 0; j < 4; j++) W[j][k] = spin[j];
      cars.forEach((c) => {
        c.X[k] = c.x;
        c.V[k] = c.speed(t);
      });
      k++;
    }

    for (let j = 0; j < 4; j++) spin[j] += (v / radius[j]) * STEP;
    v = Math.max(0, v + a * STEP);
    s += v * STEP;
    for (const c of cars) c.x += c.speed(t) * STEP;
    // the body dips under braking on its springs and rocks back as the car eases off
    const target = (a / G) * DIP_PER_G;
    pitchRate += (-2 * PITCH_ZETA * PITCH_OMEGA * pitchRate - PITCH_OMEGA * PITCH_OMEGA * (pitch - target)) * STEP;
    pitch += pitchRate * STEP;
  }
  const hold = (arr: Float32Array | Int8Array | Uint8Array) => arr.fill(arr[k - 1], k);
  for (const arr of [V, S, A, P, E, YAW, STR, ...W, ...cars.flatMap((c) => [c.X, c.V])]) hold(arr);
  for (const arr of [PH, LEAD, CLEAR]) hold(arr);

  const dt = STEP * SAVE;
  const at = (arr: Float32Array, t: number) => {
    const f = clamp(Math.max(t, 0) / dt, 0, kept - 2);
    const i = Math.floor(f);
    return arr[i] + (arr[i + 1] - arr[i]) * (f - i);
  };
  const idx = (t: number) => clamp(Math.round(Math.max(t, 0) / dt), 0, kept - 1);
  const length = at(S, tEnd);

  const egoX = (t: number) => at(S, t) + mid;
  const egoY = (t: number) => at(E, t);
  const carX = (j: number) => (t: number) => at(cars[j].X, t);

  const STATES: SensorsState[] = ['cruising', 'following', 'waiting', 'changing', 'passing', 'done'];
  const trackOf = (j: number, t: number): Track => {
    const c = cars[j];
    const k0 = idx(t);
    const d = at(c.X, t) - egoX(t);
    if (d > REACH.tele || d < -REACH.rear * 1.2) return 'out';
    if (LEAD[k0] === j && PH[k0] <= 2) return 'lead';
    // the cars in the left lane that the car is waiting for
    if (PH[k0] === 2 && c.role.lane === 1 && inTheWay(d, (c.length + egoLen) / 2, at(c.V, t), V[k0])) return 'warn';
    return 'tracked';
  };

  const traffic: TrafficCar[] = cars.map((c, j) => ({
    id: c.role.id,
    slug: c.slug,
    lane: c.role.lane,
    length: c.length,
    width: c.width,
    x: carX(j),
    y: () => c.role.lane * LANE,
    braking: (t) => c.brakes(t),
    track: (t) => trackOf(j, t),
  }));

  const readout = (t: number): SensorsReadout => {
    const k0 = idx(t);
    const phaseNow = PH[k0];
    const lead = LEAD[k0];
    const following = lead >= 0 && phaseNow <= 2;
    return {
      state: STATES[phaseNow],
      speed: at(V, t) * 3.6,
      gap: following ? at(cars[lead].X, t) - egoX(t) - (cars[lead].length + egoLen) / 2 : null,
      indicator: phaseNow === 2 || phaseNow === 3 ? 1 : 0,
      leftClear: phaseNow === 3 ? true : phaseNow === 2 ? CLEAR[k0] === 1 : null,
      tracked: cars.reduce((count, _c, j) => count + (trackOf(j, t) === 'out' ? 0 : 1), 0),
      braking: at(A, t) < -0.9,
    };
  };

  const track: PlannedRun = {
    duration: tEnd,
    stats: { maxSteer: 0.05, bounds: { min: { x: start.x, y: start.y }, max: { x: start.x + length, y: start.y + LANE } } },
    sample: (t: number): Sample => {
      const st = at(STR, t);
      return {
        x: start.x + at(S, t),
        y: start.y + egoY(t),
        yaw: start.yaw + at(YAW, t),
        steer: [st, st, 0, 0],
        spin: [at(W[0], t), at(W[1], t), at(W[2], t), at(W[3], t)],
        speed: at(V, t),
        segment: 0,
        phase: 'move',
      };
    },
    trace: () => [],
  };

  return {
    track,
    // three lanes and their shoulders, long enough that its ends are out of sight; the markings stream by at the car's speed
    road: { humps: [], from: -140, to: 140, width: LANE * 3 + 3.2, lanes: { count: 3, width: LANE } },
    scroll: (t) => at(S, t),
    chassis: (t) => ({ heave: 0, pitch: at(P, t), lift: [0, 0, 0, 0] }),
    scenario: { traffic, ego: (t) => ({ x: egoX(t), y: egoY(t), yaw: at(YAW, t) }), egoLength: egoLen, readout },
    frame: {
      // the car and the lanes about it: the camera stands behind and above, a little to the left where the overtaking is
      cx: start.x + mid + 8,
      cz: -start.y - LANE * 0.35,
      radius: 16,
      camera: { az: 128, el: 34 },
    },
  };
}
