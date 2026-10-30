/**
 * The Drive tab's choreography: when each piece of data comes on stage, and which wheels light while it does. Pure functions of the
 * run (`DriveFacts`, drive-run.ts) and of the playhead, like the motion kit's (motion.ts): scrub the run and the picture follows,
 * play it twice and it is the same picture. Nothing here draws.
 *
 * Two layers use it. The car's own wheels (viewer/TechWheelFx.tsx) glow by what each motor puts down, and at the launch they are
 * lit in turn (the front motor, the rear motors, all of them) so that the visitor sees where the drive goes. The data on the
 * left of the stage (showroom/DriveMotion.tsx) is a column of tiles, one per instrument the car's scenario lists
 * (`DriveSpec.overlays`): each is a line of live figures that opens into its own animation when the run gets to its moment
 * (the launch for the power, the stop for the brakes, the S-curve for the steering) and closes when the next one opens.
 */
import type { DriveOverlay } from '../../data/vehicles/schema';
import type { DriveFacts, DriveMotor, DrivePhase, DriveTelemetry } from './drive-run';
import { clamp, Easing, flash, progress } from './motion';

/** Four numbers in the corner order of the rig: front left, front right, rear left, rear right. */
export type Four = [number, number, number, number];

export interface Span {
  from: number;
  to: number;
}

// ------------------------------------------------------------------------------------------- the run's shape

export interface RunShape {
  duration: number;
  /** when the car starts to move: the launch cue, else the first moment it pulls */
  launch: number;
  /** the stretch of the main pull (the first run of 'pull') */
  pull: Span | null;
  /** every stretch of each phase */
  spans: Partial<Record<DrivePhase, Span[]>>;
  /** when the battery power is highest, and what it is */
  peakKw: { t: number; kw: number };
  /** when the acceleration (forwards) is highest, and what it is, g */
  peakG: { t: number; g: number };
  /** the first moment the speed reaches `kmh`, or null */
  reaches: (kmh: number) => number | null;
  /** the stretches where the car loads its tyres hard: more than 0.4 g along or 0.15 g across */
  load: Span[];
}

const STEP = 0.1;
const shapes = new WeakMap<DriveFacts, RunShape>();

/** Read a run once into the times the choreography hangs on (cached by the run). */
export function runShape(facts: DriveFacts, duration: number): RunShape {
  const hit = shapes.get(facts);
  if (hit && hit.duration === duration) return hit;

  const spans: RunShape['spans'] = {};
  const load: Span[] = [];
  const speeds: number[] = [];
  let peakKw = { t: 0, kw: 0 };
  let peakG = { t: 0, g: 0 };
  let phase: DrivePhase | null = null;
  let phaseFrom = 0;
  let loadFrom: number | null = null;
  const close = (p: DrivePhase, to: number) => (spans[p] ??= []).push({ from: phaseFrom, to });
  const n = Math.max(1, Math.ceil(duration / STEP));
  for (let i = 0; i <= n; i++) {
    const t = Math.min(i * STEP, duration);
    const tel = facts.telemetry(t);
    speeds.push(tel.speed);
    if (tel.phase !== phase) {
      if (phase) close(phase, t);
      phase = tel.phase;
      phaseFrom = t;
    }
    if (tel.powerKw > peakKw.kw) peakKw = { t, kw: tel.powerKw };
    if (tel.g > peakG.g) peakG = { t, g: tel.g };
    const hard = Math.abs(tel.g) > 0.4 || Math.abs(tel.latG) > 0.15;
    if (hard && loadFrom === null) loadFrom = t;
    if (!hard && loadFrom !== null) {
      load.push({ from: loadFrom, to: t });
      loadFrom = null;
    }
  }
  if (phase) close(phase, duration);
  if (loadFrom !== null) load.push({ from: loadFrom, to: duration });

  const launchCue = facts.events.find((e) => e.cue === 'launch')?.t;
  const pull = spans.pull?.[0] ?? null;
  const shape: RunShape = {
    duration,
    launch: launchCue ?? pull?.from ?? 0,
    pull,
    spans,
    peakKw,
    peakG,
    reaches: (kmh) => {
      const i = speeds.findIndex((v) => v >= kmh);
      return i < 0 ? null : Math.min(i * STEP, duration);
    },
    load,
  };
  shapes.set(facts, shape);
  return shape;
}

// ------------------------------------------------------------------------------------------- the wheels

export interface WheelLevels {
  /** how hard each wheel is driven, 0..1 (its motor's power against the most one wheel carries in this car) */
  drive: Four;
  /** how hard each wheel's motor feeds the battery under the brakes, 0..1 */
  regen: Four;
  /** how hard each wheel's brake works, 0..1: the share of the braking the motors do not take, split front to rear (ours: 60:40) */
  brake: Four;
}

