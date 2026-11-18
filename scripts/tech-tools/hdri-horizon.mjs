// Samples the colours around the horizon of a car's HDRI view (public/models/<car>-outside.jpg), to choose the `haze` of its `outside.road`
// (the colour the Drive tab's far scenery, verges and exit fog go into: src/data/vehicles/schema.ts `OutsideWorld.road`).
//   node scripts/tech-tools/hdri-horizon.mjs public/models/su7-ultra-outside.jpg
// Prints, for twelve sectors of the compass (the equirectangular image's columns; 0 degrees is the +x axis of the viewer), the mean colour just above the
// skyline (2 to 4 degrees up: buildings and trees), in the sky (6 to 9 degrees up) and on the ground just under the horizon (6 to 12 degrees down), and the
// all-round figures. A good haze is the sky colour of the sectors the camera looks toward, a little paler; tune it in the pane.
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const root = fileURLToPath(new URL('../../', import.meta.url));
const sharp = require(`${root}node_modules/sharp`);

const file = process.argv[2];
if (!file) {
  console.error('usage: node scripts/tech-tools/hdri-horizon.mjs <view.jpg>');
  process.exit(1);
}
const img = sharp(file);
const { width: W, height: H } = await img.metadata();
const { data, info } = await img.raw().toBuffer({ resolveWithObject: true });
const ch = info.channels;
const hex = (c) => '#' + c.map((v) => v.toString(16).padStart(2, '0')).join('');

/** mean colour of columns u0..u1 (0..1 across the image) between elevations e0 and e1 degrees (positive up) */
function band(u0, u1, e0, e1) {
  const acc = [0, 0, 0];
  let n = 0;
  const y0 = Math.round(H / 2 - (e1 / 90) * (H / 2));
  const y1 = Math.round(H / 2 - (e0 / 90) * (H / 2));
  for (let y = y0; y <= y1; y++) {
    for (let x = Math.round(u0 * W); x < Math.round(u1 * W); x += 2) {
      for (let c = 0; c < 3; c++) acc[c] += data[(y * W + x) * ch + c];
      n++;
    }
  }
  return acc.map((v) => Math.round(v / n));
}

console.log(`${file}: ${W} x ${H}`);
for (let s = 0; s < 12; s++) {
  const u0 = s / 12;
  const u1 = (s + 1) / 12;
  const az = Math.round((u0 + 1 / 24 - 0.5) * 360);
  console.log(`azimuth ${String(az).padStart(4)}  skyline ${hex(band(u0, u1, 2, 4))}  sky ${hex(band(u0, u1, 6, 9))}  ground ${hex(band(u0, u1, -12, -6))}`);
}
console.log(`all round: skyline ${hex(band(0, 1, 2, 4))}, sky ${hex(band(0, 1, 6, 9))}, zenith ${hex(band(0, 1, 40, 60))}`);
