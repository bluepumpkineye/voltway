import * as THREE from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import type { ConfiguratorSpec } from '@/data/vehicles/schema';
import { FX } from './settings';

/**
 * The cabin's smart material upgrader.
 *
 * `upgradeInteriorMaterials(scene, themeConfig)` walks a loaded cabin and turns its flat MeshStandardMaterials into
 * tactile MeshPhysicalMaterials, by what each one is (leather, perforated leather, Alcantara, screen glass, chrome,
 * brushed metal, piano black). It is built around three rules:
 *
 *  1. It never writes a colour. The Interior colour-theme switcher (configurator.ts `useTrim`) recolours the leathers
 *     by material name and tweens `.color` every frame; the upgrader replaces the material objects BEFORE useTrim looks
 *     for them (CarModel runs it in the clone's prepare step), keeps their names and userData, and leaves `.color` alone.
 *     The one colour-derived value, the sheen tint, is re-derived from the live colour by `syncSheenTint` each frame.
 *  2. It adds, it does not overwrite: a texture the Blender export already carries (the Seal's leather grain, its
 *     perforation normal, the brushed-metal streaks) is kept and only retuned; the procedural grain below is the
 *     fallback for a material that has none (or the comparison switch in the debug panel).
 *  3. Everything it sets from the debug panel's numbers is re-applied by `retuneInteriorMaterials`, so sliders are live.
 */

export type CabinKind = 'leather' | 'perf' | 'alcantara' | 'screen' | 'glass' | 'chrome' | 'brushed' | 'piano' | 'other';

const RULES: [RegExp, CabinKind][] = [
  [/leather_perf|perforat/, 'perf'],
  [/leather|nappa|soft_touch/, 'leather'],
  [/headliner|suede|alcantara|pillar/, 'alcantara'],
  [/screen_glass|display_screen|cluster/, 'screen'],
  [/band_glass|crystal/, 'glass'],
  [/chrome|logo_silver|mirror/, 'chrome'],
  [/brushed|gunmetal|knurl|speaker/, 'brushed'],
  [/piano|key_black/, 'piano'],
];

export function kindOf(name: string): CabinKind {
  const n = name.toLowerCase();
  for (const [re, k] of RULES) if (re.test(n)) return k;
  return 'other';
}

interface Base {
  kind: CabinKind;
  roughness: number;
  metalness: number;
  clearcoat: number;
  clearcoatRoughness: number;
  sheen: number;
  sheenRoughness: number;
  envMap: THREE.Texture | null;
  normalMap: THREE.Texture | null;
  normalScale: THREE.Vector2;
}

type Tuned = THREE.MeshPhysicalMaterial & { userData: { fxBase?: Base; fxKind?: CabinKind } };

function materialsOf(o: THREE.Mesh): THREE.Material[] {
  return Array.isArray(o.material) ? o.material : [o.material];
}

/** A MeshStandardMaterial as a MeshPhysicalMaterial: the standard fields carried over, the physical ones at their defaults. */
function asPhysical(m: THREE.Material): THREE.MeshPhysicalMaterial | null {
  if (m instanceof THREE.MeshPhysicalMaterial) return m;
  if (!(m instanceof THREE.MeshStandardMaterial)) return null;
  const p = new THREE.MeshPhysicalMaterial();
  THREE.MeshStandardMaterial.prototype.copy.call(p, m);
  p.name = m.name;
  return p;
}

/** The materials the colour-theme switcher recolours: their `.color` is the visitor's, the upgrader must not set it. */
function themedNames(spec: ConfiguratorSpec | undefined): Set<string> {
  const out = new Set<string>();
  for (const t of spec?.trims ?? []) for (const n of Object.keys(t.colors ?? {})) out.add(n.toLowerCase());
  return out;
}

/**
 * Pass 1, once per cloned cabin, before anything holds a reference to its materials: standard to physical, the kind of
 * each recorded, and the values the Blender export shipped kept as the baseline the panel's sliders are measured from.
 */
