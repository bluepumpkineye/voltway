'use client';

import React from 'react';
import * as THREE from 'three';
import { Canvas, useLoader, useThree } from '@react-three/fiber';
import { ContactShadows, Html, Preload, useGLTF } from '@react-three/drei';
import { HDRLoader } from 'three/examples/jsm/loaders/HDRLoader.js';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { CarModel, CabinModel, DRACO_PATH } from './CarModel';
import { OpeningsDriver, useCabinWanted } from './Openings';
import { OutsideWorld } from './OutsideWorld';
import { GroundShadow, StudioShowroom, STUDIO_WHITE } from './StudioShowroom';
import { ShowroomCameraRig, useCarFrame } from './ShowroomCameraRig';
import { DimensionRulers } from './DimensionRulers';

/**
 * The showroom's viewer (/showroom/[slug]): the same car and cabin as the
 * vehicle page, in a white studio by default or in the city world the cabin was
 * baked under, with a camera that flies between named poses.
 *
 * It renders on demand: an idle showroom draws nothing. Every store change
 * asks for a frame, the tweens and the camera ask while they move, and the
 * invalidator below covers asynchronous work (HDR decode, PMREM, shader
 * compile) that lands without telling react-three-fiber.
 */

type V3 = [number, number, number];

export function ShowroomViewer({
  vehicle,
  variant,
  className,
}: {
  vehicle: Vehicle;
  variant: Variant;
  className?: string;
}) {
  const modelUrl = vehicle.assets.modelUrl!;
  const { interiorModelUrl, interiorProbeUrl } = vehicle.assets;
  const cabinWanted = useCabinWanted();
  const reflections = useMirrorTier();

  // stream the cabin in behind the exterior, so sitting inside is instant
  React.useEffect(() => {
    if (interiorModelUrl) useGLTF.preload(interiorModelUrl, DRACO_PATH);
    if (interiorProbeUrl) useLoader.preload(HDRLoader, interiorProbeUrl);
  }, [interiorModelUrl, interiorProbeUrl]);

  return (
    <div className={className}>
      <Canvas
        frameloop="demand"
        shadows
        dpr={[1, 2]}
        gl={{
          antialias: true,
          // the Khronos PBR Neutral curve the Blender renders use
          toneMapping: THREE.NeutralToneMapping,
          toneMappingExposure: 0.92,
        }}
        camera={{ fov: 30, near: 0.02, far: 180, position: [9, 3, -8] }}
        onCreated={({ gl }) => {
          // alpha 0, and the studio's white: the mirror shows the clear colour
          // where nothing is, and ContactShadows draws with it
          gl.setClearColor(STUDIO_WHITE, 0);
        }}
      >
        <Invalidator />
        <OpeningsDriver vehicle={vehicle} />
        {process.env.NODE_ENV !== 'production' && <DebugHandle />}
        <React.Suspense fallback={<Loading />}>
          <Stage vehicle={vehicle} variant={variant} url={modelUrl} reflections={reflections} />
          <Preload all />
        </React.Suspense>
        {/* its own boundary: the cabin streaming in never blanks the car */}
        {interiorModelUrl && cabinWanted && (
          <React.Suspense fallback={null}>
            <CabinModel
              vehicle={vehicle}
              variant={variant}
              url={interiorModelUrl}
              probeUrl={interiorProbeUrl}
            />
          </React.Suspense>
        )}
      </Canvas>
    </div>
  );
}

/** Everything that needs the exterior to have loaded. */
function Stage({
  vehicle,
  variant,
  url,
  reflections,
}: {
  vehicle: Vehicle;
  variant: Variant;
  url: string;
  reflections: boolean;
}) {
  const sceneKind = useVehicleStore((s) => s.sceneKind);
  const cameraMode = useVehicleStore((s) => s.cameraMode);
  const inside = cameraMode === 'interior';
  const frame = useCarFrame(vehicle);
  const outside = vehicle.assets.outside;
  const studioShadow = vehicle.assets.studioShadow;
  const city = sceneKind === 'city' && Boolean(outside);
  // the seat's eye point, from the build's axes to the viewer's (x, z, -y)
  const eye = React.useMemo<V3>(() => {
    const e = vehicle.assets.driverEye ?? [-0.38, 0.42, 1.18];
    return [e[0], e[2], -e[1]];
  }, [vehicle.assets.driverEye]);

  return (
    <>
      <ShowroomCameraRig vehicle={vehicle} />
      {city && outside ? (
        <OutsideWorld world={outside} inside={inside} eye={eye} />
      ) : (
        <StudioShowroom reflections={reflections} inside={inside} />
      )}
      <CarModel vehicle={vehicle} variant={variant} url={url} />
      {/* the studio lays the car's baked shadow under it; the city (and a car
          without one) projects a contact shadow from the car */}
      {!inside && !city && studioShadow ? (
        <GroundShadow shadow={studioShadow} />
      ) : (
        !inside && (
          <ContactShadows
            key={city ? 'city' : 'studio'}
            position={[0, 0.002, 0]}
            opacity={city ? 0.62 : 0.5}
            scale={14}
            blur={city ? 2.4 : 2.8}
            far={3.2}
            resolution={1024}
            frames={1}
          />
        )
      )}
      <DimensionRulers vehicle={vehicle} frame={frame} />
    </>
  );
}

/** Dev only: window.__viewer = the r3f state, for inspecting frames and draw calls. */
function DebugHandle() {
  const state = useThree();
  React.useEffect(() => {
    const w = window as unknown as { __viewer?: unknown; __store?: unknown };
    w.__viewer = state;
    w.__store = useVehicleStore;
  }, [state]);
  return null;
}

/**
 * Asks for frames on demand: on every store change (paint, anchor, HMI taps),
 * and for a few seconds after mount and after each scene change, because HDR
 * decoding, PMREM and shader compilation finish without invalidating.
 */
function Invalidator() {
  const invalidate = useThree((s) => s.invalidate);
  const sceneKind = useVehicleStore((s) => s.sceneKind);

  React.useEffect(() => useVehicleStore.subscribe(() => invalidate()), [invalidate]);

  React.useEffect(() => {
    let n = 0;
    const id = window.setInterval(() => {
      invalidate();
      if (++n >= 30) window.clearInterval(id);
    }, 100);
    return () => window.clearInterval(id);
  }, [sceneKind, invalidate]);

  return null;
}

/**
 * The floor mirror renders the whole car a second time, so it is for screens
 * that can afford it: a wide window with a mouse. Phones and tablets get the
 * plain floor.
 */
function useMirrorTier() {
  const [on, setOn] = React.useState(
    () => typeof window !== 'undefined' && window.matchMedia('(min-width: 900px) and (pointer: fine)').matches,
  );
  React.useEffect(() => {
    const q = window.matchMedia('(min-width: 900px) and (pointer: fine)');
    const f = () => setOn(q.matches);
    q.addEventListener('change', f);
    return () => q.removeEventListener('change', f);
  }, []);
  return on;
}

function Loading() {
  return (
    <Html center>
      <div className="flex flex-col items-center gap-3">
        <div className="h-[3px] w-40 overflow-hidden rounded-full bg-black/10">
          <div className="h-full w-1/3 rounded-full bg-neutral-800 animate-sweep" />
        </div>
        <span className="text-[11px] uppercase tracking-[0.18em] text-neutral-500">Loading model</span>
      </div>
    </Html>
  );
}
