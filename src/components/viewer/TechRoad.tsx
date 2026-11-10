'use client';

import React from 'react';
import * as THREE from 'three';
import type { Vehicle } from '@/data/vehicles/schema';
import type { RoadStage } from '@/lib/tech/carpet';
import { humpAt, type Hump } from '@/lib/tech/ride';
import { rigOf } from '@/lib/tech/rig';
import { useRuntime } from '@/lib/tech/session';
import { STAGE_LAYER } from './StudioShowroom';
import { useDusk } from './Lights';
import { CityStreet } from './TechCity';
import { Highway } from './TechHighway';
import { asphaltMaterial, fadeEdges, paintWearStrip } from './scenery/Ground';
import { ExpresswayRoadside, Verge, expresswaySpots } from './scenery/Roadside';
import { useHaze } from './scenery/Scenery';
import { ASPHALT, PAINT, paintTyreTracks, wearPaint } from './scenery/textures';

/**
 * The road of a treadmill demo (the Magic Carpet's run): a strip of asphalt and the rubber speed humps across
 * it. The car stays on the spot and the rig rolls this group under it (`RigState.scroll`, src/lib/tech/rig.ts),
 * so the humps pass the wheels exactly as the simulated ride says. The hump's profile is the one the ride
 * model drives its wheels over (`humpAt`), so what the tyre climbs is what is drawn.
 *
 * The group's x is run distance: 0 is where the rear axle started. Mount once in the showroom's Canvas.
 *
 * A road with lanes (Autonomous Drive's) is drawn by `Highway` (TechHighway.tsx): one long strip that stands still under the
 * car, and its marks and roadside, which repeat, rolled as far as their period and no further.
 */
export function TechRoad({ vehicle }: { vehicle: Vehicle }) {
  const rt = useRuntime();
  const road = rt?.road;
  if (!road) return null;
  if (road.city) return <CityStreet road={road} city={road.city} vehicle={vehicle} />;
  // the Drive tab's wet road: the same asphalt under a dark gloss that mirrors the studio
  const wet = Boolean(rt?.launch?.drive?.env.wet);
  return road.lanes ? <Highway road={road} lanes={road.lanes} vehicle={vehicle} /> : <Road road={road} vehicle={vehicle} wet={wet} />;
}

/** pixels per metre of the asphalt's texture (less on a very long strip, to keep the canvas small) */
const PPM_MAX = 36;
const CANVAS_MAX = 4096;
/** the fade at the strip's ends and sides, m */
const FADE_END = 3.5;
const FADE_SIDE = 0.9;

const smooth = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

