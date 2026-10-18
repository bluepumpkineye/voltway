// A small stand-in of a car for a showroom stage (the parked neighbours of a Tech demo).
//
//   node scripts/make-proxy.mjs luxeed-rx          -> public/models/luxeed-rx-proxy.glb
//   node scripts/make-proxy.mjs --all
//
// It reads the shipped exterior, bakes every node's transform into the vertices and keeps three things:
// the paint panels (every M_Paint* material), the window glass, and the tyres and rims of the default
// wheels. Each is welded, given smooth normals and simplified with meshoptimizer to a triangle budget, and
// written as one primitive under a plain material name the viewer recolours (TechStage.tsx): Paint, Glass,
// Tyre, Rim. Draco-compressed, about 65 KB and 20k triangles a car, against the 400-500k of the real one.
//
// What does not work, and why it is not here: thinning the black underlay or the trim next to the paint
// (they sit 3 mm under it, so the thinned layers cut through one another and show as black shards), and
// using the "shadow shell" (M_Shadow) as the hull (it is several overlapping pieces, not one surface).
// Paint on its own has holes for the windows, lamps and grille, so the viewer draws it double-sided and
// the glass fills the windows.
import { readFileSync } from 'node:fs';
import { Document, NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS, KHRDracoMeshCompression } from '@gltf-transform/extensions';
import draco3d from 'draco3dgltf';
import { MeshoptSimplifier } from 'meshoptimizer';

/** The nodes whose wheels and calipers are not the default design (matched on the node's name). */
const CARS = {
  'luxeed-rx': { skip: /Yufeng|Sport|Caliper|DoorFrame/ },
  'su7-ultra': { skip: /DoorFrame|TrunkArms/ },
  'zeekr-7x': { skip: /Fork_Wheels|Multi_Wheels|DoorFrame/ },
  // one wheel design each, already cut into corners
  'denza-z9': { skip: /Caliper|DoorFrame/ },
  'xpeng-g9l': { skip: /Caliper|DoorFrame/ },
  'avatr-06t': { skip: /Caliper|DoorFrame/ },
  'nio-es8': { skip: /Caliper|DoorFrame/ },
};

/** Triangles after simplification. */
const BUDGET = { hull: 14000, glass: 3000, tyre: 2000, rim: 1200 };

const LOOK = {
  paint: { name: 'Paint', color: [0.72, 0.73, 0.76, 1], metallic: 0.35, roughness: 0.32 },
  glass: { name: 'Glass', color: [0.04, 0.05, 0.06, 1], metallic: 0, roughness: 0.08 },
  tyre: { name: 'Tyre', color: [0.015, 0.015, 0.016, 1], metallic: 0, roughness: 0.85 },
  rim: { name: 'Rim', color: [0.55, 0.56, 0.58, 1], metallic: 0.9, roughness: 0.32 },
};

function classify(name) {
  if (/Shadow/.test(name)) return null;
  if (/^M_Paint/.test(name)) return 'hull';
  if (/Tyre/.test(name)) return 'tyre';
  if (/Glass/.test(name) && !/Mirror/.test(name)) return 'glass';
  if (/Alu|Machined|Chrome|Wheel_/.test(name)) return 'rim';
  return null;
}

/** m (column-major 4x4) applied to a point. */
function bakePoint(m, pos, i) {
  const x = pos[i], y = pos[i + 1], z = pos[i + 2];
  pos[i] = m[0] * x + m[4] * y + m[8] * z + m[12];
  pos[i + 1] = m[1] * x + m[5] * y + m[9] * z + m[13];
  pos[i + 2] = m[2] * x + m[6] * y + m[10] * z + m[14];
}

/** Weld by position, so the simplifier and the normals see one connected surface. */
function weld(pos, idx) {
  const key = (i) => `${Math.round(pos[i] * 2000)},${Math.round(pos[i + 1] * 2000)},${Math.round(pos[i + 2] * 2000)}`;
  const map = new Map();
  const remap = new Uint32Array(pos.length / 3);
  const P = [];
  for (let v = 0; v < remap.length; v++) {
    const k = key(v * 3);
    let r = map.get(k);
    if (r === undefined) {
      r = map.size;
      map.set(k, r);
      P.push(pos[v * 3], pos[v * 3 + 1], pos[v * 3 + 2]);
    }
    remap[v] = r;
  }
  const I = Uint32Array.from(idx, (v) => remap[v]);
  // drop triangles that collapsed
  const keep = [];
  for (let t = 0; t < I.length; t += 3) if (I[t] !== I[t + 1] && I[t + 1] !== I[t + 2] && I[t] !== I[t + 2]) keep.push(I[t], I[t + 1], I[t + 2]);
  return { pos: new Float32Array(P), idx: Uint32Array.from(keep) };
}

