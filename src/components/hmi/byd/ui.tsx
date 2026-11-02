'use client';

import React from 'react';
import { useHaLocal } from '../harmonyos/shared';
import * as Ic from './icons';
import { useBy } from './theme';

/* The pieces every Seal page is made of: switches, rows, segmented selectors, tabs, the menu's pills. */

export function Switch({ on, onChange, label }: { on: boolean; onChange: (v: boolean) => void; label: string }) {
  const t = useBy();
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      aria-label={label}
      onClick={() => onChange(!on)}
      className="relative inline-block h-[28px] w-[50px] shrink-0 rounded-full outline-none transition-colors focus-visible:ring-2 focus-visible:ring-white/70"
      style={{ background: on ? (t.tone === 'dark' ? '#37c47a' : '#2fb457') : t.tone === 'dark' ? 'rgba(255,255,255,0.28)' : 'rgba(23,38,58,0.22)' }}
    >
      <span className="absolute top-[3px] h-[22px] w-[22px] rounded-full bg-white transition-all" style={{ left: on ? 25 : 3, boxShadow: '0 1px 4px rgba(0,0,0,0.35)' }} />
    </button>
  );
}

/** A row with the switch at its left, as the car's settings lay them out, and a line of help under the title. */
export function ToggleRow({ title, sub, on, onChange }: { title: string; sub?: string; on: boolean; onChange: (v: boolean) => void }) {
  const t = useBy();
  return (
    <div className="flex items-start gap-[18px] py-[14px]">
      <span className="mt-[2px]"><Switch on={on} onChange={onChange} label={title} /></span>
      <span className="min-w-0 flex-1">
        <span className="block text-[19px] leading-snug">{title}</span>
        {sub && <span className="mt-[2px] block text-[14px] leading-snug" style={{ color: t.text2 }}>{sub}</span>}
      </span>
    </div>
  );
}

/** A row with a value and a chevron at the right (Bluetooth, Wi-Fi). */
export function ValueRow({ title, value, onClick }: { title: string; value: string; onClick?: () => void }) {
  const t = useBy();
  const { notify } = useHaLocal();
  return (
    <button type="button" onClick={onClick ?? (() => notify(`${title} is not part of the showroom demo`))} className="flex w-full items-center justify-between py-[22px] text-left text-[19px] outline-none focus-visible:ring-2 focus-visible:ring-white/60">
      <span>{title}</span>
      <span className="flex items-center gap-[10px]" style={{ color: t.text2 }}>{value}<span aria-hidden className="text-[22px] leading-none">›</span></span>
    </button>
  );
}

export function Segmented({ items, value, onChange, label }: { items: string[]; value: number; onChange: (i: number) => void; label: string }) {
  const t = useBy();
  return (
    <div className="inline-flex h-[46px] gap-[2px] rounded-full p-[3px]" style={{ background: t.seg }} role="group" aria-label={label}>
      {items.map((x, i) => (
        <button
          key={x}
          type="button"
          aria-pressed={i === value}
          onClick={() => onChange(i)}
          className="rounded-full px-[26px] text-[17px] outline-none transition-colors focus-visible:ring-2 focus-visible:ring-white/70"
          style={{ background: i === value ? t.segOn : 'transparent', color: i === value ? t.segOnText : t.text }}
        >
          {x}
        </button>
      ))}
    </div>
  );
}

export function Heading({ children }: { children: React.ReactNode }) {
  return <div className="mb-[12px] mt-[22px] text-[18px]">{children}</div>;
}

export function Tabs({ tabs, value, onChange, className, style }: { tabs: string[]; value: number; onChange: (i: number) => void; className?: string; style?: React.CSSProperties }) {
  const t = useBy();
  return (
    <div className={className ?? 'flex gap-[34px]'} style={style} role="tablist">
      {tabs.map((x, i) => (
        <button key={x} role="tab" aria-selected={i === value} type="button" onClick={() => onChange(i)} className="relative whitespace-nowrap pb-[8px] text-[17px] outline-none" style={{ color: i === value ? t.text : t.text2 }}>
          {x}
          {i === value && <span className="absolute bottom-0 left-1/2 h-[3px] w-[20px] -translate-x-1/2 rounded-full" style={{ background: t.text }} />}
        </button>
      ))}
    </div>
  );
}

/** The menu down the left: a search box and rows, the chosen one in a pill. */
export function SideMenu({ items, value, onChange, search = true, style }: { items: { id: string; label: string; icon: React.ReactNode }[]; value: string; onChange: (id: string) => void; search?: boolean; style?: React.CSSProperties }) {
  const t = useBy();
  return (
    <nav className="absolute flex flex-col gap-[10px]" style={style} aria-label="Menu">
      {search && (
        <button type="button" className="flex h-[50px] items-center gap-[12px] rounded-full px-[20px] text-left text-[16px] outline-none" style={{ background: t.pill, color: t.pillText }}>
          <Ic.MenuSearch size={19} /> Search
        </button>
      )}
      {items.map((m) => {
        const on = m.id === value;
        return (
          <button key={m.id} type="button" aria-current={on ? 'page' : undefined} onClick={() => onChange(m.id)} className="flex h-[50px] items-center gap-[14px] rounded-full px-[20px] text-left text-[16px] outline-none transition-colors focus-visible:ring-2 focus-visible:ring-white/60" style={{ background: on ? t.pill : 'transparent', color: on ? t.pillText : t.text }}>
            <span className="shrink-0">{m.icon}</span>
            {m.label}
          </button>
        );
      })}
    </nav>
  );
}

/** The car, as the page's picture. */
export function CarImage({ w = 440, left = 0, top = 0, dim }: { w?: number; left?: number; top?: number; dim?: boolean }) {
  const { slug } = useHaLocal();
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={`/hmi/${slug}/car34.webp`} alt="" draggable={false} className="absolute max-w-none" style={{ width: w, left, top, filter: dim ? 'brightness(0.8)' : undefined }} />
  );
}
