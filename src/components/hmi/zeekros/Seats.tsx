'use client';

import React from 'react';
import type { Vehicle } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { useZk } from './theme';
import * as Ic from './icons';
import { useZkLocal } from './shared';

/**
 * The seat page (c10_0018): "Seat comfort" and "Seat adjust" down the left, the three comfort
 * programmes (ventilation and heat, massage, hot stones) and an All-off button, and the cabin's
 * four seats in a pale 3D drawing with a pair of AUTO chips on each. The drawing is a clay render
 * of the build's own cabin (public/hmi/<slug>/cabin-seats-light|dark.webp), with a schematic
 * behind it for when the picture is not there.
 */

const TABS = ['Vent and heat', 'Massage', 'Hot stones'];

/**
 * where the chips sit on the drawing: (x, y) of the pair's centre, in the drawing's 680 x 400.
 * They are the seats' backrest centres projected through the drawing's camera
 * (export_zx.hmi_cabin prints them as HMI_SEATS: fractions of the picture).
 */
const SEATS = [
  { id: 'FR', label: 'Front passenger', x: 253, y: 130 },
  { id: 'FL', label: 'Driver', x: 248, y: 274 },
  { id: 'RR', label: 'Rear right', x: 466, y: 126 },
  { id: 'RL', label: 'Rear left', x: 473, y: 278 },
];

function Schematic({ tone }: { tone: 'light' | 'dark' }) {
  const fill = tone === 'light' ? '#f7f8fd' : '#2a2d38';
  const side = tone === 'light' ? '#dfe3f3' : '#1f212b';
  const seat = (x: number, y: number, k: string) => (
    <g key={k} transform={`translate(${x} ${y}) scale(-1 1)`}>
      <path d="M-70 -6 L60 -22 L78 18 L-52 36 Z" fill={fill} stroke={side} strokeWidth="2" />
      <path d="M-70 -6 L-84 -52 L-30 -66 L-22 -26 Z" fill={side} />
      <path d="M-70 -6 L-84 -52 L-78 -60 L-62 -12 Z" fill={fill} />
      <ellipse cx="-62" cy="-64" rx="14" ry="9" fill={fill} stroke={side} strokeWidth="2" />
    </g>
  );
  return (
    <svg viewBox="0 0 680 400" width="680" height="400" aria-hidden className="absolute inset-0">
      <path d="M40 120 130 60 320 40 330 360 120 380 30 330Z" fill={side} opacity="0.45" />
      <circle cx="78" cy="226" r="30" fill="none" stroke={side} strokeWidth="9" />
      {seat(236, 130, 'a')}
      {seat(224, 292, 'b')}
      {seat(478, 128, 'c')}
      {seat(478, 289, 'd')}
      {seat(478, 208, 'e')}
    </svg>
  );
}

