// node unwarp.cjs <img> <cx> <cy> <rGuess> <out.jpg> [size=1400] [mode=bright|dark] [inner=0.80] [outer=1.25]
// Finds the outer edge of the wheel's bright (or dark) lip ring along rays from a rough centre,
// fits an ellipse (robust), and resamples the photo so that ellipse is a circle of radius size*0.45.
// Prints the ellipse and the transform; also writes <out>.json with the affine (x = x0 + Linv*u).
const fs = require('fs');
const sharp = require('sharp');

function solve(A, b) {                       // gaussian elimination, small n
  const n = b.length; const M = A.map((r, i) => r.concat([b[i]]));
  for (let i = 0; i < n; i++) {
    let p = i; for (let r = i + 1; r < n; r++) if (Math.abs(M[r][i]) > Math.abs(M[p][i])) p = r;
    [M[i], M[p]] = [M[p], M[i]];
    for (let r = i + 1; r < n; r++) { const f = M[r][i] / M[i][i]; for (let c = i; c <= n; c++) M[r][c] -= f * M[i][c]; }
  }
  const x = new Array(n).fill(0);
  for (let i = n - 1; i >= 0; i--) { let s = M[i][n]; for (let c = i + 1; c < n; c++) s -= M[i][c] * x[c]; x[i] = s / M[i][i]; }
  return x;
}
function fitConic(pts) {                      // A x^2 + B xy + C y^2 + D x + E y = 1, about the centroid
  const mx = pts.reduce((s, p) => s + p[0], 0) / pts.length, my = pts.reduce((s, p) => s + p[1], 0) / pts.length;
  const N = Array.from({ length: 5 }, () => new Array(5).fill(0)), r = new Array(5).fill(0);
  for (const p of pts) {
    const x = p[0] - mx, y = p[1] - my, f = [x * x, x * y, y * y, x, y];
    for (let i = 0; i < 5; i++) { r[i] += f[i]; for (let j = 0; j < 5; j++) N[i][j] += f[i] * f[j]; }
  }
  const [A, B, C, D, E] = solve(N, r);
  // centre: grad = 0 -> [2A B; B 2C] c = -[D; E]
  const det = 4 * A * C - B * B;
  const cx = (-2 * C * D + B * E) / det, cy = (B * D - 2 * A * E) / det;
  const k = 1 + A * cx * cx + B * cx * cy + C * cy * cy + D * cx + E * cy;     // (x-c)'Q(x-c) = k
  // after substituting x -> x - c the linear terms vanish: A u^2 + B uv + C v^2 = k'
  const kk = 1 + A * cx * cx + B * cx * cy + C * cy * cy + D * cx + E * cy;
  return { x0: mx + cx, y0: my + cy, Q: [[A / kk, B / 2 / kk], [B / 2 / kk, C / kk]] };
}
function symSqrt(Q) {                          // 2x2 symmetric positive definite -> Q^(1/2)
  const a = Q[0][0], b = Q[0][1], c = Q[1][1];
  const tr = a + c, d = a * c - b * b;
  const s = Math.sqrt(d), t = Math.sqrt(tr + 2 * s);
  return [[(a + s) / t, b / t], [b / t, (c + s) / t]];
}
(async () => {
  const [src, cx0, cy0, rg, out, size = 1400, mode = 'bright', inner = 0.8, outer = 1.25] = process.argv.slice(2);
  const { data, info } = await sharp(src).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  const W = info.width, H = info.height, ch = info.channels;
  const lum = (x, y) => {
    x = Math.max(0, Math.min(W - 1.001, x)); y = Math.max(0, Math.min(H - 1.001, y));
    const xi = Math.floor(x), yi = Math.floor(y), fx = x - xi, fy = y - yi;
    const g = (xx, yy) => { const i = (yy * W + xx) * ch; return 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2]; };
    return (g(xi, yi) * (1 - fx) + g(xi + 1, yi) * fx) * (1 - fy) + (g(xi, yi + 1) * (1 - fx) + g(xi + 1, yi + 1) * fx) * fy;
  };
  const cx = +cx0, cy = +cy0, R = +rg;
  let pts = [];
  for (let a = 0; a < 360; a += 2) {
    const th = a * Math.PI / 180, ux = Math.cos(th), uy = Math.sin(th);
    let best = -1e9, br = null;
    const r0 = R * +inner, r1 = R * +outer, step = 2;
    // gradient across +-8 px, outward; bright->dark (tyre outside the ring) = negative gradient
    for (let r = r0; r <= r1; r += step) {
      const g = lum(cx + ux * (r + 8), cy + uy * (r + 8)) - lum(cx + ux * (r - 8), cy + uy * (r - 8));
      const score = mode === 'bright' ? -g : g;
      if (score > best) { best = score; br = r; }
    }
    if (best > 25) pts.push([cx + ux * br, cy + uy * br, a, best]);
  }
  let fit = null, used = pts;
  for (let it = 0; it < 4; it++) {
    fit = fitConic(used);
    const L = symSqrt(fit.Q);
    const res = pts.map(p => { const dx = p[0] - fit.x0, dy = p[1] - fit.y0; const u = L[0][0] * dx + L[0][1] * dy, v = L[1][0] * dx + L[1][1] * dy; return Math.abs(Math.hypot(u, v) - 1); });
    const sd = Math.sqrt(res.reduce((s, e) => s + e * e, 0) / res.length);
    used = pts.filter((p, i) => res[i] < Math.max(2.2 * sd, 0.004));
  }
  const L = symSqrt(fit.Q);
  const det = L[0][0] * L[1][1] - L[0][1] * L[1][0];
  const Li = [[L[1][1] / det, -L[0][1] / det], [-L[1][0] / det, L[0][0] / det]];
  // axes of the ellipse
  const ev = (() => { const a = fit.Q[0][0], b = fit.Q[0][1], c = fit.Q[1][1]; const t = (a + c) / 2, d = Math.sqrt(((a - c) / 2) ** 2 + b * b); return [1 / Math.sqrt(t + d), 1 / Math.sqrt(t - d)]; })();
  console.log(JSON.stringify({ pts: pts.length, used: used.length, x0: +fit.x0.toFixed(1), y0: +fit.y0.toFixed(1), semiMajor: +Math.max(...ev).toFixed(1), semiMinor: +Math.min(...ev).toFixed(1), ratio: +(Math.min(...ev) / Math.max(...ev)).toFixed(3) }));
  const S = +size, rad = S * 0.45;               // lip radius in the output
  const buf = Buffer.alloc(S * S * 3);
  const px = (x, y, c) => {
    x = Math.max(0, Math.min(W - 1.001, x)); y = Math.max(0, Math.min(H - 1.001, y));
    const xi = Math.floor(x), yi = Math.floor(y), fx = x - xi, fy = y - yi;
    const g = (xx, yy) => data[(yy * W + xx) * ch + c];
    return (g(xi, yi) * (1 - fx) + g(xi + 1, yi) * fx) * (1 - fy) + (g(xi, yi + 1) * (1 - fx) + g(xi + 1, yi + 1) * fx) * fy;
  };
  for (let j = 0; j < S; j++) for (let i = 0; i < S; i++) {
    const u = (i - S / 2 + 0.5) / rad, v = (j - S / 2 + 0.5) / rad;
    const x = fit.x0 + Li[0][0] * u + Li[0][1] * v, y = fit.y0 + Li[1][0] * u + Li[1][1] * v;
    const o = (j * S + i) * 3;
    for (let c = 0; c < 3; c++) buf[o + c] = px(x, y, c);
  }
  await sharp(buf, { raw: { width: S, height: S, channels: 3 } }).jpeg({ quality: 90 }).toFile(out);
  fs.writeFileSync(out.replace(/\.jpg$/, '.json'), JSON.stringify({ x0: fit.x0, y0: fit.y0, Li, L, size: S, rad }));
  console.log(out);
})();