export function upgradeInteriorMaterials(root: THREE.Object3D, themeConfig?: ConfiguratorSpec): void {
  const themed = themedNames(themeConfig);
  const done = new Map<THREE.Material, THREE.MeshPhysicalMaterial>();
  root.traverse((o) => {
    const mesh = o as THREE.Mesh;
    if (!mesh.isMesh) return;
    const next = materialsOf(mesh).map((m) => {
      const hit = done.get(m);
      if (hit) return hit;
      const kind = kindOf(m.name);
      // only what the pass knows how to improve; the live HMI's backing, lamps and the like are left as built
      if (kind === 'other') return m;
      const p = asPhysical(m);
      if (!p) return m;
      const t = p as Tuned;
      t.userData.fxKind = kind;
      t.userData.fxThemed = themed.has(p.name.toLowerCase());
      t.userData.fxBase = {
        kind,
        roughness: p.roughness,
        metalness: p.metalness,
        clearcoat: p.clearcoat,
        clearcoatRoughness: p.clearcoatRoughness,
        sheen: p.sheen,
        sheenRoughness: p.sheenRoughness,
        envMap: p.envMap,
        normalMap: p.normalMap,
        normalScale: p.normalScale.clone(),
      };
      p.needsUpdate = true;
      done.set(m, p);
      return p;
    });
    if (next.some((m, i) => m !== materialsOf(mesh)[i])) mesh.material = Array.isArray(mesh.material) ? next : next[0];
  });
}

const _white = new THREE.Color(1, 1, 1);

/** Every tuned material in a cabin, once each. */
function tuned(root: THREE.Object3D): Tuned[] {
  const out = new Set<Tuned>();
  root.traverse((o) => {
    const mesh = o as THREE.Mesh;
    if (!mesh.isMesh) return;
    for (const m of materialsOf(mesh)) if ((m as Tuned).userData?.fxBase) out.add(m as Tuned);
  });
  return [...out];
}

/**
 * Pass 2, whenever a number changes: the panel's values onto the materials, from the baseline in each one's userData.
 * `glossEnv` is the softbox room's PMREM (null until it is built); `active` is false outside the seat, which puts every
 * material back as exported.
 */
export function retuneInteriorMaterials(root: THREE.Object3D, glossEnv: THREE.Texture | null, active: boolean): void {
  const on = active && FX.enabled;
  const g = FX.gloss;
  const mt = FX.materials;
  const leather = proceduralLeather();
  for (const m of tuned(root)) {
    const base = m.userData.fxBase as Base;
    const was = [m.roughness, m.metalness, m.clearcoat, m.sheen, m.envMap, m.normalMap] as const;
    // ---- start from what was exported
    m.roughness = base.roughness;
    m.metalness = base.metalness;
    m.clearcoat = base.clearcoat;
    m.clearcoatRoughness = base.clearcoatRoughness;
    m.sheen = base.sheen;
    m.sheenRoughness = base.sheenRoughness;
    m.normalMap = base.normalMap;
    m.normalScale.copy(base.normalScale);
    // the hall probe the cabin shader was given stays unless a softbox room replaces it on the gloss surfaces
    const hall = (m.userData.fxHall ??= base.envMap ?? m.envMap ?? null) as THREE.Texture | null;
    m.envMap = hall;
    m.envMapIntensity = 1;

    if (on) {
      switch (base.kind) {
        case 'leather': {
          m.roughness = mt.leatherRoughness;
          m.sheen = Math.max(base.sheen, mt.leatherSheen);
          m.sheenRoughness = 0.5;
          if (m.normalMap && !mt.proceduralLeather) {
            m.normalScale.set(mt.leatherNormal, mt.leatherNormal);
          } else {
            // no grain in the export (or the comparison switch): the procedural one, tiled over the UVs
            m.normalMap = leather.normal;
            m.normalScale.set(mt.leatherNormal, mt.leatherNormal);
          }
          break;
        }
        case 'perf': {
          // the holes' depth is in the normal map at its own strength: only the skin around them is retuned
          m.roughness = mt.leatherRoughness;
          m.sheen = Math.max(base.sheen, mt.leatherSheen);
          m.sheenRoughness = 0.5;
          if (!m.normalMap) {
            m.normalMap = proceduralPerforation();
            m.normalScale.set(1, 1);
          }
          break;
        }
        case 'alcantara':
          m.sheen = mt.alcantaraSheen;
          m.sheenRoughness = 0.8;
          m.roughness = 0.85;
          break;
        case 'screen':
          // the picture is emissive and stays crisp; the coat over it catches the studio's diagonal softbox
          m.clearcoat = 1;
          m.clearcoatRoughness = 0.04;
          m.roughness = 0.15;
          m.envMap = g.softbox && glossEnv ? glossEnv : hall;
          m.envMapIntensity = g.envIntensity;
          break;
        case 'glass':
          m.clearcoat = 1;
          m.clearcoatRoughness = 0.04;
          m.envMap = g.softbox && glossEnv ? glossEnv : hall;
          m.envMapIntensity = g.envIntensity;
          break;
        case 'chrome':
          m.metalness = 1;
          m.roughness = 0.08;
          m.envMap = g.softbox && glossEnv ? glossEnv : hall;
          m.envMapIntensity = g.chromeEnv;
          break;
        case 'brushed':
          m.metalness = Math.min(0.9, Math.max(base.metalness, 0.7));
          m.roughness = 0.28;
          break;
        case 'piano':
          m.roughness = 0.08;
          m.clearcoat = 1;
          m.clearcoatRoughness = 0.04;
          m.envMap = g.softbox && glossEnv ? glossEnv : hall;
          m.envMapIntensity = g.envIntensity;
          // #070707: a base the theme switcher never recolours
          if (!m.userData.fxThemed) m.color.set('#070707');
          break;
      }
    }
    // a feature that came or went (a coat, a sheen, a normal map) changes the program: compile it once, not per frame
    if (was[2] !== m.clearcoat && (was[2] === 0 || m.clearcoat === 0)) m.needsUpdate = true;
    if (was[3] !== m.sheen && (was[3] === 0 || m.sheen === 0)) m.needsUpdate = true;
    if (was[5] !== m.normalMap) m.needsUpdate = true;
    if (was[4] !== m.envMap) m.needsUpdate = true;
  }
}

