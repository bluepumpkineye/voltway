'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { effectiveRange } from '@/lib/performance';
import { DL } from './theme';
import * as Ic from './icons';
import { useDl } from './shared';

/* ------------------------------------------------------------ shared pieces */

function Pill({
  on, onClick, children, w, h = 44, grow,
}: {
  on?: boolean;
  onClick: () => void;
  children: React.ReactNode;
  w?: number;
  h?: number;
  grow?: boolean;
}) {
  return (
    <button
      type="button"
      aria-pressed={on}
      onClick={onClick}
      className="flex items-center justify-center gap-2 rounded-[8px] px-5 text-[16px] focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
      style={{
        width: w,
        height: h,
        flex: grow ? 1 : undefined,
        background: on ? 'linear-gradient(180deg, rgba(61,139,255,0.55), rgba(61,139,255,0.30))' : DL.card,
        color: DL.text,
        boxShadow: on ? 'inset 0 0 0 1px rgba(140,190,255,0.7)' : undefined,
      }}
    >
      {children}
    </button>
  );
}

function Switch({ on, onClick, label }: { on: boolean; onClick: () => void; label: string }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      aria-label={label}
      onClick={onClick}
      className="relative h-[28px] w-[52px] shrink-0 rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
      style={{ background: on ? DL.accent : 'rgba(255,255,255,0.22)' }}
    >
      <span className="absolute top-[3px] h-[22px] w-[22px] rounded-full bg-white shadow transition-all" style={{ left: on ? 27 : 3 }} />
    </button>
  );
}

function Row({ label, children, sub }: { label: string; sub?: string; children?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-6 rounded-[8px] px-5 py-[7px]" style={{ minHeight: 56, background: DL.card }}>
      <div className="min-w-0">
        <div className="text-[17px] leading-tight">{label}</div>
        {sub && (
          <div className="mt-[3px] text-[12px] leading-snug" style={{ color: DL.text3 }}>
            {sub}
          </div>
        )}
      </div>
      {children}
    </div>
  );
}

export function Segment({ options, value, onPick, minW = 84 }: { options: string[]; value: number; onPick: (i: number) => void; minW?: number }) {
  return (
    <div className="flex overflow-hidden rounded-[8px]" style={{ background: 'rgba(255,255,255,0.10)' }}>
      {options.map((o, i) => (
        <button
          key={o}
          type="button"
          onClick={() => onPick(i)}
          className="h-[38px] px-3 text-[15px] focus:outline-none"
          style={{
            background: value === i ? 'linear-gradient(180deg, rgba(61,139,255,0.6), rgba(61,139,255,0.32))' : 'transparent',
            color: DL.text,
            minWidth: minW,
          }}
        >
          {o}
        </button>
      ))}
    </div>
  );
}

function Slider({ value, onChange, min = 0, max = 100, label, w = 220 }: { value: number; onChange: (n: number) => void; min?: number; max?: number; label: string; w?: number }) {
  return (
    <input
      type="range"
      min={min}
      max={max}
      value={value}
      aria-label={label}
      onChange={(e) => onChange(Number(e.target.value))}
      className="cursor-pointer"
      style={{ width: w, accentColor: DL.accent }}
    />
  );
}

/** a soft blue glow behind a page, as every page of the car's screen has */
export function Glow({ x = '50%', y = '40%', c = 'rgba(40,110,255,0.34)' }: { x?: string; y?: string; c?: string }) {
  return <div className="pointer-events-none absolute inset-0" style={{ background: `radial-gradient(60% 60% at ${x} ${y}, ${c}, transparent 70%)` }} aria-hidden />;
}

/* -------------------------------------------------------------------- climate */

/**
 * The climate page (c10_0040, c10_0069): Front / Rear / Fragrance tabs, the cabin drawn in blue light
 * with the airflow, each side's temperature in big figures with A/C, AUTO, sync and the demisters
 * above, and the fan and air-direction strip along the bottom.
 */
