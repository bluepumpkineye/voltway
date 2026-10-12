'use client';

import React from 'react';
import type { HmiSkin, Variant, Vehicle } from '@/data/vehicles/schema';
import { CAR_SCREEN_H, CAR_SCREEN_W, CarScreen } from '@/components/hmi/CarScreen';
import { Fit } from '@/components/tech/Fit';
import { useWide } from '@/components/tech/TechDevices';
import { isLowBeam, LIGHT_MODES, type LightMode } from '@/lib/lights';
import { useVehicleStore } from '@/store/vehicle-store';
import { GLASS } from './Chrome';

/**
 * The Dashboard tab: the car's own screen, live, beside the car. Its headlamp controls switch the lamps,
 * and the lamps at both ends of the car (the glow, the beam on the floor, the room going to dusk) follow.
 * The dock adds what a screen does not have: which end of the car to look at, the high beam, the brake.
 *
 * On a wide window the screen stands in a column at the right, and the camera frames the car in what is
 * left (the device inset); on a narrower one the screen opens as a sheet over the car, and on a phone the
 * dock's own lamp switch is the control.
 */

const FOCUS = 'outline-none focus-visible:ring-2 focus-visible:ring-neutral-900/70 focus-visible:ring-offset-1';

/** How wide the screen's column is, px: a good share of a wide window, never more than the screen's own size. */
export function dashColumnWidth(windowWidth: number): number {
  return Math.min(700, Math.round(windowWidth * 0.46));
}

/** Where the dashboard stands in the window: whether the screen has a column, how wide it is, whether it fits at all. */
export function useDashboardLayout() {
  const wide = useWide();
  const [vw, setVw] = React.useState(1280);
  React.useEffect(() => {
    const f = () => setVw(window.innerWidth);
    f();
    window.addEventListener('resize', f);
    return () => window.removeEventListener('resize', f);
  }, []);
  return { wide, vw, colW: dashColumnWidth(vw), screenFits: wide || vw >= 700 };
}

const MODE_LABEL: Record<LightMode, string> = { off: 'Off', position: 'Position', low: 'Low beam', auto: 'Auto' };

/** Where the lamp control is on each car's own screen. */
const WHERE: Partial<Record<HmiSkin, string>> = {
  harmonyos: 'Tap the headlamp button on the bottom bar of the car’s screen, or open Vehicle control.',
  hyperos: 'Tap the headlight on the car at the centre of its screen, or open Settings, then Lights.',
  zeekros: 'Tap Lights on the car’s home screen.',
};

function coachText(vehicle: Vehicle, mode: LightMode, high: boolean, braking: boolean): string {
  if (braking) return 'Brake lights: they come on with the pedal, lamps or no lamps.';
  if (mode === 'off') return WHERE[vehicle.cockpit.skin] ?? 'Open Controls on the car’s screen and switch the headlights on.';
  if (mode === 'position') return 'Position lights. Step up to the low beam on the car’s screen.';
  if (high) return 'High beam: it reaches further and the room goes darker round it.';
  return `${MODE_LABEL[mode]}. Try the high beam, or hold Brake lights.`;
}

// ------------------------------------------------------------------------------------ the screen

/**
 * The car's screen and a line of guidance. On a wide window it is a column at the right, the camera framing
 * the car clear of it; on a narrower one it is a sheet over the car, opened from the dock.
 */
export function DashboardScreen({
  vehicle,
  variant,
  open,
  onClose,
}: {
  vehicle: Vehicle;
  variant: Variant;
  /** the sheet of a narrower window is open */
  open: boolean;
  onClose: () => void;
}) {
  const { wide, vw, colW, screenFits } = useDashboardLayout();
  const setInset = useVehicleStore((s) => s.setDeviceInset);
  const mode = useVehicleStore((s) => s.lightMode);
  const high = useVehicleStore((s) => s.highBeam);
  const braking = useVehicleStore((s) => s.braking);

  // the camera frames the car clear of the screen
  React.useEffect(() => {
    if (wide) setInset({ right: Math.min(0.6, (colW + 28) / vw), bottom: 0.07 });
    else setInset({ right: 0, bottom: 0.1 });
    return () => setInset({ right: 0, bottom: 0 });
  }, [wide, colW, vw, setInset]);

  // the sheet gives way to the column when the window grows wide
  React.useEffect(() => {
    if (wide && open) onClose();
  }, [wide, open, onClose]);

  if (!screenFits) return null;
  if (!wide && !open) return null;

  const screen = (
    <div className="w-full shrink-0" style={{ aspectRatio: `${CAR_SCREEN_W} / ${CAR_SCREEN_H}`, maxHeight: '100%' }}>
      <Fit w={CAR_SCREEN_W} h={CAR_SCREEN_H} className="h-full w-full">
        <CarScreen vehicle={vehicle} variant={variant} />
      </Fit>
    </div>
  );

  if (wide) {
    return (
      <aside
        className="pointer-events-none absolute bottom-3 right-4 top-[60px] z-10"
        style={{ width: colW }}
        aria-label="The car’s screen"
      >
        <div className="flex h-full min-h-0 flex-col items-center justify-center gap-3 pb-6">
          {screen}
          <p
            className={`pointer-events-auto flex min-h-[34px] max-w-full items-center gap-2 rounded-full px-4 py-1.5 text-[12px] text-neutral-700 ${GLASS}`}
            role="status"
            aria-live="polite"
          >
            <span className="h-[7px] w-[7px] shrink-0 animate-pulse rounded-full bg-[#2f6bff]" aria-hidden />
            <span>{coachText(vehicle, mode, high, braking)}</span>
          </p>
        </div>
      </aside>
    );
  }
  return (
    <aside className="pointer-events-none absolute inset-x-2 bottom-[128px] top-[56px] z-10" aria-label="The car’s screen">
      <div className="flex h-full min-h-0 flex-col items-center gap-2">
        <button
          type="button"
          onClick={onClose}
          className={`pointer-events-auto shrink-0 rounded-full px-4 py-2 text-[12px] font-medium text-neutral-700 ${GLASS} ${FOCUS}`}
        >
          Show the car
        </button>
        {screen}
        <p className={`pointer-events-auto max-w-full rounded-2xl px-4 py-1.5 text-center text-[12px] text-neutral-700 ${GLASS}`} role="status" aria-live="polite">
          {coachText(vehicle, mode, high, braking)}
        </p>
      </div>
    </aside>
  );
}