/** The sheen of leather and Alcantara is a slightly lighter version of whatever colour the theme has made the surface. */
export function syncSheenTint(root: THREE.Object3D): boolean {
  let changed = false;
  for (const m of tuned(root)) {
    const k = (m.userData.fxBase as Base).kind;
    if (k !== 'leather' && k !== 'perf' && k !== 'alcantara') continue;
    if (m.sheen <= 0) continue;
    const lift = k === 'alcantara' ? 0.35 : 0.22;
    const t = m.userData.fxTint as THREE.Color | undefined;
    const next = (t ?? new THREE.Color()).copy(m.color).lerp(_white, lift);
    if (!t || !t.equals(next)) {
      m.userData.fxTint = next.clone();
      m.sheenColor.copy(next);
      changed = true;
    }
  }
  return changed;
}

// ------------------------------------------------------------ the gloss environment

/**
 * A high-contrast studio for the cabin's gloss surfaces: the PMREM of three's RoomEnvironment, a dark room with bright
 * softbox panels, so chrome, piano black and screen glass catch crisp highlights instead of the hall probe's even grey.
 * Built in an effect by the caller (a render target made in a memo does not survive StrictMode's cleanup).
 */
export function buildGlossEnvironment(gl: THREE.WebGLRenderer): THREE.WebGLRenderTarget {
  const pmrem = new THREE.PMREMGenerator(gl);
  const room = new RoomEnvironment();
  const rt = pmrem.fromScene(room, 0.03);
  room.traverse((o) => {
    const m = o as THREE.Mesh;
    if (m.isMesh) {
      m.geometry.dispose();
      (m.material as THREE.Material).dispose();
    }
  });
  pmrem.dispose();
  return rt;
}

// ----------------------------------------------------------------- procedural grain

export interface GrainTextures {
  normal: THREE.CanvasTexture;
  roughness: THREE.CanvasTexture;
}

let leatherCache: GrainTextures | null = null;
const LEATHER_REPEAT = 24;

/**
 * Seamless nappa grain: wrapped Worley cells (the pebbled skin and its creases), as a normal map and a roughness map,
 * 512 px tiled LEATHER_REPEAT times over a mesh's UVs. Used when the cabin carries no grain of its own.
 */
