'use client';

import React from 'react';
import * as Ha from '../harmonyos/icons';
import { useHaLocal } from '../harmonyos/shared';
import { useAv } from './theme';

/* The pieces every Avatr page is made of: the frosted tiles, switches, segmented selectors and tab rows. */

export function Switch({ on }: { on: boolean }) {
  const t = useAv();
  return (
    <span className="relative inline-block h-[30px] w-[54px] shrink-0 rounded-full transition-colors" style={{ background: on ? t.blue : t.tone === 'dark' ? 'rgba(255,255,255,0.22)' : 'rgba(22,27,46,0.16)' }}>
      <span className="absolute top-[3px] h-[24px] w-[24px] rounded-full bg-white transition-all" style={{ left: on ? 27 : 3, boxShadow: '0 1px 4px rgba(0,0,0,0.3)' }} />
    </span>
  );
}

/** A card with a switch: its title and a line under it. */
export function ToggleCard({ title, sub, on, onChange, info }: { title: string; sub?: string; on: boolean; onChange: (v: boolean) => void; info?: boolean }) {
  const t = useAv();
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      onClick={() => onChange(!on)}
      className="flex min-h-[76px] items-center gap-[16px] rounded-[18px] px-[20px] py-[12px] text-left outline-none focus-visible:ring-2 focus-visible:ring-[#2c46f2]"
      style={{ background: t.card }}
    >
      <Switch on={on} />
      <span className="min-w-0 flex-1">
        <span className="block text-[18px] leading-snug">{title}</span>
        {sub && <span className="block text-[13px] leading-snug" style={{ color: t.text2 }}>{sub}</span>}
      </span>
      {info && <Ha.Info size={24} style={{ color: t.text3 }} />}
    </button>
  );
}

/** A card that would open a deeper page (the small corner mark); here it says so. */
export function LinkCard({ title, sub, onClick, tall }: { title: string; sub?: string; onClick?: () => void; tall?: boolean }) {
  const t = useAv();
  const { notify } = useHaLocal();
  return (
    <button
      type="button"
      onClick={onClick ?? (() => notify(`${title} is not part of the showroom demo`))}
      className="relative rounded-[18px] px-[20px] py-[14px] text-left outline-none focus-visible:ring-2 focus-visible:ring-[#2c46f2]"
      style={{ background: t.card, minHeight: tall ? 100 : 76 }}
    >
      <span className="block text-[18px] leading-snug">{title}</span>
      {sub && <span className="block text-[13px] leading-snug" style={{ color: t.text2 }}>{sub}</span>}
      <span className="absolute bottom-[7px] right-[7px] h-0 w-0" style={{ borderStyle: 'solid', borderWidth: '0 0 10px 10px', borderColor: `transparent transparent ${t.text3} transparent` }} />
    </button>
  );
}

export function Segmented({ items, value, onChange, label, sub }: { items: string[]; value: number; onChange: (i: number) => void; label: string; sub?: Record<number, string> }) {
  const t = useAv();
  return (
    <div className="flex h-[58px] gap-[2px] rounded-[18px] p-[4px]" style={{ background: t.seg }} role="group" aria-label={label}>
      {items.map((x, i) => (
        <button
          key={x}
          type="button"
          aria-pressed={i === value}
          onClick={() => onChange(i)}
          className="flex flex-1 items-center justify-center gap-[6px] rounded-[14px] text-[18px] outline-none transition-colors focus-visible:ring-2 focus-visible:ring-[#2c46f2]"
          style={{ background: i === value ? t.segOn : 'transparent', color: i === value ? t.tileOnText : t.text, boxShadow: i === value ? '0 2px 8px rgba(30,40,90,0.14)' : 'none' }}
        >
          {x}
          {sub?.[i] && <span className="text-[11px]" style={{ color: t.text2 }}>{sub[i]}</span>}
        </button>
      ))}
    </div>
  );
}

export function Section({ title, children, info, first }: { title: string; children: React.ReactNode; info?: boolean; first?: boolean }) {
  const t = useAv();
  return (
    <section className={first ? 'mt-[8px]' : 'mt-[24px]'}>
      <div className="mb-[12px] flex items-center justify-between text-[19px]">
        {title}
        {info && <Ha.Info size={24} style={{ color: t.text3 }} />}
      </div>
      {children}
    </section>
  );
}

export const Grid2 = ({ children }: { children: React.ReactNode }) => <div className="grid grid-cols-2 gap-[14px]">{children}</div>;

/** The row of tabs along the top of a page, the chosen one blue with an underline (white over the dark App Centre). */
export function TabRow({ tabs, value, onChange, className, style, onDark }: { tabs: string[]; value: number; onChange: (i: number) => void; className?: string; style?: React.CSSProperties; onDark?: boolean }) {
  const t = useAv();
  const on = onDark ? '#fff' : t.blue;
  const off = onDark ? 'rgba(255,255,255,0.55)' : t.text;
  return (
    <div className={className} style={style} role="tablist">
      {tabs.map((x, i) => (
        <button key={x} role="tab" aria-selected={i === value} type="button" onClick={() => onChange(i)} className="relative whitespace-nowrap pb-[7px] text-[19px] outline-none" style={{ color: i === value ? on : off }}>
          {x}
          {i === value && <span className="absolute inset-x-0 bottom-0 h-[2px] rounded-full" style={{ background: on }} />}
        </button>
      ))}
    </div>
  );
}

/** The car, over a soft light: the page's picture. */
export function CarImage({ w = 520, left = 0, top = 0, glow }: { w?: number; left?: number; top?: number; glow?: string }) {
  const { slug } = useHaLocal();
  return (
    <>
      {glow && <span className="absolute rounded-full" style={{ left: left - 10, top: top + w * 0.28, width: w + 20, height: w * 0.22, background: glow, filter: 'blur(26px)' }} />}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={`/hmi/${slug}/car34.webp`} alt="" draggable={false} className="absolute max-w-none" style={{ width: w, left, top }} />
    </>
  );
}

/** A pale round-cornered button with an icon and (optionally) a label. */
export function Pill({ children, on, onClick, label, style, className }: { children: React.ReactNode; on?: boolean; onClick?: () => void; label: string; style?: React.CSSProperties; className?: string }) {
  const t = useAv();
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={on}
      onClick={onClick}
      className={`flex items-center justify-center rounded-full outline-none focus-visible:ring-2 focus-visible:ring-[#2c46f2] ${className ?? ''}`}
      style={{ background: on ? t.blue : t.seg, color: on ? '#fff' : t.text, ...style }}
    >
      {children}
    </button>
  );
}
