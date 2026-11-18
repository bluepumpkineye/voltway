// Mean colour of named patches in the XPENG Cabin 360 panoramas, per trim (2026-11-18).
//
//   node scripts/photo-tools/pano_probe.cjs [trim ...]
//
// The five panoramas of a camera share one geometry, so a patch picked once applies to every trim. Patches are rectangles in a
// rectilinear view (1200 x 900) of the front (driver's head) or back (rear seat) camera, chosen on single-material surfaces.
// `sat` patches report the mean of the most saturated 15% of pixels (a thin lime piping line inside a rectangle).
const path = require('path');
const P = require('./pano.cjs');
const DIR = path.join(__dirname, '..', '..', 'blender', 'reference', 'xpeng-mona-l05', 'pano');
const TRIMS = ['light-grey', 'dark-grey', 'iris', 'titanium-green', 'star-purple'];
const W = 1200, H = 900;
const VIEWS = {
  A: { cam: 'front', yaw: 20, pitch: -8, fov: 70 },
  B: { cam: 'back', yaw: 0, pitch: -8, fov: 70 },
};
// name: [view, x0, y0, x1, y1, mode]
const PATCHES = {
  dash_top: ['A', 920, 480, 1060, 520],
  dash_face: ['A', 760, 700, 1000, 740],
  wheel_rim: ['A', 180, 450, 330, 470],
  wheel_hub: ['A', 200, 720, 380, 770],
  console_lid: ['A', 560, 840, 640, 880],
  door_pod: ['A', 1100, 740, 1180, 780],
  headrest: ['B', 40, 300, 280, 400],
  seat_shoulder: ['B', 800, 460, 1000, 495],
  seat_shell: ['B', 200, 700, 400, 780],
  piping: ['B', 60, 510, 300, 522, 'sat'],
  console_rear: ['B', 560, 740, 640, 780],
  headliner: ['B', 330, 150, 480, 185],
};
const hex = (c) => '#' + c.map((v) => Math.round(v).toString(16).padStart(2, '0')).join('');

(async () => {
  const trims = process.argv.slice(2).length ? process.argv.slice(2) : TRIMS;
  const out = {};
  for (const t of trims) {
    out[t] = {};
    const imgs = {};
    for (const [k, v] of Object.entries(VIEWS)) {
      const pano = await P.load(path.join(DIR, `xpeng_l05_interior_pano_${t}_${v.cam}.jpg`));
      imgs[k] = P.render(pano, v.yaw, v.pitch, v.fov, W, H);
    }
    for (const [name, [vw, x0, y0, x1, y1, mode]] of Object.entries(PATCHES)) {
      const buf = imgs[vw];
      const px = [];
      for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) { const i = (y * W + x) * 3; px.push([buf[i], buf[i + 1], buf[i + 2]]); }
      let use = px;
      if (mode === 'sat') {
        use = px.map((p) => ({ p, s: Math.max(...p) - Math.min(...p) })).sort((a, b) => b.s - a.s).slice(0, Math.max(1, Math.floor(px.length * 0.15))).map((o) => o.p);
      }
      const m = [0, 1, 2].map((c) => use.reduce((s, p) => s + p[c], 0) / use.length);
      out[t][name] = m.map(Math.round);
    }
  }
  const names = Object.keys(PATCHES);
  console.log('patch'.padEnd(14) + trims.map((t) => t.padEnd(22)).join(''));
  for (const n of names) console.log(n.padEnd(14) + trims.map((t) => (out[t][n].join(',') + ' ' + hex(out[t][n])).padEnd(22)).join(''));
  if (process.env.JSON) console.log(JSON.stringify(out));
})();
