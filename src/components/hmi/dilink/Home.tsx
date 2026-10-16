'use client';

import React from 'react';
import type { Vehicle } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { DL } from './theme';
import * as Ic from './icons';
import { useDl } from './shared';

/**
 * DiLink's home (c10_0030, c10_0067): a bright showroom stage, a pale-blue sky over curved white
 * walls and a glossy floor, the car standing on it, and a row of cards along the bottom: the e³
 * platform's page, the car's status, the music player, the seats, the ambient light and the phone.
 * The car is the build's own render (public/hmi/<slug>/car34.webp); the stage is drawn here.
 */
export function Stage() {
  return (
    <svg className="absolute inset-0" viewBox="0 0 1280 800" preserveAspectRatio="xMidYMid slice" aria-hidden width="1280" height="800">
      <defs>
        <linearGradient id="dlSky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#5f9be8" />
          <stop offset="0.45" stopColor="#9cc4f2" />
          <stop offset="1" stopColor="#dbeafc" />
        </linearGradient>
        <linearGradient id="dlWall" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#f6f9ff" />
          <stop offset="1" stopColor="#cfdcf2" />
        </linearGradient>
        <linearGradient id="dlFloor" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#c6d6f2" />
          <stop offset="0.5" stopColor="#a9c0ec" />
          <stop offset="1" stopColor="#7f9fe0" />
        </linearGradient>
        <radialGradient id="dlGlow" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0" stopColor="#ffffff" stopOpacity="0.65" />
          <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
        </radialGradient>
      </defs>
      <rect width="1280" height="800" fill="url(#dlSky)" />
      {/* the curved white walls: three nested bands round the stage */}
      <path d="M-60 470C120 250 420 160 640 160S1160 250 1340 470V560H-60Z" fill="url(#dlWall)" opacity="0.92" />
      <path d="M-60 500C140 300 430 215 640 215S1140 300 1340 500V560H-60Z" fill="#fff" opacity="0.55" />
      <path d="M-60 530C160 350 440 275 640 275S1120 350 1340 530V560H-60Z" fill="#e7effc" opacity="0.8" />
      <g stroke="#9db6dd" strokeWidth="1.200" opacity="0.5" fill="none">
        <path d="M-60 470C120 250 420 160 640 160S1160 250 1340 470" />
        <path d="M-60 500C140 300 430 215 640 215S1140 300 1340 500" />
        <path d="M-60 530C160 350 440 275 640 275S1120 350 1340 530" />
      </g>
      {/* the floor: glossy, with the stage's rings */}
      <path d="M-60 540C300 500 980 500 1340 540V800H-60Z" fill="url(#dlFloor)" />
      <ellipse cx="640" cy="590" rx="520" ry="78" fill="none" stroke="#fff" strokeWidth="2" opacity="0.55" />
      <ellipse cx="640" cy="590" rx="400" ry="58" fill="none" stroke="#fff" strokeWidth="1.500" opacity="0.4" />
      <ellipse cx="640" cy="585" rx="470" ry="70" fill="url(#dlGlow)" />
    </svg>
  );
}

function Card({
  x, w, children, onClick, label,
}: {
  x: number;
  w: number;
  children: React.ReactNode;
  onClick?: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      onClick={onClick}
      className="absolute flex items-center justify-between overflow-hidden rounded-[8px] px-[14px] text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
      style={{
        left: x,
        top: 662,
        width: w,
        height: 76,
        background: 'rgba(250,252,255,0.78)',
        color: '#1b2a48',
        backdropFilter: 'blur(10px)',
        WebkitBackdropFilter: 'blur(10px)',
        boxShadow: '0 4px 14px rgba(40,70,130,0.16)',
      }}
    >
      {children}
    </button>
  );
}

