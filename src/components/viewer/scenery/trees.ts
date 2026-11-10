import * as THREE from 'three';
import { Builder, cached, clamp01, hex, placement, rng, smooth, type V3 } from './kit';

/**
 * The trees: a trunk with its branches (a few hundred triangles of tapered cylinders) and a canopy of leaf-cluster cards set
 * on an ellipsoid. The cards' normals point out of the ball, a little up, so the canopy is shaded as one soft mass and
 * not as a heap of flat cards; their vertex colours darken toward the inside and the underside, which is the
 * occlusion a real crown has. Alpha-tested and double-sided: no sorting, no cost beyond the triangles.
 */
export type TreeKind = 'camphor' | 'plane' | 'ginkgo' | 'cypress' | 'hedge' | 'shrub';

interface Shape {
  trunkH: number;
  trunkR: number;
  /** canopy ellipsoid: centre height and radii */
  cy: number;
  rx: number;
  ry: number;
  rz: number;
  cards: number;
  size: [number, number];
  leaf: 'camphor' | 'plane' | 'ginkgo' | 'cypress' | 'shrub';
  bark: string;
  forks: number;
}

export const SHAPES: Record<TreeKind, Shape> = {
  camphor: { trunkH: 2.5, trunkR: 0.13, cy: 3.7, rx: 2.1, ry: 1.7, rz: 2.1, cards: 170, size: [1.15, 1.8], leaf: 'camphor', bark: '#6a5a46', forks: 4 },
  plane: { trunkH: 2.9, trunkR: 0.15, cy: 4.6, rx: 2.5, ry: 2.0, rz: 2.5, cards: 140, size: [1.5, 2.3], leaf: 'plane', bark: '#a79a86', forks: 5 },
  ginkgo: { trunkH: 2.2, trunkR: 0.1, cy: 4.0, rx: 1.25, ry: 2.4, rz: 1.25, cards: 120, size: [1.0, 1.5], leaf: 'ginkgo', bark: '#7a6d58', forks: 3 },
  cypress: { trunkH: 0.8, trunkR: 0.08, cy: 3.4, rx: 0.95, ry: 3.1, rz: 0.95, cards: 110, size: [0.9, 1.4], leaf: 'cypress', bark: '#5e5240', forks: 0 },
  hedge: { trunkH: 0, trunkR: 0, cy: 0.5, rx: 1.15, ry: 0.48, rz: 0.5, cards: 46, size: [0.5, 0.8], leaf: 'shrub', bark: '#5a4a38', forks: 0 },
  shrub: { trunkH: 0, trunkR: 0, cy: 0.55, rx: 0.7, ry: 0.5, rz: 0.7, cards: 30, size: [0.5, 0.8], leaf: 'shrub', bark: '#5a4a38', forks: 0 },
};

export interface TreeParts {
  trunk: THREE.BufferGeometry | null;
  canopy: THREE.BufferGeometry;
  /** the canopy's reach on the ground, m: where its shadow falls */
  radius: number;
  leaf: Shape['leaf'];
  /** the trunk geometry is a solid green core (hedges, shrubs), not bark */
  solid?: boolean;
}

const UP = new THREE.Vector3(0, 1, 0);

function limb(b: Builder, from: THREE.Vector3, to: THREE.Vector3, r0: number, r1: number, color: V3) {
  const dir = to.clone().sub(from);
  const len = dir.length();
  const g = new THREE.CylinderGeometry(r1, r0, len, 6, 1, true);
  const q = new THREE.Quaternion().setFromUnitVectors(UP, dir.clone().normalize());
  const m = new THREE.Matrix4().compose(from.clone().add(to).multiplyScalar(0.5), q, new THREE.Vector3(1, 1, 1));
  // the bark's v runs the limb's length: repeat it every 1.5 m or so
  const uv = g.getAttribute('uv');
  for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) * 1.5, uv.getY(i) * Math.max(1, len / 1.2));
  b.add(g, m, color);
  g.dispose();
}

/**
 * A clipped hedge or a shrub: a dark core box that fills it (so nothing shows through) and leaf cards laid over its top and sides,
 * facing out. Half sizes rx, ry (height / 2, on the ground) and rz.
 */
