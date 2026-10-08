// node maskedge.cjs <photo.jpg> <mask.png (alpha)> <out.jpg> [width=1400] [fill=0.0]
// Draws the outline of the mask's opaque area (magenta) over the photo; fill > 0 also tints the area cyan.
const sharp = require('sharp');
(async () => {
  const [photo, mask, out, wA = 1400, fillA = 0] = process.argv.slice(2);
  const W = +wA;
  const base = await sharp(photo).resize(W, W).removeAlpha().raw().toBuffer();
  const m = await sharp(mask).resize(W, W).ensureAlpha().raw().toBuffer();   // RGBA
  const a = (x, y) => (x < 0 || y < 0 || x >= W || y >= W) ? 0 : m[(y * W + x) * 4 + 3] > 127 ? 1 : 0;
  const buf = Buffer.from(base);
  for (let y = 0; y < W; y++) for (let x = 0; x < W; x++) {
    const v = a(x, y);
    const edge = v !== a(x + 1, y) || v !== a(x, y + 1) || v !== a(x - 1, y) || v !== a(x, y - 1);
    const o = (y * W + x) * 3;
    if (edge) { buf[o] = 255; buf[o + 1] = 0; buf[o + 2] = 255; }
    else if (v && +fillA > 0) { buf[o] = buf[o] * (1 - +fillA); buf[o + 1] = buf[o + 1] * (1 - +fillA) + 255 * +fillA; buf[o + 2] = buf[o + 2] * (1 - +fillA) + 255 * +fillA; }
  }
  await sharp(buf, { raw: { width: W, height: W, channels: 3 } }).jpeg({ quality: 90 }).toFile(out);
  console.log(out);
})();
