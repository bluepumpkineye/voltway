'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { effectiveRange } from '@/lib/performance';
import { cx } from '../ui';
import { HY, STATUS_H, DOCK_H } from './theme';
import * as Ic from './icons';
import { TRACKS, useClock } from './shared';

/* ------------------------------------------------------------ status bar */

/**
 * HyperOS' status bar. Left: the driver's avatar, the range with its green
 * battery bar and cycle, the car tell-tale, PRND with the gear lit, and the
 * low-beam lamp when the headlights are on. Right: outside temperature,
 * messages, dashcam, phone link, signal, the time.
 */
export function StatusBar({ variant }: { variant: Variant }) {
  const { soc, driveMode, climate, gear, setGear, headlightsOn } = useVehicleStore();
  const range = effectiveRange(variant, driveMode, soc, climate);
  const time = useClock();

  return (
    <div
      className="relative z-20 flex shrink-0 items-center gap-4 px-6 text-[15px]"
      style={{ height: STATUS_H, color: HY.text }}
    >
      <span
        className="h-[26px] w-[26px] shrink-0 rounded-full"
        style={{ background: 'radial-gradient(circle at 35% 30%, #f3d7b6, #b97a52 60%, #6b3f28)' }}
        aria-hidden
      />
      <span className="flex flex-col justify-center leading-none" aria-label={`Range ${range?.km ?? '--'} km`}>
        <span className="flex items-baseline gap-1">
          <span className="tnum text-[14px] font-medium">{range ? `${range.km}km` : '--'}</span>
          <span className="text-[10px]" style={{ color: HY.text3 }}>{range?.cycle}</span>
        </span>
        <span className="mt-[3px] h-[3px] w-[64px] overflow-hidden rounded-full" style={{ background: 'rgba(255,255,255,0.14)' }}>
          <span className="block h-full rounded-full" style={{ width: `${soc * 100}%`, background: HY.green }} />
        </span>
      </span>
      <Ic.CarGlyph size={20} style={{ color: HY.green }} />
      <span className="flex items-center gap-[7px] text-[17px] font-semibold tracking-[0.02em]" role="group" aria-label={`Gear ${gear}`}>
        {(['P', 'R', 'N', 'D'] as const).map((g) => {
          const on = g === gear;
          // the showroom car can be put in D to preview the driving desktop
          const tappable = g === 'P' || g === 'D';
          return (
            <button
              key={g}
              type="button"
              disabled={!tappable}
              onClick={() => tappable && setGear(g)}
              aria-pressed={on}
              className="leading-none focus:outline-none disabled:cursor-default"
              style={{ color: on ? '#fff' : 'rgba(255,255,255,0.28)' }}
            >
              {g}
            </button>
          );
        })}
      </span>
      {headlightsOn && <Ic.LowBeam size={20} style={{ color: HY.green }} />}

      <span className="ml-auto flex items-center gap-4" style={{ color: HY.text }}>
        <span className="tnum text-[15px]">26°</span>
        <Ic.Message size={19} />
        <Ic.Dashcam size={19} />
        <Ic.Link size={19} />
        <Ic.Signal size={17} />
        <span className="tnum min-w-[44px] text-right text-[16px] font-medium">{time.hm}</span>
      </span>
    </div>
  );
}

/* ------------------------------------------------------------------ dock */

const APPS = [
  { id: 'settings', label: 'Vehicle settings', icon: <Ic.AppVehicle /> },
  { id: 'nav', label: 'Navigation', icon: <Ic.AppNav /> },
  { id: 'media', label: 'Music', icon: <Ic.AppMusic /> },
  { id: 'track', label: 'Xiaomi Track Master', icon: <Ic.AppTrack /> },
  { id: 'apps', label: 'All apps', icon: <Ic.AppApps /> },
] as const;
export type DockApp = (typeof APPS)[number]['id'];

/**
 * The dock, always on screen: home, the driver's temperature, the app icons,
 * the music mini player, the passenger's temperature and the volume.
 * Tapping a temperature opens the climate panel, as on the car.
 */