export function proceduralLeather(): GrainTextures {
  if (leatherCache) return leatherCache;
  const N = 512;
  const cells = 48;
  // one feature point per wrapped cell
  const px = new Float32Array(cells * cells);
  const py = new Float32Array(cells * cells);
  let seed = 1337;
  const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
  for (let i = 0; i < cells * cells; i++) {
    px[i] = rnd();
    py[i] = rnd();
  }
  const height = new Float32Array(N * N);
  for (let y = 0; y < N; y++) {
    for (let x = 0; x < N; x++) {
      const u = (x / N) * cells;
      const v = (y / N) * cells;
      const cu = Math.floor(u);
      const cv = Math.floor(v);
      let d1 = 9;
      let d2 = 9;
      for (let j = -1; j <= 1; j++) {
        for (let i = -1; i <= 1; i++) {
          const ci = (((cu + i) % cells) + cells) % cells;
          const cj = (((cv + j) % cells) + cells) % cells;
          const fx = cu + i + px[cj * cells + ci] - u;
          const fy = cv + j + py[cj * cells + ci] - v;
          const d = fx * fx + fy * fy;
          if (d < d1) {
            d2 = d1;
            d1 = d;
          } else if (d < d2) d2 = d;
        }
      }
      const edge = Math.sqrt(d2) - Math.sqrt(d1);
      // pebbles with soft creases between them
      height[y * N + x] = THREE.MathUtils.smoothstep(edge, 0, 0.34);
    }
  }
  const normal = document.createElement('canvas');
  normal.width = normal.height = N;
  const rough = document.createElement('canvas');
  rough.width = rough.height = N;
  const nc = normal.getContext('2d')!;
  const rc = rough.getContext('2d')!;
  const nd = nc.createImageData(N, N);
  const rd = rc.createImageData(N, N);
  const at = (x: number, y: number) => height[((y + N) % N) * N + ((x + N) % N)];
  const k = 3.2;
  for (let y = 0; y < N; y++) {
    for (let x = 0; x < N; x++) {
      const dx = (at(x + 1, y) - at(x - 1, y)) * k;
      const dy = (at(x, y + 1) - at(x, y - 1)) * k;
      const l = Math.hypot(dx, dy, 1);
      const o = (y * N + x) * 4;
      nd.data[o] = ((-dx / l) * 0.5 + 0.5) * 255;
      nd.data[o + 1] = ((dy / l) * 0.5 + 0.5) * 255;
      nd.data[o + 2] = ((1 / l) * 0.5 + 0.5) * 255;
      nd.data[o + 3] = 255;
      // creases hold dust and are rougher than the polished tops
      const r = 0.72 + (1 - height[y * N + x]) * 0.22;
      rd.data[o] = rd.data[o + 1] = rd.data[o + 2] = r * 255;
      rd.data[o + 3] = 255;
    }
  }
  nc.putImageData(nd, 0, 0);
  rc.putImageData(rd, 0, 0);
  const make = (c: HTMLCanvasElement, srgb: boolean) => {
    const t = new THREE.CanvasTexture(c);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.repeat.set(LEATHER_REPEAT, LEATHER_REPEAT);
    t.anisotropy = 8;
    t.flipY = false;
    t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    t.needsUpdate = true;
    return t;
  };
  leatherCache = { normal: make(normal, false), roughness: make(rough, false) };
  return leatherCache;
}

let perfCache: THREE.CanvasTexture | null = null;

/** A crisp dot-grid normal map for perforated leather: round holes with a bevelled lip, 64 px per hole pair, tiled. */
export function proceduralPerforation(repeat = 40): THREE.CanvasTexture {
  if (perfCache) return perfCache;
  const N = 128;
  const c = document.createElement('canvas');
  c.width = c.height = N;
  const ctx = c.getContext('2d')!;
  const img = ctx.createImageData(N, N);
  const R = N * 0.2;
  const lip = N * 0.07;
  for (let y = 0; y < N; y++) {
    for (let x = 0; x < N; x++) {
      // two holes per tile on a staggered grid
      let nx = 0;
      let ny = 0;
      for (const [cx, cy] of [
        [N * 0.25, N * 0.25],
        [N * 0.75, N * 0.75],
      ]) {
        const dx = x - cx;
        const dy = y - cy;
        const d = Math.hypot(dx, dy);
        if (d < R + lip && d > 0.001) {
          const slope = d < R ? 1 : 1 - (d - R) / lip;
          nx += (dx / d) * slope * (d < R ? -0.9 : 0.9);
          ny += (dy / d) * slope * (d < R ? -0.9 : 0.9);
        }
      }
      const l = Math.hypot(nx, ny, 1);
      const o = (y * N + x) * 4;
      img.data[o] = ((-nx / l) * 0.5 + 0.5) * 255;
      img.data[o + 1] = ((ny / l) * 0.5 + 0.5) * 255;
      img.data[o + 2] = ((1 / l) * 0.5 + 0.5) * 255;
      img.data[o + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeat, repeat);
  t.anisotropy = 8;
  t.flipY = false;
  t.colorSpace = THREE.NoColorSpace;
  t.needsUpdate = true;
  perfCache = t;
  return t;
}
