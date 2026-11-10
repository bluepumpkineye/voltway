// Print a car's wheel-node positions (the hubs, in the viewer's axes and in Blender's) and its overall box: the numbers
// a CarSpec for carkit.anatomy needs.   node scripts/xray-tools/hubs.mjs public/models/zeekr-7x.glb
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import draco3d from 'draco3dgltf';

const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'draco3d.decoder': await draco3d.createDecoderModule() });
const doc = await io.read(process.argv[2]);
// the box of every vertex of every mesh node, by hand
const b = { min: [Infinity, Infinity, Infinity], max: [-Infinity, -Infinity, -Infinity] };
for (const n of doc.getRoot().listNodes()) {
  const mesh = n.getMesh();
  if (!mesh) continue;
  const m = n.getWorldMatrix();
  for (const p of mesh.listPrimitives()) {
    const a = p.getAttribute('POSITION');
    const v = [0, 0, 0];
    for (let i = 0; i < a.getCount(); i += 7) {
      a.getElement(i, v);
      const w = [m[0] * v[0] + m[4] * v[1] + m[8] * v[2] + m[12], m[1] * v[0] + m[5] * v[1] + m[9] * v[2] + m[13], m[2] * v[0] + m[6] * v[1] + m[10] * v[2] + m[14]];
      for (let k = 0; k < 3; k++) { b.min[k] = Math.min(b.min[k], w[k]); b.max[k] = Math.max(b.max[k], w[k]); }
    }
  }
}
const f = (v) => v.map((x) => x.toFixed(3)).join(', ');
console.log('box min', f(b.min), 'max', f(b.max));
for (const n of doc.getRoot().listNodes()) {
  if (/_wheels_(fl|fr|rl|rr)$/i.test(n.getName()) && !/caliper/i.test(n.getName())) {
    const t = n.getWorldTranslation();
    // viewer (x fwd, y up, z right) -> Blender (x fwd, y left, z up)
    console.log(n.getName().padEnd(34), 'viewer', f(t), '  blender', f([t[0], -t[2], t[1]]));
  }
}
