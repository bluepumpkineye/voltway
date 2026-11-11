// Narrow persistent tones in a loop (a whistle or ring reads as "metallic"): Welch-averaged long FFT, peaks above their neighbourhood.
//   node scripts/tech-tools/loop-peaks.mjs file.wav [from] [to]   (needs ffmpeg on the PATH)
import { execFileSync } from 'node:child_process';
const [file, fromArg = '0', toArg] = process.argv.slice(2);
const SR = 24000;
const raw = execFileSync('ffmpeg', ['-v', 'error', '-i', file, '-ac', '1', '-ar', String(SR), '-f', 'f32le', '-'], { maxBuffer: 1 << 30 });
const all = new Float32Array(raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.byteLength));
const x = all.subarray(Math.round(parseFloat(fromArg) * SR), toArg ? Math.round(parseFloat(toArg) * SR) : all.length);
const N = 8192;
function fft(re, im) {
  const n = re.length;
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) { [re[i], re[j]] = [re[j], re[i]]; [im[i], im[j]] = [im[j], im[i]]; }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = (-2 * Math.PI) / len, wr = Math.cos(ang), wi = Math.sin(ang);
    for (let i = 0; i < n; i += len) {
      let cr = 1, ci = 0;
      for (let k = 0; k < len / 2; k++) {
        const a = i + k, b = a + len / 2;
        const tr = re[b] * cr - im[b] * ci, ti = re[b] * ci + im[b] * cr;
        re[b] = re[a] - tr; im[b] = im[a] - ti; re[a] += tr; im[a] += ti;
        const nr = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = nr;
      }
    }
  }
}
const win = new Float32Array(N).map((_, i) => 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / N));
const psd = new Float64Array(N / 2);
let frames = 0;
for (let s = 0; s + N <= x.length; s += N / 4) {
  const re = new Float32Array(N), im = new Float32Array(N);
  for (let i = 0; i < N; i++) re[i] = x[s + i] * win[i];
  fft(re, im);
  for (let k = 0; k < N / 2; k++) psd[k] += re[k] * re[k] + im[k] * im[k];
  frames++;
}
const db = (v) => 10 * Math.log10(v / frames / (N * N) + 1e-18);
const med = (arr) => arr.slice().sort((a, b) => a - b)[arr.length >> 1];
const peaks = [];
const binHz = SR / N;
for (let k = Math.round(80 / binHz); k < Math.round(9000 / binHz); k++) {
  if (psd[k] < psd[k - 1] || psd[k] < psd[k + 1]) continue;
  const around = [];
  for (let j = -50; j <= 50; j++) if (Math.abs(j) > 3) around.push(db(psd[k + j]));
  const prom = db(psd[k]) - med(around);
  if (prom > 7) peaks.push({ f: Math.round(k * binHz), prom: +prom.toFixed(1), lvl: +db(psd[k]).toFixed(1) });
}
peaks.sort((a, b) => b.prom - a.prom);
console.log(`${file}  ${(x.length / SR).toFixed(2)} s, ${frames} frames, bin ${binHz.toFixed(2)} Hz`);
console.log('narrow peaks (Hz, prominence dB over the neighbourhood, level):');
console.log(peaks.slice(0, 14).map((p) => `${p.f}Hz +${p.prom}dB (${p.lvl})`).join('\n'));
