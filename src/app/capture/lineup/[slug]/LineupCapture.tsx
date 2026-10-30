'use client';

import React from 'react';
import * as THREE from 'three';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Environment, Lightformer } from '@react-three/drei';
import type { Vehicle } from '@/data/vehicles/schema';
import { flagshipVariant } from '@/data/vehicles/schema';
import { STUDIO_GAIN, STUDIO_RIG, STUDIO_VOID } from '@/data/studio/rig';
import { CabinModel, CarModel } from '@/components/viewer/CarModel';
import { useVehicleStore } from '@/store/vehicle-store';

const FOV = 18;
const D2R = Math.PI / 180;

/** The car, alone, on a transparent background, lit by the showroom's own rig, from a camera that fits it into the window. */
export function LineupCapture({ vehicle }: { vehicle: Vehicle }) {
  const reset = useVehicleStore((s) => s.reset);
  const setPaint = useVehicleStore((s) => s.setPaint);
  const [q, setQ] = React.useState<{ yaw: number; pitch: number; paint: string | null; fill: number } | null>(null);
  const [size, setSize] = React.useState<{ w: number; h: number }>({ w: 1500, h: 900 });

  React.useEffect(() => {
    reset(flagshipVariant(vehicle).id, vehicle.cockpit.defaultTheme);
    const p = new URLSearchParams(window.location.search);
    const paint = p.get('paint');
    if (paint) setPaint(paint);
    setQ({ yaw: Number(p.get('yaw') ?? 0), pitch: Number(p.get('pitch') ?? 8), paint, fill: Number(p.get('fill') ?? 0.86) });
    setSize({ w: window.innerWidth, h: window.innerHeight });
  }, [vehicle, reset, setPaint]);

  const modelUrl = vehicle.assets.modelUrl;
  if (!q || !modelUrl) return null;
  const variant = flagshipVariant(vehicle);
  const { interiorModelUrl, interiorProbeUrl } = vehicle.assets;

  // where the camera stands: round the car by `yaw`, up by `pitch`, and as far off as it takes for the car's box (a rectangle of the car's
  // length, width and height) to fill `fill` of the window's width and no more than 0.94 of its height: found by trial, since a car
  // seen nose-on has its nose much nearer the lens than its middle
  const d = vehicle.dimensions;
  const L = d.lengthMm / 1000;
  const W = d.widthMm / 1000;
  const H = d.heightMm / 1000;
  const a = q.yaw * D2R;
  const el = q.pitch * D2R;
  const target: [number, number, number] = [0, H * 0.4, 0];
  const cam = new THREE.PerspectiveCamera(FOV, size.w / size.h, 0.1, 200);
  const corners: THREE.Vector3[] = [];
  for (const x of [-L / 2, L / 2]) for (const y of [0, H]) for (const z of [-W / 2, W / 2]) corners.push(new THREE.Vector3(x, y, z));
  const place = (dist: number) => {
    cam.position.set(target[0] + dist * Math.cos(a) * Math.cos(el), target[1] + dist * Math.sin(el), target[2] + dist * Math.sin(a) * Math.cos(el));
    cam.lookAt(...target);
    cam.updateMatrixWorld();
    cam.updateProjectionMatrix();
    let ex = 0;
    let ey = 0;
    for (const c of corners) {
      const p = c.clone().project(cam);
      ex = Math.max(ex, Math.abs(p.x));
      ey = Math.max(ey, Math.abs(p.y));
    }
    return { ex, ey };
  };
  let lo = L * 0.5;
  let hi = 60;
  for (let i = 0; i < 40; i++) {
    const mid = (lo + hi) / 2;
    const { ex, ey } = place(mid);
    // too close while the box is wider or taller than allowed
    if (ex > q.fill || ey > 0.94) lo = mid;
    else hi = mid;
  }
  const dist = hi;
  place(dist);
  const pos: [number, number, number] = [cam.position.x, cam.position.y, cam.position.z];

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 9999, background: 'transparent' }}>
      <style>{'html,body{background:transparent!important}nextjs-portal{display:none!important}'}</style>
      <Canvas
        dpr={1}
        gl={{ antialias: true, alpha: true, preserveDrawingBuffer: true, toneMapping: THREE.NeutralToneMapping, toneMappingExposure: 0.95 }}
        camera={{ fov: FOV, near: 0.1, far: 200, position: pos }}
        onCreated={({ gl }) => gl.setClearColor('#000000', 0)}
      >
        <Look target={target} />
        <Environment frames={1} resolution={256} environmentIntensity={STUDIO_GAIN}>
          <color attach="background" args={[STUDIO_VOID]} />
          {STUDIO_RIG.map((p) => (
            <Lightformer key={p.id} form={p.form} position={p.position} rotation={p.rotation} scale={p.size} intensity={p.intensity} color={p.color ?? '#ffffff'} />
          ))}
        </Environment>
        <React.Suspense fallback={null}>
          <CarModel vehicle={vehicle} variant={variant} url={modelUrl} />
        </React.Suspense>
        {/* the cabin shows through the glass once it is in, as in the showroom */}
        {interiorModelUrl && (
          <React.Suspense fallback={null}>
            <CabinModel vehicle={vehicle} variant={variant} url={interiorModelUrl} probeUrl={interiorProbeUrl} />
          </React.Suspense>
        )}
        <Ready hasCabin={Boolean(interiorModelUrl)} />
      </Canvas>
    </div>
  );
}

function Look({ target }: { target: [number, number, number] }) {
  const camera = useThree((s) => s.camera);
  React.useEffect(() => {
    camera.lookAt(...target);
    camera.updateProjectionMatrix();
  }, [camera, target]);
  return null;
}

/** Says (window.__lineupReady) when the car and its cabin have been drawn for a while, so that a headless browser can take the picture. */
function Ready({ hasCabin }: { hasCabin: boolean }) {
  const cabinReady = useVehicleStore((s) => s.cabinReady);
  const frames = React.useRef(0);
  useFrame(() => {
    // the car is in when something has been drawn; wait for the cabin as well, then a few frames for the textures
    if (hasCabin && !cabinReady) return;
    frames.current++;
    if (frames.current === 45) (window as unknown as { __lineupReady?: boolean }).__lineupReady = true;
  });
  return null;
}
