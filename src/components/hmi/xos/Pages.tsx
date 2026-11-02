'use client';

import React from 'react';
import type { Vehicle } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import type { LightMode } from '@/lib/lights';
import * as Ic from '../dilink/icons';
import { XO } from './theme';
import { useDate, useXo } from './shared';
import { MapPanel, Sheet, Split } from './Split';

/* ------------------------------------------------------------ shared pieces */

export function Switch({ on, onClick, label }: { on: boolean; onClick: () => void; label: string }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      aria-label={label}
      onClick={onClick}
      className="relative h-[28px] w-[52px] shrink-0 rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-black/30"
      style={{ background: on ? XO.green : 'rgba(26,28,38,0.22)' }}
    >
      <span className="absolute top-[3px] h-[22px] w-[22px] rounded-full bg-white shadow transition-all" style={{ left: on ? 27 : 3 }} />
    </button>
  );
}

export function Row({ label, sub, children }: { label: string; sub?: string; children?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-6 rounded-[12px] px-5 py-[7px]" style={{ minHeight: 58, background: XO.card }}>
      <div className="min-w-0">
        <div className="text-[17px] leading-tight">{label}</div>
        {sub && <div className="mt-[3px] text-[12px] leading-snug" style={{ color: XO.text3 }}>{sub}</div>}
      </div>
      {children}
    </div>
  );
}

export function Segment({ options, value, onPick, minW = 84 }: { options: string[]; value: number; onPick: (i: number) => void; minW?: number }) {
  return (
    <div className="flex overflow-hidden rounded-[10px]" style={{ background: 'rgba(26,28,38,0.08)' }}>
      {options.map((o, i) => (
        <button
          key={o}
          type="button"
          onClick={() => onPick(i)}
          className="h-[38px] px-3 text-[15px] focus:outline-none"
          style={{ background: value === i ? '#fff' : 'transparent', boxShadow: value === i ? '0 1px 4px rgba(0,0,0,0.14)' : undefined, borderRadius: 10, color: XO.text, minWidth: minW }}
        >
          {o}
        </button>
      ))}
    </div>
  );
}

export function Slider({ value, onChange, min = 0, max = 100, label, w = 240 }: { value: number; onChange: (n: number) => void; min?: number; max?: number; label: string; w?: number }) {
  return (
    <input type="range" min={min} max={max} value={value} aria-label={label} onChange={(e) => onChange(Number(e.target.value))} className="cursor-pointer" style={{ width: w, accentColor: XO.green }} />
  );
}

/* ------------------------------------------------------------------ the map */

/**
 * The home (c10_0020): the car panel at the left (a tall dark cloud with the car from above) and the map
 * in a panel of its own beside it, with the search card, the settings and charging keys and the mascot.
 */
export function MapHome({ vehicle }: { vehicle: Vehicle }) {
  return (
    <Split vehicle={vehicle}>
      <MapPanel />
    </Split>
  );
}

/* --------------------------------------------------------------- quick panel */

const TABS = ['Common', 'AC', 'Seats'];

/**
 * The quick panel (c10_0021-0025): a full sheet over the map with a close button, three tabs (Common,
 * AC, Seats) and an edit button. Common is a date card, four status cards, three indigo control cards
 * (personalise, headlamps, screen brightness) and two rows of tiles.
 */
