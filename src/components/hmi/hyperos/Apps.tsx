'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore, type HmiScreen, type SettingsPage } from '@/store/vehicle-store';
import { cx } from '../ui';
import { HY } from './theme';
import * as Ic from './icons';
import { MapArt, useRangeKm } from './Desktop';
import { TRACKS, mmss } from './shared';

/* --------------------------------------------------------------- climate */

/**
 * The climate panel, raised from the dock's temperatures: both zones, fan,
 * A/C, auto, sync, recirculation, defrost and seat heating.
 */
export function ClimatePanel() {
  const { climate, patchClimate, setClimateOpen } = useVehicleStore();
  const [defrostF, setDefrostF] = React.useState(false);
  const [defrostR, setDefrostR] = React.useState(false);
  const [recirc, setRecirc] = React.useState(false);
  const [auto, setAuto] = React.useState(true);

  const step = (key: 'driverTempC' | 'passengerTempC', d: number) =>
    patchClimate({ [key]: Math.min(32, Math.max(16, Math.round((climate[key] + d) * 2) / 2)) });

  return (
    <div className="absolute inset-0 z-20">
      <button type="button" aria-label="Close climate" onClick={() => setClimateOpen(false)} className="absolute inset-0 bg-black/40 focus:outline-none" />
      <div
        className="hy-sheet absolute inset-x-3 bottom-0 rounded-t-[28px] px-8 pb-6 pt-4"
        style={{ background: 'rgba(30,31,35,0.97)', color: HY.text, boxShadow: '0 -20px 60px -20px rgba(0,0,0,0.8)' }}
        role="dialog"
        aria-label="Climate"
      >
        <div className="mx-auto mb-4 h-[5px] w-[44px] rounded-full bg-white/25" />
        <div className="grid grid-cols-[220px_1fr_220px] items-center gap-8">
          <ZoneTemp label="Driver" value={climate.driverTempC} onStep={(d) => step('driverTempC', d)} />
          <div className="flex flex-col gap-5">
            <div className="flex items-center gap-4">
              <Ic.Fan size={26} style={{ color: HY.text2 }} />
              <div className="flex flex-1 gap-1.5" role="group" aria-label="Fan speed">
                {[1, 2, 3, 4, 5].map((i) => (
                  <button
                    key={i}
                    type="button"
                    aria-label={`Fan speed ${i}`}
                    aria-pressed={i <= climate.fanSpeed}
                    onClick={() => patchClimate({ fanSpeed: i === climate.fanSpeed ? i - 1 : i })}
                    className="h-[38px] flex-1 rounded-[10px] transition-colors focus:outline-none"
                    style={{ background: i <= climate.fanSpeed ? HY.blue : HY.panel2 }}
                  />
                ))}
              </div>
              <span className="tnum w-6 text-center text-[18px]">{climate.fanSpeed}</span>
            </div>
            <div className="grid grid-cols-4 gap-3">
              <Pill on={climate.acOn} onClick={() => patchClimate({ acOn: !climate.acOn })}>A/C</Pill>
              <Pill on={auto} onClick={() => setAuto(!auto)}>AUTO</Pill>
              <Pill on={climate.sync} onClick={() => patchClimate({ sync: !climate.sync })}>SYNC</Pill>
              <Pill on={recirc} onClick={() => setRecirc(!recirc)} label="Recirculation"><Ic.Recirc size={22} /></Pill>
            </div>
          </div>
          <ZoneTemp label="Passenger" value={climate.passengerTempC} onStep={(d) => step('passengerTempC', d)} />
        </div>
        <div className="mt-6 grid grid-cols-4 gap-3">
          <SeatHeat label="Driver seat" value={climate.seatHeatDriver} onChange={(v) => patchClimate({ seatHeatDriver: v })} />
          <Pill on={defrostF} onClick={() => setDefrostF(!defrostF)} label="Front defrost" tall>
            <Ic.Defrost size={24} /> <span className="ml-2 text-[14px]">Front</span>
          </Pill>
          <Pill on={defrostR} onClick={() => setDefrostR(!defrostR)} label="Rear defrost" tall>
            <Ic.Defrost size={24} /> <span className="ml-2 text-[14px]">Rear</span>
          </Pill>
          <SeatHeat label="Passenger seat" value={climate.seatHeatPassenger} onChange={(v) => patchClimate({ seatHeatPassenger: v })} />
        </div>
      </div>
    </div>
  );
}

