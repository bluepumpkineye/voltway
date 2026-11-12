import { sharedAudio, soundOn } from './engine';
import { driveMix, voiceOf, type DriveMix, type DriveVoice } from './drive-voice';

/**
 * The Drive tab's motor: three steady loops through Web Audio, their pitch and level set every frame from what the car is doing
 * (drive-voice.ts has the model). A loop is a looping buffer source, so it wraps sample-exactly, forever: nothing is seeked and
 * nothing is tied to the clock, which is why a run of any length sounds the same at 25 s as at 5 s.
 *
 * What it does when things change:
 * - every value eases toward its target (a time constant of a few hundredths of a second), so a frame is never a step;
 * - a pause, a mute or a stall of the frames (the page was hidden) fades the whole motor out instead of cutting it;
 * - the loops start at a random point, so two cars (or two visits) do not begin on the same bar.
 */

const FILES = {
  whine: '/sounds/drive/whine.wav',
  bed: '/sounds/drive/bed.wav',
  hiss: '/sounds/drive/hiss.wav',
} as const;
type LoopName = keyof typeof FILES;
export type DriveLoops = Record<LoopName, AudioBuffer>;

/** the loops are cut to a common level; this brings their sum to a comfortable one (a limiter after it keeps a rush from clipping) */
const LEVEL = 1.45;
/** ease times, s */
const TC_LEVEL = 0.05;
const TC_RATE = 0.07;
const TC_CUT = 0.1;
/** frames that stop arriving for this long (ms) fade the motor out: the page is hidden or the clock stopped without saying so */
const STALL_MS = 700;

const raw = new Map<LoopName, Promise<ArrayBuffer | null>>();
const decoded = new WeakMap<BaseAudioContext, Promise<DriveLoops | null>>();

/** Start fetching the loops (no audio context is needed for that). */
export function prefetchDriveLoops() {
  if (typeof window === 'undefined' || raw.size) return;
  for (const name of Object.keys(FILES) as LoopName[]) {
    raw.set(
      name,
      fetch(FILES[name])
        .then((r) => (r.ok ? r.arrayBuffer() : null))
        .catch(() => null),
    );
  }
}

/** The loops decoded for a context; null when any is missing or cannot be decoded (the motor is then silent, not broken). */
export function decodeDriveLoops(ctx: BaseAudioContext): Promise<DriveLoops | null> {
  let p = decoded.get(ctx);
  if (!p) {
    prefetchDriveLoops();
    p = (async () => {
      const out: Partial<DriveLoops> = {};
      for (const name of Object.keys(FILES) as LoopName[]) {
        const bytes = await raw.get(name);
        if (!bytes) return null;
        try {
          out[name] = await ctx.decodeAudioData(bytes.slice(0));
        } catch {
          return null;
        }
      }
      return out as DriveLoops;
    })();
    decoded.set(ctx, p);
  }
  return p;
}

interface Target {
  ctx: BaseAudioContext;
  /** where the motor plugs in */
  out: AudioNode;
}

interface Graph {
  bus: GainNode;
  sources: AudioBufferSourceNode[];
  whine: { src: AudioBufferSourceNode; gain: GainNode; cut: BiquadFilterNode };
  parts: { src: AudioBufferSourceNode; gain: GainNode };
  bed: { src: AudioBufferSourceNode; gain: GainNode; cut: BiquadFilterNode };
  hissL: { src: AudioBufferSourceNode; gain: GainNode };
  hissR: { src: AudioBufferSourceNode; gain: GainNode };
  nodes: AudioNode[];
}

const SILENT: DriveMix = { whineRate: 0.6, bedRate: 0.9, hissRate: 0.95, whine: 0, parts: 0, bed: 0, hiss: 0, whineCut: 1400, bedCut: 500 };

export class DriveEngine {
  private voice: DriveVoice = voiceOf(null);
  private target: Target | null;
  private graph: Graph | null = null;
  private wantOn = false;
  private mix: DriveMix = SILENT;
  private scale = 1;
  /** how near the car sounds, 1 beside the camera to 0 lost in the distance (the Drive tab's exit: the car drives away and the motor goes with it) */
  private proximity = 1;
  private lastFrame = 0;
  private watchdog: ReturnType<typeof setInterval> | null = null;
  private building = 0;
  /** loops start at 0 in an offline render (so a render repeats), at a random point live */
  private readonly random: boolean;

  /** `target` is given for an offline render (tests); live, the page's shared context is used. */
  constructor(target: Target | null = null, random = target === null) {
    this.target = target;
    this.random = random;
  }