/** Which wheels a motor turns: its own side's wheel, or both wheels of its axle. */
export function wheelsOf(m: DriveMotor): number[] {
  if (m.axle === 'front') return m.side === 'left' ? [0] : m.side === 'right' ? [1] : [0, 1];
  return m.side === 'left' ? [2] : m.side === 'right' ? [3] : [2, 3];
}

/** The most one wheel's motor carries of the mode's peak power: the scale of the glow. */
export function wheelScale(facts: DriveFacts): number {
  let top = 0;
  for (const m of facts.motors) top = Math.max(top, m.share / wheelsOf(m).length);
  return Math.max(facts.modePeakKw * top, 1);
}

const FRONT_BIAS = 0.6;

/** What each wheel is doing at this moment of the run. */
export function wheelLevels(facts: DriveFacts, tel: DriveTelemetry): WheelLevels {
  const drive: Four = [0, 0, 0, 0];
  const regen: Four = [0, 0, 0, 0];
  const brake: Four = [0, 0, 0, 0];
  const scale = wheelScale(facts);
  // the motors' power is a magnitude; the battery's sign says whether they drive or feed it
  const feeding = tel.powerKw < 0;
  facts.motors.forEach((m, j) => {
    const kw = tel.motorKw[j] ?? 0;
    const ws = wheelsOf(m);
    for (const w of ws) {
      const level = clamp(kw / ws.length / scale);
      if (feeding) regen[w] = Math.max(regen[w], level);
      else drive[w] = Math.max(drive[w], level);
    }
  });
  if (tel.g < -0.05 && tel.speed > 0.5) {
    const hard = clamp(-tel.g / 1.0);
    const friction = hard * (1 - clamp(tel.regenFrac));
    for (let i = 0; i < 4; i++) brake[i] = friction * (i < 2 ? FRONT_BIAS : 1 - FRONT_BIAS) * 2;
    for (let i = 0; i < 4; i++) brake[i] = clamp(brake[i]);
  }
  return { drive, regen, brake };
}

// ------------------------------------------------------------------------------------------- the launch, told in acts

export type ActId = 'front' | 'rear' | 'all';

export interface Act extends Span {
  id: ActId;
  /** the headline of the act and what it says under it */
  title: string;
  line: string;
  /** which wheels it lights (the others dim) */
  wheels: Four;
}

const pct = (x: number) => `${Math.round(x * 100)} %`;
const motorWord = (n: number) => (n === 1 ? 'motor' : 'motors');

/**
 * The launch, told in acts when the car has more than one place its drive comes from: the front motor lights the front wheels,
 * the rear motors the rear wheels, then all together. A car with one axle driven lights that axle. The shares are the run's
 * (ours: the maker does not publish how the motors split a launch), and the lines say so.
 */
export function launchActs(facts: DriveFacts, launch: number): Act[] {
  const front = facts.motors.filter((m) => m.axle === 'front');
  const rear = facts.motors.filter((m) => m.axle === 'rear');
  const acts: Act[] = [];
  let t = launch + 0.1;
  // a quick car has less launch to tell it in: the acts take 5.4 s at most and are squeezed (to about half) into the pull and a second more
  const target = facts.events.find((e) => e.cue === 'target')?.t ?? launch + 4;
  const k = clamp((target - launch + 1.2) / 5.4, 0.5, 1);
  // the share an axle has at the middle of its act, from the run's own readout (the planner moves the drive rearward as the weight does)
  const share = (axle: 'front' | 'rear', mid: number) => {
    const tel = facts.telemetry(mid);
    return facts.motors.reduce((a, m, j) => a + (m.axle === axle ? (tel.motorShare[j] ?? 0) : 0), 0);
  };
  const push = (id: ActId, dur: number, title: string, line: (mid: number) => string, wheels: Four) => {
    acts.push({ id, from: t, to: t + dur * k, title, line: line(t + (dur * k) / 2), wheels });
    t += dur * k;
  };
  const both = front.length > 0 && rear.length > 0;
  if (front.length) {
    push('front', both ? 1.6 : 2.4, `Front axle · ${front.length} ${motorWord(front.length)}`, (mid) => `${pct(share('front', mid))} of the drive`, [1, 1, both ? 0.16 : 0, both ? 0.16 : 0]);
  }
  if (rear.length) {
    const sided = rear.some((m) => m.side);
    push('rear', both ? 1.6 : 2.4, `Rear axle · ${rear.length} ${motorWord(rear.length)}`, (mid) => `${pct(share('rear', mid))} of the drive${sided ? ', one motor to each wheel' : ''}`, [both ? 0.16 : 0, both ? 0.16 : 0, 1, 1]);
  }
  if (both) {
    push('all', 2, `All ${facts.motors.length} ${motorWord(facts.motors.length)} together`, () => 'Every wheel pulls. The split is modelled.', [1, 1, 1, 1]);
  }
  return acts;
}

