'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { effectiveRange } from '@/lib/performance';
import * as Ha from '../harmonyos/icons';
import { AppIcon } from '../harmonyos/appicons';
import { useHaLocal } from '../harmonyos/shared';
import * as Ic from './icons';
import { glass } from './theme';
import { TRACKS } from './media';

/**
 * The wallpaper, drawn here (the car's own is a photograph we do not ship): a dusk sea, a pale band of
 * cloud along the horizon, low hills and dark rocks standing in still water (c10_0016).
 */
export function Wallpaper() {
  const uid = React.useId().replace(/:/g, '');
  return (
    <svg className="absolute inset-0" viewBox="0 0 1280 800" preserveAspectRatio="xMidYMid slice" width="1280" height="800" aria-hidden>
      <defs>
        <linearGradient id={`${uid}s`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#0a0f20" />
          <stop offset="0.2" stopColor="#1a2547" />
          <stop offset="0.36" stopColor="#4a5d92" />
          <stop offset="0.46" stopColor="#8d9fcb" />
          <stop offset="0.5" stopColor="#3b4a7c" />
        </linearGradient>
        <linearGradient id={`${uid}w`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#34457a" />
          <stop offset="0.35" stopColor="#202e5e" />
          <stop offset="1" stopColor="#0b1432" />
        </linearGradient>
        <filter id={`${uid}b`}><feGaussianBlur stdDeviation="16" /></filter>
        <filter id={`${uid}c`}><feGaussianBlur stdDeviation="3" /></filter>
      </defs>
      <rect width="1280" height="800" fill={`url(#${uid}s)`} />
      <g filter={`url(#${uid}b)`} opacity="0.75">
        <ellipse cx="300" cy="210" rx="360" ry="34" fill="#b9c5e6" opacity="0.55" transform="rotate(-6 300 210)" />
        <ellipse cx="760" cy="150" rx="420" ry="26" fill="#8e9fd0" opacity="0.5" transform="rotate(5 760 150)" />
        <ellipse cx="640" cy="290" rx="640" ry="38" fill="#c8d2ee" opacity="0.7" />
        <ellipse cx="980" cy="230" rx="280" ry="22" fill="#d5ddf2" opacity="0.5" transform="rotate(-4 980 230)" />
      </g>
      <path d="M0 372 L140 362 L330 374 L520 366 L760 376 L980 364 L1160 372 L1280 366 V404 H0 Z" fill="#161f40" />
      <rect y="400" width="1280" height="400" fill={`url(#${uid}w)`} />
      {/* the sky's reflection and the ripples */}
      <g filter={`url(#${uid}c)`} opacity="0.5">
        <rect x="120" y="408" width="1000" height="10" fill="#8f9fcf" opacity="0.55" />
        <rect x="260" y="438" width="720" height="5" fill="#6f80b6" opacity="0.5" />
        <rect x="420" y="470" width="480" height="4" fill="#5668a2" opacity="0.5" />
      </g>
      {/* rocks standing in the water */}
      <g fill="#0b1124">
        <path d="M720 520c20-26 60-30 96-18l30 20c40-6 70 6 78 22l-250 6z" />
        <path d="M1010 470c14-30 52-52 96-44 34 8 48 30 52 62l-148 4z" />
        <path d="M862 420c10-14 30-18 50-10l16 10z" opacity="0.85" />
        <path d="M1160 530c24-18 70-16 96 4l24 22H1130z" />
        <path d="M0 640c60-70 170-110 260-84 70 18 120 60 140 110l-20 140H0z" />
        <path d="M430 700c40-22 100-24 140 0 28 18 30 44 20 70l-180 4z" opacity="0.9" />
      </g>
      <path d="M0 640c60-70 170-110 260-84 70 18 120 60 140 110" fill="none" stroke="#33426f" strokeWidth="2" opacity="0.5" />
      <rect width="1280" height="800" fill="#06091a" opacity="0.18" />
    </svg>
  );
}

function Card({ x, w, children, onClick, label }: { x: number; w: number; children: React.ReactNode; onClick?: () => void; label: string }) {
  return (
    <button
      type="button"
      aria-label={label}
      onClick={onClick}
      className="absolute overflow-hidden rounded-[22px] text-left text-white outline-none focus-visible:ring-2 focus-visible:ring-white/70"
      style={{ left: x, top: 588, width: w, height: 128, ...glass(0.4, 22), boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.09)' }}
    >
      {children}
    </button>
  );
}

/**
 * The home (c10_0016, c10_0075): the wallpaper under a row of glass cards (the frequent apps, the air-quality
 * suggestion, the driving assist, the music and the range); no clock, no car. The cards open what they show.
 */
export function HomeDesktop({ variant }: { vehicle?: Vehicle; variant: Variant }) {
  const { notify } = useHaLocal();
  const { media, patchMedia, driveMode, soc, climate, patchClimate, setHmiScreen, openSettings } = useVehicleStore();
  const range = effectiveRange(variant, driveMode, soc, climate);
  const track = TRACKS[media.trackIndex % TRACKS.length];
  const [purified, setPurified] = React.useState(false);

  return (
    <div className="absolute inset-0 overflow-hidden">
      <Wallpaper />

      <Card x={40} w={284} label="Frequent apps">
        <span className="absolute left-[18px] top-[12px] text-[13px] opacity-80">Frequent apps</span>
        {(['music', 'video', 'market', 'guide'] as const).map((id, i) => (
          <span
            key={id}
            role="button"
            aria-label={id}
            tabIndex={0}
            onClick={() => (id === 'music' ? setHmiScreen('media') : notify('This app is not part of the showroom demo'))}
            className="absolute"
            style={{ left: 16 + i * 64, top: 38 }}
          >
            <AppIcon id={id} size={54} />
          </span>
        ))}
      </Card>

      <Card
        x={348}
        w={282}
        label="Air quality suggestion"
        onClick={() => {
          setPurified(true);
          patchClimate({ acOn: true });
          notify('Purifying the air and closing all windows');
        }}
      >
        <span className="absolute left-[20px] top-[16px] flex items-center gap-[10px] text-[18px]">
          <span className="block h-[22px] w-[22px] rounded-full" style={{ background: 'conic-gradient(from 20deg, #f0f4ff, #7f93c9, #f0f4ff)' }} />
          {purified ? 'Air is being purified' : 'Poor air quality'}
        </span>
        <span className="absolute inset-x-[16px] bottom-[16px] rounded-full px-[14px] py-[11px] text-[15px] leading-tight" style={{ background: 'rgba(255,255,255,0.14)' }}>
          “Purify the cabin air and close all windows”
        </span>
      </Card>

      <Card x={646} w={124} label="Driving assist" onClick={() => openSettings('assist')}>
        <span className="absolute left-1/2 top-[16px] flex h-[56px] w-[56px] -translate-x-1/2 items-center justify-center rounded-[16px] text-white" style={{ background: 'linear-gradient(160deg,#ff5a4f,#c4161c)', boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.3)' }}>
          <Ic.Ads size={36} sw={1.9} />
        </span>
        <span className="absolute inset-x-0 bottom-[14px] text-center text-[14px] tracking-wide">HUAWEI ADS</span>
      </Card>

      <Card x={794} w={282} label="Music" onClick={() => setHmiScreen('media')}>
        <span className="absolute left-[18px] top-[20px] flex h-[54px] w-[54px] items-center justify-center rounded-[14px]" style={{ background: 'rgba(255,255,255,0.16)' }}>
          <Ha.Music size={28} />
        </span>
        <span className="absolute left-[84px] top-[26px] flex items-center gap-[20px]" onClick={(e) => e.stopPropagation()}>
          <span role="button" aria-label={media.playing ? 'Pause' : 'Play'} tabIndex={0} onClick={() => patchMedia({ playing: !media.playing })} style={{ opacity: media.playing ? 1 : 0.55 }}>
            {media.playing ? <Ha.Pause size={30} /> : <Ha.Play size={30} />}
          </span>
          <span role="button" aria-label="Next" tabIndex={0} onClick={() => patchMedia({ trackIndex: (media.trackIndex + 1) % TRACKS.length })} style={{ opacity: 0.8 }}>
            <Ha.Next size={30} />
          </span>
        </span>
        <span className="absolute left-[18px] bottom-[14px] w-[160px] truncate text-[14px]">{media.playing ? track.title : 'Nothing is playing'}</span>
        <span className="absolute bottom-[18px] top-[18px] w-px bg-white/25" style={{ left: 190 }} />
        <span className="absolute top-[18px] flex h-[50px] w-[50px] items-center justify-center rounded-[14px]" style={{ left: 212, background: 'linear-gradient(160deg,#6f8bff,#3b57e8)' }}>
          <Ha.Bluetooth size={28} />
        </span>
        <span className="absolute bottom-[14px] text-[14px]" style={{ left: 208 }}>iPhone ▾</span>
      </Card>

      <Card x={1098} w={162} label="Range" onClick={() => openSettings('energy')}>
        <span className="absolute left-[16px] top-[16px] leading-none">
          <span className="tnum text-[24px] font-semibold">{range ? range.km : '--'}</span>
          <span className="ml-[3px] text-[12px]">km</span>
          <span className="mt-[4px] block text-[12px] opacity-80">Remaining range</span>
        </span>
        <span className="absolute bottom-[14px] left-[16px] leading-tight">
          <span className="block text-[13px]">-- <span className="text-[11px]">kWh/100km</span></span>
          <span className="block text-[11px] opacity-80">Avg. consumption (trip)</span>
        </span>
      </Card>
    </div>
  );
}
