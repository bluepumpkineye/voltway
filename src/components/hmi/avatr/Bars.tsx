'use client';

import React from 'react';
import { useVehicleStore, type HmiScreen } from '@/store/vehicle-store';
import * as Ha from '../harmonyos/icons';
import { useHaLocal, useNow } from '../harmonyos/shared';
import * as Ic from './icons';
import { useAv, BAR_H, STATUS_H } from './theme';

/** Over the wallpaper everything is white glass; over a page it follows the theme. */
export type Over = 'wallpaper' | 'page';

/* ---------------------------------------------------------------- status bar */

/**
 * The status bar, floating on the page (c10_0016-46): the driver's avatar, messages, the weather outside
 * with its air-quality mark, the lock, the safety shield and the camera ring at the left; the time in the
 * middle; the dashcam, phone vibration, Bluetooth, the Wi-Fi (crossed out: the car is not connected) and
 * the signal at the right. Positions are measured on the photographs.
 */
export function StatusBar({ over }: { over: Over }) {
  const t = useAv();
  const { hm } = useNow();
  const { locked } = useVehicleStore();
  const colour = over === 'wallpaper' ? '#fff' : t.text;
  const at = (x: number, node: React.ReactNode) => (
    <span className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2" style={{ left: x }}>
      {node}
    </span>
  );
  return (
    <div className="absolute inset-x-0 top-0 z-20" style={{ height: STATUS_H, color: colour }}>
      {at(60, <Ic.User size={25} />)}
      {at(133, <Ha.Message size={25} />)}
      <span className="absolute top-1/2 flex -translate-x-1/2 -translate-y-1/2 items-center gap-[5px] text-[19px]" style={{ left: 222 }}>
        <Ic.WeatherAlert size={22} />
        <span className="tnum leading-none">19°C</span>
      </span>
      {at(302, locked ? <Ic.LockShut size={25} /> : <Ic.LockOpen size={25} />)}
      {at(362, <Ic.ShieldTick size={25} />)}
      {at(425, <Ic.CamRing size={25} />)}
      <span className="tnum absolute top-1/2 -translate-x-1/2 -translate-y-1/2 text-[22px] leading-none" style={{ left: 640 }}>
        {hm}
      </span>
      {at(934, <Ha.Dashcam size={25} />)}
      {at(1005, <Ha.Vibrate size={25} style={{ opacity: 0.85 }} />)}
      {at(1074, <Ha.Bluetooth size={23} style={{ opacity: 0.85 }} />)}
      {at(1139, <Ic.WifiOff size={24} style={{ opacity: 0.85 }} />)}
      {at(1213, <Ha.Signal size={23} />)}
    </div>
  );
}

/* ---------------------------------------------------------------- bottom bar */

/**
 * The bar along the bottom, on every screen (c10_0016): home, the app grid, Settings, the driving assist,
 * music and the driver's seat at the left; one temperature with a step each side and a pager under it;
 * then the 360 camera, the vehicle (blue while its page is open), the windscreen and rear demisters, the
 * heated wheel and the volume. Positions are measured on the photographs.
 */
