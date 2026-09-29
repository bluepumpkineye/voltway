'use client';

import React from 'react';
import * as THREE from 'three';
import { Canvas, useFrame, useThree, useLoader } from '@react-three/fiber';
import {
  OrbitControls, ContactShadows, Html, AdaptiveDpr, Preload, useGLTF,
} from '@react-three/drei';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { HDRLoader } from 'three/examples/jsm/loaders/HDRLoader.js';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore, type CameraMode } from '@/store/vehicle-store';
import { CarModel, CabinModel, DRACO_PATH } from './CarModel';
import { OutsideWorld } from './OutsideWorld';

type V3 = [number, number, number];
type Shot = { pos: V3; target: V3 };
/** A locked camera, for the pipeline's capture route (no controls, no easing). */
export type FixedShot = Shot & { fov: number };

/** Where the camera sits and looks, per mode. Distances are in metres. */
const SHOTS: Record<Exclude<CameraMode, 'interior'>, Shot> = {
  exterior: { pos: [5.6, 1.9, 5.2], target: [0, 0.72, 0] },
  transition: { pos: [2.4, 1.5, 2.6], target: [0.3, 0.95, 0.2] },
};

/**
 * The seated shot. China is LHD, so the driver sits at -Z once Blender's +Y
 * maps to glTF -Z. The camera pivots on a point 15 cm ahead of the eye, so
 * dragging turns the head rather than swinging the eye across the cabin; the
 * look is ahead and a little down and inboard, toward wheel and screen.
 */
function interiorShot(vehicle: Vehicle): Shot {
  const [x, y, z] = vehicle.assets.driverEye ?? [-0.38, 0.42, 1.18];
  const pos: V3 = [x, z, -y];
  return { pos, target: [pos[0] + 0.142, pos[1] - 0.038, pos[2] + 0.031] };
}

export function VehicleViewer({
  vehicle,
  variant,
  className,
  fixedShot,
}: {
  vehicle: Vehicle;
  variant: Variant;
  className?: string;
  fixedShot?: FixedShot;
}) {
  const modelUrl = vehicle.assets.modelUrl;
  const { interiorModelUrl, interiorProbeUrl, outside } = vehicle.assets;
  const cameraMode = useVehicleStore((s) => s.cameraMode);
  const inside = cameraMode === 'interior';
  // the world around the car in the exterior view too, or only through the
  // cabin's glass (outside.exterior === false: the studio stays outside)
  const worldOutside = Boolean(outside && outside.exterior !== false);

  // Stream the cabin in behind the exterior, so going inside is instant.
  React.useEffect(() => {
    if (interiorModelUrl) useGLTF.preload(interiorModelUrl, DRACO_PATH);
    if (interiorProbeUrl) useLoader.preload(HDRLoader, interiorProbeUrl);
  }, [interiorModelUrl, interiorProbeUrl]);

  if (!modelUrl) {
    return (
      <div className={className}>
        <NoModel vehicle={vehicle} />
      </div>
    );
  }

  return (
    <div className={className}>
      <Canvas
        shadows
        dpr={[1, 2]}
        gl={{
          antialias: true,
          // Neutral, not ACES: it is the Khronos PBR Neutral curve the Blender
          // renders use, so the web view and the lookdev renders agree. ACES
          // shifts saturated yellow toward orange and crushes it in shadow.
          toneMapping: THREE.NeutralToneMapping,
          toneMappingExposure: 0.92,
        }}
        camera={{ fov: 42, near: 0.02, far: 180, position: SHOTS.exterior.pos }}
        onCreated={({ gl }) => {
          // Clear alpha 0, not the default 1: ContactShadows renders its depth
          // pass with the renderer's clear colour, and an opaque clear left its
          // whole 13 m square dark - invisible on the black studio, a dark
          // slab on a sunlit plaza. The page behind the canvas is as dark.
          gl.setClearColor('#07080a', 0);
        }}
      >
        <AdaptiveDpr pixelated />
        {process.env.NODE_ENV !== 'production' && <DebugHandle />}
        {fixedShot ? <LockedCamera shot={fixedShot} /> : <Rig interior={interiorShot(vehicle)} />}
        {!worldOutside && <StudioEnvironment intensity={1.05} inside={inside} />}

        <React.Suspense fallback={<Loading />}>
          {outside && (
            <OutsideWorld
              world={outside}
              inside={inside}
              eye={interiorShot(vehicle).pos}
              cabinOnly={!worldOutside}
            />
          )}
          {!worldOutside && <StudioLights inside={inside} />}

          <CarModel vehicle={vehicle} variant={variant} url={modelUrl} />

          {cameraMode === 'exterior' && (
            <ContactShadows
              position={[0, 0.002, 0]}
              opacity={0.62}
              scale={13}
              blur={2.4}
              far={3.2}
              resolution={1024}
            />
          )}
          <Preload all />
        </React.Suspense>

        {/* its own boundary: the cabin streaming in never blanks the car */}
        {interiorModelUrl && cameraMode !== 'exterior' && (
          <React.Suspense fallback={null}>
            <CabinModel
              vehicle={vehicle}
              variant={variant}
              url={interiorModelUrl}
              probeUrl={interiorProbeUrl}
            />
          </React.Suspense>
        )}

        {!fixedShot && (
          <OrbitControls
            makeDefault
            enablePan={false}
            enableDamping
            dampingFactor={0.075}
            minDistance={inside ? 0.05 : 3.4}
            maxDistance={inside ? 0.3 : 11}
            // never let the camera go under the floor
            maxPolarAngle={inside ? Math.PI * 0.74 : Math.PI * 0.495}
            minPolarAngle={inside ? Math.PI * 0.2 : 0.12}
            rotateSpeed={inside ? -0.32 : 0.55}
          />
        )}
      </Canvas>
    </div>
  );
}

