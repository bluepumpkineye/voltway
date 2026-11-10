// Print a GLB's node tree with each node's translation and extras.
//   node scripts/glb-tree.mjs public/models/su7-ultra-xray.glb [--extras]
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import draco3d from 'draco3dgltf';

const file = process.argv[2];
const showExtras = process.argv.includes('--extras');
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({
  'draco3d.decoder': await draco3d.createDecoderModule(),
});
const doc = await io.read(file);
const f = (v) => v.map((x) => x.toFixed(3)).join(',');
function walk(node, depth) {
  const mesh = node.getMesh();
  let tris = 0;
  if (mesh) for (const p of mesh.listPrimitives()) tris += (p.getIndices()?.getCount() ?? 0) / 3;
  const ex = node.getExtras();
  const keys = Object.keys(ex ?? {});
  console.log(`${'  '.repeat(depth)}${node.getName()} t(${f(node.getTranslation())})${mesh ? ` ${tris} tris` : ''}${keys.length ? ' [' + keys.join(',') + ']' : ''}`);
  if (showExtras && keys.length) for (const k of keys) console.log(`${'  '.repeat(depth + 1)}${k}: ${String(ex[k]).slice(0, 160)}`);
  for (const c of node.listChildren()) walk(c, depth + 1);
}
for (const s of doc.getRoot().listScenes()) for (const n of s.listChildren()) walk(n, 0);
