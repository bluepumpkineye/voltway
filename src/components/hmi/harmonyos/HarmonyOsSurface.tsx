'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { HMI_W, HMI_H } from '../ui';
import { HaProvider, useHaLocal } from './shared';
import { useHa } from './theme';
import { BottomBar, StatusBar, type Over } from './Bars';
import { HomeDesktop } from './Desktop';
import { AppCentre } from './AppCentre';
import { ControlCentre } from './ControlCentre';
import { ClimatePage } from './Climate';
import { SeatsPage } from './Seats';
import { MediaPage } from './Media';
import { CameraPage, NavPage } from './MapNav';
import { SettingsApp } from './Settings';

/**
 * The Luxeed RX's centre screen, as Huawei HarmonyOS draws it.
 *
 * The status bar and the bottom bar stay put on every page; between them the
 * home desktop (two pages of cards over a wallpaper), the Control Centre, the
 * climate and seat pages, navigation and the 360 camera, music and radio, or the
 * Settings app. The App Centre rises over whichever is open. Everything that has
 * a counterpart writes the shared vehicle store, so the cabin in 3D and the
 * page's readouts follow (the drive mode, the doors, the ambient light).
 */
export function HarmonyOsSurface({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  return (
    <HaProvider>
      <Surface vehicle={vehicle} variant={variant} />
    </HaProvider>
  );
}

function Surface({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  const t = useHa();
  const { val } = useHaLocal();
  const { hmiScreen, setHmiScreen, appCentreOpen, openSettings } = useVehicleStore();

  // the generic screens that have no page of their own here open the Settings page they belong to
  React.useEffect(() => {
    if (hmiScreen === 'drive' || hmiScreen === 'track') openSettings('driving');
    else if (hmiScreen === 'adas') openSettings('assist');
  }, [hmiScreen, openSettings]);

  let body: React.ReactNode;
  let over: Over = 'page';
  switch (hmiScreen) {
    case 'home':
      body = <HomeDesktop tone={t.tone} />;
      over = 'wallpaper';
      break;
    case 'controls':
      body = <ControlCentre vehicle={vehicle} />;
      over = 'wallpaper';
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
      body = <CameraPage />;
      break;
    case 'settings':
    case 'drive':
    case 'track':
    case 'adas':
      body = <SettingsApp vehicle={vehicle} variant={variant} />;
      break;
    default:
      body = (
        <div className="absolute inset-0 grid place-items-center text-[28px]" style={{ color: t.text2 }}>
          {hmiScreen}
        </div>
      );
  }

  return (
    <div
      className="hmi-surface harmonyos relative overflow-hidden"
      data-theme={t.tone}
      style={{ width: HMI_W, height: HMI_H, background: t.bg, color: t.text }}
      // Mounted in the 3D cabin this tree still sits in the R3F React tree, so
      // synthetic pointer events would bubble to the Canvas and OrbitControls
      // would read a tap as a drag. Swallow them at the surface.
      onPointerDown={(e) => e.stopPropagation()}
      onPointerUp={(e) => e.stopPropagation()}
      onPointerMove={(e) => e.stopPropagation()}
      onWheel={(e) => e.stopPropagation()}
    >
      {body}
      {/* the climate and seat pages run to the top of the screen, as the car's do */}
      {!['climate', 'seats', 'camera'].includes(hmiScreen) && <StatusBar over={over} />}
      {appCentreOpen && <AppCentre />}
      <BottomBar over={over} screen={hmiScreen} onHome={() => setHmiScreen('home')} />
      {/* the Control Centre's brightness slider dims the whole screen */}
      {val.brightness < 100 && (
        <div className="pointer-events-none absolute inset-0 z-50" style={{ background: `rgba(0,0,0,${(100 - val.brightness) / 160})` }} />
      )}
    </div>
  );
}
