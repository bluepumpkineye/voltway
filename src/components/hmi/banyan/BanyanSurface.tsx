'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { HMI_W, HMI_H } from '../ui';
import { ChargeScreen } from '../screens';
import { BanyanProvider, useBanyanLocal } from './shared';
import { useBanyan, TOP_BAR_H, BOTTOM_BAR_H } from './theme';
import { StatusBar, BottomBar } from './Bars';
import { HomeScene } from './Home';
import { ControlsPage, ChassisPage, SeatsPage, ClimatePage, NavPage, MediaPage } from './Pages';
import { AppCentre } from './AppCentre';

/**
 * NIO Banyan Smart Cockpit 15.6" AMOLED Central Display Surface.
 *
 * Implements the full interactive NIO Banyan OS (NT2.0 platform) layout:
 * - Top Status Bar with real-time clock, AQI, 5G, and NOMI Mate 2.0 interactive companion
 * - 3D Interactive vehicle desktop with real-time hotspot chips for doors, frunk, tailgate, charge flap, and lights
 * - Executive card stream: NIO Power Swap 3.0, PanoCinema 7.1.4 Dolby Atmos, 4D Dynamic Chassis
 * - Sliding feature sheets for Vehicle Controls, 5-Level Air Suspension, Queen Co-pilot Seat, Tri-zone Climate & Fragrance, and App Centre
 * - Bottom Banyan Smart Dock with dual-zone climate steppers, NOMI home button, and app shortcuts
 */
export function BanyanSurface({
  vehicle,
  variant,
  className,
}: {
  vehicle: Vehicle;
  variant: Variant;
  className?: string;
}) {
  const t = useBanyan();

  return (
    <div
      className={`hmi-surface banyan relative overflow-hidden select-none ${className ?? ''}`}
      style={{
        width: HMI_W,
        height: HMI_H,
        background: t.background,
        color: t.text,
      }}
      // Swallow synthetic pointer events inside 3D cabin to prevent OrbitControls dragging
      onPointerDown={(e) => e.stopPropagation()}
      onPointerUp={(e) => e.stopPropagation()}
      onPointerMove={(e) => e.stopPropagation()}
      onWheel={(e) => e.stopPropagation()}
    >
      <style>{`
        @keyframes banyanSlideUp {
          from { transform: translateY(40px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        @keyframes nomiPop {
          from { transform: translateY(-8px) scale(0.95); opacity: 0; }
          to { transform: translateY(0) scale(1); opacity: 1; }
        }
      `}</style>
      <BanyanProvider>
        <SurfaceInner vehicle={vehicle} variant={variant} />
      </BanyanProvider>
    </div>
  );
}

function SurfaceInner({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  const t = useBanyan();
  const { hmiScreen, setHmiScreen } = useVehicleStore();
  const { brightness, notification } = useBanyanLocal();
  const [appsOpen, setAppsOpen] = React.useState(false);

  let page: React.ReactNode = null;
  let isFull = false;

  switch (hmiScreen) {
    case 'controls':
      page = <ControlsPage vehicle={vehicle} variant={variant} />;
      break;
    case 'chassis':
      page = <ChassisPage vehicle={vehicle} variant={variant} />;
      break;
    case 'seats':
      page = <SeatsPage vehicle={vehicle} />;
      break;
    case 'climate':
      page = <ClimatePage vehicle={vehicle} />;
      break;
    case 'charge':
      page = <ChargeScreen vehicle={vehicle} variant={variant} accent={t.accent} />;
      break;
    case 'nav':
      page = <NavPage />;
      isFull = true;
      break;
    case 'media':
      page = <MediaPage />;
      break;
    default:
      break;
  }

  const isHome = !page && !appsOpen;

  return (
    <>
      {/* 1. Base 3D Vehicle Desktop Scene */}
      <div className={isHome ? 'block h-full' : 'hidden'}>
        <HomeScene
          vehicle={vehicle}
          variant={variant}
          onScreen={(s) => {
            setAppsOpen(false);
            setHmiScreen(s);
          }}
        />
      </div>

      {/* 2. Slide-up Feature Page Sheet */}
      {page && !appsOpen && (
        <div
          key={hmiScreen}
          className="absolute inset-x-0 overflow-hidden z-20"
          style={{
            top: isFull ? 0 : TOP_BAR_H,
            bottom: BOTTOM_BAR_H,
            background: t.sheet,
            animation: 'banyanSlideUp 260ms cubic-bezier(0.16, 1, 0.3, 1)',
            boxShadow: isFull ? undefined : '0 -10px 30px rgba(0,0,0,0.5)',
          }}
        >
          {page}
        </div>
      )}

      {/* 3. Slide-up App Drawer */}
      {appsOpen && (
        <div
          className="absolute inset-x-0 z-30 overflow-hidden"
          style={{
            top: TOP_BAR_H,
            bottom: BOTTOM_BAR_H,
            background: t.sheet,
            animation: 'banyanSlideUp 260ms cubic-bezier(0.16, 1, 0.3, 1)',
          }}
        >
          <AppCentre
            onSelectScreen={(s) => {
              setAppsOpen(false);
              setHmiScreen(s);
            }}
            onClose={() => setAppsOpen(false)}
          />
        </div>
      )}

      {/* 4. Top Status Bar */}
      <StatusBar />

      {/* 5. Bottom Banyan Smart Dock */}
      <BottomBar
        screen={hmiScreen}
        onScreen={(s) => {
          setAppsOpen(false);
          setHmiScreen(s);
        }}
        appCentreOpen={appsOpen}
        onToggleApps={() => setAppsOpen(!appsOpen)}
      />

      {/* 6. Dynamic In-Car Toast Notification */}
      {notification && (
        <div className="pointer-events-none absolute bottom-28 left-1/2 -translate-x-1/2 z-50 rounded-2xl bg-black/85 px-6 py-3 text-[14px] font-medium text-white shadow-2xl ring-1 ring-white/20 backdrop-blur-md">
          {notification}
        </div>
      )}

      {/* 7. Brightness Overlay */}
      {brightness < 100 && (
        <div
          className="pointer-events-none absolute inset-0 z-50"
          style={{ background: `rgba(0,0,0,${(100 - brightness) / 150})` }}
        />
      )}
    </>
  );
}
