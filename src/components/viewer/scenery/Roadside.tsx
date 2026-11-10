'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { useDusk } from '../Lights';
import { makeCanvas, rng, smooth, withHaze } from './kit';
import { gantry, PROP_DOT, type PropKind } from './props';
import { Props, Trees, onStage, useHaze, type Spot } from './Scenery';
import { TILE, gantrySign, grassTexture } from './textures';

/**
 * What stands beside an open road: grass verges that fade into the studio's white, an expressway's crash barrier on one side and its
 * concrete median barrier on the other, delineator posts, kilometre posts, a gantry with its green sign, roadside trees in clumps
 * and shrubs. The road's own frame: x along it, z across (the viewer's), the road's middle on z = 0.
 */

// ------------------------------------------------------------------------------------------------ the verge

function vergeAlpha(endFrac: number, nearAtTop: boolean): THREE.CanvasTexture {
  const key = `verge-${endFrac.toFixed(3)}-${nearAtTop}`;
  const cache = (vergeAlpha as unknown as { c?: Map<string, THREE.CanvasTexture> }).c ?? ((vergeAlpha as unknown as { c: Map<string, THREE.CanvasTexture> }).c = new Map());
  const hit = cache.get(key);
  if (hit) return hit;
  const W = 128;
  const H = 64;
  const { canvas, ctx } = makeCanvas(W, H);
  const img = ctx.createImageData(W, H);
  for (let y = 0; y < H; y++) {
    // canvas y = 0 is v = 1
    const v = nearAtTop ? 1 - y / (H - 1) : y / (H - 1);
    // v = 1 is near the road: opaque; falls away over the outer 65 %
    const across = smooth(0, 0.65, v);
    for (let x = 0; x < W; x++) {
      const u = x / (W - 1);
      const along = smooth(0, endFrac, u) * smooth(0, endFrac, 1 - u);
      const a = Math.round(255 * across * along);
      const i = (y * W + x) * 4;
      img.data[i] = img.data[i + 1] = img.data[i + 2] = a;
      img.data[i + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(canvas);
  cache.set(key, t);
  return t;
}

/** A grass verge beside the road from z0 (at the road) to z1, over x0..x1, fading out at its far edge and its ends. */
export function Verge({ x0, x1, z0, z1, fadeEnd }: { x0: number; x1: number; z0: number; z1: number; fadeEnd: number }) {
  const L = x1 - x0;
  const W = Math.abs(z1 - z0);
  const nearTop = z0 > z1 ? false : true;
  const mat = React.useMemo(() => {
    const map = grassTexture().clone();
    map.repeat.set(L / TILE.grass, W / TILE.grass);
    map.needsUpdate = true;
    return withHaze(
      new THREE.MeshBasicMaterial({
        map,
        alphaMap: vergeAlpha(Math.min(0.5, fadeEnd / L), nearTop),
        transparent: true,
        depthWrite: false,
        toneMapped: false,
        polygonOffset: true,
        polygonOffsetFactor: -3,
        polygonOffsetUnits: -3,
      }),
      { height: false, distance: true },
    );
  }, [L, W, fadeEnd, nearTop]);
  React.useEffect(
    () => () => {
      mat.map?.dispose();
      mat.dispose();
    },
    [mat],
  );
  useDusk((d) => mat.color.copy(d.room).multiplyScalar(0.92));
  useHaze();
  return (
    <mesh position={[(x0 + x1) / 2, 0.001, (z0 + z1) / 2]} rotation-x={-Math.PI / 2} renderOrder={-0.55} ref={onStage} material={mat}>
      <planeGeometry args={[L, W]} />
    </mesh>
  );
}

// ------------------------------------------------------------------------------------------------ the gantry

export function Gantries({ spots, span }: { spots: Spot[]; span: number }) {
  const g = React.useMemo(() => gantry(span), [span]);
  const mats = React.useMemo(() => {
    const std = (o: THREE.MeshStandardMaterialParameters) => withHaze(new THREE.MeshStandardMaterial({ roughness: 0.7, metalness: 0.15, ...o }));
    const face = withHaze(new THREE.MeshBasicMaterial({ map: gantrySign(), toneMapped: false }), { height: false, distance: true });
    return { frame: std({ vertexColors: true }), board: std({ vertexColors: true, roughness: 0.8 }), face };
  }, []);
  React.useEffect(
    () => () => {
      Object.values(mats).forEach((m) => m.dispose());
    },
    [mats],
  );
  useDusk((d) => {
    mats.frame.color.copy(d.room);
    mats.board.color.copy(d.room);
    mats.face.color.copy(d.room);
  });
  const refs = [React.useRef<THREE.InstancedMesh>(null), React.useRef<THREE.InstancedMesh>(null), React.useRef<THREE.InstancedMesh>(null)];
  React.useLayoutEffect(() => {
    const o = new THREE.Object3D();
    spots.forEach((s, i) => {
      // turned to face back down the road: its own +z toward -x, its span across the road
      o.position.set(s.x, 0, s.z);
      o.rotation.set(0, -Math.PI / 2, 0);
      o.updateMatrix();
      for (const r of refs) r.current?.setMatrixAt(i, o.matrix);
    });
    for (const r of refs) {
      if (!r.current) continue;
      r.current.count = spots.length;
      r.current.instanceMatrix.needsUpdate = true;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [spots]);
  const n = Math.max(1, spots.length);
  return (
    <>
      <instancedMesh ref={refs[0]} args={[g.frame, mats.frame, n]} frustumCulled={false} onUpdate={onStage} />
      <instancedMesh ref={refs[1]} args={[g.board, mats.board, n]} frustumCulled={false} onUpdate={onStage} />
      <instancedMesh ref={refs[2]} args={[g.face, mats.face, n]} frustumCulled={false} onUpdate={onStage} />
    </>
  );
}

// ---------------------------------------------------------------------------------------------- the layout

type ExpressKinds = 'guardrail' | 'barrierPost' | 'delineator' | 'kmpost' | 'sign' | 'lamp' | 'camphor' | 'plane' | 'cypress' | 'ginkgo' | 'hedge' | 'shrub' | 'gantry';

/**
 * The roadside of an expressway over one repeat of `P` metres for `n` repeats each way (the road rolls by exactly one): the crash
 * barrier on the right, the median's concrete barrier with its planting on the left, trees in clumps on both banks. `edge` is the
 * half-width of the paving. Seeded, so every repeat is the same.
 */
export function expresswaySpots(edge: number, P: number, n: number, seed = 5): Record<ExpressKinds, Spot[]> {
  const out = {} as Record<ExpressKinds, Spot[]>;
  const push = (k: ExpressKinds, s: Spot) => (out[k] ??= []).push(s);
  const right = edge + 0.55;
  const left = -(edge + 0.55);
  for (let k = -n; k <= n; k++) {
    const base = k * P;
    const r = rng(seed);
    // the crash barrier, bay by bay, and the median barrier
    for (let x = 0; x < P; x += 4) {
      push('guardrail', { x: base + x, z: right, yaw: Math.PI });
      push('barrierPost', { x: base + x, z: left, yaw: 0 });
    }
    for (let x = 6; x < P; x += 20) push('delineator', { x: base + x, z: right - 0.55, yaw: Math.PI });
    push('kmpost', { x: base + P * 0.4, z: right + 1.1, yaw: Math.PI });
    push('sign', { x: base + P * 0.78, z: right + 1.6, yaw: -Math.PI / 2 });
    // the gantry's span: posts clear of the barriers on both sides
    push('gantry', { x: base + P * 0.52, z: 0 });
    // the median's planting: a shrub every 2.4 m behind its barrier, a few trees among them
    for (let x = 1.2; x < P; x += 2.4) push('hedge', { x: base + x, z: left - 1.4, yaw: 0, scale: 0.9 + r() * 0.3 });
    // banks: clumps of trees and shrubs back from the barriers
    const species: ExpressKinds[] = ['camphor', 'camphor', 'cypress', 'plane', 'camphor', 'cypress', 'ginkgo'];
    let i = 0;
    for (let x = 3 + r() * 4; x < P - 3; x += 7 + r() * 9) {
      const kind = species[i++ % species.length];
      push(kind, { x: base + x, z: right + 4.2 + r() * 6, scale: 0.9 + r() * 0.5 });
      if (r() > 0.4) push('shrub', { x: base + x + 2 + r() * 3, z: right + 2.4 + r() * 2, scale: 0.9 + r() * 0.5 });
    }
    i = 2;
    for (let x = 5 + r() * 4; x < P - 3; x += 8 + r() * 10) {
      const kind = species[i++ % species.length];
      push(kind, { x: base + x, z: left - 3.5 - r() * 7, scale: 0.9 + r() * 0.5 });
    }
  }
  return out;
}

const TREE_OF: Partial<Record<ExpressKinds, 'camphor' | 'plane' | 'cypress' | 'ginkgo' | 'hedge' | 'shrub'>> = {
  camphor: 'camphor',
  plane: 'plane',
  cypress: 'cypress',
  ginkgo: 'ginkgo',
  hedge: 'hedge',
  shrub: 'shrub',
};
const PROPS_OF: ExpressKinds[] = ['guardrail', 'barrierPost', 'delineator', 'kmpost', 'sign', 'lamp'];

/**
 * The roadside's meshes from its spots (see `expresswaySpots`). Mount it inside the rolled group. Each side of the road is its own
 * group and is hidden while the camera stands out beyond it: from there it would only be a wall of hedge and trees between the camera and
 * the car (the Drive tab's low side-on cameras), as a row of buildings is hidden when the camera is behind it.
 */
export function ExpresswayRoadside({ spots, span, edge }: { spots: Record<ExpressKinds, Spot[]>; span: number; edge: number }) {
  useHaze();
  const anchor = React.useRef<THREE.Group>(null);
  const rightG = React.useRef<THREE.Group>(null);
  const leftG = React.useRef<THREE.Group>(null);
  const sides = React.useMemo(() => {
    const split = (f: (s: Spot) => boolean) => {
      const out = {} as Record<ExpressKinds, Spot[]>;
      for (const k of Object.keys(spots) as ExpressKinds[]) out[k] = spots[k].filter(f);
      return out;
    };
    return { right: split((s) => s.z > 0.01), left: split((s) => s.z < -0.01) };
  }, [spots]);
  useFrame(({ camera }) => {
    const a = anchor.current;
    if (!a) return;
    a.getWorldPosition(tmpV);
    const rel = camera.position.z - tmpV.z;
    if (rightG.current) rightG.current.visible = rel < edge + 0.5;
    if (leftG.current) leftG.current.visible = rel > -(edge + 0.5);
  });
  const side = (sp: Record<ExpressKinds, Spot[]>) => (
    <>
      {(Object.keys(TREE_OF) as ExpressKinds[]).map((k) => {
        const s = sp[k];
        return s?.length ? <Trees key={k} kind={TREE_OF[k]!} spots={s} shadows={k !== 'hedge' && k !== 'shrub'} /> : null;
      })}
      {PROPS_OF.map((k) => {
        const s = sp[k];
        return s?.length ? <Props key={k} kind={k as PropKind} spots={s} dot={PROP_DOT[k as PropKind] ?? 0} /> : null;
      })}
    </>
  );
  return (
    <>
      <group ref={anchor} />
      <group ref={rightG}>{side(sides.right)}</group>
      <group ref={leftG}>{side(sides.left)}</group>
      {spots.gantry?.length && span > 0 ? <Gantries spots={spots.gantry} span={span} /> : null}
    </>
  );
}

const tmpV = new THREE.Vector3();