export function QuickPanel({ vehicle, tab }: { vehicle: Vehicle; tab: number }) {
  const { setVal } = useXo();
  const { setHmiScreen } = useVehicleStore();
  return (
    <div className="absolute inset-0" style={{ background: 'linear-gradient(160deg, #eceaf3, #e3e1ee)' }}>
      <button type="button" aria-label="Close" onClick={() => setHmiScreen('nav')} className="absolute flex h-[40px] w-[40px] items-center justify-center rounded-[10px] focus:outline-none" style={{ left: 42, top: 66, background: 'rgba(26,28,38,0.08)' }}>
        <Ic.Close size={20} />
      </button>
      <div className="absolute flex gap-[44px] text-[20px]" style={{ left: 0, right: 0, top: 68, justifyContent: 'center' }}>
        {TABS.map((t, i) => (
          <button key={t} type="button" onClick={() => setVal('sheetTab', i)} className="relative px-2 pb-2 focus:outline-none" style={{ color: tab === i ? XO.text : XO.text3 }}>
            {t}
            {tab === i && <span className="absolute inset-x-1 bottom-0 h-[2px] rounded-full" style={{ background: XO.green }} />}
          </button>
        ))}
      </div>
      <button type="button" aria-label="Edit" className="absolute flex h-[40px] w-[40px] items-center justify-center rounded-[10px] focus:outline-none" style={{ right: 42, top: 66, background: 'rgba(26,28,38,0.08)' }}>
        <Ic.Doc size={19} />
      </button>
      {tab === 0 && <Common vehicle={vehicle} />}
      {tab === 1 && <AirCon vehicle={vehicle} />}
      {tab === 2 && <SeatsTab vehicle={vehicle} />}
    </div>
  );
}

function Mini({ x, label, state, tone, children }: { x: number; label: string; state: string; tone: string; children?: React.ReactNode }) {
  return (
    <div className="absolute overflow-hidden rounded-[14px] px-[16px] pt-[14px]" style={{ left: x, top: 148, width: 190, height: 112, background: tone, color: '#fff' }}>
      <div className="text-[16px]">{label}</div>
      <span className="mt-[40px] inline-block rounded-[7px] px-[8px] py-[3px] text-[12px]" style={{ background: 'rgba(255,255,255,0.22)' }}>{state}</span>
      {children}
    </div>
  );
}

