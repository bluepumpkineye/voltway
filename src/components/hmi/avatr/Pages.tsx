'use client';

import React from 'react';
import type { Vehicle } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import * as Ha from '../harmonyos/icons';
import { useHaLocal } from '../harmonyos/shared';
import * as Ic from './icons';
import { useAv, BAR_H } from './theme';
import { CarImage, Pill, TabRow } from './ui';
import { TRACKS } from './media';

/* ------------------------------------------------------------- vehicle control */

const LAMP_LABEL = ['Daytime lights off', 'Position lights', 'Low beam', 'Auto'];
/** The car lists Eco, Comfort, Sport and then its own specials (c10_0076, c10_0022). */
export const MODE_ORDER = ['eco', 'comfort', 'sport', 'gt', 'snow'];
export const byModeOrder = <T extends { id: string }>(modes: T[]): T[] =>
  [...modes].sort((a, b) => MODE_ORDER.indexOf(a.id) - MODE_ORDER.indexOf(b.id));
const MODE_ICON: Record<string, React.ReactNode> = {
  eco: <Ha.Leaf size={26} />,
  comfort: <Ha.Armchair size={26} />,
  sport: <Ha.Flag size={26} />,
  gt: <Ha.Rocket size={26} />,
  snow: <Ha.Hill size={26} />,
};

/**
 * The vehicle control panel (c10_0076), opened by the blue car on the bottom bar: a blue gradient ground,
 * the drive-mode card with the car and its modes down the left, a grid of frosted switches (charge port,
 * window vent, rear fog, screen clean, power off, auto hold, brightness, trunk, parking assist, headlamps,
 * headrest, low-speed tone, the front doors) and the Smart Life card. The switches the 3D car has
 * (modes, lamps, doors, trunk) write the shared store.
 */