/** How much each wheel is lit by the act the playhead is in, 0.16..1 (1 outside the acts: the data alone decides). */
export function spotlight(acts: Act[], t: number, fade = 0.25): Four {
  const out: Four = [1, 1, 1, 1];
  for (const a of acts) {
    const w = Easing.inOutQuad(progress(t, a.from - fade, fade)) * (1 - Easing.inOutQuad(progress(t, a.to, fade)));
    if (w <= 0) continue;
    for (let i = 0; i < 4; i++) out[i] = Math.min(out[i], 1 - w * (1 - a.wheels[i]));
  }
  return out;
}

/**
 * How much each wheel is being shown off by an act, 0..1: the act's own wheels while it plays. The launch's first moments put
 * little power down, so the data alone would leave the lit wheels dim; an act lights them at least this brightly.
 */
export function actGlow(acts: Act[], t: number, fade = 0.25): Four {
  const out: Four = [0, 0, 0, 0];
  for (const a of acts) {
    const w = Easing.inOutQuad(progress(t, a.from - fade, fade)) * (1 - Easing.inOutQuad(progress(t, a.to, fade)));
    if (w <= 0) continue;
    for (let i = 0; i < 4; i++) if (a.wheels[i] >= 1) out[i] = Math.max(out[i], w);
  }
  return out;
}

export interface WheelLook {
  /** how brightly each wheel is lit, 0..1 (more while an act shows it off) */
  lit: Four;
  /** how much of each wheel's colour is the battery's feed (green) and the brakes' friction (red), 0..1 */
  regen: Four;
  brake: Four;
  /** a flash that goes through all the wheels as each act begins, 0..1 */
  kick: number;
}

/**
 * What the wheels look like at this moment, for whoever draws them (the rings on the car, the schematic on the screen): the data's
 * level on a perceptual curve (a quarter of the power still shows plainly), dimmed by the act's spotlight and lifted by its glow.
 */
export function wheelLook(facts: DriveFacts, tel: DriveTelemetry, acts: Act[], t: number): WheelLook {
  const lv = wheelLevels(facts, tel);
  const spot = spotlight(acts, t);
  const glow = actGlow(acts, t);
  const lit: Four = [0, 0, 0, 0];
  const regen: Four = [0, 0, 0, 0];
  const brake: Four = [0, 0, 0, 0];
  for (let i = 0; i < 4; i++) {
    const level = Math.max(lv.drive[i], lv.regen[i], lv.brake[i], glow[i] * 0.2);
    lit[i] = Math.max(Math.pow(level, 0.55) * spot[i], 0.7 * glow[i]);
    regen[i] = lv.regen[i] > lv.drive[i] ? clamp(lv.regen[i] / Math.max(level, 1e-3)) : 0;
    brake[i] = lv.brake[i] > 0.02 ? clamp(lv.brake[i] / Math.max(level, 1e-3)) : 0;
  }
  return { lit, regen, brake, kick: acts.reduce((m, a) => Math.max(m, flash(t, a.from, 0.7)), 0) };
}

/** The act the playhead is in, or null. */
export function actAt(acts: Act[], t: number): Act | null {
  return acts.find((a) => t >= a.from && t < a.to) ?? null;
}

/** Each wheel's own power at this moment, kW (the motor's, shared over the wheels it turns; negative while it feeds the battery). */
export function wheelKw(facts: DriveFacts, tel: DriveTelemetry): Four {
  const out: Four = [0, 0, 0, 0];
  const sign = tel.powerKw < 0 ? -1 : 1;
  facts.motors.forEach((m, j) => {
    const ws = wheelsOf(m);
    for (const w of ws) out[w] += (sign * (tel.motorKw[j] ?? 0)) / ws.length;
  });
  return out;
}

/**
 * When each wheel wears a tag with its own figure: while the launch's act lights it, in the S-curve for the wheels that
 * are driven (the split between left and right is the point of it), and under the brakes for all four.
 */
