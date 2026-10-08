// node polar.cjs <uw.jpg> <out.jpg> <theta0> <theta1> <r0> <r1> <pxPerDeg> <pxPerR> [cx cy]
// Polar unwrap of a face-on wheel image from unwarp.cjs: x = angle (deg, CCW from 3 o'clock, may exceed 360 or be negative),
// y = radius (r1 at the top, r0 at the bottom), with a labelled grid (5 deg / 0.05 R).
// Optional cx,cy: hub-centre offset in output-image pixels of the uw image (default: image centre).
const sharp = require('sharp');
(async () => {
  const [src, out, t0, t1, r0, r1, ppd, ppr, ox = 0, oy = 0, polyFile = ''] = process.argv.slice(2);
  const { data, info } = await sharp(src).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  const S = info.width, ch = info.channels, c = S / 2, R = S * 0.45;
  const T0 = +t0, T1 = +t1, R0 = +r0, R1 = +r1, PPD = +ppd, PPR = +ppr;
  const W = Math.round((T1 - T0) * PPD), H = Math.round((R1 - R0) * PPR);
  const buf = Buffer.alloc(W * H * 3);
  const px = (x, y, k) => {
    x = Math.max(0, Math.min(S - 1.001, x)); y = Math.max(0, Math.min(S - 1.001, y));
    const xi = Math.floor(x), yi = Math.floor(y), fx = x - xi, fy = y - yi;
    const g = (xx, yy) => data[(yy * S + xx) * ch + k];
    return (g(xi, yi) * (1 - fx) + g(xi + 1, yi) * fx) * (1 - fy) + (g(xi, yi + 1) * (1 - fx) + g(xi + 1, yi + 1) * fx) * fy;
  };
  for (let j = 0; j < H; j++) for (let i = 0; i < W; i++) {
    const th = (T0 + i / PPD) * Math.PI / 180, r = R1 - j / PPR;
    const x = c + +ox + R * r * Math.cos(th), y = c + +oy - R * r * Math.sin(th);
    const o = (j * W + i) * 3;
    for (let k = 0; k < 3; k++) buf[o + k] = px(x, y, k);
  }
  const parts = [];
  for (let a = Math.ceil(T0 / 5) * 5; a <= T1; a += 5) {
    const x = (a - T0) * PPD, big = ((a % 10) + 10) % 10 === 0;
    parts.push(`<line x1="${x}" y1="0" x2="${x}" y2="${H}" stroke="#ffea00" stroke-opacity="${big ? 0.55 : 0.28}" stroke-width="1"/>`);
    if (big) parts.push(`<text x="${x + 2}" y="12" font-size="12" fill="#ffea00" font-family="Arial">${((a % 360) + 360) % 360}</text>`);
  }
  for (let r = Math.ceil(R0 / 0.05) * 0.05; r <= R1 + 1e-9; r += 0.05) {
    const y = (R1 - r) * PPR, big = Math.abs(r * 10 - Math.round(r * 10)) < 1e-6;
    parts.push(`<line x1="0" y1="${y}" x2="${W}" y2="${y}" stroke="#00e5ff" stroke-opacity="${big ? 0.6 : 0.28}" stroke-width="1"/>`);
    if (big) parts.push(`<text x="2" y="${y - 2}" font-size="12" fill="#00e5ff" font-family="Arial">${r.toFixed(2)}</text>`);
  }
  if (polyFile) {
    const J = JSON.parse(require('fs').readFileSync(polyFile, 'utf8'));
    const per = J.period || 72, cols = ['#ff00ff', '#00ff66', '#ff8800', '#00aaff', '#ffffff'];
    (J.polys || []).forEach((P, pi) => {
      for (let k = -3; k <= 8; k++) {
        const pts = P.pts.map(([a, r]) => [((a + k * per - T0) * PPD), ((R1 - r) * PPR)]);
        if (pts.every(q => q[0] < -50 || q[0] > W + 50)) continue;
        const d = pts.map((q, i) => (i ? 'L' : 'M') + q[0].toFixed(1) + ' ' + q[1].toFixed(1)).join(' ') + (P.open ? '' : ' Z');
        parts.push(`<path d="${d}" fill="none" stroke="${cols[pi % cols.length]}" stroke-width="1.6" stroke-opacity="0.95"/>`);
        if (k === 0) pts.forEach((q, i) => parts.push(`<circle cx="${q[0]}" cy="${q[1]}" r="2.5" fill="${cols[pi % cols.length]}"/><text x="${q[0] + 4}" y="${q[1] - 4}" font-size="10" fill="${cols[pi % cols.length]}" font-family="Arial">${i}</text>`));
      }
    });
  }
  const svg = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${parts.join('')}</svg>`);
  await sharp(buf, { raw: { width: W, height: H, channels: 3 } }).composite([{ input: svg }]).jpeg({ quality: 90 }).toFile(out);
  console.log(out, W + 'x' + H);
})();
