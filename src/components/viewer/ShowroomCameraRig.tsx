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
 * extends and where the front-left wheel is (the origin of the `*_Wheels` node of a
 * car with one merged wheel node, or of its `*_Wheels_FL` node when the wheels are
 * one node per corner, is that wheel's centre). Measured, not assumed, so a car
 * whose origin is not at its centre still frames correctly.
 */
export function useCarFrame(vehicle: Vehicle): CarFrame {
  const { scene } = useGLTF(vehicle.assets.modelUrl!, DRACO_PATH);
  return React.useMemo(() => {
    scene.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(scene);
    let wheelFL: V3 | undefined;
    scene.traverse((o) => {
      const n = o.name.toLowerCase();
      if (wheelFL || !(n.endsWith('_wheels') || n.endsWith('_wheels_fl'))) return;
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

/** The pixels a pose lifts the picture by: its own, and what a device at the bottom of the window covers. */
const liftOf = (p: { liftPx: number; liftFrac?: number }, windowHeight: number) =>
  p.liftPx + (p.liftFrac ?? 0) * windowHeight;

/** The pixels a pose slides the picture to the left by, into the part of the window a device at the right leaves free. */
const shiftOf = (p: { shiftFrac?: number }, windowWidth: number) => (p.shiftFrac ?? 0) * windowWidth;

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
  // a control that asks for its pose again (Front, then Front once more) sends a camera the visitor has turned back to it
  const tick = useVehicleStore((s) => s.anchorTick);
  const { camera, size, invalidate } = useThree();
  const carFrame = useCarFrame(vehicle);
  // the floor a tech demo drives on: the wide shot keeps all of it in view
  const stage = useVehicleStore((s) => s.techStage);
  // what a device (the Tech tab's phone or car screen, the Dashboard tab's car screen) covers of the window:
  // every pose frames the car in the part that is left
  const inset = useVehicleStore((s) => s.deviceInset);
  const frame = React.useMemo(
    () => (stage ? { ...carFrame, inset, stage: { ...stage, inset } } : { ...carFrame, inset }),
    [carFrame, stage, inset],
  );
  const aspect = Math.round((size.width / Math.max(size.height, 1)) * 10) / 10;
  const pose = React.useMemo(
    () => resolveAnchor(anchorId, vehicle, frame, aspect),
    [anchorId, vehicle, frame, aspect],
  );

  // the pose and the window as they are now, for the frame loop and the landing
  const poseRef = React.useRef(pose);
  poseRef.current = pose;
  const viewport = React.useRef(size);
  viewport.current = size;
  const fovGoal = React.useRef(pose.fov);
  const lift = React.useRef(liftOf(pose, size.height));
  const shift = React.useRef(shiftOf(pose, size.width));
  const shown = React.useRef({ fov: NaN, lift: NaN, shift: NaN, w: 0, h: 0, near: NaN });
  const flight = React.useRef(0);
  const first = React.useRef(true);
  const moved = React.useRef(false);
  const lastId = React.useRef(pose.id);
  const lastTick = React.useRef(tick);
  const lastFloor = React.useRef('');

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

  // The Dashboard tab's Front and Rear follow the end of the car the visitor has turned the camera to, once
  // it comes to rest, so the chip that is lit is the end that is on screen.
  React.useEffect(() => {
    const c = controls.current;
    if (!c) return;
    const at = new THREE.Vector3();
    const onRest = () => {
      const s = useVehicleStore.getState();
      if (s.tab !== 'dashboard') return;
      c.getTarget(at);
      const end = c.camera.position.x - at.x >= 0 ? 'front' : 'rear';
      if (end !== s.lightsView) s.syncLightsView(end);
    };
    c.addEventListener('rest', onRest);
    return () => c.removeEventListener('rest', onRest);
  }, []);

  React.useEffect(() => {
    const c = controls.current;
    if (!c) return;
    // a tech demo with another floor to frame (its centre, size or preferred look) is a new pose even though the
    // anchor is still the wide shot: the visitor's own turns and zoom belonged to the last one
    const floor = stage ? [stage.cx, stage.cz, stage.radius, stage.camera?.az, stage.camera?.el].join() : '';
    const changed = lastId.current !== pose.id || lastTick.current !== tick || lastFloor.current !== floor;
    lastId.current = pose.id;
    lastTick.current = tick;
    lastFloor.current = floor;
    // a device that came or went moves the picture's lift and slide even where the camera is left alone
    invalidate();
    // a resize only changes the fit: leave a camera the visitor has moved alone
    if (!first.current && !changed && moved.current) return;

    c.azimuthRotateSpeed = pose.rotateSpeed;
    c.polarRotateSpeed = pose.rotateSpeed;
    fovGoal.current = pose.fov;
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
      lift.current = liftOf(pose, viewport.current.height);
      shift.current = shiftOf(pose, viewport.current.width);
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
  }, [pose, tick, stage, camera, invalidate]);

  // The field of view, the lift and the slide ease toward the pose's own (64 and
  // none in the cabin; 20-30, a lift, and a slide clear of a device outside). The
  // projection is rebuilt only when one of them, or the window, has changed.
  useFrame((_, dt) => {
    const cam = camera as THREE.PerspectiveCamera;
    const k = 1 - Math.exp(-dt * 5.5);
    let busy = false;
    const dFov = fovGoal.current - cam.fov;
    if (Math.abs(dFov) >= 0.02) {
      cam.fov += dFov * k;
      busy = true;
    } else cam.fov = fovGoal.current;
    // the goals come from the pose and the window as they are this frame: a visitor who has turned the car
    // still has it centred in the free part of the window when a device comes or goes
    const liftGoal = liftOf(poseRef.current, size.height);
    const dLift = liftGoal - lift.current;
    if (Math.abs(dLift) >= 0.05) {
      lift.current += dLift * k;
      busy = true;
    } else lift.current = liftGoal;
    const shiftGoal = shiftOf(poseRef.current, size.width);
    const dShift = shiftGoal - shift.current;
    if (Math.abs(dShift) >= 0.05) {
      shift.current += dShift * k;
      busy = true;
    } else shift.current = shiftGoal;

    // The near plane follows the distance: the cabin needs 2 cm, but the exterior's panels sit 3 mm over
    // their underlays, and a 24-bit depth buffer cannot tell them apart from 25 m with a near plane that close
    // (the Tech tab's wide shots stand that far back). One sixtieth of the distance, between 2 and 50 cm.
    const dist = controls.current?.distance ?? 10;
    const near = Math.min(0.5, Math.max(0.02, Math.round(dist / 0.6) / 100));

    const s = shown.current;
    if (
      cam.fov !== s.fov ||
      lift.current !== s.lift ||
      shift.current !== s.shift ||
      size.width !== s.w ||
      size.height !== s.h ||
      near !== s.near
    ) {
      cam.near = near;
      // a view offset moves the picture (up by the lift, left by the slide) without turning the camera:
      // the perspective and the orbit's centre are the car's
      if (lift.current > 0.01 || Math.abs(shift.current) > 0.01) {
        cam.setViewOffset(size.width, size.height, shift.current, lift.current, size.width, size.height);
      } else cam.clearViewOffset();
      cam.updateProjectionMatrix();
      shown.current = { fov: cam.fov, lift: lift.current, shift: shift.current, w: size.width, h: size.height, near };
    }
    if (busy) invalidate();
  });

  return <CameraControls ref={controls} makeDefault />;
}
