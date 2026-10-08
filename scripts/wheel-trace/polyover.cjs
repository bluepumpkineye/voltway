// node polyover.cjs uw.jpg polys.json out.jpg x0 y0 w h [outW=1400] [gamma=1] [gridless=0]
// Draws polygons given in polar coordinates ((angle deg CCW from 3 o'clock, r / lip radius), repeated
// every `period` degrees) over the round unwarped photograph (lip radius 0.45 of the image), crops the box
// (x0,y0,w,h in uw pixels) and scales it to outW. Optional gamma lifts the shadows.
// polys.json: {"period":72,"polys":[{"pts":[[a,r],...],"open":false,"color":"#ff00ff","reps":[0,1,2,3,4]}]}
const sharp = require('sharp');
const fs = require('fs');
(async () => {
  const [src, pj, out, x0, y0, w, h, outW = '1400', gam = '1', nogrid = '0'] = process.argv.slice(2);
  const meta = await sharp(src).metadata();
  const S = meta.width, c = S / 2, R = S * 0.45;
  const J = JSON.parse(fs.readFileSync(pj, 'utf8'));
  const per = J.period || 72;
  const X0 = +x0, Y0 = +y0, W = +w, H = +h, sc = +outW / W;
  const cols = ['#ff00ff', '#00ff66', '#ff8800', '#00aaff', '#ffffff', '#ffea00'];
  const parts = [];
  const P = (a, r) => [(c + R * r * Math.cos(a * Math.PI / 180) - X0) * sc, (c - R * r * Math.sin(a * Math.PI / 180) - Y0) * sc];
  if (nogrid !== '1') {
    for (let r = 0.1; r <= 1.0001; r += 0.1) {
      const pts = [];
      for (let a = 0; a <= 360; a += 2) pts.push(P(a, r));
      parts.push(`<path d="${pts.map((q, i) => (i ? 'L' : 'M') + q[0].toFixed(1) + ' ' + q[1].toFixed(1)).join(' ')}" fill="none" stroke="#00e5ff" stroke-opacity="0.35" stroke-width="1"/>`);
      const q = P(95, r);
      parts.push(`<text x="${q[0]}" y="${q[1]}" font-size="12" fill="#00e5ff" font-family="Arial">${r.toFixed(1)}</text>`);
    }
    for (let a = 0; a < 360; a += 10) {
      const q0 = P(a, 0.08), q1 = P(a, 1.0);
      parts.push(`<line x1="${q0[0]}" y1="${q0[1]}" x2="${q1[0]}" y2="${q1[1]}" stroke="#ffea00" stroke-opacity="0.3" stroke-width="1"/>`);
      const q = P(a, 0.52);
      parts.push(`<text x="${q[0]}" y="${q[1]}" font-size="12" fill="#ffea00" font-family="Arial">${a}</text>`);
    }
  }
  (J.polys || []).forEach((poly, pi) => {
    const reps = poly.reps || [0];
    reps.forEach((k) => {
      const pts = poly.pts.map(([a, r]) => P(a + k * per, r));
      const d = pts.map((q, i) => (i ? 'L' : 'M') + q[0].toFixed(1) + ' ' + q[1].toFixed(1)).join(' ') + (poly.open ? '' : ' Z');
      const col = poly.color || cols[pi % cols.length];
      parts.push(`<path d="${d}" fill="none" stroke="${col}" stroke-width="1.8" stroke-opacity="0.95"/>`);
      if (k === reps[0] && !poly.nolabel) pts.forEach((q, i) => parts.push(`<circle cx="${q[0]}" cy="${q[1]}" r="2.5" fill="${col}"/><text x="${q[0] + 4}" y="${q[1] - 4}" font-size="11" fill="${col}" font-family="Arial">${i}</text>`));
    });
  });
  const svg = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${Math.round(W * sc)}" height="${Math.round(H * sc)}">${parts.join('')}</svg>`);
  let img = sharp(src).extract({ left: Math.round(X0), top: Math.round(Y0), width: Math.round(W), height: Math.round(H) }).resize(Math.round(W * sc));
  if (+gam !== 1) img = img.gamma(+gam);
  await img.composite([{ input: svg }]).jpeg({ quality: 90 }).toFile(out);
  console.log(out);
})();
