// node scripts/silhouette/side-silhouette.cjs <side.jpg> <pxPerMetre> <frontAxlePx> <groundPx> [frontAxleM=1.565] [thr=12]
//
// The outline of a car in a level, long-lens side picture (a maker's configurator render, a studio photograph shot from far away)
// as numbers in the build's own frame (x forward in metres, the front axle at `frontAxleM`, z up from the tyre bottom), to lay
// beside the same tables for the model (glb-silhouette.cjs). The car is told from the smooth studio background by its difference
// from a background fitted row by row (the mean of the first and the last 120 columns, interpolated): this works for a picture
// whose background is a plain gradient; it will not for one with a horizon or a wall.
//
//   <pxPerMetre>   the picture's scale: the tyre-bottom-to-roof height in pixels over the published height, or a wheel's
//                  outer diameter over its published size; both should agree to 1 %, if not the picture is not level
//   <frontAxlePx>  the x pixel of the front wheel's centre; <groundPx> the y pixel of the tyre's bottom
//
// Prints the top profile every 0.1 m of x and the front and rear extreme x every 0.05 m of height. The Nio ES8's official
// side render read: front axle 672 px, ground 947 px, 362 px/m (its wheelbase then came out at 3.15 m and its height at 1.80 m,
// the published figures, and its length at 5.05 m, not the published 5.28: the build's nose stood 0.25 m too far forward).
const { createRequire } = require('module');
const path = require('path');
const sharp = createRequire(path.resolve(__dirname, '../../package.json'))('sharp');

(async () => {
  const [src, ppm, axpx, gpx, axm = '1.565', thr = '12'] = process.argv.slice(2);
  if (!gpx) { console.error('usage: side-silhouette.cjs <side.jpg> <pxPerMetre> <frontAxlePx> <groundPx> [frontAxleM] [thr]'); process.exit(1); }
  const S = +ppm, AX = +axpx, GY = +gpx, AXM = +axm, T = +thr;
  const { data, info } = await sharp(src).greyscale().blur(1.0).raw().toBuffer({ resolveWithObject: true });
  const W = info.width, H = info.height;
  const px = (x, y) => data[y * W + x];
  const bg = new Float32Array(W * H);
  for (let y = 0; y < H; y++) {
    let a = 0, b = 0;
    for (let x = 0; x < 120; x++) { a += px(x, y); b += px(W - 1 - x, y); }
    a /= 120; b /= 120;
    for (let x = 0; x < W; x++) bg[y * W + x] = a + (b - a) * x / (W - 1);
  }
  const car = (x, y) => Math.abs(px(x, y) - bg[y * W + x]) > T;
  const xm = (p) => AXM + (AX - p) / S;
  const top = [];
  for (let m = 2.8; m >= -2.8; m -= 0.1) {
    const x = Math.round(AX - (m - AXM) * S);
    if (x < 0 || x >= W) continue;
    let t = -1;
    for (let y = 0; y < H; y++) if (car(x, y)) { t = y; break; }
    top.push(m.toFixed(2) + ':' + (t < 0 ? 'NA' : ((GY - t) / S).toFixed(3)));
  }
  console.log('TOP', top.join(' '));
  for (let z = 0.30; z <= 1.30; z += 0.05) {
    const y = Math.round(GY - z * S);
    let l = -1, r = -1;
    for (let x = 100; x < W - 100; x++) if (car(x, y)) { l = x; break; }
    for (let x = W - 100; x > 100; x--) if (car(x, y)) { r = x; break; }
    console.log(z.toFixed(2) + ': front ' + xm(l).toFixed(3) + ' rear ' + xm(r).toFixed(3));
  }
})();
