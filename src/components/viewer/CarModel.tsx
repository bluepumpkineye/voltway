'use client';

import React from 'react';
import * as THREE from 'three';
import { useGLTF, Html } from '@react-three/drei';
import { addAfterEffect, useFrame, useLoader, useThree } from '@react-three/fiber';
import { HDRLoader } from 'three/examples/jsm/loaders/HDRLoader.js';
import type { OpeningId, Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { HmiSurface } from '@/components/hmi/HmiSurface';
import { HMI_W, HMI_H } from '@/components/hmi/ui';
import { useCaliper, usePaint, useTrim, useWheels } from './configurator';
import { useGlass, useHiddenWhileOpen, useHingedNodes, useOpeningPicks, useStruts } from './Openings';
import { cullBehindClearGlass, useCabinStencil, useGlassStencil } from './clearGlass';
import { useXray, useXrayCabin } from './Xray';
import { hingesOf } from '@/lib/openings';
import { prepareRig } from '@/lib/tech/rig';
import { CarLights } from './Lights';
import { useRigBinding } from './techRig';
import { rigSwivel } from './ScreenSwivel';
import { smoothBakedLight } from './bakeSmooth';

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
function useClonedScene(scene: THREE.Object3D, prepare?: (root: THREE.Object3D) => unknown) {
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
    // the tech demos' rig (wheels that steer, a body on springs): a pure rebuild of this clone
    prepare?.(root);
    return root;
  }, [scene, prepare]);
}

function materialsOf(o: THREE.Mesh): THREE.Material[] {
  return Array.isArray(o.material) ? o.material : [o.material];
}

// --------------------------------------------------------- exterior occlusion

/**
 * The exterior's baked ambient occlusion (carkit.bake.ambient_occlusion): a
 * float per vertex, 1 open to the sky and 0 shut in. A studio lights a car from
 * every side, so what shades a surface is what the car itself shuts out: the
 * arches, the cavities behind the bumpers, the cowl. Image-based light has no
 * occlusion of its own and floods all of them like the roof, so the patch
 * below multiplies the environment's light by this value, as three.js does
 * for an aoMap (aomap_fragment): indirect diffuse, clear coat and sheen, and
 * the reflections with specular occlusion. Direct light (the city's sun) has
 * its shadow map and is left alone.
 *
 * Exposed as window.__ao in development: `strength.value` 0..1 (0 = off),
 * `view.value` 1 shows the occlusion itself.
 */
const OCCLUSION = { value: 1 };
const OCCLUSION_VIEW = { value: 0 };
if (typeof window !== 'undefined' && process.env.NODE_ENV !== 'production') {
  (window as unknown as { __ao?: unknown }).__ao = { strength: OCCLUSION, view: OCCLUSION_VIEW };
}

/** Surfaces that are not shaded by what is around them: glazing and lenses, lamps, the blackout layer. */
const NO_OCCLUSION = /glass|lamp_clear|lamp_smoked|led_|m_shadow/;

function takesOcclusion(m: THREE.Material): boolean {
  return !NO_OCCLUSION.test(m.name.toLowerCase());
}

/**
 * Give the geometry the GLSL-friendly attribute the patch reads. GLTFLoader
 * lower-cases a custom attribute ("_BAKEDAO" arrives as "_bakedao"); a mesh
 * the bake did not reach gets 1 (a patched material shared with it would
 * otherwise read the attribute's default, 0, and go black).
 */
function bindOcclusion(g: THREE.BufferGeometry) {
  const raw = g.getAttribute('_bakedao');
  if (raw) {
    g.setAttribute('bakedAO', raw);
    g.deleteAttribute('_bakedao');
  } else if (!g.getAttribute('bakedAO')) {
    const n = g.getAttribute('position').count;
    g.setAttribute('bakedAO', new THREE.BufferAttribute(new Float32Array(n).fill(1), 1));
  }
}