function ZoneTemp({ label, value, onStep }: { label: string; value: number; onStep: (d: number) => void }) {
  return (
    <div className="flex flex-col items-center gap-2">
      <span className="text-[13px]" style={{ color: HY.text2 }}>{label}</span>
      <div className="flex items-center gap-2">
        <button type="button" aria-label={`Lower ${label} temperature`} onClick={() => onStep(-0.5)} className="flex h-12 w-12 items-center justify-center rounded-full focus:outline-none" style={{ background: HY.panel2 }}>
          <Ic.ChevronL size={22} />
        </button>
        <span className="tnum w-[100px] text-center text-[44px] font-extralight">{value.toFixed(1)}°</span>
        <button type="button" aria-label={`Raise ${label} temperature`} onClick={() => onStep(0.5)} className="flex h-12 w-12 items-center justify-center rounded-full focus:outline-none" style={{ background: HY.panel2 }}>
          <Ic.ChevronR size={22} />
        </button>
      </div>
    </div>
  );
}

function Pill({
  on,
  onClick,
  children,
  label,
  tall,
}: {
  on: boolean;
  onClick: () => void;
  children: React.ReactNode;
  label?: string;
  tall?: boolean;
}) {
  return (
    <button
      type="button"
      aria-pressed={on}
      aria-label={label}
      onClick={onClick}
      className={cx('flex items-center justify-center rounded-[14px] text-[15px] font-semibold tracking-wide transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60', tall ? 'h-[58px]' : 'h-[46px]')}
      style={{ background: on ? HY.blue : HY.panel2, color: on ? '#fff' : HY.text }}
    >
      {children}
    </button>
  );
}

/** Seat heating: tap to step 0 > 1 > 2 > 3 > 0, three orange bars. */
function SeatHeat({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <button
      type="button"
      aria-label={`${label} heating level ${value}`}
      onClick={() => onChange((value + 1) % 4)}
      className="flex h-[58px] items-center justify-center gap-3 rounded-[14px] focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
      style={{ background: HY.panel2, color: value ? HY.orange : HY.text }}
    >
      <Ic.SeatHeat size={26} />
      <span className="flex flex-col gap-[3px]" aria-hidden>
        {[3, 2, 1].map((i) => (
          <span key={i} className="h-[3px] w-[14px] rounded-full" style={{ background: i <= value ? HY.orange : 'rgba(255,255,255,0.18)' }} />
        ))}
      </span>
    </button>
  );
}

/* ------------------------------------------------------------ navigation */

