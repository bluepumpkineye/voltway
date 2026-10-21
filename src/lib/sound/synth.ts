/**
 * The sounds of the car's openings, synthesised: a door, the bonnet, the tailgate and the charge flap, each with three
 * cues (a latch letting go as the part starts to open, the stop at the end of its swing, the thud and latch as it shuts).
 * No recordings are used: every sound is built here from noise, damped sinusoids ("modes" of a panel) and short clicks, so
 * there is nothing to license, download or ship. They are ours and approximate; swapping in recorded samples later is a
 * matter of replacing `render` (src/lib/sound/engine.ts decodes whatever `render` returns).
 *
 * Pure DSP, no browser APIs: it runs under Node too (scratchpad/sound-check.mjs renders every cue to a WAV).
 */

export const SAMPLE_RATE = 44100;

export type Part = 'door' | 'hood' | 'tailgate' | 'flap';
/** release: the part starts to open. stop: it reaches the end of its swing. shut: it closes and latches. */
export type Cue = 'release' | 'stop' | 'shut';

export const PARTS: Part[] = ['door', 'hood', 'tailgate', 'flap'];
export const CUES: Cue[] = ['release', 'stop', 'shut'];

/** A small seeded generator, so a cue is the same every time it is built. */
function rng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

type Filter = (x: Float32Array) => Float32Array;

/** A second-order section (RBJ cookbook), run once over the buffer. */
function biquad(kind: 'lp' | 'hp' | 'bp', f0: number, q: number): Filter {
  return (x) => {
    const w0 = (2 * Math.PI * Math.min(f0, SAMPLE_RATE * 0.45)) / SAMPLE_RATE;
    const cos = Math.cos(w0);
    const alpha = Math.sin(w0) / (2 * q);
    let b0: number, b1: number, b2: number;
    if (kind === 'lp') {
      b0 = (1 - cos) / 2;
      b1 = 1 - cos;
      b2 = (1 - cos) / 2;
    } else if (kind === 'hp') {
      b0 = (1 + cos) / 2;
      b1 = -(1 + cos);
      b2 = (1 + cos) / 2;
    } else {
      b0 = alpha;
      b1 = 0;
      b2 = -alpha;
    }
    const a0 = 1 + alpha;
    const a1 = (-2 * cos) / a0;
    const a2 = (1 - alpha) / a0;
    b0 /= a0;
    b1 /= a0;
    b2 /= a0;
    const y = new Float32Array(x.length);
    let x1 = 0, x2 = 0, y1 = 0, y2 = 0;
    for (let i = 0; i < x.length; i++) {
      const v = b0 * x[i] + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2;
      x2 = x1;
      x1 = x[i];
      y2 = y1;
      y1 = v;
      y[i] = v;
    }
    return y;
  };
}

const lp = (f: number, q = 0.707): Filter => biquad('lp', f, q);
const hp = (f: number, q = 0.707): Filter => biquad('hp', f, q);
const bp = (f: number, q: number): Filter => biquad('bp', f, q);
const chain = (...fs: Filter[]): Filter => (x) => fs.reduce((v, f) => f(v), x);

class Voice {
  readonly data: Float32Array;
  private readonly rnd: () => number;
  constructor(seconds: number, seed: number) {
    this.data = new Float32Array(Math.ceil(seconds * SAMPLE_RATE));
    this.rnd = rng(seed);
  }

