'use client';

import React from 'react';
import { useVehicleStore, type HmiScreen } from '@/store/vehicle-store';
import { useZk, BAR_H, STATUS_H } from './theme';
import * as Ic from './icons';
import { useNow, useZkLocal } from './shared';

/* ---------------------------------------------------------------- status bar */

/**
 * The status bar, on every page: the driver's avatar and name, the battery, the car's shortcuts
 * (drive mode, lock, dashcam, alarm, security), the assistant's mascot in the middle, and on the
 * right the phone link, Bluetooth, signal and the date. Positions are read off the
 * photographs (c10_0016-18: the icons sit at fixed x on the 1280 wide screen).
 */
export function StatusBar() {
  const t = useZk();
  const { date, hm } = useNow();
  const { soc, locked, setLocked } = useVehicleStore();
  const at = (x: number, node: React.ReactNode, onClick?: () => void, label?: string) => (
    <span
      role={onClick ? 'button' : undefined}
      aria-label={label}
      onClick={onClick}
      className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2"
      style={{ left: x, cursor: onClick ? 'pointer' : undefined }}
    >
      {node}
    </span>
  );
  return (
    <div className="absolute inset-x-0 top-0 z-20" style={{ height: STATUS_H, color: t.text }}>
      {at(
        38,
        <span
          className="block h-[28px] w-[28px] rounded-full"
          style={{
            background: 'conic-gradient(from 210deg, #1c1d22 0 50%, #e8e9ee 50% 72%, #2b2d35 72%)',
            boxShadow: 'inset 0 0 0 1px rgba(0,0,0,0.18)',
          }}
          aria-hidden
        />,
      )}
      <span className="absolute top-1/2 -translate-y-1/2 text-[14px] leading-none" style={{ left: 60, color: t.text2 }}>
        Driver
      </span>
      {at(
        172,
        <span className="block h-[11px] w-[22px] rounded-[2.5px]" style={{ background: soc > 0.2 ? '#27c46f' : '#e5412d', boxShadow: 'inset 0 0 0 1px rgba(0,0,0,0.12)' }} />,
      )}
      <span className="tnum absolute top-1/2 -translate-y-1/2 text-[14px] leading-none" style={{ left: 190, color: t.text2 }}>
        {Math.round(soc * 100)}%
      </span>
      {at(331, <Ic.Leaf size={22} style={{ opacity: 0.85 }} />)}
      {at(384, locked ? <Ic.LockShut size={22} /> : <Ic.LockOpen size={22} />, () => setLocked(!locked), locked ? 'Unlock' : 'Lock')}
      {at(437, <Ic.DashcamSb size={22} style={{ opacity: 0.55 }} />)}
      {at(490, <Ic.Siren size={22} />)}
      {at(542, <Ic.ShieldSb size={22} />)}
      {at(636, <Ic.Mascot size={36} />)}
      {at(915, <Ic.PhoneLink size={22} />)}
      {at(967, <Ic.Bluetooth size={20} style={{ opacity: 0.55 }} />)}
      {at(1022, <Ic.Broadcast size={22} style={{ opacity: 0.55 }} />)}
      {at(1074, <Ic.Signal5G size={22} />)}
      <span className="tnum absolute top-1/2 -translate-x-1/2 -translate-y-1/2 text-[14px] leading-none" style={{ left: 1184, color: t.text }}>
        {date} {hm}
      </span>
    </div>
  );
}

/* ---------------------------------------------------------------- bottom bar */

/**
 * The bar along the bottom, on every screen: home, vehicle controls, the 360 camera, the
 * demister, the driver's seat, the driver's temperature, the fan (AUTO), the passenger's
 * temperature, the passenger's seat, the rear demister, music, the apps and the volume.
 */
