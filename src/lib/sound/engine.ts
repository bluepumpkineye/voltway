import type { OpeningId } from '@/data/vehicles/schema';
import type { Cue, Part } from './cues';

/**
 * Plays the openings' sounds through the Web Audio API, and holds the visitor's choice to hear them or not.
 *
 * The sounds are the owner's recordings of a car door (public/sounds, cut from the three files supplied on 2026-10-21 by
 * scripts/tech-tools/cut-sounds.mjs): two takes of a door being opened (the handle, then the door coming off its seal) and three of
 * it being shut. The bonnet and the tailgate use the same takes pitched down, as the owner said they may: a lower, longer thud reads
 * as a heavier lid. The end of an opening swing and the charge flap have no recording and stay silent.
 *
 * Browsers keep an audio context silent until the page has been touched, so the context is made on the first press or key, which is
 * also what opens a door; the recordings are fetched when the page loads and decoded then. A cue that comes before that is dropped,
 * not held and played late.
 */

/** which part makes the noise when this opening moves */
export const PART_OF: Record<OpeningId, Part> = {
  doorFL: 'door',
  doorFR: 'door',
  doorRL: 'door',
  doorRR: 'door',
  frunk: 'hood',
  boot: 'tailgate',
  charge: 'flap',
};

type Kind = 'open' | 'shut';

const FILES: Record<Kind, string[]> = {
  open: ['/sounds/door-open-1.wav', '/sounds/door-open-2.wav'],
  shut: ['/sounds/door-shut-1.wav', '/sounds/door-shut-2.wav', '/sounds/door-shut-3.wav'],
};

/** what each cue plays: the stop at the end of a swing has no recording of its own */
const KIND_OF: Record<Cue, Kind | null> = { release: 'open', stop: null, shut: 'shut' };

/** how each part sounds: its pitch (the recordings' own is a car door's) and level; null makes no noise */
const SOUND: Record<Part, { rate: number; level: number } | null> = {
  door: { rate: 1, level: 1 },
  hood: { rate: 0.86, level: 1 },
  tailgate: { rate: 0.93, level: 1 },
  flap: null,
};

const KEY = 'voltway.sound';

let on = true;
let loaded = false;
const listeners = new Set<() => void>();

function load() {
  if (loaded || typeof window === 'undefined') return;
  loaded = true;
  try {
    if (window.localStorage.getItem(KEY) === '0') on = false;
  } catch {
    // storage can be blocked: the sound stays on for this visit
  }
}

export function soundOn(): boolean {
  load();
  return on;
}

export function setSoundOn(v: boolean) {
  load();
  if (v === on) return;
  on = v;
  try {
    window.localStorage.setItem(KEY, v ? '1' : '0');
  } catch {
    // not remembered, still honoured for this visit
  }
  if (v) wake();
  for (const fn of listeners) fn();
}

export function subscribeSound(fn: () => void) {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}

interface Audio {
  ctx: AudioContext;
  master: GainNode;
}
let audio: Audio | null = null;

/** the recordings as fetched (no audio context is needed for that), and as decoded once there is one */
const raw = new Map<string, Promise<ArrayBuffer | null>>();
const decoded = new Map<Kind, AudioBuffer[]>();
let decoding: Promise<void> | null = null;

function prefetch() {
  if (typeof window === 'undefined' || raw.size) return;
  for (const file of Object.values(FILES).flat()) {
    raw.set(
      file,
      fetch(file)
        .then((r) => (r.ok ? r.arrayBuffer() : null))
        .catch(() => null),
    );
  }
}

/** Decode every recording once; resolves when they are ready (a recording that failed to load or decode is simply missing). */
function decodeAll(a: Audio): Promise<void> {
  decoding ??= (async () => {
    for (const kind of Object.keys(FILES) as Kind[]) {
      const list: AudioBuffer[] = [];
      for (const file of FILES[kind]) {
        const bytes = await raw.get(file);
        if (!bytes) continue;
        try {
          list.push(await a.ctx.decodeAudioData(bytes.slice(0)));
        } catch {
          // not a sound this browser can decode: left out
        }
      }
      decoded.set(kind, list);
    }
  })();
  return decoding;
}

