/**
 * Turns a baked PNG into the WebP the viewer loads (the studio ground shadow,
 * blender/scripts/carkit/studio.py):
 *
 *   node scripts/to-webp.mjs <in.png> <out.webp> [quality] [--trim] [--width N]
 *
 * --trim cuts the transparent margin off a cut-out; --width resizes to N pixels.
 *
 * Alpha is kept lossless: the shade IS the alpha channel, and a lossy alpha
 * bands visibly in a soft gradient.
 */
import { createRequire } from 'node:module';
import { statSync } from 'node:fs';

// sharp ships with Next.js (its image optimiser); it is not a dependency of ours
const sharp = createRequire(import.meta.url)('sharp');
const args = process.argv.slice(2);
const flag = (n) => args.includes(n);
const wi = args.indexOf('--width');
const width = wi >= 0 ? Number(args[wi + 1]) : 0;
const [src, out, q] = args.filter((a, i) => !a.startsWith('--') && !(wi >= 0 && i === wi + 1));
const quality = q ?? '82';
if (!src || !out) {
  console.error('usage: node scripts/to-webp.mjs <in.png> <out.webp> [quality] [--trim] [--width N]');
  process.exit(2);
}
let img = sharp(src);
if (flag('--trim')) img = sharp(await img.trim().toBuffer());
if (width) img = img.resize({ width });
await img.webp({ quality: Number(quality), alphaQuality: 100, effort: 6 }).toFile(out);
console.log(`${out}  ${(statSync(out).size / 1024).toFixed(0)} KB`);