/**
 * The studio, for cars without an outside world (`assets.outside`, see
 * OutsideWorld) or whose world is only seen from the cabin (`exterior:
 * false`, where OutsideWorld takes over once the camera is inside):
 * image-based lighting without a network round trip.
 *
 * drei's `Environment preset` pulls an HDRI from a remote CDN, which stalls the
 * whole Suspense boundary when that host is slow or blocked. RoomEnvironment
 * ships inside three and is generated on the GPU, so the car is always lit.
 * From inside, the windows look out on a dark gradient.
 */
function StudioEnvironment({ intensity = 1, inside }: { intensity?: number; inside: boolean }) {
  const { scene, gl } = useThree();
  // made and disposed in one effect: a GPU-only render target memo'd and then
  // disposed by a StrictMode effect cleanup comes back empty (OutsideWorld)
  const [env, setEnv] = React.useState<THREE.WebGLRenderTarget | null>(null);
  React.useEffect(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    const rt = pmrem.fromScene(new RoomEnvironment(), 0.04);
    pmrem.dispose();
    setEnv(rt);
    return () => rt.dispose();
  }, [gl]);

  // From inside, the studio outside is dark (the sky below), so the bodywork
  // seen through the glass - hood, mirrors - is lit down to match it. The
  // cabin has its own probe envMap, which scene.environmentIntensity skips.
  React.useEffect(() => {
    scene.environment = env?.texture ?? null;
    scene.environmentIntensity = inside ? intensity * 0.35 : intensity;
    return () => {
      scene.environment = null;
    };
  }, [scene, env, intensity, inside]);

  // the press render's dark view out (sRGB ~20/22/29 through the windscreen)
  const sky = React.useMemo(() => {
    const c = document.createElement('canvas');
    c.width = 4;
    c.height = 256;
    const g = c.getContext('2d')!;
    const grd = g.createLinearGradient(0, 0, 0, 256);
    grd.addColorStop(0, 'rgb(44,48,58)');
    grd.addColorStop(0.5, 'rgb(24,27,34)');
    grd.addColorStop(1, 'rgb(13,14,17)');
    g.fillStyle = grd;
    g.fillRect(0, 0, 4, 256);
    const t = new THREE.CanvasTexture(c);
    t.mapping = THREE.EquirectangularReflectionMapping;
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  }, []);
  React.useEffect(() => () => sky.dispose(), [sky]);

  React.useEffect(() => {
    scene.background = inside ? sky : null;
    scene.backgroundBlurriness = 0;
    scene.backgroundIntensity = 1;
    return () => {
      scene.background = null;
    };
  }, [scene, sky, inside]);
  return null;
}

/**
 * The studio's direct lights (cars without an outside world). The baked cabin
 * ignores them; from inside they only light the bodywork seen through the
 * glass, dimmed to the dark studio.
 */
