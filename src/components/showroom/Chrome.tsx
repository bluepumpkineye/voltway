'use client';

import React from 'react';
import Link from 'next/link';
import { setSoundOn, soundOn, subscribeSound } from '@/lib/sound/engine';
import type { ShowroomScene, ShowroomTab } from '@/store/vehicle-store';

/** The showroom's frosted-glass surface: light, quiet, and readable on white. */
export const GLASS =
  'bg-white/75 backdrop-blur-xl ring-1 ring-black/[0.06] shadow-[0_8px_28px_-10px_rgba(20,24,32,0.22)]';

/** For a popover over a busy picture: the same glass, nearly opaque, so small print stays readable. */
export const PANEL =
  'bg-white/95 backdrop-blur-xl ring-1 ring-black/[0.06] shadow-[0_12px_36px_-12px_rgba(20,24,32,0.32)]';

export const FOCUS =
  'outline-none focus-visible:ring-2 focus-visible:ring-neutral-900/70 focus-visible:ring-offset-1';

/** Where a panel at the top of the window starts: under the top bar, whose height the showroom publishes. */
export const BELOW_TOP = 'top-[calc(var(--top-ui,56px)+8px)]';

const TABS: { id: ShowroomTab; label: string }[] = [
  { id: 'colour', label: 'Colour' },
  { id: 'interior', label: 'Interior' },
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'wheels', label: 'Wheels' },
  { id: 'dimensions', label: 'Specifications' },
  { id: 'xray', label: 'X-ray' },
  { id: 'charging', label: 'Charging' },
  { id: 'drive', label: 'Drive' },
  { id: 'tech', label: 'Tech' },
];

