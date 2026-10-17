'use client';

import React from 'react';
import * as THREE from 'three';
import type { Vehicle } from '@/data/vehicles/schema';
import type { RoadStage } from '@/lib/tech/carpet';
import { humpAt, type Hump } from '@/lib/tech/ride';
import { rigOf } from '@/lib/tech/rig';
import { useRuntime } from '@/lib/tech/session';
import { STAGE_LAYER } from './StudioShowroom';

/**
 * The road of a treadmill demo (the Magic Carpet's run): a strip of asphalt and the rubber speed humps across
 * it. The car stays on the spot and the rig rolls this group under it (`RigState.scroll`, src/lib/tech/rig.ts),
 * so the humps pass the wheels exactly as the simulated ride says. The hump's profile is the one the ride
 * model drives its wheels over (`humpAt`), so what the tyre climbs is what is drawn.
 *
 * The group's x is run distance: 0 is where the rear axle started. Mount once in the showroom's Canvas.
 *
 * A road with lanes (Autonomous Drive's) is drawn by `Highway` below: one long strip that stands still under the car, and
 * its marks, which repeat, rolled as far as their period and no further.
 */
export function TechRoad({ vehicle }: { vehicle: Vehicle }) {
  const road = useRuntime()?.road;
  if (!road) return null;
  return road.lanes ? <Highway road={road} lanes={road.lanes} vehicle={vehicle} /> : <Road road={road} vehicle={vehicle} />;
}

/** pixels per metre of the asphalt's texture (less on a very long strip, to keep the canvas small) */
const PPM_MAX = 36;
const CANVAS_MAX = 4096;
const ASPHALT = '#4b4e54';
const PAINT = '#f1efe8';
/** the fade at the strip's ends and sides, m */
const FADE_END = 3.5;
const FADE_SIDE = 0.9;

const smooth = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

function Road({ road, vehicle }: { road: RoadStage; vehicle: Vehicle }) {
  const rig = rigOf(vehicle);
  const group = React.useRef<THREE.Group>(null);
  React.useEffect(() => {
    const g = group.current;
    if (!g) return;
    return rig.attachRoad(g, rig.rac.x);
  }, [rig, road]);

  return (
    // the lane runs along the car's own centre line
    <group position-z={-rig.rac.y}>
      <group ref={group}>
        <Asphalt road={road} />
        {road.humps.map((h, i) => (
          <HumpMesh key={i} hump={h} width={road.width - 1.6} />
        ))}
      </group>
    </group>
  );
}

function onStageLayer(o: THREE.Object3D | null) {
  o?.layers.set(STAGE_LAYER);
}

function Asphalt({ road }: { road: RoadStage }) {
  const length = road.to - road.from;
  const map = React.useMemo(() => {
    const PPM = Math.min(PPM_MAX, CANVAS_MAX / length);
    const W = Math.round(length * PPM);
    const H = Math.round(road.width * PPM);
    const canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d')!;
    ctx.fillStyle = ASPHALT;
    ctx.fillRect(0, 0, W, H);
    const px = (x: number) => (x - road.from) * PPM;
    // broken edge lines, so a road that rolls under a still car is seen to roll
    ctx.fillStyle = PAINT;
    const edge = road.width / 2 - 0.85;
    const { period, length: dash, joint } = road.markings ?? { period: 2.7, length: 0.9, joint: 6.1 };
    for (let x = road.from + FADE_END; x < road.to - FADE_END; x += period) {
      for (const side of [-1, 1]) {
        ctx.fillRect(px(x), (road.width / 2 + side * edge) * PPM - 0.06 * PPM, dash * PPM, 0.12 * PPM);
      }
    }
    // tar joints across the lane
    ctx.strokeStyle = 'rgba(20,21,24,0.55)';
    ctx.lineWidth = 0.05 * PPM;
    for (let x = road.from + 4.7; x < road.to; x += joint) {
      ctx.beginPath();
      ctx.moveTo(px(x), 0);
      ctx.lineTo(px(x + 0.12), H);
      ctx.stroke();
    }
    // grain, and the faded edge
    const img = ctx.getImageData(0, 0, W, H);
    const d = img.data;
    let seed = 777;
    const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296) - 0.5;
    for (let y = 0; y < H; y++) {
      const dy = Math.min(y, H - 1 - y) / PPM;
      for (let x = 0; x < W; x++) {
        const dx = Math.min(x, W - 1 - x) / PPM;
        const i = (y * W + x) * 4;
        const n = rnd() * 7;
        d[i] += n;
        d[i + 1] += n;
        d[i + 2] += n;
        d[i + 3] = Math.round(255 * smooth(0, FADE_SIDE, dy) * smooth(0, FADE_END, dx));
      }
    }
    ctx.putImageData(img, 0, 0);
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 8;
    return tex;
  }, [road, length]);
  React.useEffect(() => () => map.dispose(), [map]);

  return (
    <mesh position={[road.from + length / 2, 0.002, 0]} rotation-x={-Math.PI / 2} renderOrder={-0.5} ref={onStageLayer}>
      <planeGeometry args={[length, road.width]} />
      {/* biased toward the camera, as the parking lot's patch: 2 mm over the floor does not resolve at the stage's distance */}
      <meshBasicMaterial map={map} transparent depthWrite={false} toneMapped={false} polygonOffset polygonOffsetFactor={-4} polygonOffsetUnits={-4} />
    </mesh>
  );
}

