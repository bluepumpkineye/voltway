'use client';

import React from 'react';
import { useZk } from './theme';
import { useZkLocal } from './shared';

/**
 * The App Centre (c10_0025): a column of recent apps, a vertical rule, and a grid of seven by
 * three coloured tiles with their names under them. The tiles are drawn here in the colours of
 * the car's own; the glyphs are plain shapes, not the apps' logos.
 */
interface App {
  id: string;
  label: string;
  c1: string;
  c2: string;
  glyph: React.ReactNode;
}

const W = '#fff';
const g = (children: React.ReactNode) => (
  <svg viewBox="0 0 40 40" width="40" height="40" aria-hidden>
    {children}
  </svg>
);
const text = (s: string, size = 11, y = 24) => (
  <text x="20" y={y} fontSize={size} fontWeight="800" textAnchor="middle" fill={W} fontFamily="Arial, sans-serif">
    {s}
  </text>
);

const APPS: App[] = [
  { id: 'iqiyi', label: 'Video', c1: '#18c77a', c2: '#0ea45f', glyph: g(text('iQIYI', 10)) },
  { id: 'bili', label: 'Short video', c1: '#ff6aa0', c2: '#ff3f7c', glyph: g(text('bili', 12)) },
  {
    id: 'scene', label: 'Scenes', c1: '#8b5cf6', c2: '#a855f7',
    glyph: g(<><rect x="9" y="10" width="9" height="20" rx="2" fill={W} opacity="0.95" /><rect x="22" y="10" width="9" height="20" rx="2" fill={W} opacity="0.7" /></>),
  },
  {
    id: 'carmgr', label: 'Car manager', c1: '#2fd27f', c2: '#14b568',
    glyph: g(<><path d="M20 8 31 12v8c0 6-5 10-11 12-6-2-11-6-11-12v-8z" fill={W} /><rect x="14" y="17" width="12" height="7" rx="2" fill="#14b568" /></>),
  },
  {
    id: 'sound', label: 'Outside sound', c1: '#ee3a8c', c2: '#c0267a',
    glyph: g(<><rect x="9" y="17" width="3.500" height="8" rx="1.500" fill={W} /><rect x="15" y="12" width="3.500" height="16" rx="1.500" fill={W} /><rect x="21" y="15" width="3.500" height="10" rx="1.500" fill={W} /><rect x="27" y="19" width="3.500" height="4" rx="1.500" fill={W} /></>),
  },
  {
    id: 'light', label: 'Light show', c1: '#2a2b33', c2: '#101116',
    glyph: g(<path d="M8 22c4-10 12-14 24-8-3 3-5 8-10 12-6 3-11 0-14-4z" fill="none" stroke="#ff7a59" strokeWidth="3" />),
  },
  {
    id: 'eq', label: 'Sound tuning', c1: '#343844', c2: '#1a1c24',
    glyph: g(<><path d="M12 9v22M20 9v22M28 9v22" stroke="#9aa0b4" strokeWidth="2" /><rect x="9" y="14" width="6" height="5" rx="1.500" fill={W} /><rect x="17" y="22" width="6" height="5" rx="1.500" fill={W} /><rect x="25" y="12" width="6" height="5" rx="1.500" fill={W} /></>),
  },
  {
    id: 'kids', label: 'Child care', c1: '#f05a45', c2: '#d83a2e',
    glyph: g(<><circle cx="20" cy="21" r="10" fill={W} /><circle cx="16.500" cy="20" r="1.500" fill="#d83a2e" /><circle cx="23.500" cy="20" r="1.500" fill="#d83a2e" /><path d="M16 25c2 2 6 2 8 0" fill="none" stroke="#d83a2e" strokeWidth="1.600" /></>),
  },
  {
    id: 'plus', label: 'Plus', c1: '#7a4a3a', c2: '#4b2c24',
    glyph: g(<><path d="M10 20 20 10l10 10v11H10z" fill="none" stroke={W} strokeWidth="2.400" /><path d="M24 26v6M21 29h6" stroke="#ffb454" strokeWidth="2.400" /></>),
  },
  {
    id: 'space', label: 'Space', c1: '#3ea0ff', c2: '#1e6ee0',
    glyph: g(<><path d="M6 28 20 10l14 18z" fill={W} opacity="0.95" /><path d="M13 28 20 18l7 10z" fill="#8fc4ff" /></>),
  },
  { id: 'ai', label: 'AI create', c1: '#4d6bff', c2: '#a24dff', glyph: g(text('Ai', 19, 27)) },
  {
    id: 'view', label: 'Zeekr view', c1: '#3b82ff', c2: '#1d5fe0',
    glyph: g(<><rect x="14" y="8" width="12" height="24" rx="5" fill={W} /><circle cx="20" cy="26" r="2.200" fill="#1d5fe0" /></>),
  },
  {
    id: 'pod', label: 'Health pod', c1: '#a9adb8', c2: '#8d92a0',
    glyph: g(<circle cx="20" cy="20" r="10" fill="none" stroke={W} strokeWidth="3.600" />),
  },
  {
    id: 'phone', label: 'Phone', c1: '#27c4c0', c2: '#11a5a5',
    glyph: g(<path d="M11 13c0 9 7 16 16 16l3-4-5-3-3 2c-3-1-6-4-7-7l2-3-3-5z" fill={W} />),
  },
  {
    id: 'btm', label: 'Bluetooth music', c1: '#3b82ff', c2: '#1d5fe0',
    glyph: g(<path d="M14 14l12 12-6 5V9l6 5-12 12" fill="none" stroke={W} strokeWidth="2.600" strokeLinejoin="round" />),
  },
  {
    id: 'ktv', label: 'Karaoke', c1: '#232329', c2: '#101013',
    glyph: g(<><circle cx="18" cy="17" r="5.500" fill="#ffd25a" /><path d="M22 21 31 31" stroke="#ffd25a" strokeWidth="3.400" strokeLinecap="round" /></>),
  },
  {
    id: 'clean', label: 'Tidy up', c1: '#ffb324', c2: '#f0532c',
    glyph: g(<><rect x="16" y="8" width="8" height="8" rx="2" fill={W} /><path d="M11 18h18v10c0 3-2 5-5 5h-8c-3 0-5-2-5-5z" fill={W} opacity="0.95" /></>),
  },
  { id: 'food', label: 'Food', c1: '#ffd53a', c2: '#f2b900', glyph: g(text('Eat', 13, 25)) },
  {
    id: 'qq', label: 'Music', c1: '#ffe14a', c2: '#e9c200',
    glyph: g(<><circle cx="20" cy="20" r="12" fill="#2bc274" /><path d="M16 14l8 4-3 9" fill="none" stroke="#ffe14a" strokeWidth="3.200" strokeLinecap="round" /></>),
  },
  {
    id: 'cast', label: 'Screen cast', c1: '#35a9ff', c2: '#1d7fe0',
    glyph: g(<><rect x="8" y="10" width="24" height="16" rx="2.500" fill={W} /><path d="M15 31h10" stroke={W} strokeWidth="2.600" strokeLinecap="round" /></>),
  },
  {
    id: 'gallery', label: 'Gallery', c1: '#4cb8ff', c2: '#1f8ae0',
    glyph: g(<><rect x="8" y="9" width="24" height="22" rx="3" fill={W} opacity="0.95" /><path d="M10 28 18 18l5 6 4-4 5 8z" fill="#4cb8ff" /></>),
  },
];

