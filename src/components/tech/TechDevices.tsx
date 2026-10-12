'use client';

import React from 'react';
import type { TechDemoSpec, TechDevice, Variant, Vehicle } from '@/data/vehicles/schema';
import { CAR_SCREEN_H, CAR_SCREEN_W, CarScreen } from '@/components/hmi/CarScreen';
import { GLASS } from '@/components/showroom/Chrome';
import { pauseDemo, resetDemo, startDemo } from '@/lib/tech/actions';
import { useTechClock } from '@/lib/tech/clock';
import { parkPhase, type ParkPhase } from '@/lib/tech/phase';
import { useVehicleStore } from '@/store/vehicle-store';
import { Fit } from './Fit';
import { HimaApp, type AppScreen } from './phone/HimaApp';
import { DEVICE_H, DEVICE_W, PhoneFrame } from './phone/PhoneFrame';

/**
 * The devices a visitor starts a demonstration from, shown in the showroom as the owner has them: the
 * phone in their hand, running the maker's app, and the car's own centre screen. What either shows is the
 * demo's state, so starting from one is seen on the other and in the 3D scene.
 *
 * On a wide window they stand in a column at the right, and the camera frames the stage clear of them;
 * on a narrow one they come up from the bottom as a sheet.
 */

const FOCUS = 'outline-none focus-visible:ring-2 focus-visible:ring-neutral-900/70 focus-visible:ring-offset-1';
const LABEL: Record<TechDevice, string> = { phone: 'Phone', dashboard: 'Car screen' };

/** How wide the device column is, px, and what share of the window that is. */
export function columnWidth(device: TechDevice, windowWidth: number): number {
  if (device === 'phone') return 332;
  return Math.min(580, Math.round(windowWidth * 0.44));
}

/** The device on show for a demo: the visitor's pick, if the demo offers it. */
export function activeDevice(demo: TechDemoSpec, picked: TechDevice): TechDevice | null {
  const list = demo.devices ?? [];
  if (!list.length) return null;
  return list.includes(picked) ? picked : list[0];
}

/**
 * Where the devices stand in the window: which one is on show, and (on a wide window) how wide their
 * column is, so the dock and the camera can leave it clear. `vw` is the window's width.
 */
export function useDeviceColumn(demo: TechDemoSpec | undefined) {
  const picked = useVehicleStore((s) => s.techDevice);
  const wide = useWide();
  const [vw, setVw] = React.useState(1280);
  React.useEffect(() => {
    const f = () => setVw(window.innerWidth);
    f();
    window.addEventListener('resize', f);
    return () => window.removeEventListener('resize', f);
  }, []);
  const active = demo ? activeDevice(demo, picked) : null;
  return { active, wide, vw, colW: active ? columnWidth(active, vw) : 0 };
}

