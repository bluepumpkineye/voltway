'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import type { Vehicle } from '@/data/vehicles/schema';
import type { RoadStage } from '@/lib/tech/carpet';
import { rigOf } from '@/lib/tech/rig';
import { weather } from '@/lib/tech/weather';
import { useDusk } from './Lights';
import { asphaltMaterial, fadeEdges, paintWearStrip } from './scenery/Ground';
import { withBend } from './scenery/kit';
import { ExpresswayRoadside, Verge, expresswaySpots } from './scenery/Roadside';
import { onStage, useHaze } from './scenery/Scenery';
import { WetRoad } from './scenery/WetRoad';
import { ASPHALT, PAINT, TILE, edgeLineTexture, paintStripTexture, paintTyreTracks } from './scenery/textures';

/**
 * The expressway of Autonomous Drive: worn asphalt with the tyres' tracks in each of its lanes, worn white edge lines and lane
 * dashes, tar joints; a crash barrier along the right and a concrete median barrier with planting along the left, delineator
 * posts, a kilometre post, a speed sign, an overhead gantry with its green sign, clumps of roadside trees, and grass verges that fade
 * into the studio's white.
 *
 * The asphalt with its two edge lines and the grass verges stands still under the car (a long plane tilts with a hill; it does not
 * roll). What streams past (the dashes, the joints, the barriers, the trees, the gantry and the patches worn into the road) is laid
 * out over a short repeat and rolled by the rig as far as its period and no further, so a strip of a few hundred metres is endless
 * whatever the run's length. The surface of what stands still moves too: the worn edge lines, the grass and the asphalt's grain
 * slide their textures by the rig's scroll, or the car would drive over a road that looks glued to the ground. Road coordinates: x
 * along, z across (the viewer's), the road's middle on z = 0.
 */

/** the dashed lane line (Chinese expressways: 6 m of paint and 9 m of gap), the edge line, and the spacing of the tar joints, m */
const DASH = { length: 6, period: 15, width: 0.15 };
const EDGE_WIDTH = 0.2;
/** one repeat of the worn edge line's paint, m (long enough that its marks do not read as a pattern) */
const EDGE_PERIOD = 24;
const JOINT_PERIOD = 12.5;
/** the roadside (barriers, trees, gantry, worn marks) repeats every this many metres: eight dash periods */
const SIDE_PERIOD = 120;
/** the fade at the strip's far ends (it is long enough that they are out of sight) */
const HIGHWAY_FADE_END = 70;
/** how wide the grass verges are, m */
const VERGE = 15;

/** how many pieces a long plane is cut into along the road, one every 4 m (the Drive tab's curve bends the road at its vertices) */
const alongOf = (len: number) => Math.min(400, Math.max(1, Math.ceil(len / 4)));