export function Dock({
  vehicle,
  onApp,
  drawerOpen,
}: {
  vehicle: Vehicle;
  onApp: (id: DockApp) => void;
  drawerOpen: boolean;
}) {
  const {
    hmiScreen, setHmiScreen, climate, patchClimate, climateOpen, setClimateOpen, media, patchMedia,
  } = useVehicleStore();
  const track = TRACKS[media.trackIndex % TRACKS.length];
  const hasTrack = Boolean(vehicle.cockpit.driveModes?.some((m) => m.group === 'track'));

  return (
    <div className="relative z-30 flex shrink-0 items-center gap-2 px-5" style={{ height: DOCK_H, color: HY.text }}>
      <DockButton label="Home" active={hmiScreen === 'home' && !climateOpen && !drawerOpen} onClick={() => setHmiScreen('home')}>
        <Ic.Home size={26} />
      </DockButton>

      <Temp
        value={climate.driverTempC}
        onChange={(v) => patchClimate({ driverTempC: v })}
        onOpen={() => setClimateOpen(!climateOpen)}
        label="Driver temperature"
      />

      <div className="mx-auto flex items-center gap-4">
        {APPS.filter((a) => a.id !== 'track' || hasTrack).map((a) => {
          const on = a.id === 'apps' ? drawerOpen : hmiScreen === a.id && !drawerOpen;
          return (
            <button
              key={a.id}
              type="button"
              aria-label={a.label}
              aria-current={on ? 'page' : undefined}
              onClick={() => onApp(a.id)}
              className="relative rounded-[13px] transition-transform active:scale-95 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
            >
              {a.icon}
              {on && <span className="absolute -bottom-[7px] left-1/2 h-[3px] w-[14px] -translate-x-1/2 rounded-full bg-white/80" />}
            </button>
          );
        })}
      </div>

      {/* mini player */}
      <div className="flex w-[260px] items-center gap-3 rounded-[14px] px-2 py-1.5" style={{ background: 'rgba(255,255,255,0.05)' }}>
        <button
          type="button"
          aria-label="Open music"
          onClick={() => setHmiScreen('media')}
          className="h-[40px] w-[40px] shrink-0 rounded-[9px] focus:outline-none"
          style={{ background: track.art }}
        />
        <span className="min-w-0 flex-1">
          <span className="block truncate text-[13.5px] font-medium">{track.title}</span>
          <span className="mt-1 block h-[3px] overflow-hidden rounded-full" style={{ background: 'rgba(255,255,255,0.15)' }}>
            <span className="block h-full w-[38%] rounded-full bg-white/80" />
          </span>
        </span>
        <button
          type="button"
          aria-label={media.playing ? 'Pause' : 'Play'}
          onClick={() => patchMedia({ playing: !media.playing })}
          className="flex h-8 w-8 items-center justify-center rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
        >
          {media.playing ? <Ic.Pause size={20} /> : <Ic.Play size={20} />}
        </button>
        <button
          type="button"
          aria-label="Next track"
          onClick={() => patchMedia({ trackIndex: (media.trackIndex + 1) % TRACKS.length })}
          className="flex h-8 w-8 items-center justify-center rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
        >
          <Ic.Next size={18} />
        </button>
      </div>

      <Temp
        value={climate.passengerTempC}
        onChange={(v) => patchClimate({ passengerTempC: v })}
        onOpen={() => setClimateOpen(!climateOpen)}
        label="Passenger temperature"
      />
      <DockButton label="Volume" onClick={() => patchMedia({ volume: media.volume >= 80 ? 20 : media.volume + 20 })}>
        <Ic.Volume size={24} />
      </DockButton>
    </div>
  );
}

function DockButton({
  label,
  active,
  onClick,
  children,
}: {
  label: string;
  active?: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-current={active ? 'page' : undefined}
      onClick={onClick}
      className={cx(
        'flex h-[52px] w-[52px] shrink-0 items-center justify-center rounded-[14px] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60',
        active ? 'bg-white/[0.1]' : 'hover:bg-white/[0.06]',
      )}
    >
      {children}
    </button>
  );
}

/** "< 22.0° >": chevrons step half a degree, the number opens the climate panel. */
function Temp({
  value,
  onChange,
  onOpen,
  label,
}: {
  value: number;
  onChange: (v: number) => void;
  onOpen: () => void;
  label: string;
}) {
  const step = (d: number) => onChange(Math.min(32, Math.max(16, Math.round((value + d) * 2) / 2)));
  return (
    <div className="flex shrink-0 items-center" role="group" aria-label={label}>
      <button type="button" aria-label={`Lower ${label}`} onClick={() => step(-0.5)} className="flex h-11 w-8 items-center justify-center text-white/55 hover:text-white focus:outline-none">
        <Ic.ChevronL size={20} />
      </button>
      <button type="button" aria-label={`${label} ${value.toFixed(1)} degrees, open climate`} onClick={onOpen} className="tnum min-w-[62px] text-center text-[21px] font-light focus:outline-none">
        {value.toFixed(1)}°
      </button>
      <button type="button" aria-label={`Raise ${label}`} onClick={() => step(0.5)} className="flex h-11 w-8 items-center justify-center text-white/55 hover:text-white focus:outline-none">
        <Ic.ChevronR size={20} />
      </button>
    </div>
  );
}
