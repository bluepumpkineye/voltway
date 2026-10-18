'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore, type HmiScreen } from '@/store/vehicle-store';
import { effectiveRange, type DriveMode } from '@/lib/performance';
import { useChargeReadout } from '@/lib/tech/session';
import { tapChargeFlap } from '@/lib/tech/actions';
import { cx, Card, PlayIcon, PauseIcon, NextIcon, PrevIcon } from '../ui';
import { useBanyan } from './theme';
import { useBanyanLocal } from './shared';
import {
  NioPowerSwapIcon,
  Chassis4DIcon,
  DolbyAtmosIcon,
  AirSuspensionIcon,
  LightLowIcon,
} from './icons';

const TRACKS = [
  { title: 'Neon Arterial (PanoCinema 7.1.4)', artist: 'NIO Radio · 蔚来沉浸声', album: 'Night Drive' },
  { title: 'Horizon Glow (Dolby Atmos)', artist: 'Shanghai Tape Club', album: 'Soundtrack of Tomorrow' },
  { title: 'Quiet Electric Soul', artist: 'Silk Road Ambient', album: 'Acoustic Suite' },
];

export function HomeScene({
  vehicle,
  variant,
  onScreen,
}: {
  vehicle: Vehicle;
  variant: Variant;
  onScreen: (s: HmiScreen) => void;
}) {
  const t = useBanyan();
  const {
    soc,
    driveMode,
    setDriveMode,
    climate,
    openings,
    toggleOpening,
    headlightsOn,
    setHeadlights,
    media,
    patchMedia,
    rideLevel,
  } = useVehicleStore();

  const live = useChargeReadout();
  const { speakNomi } = useBanyanLocal();
  const range = effectiveRange(variant, driveMode, soc, climate);
  const track = TRACKS[media.trackIndex % TRACKS.length];

  const isCharging = live?.phase === 'charging';
  const RIDE_NAMES = ['Very High', 'High', 'Standard', 'Low', 'Very Low'];
  const rideName = RIDE_NAMES[rideLevel] ?? 'Standard';

  const onSelectMode = (mId: string) => {
    setDriveMode(mId as DriveMode);
    const m = vehicle.cockpit.driveModes?.find((d) => d.id === mId);
    speakNomi(`Switched to ${m?.label ?? mId} mode!`, mId.includes('sport') ? 'sport' : 'happy');
  };

  return (
    <div className="grid h-full grid-cols-[1.28fr_1fr] gap-4 p-6 pt-14 pb-24 select-none">
      {/* LEFT: 3D Vehicle Interactive Stage with Hotspots */}
      <div className="relative flex flex-col justify-between rounded-[26px] bg-white/[0.035] p-6 ring-1 ring-white/[0.07] overflow-hidden">
        {/* Top Header metrics */}
        <div className="flex items-center justify-between z-10">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[26px] font-semibold tracking-tight text-white">
                {vehicle.brand} {vehicle.model}
              </span>
              <span className="rounded-md bg-[#00C2A8]/15 px-2 py-0.5 text-[11px] font-bold text-[#00C2A8]">
                Banyan 2.4
              </span>
            </div>
            <div className="mt-1 flex items-center gap-3 text-[13px] text-white/50">
              <span>{variant.name}</span>
              <span>·</span>
              <span>AWD Dual-Motor 520 kW</span>
            </div>
          </div>

          {/* Air suspension height indicator */}
          <button
            type="button"
            onClick={() => onScreen('chassis')}
            className="flex items-center gap-2 rounded-xl bg-white/[0.06] px-3.5 py-2 ring-1 ring-white/10 hover:bg-white/[0.12] transition-colors"
          >
            <AirSuspensionIcon size={18} />
            <div className="text-left text-[12px]">
              <span className="block text-white/40 leading-none">Air Suspension</span>
              <span className="block font-medium text-white/90 leading-tight mt-0.5">
                {rideName}
              </span>
            </div>
          </button>
        </div>

        {/* Center Vehicle Perspective Hero + Interactive Hotspots */}
        <div className="relative my-auto flex h-[280px] w-full items-center justify-center">
          {/* Subtle pedestal illumination */}
          <div
            className="absolute inset-x-8 bottom-4 h-24 rounded-full opacity-40 blur-3xl pointer-events-none"
            style={{ background: `radial-gradient(circle, ${t.accent} 0%, rgba(0,0,0,0) 70%)` }}
          />

          {/* Perspective 3/4 Render */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={`/hmi/${vehicle.slug}/car34.webp`}
            alt={`${vehicle.brand} ${vehicle.model}`}
            draggable={false}
            className="max-h-[250px] w-auto max-w-[92%] object-contain select-none drop-shadow-[0_20px_35px_rgba(0,0,0,0.7)]"
          />

          {/* Hotspot: Frunk (Bonnet) */}
          <button
            type="button"
            onClick={() => {
              toggleOpening('frunk');
              speakNomi(openings.frunk ? 'Frunk closed' : 'Frunk opened');
            }}
            className={cx(
              'absolute left-[16%] top-[34%] flex h-8 items-center gap-1.5 rounded-full px-2.5 text-[11px] font-semibold transition-all duration-200 z-10',
              openings.frunk
                ? 'bg-amber-400 text-black shadow-[0_0_12px_rgba(251,191,36,0.8)]'
                : 'bg-black/70 text-white/80 ring-1 ring-white/20 hover:bg-white/20',
            )}
            title="Front Trunk"
          >
            <span>Frunk</span>
          </button>

          {/* Hotspot: Driver Door (FL) */}
          <button
            type="button"
            onClick={() => toggleOpening('doorFL')}
            className={cx(
              'absolute left-[36%] top-[38%] flex h-7 items-center gap-1 rounded-full px-2 text-[10px] font-medium transition-all duration-200 z-10',
              openings.doorFL
                ? 'bg-amber-400 text-black shadow-[0_0_10px_rgba(251,191,36,0.8)]'
                : 'bg-black/70 text-white/80 ring-1 ring-white/20 hover:bg-white/20',
            )}
            title="Driver Door"
          >
            <span>Driver Door</span>
          </button>

          {/* Hotspot: Rear Left Door (RL) */}
          <button
            type="button"
            onClick={() => toggleOpening('doorRL')}
            className={cx(
              'absolute left-[54%] top-[38%] flex h-7 items-center gap-1 rounded-full px-2 text-[10px] font-medium transition-all duration-200 z-10',
              openings.doorRL
                ? 'bg-amber-400 text-black shadow-[0_0_10px_rgba(251,191,36,0.8)]'
                : 'bg-black/70 text-white/80 ring-1 ring-white/20 hover:bg-white/20',
            )}
            title="Rear Left Door"
          >
            <span>Rear Door</span>
          </button>

          {/* Hotspot: Tailgate (Boot) */}
          <button
            type="button"
            onClick={() => {
              toggleOpening('boot');
              speakNomi(openings.boot ? 'Tailgate closed' : 'Tailgate opened');
            }}
            className={cx(
              'absolute right-[10%] top-[40%] flex h-8 items-center gap-1.5 rounded-full px-2.5 text-[11px] font-semibold transition-all duration-200 z-10',
              openings.boot
                ? 'bg-amber-400 text-black shadow-[0_0_12px_rgba(251,191,36,0.8)]'
                : 'bg-black/70 text-white/80 ring-1 ring-white/20 hover:bg-white/20',
            )}
            title="Tailgate"
          >
            <span>Boot</span>
          </button>

          {/* Hotspot: Charge Port Flap */}
          <button
            type="button"
            onClick={() => {
              tapChargeFlap();
              speakNomi(openings.charge ? 'Charging flap closed' : 'Charging flap opened', 'charging');
            }}
            className={cx(
              'absolute right-[21%] top-[30%] flex h-8 items-center gap-1.5 rounded-full px-2.5 text-[11px] font-semibold transition-all duration-200 z-10',
              openings.charge || isCharging
                ? 'bg-[#00C2A8] text-black shadow-[0_0_14px_rgba(0,194,168,0.9)]'
                : 'bg-black/70 text-white/80 ring-1 ring-white/20 hover:bg-white/20',
            )}
            title="Charge Port Flap"
          >
            <span>⚡ Charge</span>
          </button>

          {/* Hotspot: Headlights */}
          <button
            type="button"
            onClick={() => {
              setHeadlights(!headlightsOn);
              speakNomi(headlightsOn ? 'Headlights turned off' : 'Headlights turned on');
            }}
            className={cx(
              'absolute left-[8%] bottom-[20%] flex h-8 items-center gap-1.5 rounded-full px-3 text-[11px] font-semibold transition-all duration-200 z-10',
              headlightsOn
                ? 'bg-white text-black shadow-[0_0_15px_rgba(255,255,255,0.8)]'
                : 'bg-black/70 text-white/80 ring-1 ring-white/20 hover:bg-white/20',
            )}
            title="Headlamps"
          >
            <LightLowIcon size={14} />
            <span>Lights</span>
          </button>
        </div>

        {/* Bottom Quick Status Strip */}
        <div className="flex items-center justify-between border-t border-white/[0.08] pt-4 z-10">
          <div className="flex items-center gap-4">
            <span className="text-[13px] text-white/45">Quick Drive Modes:</span>
            <div className="flex gap-2">
              {(vehicle.cockpit.driveModes ?? []).slice(0, 4).map((m) => {
                const active = driveMode === m.id;
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => onSelectMode(m.id)}
                    className={cx(
                      'rounded-xl px-3.5 py-1.5 text-[12px] font-medium transition-all',
                      active
                        ? 'bg-[#00C2A8] text-black font-semibold shadow-[0_0_12px_rgba(0,194,168,0.4)]'
                        : 'bg-white/[0.06] text-white/70 hover:bg-white/[0.12]',
                    )}
                  >
                    {m.label}
                  </button>
                );
              })}
            </div>
          </div>

          <button
            type="button"
            onClick={() => onScreen('controls')}
            className="text-[13px] font-medium text-[#00C2A8] hover:underline"
          >
            All Vehicle Controls ›
          </button>
        </div>
      </div>

      {/* RIGHT: Dynamic Banyan Card Stream */}
      <div className="flex flex-col gap-3 min-h-0">
        {/* Card 1: NIO Power & Battery (一键加电 & 换电) */}
        <Card
          onClick={() => onScreen('charge')}
          className="group cursor-pointer flex flex-col justify-between p-5 transition-all hover:ring-[#00C2A8]/40"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#00C2A8]/15 text-[#00C2A8]">
                <NioPowerSwapIcon size={20} />
              </span>
              <div>
                <span className="text-[15px] font-medium text-white/95">NIO Power · 一键加电</span>
                <span className="block text-[11px] text-white/45">Power Swap 3.0 & 500 kW DC</span>
              </div>
            </div>
            <span className="rounded-full bg-white/[0.08] px-3 py-1 text-[12px] font-medium text-[#00C2A8] group-hover:bg-[#00C2A8] group-hover:text-black transition-colors">
              Manage ›
            </span>
          </div>

          <div className="my-2 flex items-baseline justify-between">
            <div>
              <span className="text-[12px] text-white/40">State of Charge</span>
              <div className="flex items-baseline gap-2">
                <span className="tnum text-[38px] font-light leading-none text-white">
                  {Math.round(soc * 100)}%
                </span>
                {isCharging && (
                  <span className="text-[14px] font-medium text-emerald-400 animate-pulse">
                    ⚡ {Math.round(live.kw)} kW
                  </span>
                )}
              </div>
            </div>
            <div className="text-right">
              <span className="text-[12px] text-white/40">CLTC Range</span>
              <div className="tnum text-[28px] font-light leading-none text-white/90">
                {range ? `${range.km} km` : '--'}
              </div>
            </div>
          </div>

          {/* Battery bar */}
          <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full rounded-full transition-all duration-300"
              style={{
                width: `${soc * 100}%`,
                background: isCharging ? 'linear-gradient(90deg, #00C2A8, #10B981)' : '#00C2A8',
                boxShadow: isCharging ? '0 0 8px #00C2A8' : undefined,
              }}
            />
          </div>

          <div className="mt-2 flex items-center justify-between text-[11px] text-white/50">
            <span>Nearest Power Swap: Suzhou High-Speed 3.0 (1.8 km)</span>
            <span className="text-emerald-400 font-medium">14 packs ready</span>
          </div>
        </Card>

        {/* Card 2: PanoCinema & NIO Radio (蔚来沉浸声) */}
        <Card
          onClick={() => onScreen('media')}
          className="group cursor-pointer flex flex-col justify-between p-5 transition-all hover:ring-white/20"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <DolbyAtmosIcon size={18} />
              <span className="text-[13px] font-medium uppercase tracking-[0.12em] text-white/40">
                PanoCinema 7.1.4 Dolby Atmos
              </span>
            </div>
            <span className="text-[12px] text-white/40 group-hover:text-white transition-colors">
              Open ›
            </span>
          </div>

          <div className="my-2 flex items-center gap-4">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-tr from-[#00C2A8]/30 to-blue-500/20 text-[20px] text-white ring-1 ring-white/10">
              🎵
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-[15px] font-medium text-white/95">{track.title}</div>
              <div className="truncate text-[12px] text-white/45">{track.artist}</div>
            </div>
            <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
              <button
                type="button"
                onClick={() => patchMedia({ trackIndex: Math.max(0, media.trackIndex - 1) })}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-white/[0.06] text-white/70 hover:bg-white/[0.12]"
              >
                <PrevIcon />
              </button>
              <button
                type="button"
                onClick={() => patchMedia({ playing: !media.playing })}
                className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-black hover:scale-105 active:scale-95 transition-all"
              >
                {media.playing ? <PauseIcon /> : <PlayIcon />}
              </button>
              <button
                type="button"
                onClick={() => patchMedia({ trackIndex: media.trackIndex + 1 })}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-white/[0.06] text-white/70 hover:bg-white/[0.12]"
              >
                <NextIcon />
              </button>
            </div>
          </div>
        </Card>

        {/* Card 3: 4D Dynamic Chassis & Suspension */}
        <Card
          onClick={() => onScreen('chassis')}
          className="group cursor-pointer flex items-center justify-between p-4 transition-all hover:ring-[#00C2A8]/30"
        >
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.06] text-[#00C2A8]">
              <Chassis4DIcon size={22} />
            </span>
            <div>
              <span className="text-[14px] font-medium text-white/90">NIO 4D Dynamic Chassis</span>
              <span className="block text-[11px] text-white/45">
                CDC Continuous Damping · Dual-Chamber Air Springs
              </span>
            </div>
          </div>
          <div className="text-right">
            <span className="block text-[13px] font-semibold text-[#00C2A8]">
              {rideName} Height
            </span>
            <span className="block text-[11px] text-white/40">Adaptive leveling</span>
          </div>
        </Card>
      </div>
    </div>
  );
}
