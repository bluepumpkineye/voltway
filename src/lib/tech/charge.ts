import type { Layout, PlannedRun, Sample } from './kinematics';

/**
 * The fast-charge demo's run (docs/tech-showcase.md section 11): the car's flap opens, a charging gun is drawn
 * from its pedestal and plugged into the DC socket, the car charges from 10 to 80 %, the gun comes out and the
 * flap closes. The car does not move.
 *
 * Published: 620 kW peak and 10 to 80 % in 10 minutes "at best" for the 103 kWh 6C pack (Xinhua, 2025-11-03).
 * Ours, said on screen: the curve between (a ramp up to the peak, a plateau, a taper that makes the ten minutes
 * come out exactly), the pedestal, the gun and its cable, and the speed of the clock: ten minutes play in 14
 * seconds. No value imports: it runs under plain Node, as ride.ts does.
 */

/** The charge port, in the viewer's axes (x forward, y up, z toward the passenger side), from the model. */
export interface ChargePort {
  /** the DC socket's mouth, and the direction pointing out of it (unit) */
  mouth: [number, number, number];
  axis: [number, number, number];
  /** how far the gun's nose goes in, m */
  depth: number;
}

/** the seconds of the demo clock at which each thing happens */
export const T = {
  flapOpens: 0.4,
  gunLeaves: 1.4,
  gunAtPort: 4.4,
  seated: 5.0,
  charge0: 5.4,
  chargeDur: 14,
  /** after the stop: the gun comes out, goes home, the flap closes */
  unplugAfter: 0.3,
  gunBack: 3.4,
  flapCloses: 3.6,
  tail: 1.2,
} as const;
export const T_STOP = T.charge0 + T.chargeDur;
const T_END = T_STOP + T.flapCloses + T.tail;

/** the simulated length of the charge, s (10 to 80 %, at best, published) */
export const SIM_SECONDS = 600;
export const SOC_FROM = 0.1;
export const SOC_TO = 0.8;
export const PEAK_KW = 620;

export type ChargePhase = 'ready' | 'opening' | 'connecting' | 'charging' | 'charged' | 'unplugging' | 'done';

export interface ChargeReadout {
  phase: ChargePhase;
  /** 0 to 1 */
  soc: number;
  kw: number;
  /** simulated time charging, s, and what is left to 80 % */
  elapsed: number;
  left: number;
  /** energy added, kWh */
  kwh: number;
  connected: boolean;
}

export interface GunPose {
  /** the nose's tip and the directions the nose points and the grip drops (unit), viewer axes */
  tip: [number, number, number];
  forward: [number, number, number];
  up: [number, number, number];
  /** 0 on the pedestal, 1 plugged in */
  docked: number;
}

export interface ChargeRun {
  track: PlannedRun;
  stops: number[];
  flapOpen: (t: number) => boolean;
  gun: (t: number) => GunPose;
  readout: (t: number) => ChargeReadout;
  /** the curve for the chart: kW against simulated seconds */
  curve: { s: number; kw: number; soc: number }[];
  pedestal: { x: number; z: number; yaw: number };
  /** where the cable leaves the pedestal, and the gun's cable exit in the gun's own frame (forward, up, right) */
  cableOut: [number, number, number];
  gunExit: [number, number, number];
  frame: { cx: number; cz: number; radius: number; camera: { az: number; el: number } };
}

const smooth = (x: number) => {
  const t = Math.min(1, Math.max(0, x));
  return t * t * (3 - 2 * t);
};
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const norm = (v: number[]): [number, number, number] => {
  const l = Math.hypot(v[0], v[1], v[2]) || 1;
  return [v[0] / l, v[1] / l, v[2] / l];
};

/** the charging power as a fraction of the peak at a state of charge: ramp, plateau, taper to `q` at 80 % */
function shape(s: number, q: number): number {
  if (s < 0.25) return lerp(0.72, 1, smooth((s - SOC_FROM) / (0.25 - SOC_FROM)));
  if (s < 0.45) return 1;
  return lerp(1, q, smooth((s - 0.45) / (SOC_TO - 0.45)));
}

