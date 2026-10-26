'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import type { SensorSpec, Vehicle } from '@/data/vehicles/schema';
import { techClock } from '@/lib/tech/clock';
import type { ParkNeighbour, ParkStage, Rect } from '@/lib/tech/park';
import { useRuntime, type Runtime } from '@/lib/tech/session';
import { CarCoverage, cornerBrackets } from './TechSensors';

/**
 * The SU7's parking assist, drawn the way Xiaomi's own animation draws the function (xiaomiauto.com/global/pilot): the
 * car's surround beams and ripples go with it along the row of bays, the cars it passes are bracketed as it sees them,
 * and the empty bay is picked out with a blue P when it has been seen. It draws on top of the park demo's stage (TechStage:
 * the asphalt, the bays, the cars), only while a demo with a search (ParkOptions.search) is on. Mount once in the Canvas.
 */
export function TechParkAssist({ vehicle }: { vehicle: Vehicle }) {
  const runtime = useRuntime();
  const stage = runtime?.stage;
  const spec = vehicle.sensors;
  if (!runtime || !stage?.bays?.some((b) => b.target) || !spec) return null;
  return <Overlay vehicle={vehicle} spec={spec} stage={stage} runtime={runtime} />;
}

const BLUE = '#38a8ff';
const PALE = '#9bd8ff';

function Overlay({ vehicle, spec, stage, runtime }: { vehicle: Vehicle; spec: SensorSpec; stage: ParkStage; runtime: Runtime }) {
  return (
    <group>
      {/* the beams, the ripples and the camera dots go with the car */}
      <CarCoverage vehicle={vehicle} spec={spec} runtime={runtime} parts={['surround', 'ultrasonic', 'cameras']} surroundReach={8} />
      <BayMark stage={stage} runtime={runtime} />
      {stage.neighbours.map((n, i) => (
        <Bracketed key={i} n={n} stage={stage} runtime={runtime} />
      ))}
    </group>
  );
}

/** The blue P with four corner marks, on a transparent square. */
function pTexture(): THREE.CanvasTexture {
  const S = 256;
  const c = document.createElement('canvas');
  c.width = c.height = S;
  const ctx = c.getContext('2d')!;
  ctx.strokeStyle = PALE;
  ctx.lineWidth = 9;
  ctx.lineCap = 'round';
  const m = 22;
  const l = 54;
  for (const [x, y, dx, dy] of [
    [m, m, 1, 1],
    [S - m, m, -1, 1],
    [m, S - m, 1, -1],
    [S - m, S - m, -1, -1],
  ] as const) {
    ctx.beginPath();
    ctx.moveTo(x + dx * l, y);
    ctx.lineTo(x, y);
    ctx.lineTo(x, y + dy * l);
    ctx.stroke();
  }
  ctx.fillStyle = PALE;
  ctx.shadowColor = BLUE;
  ctx.shadowBlur = 22;
  ctx.font = '700 150px system-ui, "Segoe UI", Arial, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('P', S / 2, S / 2 + 6);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

const smooth = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

/**
 * The empty bay, once it has been seen: a pale blue tile with the P on it. It stays until the car is on its way in, and
 * does not come back for the way out.
 */
function BayMark({ stage, runtime }: { stage: ParkStage; runtime: Runtime }) {
  const bay = stage.bays.find((b) => b.target)!.rect;
  const fill = React.useRef<THREE.MeshBasicMaterial>(null);
  const glyph = React.useRef<THREE.MeshBasicMaterial>(null);
  const root = React.useRef<THREE.Group>(null);
  const map = React.useMemo(() => pTexture(), []);
  React.useEffect(() => () => map.dispose(), [map]);
  const found = stage.search?.found ?? 0;
  useFrame(() => {
    const t = techClock.t;
    const stop = techClock.snapshot().stops[0] ?? Infinity;
    const car = runtime.sample(t);
    // in: when the bay has been seen; out: as the car backs toward it, and for good once it has parked
    const d = Math.hypot(car.x - bay.x, car.y - bay.y);
    const a = (stage.search ? smooth(found, found + 0.5, t) : 1) * smooth(2.6, 4.4, d) * (t < stop - 1e-3 ? 1 : 0);
    if (root.current) root.current.visible = a > 0.01;
    const pulse = 0.85 + 0.15 * Math.sin(t * 5);
    if (fill.current) fill.current.opacity = 0.28 * a * pulse;
    if (glyph.current) glyph.current.opacity = a * pulse;
  });
  const w = bay.width - 0.16;
  const l = bay.length - 0.16;
  return (
    <group ref={root} position={[bay.x, 0.03, -bay.y]} visible={false}>
      <mesh rotation-x={-Math.PI / 2} renderOrder={4}>
        <planeGeometry args={[w, l]} />
        <meshBasicMaterial ref={fill} color={BLUE} transparent opacity={0} depthWrite={false} toneMapped={false} />
      </mesh>
      {/* the glyph, near the bay's mouth where it is read from the lane */}
      <mesh rotation-x={-Math.PI / 2} position={[0, 0.004, -(l / 2 - 1.7)]} renderOrder={5}>
        <planeGeometry args={[1.9, 1.9]} />
        <meshBasicMaterial ref={glyph} map={map} transparent opacity={0} depthWrite={false} toneMapped={false} />
      </mesh>
    </group>
  );
}

/** A parked car the car has passed: white corner marks on the floor round it. */
function Bracketed({ n, stage, runtime }: { n: Pick<ParkNeighbour, 'rect'>; stage: ParkStage; runtime: Runtime }) {
  const rect: Rect = n.rect;
  const root = React.useRef<THREE.LineSegments>(null);
  const geo = React.useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(cornerBrackets(rect.length + 0.3, rect.width + 0.3, 0.8), 3));
    return g;
  }, [rect.length, rect.width]);
  React.useEffect(() => () => geo.dispose(), [geo]);
  useFrame(() => {
    const m = root.current;
    if (!m) return;
    // seen once the nose is within reach of it (the side sensors are in the front half of the car)
    const car = runtime.sample(techClock.t);
    const seen = stage.search ? car.x + runtime.body.front + 1.5 >= rect.x - 0.5 : true;
    m.visible = seen;
    if (seen) (m.material as THREE.LineBasicMaterial).opacity = 0.55 + 0.1 * Math.sin(techClock.t * 3 + rect.x);
  });
  return (
    <lineSegments ref={root} geometry={geo} position={[rect.x, 0.04, -rect.y]} rotation-y={rect.yaw} renderOrder={7} visible={false}>
      <lineBasicMaterial color="#ffffff" transparent opacity={0.55} depthWrite={false} toneMapped={false} />
    </lineSegments>
  );
}
