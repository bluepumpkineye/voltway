'use client';

import React from 'react';
import { useVehicleStore } from '@/store/vehicle-store';
import * as Ha from '../harmonyos/icons';
import { useHaLocal } from '../harmonyos/shared';
import * as Ic from './icons';
import { useBy, BAR_H, STATUS_H } from './theme';
import { CarImage, SideMenu } from './ui';

/* --------------------------------------------------------------------- climate */

const AC_MENU = [
  { id: 'ac', label: 'Air conditioning', icon: <Ic.Hex size={20} /> },
  { id: 'heat', label: 'Ventilation & heating', icon: <Ic.SeatHeat size={20} /> },
  { id: 'clean', label: 'Clean air', icon: <Ic.Hotspot size={20} /> },
  { id: 'set', label: 'Settings', icon: <Ic.Hex size={20} /> },
];

const tempText = (v: number) => (v <= 16 ? 'Lo' : v >= 32 ? 'Hi' : String(Math.round(v)));

/**
 * The air-conditioning page (s_0024, s_0092): the climate menu down the left, a row of switches across the
 * top (power, auto, A/C, max, front and rear demister, mode, ventilation), the driver's temperature and the
 * passenger's either side of a seat with the airflow drawn over it, the negative-ion button with the
 * airflow's direction, the split-zone key and the fan across the foot. Tap the red or blue triangle to step
 * a temperature by half a degree.
 */
