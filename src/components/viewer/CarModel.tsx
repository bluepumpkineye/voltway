'use client';

import React from 'react';
import * as THREE from 'three';
import { useGLTF, Html } from '@react-three/drei';
import { useFrame, useLoader, useThree } from '@react-three/fiber';
import { HDRLoader } from 'three/examples/jsm/loaders/HDRLoader.js';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { HmiSurface } from '@/components/hmi/HmiSurface';
import { HMI_W, HMI_H } from '@/components/hmi/ui';

/**
 * Blender exports with +Y up, so the car's axes arrive as:
 *   +X forward, +Y up, +Z toward the passenger side.
 */
export const DRACO_PATH = '/draco/';

/** carkit.bake.STORE_SCALE: the bake stores lighting x 0.25 to stay in [0, 1]. */
const BAKE_STORE_SCALE = 0.25;

/**
 * Object.clone() shares materials with the cached glTF, so mutating emissive
 * would leak across mounts and persist in useGLTF's cache. Clone them too.
 */
function useClonedScene(scene: THREE.Object3D) {
  return React.useMemo(() => {
    const root = scene.clone(true);
    const seen = new Map<THREE.Material, THREE.Material>();
    root.traverse((o) => {
      if (!(o instanceof THREE.Mesh)) return;
      const mats: THREE.Material[] = Array.isArray(o.material) ? o.material : [o.material];
      const cloned = mats.map((m) => {
        const hit = seen.get(m);
        if (hit) return hit;
        const c = m.clone();
        seen.set(m, c);
        return c;
      });
      o.material = Array.isArray(o.material) ? cloned : cloned[0];
    });
    return root;
  }, [scene]);
}

function materialsOf(o: THREE.Mesh): THREE.Material[] {
  return Array.isArray(o.material) ? o.material : [o.material];
}

// ------------------------------------------------------------------ exterior

interface Props {
  vehicle: Vehicle;
  variant: Variant;
  url: string;
}

export function CarModel({ vehicle, variant, url }: Props) {
  const { scene } = useGLTF(url, DRACO_PATH);
  const { headlightsOn, cameraMode } = useVehicleStore();
  const model = useClonedScene(scene);
  const inside = cameraMode === 'interior';
  const hasCabin = Boolean(vehicle.assets.interiorModelUrl);

  /*
   * The export merges the build down to a handful of meshes to hold draw calls,
   * so live surfaces are found by MATERIAL name. Two nodes are addressed by
   * name: the blackout layer (the black glass underlay and inner shadow shell
   * that make the glass read deep from outside - from inside they would wall
   * the camera in) and, on older single-file cars, the whole shell.
   */
  const refs = React.useMemo(() => {
    const headlamps: THREE.MeshStandardMaterial[] = [];
    const glass: THREE.MeshStandardMaterial[] = [];
    const blackout: THREE.Object3D[] = [];
    const shell: THREE.Object3D[] = [];
    model.traverse((o) => {
      // A node with several materials arrives as a Group of "<mesh>_N"
      // meshes, so match the node's own name on any object.
      const name = o.name.toLowerCase();
      if (name.endsWith('_blackout')) blackout.push(o);
      if (name === 'su7ultra_body' || name === 'su7ultra_wheels') shell.push(o);
      if (!(o instanceof THREE.Mesh)) return;
      o.castShadow = true;
      o.receiveShadow = true;
      for (const m of materialsOf(o)) {
        if (!(m instanceof THREE.MeshStandardMaterial)) continue;
        const mn = m.name.toLowerCase();
        // Only the light-pipe meshes emit; the housings and lenses around them
        // stay inert, which is what stops a lamp reading as a glowing blob.
        if (mn.includes('led_white')) headlamps.push(m);
        if (mn.startsWith('m_glass')) glass.push(m);
      }
    });
    return { headlamps, glass, blackout, shell };
  }, [model]);

  React.useEffect(() => {
    for (const m of refs.headlamps) {
      m.emissive = new THREE.Color('#eaf2ff');
      m.emissiveIntensity = headlightsOn ? 5.5 : 0.15;
      m.toneMapped = false;
      m.needsUpdate = true;
    }
  }, [refs.headlamps, headlightsOn]);

  // Inside the cabin: drop the blackout layer and see out through the glass.
  // Glass ships as dark opaque (KHR_materials_transmission blanks the three.js
  // frame), so from inside it becomes a tint that passes what the bake let in
  // (carkit.bake.GLASS_VLT): ~80 % through the windscreen and front door
  // glass, ~25 % through the privacy glass behind the B-pillar. Blending
  // happens on display values, not linear light, so the opacities are lower
  // than 1 - transmission (matched to the Cycles render through the same
  // camera). No reflection: the only environment it could mirror is the
  // outside, as a haze.
  React.useEffect(() => {
    if (!hasCabin) {
      // single-file cars: the old behaviour, hide the bodywork inside
      for (const o of refs.shell) o.visible = !inside;
      return;
    }
    for (const o of refs.blackout) o.visible = !inside;
    for (const m of refs.glass) {
      const privacy = m.name.toLowerCase().includes('privacy');
      m.transparent = inside;
      m.opacity = inside ? (privacy ? 0.5 : 0.12) : 1;
      m.depthWrite = !inside;
      m.envMapIntensity = inside ? 0 : 1;
      m.needsUpdate = true;
    }
    model.traverse((o) => {
      if (o instanceof THREE.Mesh && materialsOf(o).some((m) => refs.glass.includes(m as THREE.MeshStandardMaterial))) {
        o.castShadow = !inside;
      }
    });
  }, [refs, inside, hasCabin, model]);

  return (
    <group>
      <primitive object={model} />
      {!hasCabin && <LiveScreen model={model} vehicle={vehicle} variant={variant} />}
    </group>
  );
}