/** the seconds from 10 to 80 % at the shape's `q`, for a pack of `kwh` */
function seconds(kwh: number, q: number): number {
  const n = 700;
  const ds = (SOC_TO - SOC_FROM) / n;
  let t = 0;
  for (let i = 0; i < n; i++) {
    const s = SOC_FROM + (i + 0.5) * ds;
    t += (kwh * ds * 3600) / (PEAK_KW * shape(s, q));
  }
  return t;
}

/** The charging curve: the taper that makes 10 to 80 % take exactly the published ten minutes. */
export function chargeCurve(kwh: number): { s: number; kw: number; soc: number }[] {
  let lo = 0.05;
  let hi = 1.0;
  for (let i = 0; i < 40; i++) {
    const q = (lo + hi) / 2;
    if (seconds(kwh, q) > SIM_SECONDS) lo = q;
    else hi = q;
  }
  const q = (lo + hi) / 2;
  const out: { s: number; kw: number; soc: number }[] = [];
  const dt = 1;
  let soc = SOC_FROM;
  for (let t = 0; t <= SIM_SECONDS + 1e-6; t += dt) {
    const kw = PEAK_KW * shape(soc, q);
    out.push({ s: t, kw, soc });
    soc += (kw * dt) / (kwh * 3600);
  }
  return out;
}

