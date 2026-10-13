'use client';

import React from 'react';
import type { Vehicle } from '@/data/vehicles/schema';
import { useVehicleStore, type Opening } from '@/store/vehicle-store';
import { tapChargeFlap } from '@/lib/tech/actions';
import * as Ic from './icons';
import { useZkLocal } from './shared';

/**
 * ZEEKR OS's home screen: a 3D showroom scene (a curved white ribbon over a sunset wall, a pale
 * floor), the car standing in it with its closures as white chips (doors, bonnet, tailgate, the
 * charge flap, the mirrors), a rail of vehicle shortcuts down the left edge and a row of four
 * cards along the bottom (c10_0016). The car is the build's own render (public/hmi/<slug>/
 * car34.webp); the scene is drawn here.
 */
export function Scene() {
  return (
    <svg
      className="absolute inset-0"
      viewBox="0 0 1280 800"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden
      width="1280"
      height="800"
    >
      <defs>
        <linearGradient id="zkSky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#628ed5" />
          <stop offset="0.38" stopColor="#7ea8e9" />
          <stop offset="1" stopColor="#cfdcf5" />
        </linearGradient>
        <linearGradient id="zkRib" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#e9eefc" />
          <stop offset="0.55" stopColor="#d2daf2" />
          <stop offset="1" stopColor="#b9c1de" />
        </linearGradient>
        <linearGradient id="zkWall" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#8c8fb4" />
          <stop offset="0.28" stopColor="#a4a0b6" />
          <stop offset="0.7" stopColor="#bdb4bd" />
          <stop offset="1" stopColor="#dedada" />
        </linearGradient>
        <linearGradient id="zkWallSun" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#f2a547" stopOpacity="0" />
          <stop offset="0.55" stopColor="#e39b58" stopOpacity="0.28" />
          <stop offset="1" stopColor="#d9831f" stopOpacity="0.95" />
        </linearGradient>
        <linearGradient id="zkWallFade" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#fff" stopOpacity="0" />
          <stop offset="0.35" stopColor="#fff" stopOpacity="1" />
          <stop offset="1" stopColor="#fff" stopOpacity="1" />
        </linearGradient>
        <mask id="zkSunMask">
          <rect width="1280" height="800" fill="url(#zkWallFade)" />
        </mask>
        <linearGradient id="zkFloor" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#d3d2d8" />
          <stop offset="0.3" stopColor="#d4d8e6" />
          <stop offset="0.7" stopColor="#bcc3da" />
          <stop offset="1" stopColor="#a5aecb" />
        </linearGradient>
        <radialGradient id="zkGlow" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0" stopColor="#ffffff" stopOpacity="0.5" />
          <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
        </radialGradient>
      </defs>
      <rect width="1280" height="800" fill="url(#zkFloor)" />
      {/* the sky, a curved white ribbon across it (dipping to the right), and the wall under the
          ribbon: grey-lavender on the left, a low orange sunset on the right */}
      <path d="M0 0H1280V150C900 135 380 100 0 76Z" fill="url(#zkSky)" />
      <path d="M0 74C380 98 900 133 1280 148V182C900 168 380 140 0 116Z" fill="url(#zkRib)" />
      <path d="M0 116C380 140 900 168 1280 182" fill="none" stroke="#5c6290" strokeWidth="3" opacity="0.65" />
      <path d="M0 118C380 142 900 170 1280 182V320C900 294 380 250 0 222Z" fill="url(#zkWall)" />
      <path d="M0 118C380 142 900 170 1280 182V320C900 294 380 250 0 222Z" fill="url(#zkWallSun)" mask="url(#zkSunMask)" />
      {/* the floor, with the seams of its panels */}
      <path d="M0 222C380 250 900 294 1280 320V800H0Z" fill="url(#zkFloor)" />
      <g stroke="#fff" strokeWidth="1.600" opacity="0.4" fill="none">
        <path d="M0 360 L420 330 L1280 360" />
        <path d="M0 470 L520 390 L1280 470" />
        <path d="M0 640 L640 450 L1280 600" />
        <path d="M120 800 L560 410" />
        <path d="M660 800 L760 470" />
        <path d="M1180 800 L930 440" />
      </g>
      <ellipse cx="560" cy="560" rx="470" ry="60" fill="url(#zkGlow)" />
    </svg>
  );
}

