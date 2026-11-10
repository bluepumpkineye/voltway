// Tile the part renders into one contact sheet on a light ground, to review them at once.
//   node scripts/xray-tools/contact.mjs blender/renders/xray out.jpg
import { createRequire } from 'node:module';
import { readdirSync } from 'node:fs';
import path from 'node:path';

const sharp = createRequire(import.meta.url)('sharp');
const [dir, out] = process.argv.slice(2);
const files = readdirSync(dir).filter((f) => f.endsWith('.png')).sort();
const W = 450, H = 300, COLS = 4;
const rows = Math.ceil(files.length / COLS);
const comps = [];
for (let i = 0; i < files.length; i++) {
  const img = await sharp(path.join(dir, files[i])).resize(W, H, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } }).toBuffer();
  comps.push({ input: img, left: (i % COLS) * W, top: Math.floor(i / COLS) * H });
}
await sharp({ create: { width: COLS * W, height: rows * H, channels: 3, background: '#e9ecf1' } }).composite(comps).jpeg({ quality: 88 }).toFile(out);
console.log(files.join(' '));
