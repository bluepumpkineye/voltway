'use client';

import React from 'react';
import type { Vehicle } from '@/data/vehicles/schema';
import * as Ic from '../dilink/icons';
import { XO, STATUS_H, BAR_H } from './theme';
import { useXo } from './shared';

/** Where the two panels sit on the 1280 x 800 screen (measured on c10_0020: the car panel is a third of the width). */
export const PANEL_T = STATUS_H + 8;
export const PANEL_H = 800 - BAR_H - 20 - PANEL_T;
export const CAR_L = 19;
export const CAR_W = 407;
export const RIGHT_L = 443;
export const RIGHT_W = 822;

/**
 * The car panel (c10_0020): a tall rounded panel of dark blue-grey cloud with the car from above, small
 * and black, in the middle and the "park here" key at the bottom left. It stays on the home and under
 * every settings page and the app centre; only the panel beside it changes.
 */
export function CarPanel({ vehicle }: { vehicle: Vehicle }) {
  const { notify } = useXo();
  return (
    <div className="absolute overflow-hidden" style={{ left: CAR_L, top: PANEL_T, width: CAR_W, height: PANEL_H, borderRadius: 22, background: 'radial-gradient(58% 50% at 50% 52%, #1b2240 0%, #2a3358 42%, #6d789c 78%, #8c95b3 100%)' }}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={`/hmi/${vehicle.slug}/car-top.webp`}
        alt=""
        draggable={false}
        onError={(e) => {
          e.currentTarget.style.display = 'none';
        }}
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 select-none"
        style={{ height: 132, width: 'auto', filter: 'brightness(0.3) saturate(0.6)' }}
      />
      <button type="button" aria-label="Park here" onClick={() => notify('Park here (showroom demo)')} className="absolute flex h-[60px] w-[52px] flex-col items-center justify-center gap-[3px] rounded-[12px] text-[10px] focus:outline-none" style={{ left: 16, bottom: 16, background: 'rgba(240,242,250,0.82)', color: XO.text }}>
        <span className="flex h-[22px] w-[22px] items-center justify-center rounded-[6px] text-[14px] font-semibold" style={{ boxShadow: `inset 0 0 0 1.5px ${XO.text}` }}>P</span>
        Park here
      </button>
    </div>
  );
}

/** The two panels and the little drag handle between them: the car panel at the left, `children` at the right. */
export function Split({ vehicle, children }: { vehicle: Vehicle; children: React.ReactNode }) {
  return (
    <div className="absolute inset-0" style={{ background: XO.ground }}>
      <CarPanel vehicle={vehicle} />
      <span className="absolute flex flex-col gap-[3px]" style={{ left: 433, top: PANEL_T + PANEL_H / 2 - 6 }} aria-hidden>
        {[0, 1, 2].map((i) => <span key={i} className="block h-[3px] w-[3px] rounded-full" style={{ background: XO.text3 }} />)}
      </span>
      {children}
    </div>
  );
}

/** The right panel as a light sheet (settings, the app centre): rounded, frosted, with the drag handle at its top. */
export function Sheet({ children, handle = true }: { children: React.ReactNode; handle?: boolean }) {
  return (
    <div className="absolute overflow-hidden" style={{ left: RIGHT_L, top: PANEL_T, width: RIGHT_W, height: PANEL_H, borderRadius: 22, background: 'linear-gradient(160deg, rgba(236,234,246,0.97), rgba(220,220,238,0.97))', boxShadow: 'inset 0 0 0 1px rgba(26,28,38,0.05)' }}>
      {handle && (
        <span className="absolute left-1/2 top-[9px] flex -translate-x-1/2 gap-[4px]" aria-hidden>
          {[0, 1, 2].map((i) => <span key={i} className="block h-[3px] w-[3px] rounded-full" style={{ background: XO.text3 }} />)}
        </span>
      )}
      {children}
    </div>
  );
}

/**
 * The map (c10_0020): a rounded panel of drawn streets and parks, the search card at the top left with
 * the home and work shortcuts, the settings and charging keys at the bottom left, the heading-up button
 * at the top right, a road label and the assistant's mascot at the bottom right.
 */
