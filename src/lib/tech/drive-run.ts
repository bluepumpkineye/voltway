import type { Layout, PlannedRun, Sample } from './kinematics';
import type { RoadStage } from './carpet';
import type { Chassis } from './ride';
import type { LaunchMark, LaunchReadout } from './launch';

/**
 * The Drive tab's run (docs/tech-showcase.md section 19): a car's own scenario, not one sequence for every model. A
 * pull from a standstill (or a rolling pull), then what the car's scenario goes on with: a hold, a cruise, a hard stop,
 * an S-curve under power (torque vectoring), a rear-steered slalom, a crab walk.
 *
 * Published (the vehicle's data): the 0-100 km/h time, the 0-200 where the maker has one, the peak power and torque, the
 * 100-0 distance where one is quoted, the rear wheels' largest angle. Ours, said on screen: the shape of the pull
 * (launch.ts says how), the mode's and the load's effect on it, the body's pitch and roll, how the drive is shared
 * between the motors, the brake blend, the energy, the paths of the manoeuvres.
 *
 * Like the Magic Carpet's run the car stays on the spot and the road rolls under it (`RigState.scroll`); a manoeuvre
 * moves it sideways and turns it (`treadmill.lateral`). No imports of values: it runs under plain Node.
 */

const G = 9.81;
const RHO = 1.2;
/** rolling resistance coefficient, ours */
const CRR = 0.011;
/** the car stands on the line before it goes, s */
export const HOLD = 0.6;
const BUILD = 0.15;
const EASE = 0.5;
const COAST = 5.9;
/** a pull to 200 km/h goes on a little past it before the car eases off (launch.ts), s */
const CARRY = 1.2;
export const V100 = 100 / 3.6;
const STEP = 1 / 480;
const SAVE = 8;
const SPIN_SHOWN = 20;
const DEG = Math.PI / 180;

const clamp = (x: number, a: number, b: number) => Math.min(b, Math.max(a, x));
const smooth = (x: number) => {
  const t = clamp(x, 0, 1);
  return t * t * (3 - 2 * t);
};

/** what a wet road holds: the friction coefficient of wet asphalt, ours (dry is what the maker's own run was made on) */
const WET_MU = 0.72;

/**
 * What the road does to the pull and the stop: a wet road caps the acceleration at what the tyres hold (all four wheels on an
 * all-wheel-drive car, about three fifths of the weight on a rear-driven one), and a hill takes g times its slope off the pull
 * (and adds it to the stop uphill). Ours: the maker's run is dry and level.
 */
export function roadEnv(wet: boolean, awd: boolean, gradePct: number) {
  return {
    cap: wet ? WET_MU * G * (awd ? 1 : 0.62) : Infinity,
    gradeA: G * Math.sin(Math.atan(gradePct / 100)),
    wet,
  };
}

/** Tyre slip by speed: a launch holds the tyres a little past their grip, and the slip fades as the car gets going. */
const slipAt = (v: number) => 0.16 * Math.exp(-v / 15);

export type DrivePhase =
  | 'hold'
  | 'pull'
  | 'ease'
  | 'coast'
  | 'cruise'
  | 'lift'
  | 'brake'
  | 'stop'
  | 'decel'
  | 'sweep'
  | 'slalom'
  | 'crab';

const PHASES: DrivePhase[] = ['hold', 'pull', 'ease', 'coast', 'cruise', 'lift', 'brake', 'stop', 'decel', 'sweep', 'slalom', 'crab'];

export type DriveCueName = 'launch' | 'pull' | 'target' | 'cruise' | 'brake' | 'stop' | 'sweep' | 'slalom' | 'crab';

/** One motor as the run draws it: where it is and its share of the drive when the car pulls straight. */
export interface DriveMotor {
  id: string;
  label: string;
  axle: 'front' | 'rear';
  side?: 'left' | 'right';
  share: number;
}

export interface DriveEvent {
  cue: DriveCueName;
  t: number;
  label: string;
}

export interface DriveRunInfo {
  id: string;
  label: string;
  from: number;
  to: number;
  /** the time the pull takes in the chosen mode and load, s */
  time: number;
  /** the maker's figure, when this is its run at full power with the driver alone */
  published: boolean;
}

export interface DriveInput {
  /** the maker's times at full power with the driver alone, s */
  zeroTo100: number;
  zeroTo200?: number;
  /** peak output of the variant, kW and Nm */
  peakKw: number;
  peakNm?: number;
  /** the run, km/h */
  from: number;
  to: number;
  /** the share of the peak the chosen mode lets through (0 to 1) */
  powerFrac: number;
  /** the mode's damping: how much of the generic squat the body shows (Sport firmer, Comfort softer) */
  squatScale: number;
  /** the mass the run is for (kerb weight and the load) and the mass the maker's times belong to, kg */
  massKg: number;
  refMassKg: number;
  /** the times are the maker's: full power, the driver alone */
  nominal: boolean;
  /** the 0-200 time is the maker's own and not our estimate from the 0-100 */
  zeroTo200Published?: boolean;
  /** kWh per 100 km for the range the energy is turned into */
  kwhPer100?: number;
  motors: DriveMotor[];
  chassis: {
    squatDegPerG: number;
    rollDegPerG: number;
    cgHeightM: number;
    staticRear: number;
    /** the rear wheels' largest angle, degrees (0: they do not steer) */
    rearSteerMaxDeg: number;
    crabDeg: number;
  };
  /** drag coefficient times frontal area, m2 */
  cdA: number;
  finish: 'coast' | 'cruise' | 'brake';
  cruiseKmh?: number;
  /** the 100-0 distance the stop is calibrated to, m */
  brake100M?: number;
  manoeuvres?: ('sweep' | 'slalom' | 'crab')[];
  /** the extra runs the chips offer, with the time the maker publishes for 0-100 and 0-200 marked */
  runs?: { from: number; to: number }[];
  /** the road: wet or dry, and the hill in per cent (negative: downhill) */
  env?: { wet: boolean; gradePct: number };
}

