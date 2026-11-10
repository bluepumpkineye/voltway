/**
 * The scenery kit: what the street, the lot and the road scenes are built from (docs/tech-showcase.md, section 22).
 *
 * Nothing here is downloaded. Every texture is painted on a canvas when a scene first needs it (a few hundred
 * milliseconds of one-off work, kept for the page's life), every mesh is built from a seeded generator and merged into
 * one geometry per material, and the trees, lamps and building rows that repeat are instanced. The look is stylised
 * realism: real materials (asphalt aggregate, paving joints, bark, leaves, stucco, glass) lit by the studio's light,
 * baked ambient occlusion in vertex colours, soft decals for shadows, and a haze that lets the far scenery go
 * into the studio's white as air would.
 */
import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

// ------------------------------------------------------------------------------------------------ random numbers

/** A small seeded generator (mulberry32): the same seed paints the same street on every machine. */
export function rng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export const clamp01 = (x: number) => Math.min(1, Math.max(0, x));
export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
export const smooth = (a: number, b: number, x: number) => {
  const t = clamp01((x - a) / (b - a));
  return t * t * (3 - 2 * t);
};

// ------------------------------------------------------------------------------------------------ canvases

export type Canvas2D = { canvas: HTMLCanvasElement; ctx: CanvasRenderingContext2D };

export function makeCanvas(w: number, h: number): Canvas2D {
  const canvas = document.createElement('canvas');
  canvas.width = Math.max(1, Math.round(w));
  canvas.height = Math.max(1, Math.round(h));
  return { canvas, ctx: canvas.getContext('2d', { willReadFrequently: true })! };
}

export function toTexture(
  canvas: HTMLCanvasElement,
  opts: { repeat?: boolean; srgb?: boolean; aniso?: number; mipmaps?: boolean } = {},
): THREE.CanvasTexture {
  const t = new THREE.CanvasTexture(canvas);
  t.colorSpace = opts.srgb === false ? THREE.NoColorSpace : THREE.SRGBColorSpace;
  t.anisotropy = opts.aniso ?? 8;
  if (opts.repeat) t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return t;
}

const memo = new Map<string, unknown>();
/** Painted once per page, whoever asks: the scenes come and go with the tabs, the paint does not. */
export function cached<T>(key: string, make: () => T): T {
  if (!memo.has(key)) memo.set(key, make());
  return memo.get(key) as T;
}

// ------------------------------------------------------------------------------------------------ noise

/**
 * Tileable value noise on a size x size grid, summed over octaves, in 0..1. The lattice wraps, so the result
 * repeats seamlessly: the asphalt, the paving and the walls are one tile each, laid over the ground.
 */
export function tileNoise(size: number, seed: number, octaves = 5, base = 4, gain = 0.5): Float32Array {
  const r = rng(seed);
  const out = new Float32Array(size * size);
  let amp = 1;
  let total = 0;
  for (let o = 0; o < octaves; o++) {
    const cells = base * 2 ** o;
    const lat = new Float32Array(cells * cells);
    for (let i = 0; i < lat.length; i++) lat[i] = r();
    const step = size / cells;
    for (let y = 0; y < size; y++) {
      const fy = y / step;
      const y0 = Math.floor(fy);
      const ty = fy - y0;
      const sy = ty * ty * (3 - 2 * ty);
      const ya = (y0 % cells) * cells;
      const yb = ((y0 + 1) % cells) * cells;
      for (let x = 0; x < size; x++) {
        const fx = x / step;
        const x0 = Math.floor(fx);
        const tx = fx - x0;
        const sx = tx * tx * (3 - 2 * tx);
        const xa = x0 % cells;
        const xb = (x0 + 1) % cells;
        const top = lat[ya + xa] + (lat[ya + xb] - lat[ya + xa]) * sx;
        const bot = lat[yb + xa] + (lat[yb + xb] - lat[yb + xa]) * sx;
        out[y * size + x] += (top + (bot - top) * sy) * amp;
      }
    }
    total += amp;
    amp *= gain;
  }
  for (let i = 0; i < out.length; i++) out[i] /= total;
  return out;
}

