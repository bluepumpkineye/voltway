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
  // clipped hedge (rx: half length, ry: half height, rz: half depth) and a rounded shrub: a leafy mass with a fringe of small cards
  hedge: { trunkH: 0, trunkR: 0, cy: 0.5, rx: 1.25, ry: 0.55, rz: 0.5, cards: 72, size: [0.2, 0.36], leaf: 'shrub', bark: '#5a4a38', forks: 0 },
  shrub: { trunkH: 0, trunkR: 0, cy: 0.55, rx: 0.75, ry: 0.5, rz: 0.75, cards: 56, size: [0.22, 0.42], leaf: 'shrub', bark: '#5a4a38', forks: 0 },
};

export interface TreeParts {
  trunk: THREE.BufferGeometry | null;
  canopy: THREE.BufferGeometry;
  /** the canopy's reach on the ground, m: where its shadow falls */
  radius: number;
  leaf: Shape['leaf'];
  /** the trunk geometry is a solid leafy mass (hedges, shrubs), not bark */
  solid?: boolean;
  /** the soft shadow on the ground, m across and along: a hedge's is long, a canopy's round (left out: the canopy's) */
  shadow?: [number, number];
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

/** signed power: the superellipse's way round a corner (exponent 1 is a circle, small is a rounded box) */
const sgnPow = (x: number, e: number) => Math.sign(x) * Math.pow(Math.abs(x), e);

/**
 * A clipped hedge or a shrub. The body is a rounded mass (a superellipsoid: a hedge's top, sides and ends are the softly squared
 * shape of shears, a shrub is a mound with a little lumpiness) carrying the dense small-leaf texture of `foliageMass`, shaded
 * darker toward the ground and mottled; a fringe of small leaf cards lies on its skin, tilted out at the edges, to break the
 * outline. The cards are small, many and in the same greens, so nothing reads as a pom-pom or as a box with stickers.
 */
function clipped(kind: TreeKind, s: Shape, r: () => number): TreeParts {
  const hedge = kind === 'hedge';
  const e = hedge ? 0.42 : 0.82;
  const H = s.ry * 2;
  const lump = hedge ? 0.02 : 0.1;
  const ph = [r() * 6.28, r() * 6.28, r() * 6.28, r() * 6.28];
  // the skin at azimuth u (0..2 pi) and elevation v (0 at the ground, pi/2 at the top)
  const skin = (u: number, v: number): V3 => {
    const cv = Math.pow(Math.cos(v), e);
    const sv = Math.pow(Math.sin(v), e);
    const k = 1 + lump * (Math.sin(3 * u + ph[0]) * Math.cos(2.2 * v + ph[1]) + 0.6 * Math.sin(5 * u + ph[2] + v * 2));
    const kh = 1 + lump * 0.5 * Math.sin(4 * u + ph[3]);
    return [s.rx * cv * sgnPow(Math.cos(u), e) * k, H * sv * kh, s.rz * cv * sgnPow(Math.sin(u), e) * k];
  };

  // ---- the body
  const nu = 28;
  const nv = 8;
  const pos: number[] = [];
  for (let j = 0; j <= nv; j++) {
    for (let i = 0; i < nu; i++) {
      const p = skin((i / nu) * Math.PI * 2, (j / nv) * (Math.PI / 2));
      pos.push(p[0], p[1], p[2]);
    }
  }
  const idx: number[] = [];
  for (let j = 0; j < nv; j++) {
    for (let i = 0; i < nu; i++) {
      const a = j * nu + i;
      const b = j * nu + ((i + 1) % nu);
      const c = (j + 1) * nu + ((i + 1) % nu);
      const d = (j + 1) * nu + i;
      idx.push(a, d, b, b, d, c);
    }
  }
  const body = new THREE.BufferGeometry();
  body.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  body.setIndex(idx);
  body.computeVertexNormals();
  // the leaf texture is laid in metres on whichever plane the surface faces most (tops from above, sides from the side)
  const TILE = 0.9;
  const nrm = body.getAttribute('normal');
  const uv: number[] = [];
  for (let i = 0; i < nrm.count; i++) {
    const x = pos[i * 3];
    const y = pos[i * 3 + 1];
    const z = pos[i * 3 + 2];
    const ax = Math.abs(nrm.getX(i));
    const ay = Math.abs(nrm.getY(i));
    const az = Math.abs(nrm.getZ(i));
    if (ay >= ax && ay >= az) uv.push(x / TILE, z / TILE);
    else if (ax >= az) uv.push(z / TILE + 0.37, y / TILE);
    else uv.push(x / TILE, y / TILE + 0.61);
  }
  body.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  // darker toward the ground, mottled in patches the size of a hand
  const core = new Builder();
  core.add(body, new THREE.Matrix4(), [1, 1, 1], (x, y, z) => {
    const patch = 0.5 + 0.5 * Math.sin(x * 6.1 + z * 3.7 + ph[0]) * Math.sin(z * 5.3 - y * 4.1 + ph[1]);
    return (0.5 + 0.5 * smooth(0, H * 0.7, y)) * (0.86 + 0.2 * patch);
  });
  body.dispose();

  // ---- the fringe of small cards on the skin
  const cb = new Builder();
  const n = new THREE.Vector3();
  const du = new THREE.Vector3();
  const dv = new THREE.Vector3();
  for (let i = 0; i < s.cards; i++) {
    const top = r() < (hedge ? 0.42 : 0.34);
    const u = r() * Math.PI * 2;
    const v = (top ? 0.6 + r() * 0.38 : r() * 0.62) * (Math.PI / 2);
    const p = new THREE.Vector3(...skin(u, v));
    du.set(...skin(u + 0.01, v)).sub(p);
    dv.set(...skin(u, v + 0.01)).sub(p);
    n.crossVectors(dv, du).normalize();
    const a = du.clone().normalize();
    const b = new THREE.Vector3().crossVectors(n, a).normalize();
    const roll = r() * Math.PI * 2;
    const cr = a.clone().multiplyScalar(Math.cos(roll)).add(b.clone().multiplyScalar(Math.sin(roll)));
    const cu = b.clone().multiplyScalar(Math.cos(roll)).sub(a.clone().multiplyScalar(Math.sin(roll)));
    const size = s.size[0] + r() * (s.size[1] - s.size[0]);
    const hw = size / 2;
    // the card lies in the skin, its far edge lifted a little so it fringes the outline instead of lying flat on it
    const tilt = 0.25 + r() * 0.55;
    const c = p.clone().addScaledVector(n, 0.015 + r() * 0.03);
    const pt = (sx: number, sy: number): V3 => {
      const out = tilt * Math.max(0, sy) * hw;
      return [
        c.x + cr.x * hw * sx + cu.x * hw * sy + n.x * out,
        c.y + cr.y * hw * sx + cu.y * hw * sy + n.y * out,
        c.z + cr.z * hw * sx + cu.z * hw * sy + n.z * out,
      ];
    };
    const k = (0.62 + 0.38 * smooth(0, H, p.y)) * (0.92 + r() * 0.16);
    const sh = n.clone().multiplyScalar(0.6).add(new THREE.Vector3(0, 0.7, 0)).normalize();
    cb.quad(pt(-1, -1), pt(1, -1), pt(1, 1), pt(-1, 1), [k, k, k], [0, 0, 1, 1], false, [sh.x, sh.y, sh.z]);
  }
  // the soft shadow it throws on the ground: a hedge's is long (a little more than the hedge, and wider across), a shrub's round
  const shadow: [number, number] = hedge ? [s.rx * 2 * 1.2, s.rz * 2 * 2.3] : [s.rx * 2 * 1.9, s.rz * 2 * 1.9];
  return { trunk: core.build(), canopy: cb.build(), radius: Math.max(s.rx, s.rz) * 0.9, leaf: 'shrub', solid: true, shadow };
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