/** Area-weighted vertex normals. */
function normals(pos, idx) {
  const n = new Float32Array(pos.length);
  for (let t = 0; t < idx.length; t += 3) {
    const [a, b, c] = [idx[t] * 3, idx[t + 1] * 3, idx[t + 2] * 3];
    const ux = pos[b] - pos[a], uy = pos[b + 1] - pos[a + 1], uz = pos[b + 2] - pos[a + 2];
    const vx = pos[c] - pos[a], vy = pos[c + 1] - pos[a + 1], vz = pos[c + 2] - pos[a + 2];
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    for (const i of [a, b, c]) {
      n[i] += nx;
      n[i + 1] += ny;
      n[i + 2] += nz;
    }
  }
  for (let i = 0; i < n.length; i += 3) {
    const l = Math.hypot(n[i], n[i + 1], n[i + 2]) || 1;
    n[i] /= l;
    n[i + 1] /= l;
    n[i + 2] /= l;
  }
  return n;
}

/** Simplify to a triangle budget: let the error grow until the count is met, then go sloppy. */
function simplify(idx, pos, nrm, trisWanted) {
  const target = Math.min(idx.length / 3, trisWanted) * 3;
  let out = idx;
  for (const err of [0.01, 0.02, 0.05, 0.1, 0.2, 0.4, 0.8]) {
    [out] = nrm
      ? MeshoptSimplifier.simplifyWithAttributes(idx, pos, 3, nrm, 3, [1, 1, 1], null, target, err, [])
      : MeshoptSimplifier.simplify(idx, pos, 3, target, err, []);
    if (out.length <= target * 1.15) break;
  }
  if (out.length > target * 1.15) [out] = MeshoptSimplifier.simplifySloppy(idx, pos, 3, null, target, 1);
  return out;
}

/** The vertices still used, renumbered. */
function compact(idx, pos, nrm) {
  const remap = new Map();
  const P = [];
  const N = [];
  const I = new Uint32Array(idx.length);
  idx.forEach((v, k) => {
    let r = remap.get(v);
    if (r === undefined) {
      r = remap.size;
      remap.set(v, r);
      P.push(pos[v * 3], pos[v * 3 + 1], pos[v * 3 + 2]);
      N.push(nrm[v * 3], nrm[v * 3 + 1], nrm[v * 3 + 2]);
    }
    I[k] = r;
  });
  return { pos: new Float32Array(P), nrm: new Float32Array(N), idx: I };
}