function Common({ vehicle }: { vehicle: Vehicle }) {
  const { on, toggle, val, setVal, notify } = useXo();
  const d = useDate();
  const { locked, setLocked, lightMode, setLightMode, driveMode, modeId, setCarMode } = useVehicleStore();
  const modes = vehicle.cockpit.driveModes ?? [];
  const sel = modes.findIndex((m) => (modeId ? m.id === modeId : m.model === driveMode));
  const lamp: { id: number; label: string; mode: LightMode | null; icon: React.ReactNode }[] = [
    { id: 0, label: 'Off', mode: 'off', icon: <span className="text-[15px]">Off</span> },
    { id: 1, label: 'Position lamps', mode: 'position', icon: <Ic.Sun size={19} /> },
    { id: 2, label: 'Low beam', mode: 'low', icon: <Ic.Bulb size={19} /> },
    { id: 3, label: 'Auto', mode: 'auto', icon: <span className="text-[15px]">Auto</span> },
    { id: 4, label: 'Rear fog', mode: null, icon: <Ic.Bulb size={19} /> },
  ];
  const lampSel = lightMode === 'off' ? 0 : lightMode === 'position' ? 1 : lightMode === 'low' ? 2 : 3;
  const tiles = [
    { id: 'frunk', label: 'Front trunk', icon: <Ic.CarSide size={20} /> },
    { id: 'charge', label: 'Charge port cover', icon: <Ic.Bolt size={20} /> },
    { id: 'shade', label: 'Sunshade', icon: <Ic.Doc size={20} /> },
    { id: 'sentry', label: 'Sentry mode', icon: <Ic.Shield size={20} /> },
    { id: 'glove', label: 'Open glove box', icon: <Ic.Doc size={20} /> },
    { id: 'hud', label: 'HUD adjust', icon: <Ic.Doc size={20} /> },
    { id: 'mirror', label: 'Interior mirror', icon: <Ic.Doc size={20} /> },
    { id: 'wheel', label: 'Steering wheel', icon: <Ic.Wheel size={20} /> },
    { id: 'fridge', label: 'Fridge', icon: <Ic.Snow size={20} /> },
    { id: 'door', label: 'Power door', icon: <Ic.CarSide size={20} /> },
    { id: 'rse', label: 'Rear entertainment', icon: <Ic.Doc size={20} />, light: true },
    { id: 'rcs', label: 'Rear control screen', icon: <Ic.Doc size={20} />, light: true },
  ];
  return (
    <>
      <div className="absolute" style={{ left: 60, top: 150 }}>
        <div className="flex items-end gap-[14px]">
          <span className="text-[84px] font-light leading-none">{d.d}</span>
          <span className="pb-[6px] leading-tight"><span className="block text-[22px]">{d.m}</span><span className="block text-[14px]" style={{ color: XO.text2 }}>{d.w}</span></span>
        </div>
        <svg width="150" height="70" viewBox="0 0 150 70" className="absolute" style={{ left: 190, top: 6 }} aria-hidden>
          <circle cx="22" cy="12" r="12" fill="#f0a54a" /><path d="M0 70 55 18l35 30 25-20 35 42z" fill="#b6b9c8" /><path d="M55 18 40 70H80z" fill="#9ea3b8" />
        </svg>
      </div>
      <Mini x={372} label="Mirrors" state={on.mirrorsOut ? 'Unfolded' : 'Folded'} tone="linear-gradient(145deg,#4a4e66,#2f3248)"><button type="button" aria-label="Fold mirrors" onClick={() => toggle('mirrorsOut')} className="absolute inset-0 focus:outline-none" /></Mini>
      <Mini x={574} label="Door lock" state={locked ? 'Locked' : 'Unlocked'} tone="linear-gradient(145deg,#7a7fa8,#5b5f86)"><button type="button" aria-label="Lock" onClick={() => setLocked(!locked)} className="absolute inset-0 focus:outline-none" /></Mini>
      <Mini x={776} label="Boot" state={on.trunkClosed ? 'Closed' : 'Open'} tone="linear-gradient(145deg,#4f6a98,#34496e)"><button type="button" aria-label="Boot" onClick={() => toggle('trunkClosed')} className="absolute inset-0 focus:outline-none" /></Mini>
      <Mini x={978} label="Child lock" state="Off" tone="linear-gradient(145deg,#a98a78,#7f6354)"><button type="button" aria-label="Child lock" onClick={() => notify('Child lock (showroom demo)')} className="absolute inset-0 focus:outline-none" /></Mini>

      <div className="absolute rounded-[14px] px-[18px] pt-[14px]" style={{ left: 42, top: 276, width: 380, height: 108, background: `linear-gradient(145deg, ${XO.indigo}, ${XO.indigo2})`, color: '#fff' }}>
        <div className="text-[16px]">Personalise</div>
        <div className="mt-[10px] flex gap-[6px] rounded-[10px] p-[4px]" style={{ background: 'rgba(255,255,255,0.1)' }}>
          {[<Ic.Leaf key="e" size={22} />, <Ic.CarSide key="c" size={22} />, <Ic.Bolt key="s" size={22} />, <Ic.User key="u" size={22} />].map((icon, i) => {
            const m = [modes.find((q) => q.id === 'eco'), modes.find((q) => q.id === 'standard'), modes.find((q) => q.id === 'sport'), modes.find((q) => q.id === 'custom')][i];
            const on_ = m ? modes.indexOf(m) === sel : false;
            return (
              <button key={i} type="button" aria-label={m?.label ?? 'Mode'} aria-pressed={on_} onClick={() => m && setCarMode(m.id, m.model)} className="flex h-[44px] flex-1 items-center justify-center rounded-[8px] focus:outline-none" style={{ background: on_ ? 'rgba(160,140,255,0.55)' : 'transparent' }}>
                {icon}
              </button>
            );
          })}
        </div>
      </div>
      <div className="absolute rounded-[14px] px-[18px] pt-[14px]" style={{ left: 436, top: 276, width: 400, height: 108, background: 'linear-gradient(145deg,#12204a,#1e3a82)', color: '#fff' }}>
        <div className="text-[16px]">Headlamps</div>
        <div className="mt-[10px] flex gap-[6px] rounded-[10px] p-[4px]" style={{ background: 'rgba(255,255,255,0.1)' }}>
          {lamp.map((l) => (
            <button
              key={l.id}
              type="button"
              aria-label={l.label}
              aria-pressed={val.headlamp === l.id || (l.mode !== null && lampSel === l.id)}
              onClick={() => {
                setVal('headlamp', l.id);
                if (l.mode) setLightMode(l.mode);
                else notify('Rear fog lamp (showroom demo)');
              }}
              className="flex h-[44px] flex-1 items-center justify-center rounded-[8px] focus:outline-none"
              style={{ background: l.mode !== null && lampSel === l.id ? 'rgba(255,255,255,0.28)' : 'transparent' }}
            >
              {l.icon}
            </button>
          ))}
        </div>
      </div>
      <div className="absolute rounded-[14px] px-[18px] pt-[14px]" style={{ left: 850, top: 276, width: 388, height: 108, background: 'linear-gradient(145deg,#1a1a26,#2d2d3f)', color: '#fff' }}>
        <div className="text-[16px]">Screen brightness</div>
        <div className="mt-[16px] flex items-center gap-[14px]">
          <span className="flex h-[40px] w-[44px] items-center justify-center rounded-[8px]" style={{ background: 'rgba(255,255,255,0.14)' }}><Ic.Sun size={20} /></span>
          <input type="range" min={30} max={100} value={val.brightness} aria-label="Screen brightness" onChange={(e) => setVal('brightness', Number(e.target.value))} className="flex-1 cursor-pointer" style={{ accentColor: '#fff' }} />
          <span className="text-[15px]">Auto</span>
        </div>
      </div>

      <div className="absolute grid grid-cols-6 gap-[10px]" style={{ left: 42, right: 42, top: 400 }}>
        {tiles.map((t) => {
          const lit = t.id === 'sentry' ? on.sentry : t.id === 'hud' ? on.hud : t.id === 'rse' || t.id === 'rcs' ? true : false;
          return (
            <button
              key={t.id}
              type="button"
              aria-pressed={lit}
              onClick={() => {
                if (t.id === 'sentry') toggle('sentry');
                else if (t.id === 'hud') toggle('hud');
                else if (t.id === 'charge') notify('Charge port cover (showroom demo)');
                else notify(`${t.label} (showroom demo)`);
              }}
              className="flex h-[112px] flex-col justify-between rounded-[14px] px-[14px] py-[12px] text-left text-[15px] focus:outline-none focus-visible:ring-2 focus-visible:ring-black/30"
              style={{ background: (t as { light?: boolean }).light ? 'rgba(255,255,255,0.85)' : XO.tile }}
            >
              {t.label}
              <span style={{ color: XO.text2 }}>{t.icon}</span>
            </button>
          );
        })}
      </div>
    </>
  );
}