function SeatChips({ tab }: { tab: number }) {
  const t = useZk();
  const { val, setVal } = useZkLocal();
  const { climate, patchClimate } = useVehicleStore();
  const chip = (x: number, y: number, key: string, icon: React.ReactNode, on: boolean, onClick: () => void, label: string) => (
    <button
      key={key}
      type="button"
      aria-label={label}
      aria-pressed={on}
      onClick={onClick}
      className="absolute flex items-center gap-[18px] rounded-[5px] pl-[14px] focus:outline-none focus-visible:ring-2 focus-visible:ring-black/30"
      style={{
        left: x - 70,
        top: y - 21,
        width: 141,
        height: 42,
        background: t.tone === 'light' ? 'rgba(255,255,255,0.86)' : 'rgba(255,255,255,0.14)',
        color: on ? t.red : t.text3,
        boxShadow: on ? '0 2px 10px rgba(196,22,47,0.18)' : '0 1px 4px rgba(30,30,70,0.10)',
      }}
    >
      <span style={{ color: on ? t.text : t.text3 }}>{icon}</span>
      <span className="text-[15px] font-semibold tracking-wide">{tab === 1 ? (on ? 'ON' : 'OFF') : 'AUTO'}</span>
    </button>
  );
  return (
    <>
      {SEATS.map((s) => {
        const heatOn =
          s.id === 'FL' ? climate.seatHeatDriver > 0 : s.id === 'FR' ? climate.seatHeatPassenger > 0 : val[`seat${s.id}`] > 0;
        const ventOn = val[`vent${s.id}`] > 0;
        const toggleHeat = () => {
          if (s.id === 'FL') patchClimate({ seatHeatDriver: climate.seatHeatDriver > 0 ? 0 : 2 });
          else if (s.id === 'FR') patchClimate({ seatHeatPassenger: climate.seatHeatPassenger > 0 ? 0 : 2 });
          else setVal(`seat${s.id}`, val[`seat${s.id}`] > 0 ? 0 : 1);
        };
        return (
          <React.Fragment key={s.id}>
            {chip(s.x, s.y - 26, `v${s.id}`, tab === 1 ? <Ic.Sync size={22} /> : tab === 2 ? <Ic.Snow size={22} /> : <Ic.Fan size={22} />, ventOn, () => setVal(`vent${s.id}`, ventOn ? 0 : 1), `${s.label} ${TABS[tab]}`)}
            {chip(s.x, s.y + 26, `h${s.id}`, <Ic.SeatHeat size={22} />, heatOn, toggleHeat, `${s.label} heat`)}
          </React.Fragment>
        );
      })}
    </>
  );
}

export function SeatsPage({ vehicle }: { vehicle: Vehicle }) {
  const t = useZk();
  const { val, setVal, notify } = useZkLocal();
  const { patchClimate } = useVehicleStore();
  const [page, setPage] = React.useState<'comfort' | 'adjust'>('comfort');
  const tab = val.seatTab;
  const [img, setImg] = React.useState(true);

  const menu = (id: 'comfort' | 'adjust', label: string, icon: React.ReactNode, y: number) => (
    <button
      type="button"
      onClick={() => setPage(id)}
      className="absolute flex w-[114px] -translate-y-1/2 flex-col items-center gap-[10px] focus:outline-none"
      style={{ left: 0, top: y, color: page === id ? t.text : t.text2 }}
    >
      {icon}
      <span className="text-[15px] leading-none">{label}</span>
    </button>
  );

  return (
    <div className="absolute inset-0">
      <span className="absolute" style={{ left: 115, top: 12, bottom: 12, width: 1, background: t.line }} aria-hidden />
      <span className="absolute w-[3px] rounded-full" style={{ left: 113, top: page === 'comfort' ? 186 : 319, height: 30, background: t.red }} aria-hidden />
      {menu('comfort', 'Seat comfort', <Ic.SeatComfort size={36} />, 200)}
      {menu('adjust', 'Seat adjust', <Ic.SeatAdjust size={36} />, 333)}

      {page === 'comfort' ? (
        <>
          <div className="absolute overflow-hidden rounded-[4px]" style={{ left: 148, top: 152, width: 208, background: t.tone === 'light' ? '#dfe3f3' : 'rgba(255,255,255,0.08)' }}>
            {TABS.map((label, i) => (
              <button
                key={label}
                type="button"
                onClick={() => setVal('seatTab', i)}
                className="flex h-[43px] w-full items-center justify-center text-[16px] focus:outline-none"
                style={{
                  background: tab === i ? (t.tone === 'light' ? '#fff' : 'rgba(255,255,255,0.16)') : 'transparent',
                  boxShadow: tab === i ? `inset 0 0 0 1.500px ${t.red}` : undefined,
                  color: t.text,
                }}
              >
                {label}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => {
              patchClimate({ seatHeatDriver: 0, seatHeatPassenger: 0 });
              for (const k of ['FL', 'FR', 'RL', 'RR']) {
                setVal(`seat${k}`, 0);
                setVal(`vent${k}`, 0);
              }
              notify('All seat programmes off');
            }}
            className="absolute flex h-[56px] w-[199px] items-center justify-center rounded-[3px] text-[17px] focus:outline-none"
            style={{ left: 155, top: 320, background: t.pill, color: t.pillText }}
          >
            All off
          </button>
          <div className="absolute" style={{ left: 463, top: 54, width: 680, height: 400 }}>
            {!img && <Schematic tone={t.tone} />}
            {img && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={`/hmi/${vehicle.slug}/cabin-seats-${t.tone}.webp`}
                alt=""
                draggable={false}
                onError={() => setImg(false)}
                className="absolute inset-0 select-none"
                style={{ width: 680, height: 400, objectFit: 'contain' }}
              />
            )}
            <SeatChips tab={tab} />
            <button
              type="button"
              aria-label="Steering wheel heat"
              aria-pressed={val.wheelHeat > 0}
              onClick={() => setVal('wheelHeat', val.wheelHeat > 0 ? 0 : 1)}
              className="absolute flex h-[40px] w-[40px] items-center justify-center rounded-[5px] focus:outline-none"
              style={{
                left: 56,
                top: 260,
                background: t.tone === 'light' ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.16)',
                color: val.wheelHeat > 0 ? t.red : t.text,
              }}
            >
              <Ic.WheelP size={24} />
            </button>
          </div>
        </>
      ) : (
        <AdjustPanel />
      )}
      <span className="absolute" style={{ right: 75, top: 43, color: t.text }}>
        <Ic.Gear size={26} />
      </span>
    </div>
  );
}

