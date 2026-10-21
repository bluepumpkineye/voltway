// Renders the openings' sounds (src/lib/sound/synth.ts) and prints peak, level, length and brightness; with a folder, writes WAVs.
//   node --no-warnings scripts/tech-tools/sound-check.mjs [out-folder]
import { writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url)).split(String.fromCharCode(92)).join('/').replace(/[/]$/, '');
const { render, SAMPLE_RATE, PARTS, CUES } = await import(pathToFileURL(`${root}/src/lib/sound/synth.ts`).href);

const out = process.argv[2];
if (out) mkdirSync(out, { recursive: true });

function wav(samples) {
  const n = samples.length;
  const buf = Buffer.alloc(44 + n * 2);
  buf.write('RIFF', 0);
  buf.writeUInt32LE(36 + n * 2, 4);
  buf.write('WAVEfmt ', 8);
  buf.writeUInt32LE(16, 16);
  buf.writeUInt16LE(1, 20);
  buf.writeUInt16LE(1, 22);
  buf.writeUInt32LE(SAMPLE_RATE, 24);
  buf.writeUInt32LE(SAMPLE_RATE * 2, 28);
  buf.writeUInt16LE(2, 32);
  buf.writeUInt16LE(16, 34);
  buf.write('data', 36);
  buf.writeUInt32LE(n * 2, 40);
  for (let i = 0; i < n; i++) buf.writeInt16LE(Math.max(-32768, Math.min(32767, Math.round(samples[i] * 32767))), 44 + i * 2);
  return buf;
}

// a crude spectral centroid by DFT over a few frames of the first 120 ms
function centroid(x) {
  const N = 2048;
  const seg = x.slice(0, N);
  let num = 0, den = 0;
  for (let k = 1; k < N / 2; k += 2) {
    let re = 0, im = 0;
    for (let i = 0; i < N; i++) {
      const w = 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / N);
      re += seg[i] * w * Math.cos((2 * Math.PI * k * i) / N);
      im -= seg[i] * w * Math.sin((2 * Math.PI * k * i) / N);
    }
    const m = Math.hypot(re, im);
    num += (k * SAMPLE_RATE / N) * m;
    den += m;
  }
  return den ? num / den : 0;
}

let t0 = Date.now();
for (const part of PARTS) {
  for (const cue of CUES) {
    const x = render(part, cue);
    let peak = 0, sq = 0, nan = 0, over = 0, last = 0;
    for (let i = 0; i < x.length; i++) {
      const a = Math.abs(x[i]);
      if (!Number.isFinite(x[i])) nan++;
      peak = Math.max(peak, a);
      sq += x[i] * x[i];
      if (a > 0.999) over++;
      if (a > 0.01) last = i;
    }
    console.log(
      `${part}.${cue}`.padEnd(16),
      `${(x.length / SAMPLE_RATE).toFixed(2)}s`.padEnd(7),
      `peak ${peak.toFixed(2)}`.padEnd(11),
      `rms ${Math.sqrt(sq / x.length).toFixed(3)}`.padEnd(11),
      `audible to ${(last / SAMPLE_RATE).toFixed(2)}s`.padEnd(20),
      `centroid ${Math.round(centroid(x))} Hz`.padEnd(18),
      `nan ${nan} clip ${over}`,
    );
    if (out) writeFileSync(`${out}/${part}-${cue}.wav`, wav(x));
  }
}
console.log('rendered in', Date.now() - t0, 'ms');
