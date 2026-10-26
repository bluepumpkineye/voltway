'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import type { SensorSpec, Vehicle } from '@/data/vehicles/schema';
import { techClock } from '@/lib/tech/clock';
import type { ParkNeighbour, Rect } from '@/lib/tech/park';
import { useRuntime, type Runtime } from '@/lib/tech/session';
import { CarCoverage, cornerBrackets } from './TechSensors';

export interface ActiveParkStage {
  kind: 'perpendicular' | 'parallel';
  mode: 'park' | 'crab' | 'e3park';
  bays: { rect: Rect; target: boolean }[];
  neighbours: { rect: Rect }[];
  search?: { end: number; found: number } | null;
}

/**
 * Replicated smart parking assist features:
 * - Active area screening (blue diagonal surround sweep beams & ultrasonic radar waves)
 * - Flashing "P" target bay mark and illuminated floor tile
 * - Neighbor car corner bracketing
 *
 * Supports both standard perpendicular parking assist and specialized maneuvers:
 * - Denza Z9 Intelligent Crab Walk (diagonal slide into kerbside bay)
 * - Denza Z9 e³ Parking (nose-in approach, pivot stop, and tail swing into parallel gap)
 */
export function TechParkAssist({ vehicle }: { vehicle: Vehicle }) {
  const runtime = useRuntime();
  const spec = vehicle.sensors;
  if (!runtime || !spec) return null;

  let activeStage: ActiveParkStage | null = null;

  if (runtime.stage?.bays?.some((b) => b.target)) {
    activeStage = {
      kind: 'perpendicular',
      mode: 'park',
      bays: runtime.stage.bays,
      neighbours: runtime.stage.neighbours,
      search: runtime.stage.search,
    };
  } else if (
    runtime.chassis?.stage &&
    (runtime.demoId === 'crab' || runtime.demoId === 'e3-parking')
  ) {
    const street = runtime.chassis.stage;
    const mode = runtime.demoId === 'crab' ? 'crab' : 'e3park';
    const targetBay = street.bays[0];
    if (targetBay) {
      // Adjacent parked cars on the same kerbside row
      const neighbours = street.cars.filter(
        (c) => Math.abs(c.rect.y - targetBay.y) < 1.6 && Math.abs(c.rect.x - targetBay.x) < 22,
      );
      activeStage = {
        kind: 'parallel',
        mode,
        bays: [{ rect: targetBay, target: true }],
        neighbours,
        search: null,
      };
    }
  }

  if (!activeStage) return null;
  return <Overlay vehicle={vehicle} spec={spec} stage={activeStage} runtime={runtime} />;
}

const BLUE = '#38a8ff';
const PALE = '#9bd8ff';

