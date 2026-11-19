'use client';

import React from 'react';
import { useProgress } from '@react-three/drei';
import { useFrame, useThree } from '@react-three/fiber';
import type { Vehicle } from '@/data/vehicles/schema';
import { useLoadingStore } from '@/store/loading-store';
import { useVehicleStore } from '@/store/vehicle-store';
import { LoadingCardView } from '@/components/showroom/LoadingCard';

/**
 * The loading card over the viewer: one place that says what the showroom is waiting for.
 *
 *  - the car itself, until it is on screen (the files' own progress, as a number);
 *  - the cabin, when the visitor has asked for a tab that looks into it before it has streamed in;
 *  - a tab or scene change, from the click until the frames come steadily again (the work after the files: building the
 *    objects, compiling their shaders the first time they are drawn). If it brings files with it (the X-ray's hardware, the
 *    city) the number is theirs.
 *
 * It is DOM over the canvas, not a part of the scene, so it stays crisp and can be painted while the scene is busy.
 */
export function ViewerLoading({ vehicle, cabinWanted }: { vehicle: Vehicle; cabinWanted: boolean }) {
  const cabinReady = useVehicleStore((s) => s.cabinReady);
  const tab = useVehicleStore((s) => s.tab);
  const switching = useLoadingStore((s) => s.switching);
  const booting = useLoadingStore((s) => s.booting);
  const { active, progress } = useProgress();

  // another car's page, or this one opened again, begins with the card up
  React.useEffect(() => () => useLoadingStore.getState().setBooting(true), []);

  // the number only climbs while one wait lasts: the loaders' items finish in any order, and a new one raises the total
  const best = React.useRef({ key: '', value: 0 });
  const hasCabin = Boolean(vehicle.assets.interiorModelUrl);

  let key = '';
  let label = '';
  let detail: string | undefined;
  let instant = false;
  if (booting) {
    key = 'car';
    label = `Loading ${vehicle.brand} ${vehicle.model}`;
    detail = active ? 'Downloading the 3D model' : 'Setting up the scene';
    instant = true;
  } else if (switching) {
    key = `switch-${switching.token}`;
    label = switching.label;
    detail = active ? 'Downloading what it needs' : 'Setting up the scene';
  } else if (hasCabin && cabinWanted && !cabinReady && (tab === 'interior' || tab === 'xray')) {
    key = 'cabin';
    label = 'Loading the interior';
    detail = active ? 'Downloading the cabin' : 'Setting up the cabin';
  }

  if (best.current.key !== key) best.current = { key, value: 0 };
  let percent: number | null = null;
  if (key && active) {
    best.current.value = Math.max(best.current.value, progress);
    percent = best.current.value;
  }

  if (!key) return null;
  return (
    <div className="pointer-events-none absolute inset-0 z-30 grid place-items-center">
      {/* the first wait is shown at once; the others after a moment, so a change that is quick never flashes it */}
      <LoadingCardView key={key} label={label} detail={detail} percent={percent} delayMs={instant ? 0 : 350} instant={instant} />
    </div>
  );
}

/**
 * Ends the card once the scene has settled: ten frames in a row, none of them a stall (a frame that took more than 120 ms is
 * one, and counting begins again after it). That is the first frames after the car arrives (`booting`) and the frames after a
 * tab or scene change has been made. The viewer draws on demand, so while the card is up a timer asks for frames; without it
 * a change that moves nothing on screen would never be counted. A card that has not ended in twenty seconds is taken down
 * anyway.
 */
export function SwitchSettle() {
  const invalidate = useThree((s) => s.invalidate);
  const exteriorUp = useVehicleStore((s) => s.exteriorUp);
  const token = useLoadingStore((s) => (s.switching?.applied ? s.switching.token : 0));
  const booting = useLoadingStore((s) => s.booting) && exteriorUp;
  const counting = booting || token > 0;
  const calm = React.useRef(0);

  React.useEffect(() => {
    calm.current = 0;
    if (!counting) return;
    const ask = window.setInterval(invalidate, 24);
    const cap = window.setTimeout(() => {
      const st = useLoadingStore.getState();
      st.setBooting(false);
      st.end(token || undefined);
    }, 20000);
    return () => {
      window.clearInterval(ask);
      window.clearTimeout(cap);
    };
  }, [counting, token, invalidate]);

  useFrame((_, dt) => {
    if (!counting) return;
    calm.current = dt < 0.12 ? calm.current + 1 : 0;
    if (calm.current < 10) return;
    const st = useLoadingStore.getState();
    st.setBooting(false);
    if (token) st.end(token);
  });
  return null;
}
