'use client';

import React from 'react';
import type { Vehicle } from '@/data/vehicles/schema';
import { ParkTopView } from '@/components/tech/ParkTopView';
import { RearView } from '@/components/tech/RearView';
import { pauseDemo, resetDemo, startDemo } from '@/lib/tech/actions';
import { useTechClock } from '@/lib/tech/clock';
import { parkPhase, parkProgress } from '@/lib/tech/phase';
import { usePreviewRuntime } from '@/lib/tech/preview';
import { useRuntime } from '@/lib/tech/session';
import { useVehicleStore } from '@/store/vehicle-store';
import * as Ic from './icons';
import { useHa } from './theme';
import { useHaLocal } from './shared';

/**
 * The car's parking page: the 360 view's top picture on the left, the rear camera on the right, and one
 * button between them, as the HarmonyOS cockpit lays out its parking assist (blender/reference/luxeed-rx/
 * tech, board T1): the page looks for a bay, offers it ("Rear-in is ready, tap Start"), and drives the
 * car in when told. Everything on it is the demo's state, read from the clock, so the car's screen, the
 * phone's app and the 3D scene always agree.
 *
 * Opened in the cabin (the Interior tab) it shows the lot and the car as they stand; "Start" takes the
 * visitor out to the stage, where the car parks.
 */
const DEMO = 'park';

