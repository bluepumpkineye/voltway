'use client';

import React from 'react';
import { useVehicleStore, type HmiScreen } from '@/store/vehicle-store';
import * as Ha from '../harmonyos/icons';
import { useHaLocal, useNow } from '../harmonyos/shared';
import * as Ic from './icons';
import { useBy, BAR_H, STATUS_H } from './theme';

/** Over the wallpaper everything is white glass; over a page it follows the theme. */
export type Over = 'wallpaper' | 'page';

/* ---------------------------------------------------------------- status bar */

/**
 * The status bar, on every page (s_0023-40): the profile orb, the time, the music source that is playing,
 * the weather, the hotspot, Wi-Fi and Bluetooth at the left; at the right the location, the battery and
 * signal marks, the temperature inside and outside, and the driver's avatar. Positions are measured on the
 * photographs.
 */
export function StatusBar({ over }: { over: Over }) {
  const t = useBy();
  const { hm } = useNow();
  const { climate } = useVehicleStore();
  const colour = over === 'wallpaper' ? 'rgba(255,255,255,0.95)' : t.text;
  const dim = over === 'wallpaper' ? 'rgba(255,255,255,0.8)' : t.text2;
  const at = (x: number, node: React.ReactNode) => (
    <span className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2" style={{ left: x }}>
      {node}
    </span>
  );
  return (
    <div className="absolute inset-x-0 top-0 z-20" style={{ height: STATUS_H, color: colour }}>
      {at(52, <Ic.Orb size={29} />)}
      <span className="tnum absolute top-1/2 -translate-y-1/2 text-[17px] leading-none" style={{ left: 86 }}>{hm}</span>
      <span className="absolute top-1/2 flex -translate-y-1/2 items-center gap-[7px] text-[15px] leading-none" style={{ left: 150, color: dim }}>
        <Ic.Note size={16} /> Bluetooth music
      </span>
      <span className="absolute top-1/2 flex -translate-y-1/2 items-center gap-[5px] text-[16px] leading-none" style={{ left: 290 }}>
        <Ic.Sun size={17} /> 34°
      </span>
      {at(366, <Ic.Hotspot size={18} style={{ color: dim }} />)}
      {at(412, <Ic.Wifi size={19} style={{ color: dim }} />)}
      {at(456, <Ha.Bluetooth size={17} style={{ color: dim }} />)}

      {at(978, <Ic.Pin size={16} style={{ color: dim }} />)}
      {at(1008, <Ic.Battery size={18} style={{ color: dim }} />)}
      {at(1040, <Ha.Signal size={17} style={{ color: dim }} />)}
      <span className="tnum absolute top-1/2 -translate-y-1/2 text-[15px] leading-none" style={{ left: 1076 }}>
        In {Math.round(climate.driverTempC)} <span style={{ opacity: 0.6 }}>Out</span> 34
      </span>
      {at(1226, <span className="block h-[28px] w-[28px] rounded-full" style={{ background: 'radial-gradient(circle at 40% 35%, #8a7a6a, #2a2622 70%)', boxShadow: 'inset 0 0 0 1.5px rgba(255,255,255,0.35)' }} />)}
    </div>
  );
}

/* ---------------------------------------------------------------- system bar */

const tempLabel = (v: number) => (v <= 16 ? 'Lo' : v >= 32 ? 'Hi' : String(Math.round(v)));

/**
 * The system bar along the bottom, on every screen (s_0023): back, home and Settings; the fan (the climate
 * page); the driver's temperature between two arrows ("Lo" at the bottom of the range); the driver's seat
 * heating; the passenger's temperature; the windscreen demister; then the apps, split screen and the open
 * windows. Positions are measured on the photographs.
 */