// -------------------------------------------------------------------- cabin

/**
 * The cabin, lit by its Cycles bake.
 *
 * Image-based lighting has no occlusion: inside a closed cabin it lights the
 * footwells like the dash top and every glossy trim mirrors the studio. The
 * build bakes Cycles' diffuse lighting into COLOR_0 (carkit/bake.py), and a
 * panorama shot from between the front seats becomes the cabin's reflections.
 * The shader patch below uses the vertex light IN PLACE of IBL diffuse, dims
 * reflections where the bake says the surface is enclosed, and ignores the
 * exterior's direct lights, which the bake already contains.
 */
export function CabinModel(props: Props & { probeUrl?: string }) {
  return props.probeUrl ? (
    <CabinWithProbe {...props} probeUrl={props.probeUrl} />
  ) : (
    <Cabin {...props} probe={null} />
  );
}

function CabinWithProbe(props: Props & { probeUrl: string }) {
  const tex = useLoader(HDRLoader, props.probeUrl);
  const probe = React.useMemo(() => {
    tex.mapping = THREE.EquirectangularReflectionMapping;
    return tex;
  }, [tex]);
  return <Cabin {...props} probe={probe} />;
}

function Cabin({ vehicle, variant, url, probe }: Props & { probe: THREE.Texture | null }) {
  const { scene } = useGLTF(url, DRACO_PATH);
  const model = useClonedScene(scene);
  const { ambientOn, ambientHue, ambientBrightness } = useVehicleStore();

  const refs = React.useMemo(() => {
    const ambient: THREE.MeshStandardMaterial[] = [];
    const screens: THREE.MeshStandardMaterial[] = [];
    model.traverse((o) => {
      if (!(o instanceof THREE.Mesh)) return;
      // the bake already holds every shadow
      o.castShadow = false;
      o.receiveShadow = false;
      // "_BAKEDLIGHT" arrives lower-cased; give it a GLSL-friendly name
      const g = o.geometry;
      const raw = g.getAttribute('_bakedlight');
      if (raw) {
        g.setAttribute('bakedLight', raw);
        g.deleteAttribute('_bakedlight');
      }
      const baked = Boolean(g.getAttribute('bakedLight'));
      for (const m of materialsOf(o)) {
        if (!(m instanceof THREE.MeshStandardMaterial)) continue;
        if (baked) bakedLighting(m, probe);
        const mn = m.name.toLowerCase();
        if (mn.includes('ambient')) ambient.push(m);
        else if (mn.includes('int_screen')) screens.push(m);
      }
    });
    return { ambient, screens };
  }, [model, probe]);

  // ---- live material state, driven by the HMI
  React.useEffect(() => {
    const col = new THREE.Color().setHSL(ambientHue / 360, 0.92, 0.5);
    for (const m of refs.ambient) {
      m.emissive = col;
      // a 3.4 mm light guide: bright enough to read as light, not as a neon tube
      m.emissiveIntensity = ambientOn ? ambientBrightness * 2.2 : 0;
      m.toneMapped = false;
      m.needsUpdate = true;
    }
  }, [refs.ambient, ambientOn, ambientHue, ambientBrightness]);

  React.useEffect(() => {
    // the live HMI covers screen_main, so its backing material stays dim
    for (const m of refs.screens) {
      m.emissive = new THREE.Color('#0b1626');
      m.emissiveIntensity = 1.1;
      m.toneMapped = false;
      m.needsUpdate = true;
    }
  }, [refs.screens]);

  // The door cards (int_door_L/R, origin on the hinge) stay shut: the painted
  // doors are merged into the body, so a card swinging alone would pass
  // through its own door skin. Swinging both needs the exterior doors split
  // out as their own nodes (docs/3d-pipeline.md, "Openings").

  return (
    <group>
      <primitive object={model} />
      <LiveScreen model={model} vehicle={vehicle} variant={variant} />
    </group>
  );
}

