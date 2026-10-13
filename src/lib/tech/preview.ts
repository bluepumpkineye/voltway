import React from 'react';
import type { Vehicle } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { DRIVERS, visibleDemos } from './demos';
import { rigOf } from './rig';
import type { Runtime } from './session';

/**
 * A demonstration's stage and car, built for a screen that shows it while no demo is running: the car's
 * parking page in the cabin (the Interior tab) or on the vehicle page. It is the same build the Tech
 * tab's director makes, so the lot and the car's place in it are identical; only the clock is not running.
 * Null until the exterior's wheels have been measured (the rig is ready).
 */
export function usePreviewRuntime(vehicle: Vehicle, demoId: string): Runtime | null {
  const rig = rigOf(vehicle);
  const rigged = React.useSyncExternalStore(rig.subscribe, () => rig.ready, () => false);
  const speed = useVehicleStore((s) => s.parkSpeed);
  return React.useMemo(() => {
    const spec = visibleDemos(vehicle).find((d) => d.id === demoId);
    const driver = spec ? DRIVERS[spec.driver] : undefined;
    const layout = rig.layout;
    if (!spec || !driver || !rigged || !layout) return null;
    const body = { ...rig.body, halfWidth: vehicle.dimensions.widthMm / 2000 };
    const built = driver.build({
      vehicle,
      layout,
      body,
      start: { x: rig.rac.x, y: rig.rac.y, yaw: 0 },
      speed,
      ride: { carpet: true, modeId: null },
      params: spec?.params ?? {},
    });
    return { demoId, stage: built.stage, sample: (t: number) => built.track.sample(t), body };
  }, [vehicle, demoId, rig, rigged, speed]);
}
