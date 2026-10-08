// node segment.cjs <uw.jpg> <out.json> [key=value ...]
//
// Outlines of one repeat of a wheel face, read automatically. The unwarped photograph (unwarp.cjs: the
// lip a circle of radius 0.45 of the image) is unrolled into polar coordinates and the n repeats of the
// pattern are laid over each other: a pixel belongs to a class (silver, black, matte grey ...) if it does
// in MORE THAN HALF of the repeats, so a glare, a reflection or a tyre letter on one spoke is voted out.
// The outlines of the voted mask are then traced (marching squares) and simplified, and written as
// polygons of (angle in degrees counter-clockwise from 3 o'clock, radius / lip radius) - the file
// polyover.cjs and polar.cjs draw and carkit/parts/wheels.py cuts.
//
//   keys (defaults)
//     t0=0        start of the repeat window, degrees (the window is one period wide; pick a gap)
//     period=72   degrees per repeat (360 / the number of spokes)
//     r0=0.2 r1=1.0     radius range (fractions of the lip radius)
//     ppd=8 ppr=800     pixels per degree and per unit radius of the working grid
//     lum=lo:hi   luminance range of the class, 0-255 (of the photo as given: lift it first if dark)
//     sat=lo:hi   saturation range, 0-255 ((max-min)/max)
//     blur=1.2    Gaussian blur of the photo before reading it, pixels
//     open=1 close=1    morphological clean-up radii of the voted mask, pixels
//     minarea=40  smallest outline kept, grid pixels
//     eps=2       simplification tolerance, grid pixels
//     invert=0    1 = trace the complement of the class (its holes become the shapes)
//     preview=out.png   the mean picture of one repeat with the outlines over it (outlines=0: without)
//     grid=5            the preview's grid step in degrees
const sharp = require('sharp');
const fs = require('fs');