function clipped(kind: TreeKind, s: Shape, r: () => number): TreeParts {
  const hx = s.rx;
  const hy = s.ry;
  const hz = s.rz;
  const core = new Builder();
  const g = hex('#1f4326');
  core.box(-hx * 0.97, 0, -hz * 0.97, hx * 1.94, hy * 2 * 0.94, hz * 1.94, g, 0, ['-y']);
  const cb = new Builder();
  for (let i = 0; i < s.cards; i++) {
    const face = r();
    let p: V3;
    let n: V3;
    if (face < 0.5) {
      p = [(r() * 2 - 1) * hx, hy * 2 * 0.97, (r() * 2 - 1) * hz];
      n = [0, 1, 0];
    } else if (face < 0.8) {
      const side = r() < 0.5 ? -1 : 1;
      p = [(r() * 2 - 1) * hx, r() * hy * 2, side * hz];
      n = [0, 0.25, side];
    } else {
      const side = r() < 0.5 ? -1 : 1;
      p = [side * hx, r() * hy * 2, (r() * 2 - 1) * hz];
      n = [side, 0.25, 0];
    }
    const size = s.size[0] + r() * (s.size[1] - s.size[0]);
    const hw = size / 2;
    // the card lies roughly in the surface, tilted a little at random so the surface is rough
    const tilt = (r() - 0.5) * 0.9;
    const roll = r() * Math.PI * 2;
    const nn = new THREE.Vector3(...n).normalize();
    const a = new THREE.Vector3().crossVectors(nn, Math.abs(nn.y) > 0.9 ? new THREE.Vector3(1, 0, 0) : UP).normalize();
    const b = new THREE.Vector3().crossVectors(nn, a).normalize();
    const cr = a.clone().multiplyScalar(Math.cos(roll)).add(b.clone().multiplyScalar(Math.sin(roll)));
    const cu = b.clone().multiplyScalar(Math.cos(roll)).sub(a.clone().multiplyScalar(Math.sin(roll)));
    const lift = nn.clone().multiplyScalar(0.05 + r() * 0.07);
    const c = new THREE.Vector3(...p).add(lift);
    const pt = (sx: number, sy: number): V3 => [
      c.x + cr.x * hw * sx + cu.x * hw * sy + nn.x * tilt * sy * 0.3,
      c.y + cr.y * hw * sx + cu.y * hw * sy + nn.y * tilt * sy * 0.3,
      c.z + cr.z * hw * sx + cu.z * hw * sy + nn.z * tilt * sy * 0.3,
    ];
    const k = 0.78 + 0.22 * clamp01(p[1] / (hy * 2)) + (r() - 0.5) * 0.1;
    const sh = new THREE.Vector3(n[0] * 0.5, 0.9, n[2] * 0.5).normalize();
    cb.quad(pt(-1, -1), pt(1, -1), pt(1, 1), pt(-1, 1), [k, k, k], [0, 0, 1, 1], false, [sh.x, sh.y, sh.z]);
  }
  return { trunk: core.build(), canopy: cb.build(), radius: Math.max(hx, hz) * 0.9, leaf: 'shrub', solid: true };
}