export function ParkPage({ vehicle }: { vehicle: Vehicle }) {
  const t = useHa();
  const clock = useTechClock();
  const phase = parkPhase(clock);
  const progress = parkProgress(clock);
  const techAvailable = useVehicleStore((s) => s.techAvailable);
  const status = useVehicleStore((s) => s.techStatus);
  const setHmiScreen = useVehicleStore((s) => s.setHmiScreen);
  const live = useRuntime();
  const preview = usePreviewRuntime(vehicle, DEMO);
  const runtime = live ?? preview;
  const dark = t.tone === 'dark';

  // the page looks for a bay for a moment each time it opens, as the car's does
  const [looking, setLooking] = React.useState(true);
  React.useEffect(() => {
    const id = window.setTimeout(() => setLooking(false), 1500);
    return () => window.clearTimeout(id);
  }, []);
  const searching = looking && phase === 'ready';

  const moving = phase === 'parking' || phase === 'leaving';
  const paused = phase === 'paused-in' || phase === 'paused-out';
  const pct = Math.round(progress * 100);
  const canStart = techAvailable ? Boolean(runtime?.stage) && (live ? true : status !== 'none') : false;
  const go = () => startDemo(DEMO, 'dashboard');

  const search = runtime?.stage?.search;
  const isScanning = Boolean(search && phase === 'parking' && clock.t < search.found);
  const isBayFound = Boolean(search && phase === 'parking' && clock.t >= search.found && clock.t < search.end);

  const title = searching || isScanning
    ? 'Searching for a bay…'
    : isBayFound
      ? 'Target slot identified'
      : phase === 'ready'
        ? 'Rear-in is ready'
        : phase === 'parking'
          ? `Parking in… ${pct}%`
          : phase === 'leaving'
            ? `Parking out… ${pct}%`
            : paused
              ? 'Paused'
              : phase === 'parked'
                ? 'Parked'
                : 'Out of the bay';
  const sub = searching || isScanning
    ? 'Bays beside the car are being measured.'
    : isBayFound
      ? 'Target bay locked with flashing P mark.'
      : phase === 'ready'
        ? 'Tap Start parking in. Keep watching the car’s surroundings.'
        : moving
          ? 'The car is steering itself. Pause at any time.'
          : paused
            ? 'The car has stopped where it is.'
            : phase === 'parked'
              ? 'Tap Park out to drive out of the bay.'
              : 'Back where it started.';

  const panel = dark ? '#16181c' : '#f5f4f6';
  const btn = (primary: boolean, disabled = false): React.CSSProperties =>
    primary
      ? { background: t.blue, color: '#fff', opacity: disabled ? 0.4 : 1 }
      : { background: t.seg, color: t.text };

  return (
    <div className="absolute inset-0 overflow-hidden" style={{ background: dark ? '#0b0c0f' : '#e9e7ea', color: t.text }}>
      {/* the 360 view's picture: the car in its lot, from above */}
      <div className="absolute overflow-hidden rounded-[30px]" style={{ left: 22, top: 24, width: 548, height: 690, background: panel }}>
        <div className="absolute inset-x-0 top-[96px] bottom-[18px]">
          {runtime?.stage ? (
            <ParkTopView
              theme={dark ? 'dark' : 'light'}
              className="h-full w-full"
              preview={preview}
              selected={!searching}
              margin={0.5}
              sprite={{ src: `/hmi/${vehicle.slug}/car-top.webp`, aspect: 420 / 969 }}
            />
          ) : (
            <div className="grid h-full place-items-center px-10 text-center text-[20px] leading-snug" style={{ color: t.text2 }}>
              {techAvailable ? 'Loading the car…' : 'The car parks itself in the showroom.'}
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={() => setHmiScreen('camera')}
          aria-label="Back to the 360 camera"
          className="absolute left-[18px] top-[18px] flex h-[60px] items-center gap-3 rounded-full pl-[14px] pr-[26px] text-[20px] outline-none focus-visible:ring-2 focus-visible:ring-[#4a74ff]"
          style={{ background: t.seg }}
        >
          <span className="grid h-[34px] w-[34px] place-items-center rounded-full" style={{ background: t.blue, color: '#fff' }}>
            <Ic.ParkAssist size={22} />
          </span>
          Parking assist
        </button>
        {searching && <span className="absolute right-6 top-[40px] h-[16px] w-[16px] animate-ping rounded-full" style={{ background: t.blue }} aria-hidden />}
      </div>

      {/* the rear camera, and the page's one button */}
      <div className="absolute overflow-hidden rounded-[30px]" style={{ left: 586, top: 24, width: 672, height: 430 }}>
        <RearView runtime={runtime} className="h-full w-full" />
        <span className="absolute left-5 top-4 rounded-full bg-black/45 px-4 py-1.5 text-[17px] text-white">Rear view</span>
      </div>

      <div className="absolute flex flex-col justify-between rounded-[30px] p-[28px]" style={{ left: 586, top: 470, width: 672, height: 244, background: panel }}>
        <div>
          <div className="text-[30px] font-medium leading-tight">{title}</div>
          <div className="mt-1.5 text-[18px] leading-snug" style={{ color: t.text2 }}>{sub}</div>
          {(moving || paused) && (
            <div className="mt-3 h-[6px] overflow-hidden rounded-full" style={{ background: t.seg }}>
              <div className="h-full rounded-full" style={{ width: `${pct}%`, background: t.blue }} />
            </div>
          )}
        </div>
        <div className="flex items-center gap-[14px]">
          {!techAvailable ? (
            <a
              href={`/showroom/${vehicle.slug}?tab=tech&demo=${DEMO}`}
              className="flex h-[64px] flex-1 items-center justify-center rounded-full text-[22px] font-medium outline-none focus-visible:ring-2 focus-visible:ring-[#4a74ff]"
              style={btn(true)}
            >
              Watch it in the showroom
            </a>
          ) : (
            <>
              {phase === 'ready' && (
                <button type="button" disabled={searching || !canStart} onClick={go} className="h-[64px] flex-1 rounded-full text-[22px] font-medium outline-none focus-visible:ring-2 focus-visible:ring-[#4a74ff]" style={btn(true, searching || !canStart)}>
                  Start parking in
                </button>
              )}
              {moving && (
                <button type="button" onClick={pauseDemo} className="flex h-[64px] flex-1 items-center justify-center gap-3 rounded-full text-[22px] font-medium outline-none focus-visible:ring-2 focus-visible:ring-[#4a74ff]" style={btn(false)}>
                  <Ic.Pause size={24} /> Pause
                </button>
              )}
              {paused && (
                <>
                  <button type="button" onClick={resetDemo} className="h-[64px] w-[190px] rounded-full text-[21px] outline-none focus-visible:ring-2 focus-visible:ring-[#4a74ff]" style={btn(false)}>Start over</button>
                  <button type="button" onClick={go} className="flex h-[64px] flex-1 items-center justify-center gap-3 rounded-full text-[22px] font-medium outline-none focus-visible:ring-2 focus-visible:ring-[#4a74ff]" style={btn(true)}>
                    <Ic.Play size={24} /> Resume
                  </button>
                </>
              )}
              {phase === 'parked' && (
                <>
                  <button type="button" onClick={() => setHmiScreen('camera')} className="h-[64px] w-[190px] rounded-full text-[21px] outline-none focus-visible:ring-2 focus-visible:ring-[#4a74ff]" style={btn(false)}>Done</button>
                  <button type="button" onClick={go} className="h-[64px] flex-1 rounded-full text-[22px] font-medium outline-none focus-visible:ring-2 focus-visible:ring-[#4a74ff]" style={btn(true)}>Park out</button>
                </>
              )}
              {phase === 'done' && (
                <>
                  <button type="button" onClick={() => { resetDemo(); setHmiScreen('camera'); }} className="h-[64px] w-[190px] rounded-full text-[21px] outline-none focus-visible:ring-2 focus-visible:ring-[#4a74ff]" style={btn(false)}>Close</button>
                  <button type="button" onClick={resetDemo} className="h-[64px] flex-1 rounded-full text-[22px] font-medium outline-none focus-visible:ring-2 focus-visible:ring-[#4a74ff]" style={btn(true)}>Park again</button>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------- Settings > Parking assist */

/**
 * The dialog Settings > Assisted driving > Parking assist opens (board T1, tile 2): the switch for remote
 * parking assist, which the phone's app needs, and the parking speed. Both are the car's settings, in the
 * shared store, so the phone and the demo follow them.
 */
export function ParkAssistDialog({ onClose }: { onClose: () => void }) {
  const t = useHa();
  const rpa = useVehicleStore((s) => s.rpaEnabled);
  const speed = useVehicleStore((s) => s.parkSpeed);
  const setRpa = useVehicleStore((s) => s.setRpaEnabled);
  const setSpeed = useVehicleStore((s) => s.setParkSpeed);
  const speeds = [
    { id: 'slow', label: 'Slower' },
    { id: 'medium', label: 'Medium' },
    { id: 'fast', label: 'Faster' },
  ] as const;
  return (
    <div className="absolute inset-0 z-40" onClick={onClose}>
      <div className="absolute inset-0" style={{ background: 'rgba(0,0,0,0.32)' }} />
      <div
        role="dialog"
        aria-label="Parking assist"
        className="absolute"
        onClick={(e) => e.stopPropagation()}
        style={{ left: 150, top: 120, width: 980, height: 540, borderRadius: 40, background: t.panel, color: t.text, backdropFilter: 'blur(36px) saturate(1.3)', boxShadow: '0 30px 80px rgba(0,0,0,0.38)' }}
      >
        <button type="button" onClick={onClose} aria-label="Close" className="absolute left-[34px] top-[30px] grid h-[52px] w-[52px] place-items-center rounded-full outline-none focus-visible:ring-2 focus-visible:ring-[#4a74ff]" style={{ background: t.seg }}>
          <Ic.Close size={26} />
        </button>
        <h2 className="pt-[38px] text-center text-[28px] font-medium">Parking assist</h2>

        <div className="absolute flex items-center justify-between" style={{ left: 54, top: 120, width: 872 }}>
          <button
            type="button"
            role="switch"
            aria-checked={rpa}
            onClick={() => setRpa(!rpa)}
            className="flex h-[96px] w-[520px] items-center gap-[20px] rounded-[22px] px-[26px] text-left outline-none focus-visible:ring-2 focus-visible:ring-[#4a74ff]"
            style={{ background: t.card }}
          >
            <span className="relative inline-block h-[34px] w-[60px] shrink-0 rounded-full transition-colors" style={{ background: rpa ? t.blue : t.seg }}>
              <span className="absolute top-[3px] h-[28px] w-[28px] rounded-full bg-white transition-all" style={{ left: rpa ? 29 : 3, boxShadow: '0 1px 4px rgba(0,0,0,0.3)' }} />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-[23px] leading-snug">Remote parking assist</span>
              <span className="block text-[16px] leading-snug" style={{ color: t.text3 }}>Park by phone from outside the car</span>
            </span>
            <Ic.Info size={28} style={{ color: t.text2 }} />
          </button>
          <Illustration />
        </div>

        <div className="absolute" style={{ left: 54, top: 250, width: 872, height: 1, background: t.line }} />

        <div className="absolute flex items-center justify-between" style={{ left: 54, top: 290, width: 872 }}>
          <div style={{ width: 520 }}>
            <div className="mb-[14px] flex items-center justify-between pl-1 text-[22px]">
              Parking speed
              <Ic.Info size={28} style={{ color: t.text2 }} />
            </div>
            <div className="flex h-[66px] gap-[2px] rounded-[22px] p-[4px]" style={{ background: t.seg }} role="group" aria-label="Parking speed">
              {speeds.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  aria-pressed={speed === s.id}
                  onClick={() => setSpeed(s.id)}
                  className="flex-1 rounded-[18px] text-[21px] outline-none transition-colors focus-visible:ring-2 focus-visible:ring-[#4a74ff]"
                  style={{ background: speed === s.id ? t.segOn : 'transparent', color: speed === s.id ? t.tileOnText : t.text, boxShadow: speed === s.id ? '0 2px 8px rgba(0,0,0,0.10)' : 'none' }}
                >
                  {s.label}
                </button>
              ))}
            </div>
            <p className="mt-[16px] pl-1 text-[16px] leading-snug" style={{ color: t.text3 }}>
              How briskly the car moves while it parks. The phone and the Tech tab follow it.
            </p>
          </div>
          <Illustration speed />
        </div>
      </div>
    </div>
  );
}

/** The dialog's little picture: the car, the path it takes and, for remote parking, the phone that sends it. */
function Illustration({ speed = false }: { speed?: boolean }) {
  const t = useHa();
  const { slug } = useHaLocal();
  return (
    <svg width="300" height="130" viewBox="0 0 300 130" aria-hidden>
      <path d="M40 98 C110 98 150 96 196 60" fill="none" stroke={t.blue} strokeWidth="5" strokeLinecap="round" strokeDasharray="3 11" opacity="0.9" />
      <path d="M150 112 L206 112 L230 92 L172 92 Z" fill="none" stroke={t.blue} strokeWidth="3" opacity="0.7" />
      <image href={`/hmi/${slug}/car34.webp`} x="0" y="34" width="150" height="73" />
      {!speed && (
        <g transform="translate(236 30)">
          <circle cx="0" cy="0" r="30" fill="none" stroke={t.blue} strokeWidth="3" opacity="0.7" />
          <rect x="-12" y="-19" width="24" height="38" rx="5" fill={t.tone === 'dark' ? '#0a0b0e' : '#fff'} stroke={t.blue} strokeWidth="2.500" />
          <rect x="-5" y="-6" width="10" height="17" rx="3" fill={t.blue} opacity="0.8" />
        </g>
      )}
    </svg>
  );
}
