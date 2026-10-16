import React from 'react';
import * as THREE from 'three';
import { useThree } from '@react-three/fiber';

/**
 * See-through glass: the windscreen and the front door glass (the materials named M_Glass, drawn as the X-ray tab's ghost) and
 * the privacy glass behind the B-pillar (M_Glass_Privacy: the rear windows, the backlight, a glass roof, drawn tinted as an
 * open door shows it). From outside they show the cabin through them.
 *
 * Behind every pane the build lays a black underlay (M_Black_Gloss) and, a little further in, a shadow shell (M_Shadow): they
 * make the glass read deep when it is opaque, and they would wall the cabin in when it is not. They are one mesh each
 * (the car's `*_Blackout` node) spanning the whole greenhouse, so rather than hide them (the X-ray tab does, and the body then
 * leaks) the triangles that lie behind a clear pane are taken out of their index. Done once per mount, on a copy of the geometry
 * (the cache's is shared); the returned function puts the originals back.
 */

const isPane = (m: THREE.Material) => {
  const n = m.name.toLowerCase();
  return n === 'm_glass' || n === 'm_glass_privacy';
};

/** how far behind a clear pane, m, a layer's triangle is taken for the pane's backing */
const REACH = { m_black_gloss: 0.05, m_shadow: 0.07 } as const;

const CELL = 0.05;

export function cullBehindClearGlass(model: THREE.Object3D, blackout: THREE.Object3D[]): () => void {
  model.updateWorldMatrix(true, true);
  const inverse = new THREE.Matrix4().copy(model.matrixWorld).invert();
  const toModel = (mesh: THREE.Mesh) => new THREE.Matrix4().multiplyMatrices(inverse, mesh.matrixWorld);

  // the clear panes' vertices, in the model's own frame, hashed into cells
  const grid = new Map<string, number[]>();
  const cell = (x: number, y: number, z: number) => `${Math.floor(x / CELL)},${Math.floor(y / CELL)},${Math.floor(z / CELL)}`;
  const v = new THREE.Vector3();
  let any = false;
  model.traverse((o) => {
    const mesh = o as THREE.Mesh;
    if (!mesh.isMesh) return;
    const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    if (!mats.some(isPane)) return;
    const pos = mesh.geometry.getAttribute('position');
    const m = toModel(mesh);
    for (let i = 0; i < pos.count; i++) {
      v.fromBufferAttribute(pos, i).applyMatrix4(m);
      const k = cell(v.x, v.y, v.z);
      let l = grid.get(k);
      if (!l) grid.set(k, (l = []));
      l.push(v.x, v.y, v.z);
      any = true;
    }
  });
  if (!any) return () => {};

  /** the distance from a point to the nearest clear-pane vertex, or Infinity beyond `r` */
  const nearest = (x: number, y: number, z: number, r: number) => {
    const n = Math.ceil(r / CELL);
    const cx = Math.floor(x / CELL);
    const cy = Math.floor(y / CELL);
    const cz = Math.floor(z / CELL);
    let best = Infinity;
    for (let i = -n; i <= n; i++)
      for (let j = -n; j <= n; j++)
        for (let k = -n; k <= n; k++) {
          const l = grid.get(`${cx + i},${cy + j},${cz + k}`);
          if (!l) continue;
          for (let q = 0; q < l.length; q += 3) {
            const d = Math.hypot(x - l[q], y - l[q + 1], z - l[q + 2]);
            if (d < best) best = d;
          }
        }
    return best <= r ? best : Infinity;
  };

  const restore: (() => void)[] = [];
  const a = new THREE.Vector3();
  const b = new THREE.Vector3();
  const c = new THREE.Vector3();
  for (const root of blackout) {
    root.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (!mesh.isMesh || Array.isArray(mesh.material)) return;
      const reach = REACH[mesh.material.name.toLowerCase() as keyof typeof REACH];
      const g = mesh.geometry;
      if (!reach || g.groups.length) return;
      const pos = g.getAttribute('position');
      const index = g.index;
      const count = index ? index.count : pos.count;
      const m = toModel(mesh);
      const keep: number[] = [];
      for (let t = 0; t < count; t += 3) {
        const ia = index ? index.getX(t) : t;
        const ib = index ? index.getX(t + 1) : t + 1;
        const ic = index ? index.getX(t + 2) : t + 2;
        a.fromBufferAttribute(pos, ia).applyMatrix4(m);
        b.fromBufferAttribute(pos, ib).applyMatrix4(m);
        c.fromBufferAttribute(pos, ic).applyMatrix4(m);
        const cx = (a.x + b.x + c.x) / 3;
        const cy = (a.y + b.y + c.y) / 3;
        const cz = (a.z + b.z + c.z) / 3;
        if (nearest(cx, cy, cz, reach) === Infinity) keep.push(ia, ib, ic);
      }
      if (keep.length === count) return;
      const copy = g.clone();
      copy.setIndex(keep);
      mesh.geometry = copy;
      restore.push(() => {
        mesh.geometry = g;
        copy.dispose();
      });
    });
  }
  return () => restore.forEach((r) => r());
}