export function ControlPanel({ vehicle }: { vehicle: Vehicle }) {
  const { on, toggle, val, setVal, notify } = useHaLocal();
  const { modeId, setCarMode, openings, toggleOpening, setHmiScreen, openSettings } = useVehicleStore();
  const modes = byModeOrder(vehicle.cockpit.driveModes ?? []).slice(0, 4);
  const cur = modeId ?? vehicle.cockpit.driveModes?.[0]?.id;
  const bright = React.useRef<HTMLDivElement>(null);

  const tile = (col: number, row: number, label: string, icon: React.ReactNode, active: boolean, fn: () => void, span = 1) => (
    <button
      key={label}
      type="button"
      aria-pressed={active}
      onClick={fn}
      className="absolute flex flex-col items-center justify-center gap-[10px] rounded-[20px] text-[14px] outline-none focus-visible:ring-2 focus-visible:ring-white"
      style={{
        left: 297 + col * 129.5,
        top: 135 + row * 136,
        width: 112 + (span - 1) * 129.5,
        height: 114,
        background: active ? 'rgba(255,255,255,0.93)' : 'rgba(255,255,255,0.34)',
        color: '#162040',
        backdropFilter: 'blur(14px)',
      }}
    >
      {icon}
      <span className="px-1 text-center leading-tight">{label}</span>
    </button>
  );

  const dragBright = (e: React.PointerEvent) => {
    if (e.type === 'pointermove' && e.buttons === 0) return;
    const r = bright.current?.getBoundingClientRect();
    if (!r) return;
    setVal('brightness', Math.round(30 + Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)) * 70));
  };

  return (
    <div className="absolute inset-0 overflow-hidden" style={{ background: 'linear-gradient(160deg,#1c68e2 0%,#3f87ec 34%,#8fb6f1 68%,#dce8fa 100%)', color: '#162040' }}>
      <Pill label="Customise" style={{ position: 'absolute', left: 40, top: 56, width: 132, height: 52, background: 'rgba(255,255,255,0.3)', color: '#fff', fontSize: 18 }} onClick={() => notify('Customising the panel is not part of the showroom demo')}>
        Customise <span className="ml-[8px] block h-[7px] w-[7px] rounded-full bg-[#ff3b30]" />
      </Pill>
      <Pill label="Go to settings" style={{ position: 'absolute', left: 1098, top: 56, width: 142, height: 52, background: 'rgba(255,255,255,0.3)', color: '#fff', fontSize: 18 }} onClick={() => openSettings('vehicle')}>
        Go to settings
      </Pill>

      <div className="absolute overflow-hidden rounded-[24px]" style={{ left: 40, top: 135, width: 242, height: 522, background: 'rgba(255,255,255,0.3)', backdropFilter: 'blur(16px)' }}>
        <div className="absolute left-[20px] top-[18px] text-[20px] font-medium">Drive mode</div>
        <CarImage w={250} left={-2} top={86} />
        <div className="absolute inset-x-[14px] bottom-[14px] grid grid-cols-2 gap-[10px]">
          {modes.map((m) => (
            <button
              key={m.id}
              type="button"
              aria-pressed={cur === m.id}
              onClick={() => setCarMode(m.id, m.model)}
              className="flex h-[96px] flex-col items-center justify-center gap-[8px] rounded-[18px] text-[14px] leading-tight outline-none focus-visible:ring-2 focus-visible:ring-white"
              style={{ background: cur === m.id ? 'rgba(255,255,255,0.95)' : 'rgba(255,255,255,0.4)', color: cur === m.id ? '#1d3fe0' : '#162040' }}
            >
              {MODE_ICON[m.id] ?? <Ha.Armchair size={26} />}
              <span className="px-1 text-center">{m.label.replace('Shooting Brake ', '')}</span>
            </button>
          ))}
        </div>
      </div>

      {tile(0, 0, 'Charge port', <Ic.Charge size={30} />, on.chargePort, () => toggle('chargePort'))}
      {tile(1, 0, 'Window vent', <Ic.WindowVent size={30} />, on.windowVent, () => toggle('windowVent'))}
      {tile(2, 0, 'Rear fog', <Ic.FogRear size={30} />, on.rearFog, () => toggle('rearFog'))}
      {tile(3, 0, 'Screen clean', <Ic.ScreenClean size={30} />, false, () => notify('Screen cleaning mode is not part of the showroom demo'))}
      {tile(0, 1, 'Power off', <Ic.PowerOff size={30} />, false, () => notify('The showroom car stays on'))}
      {tile(1, 1, 'Auto hold', <Ic.AutoHoldA size={30} />, on.autoHold, () => toggle('autoHold'))}
      <div
        ref={bright}
        className="absolute flex cursor-ew-resize touch-none items-center gap-[12px] overflow-hidden rounded-[20px] px-[18px]"
        style={{ left: 297 + 2 * 129.5, top: 135 + 136, width: 241.5, height: 114, background: 'rgba(255,255,255,0.93)' }}
        onPointerDown={dragBright}
        onPointerMove={dragBright}
        role="slider"
        tabIndex={0}
        aria-label="Screen brightness"
        aria-valuemin={30}
        aria-valuemax={100}
        aria-valuenow={val.brightness}
      >
        <span className="absolute inset-y-0 left-0" style={{ width: `${((val.brightness - 30) / 70) * 100}%`, background: 'rgba(120,150,230,0.26)' }} />
        <Ic.Brightness size={30} style={{ position: 'relative' }} />
        <span className="relative text-[14px] leading-tight">Brightness<br /><span className="tnum text-[13px] opacity-70">{val.brightness}%</span></span>
      </div>
      {tile(0, 2, 'Rear trunk', <Ic.Trunk size={30} />, openings.boot, () => toggleOpening('boot'))}
      {tile(1, 2, 'Parking assist', <Ic.ParkP size={30} />, false, () => setHmiScreen('camera'))}
      <button
        type="button"
        onClick={() => setVal('headlamp', (val.headlamp + 1) % 4)}
        className="absolute flex items-center gap-[12px] rounded-[20px] px-[18px] text-left outline-none focus-visible:ring-2 focus-visible:ring-white"
        style={{ left: 297 + 2 * 129.5, top: 135 + 2 * 136, width: 241.5, height: 114, background: val.headlamp ? 'rgba(255,255,255,0.93)' : 'rgba(255,255,255,0.34)', color: '#162040', backdropFilter: 'blur(14px)' }}
      >
        <Ic.Headlamp size={30} />
        <span className="text-[14px] leading-tight">Headlamp control<br /><span className="text-[12px] opacity-70">{LAMP_LABEL[val.headlamp]}</span></span>
      </button>
      {tile(0, 3, 'Headrest mode', <Ic.HeadrestMode size={30} />, on.headrest, () => toggle('headrest'))}
      {tile(1, 3, 'Low-speed tone', <Ic.AlertTone size={30} />, !on.lowToneOff, () => toggle('lowToneOff'))}
      <div className="absolute flex items-center rounded-[20px] px-[10px]" style={{ left: 297 + 2 * 129.5, top: 135 + 3 * 136, width: 241.5, height: 114, background: 'rgba(255,255,255,0.34)', backdropFilter: 'blur(14px)', color: '#162040' }}>
        {(['doorFL', 'doorFR'] as const).map((d, i) => (
          <button key={d} type="button" aria-pressed={openings[d]} onClick={() => toggleOpening(d)} className="flex h-[94px] flex-1 flex-col items-center justify-center gap-[6px] rounded-[16px] text-[13px] outline-none" style={{ background: openings[d] ? 'rgba(255,255,255,0.95)' : 'transparent', order: i ? 2 : 0 }}>
            {i === 1 && <span className="sr-only">Right front door</span>}
            <span>{i ? 'Right front' : 'Left front'}</span>
          </button>
        ))}
        <span className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"><Ic.DoorGlyph size={30} /></span>
      </div>

      <div className="absolute overflow-hidden rounded-[24px] px-[22px] py-[22px]" style={{ left: 815, top: 121, width: 236, height: 536, background: 'linear-gradient(180deg,rgba(255,255,255,0.46),rgba(255,255,255,0.18))', backdropFilter: 'blur(16px)' }}>
        <Ic.SmartLife size={46} style={{ opacity: 0.8 }} />
        <p className="mt-[40px] text-[15px] leading-[1.55]" style={{ color: 'rgba(22,32,64,0.78)' }}>
          Scenes you add in the Smart Life app on your phone are shown here.
        </p>
        <button type="button" onClick={() => notify('Smart Life is not part of the showroom demo')} className="absolute bottom-[30px] left-[22px] text-[15px] outline-none">Learn more</button>
      </div>
    </div>
  );
}