export function HomeScene({ vehicle, hidden = false }: { vehicle: Vehicle; hidden?: boolean }) {
  const { notify } = useDl();
  const { media, patchMedia, ambientOn, setAmbient, setHmiScreen, locked, setLocked } = useVehicleStore();
  const hasChassis = (vehicle.tech ?? []).some((d) => d.driver === 'crab' || d.driver === 'compass' || d.driver === 'e3park');
  const TRACKS = ['AI Music Network', 'Night Drive', 'Long Exposure', 'Dust & Voltage'];

  return (
    <div className="absolute inset-0 overflow-hidden" style={{ visibility: hidden ? 'hidden' : 'visible' }}>
      <Stage />
      <div
        className="absolute"
        style={{ left: 250, top: 562, width: 780, height: 70, background: 'radial-gradient(ellipse at center, rgba(30,50,100,0.42), rgba(30,50,100,0) 70%)', filter: 'blur(6px)' }}
        aria-hidden
      />
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={`/hmi/${vehicle.slug}/car34.webp`}
        alt={`${vehicle.brand} ${vehicle.model}`}
        draggable={false}
        onError={(e) => {
          e.currentTarget.style.visibility = 'hidden';
        }}
        className="absolute select-none"
        style={{ left: 190, top: 262, width: 900, height: 'auto', filter: 'brightness(1.22) saturate(0.95)' }}
      />
      {/* the corner button of the stage */}
      <button
        type="button"
        aria-label="Vehicle status"
        onClick={() => setHmiScreen('controls')}
        className="absolute flex h-[40px] w-[40px] items-center justify-center rounded-[8px] focus:outline-none"
        style={{ left: 34, top: 606, background: 'rgba(250,252,255,0.8)', color: '#2a3a5c' }}
      >
        <Ic.CarSide size={22} />
      </button>

      {/* the cards */}
      <Card x={34} w={150} label="e³ platform" onClick={() => (hasChassis ? setHmiScreen('chassis') : notify('e³ platform (showroom demo)'))}>
        <span className="flex items-center gap-[8px]">
          <span
            className="flex h-[40px] w-[40px] items-center justify-center rounded-[10px] text-[19px] font-bold"
            style={{ background: 'linear-gradient(145deg,#e0243c,#a30f2a)', color: '#fff' }}
          >
            e³
          </span>
          <span className="text-[14px] leading-tight">e³<br />platform</span>
        </span>
      </Card>
      <Card x={196} w={196} label="Lock" onClick={() => setLocked(!locked)}>
        <span className="flex items-center gap-[10px]">
          <Ic.CarSide size={32} />
          <span className="text-[14px] leading-tight">{locked ? 'Locked' : 'Unlocked'}<br /><span style={{ color: '#5d6f93' }}>Tap to {locked ? 'unlock' : 'lock'}</span></span>
        </span>
        {locked ? <Ic.Lock size={22} /> : <Ic.Unlock size={22} />}
      </Card>
      <Card x={404} w={340} label="Music" onClick={() => setHmiScreen('media')}>
        <span className="flex min-w-0 items-center gap-[12px]">
          <span className="block h-[50px] w-[50px] shrink-0 rounded-[8px]" style={{ background: 'linear-gradient(140deg,#ff5f4d,#7a3df2)' }} />
          <span className="min-w-0">
            <span className="block truncate text-[15px] leading-tight">{TRACKS[media.trackIndex % TRACKS.length]}</span>
            <span className="block truncate text-[12px] leading-tight" style={{ color: '#5d6f93' }}>{media.playing ? 'Playing' : 'Paused'}</span>
          </span>
        </span>
        <span className="flex items-center gap-[12px]" onClick={(e) => e.stopPropagation()}>
          <span role="button" aria-label="Previous" onClick={() => patchMedia({ trackIndex: (media.trackIndex + 3) % 4 })}><Ic.Prev size={20} /></span>
          <span role="button" aria-label={media.playing ? 'Pause' : 'Play'} onClick={() => patchMedia({ playing: !media.playing })}>{media.playing ? <Ic.Pause size={24} /> : <Ic.Play size={24} />}</span>
          <span role="button" aria-label="Next" onClick={() => patchMedia({ trackIndex: (media.trackIndex + 1) % 4 })}><Ic.Next size={20} /></span>
        </span>
      </Card>
      <Card x={756} w={140} label="Seats" onClick={() => setHmiScreen('seats')}>
        <span className="flex items-center gap-[10px]"><Ic.SeatHeat size={28} /><span className="text-[14px] leading-tight">Seat<br />comfort</span></span>
      </Card>
      <Card
        x={908}
        w={140}
        label="Ambient light"
        onClick={() => {
          setAmbient({ ambientOn: !ambientOn });
          notify(ambientOn ? 'Ambient light off' : 'Ambient light on');
        }}
      >
        <span className="flex items-center gap-[10px]"><Ic.Bulb size={28} style={{ color: ambientOn ? DL.accent : undefined }} /><span className="text-[14px] leading-tight">Ambient<br />light</span></span>
      </Card>
      <Card x={1060} w={186} label="Phone" onClick={() => notify('Phone (showroom demo)')}>
        <span className="flex items-center gap-[10px]"><Ic.Phone size={28} /><span className="text-[14px] leading-tight">Phone<br /><span style={{ color: '#5d6f93' }}>Not connected</span></span></span>
      </Card>
    </div>
  );
}