/**
 * Specular occlusion from the baked light, shared by every cabin material:
 * reflections scale by clamp(pow(x * L, 1.5), y, 1), L the baked irradiance's
 * luminance. Exposed as window.__specOcc in development, for tuning against
 * the Cycles render through the capture route.
 */
const SPEC_OCC = { value: new THREE.Vector2(1.25, 0.05) };
if (typeof window !== 'undefined' && process.env.NODE_ENV !== 'production') {
  (window as unknown as { __specOcc?: THREE.Vector2 }).__specOcc = SPEC_OCC.value;
}

function bakedLighting(m: THREE.MeshStandardMaterial, probe: THREE.Texture | null) {
  if (m.userData.baked) return;
  m.userData.baked = true;
  if (probe) {
    m.envMap = probe;
    m.envMapIntensity = 1.0;
  }
  const gain = Math.PI / BAKE_STORE_SCALE;
  m.onBeforeCompile = (shader) => {
    shader.uniforms.uBakeGain = { value: gain };
    // open trim (dash top, seat backs, wheel) keeps its full reflection, a
    // footwell a small part of it (SPEC_OCC)
    shader.uniforms.uSpecOcc = SPEC_OCC;
    shader.vertexShader = shader.vertexShader
      .replace('void main() {', 'attribute vec3 bakedLight;\nvarying vec3 vBakedLight;\nvoid main() {')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\n\tvBakedLight = bakedLight;');
    shader.fragmentShader = shader.fragmentShader
      .replace(
        'void main() {',
        'uniform float uBakeGain;\nuniform vec2 uSpecOcc;\nvarying vec3 vBakedLight;\nvoid main() {',
      )
      .replace(
        '#include <lights_fragment_maps>',
        `#include <lights_fragment_maps>
        {
          vec3 bakedE = vBakedLight * uBakeGain;
          float bakedL = dot( bakedE, vec3( 0.2126, 0.7152, 0.0722 ) );
          float specOcc = clamp( pow( bakedL * uSpecOcc.x, 1.5 ), uSpecOcc.y, 1.0 );
          iblIrradiance = bakedE;
          irradiance *= 0.0;
          radiance *= specOcc;
          #ifdef USE_CLEARCOAT
            clearcoatRadiance *= specOcc;
          #endif
        }`,
      )
      .replace(
        '#include <lights_fragment_end>',
        `#include <lights_fragment_end>
        reflectedLight.directDiffuse *= 0.0;
        reflectedLight.directSpecular *= 0.0;
        #ifdef USE_CLEARCOAT
          clearcoatSpecularDirect *= 0.0;
        #endif
        #ifdef USE_SHEEN
          sheenSpecularDirect *= 0.0;
        #endif`,
      );
  };
  m.customProgramCacheKey = () => 'cabin-baked-v3';
  m.needsUpdate = true;
}

