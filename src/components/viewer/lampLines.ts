import * as THREE from 'three';

/**
 * A lamp's glow drawn as lines (docs/lights.md, "Line glow").
 *
 * The sprite glow (Lights.tsx) puts soft round blooms at points thinned out of the lamp's triangles. On an LED
 * that is a 3 mm light pipe it makes a chain of 4 cm blobs: a line drawn with a fat brush. This draws what a
 * lit light pipe looks like in a photograph instead: a razor-sharp white core exactly as wide as the pipe, a
 * tight glow hugging it, and a faint halo, all the same along the whole length, with clean rounded ends.
 *
 * The lines come from the lamp's own mesh: its triangles are welded into a graph of nodes (long edges are
 * subdivided, so a strip of two triangles has nodes along it), each connected piece is one pipe, and its
 * centreline is found by walking the graph: the node farthest from anywhere is one end, the node farthest from
 * that end is the other, and the nodes are binned by their distance along the path from the first. A bin's
 * centre is a point of the line and how far its nodes lie from the line is the pipe's half-width.
 *
 * Each line is a camera-facing ribbon (the vertex shader pushes it sideways in view space, so it is as wide
 * on screen as it is in the world), blended additively in display values like the rest of the glow.
 */

/** Distance between the samples of a line, m. */
const STEP = 0.003;
/** Vertices closer than this (in the model, m) are one node. */
const WELD = 0.00005;

export interface RibbonPack {
  /** the line's centre at each vertex, in the mesh's own space: two vertices (the two sides) per sample */
  pos: Float32Array;
  /** the line's direction there, mesh space */
  tan: Float32Array;
  /** per vertex: side (-1 or 1), distance along the line from its start (m), the line's length (m), half the pipe's width (m) */
  line: Float32Array;
  /** per vertex: -1 on the vertex row that extends the line's start, 1 on the end's, else 0 */
  ext: Float32Array;
  index: Uint32Array;
  /** how many lines, and how long they are in all, m (for the debug line) */
  lines: number;
  length: number;
}

class MinHeap {
  private d: number[] = [];
  private v: number[] = [];
  get size() {
    return this.d.length;
  }
  push(dist: number, node: number) {
    let i = this.d.length;
    this.d.push(dist);
    this.v.push(node);
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (this.d[p] <= this.d[i]) break;
      this.swap(i, p);
      i = p;
    }
  }
  pop(): [number, number] {
    const top: [number, number] = [this.d[0], this.v[0]];
    const last = this.d.length - 1;
    this.swap(0, last);
    this.d.pop();
    this.v.pop();
    let i = 0;
    for (;;) {
      const l = 2 * i + 1;
      const r = l + 1;
      let m = i;
      if (l < this.d.length && this.d[l] < this.d[m]) m = l;
      if (r < this.d.length && this.d[r] < this.d[m]) m = r;
      if (m === i) break;
      this.swap(i, m);
      i = m;
    }
    return top;
  }
  private swap(a: number, b: number) {
    [this.d[a], this.d[b]] = [this.d[b], this.d[a]];
    [this.v[a], this.v[b]] = [this.v[b], this.v[a]];
  }
}

/**
 * The lines of a lamp mesh: one per connected piece of it. `toModel` takes the mesh's space to the car's, which
 * is what lengths are measured in (a car's export is in metres). `keep` takes a point of the car's space and says
 * whether it belongs to the lamp: a triangle counts when all three of its points do. Null when the mesh has no piece
 * long enough.
 */
