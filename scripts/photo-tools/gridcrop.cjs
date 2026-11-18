// Crop a region of a reference photo (ORIGINAL pixel coordinates), upscale it and draw a labelled grid in original pixels,
// so features can be read off to a couple of pixels. usage: node scripts/photo-tools/gridcrop.cjs out.jpg photo.jpg x0 y0 x1 y1 outWidth gridStep
// usage: node gridcrop.cjs out.jpg photo x0 y0 x1 y1 outwidth step   -> crop (original px) with labelled grid
const path = require('path');
const sharp = require(path.join(__dirname, '..', '..', 'node_modules', 'sharp'));
(async () => {
  const [out, photo, x0, y0, x1, y1, ow, step] = process.argv.slice(2);
  const X0 = +x0, Y0 = +y0, X1 = +x1, Y1 = +y1, OW = +ow, ST = +step;
  const s = OW / (X1 - X0), OH = Math.round((Y1 - Y0) * s);
  const base = await sharp(photo).extract({ left: X0, top: Y0, width: X1 - X0, height: Y1 - Y0 }).resize(OW, OH).toBuffer();
  let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${OW}" height="${OH}">`;
  for (let x = Math.ceil(X0 / ST) * ST; x < X1; x += ST) {
    const px = (x - X0) * s;
    svg += `<line x1="${px}" y1="0" x2="${px}" y2="${OH}" stroke="#00ffff" stroke-opacity="0.55" stroke-width="1"/><text x="${px + 2}" y="12" font-size="12" fill="#ff0" stroke="#000" stroke-width="0.4">${x}</text>`;
  }
  for (let y = Math.ceil(Y0 / ST) * ST; y < Y1; y += ST) {
    const py = (y - Y0) * s;
    svg += `<line x1="0" y1="${py}" x2="${OW}" y2="${py}" stroke="#00ffff" stroke-opacity="0.55" stroke-width="1"/><text x="2" y="${py - 2}" font-size="12" fill="#ff0" stroke="#000" stroke-width="0.4">${y}</text>`;
  }
  svg += '</svg>';
  await sharp(base).composite([{ input: Buffer.from(svg), left: 0, top: 0 }]).jpeg({ quality: 90 }).toFile(out);
  console.log('ok', OW, OH, 'scale', s.toFixed(3));
})();