function AirCon({ vehicle }: { vehicle: Vehicle }) {
  const { on, toggle, val, setVal } = useXo();
  const { climate, patchClimate } = useVehicleStore();
  const [img, setImg] = React.useState(true);
  const nudge = (key: 'driverTempC' | 'passengerTempC', d: number) => {
    const next = Math.min(32, Math.max(16, Math.round((climate[key] + d) * 2) / 2));
    patchClimate(climate.sync ? { driverTempC: next, passengerTempC: next } : { [key]: next });
  };
  const mini = (label: string, node: React.ReactNode, pressed: boolean, onClick: () => void, w = 66) => (
    <button key={label} type="button" aria-label={label} aria-pressed={pressed} onClick={onClick} className="flex h-[52px] items-center justify-center rounded-[10px] focus:outline-none focus-visible:ring-2 focus-visible:ring-black/30" style={{ width: w, background: pressed ? '#fff' : 'rgba(26,28,38,0.07)', boxShadow: pressed ? '0 1px 5px rgba(0,0,0,0.14)' : undefined }}>
      {node}
    </button>
  );
  return (
    <>
      {img && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={`/hmi/${vehicle.slug}/cabin-climate-light.webp`} alt="" draggable={false} onError={() => setImg(false)} className="pointer-events-none absolute select-none" style={{ left: 180, top: 140, width: 920, height: 300, objectFit: 'contain', opacity: 0.95 }} />
      )}
      {!img && (
        <svg className="pointer-events-none absolute" style={{ left: 240, top: 150 }} width="800" height="270" viewBox="0 0 800 270" aria-hidden>
          <path d="M60 230C90 100 240 40 400 40S710 100 740 230" fill="none" stroke="rgba(120,130,170,0.5)" strokeWidth="2" />
          <rect x="230" y="110" width="340" height="120" rx="34" fill="rgba(150,160,200,0.22)" />
          <circle cx="310" cy="150" r="46" fill="none" stroke="rgba(100,110,150,0.7)" strokeWidth="7" />
        </svg>
      )}
      <div className="absolute flex flex-col gap-[8px]" style={{ left: 54, top: 160 }}>
        {mini('Front demist', <Ic.DefrostFront size={22} />, on.defrost, () => toggle('defrost'))}
        {mini('Rear demist', <Ic.DefrostRear size={22} />, on.defrostRear, () => toggle('defrostRear'))}
      </div>
      <div className="absolute flex items-center gap-[18px]" style={{ left: 150, top: 484 }}>
        <button type="button" aria-label="Lower driver temperature" onClick={() => nudge('driverTempC', -0.5)} className="focus:outline-none"><Ic.Chev dir="l" size={22} /></button>
        <span className="tnum text-[34px]" aria-live="polite">{climate.driverTempC.toFixed(1)}°</span>
        <button type="button" aria-label="Raise driver temperature" onClick={() => nudge('driverTempC', 0.5)} className="focus:outline-none"><Ic.Chev dir="r" size={22} /></button>
      </div>
      <div className="absolute flex items-center gap-[10px]" style={{ left: 480, top: 478 }}>
        {mini('A/C', <span className="text-[15px] font-semibold">A/C</span>, climate.acOn, () => patchClimate({ acOn: !climate.acOn }), 70)}
        <button type="button" aria-label="Power" aria-pressed={climate.acOn} onClick={() => patchClimate({ acOn: !climate.acOn })} className="flex h-[58px] w-[58px] items-center justify-center rounded-full focus:outline-none" style={{ background: climate.acOn ? XO.green : 'rgba(26,28,38,0.2)', color: '#fff' }}>
          <Ic.Power size={26} />
        </button>
        {mini('Sync', <span className="text-[14px]">Sync</span>, climate.sync, () => patchClimate({ sync: !climate.sync }), 70)}
      </div>
      <div className="absolute flex items-center gap-[18px]" style={{ right: 150, top: 484 }}>
        <button type="button" aria-label="Lower passenger temperature" onClick={() => nudge('passengerTempC', -0.5)} className="focus:outline-none"><Ic.Chev dir="l" size={22} /></button>
        <span className="tnum text-[34px]" aria-live="polite">{climate.passengerTempC.toFixed(1)}°</span>
        <button type="button" aria-label="Raise passenger temperature" onClick={() => nudge('passengerTempC', 0.5)} className="focus:outline-none"><Ic.Chev dir="r" size={22} /></button>
      </div>
      <div className="absolute flex items-center gap-[10px] rounded-[14px] px-[16px]" style={{ left: 42, right: 42, top: 560, height: 76, background: XO.card }}>
        {[<Ic.AirFace key="f" size={22} />, <Ic.AirFeet key="g" size={22} />, <Ic.DefrostFront key="d" size={22} />].map((n, i) => mini('Air ' + i, n, val.flow === i, () => setVal('flow', i), 62))}
        <span className="mx-[10px] h-[36px] w-px" style={{ background: XO.line }} />
        <Ic.Fan size={20} style={{ color: XO.text2 }} />
        <div className="flex w-[360px] gap-[6px]" role="group" aria-label="Fan speed">
          {[1, 2, 3, 4, 5, 6, 7].map((n) => (
            <button key={n} type="button" aria-label={`Fan speed ${n}`} onClick={() => { setVal('fan', n); patchClimate({ fanSpeed: Math.min(5, n), acOn: true }); }} className="relative h-[6px] flex-1 rounded-full focus:outline-none" style={{ background: n <= val.fan ? XO.text : 'rgba(26,28,38,0.2)' }}>
              <span className="absolute -inset-y-4 inset-x-0" />
            </button>
          ))}
        </div>
        <span className="tnum text-[20px]">{val.fan}</span>
        <span className="mx-[10px] h-[36px] w-px" style={{ background: XO.line }} />
        {mini('Recirculation', <Ic.Recirc size={22} />, on.recirc, () => toggle('recirc'))}
        {mini('Auto', <span className="text-[14px] font-semibold">AUTO</span>, val.auto === 1, () => setVal('auto', val.auto === 1 ? 0 : 1))}
      </div>
    </>
  );
}

