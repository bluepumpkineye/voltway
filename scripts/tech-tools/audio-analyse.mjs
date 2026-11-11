// Looks into a recording: level, band energy and the strongest tones per time slice, so a loop can be cut where the sound is steady.
//   node scripts/tech-tools/audio-analyse.mjs <file> [hop-seconds] [from] [to]
// Needs ffmpeg on the PATH (it decodes to 24 kHz mono floats).
import { execFileSync } from 'node:child_process';

const [file, hopArg = '0.5', fromArg = '0', toArg] = process.argv.slice(2);
if (!file) {
  console.log('usage: node scripts/tech-tools/audio-analyse.mjs <file> [hop-seconds] [from] [to]');
  process.exit(1);
}
const SR = 24000;
const raw = execFileSync('ffmpeg', ['-v', 'error', '-i', file, '-ac', '1', '-ar', String(SR), '-f', 'f32le', '-'], { maxBuffer: 1 << 30 });
const x = new Float32Array(raw.buffer, raw.byteOffset, raw.byteLength / 4);
const dur = x.length / SR;
const hop = parseFloat(hopArg);
const from = parseFloat(fromArg);
const to = toArg ? parseFloat(toArg) : dur;

const N = 4096;
const win = new Float32Array(N).map((_, i) => 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / N));

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

const db = (v) => (v > 1e-9 ? 20 * Math.log10(v) : -180);
console.log(`${file}\n${dur.toFixed(2)} s at ${SR} Hz`);
console.log('time   rms dB  <150   150-400  400-1k  1k-3k   >3k    centroid  strongest tones (Hz:dB above the local floor)');
for (let t = from; t + N / SR <= Math.min(to, dur); t += hop) {
  const s0 = Math.round(t * SR);
  const re = new Float32Array(N);
  const im = new Float32Array(N);
  let sq = 0;
  for (let i = 0; i < N; i++) {
    re[i] = x[s0 + i] * win[i];
    sq += x[s0 + i] ** 2;
  }
  fft(re, im);
  const mag = new Float32Array(N / 2);
  for (let k = 0; k < N / 2; k++) mag[k] = Math.hypot(re[k], im[k]);
  const band = (lo, hi) => {
    let e = 0;
    for (let k = Math.floor((lo * N) / SR); k < Math.min(N / 2, Math.floor((hi * N) / SR)); k++) e += mag[k] ** 2;
    return db(Math.sqrt(e) / N);
  };
  let num = 0;
  let den = 0;
  for (let k = 1; k < N / 2; k++) {
    num += ((k * SR) / N) * mag[k];
    den += mag[k];
  }
  // strong narrow tones: local maxima standing out of the median of the 40 bins around them
  const tones = [];
  const kLo = Math.floor((60 * N) / SR);
  const kHi = Math.floor((3500 * N) / SR);
  for (let k = kLo + 20; k < kHi - 20; k++) {
    if (mag[k] < mag[k - 1] || mag[k] < mag[k + 1]) continue;
    const around = Array.from(mag.slice(k - 20, k + 21)).sort((a, b) => a - b);
    const floor = around[20];
    const prom = db(mag[k]) - db(floor);
    if (prom > 12) tones.push({ f: Math.round((k * SR) / N), p: prom });
  }
  tones.sort((a, b) => b.p - a.p);
  const top = tones.slice(0, 4).map((o) => `${o.f}:${o.p.toFixed(0)}`).join(' ');
  console.log(
    t.toFixed(2).padStart(6),
    db(Math.sqrt(sq / N)).toFixed(1).padStart(7),
    band(20, 150).toFixed(0).padStart(6),
    band(150, 400).toFixed(0).padStart(8),
    band(400, 1000).toFixed(0).padStart(7),
    band(1000, 3000).toFixed(0).padStart(7),
    band(3000, 12000).toFixed(0).padStart(6),
    String(Math.round(num / den)).padStart(9),
    ' ',
    top,
  );
}