export function tagWindows(facts: DriveFacts, shape: RunShape, acts: Act[]): Span[][] {
  const out: Span[][] = [[], [], [], []];
  for (const a of acts) {
    for (let i = 0; i < 4; i++) if (a.wheels[i] >= 1) out[i].push({ from: a.from + 0.1, to: a.to });
  }
  const driven = new Set(facts.motors.flatMap(wheelsOf));
  for (const s of shape.spans.sweep ?? []) for (const i of driven) out[i].push({ from: s.from + 0.2, to: s.to });
  for (const s of shape.spans.slalom ?? []) for (const i of driven) out[i].push({ from: s.from + 0.2, to: s.to });
  for (const s of shape.spans.brake ?? []) for (let i = 0; i < 4; i++) out[i].push({ from: s.from, to: s.to + 0.8 });
  return out;
}

// ------------------------------------------------------------------------------------------- the stage's captions

export type CaptionTone = 'front' | 'rear' | 'all' | 'peak' | 'turn' | 'stop';

/** A line set large over the stage for a moment of the run, in kinetic type (showroom/DriveMotion.tsx). */
export interface Caption extends Span {
  id: string;
  kicker: string;
  title: string;
  line?: string;
  tone: CaptionTone;
}

/**
 * What is said on the stage and when: the launch's acts (which motor is pulling), the moment the power peaks, the curve (what
 * the motors or the rear wheels do in it), and the stop. Every figure is the run's; a caption that would cut across another is
 * left out, not squeezed in.
 */
export function captionsOf(facts: DriveFacts, shape: RunShape, acts: Act[]): Caption[] {
  const caps: Caption[] = [];
  acts.forEach((a, i) => caps.push({ id: `act-${a.id}`, from: a.from, to: a.to, kicker: `Launch · ${i + 1} of ${acts.length}`, title: a.title, line: a.line, tone: a.id }));

  const peakKw = Math.max(facts.modePeakKw, 1);
  const pk = shape.peakKw;
  if (pk.kw > peakKw * 0.9) {
    const tel = facts.telemetry(pk.t);
    caps.push({ id: 'peak', from: pk.t, to: pk.t + 2, kicker: 'Peak power', title: `${Math.round(pk.kw).toLocaleString('en-GB')} kW`, line: `at ${Math.round(tel.speed)} km/h`, tone: 'peak' });
  }

  const rearSplit = facts.motors.some((m) => m.axle === 'rear' && m.side);
  const sweep = shape.spans.sweep?.[0];
  if (sweep) {
    caps.push({
      id: 'sweep',
      from: sweep.from + 0.2,
      to: sweep.from + 3.4,
      kicker: rearSplit ? 'Torque vectoring' : 'S-curve under power',
      title: rearSplit ? 'The rear motors favour the outside wheel' : 'Both axles pull through the curve',
      line: rearSplit ? 'More torque on the outer wheel pushes the car round. The split is modelled.' : undefined,
      tone: 'turn',
    });
  }
  const slalom = shape.spans.slalom?.[0];
  if (slalom) {
    caps.push({ id: 'slalom', from: slalom.from + 0.2, to: slalom.from + 3.4, kicker: 'Rear-wheel steering', title: 'The rear wheels turn against the front', line: 'The car turns tighter than its front wheels alone could.', tone: 'turn' });
  }
  const crab = shape.spans.crab?.[0];
  if (crab) {
    caps.push({ id: 'crab', from: crab.from + 0.2, to: crab.from + 3.4, kicker: 'Crab walk', title: 'All four wheels turn the same way', line: 'The car slides sideways without turning.', tone: 'turn' });
  }

  const stop = shape.spans.stop?.[0];
  const s = facts.summary;
  if (stop && s.brakeM !== null) {
    caps.push({
      id: 'stop',
      from: stop.from,
      to: stop.from + 2.6,
      kicker: `${Math.round(s.brakeFromKmh ?? 0)} to 0 km/h`,
      title: `${s.brakeM.toFixed(1)} m`,
      line: `${(s.brakeS ?? 0).toFixed(1)} s. The motors take the first of it and feed the battery.`,
      tone: 'stop',
    });
  }

  // one at a time: a caption that overlaps an earlier one waits for it, and is left out if what is left of its time is too short to read
  caps.sort((a, b) => a.from - b.from);
  const out: Caption[] = [];
  for (const c of caps) {
    const prev = out[out.length - 1];
    const next = prev && c.from < prev.to - 1e-6 ? { ...c, from: prev.to } : c;
    // the acts are short by design (a second and a bit each); the others need time to be read
    if (next.id.startsWith('act-') || next.to - next.from >= 1.8) out.push(next);
  }
  return out;
}

// ------------------------------------------------------------------------------------------- the tiles' moments

export interface Beat {
  overlay: DriveOverlay;
  /** when the tile opens, and when it closes (Infinity: it stays open to the end of the run) */
  from: number;
  to: number;
}