/** The rail down the left edge: navigation, the camera, HUD, steering, seats, lights, more. */
function Rail() {
  const { notify } = useZkLocal();
  const { setHmiScreen, setHeadlights, headlightsOn } = useVehicleStore();
  const item = (y: number, label: string, node: React.ReactNode, onClick: () => void) => (
    <button
      type="button"
      key={label}
      aria-label={label}
      onClick={onClick}
      className="absolute flex -translate-x-1/2 -translate-y-1/2 items-center justify-center focus:outline-none"
      style={{ left: 40, top: y, width: 46, height: 46, color: '#15161a' }}
    >
      {node}
    </button>
  );
  return (
    <>
      {item(95, 'Navigation', <Ic.NavArrow size={38} />, () => setHmiScreen('nav'))}
      <button
        type="button"
        aria-label="Scan"
        onClick={() => notify('Scan (showroom demo)')}
        className="absolute flex -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-[8px] focus:outline-none"
        style={{ left: 150, top: 95, width: 40, height: 40, background: 'rgba(255,255,255,0.45)', color: '#15161a' }}
      >
        <Ic.Scan size={24} />
      </button>
      {item(167, 'Dashcam', <Ic.DashcamRail size={26} />, () => setHmiScreen('camera'))}
      {item(249, 'Head-up display', <Ic.Hud size={28} />, () => notify('HUD height (showroom demo)'))}
      {item(331, 'Steering and gear', <Ic.WheelP size={30} />, () => setHmiScreen('controls'))}
      {item(416, 'Seats', <Ic.SeatRail size={28} />, () => setHmiScreen('seats'))}
      {item(497, 'Lights', <Ic.Bulb size={28} />, () => setHeadlights(!headlightsOn))}
      {item(581, 'More', <Ic.Dots size={26} />, () => setHmiScreen('controls'))}
    </>
  );
}

/** A white chip on the car: a door, the bonnet, the tailgate ...; orange while it is open. */
function Chip({
  x, y, label, icon, active, onClick,
}: {
  x: number;
  y: number;
  label: string;
  icon: React.ReactNode;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={active}
      onClick={onClick}
      className="absolute flex -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-[8px] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
      style={{
        left: x,
        top: y,
        width: 42,
        height: 42,
        background: active ? '#ff5b24' : 'rgba(250,250,254,0.82)',
        color: active ? '#fff' : '#16171b',
        boxShadow: '0 2px 8px rgba(30,30,60,0.18)',
      }}
    >
      {icon}
    </button>
  );
}

function Card({
  x, label, art, onClick,
}: {
  x: number;
  label: string;
  art: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="absolute flex items-center justify-between rounded-[5px] px-[18px] text-left text-[16px] focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
      style={{
        left: x,
        top: 613,
        width: 246,
        height: 78,
        background: 'rgba(248,248,252,0.78)',
        color: '#15161a',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
      }}
    >
      <span>{label}</span>
      <span className="block h-[50px] w-[58px]">{art}</span>
    </button>
  );
}

