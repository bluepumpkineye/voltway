'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore, type HmiScreen } from '@/store/vehicle-store';
import { DRIVE_MODES, effectiveRange } from '@/lib/performance';
import {
  HMI_W, HMI_H, cx,
  HomeIcon, ClimateIcon, DriveIcon, NavIcon, MediaIcon, AdasIcon, ControlsIcon,
} from './ui';
import {
  HomeScreen, ClimateScreen, DriveScreen, NavScreen, MediaScreen, AdasScreen, ControlsScreen,
} from './screens';
import { HyperOsSurface } from './hyperos/HyperOsSurface';

const DOCK: { id: HmiScreen; label: string; icon: React.ReactNode }[] = [
  { id: 'home', label: 'Home', icon: <HomeIcon /> },
  { id: 'climate', label: 'Climate', icon: <ClimateIcon /> },
  { id: 'drive', label: 'Drive', icon: <DriveIcon /> },
  { id: 'nav', label: 'Navigation', icon: <NavIcon /> },
  { id: 'media', label: 'Media', icon: <MediaIcon /> },
  { id: 'adas', label: 'Assist', icon: <AdasIcon /> },
  { id: 'controls', label: 'Controls', icon: <ControlsIcon /> },
];

/**
 * The car's central display, as a real DOM tree.
 *
 * Authored at a fixed 1280x800 and scaled by the caller, so the same component
 * renders identically whether it is mounted flat on the page or projected onto
 * the screen quad inside the 3D cabin. A car whose OS has been rebuilt from its
 * maker's own screens gets that skin (HyperOS so far); the rest share the
 * generic one below.
 */
export function HmiSurface({
  vehicle,
  variant,
  className,
}: {
  vehicle: Vehicle;
  variant: Variant;
  className?: string;
}) {
  if (vehicle.cockpit.skin === 'hyperos') return <HyperOsSurface vehicle={vehicle} variant={variant} />;
  return <GenericSurface vehicle={vehicle} variant={variant} className={className} />;
}

function GenericSurface({
  vehicle,
  variant,
  className,
}: {
  vehicle: Vehicle;
  variant: Variant;
  className?: string;
}) {
  const { hmiScreen, setHmiScreen, driveMode, soc, climate } = useVehicleStore();
  const accent = vehicle.cockpit.accentColor;
  const range = effectiveRange(variant, driveMode, soc, climate);
  const modeLabel = DRIVE_MODES.find((m) => m.id === driveMode)?.label ?? '';

  const Screen = {
    home: HomeScreen,
    climate: ClimateScreen,
    drive: DriveScreen,
    nav: NavScreen,
    media: MediaScreen,
    adas: AdasScreen,
    controls: ControlsScreen,
    // HyperOS apps, as their nearest generic screen
    settings: ControlsScreen,
    track: DriveScreen,
  }[hmiScreen];

  return (
    <div
      className={cx('hmi-surface relative flex flex-col overflow-hidden bg-[#07090c]', className)}
      style={{ width: HMI_W, height: HMI_H }}
      // When mounted inside the 3D cabin this tree still sits in the R3F React
      // tree, so synthetic pointer events bubble to the Canvas and OrbitControls
      // reads a tap on the screen as a drag. Swallow them at the surface.
      onPointerDown={(e) => e.stopPropagation()}
      onPointerUp={(e) => e.stopPropagation()}
      onPointerMove={(e) => e.stopPropagation()}
      onWheel={(e) => e.stopPropagation()}
    >
      {/* status bar */}
      <div className="flex h-[52px] shrink-0 items-center gap-4 px-5 text-white/70">
        <div className="flex items-center gap-2.5">
          <span
            className="flex h-7 w-7 items-center justify-center rounded-full text-[13px] font-semibold"
            style={{ background: accent, color: '#08090b' }}
          >
            {vehicle.brand.charAt(0)}
          </span>
          <span className="tnum text-[15px]">{Math.round(soc * 100)}%</span>
          <span className="tnum text-[13px] text-white/35">
            {range ? `${range.km} km` : '--'}
          </span>
        </div>

        <GearSelector accent={accent} />

        <div className="ml-auto flex items-center gap-4 text-[13px]">
          <span
            className="rounded-full px-3 py-1 text-[12px] font-medium uppercase tracking-[0.13em]"
            style={{ background: `${accent}22`, color: accent }}
          >
            {modeLabel}
          </span>
          <span className="text-white/45">{vehicle.cockpit.os}</span>
          <SignalBars />
          <span className="tnum text-white/70">11:35</span>
        </div>
      </div>

      {/* active screen */}
      <div className="min-h-0 flex-1 px-3 pb-2">
        <Screen vehicle={vehicle} variant={variant} accent={accent} />
      </div>

      {/* dock */}
      <div className="flex h-[86px] shrink-0 items-center gap-2 px-3 pb-2">
        {DOCK.map((d) => {
          const active = hmiScreen === d.id;
          return (
            <button
              key={d.id}
              type="button"
              onClick={() => setHmiScreen(d.id)}
              aria-label={d.label}
              aria-current={active ? 'page' : undefined}
              className={cx(
                'flex h-[70px] flex-1 flex-col items-center justify-center gap-1.5 rounded-[18px] transition-all duration-200',
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-white/70',
                active ? 'bg-white/[0.12]' : 'bg-white/[0.04] hover:bg-white/[0.08]',
              )}
              style={active ? { color: accent, boxShadow: `inset 0 0 0 1px ${accent}44` } : { color: 'rgba(255,255,255,0.6)' }}
            >
              {d.icon}
              <span className="text-[12px] font-medium">{d.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function GearSelector({ accent }: { accent: string }) {
  // Park is fixed - this is a showcase, not a driving simulator.
  const gears = ['P', 'R', 'N', 'D'];
  return (
    <div className="flex items-center gap-1.5" aria-label="Gear selector, in Park">
      {gears.map((g) => (
        <span
          key={g}
          className={cx(
            'flex h-7 w-7 items-center justify-center rounded-[8px] text-[14px] font-semibold',
            g === 'P' ? '' : 'text-white/22',
          )}
          style={g === 'P' ? { background: `${accent}26`, color: accent } : undefined}
        >
          {g}
        </span>
      ))}
    </div>
  );
}

function SignalBars() {
  return (
    <svg width="18" height="14" viewBox="0 0 18 14" aria-hidden="true">
      {[0, 1, 2, 3].map((i) => (
        <rect
          key={i}
          x={i * 4.6}
          y={13 - (i + 1) * 3.1}
          width="3"
          height={(i + 1) * 3.1}
          rx="1"
          fill="rgba(255,255,255,0.55)"
        />
      ))}
    </svg>
  );
}
