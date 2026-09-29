'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore, type Opening } from '@/store/vehicle-store';
import { effectiveRange } from '@/lib/performance';
import { cx } from '../ui';
import { HY } from './theme';
import * as Ic from './icons';
import { TRACKS, mmss, useClock } from './shared';

/* ---------------------------------------------------------------- parked */

type Hotspot = { id: string; label: string; x: number; y: number; opening?: Opening; lamps?: boolean };

/**
 * Points on the parked car image, in % of it: projected from the 3D car
 * through the render camera (blender/renders/hmi, carkit web capture notes).
 */
const HOTSPOTS: Hotspot[] = [
  { id: 'frunk', label: 'Frunk', x: 33.4, y: 29.0, opening: 'frunk' },
  { id: 'lamps', label: 'Headlights', x: 37.5, y: 46.1, lamps: true },
  { id: 'doorFL', label: 'Driver door', x: 63.8, y: 31.8, opening: 'doorFL' },
  { id: 'doorRL', label: 'Rear door', x: 71.7, y: 28.4, opening: 'doorRL' },
  { id: 'boot', label: 'Boot', x: 78.8, y: 13.6, opening: 'boot' },
];

/**
 * The parked desktop: HyperOS shows the car itself in a lit scene, the time
 * large at top left, and hotspots on the car that open what they sit on.
 * The image is this build's own render of the car.
 */
