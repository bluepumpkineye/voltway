// node centrefit.cjs <uw.jpg> <repeats> [r0=0.5] [r1=0.95] [range=24]
//
// Where the wheel's axle really is in an unwarped photograph. unwarp.cjs centres the picture on the
// ellipse it fits to the lip ring, and that fit is biased by the ring's lighting (the 7X photographs'
// axle sat 12 to 19 px below the middle of a 2400 px picture, a tenth of a percent of the lip radius
// but a whole degree of angle at the side windows). A pattern of n identical repeats is a ruler: the
// luminance at (angle + k * 360 / n) agrees across k only when the polar origin is the axle. The
// origin is searched (coarse, then fine, in source pixels from the middle) for the least variance of
// that luminance across the repeats, over the radii r0..r1 (fractions of the lip radius, which is
// 0.45 of the picture).
//
// Prints the shift (dx, dy) to the axle and the variance there and at the middle. Move the picture
// with shift.cjs and trace from that copy: its polar strips are then sharp (the repeats overlie).
const sharp = require('sharp');

(async () => {
  const [src, nA, r0A = 0.5, r1A = 0.95, rangeA = 24] = process.argv.slice(2);
  const n = +nA, R0 = +r0A, R1 = +r1A, RANGE = +rangeA;
  const { data, info } = await sharp(src).blur(1.5).greyscale().raw().toBuffer({ resolveWithObject: true });
  const S = info.width, c = S / 2, R = S * 0.45, per = 360 / n;
  const px = (x, y) => {
    x = Math.max(0, Math.min(S - 1.001, x)); y = Math.max(0, Math.min(S - 1.001, y));
    const xi = Math.floor(x), yi = Math.floor(y), fx = x - xi, fy = y - yi;
    const g = (a, b) => data[b * S + a];
    return (g(xi, yi) * (1 - fx) + g(xi + 1, yi) * fx) * (1 - fy) + (g(xi, yi + 1) * (1 - fx) + g(xi + 1, yi + 1) * fx) * fy;
  };
  const variance = (dx, dy) => {
    let acc = 0, cnt = 0;
    for (let t = 0; t < per; t += 0.5) for (let r = R0; r <= R1; r += 0.01) {
      let s = 0, s2 = 0;
      for (let k = 0; k < n; k++) {
        const a = (t + k * per) * Math.PI / 180;
        const v = px(c + dx + r * R * Math.cos(a), c + dy - r * R * Math.sin(a));
        s += v; s2 += v * v;
      }
      acc += s2 / n - (s / n) * (s / n); cnt++;
    }
    return acc / cnt;
  };
  let best = { dx: 0, dy: 0, v: Infinity };
  for (let dy = -RANGE; dy <= RANGE; dy += 4) for (let dx = -RANGE; dx <= RANGE; dx += 4) {
    const v = variance(dx, dy);
    if (v < best.v) best = { dx, dy, v };
  }
  const centre = { ...best };
  for (let dy = centre.dy - 3; dy <= centre.dy + 3; dy++) for (let dx = centre.dx - 3; dx <= centre.dx + 3; dx++) {
    const v = variance(dx, dy);
    if (v < best.v) best = { dx, dy, v };
  }
  console.log(`axle at (+${best.dx}, +${best.dy}) px from the middle: variance ${best.v.toFixed(0)}, at the middle ${variance(0, 0).toFixed(0)}`);
  console.log(`node shift.cjs ${src} <out.jpg> ${best.dx} ${best.dy}`);
})();