const SEAT_MENU = ['Heat / vent', 'Massage', 'Position'];
// where each seat's back is in the picture (blender/scripts/cabin_hmi.py HMI_SEATS, the picture at 300, 120 and 800 x 470)
const SEATS = [
  { id: 'FL', label: 'Driver', x: 588, y: 437 },
  { id: 'FR', label: 'Passenger', x: 594, y: 270 },
  { id: 'RL', label: 'Rear left', x: 859, y: 439 },
  { id: 'RR', label: 'Rear right', x: 850, y: 268 },
] as const;

function SeatsTab({ vehicle }: { vehicle: Vehicle }) {
  const { val, setVal, on, toggle, notify } = useXo();
  const { climate, patchClimate } = useVehicleStore();
  const [img, setImg] = React.useState(true);
  const lvl = (id: string) => (id === 'FL' ? climate.seatHeatDriver : id === 'FR' ? climate.seatHeatPassenger : on['h' + id] ? 1 : 0);
  const press = (id: string) => {
    if (val.seatMenu === 2) return notify('Seat position (showroom demo)');
    if (id === 'FL') patchClimate({ seatHeatDriver: (climate.seatHeatDriver + 1) % 4 });
    else if (id === 'FR') patchClimate({ seatHeatPassenger: (climate.seatHeatPassenger + 1) % 4 });
    else toggle('h' + id);
  };
  return (
    <>
      <div className="absolute flex flex-col gap-[8px]" style={{ left: 54, top: 150 }}>
        {SEAT_MENU.map((t, i) => (
          <button key={t} type="button" onClick={() => setVal('seatMenu', i)} className="h-[44px] w-[148px] rounded-[10px] text-[15px] focus:outline-none" style={{ background: val.seatMenu === i ? '#fff' : 'rgba(26,28,38,0.07)', boxShadow: val.seatMenu === i ? '0 1px 5px rgba(0,0,0,0.14)' : undefined }}>
            {t}
          </button>
        ))}
      </div>
      {img && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={`/hmi/${vehicle.slug}/cabin-seats-light.webp`} alt="" draggable={false} onError={() => setImg(false)} className="pointer-events-none absolute select-none" style={{ left: 300, top: 120, width: 800, height: 470, objectFit: 'contain' }} />
      )}
      {SEATS.map((s) => (
        <button key={s.id} type="button" aria-label={`${s.label} seat`} aria-pressed={lvl(s.id) > 0} onClick={() => press(s.id)} className="absolute flex h-[58px] w-[58px] -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-black/40" style={{ left: s.x, top: s.y, background: lvl(s.id) > 0 ? XO.green : 'rgba(255,255,255,0.9)', color: lvl(s.id) > 0 ? '#fff' : XO.text, boxShadow: '0 2px 8px rgba(0,0,0,0.18)' }}>
          <Ic.SeatHeat size={24} />
          <span className="tnum text-[11px] leading-none">{lvl(s.id) > 0 ? lvl(s.id) : s.label.slice(0, 1)}</span>
        </button>
      ))}
      <div className="absolute flex flex-col gap-[8px]" style={{ left: 54, bottom: 110 }}>
        <button type="button" onClick={() => { patchClimate({ seatHeatDriver: 0, seatHeatPassenger: 0 }); notify('All off'); }} className="h-[42px] w-[148px] rounded-[10px] text-[15px] focus:outline-none" style={{ background: 'rgba(26,28,38,0.07)' }}>All off</button>
        <button type="button" onClick={() => { patchClimate({ seatHeatDriver: 3, seatHeatPassenger: 3 }); notify('All on'); }} className="h-[42px] w-[148px] rounded-[10px] text-[15px] focus:outline-none" style={{ background: 'rgba(26,28,38,0.07)' }}>All on</button>
      </div>
    </>
  );
}

