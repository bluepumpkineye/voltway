// Casts rays at a GLB (Draco ok) to find where a surface is: node scripts/tech-tools/glb-rays.mjs public/models/x.glb rays.json
// glb-rays.mjs <file.glb> : load a GLB (Draco ok), flatten every mesh to world-space triangles, then answer ray queries from a
// small script given as JSON on argv[3]: [{ name, o:[x,y,z], d:[x,y,z] }, ...] -> the first hit point of each
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { readFileSync } from 'node:fs';
const root = fileURLToPath(new URL('../../', import.meta.url)).split(String.fromCharCode(92)).join('/').replace(/[/]$/, '');
const require = createRequire(root + '/package.json');
const { NodeIO } = require('@gltf-transform/core');
const { ALL_EXTENSIONS } = require('@gltf-transform/extensions');
const draco3d = require('draco3dgltf');

const file = process.argv[2];
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'draco3d.decoder': await draco3d.createDecoderModule() });
const doc = await io.read(file);

// world matrices (column-major 4x4) per node
function mul(a, b) {
  const o = new Array(16).fill(0);
  for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) for (let k = 0; k < 4; k++) o[c * 4 + r] += a[k * 4 + r] * b[c * 4 + k];
  return o;
}
const tris = [];
const names = [];
function visit(node, parent) {
  const world = mul(parent, node.getMatrix());
  const mesh = node.getMesh();
  if (mesh) {
    for (const prim of mesh.listPrimitives()) {
      const pos = prim.getAttribute('POSITION');
      const idx = prim.getIndices();
      const n = idx ? idx.getCount() : pos.getCount();
      const get = (i) => {
        const p = pos.getElement(i, []);
        return [
          world[0] * p[0] + world[4] * p[1] + world[8] * p[2] + world[12],
          world[1] * p[0] + world[5] * p[1] + world[9] * p[2] + world[13],
          world[2] * p[0] + world[6] * p[1] + world[10] * p[2] + world[14],
        ];
      };
      for (let t = 0; t < n; t += 3) {
        const ia = idx ? idx.getScalar(t) : t, ib = idx ? idx.getScalar(t + 1) : t + 1, ic = idx ? idx.getScalar(t + 2) : t + 2;
        tris.push(get(ia), get(ib), get(ic));
        names.push(node.getName() + '/' + (prim.getMaterial()?.getName() ?? '-'));
      }
    }
  }
  for (const c of node.listChildren()) visit(c, world);
}
const I = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
for (const n of doc.getRoot().listScenes()[0].listChildren()) visit(n, I);

function hit(o, d) {
  let best = Infinity, who = '';
  for (let i = 0; i < tris.length; i += 3) {
    const a = tris[i], b = tris[i + 1], c = tris[i + 2];
    const e1 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], e2 = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
    const p = [d[1] * e2[2] - d[2] * e2[1], d[2] * e2[0] - d[0] * e2[2], d[0] * e2[1] - d[1] * e2[0]];
    const det = e1[0] * p[0] + e1[1] * p[1] + e1[2] * p[2];
    if (Math.abs(det) < 1e-12) continue;
    const s = [o[0] - a[0], o[1] - a[1], o[2] - a[2]];
    const u = (s[0] * p[0] + s[1] * p[1] + s[2] * p[2]) / det;
    if (u < 0 || u > 1) continue;
    const q = [s[1] * e1[2] - s[2] * e1[1], s[2] * e1[0] - s[0] * e1[2], s[0] * e1[1] - s[1] * e1[0]];
    const v = (d[0] * q[0] + d[1] * q[1] + d[2] * q[2]) / det;
    if (v < 0 || u + v > 1) continue;
    const t = (e2[0] * q[0] + e2[1] * q[1] + e2[2] * q[2]) / det;
    if (t > 1e-6 && t < best) { best = t; who = names[i / 3]; }
  }
  return best === Infinity ? null : { p: [o[0] + d[0] * best, o[1] + d[1] * best, o[2] + d[2] * best].map((x) => +x.toFixed(3)), who };
}

let min = [1e9, 1e9, 1e9], max = [-1e9, -1e9, -1e9];
for (const v of tris) for (let k = 0; k < 3; k++) { min[k] = Math.min(min[k], v[k]); max[k] = Math.max(max[k], v[k]); }
console.log('bounds', min.map((x) => +x.toFixed(3)), max.map((x) => +x.toFixed(3)), 'tris', tris.length / 3);
const q = JSON.parse(readFileSync(process.argv[3], 'utf8'));
for (const r of q) console.log(r.name.padEnd(28), JSON.stringify(hit(r.o, r.d)));
