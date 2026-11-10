// Solve the SU7's four corners over a range of wheel travel and check the linkage: the knuckle's two joints stay their own
// distance apart, the hub reaches the height asked for, and the arms turn the right way.
//   node scripts/xray-tools/wishbone-test.mjs [public/models/su7-ultra-xray.glb]
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import draco3d from 'draco3dgltf';
import ts from 'typescript';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const file = process.argv[2] ?? 'public/models/su7-ultra-xray.glb';
const src = fs.readFileSync('src/lib/xray/wishbone.ts', 'utf8');
const js = ts.transpileModule(src, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText;
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'wb-'));
const out = path.join(dir, 'wishbone.mjs');
fs.writeFileSync(out, js.replace("from 'three'", `from '${pathToFileURL(path.resolve('node_modules/three/build/three.module.js')).href}'`));
const { Wishbone } = await import(pathToFileURL(out).href);

const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'draco3d.decoder': await draco3d.createDecoderModule() });
const doc = await io.read(file);
let bad = 0;
for (const node of doc.getRoot().listNodes()) {
  const m = /^XR_Susp_(FL|FR|RL|RR)$/.exec(node.getName());
  if (!m) continue;
  const kin = JSON.parse(node.getExtras().kin);
  const w = new Wishbone(kin);
  const rows = [];
  for (const travel of [-0.05, -0.02, 0, 0.02, 0.05, 0.08]) {
    const p = w.solve(travel);
    const span = w.onKnuckle(w.UBJ, p).distanceTo(w.onLower(w.LBJ, p.lowerAngle));
    const err = Math.abs(p.hub.y - (w.H.y + travel));
    if (err > 1e-4 || Math.abs(span - w.span) > 1e-4) bad++;
    rows.push(`${travel >= 0 ? '+' : ''}${(travel * 100).toFixed(0)} cm: lower ${(p.lowerAngle * 57.3).toFixed(1)}° upper ${(p.upperAngle * 57.3).toFixed(1)}° hub dz ${(p.hub.y - w.H.y).toFixed(3)} dx ${(p.hub.x - w.H.x).toFixed(3)} dz-lat ${(p.hub.z - w.H.z).toFixed(3)} span err ${(span - w.span).toExponential(1)}`);
  }
  console.log(m[1] + '\n  ' + rows.join('\n  '));
}
console.log(bad ? `FAILED: ${bad} bad solutions` : 'ok');
