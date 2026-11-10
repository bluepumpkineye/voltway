'use client';

import React from 'react';
import { useVehicleStore } from '@/store/vehicle-store';
import * as Ha from '../harmonyos/icons';
import { useHaLocal } from '../harmonyos/shared';
import * as Ic from './icons';
import { glass } from './theme';

const TRACKS = ['Nothing is playing', 'Night Drive · Long Exposure', 'Dust & Voltage · Cold Harbour', 'Neon Arterial · Hong Kong Sunset'];

/**
 * The home wallpaper, drawn here (the car's own is a photograph we do not ship): a pale blue moon over a
 * dusk sea with a stripe of orange at the horizon, three dolphins leaping and a dark islet (s_0023).
 */
export function Wallpaper({ className }: { className?: string }) {
  const uid = React.useId().replace(/:/g, '');
  return (
    <svg className={className ?? 'absolute inset-0'} viewBox="0 0 1280 800" preserveAspectRatio="xMidYMid slice" width="1280" height="800" aria-hidden>
      <defs>
        <linearGradient id={`${uid}s`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#3b72b4" />
          <stop offset="0.3" stopColor="#6fa5cf" />
          <stop offset="0.52" stopColor="#bcd4e4" />
          <stop offset="0.6" stopColor="#f5b678" />
          <stop offset="0.64" stopColor="#ee7a3c" />
          <stop offset="0.66" stopColor="#5b7ea6" />
        </linearGradient>
        <linearGradient id={`${uid}w`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#7ea7c8" />
          <stop offset="0.4" stopColor="#4d7ba3" />
          <stop offset="1" stopColor="#1f456d" />
        </linearGradient>
        <radialGradient id={`${uid}m`} cx="0.42" cy="0.38" r="0.7">
          <stop offset="0" stopColor="#e6f3f7" />
          <stop offset="0.6" stopColor="#b6d4e3" />
          <stop offset="1" stopColor="#7fa9c4" />
        </radialGradient>
        <filter id={`${uid}b`}><feGaussianBlur stdDeviation="9" /></filter>
        <filter id={`${uid}c`}><feGaussianBlur stdDeviation="2.5" /></filter>
      </defs>
      <rect width="1280" height="800" fill={`url(#${uid}s)`} />
      {/* the moon, huge, and its craters */}
      <circle cx="520" cy="300" r="330" fill={`url(#${uid}m)`} />
      <g filter={`url(#${uid}b)`} opacity="0.55" fill="#7fa4c0">
        <circle cx="430" cy="250" r="64" />
        <circle cx="640" cy="200" r="46" />
        <circle cx="520" cy="420" r="80" />
        <circle cx="720" cy="360" r="54" />
        <circle cx="360" cy="380" r="40" />
      </g>
      {/* the sea, its sky-glow and the moon's reflection */}
      <rect y="515" width="1280" height="285" fill={`url(#${uid}w)`} />
      <rect y="508" width="1280" height="14" fill="#f08a4a" opacity="0.85" filter={`url(#${uid}c)`} />
      <g filter={`url(#${uid}c)`} opacity="0.5" fill="#cfe3ee">
        <rect x="360" y="560" width="420" height="8" />
        <rect x="420" y="600" width="300" height="6" />
        <rect x="470" y="640" width="200" height="5" />
      </g>
      {/* the islet */}
      <path d="M560 520c24-18 70-22 112-8l24 8z" fill="#10233a" />
      {/* three dolphins leaping, each a curved body with a beak, a dorsal fin and a fluke */}
      {[
        { x: 760, y: 238, r: -18, k: 1.15 },
        { x: 905, y: 318, r: -32, k: 0.95 },
        { x: 690, y: 330, r: 12, k: 0.62 },
      ].map((d, i) => (
        <g key={i} transform={`translate(${d.x} ${d.y}) rotate(${d.r}) scale(${d.k})`} fill="#0f2236">
          <path d="M0 52C18 14 66 0 116 14c22 6 40 6 58-6-4 22-20 40-44 48C96 68 60 66 38 80c-14 8-30 6-38-8z" />
          <path d="M60 18c4-14 12-22 24-26-2 12-4 22-10 32z" />
          <path d="M0 52C-12 44-22 46-30 36c4 14 2 28-10 38 16-2 30-6 40-22z" />
        </g>
      ))}
      <rect width="1280" height="800" fill="#06101c" opacity="0.1" />
    </svg>
  );
}

/** One glass capsule of the row. */
function Capsule({ x, w, children, label }: { x: number; w: number; children: React.ReactNode; label: string }) {
  return (
    <div role="group" aria-label={label} className="absolute text-white" style={{ left: x, top: 580, width: w, height: 108, borderRadius: 54, ...glass(0.46, 18), boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.08)' }}>
      {children}
    </div>
  );
}

function Cap({ x, label, icon, sub, onClick }: { x: number; label: string; icon: React.ReactNode; sub?: string; onClick: () => void }) {
  return (
    <button type="button" aria-label={label} onClick={onClick} className="absolute top-1/2 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-[7px] outline-none focus-visible:ring-2 focus-visible:ring-white/70" style={{ left: x }}>
      {icon}
      <span className="text-[13px] leading-none">{label}</span>
      {sub && <span className="-mt-[2px] text-[11px] leading-none opacity-75">{sub}</span>}
    </button>
  );
}

/**
 * The home (s_0023, s_0040): the wallpaper under a row of glass capsules (navigation shortcuts, the music
 * player, the car's doors and boot, the phone) and two small buttons down the left. The capsules open what
 * they show and write the shared vehicle store (the lock, the boot, the media).
 */
export function HomeDesktop() {
  const { notify, setVal, slug } = useHaLocal();
  const { media, patchMedia, locked, setLocked, openings, toggleOpening, setHmiScreen } = useVehicleStore();
  return (
    <div className="absolute inset-0 overflow-hidden">
      <Wallpaper />
      {[{ y: 468, n: 'Favourites', i: <Ic.Star size={20} /> }, { y: 534, n: 'Home page', i: <Ic.Home size={20} /> }].map((b) => (
        <button key={b.n} type="button" aria-label={b.n} onClick={() => notify(`${b.n} is not part of the showroom demo`)} className="absolute flex h-[42px] w-[42px] items-center justify-center rounded-full text-white outline-none" style={{ left: 28, top: b.y, ...glass(0.4, 12) }}>
          {b.i}
        </button>
      ))}

      <Capsule x={27} w={250} label="Navigation shortcuts">
        <button type="button" aria-label="Navigation" onClick={() => setHmiScreen('nav')} className="absolute left-[34px] top-1/2 -translate-y-1/2 outline-none"><Ic.NavArrow size={38} style={{ color: '#aee0ff' }} /></button>
        <Cap x={128} label="Home" icon={<Ic.Home size={28} />} onClick={() => setHmiScreen('nav')} />
        <Cap x={202} label="Chargers" icon={<Ic.ChargeStation size={28} />} onClick={() => setHmiScreen('nav')} />
      </Capsule>

      <Capsule x={296} w={370} label="Music">
        <span className="absolute left-[16px] top-1/2 h-[56px] w-[56px] -translate-y-1/2 rounded-full" style={{ background: 'radial-gradient(circle at 35% 30%, #d9b9a8, #6a4a40 70%)', boxShadow: 'inset 0 0 0 1.5px rgba(255,255,255,0.3)' }} />
        <div className="absolute flex items-center gap-[30px]" style={{ left: 100, top: 24 }}>
          <button type="button" aria-label="Previous" onClick={() => patchMedia({ trackIndex: (media.trackIndex + 3) % 4 })} className="outline-none"><Ha.Prev size={22} /></button>
          <button type="button" aria-label={media.playing ? 'Pause' : 'Play'} onClick={() => patchMedia({ playing: !media.playing })} className="outline-none">{media.playing ? <Ha.Pause size={24} /> : <Ha.Play size={24} />}</button>
          <button type="button" aria-label="Next" onClick={() => patchMedia({ trackIndex: (media.trackIndex + 1) % 4 })} className="outline-none"><Ha.Next size={22} /></button>
          <Ha.Bluetooth size={18} style={{ opacity: 0.8 }} />
        </div>
        <span className="absolute w-[240px] truncate text-[12px] opacity-85" style={{ left: 100, bottom: 22 }}>{media.playing ? TRACKS[media.trackIndex % 4 || 1] : TRACKS[0]}</span>
      </Capsule>

      <Capsule x={692} w={252} label="Doors and boot">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={`/hmi/${slug}/car34.webp`} alt="" draggable={false} className="absolute left-[10px] top-[22px] w-[86px]" style={{ filter: 'brightness(1.25)' }} />
        <Cap x={140} label="Doors" sub={locked ? 'Locked' : 'Unlocked'} icon={locked ? <Ic.Lock size={28} /> : <Ic.Unlock size={28} />} onClick={() => { setLocked(!locked); }} />
        <Cap x={210} label="Boot" sub={openings.boot ? 'Open' : 'Closed'} icon={<Ic.Trunk size={28} />} onClick={() => toggleOpening('boot')} />
      </Capsule>

      <Capsule x={962} w={246} label="Phone">
        <span className="absolute left-[24px] top-1/2 flex h-[54px] w-[54px] -translate-y-1/2 items-center justify-center rounded-full" style={{ background: 'linear-gradient(160deg,#3ad08a,#0f9a58)' }}>
          <Ic.PhoneHandset size={28} />
        </span>
        <Cap x={140} label="Recent calls" icon={<Ic.Clock size={26} />} onClick={() => setVal('phone', 1)} />
        <Cap x={206} label="Missed" icon={<Ic.MissedCall size={26} />} onClick={() => setVal('phone', 1)} />
      </Capsule>
      <Capsule x={1228} w={120} label="More"><span /></Capsule>
    </div>
  );
}
