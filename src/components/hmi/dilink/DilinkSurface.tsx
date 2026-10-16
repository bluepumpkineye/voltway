'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { HMI_W, HMI_H } from '../ui';
import { E3Page } from './E3';
import { DlProvider, useDl } from './shared';
import { DL, BAR_H, STATUS_H } from './theme';
import { BottomBar, StatusBar } from './Bars';
import { HomeScene } from './Home';
import { AppCentre, CameraPage, ClimatePage, ControlsPage, MediaPage, NavPage, SeatsPage } from './Pages';

/**
 * The Denza Z9's centre screen, as DiLink 150 draws it.
 *
 * Home is a bright showroom stage with the car standing on it and a row of cards along the bottom
 * (the e³ platform, the car's status, the music, the seats, the ambient light, the phone); every
 * other page is a deep blue ground with soft blue light, under the same status bar and over the same
 * bottom bar (back, home, the two temperatures, settings, the driver's seat, the demister, the
 * brightness, the camera and the apps), c10_0029-100. What has a counterpart in the 3D car writes
 * the shared vehicle store (the climate, the ambient light, the drive mode).
 */
export function DilinkSurface({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  return (
    <div
      className="hmi-surface dilink relative overflow-hidden"
      style={{ width: HMI_W, height: HMI_H, background: DL.ground, color: DL.text }}
      // Mounted in the 3D cabin this tree still sits in the R3F React tree, so synthetic pointer
      // events would bubble to the Canvas and OrbitControls would read a tap as a drag.
      onPointerDown={(e) => e.stopPropagation()}
      onPointerUp={(e) => e.stopPropagation()}
      onPointerMove={(e) => e.stopPropagation()}
      onWheel={(e) => e.stopPropagation()}
    >
      <style>{`@keyframes dlUp{from{transform:translateY(30px);opacity:0}to{transform:none;opacity:1}}`}</style>
      <DlProvider>
        <Surface vehicle={vehicle} variant={variant} />
      </DlProvider>
    </div>
  );
}

function Surface({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  const { val } = useDl();
  const { hmiScreen, appCentreOpen } = useVehicleStore();

  // the generic screens that have no page of their own here map to the nearest one
  const screen =
    hmiScreen === 'drive' || hmiScreen === 'track' || hmiScreen === 'adas' || hmiScreen === 'settings' || hmiScreen === 'charge'
      ? 'controls'
      : hmiScreen === 'park'
        ? 'camera'
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
    case 'chassis':
      page = <E3Page vehicle={vehicle} />;
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
  const onHome = !page && !appCentreOpen;

  return (
    <>
      <HomeScene vehicle={vehicle} hidden={Boolean(page) || appCentreOpen} />
      {page && (
        <div
          key={screen}
          className="absolute inset-x-0 overflow-hidden"
          style={{ top: full ? 0 : 0, bottom: BAR_H, background: DL.ground, animation: 'dlUp 260ms cubic-bezier(0.2, 0.8, 0.2, 1)' }}
        >
          <div className="absolute inset-x-0" style={{ top: full ? 0 : STATUS_H - 40, bottom: 0 }}>
            {page}
          </div>
        </div>
      )}
      {appCentreOpen && (
        <div className="absolute inset-x-0 overflow-hidden" style={{ top: 0, bottom: BAR_H, background: DL.ground, animation: 'dlUp 260ms cubic-bezier(0.2, 0.8, 0.2, 1)' }}>
          <AppCentre />
        </div>
      )}
      <StatusBar over={onHome ? 'home' : 'page'} />
      <BottomBar over={onHome ? 'home' : 'page'} screen={hmiScreen} />
      {/* the brightness button dims the whole screen */}
      {val.brightness < 100 && (
        <div className="pointer-events-none absolute inset-0 z-50" style={{ background: `rgba(0,0,0,${(100 - val.brightness) / 160})` }} />
      )}
    </>
  );
}
