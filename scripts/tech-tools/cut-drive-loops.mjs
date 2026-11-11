// Cuts the Drive tab's three engine loops out of the owner's recordings (supplied 2026-11-11) into public/sounds/drive/*.wav:
//   whine  EV-drive-SU7-2.mp3: the motor tone of an SU7 at a steady speed (a fundamental near 410 Hz and its partials)
//   bed    freesound electric-car-51375.mp3: the cabin and road drone of a long steady drive
//   hiss   freesound nissan-leaf-106184.mp3: the colour of the wind and tyre noise that swells as the car gets going
//   node scripts/tech-tools/cut-drive-loops.mjs [whine.mp3] [bed.mp3] [hiss.mp3]
// The whine and the bed are stretches where the recording is steady, levelled (its slow swells are divided out, so the loop does not
// pulse), and closed on itself: the last X seconds are cross-faded onto the first X from a length picked where the two ends match best,
// so the wrap is not a click. The hiss is NOT a stretch of the Leaf recording: a 1.3 s loop of it repeated audibly (measured on the
// mixed output: its envelope correlated at 0.76 with itself 1.26 s later) and carried a whistle near 2.6 kHz that reads as metallic.
// It is noise made to the Leaf's spectral envelope (peaks and ticks taken out), 8 s long, so it has neither. They are WAV on purpose:
// an MP3 carries an encoder delay that opens a gap in a loop.
// Needs ffmpeg on the PATH.
import { execFileSync } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url)).split(String.fromCharCode(92)).join('/').replace(/[/]$/, '');
const out = `${root}/public/sounds/drive`;
mkdirSync(out, { recursive: true });
const SR = 24000;
const home = process.env.USERPROFILE?.split(String.fromCharCode(92)).join('/') ?? '';
const [whineIn = `${home}/Downloads/EV-drive-SU7-2.mp3`, bedIn = `${home}/Downloads/freesound_community-005109_electric-car-51375.mp3`, hissIn = `${home}/Downloads/freesound_community-nissan-leaf-106184.mp3`] =
  process.argv.slice(2);

function decode(file) {
  const raw = execFileSync('ffmpeg', ['-v', 'error', '-i', file, '-ac', '1', '-ar', String(SR), '-f', 'f32le', '-'], { maxBuffer: 1 << 30 });
  return new Float32Array(raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.byteLength));
}

/** Divides out a recording's slow swells: the output's short-time level follows `target` instead. */
function level(x, windowS, target) {
  const w = Math.round(windowS * SR);
  const sq = new Float64Array(x.length + 1);
  for (let i = 0; i < x.length; i++) sq[i + 1] = sq[i] + x[i] * x[i];
  const y = new Float32Array(x.length);
  for (let i = 0; i < x.length; i++) {
    const a = Math.max(0, i - (w >> 1));
    const b = Math.min(x.length, i + (w >> 1));
    const env = Math.sqrt((sq[b] - sq[a]) / (b - a)) + 1e-6;
    y[i] = x[i] * Math.min(2.5, Math.max(0.4, target / env));
  }
  return y;
}

/** One-pole high-pass: takes the DC and the infrasound a recording carries out of a loop. */
function highpass(x, hz) {
  const a = Math.exp((-2 * Math.PI * hz) / SR);
  const y = new Float32Array(x.length);
  let px = 0;
  let py = 0;
  for (let i = 0; i < x.length; i++) {
    py = a * (py + x[i] - px);
    px = x[i];
    y[i] = py;
  }
  return y;
}

const rms = (x) => Math.sqrt(x.reduce((s, v) => s + v * v, 0) / x.length);

/** A copy at 1/d of the rate (a box average first), for a quick search. */
function decimate(x, d) {
  const y = new Float32Array(Math.floor(x.length / d));
  for (let i = 0; i < y.length; i++) {
    let s = 0;
    for (let k = 0; k < d; k++) s += x[i * d + k];
    y[i] = s / d;
  }
  return y;
}