function StudioLights({ inside }: { inside: boolean }) {
  return (
    <>
      <hemisphereLight args={['#cfd8e6', '#0a0c10', inside ? 0.15 : 0.4]} />
      <directionalLight
        position={[5.5, 7.5, 4.2]}
        intensity={inside ? 0.9 : 2.4}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-camera-left={-6}
        shadow-camera-right={6}
        shadow-camera-top={6}
        shadow-camera-bottom={-6}
      />
      <directionalLight position={[-6, 3.5, -4]} intensity={inside ? 0.3 : 0.75} color="#9fb6d6" />
      {/* rim light from behind, so the shoulder crease and shut lines read */}
      <directionalLight position={[-3.5, 2.2, 6.5]} intensity={inside ? 0.4 : 1.05} color="#ffe9cf" />
    </>
  );
}

/** Dev only: window.__viewer = { scene, camera, gl, controls } for inspection. */
function DebugHandle() {
  const state = useThree();
  React.useEffect(() => {
    (window as unknown as { __viewer?: unknown }).__viewer = state;
  }, [state]);
  return null;
}

/** Holds the camera on a fixed shot (the capture route's matched cameras). */
function LockedCamera({ shot }: { shot: FixedShot }) {
  const { camera } = useThree() as { camera: THREE.PerspectiveCamera };
  React.useLayoutEffect(() => {
    camera.position.set(...shot.pos);
    camera.up.set(0, 1, 0);
    camera.lookAt(...shot.target);
    camera.fov = shot.fov;
    camera.updateProjectionMatrix();
  }, [camera, shot]);
  return null;
}

/** Eases the camera between shots instead of cutting. */
function Rig({ interior }: { interior: Shot }) {
  const cameraMode = useVehicleStore((s) => s.cameraMode);
  const { camera, controls } = useThree() as {
    camera: THREE.PerspectiveCamera;
    controls: OrbitControlsImpl | null;
  };

  const goal = React.useRef({
    pos: new THREE.Vector3(...SHOTS.exterior.pos),
    target: new THREE.Vector3(...SHOTS.exterior.target),
  });
  const settling = React.useRef(false);

  React.useEffect(() => {
    const shot = cameraMode === 'interior' ? interior : SHOTS[cameraMode];
    goal.current.pos.set(...shot.pos);
    goal.current.target.set(...shot.target);
    settling.current = true;
    camera.fov = cameraMode === 'interior' ? 64 : 42;
    camera.updateProjectionMatrix();
    // interior is set from the vehicle data each render; only react to changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cameraMode, camera, interior.pos[0], interior.pos[1], interior.pos[2]]);

  useFrame((_, dt) => {
    if (!settling.current || !controls) return;
    const k = 1 - Math.pow(0.0016, dt); // frame-rate independent easing
    camera.position.lerp(goal.current.pos, k);
    controls.target.lerp(goal.current.target, k);
    controls.update();
    if (
      camera.position.distanceTo(goal.current.pos) < 0.004 &&
      controls.target.distanceTo(goal.current.target) < 0.004
    ) {
      settling.current = false;
    }
  });

  return null;
}

function Loading() {
  return (
    <Html center>
      <div className="flex flex-col items-center gap-3">
        <div className="h-[3px] w-40 overflow-hidden rounded-full bg-ink-600">
          <div className="h-full w-1/3 rounded-full bg-ember-500 animate-sweep" />
        </div>
        <span className="text-[12px] uppercase tracking-[0.18em] text-ink-400">
          Loading model
        </span>
      </div>
    </Html>
  );
}

function NoModel({ vehicle }: { vehicle: Vehicle }) {
  return (
    <div className="grid-bg flex h-full w-full flex-col items-center justify-center gap-4 rounded-2xl border hairline bg-ink-850 p-10 text-center">
      <div
        className="flex h-16 w-16 items-center justify-center rounded-2xl text-2xl font-semibold"
        style={{ background: `${vehicle.cockpit.accentColor}1f`, color: vehicle.cockpit.accentColor }}
      >
        {vehicle.brand.charAt(0)}
      </div>
      <div>
        <h3 className="text-lg font-medium text-ink-100">3D model not built yet</h3>
        <p className="mx-auto mt-1.5 max-w-sm text-[13px] leading-relaxed text-ink-400">
          The {vehicle.brand} {vehicle.model} is in the database with full specifications and
          sources. Its cockpit has not been reconstructed yet — the Xiaomi SU7 Ultra is the
          one you can sit inside today.
        </p>
      </div>
    </div>
  );
}