export function BottomBar({ over, screen }: { over: Over; screen: HmiScreen }) {
  const t = useAv();
  const { on, toggle } = useHaLocal();
  const { climate, patchClimate, setHmiScreen, setAppCentreOpen, appCentreOpen, openSettings, media, patchMedia } = useVehicleStore();
  const [vol, setVol] = React.useState(false);
  const wall = over === 'wallpaper';
  const fg = wall ? 'rgba(255,255,255,0.96)' : t.barIcon;
  const accent = wall ? '#6f95ff' : t.blue;

  const step = (d: number) => {
    const next = Math.min(32, Math.max(16, Math.round((climate.driverTempC + d) * 2) / 2));
    patchClimate(climate.sync ? { driverTempC: next, passengerTempC: next } : { driverTempC: next });
  };

  const btn = (x: number, label: string, node: React.ReactNode, onClick: () => void, lit = false, w = 56) => (
    <button
      key={label}
      type="button"
      aria-label={label}
      aria-pressed={lit}
      onClick={onClick}
      className="absolute top-0 flex h-full -translate-x-1/2 items-center justify-center focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
      style={{ left: x, width: w, color: lit ? accent : undefined }}
    >
      {node}
    </button>
  );

  return (
    <div
      className="absolute inset-x-0 bottom-0 z-30"
      style={{
        height: BAR_H,
        color: fg,
        background: wall ? 'linear-gradient(0deg, rgba(6,10,28,0.62), rgba(6,10,28,0.34))' : t.bar,
        backdropFilter: 'blur(22px) saturate(1.25)',
        WebkitBackdropFilter: 'blur(22px) saturate(1.25)',
      }}
    >
      {btn(96, 'Home', <Ic.Home size={31} />, () => setHmiScreen('home'))}
      {btn(214, 'App Centre', <Ic.Grid size={29} />, () => setAppCentreOpen(!appCentreOpen), appCentreOpen)}
      {btn(285, 'Settings', <Ic.Gear size={29} />, () => openSettings('vehicle'), screen === 'settings')}
      {btn(353, 'Driving assist', <Ic.Ads size={30} />, () => openSettings('assist'))}
      {btn(422, 'Music', <Ha.Music size={29} />, () => setHmiScreen('media'), screen === 'media')}
      {btn(493, 'Seats', <Ha.SeatHeat size={29} />, () => setHmiScreen('seats'), screen === 'seats')}

      <button type="button" aria-label="Lower temperature" onClick={() => step(-0.5)} className="absolute top-0 flex h-full w-[44px] -translate-x-1/2 items-center justify-center opacity-80 focus:outline-none" style={{ left: 562 }}>
        <Ha.Chev dir="l" size={13} />
      </button>
      <button
        type="button"
        aria-label={`Temperature ${climate.driverTempC.toFixed(1)} degrees, open climate`}
        onClick={() => setHmiScreen('climate')}
        className="tnum absolute top-0 flex h-full -translate-x-1/2 items-center justify-center text-[31px] font-semibold focus:outline-none"
        style={{ left: 637, width: 110 }}
      >
        {climate.driverTempC.toFixed(1)}
        <span className="relative -top-[8px] ml-[2px] text-[14px] font-normal opacity-70">°</span>
      </button>
      <button type="button" aria-label="Raise temperature" onClick={() => step(0.5)} className="absolute top-0 flex h-full w-[44px] -translate-x-1/2 items-center justify-center opacity-80 focus:outline-none" style={{ left: 712 }}>
        <Ha.Chev dir="r" size={13} />
      </button>
      <span className="pointer-events-none absolute flex gap-[3px]" style={{ left: 637, bottom: 9, transform: 'translateX(-50%)' }} aria-hidden>
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <span key={i} className="block h-[3px] rounded-full" style={{ width: i === 0 ? 8 : 9, background: 'currentColor', opacity: i === 0 ? 0.95 : 0.35 }} />
        ))}
      </span>

      {btn(781, '360 camera', <Ic.Cam360 size={31} />, () => setHmiScreen('camera'), screen === 'camera')}
      {btn(851, 'Vehicle control', <Ic.CarOutline size={34} />, () => setHmiScreen('controls'), screen === 'controls')}
      {btn(919, 'Windscreen demister', <Ha.Defrost size={30} />, () => toggle('defrost'), on.defrost)}
      {btn(989, 'Rear demister', <Ic.DefrostRear size={30} />, () => toggle('defrostRear'), on.defrostRear)}
      {btn(1058, 'Heated steering wheel', <Ic.WheelHeat size={30} />, () => toggle('wheelHeat'), on.wheelHeat)}
      {btn(1177, 'Volume', <Ha.Volume size={30} />, () => setVol((v) => !v))}

      {vol && (
        <div
          className="absolute z-40 flex flex-col items-center gap-3 rounded-[26px] px-3 py-5"
          style={{ left: 1177, bottom: BAR_H + 8, width: 70, transform: 'translateX(-50%)', background: wall ? 'rgba(18,24,52,0.9)' : t.bar, color: wall ? '#fff' : t.text, backdropFilter: 'blur(24px)' }}
        >
          <span className="tnum text-[19px]">{media.volume}</span>
          <input
            type="range"
            min={0}
            max={100}
            value={media.volume}
            aria-label="Volume"
            onChange={(e) => patchMedia({ volume: Number(e.target.value) })}
            className="h-[170px] w-6 cursor-pointer accent-[#2c46f2]"
            style={{ writingMode: 'vertical-lr', direction: 'rtl' } as React.CSSProperties}
          />
        </div>
      )}
    </div>
  );
}
