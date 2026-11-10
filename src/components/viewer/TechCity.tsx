'use client';

import React from 'react';
import * as THREE from 'three';
import type { Vehicle } from '@/data/vehicles/schema';
import type { CityRoad, RoadStage } from '@/lib/tech/carpet';
import { rigOf } from '@/lib/tech/rig';
import { useDusk } from './Lights';
import { Signal } from './TechSignal';
import { FootwayStrip, asphaltMaterial, fadeEdges, paintWearStrip } from './scenery/Ground';
import { rng } from './scenery/kit';
import { PROP_DOT, type PropKind } from './scenery/props';
import { BuildingRow, Props, Trees, onStage, useHaze, type Spot } from './scenery/Scenery';
import { ASPHALT, PAINT, YELLOW, paintStripTexture, paintTyreTracks, treePit } from './scenery/textures';

/**
 * The street of Autonomous Drive's city scenes (src/lib/tech/scenes/city.ts): asphalt with the tyres' tracks worn into it, a worn
 * line along the parking strip, dashes between the car's lane and the one beside it and a double yellow line down the middle;
 * kerbs, paved footways with a tactile strip on both sides; a row of real buildings behind each footway; street trees, lamps,
 * hedges, benches, bins, shared bikes, a bus shelter; and a zebra crossing with its stop lines.
 *
 * Like the expressway (TechRoad's `Highway`) it is drawn so that a still car can drive down it however long the run is: the
 * asphalt, kerbs and footways stand under the car; what repeats (the dashes, the buildings, the trees and furniture, the patches
 * and manholes worn into the road) is laid out over one strip and rolled by the rig as far as its period and no further; the
 * crossing and the stop lines roll with the road. The buildings and trees repeat every three of the scene's periods (72 m), so the
 * same shop front does not come round every 24 m. Road coordinates are the planner's (x along, y left); the viewer's z is -y.
 */

const HIGHWAY_FADE_END = 70;
/** how many of the scene's periods the buildings, trees and furniture take before they repeat */
const PERIODS = 3;
const SPECIES = ['tree', 'tree', 'plane', 'tree', 'ginkgo', 'tree'] as const;

