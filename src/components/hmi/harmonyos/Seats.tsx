'use client';

import React from 'react';
import { useVehicleStore } from '@/store/vehicle-store';
import * as Ic from './icons';
import { useHa, BAR_H } from './theme';
import { useHaLocal } from './shared';

type Tab = 'heat' | 'vent' | 'massage' | 'gravity';
const TABS: { id: Tab; label: string }[] = [
  { id: 'heat', label: 'Seat heating' },
  { id: 'vent', label: 'Seat ventilation' },
  { id: 'massage', label: 'Seat massage' },
  { id: 'gravity', label: 'Zero gravity' },
];

/** The four seats and where their badges sit on the cabin picture (fractions of it). */
const SEATS = [
  { id: 'driver', label: 'Driver', x: 0.39, y: 0.5, front: true },
  { id: 'passenger', label: 'Passenger', x: 0.64, y: 0.55, front: true },
  { id: 'rearL', label: 'Rear left', x: 0.23, y: 0.78, front: false },
  { id: 'rearR', label: 'Rear right', x: 0.44, y: 0.84, front: false },
] as const;

/**
 * The seat page: tabs for heating, ventilation, massage and the zero-gravity
 * posture, the cabin from above with a badge on each seat, and the cushion and
 * backrest sliders along the bottom (OFF to MAX in three steps). The front seats'
 * heating is the shared climate state, so the cabin page and the desktop card
 * agree with it.
 */
