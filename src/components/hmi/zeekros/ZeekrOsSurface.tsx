'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { HMI_W, HMI_H } from '../ui';
import { ZkProvider, useZkLocal } from './shared';
import { useZk, SHEET_TOP, BAR_H } from './theme';
import { BottomBar, StatusBar } from './Bars';
import { HomeScene } from './Home';
import { AppCentre } from './AppCentre';
import { SeatsPage } from './Seats';
import { CameraPage, ClimatePage, ControlsPage, MediaPage, NavPage } from './Pages';

/**
 * The Zeekr 7X's centre screen, as ZEEKR OS draws it.
 *
 * Home is a 3D showroom scene with the car standing in it (its doors, bonnet and tailgate are
 * chips on the car), a rail of shortcuts down the left and four cards along the bottom. Every
 * other page is a lavender-white sheet that slides up over the scene from above the bottom bar,
 * which stays put with the status bar on top (c10_0016-80). Navigation, the 360 camera and the
 * App Centre take the whole screen. Everything that has a counterpart in the 3D car writes the
 * shared vehicle store (the doors, the climate, the ambient light, the drive mode).
 */
export function ZeekrOsSurface({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  const t = useZk();
  return (
    <div
      className="hmi-surface zeekros relative overflow-hidden"
      data-theme={t.tone}
      style={{ width: HMI_W, height: HMI_H, background: t.sheet, color: t.text }}
      // Mounted in the 3D cabin this tree still sits in the R3F React tree, so
      // synthetic pointer events would bubble to the Canvas and OrbitControls
      // would read a tap as a drag. Swallow them at the surface.
      onPointerDown={(e) => e.stopPropagation()}
      onPointerUp={(e) => e.stopPropagation()}
      onPointerMove={(e) => e.stopPropagation()}
      onWheel={(e) => e.stopPropagation()}
    >
      <style>{`@keyframes zkUp{from{transform:translateY(46px);opacity:0}to{transform:none;opacity:1}}`}</style>
      <ZkProvider>
        <Surface vehicle={vehicle} variant={variant} />
      </ZkProvider>
    </div>
  );
}

function Surface({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  const t = useZk();
  const { val } = useZkLocal();
  const { hmiScreen, appCentreOpen } = useVehicleStore();

  // the generic screens that have no page of their own here map to the nearest one
  const screen =
    hmiScreen === 'drive' || hmiScreen === 'track' || hmiScreen === 'adas' || hmiScreen === 'settings'
      ? 'controls'
      : hmiScreen;

  let page: React.ReactNode = null;
  let full = false;
  switch (screen) {
    case 'climate':
      page = <ClimatePage vehicle={vehicle} />;
      break;
    case 'seats':
      page = <SeatsPage vehicle={vehicle} />;
      break;
    case 'media':
      page = <MediaPage />;
      break;
    case 'controls':
      page = <ControlsPage vehicle={vehicle} variant={variant} />;
      break;
    case 'nav':
      page = <NavPage />;
      full = true;
      break;
    case 'camera':
      page = <CameraPage vehicle={vehicle} />;
      full = true;
      break;
    default:
      break;
  }
  const onScene = !page && !appCentreOpen;

  return (
    <>
      <HomeScene vehicle={vehicle} hidden={full || appCentreOpen} />
      {page && (
        <div
          key={screen}
          className="absolute inset-x-0 overflow-hidden"
          style={{
            top: full ? 0 : SHEET_TOP,
            bottom: BAR_H,
            background: t.sheet,
            animation: 'zkUp 280ms cubic-bezier(0.2, 0.8, 0.2, 1)',
            boxShadow: full ? undefined : '0 -6px 22px rgba(40,50,110,0.14)',
          }}
        >
          {!full && <span className="absolute left-[611px] top-[8px] h-[3px] w-[70px] rounded-full" style={{ background: t.line }} aria-hidden />}
          {page}
        </div>
      )}
      {appCentreOpen && (
        <div className="absolute inset-x-0 overflow-hidden" style={{ top: 0, bottom: BAR_H, background: t.sheet, animation: 'zkUp 280ms cubic-bezier(0.2, 0.8, 0.2, 1)' }}>
          <div className="absolute inset-x-0" style={{ top: 44, bottom: 0 }}>
            <AppCentre />
          </div>
        </div>
      )}
      <StatusBar />
      <BottomBar over={onScene ? 'scene' : 'sheet'} screen={hmiScreen} />
      {/* the brightness slider dims the whole screen */}
      {val.brightness < 100 && (
        <div className="pointer-events-none absolute inset-0 z-50" style={{ background: `rgba(0,0,0,${(100 - val.brightness) / 160})` }} />
      )}
    </>
  );
}