/* --------------------------------------------------------------------- climate */

/**
 * The climate page (c10_0018, c10_0079): the cabin filling the screen, the driver's temperature down the
 * left and the passenger's down the right as a dial (tap the faint number above or below to step by half
 * a degree), the air quality, the water-ion purifier and the fan across the top, and under the cabin the
 * sync, the free wind, the air direction, the power key, auto, A/C and the heated wheel.
 */
export function ClimatePage() {
  const t = useAv();
  const dark = t.tone === 'dark';
  const { climate, patchClimate } = useVehicleStore();
  const { on, toggle, val, setVal, slug } = useHaLocal();
  const fan = climate.fanSpeed; // 0 - 5
  const track = React.useRef<HTMLDivElement>(null);
  const dragFan = (e: React.PointerEvent) => {
    if (e.type === 'pointermove' && e.buttons === 0) return;
    const r = track.current?.getBoundingClientRect();
    if (!r) return;
    patchClimate({ fanSpeed: Math.round(Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)) * 5) });
  };

  const setSide = (key: 'driverTempC' | 'passengerTempC', v: number) => {
    const c = Math.min(32, Math.max(16, Math.round(v * 2) / 2));
    patchClimate(climate.sync ? { driverTempC: c, passengerTempC: c } : { [key]: c });
  };
  const dial = (key: 'driverTempC' | 'passengerTempC', x: number) => {
    const v = climate[key];
    return (
      <div className="absolute flex flex-col items-center" style={{ left: x - 70, top: 224, width: 140 }}>
        <button type="button" aria-label={`Raise to ${(v + 0.5).toFixed(1)}`} onClick={() => setSide(key, v + 0.5)} className="tnum py-[12px] text-[28px] font-light outline-none" style={{ opacity: 0.38 }}>
          {(v + 0.5).toFixed(1)}
        </button>
        <div className="tnum py-[2px] text-[52px] font-medium leading-none" aria-live="polite">{v.toFixed(1)}</div>
        <button type="button" aria-label={`Lower to ${(v - 0.5).toFixed(1)}`} onClick={() => setSide(key, v - 0.5)} className="tnum py-[12px] text-[28px] font-light outline-none" style={{ opacity: 0.38 }}>
          {(v - 0.5).toFixed(1)}
        </button>
      </div>
    );
  };

  const air = [
    { icon: <Ha.AirFace size={28} />, label: 'Face' },
    { icon: <Ha.AirBoth size={28} />, label: 'Face and feet' },
    { icon: <Ha.AirFeet size={28} />, label: 'Feet' },
    { icon: <Ha.AirDefrost size={28} />, label: 'Feet and demist' },
  ];
  const chip = (label: string, left: number, w: number, active: boolean, fn: () => void) => (
    <Pill label={label} on={active} onClick={fn} style={{ position: 'absolute', left, bottom: BAR_H + 112, width: w, height: 50, fontSize: 18 }}>
      {label}
    </Pill>
  );
  const row2 = BAR_H + 26;

  return (
    <div className="absolute inset-0 overflow-hidden" style={{ background: t.bg, color: t.text }}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={`/hmi/${slug}/cabin-climate-${t.tone}.webp`} alt="" draggable={false} className="absolute max-w-none" style={{ left: -40, top: -78, width: 1360 }} />

      <span className="absolute flex items-center gap-[10px] text-[14px] leading-tight" style={{ left: 40, top: 56, opacity: 0.85 }}>
        <Ic.Leaf size={26} style={{ color: t.green }} />
        <span>PM 2.5<br />Inside 8</span>
      </span>
      <Pill label="Water-ion purifier" on={on.purifier} onClick={() => toggle('purifier')} style={{ position: 'absolute', left: 190, top: 58, width: 150, height: 46, fontSize: 17 }}>
        Water-ion purify
      </Pill>

      <div className="absolute flex items-center gap-[18px]" style={{ left: 392, top: 56, width: 530 }}>
        <Ha.Fan size={22} style={{ opacity: 0.55 }} />
        <div
          ref={track}
          className="relative h-[46px] flex-1 cursor-ew-resize touch-none rounded-full"
          style={{ background: dark ? 'rgba(255,255,255,0.10)' : 'rgba(110,126,176,0.22)' }}
          onPointerDown={dragFan}
          onPointerMove={dragFan}
          role="slider"
          tabIndex={0}
          aria-label="Fan speed"
          aria-valuemin={0}
          aria-valuemax={5}
          aria-valuenow={fan}
          onKeyDown={(e) => {
            if (e.key === 'ArrowRight') patchClimate({ fanSpeed: Math.min(5, fan + 1) });
            if (e.key === 'ArrowLeft') patchClimate({ fanSpeed: Math.max(0, fan - 1) });
          }}
        >
          {[1, 2, 3, 4, 5].map((i) => (
            <span key={i} className="absolute top-1/2 h-[5px] w-[5px] -translate-y-1/2 rounded-full" style={{ left: `calc(23px + (100% - 46px) * ${i / 5})`, background: t.text3 }} />
          ))}
          <span className="absolute top-1/2 h-[34px] w-[34px] -translate-y-1/2 rounded-full bg-white" style={{ left: `calc(6px + (100% - 46px) * ${fan / 5})`, boxShadow: '0 2px 10px rgba(30,40,90,0.3)' }} />
        </div>
        <Ha.Fan size={34} style={{ opacity: 0.7 }} />
      </div>
      <Pill label="Climate settings" onClick={() => setVal('climateMore', val.climateMore ? 0 : 1)} style={{ position: 'absolute', left: 1092, top: 56, width: 148, height: 50, fontSize: 18 }}>
        Settings
      </Pill>

      {dial('driverTempC', 92)}
      {dial('passengerTempC', 1188)}

      {chip('Temp sync', 40, 140, climate.sync, () => patchClimate({ sync: !climate.sync }))}
      {chip('Free wind ›', 232, 108, !!on.freeWind, () => toggle('freeWind'))}
      {chip('Driver mode', 392, 128, !!on.driverMode, () => toggle('driverMode'))}
      <Pill label="Maximum heating" on={on.demistMax} onClick={() => toggle('demistMax')} style={{ position: 'absolute', left: 962, bottom: BAR_H + 112, width: 82, height: 50 }}>
        <Ha.SunMax size={26} />
      </Pill>
      <Pill label="Maximum cooling" on={on.coolMax} onClick={() => toggle('coolMax')} style={{ position: 'absolute', left: 1126, bottom: BAR_H + 112, width: 82, height: 50 }}>
        <Ha.AcMax size={26} />
      </Pill>

      <div className="absolute flex overflow-hidden rounded-full" style={{ left: 40, bottom: row2, width: 360, height: 54, background: t.seg }} role="group" aria-label="Air direction">
        {air.map((a, i) => (
          <button
            key={a.label}
            type="button"
            aria-label={a.label}
            aria-pressed={val.airL === i}
            onClick={() => setVal('airL', i)}
            className="flex flex-1 items-center justify-center outline-none"
            style={{ background: val.airL === i ? t.blue : 'transparent', color: val.airL === i ? '#fff' : t.text }}
          >
            {a.icon}
          </button>
        ))}
      </div>
      <Pill label="Climate power" on={!on.climateOff} onClick={() => toggle('climateOff')} style={{ position: 'absolute', left: 567, bottom: row2, width: 140, height: 54 }}>
        <Ha.Power size={27} />
      </Pill>
      <Pill label="Auto" on={on.climateAuto} onClick={() => toggle('climateAuto')} style={{ position: 'absolute', left: 786, bottom: row2, width: 112, height: 54, fontSize: 19 }}>
        Auto
      </Pill>
      <Pill label="A/C" on={climate.acOn} onClick={() => patchClimate({ acOn: !climate.acOn })} style={{ position: 'absolute', left: 946, bottom: row2, width: 112, height: 54, fontSize: 19 }}>
        A/C
      </Pill>
      <Pill label="Heated steering wheel" on={on.wheelHeat} onClick={() => toggle('wheelHeat')} style={{ position: 'absolute', left: 1126, bottom: row2, width: 82, height: 54 }}>
        <Ic.WheelHeat size={27} />
      </Pill>
    </div>
  );
}