/** Navigation, full screen: the route, and how far the charge reaches in this mode. */
export function NavApp({ variant }: { variant: Variant }) {
  const range = useRangeKm(variant);
  // ring radius in map units: ~1.2 px per km at this zoom, clamped to the map
  const ring = Math.max(40, Math.min(360, (range?.km ?? 0) * 0.6));
  return (
    <div className="absolute inset-0 px-4 pb-2 pt-1">
      <div className="relative h-full overflow-hidden rounded-[24px]">
        <MapArt className="absolute inset-0 h-full w-full" ring={ring} w={1248} h={670} />
        <div className="absolute left-4 top-4 w-[330px] rounded-[20px] p-5" style={{ background: 'rgba(22,24,28,0.94)', color: HY.text }}>
          <div className="flex items-center gap-3">
            <svg width="46" height="46" viewBox="0 0 24 24" aria-hidden>
              <path fill="none" stroke={HY.blue} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" d="M7 20v-7.5a3 3 0 0 1 3-3h8M14.5 6l3.5 3.5-3.5 3.5" />
            </svg>
            <span>
              <span className="tnum text-[34px] font-semibold leading-none">800</span>
              <span className="ml-1 text-[15px]" style={{ color: HY.text2 }}>m</span>
              <span className="mt-1 block text-[15px]">Longteng Avenue</span>
            </span>
          </div>
          <div className="mt-4 border-t pt-4" style={{ borderColor: HY.line }}>
            <div className="text-[13px]" style={{ color: HY.text3 }}>Destination</div>
            <div className="mt-1 text-[18px]">Shanghai International Circuit</div>
            <div className="tnum mt-1 text-[14px]" style={{ color: HY.text2 }}>38 km · 44 min · Jiading</div>
          </div>
        </div>
        <div className="absolute bottom-4 right-4 w-[300px] rounded-[20px] p-5" style={{ background: 'rgba(22,24,28,0.94)', color: HY.text }}>
          <div className="text-[13px]" style={{ color: HY.text3 }}>Range ring</div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span className="tnum text-[34px] font-light">{range?.km ?? '--'}</span>
            <span className="text-[14px]" style={{ color: HY.text2 }}>km · {range?.cycle}</span>
          </div>
          <p className="mt-2 text-[13px] leading-snug" style={{ color: HY.text2 }}>
            The dashed circle is how far this charge reaches in the current mode. Change mode or climate and it moves.
          </p>
        </div>
      </div>
    </div>
  );
}

/* ----------------------------------------------------------------- music */