/** The loop length (samples) near `nominal` at which the X samples after it best repeat the first X: the normalised correlation. */
function bestLength(r, nominal, spread, X, d) {
  const lo = decimate(r, d);
  const Xd = Math.floor(X / d);
  const head = lo.subarray(0, Xd);
  let eh = 0;
  for (let i = 0; i < Xd; i++) eh += head[i] * head[i];
  let best = { c: -2, L: nominal };
  const from = Math.floor((nominal - spread) / d);
  const to = Math.floor((nominal + spread) / d);
  for (let Ld = from; Ld <= to; Ld++) {
    if (Ld * d + X > r.length) break;
    let dot = 0;
    let et = 0;
    for (let i = 0; i < Xd; i++) {
      dot += head[i] * lo[Ld + i];
      et += lo[Ld + i] * lo[Ld + i];
    }
    const c = dot / Math.sqrt(eh * et + 1e-12);
    if (c > best.c) best = { c, L: Ld * d };
  }
  // refine at full rate
  let fine = { c: -2, L: best.L };
  let eh2 = 0;
  for (let i = 0; i < X; i++) eh2 += r[i] * r[i];
  for (let L = best.L - d; L <= best.L + d; L++) {
    if (L + X > r.length) break;
    let dot = 0;
    let et = 0;
    for (let i = 0; i < X; i++) {
      dot += r[i] * r[L + i];
      et += r[L + i] * r[L + i];
    }
    const c = dot / Math.sqrt(eh2 * et + 1e-12);
    if (c > fine.c) fine = { c, L };
  }
  return fine;
}

/**
 * Closes a stretch into a loop of L samples: out[i<X] fades the tail (r[L+i]) out and the head (r[i]) in, the rest is r[i].
 * The fade holds the level constant for ends that correlate by `rho` (1: the same wave, as in a pure tone; 0: unrelated, as in
 * noise): a plain linear fade would dip by 3 dB at its middle for noise, and a sine fade swell by 3 dB for a tone.
 */
function closeLoop(r, L, X, rho) {
  const o = new Float32Array(L);
  for (let i = 0; i < L; i++) o[i] = r[i];
  const c = Math.max(0, Math.min(1, rho));
  for (let i = 0; i < X; i++) {
    const phi = ((i + 0.5) / X) * (Math.PI / 2);
    const k = 1 / Math.sqrt(1 + c * Math.sin(2 * phi));
    o[i] = r[i] * Math.sin(phi) * k + r[L + i] * Math.cos(phi) * k;
  }
  return o;
}

function wav(x) {
  const n = x.length;
  const buf = Buffer.alloc(44 + n * 2);
  buf.write('RIFF', 0);
  buf.writeUInt32LE(36 + n * 2, 4);
  buf.write('WAVEfmt ', 8);
  buf.writeUInt32LE(16, 16);
  buf.writeUInt16LE(1, 20);
  buf.writeUInt16LE(1, 22);
  buf.writeUInt32LE(SR, 24);
  buf.writeUInt32LE(SR * 2, 28);
  buf.writeUInt16LE(2, 32);
  buf.writeUInt16LE(16, 34);
  buf.write('data', 36);
  buf.writeUInt32LE(n * 2, 40);
  for (let i = 0; i < n; i++) buf.writeInt16LE(Math.max(-32768, Math.min(32767, Math.round(x[i] * 32767))), 44 + i * 2);
  return buf;
}

/** How steady a stretch is: the spread of its 0.25 s levels in dB, and its worst 40 ms peak over its average level. */
function steadiness(x) {
  const w = Math.round(0.25 * SR);
  const lv = [];
  for (let i = 0; i + w <= x.length; i += w) lv.push(20 * Math.log10(rms(x.subarray(i, i + w)) + 1e-9));
  const mean = lv.reduce((s, v) => s + v, 0) / lv.length;
  const sd = Math.sqrt(lv.reduce((s, v) => s + (v - mean) ** 2, 0) / lv.length);
  const w2 = Math.round(0.04 * SR);
  let worst = 0;
  for (let i = 0; i + w2 <= x.length; i += w2) worst = Math.max(worst, rms(x.subarray(i, i + w2)));
  return { sd, crest: 20 * Math.log10(worst / rms(x)) };
}

/** in-place radix-2 FFT */
function fft(re, im) {
  const n = re.length;
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) {
      [re[i], re[j]] = [re[j], re[i]];
      [im[i], im[j]] = [im[j], im[i]];
    }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = (-2 * Math.PI) / len;
    const wr = Math.cos(ang);
    const wi = Math.sin(ang);
    for (let i = 0; i < n; i += len) {
      let cr = 1;
      let ci = 0;
      for (let k = 0; k < len / 2; k++) {
        const a = i + k;
        const b = a + len / 2;
        const tr = re[b] * cr - im[b] * ci;
        const ti = re[b] * ci + im[b] * cr;
        re[b] = re[a] - tr;
        im[b] = im[a] - ti;
        re[a] += tr;
        im[a] += ti;
        const nr = cr * wr - ci * wi;
        ci = cr * wi + ci * wr;
        cr = nr;
      }
    }
  }
}

