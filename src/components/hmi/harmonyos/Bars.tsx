'use client';

import React from 'react';
import { useVehicleStore, type HmiScreen } from '@/store/vehicle-store';
import { useHa, BAR_H, STATUS_H } from './theme';
import * as Ic from './icons';
import { useHaLocal, useNow } from './shared';

/** Over the wallpaper everything is white glass; over an app page it follows the theme. */
export type Over = 'wallpaper' | 'page';

/* ---------------------------------------------------------------- status bar */

/**
 * The status bar, floating on the page: the driver's avatar and the time, the
 * message, safety and settings shortcuts; the dashcam, phone link, Bluetooth,
 * signal and the weather outside on the right. Positions are read off the
 * photographs (the icons sit at fixed x on the 1280 wide screen).
 */
export function StatusBar({ over }: { over: Over }) {
  const t = useHa();
  const { hm } = useNow();
  const colour = over === 'wallpaper' ? '#fff' : t.text;
  const at = (x: number, node: React.ReactNode) => (
    <span className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2" style={{ left: x }}>
      {node}
    </span>
  );
  return (
    <div className="absolute inset-x-0 top-0 z-20" style={{ height: STATUS_H, color: colour }}>
      {at(
        54,
        <span
          className="block h-[34px] w-[34px] rounded-full"
          style={{
            background:
              'radial-gradient(circle at 30% 30%, #6f86c9 0, #2b3a6e 28%, #0c1226 62%, #070a14 100%)',
            boxShadow: 'inset 0 0 0 1.5px rgba(255,255,255,0.18)',
          }}
          aria-hidden
        />,
      )}
      <span
        className="tnum absolute top-1/2 -translate-y-1/2 text-[23px] leading-none"
        style={{ left: 100 }}
      >
        {hm}
      </span>
      {at(
        198,
        <span className="relative block">
          <Ic.Message size={26} />
          <span className="absolute -right-0.5 -top-0.5 h-[9px] w-[9px] rounded-full" style={{ background: '#ff3b30' }} />
        </span>,
      )}
      {at(
        250,
        <span className="relative block">
          <Ic.Shield size={26} />
          <span className="absolute left-1/2 top-1/2 h-[7px] w-[7px] -translate-x-1/2 -translate-y-1/2 rounded-full" style={{ background: '#34c759' }} />
        </span>,
      )}
      {at(297, <Ic.RingGear size={26} />)}

      {at(967, <Ic.Dashcam size={26} />)}
      {at(1021, <Ic.Vibrate size={26} style={{ opacity: 0.8 }} />)}
      {at(1077, <Ic.Bluetooth size={24} style={{ opacity: 0.8 }} />)}
      {at(1134, <Ic.Signal size={24} />)}
      <span className="absolute top-1/2 flex -translate-y-1/2 items-center gap-1.5 text-[21px]" style={{ left: 1170 }}>
        <Ic.Cloud size={25} />
        <span className="tnum leading-none">27°C</span>
      </span>
    </div>
  );
}

/* ---------------------------------------------------------------- bottom bar */

/** The lights button's small label under its icon. */
const LAMP_LABEL = ['', 'POS', 'LOW', 'AUTO'];

/**
 * The bar along the bottom, on every screen: the assistant, vehicle control,
 * apps, navigation, the climate and the driver's seat on the left; the driver's
 * temperature, the home ring, the passenger's temperature; the passenger's seat,
 * music, the lights, the demister and the volume on the right. The page that
 * is open puts a dot under its icon.
 */