export function ClimatePage({ vehicle }: { vehicle: Vehicle }) {
  const { on, toggle, val, setVal } = useDl();
  const { climate, patchClimate } = useVehicleStore();
  const [img, setImg] = React.useState(true);
  const nudge = (key: 'driverTempC' | 'passengerTempC', d: number) => {
    const next = Math.min(32, Math.max(16, Math.round((climate[key] + d) * 2) / 2));
    patchClimate(climate.sync ? { driverTempC: next, passengerTempC: next } : { [key]: next });
  };
  const big = (side: 'l' | 'r') => {
    const key = side === 'l' ? 'driverTempC' : 'passengerTempC';
    const v = climate[key];
    return (
      <div className="absolute flex flex-col items-center" style={side === 'l' ? { left: 70, top: 150 } : { right: 70, top: 150 }}>
        <button type="button" aria-label={`Raise ${side === 'l' ? 'driver' : 'passenger'} temperature`} onClick={() => nudge(key, 0.5)} className="focus:outline-none" style={{ color: DL.text2 }}><Ic.Chev dir="u" size={26} /></button>
        <span className="tnum text-[56px] font-light leading-none" aria-live="polite">{v % 1 === 0 ? v.toFixed(0) : v.toFixed(1)}<span className="relative -top-[20px] text-[20px]">°C</span></span>
        <button type="button" aria-label={`Lower ${side === 'l' ? 'driver' : 'passenger'} temperature`} onClick={() => nudge(key, -0.5)} className="focus:outline-none" style={{ color: DL.text2 }}><Ic.Chev dir="d" size={26} /></button>
      </div>
    );
  };
  const tabs = ['Front', 'Rear', 'Fragrance'];
  const tog = (label: string, node: React.ReactNode, pressed: boolean, onClick: () => void) => (
    <Pill key={label} on={pressed} onClick={onClick} h={42} w={92}>{node}</Pill>
  );
  const flows = [{ id: 0, node: <Ic.AirFace size={24} /> }, { id: 1, node: <span className="flex"><Ic.AirFace size={20} /><Ic.AirFeet size={20} /></span> }, { id: 2, node: <Ic.AirFeet size={24} /> }, { id: 3, node: <Ic.DefrostFront size={24} /> }];
  return (
    <div className="absolute inset-0">
      <Glow y="45%" />
      <div className="absolute flex gap-[34px] text-[17px]" style={{ left: 0, right: 0, top: 54, justifyContent: 'center' }}>
        {tabs.map((t, i) => (
          <button key={t} type="button" onClick={() => setVal('climateTab', i)} className="relative px-2 pb-2 focus:outline-none" style={{ color: val.climateTab === i ? DL.text : DL.text3 }}>
            {t}
            {val.climateTab === i && <span className="absolute inset-x-2 bottom-0 h-[2px] rounded-full" style={{ background: DL.accent }} />}
          </button>
        ))}
      </div>
      <div className="absolute flex gap-[10px]" style={{ left: 34, top: 108 }}>
        {tog('Power', <Ic.Power size={22} />, climate.acOn, () => patchClimate({ acOn: !climate.acOn }))}
        {tog('A/C', <span className="text-[16px] font-semibold">A/C</span>, climate.acOn && !on.acOff, () => toggle('acOff'))}
        {tog('Auto', <span className="text-[16px] font-semibold">AUTO</span>, val.auto === 1, () => setVal('auto', val.auto === 1 ? 0 : 1))}
        {tog('Recirculation', <Ic.Recirc size={22} />, on.recirc, () => toggle('recirc'))}
        {tog('Sync', <span className="text-[15px]">Sync</span>, climate.sync, () => patchClimate({ sync: !climate.sync }))}
      </div>
      {img && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={`/hmi/${vehicle.slug}/cabin-climate-dark.webp`}
          alt=""
          draggable={false}
          onError={() => setImg(false)}
          className="pointer-events-none absolute select-none"
          style={{ left: 190, top: 170, width: 900, height: 292, objectFit: 'cover', opacity: 0.95 }}
        />
      )}
      {!img && (
        <svg className="pointer-events-none absolute" style={{ left: 190, top: 180 }} width="900" height="270" viewBox="0 0 900 270" aria-hidden>
          <path d="M120 230C150 110 290 40 450 40S750 110 780 230" fill="none" stroke="rgba(120,180,255,0.5)" strokeWidth="2" />
          <rect x="250" y="120" width="400" height="110" rx="30" fill="rgba(80,140,255,0.16)" stroke="rgba(120,180,255,0.4)" />
          <circle cx="330" cy="150" r="52" fill="none" stroke="rgba(160,200,255,0.65)" strokeWidth="6" />
          <path d="M280 110 450 90 620 110" stroke="rgba(120,200,255,0.7)" strokeWidth="3" fill="none" />
        </svg>
      )}
      {big('l')}
      {big('r')}
      {/* the strip: air direction, fan, seats, demisters */}
      <div className="absolute flex items-center gap-[18px] rounded-[10px] px-[22px]" style={{ left: 34, right: 34, top: 480, height: 82, background: DL.card }}>
        {flows.map((f) => (
          <Pill key={f.id} on={val.flow === f.id} onClick={() => setVal('flow', f.id)} w={72} h={50}>{f.node}</Pill>
        ))}
        <span className="mx-[6px] h-[40px] w-px" style={{ background: DL.line }} />
        <Ic.Fan size={22} style={{ color: DL.text2 }} />
        <div className="flex w-[290px] gap-[6px]" role="group" aria-label="Fan speed">
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              type="button"
              aria-label={`Fan speed ${n}`}
              onClick={() => patchClimate({ fanSpeed: n, acOn: true })}
              className="relative h-[6px] flex-1 rounded-full focus:outline-none"
              style={{ background: climate.acOn && n <= climate.fanSpeed ? DL.accent : 'rgba(255,255,255,0.2)' }}
            >
              <span className="absolute -inset-y-4 inset-x-0" />
            </button>
          ))}
        </div>
        <Ic.Fan size={30} style={{ color: DL.text }} />
        <span className="mx-[6px] h-[40px] w-px" style={{ background: DL.line }} />
        <Pill on={climate.seatHeatDriver > 0} onClick={() => patchClimate({ seatHeatDriver: climate.seatHeatDriver > 0 ? 0 : 2 })} w={72} h={50}><Ic.SeatHeat size={24} /></Pill>
        <Pill on={climate.seatHeatPassenger > 0} onClick={() => patchClimate({ seatHeatPassenger: climate.seatHeatPassenger > 0 ? 0 : 2 })} w={72} h={50}><Ic.SeatHeat size={24} /></Pill>
        <Pill on={on.defrost} onClick={() => toggle('defrost')} w={72} h={50}><Ic.DefrostFront size={24} /></Pill>
        <Pill on={on.defrostRear} onClick={() => toggle('defrostRear')} w={72} h={50}><Ic.DefrostRear size={24} /></Pill>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------------- seats */

