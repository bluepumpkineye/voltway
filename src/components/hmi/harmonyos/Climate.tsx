'use client';

import React from 'react';
import { useVehicleStore } from '@/store/vehicle-store';
import * as Ic from './icons';
import { useHa, BAR_H } from './theme';
import { useHaLocal } from './shared';

/**
 * The climate page: the cabin from above and behind, the driver's temperature
 * down the left and the passenger's down the right (tap the faint number above
 * or below to step by half a degree), the fan slider between them, the air
 * direction for each side, and Auto / A/C / power / demist / max A/C along the
 * bottom. Positions are read off the photograph of the page.
 */
export function ClimatePage() {
  const t = useHa();
  const dark = t.tone === 'dark';
  const { climate, patchClimate } = useVehicleStore();
  const { on, toggle, val, setVal, slug } = useHaLocal();
  const [tab, setTab] = React.useState<'front' | 'rear'>('front');
  const [more, setMore] = React.useState(false);
  const rear = tab === 'rear';

  const left = rear ? val.rearL || 24 : climate.driverTempC;
  const right = rear ? val.rearR || 24 : climate.passengerTempC;
  const setLeft = (v: number) => {
    const c = Math.min(32, Math.max(16, Math.round(v * 2) / 2));
    if (rear) setVal('rearL', c);
    else patchClimate({ driverTempC: c });
  };
  const setRight = (v: number) => {
    const c = Math.min(32, Math.max(16, Math.round(v * 2) / 2));
    if (rear) setVal('rearR', c);
    else patchClimate({ passengerTempC: c });
  };

  const accent = t.blue;
  const pill = { background: t.seg, color: t.text } as React.CSSProperties;

  const temp = (v: number, set: (n: number) => void, x: number, align: 'l' | 'r') => (
    <div className="absolute flex flex-col items-center" style={{ left: x - 60, top: 238, width: 120 }}>
      <button type="button" aria-label={`Raise to ${(v + 0.5).toFixed(1)}`} onClick={() => set(v + 0.5)} className="tnum py-3 text-[30px] font-light opacity-40 outline-none" style={{ textAlign: align === 'l' ? 'left' : 'right' }}>
        {(v + 0.5).toFixed(1)}
      </button>
      <div className="tnum py-1 text-[52px] font-medium leading-none" aria-live="polite">{v.toFixed(1)}</div>
      <button type="button" aria-label={`Lower to ${(v - 0.5).toFixed(1)}`} onClick={() => set(v - 0.5)} className="tnum py-3 text-[30px] font-light opacity-40 outline-none">
        {(v - 0.5).toFixed(1)}
      </button>
    </div>
  );

  const seg = (items: { icon: React.ReactNode; label: string; on: boolean; fn: () => void }[], x: number, w: number) => (
    <div className="absolute flex overflow-hidden rounded-[26px]" style={{ left: x, bottom: BAR_H + 22, width: w, height: 55, background: t.seg }} role="group">
      {items.map((it, i) => (
        <button
          key={i}
          type="button"
          aria-label={it.label}
          aria-pressed={it.on}
          onClick={it.fn}
          className="flex flex-1 items-center justify-center outline-none"
          style={{ background: it.on ? accent : 'transparent', color: it.on ? '#fff' : t.text, borderLeft: i ? `1px solid ${t.line}` : 'none' }}
        >
          {it.icon}
        </button>
      ))}
    </div>
  );

  const air = (key: string) =>
    [
      { icon: <Ic.AirFace size={28} />, label: 'Face' },
      { icon: <Ic.AirFeet size={28} />, label: 'Feet' },
      { icon: <Ic.AirBoth size={28} />, label: 'Face and feet' },
    ].map((a, i) => ({ ...a, on: val[key] === i, fn: () => setVal(key, i) }));

  const fan = climate.fanSpeed; // 0 - 5
  const track = React.useRef<HTMLDivElement>(null);
  const dragFan = (e: React.PointerEvent) => {
    if (e.type === 'pointermove' && e.buttons === 0) return;
    const r = track.current?.getBoundingClientRect();
    if (!r) return;
    patchClimate({ fanSpeed: Math.round(Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)) * 5) });
  };

  return (
    <div className="absolute inset-0 overflow-hidden" style={{ background: t.bg, color: t.text }}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={`/hmi/${slug}/cabin-climate-${t.tone}.webp`} alt="" draggable={false} className="absolute max-w-none" style={{ left: -40, top: -78, width: 1360 }} />

      {/* PM2.5 and recirculation */}
      <button type="button" onClick={() => toggle('recirc')} className="absolute flex h-[52px] items-center gap-3 rounded-full px-5 text-left text-[15px] leading-tight outline-none" style={{ left: 34, top: 36, ...pill }}>
        <Ic.Recirc size={30} style={{ color: on.recirc ? accent : undefined }} />
        <span>PM2.5<br />{on.recirc ? 'Recirc' : 'In 1'}</span>
      </button>

      <div className="absolute flex gap-[88px] text-[24px]" style={{ left: 640, top: 36, transform: 'translateX(-50%)' }} role="tablist">
        {(['front', 'rear'] as const).map((k) => (
          <button key={k} role="tab" aria-selected={tab === k} type="button" onClick={() => setTab(k)} className="relative pb-2 outline-none" style={{ color: tab === k ? accent : t.text2 }}>
            {k === 'front' ? 'Front' : 'Rear'}
            {tab === k && <span className="absolute inset-x-0 -bottom-[1px] h-[3px] rounded-full" style={{ background: accent }} />}
          </button>
        ))}
      </div>

      {temp(left, setLeft, 92, 'l')}
      {temp(right, setRight, 1184, 'r')}

      {/* fan */}
      <div className="absolute flex items-center gap-5" style={{ left: 640, top: 506, transform: 'translateX(-50%)' }}>
        <Ic.Fan size={22} style={{ opacity: 0.55 }} />
        <div
          ref={track}
          className="relative h-[34px] w-[236px] cursor-ew-resize touch-none"
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
          <span className="absolute left-0 top-1/2 h-[6px] -translate-y-1/2 rounded-full" style={{ width: `${(fan / 5) * 100}%`, background: accent }} />
          <span className="absolute inset-x-0 top-1/2 h-[6px] -translate-y-1/2 rounded-full" style={{ background: dark ? 'rgba(255,255,255,0.18)' : 'rgba(21,22,26,0.14)', zIndex: -1 }} />
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <span key={i} className="absolute top-1/2 h-[5px] w-[5px] -translate-x-1/2 -translate-y-1/2 rounded-full" style={{ left: `${(i / 5) * 100}%`, background: i <= fan ? '#fff' : t.text3 }} />
          ))}
          <span className="absolute top-1/2 h-[30px] w-[30px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-white" style={{ left: `${(fan / 5) * 100}%`, boxShadow: '0 2px 10px rgba(0,0,0,0.3)' }} />
        </div>
        <Ic.Fan size={34} style={{ opacity: 0.7 }} />
      </div>

      <button type="button" aria-pressed={climate.sync} onClick={() => patchClimate({ sync: !climate.sync })} className="absolute flex h-[53px] items-center justify-center rounded-full px-6 text-[19px] outline-none" style={{ left: 36, bottom: BAR_H + 90, ...pill, color: climate.sync ? accent : t.text }}>
        Temp sync
      </button>
      <button type="button" onClick={() => setMore((m) => !m)} className="absolute flex h-[53px] w-[140px] items-center justify-center rounded-full text-[19px] outline-none" style={{ left: 1092, bottom: BAR_H + 92, ...pill }}>
        More
      </button>

      {seg(air('airL'), 36, 304)}
      {seg(
        [
          { icon: <span className="text-[19px]">Auto</span>, label: 'Auto', on: on.climateAuto, fn: () => toggle('climateAuto') },
          { icon: <span className="text-[19px] font-medium">A/C</span>, label: 'A/C', on: climate.acOn, fn: () => patchClimate({ acOn: !climate.acOn }) },
          { icon: <Ic.Power size={26} />, label: 'Climate power', on: !on.climateOff, fn: () => toggle('climateOff') },
          { icon: <Ic.SunMax size={28} />, label: 'Demist max', on: on.demistMax, fn: () => toggle('demistMax') },
          { icon: <Ic.AcMax size={28} />, label: 'Cooling max', on: on.coolMax, fn: () => toggle('coolMax') },
        ],
        384,
        503,
      )}
      {seg(air('airR'), 932, 300)}

      {more && (
        <div className="absolute z-10 w-[300px] rounded-[26px] p-3" style={{ left: 932, bottom: BAR_H + 160, background: t.panel, backdropFilter: 'blur(24px)' }}>
          {[
            ['recirc', 'Recirculation'],
            ['purifier', 'Air purifier'],
            ['precon', 'Pre-conditioning'],
          ].map(([id, label]) => (
            <button key={id} type="button" aria-pressed={on[id]} onClick={() => toggle(id)} className="flex h-[52px] w-full items-center justify-between rounded-[16px] px-4 text-[18px] outline-none">
              {label}
              <span className="relative h-[28px] w-[48px] rounded-full" style={{ background: on[id] ? accent : t.seg }}>
                <span className="absolute top-[3px] h-[22px] w-[22px] rounded-full bg-white transition-all" style={{ left: on[id] ? 23 : 3 }} />
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