export function BottomBar({
  over,
  screen,
  onHome,
}: {
  over: Over;
  screen: HmiScreen;
  onHome: () => void;
}) {
  const t = useHa();
  const { notify, on, toggle, val, setVal } = useHaLocal();
  const {
    climate, patchClimate, setHmiScreen, setAppCentreOpen, appCentreOpen, media, patchMedia, setHeadlights,
  } = useVehicleStore();
  const [vol, setVol] = React.useState(false);
  const wall = over === 'wallpaper';
  const fg = wall ? 'rgba(255,255,255,0.95)' : t.barIcon;
  const bg = wall ? 'rgba(6,9,20,0.58)' : t.bar;

  const step = (key: 'driverTempC' | 'passengerTempC', d: number) =>
    patchClimate({ [key]: Math.min(32, Math.max(16, Math.round((climate[key] + d) * 2) / 2)) });

  const btn = (x: number, label: string, node: React.ReactNode, onClick: () => void, dot = false, w = 56) => (
    <button
      type="button"
      aria-label={label}
      onClick={onClick}
      className="absolute top-0 flex h-full -translate-x-1/2 items-center justify-center focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
      style={{ left: x, width: w }}
    >
      {node}
      {dot && <span className="absolute bottom-[7px] left-1/2 h-[4px] w-[4px] -translate-x-1/2 rounded-full" style={{ background: 'currentColor' }} />}
    </button>
  );

  const temp = (x: number, key: 'driverTempC' | 'passengerTempC', label: string) => (
    <>
      <button type="button" aria-label={`Lower ${label}`} onClick={() => step(key, -0.5)} className="absolute top-0 flex h-full w-[40px] -translate-x-1/2 items-center justify-center opacity-80 focus:outline-none" style={{ left: x - 46 }}>
        <Ic.Chev dir="l" size={14} />
      </button>
      <button
        type="button"
        aria-label={`${label} ${climate[key].toFixed(1)} degrees, open climate`}
        onClick={() => setHmiScreen('climate')}
        className="tnum absolute top-0 flex h-full -translate-x-1/2 items-center justify-center text-[27px] font-normal focus:outline-none"
        style={{ left: x, width: 80 }}
      >
        {climate[key].toFixed(1)}
      </button>
      <button type="button" aria-label={`Raise ${label}`} onClick={() => step(key, 0.5)} className="absolute top-0 flex h-full w-[40px] -translate-x-1/2 items-center justify-center opacity-80 focus:outline-none" style={{ left: x + 46 }}>
        <Ic.Chev dir="r" size={14} />
      </button>
    </>
  );

  return (
    <div
      className="absolute inset-x-0 bottom-0 z-30"
      style={{
        height: BAR_H,
        color: fg,
        background: bg,
        backdropFilter: 'blur(26px) saturate(1.3)',
        WebkitBackdropFilter: 'blur(26px) saturate(1.3)',
        // the voice icon's bars cut through the white disc: the bar's own colour
        ['--ha-voice-bars' as string]: wall || t.tone === 'dark' ? '#0d0e12' : '#ecebed',
      }}
    >
      {btn(85, 'Assistant', <Ic.Voice size={31} />, () => notify('Xiaoyi is listening (showroom demo)'))}
      {btn(152, 'Vehicle control', <Ic.CarFront size={31} />, () => setHmiScreen('controls'), screen === 'controls')}
      {btn(219, 'Apps', <Ic.Apps size={29} />, () => setAppCentreOpen(!appCentreOpen), appCentreOpen)}
      {btn(285, 'Navigation', <Ic.NavRing size={31} />, () => setHmiScreen('nav'), screen === 'nav')}
      {btn(
        351,
        'Climate',
        <Ic.Fan size={31} style={{ color: climate.acOn ? (wall ? '#6f95ff' : t.blue) : undefined }} />,
        () => setHmiScreen('climate'),
        screen === 'climate',
      )}
      {btn(422, 'Driver seat', <Ic.SeatHeat size={29} />, () => setHmiScreen('seats'), screen === 'seats')}

      {temp(525, 'driverTempC', 'driver temperature')}

      <button
        type="button"
        aria-label="Home"
        onClick={onHome}
        className="absolute top-1/2 h-[46px] w-[46px] -translate-x-1/2 -translate-y-1/2 rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
        style={{ left: 642, border: '5px solid currentColor' }}
      />

      {temp(774, 'passengerTempC', 'passenger temperature')}

      {btn(862, 'Passenger seat', <Ic.SeatHeatR size={29} />, () => setHmiScreen('seats'))}
      {btn(930, 'Music', <Ic.Music size={29} />, () => setHmiScreen('media'), screen === 'media')}
      {btn(
        997,
        'Headlamps',
        <span className="relative flex flex-col items-center" style={{ color: val.headlamp ? (wall ? '#6f95ff' : t.blue) : undefined }}>
          <Ic.CarBeam size={31} />
          {val.headlamp > 0 && <span className="absolute -bottom-[10px] text-[8px] font-bold leading-none tracking-wide">{LAMP_LABEL[val.headlamp]}</span>}
        </span>,
        () => {
          const next = (val.headlamp + 1) % 4;
          setVal('headlamp', next);
          setHeadlights(next >= 2);
        },
      )}
      {btn(
        1062,
        'Demister',
        <Ic.Defrost size={30} style={{ color: on.defrost ? (wall ? '#6f95ff' : t.blue) : undefined }} />,
        () => toggle('defrost'),
      )}
      {btn(1128, 'Volume', <Ic.Volume size={30} />, () => setVol((v) => !v))}

      {vol && (
        <div
          className="absolute z-40 flex flex-col items-center gap-3 rounded-[26px] px-3 py-5"
          style={{ left: 1128, bottom: BAR_H + 8, width: 70, transform: 'translateX(-50%)', background: t.panel, color: t.text, backdropFilter: 'blur(24px)' }}
        >
          <span className="tnum text-[19px]">{media.volume}</span>
          <input
            type="range"
            min={0}
            max={100}
            value={media.volume}
            aria-label="Volume"
            onChange={(e) => patchMedia({ volume: Number(e.target.value) })}
            className="h-[170px] w-6 cursor-pointer accent-[#4a74ff]"
            style={{ writingMode: 'vertical-lr', direction: 'rtl' } as React.CSSProperties}
          />
        </div>
      )}
    </div>
  );
}
