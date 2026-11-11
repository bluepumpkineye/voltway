'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { useDusk } from '../Lights';
import { STAGE_LAYER, STUDIO_WHITE } from '../StudioShowroom';
import { buildRow, type RowSpec } from './buildings';
import { hazeUniforms, rng, setHaze, withHaze } from './kit';
import { propGeometry, signFaces, type PropKind } from './props';
import { barkTexture, brickTexture, canopyShadow, foliageMass, leafCluster, softDot, stuccoTexture, tileTexture, windowAtlas } from './textures';
import { treeParts, type TreeKind } from './trees';

/**
 * Draws the kit (src/components/viewer/scenery): instanced trees with their canopy shadows, building rows (one
 * row can be instanced along a rolling street), street furniture. Everything lives on the studio's stage layer, like the
 * floor paint: the studio's camera sees it, the mirror and the contact-shadow passes do not. Every material follows the
 * room's dusk, and the buildings' windows and signs come on as the room darkens.
 */
export function onStage(o: THREE.Object3D | null) {
  o?.layers.set(STAGE_LAYER);
}

const WHITE = new THREE.Color(STUDIO_WHITE);
const WARM_LIFT = new THREE.Color('#7a8c72');

/** Keeps the haze's colour the room's white at its dusk. Call once in any scenery that uses `withHaze`. */
export function useHaze(height?: [number, number], amount = 1) {
  React.useEffect(() => {
    if (height) hazeUniforms.uHazeY.value.set(height[0], height[1]);
    hazeUniforms.uHazeAmount.value = amount;
  }, [height, amount]);
  useDusk((d) => setHaze(d.room, WHITE));
}

export interface Spot {
  /** floor position (the viewer's x and z) and the height of what it stands on */
  x: number;
  z: number;
  y?: number;
  yaw?: number;
  scale?: number;
  /** a tint multiplied into the foliage (a hex), for a tree a little yellower or darker than its neighbour */
  tint?: string;
}

const tmpObj = new THREE.Object3D();
const tmpCol = new THREE.Color();

// -------------------------------------------------------------------------------------------------- trees

/**
 * Trees of one kind: the trunks and the canopies are two instanced meshes (a few hundred triangles a tree), and each
 * has its soft canopy shadow on the ground. Two variants of the same kind, so a row of them does not repeat.
 */
export function Trees({ kind, spots, variants = 2, shadows = true }: { kind: TreeKind; spots: Spot[]; variants?: number; shadows?: boolean }) {
  const sets = React.useMemo(() => {
    const out: Spot[][] = Array.from({ length: variants }, () => []);
    spots.forEach((s, i) => out[i % variants].push(s));
    return out;
  }, [spots, variants]);
  return (
    <>
      {sets.map((set, i) => (
        <TreeSet key={i} kind={kind} seed={i + 1} spots={set} shadows={shadows} />
      ))}
    </>
  );
}