export function treeParts(kind: TreeKind, seed = 1): TreeParts {
  return cached(`tree-${kind}-${seed}`, () => {
    const s = SHAPES[kind];
    const r = rng(seed * 7919 + kind.length * 31);
    if (kind === 'hedge' || kind === 'shrub') return clipped(kind, s, r);

    // the trunk and its limbs
    let trunk: THREE.BufferGeometry | null = null;
    if (s.trunkH > 0) {
      const tb = new Builder();
      const bark = hex(s.bark);
      const base = new THREE.Vector3(0, 0, 0);
      const top = new THREE.Vector3((r() - 0.5) * 0.12, s.trunkH, (r() - 0.5) * 0.12);
      limb(tb, base, top, s.trunkR * 1.45, s.trunkR * (s.forks ? 1 : 0.7), bark);
      // a flare at the root
      tb.add(new THREE.CylinderGeometry(s.trunkR * 1.5, s.trunkR * 2.1, 0.22, 7, 1, true), placement(0, 0.1, 0), [bark[0] * 0.8, bark[1] * 0.8, bark[2] * 0.8]);
      for (let i = 0; i < s.forks; i++) {
        const a = (i / s.forks) * Math.PI * 2 + r() * 0.8;
        const out = s.rx * (0.34 + r() * 0.2);
        const up = (s.cy - s.trunkH) * (0.65 + r() * 0.4);
        const mid = top.clone().add(new THREE.Vector3(Math.cos(a) * out * 0.45, up * 0.45, Math.sin(a) * out * 0.45));
        const end = top.clone().add(new THREE.Vector3(Math.cos(a) * out, up, Math.sin(a) * out));
        limb(tb, top, mid, s.trunkR * 0.62, s.trunkR * 0.42, bark);
        limb(tb, mid, end, s.trunkR * 0.42, s.trunkR * 0.18, [bark[0] * 0.92, bark[1] * 0.92, bark[2] * 0.92]);
        // a twig or two
        for (let k = 0; k < 2; k++) {
          const b2 = mid.clone().add(new THREE.Vector3((r() - 0.5) * 0.9, 0.35 + r() * 0.4, (r() - 0.5) * 0.9));
          limb(tb, mid, b2, s.trunkR * 0.2, s.trunkR * 0.08, bark);
        }
      }
      trunk = tb.build();
    }

    // the canopy's cards
    const cb = new Builder();
    const centre = new THREE.Vector3(0, s.cy, 0);
    for (let i = 0; i < s.cards; i++) {
      // a point in the ellipsoid, pushed toward the skin so the crown is full at its outline and a little hollow within
      let p: THREE.Vector3;
      do {
        p = new THREE.Vector3(r() * 2 - 1, r() * 2 - 1, r() * 2 - 1);
      } while (p.lengthSq() > 1);
      const depth = Math.cbrt(p.length()) / Math.max(p.length(), 1e-6);
      p.multiplyScalar(depth * (0.55 + 0.45 * r()));
      const dist = clamp01(p.length());
      const pos = new THREE.Vector3(p.x * s.rx, s.cy + p.y * s.ry, p.z * s.rz);
      // a pleasing silhouette: the underside flattens, the top domes
      if (kind !== 'cypress' && pos.y < s.cy - s.ry * 0.55) pos.y = s.cy - s.ry * 0.55 + (pos.y - (s.cy - s.ry * 0.55)) * 0.3;
      const out = pos.clone().sub(centre);
      out.set(out.x / (s.rx * s.rx), out.y / (s.ry * s.ry), out.z / (s.rz * s.rz)).normalize();
      // the card faces out of the ball for half of them, the rest are strewn at random angles
      const facing = r() < 0.6 ? out.clone() : new THREE.Vector3(r() * 2 - 1, r() * 2 - 1, r() * 2 - 1).normalize();
      const right = new THREE.Vector3().crossVectors(UP, facing);
      if (right.lengthSq() < 1e-4) right.set(1, 0, 0);
      right.normalize();
      const up = new THREE.Vector3().crossVectors(facing, right).normalize();
      const roll = r() * Math.PI * 2;
      const cr = right.clone().multiplyScalar(Math.cos(roll)).add(up.clone().multiplyScalar(Math.sin(roll)));
      const cu = up.clone().multiplyScalar(Math.cos(roll)).sub(right.clone().multiplyScalar(Math.sin(roll)));
      const size = s.size[0] + r() * (s.size[1] - s.size[0]);
      const hw = size / 2;
      const hh = (size / 2) * (kind === 'cypress' ? 1.3 : 1);
      const pt = (sx: number, sy: number): V3 => [pos.x + cr.x * hw * sx + cu.x * hh * sy, pos.y + cr.y * hw * sx + cu.y * hh * sy, pos.z + cr.z * hw * sx + cu.z * hh * sy];
      // occlusion: deep inside and under the crown is dark, the top and the skin are bright
      const under = smooth(-0.9, 0.6, (pos.y - s.cy) / s.ry);
      const ao = (0.46 + 0.54 * smooth(0.12, 1, dist)) * (0.62 + 0.38 * under);
      const lit = 0.96 + (r() - 0.5) * 0.14;
      const k = ao * lit;
      const col: V3 = [k, k, k];
      // the shading normal: out of the ball, lifted toward the sky so the crown reads as a dome
      const nrm = out.clone().multiplyScalar(0.7).add(new THREE.Vector3(0, 0.55, 0)).normalize();
      cb.quad(pt(-1, -1), pt(1, -1), pt(1, 1), pt(-1, 1), col, [0, 0, 1, 1], false, [nrm.x, nrm.y, nrm.z]);
    }
    const radius = Math.max(s.rx, s.rz) * 0.92;
    return { trunk, canopy: cb.build(), radius, leaf: s.leaf } as TreeParts;
  });
}