export function ribbonsOf(mesh: THREE.Mesh, toModel: THREE.Matrix4, keep?: (p: THREE.Vector3) => boolean): RibbonPack | null {
  const geo = mesh.geometry as THREE.BufferGeometry;
  const pos = geo.getAttribute('position');
  if (!pos) return null;
  const index = geo.index;
  const sc = new THREE.Vector3().setFromMatrixScale(toModel);
  const unit = (sc.x + sc.y + sc.z) / 3; // mesh units to metres

  // ---- nodes: the welded vertices
  const X: number[] = [];
  const Y: number[] = [];
  const Z: number[] = [];
  const adj: number[][] = [];
  const weldKey = new Map<string, number>();
  const nodeOfVertex = new Int32Array(pos.count);
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i);
    const y = pos.getY(i);
    const z = pos.getZ(i);
    const key = `${Math.round((x * unit) / WELD)},${Math.round((y * unit) / WELD)},${Math.round((z * unit) / WELD)}`;
    let n = weldKey.get(key);
    if (n === undefined) {
      n = X.length;
      X.push(x);
      Y.push(y);
      Z.push(z);
      adj.push([]);
      weldKey.set(key, n);
    }
    nodeOfVertex[i] = n;
  }

  const dist = (a: number, b: number) => Math.hypot(X[a] - X[b], Y[a] - Y[b], Z[a] - Z[b]) * unit;
  const link = (a: number, b: number) => {
    adj[a].push(b);
    adj[b].push(a);
  };

  // ---- edges, long ones subdivided into nodes about STEP apart
  const seen = new Set<number>();
  const tris = index ? index.count / 3 : Math.floor(pos.count / 3);
  const probe = new THREE.Vector3();
  const inside = (i: number) => !keep || keep(probe.set(pos.getX(i), pos.getY(i), pos.getZ(i)).applyMatrix4(toModel));
  for (let t = 0; t < tris; t++) {
    if (keep) {
      const i0 = index ? index.getX(t * 3) : t * 3;
      const i1 = index ? index.getX(t * 3 + 1) : t * 3 + 1;
      const i2 = index ? index.getX(t * 3 + 2) : t * 3 + 2;
      if (!inside(i0) || !inside(i1) || !inside(i2)) continue;
    }
    for (let k = 0; k < 3; k++) {
      const ia = index ? index.getX(t * 3 + k) : t * 3 + k;
      const ib = index ? index.getX(t * 3 + ((k + 1) % 3)) : t * 3 + ((k + 1) % 3);
      const a = nodeOfVertex[ia];
      const b = nodeOfVertex[ib];
      if (a === b) continue;
      const key = Math.min(a, b) * 4194304 + Math.max(a, b);
      if (seen.has(key)) continue;
      seen.add(key);
      const len = dist(a, b);
      const n = Math.ceil(len / (STEP * 1.2));
      if (n <= 1) {
        link(a, b);
        continue;
      }
      let prev = a;
      for (let j = 1; j < n; j++) {
        const f = j / n;
        const m = X.length;
        X.push(X[a] + (X[b] - X[a]) * f);
        Y.push(Y[a] + (Y[b] - Y[a]) * f);
        Z.push(Z[a] + (Z[b] - Z[a]) * f);
        adj.push([]);
        link(prev, m);
        prev = m;
      }
      link(prev, b);
    }
  }

  const N = X.length;
  const comp = new Int32Array(N).fill(-1);
  const D = new Float64Array(N);

  /** Distances from `src` over its piece (Infinity elsewhere): Dijkstra. */
  const dijkstra = (src: number) => {
    D.fill(Infinity);
    D[src] = 0;
    const heap = new MinHeap();
    heap.push(0, src);
    while (heap.size) {
      const [d, u] = heap.pop();
      if (d > D[u]) continue;
      for (const v of adj[u]) {
        const nd = d + dist(u, v);
        if (nd < D[v]) {
          D[v] = nd;
          heap.push(nd, v);
        }
      }
    }
  };

  const pos3: number[] = [];
  const tan3: number[] = [];
  const lineAttr: number[] = [];
  const extAttr: number[] = [];
  const idx: number[] = [];
  let lines = 0;
  let totalLength = 0;

  for (let seed = 0; seed < N; seed++) {
    if (comp[seed] !== -1) continue;
    // the piece this node belongs to
    const members: number[] = [];
    const stack = [seed];
    comp[seed] = seed;
    while (stack.length) {
      const u = stack.pop() as number;
      members.push(u);
      for (const v of adj[u]) {
        if (comp[v] === -1) {
          comp[v] = seed;
          stack.push(v);
        }
      }
    }
    if (members.length < 3) continue;

    // its two ends
    dijkstra(members[0]);
    let a = members[0];
    for (const m of members) if (D[m] > D[a]) a = m;
    dijkstra(a);
    let b = a;
    for (const m of members) if (D[m] > D[b]) b = m;
    const length = D[b];
    if (length < 0.0006) continue;

    // bin the nodes by their distance from end `a`
    const bins = new Map<number, number[]>();
    for (const m of members) {
      const k = Math.floor(D[m] / STEP);
      const list = bins.get(k);
      if (list) list.push(m);
      else bins.set(k, [m]);
    }
    const keys = [...bins.keys()].sort((p, q) => p - q);
    const cx: number[] = [];
    const cy: number[] = [];
    const cz: number[] = [];
    const lists: number[][] = [];
    for (const k of keys) {
      const list = bins.get(k) as number[];
      let sx = 0;
      let sy = 0;
      let sz = 0;
      for (const m of list) {
        sx += X[m];
        sy += Y[m];
        sz += Z[m];
      }
      cx.push(sx / list.length);
      cy.push(sy / list.length);
      cz.push(sz / list.length);
      lists.push(list);
    }
    // a piece shorter than one bin (a round LED dot): its two ends
    if (cx.length < 2) {
      cx.splice(0, cx.length, X[a], X[b]);
      cy.splice(0, cy.length, Y[a], Y[b]);
      cz.splice(0, cz.length, Z[a], Z[b]);
      lists.splice(0, lists.length, members, members);
    }
    const S = cx.length;
    // how wide the piece is, roughly: a wide band's bins are cut diagonally at its ends and their centres zigzag, so the wider it is
    // the more it is smoothed (a thin strip needs two passes of a 1-2-1 filter, a 4 cm band about ten)
    let maxHalf = 0;
    for (let i = 0; i < S; i++) {
      for (const m of lists[i]) {
        maxHalf = Math.max(maxHalf, Math.hypot(X[m] - cx[i], Y[m] - cy[i], Z[m] - cz[i]) * unit);
      }
    }
    const passes = 2 + Math.min(10, Math.floor(maxHalf / 0.004));
    const win = 2 + Math.min(8, Math.floor(maxHalf / 0.004));
    // the ends stay put; a 1-2-1 smoothing takes the zigzag of a strip's two sides out of the middle
    for (let pass = 0; pass < passes; pass++) {
      const nx = cx.slice();
      const ny = cy.slice();
      const nz = cz.slice();
      for (let i = 1; i < S - 1; i++) {
        nx[i] = (cx[i - 1] + 2 * cx[i] + cx[i + 1]) / 4;
        ny[i] = (cy[i - 1] + 2 * cy[i] + cy[i + 1]) / 4;
        nz[i] = (cz[i - 1] + 2 * cz[i] + cz[i + 1]) / 4;
      }
      for (let i = 0; i < S; i++) {
        cx[i] = nx[i];
        cy[i] = ny[i];
        cz[i] = nz[i];
      }
    }

    // direction, arc length and the pipe's half-width at each sample
    const tx: number[] = [];
    const ty: number[] = [];
    const tz: number[] = [];
    // the direction is taken over a window that grows with the width: a ribbon reaches centimetres to each side, so a tangent that
    // jitters a few degrees between neighbouring samples swings its far edge by millimetres and the overlapping quads add into streaks
    const span = 1 + Math.min(8, Math.floor(maxHalf / 0.004));
    for (let i = 0; i < S; i++) {
      const p = Math.max(0, i - span);
      const q = Math.min(S - 1, i + span);
      let dx = cx[q] - cx[p];
      let dy = cy[q] - cy[p];
      let dz = cz[q] - cz[p];
      const l = Math.hypot(dx, dy, dz) || 1;
      dx /= l;
      dy /= l;
      dz /= l;
      tx.push(dx);
      ty.push(dy);
      tz.push(dz);
    }
    // a compact piece (a lamp segment about as wide as it is long) has no centreline worth following: one straight direction along
    // it, or its ribbon fans into a star
    const chord = Math.hypot(cx[S - 1] - cx[0], cy[S - 1] - cy[0], cz[S - 1] - cz[0]);
    if (chord > 0 && chord * unit < 6 * maxHalf) {
      const dx = (cx[S - 1] - cx[0]) / chord;
      const dy = (cy[S - 1] - cy[0]) / chord;
      const dz = (cz[S - 1] - cz[0]) / chord;
      for (let i = 0; i < S; i++) {
        tx[i] = dx;
        ty[i] = dy;
        tz[i] = dz;
      }
    }
    const arc: number[] = [0];
    for (let i = 1; i < S; i++) {
      arc.push(arc[i - 1] + Math.hypot(cx[i] - cx[i - 1], cy[i] - cy[i - 1], cz[i] - cz[i - 1]) * unit);
    }
    const lineLen = arc[S - 1];
    const half: number[] = [];
    for (let i = 0; i < S; i++) {
      let w = 0;
      for (const m of lists[i]) {
        const vx = (X[m] - cx[i]) * unit;
        const vy = (Y[m] - cy[i]) * unit;
        const vz = (Z[m] - cz[i]) * unit;
        const along = vx * tx[i] + vy * ty[i] + vz * tz[i];
        w = Math.max(w, Math.hypot(vx - along * tx[i], vy - along * ty[i], vz - along * tz[i]));
      }
      half.push(w);
    }
    // the width, smoothed over a window (five samples for a thin strip), and never thinner than a third of a millimetre
    const halfS = half.map((_, i) => {
      let s = 0;
      let n = 0;
      for (let j = Math.max(0, i - win); j <= Math.min(S - 1, i + win); j++) {
        s += half[j];
        n++;
      }
      return Math.min(0.02, Math.max(0.0003, s / n));
    });

    // the ribbon: a row of two vertices per sample, and a row at each end that the shader pushes outward
    const base = pos3.length / 3;
    const row = (i: number, ext: number) => {
      for (const side of [-1, 1]) {
        pos3.push(cx[i], cy[i], cz[i]);
        tan3.push(tx[i], ty[i], tz[i]);
        lineAttr.push(side, arc[i], lineLen, halfS[i]);
        extAttr.push(ext);
      }
    };
    row(0, -1);
    for (let i = 0; i < S; i++) row(i, 0);
    row(S - 1, 1);
    const rows = S + 2;
    for (let r = 0; r < rows - 1; r++) {
      const v = base + r * 2;
      idx.push(v, v + 1, v + 2, v + 1, v + 3, v + 2);
    }
    lines++;
    totalLength += lineLen;
  }

  if (!lines) return null;
  return {
    pos: new Float32Array(pos3),
    tan: new Float32Array(tan3),
    line: new Float32Array(lineAttr),
    ext: new Float32Array(extAttr),
    index: new Uint32Array(idx),
    lines,
    length: totalLength,
  };
}