// ------------------------------------------------------------------------------------------------ colours

const tmpC = new THREE.Color();
export function hex(h: string, mul = 1): [number, number, number] {
  tmpC.set(h);
  return [tmpC.r * mul, tmpC.g * mul, tmpC.b * mul];
}

export function shade(h: string, k: number): string {
  tmpC.set(h);
  const hsl = { h: 0, s: 0, l: 0 };
  tmpC.getHSL(hsl);
  tmpC.setHSL(hsl.h, hsl.s, clamp01(hsl.l * k));
  return `#${tmpC.getHexString()}`;
}

// ------------------------------------------------------------------------------------------------ geometry builder

export type V3 = [number, number, number];

/**
 * Accumulates flat-shaded quads, boxes and merged primitives into one geometry with position, normal, uv and a colour
 * per vertex (the colour carries the tint and the baked occlusion). The scene's pieces are made of a few thousand of
 * these, so the builder writes into plain arrays and makes the BufferGeometry once.
 */
export class Builder {
  pos: number[] = [];
  nor: number[] = [];
  uv: number[] = [];
  col: number[] = [];
  idx: number[] = [];

  get vertices() {
    return this.pos.length / 3;
  }

  /** A quad a, b, c, d counter-clockwise seen from the front; uv rect (u0, v0, u1, v1); one colour or one per corner. */
  quad(a: V3, b: V3, c: V3, d: V3, color: V3 | V3[], uv: [number, number, number, number] = [0, 0, 1, 1], flip = false, normal?: V3) {
    const e1 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
    const e2 = [d[0] - a[0], d[1] - a[1], d[2] - a[2]];
    let nx = e1[1] * e2[2] - e1[2] * e2[1];
    let ny = e1[2] * e2[0] - e1[0] * e2[2];
    let nz = e1[0] * e2[1] - e1[1] * e2[0];
    if (normal) [nx, ny, nz] = normal;
    const l = Math.hypot(nx, ny, nz) || 1;
    nx /= l;
    ny /= l;
    nz /= l;
    const base = this.vertices;
    const cs = Array.isArray(color[0]) ? (color as V3[]) : [color as V3, color as V3, color as V3, color as V3];
    const [u0, v0, u1, v1] = uv;
    const us = [u0, u1, u1, u0];
    const vs = [v0, v0, v1, v1];
    [a, b, c, d].forEach((p, i) => {
      this.pos.push(p[0], p[1], p[2]);
      this.nor.push(nx, ny, nz);
      this.uv.push(us[i], vs[i]);
      this.col.push(cs[i][0], cs[i][1], cs[i][2]);
    });
    if (flip) this.idx.push(base, base + 2, base + 1, base, base + 3, base + 2);
    else this.idx.push(base, base + 1, base + 2, base, base + 2, base + 3);
  }

  /**
   * A rectangle in a plane given by an origin and two axes (u along, v up the rectangle), `w` by `h` metres, whose uv
   * is the metre position over `tile` (a repeating wall texture) shifted by `(ou, ov)`.
   */
  rect(o: V3, u: V3, v: V3, w: number, h: number, color: V3 | V3[], tile = 0, ou = 0, ov = 0, uvRect?: [number, number, number, number]) {
    const a: V3 = o;
    const b: V3 = [o[0] + u[0] * w, o[1] + u[1] * w, o[2] + u[2] * w];
    const c: V3 = [b[0] + v[0] * h, b[1] + v[1] * h, b[2] + v[2] * h];
    const d: V3 = [o[0] + v[0] * h, o[1] + v[1] * h, o[2] + v[2] * h];
    const rect: [number, number, number, number] = uvRect ?? (tile ? [ou / tile, ov / tile, (ou + w) / tile, (ov + h) / tile] : [0, 0, 1, 1]);
    this.quad(a, b, c, d, color, rect);
  }