const RECENT = ['kids', 'qq', 'iqiyi', 'scene'];

function Tile({ app, onClick }: { app: App; onClick: () => void }) {
  const t = useZk();
  return (
    <button type="button" onClick={onClick} className="flex flex-col items-center gap-[7px] focus:outline-none" style={{ width: 120 }}>
      <span
        className="grid h-[68px] w-[68px] place-items-center overflow-hidden rounded-[16px]"
        style={{ background: `linear-gradient(145deg, ${app.c1}, ${app.c2})`, boxShadow: '0 3px 10px rgba(30,30,70,0.18)' }}
      >
        {app.glyph}
      </span>
      <span className="text-[14px] leading-none" style={{ color: t.text2 }}>
        {app.label}
      </span>
    </button>
  );
}

export function AppCentre() {
  const t = useZk();
  const { notify } = useZkLocal();
  const byId = (id: string) => APPS.find((a) => a.id === id)!;
  const cols = 7;
  return (
    <div className="absolute inset-0">
      <span className="absolute text-[18px]" style={{ left: 52, top: 30, color: t.text2 }}>
        Recent
      </span>
      <span className="absolute text-[18px]" style={{ left: 232, top: 30, color: t.text2 }}>
        App Centre
      </span>
      <span className="absolute" style={{ left: 190, top: 60, bottom: 40, width: 1, background: t.line }} aria-hidden />
      {RECENT.map((id, i) => (
        <div key={id} className="absolute" style={{ left: 65 - 60 + 22, top: 74 + i * 92 }}>
          <Tile app={byId(id)} onClick={() => notify(`${byId(id).label} (showroom demo)`)} />
        </div>
      ))}
      {APPS.map((a, i) => {
        const col = i % cols;
        const row = Math.floor(i / cols);
        return (
          <div key={a.id} className="absolute" style={{ left: 210 + col * 150, top: 56 + row * 114 }}>
            <Tile app={a} onClick={() => notify(`${a.label} (showroom demo)`)} />
          </div>
        );
      })}
      <span className="absolute left-1/2 h-[3px] w-[16px] -translate-x-1/2 rounded-full" style={{ bottom: 18, background: t.accent }} aria-hidden />
    </div>
  );
}
