'use client';

import React from 'react';
import type { Variant } from '@/data/vehicles/schema';
import { useVehicleStore, type HmiScreen } from '@/store/vehicle-store';
import { effectiveRange } from '@/lib/performance';
import * as Ic from '../dilink/icons';
import { XO, BAR_H, STATUS_H } from './theme';
import { useNow, useXo } from './shared';

/* ---------------------------------------------------------------- status bar */

/**
 * The status bar, on every page (c10_0019-56): the driver's avatar and three drive-mode dots at the
 * left, the battery chip with the range and the charge, READY, the parking-brake mark; at the right
 * the outside temperature, Bluetooth, the signal and the time.
 */
export function StatusBar({ variant }: { variant: Variant }) {
  const hm = useNow();
  const { soc, driveMode, climate } = useVehicleStore();
  const range = effectiveRange(variant, driveMode, soc, climate);
  return (
    <div className="absolute inset-x-0 top-0 z-20 flex items-center px-[24px]" style={{ height: STATUS_H, color: XO.text }}>
      <span className="flex h-[24px] w-[24px] items-center justify-center rounded-full" style={{ boxShadow: `inset 0 0 0 2px ${XO.text}` }} aria-hidden>
        <Ic.User size={13} />
      </span>
      {[0, 1, 2].map((i) => (
        <span key={i} className="ml-[8px] block h-[22px] w-[22px] rounded-full" style={{ boxShadow: `inset 0 0 0 1.5px ${XO.text3}` }} aria-hidden />
      ))}
      <span
        className="tnum ml-[14px] flex items-center gap-[6px] rounded-full px-[10px] text-[13px] leading-none"
        style={{ height: 24, background: 'rgba(255,255,255,0.55)', boxShadow: `inset 0 0 0 1px ${XO.line}` }}
      >
        <span className="block h-[11px] w-[18px] rounded-[2px]" style={{ background: soc > 0.2 ? XO.green : XO.red }} />
        {range ? `${range.km}` : '--'}<span className="text-[10px]">km</span> {Math.round(soc * 100)}%
      </span>
      <span className="ml-[14px] text-[12px] tracking-wide" style={{ color: XO.text3 }}>READY</span>
      <span className="ml-[12px] flex h-[18px] w-[18px] items-center justify-center rounded-full text-[10px] font-bold" style={{ boxShadow: `inset 0 0 0 1.5px ${XO.red}`, color: XO.red }}>P</span>
      <span className="ml-auto flex items-center gap-[16px] text-[14px]">
        <span className="tnum">28°</span>
        <Ic.Camera size={17} />
        <Ic.Bluetooth size={17} />
        <span className="tnum text-[11px] font-semibold">5G</span>
        <span className="tnum">{hm}</span>
      </span>
    </div>
  );
}

/* ---------------------------------------------------------------- bottom bar */

/**
 * The bar along the bottom: home, the driver's temperature, the quick panel, the 360 camera, the
 * lock, the car (the vehicle settings), the dashcam, the bonnet, the apps, the music player, the
 * passenger's temperature and the volume (positions measured on c10_0021).
 */