  /** An axis-aligned box from its corner, size (sx, sy, sz); `sides` leaves out faces ('-x', '+x', '-y', '+y', '-z', '+z'). */
  box(x: number, y: number, z: number, sx: number, sy: number, sz: number, color: V3, tile = 0, skip: string[] = [], ao = 0) {
    const x1 = x + sx;
    const y1 = y + sy;
    const z1 = z + sz;
    const dim = (k: number): V3 => [color[0] * k, color[1] * k, color[2] * k];
    const top = dim(1);
    const side = dim(1 - ao * 0.35);
    const bot = dim(1 - ao);
    const t = tile || 0;
    // +z (front), -z, +x, -x, +y, -y
    if (!skip.includes('+z')) this.rect([x, y, z1], [1, 0, 0], [0, 1, 0], sx, sy, side, t, x, y);
    if (!skip.includes('-z')) this.rect([x1, y, z], [-1, 0, 0], [0, 1, 0], sx, sy, side, t, -x1, y);
    if (!skip.includes('+x')) this.rect([x1, y, z1], [0, 0, -1], [0, 1, 0], sz, sy, side, t, -z1, y);
    if (!skip.includes('-x')) this.rect([x, y, z], [0, 0, 1], [0, 1, 0], sz, sy, side, t, z, y);
    if (!skip.includes('+y')) this.rect([x, y1, z1], [1, 0, 0], [0, 0, -1], sx, sz, top, t, x, -z1);
    if (!skip.includes('-y')) this.rect([x, y, z], [1, 0, 0], [0, 0, 1], sx, sz, bot, t, x, z);
  }

  /** A triangle-mesh primitive (cylinder, sphere ...) moved, scaled and tinted, appended with its own normals. */
  add(g: THREE.BufferGeometry, matrix: THREE.Matrix4, color: V3, vary?: (x: number, y: number, z: number) => number) {
    const src = g.index ? g.toNonIndexed() : g.clone();
    src.applyMatrix4(matrix);
    const p = src.getAttribute('position');
    const n = src.getAttribute('normal');
    const u = src.getAttribute('uv');
    const base = this.vertices;
    for (let i = 0; i < p.count; i++) {
      this.pos.push(p.getX(i), p.getY(i), p.getZ(i));
      this.nor.push(n.getX(i), n.getY(i), n.getZ(i));
      this.uv.push(u ? u.getX(i) : 0, u ? u.getY(i) : 0);
      const k = vary ? vary(p.getX(i), p.getY(i), p.getZ(i)) : 1;
      this.col.push(color[0] * k, color[1] * k, color[2] * k);
      this.idx.push(base + i);
    }
    src.dispose();
  }

