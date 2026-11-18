// Equirectangular panorama helper (XPENG Cabin 360 reference, 2026-11-18).
//
//   node scripts/photo-tools/pano.cjs view <pano.jpg> <out.png> <yaw> <pitch> <fov> [W=1100] [step=2] [marks]
//
// Renders a rectilinear (pinhole) view of an equirectangular panorama and draws a labelled angle grid, so a feature can be
// read off as (yaw, pitch) in degrees. Convention (the xpeng.guru viewer's): yaw 0 = straight ahead (the image centre),
// positive yaw = to the RIGHT, pitch positive = up. `fov` is the HORIZONTAL field of view. `marks` is an optional
// "yaw,pitch,label;yaw,pitch,label" list drawn as crosshairs (to check a reading).
//
//   node scripts/photo-tools/pano.cjs rect <pano.jpg> <out.png> <yaw> <pitch> <fov> [W=1100]      same, no grid
//
// Library use: const P = require('./pano.cjs'); const pano = await P.load(path); P.render(pano, yaw, pitch, fov, W, H)
const path = require('path');
const sharp = require(path.join(__dirname, '..', '..', 'node_modules', 'sharp'));

const D2R = Math.PI / 180;

async function load(file) {
  const { data, info } = await sharp(file).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  return { w: info.width, h: info.height, data };
}

/** Basis of a camera looking at (yaw, pitch): forward, right, up in the pano frame (x right, y up, z forward at yaw 0). */
function basis(yaw, pitch) {
  const y = yaw * D2R, p = pitch * D2R;
  const f = [Math.cos(p) * Math.sin(y), Math.sin(p), Math.cos(p) * Math.cos(y)];
  const r = [Math.cos(y), 0, -Math.sin(y)];
  const u = [-Math.sin(p) * Math.sin(y), Math.cos(p), -Math.sin(p) * Math.cos(y)];
  return { f, r, u };
}

/** Bilinear sample of a panorama in direction (dx, dy, dz) of the pano frame. Returns [r, g, b]. */
function sample(P, dx, dy, dz, out, o) {
  const lon = Math.atan2(dx, dz), lat = Math.atan2(dy, Math.hypot(dx, dz));
  const U = (lon / (2 * Math.PI) + 0.5) * P.w - 0.5, V = (0.5 - lat / Math.PI) * P.h - 0.5;
  let x0 = Math.floor(U), y0 = Math.floor(V);
  const fx = U - x0, fy = V - y0;
  x0 = ((x0 % P.w) + P.w) % P.w;
  const x1 = (x0 + 1) % P.w;
  y0 = Math.max(0, Math.min(P.h - 1, y0));
  const y1 = Math.min(P.h - 1, y0 + 1);
  const d = P.data;
  const i00 = (y0 * P.w + x0) * 3, i10 = (y0 * P.w + x1) * 3, i01 = (y1 * P.w + x0) * 3, i11 = (y1 * P.w + x1) * 3;
  for (let c = 0; c < 3; c++) {
    out[o + c] = (d[i00 + c] * (1 - fx) + d[i10 + c] * fx) * (1 - fy) + (d[i01 + c] * (1 - fx) + d[i11 + c] * fx) * fy;
  }
}

/** Rectilinear render -> raw RGB Buffer (W x H). fov = horizontal fov in degrees. */
function render(P, yaw, pitch, fov, W, H) {
  const { f, r, u } = basis(yaw, pitch);
  const t = Math.tan((fov * D2R) / 2);
  const buf = Buffer.alloc(W * H * 3);
  for (let y = 0; y < H; y++) {
    const sy = (1 - (2 * (y + 0.5)) / H) * t * (H / W);
    for (let x = 0; x < W; x++) {
      const sx = ((2 * (x + 0.5)) / W - 1) * t;
      sample(P, f[0] + sx * r[0] + sy * u[0], f[1] + sx * r[1] + sy * u[1], f[2] + sx * r[2] + sy * u[2], buf, (y * W + x) * 3);
    }
  }
  return buf;
}

/** Project a pano direction (yaw, pitch in degrees) into a view; null when behind the camera. */
function project(yaw, pitch, vy, vp, fov, W, H) {
  const { f, r, u } = basis(vy, vp);
  const t = Math.tan((fov * D2R) / 2);
  const d = basis(yaw, pitch).f;
  const df = d[0] * f[0] + d[1] * f[1] + d[2] * f[2];
  if (df <= 1e-6) return null;
  const sx = (d[0] * r[0] + d[1] * r[1] + d[2] * r[2]) / df / t;
  const sy = (d[0] * u[0] + d[1] * u[1] + d[2] * u[2]) / df / t / (H / W);
  return [((sx + 1) / 2) * W, ((1 - sy) / 2) * H];
}

