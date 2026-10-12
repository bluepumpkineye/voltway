'use client';

import React from 'react';
import { useVehicleStore } from '@/store/vehicle-store';
import type { Vehicle } from '@/data/vehicles/schema';
import * as Ic from './icons';
import { glass, GLASS_ON, useHa } from './theme';
import { Wallpaper, useHaLocal } from './shared';
import { ComfortBody, COMFORT_BG, useWallpaper } from './Desktop';

/**
 * The Control Centre (vehicle control): the drive modes on the left, a grid of
 * switches, the headlamp selector, the brightness slider and the driver's
 * comfort card. Laid out as the car's own: 110 px tiles 21 apart in a grid whose
 * third group is two tiles wide. The drive mode, the lock, the bonnet, the
 * tailgate, the headlamps and the light/dark mode are live (the 3D car follows).
 */
export function ControlCentre({ vehicle }: { vehicle: Vehicle }) {
  const t = useHa();
  const wp = useWallpaper(t.tone);
  const { modeId, setCarMode, openings, toggleOpening, locked, setLocked, setHmiTheme, openSettings } =
    useVehicleStore();
  const { on, toggle, val, setVal, notify } = useHaLocal();
  const modes = vehicle.cockpit.driveModes ?? [];
  const mode = modeId ?? 'comfort';

  const X = [298, 429, 560, 691, 953, 1083];
  const Y = [151, 282, 413, 544];

  const tile = (
    col: number,
    row: number,
    icon: React.ReactNode,
    label: string,
    active: boolean,
    onClick: () => void,
    spanCols = 1,
  ) => (
    <button
      key={`${col}-${row}`}
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className="absolute flex flex-col items-center justify-center gap-[9px] rounded-[26px] outline-none transition-colors focus-visible:ring-2 focus-visible:ring-white/70"
      style={{
        left: X[col],
        top: Y[row],
        width: spanCols === 2 ? 241 : 110,
        height: 110,
        background: active ? GLASS_ON : 'rgba(255,255,255,0.19)',
        color: active ? '#17181b' : '#fff',
        backdropFilter: 'blur(18px)',
      }}
    >
      {icon}
      <span className="text-[15px] leading-none">{label}</span>
    </button>
  );

  const modeIcon = (id: string) =>
    id === 'eco' ? <Ic.Leaf size={30} /> : id === 'comfort' ? <Ic.CarSide size={32} /> : id === 'sport' ? <Ic.Flag size={30} /> : <Ic.Rocket size={30} />;

  // brightness: drag across the tile
  const dragBright = (e: React.PointerEvent<HTMLDivElement>) => {
    if (e.type === 'pointermove' && e.buttons === 0) return;
    const r = e.currentTarget.getBoundingClientRect();
    setVal('brightness', Math.round(Math.min(100, Math.max(20, ((e.clientX - r.left) / r.width) * 100)) / 5) * 5);
  };

  const lamp = ['Off', 'Position', 'Low beam', 'Auto'];

  return (
    <div className="absolute inset-0 overflow-hidden" style={{ color: '#fff' }}>
      <Wallpaper id={wp.id} className="absolute inset-0 h-full w-full" />
      <div className="absolute inset-0" style={{ background: 'rgba(8,10,24,0.50)', backdropFilter: 'blur(34px) saturate(1.2)' }} />

      <button type="button" className="absolute flex h-[53px] items-center gap-3 rounded-full px-[24px] text-[20px] outline-none" style={{ left: 34, top: 78, width: 140, ...glass(0.2, 14) }} onClick={() => notify('Customise rearranges the tiles (showroom demo)')}>
        Customise
        <span className="h-[10px] w-[10px] rounded-full" style={{ background: '#ff3b30' }} />
      </button>
      <button type="button" className="absolute flex h-[53px] items-center justify-center rounded-full text-[20px] outline-none" style={{ left: 1054, top: 78, width: 138, ...glass(0.2, 14) }} onClick={() => openSettings('vehicle')}>
        Settings
      </button>

      {/* drive mode */}
      <div className="absolute overflow-hidden rounded-[30px]" style={{ left: 36, top: 151, width: 240, height: 502, background: 'linear-gradient(180deg, rgba(255,255,255,0.20), rgba(255,255,255,0.12))', backdropFilter: 'blur(18px)' }}>
        <div className="absolute left-[21px] top-[22px] text-[22px] font-semibold">Drive mode</div>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/hmi/luxeed-rx/car34.webp" alt="" draggable={false} className="absolute" style={{ left: -8, top: 92, width: 262 }} />
        <div className="absolute grid grid-cols-2 gap-[12px]" style={{ left: 17, top: 287 }}>
          {modes.filter((m) => m.id !== 'custom').map((m) => {
            const active = mode === m.id;
            return (
              <button
                key={m.id}
                type="button"
                aria-pressed={active}
                onClick={() => setCarMode(m.id, m.model)}
                className="flex h-[92px] w-[95px] flex-col items-center justify-center gap-[7px] rounded-[22px] outline-none transition-colors focus-visible:ring-2 focus-visible:ring-white/70"
                style={{ background: active ? GLASS_ON : 'rgba(255,255,255,0.18)', color: active ? '#17181b' : '#fff' }}
              >
                <span style={{ color: active && m.id === 'comfort' ? '#2f56ee' : undefined }}>{modeIcon(m.id)}</span>
                <span className="text-[15px] leading-none">{m.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* column group one */}
      {tile(0, 0, <Ic.TrunkRear size={34} />, 'Tailgate', openings.boot, () => toggleOpening('boot'))}
      {tile(1, 0, <Ic.MirrorAdj size={34} />, 'Mirrors', on.mirrorAdj, () => toggle('mirrorAdj'))}
      {tile(2, 0, <Ic.Hill size={34} />, 'Hill descent', on.hill, () => toggle('hill'))}
      {tile(0, 1, <Ic.ChargePort size={34} />, 'Charge port', on.chargePort, () => toggle('chargePort'))}
      {tile(1, 1, <Ic.Power size={34} />, 'Power off', false, () => notify('Powering off would end the showroom demo'))}
      {tile(2, 1, <Ic.AutoHold size={34} />, 'Auto hold', on.autoHold, () => toggle('autoHold'))}
      {tile(0, 2, <Ic.ChildLock size={34} />, 'Child lock', on.childLock, () => toggle('childLock'))}
      {tile(1, 2, <Ic.ParkAssist size={34} />, 'Park assist', on.parkAssist, () => toggle('parkAssist'))}
      {tile(2, 2, <Ic.DoorLock size={34} />, 'Door lock', locked, () => setLocked(!locked))}
      {tile(0, 3, <Ic.TrunkFront size={34} />, 'Frunk', openings.frunk, () => toggleOpening('frunk'))}
      {tile(1, 3, <Ic.Sunshade size={34} />, 'Sunshade', on.sunshade, () => toggle('sunshade'))}
      {tile(2, 3, <Ic.PassengerScreen size={34} />, 'Passenger screen', on.passengerScreen, () => toggle('passengerScreen'))}

      {/* column group two: wide cards */}
      <div
        className="absolute flex cursor-ew-resize items-center gap-4 overflow-hidden rounded-[26px] px-[26px]"
        style={{ left: X[3], top: Y[0], width: 241, height: 110, background: 'linear-gradient(90deg,#f1ebe5 0%,#f1ebe5 var(--fill),rgba(255,255,255,0.19) var(--fill))', color: '#17181b', ['--fill' as string]: `${val.brightness}%` }}
        onPointerDown={dragBright}
        onPointerMove={dragBright}
        role="slider"
        aria-label="Brightness"
        aria-valuenow={val.brightness}
        aria-valuemin={20}
        aria-valuemax={100}
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'ArrowRight') setVal('brightness', Math.min(100, val.brightness + 5));
          if (e.key === 'ArrowLeft') setVal('brightness', Math.max(20, val.brightness - 5));
        }}
      >
        <Ic.BrightnessA size={42} />
        <span>
          <span className="block text-[17px] leading-tight">Brightness</span>
          <span className="tnum block text-[18px] leading-tight">{val.brightness}%</span>
        </span>
      </div>

      <div className="absolute grid grid-cols-4 overflow-hidden rounded-[26px] p-[5px]" style={{ left: X[3], top: Y[1], width: 241, height: 110, background: 'rgba(255,255,255,0.19)', backdropFilter: 'blur(18px)' }} role="group" aria-label="Headlamps">
        {lamp.map((l, i) => {
          const a = val.headlamp === i;
          return (
            <button
              key={l}
              type="button"
              aria-pressed={a}
              onClick={() => setVal('headlamp', i)}
              className="flex flex-col items-center justify-center gap-[6px] rounded-[21px] text-[12px] outline-none"
              style={{ background: a ? GLASS_ON : 'transparent', color: a ? '#17181b' : '#fff' }}
            >
              {i === 0 ? <span className="text-[13px] font-semibold tracking-wide">OFF</span> : i === 1 ? <Ic.LampPos size={26} /> : i === 2 ? <Ic.LampLow size={26} /> : <span className="text-[13px] font-semibold tracking-wide">AUTO</span>}
              <span className="leading-none">{i === 0 ? 'Off' : i === 1 ? 'Pos.' : i === 2 ? 'Low' : 'Auto'}</span>
            </button>
          );
        })}
      </div>

      <button
        type="button"
        aria-pressed={on.nap}
        onClick={() => toggle('nap')}
        className="absolute flex items-center gap-4 rounded-[26px] px-[22px] text-left outline-none"
        style={{ left: X[3], top: Y[2], width: 241, height: 110, background: on.nap ? GLASS_ON : 'rgba(255,255,255,0.19)', color: on.nap ? '#17181b' : '#fff', backdropFilter: 'blur(18px)' }}
      >
        <span className="flex h-[54px] w-[54px] shrink-0 items-center justify-center rounded-full" style={{ background: 'rgba(255,255,255,0.18)' }}><Ic.Nap size={30} /></span>
        <span>
          <span className="block text-[18px] leading-tight">Nap mode</span>
          <span className="block text-[15px] leading-tight opacity-65">{on.nap ? 'On' : 'Off'}</span>
        </span>
      </button>

      <div className="absolute grid grid-cols-3 overflow-hidden rounded-[26px] p-[5px]" style={{ left: X[3], top: Y[3], width: 241, height: 110, background: 'rgba(255,255,255,0.19)', backdropFilter: 'blur(18px)' }} role="group" aria-label="Screen position">
        {['Driver', 'Centre', 'Passenger'].map((l, i) => {
          const a = val.screenAim === i;
          return (
            <button
              key={l}
              type="button"
              aria-pressed={a}
              onClick={() => setVal('screenAim', i)}
              className="flex flex-col items-center justify-center gap-[7px] rounded-[21px] text-[13px] outline-none"
              style={{ background: a ? GLASS_ON : 'transparent', color: a ? '#17181b' : '#fff' }}
            >
              <Ic.PassengerScreen size={26} style={{ transform: `perspective(60px) rotateY(${(i - 1) * -28}deg)` }} />
              <span className="leading-none">{l}</span>
            </button>
          );
        })}
      </div>

      {/* column group three */}
      {tile(4, 0, <Ic.ContrastMode size={34} />, 'Light mode', t.tone === 'light', () => setHmiTheme(t.tone === 'light' ? 'dark' : 'light'))}
      {tile(5, 0, <Ic.Headrest size={34} />, 'Headrest', on.headrest, () => toggle('headrest'))}
      {tile(4, 1, <Ic.CarWash size={34} />, 'Car wash', on.carWash, () => toggle('carWash'))}
      {tile(5, 1, <Ic.Sentry size={34} />, 'Sentry', on.sentry, () => toggle('sentry'))}

      <div className="absolute overflow-hidden rounded-[30px]" style={{ left: X[4], top: Y[2], width: 241, height: 241, ...COMFORT_BG }}>
        <ComfortBody />
      </div>

      <div className="absolute left-1/2 flex -translate-x-1/2 items-center gap-2.5" style={{ top: 681 }} aria-hidden>
        <span className="block h-[8px] w-[17px] rounded-full bg-white/90" />
        <span className="block h-[8px] w-[8px] rounded-full bg-white/40" />
      </div>
    </div>
  );
}