const SEAT_TABS = ['Ventilation', 'Heating', 'Massage', 'Position'];
// where each seat's back is in the picture (blender/scripts/cabin_hmi.py HMI_SEATS, the picture's 760 x 447 contained in
// its box at 330, 106)
const SEATS = [
  { id: 'FL', label: 'Driver', x: 629, y: 410 },
  { id: 'FR', label: 'Passenger', x: 634, y: 256 },
  { id: 'RL', label: 'Rear left', x: 861, y: 415 },
  { id: 'RR', label: 'Rear right', x: 853, y: 254 },
] as const;

/**
 * The seats page (c10_0032): the four seats drawn in the cabin, each with its comfort buttons on its
 * back; tabs for ventilation, heating, massage and position down the left, "all off" and "all on".
 */
export function SeatsPage({ vehicle }: { vehicle: Vehicle }) {
  const { val, setVal, on, toggle, notify } = useDl();
  const { climate, patchClimate } = useVehicleStore();
  const [img, setImg] = React.useState(true);
  const tab = val.seatTab;
  const level = (id: string) => {
    if (tab === 1) return id === 'FL' ? climate.seatHeatDriver : id === 'FR' ? climate.seatHeatPassenger : (on['heat' + id] ? 1 : 0);
    return on[`t${tab}${id}`] ? 1 : 0;
  };
  const press = (id: string) => {
    if (tab === 1 && id === 'FL') return patchClimate({ seatHeatDriver: (climate.seatHeatDriver + 1) % 4 });
    if (tab === 1 && id === 'FR') return patchClimate({ seatHeatPassenger: (climate.seatHeatPassenger + 1) % 4 });
    if (tab === 3) return notify('Seat position (showroom demo)');
    toggle(tab === 1 ? 'heat' + id : `t${tab}${id}`);
  };
  return (
    <div className="absolute inset-0">
      <Glow y="50%" />
      <div className="absolute flex flex-col gap-[10px]" style={{ left: 34, top: 80 }}>
        {SEAT_TABS.map((t, i) => (
          <Pill key={t} on={tab === i} onClick={() => setVal('seatTab', i)} w={150} h={46}>{t}</Pill>
        ))}
      </div>
      <div className="absolute flex flex-col gap-[10px]" style={{ left: 34, bottom: 30 }}>
        <Pill onClick={() => { patchClimate({ seatHeatDriver: 0, seatHeatPassenger: 0 }); notify('All off'); }} w={150} h={42}>All off</Pill>
        <Pill onClick={() => { patchClimate({ seatHeatDriver: 3, seatHeatPassenger: 3 }); notify('All on'); }} w={150} h={42}>All on</Pill>
      </div>
      {img && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={`/hmi/${vehicle.slug}/cabin-seats-dark.webp`}
          alt=""
          draggable={false}
          onError={() => setImg(false)}
          className="pointer-events-none absolute select-none"
          style={{ left: 330, top: 70, width: 760, height: 520, objectFit: 'contain' }}
        />
      )}
      {SEATS.map((s) => {
        const l = level(s.id);
        return (
          <button
            key={s.id}
            type="button"
            aria-label={`${s.label} seat`}
            aria-pressed={l > 0}
            onClick={() => press(s.id)}
            className="absolute flex h-[64px] w-[64px] -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
            style={{
              left: s.x,
              top: s.y,
              background: l > 0 ? 'linear-gradient(180deg, rgba(61,139,255,0.8), rgba(61,139,255,0.5))' : 'rgba(255,255,255,0.14)',
              boxShadow: '0 0 0 1px rgba(255,255,255,0.25)',
            }}
          >
            {tab === 0 ? <Ic.SeatVent size={26} /> : tab === 1 ? <Ic.SeatHeat size={26} /> : <Ic.SeatHeat size={26} />}
            <span className="tnum text-[11px] leading-none">{tab === 1 && l > 0 ? l : s.label.slice(0, 1)}</span>
          </button>
        );
      })}
    </div>
  );
}