/** The ribbons as a geometry: its bounds include the glow's reach, which the shader adds in view space. */
export function lineGeometry(p: RibbonPack, reach: number): THREE.BufferGeometry {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(p.pos, 3));
  geo.setAttribute('aTan', new THREE.BufferAttribute(p.tan, 3));
  geo.setAttribute('aLine', new THREE.BufferAttribute(p.line, 4));
  geo.setAttribute('aExt', new THREE.BufferAttribute(p.ext, 1));
  geo.setIndex(new THREE.BufferAttribute(p.index, 1));
  geo.computeBoundingBox();
  const box = geo.boundingBox as THREE.Box3;
  box.expandByScalar(reach * 2);
  geo.boundingSphere = box.getBoundingSphere(new THREE.Sphere());
  return geo;
}

export const LINE_VERT = /* glsl */ `
  attribute vec3 aTan;
  attribute vec4 aLine;
  attribute float aExt;
  uniform float uReach;
  uniform float uCap;
  uniform float uBias;
  varying vec3 vL;
  varying float vHalf;
  void main() {
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    vec2 t = (modelViewMatrix * vec4(aTan, 0.0)).xy;
    float tl = length(t);
    vec2 dir = tl > 1e-4 ? t / tl : vec2(1.0, 0.0);
    vec2 n = vec2(-dir.y, dir.x);
    // sideways by the glow's reach, and the end rows out along the line, in view space (metres)
    mv.xy += n * (aLine.x * uReach) + dir * (aExt * uCap);
    mv.z += uBias;
    gl_Position = projectionMatrix * mv;
    vL = vec3(aLine.x * uReach, aLine.y + aExt * uCap, aLine.z);
    vHalf = aLine.w;
  }
`;