export function CityStreet({ road, city, vehicle }: { road: RoadStage; city: CityRoad; vehicle: Vehicle }) {
  const rig = rigOf(vehicle);
  const repeating = React.useRef<THREE.Group>(null);
  const rolling = React.useRef<THREE.Group>(null);
  const PM = city.period * PERIODS;
  React.useEffect(() => {
    const a = repeating.current;
    const b = rolling.current;
    if (!a || !b) return;
    const offA = rig.attachRoad(a, rig.rac.x, PM);
    const offB = rig.attachRoad(b, rig.rac.x);
    return () => {
      offA();
      offB();
    };
  }, [rig, PM, road]);

  const length = road.to - road.from;
  const yc = (city.nearKerb + city.farKerb) / 2;
  const width = city.farKerb - city.nearKerb;
  useHaze([9, 46], 1);

  // ---- the asphalt: the tyres' tracks and the gutters, painted once for the whole strip (stretched along it: they run its length)
  const baseMap = React.useMemo(() => {
    const cw = 1024;
    const ppm = 40;
    const ch = Math.round(width * ppm);
    const canvas = document.createElement('canvas');
    canvas.width = cw;
    canvas.height = ch;
    const ctx = canvas.getContext('2d', { willReadFrequently: true })!;
    const py = (y: number) => (city.farKerb - y) * ppm;
    ctx.fillStyle = ASPHALT;
    ctx.fillRect(0, 0, cw, ch);
    const cuts = [city.nearKerb, ...city.lines.map((l) => l.y).sort((a, b) => a - b), city.farKerb];
    for (let i = 0; i < cuts.length - 1; i++) {
      const w = cuts[i + 1] - cuts[i];
      if (w > 2.9) paintTyreTracks(ctx, 0, cw, py(cuts[i] + w / 2), w * ppm, ppm, 11 + i);
    }
    for (const [y, dir] of [[city.nearKerb, 1], [city.farKerb, -1]] as const) {
      const g = ctx.createLinearGradient(0, py(y), 0, py(y) - dir * 0.9 * ppm);
      g.addColorStop(0, 'rgba(10,11,13,0.30)');
      g.addColorStop(1, 'rgba(10,11,13,0)');
      ctx.fillStyle = g;
      ctx.fillRect(0, dir > 0 ? py(y) - 0.9 * ppm : py(y), cw, 0.9 * ppm);
      ctx.fillStyle = 'rgba(122,125,131,0.34)';
      ctx.fillRect(0, dir > 0 ? py(y) - 0.32 * ppm : py(y), cw, 0.32 * ppm);
    }
    fadeEdges(ctx, cw, ch, ppm, HIGHWAY_FADE_END, 0, length);
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 8;
    return tex;
  }, [city, width, length]);
  const baseMat = React.useMemo(() => asphaltMaterial(baseMap, length, width), [baseMap, length, width]);
  React.useEffect(
    () => () => {
      baseMap.dispose();
      baseMat.dispose();
    },
    [baseMap, baseMat],
  );

  // ---- what is worn into the road, one repeat of it, laid end to end along the strip (rolled)
  const wearMap = React.useMemo(() => {
    const ppm = 20;
    const canvas = document.createElement('canvas');
    canvas.width = Math.round(PM * ppm);
    canvas.height = Math.round(width * ppm);
    const ctx = canvas.getContext('2d')!;
    paintWearStrip(ctx, PM, width, ppm, 17);
    const t = new THREE.CanvasTexture(canvas);
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 8;
    return t;
  }, [PM, width]);
  const wearMat = React.useMemo(
    () => new THREE.MeshBasicMaterial({ map: wearMap, transparent: true, depthWrite: false, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -5, polygonOffsetUnits: -5 }),
    [wearMap],
  );
  React.useEffect(
    () => () => {
      wearMap.dispose();
      wearMat.dispose();
    },
    [wearMap, wearMat],
  );
  useDusk((d) => {
    baseMat.color.copy(d.room);
    wearMat.color.copy(d.room);
  });

  const copies = React.useMemo(() => {
    const n = Math.ceil(length / 2 / PM);
    return Array.from({ length: 2 * n + 1 }, (_, i) => (i - n) * PM);
  }, [length, PM]);
  const wearMesh = React.useRef<THREE.InstancedMesh>(null);
  React.useLayoutEffect(() => {
    const m = wearMesh.current;
    if (!m) return;
    const t = new THREE.Matrix4();
    copies.forEach((cx, i) => m.setMatrixAt(i, t.makeTranslation(cx, 0, 0)));
    m.count = copies.length;
    m.instanceMatrix.needsUpdate = true;
  }, [copies]);

  // ---- the paint: worn strips (one repeat of a dash, a solid line, a bar)
  const paints = React.useMemo(() => {
    const white = paintStripTexture(PAINT, 2, 0.14, 5, 0.5);
    const yellow = paintStripTexture(YELLOW, 2, 0.1, 6, 0.4);
    const solidWhite = white.clone();
    solidWhite.repeat.set((length * 0.8) / 2, 1);
    const solidYellow = yellow.clone();
    solidYellow.repeat.set((length * 0.8) / 2, 1);
    const bar = paintStripTexture(PAINT, city.crossings[0]?.length ?? 4, 0.5, 8, 0.6);
    const stop = paintStripTexture(PAINT, 6, 0.38, 9, 0.5);
    return { white, yellow, solidWhite, solidYellow, bar, stop };
  }, [length, city.crossings]);
  const markMat = React.useMemo(() => {
    const m = (map: THREE.Texture, order: number) =>
      new THREE.MeshBasicMaterial({ map, transparent: true, depthWrite: false, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -6 - order, polygonOffsetUnits: -6 - order });
    return {
      white: m(paints.white, 0),
      yellow: m(paints.yellow, 0),
      solidWhite: m(paints.solidWhite, 0),
      solidYellow: m(paints.solidYellow, 0),
      bar: m(paints.bar, 1),
      stop: m(paints.stop, 1),
    };
  }, [paints]);
  React.useEffect(
    () => () => {
      Object.values(markMat).forEach((m) => m.dispose());
      paints.solidWhite.dispose();
      paints.solidYellow.dispose();
    },
    [markMat, paints],
  );
  useDusk((d) => {
    for (const m of Object.values(markMat)) m.color.copy(d.room);
  });

  const dashPeriod = 6;
  const dashSlots = React.useMemo(() => {
    const out: number[] = [];
    // the strip rolls by PM, which the dash period divides
    for (let x = -Math.ceil(length / 2 / PM) * PM - PM; x <= length / 2 + PM; x += dashPeriod) out.push(x);
    return out;
  }, [length, PM]);
  const dashes = React.useMemo(() => city.lines.filter((l) => l.dash), [city.lines]);
  const solids = React.useMemo(() => city.lines.filter((l) => !l.dash), [city.lines]);
  const dashMesh = React.useRef<THREE.InstancedMesh>(null);
  React.useLayoutEffect(() => {
    const d = dashMesh.current;
    if (!d) return;
    const m = new THREE.Matrix4();
    let i = 0;
    for (const l of dashes) for (const x of dashSlots) d.setMatrixAt(i++, m.makeTranslation(x + 1, -l.y, 0));
    d.count = i;
    d.instanceMatrix.needsUpdate = true;
  }, [dashes, dashSlots]);

  // ---- trees, lamps and the furniture, laid out over the repeat
  const spots = React.useMemo(() => citySpots(city, PM, Math.ceil(length / 2 / PM)), [city, PM, length]);

  // ---- the zebra bars (along the street, side by side across it)
  const bars = React.useMemo(() => {
    const out: { x: number; y: number }[] = [];
    for (const c of city.crossings) for (let y = city.nearKerb + 0.55; y < city.farKerb - 0.4; y += 1.0) out.push({ x: c.x, y });
    return out;
  }, [city]);
  const barMesh = React.useRef<THREE.InstancedMesh>(null);
  React.useLayoutEffect(() => {
    const b = barMesh.current;
    if (!b) return;
    const m = new THREE.Matrix4();
    bars.forEach((bar, i) => b.setMatrixAt(i, m.makeTranslation(bar.x, -bar.y, 0)));
    b.count = bars.length;
    b.instanceMatrix.needsUpdate = true;
  }, [bars]);

  const x0 = rig.rac.x - length / 2;
  const x1 = rig.rac.x + length / 2;
  const nearBuildings = React.useMemo(() => ({ length: PM, seed: 3, maxHeight: 28, minHeight: 14 }), [PM]);
  const farBuildings = React.useMemo(() => ({ length: PM, seed: 8, maxHeight: 32, minHeight: 14 }), [PM]);
  const foot = city.footway + 0.2;
  return (
    // the street's middle line is the car's own centre line at the start
    <group position-z={-rig.rac.y}>
      <mesh position={[rig.rac.x, 0.002, -yc]} rotation-x={-Math.PI / 2} renderOrder={-0.5} ref={onStage} material={baseMat}>
        <planeGeometry args={[length, width]} />
      </mesh>
      {/* the solid lines: the strip's edge and the double yellow */}
      {solids.map((l, i) => (
        <mesh key={i} position={[rig.rac.x, 0.003, -l.y]} rotation-x={-Math.PI / 2} renderOrder={-0.4} ref={onStage} material={l.color === 'yellow' ? markMat.solidYellow : markMat.solidWhite}>
          <planeGeometry args={[length * 0.8, l.color === 'yellow' ? 0.1 : 0.14]} />
        </mesh>
      ))}
      <FootwayStrip x0={x0} x1={x1} kerbY={city.nearKerb} foot={foot} side="south" fade={HIGHWAY_FADE_END} />
      <FootwayStrip x0={x0} x1={x1} kerbY={city.farKerb} foot={foot} side="north" fade={HIGHWAY_FADE_END} />
      {/* what repeats: rolled by its period */}
      <group ref={repeating}>
        <instancedMesh ref={wearMesh} args={[undefined, undefined, copies.length]} position={[PM / 2, 0.0025, -yc]} rotation-x={-Math.PI / 2} renderOrder={-0.45} frustumCulled={false} onUpdate={onStage} material={wearMat}>
          <planeGeometry args={[PM, width]} />
        </instancedMesh>
        <instancedMesh ref={dashMesh} args={[undefined, undefined, Math.max(1, dashes.length * dashSlots.length)]} rotation-x={-Math.PI / 2} position-y={0.003} renderOrder={-0.4} frustumCulled={false} onUpdate={onStage} material={markMat.white}>
          <planeGeometry args={[2, 0.14]} />
        </instancedMesh>
        <CityScenery spots={spots} copies={copies} nearBuildings={nearBuildings} farBuildings={farBuildings} PM={PM} nearZ={-(city.nearKerb - foot - 0.1)} farZ={-(city.farKerb + foot + 0.1)} />
      </group>
      {/* what rolls with the road: the crossing and its stop lines */}
      <group ref={rolling}>
        <instancedMesh ref={barMesh} args={[undefined, undefined, Math.max(1, bars.length)]} rotation-x={-Math.PI / 2} position-y={0.0035} renderOrder={-0.35} frustumCulled={false} onUpdate={onStage} material={markMat.bar}>
          <planeGeometry args={[city.crossings[0]?.length ?? 4, 0.5]} />
        </instancedMesh>
        {city.stopLines.map((l, i) => (
          <mesh key={i} position={[l.x, 0.0036, -(l.y0 + l.y1) / 2]} rotation={[-Math.PI / 2, 0, Math.PI / 2]} renderOrder={-0.34} ref={onStage} material={markMat.stop}>
            <planeGeometry args={[l.y1 - l.y0, 0.38]} />
          </mesh>
        ))}
        {(city.signals ?? []).map((sg, i) => (
          <Signal key={i} signal={sg} />
        ))}
      </group>
    </group>
  );
}