export function TechDevices({ vehicle, variant, demo }: { vehicle: Vehicle; variant: Variant; demo: TechDemoSpec }) {
  const setDevice = useVehicleStore((s) => s.setTechDevice);
  const setHmiScreen = useVehicleStore((s) => s.setHmiScreen);
  const hmiScreen = useVehicleStore((s) => s.hmiScreen);
  const rpa = useVehicleStore((s) => s.rpaEnabled);
  const clock = useTechClock();
  const [screen, setScreen] = React.useState<AppScreen>('home');
  const { active, wide, colW, vw } = useDeviceColumn(demo);
  const setInset = useVehicleStore((s) => s.setDeviceInset);
  const phase = parkPhase(clock);
  // a phone-sized window has no room for the stage and a device at once: the device opens nearly full
  // screen, and gives way to a slim bar of controls once the car is moving, so the stage can be watched
  const [sheet, setSheet] = React.useState<'open' | 'bar'>('open');
  const moving = phase === 'parking' || phase === 'leaving';
  const wasMoving = React.useRef(false);
  React.useEffect(() => {
    if (wide) return;
    if (moving && !wasMoving.current) setSheet('bar');
    if (phase === 'ready') setSheet('open');
    wasMoving.current = moving;
  }, [phase, moving, wide]);
  // a window with no room for the car's wide screen offers the phone alone
  const devices = (demo.devices ?? []).filter((d) => wide || vw >= 700 || d === 'phone');

  // the camera frames the stage clear of the devices
  React.useEffect(() => {
    if (!active) return;
    if (wide) setInset({ right: Math.min(0.6, (colW + 28) / vw), bottom: 0.14 });
    else setInset({ right: 0, bottom: 0.3 });
    return () => setInset({ right: 0, bottom: 0 });
  }, [active, wide, colW, vw, setInset]);

  // the car's screen opens on the parking page, as it does when the car is put in reverse: when the visitor
  // picks it, and when the tab opens on it (a link, or the Start button of the cabin's screen)
  const choose = (d: TechDevice) => {
    setDevice(d);
    if (d === 'dashboard') setHmiScreen('park');
  };
  React.useEffect(() => {
    if (useVehicleStore.getState().techDevice === 'dashboard') setHmiScreen('park');
  }, [setHmiScreen]);

  if (!active) return null;

  const coach =
    active === 'phone'
      ? screen === 'home'
        ? phase === 'ready'
          ? 'Tap “Remote parking” in the app.'
          : phase === 'parked'
            ? 'Parked. Open Remote parking to drive out.'
            : phase === 'done'
              ? 'Back where it started. Open Remote parking to go again.'
              : 'The car is moving. Open Remote parking to pause it.'
        : phase === 'ready'
          ? rpa
            ? 'Tap “Start parking in” and step back.'
            : 'Remote parking assist is off. Switch it on in the car’s settings.'
          : phase === 'parking' || phase === 'leaving'
            ? 'Watch the car. Pause, or leave the screen, to stop it.'
            : phase === 'parked'
              ? 'Parked. Tap “Start parking out” to leave the bay.'
              : phase === 'done'
                ? 'Out again. Tap “Park again” to repeat.'
                : 'Paused. Resume or start over.'
      : hmiScreen === 'park'
        ? phase === 'ready'
          ? 'Tap “Start parking in” on the car’s screen.'
          : phase === 'parked'
            ? 'Parked. Tap “Park out” to leave the bay.'
            : phase === 'done'
              ? 'Out again. Tap “Park again” to repeat.'
              : phase === 'paused-in' || phase === 'paused-out'
                ? 'Paused. Resume or start over.'
                : 'The car is steering itself. Pause at any time.'
        : 'This is the rest of the cabin. Open Parking assist to start.';

  const body = (
    <div className="flex h-full min-h-0 flex-col items-center gap-2">
      {(devices.length > 1 || !wide) && (
        <div className="flex w-full shrink-0 items-center justify-center gap-2">
        {devices.length > 1 && (
        <div role="group" aria-label="Start from" className={`pointer-events-auto flex shrink-0 rounded-full p-1 ${GLASS}`}>
          {devices.map((d) => (
            <button
              key={d}
              type="button"
              aria-pressed={d === active}
              onClick={() => choose(d)}
              className={`rounded-full px-4 py-1.5 text-[12px] font-medium transition-colors ${FOCUS} ${
                d === active ? 'bg-neutral-900 text-white' : 'text-neutral-600 hover:text-neutral-900'
              }`}
            >
              {LABEL[d]}
            </button>
          ))}
        </div>
        )}
        {!wide && (
          <button type="button" onClick={() => setSheet('bar')} className={`pointer-events-auto shrink-0 rounded-full px-4 py-2 text-[12px] font-medium text-neutral-700 ${GLASS} ${FOCUS}`}>
            Watch the car
          </button>
        )}
        </div>
      )}
      {active === 'phone' ? (
        <div className="min-h-0 w-full flex-1">
          <Fit w={DEVICE_W} h={DEVICE_H} className="h-full w-full">
            <PhoneFrame>
              <HimaApp vehicle={vehicle} variant={variant} demo={demo} screen={screen} setScreen={setScreen} />
            </PhoneFrame>
          </Fit>
        </div>
      ) : (
        // the car's screen is wide and short: it takes its own height, so the guidance sits right under it
        <div className="w-full shrink-0" style={{ aspectRatio: `${CAR_SCREEN_W} / ${CAR_SCREEN_H}`, maxHeight: '100%' }}>
          <Fit w={CAR_SCREEN_W} h={CAR_SCREEN_H} className="h-full w-full">
            <CarScreen vehicle={vehicle} variant={variant} />
          </Fit>
        </div>
      )}
      <div className={`pointer-events-auto ${wide ? 'flex' : 'hidden'} min-h-[34px] max-w-full shrink-0 items-center gap-2 rounded-full px-4 py-1.5 text-[12px] text-neutral-700 ${GLASS}`} role="status" aria-live="polite">
        <span className="h-[7px] w-[7px] shrink-0 animate-pulse rounded-full bg-[#2f6bff]" aria-hidden />
        <span>{coach}</span>
        {active === 'dashboard' && hmiScreen !== 'park' && (
          <button type="button" onClick={() => setHmiScreen('park')} className={`shrink-0 rounded-full bg-neutral-900 px-3 py-1 text-[11px] font-medium text-white ${FOCUS}`}>
            Open
          </button>
        )}
      </div>
    </div>
  );

  // one instance only: a wide window puts it in a column at the right, clear of the dock; a narrow one
  // opens it nearly full screen above the tabs, and shrinks it to a bar of controls while the car moves
  if (wide) {
    return (
      <aside className="pointer-events-none absolute bottom-3 right-4 top-[60px] z-10" style={{ width: colW }} aria-label={LABEL[active]}>
        {body}
      </aside>
    );
  }
  if (sheet === 'open') {
    return (
      <aside className="pointer-events-none absolute inset-x-2 bottom-[128px] top-[56px] z-10" aria-label={LABEL[active]}>
        {body}
      </aside>
    );
  }
  return (
    <aside className="pointer-events-none absolute inset-x-3 bottom-[120px] z-10" aria-label={LABEL[active]}>
      <Bar active={active} phase={phase} coach={coach} onOpen={() => setSheet('open')} />
    </aside>
  );
}