  /** a burst of noise through a filter: it rises over `attack` seconds and dies away with time constant `tau` */
  noise(at: number, dur: number, attack: number, tau: number, gain: number, filter: Filter) {
    const n = Math.min(Math.floor(dur * SAMPLE_RATE), this.data.length - Math.floor(at * SAMPLE_RATE));
    if (n <= 0) return this;
    const x = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      const t = i / SAMPLE_RATE;
      const e = t < attack ? t / attack : Math.exp(-(t - attack) / tau);
      x[i] = (this.rnd() * 2 - 1) * e;
    }
    const y = filter(x);
    const o = Math.floor(at * SAMPLE_RATE);
    for (let i = 0; i < n; i++) this.data[o + i] += y[i] * gain;
    return this;
  }

  /** a damped sinusoid whose pitch glides from f0 to f1 (time constant `glide`) */
  tone(at: number, f0: number, f1: number, glide: number, tau: number, gain: number, attack = 0.0015) {
    const o = Math.floor(at * SAMPLE_RATE);
    const n = Math.min(Math.floor(tau * 7 * SAMPLE_RATE), this.data.length - o);
    let phase = 0;
    for (let i = 0; i < n; i++) {
      const t = i / SAMPLE_RATE;
      const f = f1 + (f0 - f1) * Math.exp(-t / glide);
      phase += (2 * Math.PI * f) / SAMPLE_RATE;
      const e = t < attack ? t / attack : Math.exp(-(t - attack) / tau);
      this.data[o + i] += Math.sin(phase) * e * gain;
    }
    return this;
  }

  /** the modes of a panel or a latch: [frequency Hz, time constant s, gain] */
  modes(at: number, list: [number, number, number][]) {
    for (const [f, tau, g] of list) this.tone(at, f, f, 1, tau, g, 0.0006);
    return this;
  }

  /** peak-normalised, softly limited, with a fade at the very end */
  done(peak: number): Float32Array {
    const d = this.data;
    let m = 0;
    for (let i = 0; i < d.length; i++) m = Math.max(m, Math.abs(d[i]));
    const k = m > 0 ? peak / m : 0;
    const fade = Math.floor(0.012 * SAMPLE_RATE);
    for (let i = 0; i < d.length; i++) {
      const tail = Math.min(1, (d.length - i) / fade);
      d[i] = Math.tanh(d[i] * k * 1.15) * tail;
    }
    return d;
  }
}

/**
 * A latch: two clicks a few milliseconds apart (the striker meeting the catch, then the pawl falling), a short ring.
 * `f` shifts it up or down for a lighter or heavier part.
 */
function latch(c: Voice, at: number, f: number, gain: number) {
  c.noise(at, 0.05, 0.0004, 0.0045, 0.6 * gain, bp(2800 * f, 2.2));
  c.modes(at, [
    [1650 * f, 0.012, 0.2 * gain],
    [2750 * f, 0.008, 0.18 * gain],
    [4100 * f, 0.006, 0.1 * gain],
  ]);
  c.noise(at + 0.034, 0.04, 0.0003, 0.003, 0.4 * gain, bp(3600 * f, 2.5));
  c.modes(at + 0.034, [[2300 * f, 0.01, 0.14 * gain]]);
}

function door(cue: Cue): Float32Array {
  if (cue === 'shut') {
    const c = new Voice(0.55, 11);
    // the air in the cabin and the seal: a short low whump
    c.noise(0, 0.28, 0.002, 0.05, 0.9, chain(lp(700), lp(700)));
    // the body of the door meeting the sill
    c.tone(0, 115, 72, 0.03, 0.075, 0.85);
    c.modes(0, [
      [185, 0.07, 0.22],
      [290, 0.05, 0.18],
      [470, 0.035, 0.12],
      [760, 0.022, 0.08],
    ]);
    latch(c, 0.012, 1, 1);
    // the seal settling
    c.noise(0.02, 0.32, 0.01, 0.09, 0.16, chain(hp(900), lp(5000)));
    return c.done(0.9);
  }
  if (cue === 'release') {
    const c = new Voice(0.42, 12);
    // the handle lets the latch go, the seal lets go of the frame
    c.noise(0, 0.06, 0.0004, 0.005, 0.5, bp(2200, 2));
    c.modes(0, [
      [1400, 0.012, 0.18],
      [2600, 0.008, 0.12],
    ]);
    c.tone(0.004, 160, 120, 0.02, 0.03, 0.3);
    c.noise(0.02, 0.32, 0.02, 0.07, 0.3, chain(lp(3000), hp(300)));
    return c.done(0.7);
  }
  // stop: the door check holds it open
  const c = new Voice(0.28, 13);
  c.tone(0, 150, 110, 0.02, 0.03, 0.35);
  c.noise(0, 0.05, 0.0004, 0.006, 0.35, bp(1800, 2));
  c.modes(0, [[900, 0.02, 0.12]]);
  return c.done(0.55);
}

