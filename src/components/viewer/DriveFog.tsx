'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import { techClock } from '@/lib/tech/clock';
import { exitFog, exitInfo } from '@/lib/tech/drive-exit';
import { useDusk } from './Lights';
import { STAGE_HAZE, STUDIO_WHITE } from './StudioShowroom';

/** where the fog stands while it is out of the way, m (far past the road's end and the camera's far plane) */
const FAR_AWAY = 4000;
/** where the fog has everything at the end of the Drive tab's exit, m from the camera, and how deep it is */
const FAR_END = 120;
const DEPTH = 70;

/**
 * The studio's white as a fog, for the Drive tab's exit: when a run ends with the car still going, the car drives off down the road from a camera that
 * stays where it is (`exitAt`, src/lib/tech/drive-exit.ts) and the fog closes in over the exit's first second and a half, so that it fades into the white
 * as it goes instead of ending as a dot at the camera's far plane. Outside the exit it stands 4 km away and does nothing; it is mounted for the whole
 * showroom (not just the Drive tab), so that every material is compiled with the fog from the start: a scene that gains a fog turns a define on in
 * all of their shaders, and the car and the cabin compiled again (about fifty programs) on the first visit to the tab.
 *
 * The scenery's own haze (viewer/scenery/kit.ts) is the same white; this does not change what stands near.
 */
export function DriveFog() {
  const fog = React.useMemo(() => new THREE.Fog(STUDIO_WHITE, FAR_AWAY, FAR_AWAY + DEPTH), []);
  const invalidate = useThree((s) => s.invalidate);
  // the lamps' dusk darkens the room, and its white (or the horizon of the world the road is in) with it
  useDusk((d) => fog.color.copy(STAGE_HAZE).multiply(d.room));
  useFrame(() => {
    const k = exitFog(exitInfo, techClock.t);
    // it closes in smoothly: far = the end distance plus what is left of the way, cubed
    const far = k <= 0 ? FAR_AWAY : FAR_END + (FAR_AWAY - FAR_END) * Math.pow(1 - k, 3);
    if (far !== fog.far) {
      fog.far = far;
      fog.near = Math.max(1, far - DEPTH);
      invalidate();
    }
  });
  return <primitive object={fog} attach="fog" />;
}