function TreeSet({ kind, seed, spots, shadows }: { kind: TreeKind; seed: number; spots: Spot[]; shadows: boolean }) {
  const parts = React.useMemo(() => treeParts(kind, seed), [kind, seed]);
  const mats = React.useMemo(() => {
    const leaf = withHaze(
      new THREE.MeshStandardMaterial({
        map: leafCluster(parts.leaf),
        vertexColors: true,
        alphaTest: 0.42,
        alphaToCoverage: true,
        side: THREE.DoubleSide,
        roughness: 0.82,
        metalness: 0,
        envMapIntensity: 0.85,
      }),
    );
    const bark = withHaze(
      parts.solid
        ? new THREE.MeshStandardMaterial({ map: foliageMass(), vertexColors: true, roughness: 0.88, envMapIntensity: 0.85 })
        : new THREE.MeshStandardMaterial({ map: barkTexture(), vertexColors: true, roughness: 0.95, side: THREE.DoubleSide }),
    );
    const shade = new THREE.MeshBasicMaterial({ map: canopyShadow(), transparent: true, depthWrite: false, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -3, polygonOffsetUnits: -3 });
    return { leaf, bark, shade };
  }, [parts.leaf, parts.solid]);
  React.useEffect(
    () => () => {
      mats.leaf.dispose();
      mats.bark.dispose();
      mats.shade.dispose();
    },
    [mats],
  );
  useDusk((d) => {
    // the street's own lamps light the leaves from below at night: keep them from going black
    mats.leaf.color.copy(d.room).lerp(WARM_LIFT, 0.4 * d.night);
    mats.bark.color.copy(d.room);
    if (parts.solid) mats.bark.color.lerp(WARM_LIFT, 0.4 * d.night);
    mats.shade.opacity = 1 - 0.7 * d.night;
  });

  const canopy = React.useRef<THREE.InstancedMesh>(null);
  const trunk = React.useRef<THREE.InstancedMesh>(null);
  const shade = React.useRef<THREE.InstancedMesh>(null);
  React.useLayoutEffect(() => {
    const r = rng(spots.length * 31 + seed);
    spots.forEach((s, i) => {
      const sc = (s.scale ?? 1) * (0.9 + r() * 0.24);
      const yaw = s.yaw ?? r() * Math.PI * 2;
      tmpObj.position.set(s.x, s.y ?? 0, s.z);
      tmpObj.rotation.set(0, yaw, 0);
      tmpObj.scale.set(sc, sc * (0.92 + r() * 0.16), sc);
      tmpObj.updateMatrix();
      canopy.current?.setMatrixAt(i, tmpObj.matrix);
      trunk.current?.setMatrixAt(i, tmpObj.matrix);
      // the tint: a spread of greens (and, for the ginkgo, a spread of golds), per tree
      const k = 0.86 + r() * 0.26;
      tmpCol.set(s.tint ?? '#ffffff').multiplyScalar(k);
      if (!s.tint) tmpCol.offsetHSL((r() - 0.5) * 0.03, 0, 0);
      canopy.current?.setColorAt(i, tmpCol);
      // a hedge or a shrub's body takes the same tint as its fringe
      if (parts.solid) trunk.current?.setColorAt(i, tmpCol);
      if (shade.current) {
        const rad = parts.radius * sc * 2.45;
        // a tree's shadow falls a little to the side; a hedge's lies about its foot, long as the hedge is
        const sw = parts.shadow ? parts.shadow[0] * sc : rad;
        const sd = parts.shadow ? parts.shadow[1] * sc : rad;
        const off = parts.shadow ? 0 : 1;
        tmpObj.position.set(s.x + 0.35 * sc * off, (s.y ?? 0) + 0.012, s.z - 0.25 * sc * off);
        tmpObj.rotation.set(-Math.PI / 2, 0, yaw);
        tmpObj.scale.set(sw, sd, 1);
        tmpObj.updateMatrix();
        shade.current.setMatrixAt(i, tmpObj.matrix);
      }
    });
    for (const m of [canopy.current, trunk.current, shade.current]) {
      if (!m) continue;
      m.count = spots.length;
      m.instanceMatrix.needsUpdate = true;
      if (m.instanceColor) m.instanceColor.needsUpdate = true;
    }
  }, [spots, parts.radius, parts.solid, parts.shadow, seed]);

  const n = Math.max(1, spots.length);
  return (
    <>
      {shadows && (
        <instancedMesh ref={shade} args={[undefined, undefined, n]} frustumCulled={false} renderOrder={-0.3} onUpdate={onStage}>
          <planeGeometry args={[1, 1]} />
          <primitive object={mats.shade} attach="material" />
        </instancedMesh>
      )}
      {parts.trunk && <instancedMesh ref={trunk} args={[parts.trunk, mats.bark, n]} frustumCulled={false} onUpdate={onStage} />}
      <instancedMesh ref={canopy} args={[parts.canopy, mats.leaf, n]} frustumCulled={false} onUpdate={onStage} />
    </>
  );
}

// ------------------------------------------------------------------------------------------------- buildings