export function ParkedDesktop({ vehicle }: { vehicle: Vehicle }) {
  const { openings, toggleOpening, headlightsOn, setHeadlights } = useVehicleStore();
  const time = useClock();
  const [shown, setShown] = React.useState<string | null>(null);

  return (
    <div className="absolute inset-0 overflow-hidden">
      {/* sky, horizon glow, floor */}
      <div
        className="absolute inset-0"
        style={{
          background:
            'linear-gradient(180deg, #151a22 0%, #262d38 34%, #4a4f58 55%, #5a5a5e 58%, #34363b 62%, #1b1c1f 82%, #121315 100%)',
        }}
      />
      <div
        className="absolute left-1/2 top-[56%] h-[260px] w-[1100px] -translate-x-1/2 -translate-y-1/2 rounded-[50%]"
        style={{ background: 'radial-gradient(closest-side, rgba(255,236,190,0.16), transparent)' }}
      />

      {/* (this desktop runs under the status bar: offsets are from the screen top) */}
      <div className="absolute left-[44px] top-[70px] leading-none" style={{ color: HY.text }}>
        <div className="tnum text-[74px] font-extralight tracking-tight">{time.hm}</div>
        <div className="mt-2 text-[30px] font-light">{time.day}</div>
        <div className="tnum mt-1 text-[30px] font-light">{time.date}</div>
      </div>

      <div className="absolute left-[176px] top-[226px] w-[1040px]">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={`/hmi/${vehicle.slug}/parked.webp`}
          alt={`${vehicle.brand} ${vehicle.model}`}
          draggable={false}
          className="block w-full select-none"
        />
        {HOTSPOTS.map((h) => {
          const open = h.opening ? openings[h.opening] : h.lamps ? headlightsOn : false;
          return (
            <div key={h.id} className="absolute" style={{ left: `${h.x}%`, top: `${h.y}%` }}>
              <button
                type="button"
                aria-label={`${h.label}: ${open ? 'open' : 'closed'}`}
                aria-pressed={open}
                onClick={() => {
                  if (h.opening) toggleOpening(h.opening);
                  if (h.lamps) setHeadlights(!headlightsOn);
                  setShown(h.id);
                }}
                className="hy-hotspot absolute -left-[13px] -top-[13px] flex h-[26px] w-[26px] items-center justify-center rounded-full focus:outline-none"
              >
                <span
                  className="block h-[13px] w-[13px] rounded-full border-2"
                  style={{
                    borderColor: '#fff',
                    background: open ? HY.blue : 'rgba(20,22,26,0.55)',
                    boxShadow: '0 0 0 4px rgba(255,255,255,0.14)',
                  }}
                />
              </button>
              {shown === h.id && (
                <span
                  className="pointer-events-none absolute left-4 -top-[40px] whitespace-nowrap rounded-full px-3.5 py-1.5 text-[13px] font-medium"
                  style={{ background: 'rgba(24,26,30,0.86)', color: HY.text, backdropFilter: 'blur(8px)' }}
                >
                  {h.label} · {h.lamps ? (open ? 'On' : 'Off') : open ? 'Open' : 'Closed'}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* --------------------------------------------------------------- driving */

/**
 * The driving desktop: three cards side by side - assisted-driving view,
 * navigation, music - each with the grab handle of HyperOS' resizable cards.
 */
export function DrivingDesktop({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  return (
    <div className="absolute inset-0 grid grid-cols-[1fr_1.06fr_1fr] gap-3 px-4 pb-2 pt-1">
      <SrCard vehicle={vehicle} />
      <NavCard variant={variant} />
      <MusicCard />
    </div>
  );
}

export function DesktopCard({
  className,
  style,
  children,
}: {
  className?: string;
  style?: React.CSSProperties;
  children: React.ReactNode;
}) {
  return (
    <div className={cx('relative overflow-hidden rounded-[24px]', className)} style={{ background: HY.panel, ...style }}>
      <span className="absolute left-1/2 top-[7px] z-10 flex -translate-x-1/2 gap-[3px]" aria-hidden>
        {[0, 1, 2].map((i) => (
          <span key={i} className="h-[4px] w-[4px] rounded-full bg-white/35" />
        ))}
      </span>
      {children}
    </div>
  );
}

/** Xiaomi HAD's surround view: grey models on a light road, the car's own path. */
function SrCard({ vehicle }: { vehicle: Vehicle }) {
  const { adasActive, gear } = useVehicleStore();
  const moving = gear === 'D';
  const car = `/hmi/${vehicle.slug}/sr-ego.webp`;
  return (
    <DesktopCard style={{ background: 'linear-gradient(180deg, #f3f4f6 0%, #e3e6ea 45%, #cfd3d9 100%)' }}>
      <svg viewBox="0 0 400 660" className="absolute inset-0 h-full w-full" preserveAspectRatio="xMidYMid slice" aria-hidden>
        <defs>
          <linearGradient id="hy-road" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#e8eaee" />
            <stop offset="1" stopColor="#c9cdd3" />
          </linearGradient>
          <linearGradient id="hy-path" x1="0" y1="1" x2="0" y2="0">
            <stop offset="0" stopColor={HY.blue} stopOpacity="0.55" />
            <stop offset="1" stopColor={HY.blue} stopOpacity="0" />
          </linearGradient>
        </defs>
        {/* three lanes converging on the horizon */}
        <path d="M-120 660 L178 150 L222 150 L520 660Z" fill="url(#hy-road)" />
        <path d="M-120 660 L178 150" stroke="#fff" strokeWidth="5" />
        <path d="M520 660 L222 150" stroke="#fff" strokeWidth="5" />
        <path className={cx('hy-dash', moving && 'hy-dash-run')} d="M78 660 L193 150" stroke="#fff" strokeWidth="4" strokeDasharray="34 30" />
        <path className={cx('hy-dash', moving && 'hy-dash-run')} d="M322 660 L207 150" stroke="#fff" strokeWidth="4" strokeDasharray="34 30" />
        {adasActive && <path d="M150 600 L190 190 L210 190 L250 600Z" fill="url(#hy-path)" />}
      </svg>
      {/* traffic, then the car itself */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={car} alt="" draggable={false} className="absolute left-[18%] top-[31%] w-[16%] opacity-90" />
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={car} alt="" draggable={false} className="absolute left-[60%] top-[39%] w-[20%] opacity-90" />
      <span className="absolute bottom-[8%] left-1/2 h-[26px] w-[46%] -translate-x-1/2 rounded-[50%] bg-black/25 blur-md" />
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={car} alt="Your car" draggable={false} className="absolute bottom-[7%] left-1/2 w-[46%] -translate-x-1/2" />

      <div className="absolute left-5 top-6 flex items-center gap-3" style={{ color: '#15171a' }}>
        <span className="flex h-[40px] w-[40px] items-center justify-center rounded-full border-[4px] border-[#e5352b] bg-white text-[15px] font-bold">80</span>
        <span className="leading-none">
          <span className="tnum text-[40px] font-semibold">{moving ? 62 : 0}</span>
          <span className="ml-1 text-[13px] font-medium text-black/50">km/h</span>
        </span>
      </div>
      <span
        className="absolute right-5 top-7 rounded-full px-3 py-1 text-[12px] font-semibold"
        style={{ background: adasActive ? HY.blue : 'rgba(0,0,0,0.08)', color: adasActive ? '#fff' : 'rgba(0,0,0,0.45)' }}
      >
        {adasActive ? 'NOA on' : 'HAD ready'}
      </span>
    </DesktopCard>
  );
}

/** Route guidance on a dark map: to the Shanghai International Circuit. */
function NavCard({ variant }: { variant: Variant }) {
  const { setHmiScreen } = useVehicleStore();
  return (
    <DesktopCard>
      <MapArt className="absolute inset-0 h-full w-full" />
      <button
        type="button"
        onClick={() => setHmiScreen('nav')}
        aria-label="Open navigation"
        className="absolute inset-0 focus:outline-none"
      />
      <div className="pointer-events-none absolute left-3 right-3 top-5 rounded-[18px] px-5 py-4" style={{ background: 'rgba(22,24,28,0.92)' }}>
        <div className="flex items-center gap-3">
          <svg width="44" height="44" viewBox="0 0 24 24" aria-hidden>
            <path fill="none" stroke={HY.blue} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" d="M7 20v-7.5a3 3 0 0 1 3-3h8M14.5 6l3.5 3.5-3.5 3.5" />
          </svg>
          <span>
            <span className="tnum text-[34px] font-semibold leading-none" style={{ color: HY.text }}>800</span>
            <span className="ml-1 text-[15px]" style={{ color: HY.text2 }}>m</span>
            <span className="mt-1 block text-[15px]" style={{ color: HY.text }}>Longteng Avenue</span>
          </span>
        </div>
      </div>
      <div className="pointer-events-none absolute bottom-3 left-3 right-3 flex items-center justify-between rounded-[16px] px-4 py-3" style={{ background: 'rgba(22,24,28,0.92)' }}>
        <span className="flex items-center gap-1.5 text-[13px]" style={{ color: HY.text2 }}>
          <Ic.Exit size={18} /> Exit
        </span>
        <span className="tnum text-right text-[13px] leading-tight" style={{ color: HY.text }}>
          38 km · 44 min
          <span className="block text-[11.5px]" style={{ color: HY.text3 }}>Shanghai Int&apos;l Circuit</span>
        </span>
      </div>
      <span className="sr-only">{variant.name}</span>
    </DesktopCard>
  );
}

/**
 * The dark-theme map both navigation views draw on: the river, streets, the
 * route. Drawn for the box it fills (w x h), so the card and the full-screen
 * app are the same map at the same street scale, not one stretched.
 */
export function MapArt({
  className,
  ring,
  w = 420,
  h = 660,
}: {
  className?: string;
  ring?: number;
  w?: number;
  h?: number;
}) {
  const car = { x: w * 0.5, y: h * 0.82 };
  const route = [
    [car.x, car.y],
    [car.x + 4, h * 0.64],
    [car.x + 26, h * 0.55],
    [car.x + 52, h * 0.37],
    [car.x + 90, h * 0.23],
    [w + 30, h * 0.18],
  ]
    .map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)} ${y.toFixed(1)}`)
    .join(' ');
  const rows = Math.ceil((h * 0.5) / 36) + 1;
  const cols = Math.ceil(w / 58) + 2;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className={className} preserveAspectRatio="xMidYMid slice" role="img" aria-label="Map">
      <rect width={w} height={h} fill="#10161d" />
      {/* the Huangpu */}
      <path
        d={`M-40 ${h * 0.38} C ${w * 0.2} ${h * 0.35}, ${w * 0.36} ${h * 0.45}, ${w * 0.62} ${h * 0.42} S ${w} ${h * 0.27}, ${w + 60} ${h * 0.3} L ${w + 60} ${h * 0.39} C ${w * 0.95} ${h * 0.38}, ${w * 0.79} ${h * 0.5}, ${w * 0.6} ${h * 0.52} S ${w * 0.17} ${h * 0.45}, -40 ${h * 0.48}Z`}
        fill="#0d2334"
      />
      {/* blocks and streets south of the river */}
      {Array.from({ length: rows }).map((_, i) => (
        <path key={`h${i}`} d={`M-20 ${h * 0.58 + i * 36} L${w + 20} ${h * 0.55 + i * 36}`} stroke="#1c2530" strokeWidth={i % 3 === 0 ? 9 : 4} />
      ))}
      {Array.from({ length: cols }).map((_, i) => (
        <path key={`v${i}`} d={`M${-30 + i * 58} ${h + 20} L${i * 58} ${h * 0.55}`} stroke="#1c2530" strokeWidth={i % 3 === 1 ? 9 : 4} />
      ))}
      {/* and north of it */}
      {Array.from({ length: Math.ceil(w / 80) + 2 }).map((_, i) => (
        <path key={`n${i}`} d={`M${-10 + i * 80} ${h * 0.27} L${40 + i * 80} 0`} stroke="#1a222c" strokeWidth="4" />
      ))}
      <path d={`M-20 ${h * 0.21} L${w + 20} ${h * 0.17}`} stroke="#1c2530" strokeWidth="8" />
      {ring !== undefined && (
        <circle cx={car.x} cy={car.y} r={ring} fill={HY.green} fillOpacity="0.06" stroke={HY.green} strokeOpacity="0.45" strokeDasharray="6 7" strokeWidth="1.6" />
      )}
      {/* the route: up from the car, over the river, right toward the circuit */}
      <path d={route} fill="none" stroke="#0f7a3f" strokeWidth="15" strokeLinecap="round" strokeLinejoin="round" />
      <path d={route} fill="none" stroke={HY.green} strokeWidth="9" strokeLinecap="round" strokeLinejoin="round" />
      {/* the car */}
      <circle cx={car.x} cy={car.y} r="22" fill={HY.blue} fillOpacity="0.2" />
      <circle cx={car.x} cy={car.y} r="14" fill={HY.blue} stroke="#fff" strokeWidth="3" />
      <path d={`M${car.x} ${car.y - 9} L${car.x + 6} ${car.y + 6} L${car.x} ${car.y + 3} L${car.x - 6} ${car.y + 6}Z`} fill="#fff" />
    </svg>
  );
}

/** Now playing, tinted by the cover, as HyperOS tints its music card. */
function MusicCard() {
  const { media, patchMedia, setHmiScreen } = useVehicleStore();
  const track = TRACKS[media.trackIndex % TRACKS.length];
  const at = Math.round(track.duration * 0.38);
  return (
    <DesktopCard style={{ background: `linear-gradient(180deg, ${track.tint} 0%, #1f1a2b 55%, ${HY.panel} 100%)` }}>
      <div className="flex h-full flex-col px-6 pb-6 pt-7" style={{ color: HY.text }}>
        <button type="button" onClick={() => setHmiScreen('media')} className="flex items-center gap-2 text-[15px] focus:outline-none">
          <span className="flex h-[22px] w-[22px] items-center justify-center rounded-[6px]" style={{ background: 'linear-gradient(145deg,#ff5f6d,#c2185b)' }}>
            <svg width="13" height="13" viewBox="0 0 24 24" aria-hidden><path fill="#fff" d="M9 17.5V6.2l10-2.2v11.3a2.6 2.6 0 1 1-1.6-2.4V7.6L10.6 9v8.9A2.6 2.6 0 1 1 9 17.5Z" /></svg>
          </span>
          Music
          <Ic.ChevronDown size={18} className="ml-auto opacity-60" />
        </button>
        <div className="mx-auto mt-8 h-[228px] w-[228px] rounded-[20px] shadow-2xl" style={{ background: track.art }} />
        <div className="mt-7 text-center">
          <div className="truncate text-[21px] font-medium">{track.title}</div>
          <div className="mt-1 truncate text-[14px]" style={{ color: HY.text2 }}>{track.artist}</div>
        </div>
        <div className="mt-6">
          <div className="h-[4px] overflow-hidden rounded-full bg-white/15">
            <div className="h-full rounded-full bg-white/85" style={{ width: `${(at / track.duration) * 100}%` }} />
          </div>
          <div className="tnum mt-1.5 flex justify-between text-[11.5px]" style={{ color: HY.text3 }}>
            <span>{mmss(at)}</span>
            <span>{mmss(track.duration)}</span>
          </div>
        </div>
        <div className="mt-4 flex items-center justify-center gap-10">
          <button type="button" aria-label="Previous track" onClick={() => patchMedia({ trackIndex: (media.trackIndex + TRACKS.length - 1) % TRACKS.length })} className="focus:outline-none">
            <Ic.Prev size={26} />
          </button>
          <button type="button" aria-label={media.playing ? 'Pause' : 'Play'} onClick={() => patchMedia({ playing: !media.playing })} className="focus:outline-none">
            {media.playing ? <Ic.Pause size={38} /> : <Ic.Play size={38} />}
          </button>
          <button type="button" aria-label="Next track" onClick={() => patchMedia({ trackIndex: (media.trackIndex + 1) % TRACKS.length })} className="focus:outline-none">
            <Ic.Next size={26} />
          </button>
        </div>
        <div className="mt-auto flex justify-between px-2" style={{ color: HY.text2 }}>
          <Ic.ListIcon size={20} /><Ic.Heart size={20} /><Ic.Repeat size={20} /><Ic.Lyrics size={20} />
        </div>
      </div>
    </DesktopCard>
  );
}

export function useRangeKm(variant: Variant) {
  const { soc, driveMode, climate } = useVehicleStore();
  return effectiveRange(variant, driveMode, soc, climate);
}