export function SystemBar({ over, screen }: { over: Over; screen: HmiScreen }) {
  const t = useBy();
  const { on, toggle, notify } = useHaLocal();
  const { climate, patchClimate, setHmiScreen, setAppCentreOpen, appCentreOpen, openSettings } = useVehicleStore();
  const wall = over === 'wallpaper';
  const fg = wall ? 'rgba(255,255,255,0.95)' : t.barIcon;
  const accent = wall ? '#6fd9ad' : t.accent;

  const step = (key: 'driverTempC' | 'passengerTempC', d: number) => {
    const next = Math.min(32, Math.max(16, Math.round((climate[key] + d) * 2) / 2));
    patchClimate(climate.sync ? { driverTempC: next, passengerTempC: next } : { [key]: next });
  };

  const btn = (x: number, label: string, node: React.ReactNode, onClick: () => void, lit = false, w = 60) => (
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
  const arrow = (x: number, dir: 'l' | 'r', label: string, fn: () => void) =>
    btn(x, label, <Ha.Chev dir={dir} size={13} />, fn, false, 34);
  const temp = (x: number, key: 'driverTempC' | 'passengerTempC', label: string) => (
    <>
      {arrow(x - 40, 'l', `Lower ${label}`, () => step(key, -0.5))}
      <button
        type="button"
        aria-label={`${label} ${climate[key].toFixed(1)} degrees, open climate`}
        onClick={() => setHmiScreen('climate')}
        className="tnum absolute top-0 flex h-full -translate-x-1/2 items-center justify-center text-[25px] font-light focus:outline-none"
        style={{ left: x, width: 70 }}
      >
        {tempLabel(climate[key])}
        {tempLabel(climate[key]).length > 2 ? null : <span className="ml-[1px] mt-[6px] text-[10px] opacity-70">°c</span>}
      </button>
      {arrow(x + 40, 'r', `Raise ${label}`, () => step(key, 0.5))}
    </>
  );

  return (
    <div
      className="absolute inset-x-0 bottom-0 z-30"
      style={{
        height: BAR_H,
        color: fg,
        background: wall ? 'linear-gradient(0deg, rgba(8,14,26,0.7), rgba(8,14,26,0.4))' : t.bar,
        backdropFilter: wall ? 'blur(20px)' : undefined,
        WebkitBackdropFilter: wall ? 'blur(20px)' : undefined,
      }}
    >
      {btn(54, 'Back', <Ic.Back size={28} />, () => setHmiScreen('home'))}
      {btn(147, 'Home', <Ic.Home size={29} />, () => setHmiScreen('home'), screen === 'home' && !appCentreOpen)}
      {btn(243, 'Settings', <Ic.Hex size={28} />, () => openSettings('connection'), screen === 'settings')}
      {btn(
        403,
        'Climate',
        <span className="flex flex-col items-center gap-[1px]">
          <Ic.FanAc size={28} />
          <span className="text-[9px] font-semibold leading-none opacity-80">{climate.acOn ? 'AC' : 'OFF'}</span>
        </span>,
        () => setHmiScreen('climate'),
        screen === 'climate',
      )}
      {temp(524, 'driverTempC', 'driver temperature')}
      {btn(
        634,
        'Driver seat heating',
        <span className="flex flex-col items-center gap-[2px]">
          <Ic.SeatHeat size={30} />
          <span className="flex gap-[3px]">
            {[1, 2, 3].map((i) => (
              <span key={i} className="block h-[3px] w-[8px] rounded-full bg-current" style={{ opacity: climate.seatHeatDriver >= i ? 1 : 0.3 }} />
            ))}
          </span>
        </span>,
        () => patchClimate({ seatHeatDriver: (climate.seatHeatDriver + 1) % 4 }),
        climate.seatHeatDriver > 0,
        72,
      )}
      {temp(739, 'passengerTempC', 'passenger temperature')}
      {btn(862, 'Windscreen demister', <Ic.DefrostFront size={29} />, () => toggle('defrost'), on.defrost)}
      {btn(1023, 'Apps', <Ic.Grid size={27} />, () => setAppCentreOpen(!appCentreOpen), appCentreOpen)}
      {btn(1116, 'Split screen', <Ic.Split size={27} />, () => notify('Split screen is not part of the showroom demo'))}
      {btn(1215, 'Windows', <Ic.Windows size={27} />, () => notify('Window controls are on the vehicle page'))}
    </div>
  );
}