/** The main menu. A tab without what it needs (no cabin built) is disabled. */
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
  // on a narrow window the menu scrolls: the tab in use is brought to the middle of it
  const list = React.useRef<HTMLDivElement>(null);
  React.useEffect(() => {
    const el = list.current?.querySelector<HTMLElement>('[aria-selected="true"]');
    const box = list.current;
    if (!el || !box || box.scrollWidth <= box.clientWidth) return;
    box.scrollTo({ left: el.offsetLeft - (box.clientWidth - el.offsetWidth) / 2, behavior: 'smooth' });
  }, [tab]);
  return (
    <div ref={list} role="tablist" aria-label="Showroom" className={`hy-scroll pointer-events-auto relative flex max-w-full overflow-x-auto rounded-full p-1 ${GLASS}`}>
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
            className={`whitespace-nowrap rounded-full px-3 py-1.5 text-[13px] font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-35 sm:px-4 ${FOCUS} ${
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
    <div role="group" aria-label="Scene" className={`pointer-events-auto flex rounded-full p-1 ${GLASS}`}>
      {opts.map((o) => (
        <button
          key={o.id}
          type="button"
          aria-pressed={scene === o.id}
          onClick={() => onScene(o.id)}
          className={`rounded-full px-3 py-1.5 text-[12px] font-medium transition-colors ${FOCUS} ${
            scene === o.id ? 'bg-neutral-900 text-white' : 'text-neutral-600 hover:text-neutral-900'
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

/** Sound on or off: the doors, the bonnet, the tailgate and the charge flap make a noise as they move (src/lib/sound). */
export function SoundToggle() {
  const on = React.useSyncExternalStore(subscribeSound, soundOn, () => true);
  return (
    <button
      type="button"
      aria-pressed={on}
      aria-label={on ? 'Sound on: turn the door sounds off' : 'Sound off: turn the door sounds on'}
      title={on ? 'Sound on' : 'Sound off'}
      onClick={() => setSoundOn(!on)}
      className={`pointer-events-auto grid h-9 w-9 place-items-center rounded-full hover:text-neutral-950 ${GLASS} ${FOCUS} ${
        on ? 'text-neutral-700' : 'text-neutral-400'
      }`}
    >
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
        <path d="M2.2 6.1h2.3l3.1-2.5v8.8L4.5 9.9H2.2z" fill="currentColor" stroke="currentColor" strokeWidth="1" strokeLinejoin="round" />
        {on ? (
          <>
            <path d="M10 5.9c.9.6 1.4 1.3 1.4 2.1s-.5 1.5-1.4 2.1" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
            <path d="M11.8 4c1.5 1 2.3 2.4 2.3 4s-.8 3-2.3 4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
          </>
        ) : (
          <path d="M10.4 6l3.6 4M14 6l-3.6 4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        )}
      </svg>
    </button>
  );
}

/** A menu of the cars that have a showroom. Changing car keeps the tab, so one view can be compared car to car. */
export function CarMenu({
  current,
  cars,
  tab,
}: {
  current: string;
  cars: { slug: string; label: string }[];
  tab: ShowroomTab;
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
    <div ref={root} className="pointer-events-auto relative">
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={`Car: ${label}. Change car`}
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
        <ul role="listbox" aria-label="Cars" className={`absolute left-0 top-11 z-30 min-w-[210px] overflow-hidden rounded-2xl p-1.5 ${PANEL}`}>
          {cars.map((c) => (
            <li key={c.slug} role="option" aria-selected={c.slug === current}>
              <Link
                href={`/showroom/${c.slug}${tab === 'colour' ? '' : `?tab=${tab}`}`}
                onClick={() => setOpen(false)}
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

/**
 * The one place the showroom's small print lives: what the view shows and how far to trust it, where the figures come
 * from, and who the showroom is not. It stays out of the picture until it is asked for.
 */
export function InfoButton({
  title,
  note,
  hint,
  sources,
}: {
  title: string;
  note: string;
  /** a line about how to use the view, when it has one */
  hint?: string;
  sources: { label: string; url: string }[];
}) {
  const [open, setOpen] = React.useState(false);
  const root = React.useRef<HTMLDivElement>(null);

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
    <div ref={root} className="pointer-events-auto relative">
      <button
        type="button"
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label="About this view, sources and the showroom"
        onClick={() => setOpen((v) => !v)}
        className={`grid h-9 w-9 place-items-center rounded-full text-neutral-700 hover:text-neutral-950 ${GLASS} ${FOCUS}`}
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
          <circle cx="8" cy="8" r="6.4" stroke="currentColor" strokeWidth="1.4" />
          <path d="M8 7.2v3.6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <circle cx="8" cy="4.9" r="0.95" fill="currentColor" />
        </svg>
      </button>
      {open && (
        <div
          role="dialog"
          aria-label="About this view"
          className={`absolute right-0 top-11 z-30 max-h-[min(70vh,520px)] w-[min(340px,calc(100vw-24px))] overflow-y-auto rounded-2xl p-4 text-[12px] leading-relaxed text-neutral-700 ${PANEL}`}
        >
          <h2 className="text-[13px] font-semibold text-neutral-900">{title}</h2>
          <p className="mt-1">{note}</p>
          {hint && <p className="mt-1 text-neutral-500">{hint}</p>}
          {sources.length > 0 && (
            <>
              <h3 className="mt-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-neutral-500">Sources</h3>
              <ul className="mt-1 space-y-1">
                {sources.map((s) => (
                  <li key={s.url}>
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline decoration-neutral-300 underline-offset-2 hover:text-neutral-950"
                    >
                      {s.label}
                    </a>
                  </li>
                ))}
              </ul>
            </>
          )}
          <h3 className="mt-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-neutral-500">About Voltway</h3>
          <p className="mt-1 text-neutral-500">
            Specifications are compiled from manufacturer filings and reporting. Range is shown on its own test cycle: CLTC and WLTP are never
            mixed, since CLTC typically reads 25–35% higher for the same car. The 3D models are original reconstructions built for this
            project. Voltway is an independent showcase and is not affiliated with, endorsed by, or a partner of any manufacturer shown.
          </p>
        </div>
      )}
    </div>
  );
}