type Chapter = 'launch' | 'speed' | 'curve' | 'stop';

/** The instruments each chapter of a run is about, most telling first. The car's own order (`DriveSpec.overlays`) decides which of them it has room for. */
const ABOUT: Record<Chapter, DriveOverlay[]> = {
  launch: ['power', 'motors', 'suspension'],
  speed: ['aero', 'power', 'energy'],
  curve: ['steering', 'motors', 'suspension'],
  stop: ['brake', 'suspension', 'energy'],
};

/**
 * The run told in chapters, each with the tiles it opens: the launch (the power, the motors, the suspension), the speed (the drag, the
 * energy), each curve (the steering, the motors), the stop (the brakes). A chapter runs until the next begins, so the picture
 * is always on something. Of the tiles a chapter is about that the car's scenario lists, the scenario's first stays open for the
 * chapter and, with room for a second (`max` 2), the others take turns in that place. What the run does not have (no stop, no
 * curve) is no chapter.
 */
export function beatPlan(overlays: DriveOverlay[], facts: DriveFacts, shape: RunShape, max = 2): Beat[] {
  const L = shape.launch;
  const acts = launchActs(facts, L);
  const actsEnd = acts.length ? acts[acts.length - 1].to : L + 2;
  const chapters: { kind: Chapter; from: number; to: number }[] = [];
  chapters.push({ kind: 'launch', from: Math.max(0, L - 0.2), to: Math.max(actsEnd, Math.min(shape.pull?.to ?? L + 3, L + 4.6)) + 0.2 });
  const reach = shape.reaches(100);
  if (reach !== null && reach > L + 1) chapters.push({ kind: 'speed', from: reach, to: reach + 4.5 });
  for (const c of [...(shape.spans.sweep ?? []), ...(shape.spans.slalom ?? []), ...(shape.spans.crab ?? [])]) {
    chapters.push({ kind: 'curve', from: Math.max(0, c.from - 0.3), to: c.to + 0.3 });
  }
  const brake = shape.spans.brake?.[0];
  if (brake) chapters.push({ kind: 'stop', from: Math.max(0, brake.from - 0.3), to: shape.duration });

  // chapters follow one another: each ends where the next begins, and one under 0.8 s is not worth a change of tiles
  chapters.sort((a, b) => a.from - b.from);
  const kept: typeof chapters = [];
  for (const c of chapters) {
    const prev = kept[kept.length - 1];
    if (prev) prev.to = Math.min(prev.to, c.from);
    if (prev && prev.to - prev.from < 0.8) kept.pop();
    kept.push({ ...c });
  }
  kept.forEach((c, i) => (c.to = i + 1 < kept.length ? kept[i + 1].from : Infinity));

  const beats: Beat[] = [];
  const push = (overlay: DriveOverlay, from: number, to: number) => {
    // a tile that two stretches running keep open stays open across the change
    const prev = beats.findLast((b) => b.overlay === overlay);
    if (prev && Math.abs(prev.to - from) < 1e-6) prev.to = to;
    else beats.push({ overlay, from, to });
  };
  for (const c of kept) {
    // the car's own order says what the chapter is about: its first tile stays the whole chapter, and where there is room for a
    // second, the others about it take turns in that place (a long chapter gives each about two seconds)
    const about = overlays.filter((o) => ABOUT[c.kind].includes(o));
    if (!about.length) continue;
    push(about[0], c.from, c.to);
    const rest = about.slice(1);
    if (max < 2 || !rest.length) continue;
    const span = Number.isFinite(c.to) ? c.to - c.from : 9;
    const n = Math.min(rest.length, Math.max(1, Math.floor(span / 1.8)));
    rest.slice(0, n).forEach((o, k) => push(o, c.from + (k * span) / n, k === n - 1 ? c.to : c.from + ((k + 1) * span) / n));
  }
  return beats.sort((a, b) => a.from - b.from);
}

/** How open each tile is at `t`, 0 (a line of figures) to 1 (its animation); it opens and closes over a few tenths of a second, as a function of `t`. */
export function openAt(plan: Beat[], overlays: DriveOverlay[], t: number, inDur = 0.45, outDur = 0.4): Record<DriveOverlay, number> {
  const open = {} as Record<DriveOverlay, number>;
  for (const o of overlays) open[o] = 0;
  for (const b of plan) {
    const a = Easing.outCubic(progress(t, b.from, inDur));
    const z = b.to === Infinity ? 1 : 1 - Easing.inOutQuad(progress(t, b.to, outDur));
    open[b.overlay] = Math.max(open[b.overlay] ?? 0, a * z);
  }
  return open;
}
