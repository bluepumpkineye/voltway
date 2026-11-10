'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { HMI_W, HMI_H } from '../ui';
import { HaProvider, useHaLocal } from '../harmonyos/shared';
import { NavPage } from '../harmonyos/MapNav';
import { useBy } from './theme';
import { StatusBar, SystemBar, type Over } from './Bars';
import { HomeDesktop } from './Home';
import { AppCentre } from './AppCentre';
import { CameraPage, ClimatePage, MediaPage, PhonePage, VehiclePage } from './Pages';
import { SettingsApp } from './Settings';

/**
 * The BYD Seal's centre screen, as its DiLink draws it (components/hmi/byd/theme.ts).
 *
 * The status bar and the system bar stay put; between them the wallpaper home with its glass capsules, the
 * air-conditioning page, the vehicle page, navigation, the phone, music and the 360 camera, or Settings,
 * and the app panel over whichever is open. Everything that has a counterpart in the car writes the shared
 * vehicle store, so the 3D car follows (the lock, the boot, the lamps, the drive mode, the climate). Night
 * is the car's own default and day its other mode (Settings, DiLink, Display).
 */
export function BydSurface({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  return (
    <HaProvider slug={vehicle.slug}>
      <Surface vehicle={vehicle} variant={variant} />
    </HaProvider>
  );
}

function Surface({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  const t = useBy();
  const { val, setVal } = useHaLocal();
  const { hmiScreen, appCentreOpen, openSettings } = useVehicleStore();

  // the generic screens that have no page of their own here open the Settings page they belong to
  React.useEffect(() => {
    if (hmiScreen === 'drive' || hmiScreen === 'track') openSettings('driving');
    else if (hmiScreen === 'adas') openSettings('assist');
    else if (hmiScreen === 'charge') openSettings('energy');
    // leaving the home closes the phone, which is a page of the home
    if (hmiScreen !== 'home') setVal('phone', 0);
  }, [hmiScreen, openSettings, setVal]);

  let body: React.ReactNode;
  let over: Over = 'page';
  switch (hmiScreen) {
    case 'climate':
      body = <ClimatePage />;
      break;
    case 'controls':
      body = <VehiclePage />;
      break;
    case 'media':
      body = <MediaPage />;
      break;
    case 'nav':
      // the map page is drawn for a shorter bar: leave it the difference
      body = (
        <div className="absolute inset-x-0 top-0" style={{ bottom: 25 }}>
          <NavPage />
        </div>
      );
      break;
    case 'camera':
    case 'park':
      body = <CameraPage />;
      break;
    case 'settings':
    case 'drive':
    case 'track':
    case 'adas':
    case 'charge':
      body = <SettingsApp vehicle={vehicle} variant={variant} />;
      break;
    default:
      if (val.phone) body = <PhonePage />;
      else {
        body = <HomeDesktop />;
        over = 'wallpaper';
      }
  }
  if (appCentreOpen) over = 'wallpaper';

  return (
    <div
      className="hmi-surface byd relative overflow-hidden"
      data-theme={t.tone}
      style={{ width: HMI_W, height: HMI_H, background: t.bg, color: t.text }}
      // Mounted in the 3D cabin this tree still sits in the R3F React tree, so synthetic pointer
      // events would bubble to the Canvas and OrbitControls would read a tap as a drag.
      onPointerDown={(e) => e.stopPropagation()}
      onPointerUp={(e) => e.stopPropagation()}
      onPointerMove={(e) => e.stopPropagation()}
      onWheel={(e) => e.stopPropagation()}
    >
      {body}
      {appCentreOpen && <AppCentre />}
      {(appCentreOpen || (hmiScreen !== 'camera' && hmiScreen !== 'park')) && <StatusBar over={over} />}
      <SystemBar over={over} screen={hmiScreen} />
      {/* the brightness slider dims the whole screen */}
      {val.brightness < 100 && (
        <div className="pointer-events-none absolute inset-0 z-50" style={{ background: `rgba(0,0,0,${(100 - val.brightness) / 160})` }} />
      )}
    </div>
  );
}