export function Highway({ road, lanes, vehicle, wet = false, gantry = true }: { road: RoadStage; lanes: NonNullable<RoadStage['lanes']>; vehicle: Vehicle; wet?: boolean; gantry?: boolean }) {
  const rig = rigOf(vehicle);
  const dashes = React.useRef<THREE.Group>(null);
  const joints = React.useRef<THREE.Group>(null);
  const side = React.useRef<THREE.Group>(null);
  const still = React.useRef<THREE.Group>(null);
  // the wet sheet stays while the rain clears (the weather eases out over a second or so), then goes
  const [wetShown, setWetShown] = React.useState(wet);
  React.useEffect(() => {
    if (wet) {
      setWetShown(true);
      return;
    }
    const t = setTimeout(() => setWetShown(false), 2200);
    return () => clearTimeout(t);
  }, [wet]);
  React.useEffect(() => {
    const a = dashes.current;
    const b = joints.current;
    const c = side.current;
    const d = still.current;
    if (!a || !b || !c || !d) return;
    // what stands still under the car (the asphalt, the verges, the edge lines, the wet sheet) tilts with a hill: it is staged, not rolled
    const offs = [
      rig.attachRoad(a, rig.rac.x, DASH.period),
      rig.attachRoad(b, rig.rac.x, JOINT_PERIOD),
      rig.attachRoad(c, rig.rac.x, SIDE_PERIOD),
      rig.attachStage(d, 0),
    ];
    return () => offs.forEach((o) => o());
  }, [rig, road]);

  const length = road.to - road.from;
  const half = (lanes.count * lanes.width) / 2;
  const edge = road.width / 2;
  useHaze([9, 46], 1);
  // how far the road has rolled under the car, for the textures of what stands still
  const scroll = React.useCallback(() => rig.state.scroll, [rig]);
  const grain = React.useMemo(() => new THREE.Vector2(), []);

  // ---- the asphalt, painted once for the whole strip (stretched along it: tracks and shoulders run its length)
  const baseMap = React.useMemo(() => {
    const cw = 1024;
    const ppm = 40;
    const ch = Math.round(road.width * ppm);
    const canvas = document.createElement('canvas');
    canvas.width = cw;
    canvas.height = ch;
    const ctx = canvas.getContext('2d', { willReadFrequently: true })!;
    const pz = (z: number) => (z + road.width / 2) * ppm;
    ctx.fillStyle = ASPHALT;
    ctx.fillRect(0, 0, cw, ch);
    for (let k = 0; k < lanes.count; k++) paintTyreTracks(ctx, 0, cw, pz(-half + (k + 0.5) * lanes.width), lanes.width * ppm, ppm, 21 + k);
    // the shoulders: a hair paler (less traffic) with a dirty edge along the barrier
    for (const s of [-1, 1]) {
      const z0 = s * half;
      const z1 = s * edge;
      ctx.fillStyle = 'rgba(190,192,198,0.045)';
      ctx.fillRect(0, Math.min(pz(z0), pz(z1)), cw, Math.abs(pz(z1) - pz(z0)));
      const g = ctx.createLinearGradient(0, pz(z1), 0, pz(z1) - s * 0.9 * ppm);
      g.addColorStop(0, 'rgba(10,11,13,0.34)');
      g.addColorStop(1, 'rgba(10,11,13,0)');
      ctx.fillStyle = g;
      ctx.fillRect(0, s > 0 ? pz(z1) - 0.9 * ppm : pz(z1), cw, 0.9 * ppm);
    }
    fadeEdges(ctx, cw, ch, ppm, HIGHWAY_FADE_END, 0, length);
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 8;
    return tex;
  }, [road.width, lanes.count, lanes.width, half, edge, length]);
  const baseMat = React.useMemo(() => asphaltMaterial(baseMap, length, road.width, grain), [baseMap, length, road.width, grain]);

  // ---- what is worn into the road, one repeat of it (rolled with the roadside)
  const wearMap = React.useMemo(() => {
    const ppm = 14;
    const canvas = document.createElement('canvas');
    canvas.width = Math.round(SIDE_PERIOD * ppm);
    canvas.height = Math.round(road.width * ppm);
    const ctx = canvas.getContext('2d')!;
    paintWearStrip(ctx, SIDE_PERIOD, road.width, ppm, 29, false, 0.4);
    const t = new THREE.CanvasTexture(canvas);
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 8;
    return t;
  }, [road.width]);
  const wearMat = React.useMemo(
    () => withBend(new THREE.MeshBasicMaterial({ map: wearMap, transparent: true, depthWrite: false, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -5, polygonOffsetUnits: -5 })),
    [wearMap],
  );

  // ---- the paint
  const paints = React.useMemo(() => {
    const edgeTex = edgeLineTexture(PAINT, EDGE_PERIOD, EDGE_WIDTH, 33).clone();
    edgeTex.repeat.set((length * 0.8) / EDGE_PERIOD, 1);
    return { edge: edgeTex, dash: paintStripTexture(PAINT, DASH.length, DASH.width, 34, 0.5) };
  }, [length]);
  const markMat = React.useMemo(() => {
    const m = (map: THREE.Texture) => withBend(new THREE.MeshBasicMaterial({ map, transparent: true, depthWrite: false, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -6, polygonOffsetUnits: -6 }));
    return {
      edge: m(paints.edge),
      dash: m(paints.dash),
      // the tar joints are drawn over the paint, so they cross the edge lines and the dashes
      joint: withBend(new THREE.MeshBasicMaterial({ color: '#141518', transparent: true, opacity: 0.5, depthWrite: false, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -7, polygonOffsetUnits: -7 })),
    };
  }, [paints]);
  React.useEffect(
    () => () => {
      baseMap.dispose();
      baseMat.dispose();
      wearMap.dispose();
      wearMat.dispose();
      paints.edge.dispose();
      Object.values(markMat).forEach((m) => m.dispose());
    },
    [baseMap, baseMat, wearMap, wearMat, paints, markMat],
  );
  useDusk((d) => {
    // rain darkens the asphalt and dulls the paint
    const wetK = 1 - 0.42 * weather.level;
    const paintK = 1 - 0.18 * weather.level;
    baseMat.color.copy(d.room).multiplyScalar(wetK);
    wearMat.color.copy(d.room).multiplyScalar(wetK);
    markMat.edge.color.copy(d.room).multiplyScalar(paintK);
    markMat.dash.color.copy(d.room).multiplyScalar(paintK);
  });

  // the surface slides with the road: the edge line's wear (one repeat is EDGE_PERIOD m), and the asphalt's grain (TILE.asphalt m a tile).
  // The road moves toward -x as the scroll grows, so the texture is sampled farther along: the offsets grow with it
  useFrame(() => {
    const s = rig.state.scroll;
    paints.edge.offset.x = (s / EDGE_PERIOD) % 1;
    grain.x = s / TILE.asphalt;
  });

  // ---- one dash plane and one joint plane, laid out on instances
  const lineSlots = React.useMemo(() => {
    const out: number[] = [];
    for (let x = -Math.ceil(length / 2 / DASH.period) * DASH.period; x <= length / 2 + DASH.period; x += DASH.period) out.push(x);
    return out;
  }, [length]);
  const jointSlots = React.useMemo(() => {
    const out: number[] = [];
    for (let x = -Math.ceil(length / 2 / JOINT_PERIOD) * JOINT_PERIOD; x <= length / 2 + JOINT_PERIOD; x += JOINT_PERIOD) out.push(x);
    return out;
  }, [length]);
  const dashMesh = React.useRef<THREE.InstancedMesh>(null);
  const jointMesh = React.useRef<THREE.InstancedMesh>(null);
  React.useLayoutEffect(() => {
    const m = new THREE.Matrix4();
    const d = dashMesh.current;
    if (d) {
      let i = 0;
      // a lane line between every two lanes: at the middle of the first dash's span
      for (let k = 1; k < lanes.count; k++) {
        const z = -half + k * lanes.width;
        // the strip is laid flat by the mesh's own turn about x, which sends the instance's y to the road's -z
        for (const x of lineSlots) d.setMatrixAt(i++, m.makeTranslation(x + DASH.length / 2, -z, 0));
      }
      d.count = i;
      d.instanceMatrix.needsUpdate = true;
    }
    const j = jointMesh.current;
    if (j) {
      jointSlots.forEach((x, i) => j.setMatrixAt(i, m.makeTranslation(x, 0, 0)));
      j.count = jointSlots.length;
      j.instanceMatrix.needsUpdate = true;
    }
  }, [lineSlots, jointSlots, lanes.count, lanes.width, half]);

  // ---- the roadside's layout and the worn road laid end to end
  const n = Math.ceil(length / 2 / SIDE_PERIOD);
  const spots = React.useMemo(() => expresswaySpots(edge, SIDE_PERIOD, n), [edge, n]);
  const wearMesh = React.useRef<THREE.InstancedMesh>(null);
  React.useLayoutEffect(() => {
    const w = wearMesh.current;
    if (!w) return;
    const m = new THREE.Matrix4();
    for (let i = 0; i <= 2 * n; i++) w.setMatrixAt(i, m.makeTranslation((i - n) * SIDE_PERIOD, 0, 0));
    w.count = 2 * n + 1;
    w.instanceMatrix.needsUpdate = true;
  }, [n]);

  const x0 = rig.rac.x - length / 2;
  const x1 = rig.rac.x + length / 2;
  // the road's middle is the car's own centre line, unless the car drives in a lane that is not the middle one (a road of two lanes): the strip is then
  // moved across so that the car's lane is under it
  const laneZ = road.carLane === undefined ? 0 : -half + (road.carLane + 0.5) * lanes.width;
  return (
    <group position-z={-rig.rac.y - laneZ}>
      <group ref={still}>
        <mesh position={[rig.rac.x, 0.002, 0]} rotation-x={-Math.PI / 2} renderOrder={-0.5} ref={onStage} material={baseMat}>
          <planeGeometry args={[length, road.width, alongOf(length), 1]} />
        </mesh>
        <Verge x0={x0} x1={x1} z0={edge + 0.3} z1={edge + 0.3 + VERGE} fadeEnd={HIGHWAY_FADE_END} scroll={scroll} />
        <Verge x0={x0} x1={x1} z0={-(edge + 0.3)} z1={-(edge + 0.3 + VERGE)} fadeEnd={HIGHWAY_FADE_END} scroll={scroll} />
        {/* the solid edge lines */}
        {[-half, half].map((z) => (
          <mesh key={z} position={[rig.rac.x, 0.003, z]} rotation-x={-Math.PI / 2} renderOrder={-0.4} ref={onStage} material={markMat.edge}>
            <planeGeometry args={[length * 0.8, EDGE_WIDTH, alongOf(length * 0.8), 1]} />
          </mesh>
        ))}
        {/* rain: the road is a mirror (a second picture of the scene from under it, drawn only while it rains) */}
        {(wet || wetShown) && <WetRoad rig={rig} x={rig.rac.x} length={length} width={road.width} lanes={lanes} fadeEnd={HIGHWAY_FADE_END} />}
      </group>
      {/* tar joints across the whole road, shoulders and edge lines too, and the dashes between them: the rig rolls these */}
      <group ref={joints}>
        <instancedMesh ref={jointMesh} args={[undefined, undefined, jointSlots.length]} rotation-x={-Math.PI / 2} position-y={0.0034} renderOrder={-0.38} frustumCulled={false} onUpdate={onStage} material={markMat.joint}>
          <planeGeometry args={[0.05, road.width]} />
        </instancedMesh>
      </group>
      <group ref={dashes}>
        <instancedMesh ref={dashMesh} args={[undefined, undefined, lineSlots.length * (lanes.count - 1)]} rotation-x={-Math.PI / 2} position-y={0.003} renderOrder={-0.4} frustumCulled={false} onUpdate={onStage} material={markMat.dash}>
          <planeGeometry args={[DASH.length, DASH.width]} />
        </instancedMesh>
      </group>
      {/* the worn road, the barriers, the trees and the gantry: rolled by one repeat */}
      <group ref={side}>
        <instancedMesh ref={wearMesh} args={[undefined, undefined, 2 * n + 1]} position={[SIDE_PERIOD / 2, 0.0025, 0]} rotation-x={-Math.PI / 2} renderOrder={-0.45} frustumCulled={false} onUpdate={onStage} material={wearMat}>
          <planeGeometry args={[SIDE_PERIOD, road.width, alongOf(SIDE_PERIOD), 1]} />
        </instancedMesh>
        <ExpresswayRoadside spots={spots} span={gantry ? (edge + 1.3) * 2 : 0} edge={edge} />
      </group>
    </group>
  );
}
