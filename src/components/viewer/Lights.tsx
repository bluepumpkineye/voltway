'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import type { Vehicle } from '@/data/vehicles/schema';
import {
  frontEmissive,
  isLampMaterial,
  lampTargets,
  lightsOf,
  lightsRig,
  rearEmissive,
  type LampLook,
  type ResolvedLights,
} from '@/lib/lights';
import { useVehicleStore } from '@/store/vehicle-store';
import { motionOk } from './configurator';

/**
 * The car's lamps in the viewer (docs/lights.md).
 *
 * src/lib/lights.ts holds what the lamps are doing, as levels that ramp toward the visitor's switches.
 * This file draws it, with no post-processing: the renderer stays as the rest of the showroom has it
 * (Neutral tone mapping, the glass blending in the framebuffer), and the light is geometry added to
 * that pass.
 *
 *  - The LED parts of the car drive their emissive strength (the lamp material, found by name).
 *  - A glow: camera-facing quads, added on top, at points thinned out of the lamp's own triangles. They
 *    ride on the lamp's mesh, so a tailgate that swings takes its lamps' glow with it.
 *  - The beam on the floor ahead of the car, and the red wash behind it, as additive patches.
 *  - The room dims to dusk (`useDusk`), so the light has something to shine against.
 *
 * Everything here lives on LIGHT_LAYER, which the view camera sees and ContactShadows' depth pass and the
 * floor mirror do not: a camera-facing quad has no business in either.
 */

export const LIGHT_LAYER = 2;

/** Tunable from the console in development (window.__lights): call __viewer.invalidate() to redraw. */
const U = {
  /** half-size of a glow quad at full level, m */
  size: { value: 0.04 },
  /** how far the quad is pulled toward the camera, so a lens in front of the LED does not hide it, m */
  bias: { value: 0.02 },
  /** the glow's wide halo and its tight bloom, display values per quad */
  peakW: { value: 0.12 },
  peakT: { value: 0.5 },
  /** the beam and the tail wash on the floor */
  beam: { value: 0.62 },
  wash: { value: 0.9 },
  /** how far the room goes toward dusk (1 = as dark as it is set to go) and how far the reflections dim */
  dusk: { value: 1 },
  envDim: { value: 0.58 },
};
if (typeof window !== 'undefined' && process.env.NODE_ENV !== 'production') {
  (window as unknown as { __lights?: unknown }).__lights = { rig: lightsRig, ...U };
}

// ---------------------------------------------------------------------------- the driver

/**
 * Follows the store's lamp switches and steps the lamps' levels. Mount once inside the Canvas; it asks
 * for frames only while a level is still moving, so a demand canvas stays idle.
 */
export function LightsDriver() {
  const invalidate = useThree((s) => s.invalidate);
  const camera = useThree((s) => s.camera);

  React.useEffect(() => {
    camera.layers.enable(LIGHT_LAYER);
  }, [camera]);

  React.useEffect(() => {
    const follow = (s: { lightMode: Parameters<typeof lampTargets>[0]; highBeam: boolean; braking: boolean }, snap: boolean) => {
      lightsRig.aim(lampTargets(s.lightMode, s.highBeam, s.braking), snap);
      invalidate();
    };
    // a page that opens with the lamps already on shows them on; a switch afterwards ramps
    follow(useVehicleStore.getState(), true);
    return useVehicleStore.subscribe((s, prev) => {
      if (s.lightMode !== prev.lightMode || s.highBeam !== prev.highBeam || s.braking !== prev.braking) {
        follow(s, !motionOk());
      }
    });
  }, [invalidate]);

  // before everything that reads the levels (the lowest priority number runs first)
  useFrame((_, dt) => {
    if (lightsRig.step(dt)) invalidate();
  }, -20);
  return null;
}

// ---------------------------------------------------------------------------- dusk

export interface Dusk {
  /** how far the lamps have taken the room toward dusk, 0..1 */
  night: number;
  /** what a bright, unlit surface of the room is multiplied by (linear, as a colour's own values are) */
  room: THREE.Color;
  /** what the image-based light, and the sun, are multiplied by */
  env: number;
  sun: number;
}

