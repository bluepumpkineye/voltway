// Turn the part renders (blender/renders/xray/*.png, from su7_anatomy_renders.py) into the cards' images: trim the empty margin,
// fit the part into a 3:2 frame with room round it, and write a WebP with the alpha kept.
//   node scripts/xray-tools/render-cards.mjs blender/renders/xray public/xray/su7-ultra
import { createRequire } from 'node:module';
import { mkdirSync, readdirSync, statSync } from 'node:fs';
import path from 'node:path';

const sharp = createRequire(import.meta.url)('sharp');
const [dir, out] = process.argv.slice(2);
mkdirSync(out, { recursive: true });
const W = 640, H = 420, PAD = 26;
let total = 0;
for (const f of readdirSync(dir).filter((n) => n.endsWith('.png') && !n.startsWith('_'))) {
  const trimmed = await sharp(path.join(dir, f)).trim({ threshold: 4 }).toBuffer();
  const fitted = await sharp(trimmed).resize(W - 2 * PAD, H - 2 * PAD, { fit: 'inside' }).toBuffer();
  const meta = await sharp(fitted).metadata();
  const dest = path.join(out, f.replace(/\.png$/, '.webp'));
  await sharp({ create: { width: W, height: H, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 0 } } })
    .composite([{ input: fitted, left: Math.round((W - meta.width) / 2), top: Math.round((H - meta.height) / 2) }])
    .webp({ quality: 84, alphaQuality: 90, effort: 5 })
    .toFile(dest);
  total += statSync(dest).size;
  console.log(path.basename(dest), Math.round(statSync(dest).size / 1024) + ' KB');
}
console.log('total', Math.round(total / 1024) + ' KB');
