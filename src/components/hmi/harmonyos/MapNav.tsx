'use client';

import React from 'react';
import { useVehicleStore } from '@/store/vehicle-store';
import * as Ic from './icons';
import { useHa, BAR_H } from './theme';
import { useHaLocal } from './shared';

/* ----------------------------------------------------------------------- map */

/** A small seeded generator, so the demo map is the same every time. */
function rng(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

const MAP_W = 2600;
const MAP_H = 1700;

/**
 * A made-up city, drawn: a river, parks, a ring road, a street grid with some
 * diagonals. The car's own maps are a licensed product; this one is invented and
 * says so.
 */
function CityMap({ dark }: { dark: boolean }) {
  const c = dark
    ? { land: '#12161a', water: '#0d2431', park: '#112a1c', minor: '#27322f', major: '#2fae6a', casing: '#0a0d10', text: '#8fa0a6' }
    : { land: '#ecebf0', water: '#c9ddf1', park: '#d3e9cf', minor: '#ffffff', major: '#ffffff', casing: '#d4d1da', text: '#6c6b78' };
  const parts = React.useMemo(() => {
    const r = rng(7);
    const roads: { d: string; w: number; big: boolean }[] = [];
    // the street grid, a little off true
    for (let i = 0; i <= 17; i++) {
      const x = 80 + i * 150 + (r() - 0.5) * 40;
      roads.push({ d: `M${x} 0 L${x + (r() - 0.5) * 120} ${MAP_H}`, w: i % 4 === 0 ? 9 : 4.5, big: i % 4 === 0 });
    }
    for (let j = 0; j <= 11; j++) {
      const y = 70 + j * 150 + (r() - 0.5) * 40;
      roads.push({ d: `M0 ${y} L${MAP_W} ${y + (r() - 0.5) * 120}`, w: j % 3 === 0 ? 9 : 4.5, big: j % 3 === 0 });
    }
    // diagonals and the ring
    roads.push({ d: `M0 300 C 700 520, 1500 900, ${MAP_W} 1500`, w: 11, big: true });
    roads.push({ d: `M300 ${MAP_H} C 800 1100, 1500 600, 2200 0`, w: 11, big: true });
    roads.push({ d: 'M1300 250 a 650 480 0 1 0 0.1 0 Z', w: 12, big: true });
    const blocks: { x: number; y: number; w: number; h: number }[] = [];
    for (let i = 0; i < 260; i++) blocks.push({ x: r() * MAP_W, y: r() * MAP_H, w: 30 + r() * 60, h: 24 + r() * 50 });
    return { roads, blocks };
  }, []);

  return (
    <svg width={MAP_W} height={MAP_H} viewBox={`0 0 ${MAP_W} ${MAP_H}`} aria-hidden>
      <rect width={MAP_W} height={MAP_H} fill={c.land} />
      {parts.blocks.map((b, i) => (
        <rect key={i} x={b.x} y={b.y} width={b.w} height={b.h} rx="4" fill={dark ? '#171c21' : '#e3e1e8'} />
      ))}
      <path d="M-50 1180 C 450 1050, 700 1350, 1250 1180 S 2000 700, 2700 820 L 2700 940 C 2050 840, 1650 1260, 1250 1330 S 400 1230, -50 1330 Z" fill={c.water} />
      {[[420, 380, 260, 170], [1750, 1280, 300, 190], [1900, 330, 240, 180], [650, 880, 200, 140]].map(([x, y, w, h], i) => (
        <rect key={i} x={x} y={y} width={w} height={h} rx="46" fill={c.park} />
      ))}
      {parts.roads.map((r, i) => (
        <path key={`c${i}`} d={r.d} fill="none" stroke={c.casing} strokeWidth={r.w + 3} strokeLinecap="round" />
      ))}
      {parts.roads.map((r, i) => (
        <path key={i} d={r.d} fill="none" stroke={r.big ? c.major : c.minor} strokeWidth={r.w} strokeLinecap="round" />
      ))}
      {[
        [520, 470, 'Central Park'], [1850, 420, 'North Gardens'], [760, 960, 'Old Town'], [1980, 1380, 'Harbour'],
        [1250, 1090, 'Riverside Avenue'], [300, 340, 'Ring Road'],
      ].map(([x, y, s]) => (
        <text key={String(s)} x={Number(x)} y={Number(y)} fontSize="30" fontWeight="500" fill={c.text} fontFamily="Inter, system-ui, sans-serif">{String(s)}</text>
      ))}
    </svg>
  );
}

/** Navigation: a draggable map, a destination search with home and work, a route. */
export function NavPage() {
  const t = useHa();
  const dark = t.tone === 'dark';
  const { notify } = useHaLocal();
  const [pan, setPan] = React.useState({ x: -760, y: -480 });
  const [zoom, setZoom] = React.useState(1);
  const drag = React.useRef<{ x: number; y: number; px: number; py: number } | null>(null);
  const [open, setOpen] = React.useState(false);
  const [route, setRoute] = React.useState<null | { to: string; km: number; min: number }>(null);

  const go = (to: string, km: number, min: number) => {
    setRoute({ to, km, min });
    setOpen(false);
  };
  const glassBg = dark ? 'rgba(30,34,38,0.86)' : 'rgba(255,255,255,0.86)';

  return (
    <div className="absolute inset-0 overflow-hidden" style={{ background: dark ? '#12161a' : '#ecebf0', color: t.text }}>
      <div
        className="absolute inset-0 cursor-grab touch-none active:cursor-grabbing"
        onPointerDown={(e) => {
          (e.target as Element).setPointerCapture?.(e.pointerId);
          drag.current = { x: e.clientX, y: e.clientY, px: pan.x, py: pan.y };
        }}
        onPointerMove={(e) => {
          const d = drag.current;
          if (!d) return;
          setPan({ x: d.px + (e.clientX - d.x), y: d.py + (e.clientY - d.y) });
        }}
        onPointerUp={() => (drag.current = null)}
        onPointerCancel={() => (drag.current = null)}
      >
        <div className="absolute" style={{ left: 0, top: 0, width: MAP_W, height: MAP_H, transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`, transformOrigin: '1300px 850px' }}>
          <CityMap dark={dark} />
          {route && (
            <svg className="absolute inset-0" width={MAP_W} height={MAP_H} aria-hidden>
              <path d="M1300 850 L1300 700 L1530 700 L1530 520 L1860 520" fill="none" stroke="#2c6bff" strokeWidth="16" strokeLinecap="round" strokeLinejoin="round" opacity="0.95" />
              <circle cx="1860" cy="520" r="20" fill="#ff4a3f" stroke="#fff" strokeWidth="5" />
            </svg>
          )}
        </div>
        {/* the car, fixed at the middle of the screen */}
        <svg className="pointer-events-none absolute" style={{ left: 640 - 26, top: 400 - 26 }} width="52" height="52" viewBox="0 0 52 52" aria-hidden>
          <circle cx="26" cy="26" r="24" fill="rgba(44,107,255,0.18)" />
          <path d="M26 6l14 36-14-8-14 8z" fill="#2c6bff" stroke="#fff" strokeWidth="3" strokeLinejoin="round" />
        </svg>
      </div>

      {/* search card */}
      <div className="absolute z-10 overflow-hidden rounded-[26px] backdrop-blur-xl" style={{ left: 34, top: 76, width: 370, background: glassBg, boxShadow: '0 10px 30px rgba(0,0,0,0.16)' }}>
        <button type="button" onClick={() => setOpen((o) => !o)} className="flex h-[66px] w-full items-center gap-3 px-5 text-left text-[20px] outline-none" style={{ color: t.text2 }}>
          <Ic.Search size={26} />
          Search destination
        </button>
        <div className="flex gap-6 px-5 pb-4 text-[15px]">
          <button type="button" onClick={() => go('Home', 5.4, 12)} className="flex items-center gap-2 outline-none"><span className="flex h-[30px] w-[30px] items-center justify-center rounded-full" style={{ background: '#ff9a3d', color: '#fff' }}><Ic.Pin size={17} /></span><span>Home<br /><span style={{ color: t.text3 }}>Tap to set</span></span></button>
          <button type="button" onClick={() => go('Work', 9.1, 21)} className="flex items-center gap-2 outline-none"><span className="flex h-[30px] w-[30px] items-center justify-center rounded-full" style={{ background: '#3d8bff', color: '#fff' }}><Ic.Pin size={17} /></span><span>Work<br /><span style={{ color: t.text3 }}>Tap to set</span></span></button>
        </div>
        {open && (
          <ul className="border-t px-2 py-2 text-[18px]" style={{ borderColor: t.line }}>
            {[['Nearest charging station', 2.1, 6], ['Central Park', 3.8, 9], ['North Station', 11.6, 24]].map(([n, km, min]) => (
              <li key={n as string}>
                <button type="button" onClick={() => go(n as string, km as number, min as number)} className="flex h-[52px] w-full items-center justify-between rounded-[14px] px-3 text-left outline-none">
                  {n}
                  <span className="tnum text-[15px]" style={{ color: t.text3 }}>{km} km</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* compass and zoom */}
      <div className="absolute z-10 flex flex-col items-center gap-3" style={{ right: 38, top: 76 }}>
        <button type="button" aria-label="Recentre north" onClick={() => setPan({ x: -760, y: -480 })} className="flex h-[58px] w-[58px] items-center justify-center rounded-full text-[19px] font-medium outline-none" style={{ background: glassBg }}>N</button>
        <div className="flex flex-col overflow-hidden rounded-[20px]" style={{ background: glassBg }}>
          <button type="button" aria-label="Zoom in" onClick={() => setZoom((z) => Math.min(1.8, z + 0.2))} className="flex h-[52px] w-[52px] items-center justify-center outline-none"><Ic.Plus size={24} /></button>
          <button type="button" aria-label="Zoom out" onClick={() => setZoom((z) => Math.max(0.6, z - 0.2))} className="flex h-[52px] w-[52px] items-center justify-center border-t outline-none" style={{ borderColor: t.line }}><Ic.Minus size={24} /></button>
        </div>
      </div>

      {/* shortcuts */}
      {!route ? (
        <div className="absolute z-10 flex items-center gap-1 rounded-[24px] px-3 py-2 backdrop-blur-xl" style={{ left: 34, bottom: BAR_H + 18, background: glassBg }}>
          {[['Settings', <Ic.MenuSystem key="a" size={26} />], ['Traffic', <Ic.MenuStatus key="b" size={26} />], ['Charging', <Ic.ChargePort key="c" size={26} />], ['More', <Ic.Apps key="d" size={24} />], ['Recentre', <Ic.Locate key="e" size={26} />]].map(([l, ic]) => (
            <button key={l as string} type="button" onClick={() => (l === 'Recentre' ? setPan({ x: -760, y: -480 }) : notify(`${l} is not part of the showroom demo`))} className="flex w-[84px] flex-col items-center gap-1 rounded-[16px] py-1 text-[13px] outline-none">
              {ic as React.ReactNode}
              {l as string}
            </button>
          ))}
        </div>
      ) : (
        <div className="absolute z-10 flex items-center gap-6 rounded-[28px] px-7 py-4 backdrop-blur-xl" style={{ left: 34, bottom: BAR_H + 18, width: 560, background: glassBg, boxShadow: '0 10px 30px rgba(0,0,0,0.18)' }}>
          <span className="flex h-[52px] w-[52px] items-center justify-center rounded-full text-white" style={{ background: '#2c6bff' }}><Ic.NavRing size={28} /></span>
          <div className="min-w-0 flex-1">
            <div className="truncate text-[22px] font-medium">To {route.to}</div>
            <div className="tnum text-[17px]" style={{ color: t.text2 }}>{route.km} km · {route.min} min</div>
          </div>
          <button type="button" onClick={() => setRoute(null)} className="h-[48px] rounded-full px-6 text-[18px] text-white outline-none" style={{ background: '#e8322d' }}>Exit</button>
        </div>
      )}
      <div className="absolute z-10 text-[11px]" style={{ right: 40, bottom: BAR_H + 8, color: t.text3 }}>Demo map, not to scale</div>
    </div>
  );
}

/* --------------------------------------------------------------- 360 camera */

const VIEWS = [
  { id: 'front', label: 'Front' },
  { id: 'rear', label: 'Rear' },
  { id: 'rearL', label: 'Left rear' },
  { id: 'rearR', label: 'Right rear' },
  { id: 'frontL', label: 'Left front' },
  { id: 'frontR', label: 'Right front' },
  { id: '3d', label: '3D view' },
] as const;

/** A camera feed, drawn: sky, a paved ground in perspective with a painted bay. */
function Feed({ label, tilt = 0, sky = true }: { label: string; tilt?: number; sky?: boolean }) {
  const uid = React.useId().replace(/:/g, '');
  return (
    <svg className="absolute inset-0 h-full w-full" viewBox="0 0 600 340" preserveAspectRatio="xMidYMid slice" aria-label={label}>
      <defs>
        <linearGradient id={`${uid}a`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#9fb7d4" /><stop offset="1" stopColor="#dfe6ee" /></linearGradient>
        <linearGradient id={`${uid}g`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#8b8e93" /><stop offset="1" stopColor="#5c5f65" /></linearGradient>
      </defs>
      {sky && <rect width="600" height="130" fill={`url(#${uid}a)`} />}
      <path d="M0 130 L600 130 L600 340 L0 340 Z" fill={`url(#${uid}g)`} />
      <g transform={`rotate(${tilt} 300 340)`} stroke="#f4f2e8" strokeWidth="5" fill="none" opacity="0.9">
        <path d="M250 130 L90 340M350 130 L510 340M300 130 L300 340" />
        <path d="M232 190 L368 190M205 250 L395 250" strokeWidth="4" />
      </g>
      <path d="M0 340 Q300 290 600 340" fill="#2a2c31" opacity="0.8" />
    </svg>
  );
}

/** The 360-degree camera: the car from above, a camera selector and the feeds. */
export function CameraPage() {
  const t = useHa();
  const { slug } = useHaLocal();
  const dark = t.tone === 'dark';
  const { setHmiScreen } = useVehicleStore();
  const [view, setView] = React.useState<(typeof VIEWS)[number]['id']>('front');
  const [wheel, setWheel] = React.useState<'front' | 'rear'>('front');
  const label = VIEWS.find((v) => v.id === view)!.label;

  return (
    <div className="absolute inset-0 overflow-hidden" style={{ background: dark ? '#0b0c0f' : '#e9e7ea', color: t.text }}>
      {/* the car from above on its ground */}
      <div className="absolute overflow-hidden rounded-[30px]" style={{ left: 22, top: 24, width: 548, height: 690, background: 'repeating-linear-gradient(0deg,#9a9ca2 0 46px,#8e9096 46px 48px), repeating-linear-gradient(90deg,transparent 0 46px,rgba(0,0,0,0.12) 46px 48px)' }}>
        <div className="absolute inset-0" style={{ background: 'radial-gradient(ellipse at 50% 50%, transparent 40%, rgba(0,0,0,0.35))' }} />
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={`/hmi/${slug}/car-top.webp`} alt="" draggable={false} className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2" style={{ height: 600 }} />
        <button type="button" className="absolute left-[16px] top-[16px] flex h-[72px] w-[62px] flex-col items-center justify-center gap-1 rounded-[18px] bg-black/60 text-[13px] text-white outline-none" onClick={() => setHmiScreen('park')} aria-label="Parking assist"><Ic.MenuAssist size={24} />Park</button>
        <button type="button" className="absolute left-[16px] top-[98px] flex h-[72px] w-[62px] flex-col items-center justify-center gap-1 rounded-[18px] bg-black/60 text-[13px] text-white outline-none" aria-label="Reverse"><Ic.Recirc size={24} />Reverse</button>
      </div>

      {/* camera selector */}
      <div className="absolute flex flex-col gap-[10px]" style={{ left: 586, top: 24 }}>
        {VIEWS.map((v) => {
          const a = v.id === view;
          return (
            <button key={v.id} type="button" aria-pressed={a} onClick={() => setView(v.id)} className="flex h-[82px] w-[64px] flex-col items-center justify-center gap-1 rounded-[18px] text-[12px] outline-none" style={{ background: a ? t.blue : dark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.55)', color: '#fff' }}>
              {v.id === '3d' ? <Ic.Apps size={22} /> : <Ic.Camera size={22} />}
              {v.label.replace(' view', '')}
            </button>
          );
        })}
      </div>

      {/* the feeds */}
      <div className="absolute overflow-hidden rounded-[26px]" style={{ left: 664, top: 24, width: 594, height: 390 }}>
        <Feed label={`${label} camera`} tilt={view === 'rear' ? 180 : 0} />
        <span className="absolute left-[24px] top-[18px] rounded-full bg-black/45 px-4 py-1.5 text-[18px] text-white">{label}</span>
        <span className="absolute left-[170px] top-[16px] rounded-full bg-black/55 px-4 py-2 text-[15px] text-white">You can say anything</span>
      </div>
      <div className="absolute flex gap-[8px]" style={{ left: 664, top: 428, width: 594, height: 286 }}>
        <div className="relative flex-1 overflow-hidden rounded-[22px]"><Feed label="Left wheel" tilt={-8} sky={false} /></div>
        <div className="flex w-[82px] shrink-0 flex-col items-center justify-center gap-2 rounded-[22px] bg-black/55 text-[14px] text-white">
          {(['front', 'rear'] as const).map((w) => (
            <button key={w} type="button" onClick={() => setWheel(w)} aria-pressed={wheel === w} className="rounded-full px-3 py-2 outline-none" style={{ background: wheel === w ? t.blue : 'transparent' }}>
              {w === 'front' ? 'Front wheels' : 'Rear wheels'}
            </button>
          ))}
        </div>
        <div className="relative flex-1 overflow-hidden rounded-[22px]"><Feed label="Right wheel" tilt={8} sky={false} /></div>
      </div>
    </div>
  );
}
