'use client';

import React from 'react';
import { STEPS } from '@/lib/tech/boost';
import { useVehicleStore } from '@/store/vehicle-store';
import { HA } from './theme';

/**
 * What the car's screen shows while BOOST is on, in the BOOST demo (docs/tech-showcase.md section 13). A STAND-IN: the
 * maker's own BOOST screens (the cluster, the centre screen and the head-up display change together) are not in any
 * photograph, so this is not a copy of them. It lists what the maker says BOOST does, in the order the demo applies it,
 * and the +10 % instantaneous torque as a relative bar (the car's torque is not published). The page says so on its face.
 */
export function BoostScreen() {
  const step = useVehicleStore((s) => s.boostStep);
  const t = HA.dark;
  return (
    <div
      className="absolute inset-0 z-[45] overflow-hidden"
      role="status"
      aria-label="BOOST is on"
      style={{ background: 'radial-gradient(900px 560px at 18% 12%, rgba(38,76,190,0.55), rgba(7,8,11,0) 62%), radial-gradient(700px 500px at 100% 100%, rgba(255,74,63,0.20), rgba(7,8,11,0) 60%), #07080b', color: t.text }}
    >
      <div className="absolute flex items-center gap-[22px]" style={{ left: 64, top: 52 }}>
        <span className="relative grid h-[84px] w-[84px] place-items-center rounded-full" style={{ boxShadow: `0 0 34px ${t.blue}`, border: `5px solid ${t.blue}` }}>
          <span className="h-[34px] w-[34px] rounded-full" style={{ background: t.blue, opacity: 0.85 }} />
        </span>
        <div>
          <div className="text-[64px] font-semibold leading-none" style={{ letterSpacing: '0.12em' }}>BOOST</div>
          <div className="mt-[8px] flex items-center gap-[10px] text-[22px]" style={{ color: t.text2 }}>
            <span className="h-[12px] w-[12px] animate-pulse rounded-full" style={{ background: t.blue }} />
            On
          </div>
        </div>
      </div>

      <ul className="absolute flex flex-col gap-[14px]" style={{ left: 64, top: 200, width: 660 }}>
        {STEPS.map((s, i) => {
          const done = i < step;
          return (
            <li
              key={s.id}
              className="flex items-center gap-[22px] rounded-[26px] px-[26px] transition-all duration-500"
              style={{ height: 88, background: done ? 'rgba(74,116,255,0.16)' : 'rgba(255,255,255,0.05)', opacity: done ? 1 : 0.42, border: `2px solid ${done ? 'rgba(74,116,255,0.55)' : 'transparent'}` }}
            >
              <span className="grid h-[38px] w-[38px] shrink-0 place-items-center rounded-full transition-colors duration-500" style={{ background: done ? t.blue : 'rgba(255,255,255,0.14)' }} aria-hidden>
                {done && (
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12.5l4.5 4.5L19 7.5" />
                  </svg>
                )}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-[27px] leading-tight">{s.label}</span>
                <span className="block text-[18px] leading-tight" style={{ color: t.text2 }}>{s.detail}</span>
              </span>
            </li>
          );
        })}
      </ul>

      <div className="absolute rounded-[30px] px-[34px] py-[28px]" style={{ left: 790, top: 200, width: 430, height: 470, background: 'rgba(255,255,255,0.06)' }}>
        <div className="text-[22px]" style={{ color: t.text2 }}>Instantaneous torque, relative</div>
        <div className="mt-[26px] flex items-end justify-around" style={{ height: 300 }}>
          {[
            { label: 'Normal', pct: 100, color: 'rgba(255,255,255,0.34)', on: true },
            { label: 'BOOST', pct: 110, color: t.blue, on: step >= 1 },
          ].map((b) => (
            <div key={b.label} className="flex flex-col items-center gap-[10px]">
              <span className="text-[26px] font-medium tabular-nums">{b.on ? `${b.pct} %` : '—'}</span>
              <span className="block w-[96px] rounded-t-[18px] transition-all duration-700" style={{ height: b.on ? (b.pct / 110) * 236 : 8, background: b.color }} />
              <span className="text-[20px]" style={{ color: t.text2 }}>{b.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="absolute flex justify-between gap-[30px] text-[16px] leading-snug" style={{ left: 64, right: 60, bottom: 40, color: t.text3 }}>
        <span style={{ maxWidth: 520 }}>A stand-in drawn by the showroom: the maker’s BOOST screens are not photographed.</span>
        <span className="text-right" style={{ maxWidth: 560 }}>Published: +10 % instantaneous torque · up to 21,000 rpm · 251 km/h · 98.2 % motor efficiency · torque response within 1 ms</span>
      </div>
    </div>
  );
}
