// Crop of a reference photo (ORIGINAL pixels) with a labelled grid, for reading a BLACK car whose parts hide against each other:
// mode clahe = shadows lifted + contrast-limited local equalisation, lift = gamma only, plain = none.
// usage: node scripts/photo-tools/gridcrop-clahe.cjs photo out.png x y w h outW clahe|lift|plain [step=25] [overlay.json]
// draws a labelled grid (original pixel coordinates) over the crop; optional overlay.json = {"polys":[{"pts":[[u,v],...],"color":"#f0f","closed":true}], "dots":[[u,v,"label"]]}
const path = require('path');
const sharp = require(path.join(__dirname, '..', '..', 'node_modules', 'sharp'));
const fs = require('fs');
(async () => {
  const [inp, out, x, y, w, h, outW, mode = 'clahe', step = '25', ov = ''] = process.argv.slice(2);
  const sc = +outW / +w, W = +outW, H = Math.round(+h * sc);
  let img = sharp(inp).extract({ left: +x, top: +y, width: +w, height: +h }).resize({ width: W });
  if (mode === 'clahe') img = img.gamma(1.6, 1.0).normalise().clahe({ width: 48, height: 32, maxSlope: 6 });
  else if (mode === 'lift') img = img.gamma(2.0, 1.0);
  let buf = await img.png().toBuffer();
  const g = +step;
  let s = `<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg">`;
  for (let gx = Math.ceil(+x / g) * g; gx < +x + +w; gx += g) {
    const px = (gx - +x) * sc, major = gx % 100 === 0;
    s += `<line x1="${px}" y1="0" x2="${px}" y2="${H}" stroke="${major ? '#0ff' : '#08a'}" stroke-width="${major ? 0.8 : 0.4}" opacity="0.6"/>`;
    if (gx % (g * 2) === 0) s += `<text x="${px + 2}" y="11" font-size="10" fill="#ff0">${gx}</text>`;
  }
  for (let gy = Math.ceil(+y / g) * g; gy < +y + +h; gy += g) {
    const py = (gy - +y) * sc, major = gy % 100 === 0;
    s += `<line x1="0" y1="${py}" x2="${W}" y2="${py}" stroke="${major ? '#0ff' : '#08a'}" stroke-width="${major ? 0.8 : 0.4}" opacity="0.6"/>`;
    if (gy % (g * 2) === 0) s += `<text x="2" y="${py - 2}" font-size="10" fill="#ff0">${gy}</text>`;
  }
  if (ov) {
    const o = JSON.parse(fs.readFileSync(ov, 'utf8'));
    for (const p of o.polys || []) {
      const pts = p.pts.map(([u, v]) => `${((u - +x) * sc).toFixed(1)},${((v - +y) * sc).toFixed(1)}`).join(' ');
      s += p.closed === false
        ? `<polyline points="${pts}" fill="none" stroke="${p.color || '#f0f'}" stroke-width="1.6"/>`
        : `<polygon points="${pts}" fill="none" stroke="${p.color || '#f0f'}" stroke-width="1.6"/>`;
      if (p.label) { const [u, v] = p.pts[0]; s += `<text x="${((u - +x) * sc + 4).toFixed(1)}" y="${((v - +y) * sc - 4).toFixed(1)}" font-size="13" fill="${p.color || '#f0f'}">${p.label}</text>`; }
    }
    for (const [u, v, lab] of o.dots || []) {
      const px = (u - +x) * sc, py = (v - +y) * sc;
      s += `<circle cx="${px}" cy="${py}" r="3" fill="#f0f"/>` + (lab ? `<text x="${px + 5}" y="${py - 5}" font-size="12" fill="#f8f">${lab}</text>` : '');
    }
  }
  s += '</svg>';
  await sharp(buf).composite([{ input: Buffer.from(s), left: 0, top: 0 }]).png().toFile(out);
  console.log('ok', out);
})();