/** How bright a white room still looks, as it is seen (display values), at full dusk: a dim blue-grey. */
const DUSK = { r: 0.1, g: 0.13, b: 0.2 };
const dusk: Dusk = { night: 0, room: new THREE.Color(1, 1, 1), env: 1, sun: 1 };

export function duskOf(night: number): Dusk {
  const k = night * U.dusk.value;
  // the dimming is worked out as it looks, then taken back to the linear values a colour holds
  const linear = (c: number) => Math.pow(Math.max(0, 1 - k * (1 - c)), 2.2);
  dusk.night = night;
  dusk.room.setRGB(linear(DUSK.r), linear(DUSK.g), linear(DUSK.b));
  dusk.env = 1 - U.envDim.value * night;
  dusk.sun = 1 - 0.9 * night;
  return dusk;
}

/**
 * Calls `apply` every frame with the room's dusk. Per frame, not on a change, so that a surface that
 * remounts (the floor swaps its mirror in once the white light is made) is dimmed with the rest; the
 * work is a few multiplications.
 */
export function useDusk(apply: (d: Dusk) => void) {
  useFrame(() => apply(duskOf(lightsRig.now.night)));
}

// ---------------------------------------------------------------------------- finding the lamps

function materialsOf(o: THREE.Mesh): THREE.Material[] {
  return Array.isArray(o.material) ? o.material : [o.material];
}

/** One mesh of the car that carries a lamp, and the points its glow sits at. */
interface LampPart {
  mesh: THREE.Mesh;
  /** the glow points in the mesh's own space, xyz */
  local: Float32Array;
  /** the same in the model's space, which is where the beam on the floor is worked out */
  car: Float32Array;
}

interface LampSet {
  look: LampLook;
  /** the lamp's materials, with the emissive light the build gave them: a lamp that is off is the build */
  mats: { m: THREE.MeshStandardMaterial; built: number; color: THREE.Color }[];
  parts: LampPart[];
}

const CELL = 0.012;
const MAX_POINTS = 1500;

/**
 * Thin a lamp mesh down to evenly spaced points on its surface: its vertices, plus points along its
 * edges (a long straight strip is two vertices), merged into cells `cell` metres across. A glow at
 * every vertex would be dense where the lamp is modelled finely and gappy where it is not.
 */
function thin(mesh: THREE.Mesh, toModel: THREE.Matrix4, cell: number): LampPart | null {
  const geo = mesh.geometry as THREE.BufferGeometry;
  const pos = geo.getAttribute('position');
  if (!pos) return null;
  const index = geo.index;
  const tris = index ? index.count / 3 : Math.floor(pos.count / 3);
  const cells = new Map<number, number[]>();

  const pl = [new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()];
  const pc = [new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()];
  const sl = new THREE.Vector3();
  const sc = new THREE.Vector3();
  const add = () => {
    const key =
      ((Math.floor(sc.x / cell) + 1024) * 2048 + (Math.floor(sc.y / cell) + 1024)) * 2048 +
      (Math.floor(sc.z / cell) + 1024);
    let e = cells.get(key);
    if (!e) cells.set(key, (e = [0, 0, 0, 0, 0, 0, 0]));
    e[0] += sl.x;
    e[1] += sl.y;
    e[2] += sl.z;
    e[3] += sc.x;
    e[4] += sc.y;
    e[5] += sc.z;
    e[6]++;
  };

  for (let t = 0; t < tris; t++) {
    for (let k = 0; k < 3; k++) {
      const i = index ? index.getX(t * 3 + k) : t * 3 + k;
      pl[k].set(pos.getX(i), pos.getY(i), pos.getZ(i));
      pc[k].copy(pl[k]).applyMatrix4(toModel);
    }
    for (let k = 0; k < 3; k++) {
      const a = k;
      const b = (k + 1) % 3;
      const n = Math.max(1, Math.ceil(pc[a].distanceTo(pc[b]) / (cell * 0.7)));
      for (let j = 0; j < n; j++) {
        sl.lerpVectors(pl[a], pl[b], j / n);
        sc.lerpVectors(pc[a], pc[b], j / n);
        add();
      }
    }
    sl.copy(pl[0]).add(pl[1]).add(pl[2]).multiplyScalar(1 / 3);
    sc.copy(pc[0]).add(pc[1]).add(pc[2]).multiplyScalar(1 / 3);
    add();
  }
  if (!cells.size) return null;

  const local = new Float32Array(cells.size * 3);
  const car = new Float32Array(cells.size * 3);
  let i = 0;
  for (const e of cells.values()) {
    const n = e[6];
    local[i * 3] = e[0] / n;
    local[i * 3 + 1] = e[1] / n;
    local[i * 3 + 2] = e[2] / n;
    car[i * 3] = e[3] / n;
    car[i * 3 + 1] = e[4] / n;
    car[i * 3 + 2] = e[5] / n;
    i++;
  }
  return { mesh, local, car };
}