// ------------------------------------------------------------------------------------ the dock

const segment = (on: boolean) =>
  `rounded-full px-3.5 py-1.5 text-[12px] font-medium transition-colors ${FOCUS} ${
    on ? 'bg-neutral-900 text-white' : 'text-neutral-600 hover:text-neutral-900'
  }`;

/** The press-and-hold brake pedal: the tail lamps come on brighter for as long as it is held. */
function BrakeButton() {
  const braking = useVehicleStore((s) => s.braking);
  const setBraking = useVehicleStore((s) => s.setBraking);
  // leaving the tab with the pedal down must not leave the lamps on
  React.useEffect(() => () => setBraking(false), [setBraking]);
  return (
    <button
      type="button"
      aria-pressed={braking}
      title="Hold to brake"
      onPointerDown={(e) => {
        e.currentTarget.setPointerCapture?.(e.pointerId);
        setBraking(true);
      }}
      onPointerUp={() => setBraking(false)}
      onPointerCancel={() => setBraking(false)}
      onKeyDown={(e) => {
        if ((e.key === ' ' || e.key === 'Enter') && !e.repeat) {
          e.preventDefault();
          setBraking(true);
        }
      }}
      onKeyUp={(e) => {
        if (e.key === ' ' || e.key === 'Enter') setBraking(false);
      }}
      onBlur={() => setBraking(false)}
      // a screen reader's activation sends a click and nothing else: a short press
      onClick={(e) => {
        if (e.detail !== 0) return;
        setBraking(true);
        window.setTimeout(() => setBraking(false), 1200);
      }}
      className={`pointer-events-auto flex items-baseline gap-2 rounded-full px-4 py-2 text-[12px] font-medium transition-colors ${GLASS} ${FOCUS} ${
        braking ? '!bg-[#d6281b] text-white' : 'text-neutral-700 hover:text-neutral-900'
      }`}
    >
      Brake lights
      <span className={`text-[11px] font-normal ${braking ? 'text-white/75' : 'text-neutral-400'}`}>hold</span>
    </button>
  );
}

/**
 * The Dashboard tab's dock: the end of the car to look at, the lamp switch (the screen has it too; it is
 * the only one on a phone), the high beam, the brake.
 */
export function DashboardControls({
  screenFits,
  wide,
  screenOpen,
  onScreen,
}: {
  screenFits: boolean;
  wide: boolean;
  screenOpen: boolean;
  onScreen: (open: boolean) => void;
}) {
  const view = useVehicleStore((s) => s.lightsView);
  const mode = useVehicleStore((s) => s.lightMode);
  const high = useVehicleStore((s) => s.highBeam);
  const setView = useVehicleStore((s) => s.setLightsView);
  const setMode = useVehicleStore((s) => s.setLightMode);
  const setHigh = useVehicleStore((s) => s.setHighBeam);

  // a sheet over the car is the screen: its own controls are what the visitor needs
  if (screenOpen && !wide) return null;

  return (
    <div className="pointer-events-none flex max-w-full flex-wrap items-center justify-center gap-2">
      <div role="group" aria-label="End of the car" className={`pointer-events-auto flex rounded-full p-1 ${GLASS}`}>
        {(['front', 'rear'] as const).map((v) => (
          <button key={v} type="button" aria-pressed={view === v} onClick={() => setView(v)} className={segment(view === v)}>
            {v === 'front' ? 'Front' : 'Rear'}
          </button>
        ))}
      </div>
      <div role="group" aria-label="Headlamps" className={`pointer-events-auto flex rounded-full p-1 ${GLASS}`}>
        {LIGHT_MODES.map((m) => (
          <button key={m} type="button" aria-pressed={mode === m} onClick={() => setMode(m)} className={segment(mode === m)}>
            {MODE_LABEL[m]}
          </button>
        ))}
      </div>
      <button
        type="button"
        aria-pressed={high}
        onClick={() => {
          // the high beam rides on the low beam: asking for it from off lights both
          if (!high && !isLowBeam(mode)) setMode('low');
          setHigh(!high);
        }}
        className={`pointer-events-auto rounded-full px-4 py-2 text-[12px] font-medium transition-colors ${GLASS} ${FOCUS} ${
          high ? '!bg-neutral-900 text-white' : 'text-neutral-700 hover:text-neutral-900'
        }`}
      >
        High beam
      </button>
      <BrakeButton />
      {screenFits && !wide && (
        <button
          type="button"
          onClick={() => onScreen(true)}
          className={`pointer-events-auto rounded-full px-4 py-2 text-[12px] font-medium text-neutral-700 ${GLASS} ${FOCUS}`}
        >
          Car screen
        </button>
      )}
    </div>
  );
}
