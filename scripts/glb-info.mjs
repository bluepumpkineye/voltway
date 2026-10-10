// List a GLB's mesh nodes with their triangle counts and materials.
//   node scripts/glb-info.mjs public/models/luxeed-rx.glb
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import draco3d from 'draco3dgltf';

const file = process.argv[2];
if (!file) {
  console.error('usage: node scripts/glb-info.mjs <file.glb>');
  process.exit(1);
}

const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({
  'draco3d.decoder': await draco3d.createDecoderModule(),
});
const doc = await io.read(file);
const root = doc.getRoot();

let tris = 0;
const rows = [];
for (const node of root.listNodes()) {
  const mesh = node.getMesh();
  if (!mesh) continue;
  let t = 0;
  const mats = new Set();
  for (const p of mesh.listPrimitives()) {
    const idx = p.getIndices();
    t += idx ? idx.getCount() / 3 : (p.getAttribute('POSITION')?.getCount() ?? 0) / 3;
    mats.add(p.getMaterial()?.getName() ?? '-');
  }
  tris += t;
  rows.push(`${node.getName()}\t${t}\t${[...mats].join(',')}`);
}
console.log(`triangles ${tris}, mesh nodes ${rows.length}, materials ${root.listMaterials().length}`);
console.log(rows.join('\n'));

// triangles per material, over every node
if (process.argv.includes('--materials')) {
  const per = new Map();
  for (const node of root.listNodes()) {
    const mesh = node.getMesh();
    if (!mesh) continue;
    for (const p of mesh.listPrimitives()) {
      const idx = p.getIndices();
      const n = idx ? idx.getCount() / 3 : 0;
      const k = p.getMaterial()?.getName() ?? '-';
      per.set(k, (per.get(k) ?? 0) + n);
    }
  }
  console.log([...per].sort((a, b) => b[1] - a[1]).map(([k, n]) => `${k}\t${n}`).join('\n'));
}
