// Solve where an equirectangular panorama's camera stood, from landmarks whose 3D position in OUR model is known.
//
//   node scripts/photo-tools/pano_solve.cjs <landmarks.json> <front|back> [--free-yaw] [--use a,b,c] [--screen-top-x X]
//
// landmarks.json: { "<name>": { "model": [x, y, z], "front": {"yaw": deg, "pitch": deg}, "back": {...} } }
// Model frame: x forward, y left, z up (Blender). Pano frame: yaw 0 = forward, yaw > 0 = to the right, pitch up.
// Solves the camera position (3) by Levenberg-Marquardt on the angle between each measured bearing and the direction to
// the landmark; with --free-yaw it also solves a yaw offset (the pano's forward axis vs the car's). Prints the residual
// of EVERY landmark that has a reading (those not in --use are held out: they audit the model, they do not steer the fit).
const fs = require('fs');
const D2R = Math.PI / 180;

function bearing(yaw, pitch) {                      // pano angles -> model-frame unit vector
  const y = yaw * D2R, p = pitch * D2R;
  return [Math.cos(p) * Math.cos(y), -Math.cos(p) * Math.sin(y), Math.sin(p)];
}
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const norm = (a) => { const n = Math.hypot(...a); return [a[0] / n, a[1] / n, a[2] / n]; };
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
function rotZ(v, a) { const c = Math.cos(a), s = Math.sin(a); return [c * v[0] - s * v[1], s * v[0] + c * v[1], v[2]]; }

function residuals(theta, lms, which, freeYaw) {
  const C = theta.slice(0, 3), off = freeYaw ? theta[3] : 0;
  const r = [];
  for (const l of lms) {
    const m = l[which];
    const b = rotZ(bearing(m.yaw, m.pitch), off);
    const d = norm(sub(l.model, C));
    r.push(b[0] - d[0], b[1] - d[1], b[2] - d[2]);
  }
  return r;
}

function lm(f, x0, iters = 80) {
  let x = x0.slice(), lam = 1e-3;
  let r = f(x), cost = dot(r, r);
  for (let it = 0; it < iters; it++) {
    const n = x.length, J = [];
    for (let j = 0; j < n; j++) {
      const h = 1e-6, xp = x.slice(); xp[j] += h;
      const rp = f(xp); J.push(rp.map((v, i) => (v - r[i]) / h));
    }
    const A = Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => J[i].reduce((s, v, k) => s + v * J[j][k], 0)));
    const g = J.map((row) => row.reduce((s, v, k) => s + v * r[k], 0));
    for (let i = 0; i < n; i++) A[i][i] *= 1 + lam;
    // solve A dx = -g (Gaussian elimination)
    const M = A.map((row, i) => [...row, -g[i]]);
    for (let i = 0; i < n; i++) {
      let p = i; for (let k = i + 1; k < n; k++) if (Math.abs(M[k][i]) > Math.abs(M[p][i])) p = k;
      [M[i], M[p]] = [M[p], M[i]];
      for (let k = i + 1; k < n; k++) { const f2 = M[k][i] / M[i][i]; for (let c = i; c <= n; c++) M[k][c] -= f2 * M[i][c]; }
    }
    const dx = new Array(n);
    for (let i = n - 1; i >= 0; i--) { let s = M[i][n]; for (let c = i + 1; c < n; c++) s -= M[i][c] * dx[c]; dx[i] = s / M[i][i]; }
    const xn = x.map((v, i) => v + dx[i]);
    const rn = f(xn), cn = dot(rn, rn);
    if (cn < cost) { x = xn; r = rn; cost = cn; lam = Math.max(lam / 3, 1e-9); if (Math.sqrt(dot(dx, dx)) < 1e-9) break; } else lam *= 4;
  }
  return { x, cost };
}

