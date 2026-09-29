'use client';

import React from 'react';
import { cx } from '../ui';
import { HY } from './theme';
import { Info } from './icons';

/**
 * The segmented selector of HyperOS settings pages: a grey track, the chosen
 * segment filled blue. Segments may carry a second line (M1 over its name).
 */
export function Segmented<T extends string>({
  value,
  options,
  onChange,
  label,
  height = 52,
  tone = HY.blue,
}: {
  value: T | null;
  options: { id: T; label: string; sub?: string }[];
  onChange: (v: T) => void;
  label: string;
  height?: number;
  tone?: string;
}) {
  return (
    <div
      role="radiogroup"
      aria-label={label}
      className="flex rounded-[14px] p-[3px]"
      style={{ background: HY.panel2, height }}
    >
      {options.map((o) => {
        const on = o.id === value;
        return (
          <button
            key={o.id}
            type="button"
            role="radio"
            aria-checked={on}
            onClick={() => onChange(o.id)}
            className="flex flex-1 flex-col items-center justify-center rounded-[11px] transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
            style={{ background: on ? tone : 'transparent', color: on ? '#fff' : HY.text }}
          >
            <span className="text-[16px] font-medium leading-tight">{o.label}</span>
            {o.sub && (
              <span className="text-[11px] leading-tight" style={{ color: on ? 'rgba(255,255,255,0.8)' : HY.text3 }}>
                {o.sub}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

/** The HyperOS switch: blue when on. */
export function Switch({
  on,
  onChange,
  label,
}: {
  on: boolean;
  onChange: (v: boolean) => void;
  label: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      aria-label={label}
      onClick={() => onChange(!on)}
      className="relative h-[30px] w-[52px] shrink-0 rounded-full transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
      style={{ background: on ? HY.blue : HY.panel3 }}
    >
      <span
        className="absolute top-[3px] h-6 w-6 rounded-full bg-white shadow transition-all duration-200"
        style={{ left: on ? 25 : 3 }}
      />
    </button>
  );
}

/** A thick HyperOS slider (the brightness / volume kind). */
export function Slider({
  value,
  min = 0,
  max = 100,
  onChange,
  label,
  tone = HY.blue,
}: {
  value: number;
  min?: number;
  max?: number;
  onChange: (v: number) => void;
  label: string;
  tone?: string;
}) {
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <input
      type="range"
      min={min}
      max={max}
      value={value}
      aria-label={label}
      onChange={(e) => onChange(Number(e.target.value))}
      className="hy-slider h-[34px] w-full cursor-pointer appearance-none rounded-[12px]"
      style={{ background: `linear-gradient(to right, ${tone} ${pct}%, ${HY.panel2} ${pct}%)` }}
    />
  );
}

/** A section heading inside a settings page, with an optional (i). */
export function SectionLabel({ children, info }: { children: React.ReactNode; info?: boolean }) {
  return (
    <div className="mb-3 flex items-center gap-1.5 text-[14px]" style={{ color: HY.text2 }}>
      {children}
      {info && <Info size={17} />}
    </div>
  );
}

/** A flat HyperOS row: label (and hint) on the left, a control on the right. */
export function Row({
  label,
  hint,
  children,
  className,
}: {
  label: string;
  hint?: string;
  children?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cx('flex items-center gap-4 rounded-[16px] px-5 py-3.5', className)} style={{ background: HY.panel }}>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-[16px]" style={{ color: HY.text }}>{label}</span>
        {hint && <span className="mt-0.5 block truncate text-[12.5px]" style={{ color: HY.text3 }}>{hint}</span>}
      </span>
      {children}
    </div>
  );
}
