'use client';

import React from 'react';
import { pauseDemo } from '@/lib/tech/actions';
import { techClock, useTechClock } from '@/lib/tech/clock';
import { runPhase } from '@/lib/tech/phase';
import { BUTTONS, afterPress, type ButtonId } from '@/lib/tech/swivel';
import { useVehicleStore } from '@/store/vehicle-store';
import { GLASS } from './Chrome';

const FOCUS = 'outline-none focus-visible:ring-2 focus-visible:ring-neutral-900/70 focus-visible:ring-offset-1';

const FACING = { driver: 'toward the driver', centre: 'square on', passenger: 'toward the passenger' } as const;

/**
 * The swivel screen demo's own panel, the showroom's and not the car's: the button that runs the presses, the same
 * four buttons the car's direction dialog has (for a window too small to tap the dialog on the screen), and the
 * maker's figures. The dialog on the car's own screen in the cabin is the device the demo starts from; this panel is
 * the director's tool beside the playback bar. The 55 mm and the 30° are published, the speed and the order are ours.
 */
export function SwivelTools() {
  const clock = useTechClock();
  const run = runPhase(clock);
  const turn = useVehicleStore((s) => s.screenTurn);
  const slide = useVehicleStore((s) => s.screenSlide);
  const setPose = useVehicleStore((s) => s.setScreenPose);
  // this panel covers the foot of the window: the cabin picture is lifted clear of it
  const setInset = useVehicleStore((s) => s.setDeviceInset);
  React.useEffect(() => {
    setInset({ right: 0, bottom: 0.3 });
    return () => setInset({ right: 0, bottom: 0 });
  }, [setInset]);

  const press = (id: ButtonId) => {
    techClock.pause();
    const next = afterPress({ turn, slide }, id);
    setPose(next.turn, next.slide);
  };
  const lit = (b: (typeof BUTTONS)[number]) => b.turn === turn && (b.slide === null || b.slide === slide);

  const action =
    run === 'driving'
      ? { label: 'Pause', run: pauseDemo }
      : run === 'paused'
        ? { label: 'Resume', run: () => techClock.play() }
        : run === 'done'
          ? { label: 'Again', run: () => techClock.play() }
          : { label: 'Start', run: () => techClock.play() };

  return (
    <div className={`pointer-events-auto w-full max-w-[620px] rounded-2xl px-3.5 py-2.5 ${GLASS}`}>
      <div className="flex items-center gap-3">
        <button type="button" onClick={action.run} className={`shrink-0 rounded-full bg-neutral-900 px-4 py-2 text-[12px] font-medium text-white ${FOCUS}`}>
          {action.label}
        </button>
        <div className="min-w-0 flex-1 text-[12px] leading-snug text-neutral-700" aria-live="polite">
          <span className="font-medium text-neutral-900">Screen {FACING[turn]}</span>
          <span className="text-neutral-500">, {slide === 'front' ? 'slid forward' : 'pulled back'}</span>
        </div>
      </div>
      <div className="mt-2 flex flex-wrap gap-1.5" role="group" aria-label="Screen direction">
        {BUTTONS.map((b) => (
          <button
            key={b.id}
            type="button"
            aria-pressed={lit(b)}
            onClick={() => press(b.id)}
            className={`rounded-full px-3 py-1 text-[11px] transition-colors ${FOCUS} ${
              lit(b) ? 'bg-neutral-900 text-white' : 'bg-black/[0.06] text-neutral-700 hover:bg-black/[0.1]'
            }`}
          >
            {b.label}
          </button>
        ))}
      </div>
      <p className="mt-2 text-[10.5px] leading-snug text-neutral-500">
        16.1 in · 55 mm forward and back · up to 30° to either side <span className="text-neutral-400">published, some trims only</span>. The speed it moves at is ours.
      </p>
    </div>
  );
}