/** The meshes of `model` that wear the lamp's material, thinned, and the materials themselves. */
function findLamp(model: THREE.Object3D, look: LampLook): LampSet | null {
  model.updateMatrixWorld(true);
  const inverse = new THREE.Matrix4().copy(model.matrixWorld).invert();
  const mats = new Map<THREE.Material, number>();
  const parts: LampPart[] = [];
  model.traverse((o) => {
    if (!(o instanceof THREE.Mesh)) return;
    const own = materialsOf(o).filter(
      (m): m is THREE.MeshStandardMaterial => m instanceof THREE.MeshStandardMaterial && isLampMaterial(look, m.name),
    );
    if (!own.length) return;
    for (const m of own) if (!mats.has(m)) mats.set(m, m.emissiveIntensity * (m.emissive.getHex() > 0 ? 1 : 0));
    const toModel = new THREE.Matrix4().multiplyMatrices(inverse, o.matrixWorld);
    for (let cell = CELL; cell < 0.2; cell *= 1.5) {
      const part = thin(o, toModel, cell);
      if (!part) break;
      if (part.local.length / 3 <= MAX_POINTS) {
        parts.push(part);
        break;
      }
    }
  });
  if (!mats.size) return null;
  return {
    look,
    mats: [...mats].map(([m, built]) => ({ m: m as THREE.MeshStandardMaterial, built, color: (m as THREE.MeshStandardMaterial).emissive.clone() })),
    parts,
  };
}

// ---------------------------------------------------------------------------- the glow

const GLOW_VERT = /* glsl */ `
  attribute vec3 aPos;
  uniform float uSize;
  uniform float uBias;
  varying vec2 vUv;
  void main() {
    vUv = position.xy;
    vec4 mv = modelViewMatrix * vec4(aPos, 1.0);
    mv.z += uBias;
    mv.xy += position.xy * uSize;
    gl_Position = projectionMatrix * mv;
  }
`;

// Display values, added in the framebuffer as the glass is: a halo that falls off wide and a bloom
// that falls off tight, both fading to nothing at the quad's edge.
const GLOW_FRAG = /* glsl */ `
  uniform vec3 uHalo;
  uniform vec3 uCore;
  uniform float uSize;
  uniform float uLevel;
  uniform float uSigmaW;
  uniform float uSigmaT;
  uniform float uPeakW;
  uniform float uPeakT;
  varying vec2 vUv;
  void main() {
    float u = length(vUv);
    float r = u * uSize;
    float w = exp(-(r * r) / (uSigmaW * uSigmaW));
    float t = exp(-(r * r) / (uSigmaT * uSigmaT));
    float edge = 1.0 - smoothstep(0.65, 1.0, u);
    vec3 c = (uHalo * (w * uPeakW) + uCore * (t * uPeakT)) * (edge * uLevel);
    gl_FragColor = vec4(c, 1.0);
  }
`;

type Kind = 'front' | 'projector' | 'rear';

/** How much of the default glow each kind of lamp has: the projector lenses are small points. */
const GLOW_GAIN: Record<Kind, number> = { front: 1, projector: 0.8, rear: 0.9 };
/** How far the hot centre of the glow goes toward white: a red lamp stays red, a white one clips to white. */
const GLOW_WHITE: Record<Kind, number> = { front: 0.55, projector: 0.55, rear: 0.1 };
/** How strong the glow is, against the default. */
const GLOW_STRENGTH: Record<Kind, number> = { front: 1, projector: 1, rear: 0.75 };

interface Glow {
  kind: Kind;
  set: LampSet;
  material: THREE.ShaderMaterial;
  meshes: THREE.Mesh[];
}

