'use client';

import React from 'react';
import { useVehicleStore } from '@/store/vehicle-store';
import { AppIcon, type AppId } from '../harmonyos/appicons';
import { useHaLocal } from '../harmonyos/shared';
import * as Ic from './icons';
import { STATUS_H, BAR_H } from './theme';

type Tile = { id: string; label: string; app?: AppId; bg?: string; glyph?: React.ReactNode };

const ST = { fill: 'none', stroke: '#fff', strokeWidth: 3, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
const OWN: Record<string, { bg: string; g: React.ReactNode }> = {
  voice: { bg: 'linear-gradient(160deg,#4cd9c0,#17a58e)', g: <path d="M12 20v8M18 14v20M24 18v12M30 12v24M36 20v8" {...ST} /> },
  maps: { bg: 'linear-gradient(160deg,#5aa8ff,#2c6fe0)', g: <path d="M24 9l12 28-12-6-12 6z" fill="#fff" /> },
  themes: { bg: 'linear-gradient(160deg,#46d6b6,#1fa88e)', g: <path d="M24 10l4 9 10 1-7.500 6.500 2.500 10L24 31l-9 5.500 2.500-10L10 20l10-1z" fill="#fff" /> },
  tools: { bg: 'linear-gradient(160deg,#2b2f38,#12151a)', g: <><circle cx="15" cy="24" r="4" fill="#ff6a4d" /><circle cx="24" cy="24" r="4" fill="#ffc94d" /><circle cx="33" cy="24" r="4" fill="#ff6a8a" /></> },
};

const RECENT: Tile[] = [
  { id: 'market', label: 'App market', app: 'market' },
  { id: 'music', label: 'Music', app: 'music' },
  { id: 'settings', label: 'Settings', app: 'settings' },
];
const APPS: Tile[] = [
  { id: 'voice', label: 'Voice assistant' },
  { id: 'maps', label: 'Maps' },
  { id: 'butler', label: 'My car', app: 'butler' },
  { id: 'phone', label: 'Bluetooth phone', app: 'phone' },
  { id: 'music', label: 'Music', app: 'music' },
  { id: 'dashcam', label: 'Vehicle imaging', app: 'dashcam' },
  { id: 'themes', label: 'Themes' },
  { id: 'market', label: 'App market', app: 'market' },
  { id: 'settings', label: 'Settings', app: 'settings' },
  { id: 'radio', label: 'Cloud listening', app: 'radio' },
  { id: 'dashcam2', label: 'Dash cam', app: 'dashcam' },
  { id: 'tools', label: 'Utilities' },
  { id: 'weather', label: 'Weather', app: 'weather' },
  { id: 'camera', label: 'Camera', app: 'camera' },
  { id: 'gallery', label: 'Album', app: 'gallery' },
];

function Icon({ a, size }: { a: Tile; size: number }) {
  if (a.app) return <AppIcon id={a.app} size={size} />;
  const o = OWN[a.id];
  return (
    <span className="inline-flex shrink-0 items-center justify-center" style={{ width: size, height: size, borderRadius: size * 0.27, background: o.bg, boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.18)' }} aria-hidden>
      <svg viewBox="0 0 48 48" width={size} height={size}>{o.g}</svg>
    </span>
  );
}

/**
 * The apps (s_0028, s_0029, s_0093): a rounded panel over the dimmed page with a close key, a search box and
 * a microphone, the recently used apps at the left and "My apps" in rows of five, with the app market's
 * link at the top right. The apps the showroom can open do; the others say so.
 */
export function AppCentre() {
  const { setAppCentreOpen, setHmiScreen, openSettings, patchMedia } = useVehicleStore();
  const { notify, setVal } = useHaLocal();
  const dark = useVehicleStore((s) => s.hmiTheme) === 'dark';

  const open = (a: Tile) => {
    setAppCentreOpen(false);
    switch (a.id) {
      case 'settings': openSettings('connection'); return;
      case 'music': setVal('musicSrc', 3); patchMedia({ playing: true }); setHmiScreen('media'); return;
      case 'maps': setHmiScreen('nav'); return;
      case 'phone': setVal('phone', 1); setHmiScreen('home'); return;
      case 'camera':
      case 'dashcam': setHmiScreen('camera'); return;
      case 'butler': setHmiScreen('controls'); return;
      default:
        setAppCentreOpen(true);
        notify(`${a.label} is not part of the showroom demo`);
    }
  };
  const cell = (a: Tile, size: number, k: string) => (
    <button key={k} type="button" onClick={() => open(a)} className="flex flex-col items-center gap-[9px] rounded-[14px] outline-none focus-visible:ring-2 focus-visible:ring-white/70">
      <Icon a={a} size={size} />
      <span className="w-[130px] truncate text-center text-[13px] leading-none text-white/90">{a.label}</span>
    </button>
  );

  return (
    <div className="absolute inset-0 z-10" style={{ background: 'rgba(3,8,14,0.55)', backdropFilter: 'blur(14px)', WebkitBackdropFilter: 'blur(14px)' }}>
      <div className="absolute overflow-hidden rounded-[30px]" style={{ left: 26, right: 26, top: STATUS_H + 6, bottom: BAR_H + 6, background: dark ? 'linear-gradient(135deg,rgba(40,70,90,0.78),rgba(14,28,44,0.9))' : 'linear-gradient(135deg,rgba(214,232,248,0.92),rgba(190,214,238,0.92))', boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.12)' }}>
        <button type="button" aria-label="Close apps" onClick={() => setAppCentreOpen(false)} className="absolute left-[22px] top-[18px] outline-none" style={{ color: dark ? '#fff' : '#17263a' }}><Ic.Close size={26} /></button>
        <div className="absolute flex h-[46px] w-[260px] items-center gap-[10px] rounded-full px-[18px]" style={{ left: 56, top: 52, background: 'rgba(255,255,255,0.12)', color: dark ? '#fff' : '#17263a' }}>
          <Ic.MenuSearch size={19} /> <span className="flex-1 text-[15px] opacity-70">Search</span> <Ic.Mic size={19} />
        </div>
        <div className="absolute text-[15px]" style={{ left: 56, top: 128, color: dark ? 'rgba(255,255,255,0.8)' : '#17263a' }}>Recently used</div>
        <div className="absolute flex gap-[26px]" style={{ left: 40, top: 168 }}>{RECENT.map((a, i) => cell(a, 66, `r${i}`))}</div>
        <div className="absolute text-[15px]" style={{ left: 480, top: 58, color: dark ? 'rgba(255,255,255,0.8)' : '#17263a' }}>My apps</div>
        <button type="button" onClick={() => notify('The app market is not part of the showroom demo')} className="absolute text-[14px] outline-none" style={{ right: 36, top: 58, color: dark ? 'rgba(255,255,255,0.75)' : '#17263a' }}>App market ›</button>
        <div className="absolute grid grid-cols-5 gap-y-[28px]" style={{ left: 440, right: 30, top: 100 }}>{APPS.map((a, i) => cell(a, 80, `a${i}`))}</div>
      </div>
    </div>
  );
}