// ---------------------------------------------------------------------------------------------- the scenery

type Kinds = 'tree' | 'plane' | 'ginkgo' | 'hedge' | PropKind;

/**
 * The street's trees, lamps and furniture over one repeat of `PM` metres on both footways, for `n` repeats each way. Seeded: the
 * same layout every time, and the same in every repeat (the strip rolls by exactly one).
 */
function citySpots(city: CityRoad, PM: number, n: number): Record<Kinds, Spot[]> {
  const out = {} as Record<Kinds, Spot[]>;
  const push = (k: Kinds, s: Spot) => (out[k] ??= []).push(s);
  const foot = city.footway + 0.2;
  const KERB = 0.15;
  for (let k = -n; k <= n; k++) {
    const base = k * PM;
    const r = rng(77);
    for (const side of [-1, 1] as const) {
      // distance d from the kerb onto the footway; floor y; the viewer's z is -y
      const kerbY = side < 0 ? city.nearKerb : city.farKerb;
      const at = (x: number, d: number, kind: Kinds, yaw = 0, scale = 1) => push(kind, { x: base + x, y: KERB, z: -(kerbY + side * d), yaw, scale });
      const toward = side < 0 ? 1 : -1;
      const lampYaw = (Math.PI / 2) * toward;
      const faceRoad = side < 0 ? Math.PI : 0;
      const off = side < 0 ? 0 : 12;
      // lamps every 24 m, trees every 12 m between them
      for (let i = 0; i < 3; i++) at(6 + off + 24 * i, 0.5, 'lamp', lampYaw);
      // the near side (the camera's) has a tree every 24 m so that they do not stand in front of the car; the far side every 12
      for (let i = 0; i < 6; i++) if (side > 0 || i % 2 === 0) at(((side < 0 ? 3 : 9) + 12 * i) % PM, 1.55, SPECIES[(i + (side < 0 ? 0 : 3) + k + n) % SPECIES.length], 0, (side < 0 ? 0.85 : 0.95) + r() * 0.2);
      // hedges along the building line, in breaks
      for (let x = 1.5; x < PM - 3; x += 7 + r() * 6) if (r() > 0.3) at(x, foot - 0.55, 'hedge');
      // benches, bins, bikes, a planter, a hydrant, signs and a shelter
      at(side < 0 ? 14 : 38, 2.25, 'bench', faceRoad);
      at(side < 0 ? 50 : 62, 2.25, 'bench', faceRoad);
      for (const x of side < 0 ? [10, 34, 58] : [22, 46, 70]) at(x % PM, 0.95, 'bin', faceRoad);
      at(side < 0 ? 27 : 53, 1.2, 'bikes', Math.PI / 2);
      if (side > 0) at(33, 1.0, 'planter');
      at(side < 0 ? 41 : 17, 0.35, 'hydrant');
      at(side < 0 ? 64 : 5, 0.4, side < 0 ? 'sign' : 'streetsign', lampYaw);
      if (side > 0) at(PM * 0.64, 1.5, 'shelter', 0);
    }
  }
  return out;
}