/* ----------------------------------------------------------------------- seats */

const SEAT_TABS = ['Seat heating', 'Seat ventilation', 'Seat massage', 'Zero gravity'];
/** The four seats and where their badges sit on the cabin picture (fractions of it). */
const SEATS = [
  { id: 'driver', label: 'Driver', x: 0.41, y: 0.4, front: true },
  { id: 'passenger', label: 'Passenger', x: 0.69, y: 0.45, front: true },
  { id: 'rearL', label: 'Rear left', x: 0.28, y: 0.78, front: false },
  { id: 'rearR', label: 'Rear right', x: 0.54, y: 0.85, front: false },
] as const;
const MASSAGE = ['Wave', 'Cat step', 'Stretch', 'Snake', 'Butterfly'];

/**
 * The seat page (c10_0035-38): four tabs along the top (heating, ventilation, massage, zero gravity), the
 * cabin from above and behind with a round badge on each seat, and at the foot the auto switches (heating,
 * ventilation), the seat pickers and the massage programmes, or the zero-gravity posture keys. The front
 * seats' heating is the shared climate state, so the home and the climate page agree with it.
 */
export function SeatsPage() {
  const t = useAv();
  const { climate, patchClimate } = useVehicleStore();
  const { val, setVal, slug, on, toggle } = useHaLocal();
  const [tab, setTab] = React.useState(0);
  const [seat, setSeat] = React.useState<(typeof SEATS)[number]['id']>('driver');
  const key = (part: string) => `${tab}.${seat}.${part}`;
  const level = (id: 'driver' | 'passenger' | 'rearL' | 'rearR') => {
    if (tab === 0 && id === 'driver') return climate.seatHeatDriver;
    if (tab === 0 && id === 'passenger') return climate.seatHeatPassenger;
    return val[`${tab}.${id}.level`];
  };
  const bump = (id: 'driver' | 'passenger' | 'rearL' | 'rearR') => {
    const next = (level(id) + 1) % 4;
    if (tab === 0 && id === 'driver') patchClimate({ seatHeatDriver: next });
    else if (tab === 0 && id === 'passenger') patchClimate({ seatHeatPassenger: next });
    else setVal(`${tab}.${id}.level`, next);
  };
  const icons = [<Ha.HeatUp key="h" size={28} />, <Ha.Fan key="f" size={28} />, <Ha.HeatWave key="m" size={28} />, <Ha.SeatHeat key="z" size={28} />];

  return (
    <div className="absolute inset-0 overflow-hidden" style={{ background: t.bg, color: t.text }}>
      <TabRow tabs={SEAT_TABS} value={tab} onChange={setTab} className="absolute flex gap-[64px]" style={{ left: 640, top: 52, transform: 'translateX(-50%)' }} />
      {tab === 2 && (
        <Pill label="Massage settings" style={{ position: 'absolute', left: 1108, top: 48, width: 128, height: 46, fontSize: 17 }} onClick={() => toggle('massageSettings')}>Settings</Pill>
      )}

      <div className="absolute" style={{ left: 640, top: 96, width: 900, height: 564, transform: 'translateX(-50%)' }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={`/hmi/${slug}/cabin-seats-${t.tone}.webp`} alt="" draggable={false} className="h-full w-full object-contain" style={{ WebkitMaskImage: 'radial-gradient(ellipse at 50% 50%, #000 62%, transparent 100%)', maskImage: 'radial-gradient(ellipse at 50% 50%, #000 62%, transparent 100%)' }} />
        {SEATS.map((s) => {
          const sel = s.id === seat;
          const lit = level(s.id) > 0;
          return (
            <button
              key={s.id}
              type="button"
              aria-label={`${s.label} seat`}
              aria-pressed={sel}
              onClick={() => (sel ? bump(s.id) : setSeat(s.id))}
              className="absolute flex h-[58px] w-[58px] items-center justify-center rounded-full outline-none transition-transform"
              style={{
                left: `${s.x * 100}%`,
                top: `${s.y * 100}%`,
                background: lit ? t.blue : '#f6f7fb',
                color: lit ? '#fff' : '#17192b',
                boxShadow: sel ? `0 0 0 4px ${t.blue}55, 0 4px 14px rgba(30,40,90,0.28)` : '0 4px 14px rgba(30,40,90,0.22)',
                transform: `translate(-50%, -50%) scale(${sel ? 1.08 : 1})`,
              }}
            >
              {icons[tab]}
              {lit && <span className="absolute -bottom-[2px] -right-[2px] flex h-[20px] w-[20px] items-center justify-center rounded-full bg-[#162040] text-[11px] text-white">{level(s.id)}</span>}
            </button>
          );
        })}
      </div>

      <div className="absolute" style={{ left: 40, right: 40, bottom: BAR_H + 22 }}>
        {tab <= 1 && (
          <div className="flex gap-[2px]">
            <Pill label="Driver auto" on={tab === 0 ? !!on.autoHeatD : !!on.autoVentD} onClick={() => toggle(tab === 0 ? 'autoHeatD' : 'autoVentD')} style={{ height: 50, padding: '0 22px', fontSize: 17, borderRadius: 25, background: (tab === 0 ? on.autoHeatD : on.autoVentD) ? '#e0582a' : t.seg }}>
              Driver auto {tab === 0 ? 'heat' : 'ventilation'}
            </Pill>
            <Pill label="Passenger auto" on={tab === 0 ? !!on.autoHeatP : !!on.autoVentP} onClick={() => toggle(tab === 0 ? 'autoHeatP' : 'autoVentP')} style={{ height: 50, padding: '0 22px', fontSize: 17, borderRadius: 25, marginLeft: 10, background: (tab === 0 ? on.autoHeatP : on.autoVentP) ? '#e0582a' : t.seg }}>
              Passenger auto {tab === 0 ? 'heat' : 'ventilation'}
            </Pill>
          </div>
        )}
        {tab === 2 && (
          <div className="flex items-center justify-between">
            <div className="flex gap-[6px]">
              {(['driver', 'passenger'] as const).map((s) => (
                <Pill key={s} label={s} on={seat === s} onClick={() => setSeat(s)} style={{ height: 46, width: 84, fontSize: 17 }}>{s === 'driver' ? 'Driver' : 'Pass.'}</Pill>
              ))}
            </div>
            <div className="flex gap-[6px]">
              {(['rearL', 'rearR'] as const).map((s) => (
                <Pill key={s} label={s} on={seat === s} onClick={() => setSeat(s)} style={{ height: 46, width: 104, fontSize: 17 }}>{s === 'rearL' ? 'Rear left' : 'Rear right'}</Pill>
              ))}
            </div>
          </div>
        )}
        {tab === 2 && (
          <div className="mt-[14px] flex h-[52px] items-center justify-around rounded-full" style={{ background: t.seg }}>
            {MASSAGE.map((m, i) => (
              <button key={m} type="button" aria-pressed={val[key('prog')] === i + 1} onClick={() => setVal(key('prog'), val[key('prog')] === i + 1 ? 0 : i + 1)} className="h-full px-[26px] text-[17px] outline-none" style={{ color: val[key('prog')] === i + 1 ? t.blue : t.text }}>
                {m}
              </button>
            ))}
          </div>
        )}
        {tab === 3 && (
          <div>
            <div className="flex gap-[6px]">
              {(['driver', 'passenger'] as const).map((s) => (
                <Pill key={s} label={s} on={seat === s} onClick={() => setSeat(s)} style={{ height: 46, width: 84, fontSize: 17 }}>{s === 'driver' ? 'Driver' : 'Pass.'}</Pill>
              ))}
            </div>
            <div className="mt-[12px] flex gap-[10px]">
              <Pill label="Zero-gravity posture" on={val[key('pose')] === 1} onClick={() => setVal(key('pose'), val[key('pose')] === 1 ? 0 : 1)} style={{ height: 52, width: 96 }}>
                <Ha.SeatPose n={1} size={28} />
              </Pill>
              <Pill label="Lounge posture" on={val[key('pose')] === 2} onClick={() => setVal(key('pose'), val[key('pose')] === 2 ? 0 : 2)} style={{ height: 52, width: 96 }}>
                <Ha.Nap size={28} />
              </Pill>
              <Pill label="Clear position" onClick={() => setVal(key('pose'), 0)} style={{ height: 52, padding: '0 26px', fontSize: 17 }}>
                Clear position
              </Pill>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ----------------------------------------------------------------------- music */

const MUSIC_TABS = ['Recommended', 'Spatial audio', 'Charts', 'Podcasts', 'Kids', 'Featured'];
const COVERS = ['#7a5f8c,#d9c6e8', '#5a9a8a,#e6d98f', '#3d6aa8,#e0a24a', '#a86a8a,#f2d7c4', '#2f3b55,#a8b4cc', '#c4452e,#2a2f55', '#d9a02e,#3a4fa0', '#5a4a8c,#c46a5a'];

/**
 * The music app (c10_0017): Huawei Music's recommendations. Its source and tabs along the top, three feature
 * cards (the car's own are album art we do not ship: gradients stand in), the playlists for you, and the
 * player along the foot with the shared media state's play and track.
 */
export function MediaPage() {
  const t = useAv();
  const { media, patchMedia } = useVehicleStore();
  const [tab, setTab] = React.useState(0);
  const track = TRACKS[media.trackIndex % TRACKS.length];
  const next = (d: number) => patchMedia({ trackIndex: (media.trackIndex + d + TRACKS.length) % TRACKS.length });
  const FEATURES = [
    { title: 'Listen now', sub: `${TRACKS[0].title} · ${TRACKS[0].artist}`, bg: 'linear-gradient(120deg,#23242c,#3a3c48)', fg: '#fff' },
    { title: 'Daily 30', sub: `${TRACKS[1].title} · ${TRACKS[1].artist}`, bg: 'linear-gradient(120deg,#6b7596,#a9b2cf)', fg: '#fff' },
    { title: 'New songs', sub: `${TRACKS[2].title} · ${TRACKS[2].artist}`, bg: 'linear-gradient(120deg,#4a3a2a,#7a5f3e)', fg: '#fff' },
  ];

  return (
    <div className="absolute inset-0 overflow-hidden" style={{ background: t.bg, color: t.text }}>
      <div className="absolute flex items-center gap-[10px]" style={{ left: 40, top: 80 }}>
        <span className="flex h-[40px] w-[40px] items-center justify-center rounded-full text-white" style={{ background: 'linear-gradient(160deg,#6f8bff,#3b57e8)' }}><Ha.Music size={22} /></span>
        <span className="text-[18px]">Music ▾</span>
      </div>
      <TabRow tabs={MUSIC_TABS} value={tab} onChange={setTab} className="absolute flex gap-[44px]" style={{ left: 250, top: 84 }} />
      <span className="absolute" style={{ left: 1196, top: 84 }}><Ha.Search size={28} /></span>

      <div className="absolute flex gap-[18px]" style={{ left: 40, top: 142, width: 1200 }}>
        {FEATURES.map((f, i) => (
          <button key={f.title} type="button" onClick={() => { patchMedia({ trackIndex: i, playing: true }); }} className="relative h-[190px] flex-1 overflow-hidden rounded-[20px] px-[22px] py-[22px] text-left outline-none" style={{ background: f.bg, color: f.fg }}>
            <span className="block text-[26px] font-semibold">{f.title}</span>
            <span className="mt-[8px] block max-w-[190px] truncate text-[15px] opacity-80">{f.sub}</span>
            <span className="absolute bottom-[18px] left-[22px] flex h-[40px] w-[40px] items-center justify-center rounded-full" style={{ background: 'rgba(255,255,255,0.3)' }}><Ha.Play size={20} /></span>
            <span className="absolute right-[18px] top-[18px] h-[150px] w-[150px] rounded-[10px]" style={{ background: `linear-gradient(140deg,${COVERS[i * 2].split(',')[0]},${COVERS[i * 2].split(',')[1]})`, opacity: 0.9 }} />
          </button>
        ))}
      </div>

      <div className="absolute text-[20px]" style={{ left: 40, top: 360 }}>Playlists for you</div>
      <div className="absolute flex gap-[16px]" style={{ left: 40, top: 400, width: 1200 }}>
        {COVERS.map((c, i) => {
          const [a, b] = c.split(',');
          return (
            <button key={c} type="button" onClick={() => patchMedia({ trackIndex: i % TRACKS.length, playing: true })} className="w-[138px] shrink-0 text-left outline-none">
              <span className="relative block h-[138px] w-[138px] rounded-[14px]" style={{ background: `linear-gradient(140deg,${a},${b})` }}>
                <span className="absolute bottom-[10px] left-[10px] flex h-[34px] w-[34px] items-center justify-center rounded-full text-white" style={{ background: 'rgba(0,0,0,0.38)' }}><Ha.Play size={16} /></span>
              </span>
              <span className="mt-[8px] block truncate text-[14px]">{['Awards decade', 'Sleepover mix', 'Million sellers', 'Duets', 'Warm voices', 'Hip-hop and break', 'Nostalgia', 'Anime picks'][i]}</span>
            </button>
          );
        })}
      </div>

      <div className="absolute inset-x-0 flex items-center" style={{ bottom: BAR_H, height: 76, background: t.bar }}>
        <span className="ml-[14px] block h-[52px] w-[52px] rounded-[8px]" style={{ background: 'linear-gradient(140deg,#5a4a8c,#c46a5a)' }} />
        <span className="ml-[16px] w-[300px] truncate text-[19px]">{track.title} <span className="rounded-[4px] border px-[4px] text-[10px]" style={{ color: t.red, borderColor: t.red }}>VIP</span></span>
        <div className="absolute flex items-center gap-[64px]" style={{ left: 500 }}>
          <button type="button" aria-label="Favourite" className="outline-none"><Ha.Heart size={26} /></button>
          <button type="button" aria-label="Previous" onClick={() => next(-1)} className="outline-none"><Ha.Prev size={30} /></button>
          <button type="button" aria-label={media.playing ? 'Pause' : 'Play'} onClick={() => patchMedia({ playing: !media.playing })} className="outline-none">{media.playing ? <Ha.Pause size={34} /> : <Ha.Play size={34} />}</button>
          <button type="button" aria-label="Next" onClick={() => next(1)} className="outline-none"><Ha.Next size={30} /></button>
          <button type="button" aria-label="Queue" className="outline-none"><Ha.MoreV size={26} /></button>
        </div>
        <span className="absolute" style={{ right: 36 }}><Ha.Repeat size={26} /></span>
      </div>
    </div>
  );
}