/* ---------------------------------------------------------------- media, apps, camera */

const TRACKS = [
  { title: 'Anytime, anywhere', artist: 'Daily mix', c: ['#b9bfd6', '#8e94b4'] },
  { title: 'Neon Arterial', artist: 'Hong Kong Sunset', c: ['#6a5cff', '#ff7ab8'] },
  { title: 'Bund at 3AM', artist: 'Shanghai Tape Club', c: ['#1d3a8a', '#4dc3ff'] },
  { title: 'Gobi Transmission', artist: 'Silk Road Signal', c: ['#f08a3c', '#f4d35e'] },
];

export function MediaPage() {
  const { media, patchMedia } = useVehicleStore();
  const track = TRACKS[media.trackIndex % TRACKS.length];
  return (
    <div className="absolute inset-0" style={{ background: 'linear-gradient(160deg, #eceaf3, #e3e1ee)' }}>
      <div className="absolute flex items-center gap-[48px]" style={{ left: 150, top: 150 }}>
        <div className="grid h-[320px] w-[320px] place-items-center rounded-[22px]" style={{ background: `linear-gradient(140deg, ${track.c[0]}, ${track.c[1]})`, boxShadow: '0 20px 44px rgba(40,40,80,0.28)' }}>
          <Ic.Music size={110} style={{ color: 'rgba(255,255,255,0.9)' }} />
        </div>
        <div style={{ width: 520 }}>
          <div className="text-[36px] font-light leading-tight">{track.title}</div>
          <div className="mt-2 text-[18px]" style={{ color: XO.text2 }}>{track.artist}</div>
          <div className="mt-[40px] flex items-center gap-[44px]">
            <button type="button" aria-label="Previous" onClick={() => patchMedia({ trackIndex: (media.trackIndex + 3) % 4 })} className="focus:outline-none"><Ic.Prev size={38} /></button>
            <button type="button" aria-label={media.playing ? 'Pause' : 'Play'} onClick={() => patchMedia({ playing: !media.playing })} className="grid h-[72px] w-[72px] place-items-center rounded-full focus:outline-none" style={{ background: XO.text, color: '#fff' }}>
              {media.playing ? <Ic.Pause size={30} /> : <Ic.Play size={30} />}
            </button>
            <button type="button" aria-label="Next" onClick={() => patchMedia({ trackIndex: (media.trackIndex + 1) % 4 })} className="focus:outline-none"><Ic.Next size={38} /></button>
          </div>
        </div>
      </div>
    </div>
  );
}

