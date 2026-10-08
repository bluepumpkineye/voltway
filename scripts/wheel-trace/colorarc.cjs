// node colorarc.cjs uw.jpg kind rlist   kind: yellow | orange | red ; prints the angular intervals (deg) of that colour at each radius
const sharp = require('sharp');
(async () => {
  const [src, kind, rl] = process.argv.slice(2);
  const { data, info } = await sharp(src).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  const S = info.width, ch = info.channels, R = S * 0.45, c = S / 2;
  const isC = (r, g, b) => kind === 'red' ? (r > 110 && g < 0.45 * r && b < 0.45 * r) : kind === 'yellow' ? (r > 140 && g > 110 && b < 100 && r - b > 80 && g > 0.7 * r) : (r > 150 && g > 70 && g < 0.75 * r && b < 80);
  for (const rr of rl.split(',').map(Number)) {
    const iv = []; let start = null;
    for (let a = -180; a <= 180; a += 0.5) {
      const x = Math.round(c + R * rr * Math.cos(a * Math.PI / 180)), y = Math.round(c - R * rr * Math.sin(a * Math.PI / 180));
      const o = (y * S + x) * ch; const hit = isC(data[o], data[o + 1], data[o + 2]);
      if (hit && start === null) start = a; if (!hit && start !== null) { if (a - start >= 1.5) iv.push([start, a - 0.5]); start = null; }
    }
    if (start !== null) iv.push([start, 180]);
    console.log('r=' + rr + ' ' + iv.map(([a, b]) => a.toFixed(1) + '..' + b.toFixed(1)).join('  '));
  }
})();