  setVoice(slug: string | null | undefined) {
    this.voice = voiceOf(slug);
  }

  /** the playback speed of the demo (slow motion): the sound slows with it, as a film's does */
  setTimeScale(k: number) {
    this.scale = Math.min(2, Math.max(0.25, k));
  }

  /** Start the motor (silent until frames arrive). Call from a press or a play: a browser lets audio start then. */
  start() {
    this.wantOn = true;
    this.proximity = 1;
    this.lastFrame = performance.now();
    if (this.graph) return;
    const target = this.target ?? sharedTarget();
    if (!target) return;
    this.target = target;
    const ctx = target.ctx;
    if (ctx.state === 'suspended' && 'resume' in ctx) void (ctx as AudioContext).resume().catch(() => {});
    const ticket = ++this.building;
    void decodeDriveLoops(ctx).then((loops) => {
      if (!loops || !this.wantOn || this.graph || ticket !== this.building) return;
      this.graph = this.build(target, loops);
      this.apply(ctx.currentTime);
    });
    if (!this.watchdog && this.random) {
      this.watchdog = setInterval(() => {
        if (this.graph && this.wantOn && performance.now() - this.lastFrame > STALL_MS) this.silence(0.12);
      }, 250);
    }
  }

  /**
   * What the car is doing now: speed km/h, pull g, run phase. `at` schedules it on the context's clock (an offline render). `proximity` is how near the
   * car sounds, 1 beside the camera, 0 gone: the whole motor is quieter with the square of it, and the highs go first (the air takes them).
   */
  update(speed: number, g: number, phase?: string, at?: number, proximity = 1) {
    this.lastFrame = performance.now();
    this.proximity = Math.min(1, Math.max(0, proximity));
    this.mix = driveMix(this.voice, speed, g, phase);
    if (this.graph && this.target) this.apply(at ?? this.target.ctx.currentTime);
  }

  /** Fade the motor out and stop it (a pause, a car change, the end of the run). */
  stop(fadeS = 0.18) {
    this.wantOn = false;
    this.building++;
    this.mix = SILENT;
    if (!this.graph) return;
    this.silence(fadeS);
    // the faded-out graph is taken apart once it is silent; a start() in the meantime builds a new one and leaves this to finish
    const g = this.graph;
    this.graph = null;
    setTimeout(() => {
      for (const s of g.sources) {
        try {
          s.stop();
        } catch {
          // already stopped
        }
      }
      for (const n of g.nodes) n.disconnect();
    }, fadeS * 1000 + 120);
  }

  dispose() {
    this.stop(0.05);
    if (this.watchdog) {
      clearInterval(this.watchdog);
      this.watchdog = null;
    }
  }

  private silence(fadeS: number) {
    const g = this.graph;
    if (!g || !this.target) return;
    const t = this.target.ctx.currentTime;
    g.bus.gain.cancelScheduledValues(t);
    g.bus.gain.setTargetAtTime(0, t, fadeS / 4);
  }

  private build({ ctx, out }: Target, loops: DriveLoops): Graph {
    const nodes: AudioNode[] = [];
    const sources: AudioBufferSourceNode[] = [];
    const add = <T extends AudioNode>(n: T): T => {
      nodes.push(n);
      return n;
    };
    const loop = (buf: AudioBuffer, rate: number) => {
      const src = add(ctx.createBufferSource());
      src.buffer = buf;
      src.loop = true;
      src.playbackRate.value = rate;
      sources.push(src);
      return src;
    };
    const filter = (type: BiquadFilterType, hz: number, q = 0.7) => {
      const f = add(ctx.createBiquadFilter());
      f.type = type;
      f.frequency.value = hz;
      f.Q.value = q;
      return f;
    };
    const gain = (v = 0) => {
      const g = add(ctx.createGain());
      g.gain.value = v;
      return g;
    };

    // the bus: a limiter so that the loudest passage (a rush of wind at the top speed) cannot clip, then out
    const bus = gain(0);
    const limiter = add(ctx.createDynamicsCompressor());
    limiter.threshold.value = -14;
    limiter.knee.value = 12;
    limiter.ratio.value = 6;
    limiter.attack.value = 0.004;
    limiter.release.value = 0.15;
    bus.connect(limiter);
    limiter.connect(out);

    const whineSrc = loop(loops.whine, 1);
    const whineCut = filter('lowpass', 3000);
    const whineGain = gain();
    whineSrc.connect(whineCut);
    whineCut.connect(whineGain);
    whineGain.connect(bus);

    const partsSrc = loop(loops.whine, 1.5);
    const partsGain = gain();
    partsSrc.connect(partsGain);
    partsGain.connect(bus);

    const bedSrc = loop(loops.bed, 1);
    const bedCut = filter('lowpass', 1500);
    const bedGain = gain();
    bedSrc.connect(bedCut);
    bedCut.connect(bedGain);
    bedGain.connect(bus);

    // the hiss twice, a little apart in pitch and in the ears, so its short loop does not show
    const hissOf = (rate: number, pan: number) => {
      const src = loop(loops.hiss, rate);
      const hp = filter('highpass', 500);
      const g = gain();
      src.connect(hp);
      hp.connect(g);
      if (typeof ctx.createStereoPanner === 'function') {
        const p = add(ctx.createStereoPanner());
        p.pan.value = pan;
        g.connect(p);
        p.connect(bus);
      } else {
        g.connect(bus);
      }
      return { src, gain: g };
    };
    const hissL = hissOf(1, -0.6);
    const hissR = hissOf(1.037, 0.6);

    const at = ctx.currentTime;
    const offset = (buf: AudioBuffer) => (this.random ? Math.random() * buf.duration : 0);
    whineSrc.start(at, offset(loops.whine));
    partsSrc.start(at, offset(loops.whine));
    bedSrc.start(at, offset(loops.bed));
    hissL.src.start(at, offset(loops.hiss));
    hissR.src.start(at, offset(loops.hiss));

    return {
      bus,
      sources,
      whine: { src: whineSrc, gain: whineGain, cut: whineCut },
      parts: { src: partsSrc, gain: partsGain },
      bed: { src: bedSrc, gain: bedGain, cut: bedCut },
      hissL,
      hissR,
      nodes,
    };
  }