// d is the distance to the line (a capsule: the line's own segment, rounded at the ends), in metres. fwidth(vL.x) is how
// many metres a pixel is across the ribbon, so a thin line is never thinner than a pixel and the core's edge is
// anti-aliased at any distance. Display values, added in the framebuffer.
export const LINE_FRAG = /* glsl */ `
  uniform vec3 uCore;
  uniform vec3 uInner;
  uniform vec3 uHalo;
  uniform float uLevel;
  uniform float uCoreK;
  uniform float uSigIn;
  uniform float uSigHalo;
  uniform float uPeakIn;
  uniform float uPeakHalo;
  uniform float uReach;
  uniform float uCoreMax;
  varying vec3 vL;
  varying float vHalf;
  void main() {
    float over = max(max(-vL.y, vL.y - vL.z), 0.0);
    float d = length(vec2(vL.x, over));
    float px = max(fwidth(vL.x), 0.00002);
    // the white core is the pipe itself, but never wider than a tube: a wide band (a tail lamp's corner) is lit by the
    // mesh's own emissive and gets the glow round its edge, with only a thin hot line down its middle
    float w = max(min(vHalf, uCoreMax) + 0.0002, px * 0.8);
    float core = 1.0 - smoothstep(w - px * 0.7, w + px * 0.7, d);
    float dEdge = max(d - max(vHalf - w, 0.0), 0.0);
    float si = max(uSigIn, px * 1.6);
    float sh = max(uSigHalo, px * 3.5);
    float gi = exp(-(dEdge * dEdge) / (si * si));
    float gh = exp(-(dEdge * dEdge) / (sh * sh));
    float edge = 1.0 - smoothstep(0.6, 1.0, abs(vL.x) / uReach);
    vec3 c = uCore * (core * uCoreK) + uInner * (gi * uPeakIn * uLevel) + uHalo * (gh * uPeakHalo * uLevel);
    gl_FragColor = vec4(c * edge, 1.0);
  }
`;
