'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { HMI_W, HMI_H } from '../ui';
import { ChassisScreen } from '../chassis';
import { XoProvider, useXo } from './shared';
import { XO } from './theme';
import { BottomBar, StatusBar } from './Bars';
import { AppCentre, CameraPage, MapHome, MediaPage, QuickPanel, SettingsPage } from './Pages';

/**
 * The XPeng G9L's centre screen, as XOS Tianji draws it.
 *
 * The map is the home, with the car from above in a tall panel on its left; the quick panel (Common,
 * AC, Seats), the settings and the other pages are sheets over it, under the same status bar and over
 * the same rounded bottom bar (home, the two temperatures, the quick panel, the 360 camera, the lock,
 * the vehicle, the seats, the climate, the apps, the music player and the volume), c10_0019-56. What
 * has a counterpart in the 3D car writes the shared vehicle store (the climate, the drive mode, the
 * headlamps, the ambient light).
 */
export function XosSurface({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  return (
    <div
      className="hmi-surface xos relative overflow-hidden"
      style={{ width: HMI_W, height: HMI_H, background: XO.ground, color: XO.text }}
      // Mounted in the 3D cabin this tree still sits in the R3F React tree, so synthetic pointer
      // events would bubble to the Canvas and OrbitControls would read a tap as a drag.
      onPointerDown={(e) => e.stopPropagation()}
      onPointerUp={(e) => e.stopPropagation()}
      onPointerMove={(e) => e.stopPropagation()}
      onWheel={(e) => e.stopPropagation()}
    >
      <style>{`@keyframes xoUp{from{transform:translateY(24px);opacity:0}to{transform:none;opacity:1}}`}</style>
      <XoProvider>
        <Surface vehicle={vehicle} variant={variant} />
      </XoProvider>
    </div>
  );
}

function Surface({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  const { val } = useXo();
  const { hmiScreen, appCentreOpen } = useVehicleStore();

  let page: React.ReactNode;
  switch (hmiScreen) {
    case 'controls':
      page = <QuickPanel vehicle={vehicle} tab={val.sheetTab} />;
      break;
    case 'climate':
      page = <QuickPanel vehicle={vehicle} tab={1} />;
      break;
    case 'seats':
      page = <QuickPanel vehicle={vehicle} tab={2} />;
      break;
    case 'settings':
    case 'drive':
    case 'adas':
    case 'track':
    case 'charge':
      page = <SettingsPage vehicle={vehicle} variant={variant} />;
      break;
    case 'media':
      page = <MediaPage />;
      break;
    case 'camera':
    case 'park':
      page = <CameraPage vehicle={vehicle} />;
      break;
    case 'chassis':
      page = (
        <div className="absolute inset-0" style={{ background: 'linear-gradient(160deg, #1a1d2c, #10121c)' }}>
          <div className="absolute inset-x-[14px] top-[52px] bottom-[84px]">
            <ChassisScreen vehicle={vehicle} variant={variant} accent={XO.purple} />
          </div>
        </div>
      );
      break;
    default:
      page = <MapHome vehicle={vehicle} />;
  }

  return (
    <>
      <div key={hmiScreen} className="absolute inset-0 overflow-hidden" style={{ animation: 'xoUp 240ms cubic-bezier(0.2, 0.8, 0.2, 1)' }}>
        {page}
      </div>
      {appCentreOpen && (
        <div className="absolute inset-0 overflow-hidden" style={{ animation: 'xoUp 240ms cubic-bezier(0.2, 0.8, 0.2, 1)' }}>
          <AppCentre />
        </div>
      )}
      <StatusBar variant={variant} />
      <BottomBar screen={hmiScreen} />
      {/* the brightness slider dims the whole screen */}
      {val.brightness < 100 && (
        <div className="pointer-events-none absolute inset-0 z-50" style={{ background: `rgba(0,0,0,${(100 - val.brightness) / 160})` }} />
      )}
    </>
  );
}
