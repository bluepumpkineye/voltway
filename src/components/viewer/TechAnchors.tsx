'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import type { Vehicle } from '@/data/vehicles/schema';
import { ANCHORS, anchorLocal, boxCorners, driveAnchors, type AnchorFrame, type CarGeometry, type ScreenPt } from '@/lib/tech/drive-anchors';
import { rigOf } from '@/lib/tech/rig';
import { useVehicleStore } from '@/store/vehicle-store';
import { CarFollower } from './techRig';

/**
 * Puts the Drive tab's anchor points (src/lib/tech/drive-anchors.ts: the arch, the disc, the hubs, the pack, the roof) on the screen, every
 * frame, for the cards that float beside the car (showroom/DriveMotion.tsx). The points ride with the car (a `CarFollower` frame: its place on
 * the floor and the body's pitch, roll and heave), they are the ones on the side of the car the camera is on, and what is published is only
 * where they land on the window: this draws nothing.
 *
 * Inside the cabin camera there is nothing to point at from the outside: the frame is null and the cards fall back to a column.
 */
export function TechAnchors({ vehicle }: { vehicle: Vehicle }) {
  const on = useVehicleStore((s) => s.tab === 'drive');
  React.useEffect(() => {
    if (!on) driveAnchors.frame = null;
    return () => {
      driveAnchors.frame = null;
    };
  }, [on]);
  if (!on) return null;
  return (
    <CarFollower vehicle={vehicle}>
      <Probe vehicle={vehicle} />
    </CarFollower>
  );
}

const v3 = new THREE.Vector3();
let version = 0;

function Probe({ vehicle }: { vehicle: Vehicle }) {
  const rig = rigOf(vehicle);
  const mounts = React.useSyncExternalStore(rig.subscribe, () => rig.mounts, () => 0);
  const group = React.useRef<THREE.Group>(null);
  const camera = useThree((s) => s.camera);
  const size = useThree((s) => s.size);
  const side = React.useRef<1 | -1>(1);

  const geo = React.useMemo<CarGeometry | null>(() => {
    const layout = rig.layout;
    if (!layout) return null;
    const { rac, body } = rig;
    const r = (layout.radius.FL + layout.radius.FR + layout.radius.RL + layout.radius.RR) / 4;
    const d = vehicle.dimensions;
    return {
      rearX: rac.x,
      wheelbase: layout.wheelbase,
      midZ: -rac.y,
      halfTrack: Math.abs(layout.wheels.FL.y - layout.wheels.FR.y) / 2,
      radius: r,
      halfBody: d.widthMm / 2000 - 0.02,
      height: d.heightMm / 1000,
      xMin: rac.x - body.rear,
      xMax: rac.x + body.front,
    };
    // the wheels arrive with the exterior; a new mount measures again
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rig, vehicle, mounts]);

  useFrame(() => {
    const g = group.current;
    // inside the car there is nothing to point at
    if (!g || !geo || useVehicleStore.getState().drive.cam === 'cabin') {
      driveAnchors.frame = null;
      return;
    }
    camera.updateMatrixWorld();
    g.updateWorldMatrix(true, false);

    // the side of the car the camera is on, held until it is a half metre over the middle the other way
    v3.copy(camera.position);
    g.worldToLocal(v3);
    const dz = v3.z - geo.midZ;
    if (Math.abs(dz) > 0.5) side.current = dz > 0 ? 1 : -1;

    const W = size.width;
    const H = size.height;
    const project = (p: [number, number, number]): ScreenPt => {
      v3.set(p[0], p[1], p[2]).applyMatrix4(g.matrixWorld).project(camera);
      return { x: ((v3.x + 1) / 2) * W, y: ((1 - v3.y) / 2) * H, ok: v3.z > -1 && v3.z < 1 };
    };
    const pts = {} as AnchorFrame['pts'];
    for (const name of ANCHORS) pts[name] = project(anchorLocal(name, geo, side.current));

    let x0 = Infinity;
    let y0 = Infinity;
    let x1 = -Infinity;
    let y1 = -Infinity;
    for (const c of boxCorners(geo)) {
      const p = project(c);
      x0 = Math.min(x0, p.x);
      y0 = Math.min(y0, p.y);
      x1 = Math.max(x1, p.x);
      y1 = Math.max(y1, p.y);
    }
    driveAnchors.frame = { version: ++version, width: W, height: H, side: side.current, box: { x: x0, y: y0, w: x1 - x0, h: y1 - y0 }, pts };
  });

  return <group ref={group} />;
}