/** An sRGB colour as the display numbers it is made of (the glow is blended in the framebuffer). */
const display = (hex: string) => new THREE.Color(hex).convertLinearToSRGB();

const noRaycast = () => {};

function makeGlow(kind: Kind, set: LampSet): Glow {
  const halo = display(set.look.halo);
  const core = halo.clone().lerp(new THREE.Color(1, 1, 1), GLOW_WHITE[kind]);
  const material = new THREE.ShaderMaterial({
    vertexShader: GLOW_VERT,
    fragmentShader: GLOW_FRAG,
    uniforms: {
      uHalo: { value: halo },
      uCore: { value: core },
      uSize: { value: U.size.value },
      uSigmaW: { value: U.size.value / 1.9 },
      uSigmaT: { value: U.size.value * 0.4 },
      uPeakW: U.peakW,
      uPeakT: U.peakT,
      uBias: U.bias,
      uLevel: { value: 0 },
    },
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const meshes = set.parts.map((part) => {
    const geo = new THREE.InstancedBufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array([-1, -1, 0, 1, -1, 0, 1, 1, 0, -1, 1, 0]), 3));
    geo.setIndex([0, 1, 2, 0, 2, 3]);
    geo.setAttribute('aPos', new THREE.InstancedBufferAttribute(part.local, 3));
    geo.instanceCount = part.local.length / 3;
    // the real extent, not the unit quad's: a bounding-box walk of the model must not find a 2 m square
    const box = new THREE.Box3();
    const v = new THREE.Vector3();
    for (let i = 0; i < part.local.length; i += 3) box.expandByPoint(v.set(part.local[i], part.local[i + 1], part.local[i + 2]));
    box.expandByScalar(0.2);
    geo.boundingBox = box;
    geo.boundingSphere = box.getBoundingSphere(new THREE.Sphere());
    const mesh = new THREE.Mesh(geo, material);
    mesh.layers.set(LIGHT_LAYER);
    mesh.renderOrder = 30;
    mesh.raycast = noRaycast;
    mesh.visible = false;
    return mesh;
  });
  return { kind, set, material, meshes };
}

function driveGlow(g: Glow, level: number) {
  const size = U.size.value * GLOW_GAIN[g.kind] * (0.8 + 0.2 * Math.min(level, 1));
  const u = g.material.uniforms;
  u.uSize.value = size;
  u.uSigmaW.value = size / 1.9;
  u.uSigmaT.value = size * 0.4;
  u.uLevel.value = level * GLOW_STRENGTH[g.kind];
  const show = level > 0.004;
  for (const m of g.meshes) m.visible = show;
}

// ---------------------------------------------------------------------------- the floor

const POOL_VERT = /* glsl */ `
  varying vec2 vP;
  void main() {
    vP = position.xz;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

// The headlamps' beam on the floor ahead of the nose: two lobes, one per lamp, toed out a little, as
// long as the beam reaches and as wide as the beam spreads (narrower for the high beam).
const BEAM_FRAG = /* glsl */ `
  uniform float uLevel;
  uniform float uReach;
  uniform float uNose;
  uniform float uLat;
  uniform float uK;
  uniform vec3 uColor;
  varying vec2 vP;
  float lobe(float d, float s, float spread, float reach) {
    float w = 0.46 + d * spread;
    float lat = exp(-(s * s) / (w * w) * 1.7);
    float along = smoothstep(0.0, 0.7, d) * exp(-d / (0.5 * reach)) * (1.0 - smoothstep(0.55 * reach, reach, d));
    return along * lat;
  }
  void main() {
    float reach = max(uReach, 0.5);
    float d = vP.x - uNose;
    float spread = mix(0.36, 0.19, clamp((uReach - 7.0) / 5.0, 0.0, 1.0));
    float toe = d * 0.04;
    float i = lobe(d, vP.y - (uLat + toe), spread, reach) + lobe(d, vP.y + (uLat + toe), spread, reach);
    gl_FragColor = vec4(uColor * (uLevel * uK * i), 1.0);
  }
