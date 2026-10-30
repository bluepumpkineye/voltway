// node px2ar.cjs <in.json> <out.json> <t0> <ppd> <ppr> [r1=1.0] [angleOffset=0]
// in.json: {"name": [[x,y],...], ...} strip pixel coordinates (as read off a polar.cjs picture);
// out.json: polar.cjs polygons {"period":72,"polys":[{"pts":[[a,r],...],"reps":[0]}]} with a = t0 + x/ppd - offset, r = r1 - y/ppr
const fs = require('fs');
const [inp, out, t0, ppd, ppr, r1 = '1.0', off = '0'] = process.argv.slice(2);
const d = JSON.parse(fs.readFileSync(inp, 'utf8'));
const polys = [];
for (const k of Object.keys(d)) {
  const pts = d[k].map(([x, y]) => [+(+t0 + x / +ppd - +off).toFixed(2), +(+r1 - y / +ppr).toFixed(3)]);
  polys.push({ name: k, pts, reps: [0] });
  console.log(k, JSON.stringify(pts));
}
fs.writeFileSync(out, JSON.stringify({ period: 72, polys }));