function gridSvg(vy, vp, fov, W, H, step, marks) {
  let s = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">`;
  const vfov = (2 * Math.atan(Math.tan((fov * D2R) / 2) * (H / W))) / D2R;
  const ymin = Math.floor((vy - fov * 0.75) / step) * step, ymax = Math.ceil((vy + fov * 0.75) / step) * step;
  const pmin = Math.max(-89, Math.floor((vp - vfov * 0.75) / step) * step), pmax = Math.min(89, Math.ceil((vp + vfov * 0.75) / step) * step);
  const major = (v) => Math.abs(v % (step * 5)) < 1e-6;
  const line = (pts, major_, label, lx, ly) => {
    const seg = [];
    let cur = [];
    for (const p of pts) { if (p) cur.push(p); else if (cur.length) { seg.push(cur); cur = []; } }
    if (cur.length) seg.push(cur);
    for (const c of seg) {
      s += `<polyline points="${c.map((p) => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join(' ')}" fill="none" stroke="#00ffff" stroke-opacity="${major_ ? 0.75 : 0.3}" stroke-width="${major_ ? 1.6 : 0.7}"/>`;
    }
    // labels where the line meets the frame edges: yaw lines top + bottom, pitch lines left + right
    const txt = (x, y, anchor) => `<text x="${x.toFixed(1)}" y="${y.toFixed(1)}" text-anchor="${anchor}" font-family="Arial" font-weight="bold" font-size="${major_ ? 17 : 14}" fill="#ffee00" stroke="#000" stroke-width="3" paint-order="stroke">${label}</text>`;
    const pick = (score) => {
      let best = null;
      for (const c of seg) for (const p of c) {
        if (p[0] < 0 || p[0] > W || p[1] < 0 || p[1] > H) continue;
        const sc = score(p);
        if (!best || sc < best.sc) best = { p, sc };
      }
      return best;
    };
    if (lx !== null) {
      const a = pick((p) => p[1]), b = pick((p) => H - p[1]);
      if (a) s += txt(a.p[0], 18, 'middle');
      if (b) s += txt(b.p[0], H - 6, 'middle');
    } else {
      const a = pick((p) => p[0]), b = pick((p) => W - p[0]);
      if (a) s += txt(4, a.p[1] + 5, 'start');
      if (b) s += txt(W - 4, b.p[1] + 5, 'end');
    }
  };
  for (let yv = ymin; yv <= ymax; yv += step) {
    const pts = [];
    for (let pv = pmin; pv <= pmax; pv += 1) pts.push(project(yv, pv, vy, vp, fov, W, H));
    line(pts, major(((yv % 360) + 360) % 360 > 180 ? yv - 360 : yv), String(yv), 0, null);
  }
  for (let pv = pmin; pv <= pmax; pv += step) {
    const pts = [];
    for (let yv = ymin; yv <= ymax; yv += 1) pts.push(project(yv, pv, vy, vp, fov, W, H));
    line(pts, major(pv), String(pv), null, 0);
  }
  for (const m of marks) {
    const p = project(m.yaw, m.pitch, vy, vp, fov, W, H);
    if (!p) continue;
    s += `<g stroke="#ff2a2a" stroke-width="1.4" fill="none"><line x1="${p[0] - 9}" y1="${p[1]}" x2="${p[0] + 9}" y2="${p[1]}"/><line x1="${p[0]}" y1="${p[1] - 9}" x2="${p[0]}" y2="${p[1] + 9}"/><circle cx="${p[0]}" cy="${p[1]}" r="4"/></g>`;
    s += `<text x="${p[0] + 7}" y="${p[1] - 6}" font-size="12" fill="#ff5050" stroke="#000" stroke-width="0.4">${m.label || ''}</text>`;
  }
  return s + '</svg>';
}

async function toPng(buf, W, H, out, svg) {
  let img = sharp(buf, { raw: { width: W, height: H, channels: 3 } });
  if (svg) img = img.composite([{ input: Buffer.from(svg), left: 0, top: 0 }]);
  await img.png().toFile(out);
}

/** Inverse of project(): a pixel (x, y) of a view -> pano (yaw, pitch) in degrees. */
function unproject(x, y, vy, vp, fov, W, H) {
  const { f, r, u } = basis(vy, vp);
  const t = Math.tan((fov * D2R) / 2);
  const sx = ((2 * x) / W - 1) * t, sy = (1 - (2 * y) / H) * t * (H / W);
  const d = [f[0] + sx * r[0] + sy * u[0], f[1] + sx * r[1] + sy * u[1], f[2] + sx * r[2] + sy * u[2]];
  return [Math.atan2(d[0], d[2]) / D2R, Math.atan2(d[1], Math.hypot(d[0], d[2])) / D2R];
}

module.exports = { load, render, project, unproject, basis, sample, gridSvg, toPng };

// node pano.cjs pix <yaw> <pitch> <fov> <W> "x,y,name;x,y,name"   -> (yaw, pitch) of view pixels (H = 0.75 W)
if (require.main === module && process.argv[2] === 'pix') {
  const [, , , vy, vp, fov, w, list] = process.argv;
  const W = +w, H = Math.round(W * 0.75);
  for (const it of list.split(';').filter(Boolean)) {
    const [x, y, ...n] = it.split(',');
    const [yw, pt] = unproject(+x, +y, +vy, +vp, +fov, W, H);
    console.log(JSON.stringify({ name: n.join(','), yaw: +yw.toFixed(3), pitch: +pt.toFixed(3) }));
  }
  process.exit(0);
}

if (require.main === module) {
  (async () => {
    const [cmd, file, out, yaw, pitch, fov, w, step, marksArg] = process.argv.slice(2);
    if (!['view', 'rect'].includes(cmd) || !out) { console.log('usage: see the header of this file'); process.exit(1); }
    const W = +(w || 1100), H = Math.round(W * 0.75);
    const P = await load(file);
    const buf = render(P, +yaw, +pitch, +fov, W, H);
    let svg = null;
    if (cmd === 'view') {
      const marks = (marksArg || '').split(';').filter(Boolean).map((m) => { const [y, p, ...l] = m.split(','); return { yaw: +y, pitch: +p, label: l.join(',') }; });
      svg = gridSvg(+yaw, +pitch, +fov, W, H, +(step || 2), marks);
    }
    await toPng(buf, W, H, out, svg);
    console.log('ok', out, W + 'x' + H);
  })();
}