// --------------------------------------------------------------- live HMI

/**
 * The live HMI, pinned onto `screen_main` by a per-frame perspective warp.
 *
 * drei's `<Html transform>` builds a CSS 3D camera in world units. The car is
 * in metres, so the page's 3D context has the eye ~0.7 "px" from the screen
 * under a ~500 px perspective, and Chrome's compositor (float32) drew the
 * layer a full screen-height above where layout - getBoundingClientRect,
 * hit-testing - put it. Instead: project the quad's four corners every frame
 * and map the 1280x800 surface onto them with a 2D homography (matrix3d with
 * only projective terms), which composites exactly where layout says.
 */
function LiveScreen({
  model,
  vehicle,
  variant,
}: {
  model: THREE.Object3D;
  vehicle: Vehicle;
  variant: Variant;
}) {
  const cameraMode = useVehicleStore((s) => s.cameraMode);
  const { camera, size } = useThree();
  const surface = React.useRef<HTMLDivElement>(null);

  const quad = React.useMemo(() => {
    let found: THREE.Mesh | null = null;
    model.traverse((o) => {
      if (o instanceof THREE.Mesh && o.name === 'screen_main') found = o;
    });
    if (!found) return null;
    const b = screenBasis(found);
    const across = new THREE.Vector3(1, 0, 0).applyQuaternion(b.quaternion);
    const up = new THREE.Vector3(0, 1, 0).applyQuaternion(b.quaternion);
    const hw = b.width / 2;
    const hh = (b.width * HMI_H) / HMI_W / 2;
    const at = (sx: number, sy: number) =>
      b.position.clone().addScaledVector(across, sx * hw).addScaledVector(up, sy * hh);
    // top-left, top-right, bottom-right, bottom-left as the driver sees it
    return { corners: [at(-1, 1), at(1, 1), at(1, -1), at(-1, -1)], centre: b.position };
  }, [model]);

  const tmp = React.useMemo(() => new THREE.Vector3(), []);
  useFrame(() => {
    const el = surface.current;
    if (!el || !quad) return;
    camera.updateMatrixWorld();
    const pts: [number, number][] = [];
    for (const c of quad.corners) {
      tmp.copy(c).applyMatrix4(camera.matrixWorldInverse);
      if (tmp.z > -0.02) {
        el.style.visibility = 'hidden'; // a corner is behind the eye
        return;
      }
      tmp.copy(c).project(camera);
      pts.push([(tmp.x + 1) * 0.5 * size.width, (1 - tmp.y) * 0.5 * size.height]);
    }
    el.style.visibility = 'visible';
    el.style.transform = quadToCss(pts, HMI_W, HMI_H);
  });

  if (!quad || cameraMode === 'exterior') return null;
  return (
    <Html calculatePosition={() => [0, 0]} zIndexRange={[16, 0]} wrapperClass="hmi-wrapper">
      <div
        ref={surface}
        style={{
          position: 'absolute', left: 0, top: 0, width: HMI_W, height: HMI_H,
          transformOrigin: '0 0', pointerEvents: 'auto', visibility: 'hidden',
        }}
      >
        <HmiSurface vehicle={vehicle} variant={variant} />
      </div>
    </Html>
  );
}

/**
 * CSS matrix3d taking a w x h box onto the quad p0..p3 (tl, tr, br, bl),
 * the classic square-to-quad homography scaled to the box.
 */
