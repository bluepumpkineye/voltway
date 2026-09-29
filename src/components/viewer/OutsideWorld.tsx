'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useLoader, useThree } from '@react-three/fiber';
import { HDRLoader } from 'three/examples/jsm/loaders/HDRLoader.js';
import { GroundedSkybox } from 'three/examples/jsm/objects/GroundedSkybox.js';
import type { OutsideWorld as World } from '@/data/vehicles/schema';

type V3 = [number, number, number];

/** Within this distance of the seat (m) the camera is in the cabin's world. */
const CABIN_RADIUS = 1.2;

/**
 * The layer the dome and the shadow-only plane live on. Seen by the view
 * camera only: ContactShadows renders every layer-0 object into its depth
 * pass, and the dome's floor, sitting on y = 0, turned the whole 13 m
 * contact-shadow square dark.
 */
const BACKDROP_LAYER = 1;

/**
 * The world the car stands in: an HDRI (export_gltf.OUTSIDE) as ground,
 * backdrop and light, in both views.
 *
 * Outside, the photo is projected onto a ground dome (GroundedSkybox), so the
 * car stands on the plaza instead of floating over a panorama; the sun that
 * the light HDR clamps away comes back as a directional light, casting the
 * car's shadow on a shadow-only plane. Inside, the photo is an ordinary
 * background at infinity, as in the Cycles bake, fading in over the last
 * stretch to the seat.
 *
 * The two views turn the world differently (OutsideWorld.exteriorTurnDeg):
 * the cabin wants the skyline ahead and the sun behind; the exterior's default
 * camera wants the sun at its back. Which orientation applies is decided from
 * where the camera is, every frame, so the switch happens only once the
 * camera is inside the car.
 *
 * Both images are pre-tone-mapped where they are seen (an sRGB background and
 * the dome's material skip tone mapping), and the light HDR is linear.
 * Suspends until both have loaded, so the car never appears in a studio and
 * then jumps outdoors.
 *
 * cabinOnly (world.exterior === false): the world is only the view out of the
 * cabin. Outside the seat's radius this does nothing - no dome, no sun - and
 * the studio (VehicleViewer's StudioEnvironment) keeps the scene.
 */
export function OutsideWorld({
  world,
  inside,
  eye,
  cabinOnly = false,
}: {
  world: World;
  inside: boolean;
  eye: V3;
  cabinOnly?: boolean;
}) {
  const view = useLoader(THREE.TextureLoader, world.view);
  const hdr = useLoader(HDRLoader, world.light);
  const { scene, gl, camera } = useThree();

  // Made in an effect, not a memo: the prefiltered map lives only on the GPU,
  // and a memo'd one disposed by a (StrictMode) effect cleanup came back as
  // an empty texture - the car lit by the sun alone, its glass black.
  const [light, setLight] = React.useState<THREE.WebGLRenderTarget | null>(null);
  React.useEffect(() => {
    hdr.mapping = THREE.EquirectangularReflectionMapping;
    const pmrem = new THREE.PMREMGenerator(gl);
    const rt = pmrem.fromEquirectangular(hdr);
    pmrem.dispose();
    setLight(rt);
    return () => rt.dispose();
  }, [hdr, gl]);

  const turn = THREE.MathUtils.degToRad(world.exteriorTurnDeg);
  const { height, radius } = world.ground;
  const dome = React.useMemo(() => {
    view.colorSpace = THREE.SRGBColorSpace;
    view.mapping = THREE.EquirectangularReflectionMapping;
    const d = new GroundedSkybox(view, height, radius);
    d.position.y = height - 0.01;
    d.rotation.y = turn;
    d.renderOrder = -1;
    d.layers.set(BACKDROP_LAYER);
    (d.material as THREE.MeshBasicMaterial).toneMapped = false;
    return d;
  }, [view, height, radius, turn]);
  React.useEffect(() => {
    camera.layers.enable(BACKDROP_LAYER);
  }, [camera]);
  React.useEffect(
    () => () => {
      dome.geometry.dispose();
      (dome.material as THREE.Material).dispose();
    },
    [dome],
  );

  const sun = React.useRef<THREE.DirectionalLight>(null);
  const seat = React.useMemo(() => new THREE.Vector3(...eye), [eye[0], eye[1], eye[2]]); // eslint-disable-line react-hooks/exhaustive-deps
  const owned = React.useRef(false);

  useFrame(() => {
    const d = camera.position.distanceTo(seat);
    const cabin = inside && d < CABIN_RADIUS;
    dome.visible = !cabin && !cabinOnly;
    if (cabinOnly && !cabin) {
      // outside, the studio owns the scene; hand its orientation back once
      if (sun.current) sun.current.intensity = 0;
      if (owned.current) {
        scene.environmentRotation.set(0, 0, 0);
        owned.current = false;
      }
      return;
    }
    owned.current = true;
    scene.environment = light?.texture ?? null;
    scene.environmentIntensity = 1;
    scene.environmentRotation.set(0, cabin ? 0 : turn, 0);
    scene.background = cabin ? view : null;
    scene.backgroundIntensity = cabin ? THREE.MathUtils.smoothstep(CABIN_RADIUS - d, 0, 0.6) : 1;
    if (sun.current) sun.current.intensity = cabin ? 0 : world.sun.intensity;
  });
  React.useEffect(
    () => () => {
      // cabin only: clear the scene only if this world holds it. The studio
      // set it, and StrictMode's mount-unmount-mount in development wiped the
      // studio's environment - the car lit by direct light alone
      if (cabinOnly && !owned.current) return;
      scene.environment = null;
      scene.background = null;
      scene.environmentRotation.set(0, 0, 0);
    },
    [scene, cabinOnly],
  );

  const [x, y, z] = world.sun.direction;
  return (
    <>
      <primitive object={dome} />
      <directionalLight
        ref={sun}
        position={[x * 14, y * 14, z * 14]}
        color={world.sun.color}
        intensity={cabinOnly ? 0 : world.sun.intensity}
        castShadow={!cabinOnly}
        shadow-mapSize={[2048, 2048]}
        shadow-camera-left={-9}
        shadow-camera-right={9}
        shadow-camera-top={9}
        shadow-camera-bottom={-9}
        shadow-camera-near={1}
        shadow-camera-far={40}
        shadow-bias={-0.0004}
        shadow-normalBias={0.02}
      />
      {/* the car's sun shadow on the plaza: the ground itself is the photo */}
      {!inside && !cabinOnly && (
        <mesh
          rotation-x={-Math.PI / 2}
          position-y={0.001}
          receiveShadow
          ref={(m: THREE.Mesh | null) => m?.layers.set(BACKDROP_LAYER)}
        >
          <planeGeometry args={[40, 40]} />
          <shadowMaterial opacity={0.3} />
        </mesh>
      )}
    </>
  );
}