export function BottomBar({ screen }: { screen: HmiScreen }) {
  const { val, setVal } = useXo();
  const {
    climate, patchClimate, setHmiScreen, setAppCentreOpen, appCentreOpen, media, patchMedia, locked, setLocked,
  } = useVehicleStore();
  const [vol, setVol] = React.useState(false);

  const step = (key: 'driverTempC' | 'passengerTempC', d: number) => {
    const next = Math.min(32, Math.max(16, Math.round((climate[key] + d) * 2) / 2));
    patchClimate(climate.sync ? { driverTempC: next, passengerTempC: next } : { [key]: next });
  };
  const go = (s: HmiScreen, tab?: number) => () => {
    setAppCentreOpen(false);
    if (tab !== undefined) setVal('sheetTab', tab);
    setHmiScreen(s);
  };
  const btn = (x: number, label: string, node: React.ReactNode, onClick: () => void, pressed?: boolean, w = 54) => (
    <button
      key={label}
      type="button"
      aria-label={label}
      aria-pressed={pressed}
      onClick={onClick}
      className="absolute top-0 flex h-full -translate-x-1/2 items-center justify-center focus:outline-none focus-visible:ring-2 focus-visible:ring-black/40"
      style={{ left: x, width: w, color: XO.text }}
    >
      {pressed && <span className="absolute h-[36px] w-[42px] rounded-[10px]" style={{ background: 'rgba(122,92,240,0.16)' }} />}
      <span className="relative">{node}</span>
    </button>
  );
  const temp = (x: number, key: 'driverTempC' | 'passengerTempC', label: string) => (
    <>
      {btn(x - 58, `Lower ${label}`, <Ic.Chev dir="l" size={15} sw={2.4} />, () => step(key, -0.5), undefined, 36)}
      <button
        type="button"
        aria-label={`${label} ${climate[key].toFixed(1)} degrees, open climate`}
        onClick={go('home', 1)}
        className="tnum absolute top-0 flex h-full -translate-x-1/2 items-center justify-center text-[24px] focus:outline-none"
        style={{ left: x, width: 100, color: XO.text }}
      >
        {climate[key].toFixed(1)}°
      </button>
      {btn(x + 58, `Raise ${label}`, <Ic.Chev dir="r" size={15} sw={2.4} />, () => step(key, 0.5), undefined, 36)}
    </>
  );

  // the quick panel and the settings sheet are opened from the bar; the map is the home
  return (
    <div
      className="absolute z-30"
      style={{
        left: 22,
        right: 22,
        bottom: 8,
        height: BAR_H,
        borderRadius: 18,
        background: 'rgba(250,250,255,0.82)',
        backdropFilter: 'blur(14px)',
        WebkitBackdropFilter: 'blur(14px)',
        boxShadow: '0 2px 14px rgba(40,40,80,0.10)',
      }}
    >
      {btn(50 - 22, 'Home', <Ic.Home size={25} />, go('nav'), screen === 'nav' || screen === 'home')}
      {temp(190 - 22, 'driverTempC', 'driver temperature')}
      {btn(331 - 22, 'Quick panel', <Ic.Grid size={23} />, go('controls', 0), screen === 'controls')}
      {btn(400 - 22, '360 camera', <Ic.Camera size={25} />, go('camera'), screen === 'camera')}
      {btn(471 - 22, locked ? 'Unlock' : 'Lock', locked ? <Ic.Lock size={23} /> : <Ic.Unlock size={23} />, () => setLocked(!locked))}
      {btn(540 - 22, 'Vehicle', <Ic.CarSide size={27} />, go('settings'), screen === 'settings')}
      {btn(610 - 22, 'Seats', <Ic.SeatHeat size={24} />, go('seats'), screen === 'seats')}
      {btn(678 - 22, 'Climate', <Ic.Fan size={25} />, go('climate'), screen === 'climate')}
      {btn(749 - 22, 'Apps', <Ic.Grid size={25} />, () => setAppCentreOpen(!appCentreOpen), appCentreOpen)}
      <button
        type="button"
        aria-label="Music"
        onClick={go('media')}
        className="absolute top-0 flex h-full items-center gap-[10px] text-left focus:outline-none"
        style={{ left: 789 - 22, width: 220, color: XO.text }}
      >
        <span className="block h-[30px] w-[30px] shrink-0 rounded-[7px]" style={{ background: 'linear-gradient(140deg,#b9bfd6,#8e94b4)' }} />
        <span className="min-w-0 flex-1 truncate text-[14px]">Anytime, anywhere</span>
      </button>
      {btn(963 - 22, media.playing ? 'Pause' : 'Play', media.playing ? <Ic.Pause size={22} /> : <Ic.Play size={22} />, () => patchMedia({ playing: !media.playing }))}
      {temp(1088 - 22, 'passengerTempC', 'passenger temperature')}
      {btn(1234 - 22, 'Volume', <Ic.Volume size={25} />, () => setVol((v) => !v))}
      {vol && (
        <div
          className="absolute z-40 flex flex-col items-center gap-3 rounded-[14px] px-3 py-5"
          style={{ left: 1234 - 22, bottom: BAR_H + 8, width: 66, transform: 'translateX(-50%)', background: 'rgba(252,252,255,0.97)', boxShadow: '0 6px 24px rgba(0,0,0,0.18)' }}
        >
          <span className="tnum text-[18px]">{media.volume}</span>
          <input
            type="range"
            min={0}
            max={100}
            value={media.volume}
            aria-label="Volume"
            onChange={(e) => patchMedia({ volume: Number(e.target.value) })}
            className="h-[160px] w-6 cursor-pointer"
            style={{ writingMode: 'vertical-lr', direction: 'rtl', accentColor: XO.purple } as React.CSSProperties}
          />
        </div>
      )}
      <span className="hidden">{val.sheetTab}</span>
    </div>
  );
}