const APPS: { id: string; label: string; c: [string, string] }[] = [
  { id: 'nav', label: 'Navigation', c: ['#4aa8ff', '#2b6be6'] },
  { id: 'music', label: 'Music', c: ['#ff6a5a', '#c8243d'] },
  { id: 'cam', label: '360 camera', c: ['#7a8cff', '#4655d8'] },
  { id: 'video', label: 'Video', c: ['#ffa940', '#e0701b'] },
  { id: 'game', label: 'Games', c: ['#b06bff', '#6d33d6'] },
  { id: 'kids', label: 'Kids', c: ['#ffd24d', '#f09a1a'] },
  { id: 'phone', label: 'Phone', c: ['#46d07c', '#1f9a52'] },
  { id: 'weather', label: 'Weather', c: ['#5aaaff', '#2e6fd0'] },
  { id: 'chat', label: 'Messages', c: ['#4cd964', '#2da24a'] },
  { id: 'car', label: 'Vehicle', c: ['#8a8fb0', '#5b5f86'] },
  { id: 'ev', label: 'Charging', c: ['#2dc9a6', '#1b8d85'] },
  { id: 'set', label: 'Settings', c: ['#9aa0b4', '#6c7388'] },
];

export function AppCentre({ vehicle }: { vehicle: Vehicle }) {
  const { notify } = useXo();
  const { setHmiScreen, setAppCentreOpen, openSettings } = useVehicleStore();
  const run = (id: string) => {
    const to: Record<string, () => void> = {
      nav: () => setHmiScreen('nav'),
      music: () => setHmiScreen('media'),
      cam: () => setHmiScreen('camera'),
      car: () => openSettings('vehicle'),
      set: () => openSettings('vehicle'),
      ev: () => openSettings('charging'),
    };
    if (to[id]) {
      setAppCentreOpen(false);
      to[id]();
    } else notify('This app is not part of the showroom demo');
  };
  return (
    <Split vehicle={vehicle}>
      <Sheet>
        <div className="absolute inset-x-0 top-[22px] text-center text-[17px]">App centre</div>
        <div className="absolute grid grid-cols-5 gap-x-[26px] gap-y-[30px]" style={{ left: 54, right: 54, top: 86 }}>
          {APPS.map((a) => (
            <button key={a.id} type="button" onClick={() => run(a.id)} className="flex flex-col items-center gap-[9px] focus:outline-none">
              <span className="block h-[72px] w-[72px] rounded-[20px]" style={{ background: `linear-gradient(145deg, ${a.c[0]}, ${a.c[1]})`, boxShadow: '0 6px 14px rgba(40,40,80,0.2)' }} />
              <span className="text-[13px]" style={{ color: XO.text2 }}>{a.label}</span>
            </button>
          ))}
        </div>
      </Sheet>
    </Split>
  );
}