function run(file, which, opts) {
  const all = JSON.parse(fs.readFileSync(file, 'utf8'));
  const lmsAll = Object.entries(all).filter(([, v]) => v.model && v[which]).map(([name, v]) => ({ name, ...v }));
  const use = opts.use ? opts.use : lmsAll.map((l) => l.name);
  const fit = lmsAll.filter((l) => use.includes(l.name));
  const x0 = opts.freeYaw ? [-0.25, 0.41, 1.3, 0] : [-0.25, 0.41, 1.3];
  const { x } = lm((t) => residuals(t, fit, which, opts.freeYaw), x0);
  const C = x.slice(0, 3), off = opts.freeYaw ? x[3] : 0;
  console.log(`${which} camera (model x fwd, y left, z up): ${C.map((v) => v.toFixed(3)).join(', ')}` + (opts.freeYaw ? `   yaw offset ${(off / D2R).toFixed(2)} deg` : ''));
  let ss = 0;
  for (const l of lmsAll) {
    const m = l[which];
    const b = rotZ(bearing(m.yaw, m.pitch), off), d = norm(sub(l.model, C));
    const ang = Math.acos(Math.max(-1, Math.min(1, dot(b, d)))) / D2R;
    const dist = Math.hypot(...sub(l.model, C));
    // signed components: horizontal (positive = model is to the RIGHT of the photo) and vertical (positive = model is ABOVE)
    const yawM = Math.atan2(-d[1], d[0]) / D2R, pitM = Math.asin(d[2]) / D2R;
    const dy = yawM - (Math.atan2(-b[1], b[0]) / D2R), dp = pitM - (Math.asin(b[2]) / D2R);
    const tag = use.includes(l.name) ? ' ' : '*';
    if (use.includes(l.name)) ss += ang * ang;
    console.log(`${tag} ${l.name.padEnd(16)} d ${dist.toFixed(2)} m   dyaw ${dy.toFixed(2).padStart(6)}  dpitch ${dp.toFixed(2).padStart(6)}  = ${(dist * Math.tan(Math.abs(ang) * D2R) * 1000).toFixed(0).padStart(4)} mm   (dx ${(dist * Math.tan(dy * D2R) * 1000).toFixed(0)} mm, dz ${(dist * Math.tan(dp * D2R) * 1000).toFixed(0)} mm)`);
  }
  console.log(`fit rms ${Math.sqrt(ss / Math.max(1, fit.length)).toFixed(3)} deg over ${fit.length} landmarks  (* = held out)`);
  return { C, off };
}

if (require.main === module && process.argv[2] !== 'tri') {
  const a = process.argv.slice(2);
  const opts = { freeYaw: a.includes('--free-yaw'), use: a.includes('--use') ? a[a.indexOf('--use') + 1].split(',') : null };
  run(a[0], a[1], opts);
}
module.exports = { run, bearing, lm };

// ---- triangulation: where a landmark read in BOTH panoramas really is (independent of our model) ----------------------
//   node scripts/photo-tools/pano_solve.cjs tri <landmarks.json> <cams.json>
// Midpoint of the two rays (front camera, back camera); prints the ray gap (a consistency check) and, where our model has
// the landmark, our position and the difference (x forward, y left, z up, mm).
if (require.main === module && process.argv[2] === 'tri') {
  const lms = JSON.parse(fs.readFileSync(process.argv[3], 'utf8')), cams = JSON.parse(fs.readFileSync(process.argv[4], 'utf8'));
  const A = cams.front.pos, B = cams.back.pos;
  for (const [name, l] of Object.entries(lms)) {
    if (!l.front || !l.back) continue;
    const d1 = bearing(l.front.yaw, l.front.pitch), d2 = bearing(l.back.yaw, l.back.pitch);
    const w = sub(A, B), a = dot(d1, d1), b = dot(d1, d2), c = dot(d2, d2), d = dot(d1, w), e = dot(d2, w);
    const den = a * c - b * b, s = (b * e - c * d) / den, t = (a * e - b * d) / den;
    const p1 = A.map((v, i) => v + s * d1[i]), p2 = B.map((v, i) => v + t * d2[i]);
    const mid = p1.map((v, i) => (v + p2[i]) / 2);
    const gap = Math.hypot(...sub(p1, p2)) * 1000;
    let line = `${name.padEnd(12)} at ${mid.map((v) => v.toFixed(3)).join(', ')}   ray gap ${gap.toFixed(0)} mm   (front ray ${s.toFixed(2)} m, back ray ${t.toFixed(2)} m)`;
    if (l.model) line += `\n${''.padEnd(12)} ours ${l.model.map((v) => v.toFixed(3)).join(', ')}   target - ours: ${mid.map((v, i) => ((v - l.model[i]) * 1000).toFixed(0)).join(', ')} mm`;
    console.log(line);
  }
}