  /** Eases every setting toward the current mix, from time `t` on the context's clock. */
  private apply(t: number) {
    const g = this.graph;
    if (!g) return;
    const m = this.mix;
    const ease = (p: AudioParam, v: number, tc: number) => {
      p.cancelScheduledValues(t);
      p.setTargetAtTime(Number.isFinite(v) ? v : 0, t, tc);
    };
    const k = this.scale;
    // a car at a steady speed is never dead steady: its pitch and level drift a little (a few tenths of a percent, a few percent),
    // which also hides the loops' repeat. Slow sines of unrelated periods, so it does not itself repeat
    const wob = (hz: number, phase: number, amount: number) => 1 + amount * Math.sin(2 * Math.PI * hz * t + phase);
    const pitchDrift = wob(0.31, 0, 0.005) * wob(0.83, 1.7, 0.003);
    // muted by the visitor: the whole motor goes quiet (the loops keep turning, so the sound comes back in place)
    const near = this.proximity;
    ease(g.bus.gain, soundOn() ? LEVEL * near * near : 0, 0.06);
    ease(g.whine.src.playbackRate, m.whineRate * k * pitchDrift, TC_RATE);
    ease(g.parts.src.playbackRate, m.whineRate * k * pitchDrift * (this.voice.parts?.ratio ?? 1.5), TC_RATE);
    ease(g.bed.src.playbackRate, m.bedRate * k, TC_RATE);
    ease(g.hissL.src.playbackRate, m.hissRate * k, TC_RATE);
    ease(g.hissR.src.playbackRate, m.hissRate * k * 1.037, TC_RATE);
    ease(g.whine.gain.gain, m.whine * wob(0.17, 2, 0.05), TC_LEVEL);
    ease(g.parts.gain.gain, m.parts * wob(0.21, 0.5, 0.06), TC_LEVEL);
    ease(g.bed.gain.gain, m.bed * wob(0.11, 4, 0.04), TC_LEVEL);
    ease(g.hissL.gain.gain, m.hiss * wob(0.23, 1, 0.08), TC_LEVEL);
    ease(g.hissR.gain.gain, m.hiss * wob(0.19, 3, 0.08), TC_LEVEL);
    ease(g.whine.cut.frequency, m.whineCut * (0.35 + 0.65 * near), TC_CUT);
    ease(g.bed.cut.frequency, m.bedCut * (0.5 + 0.5 * near), TC_CUT);
  }
}

function sharedTarget(): Target | null {
  const a = sharedAudio();
  return a ? { ctx: a.ctx, out: a.master } : null;
}

/** Dev only: window.__driveSound, to render a run's sound offline and look at it (see docs/tech-showcase.md, the Drive tab's sound). */
if (typeof window !== 'undefined' && process.env.NODE_ENV !== 'production') {
  (window as unknown as { __driveSound?: unknown }).__driveSound = { DriveEngine, decodeDriveLoops, driveMix, voiceOf };
}