/** What the run reads at one moment (the panel's instruments, the HUD's stopwatch). */
export interface DriveTelemetry {
  phase: DrivePhase;
  /** km/h */
  speed: number;
  /** longitudinal acceleration in g (negative: braking) */
  g: number;
  latG: number;
  /** battery power, kW (negative: the brakes feed it) */
  powerKw: number;
  torqueNm: number | null;
  /** each motor's share of the output (the run's motor order; sums to 1) and its power, kW */
  motorShare: number[];
  motorKw: number[];
  /** the rear axle's share of the weight on the road */
  axleRear: number;
  pitchDeg: number;
  rollDeg: number;
  /** each corner's spring compression, mm: FL, FR, RL, RR (negative: it has extended) */
  corner: [number, number, number, number];
  energyWh: number;
  regenWh: number;
  /** the range the net energy used would have driven, km */
  rangeKm: number | null;
  /** how much of the braking the motors do (the rest is the brakes' friction), 0 to 1 */
  regenFrac: number;
  /** the distance since the brakes came on, m */
  brakeDistM: number;
  dragN: number;
  dragKw: number;
  /** the angle of the front and the rear wheels at the middle of the axle, degrees, and the front angle without rear steering */
  steerFront: number;
  steerRear: number;
  frontOnly: number;
  /** the radius of the curve being driven, m (null on a straight) */
  radius: number | null;
  /** how much the rear motors favour the outside wheel, -1 to 1 (positive: the right wheel) */
  vectoring: number;
  /** the crab angle, degrees */
  crabDeg: number;
  /** how many times wider than the readout the car's wheels are drawn turned (the S-curve's, so that they can be seen) */
  steerScale: number;
  /** the road the car has covered, m */
  distance: number;
}

export interface DriveSummary {
  /** the pull's time, s (null when the run never reached its target) */
  runTime: number | null;
  topKmh: number;
  peakG: number;
  peakKw: number;
  energyWh: number;
  regenWh: number;
  rangeKm: number | null;
  /** the stop: the distance from the brakes coming on, the speed they came on at (km/h), and the time it took */
  brakeM: number | null;
  brakeFromKmh: number | null;
  brakeS: number | null;
  peakLatG: number;
  peakPitchDeg: number;
  peakRollDeg: number;
  /** the widest rear and front angles in the run, degrees */
  maxRearDeg: number;
  maxFrontDeg: number;
  /** the tightest radius driven, and the one the front wheels alone would have needed at the same front angle */
  minRadius: number | null;
}

export interface DriveFacts {
  motors: DriveMotor[];
  /** the most the mode lets the battery give, kW (the scale of the power the instruments draw) */
  modePeakKw: number;
  events: DriveEvent[];
  runs: DriveRunInfo[];
  /** the active run's id */
  run: string;
  telemetry: (t: number) => DriveTelemetry;
  /** the speed against time, for the chart: every 0.1 s */
  curve: { dt: number; v: number[] };
  summary: DriveSummary;
  /** the run is the maker's own figure (full power, driver alone) */
  nominal: boolean;
  /** the road the run is on */
  env: { wet: boolean; gradePct: number };
  lateral: boolean;
  rearSteerMaxDeg: number;
}

export interface DriveRun {
  track: PlannedRun;
  road: RoadStage;
  scroll: (t: number) => number;
  chassis: (t: number) => Chassis;
  launch: {
    readout: (t: number) => LaunchReadout;
    marks: LaunchMark[];
    target: number;
    drive: DriveFacts;
  };
  frame: { cx: number; cz: number; radius: number; camera: { az: number; el: number } };
  lateral: boolean;
}

// ------------------------------------------------------------------------------------------- the pull

/**
 * Past 100 km/h the pull falls with speed, a = a0 (V100 / v)^p, as a power-limited car's does. The exponent that
 * takes the car from 100 to 200 km/h in the published time.
 */