/* ----------------------------------------------------------------- settings */

const MENU = ['Search', 'Common', 'Lights', 'Doors & Locks', 'Sound & Display', 'Energy', 'Driving', 'DiPilot', 'DiLink'] as const;

const CLOSURES: { id: 'doorFL' | 'doorFR' | 'doorRL' | 'doorRR' | 'boot'; label: string }[] = [
  { id: 'doorFL', label: 'Front left window' },
  { id: 'doorFR', label: 'Front right window' },
  { id: 'doorRL', label: 'Rear left window' },
  { id: 'doorRR', label: 'Rear right window' },
];

/**
 * Settings (c10_0041, 0042, 0074-0097): a menu down the left (Search, Common, Lights, Doors & Locks,
 * Sound & Display, Energy, Driving, DiPilot, DiLink), the page beside it and the car on the right.
 * Common is the quick panel of tiles; Driving holds the drive modes, the car's own, with the e³
 * manoeuvres opening the chassis page.
 */
export function ControlsPage({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  const { val, setVal, on, toggle, notify } = useDl();
  const {
    locked, setLocked, headlightsOn, setHeadlights, ambientOn, ambientHue, ambientBrightness, setAmbient,
    setHmiScreen, driveMode, modeId, setCarMode, soc, climate, media, patchMedia,
  } = useVehicleStore();
  const [img, setImg] = React.useState(true);
  const page = val.setPage;
  const modes = vehicle.cockpit.driveModes ?? [];
  const street = modes.filter((m) => m.group === 'street');
  const special = modes.filter((m) => m.group === 'special');
  const current = street.findIndex((m) => (modeId ? m.id === modeId : m.model === driveMode));
  const range = effectiveRange(variant, driveMode, soc, climate);
  const hasChassis = (vehicle.tech ?? []).some((d) => d.driver === 'crab' || d.driver === 'compass' || d.driver === 'e3park');

  let body: React.ReactNode;
  switch (MENU[page]) {
    case 'Search':
      body = (
        <div className="flex flex-col gap-[10px]">
          <div className="flex h-[52px] items-center gap-3 rounded-[8px] px-5 text-[17px]" style={{ background: DL.card, color: DL.text3 }}>
            <Ic.Search size={20} /> Search settings
          </div>
          {['Lights', 'Doors & Locks', 'Driving modes', 'Energy', 'Sound & Display'].map((s) => (
            <Row key={s} label={s}><Ic.Chev dir="r" size={18} /></Row>
          ))}
        </div>
      );
      break;
    case 'Common':
      body = (
        <div className="grid grid-cols-4 gap-[10px]">
          {[
            { id: 'bt', label: 'Bluetooth', icon: <Ic.Bluetooth size={26} />, on: true },
            { id: 'wifi', label: 'Wi-Fi', icon: <Ic.Wifi size={26} />, on: on.wifi },
            { id: 'mute', label: 'Mute', icon: <Ic.Mute size={26} />, on: media.volume === 0 },
            { id: 'lock', label: locked ? 'Locked' : 'Unlocked', icon: locked ? <Ic.Lock size={26} /> : <Ic.Unlock size={26} />, on: locked },
            { id: 'lights', label: 'Headlamps', icon: <Ic.Bulb size={26} />, on: headlightsOn },
            { id: 'ambient', label: 'Ambient light', icon: <Ic.Bulb size={26} />, on: ambientOn },
            { id: 'hud', label: 'Head-up display', icon: <Ic.Doc size={26} />, on: on.hud },
            { id: 'autohold', label: 'Auto hold', icon: <Ic.Wheel size={26} />, on: on.autoHold },
          ].map((t) => (
            <button
              key={t.id}
              type="button"
              aria-pressed={t.on}
              onClick={() => {
                if (t.id === 'mute') patchMedia({ volume: media.volume === 0 ? 40 : 0 });
                else if (t.id === 'lock') setLocked(!locked);
                else if (t.id === 'lights') setHeadlights(!headlightsOn);
                else if (t.id === 'ambient') setAmbient({ ambientOn: !ambientOn });
                else if (t.id === 'hud') toggle('hud');
                else if (t.id === 'autohold') toggle('autoHold');
                else if (t.id === 'wifi') toggle('wifi');
                else notify('Bluetooth (showroom demo)');
              }}
              className="flex h-[96px] flex-col items-center justify-center gap-[8px] rounded-[8px] text-[14px] focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
              style={{ background: t.on ? 'linear-gradient(180deg, rgba(61,139,255,0.5), rgba(61,139,255,0.26))' : DL.card, boxShadow: t.on ? 'inset 0 0 0 1px rgba(140,190,255,0.6)' : undefined }}
            >
              {t.icon}
              {t.label}
            </button>
          ))}
          <div className="col-span-4 mt-[6px] flex flex-col gap-[10px]">
            <Row label="Volume"><Slider value={media.volume} onChange={(n) => patchMedia({ volume: n })} label="Volume" w={320} /></Row>
            <Row label="Screen brightness"><Slider value={val.brightness} min={30} onChange={(n) => setVal('brightness', n)} label="Screen brightness" w={320} /></Row>
          </div>
        </div>
      );
      break;
    case 'Lights':
      body = (
        <div className="flex flex-col gap-[10px]">
          <div className="flex gap-[10px]">
            {['In-car lights', 'Exterior lights', 'Welcome light'].map((t, i) => (
              <Pill key={t} on={val.lightTab === i} onClick={() => setVal('lightTab', i)} h={40} grow>{t}</Pill>
            ))}
          </div>
          {val.lightTab === 0 && (
            <>
              <Row label="Ambient light"><Switch on={ambientOn} onClick={() => setAmbient({ ambientOn: !ambientOn })} label="Ambient light" /></Row>
              <Row label="Ambient colour"><Slider value={ambientHue} min={0} max={360} onChange={(n) => setAmbient({ ambientHue: n })} label="Ambient colour" /></Row>
              <Row label="Ambient brightness"><Slider value={Math.round(ambientBrightness * 100)} onChange={(n) => setAmbient({ ambientBrightness: n / 100 })} label="Ambient brightness" /></Row>
            </>
          )}
          {val.lightTab === 1 && (
            <>
              <Row label="Headlamps" sub={headlightsOn ? 'On' : 'Off'}><Switch on={headlightsOn} onClick={() => setHeadlights(!headlightsOn)} label="Headlamps" /></Row>
              <Row label="Smart low beam"><Switch on={on.smartLowBeam} onClick={() => toggle('smartLowBeam')} label="Smart low beam" /></Row>
              <Row label="Smart logo light"><Switch on={on.smartLogo} onClick={() => toggle('smartLogo')} label="Smart logo light" /></Row>
            </>
          )}
          {val.lightTab === 2 && (
            <>
              <Row label="Welcome light show" sub="Plays the lamps' sequence when the car is unlocked"><Switch on={on.welcome} onClick={() => toggle('welcome')} label="Welcome light show" /></Row>
              <Row label="Follow-me-home lights"><Switch on={on.followHome} onClick={() => toggle('followHome')} label="Follow-me-home lights" /></Row>
            </>
          )}
        </div>
      );
      break;
    case 'Doors & Locks':
      body = (
        <div className="grid grid-cols-2 gap-[10px]">
          <Row label="Lock" sub={locked ? 'Locked' : 'Unlocked'}><Switch on={locked} onClick={() => setLocked(!locked)} label="Lock" /></Row>
          <Row label="Auto lock when leaving"><Switch on={on.autoLock} onClick={() => toggle('autoLock')} label="Auto lock" /></Row>
          <Row label="Fold mirrors when locked"><Switch on={on.mirrorsFold} onClick={() => toggle('mirrorsFold')} label="Fold mirrors" /></Row>
          <Row label="Close windows in rain"><Switch on={on.rainClose} onClick={() => toggle('rainClose')} label="Close windows in rain" /></Row>
          {CLOSURES.map((c) => (
            <Row key={c.id} label={c.label}><Segment options={['Up', 'Down']} value={on['w' + c.id] ? 1 : 0} onPick={() => toggle('w' + c.id)} minW={60} /></Row>
          ))}
        </div>
      );
      break;
    case 'Sound & Display':
      body = (
        <div className="flex flex-col gap-[10px]">
          <Row label="Volume"><Slider value={media.volume} onChange={(n) => patchMedia({ volume: n })} label="Volume" /></Row>
          <Row label="Sound field"><Segment options={['Driver', 'Front', 'Rear', 'Whole car']} value={val.steering} onPick={(i) => setVal('steering', i)} minW={78} /></Row>
          <Row label="Screen brightness"><Slider value={val.brightness} min={30} onChange={(n) => setVal('brightness', n)} label="Screen brightness" /></Row>
          <Row label="Head-up display" sub="50 inch augmented-reality projection"><Switch on={on.hud} onClick={() => toggle('hud')} label="Head-up display" /></Row>
        </div>
      );
      break;
    case 'Energy':
      body = (
        <div className="flex flex-col gap-[10px]">
          <div className="flex items-end gap-6 rounded-[8px] px-6 py-5" style={{ background: DL.card }}>
            <span className="tnum text-[64px] font-light leading-none">{Math.round(soc * 100)}<span className="text-[26px]">%</span></span>
            <span className="pb-2 text-[18px]" style={{ color: DL.text2 }}>{range ? `${range.km} km` : '--'} · {variant.name}</span>
          </div>
          <Row label="Energy recovery"><Segment options={['Standard', 'Large']} value={val.regen} onPick={(i) => setVal('regen', i)} /></Row>
          <Row label="Charge limit" sub="Stop charging at"><Segment options={['80%', '90%', '100%']} value={2} onPick={() => notify('Charge limit (showroom demo)')} minW={70} /></Row>
        </div>
      );
      break;
    case 'Driving':
      body = (
        <div className="flex flex-col gap-[10px]">
          <div className="text-[15px]" style={{ color: DL.text2 }}>Drive mode</div>
          <Segment options={street.map((m) => m.label)} value={current} onPick={(i) => setCarMode(street[i].id, street[i].model)} minW={120} />
          {special.length > 0 && (
            <>
              <div className="mt-[6px] text-[15px]" style={{ color: DL.text2 }}>e³ manoeuvres</div>
              <div className="flex gap-[10px]">
                {special.map((m) => (
                  <Pill
                    key={m.id}
                    on={modeId === m.id}
                    onClick={() => {
                      setCarMode(m.id, m.model);
                      if (hasChassis) setHmiScreen('chassis');
                    }}
                    h={52}
                    grow
                  >
                    {m.label}
                  </Pill>
                ))}
              </div>
            </>
          )}
          <Row label="Steering feel"><Segment options={['Light', 'Standard', 'Heavy']} value={val.steering > 2 ? 1 : val.steering} onPick={(i) => setVal('steering', i)} minW={84} /></Row>
          <Row label="Auto hold" sub="Keeps the car still once it has stopped"><Switch on={on.autoHold} onClick={() => toggle('autoHold')} label="Auto hold" /></Row>
        </div>
      );
      break;
    case 'DiPilot':
      body = (
        <div className="flex flex-col gap-[10px]">
          {['Lane keeping assist', 'Adaptive cruise control', 'Automatic emergency braking', 'Blind-spot warning', 'Door-open warning'].map((s) => (
            <Row key={s} label={s}><Switch on={on['dp' + s]} onClick={() => toggle('dp' + s)} label={s} /></Row>
          ))}
        </div>
      );
      break;
    default:
      body = (
        <div className="flex flex-col gap-[10px]">
          <Row label="Model" sub={`${vehicle.brand} ${vehicle.model} ${vehicle.year}`}><span className="text-[15px]" style={{ color: DL.text2 }}>{variant.name}</span></Row>
          <Row label="Operating system"><span className="text-[15px]" style={{ color: DL.text2 }}>{vehicle.cockpit.os}</span></Row>
          <Row label="Software" sub="This is a showroom demonstration"><span className="text-[15px]" style={{ color: DL.text3 }}>Up to date</span></Row>
        </div>
      );
  }

  return (
    <div className="absolute inset-0">
      <Glow x="80%" y="55%" c="rgba(40,100,255,0.22)" />
      <div className="absolute flex flex-col" style={{ left: 22, top: 56, width: 190 }}>
        {MENU.map((p, i) => (
          <button
            key={p}
            type="button"
            onClick={() => setVal('setPage', i)}
            className="relative flex h-[50px] items-center rounded-[8px] px-[16px] text-left text-[16px] focus:outline-none"
            style={{ background: page === i ? 'linear-gradient(90deg, rgba(61,139,255,0.5), rgba(61,139,255,0.14))' : 'transparent', color: page === i ? DL.text : DL.text2 }}
          >
            {p}
          </button>
        ))}
      </div>
      <div className="absolute overflow-y-auto pr-2" style={{ left: 232, top: 56, width: 640, bottom: 18, scrollbarWidth: 'none' }}>
        {body}
      </div>
      {img && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={`/hmi/${vehicle.slug}/car34.webp`}
          alt=""
          aria-hidden
          draggable={false}
          onError={() => setImg(false)}
          className="pointer-events-none absolute select-none object-contain"
          style={{ right: 10, top: 130, width: 380, filter: 'brightness(1.1)' }}
        />
      )}
    </div>
  );
}