/** The materials of a row: the walls take the room's dusk, the windows and signs light up as it falls. */
export function useRowMaterials() {
  const mats = React.useMemo(() => {
    const std = (map: THREE.Texture | null, rough: number, env = 0.7) =>
      withHaze(new THREE.MeshStandardMaterial({ map: map ?? undefined, vertexColors: true, roughness: rough, metalness: 0, envMapIntensity: env }));
    const lit = new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false });
    const signLit = new THREE.MeshBasicMaterial({ map: windowAtlas(), vertexColors: true, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false });
    return {
      stucco: std(stuccoTexture(), 0.92),
      tile: std(tileTexture(), 0.6, 0.9),
      brick: std(brickTexture(), 0.95),
      trim: std(null, 0.85),
      atlas: std(windowAtlas(), 0.28, 1.15),
      lit,
      signLit,
    };
  }, []);
  React.useEffect(
    () => () => {
      Object.values(mats).forEach((m) => m.dispose());
    },
    [mats],
  );
  useDusk((d) => {
    mats.stucco.color.copy(d.room);
    mats.tile.color.copy(d.room);
    mats.brick.color.copy(d.room);
    mats.trim.color.copy(d.room);
    mats.atlas.color.copy(d.room);
    mats.lit.opacity = Math.min(1, d.night * 1.15) * 0.9;
    mats.signLit.opacity = Math.min(1, d.night * 1.25) * 0.85;
  });
  return mats;
}

/**
 * A building row (src/components/viewer/scenery/buildings.ts) standing on a street: placed at (x, z), turned to face `yaw`, and
 * copied along x at the given offsets (a rolling street instances one period of buildings along its strip; a still street
 * has one copy at 0). Hidden when the camera is on the far side of its facade, as the old painted wall was: seen from
 * behind it would only stand between the camera and the car.
 */