export function MusicApp() {
  const { media, patchMedia } = useVehicleStore();
  const track = TRACKS[media.trackIndex % TRACKS.length];
  const at = Math.round(track.duration * 0.38);
  return (
    <div className="absolute inset-0 px-4 pb-2 pt-1">
      <div
        className="grid h-full grid-cols-[1fr_400px] gap-8 rounded-[24px] p-10"
        style={{ background: `linear-gradient(135deg, ${track.tint} 0%, #17151f 60%, ${HY.panel} 100%)`, color: HY.text }}
      >
        <div className="flex items-center gap-10">
          <div className="h-[340px] w-[340px] shrink-0 rounded-[26px] shadow-2xl" style={{ background: track.art }} />
          <div className="min-w-0 flex-1">
            <div className="truncate text-[34px] font-medium">{track.title}</div>
            <div className="mt-2 text-[18px]" style={{ color: HY.text2 }}>{track.artist}</div>
            <div className="mt-10 h-[5px] overflow-hidden rounded-full bg-white/15">
              <div className="h-full rounded-full bg-white/85" style={{ width: `${(at / track.duration) * 100}%` }} />
            </div>
            <div className="tnum mt-2 flex justify-between text-[13px]" style={{ color: HY.text3 }}>
              <span>{mmss(at)}</span><span>{mmss(track.duration)}</span>
            </div>
            <div className="mt-6 flex items-center gap-12">
              <button type="button" aria-label="Previous track" onClick={() => patchMedia({ trackIndex: (media.trackIndex + TRACKS.length - 1) % TRACKS.length })} className="focus:outline-none"><Ic.Prev size={32} /></button>
              <button type="button" aria-label={media.playing ? 'Pause' : 'Play'} onClick={() => patchMedia({ playing: !media.playing })} className="flex h-[72px] w-[72px] items-center justify-center rounded-full bg-white text-black focus:outline-none">
                {media.playing ? <Ic.Pause size={34} /> : <Ic.Play size={34} />}
              </button>
              <button type="button" aria-label="Next track" onClick={() => patchMedia({ trackIndex: (media.trackIndex + 1) % TRACKS.length })} className="focus:outline-none"><Ic.Next size={32} /></button>
            </div>
          </div>
        </div>
        <div className="flex flex-col gap-2 overflow-hidden">
          <div className="mb-2 text-[15px]" style={{ color: HY.text2 }}>Up next</div>
          {TRACKS.map((t, i) => (
            <button
              key={t.title}
              type="button"
              onClick={() => patchMedia({ trackIndex: i, playing: true })}
              className="flex items-center gap-4 rounded-[16px] px-3 py-2.5 text-left transition-colors focus:outline-none"
              style={{ background: i === media.trackIndex % TRACKS.length ? 'rgba(255,255,255,0.1)' : 'transparent' }}
            >
              <span className="h-[52px] w-[52px] shrink-0 rounded-[10px]" style={{ background: t.art }} />
              <span className="min-w-0 flex-1">
                <span className="block truncate text-[16px]">{t.title}</span>
                <span className="block truncate text-[13px]" style={{ color: HY.text3 }}>{t.artist}</span>
              </span>
              <span className="tnum text-[13px]" style={{ color: HY.text3 }}>{mmss(t.duration)}</span>
            </button>
          ))}
          <div className="mt-auto flex items-center gap-3 rounded-[16px] px-4 py-3" style={{ background: 'rgba(255,255,255,0.06)' }}>
            <Ic.Volume size={22} />
            <input
              type="range"
              min={0}
              max={100}
              value={media.volume}
              onChange={(e) => patchMedia({ volume: Number(e.target.value) })}
              aria-label="Volume"
              className="h-1.5 flex-1 cursor-pointer appearance-none rounded-full bg-white/20"
              style={{ accentColor: '#fff' }}
            />
            <span className="tnum w-8 text-right text-[13px]">{media.volume}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------ app drawer */

/** Every app, from the dock's grid icon. */
export function AppDrawer({ vehicle, onClose }: { vehicle: Vehicle; onClose: () => void }) {
  const { setHmiScreen, openSettings, setClimateOpen } = useVehicleStore();
  const hasTrack = Boolean(vehicle.cockpit.driveModes?.some((m) => m.group === 'track'));
  const go = (s: HmiScreen) => { setHmiScreen(s); onClose(); };
  const page = (p: SettingsPage) => { openSettings(p); onClose(); };
  const apps: { label: string; icon: React.ReactNode; run: () => void }[] = [
    { label: 'Settings', icon: <Ic.AppVehicle />, run: () => page('vehicle') },
    { label: 'Navigation', icon: <Ic.AppNav />, run: () => go('nav') },
    { label: 'Music', icon: <Ic.AppMusic />, run: () => go('media') },
    ...(hasTrack ? [{ label: 'Track Master', icon: <Ic.AppTrack />, run: () => go('track') }] : []),
    { label: 'Climate', icon: <Ic.AppTile from="#3ea8ff" to="#1665d8"><Ic.Fan size={24} /></Ic.AppTile>, run: () => { go('home'); setClimateOpen(true); } },
    { label: 'Xiaomi HAD', icon: <Ic.AppTile from="#5b8cff" to="#3048c9"><Ic.MenuAssist size={24} /></Ic.AppTile>, run: () => page('assist') },
    { label: 'Energy', icon: <Ic.AppTile from="#46d17a" to="#15964a"><Ic.MenuCharging size={24} /></Ic.AppTile>, run: () => page('charging') },
    { label: 'Lights', icon: <Ic.AppTile from="#ffcf4a" to="#e08a00"><Ic.MenuLights size={24} /></Ic.AppTile>, run: () => page('lights') },
  ];
  return (
    <div className="absolute inset-0 z-20">
      <button type="button" aria-label="Close apps" onClick={onClose} className="absolute inset-0 bg-black/55 backdrop-blur-sm focus:outline-none" />
      <div className="hy-sheet absolute inset-x-[200px] bottom-3 grid grid-cols-4 gap-y-7 rounded-[28px] px-10 py-9" style={{ background: 'rgba(30,31,35,0.97)', color: HY.text }}>
        {apps.map((a) => (
          <button key={a.label} type="button" onClick={a.run} className="flex flex-col items-center gap-2.5 focus:outline-none">
            <span className="scale-[1.3]">{a.icon}</span>
            <span className="mt-2 text-[14px]">{a.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