function hood(cue: Cue): Float32Array {
  if (cue === 'shut') {
    const c = new Voice(0.85, 21);
    c.noise(0, 0.45, 0.003, 0.08, 1, chain(lp(480), lp(480)));
    c.tone(0, 70, 48, 0.05, 0.11, 1);
    c.modes(0, [
      [112, 0.12, 0.35],
      [165, 0.09, 0.28],
      [240, 0.07, 0.2],
      [350, 0.05, 0.14],
      [540, 0.03, 0.08],
    ]);
    // the bonnet's latch is slower and lower than a door's: a clack, then the safety catch
    c.noise(0.03, 0.06, 0.0005, 0.007, 0.6, bp(1500, 1.6));
    c.modes(0.03, [
      [1100, 0.016, 0.22],
      [2100, 0.012, 0.14],
    ]);
    c.noise(0.085, 0.05, 0.0004, 0.004, 0.35, bp(2400, 2));
    return c.done(0.95);
  }
  if (cue === 'release') {
    const c = new Voice(0.9, 22);
    // the release lever and the catch: a pop and a dull knock
    c.noise(0, 0.08, 0.0006, 0.009, 0.65, bp(1100, 1.4));
    c.tone(0, 210, 150, 0.03, 0.035, 0.4);
    // the gas struts take the weight: a faint hiss
    c.noise(0.05, 0.8, 0.08, 0.25, 0.09, bp(2800, 0.8));
    return c.done(0.7);
  }
  const c = new Voice(0.5, 23);
  // the struts reach their stop
  c.tone(0, 95, 70, 0.05, 0.05, 0.55);
  c.modes(0, [
    [640, 0.04, 0.14],
    [1210, 0.025, 0.09],
  ]);
  c.noise(0, 0.15, 0.001, 0.04, 0.35, lp(500));
  return c.done(0.6);
}

function tailgate(cue: Cue): Float32Array {
  if (cue === 'shut') {
    const c = new Voice(0.75, 31);
    c.tone(0, 85, 58, 0.04, 0.1, 0.9);
    c.noise(0, 0.4, 0.003, 0.07, 0.8, chain(lp(600), lp(600)));
    c.modes(0, [
      [135, 0.1, 0.3],
      [210, 0.08, 0.22],
      [330, 0.055, 0.16],
    ]);
    latch(c, 0.03, 0.68, 1);
    // the big seal round the opening
    c.noise(0.03, 0.4, 0.015, 0.12, 0.14, chain(hp(1000), lp(4500)));
    return c.done(0.92);
  }
  if (cue === 'release') {
    const c = new Voice(0.85, 32);
    c.noise(0, 0.06, 0.0005, 0.006, 0.55, bp(1900, 2));
    c.tone(0.002, 180, 130, 0.025, 0.04, 0.35);
    c.noise(0.05, 0.7, 0.08, 0.22, 0.08, bp(2600, 0.8));
    return c.done(0.65);
  }
  const c = new Voice(0.45, 33);
  c.tone(0, 105, 78, 0.05, 0.05, 0.5);
  c.modes(0, [[760, 0.035, 0.12]]);
  c.noise(0, 0.15, 0.001, 0.04, 0.35, lp(700));
  return c.done(0.55);
}

function flap(cue: Cue): Float32Array {
  if (cue === 'release') {
    // a spring flap pops open: a plastic click
    const c = new Voice(0.2, 41);
    c.noise(0, 0.04, 0.0003, 0.004, 0.5, bp(3200, 3));
    c.tone(0, 420, 300, 0.012, 0.015, 0.25);
    return c.done(0.45);
  }
  if (cue === 'stop') {
    const c = new Voice(0.15, 42);
    c.noise(0, 0.03, 0.0003, 0.003, 0.3, bp(2600, 3));
    return c.done(0.3);
  }
  const c = new Voice(0.22, 43);
  c.noise(0, 0.05, 0.0004, 0.006, 0.5, bp(2400, 2.5));
  c.tone(0, 260, 220, 0.02, 0.02, 0.3);
  return c.done(0.45);
}

const BUILDERS: Record<Part, (cue: Cue) => Float32Array> = { door, hood, tailgate, flap };

/** One cue as mono samples at SAMPLE_RATE, peak between 0.3 and 0.95. */
export function render(part: Part, cue: Cue): Float32Array {
  return BUILDERS[part](cue);
}