function bakedOcclusion(m: THREE.Material) {
  if (m.userData.occluded) return;
  m.userData.occluded = true;
  const chained = m.onBeforeCompile;
  m.onBeforeCompile = (shader, renderer) => {
    chained.call(m, shader, renderer);
    shader.uniforms.uOcclusion = OCCLUSION;
    shader.uniforms.uOcclusionView = OCCLUSION_VIEW;
    shader.vertexShader = shader.vertexShader
      .replace('void main() {', 'attribute float bakedAO;\nvarying float vBakedAO;\nvoid main() {')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\n\tvBakedAO = bakedAO;');
    shader.fragmentShader = shader.fragmentShader
      .replace(
        'void main() {',
        'uniform float uOcclusion;\nuniform float uOcclusionView;\nvarying float vBakedAO;\nvoid main() {',
      )
      .replace(
        '#include <aomap_fragment>',
        `#include <aomap_fragment>
        {
          float bakedOcc = mix( 1.0, vBakedAO, uOcclusion );
          reflectedLight.indirectDiffuse *= bakedOcc;
          #ifdef USE_CLEARCOAT
            clearcoatSpecularIndirect *= bakedOcc;
          #endif
          #ifdef USE_SHEEN
            sheenSpecularIndirect *= bakedOcc;
          #endif
          #if defined( USE_ENVMAP ) && defined( STANDARD )
            float dotNVocc = saturate( dot( geometryNormal, geometryViewDir ) );
            reflectedLight.indirectSpecular *= computeSpecularOcclusion( dotNVocc, bakedOcc, material.roughness );
          #endif
        }`,
      )
      .replace(
        '#include <opaque_fragment>',
        'if ( uOcclusionView > 0.5 ) outgoingLight = vec3( vBakedAO );\n#include <opaque_fragment>',
      );
  };
  m.customProgramCacheKey = () => 'exterior-occlusion-v1';
  m.needsUpdate = true;
}

// ------------------------------------------------------------------ exterior

interface Props {
  vehicle: Vehicle;
  variant: Variant;
  url: string;
  customPaintId?: string;
  forceClearGlass?: boolean;
}