  build(): THREE.BufferGeometry {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(this.pos, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(this.nor, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(this.uv, 2));
    g.setAttribute('color', new THREE.Float32BufferAttribute(this.col, 3));
    g.setIndex(this.idx);
    g.computeBoundingSphere();
    g.computeBoundingBox();
    return g;
  }
}

const M = new THREE.Matrix4();
const Q = new THREE.Quaternion();
const E = new THREE.Euler();
export function placement(x: number, y: number, z: number, ry = 0, sx = 1, sy = sx, sz = sx, rx = 0, rz = 0): THREE.Matrix4 {
  E.set(rx, ry, rz);
  Q.setFromEuler(E);
  return M.clone().compose(new THREE.Vector3(x, y, z), Q, new THREE.Vector3(sx, sy, sz));
}

export function mergeAll(parts: THREE.BufferGeometry[]): THREE.BufferGeometry {
  return mergeGeometries(parts, false)!;
}

// ------------------------------------------------------------------------------------------------ haze

/**
 * The air between the camera and the far scenery, and the studio's white above it. One set of uniforms is shared by
 * every scenery material: the colour is the studio's white in the room's dusk (updated each frame by whoever
 * calls `setHaze`), the rest is geometry. Materials opt in with `withHaze`.
 *
 * The mix is done on the output colour, after tone mapping, as the studio's own gradient is: a hazed surface
 * and the wall behind it become the same white, so there is no seam.
 */
export const hazeUniforms = {
  uHazeColor: { value: new THREE.Vector3(0.945, 0.949, 0.957) },
  /** metres: the height at which the haze starts and the height at which the surface is all haze */
  uHazeY: { value: new THREE.Vector2(7, 30) },
  /** how much of the height haze to apply (a building's own top), and the distance haze's density */
  uHazeAmount: { value: 1 },
  uHazeDensity: { value: 0.0042 },
};

export function setHaze(room: THREE.Color, studioWhite: THREE.Color) {
  const c = tmpC.copy(studioWhite).multiply(room);
  const rgb = { r: 0, g: 0, b: 0 };
  c.getRGB(rgb, THREE.SRGBColorSpace);
  hazeUniforms.uHazeColor.value.set(rgb.r, rgb.g, rgb.b);
}

type HazeOpts = { height?: boolean; distance?: boolean; detail?: { map: THREE.Texture; repeat: THREE.Vector2; strength: number } };

/** Lets a material go into haze (and, if given, multiplies a tiled detail texture over its map). */
export function withHaze<T extends THREE.Material>(mat: T, opts: HazeOpts = {}): T {
  const height = opts.height !== false;
  const distance = opts.distance !== false;
  const detail = opts.detail;
  mat.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, hazeUniforms);
    if (detail) {
      shader.uniforms.uDetail = { value: detail.map };
      shader.uniforms.uDetailRepeat = { value: detail.repeat };
      shader.uniforms.uDetailStrength = { value: detail.strength };
    }
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vHazeW;')
      .replace(
        '#include <project_vertex>',
        `#include <project_vertex>
        vec4 hzp = vec4( transformed, 1.0 );
        #ifdef USE_INSTANCING
          hzp = instanceMatrix * hzp;
        #endif
        vHazeW = ( modelMatrix * hzp ).xyz;`,
      );
    let frag = shader.fragmentShader.replace(
      '#include <common>',
      `#include <common>
      varying vec3 vHazeW;
      uniform vec3 uHazeColor;
      uniform vec2 uHazeY;
      uniform float uHazeAmount;
      uniform float uHazeDensity;${detail ? '\nuniform sampler2D uDetail;\nuniform vec2 uDetailRepeat;\nuniform float uDetailStrength;' : ''}`,
    );
    if (detail) {
      frag = frag.replace(
        '#include <map_fragment>',
        `#include <map_fragment>
        vec2 dUv = vMapUv * uDetailRepeat;
        vec3 dtl = texture2D( uDetail, dUv ).rgb * texture2D( uDetail, dUv * 0.23 + vec2( 0.37, 0.61 ) ).rgb * 2.0 * texture2D( uDetail, dUv * 3.1 + vec2( 0.13, 0.29 ) ).rgb * 2.0;
        diffuseColor.rgb *= mix( vec3( 1.0 ), dtl * 2.0, uDetailStrength );`,
      );
    }
    frag = frag.replace(
      '#include <dithering_fragment>',
      `#include <dithering_fragment>
      float hzH = ${height ? 'smoothstep( uHazeY.x, uHazeY.y, vHazeW.y ) * uHazeAmount' : '0.0'};
      float hzD = ${distance ? '1.0 - exp( -length( vHazeW - cameraPosition ) * uHazeDensity )' : '0.0'};
      gl_FragColor.rgb = mix( gl_FragColor.rgb, uHazeColor, clamp( max( hzH, hzD * 0.85 ), 0.0, 1.0 ) );`,
    );
    shader.fragmentShader = frag;
  };
  mat.customProgramCacheKey = () => `haze${height ? 'H' : ''}${distance ? 'D' : ''}${detail ? 'T' : ''}`;
  return mat;
}
