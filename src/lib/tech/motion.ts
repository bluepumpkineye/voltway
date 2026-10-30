/**
 * The Drive tab's motion kit: what an animation is, as a pure function of the playhead.
 *
 * The model is Remotion's (https://www.remotion.dev/docs/): a picture is a function of the frame, and nothing keeps a state of
 * its own. An entrance, a count-up, a bar that overshoots and settles are each a value worked out from "seconds since it began",
 * so they play forwards, backwards, paused and scrubbed, and the same run draws the same picture every time. That is why
 * there are no CSS transitions on the data (a transition runs on the browser's clock, not the run's: it lags a scrub and
 * does not play back). Nothing here touches the DOM or three.js, so the Node tests in scripts/tech-tools/motion-test.mjs run it.
 *
 * The helpers (`interpolate`, `spring`, `Easing`) take the names and the shapes of Remotion's. They are written out here, in a
 * few lines, rather than imported: the Remotion package is source-available with its own licence for companies, and the
 * showroom needs only these few functions, not a video renderer.
 */

export const clamp = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));

export type EasingFn = (x: number) => number;

/** The easings the data uses; each takes 0..1 and returns 0..1 (the back easing overshoots 1 on the way). */
export const Easing = {
  linear: ((x) => x) as EasingFn,
  inQuad: ((x) => x * x) as EasingFn,
  outQuad: ((x) => 1 - (1 - x) * (1 - x)) as EasingFn,
  inOutQuad: ((x) => (x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2)) as EasingFn,
  outCubic: ((x) => 1 - Math.pow(1 - x, 3)) as EasingFn,
  inOutCubic: ((x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2)) as EasingFn,
  outExpo: ((x) => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x))) as EasingFn,
  /** the overshoot of an "out back": the value passes 1 by about `s` / 10 and comes home */
  outBack: (s = 1.70158): EasingFn => (x) => 1 + (s + 1) * Math.pow(x - 1, 3) + s * Math.pow(x - 1, 2),
  /** a cubic Bézier through (0,0), (x1,y1), (x2,y2), (1,1): CSS's `cubic-bezier`, solved by bisection */
  bezier:
    (x1: number, y1: number, x2: number, y2: number): EasingFn =>
    (x) => {
      if (x <= 0) return 0;
      if (x >= 1) return 1;
      const at = (a: number, b: number, u: number) => 3 * a * (1 - u) * (1 - u) * u + 3 * b * (1 - u) * u * u + u * u * u;
      let lo = 0;
      let hi = 1;
      for (let i = 0; i < 28; i++) {
        const mid = (lo + hi) / 2;
        if (at(x1, x2, mid) < x) lo = mid;
        else hi = mid;
      }
      return at(y1, y2, (lo + hi) / 2);
    },
};

/** The Expo-out curve designers reach for first: fast off the mark, long settle. */
export const EASE_OUT = Easing.bezier(0.16, 1, 0.3, 1);

export interface InterpolateOptions {
  easing?: EasingFn;
  extrapolateLeft?: 'clamp' | 'extend';
  extrapolateRight?: 'clamp' | 'extend';
}

/**
 * `x` mapped from the ranges in `input` (ascending) to the values in `output`, piece by piece, as Remotion's `interpolate`:
 * the easing shapes each piece, and outside the ends the value is held (`clamp`, the default) or carried on (`extend`).
 */
export function interpolate(x: number, input: readonly number[], output: readonly number[], opts: InterpolateOptions = {}): number {
  const n = input.length;
  if (n < 2 || n !== output.length) throw new Error('interpolate: input and output must be the same length, at least two');
  const { easing = Easing.linear, extrapolateLeft = 'clamp', extrapolateRight = 'clamp' } = opts;
  let i = 0;
  while (i < n - 2 && x > input[i + 1]) i++;
  const a = input[i];
  const b = input[i + 1];
  let u = b === a ? (x < a ? 0 : 1) : (x - a) / (b - a);
  if (u < 0 && extrapolateLeft === 'clamp') u = 0;
  if (u > 1 && extrapolateRight === 'clamp') u = 1;
  // an easing is defined on 0..1; a value that is carried on outside it is carried on in a straight line
  const e = u < 0 || u > 1 ? u : easing(u);
  return output[i] + (output[i + 1] - output[i]) * e;
}

export interface SpringConfig {
  /** Remotion's defaults: mass 1, damping 10, stiffness 100 (a lively spring that overshoots a little) */
  mass?: number;
  damping?: number;
  stiffness?: number;
}