export function BuildingRow({
  spec,
  x,
  y = 0,
  z,
  faces,
  copies = [0],
  hideBehind = true,
  mirror = false,
}: {
  spec: RowSpec;
  x: number;
  y?: number;
  z: number;
  /** which way the facade looks along z: +1 toward +z, -1 toward -z (in the parent's frame) */
  faces: 1 | -1;
  copies?: number[];
  hideBehind?: boolean;
  /** the world z of the facade for the camera test, if the parent is itself moved in z */
  mirror?: boolean;
}) {
  const row = React.useMemo(() => buildRow(spec), [spec]);
  const mats = useRowMaterials();
  const group = React.useRef<THREE.Group>(null);
  const n = copies.length;
  const refs = {
    stucco: React.useRef<THREE.InstancedMesh>(null),
    tile: React.useRef<THREE.InstancedMesh>(null),
    brick: React.useRef<THREE.InstancedMesh>(null),
    trim: React.useRef<THREE.InstancedMesh>(null),
    atlas: React.useRef<THREE.InstancedMesh>(null),
    lit: React.useRef<THREE.InstancedMesh>(null),
    signLit: React.useRef<THREE.InstancedMesh>(null),
  };
  React.useLayoutEffect(() => {
    const m = new THREE.Matrix4();
    for (const ref of Object.values(refs)) {
      const mesh = ref.current;
      if (!mesh) continue;
      copies.forEach((cx, i) => mesh.setMatrixAt(i, m.makeTranslation(cx, 0, 0)));
      mesh.count = n;
      mesh.instanceMatrix.needsUpdate = true;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [copies, n, row]);
  const worldZ = React.useRef(0);
  useFrame(({ camera }) => {
    const g = group.current;
    if (!g || !hideBehind) return;
    g.getWorldPosition(tmpV);
    worldZ.current = tmpV.z;
    g.visible = faces * (camera.position.z - tmpV.z) > -0.5;
  });
  void mirror;
  const item = (key: keyof typeof refs, geo: THREE.BufferGeometry, mat: THREE.Material, order = 0) => (
    <instancedMesh key={key} ref={refs[key]} args={[geo, mat, n]} frustumCulled={false} renderOrder={order} onUpdate={onStage} />
  );
  return (
    // the row's own frame faces +z; turned about y for the other side
    <group ref={group} position={[x, y, z]} rotation-y={faces === 1 ? 0 : Math.PI}>
      {item('stucco', row.stucco, mats.stucco)}
      {item('tile', row.tile, mats.tile)}
      {item('brick', row.brick, mats.brick)}
      {item('trim', row.trim, mats.trim)}
      {item('atlas', row.atlas, mats.atlas)}
      {item('lit', row.lit, mats.lit, 2)}
      {item('signLit', row.signLit, mats.signLit, 2)}
    </group>
  );
}
const tmpV = new THREE.Vector3();

// ----------------------------------------------------------------------------------------------- furniture

export interface PropSpot extends Spot {
  /** the kind of prop a spot is */
  kind: PropKind;
}

/** One prop kind, instanced, each with a small soft contact shadow of its footprint (radius `dot`, m, 0 for none). */
export function Props({ kind, spots, dot = 0, light = false }: { kind: PropKind; spots: Spot[]; dot?: number; light?: boolean }) {
  const geo = React.useMemo(() => propGeometry(kind), [kind]);
  const mat = React.useMemo(() => withHaze(new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.78, metalness: 0.08, envMapIntensity: 0.9, side: THREE.DoubleSide })), []);
  const shade = React.useMemo(() => new THREE.MeshBasicMaterial({ map: softDot(), transparent: true, depthWrite: false, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -3, polygonOffsetUnits: -3 }), []);
  React.useEffect(
    () => () => {
      mat.dispose();
      shade.dispose();
    },
    [mat, shade],
  );
  useDusk((d) => {
    mat.color.copy(d.room);
    shade.opacity = 1 - 0.6 * d.night;
  });
  const mesh = React.useRef<THREE.InstancedMesh>(null);
  const dots = React.useRef<THREE.InstancedMesh>(null);
  const lit = React.useRef<THREE.InstancedMesh>(null);
  // a sign's face lights at night: the same faces, additive, over the dimmed ones
  const faces = kind === 'sign' || kind === 'streetsign' ? kind : null;
  const faceGeo = React.useMemo(() => (faces ? signFaces(faces) : null), [faces]);
  const faceMat = React.useMemo(
    () => new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }),
    [],
  );
  React.useEffect(() => () => faceMat.dispose(), [faceMat]);
  useDusk((d) => {
    faceMat.opacity = Math.min(1, d.night * 1.6) * 0.85;
  });
  React.useLayoutEffect(() => {
    spots.forEach((s, i) => {
      tmpObj.position.set(s.x, s.y ?? 0, s.z);
      tmpObj.rotation.set(0, s.yaw ?? 0, 0);
      const sc = s.scale ?? 1;
      tmpObj.scale.set(sc, sc, sc);
      tmpObj.updateMatrix();
      mesh.current?.setMatrixAt(i, tmpObj.matrix);
      lit.current?.setMatrixAt(i, tmpObj.matrix);
      if (dots.current) {
        tmpObj.position.set(s.x, (s.y ?? 0) + 0.01, s.z);
        tmpObj.rotation.set(-Math.PI / 2, 0, 0);
        tmpObj.scale.set(dot * 2 * sc, dot * 2 * sc, 1);
        tmpObj.updateMatrix();
        dots.current.setMatrixAt(i, tmpObj.matrix);
      }
    });
    for (const m of [mesh.current, dots.current, lit.current]) {
      if (!m) continue;
      m.count = spots.length;
      m.instanceMatrix.needsUpdate = true;
    }
  }, [spots, dot]);
  const n = Math.max(1, spots.length);
  void light;
  return (
    <>
      {kind === 'lamp' && <LampGlow spots={spots} />}
      {dot > 0 && (
        <instancedMesh ref={dots} args={[undefined, undefined, n]} frustumCulled={false} renderOrder={-0.3} onUpdate={onStage}>
          <planeGeometry args={[1, 1]} />
          <primitive object={shade} attach="material" />
        </instancedMesh>
      )}
      <instancedMesh ref={mesh} args={[geo, mat, n]} frustumCulled={false} onUpdate={onStage} />
      {faceGeo && <instancedMesh ref={lit} args={[faceGeo, faceMat, n]} frustumCulled={false} renderOrder={2} onUpdate={onStage} />}
    </>
  );
}

// ------------------------------------------------------------------------------------------------ lamp glow

