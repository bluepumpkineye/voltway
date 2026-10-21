import type { Layout, PlannedRun, Sample } from './kinematics';
import type { RoadStage } from './carpet';
import type { Chassis } from './ride';

/**
 * The engine behind Autonomous Drive's scenes (docs/tech-showcase.md section 12): the car stays on the spot and the road rolls
 * under it; the other road users move as each scene scripts them (a car holds a speed and a lane, brakes, cuts in; a person
 * walks across; a box lies in the road), and the car drives itself among them: it holds a set speed, follows what is ahead,
 * stops where a scene tells it to stop, and changes lane when a scene tells it to. What the car decides, and when, is the
 * scene's (src/lib/tech/scenes): each step a scene is given the world and answers with a `Command`.
 *
 * The scenarios are ours, said on each car's panel: no maker publishes a scenario, its speeds or its timing. Run it under Node
 * with the scratchpad's loader (the scenes are plain TypeScript): there are no value imports of anything that needs a browser.
 */

const G = 9.81;
/** nose dip per g of braking, rad (about 1.1 degrees; ours) */
const DIP_PER_G = (1.1 * Math.PI) / 180;
const PITCH_OMEGA = 2 * Math.PI * 1.6;
const PITCH_ZETA = 0.38;
/** the hardest the car brakes, m/s^2 (an emergency stop on dry asphalt) */
const BRAKE_MAX = 8;
/** how hard a following car may brake without being in an emergency, m/s^2 */
const BRAKE_FOLLOW = 3.4;

export const clamp = (x: number, a: number, b: number) => Math.min(b, Math.max(a, x));

export type ActorKind = 'car' | 'person' | 'box';

/** What the sensors make of one actor: out of reach, in reach, the one being followed, or a hazard (in the way, or about to be). */
export type Track = 'out' | 'tracked' | 'lead' | 'warn';

/** One road user as a scene scripts it. */
export interface ActorDef {
  id: string;
  kind: ActorKind;
  /** a car's stand-in model (a vehicle slug); empty for anything else */
  slug: string;
  length: number;
  width: number;
  /** where its middle is at the start, m ahead of the car's middle (negative: behind) */
  gap: number;
  /** its speed along the road at time t, m/s (negative: it comes toward the car); a person or a box stands still along the road */
  speed: (t: number) => number;
  /** the middle's place across the road at time t, m, left of the road's middle */
  y: (t: number) => number;
  /** 1 drives the way the car does, -1 comes toward it (drawn turned round) */
  facing?: 1 | -1;
  /** the sensors have it within this reach ahead, m, instead of the scene's (a lidar sees a small box far off) */
  reach?: number;
  /** the sensors cannot see it until this time, s (someone behind a parked car): it is drawn, but not marked as tracked */
  unseenUntil?: number;
}

/** An actor at one moment, as a scene's decisions see it. */
export interface ActorNow {
  j: number;
  def: ActorDef;
  x: number;
  y: number;
  /** along the road and across it, m/s */
  vx: number;
  vy: number;
}

export interface World {
  t: number;
  /** the car's middle along the road, its nose, its speed, and its place across the road */
  x: number;
  nose: number;
  v: number;
  e: number;
  egoLen: number;
  egoWid: number;
  actors: ActorNow[];
  /** the nearest thing in the car's path ahead: its index, the gap from nose to its tail, its speed along the road */
  lead: { j: number; gap: number; v: number } | null;
}

/** What a scene tells the car to do, from now until it says otherwise. */
export interface Command {
  /** the set speed, m/s, and how hard the car may accelerate to it */
  vSet: number;
  aMax?: number;
  /** stop with the nose here (a line, a crossing someone is on); null: no such place */
  stopAt?: number | null;
  /** change lane now: the place across the road to move to, and how long it takes, s */
  changeTo?: { y: number; dur: number };
  /** the readout: a short word for the state, what the car is doing in the panel's words, a second line */
  state: string;
  message: string;
  note?: string | null;
  /** the indicator: +1 left, -1 right */
  indicator?: -1 | 0 | 1;
  /** the lane the car means to move into, and whether it is clear (drawn on the road) */
  lane?: { y: number; clear: boolean } | null;
  /** the car ahead is the one being followed (a line is drawn to it and the gap is read out) */
  showLead?: boolean;
  /** the actors that are a hazard now (drawn in amber) */
  warn?: string[];
}

