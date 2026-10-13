'use client';

import React from 'react';
import type { Variant, Vehicle } from '@/data/vehicles/schema';
import { CAR_SCREEN_H, CAR_SCREEN_W, CarScreen } from '@/components/hmi/CarScreen';
import { Fit } from '@/components/tech/Fit';
import { pauseDemo, pressBoost } from '@/lib/tech/actions';
import { useTechClock } from '@/lib/tech/clock';
import { STEPS } from '@/lib/tech/boost';
import { runPhase } from '@/lib/tech/phase';
import { useVehicleStore } from '@/store/vehicle-store';
import { GLASS } from './Chrome';
import { useDashboardLayout } from './Dashboard';

const FOCUS = 'outline-none focus-visible:ring-2 focus-visible:ring-neutral-900/70 focus-visible:ring-offset-1';

/** How wide the enlarged screen's column is, px: half a wide window, so the BOOST page can be read from its rows. */
export function boostColumnWidth(windowWidth: number): number {
  return Math.min(760, Math.round(windowWidth * 0.5));
}

/**
 * The BOOST demo's own panel, the showroom's and not the car's: a button for the knob (the knob on the wheel, in the cabin
 * in front of the visitor, does the same), what BOOST is doing now and the maker's list of what it does, ticked off as the
 * demo applies it. The list is the maker's, the order and the timing are ours, and the screen the cabin shows is a stand-in.
 */
export function BoostTools() {
  const clock = useTechClock();
  const run = runPhase(clock);
  const on = useVehicleStore((s) => s.boostOn);
  const step = useVehicleStore((s) => s.boostStep);
  const up = useVehicleStore((s) => s.boostPopup);
  const setUp = useVehicleStore((s) => s.setBoostPopup);
  const { wide, vw, screenFits } = useDashboardLayout();
  // this panel covers the foot of the window, and the enlarged screen stands at the right: the cabin picture is lifted
  // clear of the one and slid clear of the other
  const setInset = useVehicleStore((s) => s.setDeviceInset);
  const right = up && wide && screenFits ? Math.min(0.6, (boostColumnWidth(vw) + 28) / vw) : 0;
  React.useEffect(() => {
    setInset({ right, bottom: 0.3 });
    return () => setInset({ right: 0, bottom: 0 });
  }, [setInset, right]);

  const action =
    run === 'driving'
      ? { label: 'Pause', run: pauseDemo }
      : run === 'paused'
        ? { label: 'Resume', run: pressBoost }
        : run === 'done'
          ? { label: 'Again', run: pressBoost }
          : { label: 'Press BOOST', run: pressBoost };

  return (
    <div className={`pointer-events-auto w-full max-w-[620px] rounded-2xl px-3.5 py-2.5 ${GLASS}`}>
      <div className="flex items-center gap-3">
        <button type="button" onClick={action.run} className={`shrink-0 rounded-full bg-neutral-900 px-4 py-2 text-[12px] font-medium text-white ${FOCUS}`}>
          {action.label}
        </button>
        <div className="min-w-0 flex-1 text-[12px] leading-snug" aria-live="polite">
          <span className="font-medium text-neutral-900">BOOST {on ? 'on' : 'off'}</span>
          <span className="text-neutral-500">
            {on ? `, ${step} of ${STEPS.length} applied` : run === 'done' ? ', pressed again' : ', the knob is on the wheel’s lower right'}
          </span>
        </div>
        {screenFits && !up && (
          <button type="button" onClick={() => setUp(true)} className={`shrink-0 rounded-full px-3 py-2 text-[12px] font-medium text-neutral-700 ${FOCUS}`}>
            Enlarge the screen
          </button>
        )}
      </div>
      <ul className="mt-2 flex flex-wrap gap-1.5">
        {STEPS.map((s, i) => {
          const done = on && i < step;
          return (
            <li key={s.id} className={`rounded-full px-2.5 py-1 text-[11px] transition-colors ${done ? 'bg-[#2f6bff] text-white' : 'bg-black/[0.05] text-neutral-500'}`}>
              {s.label}
              <span className={done ? 'text-white/80' : 'text-neutral-400'}> · {s.detail}</span>
            </li>
          );
        })}
      </ul>
      <p className="mt-2 text-[10.5px] leading-snug text-neutral-500">
        The list is the maker’s <span className="text-neutral-400">published, some trims only</span>; the order and the timing are ours. The screen in the cabin is a stand-in drawn by the showroom: the maker’s BOOST screens are not photographed.
      </p>
    </div>
  );
}

