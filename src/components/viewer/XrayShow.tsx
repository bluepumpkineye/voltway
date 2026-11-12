'use client';

import React from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import type { Vehicle } from '@/data/vehicles/schema';
import { techClock } from '@/lib/tech/clock';
import { techSession } from '@/lib/tech/session';
import { planFor, poseAt, SHOW_EXIT_S } from '@/lib/xray/show';
import { useVehicleStore } from '@/store/vehicle-store';
import { useCarFrame } from './ShowroomCameraRig';

type Controls = {
  enabled: boolean;
  setLookAt: (px: number, py: number, pz: number, tx: number, ty: number, tz: number, smooth: boolean) => Promise<void>;
  update: (dt: number) => boolean;
};

/** a window's aspect the shots are composed for; a narrower one stands further back (as the anchors' poses do) */
const REF_ASPECT = 1.6;

/**
 * The X-ray tab's Play camera: while the show runs it puts the camera where the shot list says (src/lib/xray/show.ts) for the run's playhead,
 * every frame, so a scrubbed run shows the picture a played one does. The visitor's own orbit is switched off while it runs and
 * comes back, with the camera flown home to the tab's pose, when it ends.
 *
 * It sits inside the viewer's Suspense boundary because it measures the loaded exterior (`useCarFrame`), as the camera rig does.
 */
export function XrayShowCamera({ vehicle }: { vehicle: Vehicle }) {
  const on = useVehicleStore((s) => s.tab === 'xray' && s.xrayShow);
  const controls = useThree((s) => s.controls) as unknown as Controls | null;
  const size = useThree((s) => s.size);
  const frame = useCarFrame(vehicle);
  const d = vehicle.dimensions;
  const L = d.lengthMm / 1000;
  const W = d.widthMm / 1000;
  const H = d.heightMm / 1000;
  const cx = (frame.xMin + frame.xMax) / 2;
  const aspect = size.width / Math.max(size.height, 1);
  const stand = Math.max(1, REF_ASPECT / Math.max(aspect, 0.2));

  React.useEffect(() => {
    if (!on || !controls) return;
    controls.enabled = false;
    return () => {
      controls.enabled = true;
      // the tab's own pose again: the rig flies the camera back to it
      useVehicleStore.setState((s) => ({ anchorTick: s.anchorTick + 1 }));
    };
  }, [on, controls]);

  useFrame(() => {
    const f = techSession.runtime?.launch?.drive;
    if (!on || !controls || !f || techClock.duration <= 0) return;
    const p = poseAt(planFor(f, { events: f.events, duration: techClock.duration, exit: SHOW_EXIT_S }), techClock.t);
    const az = (p.az * Math.PI) / 180;
    const el = (p.el * Math.PI) / 180;
    const dist = p.d * L * stand;
    const tx = cx + p.u * L;
    const ty = p.h * H;
    const tz = p.lat * W;
    controls.setLookAt(
      tx + Math.cos(az) * Math.cos(el) * dist,
      ty + Math.sin(el) * dist,
      tz - Math.sin(az) * Math.cos(el) * dist,
      tx,
      ty,
      tz,
      false,
    );
    controls.update(0);
  });
  return null;
}