/**
 * The spectral envelope of a stretch of a recording, N/2 + 1 magnitudes: the average over Hann frames, with the narrow peaks taken out
 * (a median over about a tenth of an octave rejects a whistle three bins wide) and the rest smoothed over a fifth of an octave.
 */
function envelopeOf(x, N) {
  const mag = new Float64Array(N / 2 + 1);
  const win = new Float32Array(N).map((_, i) => 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / N));
  let frames = 0;
  for (let s = 0; s + N <= x.length; s += N / 4) {
    const re = new Float32Array(N);
    const im = new Float32Array(N);
    for (let i = 0; i < N; i++) re[i] = x[s + i] * win[i];
    fft(re, im);
    for (let k = 0; k <= N / 2; k++) mag[k] += re[k] * re[k] + im[k] * im[k];
    frames++;
  }
  for (let k = 0; k <= N / 2; k++) mag[k] = Math.sqrt(mag[k] / frames);
  const med = new Float64Array(mag.length);
  for (let k = 0; k < mag.length; k++) {
    const h = Math.max(5, Math.round(k * 0.055));
    const w = [];
    for (let j = Math.max(0, k - h); j <= Math.min(mag.length - 1, k + h); j++) w.push(mag[j]);
    w.sort((p, q) => p - q);
    med[k] = w[w.length >> 1];
  }
  const out = new Float64Array(mag.length);
  for (let k = 0; k < mag.length; k++) {
    const h = Math.max(3, Math.round(k * 0.1));
    let sum = 0;
    let n = 0;
    for (let j = Math.max(0, k - h); j <= Math.min(mag.length - 1, k + h); j++) {
      sum += Math.log(med[j] + 1e-9);
      n++;
    }
    out[k] = Math.exp(sum / n);
  }
  return out;
}

/** Gaussian white noise, seeded (Box-Muller over a small LCG). */
function whiteNoise(n, seed) {
  let a = seed >>> 0 || 1;
  const u = () => {
    a = (Math.imul(a, 1664525) + 1013904223) >>> 0;
    return (a + 0.5) / 4294967296;
  };
  const x = new Float32Array(n);
  for (let i = 0; i < n; i += 2) {
    const r = Math.sqrt(-2 * Math.log(u()));
    const t = 2 * Math.PI * u();
    x[i] = r * Math.cos(t);
    if (i + 1 < n) x[i + 1] = r * Math.sin(t);
  }
  return x;
}

/** White noise shaped to a spectral envelope (given at `envN`-point resolution), by short-time filtering with 75 % overlapped Hann frames. */
function shapeNoise(white, env, envN, N = 2048) {
  const hop = N / 4;
  const out = new Float32Array(white.length);
  const win = new Float32Array(N).map((_, i) => 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / N));
  const H = new Float64Array(N / 2 + 1);
  for (let k = 0; k <= N / 2; k++) H[k] = env[Math.min(env.length - 1, Math.round((k * envN) / N))];
  for (let s = 0; s + N <= white.length; s += hop) {
    const re = new Float32Array(N);
    const im = new Float32Array(N);
    for (let i = 0; i < N; i++) re[i] = white[s + i] * win[i];
    fft(re, im);
    for (let k = 0; k <= N / 2; k++) {
      re[k] *= H[k];
      im[k] *= H[k];
      if (k > 0 && k < N / 2) {
        re[N - k] = re[k];
        im[N - k] = -im[k];
      }
    }
    // inverse by conjugation
    for (let k = 0; k < N; k++) im[k] = -im[k];
    fft(re, im);
    for (let i = 0; i < N; i++) out[s + i] += (re[i] / N) * win[i];
  }
  return out;
}