export interface SceneDef {
  id: string;
  duration: number;
  /** the car's speed at the start, m/s */
  v0: number;
  actors: ActorDef[];
  road: RoadStage;
  /** how far the sensors reach for the cars drawn round it: ahead and behind, m */
  reach: { ahead: number; behind: number };
  /**
   * the car's distance to what it follows: d0 standing, T seconds of speed on top of it; `stopGap` is how far short it stops of
   * something that is not moving (a stopped car, a person, a box), where the following controller alone would overshoot
   */
  follow: { d0: number; T: number; stopGap?: number };
  /** how fast the pedal comes back up, m/s^3 (default 2.4: a car easing off) */
  jerkUp?: number;
  /** is this actor in the car's way (default: it overlaps the car's path across the road by a margin) */
  inPath?: (a: ActorNow, w: Omit<World, 'lead'>) => boolean;
  initial: Command;
  decide: (w: World) => Command;
  frame: { cx: number; cz: number; radius: number; camera: { az: number; el: number } };
}

/** What a scene is built from: the stand-ins for the other cars, in turn, and the measurements of the car. */
export interface SceneContext {
  cars: { slug: string; length: number; width: number }[];
  egoLen: number;
  egoWid: number;
  /** the car's middle, from its rear axle, m */
  mid: number;
  start: { x: number; y: number; yaw: number };
}

export type SceneFactory = (ctx: SceneContext) => SceneDef;

export interface SensorsReadout {
  state: string;
  message: string;
  /** km/h */
  speed: number;
  /** the distance from the car's nose to the tail of the car it is following, m; null while nothing is followed */
  gap: number | null;
  /** +1 left, -1 right */
  indicator: -1 | 0 | 1;
  lane: { y: number; clear: boolean } | null;
  /** how many road users the sensors have within their drawn reach */
  tracked: number;
  braking: boolean;
  note: string | null;
}

export interface Actor {
  id: string;
  kind: ActorKind;
  slug: string;
  length: number;
  width: number;
  /** the middle in the road's frame (x: run distance, the rear axle's start is 0), y: left of the road's middle, m */
  x: (t: number) => number;
  y: (t: number) => number;
  /** the way it faces, rad (0 along the road, counter-clockwise from above) */
  yaw: (t: number) => number;
  /** its brake lamps are lit */
  braking: (t: number) => boolean;
  /** how fast it goes across the ground, m/s (a person's stride) */
  pace: (t: number) => number;
  track: (t: number) => Track;
}

export interface SensorsRun {
  track: PlannedRun;
  road: RoadStage;
  scroll: (t: number) => number;
  chassis: (t: number) => Chassis;
  scenario: {
    id: string;
    traffic: Actor[];
    /** the car's middle in the road's frame, its heading, and its length */
    ego: (t: number) => { x: number; y: number; yaw: number };
    egoLength: number;
    readout: (t: number) => SensorsReadout;
  };
  frame: SceneDef['frame'];
}

