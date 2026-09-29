'use client';

import React from 'react';

/**
 * Primitives for the in-car UI.
 *
 * The whole HMI is authored in a fixed 1280x800 coordinate space and scaled to
 * whatever the screen quad measures in 3D, so sizes here are in "screen pixels"
 * of the car's own display rather than CSS pixels of the page.
 */

export const HMI_W = 1280;
export const HMI_H = 800;

export function cx(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(' ');
}

export function Card({
  className,
  children,
  ...rest
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cx(
        'rounded-[22px] bg-white/[0.045] ring-1 ring-white/[0.07] backdrop-blur-sm',
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}

export function CardTitle({ children }: { children: React.ReactNode }) {
  return (
    <div className="px-5 pt-4 pb-2 text-[13px] font-medium uppercase tracking-[0.15em] text-white/40">
      {children}
    </div>
  );
}

export function Tile({
  active,
  accent,
  icon,
  label,
  sublabel,
  onClick,
  disabled,
}: {
  active?: boolean;
  accent: string;
  icon: React.ReactNode;
  label: string;
  sublabel?: string;
  onClick?: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-pressed={active}
      className={cx(
        'group flex h-full w-full flex-col items-start justify-between rounded-[20px] p-4 text-left transition-all duration-200',
        'ring-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/70',
        active
          ? 'bg-white/[0.13] ring-white/25'
          : 'bg-white/[0.045] ring-white/[0.07] hover:bg-white/[0.085]',
        disabled && 'cursor-not-allowed opacity-40',
      )}
      style={active ? { boxShadow: `inset 0 0 0 1px ${accent}55, 0 8px 28px -14px ${accent}` } : undefined}
    >
      <span
        className="flex h-11 w-11 items-center justify-center rounded-[14px] transition-colors"
        style={{
          background: active ? accent : 'rgba(255,255,255,0.07)',
          color: active ? '#08090b' : 'rgba(255,255,255,0.82)',
        }}
      >
        {icon}
      </span>
      <span className="mt-3 block w-full">
        <span className="block truncate text-[17px] font-medium text-white/95">{label}</span>
        {sublabel && (
          <span className="mt-0.5 block truncate text-[13px] text-white/45">{sublabel}</span>
        )}
      </span>
    </button>
  );
}

export function Stepper({
  value,
  min,
  max,
  step = 0.5,
  unit,
  label,
  onChange,
  accent,
}: {
  value: number;
  min: number;
  max: number;
  step?: number;
  unit: string;
  label: string;
  onChange: (v: number) => void;
  accent: string;
}) {
  const clamp = (v: number) => Math.min(max, Math.max(min, Math.round(v / step) * step));
  return (
    <div className="flex flex-col items-center gap-3">
      <span className="text-[13px] uppercase tracking-[0.16em] text-white/40">{label}</span>
      <div className="flex items-center gap-4">
        <RoundButton label={`Decrease ${label}`} onClick={() => onChange(clamp(value - step))}>
          <MinusIcon />
        </RoundButton>
        <span className="tnum min-w-[132px] text-center text-[52px] font-light leading-none text-white">
          {value.toFixed(step < 1 ? 1 : 0)}
          <span className="ml-1 align-top text-[20px] text-white/45">{unit}</span>
        </span>
        <RoundButton label={`Increase ${label}`} onClick={() => onChange(clamp(value + step))} accent={accent}>
          <PlusIcon />
        </RoundButton>
      </div>
    </div>
  );
}

export function RoundButton({
  children,
  onClick,
  label,
  accent,
}: {
  children: React.ReactNode;
  onClick: () => void;
  label: string;
  accent?: string;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      onClick={onClick}
      className="flex h-14 w-14 items-center justify-center rounded-full bg-white/[0.07] text-white/85 ring-1 ring-white/10 transition-all hover:bg-white/[0.14] active:scale-95 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
      style={accent ? { color: accent } : undefined}
    >
      {children}
    </button>
  );
}

export function SegmentBar({
  value,
  max,
  onChange,
  accent,
  label,
}: {
  value: number;
  max: number;
  onChange: (v: number) => void;
  accent: string;
  label: string;
}) {
  return (
    <div className="flex items-center gap-1.5" role="group" aria-label={label}>
      {Array.from({ length: max }, (_, i) => i + 1).map((i) => (
        <button
          key={i}
          type="button"
          aria-label={`${label} level ${i}`}
          aria-pressed={i <= value}
          onClick={() => onChange(i === value ? i - 1 : i)}
          className="h-9 flex-1 rounded-[6px] transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
          style={{
            background: i <= value ? accent : 'rgba(255,255,255,0.08)',
            opacity: i <= value ? 0.35 + (i / max) * 0.65 : 1,
          }}
        />
      ))}
    </div>
  );
}

export function Toggle({
  on,
  onChange,
  label,
  accent,
}: {
  on: boolean;
  onChange: (v: boolean) => void;
  label: string;
  accent: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      aria-label={label}
      onClick={() => onChange(!on)}
      className="relative h-9 w-[62px] shrink-0 rounded-full transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
      style={{ background: on ? accent : 'rgba(255,255,255,0.12)' }}
    >
      <span
        className="absolute top-1 h-7 w-7 rounded-full bg-white shadow-md transition-all duration-200"
        style={{ left: on ? 30 : 4 }}
      />
    </button>
  );
}

export function Row({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-4 px-5 py-3.5">
      <span className="min-w-0 flex-1">
        <span className="block truncate text-[17px] text-white/90">{label}</span>
        {hint && <span className="block truncate text-[13px] text-white/40">{hint}</span>}
      </span>
      {children}
    </div>
  );
}

/* ------------------------------------------------------------------ icons */
/* Inline so the HMI never waits on a font or sprite sheet to become legible. */

const S = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };

export const PlusIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" {...S}><path d="M12 5v14M5 12h14" /></svg>
);
export const MinusIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" {...S}><path d="M5 12h14" /></svg>
);
export const HomeIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" {...S}><path d="M3 10.5 12 3l9 7.5" /><path d="M5.5 9.5V20h13V9.5" /></svg>
);
export const ClimateIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" {...S}><path d="M12 3v18M4.5 7.5l15 9M19.5 7.5l-15 9" /></svg>
);
export const DriveIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" {...S}><circle cx="12" cy="12" r="8.5" /><path d="M12 3.5v5M20.5 12h-5M3.5 12h5" /></svg>
);
export const NavIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" {...S}><path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11Z" /><circle cx="12" cy="10" r="2.5" /></svg>
);
export const MediaIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" {...S}><path d="M9 18V5l11-2v13" /><circle cx="6.5" cy="18" r="2.5" /><circle cx="17.5" cy="16" r="2.5" /></svg>
);
export const AdasIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" {...S}><path d="M12 3.5 4 7v5.5c0 4.6 3.4 7.4 8 8.5 4.6-1.1 8-3.9 8-8.5V7Z" /><path d="m9 12 2.2 2.2L15.5 10" /></svg>
);
export const ControlsIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" {...S}><path d="M4 8h10M18 8h2M4 16h4M12 16h8" /><circle cx="16" cy="8" r="2" /><circle cx="10" cy="16" r="2" /></svg>
);
export const PlayIcon = () => (
  <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5.5v13l11-6.5Z" /></svg>
);
export const PauseIcon = () => (
  <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5h3v14H8zM13 5h3v14h-3z" /></svg>
);
export const NextIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M6 5.5v13l9-6.5ZM16 5h2.5v14H16z" /></svg>
);
export const PrevIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M18 5.5v13L9 12ZM5.5 5H8v14H5.5z" /></svg>
);
export const LockIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" {...S}><rect x="5" y="10.5" width="14" height="9.5" rx="2" /><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3" /></svg>
);
export const LightIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" {...S}><circle cx="12" cy="12" r="4" /><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9 17 7M7 17l-2.1 2.1" /></svg>
);
export const BoltIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" {...S}><path d="M13 2 4.5 13.5H11L10 22l8.5-11.5H12Z" /></svg>
);
