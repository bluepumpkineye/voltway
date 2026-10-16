'use client';

import React from 'react';
import { useVehicleStore, type HmiScreen } from '@/store/vehicle-store';
import { DL, BAR_H, STATUS_H } from './theme';
import * as Ic from './icons';
import { useDl, useNow } from './shared';

/* ---------------------------------------------------------------- status bar */

/**
 * The status bar, on every page (c10_0030-97): the maker's mark and the time at the left with the
 * music app that is playing, and at the right the location, Bluetooth and hotspot icons and the
 * driver's avatar. Over the bright home the glyphs are dark blue-grey, over a page white.
 */
export function StatusBar({ over }: { over: 'home' | 'page' }) {
  const hm = useNow();
  const { media } = useVehicleStore();
  const ink = over === 'home' ? '#2a3a5c' : DL.text;
  const ink2 = over === 'home' ? 'rgba(42,58,92,0.62)' : DL.text2;
  return (
    <div className="absolute inset-x-0 top-0 z-20 flex items-center px-[26px]" style={{ height: STATUS_H, color: ink }}>
      <span
        className="block h-[20px] w-[20px] rounded-full"
        style={{ boxShadow: `inset 0 0 0 2px ${ink}`, background: `radial-gradient(circle at 50% 50%, transparent 0 4px, ${ink2} 4px 6px, transparent 6px)` }}
        aria-hidden
      />
      <span className="tnum ml-[14px] text-[15px] leading-none">{hm}</span>
      <span className="ml-[16px] flex items-center gap-[6px] text-[14px] leading-none" style={{ color: ink2 }}>
        <Ic.Music size={15} />
        {media.playing ? 'Cloud Music' : 'Cloud'}
      </span>
      <span className="ml-auto flex items-center gap-[20px]" style={{ color: ink2 }}>
        <Ic.Pin size={17} />
        <Ic.Bluetooth size={17} />
        <Ic.Wifi size={17} />
        <span className="flex h-[24px] w-[24px] items-center justify-center rounded-full" style={{ boxShadow: `inset 0 0 0 1.5px ${ink2}` }}>
          <Ic.User size={15} />
        </span>
      </span>
    </div>
  );
}

/* ---------------------------------------------------------------- bottom bar */

/**
 * The bar along the bottom, on every screen: back, home, the driver's temperature, settings, the
 * driver's seat heat and ventilation, the windscreen demister, the screen brightness, the
 * passenger's temperature, the camera and the app grid (positions measured on c10_0030).
 */
export function BottomBar({ over, screen }: { over: 'home' | 'page'; screen: HmiScreen }) {
  const { on, toggle, val, setVal } = useDl();
  const { climate, patchClimate, setHmiScreen, setAppCentreOpen, appCentreOpen } = useVehicleStore();
  const ink = over === 'home' ? '#26385a' : DL.text;

  const step = (key: 'driverTempC' | 'passengerTempC', d: number) => {
    const next = Math.min(32, Math.max(16, Math.round((climate[key] + d) * 2) / 2));
    patchClimate(climate.sync ? { driverTempC: next, passengerTempC: next } : { [key]: next });
  };
  const go = (s: HmiScreen) => () => {
    setAppCentreOpen(false);
    setHmiScreen(s);
  };

  const btn = (x: number, label: string, node: React.ReactNode, onClick: () => void, pressed?: boolean, w = 56) => (
    <button
      key={label}
      type="button"
      aria-label={label}
      aria-pressed={pressed}
      onClick={onClick}
      className="absolute top-0 flex h-full -translate-x-1/2 items-center justify-center focus:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
      style={{ left: x, width: w, color: pressed ? DL.accent : ink }}
    >
      {node}
    </button>
  );
  const temp = (x: number, key: 'driverTempC' | 'passengerTempC', label: string) => (
    <>
      {btn(x - 92, `Lower ${label}`, <Ic.Chev dir="l" size={17} sw={2.4} />, () => step(key, -0.5), undefined, 40)}
      <button
        type="button"
        aria-label={`${label} ${climate[key].toFixed(0)} degrees, open climate`}
        onClick={go('climate')}
        className="tnum absolute top-0 flex h-full -translate-x-1/2 items-center justify-center text-[25px] font-light focus:outline-none"
        style={{ left: x, width: 100, color: ink }}
      >
        {Math.round(climate[key])}
        <span className="relative -top-[6px] ml-[1px] text-[13px]">°</span>
      </button>
      {btn(x + 92, `Raise ${label}`, <Ic.Chev dir="r" size={17} sw={2.4} />, () => step(key, 0.5), undefined, 40)}
    </>
  );

  return (
    <div
      className="absolute inset-x-0 bottom-0 z-30"
      style={{
        height: BAR_H,
        background: over === 'home' ? DL.barHome : DL.barPage,
        backdropFilter: over === 'home' ? 'blur(12px)' : undefined,
        WebkitBackdropFilter: over === 'home' ? 'blur(12px)' : undefined,
        boxShadow: over === 'page' ? 'inset 0 1px 0 rgba(255,255,255,0.08)' : undefined,
      }}
    >
      {btn(123, 'Back', <Ic.Back size={26} />, go('home'))}
      {btn(218, 'Home', <Ic.Home size={26} />, go('home'), screen === 'home')}
      {temp(407, 'driverTempC', 'driver temperature')}
      {btn(580, 'Settings', <Ic.Gear size={25} />, go('controls'), screen === 'controls')}
      {btn(661, 'Driver seat heating', <Ic.SeatHeat size={26} />, () => patchClimate({ seatHeatDriver: climate.seatHeatDriver > 0 ? 0 : 2 }), climate.seatHeatDriver > 0)}
      {btn(745, 'Driver seat ventilation', <Ic.SeatVent size={26} />, () => toggle('ventDriver'), on.ventDriver)}
      {btn(822, 'Windscreen demister', <Ic.DefrostFront size={26} />, () => toggle('defrost'), on.defrost)}
      {btn(897, 'Screen brightness', <Ic.Sun size={25} />, () => setVal('brightness', val.brightness > 50 ? 40 : 100))}
      {temp(1047, 'passengerTempC', 'passenger temperature')}
      {btn(1175, '360 camera', <Ic.Camera size={26} />, go('camera'), screen === 'camera')}
      {btn(1238, 'Apps', <Ic.Grid size={25} />, () => setAppCentreOpen(!appCentreOpen), appCentreOpen)}
    </div>
  );
}