(async () => {
  const [src, out] = process.argv.slice(2, 4);
  const kv = Object.fromEntries(process.argv.slice(4).map((s) => { const i = s.indexOf('='); return [s.slice(0, i), s.slice(i + 1)]; }));
  const T0 = +(kv.t0 ?? 0), PER = +(kv.period ?? 72), R0 = +(kv.r0 ?? 0.2), R1 = +(kv.r1 ?? 1.0);
  const PPD = +(kv.ppd ?? 8), PPR = +(kv.ppr ?? 800);
  const [lumLo, lumHi] = (kv.lum ?? '0:255').split(':').map(Number);
  const [satLo, satHi] = (kv.sat ?? '0:255').split(':').map(Number);
  const blur = +(kv.blur ?? 1.2), OPEN = +(kv.open ?? 1), CLOSE = +(kv.close ?? 1);
  const MINA = +(kv.minarea ?? 40), EPS = +(kv.eps ?? 2), INV = +(kv.invert ?? 0);
  const reps = Math.round(360 / PER);

  let img = sharp(src).removeAlpha();
  if (blur > 0.3) img = img.blur(blur);
  const { data, info } = await img.raw().toBuffer({ resolveWithObject: true });
  const S = info.width, ch = info.channels, c = S / 2, R = S * 0.45;
  const px = (x, y, k) => {
    x = Math.max(0, Math.min(S - 1.001, x)); y = Math.max(0, Math.min(S - 1.001, y));
    const xi = Math.floor(x), yi = Math.floor(y), fx = x - xi, fy = y - yi;
    const g = (xx, yy) => data[(yy * S + xx) * ch + k];
    return (g(xi, yi) * (1 - fx) + g(xi + 1, yi) * fx) * (1 - fy) + (g(xi, yi + 1) * (1 - fx) + g(xi + 1, yi + 1) * fx) * fy;
  };

  // the window: three periods wide, so that a shape crossing the repeat's edge is whole in the middle one
  const W = Math.round(3 * PER * PPD), H = Math.round((R1 - R0) * PPR);
  const V = new Float32Array(W * H);
  const mean = new Float32Array(W * H * 3);
  for (let j = 0; j < H; j++) {
    const r = R1 - j / PPR;
    for (let i = 0; i < W; i++) {
      const th0 = T0 - PER + i / PPD;
      let vote = 0, rs = 0, gs = 0, bs = 0;
      for (let q = 0; q < reps; q++) {
        const th = (th0 + q * PER) * Math.PI / 180;
        const x = c + R * r * Math.cos(th), y = c - R * r * Math.sin(th);
        const rr = px(x, y, 0), gg = px(x, y, 1), bb = px(x, y, 2);
        const mx = Math.max(rr, gg, bb), mn = Math.min(rr, gg, bb);
        const lum = 0.2126 * rr + 0.7152 * gg + 0.0722 * bb, sat = mx > 0 ? 255 * (mx - mn) / mx : 0;
        if (lum >= lumLo && lum <= lumHi && sat >= satLo && sat <= satHi) vote++;
        rs += rr; gs += gg; bs += bb;
      }
      V[j * W + i] = vote / reps;
      const o = (j * W + i) * 3;
      mean[o] = rs / reps; mean[o + 1] = gs / reps; mean[o + 2] = bs / reps;
    }
  }

  // binary mask, morphology
  let B = new Uint8Array(W * H);
  for (let k = 0; k < W * H; k++) B[k] = (V[k] > 0.5) !== !!INV ? 1 : 0;
  const morph = (A, rad, grow) => {
    if (rad < 1) return A;
    const O = new Uint8Array(W * H);
    for (let j = 0; j < H; j++) for (let i = 0; i < W; i++) {
      let hit = grow ? 0 : 1;
      for (let dj = -rad; dj <= rad && (grow ? !hit : hit); dj++) for (let di = -rad; di <= rad; di++) {
        const jj = j + dj, ii = i + di;
        const v = (jj < 0 || jj >= H || ii < 0 || ii >= W) ? 0 : A[jj * W + ii];
        if (grow && v) { hit = 1; break; }
        if (!grow && !v) { hit = 0; break; }
      }
      O[j * W + i] = hit;
    }
    return O;
  };
  B = morph(morph(B, OPEN, false), OPEN, true);
  B = morph(morph(B, CLOSE, true), CLOSE, false);

  // a smooth field for the contours: the mask blurred by a 3 x 3 box
  const F = new Float32Array(W * H);
  for (let j = 0; j < H; j++) for (let i = 0; i < W; i++) {
    let s = 0, n = 0;
    for (let dj = -1; dj <= 1; dj++) for (let di = -1; di <= 1; di++) {
      const jj = j + dj, ii = i + di;
      if (jj < 0 || jj >= H || ii < 0 || ii >= W) continue;
      s += B[jj * W + ii]; n++;
    }
    F[j * W + i] = s / n;
  }

  // marching squares at 0.5
  const segs = new Map(); // edge id -> [segment indices]
  const edges = []; // each segment: [edgeA, edgeB, ptA, ptB]
  const eid = (t, i, j) => `${t},${i},${j}`;
  const lerp = (a, b, va, vb) => (0.5 - va) / (vb - va) * (b - a) + a;
  const add = (ea, eb, pa, pb) => {
    const k = edges.length; edges.push([ea, eb, pa, pb]);
    for (const e of [ea, eb]) { if (!segs.has(e)) segs.set(e, []); segs.get(e).push(k); }
  };
  for (let j = 0; j < H - 1; j++) for (let i = 0; i < W - 1; i++) {
    const a = F[j * W + i], b = F[j * W + i + 1], d = F[(j + 1) * W + i], e = F[(j + 1) * W + i + 1];
    let idx = (a > 0.5 ? 1 : 0) | (b > 0.5 ? 2 : 0) | (e > 0.5 ? 4 : 0) | (d > 0.5 ? 8 : 0);
    if (idx === 0 || idx === 15) continue;
    // edge points: top (a-b), right (b-e), bottom (d-e), left (a-d)
    const top = () => [eid('h', i, j), [lerp(i, i + 1, a, b), j]];
    const right = () => [eid('v', i + 1, j), [i + 1, lerp(j, j + 1, b, e)]];
    const bottom = () => [eid('h', i, j + 1), [lerp(i, i + 1, d, e), j + 1]];
    const left = () => [eid('v', i, j), [i, lerp(j, j + 1, a, d)]];
    const link = (p, q) => add(p[0], q[0], p[1], q[1]);
    switch (idx) {
      case 1: case 14: link(left(), top()); break;
      case 2: case 13: link(top(), right()); break;
      case 3: case 12: link(left(), right()); break;
      case 4: case 11: link(right(), bottom()); break;
      case 6: case 9: link(top(), bottom()); break;
      case 7: case 8: link(left(), bottom()); break;
      case 5: case 10: {
        const centre = (a + b + d + e) / 4 > 0.5;
        if ((idx === 5) === centre) { link(left(), top()); link(right(), bottom()); } else { link(top(), right()); link(left(), bottom()); }
        break;
      }
    }
  }
  const used = new Array(edges.length).fill(false);
  const loops = [];
  for (let s = 0; s < edges.length; s++) {
    if (used[s]) continue;
    used[s] = true;
    const pts = [edges[s][2]];
    let cur = edges[s][1], pt = edges[s][3];
    const first = edges[s][0];
    let guard = 0;
    while (cur !== first && guard++ < 1e6) {
      pts.push(pt);
      const nx = (segs.get(cur) || []).find((k) => !used[k]);
      if (nx === undefined) break;
      used[nx] = true;
      if (edges[nx][0] === cur) { cur = edges[nx][1]; pt = edges[nx][3]; } else { cur = edges[nx][0]; pt = edges[nx][2]; }
    }
    if (pts.length > 4) loops.push(pts);
  }

  const area = (p) => { let s = 0; for (let i = 0; i < p.length; i++) { const q = p[(i + 1) % p.length]; s += p[i][0] * q[1] - q[0] * p[i][1]; } return 0.5 * s; };
  const rdp = (p, eps) => {
    // closed polygon: split at the two farthest apart points, simplify each half
    const n = p.length; let a = 0, b = 0, best = -1;
    for (let i = 0; i < n; i += Math.max(1, Math.floor(n / 60))) for (let j = i + 1; j < n; j += Math.max(1, Math.floor(n / 60))) {
      const d = (p[i][0] - p[j][0]) ** 2 + (p[i][1] - p[j][1]) ** 2; if (d > best) { best = d; a = i; b = j; }
    }
    const half = (pts) => {
      if (pts.length < 3) return pts;
      const A = pts[0], Bp = pts[pts.length - 1]; let md = -1, mi = 0;
      const dx = Bp[0] - A[0], dy = Bp[1] - A[1], L = Math.hypot(dx, dy) || 1e-9;
      for (let i = 1; i < pts.length - 1; i++) { const d = Math.abs(dy * (pts[i][0] - A[0]) - dx * (pts[i][1] - A[1])) / L; if (d > md) { md = d; mi = i; } }
      if (md <= eps) return [A, Bp];
      return half(pts.slice(0, mi + 1)).slice(0, -1).concat(half(pts.slice(mi)));
    };
    const h1 = half(p.slice(Math.min(a, b), Math.max(a, b) + 1));
    const h2 = half(p.slice(Math.max(a, b)).concat(p.slice(0, Math.min(a, b) + 1)));
    return h1.slice(0, -1).concat(h2.slice(0, -1));
  };

  // nesting depth by ray casting: an outline inside an odd number of others is a hole
  const inside = (pt, poly) => {
    let c2 = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      if (((poly[i][1] > pt[1]) !== (poly[j][1] > pt[1])) &&
          (pt[0] < (poly[j][0] - poly[i][0]) * (pt[1] - poly[i][1]) / (poly[j][1] - poly[i][1]) + poly[i][0])) c2 = !c2;
    }
    return c2;
  };
  const polys = [];
  for (const L of loops) {
    const A = area(L);
    if (Math.abs(A) < MINA) continue;
    const cx = L.reduce((s, p) => s + p[0], 0) / L.length;
    const th = T0 - PER + cx / PPD;
    if (th < T0 || th >= T0 + PER) continue;
    let depth = 0;
    for (const M of loops) if (M !== L && Math.abs(area(M)) > Math.abs(A) && inside(L[0], M)) depth++;
    const S2 = rdp(L, EPS);
    polys.push({ name: 'p' + polys.length, hole: depth % 2 === 1, area: Math.abs(A) / (PPD * PPR),
      pts: S2.map(([x, y]) => [+(T0 - PER + x / PPD).toFixed(2), +(R1 - y / PPR).toFixed(4)]) });
  }
  polys.sort((p, q) => q.area - p.area);
  polys.forEach((p, k) => { p.name = (p.hole ? 'hole' : 'shape') + k; });
  fs.writeFileSync(out, JSON.stringify({ period: PER, source: src, polys }, null, 0));
  console.log(out, polys.length, 'outlines;', polys.map((p) => `${p.name}:${p.pts.length}pts`).join(' '));

  if (kv.preview) {
    // the mean picture of one repeat (the middle window) with the outlines over it, a labelled grid
    const x0 = Math.round(PER * PPD), PW = Math.round(PER * PPD);
    const buf = Buffer.alloc(PW * H * 3);
    for (let j = 0; j < H; j++) for (let i = 0; i < PW; i++) for (let k = 0; k < 3; k++) buf[(j * PW + i) * 3 + k] = mean[(j * W + x0 + i) * 3 + k];
    const parts = [];
    const GS = +(kv.grid ?? 5);
    for (let a = Math.ceil(T0 / GS) * GS; a < T0 + PER; a += GS) {
      const x = (a - T0) * PPD;
      parts.push(`<line x1="${x}" y1="0" x2="${x}" y2="${H}" stroke="#ffea00" stroke-opacity="0.3"/><text x="${x + 2}" y="12" font-size="12" fill="#ffea00" font-family="Arial">${a}</text>`);
    }
    for (let r = Math.ceil(R0 / 0.05) * 0.05; r <= R1 + 1e-9; r += 0.05) {
      const y = (R1 - r) * PPR;
      parts.push(`<line x1="0" y1="${y}" x2="${PW}" y2="${y}" stroke="#00e5ff" stroke-opacity="0.3"/><text x="2" y="${y - 2}" font-size="12" fill="#00e5ff" font-family="Arial">${r.toFixed(2)}</text>`);
    }
    const cols = ['#ff00ff', '#00ff66', '#ff8800', '#00aaff', '#ffffff', '#ffea00'];
    if (kv.outlines !== '0') polys.forEach((p, pi) => {
      const d = p.pts.map(([a, r], i) => (i ? 'L' : 'M') + ((a - T0) * PPD).toFixed(1) + ' ' + ((R1 - r) * PPR).toFixed(1)).join(' ') + ' Z';
      parts.push(`<path d="${d}" fill="none" stroke="${cols[pi % cols.length]}" stroke-width="1.6"/>`);
    });
    const svg = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${PW}" height="${H}">${parts.join('')}</svg>`);
    await sharp(buf, { raw: { width: PW, height: H, channels: 3 } }).composite([{ input: svg }]).png().toFile(kv.preview);
    console.log(kv.preview, PW + 'x' + H);
  }
})();
