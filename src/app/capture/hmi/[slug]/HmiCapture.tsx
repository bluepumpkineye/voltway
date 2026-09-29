'use client';

import React from 'react';
import type { Vehicle } from '@/data/vehicles/schema';
import { flagshipVariant } from '@/data/vehicles/schema';
import { HmiSurface } from '@/components/hmi/HmiSurface';
import { HMI_W, HMI_H } from '@/components/hmi/ui';
import { useVehicleStore, type Gear, type HmiScreen, type SettingsPage } from '@/store/vehicle-store';

/**
 * The HMI alone, at native size, pinned to the top-left corner over the site
 * chrome - so a headless browser screenshot of a HMI_W x HMI_H window is
 * exactly the screen image. The 3D pipeline uses it as the centre-screen
 * texture in Blender renders (the live app mounts the real DOM instead).
 *
 * Query parameters put the HMI in a given state for a capture:
 *   screen=home|nav|media|settings|track   gear=P|D   page=<settings page>
 *   mode=<car drive mode id>   climate=1
 */
export function HmiCapture({ vehicle }: { vehicle: Vehicle }) {
  const [ready, setReady] = React.useState(false);
  React.useEffect(() => {
    const q = new URLSearchParams(window.location.search);
    const s = useVehicleStore.getState();
    s.reset(flagshipVariant(vehicle).id);
    const gear = q.get('gear');
    if (gear === 'P' || gear === 'D') s.setGear(gear as Gear);
    const page = q.get('page');
    if (page) s.openSettings(page as SettingsPage);
    const screen = q.get('screen');
    if (screen) s.setHmiScreen(screen as HmiScreen);
    const mode = vehicle.cockpit.driveModes?.find((m) => m.id === q.get('mode'));
    if (mode) s.setCarMode(mode.id, mode.model);
    if (q.get('climate') === '1') s.setClimateOpen(true);
    setReady(true);
  }, [vehicle]);

  return (
    <div
      style={{
        position: 'fixed', left: 0, top: 0, width: HMI_W, height: HMI_H,
        zIndex: 9999, overflow: 'hidden', background: '#000',
      }}
    >
      {/* the dev-mode indicator would be baked into the texture */}
      <style>{'nextjs-portal{display:none!important}'}</style>
      {ready && <HmiSurface vehicle={vehicle} variant={flagshipVariant(vehicle)} />}
    </div>
  );
}