/**
 * The car's screen, enlarged: it comes up when BOOST is pressed, so the page the cabin's screen shows (small in the picture
 * of the cabin) can be read row by row. A column at the right of a wide window, the cabin framed in what is left; a sheet
 * over the cabin on a narrower one; nothing on a phone, whose screen cannot show it any larger than the cabin does. The
 * visitor can close it, and the panel's button brings it back.
 */
export function BoostPopup({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  const up = useVehicleStore((s) => s.boostPopup);
  const setUp = useVehicleStore((s) => s.setBoostPopup);
  const { screenFits } = useDashboardLayout();
  // leaving the demo takes it down
  React.useEffect(() => () => setUp(false), [setUp]);
  if (!up || !screenFits) return null;
  return <Popup vehicle={vehicle} variant={variant} />;
}

function Popup({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  const on = useVehicleStore((s) => s.boostOn);
  const step = useVehicleStore((s) => s.boostStep);
  const setUp = useVehicleStore((s) => s.setBoostPopup);
  const { wide, vw } = useDashboardLayout();
  const ref = React.useRef<HTMLElement>(null);

  // it slides in from the right, as the cabin's picture slides left to make room (not under reduced motion)
  React.useEffect(() => {
    const el = ref.current;
    if (!el || typeof el.animate !== 'function') return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const a = el.animate(
      [
        { opacity: 0, transform: wide ? 'translateX(36px)' : 'translateY(18px)' },
        { opacity: 1, transform: 'none' },
      ],
      { duration: 480, easing: 'cubic-bezier(0.2, 0.7, 0.2, 1)' },
    );
    return () => a.cancel();
  }, [wide]);

  const close = () => setUp(false);
  const screen = (
    <div className="w-full shrink-0" style={{ aspectRatio: `${CAR_SCREEN_W} / ${CAR_SCREEN_H}`, maxHeight: '100%' }}>
      <Fit w={CAR_SCREEN_W} h={CAR_SCREEN_H} className="h-full w-full">
        <CarScreen vehicle={vehicle} variant={variant} />
      </Fit>
    </div>
  );
  const status = (
    <span className="flex items-center gap-2">
      <span className={`h-[7px] w-[7px] shrink-0 rounded-full ${on ? 'animate-pulse bg-[#2f6bff]' : 'bg-neutral-400'}`} aria-hidden />
      <span>{on ? `BOOST is on: ${step} of ${STEPS.length} applied.` : 'BOOST is off.'}</span>
    </span>
  );

  if (wide) {
    return (
      // above the cabin's own pinned screen (z 16), which is the same page, small
      <aside ref={ref} className="pointer-events-none absolute bottom-3 right-4 top-[60px] z-[30]" style={{ width: boostColumnWidth(vw) }} aria-label="The car’s screen, enlarged">
        <div className="flex h-full min-h-0 flex-col items-center justify-center gap-3 pb-6">
          {screen}
          <div className={`pointer-events-auto flex min-h-[34px] max-w-full items-center gap-3 rounded-full py-1 pl-4 pr-1.5 text-[12px] text-neutral-700 ${GLASS}`} role="status" aria-live="polite">
            {status}
            <button type="button" onClick={close} className={`shrink-0 rounded-full bg-neutral-900 px-3.5 py-1 text-[11px] font-medium text-white ${FOCUS}`}>
              Close
            </button>
          </div>
        </div>
      </aside>
    );
  }
  return (
    <aside ref={ref} className="pointer-events-none absolute inset-x-2 bottom-[190px] top-[56px] z-[30]" aria-label="The car’s screen, enlarged">
      <div className="flex h-full min-h-0 flex-col items-center gap-2">
        <button type="button" onClick={close} className={`pointer-events-auto shrink-0 rounded-full px-4 py-2 text-[12px] font-medium text-neutral-700 ${GLASS} ${FOCUS}`}>
          Show the cabin
        </button>
        {screen}
        <p className={`pointer-events-auto max-w-full rounded-2xl px-4 py-1.5 text-center text-[12px] text-neutral-700 ${GLASS}`} role="status" aria-live="polite">
          {status}
        </p>
      </div>
    </aside>
  );
}