/*
 * The stencil. With the cabin mounted behind a closed car, anything of it that is not behind a clear pane must not show: the
 * jamb of a door lining a few millimetres proud of the skin would stand in the paint. So the clear panes write 1 into the stencil
 * where they are in front (a copy of each pane's mesh that draws no colour and no depth, after every other opaque thing), and the
 * cabin is drawn only where the stencil is 1 (after it). The ghost pane then blends over the cabin as it is drawn last, with the
 * transparent things.
 */
const WRITER_ORDER = 1;
const CABIN_ORDER = 2;

/** Over each clear pane (M_Glass), a copy of its mesh that writes the stencil; on while `on`. */
export function useGlassStencil(model: THREE.Object3D, on: boolean) {
  const invalidate = useThree((s) => s.invalidate);
  const writers = React.useRef<THREE.Mesh[]>([]);

  React.useEffect(() => {
    const mat = new THREE.MeshBasicMaterial({
      colorWrite: false,
      depthWrite: false,
      side: THREE.DoubleSide,
      stencilWrite: true,
      stencilRef: 1,
      stencilFunc: THREE.AlwaysStencilFunc,
      stencilZPass: THREE.ReplaceStencilOp,
    });
    const made: THREE.Mesh[] = [];
    model.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (!mesh.isMesh || Array.isArray(mesh.material) || !isPane(mesh.material)) return;
      if (!mesh.parent || mesh.userData.stencilWriter) return;
      const w = new THREE.Mesh(mesh.geometry, mat);
      w.userData.stencilWriter = true;
      w.position.copy(mesh.position);
      w.quaternion.copy(mesh.quaternion);
      w.scale.copy(mesh.scale);
      w.renderOrder = WRITER_ORDER;
      w.raycast = () => {};
      w.visible = false;
      mesh.parent.add(w);
      made.push(w);
    });
    writers.current = made;
    return () => {
      for (const w of made) w.parent?.remove(w);
      mat.dispose();
      writers.current = [];
    };
  }, [model]);

  React.useEffect(() => {
    for (const w of writers.current) w.visible = on;
    invalidate();
  }, [on, invalidate, model]);
}

/** The cabin's meshes, drawn only where the stencil is 1 while `masked` (after the writers), as usual otherwise. */
export function useCabinStencil(model: THREE.Object3D, masked: boolean) {
  const invalidate = useThree((s) => s.invalidate);
  React.useEffect(() => {
    const mats = new Set<THREE.Material>();
    const meshes: THREE.Mesh[] = [];
    model.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (!mesh.isMesh) return;
      meshes.push(mesh);
      for (const m of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) mats.add(m);
    });
    for (const m of mats) {
      m.stencilWrite = masked;
      m.stencilRef = 1;
      m.stencilFunc = THREE.EqualStencilFunc;
      m.stencilFail = THREE.KeepStencilOp;
      m.stencilZFail = THREE.KeepStencilOp;
      m.stencilZPass = THREE.KeepStencilOp;
    }
    for (const mesh of meshes) mesh.renderOrder = masked ? CABIN_ORDER : 0;
    invalidate();
  }, [model, masked, invalidate]);
}