function make(): Audio | null {
  if (audio) return audio;
  if (typeof window === 'undefined') return null;
  const Ctx = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!Ctx) return null;
  try {
    const ctx = new Ctx();
    const master = ctx.createGain();
    master.gain.value = 0.85;
    master.connect(ctx.destination);
    audio = { ctx, master };
  } catch {
    return null;
  }
  void decodeAll(audio);
  return audio;
}

/** Make the context and wake it: called from a press or a key, which is when a browser lets it start. */
function wake() {
  const a = make();
  if (a && a.ctx.state === 'suspended') void a.ctx.resume().catch(() => {});
}

if (typeof window !== 'undefined') {
  prefetch();
  const first = () => {
    window.removeEventListener('pointerdown', first, true);
    window.removeEventListener('keydown', first, true);
    load();
    if (on) wake();
  };
  window.addEventListener('pointerdown', first, true);
  window.addEventListener('keydown', first, true);
}

export interface CueOptions {
  /** -1 (left) to 1 (right): where the part is in the picture */
  pan?: number;
  /** 0 to 1: how near the camera is to it (louder when near) */
  near?: number;
  /** heard from inside the car: duller and a little quieter */
  inside?: boolean;
}

/** when the last few cues started, so that a car shut all at once (six parts) is not six times as loud */
const recent: number[] = [];
const lastOf = new Map<string, number>();
/** the take each kind played last, so that the same one is not heard twice running */
const lastTake = new Map<Kind, number>();

/** how long a cue may wait for the recordings to be decoded before it is dropped, ms */
const STALE_MS = 300;

/** Play one cue now. Silent when the visitor has turned sound off, the part has no sound, or the browser has not yet let audio start. */
export function playCue(part: Part, cue: Cue, opts: CueOptions = {}) {
  load();
  if (!on) return;
  const sound = SOUND[part];
  const kind = KIND_OF[cue];
  if (!sound || !kind) return;
  const a = make();
  if (!a) return;
  if (a.ctx.state === 'suspended') void a.ctx.resume().catch(() => {});
  if (a.ctx.state !== 'running') return;

  const born = performance.now();
  const go = () => {
    if (performance.now() - born > STALE_MS) return;
    const takes = decoded.get(kind) ?? [];
    if (!takes.length) return;

    const now = a.ctx.currentTime;
    const key = `${part}.${cue}`;
    // the same cue twice in a few milliseconds (a scrubbed demo, a double press) is one noise
    if (now - (lastOf.get(key) ?? -1) < 0.07) return;
    lastOf.set(key, now);
    while (recent.length && now - recent[0] > 0.2) recent.shift();
    // cues that pile up are spread over a few hundredths of a second and each made a little quieter
    const queue = Math.min(recent.length, 5);
    const at = now + queue * 0.045 + 0.005;
    recent.push(now);

    // another take than the last, when there is one
    let i = Math.floor(Math.random() * takes.length);
    if (takes.length > 1 && i === lastTake.get(kind)) i = (i + 1) % takes.length;
    lastTake.set(kind, i);

    const src = a.ctx.createBufferSource();
    src.buffer = takes[i];
    // no two are exactly alike
    src.playbackRate.value = sound.rate * (0.97 + Math.random() * 0.06);

    const gain = a.ctx.createGain();
    const near = opts.near ?? 0.8;
    gain.gain.value = (sound.level * (0.45 + 0.55 * near) * (opts.inside ? 0.6 : 1)) / Math.sqrt(1 + queue * 0.6);

    let tail: AudioNode = src;
    if (opts.inside) {
      // the cabin: the same sound through the shell, lows and a dull middle only
      const f = a.ctx.createBiquadFilter();
      f.type = 'lowpass';
      f.frequency.value = 1400;
      f.Q.value = 0.5;
      tail.connect(f);
      tail = f;
    }
    tail.connect(gain);
    let out: AudioNode = gain;
    if (!opts.inside && typeof a.ctx.createStereoPanner === 'function') {
      const p = a.ctx.createStereoPanner();
      p.pan.value = Math.max(-0.85, Math.min(0.85, opts.pan ?? 0));
      gain.connect(p);
      out = p;
    }
    out.connect(a.master);
    src.start(at);
    src.onended = () => {
      src.disconnect();
      out.disconnect();
    };
  };

  if (decoded.size === Object.keys(FILES).length) go();
  else void decodeAll(a).then(go);
}