export function SeatsPage() {
  const t = useHa();
  const { climate, patchClimate } = useVehicleStore();
  const { val, setVal } = useHaLocal();
  const [tab, setTab] = React.useState<Tab>('heat');
  const [seat, setSeat] = React.useState<(typeof SEATS)[number]['id']>('driver');

  const key = (part: string) => `${tab}.${seat}.${part}`;
  const level = (part: 'cushion' | 'back') => {
    if (tab === 'heat' && part === 'cushion' && seat === 'driver') return climate.seatHeatDriver;
    if (tab === 'heat' && part === 'cushion' && seat === 'passenger') return climate.seatHeatPassenger;
    return val[key(part)];
  };
  const setLevel = (part: 'cushion' | 'back', v: number) => {
    if (tab === 'heat' && part === 'cushion' && seat === 'driver') patchClimate({ seatHeatDriver: v });
    else if (tab === 'heat' && part === 'cushion' && seat === 'passenger') patchClimate({ seatHeatPassenger: v });
    else setVal(key(part), v);
  };
  const front = SEATS.find((s) => s.id === seat)!.front;

  return (
    <div className="absolute inset-0 overflow-hidden" style={{ background: t.bg, color: t.text }}>
      <div className="absolute flex gap-[60px] text-[21px]" style={{ left: 640, top: 48, transform: 'translateX(-50%)' }} role="tablist">
        {TABS.map((x) => (
          <button key={x.id} role="tab" aria-selected={tab === x.id} type="button" onClick={() => setTab(x.id)} className="relative whitespace-nowrap pb-2 outline-none" style={{ color: tab === x.id ? t.blue : t.text }}>
            {x.label}
            {tab === x.id && <span className="absolute inset-x-0 -bottom-[1px] h-[2px] rounded-full" style={{ background: t.blue }} />}
          </button>
        ))}
      </div>

      <div className="absolute" style={{ left: 640, top: 102, width: 800, height: 500, transform: 'translateX(-50%)' }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={`/hmi/luxeed-rx/cabin-seats-${t.tone}.webp`} alt="" draggable={false} className="h-full w-full object-contain" style={{ WebkitMaskImage: 'radial-gradient(ellipse at 50% 50%, #000 62%, transparent 100%)', maskImage: 'radial-gradient(ellipse at 50% 50%, #000 62%, transparent 100%)' }} />
        {SEATS.map((s) => {
          const sel = s.id === seat;
          const lit = tab === 'heat' && s.id === 'driver' ? climate.seatHeatDriver > 0 : tab === 'heat' && s.id === 'passenger' ? climate.seatHeatPassenger > 0 : false;
          return (
            <button
              key={s.id}
              type="button"
              aria-label={`${s.label} seat`}
              aria-pressed={sel}
              onClick={() => setSeat(s.id)}
              className="absolute flex h-[58px] w-[58px] -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full outline-none transition-transform"
              style={{
                left: `${s.x * 100}%`,
                top: `${s.y * 100}%`,
                background: lit ? t.blue : '#f6f4f2',
                color: lit ? '#fff' : '#17181b',
                boxShadow: sel ? `0 0 0 4px ${t.blue}, 0 4px 14px rgba(0,0,0,0.25)` : '0 4px 14px rgba(0,0,0,0.2)',
                transform: `translate(-50%, -50%) scale(${sel ? 1.08 : 1})`,
              }}
            >
              {tab === 'heat' ? <Ic.HeatUp size={26} /> : tab === 'vent' ? <Ic.Fan size={26} /> : tab === 'massage' ? <Ic.HeatWave size={26} /> : <Ic.SeatHeat size={26} />}
            </button>
          );
        })}
      </div>

      <div className="absolute flex items-end gap-[30px]" style={{ left: 640, bottom: BAR_H + 22, transform: 'translateX(-50%)' }}>
        {tab === 'heat' || tab === 'vent' ? (
          <>
            <Step label="Cushion" value={level('cushion')} onChange={(v) => setLevel('cushion', v)} />
            {front && <Step label="Backrest" value={level('back')} onChange={(v) => setLevel('back', v)} />}
            {front && (
              <button type="button" onClick={() => setLevel('back', level('cushion'))} className="flex h-[58px] items-center rounded-full px-7 text-[19px] outline-none" style={{ background: t.segOn, color: t.tileOnText }}>
                Sync
              </button>
            )}
          </>
        ) : tab === 'massage' ? (
          <div className="flex gap-3">
            {['Off', 'Wave', 'Pulse', 'Lumbar'].map((m, i) => (
              <button key={m} type="button" aria-pressed={val[key('mode')] === i} onClick={() => setVal(key('mode'), i)} className="h-[58px] rounded-full px-8 text-[19px] outline-none" style={{ background: val[key('mode')] === i ? t.blue : t.seg, color: val[key('mode')] === i ? '#fff' : t.text }}>
                {m}
              </button>
            ))}
          </div>
        ) : (
          <div className="flex gap-3">
            {['Off', 'Pose 1', 'Pose 2', 'Pose 3'].map((m, i) => (
              <button key={m} type="button" aria-pressed={val[key('pose')] === i} onClick={() => setVal(key('pose'), i)} className="h-[58px] rounded-full px-8 text-[19px] outline-none" style={{ background: val[key('pose')] === i ? t.blue : t.seg, color: val[key('pose')] === i ? '#fff' : t.text }}>
                {m}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/** OFF to MAX in three steps, as the car's own seat sliders. */
function Step({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  const t = useHa();
  const ref = React.useRef<HTMLDivElement>(null);
  const move = (e: React.PointerEvent) => {
    if (e.type === 'pointermove' && e.buttons === 0) return;
    const r = ref.current?.getBoundingClientRect();
    if (!r) return;
    onChange(Math.round(Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)) * 3));
  };
  return (
    <div>
      <div className="mb-[8px] ml-[4px] text-[19px]">{label}</div>
      <div className="relative h-[58px] w-[290px] rounded-full" style={{ background: t.seg }}>
        <span className="absolute left-[24px] top-1/2 -translate-y-1/2 text-[14px] font-medium" style={{ opacity: value === 0 ? 0 : 1 }}>OFF</span>
        <span className="absolute right-[22px] top-1/2 -translate-y-1/2 text-[14px] font-medium">MAX</span>
        <div
          ref={ref}
          className="absolute inset-y-0 cursor-ew-resize touch-none"
          style={{ left: 29, right: 29 }}
          onPointerDown={move}
          onPointerMove={move}
          role="slider"
          tabIndex={0}
          aria-label={label}
          aria-valuemin={0}
          aria-valuemax={3}
          aria-valuenow={value}
          onKeyDown={(e) => {
            if (e.key === 'ArrowRight') onChange(Math.min(3, value + 1));
            if (e.key === 'ArrowLeft') onChange(Math.max(0, value - 1));
          }}
        >
          <span className="absolute top-1/2 h-[8px] -translate-y-1/2 rounded-full" style={{ left: 0, width: `${(value / 3) * 100}%`, background: t.blue, opacity: value ? 1 : 0 }} />
          {[1, 2].map((i) => (
            <span key={i} className="absolute top-1/2 h-[5px] w-[5px] -translate-y-1/2 rounded-full" style={{ left: `${(i / 3) * 100}%`, background: t.text3 }} />
          ))}
          <span className="absolute top-1/2 h-[38px] w-[38px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-white" style={{ left: `${(value / 3) * 100}%`, boxShadow: '0 2px 10px rgba(0,0,0,0.28)' }} />
        </div>
      </div>
    </div>
  );
}