export function falloff(a0: number, span: number): number {
  const time = (p: number) => {
    const n = 2000;
    const dv = V100 / n;
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

/**
 * The times of a mode and a load: 0-100 scales with the inverse cube root of the power the mode lets through
 * (lib/performance.ts) and with the mass to the 0.4 (the power-limited part of a pull feels the mass fully, the grip-limited
 * part not at all); the 0-200 keeps the shape of the maker's pull.
 */
export function driveTimes(zeroTo100: number, zeroTo200: number | undefined, powerFrac: number, massRatio: number) {
  const k = Math.pow(massRatio, 0.4) / Math.cbrt(Math.max(powerFrac, 0.05));
  return { t100: zeroTo100 * k, t200: zeroTo200 !== undefined ? zeroTo200 * k : undefined };
}

/** The pull's acceleration by speed (the launch's shape): a plateau to 100 km/h, then falling as a power-limited car's. */
export function pullModel(t100: number, t200: number | undefined) {
  const a0 = V100 / (t100 - BUILD / 2);
  const p = t200 && t200 > t100 + 0.5 ? falloff(a0, t200 - t100) : 1;
  return {
    a0,
    p,
    /** the acceleration at speed v (m/s), m/s^2, before the build-up */
    at: (v: number) => (v <= V100 ? a0 : a0 * Math.pow(V100 / v, p)),
  };
}

/** The time a pull takes between two speeds, km/h, and the speed against time from the start of it, for a chart or a chip. */
export function pullCurve(
  t100: number,
  t200: number | undefined,
  from: number,
  to: number,
  dt = 0.1,
  env: { cap: number; gradeA: number } = { cap: Infinity, gradeA: 0 },
) {
  const m = pullModel(t100, t200);
  const vTo = to / 3.6;
  let v = from / 3.6;
  let t = 0;
  const out = [from];
  let next = dt;
  while (v < vTo && t < 60) {
    const build = from === 0 ? smooth(t / BUILD) : smooth(t / 0.25);
    v += Math.max((Math.min(m.at(v), env.cap) - env.gradeA) * build, 0.05) * (1 / 960);
    t += 1 / 960;
    if (t >= next) {
      out.push(Math.min(v, vTo) * 3.6);
      next += dt;
    }
  }
  return { time: t, v: out, dt };
}

/**
 * How far along the road a car has got at time t when it holds its start speed for the stand on the line, pulls through its own
 * curve (the same one the chart draws) and holds the speed it reached: the Drive tab's rival, drawn beside the car.
 */
export function pullTrack(
  t100: number,
  t200: number | undefined,
  from: number,
  to: number,
  env?: { cap: number; gradeA: number },
): (t: number) => number {
  const c = pullCurve(t100, t200, from, to, 0.1, env);
  const n = c.v.length;
  const s: number[] = [0];
  for (let i = 0; i + 1 < n; i++) s.push(s[i] + (((c.v[i] + c.v[i + 1]) / 2) / 3.6) * c.dt);
  const v0 = from / 3.6;
  return (t) => {
    if (t <= HOLD) return v0 * Math.max(t, 0);
    const base = v0 * HOLD;
    const tau = t - HOLD;
    const i = Math.min(Math.floor(tau / c.dt), n - 1);
    const d = tau - i * c.dt;
    if (i >= n - 1) return base + s[n - 1] + (c.v[n - 1] / 3.6) * d;
    const a = (c.v[i + 1] - c.v[i]) / 3.6 / c.dt;
    return base + s[i] + (c.v[i] / 3.6) * d + 0.5 * a * d * d;
  };
}

// ------------------------------------------------------------------------------------------- the stop

/** The deceleration law of a stop: the pedal eases off as the car comes to rest. */
function brakeDistance(aB: number, v0: number): number {
  const dt = 1 / 960;
  let v = v0;
  let a = 0;
  let d = 0;
  for (let i = 0; i < 40000 && v > 0.03; i++) {
    const aCmd = -aB * clamp(v / 1.2, 0.3, 1);
    a += clamp(aCmd - a, -60 * dt, 60 * dt);
    v += a * dt;
    d += Math.max(v, 0) * dt;
  }
  return d;
}

/** The peak deceleration that stops the car from v0 in this distance. */
function calibrateBrake(distance: number, v0: number): number {
  let lo = 3;
  let hi = 16;
  for (let i = 0; i < 40; i++) {
    const mid = (lo + hi) / 2;
    if (brakeDistance(mid, v0) > distance) lo = mid;
    else hi = mid;
  }
  return (lo + hi) / 2;
}

/** 100-0 in 36 m when the maker does not say (about 1.1 g), ours */
const DEFAULT_BRAKE_100 = 36;

// ------------------------------------------------------------------------------------------- the plan

type Seg =
  | { kind: 'hold'; dur: number }
  | { kind: 'pull' }
  | { kind: 'carry'; dur: number }
  | { kind: 'ease'; dur: number }
  | { kind: 'coast'; dur: number }
  | { kind: 'cruise'; vTo: number; dur: number }
  | { kind: 'lift'; dur: number }
  | { kind: 'brake' }
  | { kind: 'gentle' }
  | { kind: 'stop'; dur: number }
  | { kind: 'decel'; vTo: number }
  | { kind: 'sweep'; vCap: number }
  | { kind: 'slalom'; v: number }
  | { kind: 'crab'; v: number };

const SWEEP = { amp: 1.0, lambda: 130, periods: 2, push: 0.26 };
/**
 * At 100 km/h the road wheels of a sedan turn about half a degree in a gentle S-curve, too little to see: they are drawn this many
 * times wider in the sweep (the readout gives the real angle and says so), within a few degrees.
 */
export const SWEEP_STEER_DRAWN = 8;
const SWEEP_STEER_MAX = 6 * DEG;
const SLALOM = { amp: 1.4, lambda: 24, periods: 2 };
const CRAB = { shift: 1.8 };

function segmentsOf(inp: DriveInput, brakeNow: boolean): Seg[] {
  const segs: Seg[] = [{ kind: 'hold', dur: HOLD }, { kind: 'pull' }];
  if (inp.to >= 200) segs.push({ kind: 'carry', dur: CARRY });
  segs.push({ kind: 'ease', dur: EASE });
  const moves = inp.to <= 150 ? (inp.manoeuvres ?? []) : [];
  if (moves.length) {
    for (const m of moves) {
      if (m === 'sweep') segs.push({ kind: 'sweep', vCap: 130 / 3.6 });
      if (m === 'slalom') segs.push({ kind: 'decel', vTo: 16 / 3.6 }, { kind: 'slalom', v: 16 / 3.6 });
      if (m === 'crab') segs.push({ kind: 'decel', vTo: 7 / 3.6 }, { kind: 'crab', v: 7 / 3.6 });
    }
    const last = moves[moves.length - 1];
    if (last === 'sweep') segs.push({ kind: 'coast', dur: 2 });
    else segs.push({ kind: 'gentle' }, { kind: 'stop', dur: 1.4 });
  } else if (brakeNow) {
    segs.push({ kind: 'lift', dur: 1 }, { kind: 'brake' }, { kind: 'stop', dur: 2 });
  } else if (inp.finish === 'cruise') {
    segs.push({ kind: 'cruise', vTo: (inp.cruiseKmh ?? 120) / 3.6, dur: 4.5 });
  } else {
    segs.push({ kind: 'coast', dur: COAST });
  }
  return segs;
}

export function planDrive(
  layout: Layout,
  body: { rear: number; front: number; halfWidth: number },
  start: { x: number; y: number; yaw: number },
  inp: DriveInput,
  opts: { brake?: boolean; rival?: boolean } = {},
): DriveRun {
  const brakeNow = inp.finish === 'brake' || opts.brake === true;
  const segs = segmentsOf(inp, brakeNow && !(inp.manoeuvres?.length && inp.to <= 150));
  const lateral = segs.some((s) => s.kind === 'sweep' || s.kind === 'slalom' || s.kind === 'crab');
  const L = layout.wheelbase;
  const radius = [layout.radius.FL, layout.radius.FR, layout.radius.RL, layout.radius.RR];
  const corners = (['FL', 'FR', 'RL', 'RR'] as const).map((c) => layout.wheels[c]);
  const halfTrack = Math.abs(layout.wheels.FL.y - layout.wheels.FR.y) / 2;

  // the pull: the times in this mode and load, and the shape through them
  const { t100, t200 } = driveTimes(inp.zeroTo100, inp.zeroTo200, inp.powerFrac, inp.massKg / inp.refMassKg);
  const model = pullModel(t100, t200);
  const nominalModel = pullModel(inp.zeroTo100, inp.zeroTo200);
  const v0 = inp.from / 3.6;
  const vTo = inp.to / 3.6;
  const rolling = inp.from > 0;

  // the force that turns the battery's power into the car's: calibrated so that the maker's own run (full power, the driver
  // alone) draws the variant's peak, whatever the mass and drag of the stand-in
  const dragAt = (v: number) => 0.5 * RHO * inp.cdA * v * v;
  const rollF = (m: number) => CRR * m * G;
  let wheelPeak = 0;
  for (let v = 1; v <= 200 / 3.6; v += 0.5) {
    wheelPeak = Math.max(wheelPeak, (inp.refMassKg * nominalModel.at(v) + dragAt(v) + rollF(inp.refMassKg)) * v);
  }
  const eta = clamp(wheelPeak / (0.97 * inp.peakKw * 1000), 0.7, 1);
  const peakW = inp.peakKw * inp.powerFrac * 1000;
  const forceRef = inp.refMassKg * nominalModel.a0 + rollF(inp.refMassKg);
  const regenMaxF = 0.3 * inp.massKg * G;
  const regenMaxW = Math.min(300, 0.3 * inp.peakKw) * 1000;

  const dBrake = inp.brake100M ?? DEFAULT_BRAKE_100;
  const aBrake = calibrateBrake(dBrake, V100);
  const squatRad = inp.chassis.squatDegPerG * DEG * inp.squatScale * (inp.massKg / inp.refMassKg);
  const diveRad = squatRad * 1.25;
  const rollRad = inp.chassis.rollDegPerG * DEG * (inp.massKg / inp.refMassKg);
  const h = inp.chassis.cgHeightM;
  const rearMax = inp.chassis.rearSteerMaxDeg * DEG;
  const motors = inp.motors;
  const frontSum0 = motors.filter((m) => m.axle === 'front').reduce((s, m) => s + m.share, 0);
  const road = roadEnv(Boolean(inp.env?.wet), frontSum0 > 0 && frontSum0 < 1, inp.env?.gradePct ?? 0);
  const gradeA = road.gradeA;
  // a wet road: the tyres slip more, and the stop is what they hold
  const slipGain = road.wet ? 1.8 : 1;
  const aBrakeNow = road.wet ? Math.min(aBrake, WET_MU * G * 0.97) : aBrake;

  // state
  let seg = 0;
  let segT = 0;
  let segS = 0;
  let segAux = 0;
  let t = 0;
  let v = v0;
  let s = 0;
  let a = 0;
  let aEnd = 0;
  let aSeg0 = 0;
  let pitch = 0;
  let pitchRate = 0;
  let roll = 0;
  let rollRate = 0;
  let e = 0;
  let yaw = 0;
  let kappa = 0;
  let steerF = 0;
  let steerR = 0;
  let xc = 0;
  let crabAng = 0;
  let vect = 0;
  let energy = 0;
  let regen = 0;
  let brakeD = 0;
  let braking = false;
  let tPull0 = -1;
  let tTarget = -1;
  let tBrake0 = -1;
  let vBrake0 = 0;
  let brakeTime: number | null = null;
  let stopT = -1;
  const spin = [0, 0, 0, 0];
  const events: DriveEvent[] = [];
  const crossings = new Map<number, number>();
  const watch = [100, 150, 200].filter((x) => x > inp.from && x < inp.to);
  const crossAt = [...watch, inp.to];
  const ch: Record<string, number[]> = {};
  const rec = (k: string, x: number) => {
    (ch[k] ??= []).push(x);
  };
  const phaseIdx: number[] = [];

  const note = (cue: DriveCueName, label: string) => {
    if (!events.some((x) => x.cue === cue)) events.push({ cue, t, label });
  };

  const sweepLen = SWEEP.lambda * SWEEP.periods;
  const slalomLen = SLALOM.lambda * SLALOM.periods;
  const crabDx = (1.5 * CRAB.shift) / Math.tan(inp.chassis.crabDeg * DEG);

  // a path y(x) = amp * window(x) * sin(kx), the window easing the curve in over the first half wavelength and out over the
  // last, with its slope and its second derivative
  const wave = (x: number, amp: number, lam: number, len: number) => {
    const k = (2 * Math.PI) / lam;
    const ramp = lam / 2;
    let w = 1;
    let dw = 0;
    let ddw = 0;
    if (x < ramp) {
      const u = clamp(x / ramp, 0, 1);
      w = smooth(u);
      dw = (6 * u * (1 - u)) / ramp;
      ddw = (6 * (1 - 2 * u)) / (ramp * ramp);
    } else if (len - x < ramp) {
      const u = clamp((len - x) / ramp, 0, 1);
      w = smooth(u);
      dw = -(6 * u * (1 - u)) / ramp;
      ddw = (6 * (1 - 2 * u)) / (ramp * ramp);
    }
    const sn = Math.sin(k * x);
    const cs = Math.cos(k * x);
    return {
      y: amp * w * sn,
      dy: amp * (dw * sn + w * k * cs),
      ddy: amp * (ddw * sn + 2 * dw * k * cs - w * k * k * sn),
    };
  };

  let n = 0;
  let finished = false;
  const maxN = Math.ceil(120 / STEP);
  for (let i = 0; i < maxN && !finished; i++) {
    t = i * STEP;
    const sg = segs[seg];
    let aCmd = 0;
    let down = 8;
    let up = 5;
    let direct = false;
    let phase: DrivePhase = 'coast';
    let advance = false;
    kappa = 0;
    steerF = 0;
    steerR = 0;
    crabAng = 0;
    vect = 0;
    let latE = e;

    switch (sg.kind) {
      case 'hold':
        phase = 'hold';
        direct = true;
        a = 0;
        advance = segT >= sg.dur;
        break;
      case 'pull': {
        phase = 'pull';
        direct = true;
        if (tPull0 < 0) {
          tPull0 = t;
          note('launch', rolling ? `${inp.from} km/h` : 'Launch');
        }
        const build = rolling ? smooth(segT / 0.25) : smooth(segT / BUILD);
        a = (Math.min(model.at(v), road.cap) - gradeA) * build;
        aEnd = a;
        advance = v >= vTo;
        break;
      }
      case 'carry':
        phase = 'pull';
        direct = true;
        a = aEnd * 0.85 * (1 - 0.5 * smooth(segT / sg.dur));
        advance = segT >= sg.dur;
        break;
      case 'ease': {
        phase = 'ease';
        direct = true;
        if (tTarget < 0) {
          tTarget = t;
          note('target', `${inp.to} km/h`);
        }
        // from where the pull left off to a lift of the pedal, then away to nothing
        a = (aEnd * 0.42 + (aSeg0 - aEnd * 0.42) * (1 - smooth(segT / 0.12))) * (1 - smooth(segT / sg.dur));
        advance = segT >= sg.dur;
        break;
      }
      case 'coast':
        phase = 'coast';
        aCmd = 0;
        advance = segT >= sg.dur;
        break;
      case 'cruise': {
        phase = 'ease';
        aCmd = clamp(0.8 * (sg.vTo - v), -1.2, 0.6);
        down = 3;
        up = 2;
        if (Math.abs(sg.vTo - v) < 0.25 && segAux === 0) {
          segAux = segT;
          note('cruise', `${Math.round(sg.vTo * 3.6)} km/h`);
        }
        if (segAux > 0) phase = 'cruise';
        advance = (segAux > 0 && segT - segAux >= sg.dur) || segT > 14;
        break;
      }
      case 'lift':
        // off the pedal and onto the speed the stop is quoted from (100 km/h after a 0-100 pull)
        phase = 'lift';
        aCmd = clamp(2 * (vTo - v), -1.5, 0.3);
        down = 3;
        up = 3;
        advance = (segT >= sg.dur && Math.abs(vTo - v) < 0.1) || segT > 3;
        break;
      case 'brake':
      case 'gentle': {
        phase = 'brake';
        if (sg.kind === 'brake') {
          if (tBrake0 < 0) {
            tBrake0 = t;
            vBrake0 = v;
            note('brake', 'Brake');
            braking = true;
          }
          aCmd = -aBrakeNow * clamp(v / 1.2, 0.3, 1) - gradeA;
          down = 60;
          up = 60;
        } else {
          phase = 'decel';
          aCmd = -3 * clamp(v / 1.0, 0.25, 1) - gradeA;
          down = 6;
          up = 6;
        }
        advance = v <= 0.03;
        break;
      }
      case 'stop':
        phase = 'stop';
        v = 0;
        a = 0;
        direct = true;
        if (stopT < 0) {
          stopT = t;
          note('stop', 'Stop');
        }
        advance = segT >= sg.dur;
        break;
      case 'decel':
        phase = 'decel';
        aCmd = -Math.min(0.5 * G, 1.2 * Math.max(v - sg.vTo, 0)) - gradeA;
        down = 6;
        up = 6;
        advance = v <= sg.vTo + 0.1;
        break;
      case 'sweep': {
        phase = 'sweep';
        note('sweep', 'S-curve');
        aCmd = v < sg.vCap ? SWEEP.push * G * Math.pow(V100 / Math.max(v, V100), 0.8) : 0.4 * (sg.vCap - v);
        down = 6;
        up = 4;
        const w = wave(segS, SWEEP.amp, SWEEP.lambda, sweepLen);
        latE = w.y;
        kappa = w.ddy / Math.pow(1 + w.dy * w.dy, 1.5);
        yaw = Math.atan(w.dy);
        advance = segS >= sweepLen;
        break;
      }
      case 'slalom': {
        phase = 'slalom';
        note('slalom', 'Slalom');
        aCmd = 0.8 * (sg.v - v);
        const w = wave(segS, SLALOM.amp, SLALOM.lambda, slalomLen);
        latE = w.y;
        kappa = w.ddy / Math.pow(1 + w.dy * w.dy, 1.5);
        yaw = Math.atan(w.dy);
        advance = segS >= slalomLen;
        break;
      }
      case 'crab': {
        phase = 'crab';
        note('crab', 'Crab walk');
        aCmd = 0.8 * (sg.v - v);
        const u = clamp(segS / crabDx, 0, 1);
        latE = CRAB.shift * smooth(u);
        const slope = u > 0 && u < 1 ? (CRAB.shift * 6 * u * (1 - u)) / crabDx : 0;
        crabAng = Math.atan(slope);
        yaw = 0;
        advance = segS >= crabDx;
        break;
      }
    }

    // the wheels' angles from the curve (a rotation about a point on the car's axis) or from the crab
    let steer: [number, number, number, number] = [0, 0, 0, 0];
    const lk = L * Math.abs(kappa);
    if (lk > 1e-6) {
      // slalom lets the rear wheels help; at speed they stay straight
      const wantC = sg.kind === 'slalom' && rearMax > 0 ? 0.6 : 0;
      let tf = lk / (1 + wantC);
      let tr = wantC * tf;
      if (tr > Math.tan(rearMax)) {
        tr = Math.tan(rearMax);
        tf = lk - tr;
      }
      xc = tr / Math.abs(kappa);
      steer = corners.map((c) => Math.atan((kappa * (c.x - xc)) / (1 - kappa * c.y))) as typeof steer;
      if (sg.kind === 'sweep') steer = steer.map((a) => clamp(a * SWEEP_STEER_DRAWN, -SWEEP_STEER_MAX, SWEEP_STEER_MAX)) as typeof steer;
      steerF = Math.atan(Math.sign(kappa) * tf);
      steerR = -Math.atan(Math.sign(kappa) * tr);
      yaw += Math.atan(kappa * xc);
    } else if (sg.kind === 'crab') {
      const rear = Math.sign(crabAng) * Math.min(Math.abs(crabAng), rearMax || crabAng);
      steer = [crabAng, crabAng, rear, rear];
      steerF = crabAng;
      steerR = rear;
    }
    e = latE;

    // lateral acceleration, and how the rear motors favour the outside wheel
    const ay = v * v * kappa;
    const latG = ay / G;
    if (sg.kind === 'sweep') vect = clamp(0.9 * latG, -0.4, 0.4);
    if (sg.kind === 'crab') vect = 0.25 * Math.sign(crabAng) * clamp(Math.abs(crabAng) / (inp.chassis.crabDeg * DEG), 0, 1);

    // the car's acceleration: the pull's own, or the pedal's through a jerk limit
    if (!direct) a += clamp(aCmd - a, -down * STEP, up * STEP);
    if (v <= 0.001 && a < 0) a = 0;

    // the force at the road, the battery's power, and where the brakes' energy goes
    const drag = dragAt(v);
    const rolling_ = v > 0.1 ? rollF(inp.massKg) : 0;
    const force = inp.massKg * (a + gradeA) + drag + rolling_;
    let powerW = 0;
    let torque = 0;
    let regenFrac = 0;
    if (force >= 0) {
      powerW = Math.min((force * v) / eta, peakW);
      torque = clamp((force / forceRef) * (inp.peakNm ?? 1), 0, inp.peakNm ?? 1);
    } else {
      const fb = -force;
      const blend = clamp((v * 3.6 - 3) / 5, 0, 1);
      const fr = Math.min(fb, regenMaxF, v > 0.1 ? regenMaxW / v : 0) * blend;
      regenFrac = fb > 0 ? fr / fb : 0;
      powerW = -fr * v * 0.85;
      torque = -clamp((fr / forceRef) * (inp.peakNm ?? 1), 0, inp.peakNm ?? 1);
    }
    energy += Math.max(powerW, 0) * STEP / 3600;
    regen += Math.max(-powerW, 0) * STEP / 3600;
    if (braking && v > 0.03) brakeD += v * STEP;

    // body: pitch under the pedal, roll in the curve, both on their springs
    const targetP = a >= 0 ? (a / G) * squatRad : (a / G) * diveRad;
    pitchRate += (-2 * 0.35 * 2 * Math.PI * 1.5 * pitchRate - Math.pow(2 * Math.PI * 1.5, 2) * (pitch - targetP)) * STEP;
    pitch += pitchRate * STEP;
    const targetR = latG * rollRad;
    rollRate += (-2 * 0.4 * 2 * Math.PI * 1.8 * rollRate - Math.pow(2 * Math.PI * 1.8, 2) * (roll - targetR)) * STEP;
    roll += rollRate * STEP;

    if (i % SAVE === 0) {
      const g = a / G;
      const rearW = clamp(inp.chassis.staticRear + g * (h / L), 0.2, 0.8);
      // how the drive is shared: the rear takes more under power and the front under the brakes; the rear pair follows the curve
      const shift = clamp(0.35 * g * (h / L), -0.12, 0.12);
      const frontSum = frontSum0 > 0 && frontSum0 < 1 ? clamp(frontSum0 - shift, 0.02, 0.98) : frontSum0;
      const shares = motors.map((m) => {
        const axleSum = m.axle === 'front' ? frontSum0 : 1 - frontSum0;
        const axleNow = m.axle === 'front' ? frontSum : 1 - frontSum;
        let share = axleSum > 0 ? (m.share / axleSum) * axleNow : 0;
        if (m.axle === 'rear' && m.side) {
          const pair = motors.filter((o) => o.axle === 'rear' && o.side).length;
          if (pair === 2) share = axleNow * (m.side === 'right' ? 0.5 + vect / 2 : 0.5 - vect / 2);
        }
        return share;
      });
      rec('V', v);
      rec('S', s);
      rec('A', a);
      rec('P', pitch);
      rec('R', roll);
      rec('Q', a > 0.2 ? slipAt(v) * slipGain * clamp(a / model.a0, 0, 1) : 0);
      rec('E', e);
      rec('YAW', yaw);
      rec('KAP', kappa);
      rec('LATG', latG);
      rec('SF', steerF);
      rec('SR', steerR);
      rec('PW', powerW / 1000);
      rec('TQ', torque);
      rec('EN', energy);
      rec('RG', regen);
      rec('BD', brakeD);
      rec('RF', regenFrac);
      rec('RW', rearW);
      rec('DRAG', drag);
      rec('VEC', vect);
      rec('CRAB', crabAng);
      for (let j = 0; j < 4; j++) {
        rec(`W${j}`, spin[j]);
        rec(`ST${j}`, steer[j]);
      }
      motors.forEach((_m, j) => rec(`M${j}`, shares[j]));
      phaseIdx.push(PHASES.indexOf(phase));
      n++;
    }

    // watch the crossings of the stopwatch's speeds
    for (const w of crossAt) {
      if (!crossings.has(w) && tPull0 >= 0 && v >= w / 3.6) {
        crossings.set(w, t - HOLD);
        if (w !== inp.to) events.push({ cue: 'pull', t, label: `${w} km/h` });
      }
    }

    // wheels: they spin a touch ahead of the road, and at the very start spin up before the car has moved
    const lead = !rolling && t >= HOLD ? 1.2 * Math.exp(-(t - HOLD) / 0.18) : 0;
    const slip = a > 0.2 ? slipAt(v) * slipGain * clamp(a / model.a0, 0, 1) : 0;
    for (let j = 0; j < 4; j++) {
      const scrub = sg.kind === 'crab' ? Math.cos(crabAng - steer[j]) : 1;
      const w = ((v * (1 + slip) + lead) * scrub) / radius[j];
      spin[j] += SPIN_SHOWN * Math.tanh(w / SPIN_SHOWN) * STEP;
    }
    v = Math.max(0, v + a * STEP);
    s += v * STEP;
    segT += STEP;
    segS += v * STEP;
    if (advance) {
      if (sg.kind === 'brake' && brakeTime === null && tBrake0 >= 0) brakeTime = t - tBrake0;
      seg++;
      segT = 0;
      segS = 0;
      segAux = 0;
      aSeg0 = a;
      if (seg >= segs.length) finished = true;
    }
  }

  // hold the last values to the end so a read at the very end does not run into zeros
  const fill = (name: string) => {
    const arr = Float32Array.from(ch[name] ?? [0]);
    return arr;
  };
  const C: Record<string, Float32Array> = {};
  for (const k of Object.keys(ch)) C[k] = fill(k);
  const kept = n;
  const dt = STEP * SAVE;
  const duration = (kept - 1) * dt;
  const at = (arr: Float32Array, time: number) => {
    const f = clamp(Math.max(time, 0) / dt, 0, kept - 1.0001);
    const k = Math.floor(f);
    return arr[k] + (arr[k + 1] - arr[k]) * (f - k);
  };
  const near = (time: number) => clamp(Math.round(Math.max(time, 0) / dt), 0, kept - 1);
  const length = at(C.S, duration);

  // the stopwatch's marks: the speeds the run passes and where it ends
  const tRun = crossings.get(inp.to) ?? t - HOLD;
  const marks: LaunchMark[] = [];
  const pub = (sp: number) => inp.nominal && !rolling && (sp === 100 || (sp === 200 && inp.zeroTo200Published === true));
  for (const w of watch) marks.push({ speed: w, time: crossings.get(w) ?? 0, published: pub(w) });
  marks.push({ speed: inp.to, time: Math.round(tRun * 100) / 100, published: pub(inp.to) });

  const telemetry = (time: number): DriveTelemetry => {
    const k = near(time);
    const speedMs = at(C.V, time);
    const aNow = at(C.A, time);
    const pw = at(C.PW, time);
    const share = motors.map((_m, j) => at(C[`M${j}`], time));
    const tq = at(C.TQ, time);
    const pitchV = at(C.P, time);
    const rollV = at(C.R, time);
    const pm = pitchV * (L / 2) * 1000;
    const rm = rollV * halfTrack * 1000;
    const kap = at(C.KAP, time);
    const sf = at(C.SF, time);
    const net = at(C.EN, time) - at(C.RG, time);
    const lkNow = L * Math.abs(kap);
    return {
      phase: PHASES[phaseIdx[k]] ?? 'coast',
      speed: speedMs * 3.6,
      g: aNow / G,
      latG: at(C.LATG, time),
      powerKw: pw,
      torqueNm: inp.peakNm ? tq : null,
      motorShare: share,
      motorKw: share.map((x) => x * Math.abs(pw)),
      axleRear: at(C.RW, time),
      pitchDeg: pitchV / DEG,
      rollDeg: rollV / DEG,
      corner: [-pm - rm, -pm + rm, pm - rm, pm + rm] as [number, number, number, number],
      energyWh: at(C.EN, time),
      regenWh: at(C.RG, time),
      rangeKm: inp.kwhPer100 ? Math.max(net, 0) / (10 * inp.kwhPer100) : null,
      regenFrac: at(C.RF, time),
      brakeDistM: at(C.BD, time),
      dragN: at(C.DRAG, time),
      dragKw: (at(C.DRAG, time) * speedMs) / 1000,
      steerFront: sf / DEG,
      steerRear: at(C.SR, time) / DEG,
      frontOnly: lkNow > 1e-6 ? Math.atan(lkNow) / DEG * Math.sign(kap) : 0,
      radius: Math.abs(kap) > 1e-4 ? 1 / Math.abs(kap) : null,
      vectoring: at(C.VEC, time),
      crabDeg: at(C.CRAB, time) / DEG,
      steerScale: PHASES[phaseIdx[k]] === 'sweep' ? SWEEP_STEER_DRAWN : 1,
      distance: at(C.S, time),
    };
  };

  // the summary the post-run card reads
  let topKmh = 0;
  let peakG = 0;
  let peakKw = 0;
  let peakLat = 0;
  let peakPitch = 0;
  let peakRoll = 0;
  let maxRear = 0;
  let maxFront = 0;
  let minRadius: number | null = null;
  for (let k = 0; k < kept; k++) {
    topKmh = Math.max(topKmh, C.V[k] * 3.6);
    peakG = Math.max(peakG, C.A[k] / G);
    peakKw = Math.max(peakKw, C.PW[k]);
    peakLat = Math.max(peakLat, Math.abs(C.LATG[k]));
    peakPitch = Math.max(peakPitch, Math.abs(C.P[k] / DEG));
    peakRoll = Math.max(peakRoll, Math.abs(C.R[k] / DEG));
    maxRear = Math.max(maxRear, Math.abs(C.SR[k] / DEG), Math.abs(C.CRAB[k] > 0 ? Math.min(C.CRAB[k], rearMax || C.CRAB[k]) / DEG : 0));
    maxFront = Math.max(maxFront, Math.abs(C.SF[k] / DEG));
    if (Math.abs(C.KAP[k]) > 1e-4) {
      const r = 1 / Math.abs(C.KAP[k]);
      minRadius = minRadius === null ? r : Math.min(minRadius, r);
    }
  }
  const net = Math.max(C.EN[kept - 1] - C.RG[kept - 1], 0);
  const summary: DriveSummary = {
    runTime: crossings.has(inp.to) ? Math.round((crossings.get(inp.to) ?? 0) * 100) / 100 : null,
    topKmh,
    peakG,
    peakKw,
    energyWh: C.EN[kept - 1],
    regenWh: C.RG[kept - 1],
    rangeKm: inp.kwhPer100 ? net / (10 * inp.kwhPer100) : null,
    brakeM: tBrake0 >= 0 ? brakeD : null,
    brakeFromKmh: tBrake0 >= 0 ? vBrake0 * 3.6 : null,
    brakeS: brakeTime,
    peakLatG: peakLat,
    peakPitchDeg: peakPitch,
    peakRollDeg: peakRoll,
    maxRearDeg: maxRear,
    maxFrontDeg: maxFront,
    minRadius,
  };
  const curveStep = 0.1;
  const curveV: number[] = [];
  for (let time = 0; time <= duration + 1e-6; time += curveStep) curveV.push(at(C.V, time) * 3.6);

  const runs = runList(inp, t100, t200);
  const runId = `${inp.from}-${inp.to}`;

  const track: PlannedRun = {
    duration,
    stats: {
      maxSteer: Math.max(maxFront, maxRear) * DEG,
      bounds: { min: { x: start.x, y: start.y - 2 }, max: { x: start.x + length, y: start.y + 2 } },
    },
    sample: (time: number): Sample => ({
      x: start.x + at(C.S, time),
      y: start.y + at(C.E, time),
      yaw: start.yaw + at(C.YAW, time),
      steer: [at(C.ST0, time), at(C.ST1, time), at(C.ST2, time), at(C.ST3, time)],
      spin: [at(C.W0, time), at(C.W1, time), at(C.W2, time), at(C.W3, time)],
      speed: at(C.V, time),
      segment: 0,
      phase: 'move',
    }),
    trace: () => [],
  };

  const facts: DriveFacts = {
    motors,
    modePeakKw: inp.peakKw * inp.powerFrac,
    events: events.sort((x, y) => x.t - y.t),
    runs,
    run: runId,
    telemetry,
    curve: { dt: curveStep, v: curveV },
    summary,
    nominal: inp.nominal,
    env: { wet: road.wet, gradePct: inp.env?.gradePct ?? 0 },
    lateral,
    rearSteerMaxDeg: inp.chassis.rearSteerMaxDeg,
  };

  return {
    track,
    // the strip is a long one, with broad dashes: what streams past is the speed; a manoeuvre needs room to move sideways
    road: { humps: [], from: -10, to: length + 30, width: opts.rival ? 9.6 : lateral ? 7.6 : 5.2, markings: { period: 9, length: 3.2, joint: 12.5 } },
    scroll: (time) => at(C.S, time),
    chassis: (time) => ({ heave: 0, pitch: at(C.P, time), roll: at(C.R, time), lift: [0, 0, 0, 0] }),
    launch: {
      readout: (time) => ({
        speed: at(C.V, time) * 3.6,
        g: at(C.A, time) / G,
        elapsed: Math.max(0, time - HOLD),
        slip: at(C.Q, time),
        phase: PHASES[phaseIdx[near(time)]] ?? 'coast',
      }),
      marks,
      target: inp.to,
      drive: facts,
    },
    frame: {
      cx: start.x + (body.front - body.rear) / 2,
      cz: -start.y,
      radius: (body.rear + body.front) * (lateral ? 0.72 : 0.62) * (opts.rival ? 1.45 : 1),
      camera: { az: 72, el: 8 },
    },
    lateral,
  };
}

/** The chips of the run: 0-100, 0-200 where the variant has a time for it, and the scenario's own (a rolling pull). */
export function runList(inp: Pick<DriveInput, 'zeroTo100' | 'zeroTo200' | 'nominal' | 'runs' | 'zeroTo200Published' | 'motors' | 'env'>, t100: number, t200: number | undefined): DriveRunInfo[] {
  const env = roadEnv(Boolean(inp.env?.wet), inp.motors.some((m) => m.axle === 'front') && inp.motors.some((m) => m.axle === 'rear'), inp.env?.gradePct ?? 0);
  const all: { from: number; to: number }[] = [{ from: 0, to: 100 }];
  if (t200 !== undefined) all.push({ from: 0, to: 200 });
  for (const r of inp.runs ?? []) if (!all.some((x) => x.from === r.from && x.to === r.to)) all.push(r);
  return all.map((r) => ({
    id: `${r.from}-${r.to}`,
    label: r.from === 0 ? `0–${r.to}` : `${r.from}–${r.to}`,
    from: r.from,
    to: r.to,
    time: Math.round(pullCurve(t100, t200, r.from, r.to, 0.1, env).time * 100) / 100,
    published: inp.nominal && r.from === 0 && (r.to === 100 || (r.to === 200 && inp.zeroTo200Published === true)),
  }));
}