`;

// The tail lamps' red on the floor behind the car: a soft wash that falls off quickly.
const WASH_FRAG = /* glsl */ `
  uniform float uLevel;
  uniform float uTail;
  uniform float uHalf;
  uniform float uK;
  uniform vec3 uColor;
  varying vec2 vP;
  void main() {
    float d = uTail - vP.x;
    float w = uHalf + d * 0.22;
    float lat = exp(-(vP.y * vP.y) / (w * w) * 1.1);
    float along = smoothstep(-0.02, 0.3, d) * exp(-d / 0.85) * (1.0 - smoothstep(1.8, 3.2, d));
    gl_FragColor = vec4(uColor * (uLevel * uK * lat * along), 1.0);
  }
`;

interface Pool {
  mesh: THREE.Mesh;
  material: THREE.ShaderMaterial;
}

const FLOOR_Y = 0.006;

/** A flat patch of floor in the model's space, from x0 to x1 and z0 to z1, lit by `frag`. */
function makePool(frag: string, uniforms: Record<string, THREE.IUniform>, x0: number, x1: number, z0: number, z1: number): Pool {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute(
    'position',
    new THREE.BufferAttribute(new Float32Array([x0, FLOOR_Y, z0, x1, FLOOR_Y, z0, x1, FLOOR_Y, z1, x0, FLOOR_Y, z1]), 3),
  );
  geo.setIndex([0, 2, 1, 0, 3, 2]);
  const material = new THREE.ShaderMaterial({
    vertexShader: POOL_VERT,
    fragmentShader: frag,
    uniforms,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
    toneMapped: false,
    // over the floor's own decals (the baked shadow, the lot's paint), at any distance the camera has
    polygonOffset: true,
    polygonOffsetFactor: -8,
    polygonOffsetUnits: -8,
  });
  const mesh = new THREE.Mesh(geo, material);
  mesh.layers.set(LIGHT_LAYER);
  mesh.renderOrder = 25;
  mesh.raycast = noRaycast;
  mesh.visible = false;
  return { mesh, material };
}

// ---------------------------------------------------------------------------- the car

interface Built {
  look: ResolvedLights;
  front: LampSet | null;
  projector: LampSet | null;
  rear: LampSet | null;
}

function buildLamps(model: THREE.Object3D, look: ResolvedLights): Built {
  const t0 = performance.now();
  const built = {
    look,
    front: findLamp(model, look.front),
    projector: look.projector ? findLamp(model, look.projector) : null,
    rear: findLamp(model, look.rear),
  };
  if (process.env.NODE_ENV !== 'production') {
    const n = (s: LampSet | null) => s?.parts.reduce((a, p) => a + p.local.length / 3, 0) ?? 0;
    console.debug(
      `[lights] glow points front ${n(built.front)}, projector ${n(built.projector)}, rear ${n(built.rear)} in ${(performance.now() - t0).toFixed(0)} ms`,
    );
  }
  return built;
}

/** Where a lamp set sits: the end of the car it is at and its half-width, from the points of its glow. */
function extent(set: LampSet) {
  let xMin = Infinity;
  let xMax = -Infinity;
  let z = 0;
  for (const p of set.parts) {
    for (let i = 0; i < p.car.length; i += 3) {
      xMin = Math.min(xMin, p.car[i]);
      xMax = Math.max(xMax, p.car[i]);
      z = Math.max(z, Math.abs(p.car[i + 2]));
    }
  }
  return { xMin, xMax, half: z };
}

interface Live {
  glows: Glow[];
  beam?: Pool;
  wash?: Pool;
  root: THREE.Group;
}

/**
 * Lights the car it is mounted in: the lamp materials, the glow quads on the lamp meshes, and the patches
 * of floor ahead of and behind the car. Rendered inside the car's group, so a car that drives (the Tech
 * tab) takes its light with it.
 */
export function CarLights({ model, vehicle }: { model: THREE.Object3D; vehicle: Vehicle }) {
  const invalidate = useThree((s) => s.invalidate);
  const built = React.useMemo(() => buildLamps(model, lightsOf(vehicle.lights)), [model, vehicle.lights]);
  const root = React.useMemo(() => new THREE.Group(), []);
  const live = React.useRef<Live | null>(null);
  const seen = React.useRef(-1);

  const apply = React.useCallback(() => {
    const l = live.current;
    if (!l) return;
    const n = lightsRig.now;
    const { front, projector, rear } = built;
    // The front LED's off state is the showroom's own (a faint white, never tone-mapped). The other lamps,
    // off, are the build exactly: its emissive colour and strength, tone-mapped like the rest of the car.
    if (front) {
      for (const { m } of front.mats) {
        m.emissive.set(front.look.color);
        m.emissiveIntensity = frontEmissive(front.look, n.front);
      }
    }
    if (projector) {
      const lit = n.projector > 0.001;
      for (const { m, color } of projector.mats) {
        if (lit) m.emissive.set(projector.look.color);
        else m.emissive.copy(color);
        m.emissiveIntensity = lit ? frontEmissive(projector.look, n.projector) : 0;
        if (m.toneMapped === lit) {
          m.toneMapped = !lit;
          m.needsUpdate = true;
        }
      }
    }
    if (rear) {
      const lit = n.rear > 0.001;
      for (const { m, built: b, color } of rear.mats) {
        if (lit) m.emissive.set(rear.look.color);
        else m.emissive.copy(color);
        m.emissiveIntensity = rearEmissive(rear.look, b, n.rear);
        if (m.toneMapped === lit) {
          m.toneMapped = !lit;
          m.needsUpdate = true;
        }
      }
    }
    for (const g of l.glows) driveGlow(g, g.kind === 'front' ? n.front : g.kind === 'projector' ? n.projector : n.rear);
    if (l.beam) {
      l.beam.mesh.visible = n.beam > 0.004;
      l.beam.material.uniforms.uLevel.value = n.beam;
      l.beam.material.uniforms.uReach.value = n.reach;
    }
    if (l.wash) {
      l.wash.mesh.visible = n.rear > 0.004;
      l.wash.material.uniforms.uLevel.value = n.rear;
    }
  }, [built]);

  React.useEffect(() => {
    const glows: Glow[] = [];
    for (const [kind, set] of [['front', built.front], ['projector', built.projector], ['rear', built.rear]] as const) {
      if (!set) continue;
      // the front LEDs are never tone-mapped: they are lit light, not a lit surface (the projector lenses and
      // the tail lamp are, until they are lit: see apply)
      if (kind === 'front') for (const { m } of set.mats) m.toneMapped = false;
      if (!set.parts.length) continue;
      const glow = makeGlow(kind, set);
      glow.meshes.forEach((mesh, i) => set.parts[i].mesh.add(mesh));
      glows.push(glow);
    }

    const l: Live = { glows, root };
    if (built.front?.parts.length) {
      const e = extent(built.front);
      l.beam = makePool(
        BEAM_FRAG,
        {
          uLevel: { value: 0 },
          uReach: { value: 0 },
          uNose: { value: e.xMax },
          uLat: { value: Math.max(0.5, e.half * 0.62) },
          uK: U.beam,
          uColor: { value: display('#cfe0ff') },
        },
        e.xMax - 0.3,
        e.xMax + 13.5,
        -4.8,
        4.8,
      );
      root.add(l.beam.mesh);
    }
    if (built.rear?.parts.length) {
      const e = extent(built.rear);
      l.wash = makePool(
        WASH_FRAG,
        {
          uLevel: { value: 0 },
          uTail: { value: e.xMin },
          uHalf: { value: Math.max(0.4, e.half * 0.8) },
          uK: U.wash,
          uColor: { value: display(built.look.rear.halo) },
        },
        e.xMin - 3.6,
        e.xMin + 0.3,
        -3,
        3,
      );
      root.add(l.wash.mesh);
    }
    live.current = l;
    seen.current = -1;
    apply();
    invalidate();

    return () => {
      live.current = null;
      for (const g of glows) {
        g.meshes.forEach((mesh) => {
          mesh.removeFromParent();
          mesh.geometry.dispose();
        });
        g.material.dispose();
      }
      for (const p of [l.beam, l.wash]) {
        if (!p) continue;
        p.mesh.removeFromParent();
        p.mesh.geometry.dispose();
        p.material.dispose();
      }
    };
  }, [built, root, apply, invalidate]);

  useFrame(() => {
    // the glow's size is part of what is drawn: a change made from the console in development counts too
    const stamp = lightsRig.version * 1000 + U.size.value;
    if (seen.current === stamp) return;
    seen.current = stamp;
    apply();
  });

  return <primitive object={root} />;
}
