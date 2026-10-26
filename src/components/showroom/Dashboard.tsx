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
  banyan: 'Tap Lights on the vehicle stage or open Controls on the Banyan display.',
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
 * The car's screen and a line of guidance.
 * Displays the car's interactive HMI central display in a floating, moveable tablet enclosure.
 * Users can grab the top bezel / grip bar (with hand cursor) and drag the tablet freely across the screen.
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

  // Moveable / Floating Drag State
  const [offset, setOffset] = React.useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = React.useState(false);
  const dragStart = React.useRef<{
    startX: number;
    startY: number;
    initOffsetX: number;
    initOffsetY: number;
  } | null>(null);
  const tabletRef = React.useRef<HTMLDivElement>(null);

  // Reset offset if vehicle or breakpoint changes
  React.useEffect(() => {
    setOffset({ x: 0, y: 0 });
  }, [vehicle.slug, wide]);

  // the camera frames the car clear of the screen
  React.useEffect(() => {
    if (wide) setInset({ right: Math.min(0.6, (colW + 28) / vw), bottom: 0 });
    else setInset({ right: 0, bottom: 0.1 });
    return () => setInset({ right: 0, bottom: 0 });
  }, [wide, colW, vw, setInset]);

  // the sheet gives way to the column when the window grows wide
  React.useEffect(() => {
    if (wide && open) onClose();
  }, [wide, open, onClose]);

  if (!screenFits) return null;
  if (!wide && !open) return null;

  // Drag Event Handlers with Viewport Bounding
  const handlePointerDown = (e: React.PointerEvent) => {
    const target = e.target as HTMLElement;
    // Don't drag if clicking buttons, links, inputs, selects, textareas or any role="button" inside HMI
    if (target.closest('button, a, input, select, textarea, [role="button"], [role="switch"], [role="tab"], [role="slider"]')) return;

    e.preventDefault();
    e.stopPropagation();

    try {
      e.currentTarget.setPointerCapture(e.pointerId);
    } catch {}

    dragStart.current = {
      startX: e.clientX,
      startY: e.clientY,
      initOffsetX: offset.x,
      initOffsetY: offset.y,
    };
    setIsDragging(true);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!dragStart.current) return;
    e.preventDefault();
    e.stopPropagation();

    const dx = e.clientX - dragStart.current.startX;
    const dy = e.clientY - dragStart.current.startY;
    let nextX = dragStart.current.initOffsetX + dx;
    let nextY = dragStart.current.initOffsetY + dy;

    if (tabletRef.current) {
      const rect = tabletRef.current.getBoundingClientRect();
      const minX = -rect.left + offset.x + 8;
      const maxX = window.innerWidth - (rect.left - offset.x) - rect.width - 8;
      const minY = -rect.top + offset.y + 48;
      const maxY = window.innerHeight - (rect.top - offset.y) - rect.height - 8;

      nextX = Math.max(minX, Math.min(maxX, nextX));
      nextY = Math.max(minY, Math.min(maxY, nextY));
    }

    setOffset({ x: nextX, y: nextY });
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    if (!dragStart.current) return;
    try {
      e.currentTarget.releasePointerCapture(e.pointerId);
    } catch {}
    dragStart.current = null;
    setIsDragging(false);
  };

  const resetPosition = (e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setOffset({ x: 0, y: 0 });
  };

  const hasMoved = offset.x !== 0 || offset.y !== 0;

  return (
    <div className="pointer-events-none fixed inset-0 z-20 overflow-hidden" aria-label="The car’s screen">
      <div
        ref={tabletRef}
        role="region"
        aria-label="Interactive Car Central Display Tablet"
        style={{
          width: wide ? colW : undefined,
          transform: `translate3d(${offset.x}px, ${offset.y}px, 0)`,
          transition: isDragging ? 'none' : 'transform 0.35s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
        className={`pointer-events-auto absolute ${
          wide
            ? 'top-[calc(var(--top-ui,56px)+16px)] right-6 max-w-[calc(100vw-32px)]'
            : 'bottom-20 inset-x-2 mx-auto w-[calc(100vw-16px)] max-w-[560px]'
        } select-none`}
      >
        {/* Outer Floating Tablet Enclosure */}
        <div
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerUp}
          onDoubleClick={resetPosition}
          className={`group relative overflow-hidden rounded-[22px] bg-gradient-to-b from-[#242b38] via-[#161c26] to-[#0d121a] p-1.5 sm:p-2 transition-shadow duration-300 ${
            isDragging
              ? 'cursor-grabbing shadow-[0_40px_100px_-20px_rgba(0,0,0,0.95),0_0_0_1.5px_rgba(6,182,212,0.5)_inset] scale-[1.006]'
              : 'cursor-grab shadow-[0_24px_60px_-16px_rgba(0,0,0,0.85),0_0_0_1px_rgba(255,255,255,0.12)_inset,0_2px_4px_rgba(255,255,255,0.2)_inset]'
          }`}
        >
          {/* Top Tablet Hardware Bezel: Sensor Dot, Brand/Model Title, Grip Pill, and Reset */}
          <div className="relative mb-1 flex items-center justify-between px-2 pt-0.5">
            {/* Left: Sensor dots & Model label */}
            <div className="flex items-center gap-2 min-w-0">
              <div className="flex items-center gap-1 opacity-60 shrink-0">
                <div className="h-1 w-1 rounded-full bg-[#070b12] border border-white/20" />
                <div className="h-1.5 w-1.5 rounded-full bg-[#03060a] border border-cyan-500/40" />
              </div>
              <span className="font-mono text-[9px] sm:text-[10px] uppercase tracking-[0.14em] text-neutral-300 truncate">
                {vehicle.brand} {vehicle.model} · Central Display
              </span>
            </div>

            {/* Center: Minimal Physical Grip Pill (Hand Cursor Area) */}
            <div
              className="flex items-center justify-center py-0.5 px-3 rounded-full hover:bg-white/[0.08] transition-colors shrink-0"
              title="Drag to reposition display · Double-click to reset"
            >
              <div className="h-1 w-10 rounded-full bg-white/25 group-hover:bg-cyan-400/70 transition-colors" />
            </div>

            {/* Right: Reset and Close buttons */}
            <div className="flex items-center gap-1.5 shrink-0">
              {hasMoved && (
                <button
                  type="button"
                  onClick={resetPosition}
                  className="inline-flex items-center gap-1 rounded-full bg-white/[0.08] hover:bg-white/15 px-2 py-0.5 text-[8.5px] font-medium tracking-wider text-neutral-300 hover:text-white transition-colors"
                  title="Reset to default position"
                >
                  <span>↺</span>
                  <span>Reset</span>
                </button>
              )}
              {!wide && (
                <button
                  type="button"
                  onClick={onClose}
                  className="rounded-full bg-white/[0.08] hover:bg-white/15 px-2 py-0.5 text-[8.5px] font-medium tracking-wider text-neutral-300 hover:text-white transition-colors"
                  title="Close screen"
                >
                  ✕ Close
                </button>
              )}
            </div>
          </div>

          {/* Screen Display Surface */}
          <div className="relative overflow-hidden rounded-[16px] border border-white/[0.08] bg-[#060a12] shadow-[inset_0_0_30px_rgba(0,8,16,0.95)]">
            <div className="w-full shrink-0" style={{ aspectRatio: `${CAR_SCREEN_W} / ${CAR_SCREEN_H}`, maxHeight: '100%' }}>
              <Fit w={CAR_SCREEN_W} h={CAR_SCREEN_H} className="h-full w-full">
                <CarScreen vehicle={vehicle} variant={variant} />
              </Fit>
            </div>
          </div>

          {/* Coach Guidance Status Bar (Docked at Bottom of Tablet) */}
          <div className="mt-1.5 flex items-center justify-between rounded-lg bg-[#080d15]/90 px-2.5 py-1 border border-white/[0.06] text-[10.5px] text-neutral-300 backdrop-blur-md">
            <div className="flex items-center gap-2 truncate">
              <span className="h-1.5 w-1.5 shrink-0 animate-pulse rounded-full bg-cyan-400" aria-hidden />
              <span className="truncate">{coachText(vehicle, mode, high, braking)}</span>
            </div>
            <span className="shrink-0 font-mono text-[8.5px] text-neutral-500 uppercase tracking-wider ml-2">
              HMI Live
            </span>
          </div>
        </div>
      </div>
    </div>
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