const ARTS = {
  show: (
    <svg viewBox="0 0 58 50" width="58" height="50" aria-hidden>
      <rect x="6" y="8" width="46" height="34" rx="4" fill="#f2b7a0" />
      {[0, 1, 2, 3, 4, 5].map((i) => [0, 1, 2, 3, 4].map((j) => (
        <rect key={`${i}${j}`} x={9 + i * 7.4} y={11 + j * 6.4} width="6" height="5.200" rx="1" fill={(i + j) % 3 === 0 ? '#f6e6d8' : '#e9806a'} />
      )))}
    </svg>
  ),
  susp: (
    <svg viewBox="0 0 58 50" width="58" height="50" aria-hidden>
      <rect x="22" y="6" width="14" height="34" rx="7" fill="#dfe6f5" transform="rotate(35 29 25)" />
      <rect x="25" y="2" width="8" height="22" rx="4" fill="#f08b3c" transform="rotate(35 29 25)" />
      <rect x="25" y="26" width="8" height="18" rx="4" fill="#2b4f9e" transform="rotate(35 29 25)" />
    </svg>
  ),
  pod: (
    <svg viewBox="0 0 58 50" width="58" height="50" aria-hidden>
      <ellipse cx="29" cy="28" rx="23" ry="17" fill="#e6dccf" />
      <ellipse cx="29" cy="25" rx="14" ry="9" fill="#f6efe6" />
      <ellipse cx="22" cy="23" rx="6" ry="4" fill="#d8c9b8" />
    </svg>
  ),
  tent: (
    <svg viewBox="0 0 58 50" width="58" height="50" aria-hidden>
      <path d="M4 44 28 8l26 36z" fill="#f08b3c" />
      <path d="M28 8 14 44h14z" fill="#f4b04a" />
      <path d="M28 44 22 44 28 22 34 44z" fill="#fff4e2" />
    </svg>
  ),
};

export function HomeScene({ vehicle, hidden = false }: { vehicle: Vehicle; hidden?: boolean }) {
  const { notify, on, toggle } = useZkLocal();
  const { openings, toggleOpening, ambientOn, setAmbient, setHmiScreen } = useVehicleStore();
  const open = (id: Opening) => () => toggleOpening(id);

  return (
    <div className="absolute inset-0 overflow-hidden" style={{ visibility: hidden ? 'hidden' : 'visible' }}>
      <Scene />
      {/* the car, standing on its own shadow */}
      <div
        className="absolute"
        style={{ left: 230, top: 470, width: 740, height: 64, background: 'radial-gradient(ellipse at center, rgba(40,42,70,0.46), rgba(40,42,70,0) 70%)', filter: 'blur(5px)' }}
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
        // the studio rig renders the paint darker than the screen's own picture of the car
        style={{ left: 227, top: 204, width: 738, height: 'auto', filter: 'brightness(1.28) saturate(0.92)' }}
      />
      <Rail />
      <Chip x={248} y={324} label="Bonnet" icon={<Ic.HsFrunk size={26} />} active={openings.frunk} onClick={open('frunk')} />
      <Chip x={566} y={252} label="Mirrors" icon={<Ic.HsMirror size={26} />} active={on.mirrorsFold} onClick={() => toggle('mirrorsFold')} />
      <Chip x={618} y={190} label="Front door" icon={<Ic.HsDoor size={26} />} active={openings.doorFL} onClick={open('doorFL')} />
      <Chip x={752} y={204} label="Rear door" icon={<Ic.HsDoorRear size={26} />} active={openings.doorRL} onClick={open('doorRL')} />
      <Chip x={896} y={214} label="Tailgate" icon={<Ic.HsBoot size={26} />} active={openings.boot} onClick={open('boot')} />
      <Chip x={890} y={288} label="Charge flap" icon={<Ic.HsCharge size={24} />} active={openings.charge} onClick={tapChargeFlap} />

      <Card
        x={126}
        label="Light show"
        art={ARTS.show}
        onClick={() => {
          setAmbient({ ambientOn: !ambientOn });
          notify(ambientOn ? 'Light show off' : 'Light show on (ambient lighting)');
        }}
      />
      <Card
        x={382}
        label="Suspension"
        art={ARTS.susp}
        // the car's suspension control is on Settings > Quick settings (five heights, c10_0033)
        onClick={() => setHmiScreen('controls')}
      />
      <Card x={642} label="Health pod" art={ARTS.pod} onClick={() => setHmiScreen('seats')} />
      <Card x={905} label="Camping mode" art={ARTS.tent} onClick={() => notify('Camping mode (showroom demo)')} />
    </div>
  );
}