/* -------------------------------------------------------------------- media */

const STATIONS = [
  ['Happy FM', '106.2'], ['Xianfeng', '89.8'], ['Traffic', '105.2'], ['Music', '99.3'], ['City', '103.6'],
  ['Sports', '107.7'], ['Fly FM', '97.1'], ['Life', '94.2'], ['News', '91.4'], ['Economy', '97.4'],
];
const TRACKS = [
  { title: 'Neon Arterial', artist: 'Hong Kong Sunset', c: ['#6a5cff', '#ff7ab8'] },
  { title: 'Bund at 3AM', artist: 'Shanghai Tape Club', c: ['#1d3a8a', '#4dc3ff'] },
  { title: 'Gobi Transmission', artist: 'Silk Road Signal', c: ['#f08a3c', '#f4d35e'] },
  { title: 'Pearl River Delta', artist: 'Nanfang', c: ['#12a67a', '#a3e635'] },
];

export function MediaPage() {
  const { media, patchMedia } = useVehicleStore();
  const { val, setVal } = useDl();
  const track = TRACKS[media.trackIndex % TRACKS.length];
  const src = val.mediaSource;
  return (
    <div className="absolute inset-0">
      <Glow y="30%" />
      <div className="absolute flex gap-[28px] text-[18px]" style={{ left: 0, right: 0, top: 54, justifyContent: 'center' }}>
        {['Online radio', 'Music', 'Bluetooth'].map((s, i) => (
          <button key={s} type="button" onClick={() => setVal('mediaSource', i)} className="relative px-2 pb-2 focus:outline-none" style={{ color: src === i ? DL.text : DL.text3 }}>
            {s}
            {src === i && <span className="absolute inset-x-2 bottom-0 h-[2px] rounded-full" style={{ background: DL.accent }} />}
          </button>
        ))}
      </div>
      {src === 0 ? (
        <div className="absolute grid grid-cols-5 gap-[14px]" style={{ left: 40, right: 40, top: 120 }}>
          {STATIONS.map(([n, f], i) => (
            <button
              key={n}
              type="button"
              onClick={() => patchMedia({ trackIndex: i % 4, playing: true })}
              className="flex h-[150px] flex-col items-center justify-center gap-[10px] rounded-[10px] focus:outline-none"
              style={{ background: DL.card }}
            >
              <span className="flex h-[74px] w-[74px] items-center justify-center rounded-[14px] text-[22px] font-bold" style={{ background: `linear-gradient(140deg, hsl(${(i * 47) % 360} 70% 55%), hsl(${(i * 47 + 40) % 360} 70% 40%))` }}>
                FM
              </span>
              <span className="text-[15px]">{n}</span>
              <span className="tnum text-[12px]" style={{ color: DL.text3 }}>FM{f}</span>
            </button>
          ))}
        </div>
      ) : (
        <div className="absolute flex items-center gap-[40px]" style={{ left: 120, top: 150 }}>
          <div className="grid h-[300px] w-[300px] place-items-center rounded-[18px]" style={{ background: `linear-gradient(140deg, ${track.c[0]}, ${track.c[1]})`, boxShadow: '0 18px 40px rgba(0,0,0,0.5)' }}>
            <Ic.Music size={110} style={{ color: 'rgba(255,255,255,0.9)' }} />
          </div>
          <div style={{ width: 520 }}>
            <div className="text-[36px] font-light leading-tight">{track.title}</div>
            <div className="mt-2 text-[18px]" style={{ color: DL.text2 }}>{track.artist}</div>
            <div className="mt-[34px] flex items-center gap-[44px]">
              <button type="button" aria-label="Previous" onClick={() => patchMedia({ trackIndex: (media.trackIndex + 3) % 4 })} className="focus:outline-none"><Ic.Prev size={38} /></button>
              <button type="button" aria-label={media.playing ? 'Pause' : 'Play'} onClick={() => patchMedia({ playing: !media.playing })} className="grid h-[70px] w-[70px] place-items-center rounded-full focus:outline-none" style={{ background: DL.accent }}>
                {media.playing ? <Ic.Pause size={30} /> : <Ic.Play size={30} />}
              </button>
              <button type="button" aria-label="Next" onClick={() => patchMedia({ trackIndex: (media.trackIndex + 1) % 4 })} className="focus:outline-none"><Ic.Next size={38} /></button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* --------------------------------------------------------------- nav and camera */

export function NavPage() {
  const { notify } = useDl();
  return (
    <div className="absolute inset-0 overflow-hidden" style={{ background: '#e8eef3' }}>
      <svg viewBox="0 0 1280 700" preserveAspectRatio="xMidYMid slice" className="absolute inset-0 h-full w-full" aria-hidden>
        <rect width="1280" height="700" fill="#e8eef3" />
        <path d="M0 520C240 470 400 260 640 250S1040 120 1280 90V0H0Z" fill="#cfe5cc" opacity="0.8" />
        <path d="M900 700C980 600 1100 560 1280 550V700Z" fill="#c4dcef" />
        <path d="M-20 600C280 520 440 340 660 310S980 170 1300 120" fill="none" stroke="#fff" strokeWidth="26" />
        <path d="M-20 600C280 520 440 340 660 310S980 170 1300 120" fill="none" stroke="#38c46f" strokeWidth="7" strokeLinecap="round" />
        <path d="M180 0 430 700M780 0 700 700M1060 0 1180 700M0 300 1280 420" stroke="#fff" strokeWidth="14" opacity="0.9" />
        <circle cx="660" cy="310" r="14" fill="#2d7df6" stroke="#fff" strokeWidth="4" />
      </svg>
      <button
        type="button"
        onClick={() => notify('Search (showroom demo)')}
        className="absolute flex items-center gap-3 rounded-[10px] px-5 text-left text-[17px] focus:outline-none"
        style={{ left: 40, top: 60, height: 54, width: 420, background: 'rgba(255,255,255,0.95)', color: '#5b6577' }}
      >
        <Ic.Search size={20} /> Where to?
      </button>
    </div>
  );
}

export function CameraPage({ vehicle }: { vehicle: Vehicle }) {
  const [pair, setPair] = React.useState(0);
  const feeds = pair === 0 ? ['Front view', 'Rear view'] : ['Left view', 'Right view'];
  return (
    <div className="absolute inset-0">
      <div className="absolute grid place-items-center overflow-hidden rounded-[10px]" style={{ left: 22, top: 56, width: 400, bottom: 14, background: '#dfe6f1' }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={`/hmi/${vehicle.slug}/car-top.webp`}
          alt=""
          draggable={false}
          onError={(e) => {
            e.currentTarget.style.display = 'none';
          }}
          style={{ height: 460, width: 'auto', filter: 'brightness(1.25)' }}
        />
        <div className="absolute bottom-4 flex gap-2">
          <Pill on={pair === 0} onClick={() => setPair(0)} h={34}>Front / Rear</Pill>
          <Pill on={pair === 1} onClick={() => setPair(1)} h={34}>Left / Right</Pill>
        </div>
      </div>
      {feeds.map((f, k) => (
        <div key={f} className="absolute overflow-hidden rounded-[10px]" style={{ left: 440, right: 22, top: 56 + k * 322, height: 308, background: '#c8d1de' }}>
          <svg viewBox="0 0 800 308" width="100%" height="100%" preserveAspectRatio="none" aria-hidden>
            <path d="M0 308 230 128H570L800 308Z" fill="#aab4c6" />
            <path d="M0 150h800" stroke="rgba(0,0,0,0.12)" strokeWidth="2" />
            <path d="M280 308 330 190M520 308 470 190" stroke="#58c46e" strokeWidth="6" strokeLinecap="round" opacity="0.9" />
          </svg>
          <span className="absolute left-4 top-3 text-[15px]" style={{ color: '#34405a' }}>{f}</span>
        </div>
      ))}
    </div>
  );
}

/* ---------------------------------------------------------------- app centre */

const APPS: { id: string; label: string; c: [string, string] }[] = [
  { id: 'nav', label: 'Navigation', c: ['#3aa3ff', '#2b6be6'] },
  { id: 'music', label: 'Cloud Music', c: ['#ff5f4d', '#c8243d'] },
  { id: 'radio', label: 'Radio', c: ['#2dc9a6', '#1b8d85'] },
  { id: 'phone', label: 'Phone', c: ['#46d07c', '#1f9a52'] },
  { id: 'camera', label: '360 camera', c: ['#7a8cff', '#4655d8'] },
  { id: 'video', label: 'Video', c: ['#ffa940', '#e0701b'] },
  { id: 'kids', label: 'Kids', c: ['#ffd24d', '#f09a1a'] },
  { id: 'game', label: 'Games', c: ['#b06bff', '#6d33d6'] },
  { id: 'etc', label: 'Toll', c: ['#42c4e8', '#1d86b4'] },
  { id: 'weather', label: 'Weather', c: ['#5aaaff', '#2e6fd0'] },
  { id: 'chat', label: 'Messages', c: ['#4cd964', '#2da24a'] },
  { id: 'car', label: 'Vehicle check', c: ['#ff7a59', '#d0432b'] },
];

export function AppCentre() {
  const { notify } = useDl();
  const { setHmiScreen, setAppCentreOpen } = useVehicleStore();
  const run = (id: string) => {
    const to: Record<string, () => void> = {
      nav: () => setHmiScreen('nav'),
      music: () => setHmiScreen('media'),
      radio: () => setHmiScreen('media'),
      camera: () => setHmiScreen('camera'),
      car: () => setHmiScreen('controls'),
    };
    if (to[id]) {
      setAppCentreOpen(false);
      to[id]();
    } else notify('This app is not part of the showroom demo');
  };
  return (
    <div className="absolute inset-0">
      <Glow y="30%" />
      <div className="absolute text-center text-[18px]" style={{ left: 0, right: 0, top: 54, color: DL.text2 }}>App centre</div>
      <div className="absolute grid grid-cols-6 gap-x-[40px] gap-y-[34px]" style={{ left: 150, right: 150, top: 120 }}>
        {APPS.map((a) => (
          <button key={a.id} type="button" onClick={() => run(a.id)} className="flex flex-col items-center gap-[10px] focus:outline-none">
            <span className="block h-[84px] w-[84px] rounded-[20px]" style={{ background: `linear-gradient(145deg, ${a.c[0]}, ${a.c[1]})`, boxShadow: '0 8px 20px rgba(0,0,0,0.4)' }} />
            <span className="text-[14px]" style={{ color: DL.text2 }}>{a.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