export function ClimatePage() {
  const t = useBy();
  const dark = t.tone === 'dark';
  const { climate, patchClimate } = useVehicleStore();
  const { on, toggle, val, setVal } = useHaLocal();
  const [menu, setMenu] = React.useState('ac');
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

  const chip = (x: number, label: string, active: boolean, fn: () => void, w = 92) => (
    <button
      key={label}
      type="button"
      aria-pressed={active}
      onClick={fn}
      className="absolute flex h-[50px] -translate-x-1/2 items-center justify-center rounded-full text-[16px] outline-none focus-visible:ring-2 focus-visible:ring-white/60"
      style={{ left: x, top: 150, width: w, background: active ? (dark ? '#d9e1ea' : '#1f7bea') : t.seg, color: active ? (dark ? '#0a1018' : '#fff') : t.text }}
    >
      {label}
    </button>
  );

  const dial = (key: 'driverTempC' | 'passengerTempC', x: number) => {
    const v = climate[key];
    return (
      <div className="absolute flex flex-col items-center" style={{ left: x - 70, top: 236, width: 140 }}>
        <button type="button" aria-label={`Raise ${key === 'driverTempC' ? 'driver' : 'passenger'} temperature`} onClick={() => setSide(key, v + 0.5)} className="pb-[8px] outline-none" style={{ color: '#ef4a3d' }}>
          <svg width="22" height="14" viewBox="0 0 22 14" aria-hidden><path d="M11 1l10 12H1z" fill="currentColor" /></svg>
        </button>
        <span className="tnum text-[24px] opacity-60">{tempText(Math.min(32, v + 1))}</span>
        <span className="tnum my-[6px] text-[44px] font-light leading-none" aria-live="polite">
          {tempText(v)}
          {tempText(v).length <= 2 && v > 16 && v < 32 && <span className="ml-[2px] text-[16px] opacity-70">°c</span>}
        </span>
        <span className="tnum text-[24px] opacity-60">{tempText(Math.max(16, v - 1))}</span>
        <button type="button" aria-label={`Lower ${key === 'driverTempC' ? 'driver' : 'passenger'} temperature`} onClick={() => setSide(key, v - 0.5)} className="pt-[8px] outline-none" style={{ color: '#3b9dff' }}>
          <svg width="22" height="14" viewBox="0 0 22 14" aria-hidden><path d="M11 13L1 1h20z" fill="currentColor" /></svg>
        </button>
      </div>
    );
  };

  const flow = ['Face', 'Feet', 'Face and feet', 'Windscreen'];
  return (
    <div className="absolute inset-0" style={{ background: t.bg, color: t.text }}>
      <SideMenu items={AC_MENU} value={menu} onChange={setMenu} search={false} style={{ left: 26, top: STATUS_H + 28, width: 218 }} />

      {chip(356, 'Fan', !on.climateOff, () => toggle('climateOff'), 84)}
      {chip(463, 'Auto', !!on.climateAuto, () => toggle('climateAuto'))}
      {chip(575, 'A/C', climate.acOn, () => patchClimate({ acOn: !climate.acOn }))}
      {chip(691, 'Max', !!on.coolMax, () => toggle('coolMax'))}
      {chip(804, 'Front', !!on.defrost, () => toggle('defrost'))}
      {chip(913, 'Rear', !!on.defrostRear, () => toggle('defrostRear'))}
      {chip(1023, 'Recirc', !!on.recirc, () => toggle('recirc'))}
      {chip(1135, 'Vent', !!on.ventAuto, () => toggle('ventAuto'))}

      {dial('driverTempC', 330)}
      {dial('passengerTempC', 1170)}

      {/* the seat, with the air drawn over it */}
      <svg className="absolute" style={{ left: 560, top: 230, width: 520, height: 280 }} viewBox="0 0 520 280" aria-hidden>
        <defs>
          <linearGradient id="byAir" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor={dark ? '#7fd6e8' : '#4fb4ef'} stopOpacity="0" />
            <stop offset="0.5" stopColor={dark ? '#a8e6f3' : '#3a9fe6'} stopOpacity="0.9" />
            <stop offset="1" stopColor={dark ? '#7fd6e8' : '#4fb4ef'} stopOpacity="0.2" />
          </linearGradient>
        </defs>
        <path d="M312 40c26-14 44 6 34 26l-26 56 14 78h90a20 20 0 0 1 20 20v14H200" fill="none" stroke={dark ? '#c7d3de' : '#9db7d3'} strokeWidth="16" strokeLinecap="round" strokeLinejoin="round" opacity="0.8" />
        {[0, 1, 2].map((i) => (
          <path key={i} d={`M20 ${110 + i * 26}c70 ${-22 + i * 6} 140 ${-6 + i * 8} 210 ${-30 + i * 14}`} fill="none" stroke="url(#byAir)" strokeWidth={4 - i} strokeLinecap="round" opacity={climate.fanSpeed / 5 * 0.8 + 0.2} />
        ))}
      </svg>
      <button type="button" aria-pressed={!!on.ions} aria-label="Negative ions" onClick={() => toggle('ions')} className="absolute flex h-[64px] w-[64px] items-center justify-center rounded-full text-[12px] outline-none" style={{ left: 458, top: 370, background: on.ions ? '#37c47a' : dark ? 'rgba(130,150,170,0.45)' : 'rgba(31,123,234,0.25)', color: on.ions ? '#fff' : t.text }}>
        Ions
      </button>
      <div className="absolute flex flex-col items-center gap-[4px]" style={{ left: 490, top: 322 }} aria-hidden><Ha.Chev dir="d" size={14} /></div>
      <div className="absolute flex items-center" style={{ left: 534, top: 390 }}>
        {flow.map((f, i) => (
          <button key={f} type="button" aria-label={f} aria-pressed={val.airFlow === i} onClick={() => setVal('airFlow', i)} className="mx-[3px] h-[28px] w-[28px] rounded-full text-[0px] outline-none" style={{ background: val.airFlow === i ? t.accent : t.seg }}>{f}</button>
        ))}
      </div>

      <button type="button" aria-pressed={!climate.sync} onClick={() => patchClimate({ sync: !climate.sync })} className="absolute h-[44px] rounded-full px-[26px] text-[16px] outline-none" style={{ left: 290, top: 620, background: !climate.sync ? t.accent : t.seg, color: !climate.sync ? '#fff' : t.text }}>
        Split zones
      </button>
      <div className="absolute flex items-center gap-[18px]" style={{ left: 496, top: 628, width: 490 }}>
        <Ic.FanAc size={20} style={{ opacity: 0.7 }} />
        <div
          ref={track}
          className="relative h-[28px] flex-1 cursor-ew-resize touch-none rounded-full"
          style={{ background: t.seg }}
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
          <span className="absolute inset-y-[2px] left-[2px] rounded-full" style={{ width: `calc(${(fan / 5) * 100}% - 4px)`, minWidth: 24, background: dark ? '#e8eef4' : '#1f7bea' }} />
        </div>
        <Ic.FanAc size={34} />
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------- vehicle */

/**
 * The vehicle page (s_0027): the car on a dusk-lake ground with its doors, boot, windows, mirrors, seat and
 * ambient-light tiles down the left, and the trip and consumption under them. The tiles that have a
 * counterpart in the 3D car (the lock, the boot, the ambient light) write the shared store.
 */
export function VehiclePage() {
  const { notify, on, toggle } = useHaLocal();
  const { locked, setLocked, openings, toggleOpening, ambientOn, setAmbient, climate, patchClimate } = useVehicleStore();
  const tile = (col: number, row: number, label: string, sub: string | undefined, icon: React.ReactNode, active: boolean, fn: () => void) => (
    <button
      key={label}
      type="button"
      aria-pressed={active}
      onClick={fn}
      className="absolute flex flex-col items-center justify-center gap-[7px] rounded-[16px] text-[13px] leading-tight outline-none focus-visible:ring-2 focus-visible:ring-white"
      style={{ left: 40 + col * 118, top: 120 + row * 118, width: 106, height: 106, background: active ? 'rgba(255,255,255,0.92)' : 'rgba(20,34,56,0.55)', color: active ? '#0d1a2c' : '#fff', backdropFilter: 'blur(12px)' }}
    >
      {icon}
      <span className="px-1 text-center">{label}</span>
      {sub && <span className="-mt-[4px] text-[11px] opacity-75">{sub}</span>}
    </button>
  );
  return (
    <div className="absolute inset-0 overflow-hidden text-white" style={{ background: 'linear-gradient(180deg,#26425f 0%,#42647f 38%,#5f7f94 56%,#243b52 57%,#0f1d2e 100%)' }}>
      <svg className="absolute inset-0" viewBox="0 0 1280 800" preserveAspectRatio="none" width="1280" height="800" aria-hidden>
        <path d="M0 330l120-60 90 40 130-90 110 70 100-50 150 80 140-60 120 60 140-50 170 70v70H0z" fill="#3a566f" opacity="0.7" />
        <path d="M0 400l200-40 160 30 240-30 200 40 220-30 260 30v40H0z" fill="#1c3047" opacity="0.8" />
      </svg>
      <span className="absolute rounded-full px-[22px] py-[8px] text-[15px]" style={{ left: 640, top: 90, transform: 'translateX(-50%)', background: 'rgba(20,34,56,0.55)' }}>Interior panorama</span>
      <CarImage w={640} left={500} top={230} />

      {tile(0, 0, 'Doors', locked ? 'Locked' : 'Unlocked', locked ? <Ic.Lock size={26} /> : <Ic.Unlock size={26} />, !locked, () => setLocked(!locked))}
      {tile(1, 0, 'Boot', openings.boot ? 'Open' : 'Closed', <Ic.Trunk size={26} />, openings.boot, () => toggleOpening('boot'))}
      {tile(2, 0, 'Open all windows', undefined, <Ic.Windows4 size={26} />, !!on.windows, () => toggle('windows'))}
      {tile(0, 1, 'Close all windows', undefined, <Ic.Windows4 size={26} />, false, () => notify('All windows closed'))}
      {tile(1, 1, 'Mirrors', on.mirrorFold ? 'Folded' : 'Unfolded', <Ic.CarSide size={26} />, !!on.mirrorFold, () => toggle('mirrorFold'))}
      {tile(2, 1, 'Seat adjust', undefined, <Ic.SeatSilhouette size={26} />, false, () => notify('Seat adjustment is not part of the showroom demo'))}
      {tile(0, 2, 'Ambient light', ambientOn ? 'On' : 'Off', <Ic.Bulb size={26} />, ambientOn, () => setAmbient({ ambientOn: !ambientOn }))}
      {tile(1, 2, 'Seat ventilation', undefined, <Ic.SeatHeat size={26} />, climate.seatHeatDriver > 0, () => patchClimate({ seatHeatDriver: climate.seatHeatDriver > 0 ? 0 : 2 }))}
      {tile(2, 2, 'More', undefined, <Ic.Dots size={26} />, false, () => notify('More controls are in Settings, Vehicle settings'))}

      <div className="absolute flex gap-[12px]" style={{ left: 40, top: 480 }}>
        {[['0.0 km', 'Trip'], ['4.9 kWh', 'Consumption']].map(([a, b]) => (
          <div key={b} className="rounded-[14px] px-[22px] py-[14px]" style={{ background: 'rgba(20,34,56,0.55)', minWidth: 170 }}>
            <div className="tnum text-[20px]">{a}</div>
            <div className="text-[12px] opacity-70">{b}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ----------------------------------------------------------------------- phone */

const CONTACTS: [string, string][] = [['A', 'Alex Wen'], ['B', 'Home'], ['B', 'BYD service'], ['C', 'Cai Chunguang'], ['C', 'Cai Jiahua'], ['D', 'Dad']];

/**
 * The phone (s_0026): Contacts, Recent calls and Missed calls down the left, the address book with its
 * alphabet beside it and a dial pad with the green call key; the phone's name sits at the foot.
 */
export function PhonePage() {
  const t = useBy();
  const [menu, setMenu] = React.useState('contacts');
  const [num, setNum] = React.useState('');
  const { notify } = useHaLocal();
  const keys = [['1', ''], ['2', 'ABC'], ['3', 'DEF'], ['4', 'GHI'], ['5', 'JKL'], ['6', 'MNO'], ['7', 'PQRS'], ['8', 'TUV'], ['9', 'WXYZ'], ['*', ''], ['0', '+'], ['#', '']];
  return (
    <div className="absolute inset-0" style={{ background: t.bg, color: t.text }}>
      <SideMenu
        items={[{ id: 'contacts', label: 'Contacts', icon: <Ic.MenuDilink size={20} /> }, { id: 'recent', label: 'Recent calls', icon: <Ic.Clock size={20} /> }, { id: 'missed', label: 'Missed calls', icon: <Ic.MissedCall size={20} /> }]}
        value={menu}
        onChange={setMenu}
        search={false}
        style={{ left: 26, top: STATUS_H + 28, width: 218 }}
      />
      <div className="absolute flex items-center gap-[10px] text-[15px]" style={{ left: 34, bottom: BAR_H + 16, color: t.text2 }}><Ha.Bluetooth size={16} /> Alex’s iPhone</div>
      <div className="absolute" style={{ left: 330, top: STATUS_H + 28, width: 480, bottom: BAR_H + 10 }}>
        <div className="mb-[10px] flex justify-between text-[14px]" style={{ color: t.text2 }}><span>621 contacts</span><span>Refresh</span></div>
        {CONTACTS.map(([l, n], i) => (
          <div key={n}>
            {(i === 0 || CONTACTS[i - 1][0] !== l) && <div className="mt-[8px] text-[13px]" style={{ color: t.text3 }}>{l}</div>}
            <button type="button" onClick={() => setNum(n)} className="flex w-full items-center gap-[14px] py-[10px] text-left text-[18px] outline-none">
              <span className="flex h-[34px] w-[34px] items-center justify-center rounded-full text-[14px] text-white" style={{ background: ['#c9a24a', '#c45a64', '#4a7ac9', '#4ab07a', '#7a5ac9', '#c9774a'][i % 6] }}>{n[0]}</span>
              {n}
            </button>
          </div>
        ))}
      </div>
      <div className="absolute grid grid-cols-3 gap-[14px]" style={{ left: 884, top: STATUS_H + 70, width: 330 }}>
        <div className="col-span-3 mb-[6px] h-[40px] text-center text-[26px] tracking-widest">{num}</div>
        {keys.map(([k, sub]) => (
          <button key={k} type="button" onClick={() => setNum((n) => (n.length < 14 && /\d|\*|#/.test(k) ? n + k : n))} className="flex h-[64px] flex-col items-center justify-center rounded-[14px] outline-none" style={{ background: t.card }}>
            <span className="text-[26px] leading-none">{k}</span>
            <span className="text-[10px] leading-none opacity-55">{sub}</span>
          </button>
        ))}
        <button type="button" onClick={() => notify('Calls are not part of the showroom demo')} className="col-span-3 mt-[6px] flex h-[58px] items-center justify-center rounded-full text-white outline-none" style={{ background: '#37c47a' }}>
          <Ic.PhoneHandset size={26} />
        </button>
      </div>
    </div>
  );
}

/* ----------------------------------------------------------------------- music */

const SOURCES = ['Cool Music', 'Ximalaya', 'Online radio', 'Bluetooth music', 'Local media', 'K songs'];
const TRACKS = ['Night Drive · Long Exposure', 'Dust & Voltage · Cold Harbour', 'Neon Arterial · Hong Kong Sunset', 'Cold Harbour · The Estate Cars'];

/**
 * The music app (s_0095): the sources down the left, the tabs across the top, the album on the stage and the
 * player along the foot with the shared media state's play and track. Bluetooth music is the source the
 * status bar names.
 */
export function MediaPage() {
  const t = useBy();
  const { media, patchMedia } = useVehicleStore();
  const { val, setVal } = useHaLocal();
  const src = val.musicSrc || 3;
  const title = TRACKS[media.trackIndex % TRACKS.length];
  const next = (d: number) => patchMedia({ trackIndex: (media.trackIndex + d + TRACKS.length) % TRACKS.length });
  return (
    <div className="absolute inset-0" style={{ background: t.bg, color: t.text }}>
      <nav className="absolute flex flex-col gap-[6px]" style={{ left: 26, top: STATUS_H + 22, width: 260 }} aria-label="Sources">
        {SOURCES.map((s, i) => (
          <button key={s} type="button" aria-current={i === src} onClick={() => setVal('musicSrc', i)} className="flex h-[50px] items-center gap-[14px] rounded-full px-[20px] text-left text-[17px] outline-none" style={{ background: i === src ? t.pill : 'transparent', color: i === src ? t.pillText : t.text }}>
            <Ic.Note size={20} /> {s}
          </button>
        ))}
      </nav>
      <div className="absolute flex items-center justify-center" style={{ left: 330, right: 40, top: STATUS_H + 8, bottom: BAR_H + 110 }}>
        <div className="flex items-center gap-[56px]">
          <span className="block h-[270px] w-[270px] rounded-[18px]" style={{ background: 'linear-gradient(140deg,#2a3a66,#7a5a9c 55%,#d98a6a)', boxShadow: '0 18px 50px rgba(0,0,0,0.4)' }} />
          <div>
            <div className="text-[30px]">{title.split(' · ')[0]}</div>
            <div className="mt-[8px] text-[18px]" style={{ color: t.text2 }}>{title.split(' · ')[1]}</div>
            <div className="mt-[28px] h-[6px] w-[360px] rounded-full" style={{ background: t.seg }}><span className="block h-full w-[38%] rounded-full" style={{ background: t.accent }} /></div>
            <div className="mt-[6px] flex w-[360px] justify-between text-[13px]" style={{ color: t.text3 }}><span>01:24</span><span>03:41</span></div>
          </div>
        </div>
      </div>
      <div className="absolute inset-x-[40px] flex items-center justify-center gap-[64px] rounded-full" style={{ bottom: BAR_H + 18, height: 80, background: t.card }}>
        <button type="button" aria-label="Previous" onClick={() => next(-1)} className="outline-none"><Ha.Prev size={30} /></button>
        <button type="button" aria-label={media.playing ? 'Pause' : 'Play'} onClick={() => patchMedia({ playing: !media.playing })} className="flex h-[58px] w-[58px] items-center justify-center rounded-full outline-none" style={{ background: t.segOn, color: t.segOnText }}>{media.playing ? <Ha.Pause size={30} /> : <Ha.Play size={30} />}</button>
        <button type="button" aria-label="Next" onClick={() => next(1)} className="outline-none"><Ha.Next size={30} /></button>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------------- camera */

/**
 * The 360 camera (s_0039): a column of keys down the left (the parking mode, settings, 3D, parking assist,
 * the radar and the cameras' own), the car from above with its blind spots at the left and the chosen
 * camera's view at the right.
 */
export function CameraPage() {
  const t = useBy();
  const { slug } = useHaLocal();
  const [view, setView] = React.useState(0);
  const keys = [<Ic.Hex key="s" size={22} />, <Ic.Windows4 key="3" size={22} />, <Ic.CarSide key="p" size={24} />, <Ic.Pin key="r" size={22} />, <Ic.Clock key="c" size={22} />];
  const views = ['Front', 'Rear', 'Left', 'Right'];
  return (
    <div className="absolute inset-0 text-white" style={{ background: '#0a0f15', paddingBottom: BAR_H }}>
      <div className="absolute flex flex-col items-center gap-[18px] rounded-[16px] py-[18px]" style={{ left: 24, top: 40, width: 66, background: 'rgba(255,255,255,0.08)' }}>
        <span className="text-[16px] font-semibold">P⊖</span>
        {keys.map((k, i) => (
          <button key={i} type="button" aria-label={`Camera key ${i + 1}`} onClick={() => setView(i % 4)} className="flex h-[48px] w-[48px] items-center justify-center rounded-[12px] outline-none" style={{ background: i === 2 ? t.accent : 'transparent', color: i === 2 ? '#04130d' : '#fff' }}>{k}</button>
        ))}
      </div>
      <div className="absolute overflow-hidden rounded-[10px]" style={{ left: 108, top: 40, width: 420, bottom: BAR_H + 22, background: 'linear-gradient(180deg,#3a3f46,#20252b)' }}>
        <svg className="absolute inset-0" viewBox="0 0 420 640" preserveAspectRatio="none" aria-hidden>
          <path d="M0 520L90 0H330L420 520" fill="#4b5058" opacity="0.5" />
          <path d="M150 640L180 0M270 640L240 0" stroke="#6b717a" strokeWidth="3" opacity="0.7" fill="none" />
        </svg>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={`/hmi/${slug}/car-top.webp`} alt="" draggable={false} className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2" style={{ height: 470 }} />
        <span className="absolute h-[8px] w-[110px] rounded-full" style={{ left: 154, top: 150, background: '#ef4a3d' }} />
      </div>
      <div className="absolute overflow-hidden rounded-[10px]" style={{ left: 544, top: 40, right: 24, bottom: BAR_H + 22, background: 'linear-gradient(180deg,#9bb4c8 0%,#c9d3da 40%,#7c8085 41%,#4a4e54 100%)' }}>
        <svg className="absolute inset-0" viewBox="0 0 700 640" preserveAspectRatio="none" aria-hidden>
          <path d="M120 640L330 262M580 640L370 262" stroke="#e6e9ec" strokeWidth="6" opacity="0.8" />
          <path d="M260 640L338 262M440 640L362 262" stroke="#e6e9ec" strokeWidth="3" opacity="0.5" strokeDasharray="22 18" />
          <path d="M0 262h700V160L560 110 420 90H280L140 110 0 160z" fill="#6c8aa3" opacity="0.5" />
        </svg>
        <span className="absolute left-[18px] top-[14px] text-[13px] opacity-80">{views[view]}</span>
        <span className="absolute bottom-[12px] left-1/2 -translate-x-1/2 text-[12px] opacity-70">Double-tap to switch to the wide view</span>
      </div>
    </div>
  );
}