export function planCharge(
  layout: Layout,
  body: { rear: number; front: number; halfWidth: number },
  start: { x: number; y: number; yaw: number },
  opts: { port: ChargePort; kwh: number },
): ChargeRun {
  const { port, kwh } = opts;
  const curve = chargeCurve(kwh);
  const at = (sim: number) => {
    const f = Math.min(Math.max(sim, 0), SIM_SECONDS);
    const i = Math.min(Math.floor(f), curve.length - 2);
    const k = f - i;
    return { kw: lerp(curve[i].kw, curve[i + 1].kw, k), soc: lerp(curve[i].soc, curve[i + 1].soc, k) };
  };
  const kwhAt = (sim: number) => (at(sim).soc - SOC_FROM) * kwh;

  const track: PlannedRun = {
    duration: T_END,
    stats: { maxSteer: 0, bounds: { min: { x: start.x, y: start.y }, max: { x: start.x, y: start.y } } },
    sample: (): Sample => ({ ...start, steer: [0, 0, 0, 0], spin: [0, 0, 0, 0], speed: 0, segment: 0, phase: 'dwell' }),
    trace: () => [],
  };

  const unplug0 = T_STOP + T.unplugAfter;
  const closeAt = T_STOP + T.flapCloses;
  const flapOpen = (t: number) => t >= T.flapOpens && t < closeAt;

  const sim = (t: number) => ((Math.min(Math.max(t, T.charge0), T_STOP) - T.charge0) / T.chargeDur) * SIM_SECONDS;
  const phaseOf = (t: number): ChargePhase => {
    if (t < T.flapOpens) return 'ready';
    if (t < T.gunLeaves) return 'opening';
    if (t < T.charge0) return 'connecting';
    if (t < T_STOP - 1e-3) return 'charging';
    if (t < unplug0) return 'charged';
    return t >= T_END - 1e-3 ? 'done' : 'unplugging';
  };

  // the pedestal stands out from the left flank, level with the port; the gun hangs on its front face
  const out = port.axis;
  const px = port.mouth[0] + 0.55;
  const pz = port.mouth[2] + out[2] * 1.35;
  const FRONT = 0.115;
  const holster: [number, number, number] = [px, 1.1, pz + FRONT + 0.01];
  const A: [number, number, number] = [port.mouth[0] + out[0] * 0.24, port.mouth[1] + out[1] * 0.24, port.mouth[2] + out[2] * 0.24];
  const seat: [number, number, number] = [
    port.mouth[0] - out[0] * port.depth, port.mouth[1] - out[1] * port.depth, port.mouth[2] - out[2] * port.depth,
  ];
  const fwdPort = norm([-out[0], -out[1], -out[2]]);
  const psi1 = Math.atan2(fwdPort[0], fwdPort[2]);
  const pitch1 = Math.asin(fwdPort[1]);
  const psi0 = Math.PI;                        // the gun goes into the pedestal pointing away from the car
  const pull: [number, number, number] = [holster[0] + 0.02, holster[1] + 0.03, holster[2] + 0.28];
  // the way out, turning through the car's front: pull, a high swing, the approach
  const waypoints = [holster, pull, [lerp(pull[0], A[0], 0.55), Math.max(pull[1], A[1]) + 0.12, lerp(pull[2], A[2], 0.5)], A];
  const spline = (s: number): [number, number, number] => {
    const n = waypoints.length - 1;
    const f = Math.min(Math.max(s, 0), 1) * n;
    const i = Math.min(Math.floor(f), n - 1);
    const k = f - i;
    const p0 = waypoints[Math.max(i - 1, 0)];
    const p1 = waypoints[i];
    const p2 = waypoints[i + 1];
    const p3 = waypoints[Math.min(i + 2, n)];
    const c = (j: number) =>
      0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * k + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * k * k + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * k ** 3);
    return [c(0), c(1), c(2)];
  };
  const orient = (psi: number, pitch: number) => {
    const f = norm([Math.cos(pitch) * Math.sin(psi), Math.sin(pitch), Math.cos(pitch) * Math.cos(psi)]);
    const u = norm([-Math.sin(pitch) * Math.sin(psi), Math.cos(pitch), -Math.sin(pitch) * Math.cos(psi)]);
    return { f, u };
  };

  // the gun's progress along the way to the port (0 on the pedestal, 1 at the approach), then the push in
  const approach = (t: number) => smooth((t - T.gunLeaves) / (T.gunAtPort - T.gunLeaves));
  const push = (t: number) => smooth((t - T.gunAtPort) / (T.seated - T.gunAtPort));
  const gun = (t: number): GunPose => {
    let s: number;
    let p: number;
    if (t < unplug0) {
      s = approach(t);
      p = push(t);
    } else {
      // the way back is the way out, run backwards
      const k = smooth((t - unplug0) / (T.gunBack - T.unplugAfter));
      const back = smooth(k / 0.18);
      s = 1 - smooth((k - 0.12) / 0.88);
      p = 1 - back;
    }
    const turn = smooth((s - 0.1) / 0.8);
    const { f, u } = orient(lerp(psi0, psi1, turn), lerp(0, pitch1, turn));
    const base = spline(s);
    const tip: [number, number, number] = [
      lerp(base[0], seat[0], p),
      lerp(base[1], seat[1], p),
      lerp(base[2], seat[2], p),
    ];
    return { tip, forward: f, up: u, docked: p };
  };

  const readout = (t: number): ChargeReadout => {
    const ph = phaseOf(t);
    const sm = sim(t);
    const { kw, soc } = at(sm);
    return {
      phase: ph,
      soc: t < T.charge0 ? SOC_FROM : soc,
      kw: ph === 'charging' ? kw : 0,
      elapsed: t < T.charge0 ? 0 : sm,
      left: Math.max(0, SIM_SECONDS - sm),
      kwh: t < T.charge0 ? 0 : kwhAt(sm),
      connected: t >= T.gunAtPort && t < unplug0 + 0.8,
    };
  };

  return {
    track,
    stops: [T_STOP],
    flapOpen,
    gun,
    readout,
    curve,
    pedestal: { x: px, z: pz, yaw: 0 },
    cableOut: [px + 0.075, 0.62, pz + FRONT],
    gunExit: [-0.215, -0.17, 0],
    // the rear three-quarter of the car's left side: the port, the pedestal ahead of it
    frame: {
      cx: port.mouth[0] + 0.05,
      cz: (port.mouth[2] + pz) / 2,
      radius: 1.8,
      camera: { az: 126, el: 10 },
    },
  };
}
