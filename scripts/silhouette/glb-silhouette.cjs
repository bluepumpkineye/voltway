// node scripts/silhouette/glb-silhouette.cjs <car.glb> [skipRegex='Wheel|Caliper|Blackout']
//
// A shipped car's outline in the same tables as side-silhouette.cjs prints for a picture: the top profile (the highest point of the
// exterior at each 0.1 m of x) and the front and rear extreme x at each 0.05 m of height (world space, x forward, y up in glTF).
// Wheels, calipers, the hidden blackout underlay and M_Shadow surfaces are left out. Compare the two tables number for number: it
// found the ES8's nose 0.25 m too long, its hood 8 cm low and its windscreen 8 degrees too steep when the eye only saw "an estate".
const { createRequire } = require('module');
const path = require('path');
const req = createRequire(path.resolve(__dirname, '../../package.json'));
const { NodeIO } = req('@gltf-transform/core');
const { ALL_EXTENSIONS } = req('@gltf-transform/extensions');
const draco3d = req('draco3dgltf');

(async () => {
  const [f, skip = 'Wheel|Caliper|Blackout'] = process.argv.slice(2);
  if (!f) { console.error('usage: glb-silhouette.cjs <car.glb> [skipRegex]'); process.exit(1); }
  const rx = new RegExp(skip, 'i');
  const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'draco3d.decoder': await draco3d.createDecoderModule() });
  const doc = await io.read(f);
  const top = new Map(), lo = new Map(), hi = new Map();
  for (const node of doc.getRoot().listNodes()) {
    const mesh = node.getMesh();
    if (!mesh || rx.test(node.getName())) continue;
    const m = node.getWorldMatrix();
    for (const prim of mesh.listPrimitives()) {
      if (/Shadow/i.test(prim.getMaterial() ? prim.getMaterial().getName() : '')) continue;
      const pos = prim.getAttribute('POSITION');
      const v = [0, 0, 0];
      for (let i = 0; i < pos.getCount(); i++) {
        pos.getElement(i, v);
        const X = m[0] * v[0] + m[4] * v[1] + m[8] * v[2] + m[12];
        const Y = m[1] * v[0] + m[5] * v[1] + m[9] * v[2] + m[13];
        const k = Math.round(X * 10);
        if (!top.has(k) || Y > top.get(k)) top.set(k, Y);
        const kz = Math.round(Y / 0.05);
        if (!lo.has(kz) || X < lo.get(kz)) lo.set(kz, X);
        if (!hi.has(kz) || X > hi.get(kz)) hi.set(kz, X);
      }
    }
  }
  console.log('TOP', [...top.keys()].sort((a, b) => b - a).map((k) => (k / 10).toFixed(2) + ':' + top.get(k).toFixed(3)).join(' '));
  for (let z = 0.30; z <= 1.30; z += 0.05) {
    const k = Math.round(z / 0.05);
    console.log(z.toFixed(2) + ': front ' + (hi.get(k) ?? NaN).toFixed(3) + ' rear ' + (lo.get(k) ?? NaN).toFixed(3));
  }
})();