/** Seat adjust: the driver's seat in profile with its sliders (kept in the page, not the car). */
function AdjustPanel() {
  const t = useZk();
  const { val, setVal } = useZkLocal();
  const slide = (id: string, label: string, def: number, y: number) => (
    <div className="absolute flex items-center gap-4" style={{ left: 260, top: y, width: 520 }}>
      <span className="w-[150px] text-[16px]" style={{ color: t.text2 }}>
        {label}
      </span>
      <input
        type="range"
        min={0}
        max={100}
        value={id in val ? val[id] : def}
        onChange={(e) => setVal(id, Number(e.target.value))}
        aria-label={label}
        className="h-1 flex-1 cursor-pointer"
        style={{ accentColor: t.accent }}
      />
      <span className="tnum w-[40px] text-right text-[15px]">{id in val ? val[id] : def}</span>
    </div>
  );
  const back = 8 + (('adjBack' in val ? val.adjBack : 40) / 100) * 24;
  const slideX = (('adjSlide' in val ? val.adjSlide : 50) / 100) * 60;
  return (
    <>
      {slide('adjSlide', 'Seat position', 50, 88)}
      {slide('adjBack', 'Backrest angle', 40, 148)}
      {slide('adjHeight', 'Seat height', 55, 208)}
      {slide('adjLumbar', 'Lumbar support', 30, 268)}
      <svg viewBox="0 0 260 220" width="260" height="220" className="absolute" style={{ left: 880, top: 84 }} aria-hidden>
        <g transform={`translate(${60 + slideX} 0)`}>
          <path d="M0 150 L100 150 L110 176 L10 176 Z" fill={t.tone === 'light' ? '#fff' : '#2a2d38'} stroke={t.line} strokeWidth="2" />
          <g transform={`rotate(${-back} 6 150)`}>
            <rect x="-6" y="40" width="30" height="112" rx="10" fill={t.tone === 'light' ? '#fff' : '#2a2d38'} stroke={t.line} strokeWidth="2" />
            <rect x="-4" y="12" width="26" height="26" rx="8" fill={t.tone === 'light' ? '#fff' : '#2a2d38'} stroke={t.line} strokeWidth="2" />
          </g>
        </g>
        <path d="M30 190H240" stroke={t.line} strokeWidth="3" />
      </svg>
    </>
  );
}