function quadToCss(p: [number, number][], w: number, h: number) {
  const [[x0, y0], [x1, y1], [x2, y2], [x3, y3]] = p;
  const dx1 = x1 - x2, dx2 = x3 - x2, dx3 = x0 - x1 + x2 - x3;
  const dy1 = y1 - y2, dy2 = y3 - y2, dy3 = y0 - y1 + y2 - y3;
  let g = 0, k = 0;
  const den = dx1 * dy2 - dx2 * dy1;
  if (Math.abs(den) > 1e-9) {
    g = (dx3 * dy2 - dx2 * dy3) / den;
    k = (dx1 * dy3 - dx3 * dy1) / den;
  }
  const a = x1 - x0 + g * x1, b = x3 - x0 + k * x3, c = x0;
  const d = y1 - y0 + g * y1, e = y3 - y0 + k * y3, f = y0;
  const m = [a / w, d / w, 0, g / w, b / h, e / h, 0, k / h, 0, 0, 1, 0, c, f, 0, 1];
  return `matrix3d(${m.map((v) => (Math.abs(v) < 1e-12 ? 0 : v)).join(',')})`;
}

/**
 * Derive the screen quad's basis from its geometry.
 *
 * Vertex order cannot be trusted - the glTF exporter reindexes meshes, so
 * assuming corner 0 is bottom-left rotates the UI by 90 degrees. Instead this
 * takes the face normal, projects world-up onto the plane to get the screen's
 * own up axis, and measures width and height as extents along that basis.
 * Order-independent, and it survives the cockpit being rebuilt.
 */
function screenBasis(mesh: THREE.Mesh) {
  mesh.updateWorldMatrix(true, false);
  const posAttr = mesh.geometry.getAttribute('position');
  const corners: THREE.Vector3[] = [];
  for (let i = 0; i < posAttr.count; i++) {
    corners.push(new THREE.Vector3().fromBufferAttribute(posAttr, i).applyMatrix4(mesh.matrixWorld));
  }
  if (corners.length < 3) {
    return { position: new THREE.Vector3(), quaternion: new THREE.Quaternion(), width: 0.35 };
  }

  const center = corners
    .reduce((a, c) => a.add(c), new THREE.Vector3())
    .multiplyScalar(1 / corners.length);

  // face normal from the largest triangle we can find among the corners
  let normal = new THREE.Vector3(0, 0, 1);
  let bestArea = 0;
  for (let i = 1; i < corners.length - 1; i++) {
    const a = new THREE.Vector3().subVectors(corners[i], corners[0]);
    const b = new THREE.Vector3().subVectors(corners[i + 1], corners[0]);
    const n = new THREE.Vector3().crossVectors(a, b);
    const area = n.length();
    if (area > bestArea) {
      bestArea = area;
      normal = n.clone().normalize();
    }
  }

  // the display faces the occupants, who sit behind it at smaller X
  if (normal.x > 0) normal.negate();

  const worldUp = new THREE.Vector3(0, 1, 0);
  const up = worldUp.clone().addScaledVector(normal, -worldUp.dot(normal)).normalize();
  const across = new THREE.Vector3().crossVectors(up, normal).normalize();

  const extent = (axis: THREE.Vector3) => {
    let lo = Infinity;
    let hi = -Infinity;
    for (const c of corners) {
      const d = new THREE.Vector3().subVectors(c, center).dot(axis);
      lo = Math.min(lo, d);
      hi = Math.max(hi, d);
    }
    return hi - lo;
  };

  const width = extent(across);
  const m = new THREE.Matrix4().makeBasis(across, up, normal);
  const quaternion = new THREE.Quaternion().setFromRotationMatrix(m);

  // sit a hair proud of the mesh so the HTML never z-fights its backing
  const position = center.clone().addScaledVector(normal, 0.004);

  return { position, quaternion, width };
}

useGLTF.preload('/models/su7-ultra.glb', DRACO_PATH);
