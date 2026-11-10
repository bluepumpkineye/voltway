'use client';

import React from 'react';
import * as THREE from 'three';
import { useGLTF } from '@react-three/drei';
import { getVehicle } from '@/data/vehicles';
import type { ParkNeighbour, ParkStage, Rect } from '@/lib/tech/park';
import { useVehicleStore } from '@/store/vehicle-store';
import { DRACO_PATH } from './CarModel';
import { useDusk } from './Lights';
import { asphaltMaterial, fadeEdges, paintAsphaltBase } from './scenery/Ground';
import { rng } from './scenery/kit';
import { useHaze } from './scenery/Scenery';
import { PAINT, paintArrow, paintDrain, paintOil, wearPaint } from './scenery/textures';
import { GroundShadow, STAGE_LAYER } from './StudioShowroom';

/**
 * The floor a tech demo drives on, drawn round the car: a patch of asphalt with the bays painted on it,
 * the wheel stops at their backs, and the cars parked beside the empty bay. The geometry is the stage
 * the demo's planner made (src/lib/tech/park.ts); this only draws it.
 *
 * Floor coordinates are the kinematics' (x forward, y left); the viewer's z is -y.
 */
export function TechStage() {
  const stage = useVehicleStore((s) => s.techScene);
  if (!stage) return null;
  return (
    <group>
      <Asphalt stage={stage} />
      {stage.stops.map((r, i) => (
        <WheelStop key={i} rect={r} />
      ))}
      {stage.neighbours.map((n, i) => (
        <React.Suspense key={`${n.slug}-${i}`} fallback={null}>
          <Neighbour n={n} tone={TONES[i % TONES.length]} />
        </React.Suspense>
      ))}
    </group>
  );
}

/** the paint of the parked cars: neutral, so the car in the demo stays the one the eye follows */
export const TONES = ['#c9ccd2', '#aeb3bb', '#363b45', '#8d929b'];

/** pixels per metre of the painted ground's texture */
const PPM = 70;
/** the fade at the edge of the patch, m */
const FADE = 1.15;

/**
 * The asphalt: one canvas texture holding the paint, with the edge faded out into the studio's white so the patch reads as a stage
 * and not as a sheet laid on the floor. Painted the way a car park is used: the tyres' tracks down the lane, oil under the bays,
 * patches and cracks, a drain, chipped bay lines with their numbers, the lane's arrow; and the tiled aggregate over it all.
 */