export function CameraPage({ vehicle }: { vehicle: Vehicle }) {
  const [pair, setPair] = React.useState(0);
  const feeds = pair === 0 ? ['Front view', 'Rear view'] : ['Left view', 'Right view'];
  return (
    <div className="absolute inset-0" style={{ background: 'linear-gradient(160deg, #eceaf3, #e3e1ee)' }}>
      <div className="absolute grid place-items-center overflow-hidden rounded-[16px]" style={{ left: 42, top: 60, width: 380, bottom: 84, background: 'radial-gradient(70% 55% at 50% 50%, #6a7490, #8c95ad 55%, #a9b0c5)' }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={`/hmi/${vehicle.slug}/car-top.webp`} alt="" draggable={false} onError={(e) => { e.currentTarget.style.display = 'none'; }} style={{ height: 470, width: 'auto', filter: 'brightness(0.95)' }} />
        <div className="absolute bottom-4 flex gap-2">
          {['Front / Rear', 'Left / Right'].map((l, i) => (
            <button key={l} type="button" onClick={() => setPair(i)} className="h-[34px] rounded-[9px] px-3 text-[13px] focus:outline-none" style={{ background: pair === i ? '#fff' : 'rgba(255,255,255,0.45)' }}>{l}</button>
          ))}
        </div>
      </div>
      {feeds.map((f, k) => (
        <div key={f} className="absolute overflow-hidden rounded-[16px]" style={{ left: 442, right: 42, top: 60 + k * 322, height: 308, background: '#c8d1de' }}>
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
