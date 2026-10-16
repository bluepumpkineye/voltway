import * as THREE from 'three';

/**
 * Denoises a cabin mesh's baked light.
 *
 * The cabin's lighting is Cycles' diffuse light baked per vertex (carkit/bake.py). Each vertex is its own Monte Carlo
 * estimate, and the Blender side only averages two passes over the mesh's edges: what is left shows on leather as soft
 * dark blotches, "dirty" patches a few centimetres across, and a lone dark vertex fades into a spot over its triangles.
 *
 * Here the light is relaxed over the mesh again, on the loaded geometry:
 *   - vertices that share a position (the glTF split them at UV seams and hard edges) are welded first, so a seam does
 *     not show as a step between two separately smoothed halves;
 *   - each pass blends a vertex with its edge neighbours, weighted by how alike their normals are and skipping neighbours
 *     across a crease, so a dash does not bleed into the windscreen's shadow;
 *   - a vertex far darker than the neighbours' median is a bake outlier, not a shadow, and is pulled up to it first.
 *
 * About 160 ms for the Z9's 174k vertices; runs once per geometry (the loader caches it).
 */
export const BAKE_SMOOTH_PASSES = 6;

const KEEP = 0.35; // share of its own value a vertex keeps each pass
const CREASE = 0.7; // neighbours whose normals differ by more than ~45 degrees are not averaged in
const OUTLIER = 0.3; // a vertex below this fraction of its neighbours' mean is replaced by it

export function smoothBakedLight(geometry: THREE.BufferGeometry, passes = BAKE_SMOOTH_PASSES) {
  const flag = geometry.userData as { bakeSmoothed?: boolean };
  if (flag.bakeSmoothed || passes <= 0) return;
  flag.bakeSmoothed = true;

  const pos = geometry.getAttribute('position');
  const nor = geometry.getAttribute('normal');
  const index = geometry.index;
  const sets = ['bakedLight', 'bakedLightOpen']
    .map((n) => geometry.getAttribute(n))
    .filter((a, i, all): a is THREE.BufferAttribute => Boolean(a) && all.indexOf(a) === i);
  if (!pos || !nor || !index || sets.length === 0) return;

  const n = pos.count;
  // weld by position (0.5 mm)
  const ids = new Map<number, number>();
  const gid = new Int32Array(n);
  let ng = 0;
  const Q = 2000;
  const OFF = 16384;
  for (let i = 0; i < n; i++) {
    const key =
      ((Math.round(pos.getX(i) * Q) + OFF) * 32768 + (Math.round(pos.getY(i) * Q) + OFF)) * 32768 +
      (Math.round(pos.getZ(i) * Q) + OFF);
    let id = ids.get(key);
    if (id === undefined) {
      id = ng++;
      ids.set(key, id);
    }
    gid[i] = id;
  }

  const gn = new Float32Array(ng * 3);
  for (let i = 0; i < n; i++) {
    const k = gid[i] * 3;
    gn[k] += nor.getX(i);
    gn[k + 1] += nor.getY(i);
    gn[k + 2] += nor.getZ(i);
  }
  for (let k = 0; k < ng; k++) {
    const l = Math.hypot(gn[k * 3], gn[k * 3 + 1], gn[k * 3 + 2]) || 1;
    gn[k * 3] /= l;
    gn[k * 3 + 1] /= l;
    gn[k * 3 + 2] /= l;
  }

  // the edge list between welded vertices, one entry per triangle edge
  const tri = index.count;
  const ea = new Int32Array(tri);
  const eb = new Int32Array(tri);
  const ew = new Float32Array(tri);
  let ne = 0;
  const edge = (a: number, b: number) => {
    if (a === b) return;
    const d = gn[a * 3] * gn[b * 3] + gn[a * 3 + 1] * gn[b * 3 + 1] + gn[a * 3 + 2] * gn[b * 3 + 2];
    if (d < CREASE) return;
    ea[ne] = a;
    eb[ne] = b;
    ew[ne] = d;
    ne++;
  };
  for (let t = 0; t < tri; t += 3) {
    const a = gid[index.getX(t)];
    const b = gid[index.getX(t + 1)];
    const c = gid[index.getX(t + 2)];
    edge(a, b);
    edge(b, c);
    edge(c, a);
  }

  const acc = new Float32Array(ng * 3);
  const wsum = new Float32Array(ng);
  for (const attr of sets) {
    // welded colours: the mean over a vertex's duplicates
    const col = new Float32Array(ng * 3);
    const cnt = new Float32Array(ng);
    for (let i = 0; i < n; i++) {
      const k = gid[i] * 3;
      col[k] += attr.getX(i);
      col[k + 1] += attr.getY(i);
      col[k + 2] += attr.getZ(i);
      cnt[gid[i]]++;
    }
    for (let g = 0; g < ng; g++) {
      col[g * 3] /= cnt[g];
      col[g * 3 + 1] /= cnt[g];
      col[g * 3 + 2] /= cnt[g];
    }

    for (let pass = 0; pass < passes; pass++) {
      acc.fill(0);
      wsum.fill(0);
      for (let e = 0; e < ne; e++) {
        const a = ea[e] * 3;
        const b = eb[e] * 3;
        const w = ew[e];
        acc[a] += w * col[b];
        acc[a + 1] += w * col[b + 1];
        acc[a + 2] += w * col[b + 2];
        acc[b] += w * col[a];
        acc[b + 1] += w * col[a + 1];
        acc[b + 2] += w * col[a + 2];
        wsum[ea[e]] += w;
        wsum[eb[e]] += w;
      }
      for (let g = 0; g < ng; g++) {
        const w = wsum[g];
        if (w <= 0) continue;
        const k = g * 3;
        const nr = acc[k] / w;
        const ng1 = acc[k + 1] / w;
        const nb = acc[k + 2] / w;
        const lum = 0.2126 * col[k] + 0.7152 * col[k + 1] + 0.0722 * col[k + 2];
        const nlum = 0.2126 * nr + 0.7152 * ng1 + 0.0722 * nb;
        // an outlier takes the neighbours' value outright (first pass only)
        const keep = pass === 0 && lum < OUTLIER * nlum ? 0 : KEEP;
        col[k] = keep * col[k] + (1 - keep) * nr;
        col[k + 1] = keep * col[k + 1] + (1 - keep) * ng1;
        col[k + 2] = keep * col[k + 2] + (1 - keep) * nb;
      }
    }

    for (let i = 0; i < n; i++) {
      const k = gid[i] * 3;
      attr.setXYZ(i, col[k], col[k + 1], col[k + 2]);
    }
    attr.needsUpdate = true;
  }
}
