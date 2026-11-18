// A/B sheets: the target panorama and our equirect render cut into the SAME rectilinear views (2026-11-18, xpeng.guru benchmark).
//
//   node scripts/photo-tools/pano_ab.cjs <target.jpg> <ours.png> <outPrefix> "<name>:<yaw>:<pitch>:<fov>,..." [W=760]
//
// One <outPrefix>_<name>.png per view: top row target | ours, bottom row edges (red = target, cyan = ours, on our render) |
// 50/50 blend. Prints, per view, the tonal statistics of both (luma p5 / p50 / p95, saturation, fine-detail energy `hf`).
const path = require('path');
const sharp = require(path.join(__dirname, '..', '..', 'node_modules', 'sharp'));
const P = require('./pano.cjs');

function lumaOf(buf, n) { const Y = new Float32Array(n); for (let i = 0; i < n; i++) Y[i] = 0.2126 * buf[i * 3] + 0.7152 * buf[i * 3 + 1] + 0.0722 * buf[i * 3 + 2]; return Y; }

function stats(buf, W, H) {
  const n = W * H, Y = lumaOf(buf, n);
  const s = Float32Array.from(Y).sort(), q = (f) => s[Math.floor(f * (n - 1))];
  let sat = 0; for (let i = 0; i < n; i++) { const r = buf[i * 3], g = buf[i * 3 + 1], b = buf[i * 3 + 2], mx = Math.max(r, g, b), mn = Math.min(r, g, b); sat += mx ? (mx - mn) / mx : 0; }
  const I = new Float64Array((W + 1) * (H + 1));
  for (let y = 0; y < H; y++) { let row = 0; for (let x = 0; x < W; x++) { row += Y[y * W + x]; I[(y + 1) * (W + 1) + x + 1] = I[y * (W + 1) + x + 1] + row; } }
  const R = 3; let hf = 0, c = 0;
  for (let y = R; y < H - R; y += 2) for (let x = R; x < W - R; x += 2) {
    const a = I[(y + R + 1) * (W + 1) + x + R + 1] - I[(y - R) * (W + 1) + x + R + 1] - I[(y + R + 1) * (W + 1) + x - R] + I[(y - R) * (W + 1) + x - R];
    hf += Math.abs(Y[y * W + x] - a / ((2 * R + 1) * (2 * R + 1))); c++;
  }
  return { p5: Math.round(q(0.05)), p50: Math.round(q(0.5)), p95: Math.round(q(0.95)), sat: +(sat / n).toFixed(3), hf: +(hf / c).toFixed(2) };
}

/** Edge mask (top ~8% of the Sobel magnitude of a lightly blurred luma). */
function edges(buf, W, H) {
  const Y = lumaOf(buf, W * H), B = new Float32Array(W * H);
  for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) { let s = 0; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) s += Y[(y + dy) * W + x + dx]; B[y * W + x] = s / 9; }
  const M = new Float32Array(W * H);
  for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) {
    const i = y * W + x;
    const gx = -B[i - W - 1] - 2 * B[i - 1] - B[i + W - 1] + B[i - W + 1] + 2 * B[i + 1] + B[i + W + 1];
    const gy = -B[i - W - 1] - 2 * B[i - W] - B[i - W + 1] + B[i + W - 1] + 2 * B[i + W] + B[i + W + 1];
    M[i] = Math.hypot(gx, gy);
  }
  const s = Float32Array.from(M).sort(), t = s[Math.floor(0.92 * s.length)];
  return M.map((v) => (v >= t && v > 8 ? 1 : 0));
}

async function main() {
  const [tFile, oFile, prefix, viewsArg, w] = process.argv.slice(2);
  const W = +(w || 760), H = Math.round(W * 0.75);
  const T = await P.load(tFile), O = await P.load(oFile);
  for (const v of viewsArg.split(',')) {
    const [name, yaw, pitch, fov] = v.split(':');
    const a = P.render(T, +yaw, +pitch, +fov, W, H), b = P.render(O, +yaw, +pitch, +fov, W, H);
    const ea = edges(a, W, H), eb = edges(b, W, H);
    const sheet = Buffer.alloc(2 * W * 2 * H * 3);
    const put = (px, ox, oy) => { for (let y = 0; y < H; y++) px(y, (x, r, g, bl) => { const o = ((oy + y) * 2 * W + ox + x) * 3; sheet[o] = r; sheet[o + 1] = g; sheet[o + 2] = bl; }); };
    put((y, set) => { for (let x = 0; x < W; x++) { const i = (y * W + x) * 3; set(x, a[i], a[i + 1], a[i + 2]); } }, 0, 0);
    put((y, set) => { for (let x = 0; x < W; x++) { const i = (y * W + x) * 3; set(x, b[i], b[i + 1], b[i + 2]); } }, W, 0);
    put((y, set) => { for (let x = 0; x < W; x++) { const i = y * W + x, j = i * 3, g = 0.299 * b[j] + 0.587 * b[j + 1] + 0.114 * b[j + 2]; let r = g * 0.55, gg = g * 0.55, bb = g * 0.55;
      if (eb[i]) { r = 40; gg = 235; bb = 255; } if (ea[i]) { r = 255; gg = 40; bb = 40; } set(x, r, gg, bb); } }, 0, H);
    put((y, set) => { for (let x = 0; x < W; x++) { const j = (y * W + x) * 3; set(x, (a[j] + b[j]) / 2, (a[j + 1] + b[j + 1]) / 2, (a[j + 2] + b[j + 2]) / 2); } }, W, H);
    const sa = stats(a, W, H), sb = stats(b, W, H);
    const lab = (t, x, y) => `<text x="${x}" y="${y}" font-family="Arial" font-weight="bold" font-size="20" fill="#fff" stroke="#000" stroke-width="4" paint-order="stroke">${t}</text>`;
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${2 * W}" height="${2 * H}">${lab('TARGET (XPENG)', 10, 26)}${lab('OURS (Cycles, hall)', W + 10, 26)}${lab('edges: red target / cyan ours', 10, H + 26)}${lab('50/50', W + 10, H + 26)}${lab(name + '  yaw ' + yaw + ' pitch ' + pitch + ' fov ' + fov, 10, 2 * H - 12)}</svg>`;
    await sharp(sheet, { raw: { width: 2 * W, height: 2 * H, channels: 3 } }).composite([{ input: Buffer.from(svg) }]).png().toFile(`${prefix}_${name}.png`);
    console.log(name.padEnd(10), 'target', JSON.stringify(sa), ' ours', JSON.stringify(sb));
  }
}
main();
