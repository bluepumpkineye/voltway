import * as THREE from 'three';

/**
 * Cuts a merged wheel node into the per-corner nodes the rig wants (src/lib/tech/rig.ts), in the browser.
 *
 * The RX and the 7X export `<design>_Wheels_<FL|FR|RL|RR>` (one node per corner, origin at the hub).
 * The SU7's export is older: one node, `SU7Ultra_Wheels`, a mesh per material with all four wheels in each.
 * Re-exporting that car would rebuild its whole body, so its wheels are cut here instead: every triangle goes
 * to the corner it stands at, each corner gets a node at its hub (the middle of its tyre), and the brake
 * calipers, which do not spin, get a node of their own. The vertex buffers are shared with the original, so
 * nothing is copied but the four index lists.
 *
 * Works in the exterior's own frame (the viewer's: x forward, y up, z toward the passenger side). Returns the
 * design's name when it cut something, null when there was no merged wheel node to cut.
 */

const CORNERS = ['FL', 'FR', 'RL', 'RR'] as const;
type Corner = (typeof CORNERS)[number];

const _p = new THREE.Vector3();

export function splitMergedWheels(root: THREE.Object3D): string | null {
  let merged: THREE.Object3D | undefined;
  root.traverse((o) => {
    if (!merged && /_wheels$/i.test(o.name)) merged = o;
  });
  if (!merged) return null;

  const meshes: THREE.Mesh[] = [];
  merged.traverse((o) => {
    if (o instanceof THREE.Mesh) meshes.push(o);
  });
  if (!meshes.length || meshes.some((m) => Array.isArray(m.material) || !m.geometry.getIndex())) return null;

  root.updateWorldMatrix(true, true);
  const toRoot = new THREE.Matrix4().copy(root.matrixWorld).invert();

  // every vertex in the exterior's frame, once
  const rel = new Map<THREE.Mesh, THREE.Matrix4>();
  const world = new Map<THREE.Mesh, Float32Array>();
  const lo = new THREE.Vector3(Infinity, Infinity, Infinity);
  const hi = new THREE.Vector3(-Infinity, -Infinity, -Infinity);
  for (const m of meshes) {
    const matrix = new THREE.Matrix4().multiplyMatrices(toRoot, m.matrixWorld);
    rel.set(m, matrix);
    const pos = m.geometry.getAttribute('position');
    const xyz = new Float32Array(pos.count * 3);
    for (let i = 0; i < pos.count; i++) {
      _p.fromBufferAttribute(pos, i).applyMatrix4(matrix);
      xyz.set([_p.x, _p.y, _p.z], i * 3);
      lo.min(_p);
      hi.max(_p);
    }
    world.set(m, xyz);
  }
  const mid = lo.clone().add(hi).multiplyScalar(0.5);
  const corner = (x: number, z: number): Corner => `${x > mid.x ? 'F' : 'R'}${z < mid.z ? 'L' : 'R'}` as Corner;

  // which triangles stand at which corner, per mesh, and each corner's tyre box (its hub is the middle of that)
  const picks = new Map<THREE.Mesh, Record<Corner, number[]>>();
  const tyre = {} as Record<Corner, THREE.Box3>;
  const all = {} as Record<Corner, THREE.Box3>;
  for (const k of CORNERS) {
    tyre[k] = new THREE.Box3();
    all[k] = new THREE.Box3();
  }
  for (const m of meshes) {
    const index = m.geometry.getIndex()!;
    const xyz = world.get(m)!;
    const isTyre = /tyre|tire/i.test((m.material as THREE.Material).name);
    const by: Record<Corner, number[]> = { FL: [], FR: [], RL: [], RR: [] };
    for (let t = 0; t < index.count; t += 3) {
      const a = index.getX(t);
      const b = index.getX(t + 1);
      const c = index.getX(t + 2);
      const x = (xyz[a * 3] + xyz[b * 3] + xyz[c * 3]) / 3;
      const z = (xyz[a * 3 + 2] + xyz[b * 3 + 2] + xyz[c * 3 + 2]) / 3;
      const k = corner(x, z);
      by[k].push(a, b, c);
      for (const v of [a, b, c]) {
        _p.set(xyz[v * 3], xyz[v * 3 + 1], xyz[v * 3 + 2]);
        all[k].expandByPoint(_p);
        if (isTyre) tyre[k].expandByPoint(_p);
      }
    }
    picks.set(m, by);
  }
  const hub = {} as Record<Corner, THREE.Vector3>;
  for (const k of CORNERS) {
    const box = tyre[k].isEmpty() ? all[k] : tyre[k];
    if (box.isEmpty()) return null;
    hub[k] = box.getCenter(new THREE.Vector3());
  }

  const design = merged.name;
  const made: THREE.Object3D[] = [];
  for (const k of CORNERS) {
    const wheel = new THREE.Group();
    wheel.name = `${design}_${k}`;
    wheel.position.copy(hub[k]);
    const caliper = new THREE.Group();
    caliper.name = `${design}_Caliper_${k}`;
    caliper.position.copy(hub[k]);
    const shift = new THREE.Matrix4().makeTranslation(-hub[k].x, -hub[k].y, -hub[k].z);
    for (const m of meshes) {
      const list = picks.get(m)![k];
      if (!list.length) continue;
      const g = new THREE.BufferGeometry();
      for (const [name, attr] of Object.entries(m.geometry.attributes)) g.setAttribute(name, attr);
      g.setIndex(new THREE.BufferAttribute(new Uint32Array(list), 1));
      const part = new THREE.Mesh(g, m.material);
      part.name = `${m.name}_${k}`;
      part.castShadow = m.castShadow;
      part.receiveShadow = m.receiveShadow;
      part.renderOrder = m.renderOrder;
      part.layers.mask = m.layers.mask;
      part.userData = { ...m.userData };
      part.frustumCulled = false;
      new THREE.Matrix4().multiplyMatrices(shift, rel.get(m)!).decompose(part.position, part.quaternion, part.scale);
      const isCaliper = /caliper/i.test((m.material as THREE.Material).name) || /caliper/i.test(m.name);
      (isCaliper ? caliper : wheel).add(part);
    }
    made.push(wheel);
    if (caliper.children.length) made.push(caliper);
  }
  merged.parent?.remove(merged);
  root.add(...made);
  return design;
}