/** A few springs the data uses: a settle with a visible overshoot, a firm one, a soft one that does not overshoot. */
export const SPRINGS = {
  pop: { mass: 1, damping: 11, stiffness: 140 } as SpringConfig,
  firm: { mass: 1, damping: 18, stiffness: 190 } as SpringConfig,
  soft: { mass: 1, damping: 26, stiffness: 120 } as SpringConfig,
  /** a quick rise that settles on its mark with no overshoot to speak of: for type coming out of a mask */
  rise: { mass: 1, damping: 28, stiffness: 260 } as SpringConfig,
};

/**
 * A spring that runs from 0 to 1 from rest, at `t` seconds after it was let go. The closed form of the damped oscillator, so
 * the value at any time is worked out directly (Remotion steps the same equation frame by frame; this lands on the same
 * curve and can be asked for any t, in any order).
 */
export function spring(t: number, cfg: SpringConfig = {}): number {
  if (t <= 0) return 0;
  const { mass = 1, damping = 10, stiffness = 100 } = cfg;
  const w = Math.sqrt(stiffness / mass);
  const z = damping / (2 * Math.sqrt(stiffness * mass));
  if (z < 1) {
    const wd = w * Math.sqrt(1 - z * z);
    return 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + ((z * w) / wd) * Math.sin(wd * t));
  }
  if (z === 1) return 1 - Math.exp(-w * t) * (1 + w * t);
  const s = w * Math.sqrt(z * z - 1);
  const r1 = -z * w + s;
  const r2 = -z * w - s;
  return 1 - (r2 * Math.exp(r1 * t) - r1 * Math.exp(r2 * t)) / (r2 - r1);
}

/** How long a spring takes to come within 1 % of 1 and stay there, s (for fitting an exit or a hold around it). */
export function springDuration(cfg: SpringConfig = {}): number {
  let last = 0;
  for (let t = 0; t < 8; t += 1 / 60) if (Math.abs(spring(t, cfg) - 1) > 0.01) last = t;
  return last + 1 / 60;
}

/** Progress 0..1 of a stretch of time that begins at `from` and lasts `dur`, held at both ends. */
export function progress(t: number, from: number, dur: number): number {
  return dur <= 0 ? (t >= from ? 1 : 0) : clamp((t - from) / dur);
}

export interface Presence {
  /** the entrance, 0..1 (a spring: it overshoots 1 a little) */
  enter: number;
  /** the exit, 0 while it is up and 1 once it has gone (an ease) */
  exit: number;
  /** on screen at all: between the first and the last of its time */
  visible: boolean;
  /** seconds since it came on (0 before) */
  age: number;
}

/**
 * A thing that comes on at `from`, stays, and leaves at `to` (`to` = Infinity: it stays). `enterSpring` shapes the entrance;
 * the exit takes `outDur`.
 */
export function presence(t: number, from: number, to = Infinity, outDur = 0.35, enterSpring: SpringConfig = SPRINGS.pop): Presence {
  const age = Math.max(0, t - from);
  const enter = spring(t - from, enterSpring);
  const exit = to === Infinity ? 0 : Easing.inOutQuad(progress(t, to, outDur));
  return { enter, exit, visible: t >= from && (to === Infinity || t < to + outDur), age };
}

/** `n` things coming on one after another, `gap` seconds apart: the start time of the i-th. */
export const stagger = (from: number, i: number, gap = 0.08) => from + i * gap;

/** A number counting up to its value: `p` is the progress 0..1 (eased out so that the last digits arrive slowly). */
export function countTo(value: number, p: number, from = 0): number {
  return from + (value - from) * EASE_OUT(clamp(p));
}

/** A brief flash: 0 at `at`, up to 1 almost at once, then a smooth decay over `dur`; 0 before and after. */
export function flash(t: number, at: number, dur = 0.6): number {
  const d = t - at;
  if (d < 0 || d > dur) return 0;
  return d < 0.04 ? d / 0.04 : Math.pow(1 - (d - 0.04) / (dur - 0.04), 2);
}

/** Round `x` to the digits a readout shows, as a string with a thousands comma (the figures read at a glance). */
export function fmt(x: number, digits = 0): string {
  const s = Math.abs(x).toFixed(digits);
  const [int, dec] = s.split('.');
  const grouped = int.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  return `${x < 0 && Number(s) !== 0 ? '−' : ''}${grouped}${dec ? `.${dec}` : ''}`;
}
