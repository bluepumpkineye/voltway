// node shift.cjs <in.jpg> <out.jpg> <dx> <dy>
// Moves the picture's content by (-dx, -dy) pixels (black fills the edge) so that the point
// (middle + dx, middle + dy) lands on the middle: the copy of an unwarped photograph centred on the
// axle that centrefit.cjs found. Every tool that reads polar strips (polar.cjs, segment.cjs) takes
// the middle as the origin.
const sharp = require('sharp');

(async () => {
  const [inp, out, dxA, dyA] = process.argv.slice(2);
  const dx = Math.round(+dxA), dy = Math.round(+dyA);
  const m = await sharp(inp).metadata();
  const S = m.width;
  const w = S - Math.abs(dx), h = S - Math.abs(dy);
  const buf = await sharp(inp).extract({ left: Math.max(0, dx), top: Math.max(0, dy), width: w, height: h }).toBuffer();
  await sharp(buf)
    .extend({ left: Math.max(0, -dx), right: Math.max(0, dx), top: Math.max(0, -dy), bottom: Math.max(0, dy), background: '#000' })
    .jpeg({ quality: 94 })
    .toFile(out);
  console.log('wrote', out);
})();