type RowSpecLite = { length: number; seed: number; maxHeight: number; minHeight: number };

function CityScenery({ spots, copies, nearBuildings, farBuildings, PM, nearZ, farZ }: { spots: Record<Kinds, Spot[]>; copies: number[]; nearBuildings: RowSpecLite; farBuildings: RowSpecLite; PM: number; nearZ: number; farZ: number }) {
  const trees = React.useMemo(() => [...(spots.tree ?? []), ...(spots.plane ?? []), ...(spots.ginkgo ?? [])], [spots]);
  // the buildings: one repeat of each side, copied along the strip; the near row looks toward -z from y = near footway's outer edge
  return (
    <>
      <BuildingRow spec={nearBuildings} x={PM / 2} y={0.15} z={nearZ} faces={-1} copies={copies} />
      <BuildingRow spec={farBuildings} x={-PM / 2} y={0.15} z={farZ} faces={1} copies={copies} />
      {(['tree', 'plane', 'ginkgo', 'hedge'] as const).map((k) => {
        const s = spots[k];
        if (!s?.length) return null;
        return <Trees key={k} kind={k === 'tree' ? 'camphor' : k} spots={s} shadows={k !== 'hedge'} />;
      })}
      <Pits spots={trees} />
      {(['lamp', 'bench', 'bin', 'bikes', 'planter', 'hydrant', 'shelter', 'sign', 'streetsign'] as const).map((k) => {
        const s = spots[k];
        if (!s?.length) return null;
        return <Props key={k} kind={k} spots={s} dot={PROP_DOT[k] ?? 0} />;
      })}
    </>
  );
}