export function MapPanel() {
  const { notify } = useXo();
  return (
    <div className="absolute overflow-hidden" style={{ left: RIGHT_L, top: PANEL_T, width: RIGHT_W, height: PANEL_H, borderRadius: 22, background: '#e4e8ee' }}>
      <svg viewBox="0 0 822 666" preserveAspectRatio="xMidYMid slice" className="absolute inset-0 h-full w-full" aria-hidden>
        <rect width="822" height="666" fill="#e5e9ef" />
        <path d="M0 40C90 20 190 60 280 0H440C400 90 440 190 420 300C380 400 300 420 250 520C200 620 220 640 200 666H0Z" fill="#cde4cc" opacity="0.9" />
        <path d="M0 330C160 300 300 330 420 280C380 400 300 420 250 520" fill="#d3e5d3" opacity="0.8" />
        <path d="M40 380C150 350 220 380 270 460C300 520 280 560 240 620L120 600C60 540 30 460 40 380Z" fill="#dfe6e6" />
        <path d="M520 0C560 140 600 280 640 420S700 600 740 666" stroke="#b9d9b9" strokeWidth="9" fill="none" />
        <path d="M270 0C300 120 340 260 420 380S540 560 600 666" stroke="#fff" strokeWidth="14" fill="none" />
        <path d="M270 0C300 120 340 260 420 380S540 560 600 666" stroke="#cfd4de" strokeWidth="1.500" fill="none" strokeDasharray="6 6" opacity="0.7" />
        <path d="M0 480C180 440 300 400 420 380S640 300 822 270" stroke="#fff" strokeWidth="10" fill="none" />
        <path d="M620 0C640 100 700 220 760 330" stroke="#fff" strokeWidth="9" fill="none" />
        <path d="M560 230C650 250 730 300 780 380" stroke="#dbe0ea" strokeWidth="6" fill="none" />
        <g fill="#aeb6c6" opacity="0.8"><rect x="470" y="150" width="46" height="34" rx="4" /><rect x="560" y="400" width="52" height="38" rx="4" /><rect x="690" y="460" width="60" height="42" rx="4" /><rect x="350" y="520" width="44" height="32" rx="4" /></g>
        <circle cx="440" cy="400" r="17" fill="#3b6df0" stroke="#fff" strokeWidth="5" />
        <path d="M440 384 452 412 440 406 428 412z" fill="#fff" />
      </svg>
      <button type="button" onClick={() => notify('Search (showroom demo)')} className="absolute flex items-center gap-3 rounded-[14px] px-4 text-left text-[16px] focus:outline-none" style={{ left: 18, top: 18, width: 300, height: 48, background: 'rgba(240,242,248,0.92)', color: XO.text2 }}>
        <Ic.Search size={18} /> <span className="flex-1">Search destination</span> <Ic.Home size={17} /> <Ic.Pin size={17} />
      </button>
      <span className="absolute flex h-[44px] w-[44px] flex-col items-center justify-center rounded-[10px] text-[9px]" style={{ right: 16, top: 18, background: 'rgba(240,242,248,0.92)' }}><Ic.Pin size={16} />Heading up</span>
      <div className="absolute flex h-[56px] items-center gap-[18px] rounded-[12px] px-[14px] text-[10px]" style={{ left: 16, bottom: 14, background: 'rgba(240,242,248,0.92)' }}>
        <span className="flex flex-col items-center gap-[2px]"><Ic.Gear size={19} />Settings</span>
        <span className="flex flex-col items-center gap-[2px]"><Ic.Bolt size={19} />Charge</span>
      </div>
      <span className="absolute left-1/2 rounded-[9px] px-[14px] py-[7px] text-[14px]" style={{ bottom: 22, transform: 'translateX(-35%)', background: 'rgba(240,242,248,0.92)', color: XO.text }}>Unnamed road</span>
      <span className="absolute flex h-[50px] w-[50px] items-end justify-center" style={{ right: 6, bottom: 4 }} aria-hidden>
        <span className="block h-[38px] w-[42px] rounded-[16px]" style={{ background: 'radial-gradient(circle at 50% 30%, #3a3f52, #12141c)', boxShadow: 'inset 0 0 0 2px #cfd6ea' }}>
          <span className="mx-auto mt-[12px] flex w-[24px] justify-between"><span className="block h-[8px] w-[7px] rounded-full bg-[#7fd7ff]" /><span className="block h-[8px] w-[7px] rounded-full bg-[#7fd7ff]" /></span>
        </span>
      </span>
    </div>
  );
}
