'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { HMI_W, HMI_H } from '../ui';
import { HY } from './theme';
import { StatusBar, Dock, type DockApp } from './Bars';
import { ParkedDesktop, DrivingDesktop } from './Desktop';
import { ClimatePanel, NavApp, MusicApp, AppDrawer } from './Apps';
import { SettingsApp } from './Settings';
import { TrackMaster } from './TrackMaster';

/**
 * The SU7 Ultra's centre screen, as Xiaomi HyperOS draws it.
 *
 * The status bar and the dock stay put; between them the parked desktop (the
 * car, the time) or, in D, the driving desktop's three cards, or an app.
 * The climate panel rises from the dock's temperatures. Everything writes the
 * shared vehicle store, so the cabin in 3D and the page's readouts follow.
 */
export function HyperOsSurface({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  const { hmiScreen, setHmiScreen, openSettings, gear, climateOpen, setClimateOpen } = useVehicleStore();
  const [drawer, setDrawer] = React.useState(false);

  const onApp = (id: DockApp) => {
    if (id === 'apps') {
      setClimateOpen(false);
      setDrawer(!drawer);
      return;
    }
    setDrawer(false);
    if (id === 'settings') openSettings(useVehicleStore.getState().settingsPage);
    else setHmiScreen(id);
  };

  let body: React.ReactNode;
  switch (hmiScreen) {
    case 'settings':
    case 'drive':
    case 'controls':
    case 'adas':
      body = <SettingsApp vehicle={vehicle} variant={variant} />;
      break;
    case 'nav':
      body = <NavApp variant={variant} />;
      break;
    case 'media':
      body = <MusicApp />;
      break;
    case 'track':
      body = <TrackMaster vehicle={vehicle} variant={variant} />;
      break;
    default:
      body = gear === 'D' ? <DrivingDesktop vehicle={vehicle} variant={variant} /> : <ParkedDesktop vehicle={vehicle} />;
  }
  const parked = hmiScreen === 'home' && gear === 'P';

  return (
    <div
      className="hmi-surface hyperos relative flex flex-col overflow-hidden"
      style={{ width: HMI_W, height: HMI_H, background: HY.bg, color: HY.text }}
      // Mounted in the 3D cabin this tree still sits in the R3F React tree, so
      // synthetic pointer events would bubble to the Canvas and OrbitControls
      // would read a tap as a drag. Swallow them at the surface.
      onPointerDown={(e) => e.stopPropagation()}
      onPointerUp={(e) => e.stopPropagation()}
      onPointerMove={(e) => e.stopPropagation()}
      onWheel={(e) => e.stopPropagation()}
    >
      {/* the parked desktop runs under the status bar and the dock */}
      {parked && <div className="absolute inset-0">{body}</div>}
      <StatusBar variant={variant} />
      {/* parked, this layer only carries the overlays: let taps through to the car */}
      <div className={`relative min-h-0 flex-1 ${parked ? 'pointer-events-none [&>*]:pointer-events-auto' : ''}`}>
        {!parked && body}
        {climateOpen && <ClimatePanel />}
        {drawer && <AppDrawer vehicle={vehicle} onClose={() => setDrawer(false)} />}
      </div>
      <Dock vehicle={vehicle} onApp={onApp} drawerOpen={drawer} />
    </div>
  );
}
