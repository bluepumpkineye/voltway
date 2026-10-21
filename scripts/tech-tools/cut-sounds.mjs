// Cuts the showroom's door sounds (public/sounds/*.wav) out of the three recordings the owner supplied (2026-10-21):
//   open-car-door.mp3                 1.10 s  a handle click (0.27 s), then the door popping open (0.48 s)
//   car-door-shut.mp3                 0.47 s  one shut: the impact is 0.03 s in
//   car-door-closing-and-opening.mp3  7.54 s  a shut (0.75 s), the handle and the door opening (3.0 s), a second shut (5.0 s)
// Each excerpt is decoded with ffmpeg, mixed to mono at 44.1 kHz, trimmed with a short fade in and a longer fade out so that
// nothing clicks, and scaled so its peak is the same for every cue of a kind (a shut is louder than an opening). The cut
// points were read off the recordings' loudness envelopes (the first sound of each excerpt is the one the animation cues).
//
//   node scripts/tech-tools/cut-sounds.mjs <folder holding the three mp3 files> [out folder, default public/sounds]
import { spawnSync } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url)).split(String.fromCharCode(92)).join('/');
const from = process.argv[2];
const out = process.argv[3] ?? `${root}public/sounds`;
if (!from) {
  console.error('usage: node scripts/tech-tools/cut-sounds.mjs <folder with the three mp3 files> [out folder]');
  process.exit(1);
}
const SR = 44100;

/** name, source, from s, to s, peak (0 to 1) */
const CUTS = [
  ['open-1', 'open-car-door.mp3', 0.14, 0.92, 0.7],
  ['open-2', 'car-door-closing-and-opening.mp3', 2.86, 3.6, 0.7],
  ['shut-1', 'car-door-shut.mp3', 0.0, 0.36, 0.92],
  ['shut-2', 'car-door-closing-and-opening.mp3', 0.72, 1.3, 0.92],
  ['shut-3', 'car-door-closing-and-opening.mp3', 4.93, 5.5, 0.92],
];

function decode(file) {
  const r = spawnSync(process.env.FFMPEG ?? 'ffmpeg', ['-v', 'error', '-i', file, '-ac', '1', '-ar', String(SR), '-f', 'f32le', '-'], { maxBuffer: 1 << 28 });
  if (r.status !== 0) throw new Error(`ffmpeg failed on ${file}: ${r.stderr}`);
  return new Float32Array(r.stdout.buffer, r.stdout.byteOffset, Math.floor(r.stdout.byteLength / 4));
}

function wav(samples) {
  const n = samples.length;
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
  for (let i = 0; i < n; i++) buf.writeInt16LE(Math.max(-32768, Math.min(32767, Math.round(samples[i] * 32767))), 44 + i * 2);
  return buf;
}

mkdirSync(out, { recursive: true });
const cache = new Map();
for (const [name, src, t0, t1, peak] of CUTS) {
  if (!cache.has(src)) cache.set(src, decode(`${from}/${src}`));
  const all = cache.get(src);
  const a = Math.max(0, Math.round(t0 * SR));
  const b = Math.min(all.length, Math.round(t1 * SR));
  const x = Float32Array.from(all.subarray(a, b));
  // fade in over 4 ms (an excerpt that starts on an impact keeps its first sample), out over 60 ms
  const fi = Math.round(0.004 * SR);
  const fo = Math.round(0.06 * SR);
  for (let i = 0; i < fi && i < x.length; i++) x[i] *= i / fi;
  for (let i = 0; i < fo && i < x.length; i++) x[x.length - 1 - i] *= i / fo;
  let m = 0;
  for (const v of x) m = Math.max(m, Math.abs(v));
  const k = m > 0 ? peak / m : 1;
  for (let i = 0; i < x.length; i++) x[i] *= k;
  writeFileSync(`${out}/door-${name}.wav`, wav(x));
  console.log(`door-${name}.wav  ${(x.length / SR).toFixed(2)} s  from ${src} ${t0}-${t1} s  gain ${k.toFixed(2)}`);
}