/** A loop of noise in the colour of `src` between `from` and `to` seconds: no tone, no tick, no short repeat. */
function makeNoise(name, src, { from, to, loopS, fadeS, targetDb, hpHz, seed }) {
  const N = 4096;
  const envelope = envelopeOf(src.subarray(Math.round(from * SR), Math.round(to * SR)), N);
  const X = Math.round(fadeS * SR);
  const L = Math.round(loopS * SR);
  const white = whiteNoise(L + X + 4096, seed);
  const shaped = shapeNoise(white, envelope, N).subarray(2048, 2048 + L + X);
  const loop = closeLoop(highpass(shaped, hpHz), L, X, 0);
  const g = Math.pow(10, targetDb / 20) / rms(loop);
  const final = new Float32Array(L);
  for (let i = 0; i < L; i++) final[i] = loop[i] * g;
  const peak = final.reduce((m, v) => Math.max(m, Math.abs(v)), 0);
  writeFileSync(`${out}/${name}.wav`, wav(final));
  const lo = envelope.reduce((m, v, k) => (k > 20 ? Math.min(m, v) : m), 1e9);
  const hi = envelope.reduce((m, v) => Math.max(m, v), 0);
  console.log(
    `${name.padEnd(6)} noise to the envelope of ${from}-${to} s  length ${(L / SR).toFixed(2)} s  rms ${(20 * Math.log10(rms(final))).toFixed(1)} dB  peak ${(20 * Math.log10(peak)).toFixed(1)} dB  envelope span ${(20 * Math.log10(hi / lo)).toFixed(0)} dB  ${((final.length * 2) / 1024).toFixed(0)} KB`,
  );
}

function make(name, src, { from, loopS, fadeS, spreadS, levelWindowS, targetDb, hpHz, decimateBy, scan }) {
  const X = Math.round(fadeS * SR);
  const nominal = Math.round(loopS * SR);
  const spread = Math.round(spreadS * SR);
  let start = from;
  if (scan) {
    // the steadiest stretch in a range: the long recording has a ramp-up and a fade-out at its ends and a few bumps between
    let best = { score: 1e9, t: from };
    for (let t = scan.from; t <= scan.to; t += scan.step) {
      const seg = src.subarray(Math.round(t * SR), Math.round((t + loopS + fadeS + spreadS) * SR));
      const s = steadiness(seg);
      const score = s.sd + 0.5 * s.crest;
      if (score < best.score) best = { score, t };
    }
    start = best.t;
  }
  const a = Math.round(start * SR);
  let r = src.subarray(a, a + nominal + spread + X + 2 * (decimateBy ?? 1)).slice();
  r = highpass(level(r, levelWindowS, Math.pow(10, targetDb / 20)), hpHz);
  const { c, L } = bestLength(r, nominal, spread, X, decimateBy ?? 4);
  const loop = closeLoop(r, L, X, c);
  // the wrap against the loop's own step size: out[L-1] -> out[0] should look like any other step
  const steps = [];
  for (let i = 1; i < L; i++) steps.push(Math.abs(loop[i] - loop[i - 1]));
  steps.sort((p, q) => p - q);
  const wrap = Math.abs(loop[0] - loop[L - 1]);
  const p99 = steps[Math.floor(steps.length * 0.99)];
  const final = new Float32Array(L);
  const g = Math.pow(10, targetDb / 20) / rms(loop);
  for (let i = 0; i < L; i++) final[i] = loop[i] * g;
  const peak = final.reduce((m, v) => Math.max(m, Math.abs(v)), 0);
  writeFileSync(`${out}/${name}.wav`, wav(final));
  console.log(
    `${name.padEnd(6)} from ${start.toFixed(2)} s  length ${(L / SR).toFixed(3)} s  match ${c.toFixed(3)}  wrap step ${(wrap / p99).toFixed(2)}x the 99th-percentile step  rms ${(20 * Math.log10(rms(final))).toFixed(1)} dB  peak ${(20 * Math.log10(peak)).toFixed(1)} dB  ${(final.length * 2 / 1024).toFixed(0)} KB`,
  );
}

make('whine', decode(whineIn), { from: 1.2, loopS: 2.2, fadeS: 0.4, spreadS: 0.25, levelWindowS: 0.3, targetDb: -22, hpHz: 60, decimateBy: 2 });
make('bed', decode(bedIn), {
  from: 100,
  loopS: 10,
  fadeS: 2,
  spreadS: 1,
  levelWindowS: 1.5,
  targetDb: -22,
  hpHz: 28,
  decimateBy: 8,
  scan: { from: 100, to: 190, step: 2 },
});
makeNoise('hiss', decode(hissIn), { from: 6.4, to: 8.3, loopS: 8, fadeS: 1.5, targetDb: -23, hpHz: 200, seed: 20261111 });