function Road({ road, vehicle, wet = false }: { road: RoadStage; vehicle: Vehicle; wet?: boolean }) {
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
        <TrackSides road={road} />
        {wet && <WetSheen road={road} />}
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

/**
 * The strip of road the Drive tab, the launch and the Magic Carpet run on: worn asphalt with the tyres' tracks in the lane, the
 * broken edge lines (chipped paint), tar joints across, mended patches and hairline cracks. It rolls under the car as one piece
 * (the rig's scroll), so everything painted into it moves with the road.
 */
function Asphalt({ road }: { road: RoadStage }) {
  const length = road.to - road.from;
  const map = React.useMemo(() => {
    // pixels to the metre: sharp across the road (tracks, lines), stretched along it where a long strip would overrun the canvas
    const ppmY = 40;
    const ppmX = Math.min(PPM_MAX, CANVAS_MAX / length);
    const W = Math.round(length * ppmX);
    const H = Math.round(road.width * ppmY);
    const canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d', { willReadFrequently: true })!;
    const px = (x: number) => (x - road.from) * ppmX;
    ctx.fillStyle = ASPHALT;
    ctx.fillRect(0, 0, W, H);
    // the lane the car drives: two tracks, a pale crown between them, dirty margins
    paintTyreTracks(ctx, 0, W, H / 2, Math.min(road.width, 3.6) * ppmY, ppmY, 3);
    for (const s of [-1, 1]) {
      const g = ctx.createLinearGradient(0, s < 0 ? 0 : H, 0, s < 0 ? 0.9 * ppmY : H - 0.9 * ppmY);
      g.addColorStop(0, 'rgba(10,11,13,0.32)');
      g.addColorStop(1, 'rgba(10,11,13,0)');
      ctx.fillStyle = g;
      ctx.fillRect(0, s < 0 ? 0 : H - 0.9 * ppmY, W, 0.9 * ppmY);
    }
    // broken edge lines, so a road that rolls under a still car is seen to roll (chipped, as paint is)
    ctx.fillStyle = PAINT;
    const edge = road.width / 2 - 0.85;
    const { period, length: dash, joint } = road.markings ?? { period: 2.7, length: 0.9, joint: 6.1 };
    const lw = 0.12 * ppmY;
    for (let x = road.from + FADE_END; x < road.to - FADE_END; x += period) {
      for (const side of [-1, 1]) {
        const y = (road.width / 2 + side * edge) * ppmY - lw / 2;
        ctx.fillRect(px(x), y, dash * ppmX, lw);
        wearPaint(ctx, px(x), y, dash * ppmX, lw, ppmY, Math.round(x * 7) + side, 0.5);
      }
    }
    // tar joints across the lane
    ctx.strokeStyle = 'rgba(20,21,24,0.55)';
    ctx.lineWidth = 0.05 * ppmX;
    for (let x = road.from + 4.7; x < road.to; x += joint) {
      ctx.beginPath();
      ctx.moveTo(px(x), 0);
      ctx.lineTo(px(x + 0.12), H);
      ctx.stroke();
    }
    fadeEdges(ctx, W, H, ppmX, FADE_END, 0, length);
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 8;
    return tex;
  }, [road, length]);
  const mat = React.useMemo(() => asphaltMaterial(map, length, road.width), [map, length, road.width]);
  // the worn patches, cracks and oil: one repeat of them, laid end to end along the strip (they roll with it)
  const WEAR = 60;
  const wearMap = React.useMemo(() => {
    const ppm = 22;
    const canvas = document.createElement('canvas');
    canvas.width = Math.round(WEAR * ppm);
    canvas.height = Math.round(road.width * ppm);
    const ctx = canvas.getContext('2d')!;
    paintWearStrip(ctx, WEAR, road.width, ppm, 41, false, 0.8);
    const t = new THREE.CanvasTexture(canvas);
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 8;
    return t;
  }, [road.width]);
  const wearMat = React.useMemo(
    () => new THREE.MeshBasicMaterial({ map: wearMap, transparent: true, depthWrite: false, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -5, polygonOffsetUnits: -5 }),
    [wearMap],
  );
  React.useEffect(
    () => () => {
      map.dispose();
      mat.dispose();
      wearMap.dispose();
      wearMat.dispose();
    },
    [map, mat, wearMap, wearMat],
  );
  useDusk((d) => {
    mat.color.copy(d.room);
    wearMat.color.copy(d.room);
  });
  useHaze();
  const copies = Math.ceil(length / WEAR);
  const wearMesh = React.useRef<THREE.InstancedMesh>(null);
  React.useLayoutEffect(() => {
    const w = wearMesh.current;
    if (!w) return;
    const m = new THREE.Matrix4();
    for (let i = 0; i < copies; i++) w.setMatrixAt(i, m.makeTranslation(road.from + WEAR / 2 + i * WEAR, 0, 0));
    w.count = copies;
    w.instanceMatrix.needsUpdate = true;
  }, [copies, road.from]);

  return (
    <>
      {/* biased toward the camera, as the parking lot's patch: 2 mm over the floor does not resolve at the stage's distance */}
      <mesh position={[road.from + length / 2, 0.002, 0]} rotation-x={-Math.PI / 2} renderOrder={-0.5} ref={onStageLayer} material={mat}>
        <planeGeometry args={[length, road.width]} />
      </mesh>
      <instancedMesh ref={wearMesh} args={[undefined, undefined, copies]} position-y={0.0025} rotation-x={-Math.PI / 2} renderOrder={-0.45} frustumCulled={false} onUpdate={onStageLayer} material={wearMat}>
        <planeGeometry args={[WEAR, road.width]} />
      </instancedMesh>
    </>
  );
}

/**
 * What lines the road: grass verges that fade into the studio's white, the crash barrier along one side and the median's concrete
 * barrier and planting along the other, delineator posts, kilometre posts, and clumps of roadside trees. It stands in the road's
 * own frame, so it rolls with it (the rig's scroll), and is laid out over the strip's length in repeats of 120 m.
 */
function TrackSides({ road }: { road: RoadStage }) {
  const length = road.to - road.from;
  const edge = road.width / 2;
  const P = 120;
  const n = Math.ceil(length / 2 / P);
  const spots = React.useMemo(() => {
    const s = expresswaySpots(edge, P, n, 9);
    // a test road has no gantry
    delete (s as Record<string, unknown>).gantry;
    return s;
  }, [edge, n]);
  const x0 = road.from;
  const x1 = road.to;
  return (
    <>
      <Verge x0={x0} x1={x1} z0={edge - 0.1} z1={edge + 0.3 + 14} fadeEnd={Math.min(40, length / 3)} />
      <Verge x0={x0} x1={x1} z0={-(edge - 0.1)} z1={-(edge + 0.3 + 14)} fadeEnd={Math.min(40, length / 3)} />
      <group position-x={(x0 + x1) / 2}>
        <ExpresswayRoadside spots={spots} span={0} edge={edge} />
      </group>
    </>
  );
}

/**
 * A wet road: a dark gloss over the asphalt, faded at the edges as it is, lit by the studio's environment so that it mirrors the
 * rig's lamps and the car. Drawn the same size as the asphalt, a hair above it.
 */
function WetSheen({ road }: { road: RoadStage }) {
  const length = road.to - road.from;
  const alpha = React.useMemo(() => {
    const W = 1024;
    const H = 128;
    const canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d')!;
    const img = ctx.createImageData(W, H);
    for (let y = 0; y < H; y++) {
      const dy = (Math.min(y, H - 1 - y) / H) * road.width;
      for (let x = 0; x < W; x++) {
        const dx = (Math.min(x, W - 1 - x) / W) * length;
        const i = (y * W + x) * 4;
        const v = Math.round(255 * smooth(0, FADE_SIDE, dy) * smooth(0, FADE_END, dx));
        img.data[i] = img.data[i + 1] = img.data[i + 2] = v;
        img.data[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
    return new THREE.CanvasTexture(canvas);
  }, [road.width, length]);
  React.useEffect(() => () => alpha.dispose(), [alpha]);
  return (
    <mesh position={[road.from + length / 2, 0.0035, 0]} rotation-x={-Math.PI / 2} renderOrder={-0.4} ref={onStageLayer}>
      <planeGeometry args={[length, road.width]} />
      <meshStandardMaterial
        color="#161a22"
        roughness={0.08}
        metalness={0}
        envMapIntensity={2.6}
        transparent
        opacity={0.8}
        alphaMap={alpha}
        depthWrite={false}
        polygonOffset
        polygonOffsetFactor={-6}
        polygonOffsetUnits={-6}
      />
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