/** Yellow and black bars across the lane, as the rubber humps are made. */
function barTexture(): THREE.CanvasTexture {
  const c = document.createElement('canvas');
  c.width = 256;
  c.height = 8;
  const ctx = c.getContext('2d')!;
  const bars = 12;
  for (let i = 0; i < bars; i++) {
    ctx.fillStyle = i % 2 ? '#1b1c1f' : '#f2c21b';
    ctx.fillRect((i * 256) / bars, 0, 256 / bars + 1, 8);
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = THREE.ClampToEdgeWrapping;
  return t;
}

/** One hump, across the lane: its profile from `humpAt`, the top and the two end walls. */
function HumpMesh({ hump, width }: { hump: Hump; width: number }) {
  const { geometry, map } = React.useMemo(() => {
    const n = 28;
    const pos: number[] = [];
    const nor: number[] = [];
    const uv: number[] = [];
    const idx: number[] = [];
    const half = hump.length / 2;
    const prof: { x: number; y: number }[] = [];
    for (let i = 0; i <= n; i++) {
      const x = -half + (hump.length * i) / n;
      prof.push({ x, y: humpAt({ ...hump, x: 0 }, x) });
    }
    // the top: two rows of vertices (the lane's two sides) per profile point
    for (let i = 0; i <= n; i++) {
      const p = prof[i];
      const a = prof[Math.max(0, i - 1)];
      const b = prof[Math.min(n, i + 1)];
      const sx = b.x - a.x;
      const sy = b.y - a.y;
      const l = Math.hypot(sx, sy) || 1;
      for (const z of [-width / 2, width / 2]) {
        pos.push(p.x, p.y, z);
        nor.push(-sy / l, sx / l, 0);
        uv.push(z > 0 ? 1 : 0, 0);
      }
    }
    for (let i = 0; i < n; i++) {
      const a = i * 2;
      idx.push(a, a + 1, a + 3, a, a + 3, a + 2);
    }
    // the end walls: the profile down to the road, flat-shaded toward the side
    for (const z of [-width / 2, width / 2]) {
      const base = pos.length / 3;
      for (let i = 0; i <= n; i++) {
        pos.push(prof[i].x, prof[i].y, z, prof[i].x, 0, z);
        nor.push(0, 0, Math.sign(z), 0, 0, Math.sign(z));
        const u = z > 0 ? 1 : 0;
        uv.push(u, 0, u, 0);
      }
      for (let i = 0; i < n; i++) {
        const a = base + i * 2;
        if (z > 0) idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
        else idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3);
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    g.setIndex(idx);
    return { geometry: g, map: barTexture() };
  }, [hump, width]);
  React.useEffect(
    () => () => {
      geometry.dispose();
      map.dispose();
    },
    [geometry, map],
  );
  return (
    <mesh geometry={geometry} position={[hump.x, 0.004, 0]} ref={onStageLayer}>
      <meshStandardMaterial map={map} roughness={0.78} metalness={0} />
    </mesh>
  );
}

// ------------------------------------------------------------------ the highway

/** the dashed lane line (Chinese expressways: 6 m of paint and 9 m of gap), the edge line, and the spacing of the tar joints, m */
const DASH = { length: 6, period: 15, width: 0.15 };
const EDGE_WIDTH = 0.2;
const JOINT_PERIOD = 12.5;
/** the fade at the strip's far ends (it is long enough that they are out of sight) and at its sides, m */
const HIGHWAY_FADE_END = 70;
const HIGHWAY_FADE_SIDE = 1.1;

/**
 * The expressway of Autonomous Drive: the asphalt with its two solid edge lines stands still under the car; the dashes
 * between the lanes and the tar joints are short repeating strips that the rig rolls by the road's scroll modulo their
 * period, so they stream past at the car's speed on a strip of a few hundred metres, whatever the run's length.
 */
function Highway({ road, lanes, vehicle }: { road: RoadStage; lanes: NonNullable<RoadStage['lanes']>; vehicle: Vehicle }) {
  const rig = rigOf(vehicle);
  const dashes = React.useRef<THREE.Group>(null);
  const joints = React.useRef<THREE.Group>(null);
  React.useEffect(() => {
    const a = dashes.current;
    const b = joints.current;
    if (!a || !b) return;
    const offA = rig.attachRoad(a, rig.rac.x, DASH.period);
    const offB = rig.attachRoad(b, rig.rac.x, JOINT_PERIOD);
    return () => {
      offA();
      offB();
    };
  }, [rig, road]);

  const length = road.to - road.from;
  const half = (lanes.count * lanes.width) / 2;
  const map = React.useMemo(() => {
    const W = 1536;
    const H = 96;
    const canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d')!;
    ctx.fillStyle = ASPHALT;
    ctx.fillRect(0, 0, W, H);
    const img = ctx.getImageData(0, 0, W, H);
    const d = img.data;
    let seed = 4711;
    const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296) - 0.5;
    for (let y = 0; y < H; y++) {
      const dy = (Math.min(y, H - 1 - y) / H) * road.width;
      for (let x = 0; x < W; x++) {
        const dx = (Math.min(x, W - 1 - x) / W) * length;
        const i = (y * W + x) * 4;
        const n = rnd() * 6;
        d[i] += n;
        d[i + 1] += n;
        d[i + 2] += n;
        d[i + 3] = Math.round(255 * smooth(0, HIGHWAY_FADE_SIDE, dy) * smooth(0, HIGHWAY_FADE_END, dx));
      }
    }
    ctx.putImageData(img, 0, 0);
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 8;
    return tex;
  }, [road, length]);
  React.useEffect(() => () => map.dispose(), [map]);

  // one dash plane and one joint plane, laid out on instances
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

  const mark = { polygonOffset: true, polygonOffsetFactor: -6, polygonOffsetUnits: -6, toneMapped: false, depthWrite: false } as const;
  return (
    // the road's middle is the car's own centre line
    <group position-z={-rig.rac.y}>
      <mesh position={[rig.rac.x, 0.002, 0]} rotation-x={-Math.PI / 2} renderOrder={-0.5} ref={onStageLayer}>
        <planeGeometry args={[length, road.width]} />
        <meshBasicMaterial map={map} transparent polygonOffset polygonOffsetFactor={-4} polygonOffsetUnits={-4} depthWrite={false} toneMapped={false} />
      </mesh>
      {/* the solid edge lines */}
      {[-half, half].map((z) => (
        <mesh key={z} position={[rig.rac.x, 0.003, z]} rotation-x={-Math.PI / 2} renderOrder={-0.4} ref={onStageLayer}>
          <planeGeometry args={[length * 0.8, EDGE_WIDTH]} />
          <meshBasicMaterial color={PAINT} transparent opacity={0.92} {...mark} />
        </mesh>
      ))}
      {/* tar joints across the lanes, and the dashes between them: the rig rolls these */}
      <group ref={joints}>
        <instancedMesh ref={jointMesh} args={[undefined, undefined, jointSlots.length]} rotation-x={-Math.PI / 2} position-y={0.0025} renderOrder={-0.42} frustumCulled={false} onUpdate={onStageLayer}>
          <planeGeometry args={[0.05, half * 2]} />
          <meshBasicMaterial color="#141518" transparent opacity={0.5} {...mark} />
        </instancedMesh>
      </group>
      <group ref={dashes}>
        <instancedMesh ref={dashMesh} args={[undefined, undefined, lineSlots.length * (lanes.count - 1)]} rotation-x={-Math.PI / 2} position-y={0.003} renderOrder={-0.4} frustumCulled={false} onUpdate={onStageLayer}>
          <planeGeometry args={[DASH.length, DASH.width]} />
          <meshBasicMaterial color={PAINT} transparent opacity={0.92} {...mark} />
        </instancedMesh>
      </group>
    </group>
  );
}