function Asphalt({ stage }: { stage: ParkStage }) {
  const a = stage.asphalt;
  const map = React.useMemo(() => {
    const W = Math.round(a.length * PPM);
    const H = Math.round(a.width * PPM);
    const canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d', { willReadFrequently: true })!;
    // floor (x, y) to canvas pixels: north at the top
    const px = (x: number) => (x - (a.x - a.length / 2)) * PPM;
    const py = (y: number) => (a.y + a.width / 2 - y) * PPM;

    // the lane's own strip: from the bays' mouths to the far edge
    const mouth = Math.min(...stage.bays.map((b) => b.rect.y - b.rect.length / 2)) + Math.max(...stage.bays.map((b) => b.rect.length));
    const laneTop = Math.max(stage.laneEdgeY, mouth);
    const laneBot = Math.min(stage.laneEdgeY, mouth);
    paintAsphaltBase(ctx, W, H, PPM, [{ y: py((laneTop + laneBot) / 2), w: Math.abs(laneTop - laneBot) * PPM }], { seed: 5, patches: Math.round(a.length / 4), cracks: Math.round(a.length * 1.3) });
    // oil under the bays, where cars stand all day
    const r = rng(19);
    for (const b of stage.bays) {
      const bx = b.rect.x;
      const by = b.rect.y;
      if (r() > 0.25) paintOil(ctx, px(bx + (r() - 0.5) * 0.5), py(by + (r() - 0.5) * 1.2), (0.25 + r() * 0.3) * PPM, 0.34);
      if (r() > 0.6) paintOil(ctx, px(bx + (r() - 0.5) * 0.9), py(by - 1.2 + (r() - 0.5) * 0.8), 0.2 * PPM, 0.26);
    }
    // a drain in the lane and the tyres' scuff where cars turn in
    paintDrain(ctx, px(a.x - a.length * 0.18), py(stage.start.y - 1.4), 1.1 * PPM, 0.38 * PPM, PPM);

    ctx.strokeStyle = PAINT;
    ctx.lineCap = 'butt';
    ctx.lineWidth = 0.1 * PPM;
    stage.bays.forEach((b, i) => {
      // the bay is open at the lane: its two sides and its back
      const rc = b.rect;
      const x0 = rc.x - rc.width / 2;
      const x1 = rc.x + rc.width / 2;
      const y1 = rc.y + rc.length / 2;
      const y0 = rc.y - rc.length / 2;
      ctx.beginPath();
      ctx.moveTo(px(x0), py(y1));
      ctx.lineTo(px(x0), py(y0));
      ctx.lineTo(px(x1), py(y0));
      ctx.lineTo(px(x1), py(y1));
      ctx.stroke();
      wearPaint(ctx, px(x0) - 0.06 * PPM, py(y1), 0.12 * PPM, rc.length * PPM, PPM, 31 + i, 0.5);
      wearPaint(ctx, px(x1) - 0.06 * PPM, py(y1), 0.12 * PPM, rc.length * PPM, PPM, 61 + i, 0.5);
      wearPaint(ctx, px(x0), py(y0) - 0.06 * PPM, rc.width * PPM, 0.12 * PPM, PPM, 91 + i, 0.5);
      // the bay's number, big, at the back, read from the lane
      ctx.save();
      ctx.translate(px(rc.x), py(y0 + 0.9));
      ctx.rotate(Math.PI / 2);
      ctx.fillStyle = 'rgba(241,239,232,0.82)';
      ctx.font = `700 ${0.62 * PPM}px "Arial Narrow","Helvetica Neue",Arial,sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(String(i + 1).padStart(2, '0'), 0, 0);
      ctx.restore();
      if (b.target) {
        // the bay the demo parks in: a pale-blue wash with a small plug mark, as an EV bay is
        ctx.fillStyle = 'rgba(70,170,150,0.22)';
        ctx.fillRect(px(x0) + 0.07 * PPM, py(y1), (x1 - x0) * PPM - 0.14 * PPM, rc.length * PPM);
      }
    });
    // the lane's far edge
    ctx.strokeStyle = PAINT;
    ctx.lineWidth = 0.12 * PPM;
    ctx.beginPath();
    ctx.moveTo(px(a.x - a.length / 2 + FADE), py(stage.laneEdgeY));
    ctx.lineTo(px(a.x + a.length / 2 - FADE), py(stage.laneEdgeY));
    ctx.stroke();
    wearPaint(ctx, px(a.x - a.length / 2 + FADE), py(stage.laneEdgeY) - 0.06 * PPM, (a.length - 2 * FADE) * PPM, 0.12 * PPM, PPM, 7, 0.45);
    // an arrow along the lane, in the part the car does not use
    paintArrow(ctx, px(a.x - a.length / 2 + FADE + 2.8), py(stage.start.y), 2.4 * PPM, PPM);
    fadeEdges(ctx, W, H, PPM, FADE, FADE);

    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 8;
    return tex;
  }, [stage, a]);
  const mat = React.useMemo(() => asphaltMaterial(map, a.length, a.width), [map, a.length, a.width]);
  React.useEffect(
    () => () => {
      map.dispose();
      mat.dispose();
    },
    [map, mat],
  );
  // the lamps take the room toward dusk, and the lot with it
  useDusk((d) => mat.color.copy(d.room));
  useHaze();

  return (
    <mesh position={[a.x, 0.002, -a.y]} rotation-x={-Math.PI / 2} renderOrder={-0.5} ref={onStageLayer} material={mat}>
      <planeGeometry args={[a.length, a.width]} />
    </mesh>
  );
}

/** Seen by the view camera only, as the studio's own floor: a painted patch is not reflected. */
function onStageLayer(o: THREE.Object3D | null) {
  o?.layers.set(STAGE_LAYER);
}

function WheelStop({ rect }: { rect: Rect }) {
  return (
    <mesh position={[rect.x, 0.045, -rect.y]} rotation-y={rect.yaw}>
      <boxGeometry args={[rect.length, 0.09, rect.width]} />
      <meshStandardMaterial color="#b9bbc0" roughness={0.9} />
    </mesh>
  );
}

/**
 * A parked car: the stand-in of another modelled car (scripts/make-proxy.mjs), recoloured to a neutral
 * paint, on the baked floor shadow of the real one. Placed so the middle of its body is the middle of
 * its bay, whatever the model's origin is.
 */
export function Neighbour({ n, tone }: { n: Pick<ParkNeighbour, 'slug' | 'rect'>; tone: string }) {
  const vehicle = getVehicle(n.slug);
  const url = vehicle?.assets.proxyUrl;
  if (!vehicle || !url) return null;
  return <NeighbourModel n={n} tone={tone} url={url} shadow={vehicle.assets.studioShadow} />;
}

/**
 * Another car's stand-in (scripts/make-proxy.mjs) in neutral paint: the model, and where the middle of its body is (the
 * model's origin is not it). Shared by the parked cars and the traffic of Autonomous Drive.
 */
export function useStandIn(url: string, tone: string): { model: THREE.Object3D; centre: THREE.Vector3 } {
  const { scene } = useGLTF(url, DRACO_PATH);
  const standIn = React.useMemo(() => {
    const root = scene.clone(true);
    // a matte paint, like a maquette's: the stand-ins are coarse, and a gloss finish would show every facet
    const paint = new THREE.MeshStandardMaterial({ color: tone, roughness: 0.62, metalness: 0.05, side: THREE.DoubleSide });
    const glass = new THREE.MeshStandardMaterial({ color: '#0b0e12', roughness: 0.2, metalness: 0.1 });
    const trim = new THREE.MeshStandardMaterial({ color: '#16171a', roughness: 0.55, metalness: 0.1 });
    const tyre = new THREE.MeshStandardMaterial({ color: '#0d0d0f', roughness: 0.9 });
    const rim = new THREE.MeshStandardMaterial({ color: '#9a9da3', roughness: 0.35, metalness: 0.85 });
    const byName: Record<string, THREE.Material> = { Paint: paint, Glass: glass, Trim: trim, Tyre: tyre, Rim: rim };
    root.traverse((o) => {
      if (!(o instanceof THREE.Mesh)) return;
      const src = Array.isArray(o.material) ? o.material[0] : o.material;
      o.material = byName[src.name] ?? trim;
    });
    const box = new THREE.Box3().setFromObject(root);
    return { model: root, centre: box.getCenter(new THREE.Vector3()) };
  }, [scene, tone]);
  React.useEffect(
    () => () => {
      standIn.model.traverse((o) => {
        if (o instanceof THREE.Mesh) (o.material as THREE.Material).dispose();
      });
    },
    [standIn],
  );
  return standIn;
}

function NeighbourModel({
  n,
  tone,
  url,
  shadow,
}: {
  n: Pick<ParkNeighbour, 'slug' | 'rect'>;
  tone: string;
  url: string;
  shadow: Parameters<typeof GroundShadow>[0]['shadow'] | undefined;
}) {
  const { model, centre } = useStandIn(url, tone);

  // the group sits at the model's origin; the middle of the body goes to the middle of the bay
  const { x, y, yaw } = n.rect;
  const c = Math.cos(yaw);
  const s = Math.sin(yaw);
  const px = x - (centre.x * c + centre.z * s);
  const pz = -y - (-centre.x * s + centre.z * c);
  return (
    <group position={[px, 0, pz]} rotation-y={yaw}>
      <primitive object={model} />
      {shadow && <GroundShadow shadow={shadow} />}
    </group>
  );
}
