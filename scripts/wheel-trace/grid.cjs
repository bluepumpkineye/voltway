// node grid.cjs <uw.jpg> <out.jpg> [cropX cropY cropW cropH outW] [step=10] [rings=0.1]
// overlays a polar grid (angles every <step> deg, CCW from +x / 3 o'clock with y up; circles every <rings> of the lip radius)
// on an unwarped wheel image made by unwarp.cjs (lip radius = 0.45*size, centre = size/2).
const sharp = require('sharp');
(async () => {
  const [src, out, cx = 0, cy = 0, cw = 0, ch = 0, ow = 1400, step = 10, rings = 0.1] = process.argv.slice(2);
  const m = await sharp(src).metadata();
  const S = m.width, c = S / 2, R = S * 0.45;
  const parts = [];
  for (let r = +rings; r < 1.0001; r += +rings) {
    const lab = r.toFixed(1);
    parts.push(`<circle cx="${c}" cy="${c}" r="${R * r}" fill="none" stroke="${Math.abs(r - 0.5) < 1e-6 || Math.abs(r - 1) < 1e-6 ? '#00e5ff' : '#00e5ff'}" stroke-opacity="${Math.abs(r - 1) < 1e-6 ? 0.9 : 0.45}" stroke-width="${S / 1400}"/>`);
    parts.push(`<text x="${c + R * r * Math.cos(Math.PI / 4) + 3}" y="${c - R * r * Math.sin(Math.PI / 4) - 3}" font-size="${S / 70}" fill="#00e5ff" font-family="Arial">${lab}</text>`);
  }
  for (let a = 0; a < 360; a += +step) {
    const t = a * Math.PI / 180;
    const x1 = c + R * 0.12 * Math.cos(t), y1 = c - R * 0.12 * Math.sin(t), x2 = c + R * 1.02 * Math.cos(t), y2 = c - R * 1.02 * Math.sin(t);
    parts.push(`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#ffea00" stroke-opacity="${a % 30 === 0 ? 0.7 : 0.35}" stroke-width="${S / 1400}"/>`);
    parts.push(`<text x="${c + R * 1.05 * Math.cos(t) - S / 90}" y="${c - R * 1.05 * Math.sin(t) + S / 180}" font-size="${S / 62}" fill="#ffea00" font-family="Arial">${a}</text>`);
  }
  const svg = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${S}" height="${S}">${parts.join('')}</svg>`);
  let img = sharp(src).composite([{ input: svg }]);
  const buf = await img.png().toBuffer();
  let p = sharp(buf);
  if (+cw) p = p.extract({ left: Math.round(+cx), top: Math.round(+cy), width: Math.round(+cw), height: Math.round(+ch) });
  if (+ow) p = p.resize({ width: Math.round(+ow) });
  await p.jpeg({ quality: 90 }).toFile(out);
  console.log(out);
})();
