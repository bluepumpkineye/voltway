// node period.cjs <uw.jpg> <r> [rmin rmax]  - the number of repeats of a wheel's pattern: the circular
// autocorrelation of the luminance round the circle of radius r (fractions of the lip radius), averaged over
// a few radii, and the dominant n (period 360 / n) from its first strong peak.
const sharp = require('sharp');
(async () => {
  const [src, rs = '0.8'] = process.argv.slice(2);
  const rads = rs.split(',').map(Number);
  const { data, info } = await sharp(src).removeAlpha().blur(1.2).raw().toBuffer({ resolveWithObject: true });
  const S = info.width, ch = info.channels, c = S / 2, R = S * 0.45;
  const N = 1440;
  const px = (x, y) => {
    const xi = Math.floor(x), yi = Math.floor(y), fx = x - xi, fy = y - yi;
    const g = (xx, yy) => { const o = (yy * S + xx) * ch; return 0.2126 * data[o] + 0.7152 * data[o + 1] + 0.0722 * data[o + 2]; };
    return (g(xi, yi) * (1 - fx) + g(xi + 1, yi) * fx) * (1 - fy) + (g(xi, yi + 1) * (1 - fx) + g(xi + 1, yi + 1) * fx) * fy;
  };
  const ac = new Float64Array(N);
  for (const r of rads) {
    const v = new Float64Array(N);
    for (let i = 0; i < N; i++) { const t = 2 * Math.PI * i / N; v[i] = px(c + R * r * Math.cos(t), c - R * r * Math.sin(t)); }
    const m = v.reduce((a, b) => a + b, 0) / N;
    for (let i = 0; i < N; i++) v[i] -= m;
    const e = v.reduce((a, b) => a + b * b, 0);
    for (let k = 0; k < N; k++) { let s = 0; for (let i = 0; i < N; i++) s += v[i] * v[(i + k) % N]; ac[k] += s / e / rads.length; }
  }
  const peaks = [];
  for (let k = 8; k < N / 2; k++) if (ac[k] > ac[k - 1] && ac[k] >= ac[k + 1] && ac[k] > 0.15) peaks.push([+(k * 360 / N).toFixed(2), +ac[k].toFixed(3), +(360 / (k * 360 / N)).toFixed(2)]);
  console.log('peaks [lag deg, autocorr, 360/lag]:', JSON.stringify(peaks.slice(0, 8)));
})();
