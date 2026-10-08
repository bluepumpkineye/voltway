'use client';

import React from 'react';
import Link from 'next/link';
import type { ShowroomScene, ShowroomTab } from '@/store/vehicle-store';

/** The showroom's frosted-glass surface: light, quiet, and readable on white. */
export const GLASS =
  'bg-white/75 backdrop-blur-xl ring-1 ring-black/[0.06] shadow-[0_8px_28px_-10px_rgba(20,24,32,0.22)]';

const FOCUS =
  'outline-none focus-visible:ring-2 focus-visible:ring-neutral-900/70 focus-visible:ring-offset-1';

const TABS: { id: ShowroomTab; label: string }[] = [
  { id: 'colour', label: 'Colour' },
  { id: 'interior', label: 'Interior' },
  { id: 'wheels', label: 'Wheels' },
  { id: 'dimensions', label: 'Dimensions' },
  { id: 'xray', label: 'X-ray' },
];

/** The bottom pill. A tab without what it needs (no cabin built) is disabled. */
export function TabBar({
  tab,
  onTab,
  disabled,
  hidden = [],
}: {
  tab: ShowroomTab;
  onTab: (t: ShowroomTab) => void;
  disabled: Partial<Record<ShowroomTab, string>>;
  /** tabs this car does not offer at all (no X-ray model) */
  hidden?: ShowroomTab[];
}) {
  return (
    <div role="tablist" aria-label="Showroom" className={`flex rounded-full p-1 ${GLASS}`}>
      {TABS.filter((t) => !hidden.includes(t.id)).map((t) => {
        const off = disabled[t.id];
        const active = tab === t.id;
        return (
          <button
            key={t.id}
            role="tab"
            type="button"
            aria-selected={active}
            disabled={Boolean(off)}
            title={off}
            onClick={() => onTab(t.id)}
            className={`whitespace-nowrap rounded-full px-3.5 py-2 text-[13px] font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-35 sm:px-5 ${FOCUS} ${
              active ? 'bg-neutral-900 text-white shadow-sm' : 'text-neutral-600 hover:text-neutral-900'
            }`}
          >
            {t.label}
          </button>
        );
      })}
    </div>
  );
}

/** A two-way switch: the studio, or the city the cabin was baked in. */
export function SceneToggle({
  scene,
  onScene,
}: {
  scene: ShowroomScene;
  onScene: (s: ShowroomScene) => void;
}) {
  const opts: { id: ShowroomScene; label: string }[] = [
    { id: 'studio', label: 'Studio' },
    { id: 'city', label: 'City' },
  ];
  return (
    <div role="group" aria-label="Scene" className={`flex rounded-full p-1 ${GLASS}`}>
      {opts.map((o) => (
        <button
          key={o.id}
          type="button"
          aria-pressed={scene === o.id}
          onClick={() => onScene(o.id)}
          className={`rounded-full px-3.5 py-1.5 text-[12px] font-medium transition-colors ${FOCUS} ${
            scene === o.id ? 'bg-neutral-900 text-white' : 'text-neutral-600 hover:text-neutral-900'
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

/** Back to the vehicle page, and a menu of the cars that have a showroom. */
export function CarMenu({
  backHref,
  current,
  cars,
}: {
  backHref: string;
  current: string;
  cars: { slug: string; label: string }[];
}) {
  const [open, setOpen] = React.useState(false);
  const root = React.useRef<HTMLDivElement>(null);
  const label = cars.find((c) => c.slug === current)?.label ?? current;

  React.useEffect(() => {
    if (!open) return;
    const away = (e: PointerEvent) => {
      if (!root.current?.contains(e.target as Node)) setOpen(false);
    };
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false);
    document.addEventListener('pointerdown', away);
    document.addEventListener('keydown', esc);
    return () => {
      document.removeEventListener('pointerdown', away);
      document.removeEventListener('keydown', esc);
    };
  }, [open]);

  return (
    <div ref={root} className="pointer-events-auto relative flex items-center gap-2">
      <Link
        href={backHref}
        aria-label="Back to the vehicle page"
        className={`flex h-9 w-9 items-center justify-center rounded-full text-neutral-700 hover:text-neutral-950 ${GLASS} ${FOCUS}`}
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
          <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </Link>
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className={`flex h-9 items-center gap-2 rounded-full px-4 text-[14px] font-medium text-neutral-900 ${GLASS} ${FOCUS}`}
      >
        {label}
        {cars.length > 1 && (
          <svg width="9" height="6" viewBox="0 0 9 6" aria-hidden className={`transition-transform ${open ? 'rotate-180' : ''}`}>
            <path d="M1 1l3.5 3.5L8 1" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        )}
      </button>
      {open && cars.length > 1 && (
        <ul role="listbox" className={`absolute left-11 top-11 z-10 min-w-[200px] overflow-hidden rounded-2xl p-1.5 ${GLASS}`}>
          {cars.map((c) => (
            <li key={c.slug} role="option" aria-selected={c.slug === current}>
              <Link
                href={`/showroom/${c.slug}`}
                className={`block rounded-xl px-3.5 py-2 text-[13px] ${FOCUS} ${
                  c.slug === current ? 'bg-neutral-900 text-white' : 'text-neutral-700 hover:bg-black/5'
                }`}
              >
                {c.label}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
