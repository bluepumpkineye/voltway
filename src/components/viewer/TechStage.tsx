'use client';

import React from 'react';
import * as THREE from 'three';
import { useGLTF } from '@react-three/drei';
import { getVehicle } from '@/data/vehicles';
import type { ParkNeighbour, ParkStage, Rect } from '@/lib/tech/park';
import { useVehicleStore } from '@/store/vehicle-store';
import { DRACO_PATH } from './CarModel';
import { useDusk } from './Lights';
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
const ASPHALT = '#4b4e54';
const PAINT = '#f1efe8';
/** the fade at the edge of the patch, m */
const FADE = 1.15;

const smooth = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

/**
 * The asphalt: one canvas texture holding the paint, with the edge faded out into the studio's white
 * so the patch reads as a stage and not as a sheet laid on the floor.
 */
function Asphalt({ stage }: { stage: ParkStage }) {
  const a = stage.asphalt;
  const map = React.useMemo(() => {
    const W = Math.round(a.length * PPM);
    const H = Math.round(a.width * PPM);
    const canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d')!;
    ctx.fillStyle = ASPHALT;
    ctx.fillRect(0, 0, W, H);
    // floor (x, y) to canvas pixels: north at the top
    const px = (x: number) => (x - (a.x - a.length / 2)) * PPM;
    const py = (y: number) => ((a.y + a.width / 2) - y) * PPM;

    ctx.strokeStyle = PAINT;
    ctx.lineCap = 'butt';
    ctx.lineWidth = 0.1 * PPM;
    for (const b of stage.bays) {
      // the bay is open at the lane: its two sides and its back
      const r = b.rect;
      const x0 = r.x - r.width / 2;
      const x1 = r.x + r.width / 2;
      const y1 = r.y + r.length / 2;
      const y0 = r.y - r.length / 2;
      ctx.beginPath();
      ctx.moveTo(px(x0), py(y1));
      ctx.lineTo(px(x0), py(y0));
      ctx.lineTo(px(x1), py(y0));
      ctx.lineTo(px(x1), py(y1));
      ctx.stroke();
    }
    // the lane's far edge
    ctx.lineWidth = 0.12 * PPM;
    ctx.beginPath();
    ctx.moveTo(px(a.x - a.length / 2 + FADE), py(stage.laneEdgeY));
    ctx.lineTo(px(a.x + a.length / 2 - FADE), py(stage.laneEdgeY));
    ctx.stroke();
    // an arrow along the lane, in the part the car does not use
    const ax = a.x - a.length / 2 + FADE + 3.4;
    const ay = stage.start.y;
    ctx.fillStyle = PAINT;
    ctx.beginPath();
    ctx.moveTo(px(ax - 2.2), py(ay + 0.16));
    ctx.lineTo(px(ax - 0.5), py(ay + 0.16));
    ctx.lineTo(px(ax - 0.5), py(ay + 0.55));
    ctx.lineTo(px(ax + 0.6), py(ay));
    ctx.lineTo(px(ax - 0.5), py(ay - 0.55));
    ctx.lineTo(px(ax - 0.5), py(ay - 0.16));
    ctx.lineTo(px(ax - 2.2), py(ay - 0.16));
    ctx.closePath();
    ctx.fill();

    // grain, and the faded edge
    const img = ctx.getImageData(0, 0, W, H);
    const d = img.data;
    let seed = 12345;
    const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296) - 0.5;
    for (let y = 0; y < H; y++) {
      const dy = Math.min(y, H - 1 - y) / PPM;
      for (let x = 0; x < W; x++) {
        const dist = Math.min(dy, Math.min(x, W - 1 - x) / PPM);
        const i = (y * W + x) * 4;
        const n = rnd() * 7;
        d[i] += n;
        d[i + 1] += n;
        d[i + 2] += n;
        d[i + 3] = Math.round(255 * smooth(0, FADE, dist));
      }
    }
    ctx.putImageData(img, 0, 0);

    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 8;
    return tex;
  }, [stage, a]);
  React.useEffect(() => () => map.dispose(), [map]);
  // the lamps take the room toward dusk, and the lot with it
  const mat = React.useRef<THREE.MeshBasicMaterial>(null);
  useDusk((d) => mat.current?.color.copy(d.room));

  return (
    <mesh position={[a.x, 0.002, -a.y]} rotation-x={-Math.PI / 2} renderOrder={-0.5} ref={onStageLayer}>
      <planeGeometry args={[a.length, a.width]} />
      {/* biased toward the camera: 2 mm over the floor is less than the depth buffer resolves at the stage's distance */}
      <meshBasicMaterial ref={mat} map={map} transparent depthWrite={false} toneMapped={false} polygonOffset polygonOffsetFactor={-4} polygonOffsetUnits={-4} />
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