async function makeProxy(slug, io, encoder) {
  const cfg = CARS[slug];
  if (!cfg) throw new Error(`unknown car ${slug}: ${Object.keys(CARS).join(', ')}`);
  const src = await io.read(`public/models/${slug}.glb`);

  // 1. every kept primitive in world space, by class
  const acc = {};
  for (const node of src.getRoot().listNodes()) {
    const mesh = node.getMesh();
    if (!mesh || cfg.skip.test(node.getName())) continue;
    const m = node.getWorldMatrix();
    for (const prim of mesh.listPrimitives()) {
      const cls = classify(prim.getMaterial()?.getName() ?? '');
      const P = prim.getAttribute('POSITION');
      const idx = prim.getIndices();
      if (!cls || !P || !idx) continue;
      const pos = Float32Array.from(P.getArray());
      for (let i = 0; i < pos.length; i += 3) bakePoint(m, pos, i);
      const a = (acc[cls] ??= { pos: [], idx: [], base: 0 });
      a.pos.push(pos);
      a.idx.push(Uint32Array.from(idx.getArray(), (v) => v + a.base));
      a.base += pos.length / 3;
    }
  }
  const join = (a) => ({
    pos: Float32Array.from(a.pos.flatMap((x) => [...x])),
    idx: Uint32Array.from(a.idx.flatMap((x) => [...x])),
  });

  await MeshoptSimplifier.ready;
  const doc = new Document();
  const buffer = doc.createBuffer();
  const mesh = doc.createMesh(`${slug}-proxy`);
  const report = [];
  let paintPrim;
  let glassPrim;
  const addPrimitive = (look, g) => {
    const mat = doc
      .createMaterial(look.name)
      .setBaseColorFactor(look.color)
      .setMetallicFactor(look.metallic)
      .setRoughnessFactor(look.roughness);
    mesh.addPrimitive(
      doc
        .createPrimitive()
        .setMaterial(mat)
        .setAttribute('POSITION', doc.createAccessor().setType('VEC3').setArray(g.pos).setBuffer(buffer))
        .setAttribute('NORMAL', doc.createAccessor().setType('VEC3').setArray(g.nrm).setBuffer(buffer))
        .setIndices(doc.createAccessor().setType('SCALAR').setArray(g.idx).setBuffer(buffer)),
    );
  };

  // 2. the hull: welded, pushed out to the skin, simplified, split by height into paint and glass
  if (!acc.hull) throw new Error(`${slug}: no paint in the GLB`);
  const hullRaw = join(acc.hull);
  const hull = weld(hullRaw.pos, hullRaw.idx);
  const n0 = normals(hull.pos, hull.idx);
  const sIdx = simplify(hull.idx, hull.pos, n0, BUDGET.hull);
  const h = compact(sIdx, hull.pos, n0);
  report.push(`hull ${hull.idx.length / 3} -> ${h.idx.length / 3}`);

  // the window glass as its own piece, thinned on its own
  if (acc.glass) {
    const raw = join(acc.glass);
    const w = weld(raw.pos, raw.idx);
    const nr = normals(w.pos, w.idx);
    const out = simplify(w.idx, w.pos, nr, BUDGET.glass);
    const g = compact(out, w.pos, nr);
    report.push(`glass ${w.idx.length / 3} -> ${g.idx.length / 3}`);
    paintPrim = { ...h };
    glassPrim = g;
  } else paintPrim = { ...h };
  addPrimitive(LOOK.paint, paintPrim);
  if (glassPrim) addPrimitive(LOOK.glass, glassPrim);

  // 3. tyres and rims
  for (const cls of ['tyre', 'rim']) {
    if (!acc[cls]) continue;
    const raw = join(acc[cls]);
    const w = weld(raw.pos, raw.idx);
    const nr = normals(w.pos, w.idx);
    const out = simplify(w.idx, w.pos, nr, BUDGET[cls]);
    const g = compact(out, w.pos, nr);
    addPrimitive(LOOK[cls], g);
    report.push(`${cls} ${w.idx.length / 3} -> ${g.idx.length / 3}`);
  }
  doc.createScene('proxy').addChild(doc.createNode(`${slug}-proxy`).setMesh(mesh));

  // 4. Draco
  doc
    .createExtension(KHRDracoMeshCompression)
    .setRequired(true)
    .setEncoderOptions({
      method: KHRDracoMeshCompression.EncoderMethod.EDGEBREAKER,
      encodeSpeed: 5,
      decodeSpeed: 5,
      quantizationBits: { POSITION: 13, NORMAL: 9 },
    });
  const out = `public/models/${slug}-proxy.glb`;
  await new NodeIO()
    .registerExtensions(ALL_EXTENSIONS)
    .registerDependencies({ 'draco3d.encoder': encoder })
    .write(out, doc);
  const kb = Math.round(readFileSync(out).length / 1024);
  console.log(`${slug}: ${report.join(', ')} -> ${out} (${kb} KB)`);
}

const arg = process.argv[2];
if (!arg) {
  console.error('usage: node scripts/make-proxy.mjs <luxeed-rx|su7-ultra|zeekr-7x|--all>');
  process.exit(1);
}
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({
  'draco3d.decoder': await draco3d.createDecoderModule(),
});
const encoder = await draco3d.createEncoderModule();
for (const slug of arg === '--all' ? Object.keys(CARS) : [arg]) await makeProxy(slug, io, encoder);