export function BottomBar({ over, screen }: { over: 'scene' | 'sheet'; screen: HmiScreen }) {
  const t = useZk();
  const { on, toggle } = useZkLocal();
  const {
    climate, patchClimate, setHmiScreen, setAppCentreOpen, appCentreOpen, media, patchMedia,
  } = useVehicleStore();
  const [vol, setVol] = React.useState(false);

  const step = (key: 'driverTempC' | 'passengerTempC', d: number) =>
    patchClimate({ [key]: Math.min(32, Math.max(16, Math.round((climate[key] + d) * 2) / 2)) });

  const btn = (x: number, label: string, node: React.ReactNode, onClick: () => void, w = 58) => (
    <button
      type="button"
      aria-label={label}
      onClick={onClick}
      className="absolute top-0 flex h-full -translate-x-1/2 items-center justify-center focus:outline-none focus-visible:ring-2 focus-visible:ring-black/40"
      style={{ left: x, width: w }}
    >
      {node}
    </button>
  );

  const temp = (x: number, key: 'driverTempC' | 'passengerTempC', label: string) => (
    <>
      {btn(x - 66, `Lower ${label}`, <Ic.Chev dir="l" size={16} sw={2.600} />, () => step(key, -0.5), 40)}
      <button
        type="button"
        aria-label={`${label} ${climate[key].toFixed(1)} degrees, open climate`}
        onClick={() => setHmiScreen('climate')}
        className="tnum absolute top-0 flex h-full -translate-x-1/2 items-center justify-center text-[29px] font-light focus:outline-none"
        style={{ left: x, width: 100 }}
      >
        {climate[key].toFixed(1)}
        <span className="relative -top-[7px] ml-[1px] text-[14px]">°C</span>
      </button>
      {btn(x + 66, `Raise ${label}`, <Ic.Chev dir="r" size={16} sw={2.600} />, () => step(key, 0.5), 40)}
    </>
  );

  return (
    <div
      className="absolute inset-x-0 bottom-0 z-30"
      style={{
        height: BAR_H,
        color: t.text,
        background: over === 'sheet' ? t.bar : t.barScene,
        backdropFilter: over === 'scene' ? 'blur(10px)' : undefined,
        WebkitBackdropFilter: over === 'scene' ? 'blur(10px)' : undefined,
      }}
    >
      {btn(41, 'Home', <Ic.Home size={27} />, () => {
        setAppCentreOpen(false);
        setHmiScreen('home');
      })}
      {btn(123, 'Vehicle controls', <Ic.CarFront size={28} style={{ opacity: screen === 'controls' ? 1 : 0.9 }} />, () => {
        setAppCentreOpen(false);
        setHmiScreen('controls');
      })}
      {btn(205, '360 camera', <Ic.Cam360 size={30} />, () => {
        setAppCentreOpen(false);
        setHmiScreen('camera');
      })}
      {btn(287, 'Demister', <Ic.DefrostFront size={27} style={{ color: on.defrost ? t.accent : undefined }} />, () => toggle('defrost'))}
      {btn(370, 'Driver seat', <Ic.SeatHeat size={27} style={{ color: screen === 'seats' ? t.accent : undefined }} />, () => {
        setAppCentreOpen(false);
        setHmiScreen('seats');
      })}

      {temp(499, 'driverTempC', 'driver temperature')}

      {btn(
        636,
        'Climate',
        <span className="relative flex flex-col items-center" style={{ color: climate.acOn ? undefined : t.text3 }}>
          <Ic.Fan size={27} />
          <span className="-mt-[1px] text-[7px] font-semibold leading-none tracking-wide">AUTO</span>
        </span>,
        () => {
          setAppCentreOpen(false);
          setHmiScreen('climate');
        },
        64,
      )}

      {temp(775, 'passengerTempC', 'passenger temperature')}

      {btn(905, 'Passenger seat', <Ic.SeatAuto size={28} />, () => {
        setAppCentreOpen(false);
        setHmiScreen('seats');
      })}
      {btn(989, 'Rear demister', <Ic.DefrostRear size={27} style={{ color: on.defrostRear ? t.accent : undefined }} />, () => toggle('defrostRear'))}
      {btn(1071, 'Music', <Ic.Music size={26} style={{ color: screen === 'media' ? t.accent : undefined }} />, () => {
        setAppCentreOpen(false);
        setHmiScreen('media');
      })}
      {btn(1155, 'Apps', <Ic.Apps size={26} style={{ color: appCentreOpen ? t.accent : undefined }} />, () => setAppCentreOpen(!appCentreOpen))}
      {btn(1237, 'Volume', <Ic.Volume size={27} />, () => setVol((v) => !v))}

      {vol && (
        <div
          className="absolute z-40 flex flex-col items-center gap-3 rounded-[16px] px-3 py-5"
          style={{
            left: 1237,
            bottom: BAR_H + 8,
            width: 66,
            transform: 'translateX(-50%)',
            background: t.tone === 'light' ? 'rgba(250,251,255,0.97)' : 'rgba(36,38,48,0.97)',
            color: t.text,
            boxShadow: '0 6px 24px rgba(0,0,0,0.18)',
          }}
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
            style={{ writingMode: 'vertical-lr', direction: 'rtl', accentColor: t.accent } as React.CSSProperties}
          />
        </div>
      )}
    </div>
  );
}