function Overlay({
  vehicle,
  spec,
  stage,
  runtime,
}: {
  vehicle: Vehicle;
  spec: SensorSpec;
  stage: ActiveParkStage;
  runtime: Runtime;
}) {
  return (
    <group>
      {/* The blue beams, ripples and camera dots move with the car */}
      <CarCoverage
        vehicle={vehicle}
        spec={spec}
        runtime={runtime}
        parts={['surround', 'ultrasonic', 'cameras']}
        surroundReach={stage.kind === 'parallel' ? 8.5 : 8}
      />
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
 * The empty bay, once it has been seen: a pale blue tile with the P on it.
 * Adapts to both perpendicular lots and parallel street spaces.
 */
function BayMark({ stage, runtime }: { stage: ActiveParkStage; runtime: Runtime }) {
  const bay = stage.bays.find((b) => b.target)!.rect;
  const isParallel = stage.kind === 'parallel';
  const fill = React.useRef<THREE.MeshBasicMaterial>(null);
  const glyph = React.useRef<THREE.MeshBasicMaterial>(null);
  const root = React.useRef<THREE.Group>(null);
  const map = React.useMemo(() => pTexture(), []);
  React.useEffect(() => () => map.dispose(), [map]);
  const found = stage.search?.found ?? 0;

  useFrame(() => {
    const t = techClock.t;
    const dur = techClock.duration;
    let a = 0;

    if (stage.mode === 'crab') {
      // Crab walk: bay target is locked right at start; pulses actively as car slides diagonally,
      // and smoothly settles as car reaches curb
      const inFactor = smooth(0, 0.4, t);
      const outFactor = smooth(dur, Math.max(0, dur - 0.7), t);
      a = inFactor * outFactor;
    } else if (stage.mode === 'e3park') {
      // e3 parking: visible during approach and nose-in stop, pulses through pivot, settles at finish
      const inFactor = smooth(0, 0.5, t);
      const outFactor = smooth(dur, Math.max(0, dur - 0.7), t);
      a = inFactor * outFactor;
    } else {
      // Standard perpendicular parking
      const stop = techClock.snapshot().stops[0] ?? Infinity;
      const car = runtime.sample(t);
      const d = Math.hypot(car.x - bay.x, car.y - bay.y);
      a = (stage.search ? smooth(found, found + 0.5, t) : 1) * smooth(2.6, 4.4, d) * (t < stop - 1e-3 ? 1 : 0);
    }

    if (root.current) root.current.visible = a > 0.01;
    const pulse = 0.85 + 0.15 * Math.sin(t * 5);
    if (fill.current) fill.current.opacity = 0.28 * a * pulse;
    if (glyph.current) glyph.current.opacity = a * pulse;
  });

  // Parallel bays are oriented along the curb (length along X, width along Y)
  // Perpendicular bays are oriented across the driving lane (width along X, length along Y)
  const geomArgs: [number, number] = isParallel
    ? [Math.max(1, bay.length - 0.2), Math.max(1, bay.width - 0.2)]
    : [Math.max(1, bay.width - 0.16), Math.max(1, bay.length - 0.16)];

  // For parallel bays, place the flashing "P" right at the centre of the bay;
  // for perpendicular bays, near the mouth facing the lane
  const glyphPos: [number, number, number] = isParallel
    ? [0, 0.004, 0]
    : [0, 0.004, -(bay.length / 2 - 1.7)];

  return (
    <group ref={root} position={[bay.x, 0.03, -bay.y]} visible={false}>
      <mesh rotation-x={-Math.PI / 2} renderOrder={4}>
        <planeGeometry args={geomArgs} />
        <meshBasicMaterial ref={fill} color={BLUE} transparent opacity={0} depthWrite={false} toneMapped={false} />
      </mesh>
      {/* the glyph */}
      <mesh rotation-x={-Math.PI / 2} position={glyphPos} renderOrder={5}>
        <planeGeometry args={[1.9, 1.9]} />
        <meshBasicMaterial ref={glyph} map={map} transparent opacity={0} depthWrite={false} toneMapped={false} />
      </mesh>
    </group>
  );
}

/** A parked car: white corner marks on the floor round it when detected. */
function Bracketed({
  n,
  stage,
  runtime,
}: {
  n: Pick<ParkNeighbour, 'rect'>;
  stage: ActiveParkStage;
  runtime: Runtime;
}) {
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
    const car = runtime.sample(techClock.t);
    let seen = true;
    if (stage.search) {
      seen = car.x + runtime.body.front + 1.5 >= rect.x - 0.5;
    } else if (stage.kind === 'parallel') {
      const d = Math.hypot(car.x - rect.x, car.y - rect.y);
      seen = d <= 9.0;
    }
    m.visible = seen;
    if (seen) (m.material as THREE.LineBasicMaterial).opacity = 0.55 + 0.1 * Math.sin(techClock.t * 3 + rect.x);
  });

  return (
    <lineSegments ref={root} geometry={geo} position={[rect.x, 0.04, -rect.y]} rotation-y={rect.yaw} renderOrder={7} visible={false}>
      <lineBasicMaterial color="#ffffff" transparent opacity={0.55} depthWrite={false} toneMapped={false} />
    </lineSegments>
  );
}