export function CarModel({ vehicle, variant, url, customPaintId, forceClearGlass }: Props) {
  const { scene } = useGLTF(url, DRACO_PATH);
  const { cameraMode, paintId: storePaintId, caliperId, wheelId } = useVehicleStore();
  const paintId = customPaintId !== undefined ? customPaintId : storePaintId;
  const invalidate = useThree((s) => s.invalidate);
  const model = useClonedScene(scene, prepareRig);
  useRigBinding(model, vehicle);
  const inside = cameraMode === 'interior';
  const hasCabin = Boolean(vehicle.assets.interiorModelUrl);

  // the showroom's paint swatches (the first option is the car as exported)
  usePaint(model, vehicle.configurator, paintId);
  useCaliper(model, vehicle.configurator, caliperId);
  useWheels(model, vehicle.configurator, wheelId);

  // the doors swing on their hinge nodes (vehicle.openings) and open on a tap
  useHingedNodes(model, vehicle, 'node');
  useHingedNodes(model, vehicle, 'frameNode');
  const xray = useVehicleStore((s) => s.tab === 'xray') && Boolean(vehicle.xray) && hasCabin;
  // the cabin is mounted behind the exterior (ShowroomViewer): the windscreen and the front windows are clear glass once it is
  const cabinReady = useVehicleStore((s) => s.cabinReady);
  const isCabinReady = forceClearGlass !== undefined ? forceClearGlass : cabinReady;
  // not on the Tech tab: its demos move the car, and the cabin does not move with it
  const clearTab = useVehicleStore((s) => s.tab !== 'tech');
  const shut = useVehicleStore((s) => s.shut);
  useGlass(model, vehicle, inside, hasCabin, xray, isCabinReady && clearTab);
  useGlassStencil(model, hasCabin && isCabinReady && clearTab && !inside && !xray && shut);
  useXray(model, vehicle, xray);
  useStruts(model, vehicle);
  const picks = useOpeningPicks(model, vehicle, 'node');

  /*
   * The export merges the build down to a handful of meshes to hold draw calls,
   * so live surfaces are found by MATERIAL name. Two nodes are addressed by
   * name: the blackout layer (the black glass underlay and inner shadow shell
   * that make the glass read deep from outside - from inside they would wall
   * the camera in) and, on older single-file cars, the whole shell.
   */
  const refs = React.useMemo(() => {
    const blackout: THREE.Object3D[] = [];
    const shadow: THREE.Object3D[] = [];
    const shell: THREE.Object3D[] = [];
    // a car whose exterior was baked with occlusion (the others render as
    // before). The geometry is shared with useGLTF's cache, so a second mount
    // finds the attribute already renamed.
    let baked = false;
    model.traverse((o) => {
      if (o instanceof THREE.Mesh && (o.geometry.getAttribute('_bakedao') || o.geometry.getAttribute('bakedAO'))) {
        baked = true;
      }
    });
    model.traverse((o) => {
      // A node with several materials arrives as a Group of "<mesh>_N"
      // meshes, so match the node's own name on any object.
      const name = o.name.toLowerCase();
      if (name.endsWith('_blackout')) blackout.push(o);
      if (name === 'su7ultra_body' || name === 'su7ultra_wheels') shell.push(o);
      if (!(o instanceof THREE.Mesh)) return;
      o.castShadow = true;
      o.receiveShadow = true;
      if (baked) bindOcclusion(o.geometry);
      for (const m of materialsOf(o)) {
        if (!(m instanceof THREE.MeshStandardMaterial)) continue;
        if (baked && takesOcclusion(m)) bakedOcclusion(m);
        // the dark backing of a pane that is not in the blackout node (the tailgate's)
        if (m.name.toLowerCase() === 'm_shadow') shadow.push(o);
      }
    });
    return { blackout, shadow, shell };
  }, [model]);

  // the car is on screen: the cabin may come in behind it
  const setExteriorUp = useVehicleStore((s) => s.setExteriorUp);
  React.useEffect(() => {
    setExteriorUp(true);
    return () => setExteriorUp(false);
  }, [setExteriorUp]);

  // the black layers behind the windscreen and the front windows are cut away, so the cabin shows through them (clearGlass.ts)
  React.useEffect(() => (hasCabin ? cullBehindClearGlass(model, refs.blackout) : undefined), [model, refs, hasCabin]);

  // Inside the cabin: drop the blackout layer and see out through the glass
  // (useGlass tints it: ~80 % through the windscreen and front door glass,
  // ~25 % through the privacy glass behind the B-pillar, matched to the Cycles
  // render through the same camera - carkit.bake.GLASS_VLT - with no
  // reflection: the only environment it could mirror is the outside, as a haze).
  React.useEffect(() => {
    if (!hasCabin) {
      // single-file cars: the old behaviour, hide the bodywork inside
      for (const o of refs.shell) o.visible = !inside;
      return;
    }
    const clear = inside || xray;
    for (const o of refs.blackout) o.visible = !clear;
    for (const o of refs.shadow) o.visible = !clear;
    model.traverse((o) => {
      if (o instanceof THREE.Mesh && materialsOf(o).some((m) => m.name.toLowerCase().startsWith('m_glass'))) {
        o.castShadow = !inside;
      }
    });
    invalidate();
  }, [refs, inside, xray, hasCabin, model, invalidate]);

  return (
    <group>
      <primitive object={model} {...picks} />
      {/* the LED lamps, their glow and their light on the floor (Lights.tsx) */}
      <CarLights model={model} vehicle={vehicle} />
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
  const { ambientOn, ambientHue, ambientBrightness, trimId } = useVehicleStore();
  const invalidate = useThree((s) => s.invalidate);
  React.useEffect(() => {
    if (process.env.NODE_ENV !== 'production') (window as unknown as { __invalidate?: () => void }).__invalidate = invalidate;
  }, [invalidate]);

  // a car with a motorised centre screen: its frame is cut out of the merged cabin mesh and hung with the picture on a
  // pivot (ScreenDriver turns it). Done while rendering, so the live HMI below finds the picture under its pivot.
  React.useMemo(() => {
    if (vehicle.swivel) rigSwivel(model, vehicle.swivel);
  }, [model, vehicle]);

  // each door card gets materials of its own: its light follows its swing
  React.useMemo(() => {
    for (const s of vehicle.openings ?? []) {
      const card = s.cardNode ? model.getObjectByName(s.cardNode) : undefined;
      card?.traverse((o) => {
        const mesh = o as THREE.Mesh;
        if (!mesh.isMesh) return;
        const own = materialsOf(mesh).map((m) => {
          const c = m.clone();
          c.userData = { ...m.userData, baked: false, opening: s.id };
          return c;
        });
        mesh.material = Array.isArray(mesh.material) ? own : own[0];
      });
    }
  }, [model, vehicle]);

  // the showroom's cabin colourways (the first option is the cabin as built)
  useTrim(model, vehicle.configurator, trimId);

  // the cabin is there: the exterior's clear glass may show it
  const setCabinReady = useVehicleStore((s) => s.setCabinReady);
  React.useEffect(() => {
    setCabinReady(true);
    return () => setCabinReady(false);
  }, [setCabinReady]);

  // From outside, with every part shut, the cabin is drawn only where clear glass is in front of it: nothing of it can show
  // through the bodywork, and the windscreen and front windows are windows (clearGlass.ts)
  const masked = useVehicleStore((s) => s.cameraMode === 'exterior' && s.tab !== 'xray' && s.tab !== 'tech' && s.shut);
  useCabinStencil(model, masked);

  // The boot's carpet, trim and plate (INT_Boot_*) are the open hatch's to show. Shut, nothing of them is seen through the
  // glass; but with a door open the cabin is no longer stencilled to the glass, and the shut line beside the hatch showed
  // them as a black blade down each tail corner.
  const bootShown = useVehicleStore((s) => s.openings.boot || s.tab === 'xray');
  React.useEffect(() => {
    model.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (mesh.isMesh && materialsOf(mesh).some((m) => m.name.startsWith('INT_Boot_'))) mesh.visible = bootShown;
    });
    invalidate();
  }, [model, bootShown, invalidate]);

  // the door cards turn about the same hinges as the exterior doors
  useHingedNodes(model, vehicle, 'cardNode');
  useHiddenWhileOpen(model, vehicle, useVehicleStore((s) => s.cameraMode !== 'exterior'));
  useXrayCabin(model, vehicle, useVehicleStore((s) => s.tab === 'xray'));
  const picks = useOpeningPicks(model, vehicle, 'cardNode');

  const refs = React.useMemo(() => {
    CABIN_GAIN.value = vehicle.assets.cabinGain ?? 1;
    const ambient: THREE.MeshStandardMaterial[] = [];
    const screens: THREE.MeshStandardMaterial[] = [];
    model.traverse((o) => {
      if (!(o instanceof THREE.Mesh)) return;
      // the bake already holds every shadow
      o.castShadow = false;
      o.receiveShadow = false;
      // "_BAKEDLIGHT" arrives lower-cased; give it a GLSL-friendly name. The
      // second set (_BAKEDLIGHT_OPEN, the cabin baked with its doors and
      // tailgate open) falls back to the first for a car that has none.
      const g = o.geometry;
      const raw = g.getAttribute('_bakedlight');
      if (raw) {
        g.setAttribute('bakedLight', raw);
        g.setAttribute('bakedLightOpen', g.getAttribute('_bakedlight_open') ?? raw);
        g.deleteAttribute('_bakedlight');
        g.deleteAttribute('_bakedlight_open');
        // the bake is one Monte Carlo estimate per vertex: relax it, or the leather reads as dirty, blotchy
        smoothBakedLight(g);
      }
      const baked = Boolean(g.getAttribute('bakedLight'));
      // a cabin with an occlusion atlas on its second UV set (carkit.aoatlas) is lit by the hall instead
      const atlas = !baked && Boolean(g.getAttribute('uv1'));
      for (const m of materialsOf(o)) {
        if (!(m instanceof THREE.MeshStandardMaterial)) continue;
        if (atlas) hallLighting(m, probe);
        else if (baked) {
          const id = m.userData.opening as OpeningId | undefined;
          const hinges = hingesOf(vehicle);
          bakedLighting(m, probe, id && hinges ? hinges.liftOf(id) : hinges?.lift.cabin);
        }
        const mn = m.name.toLowerCase();
        if (mn.includes('ambient')) ambient.push(m);
        else if (mn.includes('int_screen')) screens.push(m);
      }
    });
    return { ambient, screens };
  }, [model, probe, vehicle]);

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
    invalidate();
  }, [refs.ambient, ambientOn, ambientHue, ambientBrightness, invalidate]);

  React.useEffect(() => {
    // the live HMI covers screen_main, so its backing material stays dim
    for (const m of refs.screens) {
      m.emissive = new THREE.Color('#0b1626');
      m.emissiveIntensity = 1.1;
      m.toneMapped = false;
      m.needsUpdate = true;
    }
    invalidate();
  }, [refs.screens, invalidate]);

  return (
    <group>
      <primitive object={model} {...picks} />
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
/**
 * A car's own multiplier on its baked cabin light (`assets.cabinGain`, 1 when unset): a pale
 * cabin lit by daylight through the glass reads darker than the studio photographs of it, and
 * this lifts it without re-baking. Exposed as window.__cabinGain in development.
 */
const CABIN_GAIN = { value: 1 };

if (typeof window !== 'undefined' && process.env.NODE_ENV !== 'production') {
  (window as unknown as { __specOcc?: THREE.Vector2 }).__specOcc = SPEC_OCC.value;
  Object.defineProperty(window, '__cabinGain', {
    configurable: true,
    get: () => CABIN_GAIN.value,
    set: (v: number) => {
      CABIN_GAIN.value = v;
    },
  });
}


/**
 * HIMA's cabin light: a bright, even hall environment shaded by a baked occlusion atlas, and nothing else (docs/hima-benchmark.md).
 * The glTF's occlusionTexture (TEXCOORD_1, carkit.aoatlas) multiplies the environment's diffuse and specular light in three's own
 * aomap_fragment; the scene's lamps and ambient light stay out. x = diffuse gain (times the car's `cabinGain`), y = reflection
 * gain, both tunable live as window.__hallGain in development.
 */
const HALL_GAIN = { value: new THREE.Vector2(2.0, 1.4) };
if (typeof window !== 'undefined' && process.env.NODE_ENV !== 'production') {
  (window as unknown as { __hallGain?: THREE.Vector2 }).__hallGain = HALL_GAIN.value;
}

/**
 * How much of the atlas shows (three's aoMapIntensity: 1 is the bake as it is, 0 none). The long-range pass of the bake darkens
 * a seat's flanks and the footwell like a dirty stain against the cream; at 0.6 the creases and seams stay and the leather
 * stays clean. window.__hallAo changes it live in development (it applies to materials made after, so reload).
 */
const HALL_AO = 0.6;

function hallLighting(m: THREE.MeshStandardMaterial, env: THREE.Texture | null) {
  if (m.userData.baked) return;
  m.userData.baked = true;
  m.aoMapIntensity = HALL_AO;
  if (env) {
    m.envMap = env;
    m.envMapIntensity = 1.0;
  }
  m.onBeforeCompile = (shader) => {
    shader.uniforms.uHallGain = HALL_GAIN;
    shader.uniforms.uCabinGain = CABIN_GAIN;
    shader.fragmentShader = shader.fragmentShader
      .replace('void main() {', 'uniform vec2 uHallGain;\nuniform float uCabinGain;\nvoid main() {')
      .replace(
        '#include <lights_fragment_maps>',
        `#include <lights_fragment_maps>
        iblIrradiance *= uHallGain.x * uCabinGain;
        irradiance *= 0.0;
        radiance *= uHallGain.y;
        #ifdef USE_CLEARCOAT
          clearcoatRadiance *= uHallGain.y;
        #endif`,
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
  m.customProgramCacheKey = () => 'cabin-hall-v1';
  m.needsUpdate = true;
}

function bakedLighting(
  m: THREE.MeshStandardMaterial,
  probe: THREE.Texture | null,
  open: { value: number } = { value: 0 },
) {
  if (m.userData.baked) return;
  m.userData.baked = true;
  if (probe) {
    m.envMap = probe;
    m.envMapIntensity = 1.0;
  }
  const gain = Math.PI / BAKE_STORE_SCALE;
  m.onBeforeCompile = (shader) => {
    shader.uniforms.uBakeGain = { value: gain };
    shader.uniforms.uCabinGain = CABIN_GAIN;
    shader.uniforms.uOpen = open;
    // open trim (dash top, seat backs, wheel) keeps its full reflection, a
    // footwell a small part of it (SPEC_OCC)
    shader.uniforms.uSpecOcc = SPEC_OCC;
    shader.vertexShader = shader.vertexShader
      .replace(
        'void main() {',
        'attribute vec3 bakedLight;\nattribute vec3 bakedLightOpen;\nvarying vec3 vBakedLight;\nvarying vec3 vBakedLightOpen;\nvoid main() {',
      )
      .replace(
        '#include <begin_vertex>',
        '#include <begin_vertex>\n\tvBakedLight = bakedLight;\n\tvBakedLightOpen = bakedLightOpen;',
      );
    shader.fragmentShader = shader.fragmentShader
      .replace(
        'void main() {',
        'uniform float uBakeGain;\nuniform float uCabinGain;\nuniform float uOpen;\nuniform vec2 uSpecOcc;\nuniform vec4 uHall;\nuniform float uHallSpec;\nvarying vec3 vBakedLight;\nvarying vec3 vBakedLightOpen;\nvoid main() {',
      )
      .replace(
        '#include <lights_fragment_maps>',
        `#include <lights_fragment_maps>
        {
          vec3 bakedE = mix( vBakedLight, vBakedLightOpen, uOpen ) * uBakeGain * uCabinGain;
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
  m.customProgramCacheKey = () => 'cabin-baked-v6';
  m.needsUpdate = true;
}

// --------------------------------------------------------------- live HMI

/**
 * What the picture's window draws: nothing at all, not even the page's white, so the HMI page behind the canvas shows. The
 * polygon offset pulls it in front of the dim backing quad it sits on.
 */
const HOLE = new THREE.MeshBasicMaterial({
  colorWrite: true,
  side: THREE.DoubleSide,
  blending: THREE.CustomBlending,
  blendEquation: THREE.AddEquation,
  blendSrc: THREE.ZeroFactor,
  blendDst: THREE.ZeroFactor,
  blendSrcAlpha: THREE.ZeroFactor,
  blendDstAlpha: THREE.ZeroFactor,
  polygonOffset: true,
  polygonOffsetFactor: -4,
  polygonOffsetUnits: -4,
  toneMapped: false,
});

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
    // top-left, top-right, bottom-right, bottom-left as the driver sees it. Each is pinned to the picture's parent,
    // so a screen that turns and slides (the RX's) carries the corners with it.
    const parent = (found as THREE.Mesh).parent ?? model;
    parent.updateWorldMatrix(true, false);
    const inverse = parent.matrixWorld.clone().invert();
    const corners = [at(-1, 1), at(1, 1), at(1, -1), at(-1, -1)].map((c) => {
      const o = new THREE.Object3D();
      o.position.copy(c).applyMatrix4(inverse);
      parent.add(o);
      return o;
    });
    return { corners, parent };
  }, [model]);

  // The HMI is a page over the canvas, so by itself it would be drawn over anything standing between the eye and the
  // screen (the steering wheel, a pillar). Instead the picture is a window: a mesh on the picture's plane that clears the
  // canvas to transparent, so the HMI behind it shows through, and after every frame the canvas inside the HMI's outline
  // is copied back over the page, which puts the wheel, the bezel and the like in front of the HMI where they belong.
  const hole = React.useRef<THREE.Mesh | null>(null);
  const poly = React.useRef<[number, number][] | null>(null);
  const events = useThree((s) => s.events);
  const gl = useThree((s) => s.gl);
  const invalidate = useThree((s) => s.invalidate);
  const inside = cameraMode !== 'exterior';
  React.useEffect(() => {
    if (!quad || !inside) return;
    const geo = new THREE.BufferGeometry();
    geo.setAttribute(
      'position',
      new THREE.Float32BufferAttribute(quad.corners.flatMap((o) => o.position.toArray()), 3),
    );
    geo.setIndex([0, 3, 2, 0, 2, 1]);
    const mesh = new THREE.Mesh(geo, HOLE);
    mesh.name = 'hmi_window';
    mesh.raycast = () => undefined;
    mesh.frustumCulled = false;
    quad.parent.add(mesh);
    hole.current = mesh;

    const host = (events.connected as HTMLElement | undefined) ?? gl.domElement.parentElement;
    const src = gl.domElement;
    const cv = document.createElement('canvas');
    cv.setAttribute('aria-hidden', 'true');
    cv.style.cssText = 'position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none;z-index:17';
    host?.appendChild(cv);
    const ctx = cv.getContext('2d');

    // the canvas is only readable in the task that drew it: note when the main view was drawn
    let drawn = false;
    const render = gl.render;
    gl.render = (scene, cam) => {
      render.call(gl, scene, cam);
      if (gl.getRenderTarget() === null) drawn = true;
    };
    let last: [number, number, number, number] | null = null;
    const stop = addAfterEffect(() => {
      if (!ctx || !drawn) return;
      drawn = false;
      if (cv.width !== src.width || cv.height !== src.height) {
        cv.width = src.width;
        cv.height = src.height;
        last = null;
      }
      if (last) ctx.clearRect(...last);
      last = null;
      const p = poly.current;
      if (!p) return;
      const k = src.width / Math.max(1, src.clientWidth);
      const xs = p.map((q) => q[0] * k);
      const ys = p.map((q) => q[1] * k);
      const x0 = Math.max(0, Math.floor(Math.min(...xs)) - 2);
      const y0 = Math.max(0, Math.floor(Math.min(...ys)) - 2);
      const x1 = Math.min(cv.width, Math.ceil(Math.max(...xs)) + 2);
      const y1 = Math.min(cv.height, Math.ceil(Math.max(...ys)) + 2);
      if (x1 <= x0 || y1 <= y0) return;
      ctx.save();
      ctx.beginPath();
      p.forEach((q, i) => (i ? ctx.lineTo(q[0] * k, q[1] * k) : ctx.moveTo(q[0] * k, q[1] * k)));
      ctx.closePath();
      ctx.clip();
      ctx.drawImage(src, x0, y0, x1 - x0, y1 - y0, x0, y0, x1 - x0, y1 - y0);
      ctx.restore();
      last = [x0, y0, x1 - x0, y1 - y0];
    });
    invalidate();
    return () => {
      stop();
      gl.render = render;
      cv.remove();
      quad.parent.remove(mesh);
      geo.dispose();
      hole.current = null;
      poly.current = null;
    };
  }, [quad, inside, events, gl, invalidate]);

  const tmp = React.useMemo(() => new THREE.Vector3(), []);
  const world = React.useMemo(() => new THREE.Vector3(), []);
  useFrame(() => {
    const el = surface.current;
    if (!el || !quad) return;
    camera.updateMatrixWorld();
    const pts: [number, number][] = [];
    for (const o of quad.corners) {
      const c = o.getWorldPosition(world);
      tmp.copy(c).applyMatrix4(camera.matrixWorldInverse);
      if (tmp.z > -0.02) {
        el.style.visibility = 'hidden'; // a corner is behind the eye
        poly.current = null;
        if (hole.current) hole.current.visible = false;
        return;
      }
      tmp.copy(c).project(camera);
      pts.push([(tmp.x + 1) * 0.5 * size.width, (1 - tmp.y) * 0.5 * size.height]);
    }
    // a pixel and a half wider than the glass: the window's anti-aliased edge never shows the page's white, and the
    // frame, copied back over the HMI, hides the overlap
    const cx = (pts[0][0] + pts[1][0] + pts[2][0] + pts[3][0]) / 4;
    const cy = (pts[0][1] + pts[1][1] + pts[2][1] + pts[3][1]) / 4;
    const grown = pts.map(([x, y]) => {
      const d = Math.hypot(x - cx, y - cy) || 1;
      return [x + ((x - cx) / d) * 1.5, y + ((y - cy) / d) * 1.5] as [number, number];
    });
    poly.current = grown;
    if (hole.current) hole.current.visible = true;
    el.style.visibility = 'visible';
    el.style.transform = quadToCss(grown, HMI_W, HMI_H);
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
