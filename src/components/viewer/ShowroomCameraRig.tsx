'use client';

import React from 'react';
import * as THREE from 'three';
import { CameraControls, CameraControlsImpl, useGLTF } from '@react-three/drei';
import { useFrame, useThree } from '@react-three/fiber';
import type { Vehicle } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { resolveAnchor, type CarFrame, type V3 } from '@/lib/showroom/anchors';
import { DRACO_PATH } from './CarModel';
import { motionOk } from './configurator';

/**
 * What the showroom needs from the loaded exterior: how far along the car it
 * extends and where the front-left wheel is (the `*_Wheels` node's origin is
 * that wheel's centre). Measured, not assumed, so a car whose origin is not at
 * its centre still frames correctly.
 */
export function useCarFrame(vehicle: Vehicle): CarFrame {
  const { scene } = useGLTF(vehicle.assets.modelUrl!, DRACO_PATH);
  return React.useMemo(() => {
    scene.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(scene);
    let wheelFL: V3 | undefined;
    scene.traverse((o) => {
      if (wheelFL || !o.name.toLowerCase().endsWith('_wheels')) return;
      const p = o.getWorldPosition(new THREE.Vector3());
      wheelFL = [p.x, p.y, p.z];
    });
    if (process.env.NODE_ENV !== 'production') {
      const built = box.max.x - box.min.x;
      const published = vehicle.dimensions.lengthMm / 1000;
      if (Math.abs(built - published) / published > 0.015) {
        console.warn(`[showroom] ${vehicle.slug}: model is ${built.toFixed(3)} m long, published ${published} m`);
      }
    }
    return { xMin: box.min.x, xMax: box.max.x, wheelFL };
  }, [scene, vehicle]);
}

/**
 * Flies the camera between the showroom's anchors (src/lib/showroom/anchors).
 *
 * The distance and angle limits belong to the pose the camera is in, so they
 * are relaxed for the flight and set once it lands: the cabin's 0.3 m cap
 * would otherwise snap the camera to the seat the instant it was applied.
 * Field of view eases separately. Resizing re-fits the pose only if the
 * visitor has not moved the camera since it landed.
 */
export function ShowroomCameraRig({ vehicle }: { vehicle: Vehicle }) {
  const controls = React.useRef<CameraControlsImpl>(null);
  const anchorId = useVehicleStore((s) => s.anchorId);
  const { camera, size, invalidate } = useThree();
  const frame = useCarFrame(vehicle);
  const aspect = Math.round((size.width / Math.max(size.height, 1)) * 10) / 10;
  const pose = React.useMemo(
    () => resolveAnchor(anchorId, vehicle, frame, aspect),
    [anchorId, vehicle, frame, aspect],
  );

  const fovGoal = React.useRef(pose.fov);
  const liftGoal = React.useRef(pose.liftPx);
  const lift = React.useRef(pose.liftPx);
  const shown = React.useRef({ fov: NaN, lift: NaN, w: 0, h: 0 });
  const flight = React.useRef(0);
  const first = React.useRef(true);
  const moved = React.useRef(false);
  const lastId = React.useRef(pose.id);

  // buttons: drag orbits, wheel and pinch zoom, nothing pans the car off-centre
  React.useEffect(() => {
    const c = controls.current;
    if (!c) return;
    const A = CameraControlsImpl.ACTION;
    c.mouseButtons.left = A.ROTATE;
    c.mouseButtons.right = A.NONE;
    c.mouseButtons.middle = A.NONE;
    c.mouseButtons.wheel = A.DOLLY;
    c.touches.one = A.TOUCH_ROTATE;
    c.touches.two = A.TOUCH_DOLLY;
    c.touches.three = A.NONE;
    c.draggingSmoothTime = 0.08;
    const onStart = () => {
      moved.current = true;
    };
    c.addEventListener('controlstart', onStart);
    return () => c.removeEventListener('controlstart', onStart);
  }, []);

  React.useEffect(() => {
    const c = controls.current;
    if (!c) return;
    const changed = lastId.current !== pose.id;
    lastId.current = pose.id;
    // a resize only changes the fit: leave a camera the visitor has moved alone
    if (!first.current && !changed && moved.current) return;

    c.azimuthRotateSpeed = pose.rotateSpeed;
    c.polarRotateSpeed = pose.rotateSpeed;
    fovGoal.current = pose.fov;
    liftGoal.current = pose.liftPx;
    moved.current = false;

    const lock = () => {
      c.minDistance = pose.minDistance;
      c.maxDistance = pose.maxDistance;
      c.minPolarAngle = pose.minPolar;
      c.maxPolarAngle = pose.maxPolar;
    };

    if (first.current) {
      first.current = false;
      const cam = camera as THREE.PerspectiveCamera;
      cam.fov = pose.fov;
      lift.current = pose.liftPx;
      void c.setLookAt(...pose.pos, ...pose.target, false);
      lock();
      invalidate();
      return;
    }

    // relax the limits for the flight, and set the pose's own on landing
    c.minDistance = 0.01;
    c.maxDistance = 200;
    c.minPolarAngle = 0;
    c.maxPolarAngle = Math.PI;
    c.smoothTime = motionOk() ? 0.55 : 0.01;
    const id = ++flight.current;
    void c.setLookAt(...pose.pos, ...pose.target, true).then(() => {
      if (id !== flight.current) return;
      c.smoothTime = 0.22;
      lock();
    });
    invalidate();
  }, [pose, camera, invalidate]);

  // The field of view and the lift ease toward the pose's own (64 and none in
  // the cabin; 20-30 and a lift outside). The projection is rebuilt only when
  // one of them, or the window, has changed.
  useFrame((_, dt) => {
    const cam = camera as THREE.PerspectiveCamera;
    const k = 1 - Math.exp(-dt * 5.5);
    let busy = false;
    const dFov = fovGoal.current - cam.fov;
    if (Math.abs(dFov) >= 0.02) {
      cam.fov += dFov * k;
      busy = true;
    } else cam.fov = fovGoal.current;
    const dLift = liftGoal.current - lift.current;
    if (Math.abs(dLift) >= 0.05) {
      lift.current += dLift * k;
      busy = true;
    } else lift.current = liftGoal.current;

    const s = shown.current;
    if (cam.fov !== s.fov || lift.current !== s.lift || size.width !== s.w || size.height !== s.h) {
      if (lift.current > 0.01) cam.setViewOffset(size.width, size.height, 0, lift.current, size.width, size.height);
      else cam.clearViewOffset();
      cam.updateProjectionMatrix();
      shown.current = { fov: cam.fov, lift: lift.current, w: size.width, h: size.height };
    }
    if (busy) invalidate();
  });

  return <CameraControls ref={controls} makeDefault />;
}