export function simulate(build: SceneFactory, ctx: SceneContext, layout: Layout): SensorsRun {
  const def = build(ctx);
  const { egoLen, egoWid, mid, start } = ctx;
  const STEP = 1 / 120;
  const SAVE = 2;
  const n = Math.ceil(def.duration / STEP) + 1;
  const kept = Math.floor(n / SAVE) + 2;
  const radius = [layout.radius.FL, layout.radius.FR, layout.radius.RL, layout.radius.RR];

  const actors = def.actors.map((d) => ({
    def: d,
    x: mid + d.gap,
    X: new Float32Array(kept),
    V: new Float32Array(kept),
    WARN: new Uint8Array(kept),
  }));
  const ids = new Map(actors.map((a, j) => [a.def.id, j]));

  // what the car does, one array per quantity, saved at 60 Hz
  const V = new Float32Array(kept);
  const S = new Float32Array(kept);
  const A = new Float32Array(kept);
  const P = new Float32Array(kept);
  const E = new Float32Array(kept);
  const YAW = new Float32Array(kept);
  const STR = new Float32Array(kept);
  const LEAD = new Int8Array(kept);
  const SHOW = new Uint8Array(kept);
  const IND = new Int8Array(kept);
  const LANE_Y = new Float32Array(kept);
  const LANE_C = new Int8Array(kept);
  const STATE = new Uint8Array(kept);
  const MSG = new Uint8Array(kept);
  const NOTE = new Uint8Array(kept);
  const W = [0, 1, 2, 3].map(() => new Float32Array(kept));
  const strings: string[] = [''];
  const word = (s: string | null | undefined) => {
    if (!s) return 0;
    let i = strings.indexOf(s);
    if (i < 0) i = strings.push(s) - 1;
    return i;
  };

  let v = def.v0;
  let s = 0;
  let a = 0;
  let pitch = 0;
  let pitchRate = 0;
  const spin = [0, 0, 0, 0];
  let lc: { t0: number; e0: number; e1: number; dur: number } | null = null;
  let cmd = def.initial;
  let k = 0;

  for (let i = 0; i < n; i++) {
    const t = i * STEP;
    const xe = s + mid;
    const nose = xe + egoLen / 2;
    // the lateral offset of the car (left positive) and its rate: a raised cosine over a lane change
    const e: number = lc ? lc.e0 + (lc.e1 - lc.e0) * (1 - Math.cos(Math.PI * clamp((t - lc.t0) / lc.dur, 0, 1))) / 2 : 0;
    let de = 0;
    if (lc) {
      const u = clamp((t - lc.t0) / lc.dur, 0, 1);
      de = u > 0 && u < 1 ? ((lc.e1 - lc.e0) * Math.PI * Math.sin(Math.PI * u)) / (2 * lc.dur) : 0;
    }

    const now: ActorNow[] = actors.map((c, j) => ({
      j,
      def: c.def,
      x: c.x,
      y: c.def.y(t),
      vx: c.def.speed(t),
      vy: (c.def.y(t + 0.02) - c.def.y(t - 0.02)) / 0.04,
    }));
    const w0 = { t, x: xe, nose, v, e, egoLen, egoWid, actors: now };

    // the car ahead: the nearest one in the car's path
    const inPath =
      def.inPath ?? ((c: ActorNow) => Math.abs(c.y - e) <= (c.def.width + egoWid) / 2 + 0.3);
    let lead = -1;
    let leadGap = Infinity;
    for (const c of now) {
      if (!inPath(c, w0)) continue;
      const g = c.x - xe - (c.def.length + egoLen) / 2;
      if (g > -1 && g < leadGap) {
        leadGap = g;
        lead = c.j;
      }
    }
    const vLead = lead >= 0 ? now[lead].vx : 0;

    // the longitudinal control: hold the set speed, follow the car ahead, stop where told to
    const aMax = cmd.aMax ?? 1.2;
    let aCmd = clamp(0.5 * (cmd.vSet - v), -2, aMax);
    // a thing that is not moving, where the scene says how far short to stop of it, is stopped for below, not followed
    const standing = lead >= 0 && vLead < 0.5 && def.follow.stopGap !== undefined;
    if (lead >= 0 && leadGap < 140 && !standing) {
      const want = def.follow.d0 + def.follow.T * v;
      let aLead = clamp(0.45 * (vLead - v) + 0.1 * (leadGap - want), -BRAKE_FOLLOW, aMax);
      // what braking would just stop it short, and if that is more than a following car brakes, the car brakes that hard
      const closing = v - vLead;
      if (closing > 0) {
        const areq = (closing * closing) / (2 * Math.max(leadGap - 2, 0.15));
        if (areq > 2.6) aLead = Math.min(aLead, -Math.min(areq * 1.1, BRAKE_MAX));
      }
      aCmd = Math.min(aCmd, aLead);
    }
    // stopping at a place: a line, a crossing someone is on, or (where the scene says how far short) a thing that is not moving
    const stopFor = (dist: number) => {
      const areq = (v * v) / (2 * Math.max(dist, 0.05));
      if (dist <= 0) aCmd = Math.min(aCmd, -v / 0.4);
      else if (areq > 1.6) aCmd = Math.min(aCmd, -Math.min(areq * 1.08, BRAKE_MAX));
      else if (dist < 1.5 && v < 1.2) aCmd = Math.min(aCmd, -Math.max(v / 0.5, 0.5));
    };
    if (cmd.stopAt != null) stopFor(cmd.stopAt - nose - 0.3);
    if (standing && leadGap < 140) stopFor(leadGap - (def.follow.stopGap as number));
    // a jerk limit: the pedal is not slammed, except in an emergency
    const down = aCmd < -4 ? 25 : 2.6;
    a += clamp(aCmd - a, -down * STEP, (def.jerkUp ?? 2.4) * STEP);
    if (v <= 0.001 && a < 0) a = 0;

    // the decisions (they take effect on the next step)
    const world: World = { ...w0, lead: lead >= 0 ? { j: lead, gap: leadGap, v: vLead } : null };
    const next = def.decide(world);
    if (next.changeTo) lc = { t0: t, e0: e, e1: next.changeTo.y, dur: next.changeTo.dur };
    cmd = next;

    if (i % SAVE === 0) {
      V[k] = v;
      S[k] = s;
      A[k] = a;
      P[k] = pitch;
      E[k] = e;
      YAW[k] = Math.atan2(de, Math.max(v, 1));
      // the front wheels' angle for the path's curvature (bicycle model); the rear wheels stay straight
      const u = lc ? clamp((t - lc.t0) / lc.dur, 0, 1) : 0;
      const kappa = lc && u > 0 && u < 1 ? ((lc.e1 - lc.e0) * Math.PI ** 2 * Math.cos(Math.PI * u)) / (2 * lc.dur ** 2 * Math.max(v, 1) ** 2) : 0;
      STR[k] = Math.atan(layout.wheelbase * kappa);
      LEAD[k] = lead;
      SHOW[k] = cmd.showLead === false ? 0 : 1;
      IND[k] = cmd.indicator ?? 0;
      LANE_Y[k] = cmd.lane?.y ?? 0;
      LANE_C[k] = cmd.lane ? (cmd.lane.clear ? 1 : 0) : -1;
      STATE[k] = word(cmd.state);
      MSG[k] = word(cmd.message);
      NOTE[k] = word(cmd.note);
      for (let j = 0; j < 4; j++) W[j][k] = spin[j];
      actors.forEach((c) => {
        c.X[k] = c.x;
        c.V[k] = c.def.speed(t);
      });
      for (const id of cmd.warn ?? []) {
        const j = ids.get(id);
        if (j !== undefined) actors[j].WARN[k] = 1;
      }
      k++;
    }

    for (let j = 0; j < 4; j++) spin[j] += (v / radius[j]) * STEP;
    v = Math.max(0, v + a * STEP);
    s += v * STEP;
    for (const c of actors) c.x += c.def.speed(t) * STEP;
    // the body dips under braking on its springs and rocks back as the car eases off
    const target = (a / G) * DIP_PER_G;
    pitchRate += (-2 * PITCH_ZETA * PITCH_OMEGA * pitchRate - PITCH_OMEGA * PITCH_OMEGA * (pitch - target)) * STEP;
    pitch += pitchRate * STEP;
  }
  const hold = (arr: Float32Array | Int8Array | Uint8Array) => arr.fill(arr[k - 1], k);
  for (const arr of [V, S, A, P, E, YAW, STR, LANE_Y, ...W, ...actors.flatMap((c) => [c.X, c.V])]) hold(arr);
  for (const arr of [LEAD, SHOW, IND, LANE_C, STATE, MSG, NOTE, ...actors.map((c) => c.WARN)]) hold(arr);

  const dt = STEP * SAVE;
  const at = (arr: Float32Array, t: number) => {
    const f = clamp(Math.max(t, 0) / dt, 0, kept - 2);
    const i = Math.floor(f);
    return arr[i] + (arr[i + 1] - arr[i]) * (f - i);
  };
  const idx = (t: number) => clamp(Math.round(Math.max(t, 0) / dt), 0, kept - 1);
  const length = at(S, def.duration);
  const egoX = (t: number) => at(S, t) + mid;
  const egoY = (t: number) => at(E, t);

  const trackOf = (j: number, t: number): Track => {
    const c = actors[j];
    const k0 = idx(t);
    const d = at(c.X, t) - egoX(t);
    if (t < (c.def.unseenUntil ?? 0)) return 'out';
    if (d > (c.def.reach ?? def.reach.ahead) || d < -def.reach.behind) return 'out';
    if (LEAD[k0] === j && SHOW[k0]) return 'lead';
    if (c.WARN[k0]) return 'warn';
    return 'tracked';
  };

  const traffic: Actor[] = actors.map((c, j) => {
    const facing = c.def.facing === -1 ? Math.PI : 0;
    const accel = (t: number) => (at(c.V, t + 0.25) - at(c.V, t - 0.25)) / 0.5;
    const vy = (t: number) => (c.def.y(t + 0.05) - c.def.y(t - 0.05)) / 0.1;
    return {
      id: c.def.id,
      kind: c.def.kind,
      slug: c.def.slug,
      length: c.def.length,
      width: c.def.width,
      x: (t) => at(c.X, t),
      y: (t) => c.def.y(t),
      yaw: (t) => {
        const vx = at(c.V, t);
        // a person faces the way they walk; a car's heading follows its path (across the lane when it changes lane)
        if (c.def.kind === 'person') return Math.abs(vy(t)) > 0.05 ? Math.atan2(vy(t), 0.001 + vx) : 0;
        return Math.abs(vx) > 1 ? Math.atan2(vy(t), vx) : facing;
      },
      // the lamps are lit while the car's speed is falling (its magnitude, whichever way it goes)
      braking: (t) => c.def.kind === 'car' && accel(t) * Math.sign(at(c.V, t)) < -0.45 && Math.abs(at(c.V, t)) > 0.3,
      pace: (t) => Math.hypot(at(c.V, t), vy(t)),
      track: (t) => trackOf(j, t),
    };
  });

  const readout = (t: number): SensorsReadout => {
    const k0 = idx(t);
    const lead = LEAD[k0];
    const following = SHOW[k0] === 1 && lead >= 0;
    return {
      state: strings[STATE[k0]],
      message: strings[MSG[k0]],
      speed: at(V, t) * 3.6,
      gap: following ? at(actors[lead].X, t) - egoX(t) - (actors[lead].def.length + egoLen) / 2 : null,
      indicator: IND[k0] as -1 | 0 | 1,
      lane: LANE_C[k0] < 0 ? null : { y: LANE_Y[k0], clear: LANE_C[k0] === 1 },
      tracked: actors.reduce((count, _c, j) => count + (trackOf(j, t) === 'out' ? 0 : 1), 0),
      braking: at(A, t) < -0.9,
      note: NOTE[k0] ? strings[NOTE[k0]] : null,
    };
  };

  const track: PlannedRun = {
    duration: def.duration,
    stats: { maxSteer: 0.05, bounds: { min: { x: start.x, y: start.y }, max: { x: start.x + length, y: start.y + 3.75 } } },
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
    road: def.road,
    scroll: (t) => at(S, t),
    chassis: (t) => ({ heave: 0, pitch: at(P, t), lift: [0, 0, 0, 0] }),
    scenario: { id: def.id, traffic, ego: (t) => ({ x: egoX(t), y: egoY(t), yaw: at(YAW, t) }), egoLength: egoLen, readout },
    frame: def.frame,
  };
}