let poolTexture: THREE.CanvasTexture | null = null;
/** A warm pool of light on the ground: a radial fall-off, white at the middle, drawn additively. */
function lightPool(): THREE.CanvasTexture {
  if (poolTexture) return poolTexture;
  const S = 128;
  const c = document.createElement('canvas');
  c.width = c.height = S;
  const ctx = c.getContext('2d')!;
  const g = ctx.createRadialGradient(S / 2, S / 2, 2, S / 2, S / 2, S / 2);
  g.addColorStop(0, 'rgba(255,222,160,0.95)');
  g.addColorStop(0.35, 'rgba(255,205,140,0.45)');
  g.addColorStop(0.7, 'rgba(255,190,120,0.14)');
  g.addColorStop(1, 'rgba(255,190,120,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, S, S);
  poolTexture = new THREE.CanvasTexture(c);
  poolTexture.colorSpace = THREE.SRGBColorSpace;
  return poolTexture;
}

/**
 * What a street lamp does at night: its lens lights up and it throws a warm pool of light on the ground under its arm. Both are
 * drawn additively and ramp in with the room's dusk; by day they are invisible (opacity 0), and the scene keeps no lights of its own.
 * The lantern's lens is at x = 1.5 along the arm (src/components/viewer/scenery/props.ts), 6 m up.
 */
function LampGlow({ spots }: { spots: Spot[] }) {
  const pools = React.useRef<THREE.InstancedMesh>(null);
  const lenses = React.useRef<THREE.InstancedMesh>(null);
  const mats = React.useMemo(
    () => ({
      pool: new THREE.MeshBasicMaterial({ map: lightPool(), transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -6, polygonOffsetUnits: -6 }),
      lens: new THREE.MeshBasicMaterial({ color: '#fff0c8', transparent: true, opacity: 0, toneMapped: false }),
    }),
    [],
  );
  const lensGeo = React.useMemo(() => new THREE.BoxGeometry(0.8, 0.05, 0.26).translate(1.5, 6.0, 0), []);
  // the lantern seen from the side is a thin slit: a halo that always faces the camera makes it a lamp
  const halos = React.useMemo(
    () =>
      spots.map((s) => {
        const yaw = s.yaw ?? 0;
        const sc = s.scale ?? 1;
        return { x: s.x + Math.cos(yaw) * 1.5 * sc, y: (s.y ?? 0) + 5.98 * sc, z: s.z - Math.sin(yaw) * 1.5 * sc, size: 3.4 * sc };
      }),
    [spots],
  );
  React.useEffect(
    () => () => {
      mats.pool.dispose();
      mats.lens.dispose();
      lensGeo.dispose();
    },
    [mats, lensGeo],
  );
  useDusk((d) => {
    mats.pool.opacity = Math.min(1, d.night * 1.2) * 0.75;
    mats.lens.opacity = Math.min(1, d.night * 3);
    mats.pool.visible = mats.pool.opacity > 0.01;
  });
  React.useLayoutEffect(() => {
    spots.forEach((s, i) => {
      const yaw = s.yaw ?? 0;
      const sc = s.scale ?? 1;
      // the pool lies under the lantern: 1.5 m along the arm, which a turn of `yaw` about y sends to (cos, -sin)
      tmpObj.position.set(s.x + Math.cos(yaw) * 1.5 * sc, (s.y ?? 0) + 0.014, s.z - Math.sin(yaw) * 1.5 * sc);
      tmpObj.rotation.set(-Math.PI / 2, 0, 0);
      tmpObj.scale.set(9 * sc, 9 * sc, 1);
      tmpObj.updateMatrix();
      pools.current?.setMatrixAt(i, tmpObj.matrix);
      tmpObj.position.set(s.x, s.y ?? 0, s.z);
      tmpObj.rotation.set(0, yaw, 0);
      tmpObj.scale.set(sc, sc, sc);
      tmpObj.updateMatrix();
      lenses.current?.setMatrixAt(i, tmpObj.matrix);
    });
    for (const m of [pools.current, lenses.current]) {
      if (!m) continue;
      m.count = spots.length;
      m.instanceMatrix.needsUpdate = true;
    }
  }, [spots]);
  const n = Math.max(1, spots.length);
  return (
    <>
      <instancedMesh ref={pools} args={[undefined, undefined, n]} frustumCulled={false} renderOrder={1} onUpdate={onStage}>
        <planeGeometry args={[1, 1]} />
        <primitive object={mats.pool} attach="material" />
      </instancedMesh>
      <instancedMesh ref={lenses} args={[lensGeo, mats.lens, n]} frustumCulled={false} renderOrder={2} onUpdate={onStage} />
      <Halos spots={halos} />
    </>
  );
}

// ----------------------------------------------------------------------------------------------- halos

let haloTexture: THREE.CanvasTexture | null = null;
/** A soft glow: white-hot at the middle, warm round it, nothing at the rim. */
function lampHalo(): THREE.CanvasTexture {
  if (haloTexture) return haloTexture;
  const S = 128;
  const c = document.createElement('canvas');
  c.width = c.height = S;
  const ctx = c.getContext('2d')!;
  const g = ctx.createRadialGradient(S / 2, S / 2, 0, S / 2, S / 2, S / 2);
  g.addColorStop(0, 'rgba(255,248,226,1)');
  g.addColorStop(0.1, 'rgba(255,238,190,0.85)');
  g.addColorStop(0.28, 'rgba(255,214,150,0.32)');
  g.addColorStop(0.55, 'rgba(255,196,120,0.09)');
  g.addColorStop(1, 'rgba(255,190,120,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, S, S);
  haloTexture = new THREE.CanvasTexture(c);
  haloTexture.colorSpace = THREE.SRGBColorSpace;
  return haloTexture;
}

/** A material for quads that always face the camera: the instance matrix gives a quad's middle and its size (a glow round a lamp). */
function billboardMaterial(map: THREE.Texture, color: string): THREE.MeshBasicMaterial {
  const m = new THREE.MeshBasicMaterial({ map, color, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false });
  m.onBeforeCompile = (shader) => {
    shader.vertexShader = shader.vertexShader.replace(
      '#include <project_vertex>',
      `vec4 mvPosition = modelViewMatrix * instanceMatrix * vec4(0.0, 0.0, 0.0, 1.0);
       float bbSize = length(instanceMatrix[0].xyz);
       mvPosition.xy += position.xy * bbSize;
       gl_Position = projectionMatrix * mvPosition;`,
    );
  };
  m.customProgramCacheKey = () => 'billboard-halo';
  return m;
}

/**
 * Glows at points, drawn additively and always facing the camera, that ramp in with the room's dusk (invisible by day): the street
 * lamps' lanterns and the fixtures that light a gantry's sign. `size` is the glow's diameter in metres.
 */
export function Halos({ spots, tint = '#fff0c8', gain = 1 }: { spots: { x: number; y: number; z: number; size: number }[]; tint?: string; gain?: number }) {
  const mat = React.useMemo(() => billboardMaterial(lampHalo(), tint), [tint]);
  const mesh = React.useRef<THREE.InstancedMesh>(null);
  React.useEffect(() => () => mat.dispose(), [mat]);
  useDusk((d) => {
    mat.opacity = Math.min(1, d.night * 2) * gain;
    if (mesh.current) mesh.current.visible = mat.opacity > 0.01;
  });
  React.useLayoutEffect(() => {
    const m = mesh.current;
    if (!m) return;
    spots.forEach((s, i) => {
      tmpObj.position.set(s.x, s.y, s.z);
      tmpObj.rotation.set(0, 0, 0);
      tmpObj.scale.set(s.size, s.size, 1);
      tmpObj.updateMatrix();
      m.setMatrixAt(i, tmpObj.matrix);
    });
    m.count = spots.length;
    m.instanceMatrix.needsUpdate = true;
  }, [spots]);
  return (
    <instancedMesh ref={mesh} args={[undefined, undefined, Math.max(1, spots.length)]} frustumCulled={false} renderOrder={3} onUpdate={onStage}>
      <planeGeometry args={[1, 1]} />
      <primitive object={mat} attach="material" />
    </instancedMesh>
  );
}

