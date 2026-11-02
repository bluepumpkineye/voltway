'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { HMI_W, HMI_H } from '../ui';
import { HaProvider, useHaLocal } from '../harmonyos/shared';
import { CameraPage, NavPage } from '../harmonyos/MapNav';
import { useAv } from './theme';
import { BottomBar, StatusBar, type Over } from './Bars';
import { HomeDesktop } from './Home';
import { AppCentre } from './AppCentre';
import { ClimatePage, ControlPanel, MediaPage, SeatsPage } from './Pages';
import { SettingsApp } from './Settings';

/**
 * The Avatr 06T's centre screen, as its HarmonyOS cockpit draws it (components/hmi/avatr/theme.ts).
 *
 * The status bar and the bottom bar stay put; between them the wallpaper home with its glass cards, the
 * vehicle control panel, the climate and seat pages, music, navigation and the 360 camera, or the
 * Settings app, and the App Centre over whichever is open. Everything that has a counterpart in the car
 * writes the shared vehicle store, so the 3D cabin follows (the drive mode, the lamps, the doors, the
 * climate). The building blocks the car shares with the Luxeed RX (the HarmonyOS skin) are used as they are.
 */
export function AvatrSurface({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  return (
    <HaProvider slug={vehicle.slug}>
      <Surface vehicle={vehicle} variant={variant} />
    </HaProvider>
  );
}

/** The pages that run to the top of the screen, as the car's do. */
const FULL = ['controls', 'climate', 'seats', 'camera', 'park'];

function Surface({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  const t = useAv();
  const { val } = useHaLocal();
  const { hmiScreen, appCentreOpen, openSettings } = useVehicleStore();

  // the generic screens that have no page of their own here open the Settings page they belong to
  React.useEffect(() => {
    if (hmiScreen === 'drive' || hmiScreen === 'track') openSettings('driving');
    else if (hmiScreen === 'adas') openSettings('assist');
    else if (hmiScreen === 'charge') openSettings('energy');
  }, [hmiScreen, openSettings]);

  let body: React.ReactNode;
  let over: Over = 'page';
  switch (hmiScreen) {
    case 'controls':
      body = <ControlPanel vehicle={vehicle} />;
      break;
    case 'climate':
      body = <ClimatePage />;
      break;
    case 'seats':
      body = <SeatsPage />;
      break;
    case 'media':
      body = <MediaPage />;
      break;
    case 'nav':
      body = <NavPage />;
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
      body = <HomeDesktop vehicle={vehicle} variant={variant} />;
      over = 'wallpaper';
  }
  if (appCentreOpen) over = 'wallpaper';

  return (
    <div
      className="hmi-surface avatr relative overflow-hidden"
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
      {appCentreOpen && <AppCentre variant={variant} />}
      {(appCentreOpen || !FULL.includes(hmiScreen)) && <StatusBar over={over} />}
      <BottomBar over={over} screen={hmiScreen} />
      {/* the brightness slider dims the whole screen */}
      {val.brightness < 100 && (
        <div className="pointer-events-none absolute inset-0 z-50" style={{ background: `rgba(0,0,0,${(100 - val.brightness) / 160})` }} />
      )}
    </div>
  );
}