/**
 * The slim bar of a narrow window while the device is put away: what is happening, the one control
 * that matters now (pause, resume, drive out), and a way back to the device.
 */
function Bar({ active, phase, coach, onOpen }: { active: TechDevice; phase: ParkPhase; coach: string; onOpen: () => void }) {
  const go = () => startDemo('park', active);
  const action =
    phase === 'parking' || phase === 'leaving'
      ? { label: 'Pause', run: pauseDemo }
      : phase === 'paused-in' || phase === 'paused-out'
        ? { label: 'Resume', run: go }
        : phase === 'parked'
          ? { label: 'Park out', run: go }
          : phase === 'done'
            ? { label: 'Park again', run: resetDemo }
            : null;
  return (
    <div className={`pointer-events-auto flex items-center gap-2 rounded-full py-1.5 pl-4 pr-1.5 text-[12px] text-neutral-700 ${GLASS}`} role="status" aria-live="polite">
      <span className="h-[7px] w-[7px] shrink-0 animate-pulse rounded-full bg-[#2f6bff]" aria-hidden />
      <span className="min-w-0 flex-1 truncate">{coach}</span>
      {action && (
        <button type="button" onClick={action.run} className={`shrink-0 rounded-full bg-neutral-900 px-4 py-2 text-[12px] font-medium text-white ${FOCUS}`}>
          {action.label}
        </button>
      )}
      <button type="button" onClick={onOpen} className={`shrink-0 rounded-full px-3 py-2 text-[12px] font-medium ${FOCUS}`}>
        {active === 'phone' ? 'App' : 'Screen'}
      </button>
    </div>
  );
}

/** A window wide enough for the devices to stand beside the stage. */
export function useWide(): boolean {
  const [wide, setWide] = React.useState(true);
  React.useEffect(() => {
    const q = window.matchMedia('(min-width: 1024px)');
    const f = () => setWide(q.matches);
    f();
    q.addEventListener('change', f);
    return () => q.removeEventListener('change', f);
  }, []);
  return wide;
}