function Pits({ spots }: { spots: Spot[] }) {
  const mesh = React.useRef<THREE.InstancedMesh>(null);
  const map = React.useMemo(() => treePit(), []);
  const mat = React.useMemo(() => new THREE.MeshBasicMaterial({ map, transparent: true, depthWrite: false, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 }), [map]);
  React.useEffect(() => () => mat.dispose(), [mat]);
  useDusk((d) => mat.color.copy(d.room));
  React.useLayoutEffect(() => {
    const o = new THREE.Object3D();
    spots.forEach((s, i) => {
      o.position.set(s.x, (s.y ?? 0) + 0.008, s.z);
      o.rotation.set(-Math.PI / 2, 0, 0);
      o.scale.set(1.3, 1.3, 1);
      o.updateMatrix();
      mesh.current?.setMatrixAt(i, o.matrix);
    });
    if (mesh.current) {
      mesh.current.count = spots.length;
      mesh.current.instanceMatrix.needsUpdate = true;
    }
  }, [spots]);
  if (!spots.length) return null;
  return (
    <instancedMesh ref={mesh} args={[undefined, undefined, spots.length]} frustumCulled={false} renderOrder={-0.37} onUpdate={onStage}>
      <planeGeometry args={[1, 1]} />
      <primitive object={mat} attach="material" />
    </instancedMesh>
  );
}
