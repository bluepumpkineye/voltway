'use client';

import React from 'react';
import { useVehicleStore } from '@/store/vehicle-store';
import { TRACKS } from '../hyperos/shared';
import * as Ic from './icons';
import { AppIcon } from './appicons';
import { glass, GLASS_ON } from './theme';
import { Wallpaper, WALLPAPERS, useHaLocal, useNow, type WallpaperId } from './shared';

/** The wallpaper in force: the theme's own until the visitor switches it. */
export function useWallpaper(tone: 'dark' | 'light'): { id: WallpaperId; next: () => void; prev: () => void } {
  const { val, setVal } = useHaLocal();
  const own = val.wallpaper;
  const idx = own < 0 ? (tone === 'dark' ? 0 : 1) : own;
  const go = (d: number) => setVal('wallpaper', (idx + d + WALLPAPERS.length) % WALLPAPERS.length);
  return { id: WALLPAPERS[idx].id, next: () => go(1), prev: () => go(-1) };
}

/**
 * The home desktop: a wallpaper, the clock, and a row of cards in two pages.
 * Layout is read off the photographs of the car's screen (1280 x 800 space): the
 * clock centred at y 227, the cards 196 high with their labels under them, four
 * 197 wide columns 43 apart.
 */
export function HomeDesktop({ tone }: { tone: 'dark' | 'light' }) {
  const [page, setPage] = React.useState(0);
  const drag = React.useRef<number | null>(null);
  const wp = useWallpaper(tone);

  const onDown = (e: React.PointerEvent) => {
    drag.current = e.clientX;
  };
  const onUp = (e: React.PointerEvent) => {
    if (drag.current === null) return;
    const d = e.clientX - drag.current;
    drag.current = null;
    if (d < -60) setPage(1);
    if (d > 60) setPage(0);
  };

  return (
    <div className="absolute inset-0 overflow-hidden" onPointerDown={onDown} onPointerUp={onUp} style={{ color: '#fff' }}>
      <Wallpaper id={wp.id} className="absolute inset-0 h-full w-full" />
      <div
        className="absolute inset-y-0 left-0 flex transition-transform duration-500 ease-out"
        style={{ width: 2560, transform: `translateX(${-1280 * page}px)` }}
      >
        <PageOne />
        <PageTwo wallpaper={wp} />
      </div>
      <div className="absolute left-1/2 z-10 flex -translate-x-1/2 items-center gap-2.5" style={{ top: 681 }}>
        {[0, 1].map((i) => (
          <button
            key={i}
            type="button"
            aria-label={`Page ${i + 1}`}
            aria-current={page === i}
            onClick={() => setPage(i)}
            className="flex h-6 items-center focus:outline-none"
          >
            <span
              className="block h-[8px] rounded-full transition-all"
              style={{ width: page === i ? 17 : 8, background: page === i ? 'rgba(255,255,255,0.92)' : 'rgba(255,255,255,0.42)' }}
            />
          </button>
        ))}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------- pieces */

const COL = [63, 543, 783, 1023];

function Card({
  x,
  y,
  w = 197,
  label,
  onClick,
  children,
  style,
  aria,
}: {
  x: number;
  y: number;
  w?: number;
  label: string;
  onClick?: () => void;
  children: React.ReactNode;
  style?: React.CSSProperties;
  aria?: string;
}) {
  return (
    <div className="absolute" style={{ left: x, top: y, width: w }}>
      <div
        role={onClick ? 'button' : undefined}
        tabIndex={onClick ? 0 : undefined}
        aria-label={aria}
        onClick={onClick}
        onKeyDown={(e) => onClick && (e.key === 'Enter' || e.key === ' ') && onClick()}
        className="relative overflow-hidden outline-none focus-visible:ring-2 focus-visible:ring-white/70"
        style={{ height: 196, borderRadius: 33, ...style }}
      >
        {children}
      </div>
      <div className="mt-[8px] text-center text-[17px] leading-none" style={{ color: 'rgba(255,255,255,0.92)', textShadow: '0 1px 6px rgba(0,0,0,0.35)' }}>
        {label}
      </div>
    </div>
  );
}

function Tile({
  icon,
  label,
  on,
  onClick,
  size = 83,
}: {
  icon: React.ReactNode;
  label: string;
  on?: boolean;
  onClick: () => void;
  size?: number;
}) {
  return (
    <button
      type="button"
      aria-pressed={on}
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
      className="flex flex-col items-center justify-center gap-[5px] rounded-[21px] outline-none transition-colors focus-visible:ring-2 focus-visible:ring-white/70"
      style={{
        width: size,
        height: size,
        background: on ? GLASS_ON : 'rgba(255,255,255,0.17)',
        color: on ? '#17181b' : '#fff',
        backdropFilter: 'blur(16px)',
      }}
    >
      {icon}
      <span className="text-[13px] leading-none">{label}</span>
    </button>
  );
}

/* ----------------------------------------------------------------- page one */

function PageOne() {
  const now = useNow();
  return (
    <div className="relative h-full shrink-0" style={{ width: 1280 }}>
      <div className="absolute inset-x-0 text-center" style={{ top: 143 }}>
        <div className="tnum font-bold leading-none" style={{ fontSize: 152, letterSpacing: '-0.01em', color: 'rgba(255,255,255,0.9)', textShadow: '0 4px 30px rgba(0,0,0,0.18)' }}>
          {now.hm || '--:--'}
        </div>
        <div className="mt-[8px] flex items-center justify-center gap-3 text-[21px]" style={{ letterSpacing: '0.12em', color: 'rgba(255,255,255,0.92)' }}>
          <span>{now.date}</span>
          <span style={{ opacity: 0.7 }}>|</span>
          <span>27°</span>
          <Ic.Cloud size={24} />
        </div>
      </div>
      <FlexCard />
      <ComfortCard x={COL[1]} y={393} />
      <MediaCard x={COL[2]} y={393} />
      <TipCard x={COL[3]} y={393} />
    </div>
  );
}

function FlexCard({ y = 393 }: { y?: number }) {
  const { openings, toggleOpening } = useVehicleStore();
  const { on, toggle, notify } = useHaLocal();
  return (
    <Card x={COL[0]} y={y} w={437} label="3D Flex Space" style={{ ...glass(0.2, 18), border: '1px solid rgba(255,255,255,0.14)' }}>
      {/* the car in its own little landscape */}
      <div
        className="absolute inset-y-0 left-0"
        style={{
          width: 250,
          background:
            'radial-gradient(ellipse at 40% 100%, rgba(255,255,255,0.35), transparent 60%), linear-gradient(180deg, rgba(120,150,210,0.55), rgba(40,50,90,0.55))',
        }}
      />
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/hmi/luxeed-rx/car34.webp" alt="" className="absolute" style={{ left: 8, bottom: 22, width: 232 }} draggable={false} />
      <div className="absolute grid grid-cols-2 gap-[12px]" style={{ left: 252, top: 14 }}>
        <Tile icon={<Ic.ChargePort size={30} />} label="Charge port" on={on.chargePort} onClick={() => { toggle('chargePort'); notify(on.chargePort ? 'Charge port closed' : 'Charge port open'); }} />
        <Tile icon={<Ic.WindowOpen size={30} />} label="Windows" on={on.windows} onClick={() => toggle('windows')} />
        <Tile icon={<Ic.TrunkRear size={30} />} label="Tailgate" on={openings.boot} onClick={() => toggleOpening('boot')} />
        <Tile icon={<Ic.MirrorFold size={30} />} label="Mirrors" on={on.mirrorFold} onClick={() => toggle('mirrorFold')} />
      </div>
    </Card>
  );
}

/** The driver's comfort card: heating, ventilation and back heating, three buttons. */
export function ComfortCard({ x, y, label = 'Driver comfort' }: { x: number; y: number; label?: string }) {
  return (
    <Card x={x} y={y} label={label} style={COMFORT_BG}>
      <ComfortBody />
    </Card>
  );
}

export const COMFORT_BG: React.CSSProperties = {
  background: 'linear-gradient(160deg,#4cc0cf,#2a8fa8 60%,#4aa6b8)',
  boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.18)',
};

/** The comfort card's contents, filling whatever box holds them (the desktop's 197 x 196, the Control Centre's 241 x 241). */
export function ComfortBody() {
  const { climate, patchClimate } = useVehicleStore();
  const { on, toggle } = useHaLocal();
  const heat = climate.seatHeatDriver;
  const state = heat ? `Heating ${heat}` : on.driverVent ? 'Ventilation on' : on.driverBack ? 'Back heating on' : 'Off';
  return (
    <>
      <div className="absolute left-[16px] top-[14px]">
        <div className="text-[19px] font-semibold leading-tight">Driver comfort</div>
        <div className="mt-[4px] text-[14px] opacity-80">{state}</div>
      </div>
      <svg className="absolute" style={{ right: 6, top: 8 }} width="104" height="120" viewBox="0 0 104 120" aria-hidden>
        <path d="M30 6c14-6 34-2 38 14l8 54H22z" fill="rgba(255,255,255,0.26)" />
        <path d="M22 74h54c8 0 12 5 12 12v10H16v-8c0-8 2-14 6-14z" fill="rgba(255,255,255,0.20)" />
      </svg>
      <div className="absolute inset-x-[12px] bottom-[12px] flex gap-[7px]">
        {[
          { id: 'heat', icon: <Ic.HeatUp size={28} />, active: heat > 0, fn: () => patchClimate({ seatHeatDriver: (heat + 1) % 4 }), label: 'Seat heating' },
          { id: 'vent', icon: <Ic.Fan size={26} />, active: on.driverVent, fn: () => toggle('driverVent'), label: 'Seat ventilation' },
          { id: 'back', icon: <Ic.HeatWave size={26} />, active: on.driverBack, fn: () => toggle('driverBack'), label: 'Back heating' },
        ].map((b) => (
          <button
            key={b.id}
            type="button"
            aria-label={b.label}
            aria-pressed={b.active}
            onClick={(e) => { e.stopPropagation(); b.fn(); }}
            className="flex h-[54px] flex-1 items-center justify-center rounded-[16px] outline-none focus-visible:ring-2 focus-visible:ring-white/70"
            style={{ background: b.active ? GLASS_ON : 'rgba(255,255,255,0.20)', color: b.active ? '#17181b' : '#fff' }}
          >
            {b.icon}
          </button>
        ))}
      </div>
    </>
  );
}

function MediaCard({ x, y }: { x: number; y: number }) {
  const { media, patchMedia, setHmiScreen } = useVehicleStore();
  const track = TRACKS[media.trackIndex % TRACKS.length];
  return (
    <Card x={x} y={y} label="Media centre" onClick={() => setHmiScreen('media')} aria="Open music" style={{ background: track.art }}>
      <div className="absolute inset-0" style={{ background: 'linear-gradient(180deg, rgba(0,0,0,0.0) 40%, rgba(0,0,0,0.55))' }} />
      <span
        className="absolute right-[14px] top-[12px] flex h-[30px] w-[30px] items-center justify-center rounded-[9px]"
        style={{ background: 'linear-gradient(160deg,#4aa6ff,#1b6ee0)' }}
        aria-hidden
      >
        <Ic.Music size={17} />
      </span>
      <div className="absolute left-[16px] right-[16px]" style={{ bottom: 62 }}>
        <div className="truncate text-[17px] font-medium leading-tight">{track.title}</div>
        <div className="truncate text-[13px] opacity-75">{track.artist}</div>
      </div>
      <div className="absolute inset-x-0 bottom-[12px] flex items-center justify-center gap-[22px]">
        <button type="button" aria-label="Previous" onClick={(e) => { e.stopPropagation(); patchMedia({ trackIndex: (media.trackIndex + TRACKS.length - 1) % TRACKS.length }); }} className="outline-none"><Ic.Prev size={26} /></button>
        <button type="button" aria-label={media.playing ? 'Pause' : 'Play'} onClick={(e) => { e.stopPropagation(); patchMedia({ playing: !media.playing }); }} className="outline-none">
          {media.playing ? <Ic.Pause size={30} /> : <Ic.Play size={30} />}
        </button>
        <button type="button" aria-label="Next" onClick={(e) => { e.stopPropagation(); patchMedia({ trackIndex: (media.trackIndex + 1) % TRACKS.length }); }} className="outline-none"><Ic.Next size={26} /></button>
      </div>
    </Card>
  );
}

function TipCard({ x, y }: { x: number; y: number }) {
  return (
    <Card x={x} y={y} label="Xiaoyi tips" style={{ ...glass(0.2, 20), background: 'linear-gradient(160deg, rgba(140,160,210,0.50), rgba(80,95,150,0.50))', border: '1px solid rgba(255,255,255,0.16)' }}>
      <div className="absolute left-[18px] top-[16px] text-[15px] opacity-90">Dongcheng</div>
      <span className="absolute right-[16px] top-[14px] opacity-90"><Ic.Cloud size={24} /></span>
      <div className="absolute left-[16px] top-[40px] flex items-start leading-none">
        <span className="tnum text-[54px] font-medium">27</span>
        <span className="mt-[6px] text-[22px]">°C</span>
      </div>
      <div className="absolute left-[18px] text-[15px] opacity-90" style={{ top: 118 }}>Cloudy · Air good</div>
      <div className="tnum absolute left-[18px] text-[15px] opacity-90" style={{ top: 144 }}>28°C / 22°C</div>
    </Card>
  );
}

/* ----------------------------------------------------------------- page two */

function PageTwo({ wallpaper }: { wallpaper: ReturnType<typeof useWallpaper> }) {
  const { on, toggle, notify } = useHaLocal();
  const { setAppCentreOpen } = useVehicleStore();
  const row1 = 154;
  const row2 = 395;
  return (
    <div className="relative h-full shrink-0" style={{ width: 1280 }}>
      {/* Super Desktop */}
      <Card x={COL[0]} y={row1} w={437} label="Super Desktop" onClick={() => notify('Super Desktop mirrors phone apps (showroom demo)')} style={{ background: '#0a0a0c', boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.06)' }}>
        <div className="absolute left-[18px] top-[16px]">
          <div className="text-[24px] font-semibold leading-tight">Super Desktop</div>
          <div className="mt-[6px] text-[15px] opacity-70">Use phone apps in the cockpit</div>
        </div>
        <svg className="absolute" style={{ right: 0, bottom: 0 }} width="260" height="150" viewBox="0 0 260 150" aria-hidden>
          {[
            { x: 70, y: 62, c: '#2f7bff' }, { x: 134, y: 28, c: '#31c47a' }, { x: 198, y: 62, c: '#ffffff' },
            { x: 102, y: 100, c: '#ffd23f' }, { x: 166, y: 96, c: '#ff4d3a' }, { x: 230, y: 120, c: '#3b3b44' },
          ].map((t, i) => (
            <g key={i} transform={`translate(${t.x} ${t.y}) skewY(-18) rotate(-6)`} opacity={0.95}>
              <rect x="-22" y="-16" width="44" height="32" rx="9" fill="#202026" />
              <rect x="-10" y="-7" width="20" height="14" rx="4" fill={t.c} />
            </g>
          ))}
        </svg>
      </Card>
      {/* Video */}
      <Card x={COL[1]} y={row1} label="Video" onClick={() => notify('Video playback is not part of the showroom demo')} style={{ background: 'linear-gradient(170deg,#ffe0ef,#d6c8ff 55%,#9fd8ff)' }}>
        <svg className="absolute inset-0" viewBox="0 0 197 196" aria-hidden>
          <rect x="20" y="70" width="96" height="44" rx="20" fill="#ff8fb6" />
          <rect x="62" y="96" width="106" height="52" rx="24" fill="#ffd24d" />
          <circle cx="40" cy="120" r="9" fill="#44475a" />
          <circle cx="132" cy="150" r="10" fill="#44475a" />
          <circle cx="58" cy="82" r="5" fill="#fff" />
          <circle cx="94" cy="108" r="5" fill="#fff" />
        </svg>
        <div className="absolute inset-x-0 bottom-0 h-[84px]" style={{ background: 'linear-gradient(180deg,transparent,rgba(0,0,0,0.6))' }} />
        <div className="absolute bottom-[14px] left-[14px]">
          <div className="text-[16px] leading-tight">You are watching</div>
          <div className="text-[13px] opacity-80">Rescue Team (demo)</div>
        </div>
        <span className="absolute bottom-[14px] right-[14px] flex h-[38px] w-[38px] items-center justify-center rounded-full bg-white/90 text-black"><Ic.Play size={18} /></span>
      </Card>
      {/* Apps */}
      <Card x={COL[2]} y={row1} label="Apps" onClick={() => setAppCentreOpen(true)} style={{ ...glass(0.26, 24), border: '1px solid rgba(255,255,255,0.18)' }}>
        <div className="absolute inset-[14px] grid grid-cols-3 gap-[10px]">
          {(['weather', 'music', 'connect', 'video', 'calendar', 'phone', 'camera', 'gallery', 'health'] as const).map((id) => (
            <AppIcon key={id} id={id} size={52} />
          ))}
        </div>
      </Card>
      {/* Wallpaper */}
      <Card x={COL[0]} y={row2} w={437} label="Wallpaper switch" style={{ boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.14)' }}>
        <Wallpaper id={wallpaper.id} className="absolute inset-0 h-full w-full" />
        <div className="absolute inset-0" style={{ background: 'linear-gradient(180deg,rgba(0,0,0,0.35),rgba(0,0,0,0) 45%,rgba(0,0,0,0.35))' }} />
        <div className="absolute left-[18px] top-[14px]">
          <div className="text-[19px] font-semibold">Wallpaper</div>
          <div className="text-[13px] opacity-75">Tap an arrow to switch</div>
        </div>
        <div className="absolute bottom-[16px] left-[18px] flex gap-[12px]">
          <button type="button" aria-label="Previous wallpaper" onClick={(e) => { e.stopPropagation(); wallpaper.prev(); }} className="flex h-[48px] w-[92px] items-center justify-center rounded-full outline-none focus-visible:ring-2 focus-visible:ring-white/70" style={{ background: 'rgba(255,255,255,0.22)', backdropFilter: 'blur(10px)' }}><Ic.ChevThin dir="l" size={24} /></button>
          <button type="button" aria-label="Next wallpaper" onClick={(e) => { e.stopPropagation(); wallpaper.next(); }} className="flex h-[48px] w-[92px] items-center justify-center rounded-full outline-none focus-visible:ring-2 focus-visible:ring-white/70" style={{ background: 'rgba(255,255,255,0.22)', backdropFilter: 'blur(10px)' }}><Ic.ChevThin dir="r" size={24} /></button>
        </div>
      </Card>
      {/* Nap mode */}
      <Card x={COL[1]} y={row2} w={437} label="Nap mode" style={{ background: 'linear-gradient(135deg,#2f6a72,#274e5e 55%,#39636c)', boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.14)' }}>
        <div className="absolute left-[20px] top-[16px]">
          <div className="text-[23px] font-semibold leading-tight">Nap mode</div>
          <div className="mt-[6px] text-[15px] opacity-75">Quiet rest and guided relaxation</div>
        </div>
        <span className="absolute right-[18px] top-[18px] opacity-80"><Ic.ChevThin dir="r" size={22} /></span>
        <button
          type="button"
          onClick={() => { toggle('nap'); notify(on.nap ? 'Nap mode off' : 'Nap mode on: seats recline, cabin lights dim (showroom demo)'); }}
          className="absolute bottom-[18px] left-[18px] flex h-[56px] items-center gap-3 rounded-full px-6 text-[19px] outline-none focus-visible:ring-2 focus-visible:ring-white/70"
          style={{ background: on.nap ? GLASS_ON : 'rgba(255,255,255,0.20)', color: on.nap ? '#17181b' : '#fff' }}
        >
          <Ic.Nap size={26} />
          {on.nap ? 'Stop' : 'Start'}
        </button>
      </Card>
    </div>
  );
}

