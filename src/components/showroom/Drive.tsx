'use client';

import React from 'react';
import Link from 'next/link';
import type { DriveCamera, Variant, Vehicle } from '@/data/vehicles/schema';
import { vehicles } from '@/data/vehicles';
import { techClock, useTechClock } from '@/lib/tech/clock';
import { useRuntime } from '@/lib/tech/session';
import { DRIVE_CAMERAS, camerasOf, driveSetup, type DriveSetup } from '@/lib/tech/drive-setup';
import { useVehicleStore } from '@/store/vehicle-store';
import { LaunchTools } from './Launch';

const f0 = (x: number) => Math.round(x).toString();
const f1 = (x: number) => x.toFixed(1);
const f2 = (x: number) => x.toFixed(2);

// ------------------------------------------------------------------------------------------- the cockpit
//
// The Drive tab's controls live in the instruments, not beside them. The speedometer and the tachometer stand in the middle, as they
// always did, and the buttons that set the run stand at their sides like the switchgear of a cockpit: on the left the car (its trim
// and its drive mode), on the right the conditions (road, hill, camera, load, and what the car does after the run). A window too
// narrow for the two banks has them in one row above the gauges (`strip`); a phone held sideways, which has no height to spare,
// has that row with the icons alone (`mini`). Nothing is explained in words: a button is an icon and a name, and the instruments say the rest.

/** The width of one bank of buttons beside the gauges, px. */
export const BANK_W = 248;
/** The narrowest window that has the two banks beside the gauges (the gauges shrink a little to make room). */
export const BANKS_MIN_W = 1200;

export type CockpitForm = 'banks' | 'strip' | 'mini';

export function cockpitForm(vw: number, short: boolean): CockpitForm {
  return short ? 'mini' : vw >= BANKS_MIN_W ? 'banks' : 'strip';
}

/** How much taller the dock is than the instruments alone, px: the row of buttons stands above the gauges in the narrower forms. */
export function cockpitLift(form: CockpitForm): number {
  return form === 'strip' ? 84 : form === 'mini' ? 46 : 0;
}

// ------------------------------------------------------------------------------------------- the look
//
// The buttons wear the speedometers' own look (Launch.tsx): dark glass like the gauges' backing (rgba(16,20,27,.65) with a 12 % white
// rim), Chakra Petch, white figures, slate labels (#94a3b8), cyan for what is chosen (the HUD's run chips), the HUD's red (#ff1a2a)
// for the fast and the stop, emerald for what is reached and green, amber for the loose and the wet.

const FONT = "font-['Chakra_Petch',sans-serif]";
const BANK = 'bg-[#10141b]/70 text-white backdrop-blur-xl ring-1 ring-white/12 shadow-[0_10px_28px_-10px_rgba(0,0,0,0.7)]';
const DFOCUS = 'outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:ring-offset-1 focus-visible:ring-offset-transparent';
const IDLE = 'bg-white/[0.045] text-slate-300 ring-1 ring-white/10 hover:bg-white/[0.09] hover:text-white';

type Tone = 'cyan' | 'emerald' | 'red' | 'amber';
/** a chosen button: its tone's tint, ring and glow */
const CHOSEN: Record<Tone, string> = {
  cyan: 'bg-cyan-500/15 text-cyan-100 ring-1 ring-cyan-400 shadow-[0_0_14px_rgba(0,229,255,0.28)]',
  emerald: 'bg-emerald-500/15 text-emerald-100 ring-1 ring-emerald-400 shadow-[0_0_14px_rgba(16,185,129,0.3)]',
  red: 'bg-[#ff1a2a]/15 text-red-100 ring-1 ring-[#ff1a2a] shadow-[0_0_14px_rgba(255,26,42,0.32)]',
  amber: 'bg-amber-400/15 text-amber-100 ring-1 ring-amber-300 shadow-[0_0_14px_rgba(250,204,21,0.26)]',
};

/** The tone of a drive mode (read from its id and its label): green for the thrifty, red for the fast, amber for the loose surfaces, cyan for the rest. */
function toneOfMode(id: string, label = ''): Tone {
  const s = `${id} ${label}`.toLowerCase();
  if (/eco|range|save/.test(s)) return 'emerald';
  if (/sport|track|race|drag|boost|launch|insane/.test(s)) return 'red';
  if (/snow|sand|wet|rain|off|mud|slip/.test(s)) return 'amber';
  return 'cyan';
}

// ------------------------------------------------------------------------------------------- icons

const ico = { width: 16, height: 16, viewBox: '0 0 16 16', fill: 'none', stroke: 'currentColor', strokeWidth: 1.4, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true } as const;

const LeafIcon = () => (
  <svg {...ico}>
    <path d="M3 13C3 7 6.5 3 13 3c0 6.5-4 10-10 10z" />
    <path d="M3 13l6-6" />
  </svg>
);
const BoltIcon = () => (
  <svg {...ico}>
    <path d="M9.2 1.6L3.6 9H8l-1 5.4L12.6 7H8z" />
  </svg>
);
const FlagIcon = () => (
  <svg {...ico}>
    <path d="M3.5 14V2.5" />
    <path d="M3.5 3h8.6l-1.9 2.7 1.9 2.7H3.5" />
  </svg>
);
const PeakIcon = () => (
  <svg {...ico}>
    <path d="M1.5 13.5l4.2-7 2.6 4 1.7-2.4 4.5 5.4z" />
  </svg>
);
const DialIcon = () => (
  <svg {...ico}>
    <path d="M2.5 11.5a5.5 5.5 0 0 1 11 0" />
    <path d="M8 11.5l2.6-3.4" />
    <circle cx="8" cy="11.5" r="0.9" fill="currentColor" stroke="none" />
  </svg>
);
const SunIcon = () => (
  <svg {...ico}>
    <circle cx="8" cy="8" r="2.8" />
    <path d="M8 1.5v1.6M8 12.9v1.6M1.5 8h1.6M12.9 8h1.6M3.4 3.4l1.1 1.1M11.5 11.5l1.1 1.1M3.4 12.6l1.1-1.1M11.5 4.5l1.1-1.1" />
  </svg>
);
const DropIcon = () => (
  <svg {...ico}>
    <path d="M8 1.8c2.4 3 4 4.9 4 7.1a4 4 0 0 1-8 0c0-2.2 1.6-4.1 4-7.1z" />
  </svg>
);
const SlopeIcon = ({ pct }: { pct: number }) => (
  <svg {...ico}>
    <path d="M1.5 13.5h13" opacity="0.4" />
    <path d={pct > 0 ? 'M2 11.5L14 4.5' : pct < 0 ? 'M2 4.5L14 11.5' : 'M2 8h12'} />
  </svg>
);
const PersonIcon = () => (
  <svg {...ico}>
    <circle cx="8" cy="5" r="2.3" />
    <path d="M3.5 13.5c0-3 2-4.6 4.5-4.6s4.5 1.6 4.5 4.6" />
  </svg>
);
const PeopleIcon = () => (
  <svg {...ico}>
    <circle cx="5.6" cy="5.4" r="1.9" />
    <path d="M2 13c0-2.6 1.6-4 3.6-4s3.6 1.4 3.6 4" />
    <circle cx="11" cy="6" r="1.6" />
    <path d="M9.9 9.2c.4-.1.7-.2 1.1-.2 1.8 0 3 1.2 3 3.6" />
  </svg>
);
const GoIcon = () => (
  <svg {...ico}>
    <path d="M2 8h10.5M9 4.4L12.6 8 9 11.6" />
  </svg>
);
const StopIcon = () => (
  <svg {...ico}>
    <path d="M5.2 2h5.6L14 5.2v5.6L10.8 14H5.2L2 10.8V5.2z" />
    <path d="M5.2 8h5.6" />
  </svg>
);
// the six cameras: what the camera sees of the car
const CAM_ICON: Record<DriveCamera, React.ReactNode> = {
  hero: (
    <svg {...ico}>
      <path d="M2 11.5v-2l2.1-1 1.5-2.2h4.6l1.9 2.4 1.9.8v2z" />
      <path d="M3 3.8a7.5 3 0 0 1 10 0" opacity="0.55" />
    </svg>
  ),
  chase: (
    <svg {...ico}>
      <rect x="4.2" y="4.6" width="7.6" height="5.4" rx="1.6" />
      <path d="M2.8 10.4h10.4M4.6 10.4v2.2M11.4 10.4v2.2M6 7.6h4" />
    </svg>
  ),
  side: (
    <svg {...ico}>
      <path d="M1.8 11V9.1l1.8-.6 1.6-2.4h5.4l1.8 2.4 1.8.6V11z" />
      <circle cx="5" cy="11.2" r="1.3" />
      <circle cx="11" cy="11.2" r="1.3" />
    </svg>
  ),
  top: (
    <svg {...ico}>
      <rect x="5" y="1.8" width="6" height="12.4" rx="2.4" />
      <path d="M5.4 5.3h5.2M5.4 10.7h5.2" />
    </svg>
  ),
  cabin: (
    <svg {...ico}>
      <circle cx="8" cy="8" r="6" />
      <circle cx="8" cy="8" r="1.5" />
      <path d="M2.2 7.6h4.4M9.4 7.6h4.4M8 9.5v4.3" />
    </svg>
  ),
  xray: (
    <svg {...ico}>
      <path d="M8 1.8l5.6 3.1v6.2L8 14.2l-5.6-3.1V4.9zM2.4 4.9L8 8l5.6-3.1M8 8v6.2" />
    </svg>
  ),
};

function ModeIcon({ id, label }: { id: string; label: string }) {
  const s = `${id} ${label}`.toLowerCase();
  if (/eco|econ|range|save/.test(s)) return <LeafIcon />;
  if (/drag|launch|insane|ludicrous/.test(s)) return <FlagIcon />;
  if (/sport|track|race|boost|\bgt\b/.test(s)) return <BoltIcon />;
  if (/snow|sand|mud|off|slip|wet|rain/.test(s)) return <PeakIcon />;
  return <DialIcon />;
}

// ------------------------------------------------------------------------------------------- small parts

/** A dial of 270 degrees, opened at the bottom like the HUD's gauges: `value` (0 to 1) of it lit, the number in its middle. */
function MiniGauge({ value, text, lit, size = 38 }: { value: number; text: string; lit: boolean; size?: number }) {
  const R = 13.5;
  const at = (deg: number) => {
    const a = (deg * Math.PI) / 180;
    return `${(18 + R * Math.cos(a)).toFixed(2)} ${(18 + R * Math.sin(a)).toFixed(2)}`;
  };
  const v = Math.min(1, Math.max(0, value));
  const end = 135 + 270 * v;
  return (
    <svg width={size} height={size} viewBox="0 0 36 36" aria-hidden className="shrink-0">
      <path d={`M ${at(135)} A ${R} ${R} 0 1 1 ${at(405)}`} fill="none" stroke="rgba(255,255,255,0.16)" strokeWidth="2.6" strokeLinecap="round" />
      {v > 0.02 && <path d={`M ${at(135)} A ${R} ${R} 0 ${270 * v > 180 ? 1 : 0} 1 ${at(end)}`} fill="none" stroke={lit ? '#22d3ee' : '#94a3b8'} strokeWidth="2.6" strokeLinecap="round" />}
      <text x="18" y="21" textAnchor="middle" fontSize="9.5" fontWeight="700" fill="#ffffff" fontFamily="'Chakra Petch', sans-serif">
        {text}
      </text>
    </svg>
  );
}

type TileSize = 'bank' | 'strip' | 'mini';

/**
 * One button: an icon over its name (`row`: beside it, for a tile wide enough). `sub` is a second small line. The icon-only form (`mini`)
 * keeps the name for the screen reader and the tooltip.
 */
function Tile({
  on,
  onClick,
  label,
  hint,
  icon,
  tone = 'cyan',
  sub,
  row = false,
  size,
}: {
  on: boolean;
  onClick: () => void;
  label: string;
  hint?: string;
  icon?: React.ReactNode;
  tone?: Tone;
  sub?: string;
  row?: boolean;
  size: TileSize;
}) {
  const showLabel = size !== 'mini' || !icon;
  return (
    <button
      type="button"
      aria-pressed={on}
      aria-label={showLabel ? undefined : label}
      title={hint ?? (showLabel ? undefined : label)}
      onClick={onClick}
      className={`flex min-w-0 items-center justify-center rounded-lg font-bold leading-none transition-all ${DFOCUS} ${row ? 'flex-row gap-2' : 'flex-col gap-[3px]'} ${
        size === 'bank'
          ? row
            ? 'h-[42px] px-2 text-[10px] tracking-wide'
            : 'h-[42px] px-0 text-[9px] tracking-normal'
          : size === 'strip'
            ? 'h-[44px] min-w-[50px] shrink-0 px-1.5 text-[10px] tracking-wide'
            : 'h-8 min-w-[36px] shrink-0 px-2 text-[10px] tracking-wide'
      } ${on ? CHOSEN[tone] : IDLE}`}
    >
      {icon}
      {showLabel && <span className="max-w-full truncate">{label}</span>}
      {showLabel && sub && <span className={`tnum max-w-full truncate text-[9px] font-semibold ${on ? 'text-white/80' : 'text-slate-500'}`}>{sub}</span>}
    </button>
  );
}

/** A group of buttons with its small label above (the icon-only form has no label). */
function Group({ label, size, children, className = '' }: { label: string; size: TileSize; children: React.ReactNode; className?: string }) {
  return (
    <div role="group" aria-label={label} className={`min-w-0 ${className}`}>
      {size !== 'mini' && (
        <div className="mb-1 flex items-center gap-1.5 text-[9px] font-semibold uppercase tracking-[0.16em] text-slate-400">
          <span aria-hidden className="h-px w-2.5 bg-white/35" />
          <span className="truncate">{label}</span>
        </div>
      )}
      {children}
    </div>
  );
}

/** The buttons of a group side by side: equal columns in a bank, as many as there are in a strip. */
function Tiles({ size, cols, children }: { size: TileSize; cols: number; children: React.ReactNode }) {
  return size === 'bank' ? (
    <div className={`grid ${cols > 4 ? 'gap-[3px]' : 'gap-1'}`} style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}>
      {children}
    </div>
  ) : (
    <div className="flex gap-1">{children}</div>
  );
}

// ------------------------------------------------------------------------------------------- the scenario as set

/** The scenario as the visitor has set it (trim, mode, load, run, stop, road and hill): what the planner was given. */
export function useDriveSetup(vehicle: Vehicle): DriveSetup {
  const choice = useVehicleStore((s) => s.drive);
  const variantId = useVehicleStore((s) => s.variantId);
  return React.useMemo(
    () => driveSetup(vehicle, { variantId, runId: choice.run, modeId: choice.mode, loadId: choice.load, brake: choice.brake, surface: choice.surface, grade: choice.grade }),
    [vehicle, variantId, choice.run, choice.mode, choice.load, choice.brake, choice.surface, choice.grade],
  );
}

function useControls(vehicle: Vehicle) {
  const choice = useVehicleStore((s) => s.drive);
  const setDrive = useVehicleStore((s) => s.setDrive);
  const setVariant = useVehicleStore((s) => s.setVariant);
  const setup = useDriveSetup(vehicle);
  const trims = React.useMemo(() => vehicle.variants.filter((v) => v.performance.zeroTo100S !== undefined), [vehicle]);
  return { vehicle, choice, setDrive, setVariant, setup, trims };
}
type Ctl = ReturnType<typeof useControls>;

// ------------------------------------------------------------------------------------------- the groups

const shortName = (name: string) => name.replace(/\s*\(.*\)/, '');

/** One trim as a row: a dial of its power against the strongest, its name and output, and its 0-100 time. A lone trim is the car's identity, not a choice. */
function TrimRow({ t, max, on, pick }: { t: Variant; max: number; on: boolean; pick?: () => void }) {
  const p = t.performance;
  const body = (
    <>
      <MiniGauge size={30} value={p.powerKw / max} text={f0(p.powerKw)} lit={on} />
      <span className="min-w-0 flex-1 text-left">
        <span className={`line-clamp-2 block text-[10.5px] font-bold leading-[1.15] ${on ? 'text-white' : ''}`}>{shortName(t.name)}</span>
        <span className="block truncate text-[9px] font-medium text-slate-400">
          {p.powerKw} kW{p.torqueNm ? ` · ${p.torqueNm} N·m` : ''}
        </span>
      </span>
      <span className="shrink-0 text-right leading-none">
        <span className={`tnum text-[17px] font-bold ${on ? 'text-white' : 'text-slate-200'}`}>{f2(p.zeroTo100S ?? 0)}</span>
        <span className="ml-px text-[9px] font-semibold text-slate-400">s</span>
        <span className="mt-0.5 block text-[7.5px] font-semibold uppercase tracking-[0.14em] text-slate-500">0–100</span>
      </span>
    </>
  );
  const cls = 'flex w-full items-center gap-2 rounded-lg px-1.5 py-1 transition-all';
  return pick ? (
    <button type="button" aria-pressed={on} title={shortName(t.name)} onClick={pick} className={`${cls} ${DFOCUS} ${on ? CHOSEN.cyan : IDLE}`}>
      {body}
    </button>
  ) : (
    <div className={`${cls} bg-white/[0.045] ring-1 ring-white/10`}>{body}</div>
  );
}

function TrimGroup({ c, size }: { c: Ctl; size: TileSize }) {
  const { trims, setup } = c;
  if (!trims.length) return null;
  if (size === 'bank') {
    const max = Math.max(1, ...trims.map((t) => t.performance.powerKw));
    return (
      <Group label={trims.length > 1 ? 'Trim' : 'Powertrain'} size={size}>
        <div className="space-y-1">
          {trims.map((t) => (
            <TrimRow key={t.id} t={t} max={max} on={t.id === setup.variant.id} pick={trims.length > 1 ? () => c.setVariant(t.id) : undefined} />
          ))}
        </div>
      </Group>
    );
  }
  if (trims.length < 2) return null;
  return (
    <Group label="Trim" size={size}>
      <Tiles size={size} cols={trims.length}>
        {trims.map((t) => (
          <Tile key={t.id} size={size} on={t.id === setup.variant.id} onClick={() => c.setVariant(t.id)} label={shortName(t.name)} sub={`${f2(t.performance.zeroTo100S ?? 0)} s`} hint={`${shortName(t.name)} · ${t.performance.powerKw} kW`} />
        ))}
      </Tiles>
    </Group>
  );
}

function ModeGroup({ c, size }: { c: Ctl; size: TileSize }) {
  const { modes, mode } = c.setup;
  if (modes.length < 2) return null;
  const cols = modes.length === 4 ? 2 : Math.min(modes.length, 3);
  return (
    <Group label="Drive mode" size={size}>
      <Tiles size={size} cols={cols}>
        {modes.map((m) => (
          <Tile
            key={m.id}
            size={size}
            row={size === 'bank' && cols === 2}
            on={m.id === mode.id}
            onClick={() => c.setDrive({ mode: m.id })}
            label={m.label}
            hint={m.native}
            tone={toneOfMode(m.id, m.label)}
            icon={<ModeIcon id={m.id} label={m.label} />}
          />
        ))}
      </Tiles>
    </Group>
  );
}

function RoadGroup({ c, size }: { c: Ctl; size: TileSize }) {
  const value = c.choice.surface ?? 'dry';
  return (
    <Group label="Road" size={size}>
      <Tiles size={size} cols={2}>
        <Tile size={size} on={value === 'dry'} onClick={() => c.setDrive({ surface: 'dry' })} label="Dry" hint="The maker’s own run is dry and level" icon={<SunIcon />} />
        <Tile size={size} on={value === 'wet'} onClick={() => c.setDrive({ surface: 'wet' })} label="Wet" hint="The tyres hold about 0.7 g; ours" icon={<DropIcon />} tone="amber" />
      </Tiles>
    </Group>
  );
}

function HillGroup({ c, size }: { c: Ctl; size: TileSize }) {
  const value = c.choice.grade ?? 0;
  return (
    <Group label="Hill" size={size}>
      <Tiles size={size} cols={3}>
        {[
          { pct: -6, label: '−6%', hint: 'Downhill' },
          { pct: 0, label: 'Level', hint: undefined },
          { pct: 6, label: '+6%', hint: 'Uphill' },
        ].map((h) => (
          <Tile key={h.pct} size={size} on={value === h.pct} onClick={() => c.setDrive({ grade: h.pct })} label={h.label} hint={h.hint} icon={<SlopeIcon pct={h.pct} />} />
        ))}
      </Tiles>
    </Group>
  );
}

function ViewGroup({ c, size }: { c: Ctl; size: TileSize }) {
  const cams = camerasOf(c.vehicle);
  const value = c.choice.cam ?? c.setup.camera;
  return (
    <Group label="Camera" size={size}>
      <Tiles size={size} cols={cams.length}>
        {cams.map((id) => (
          <Tile key={id} size={size} on={id === value} onClick={() => c.setDrive({ cam: id })} label={DRIVE_CAMERAS[id].label} icon={CAM_ICON[id]} />
        ))}
      </Tiles>
    </Group>
  );
}

/** What the car carries: the driver alone (the maker's figures), or the car's own family load. */
function LoadGroup({ c, size }: { c: Ctl; size: TileSize }) {
  const { loads, load } = c.setup;
  if (loads.length < 2) return null;
  const base = loads[0].payloadKg;
  return (
    <Group label="Load" size={size} className="flex-1">
      <Tiles size={size} cols={loads.length}>
        {loads.map((l, i) => (
          <Tile
            key={l.id}
            size={size}
            on={l.id === load.id}
            onClick={() => c.setDrive({ load: l.id })}
            label={i === 0 ? l.label : `+${f0(l.payloadKg - base)} kg`}
            hint={`${l.label}, ${l.payloadKg} kg`}
            icon={i === 0 ? <PersonIcon /> : <PeopleIcon />}
          />
        ))}
      </Tiles>
    </Group>
  );
}

/** What the car does when the pull is over: carry on (or coast), or brake to a stop. */
function StopGroup({ c, size }: { c: Ctl; size: TileSize }) {
  const { canBrake, brake, spec } = c.setup;
  if (!canBrake) return null;
  return (
    <Group label="After the run" size={size} className="flex-1">
      <Tiles size={size} cols={2}>
        <Tile size={size} on={!brake} onClick={() => c.setDrive({ brake: false })} label={spec.finish === 'cruise' ? 'Cruise' : 'Coast'} icon={<GoIcon />} />
        <Tile size={size} on={brake} onClick={() => c.setDrive({ brake: true })} label="Stop" hint="Brake to a stop after the pull" icon={<StopIcon />} tone="red" />
      </Tiles>
    </Group>
  );
}

// ------------------------------------------------------------------------------------------- the forms

/** One of the two banks beside the gauges, with the red mark of the panel's old header on its top edge. */
function Bank({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <aside aria-label={label} className={`pointer-events-auto relative flex flex-col justify-center gap-3 rounded-2xl p-2.5 ${BANK}`}>
      <span aria-hidden className="absolute left-3 top-0 h-[2px] w-8 rounded-full bg-[#ff1a2a] shadow-[0_0_8px_rgba(255,26,42,0.7)]" />
      {children}
    </aside>
  );
}

function LeftBank({ c }: { c: Ctl }) {
  return (
    <Bank label="Car controls">
      <TrimGroup c={c} size="bank" />
      <ModeGroup c={c} size="bank" />
    </Bank>
  );
}

function RightBank({ c }: { c: Ctl }) {
  const run = c.setup.loads.length > 1 || c.setup.canBrake;
  return (
    <Bank label="Road and camera controls">
      <div className="flex gap-2.5">
        <div style={{ flex: '2 1 0' }} className="min-w-0">
          <RoadGroup c={c} size="bank" />
        </div>
        <div style={{ flex: '3 1 0' }} className="min-w-0">
          <HillGroup c={c} size="bank" />
        </div>
      </div>
      <ViewGroup c={c} size="bank" />
      {run && (
        <div className="flex gap-2.5">
          <LoadGroup c={c} size="bank" />
          <StopGroup c={c} size="bank" />
        </div>
      )}
    </Bank>
  );
}

/** The fade at the ends of a row that scrolls: it says there is more to reach, and goes when there is not. */
function useScrollFade() {
  const scroller = React.useRef<HTMLDivElement>(null);
  const content = React.useRef<HTMLDivElement>(null);
  const [fade, setFade] = React.useState({ left: false, right: false });
  React.useEffect(() => {
    const el = scroller.current;
    if (!el) return;
    const measure = () => {
      const left = el.scrollLeft > 4;
      const right = el.scrollLeft + el.clientWidth < el.scrollWidth - 4;
      setFade((f) => (f.left === left && f.right === right ? f : { left, right }));
    };
    measure();
    el.addEventListener('scroll', measure, { passive: true });
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    if (content.current) ro.observe(content.current);
    return () => {
      el.removeEventListener('scroll', measure);
      ro.disconnect();
    };
  }, []);
  const mask = `linear-gradient(90deg, ${fade.left ? 'transparent 0, #000 24px' : '#000 0'}, ${fade.right ? '#000 calc(100% - 32px), transparent 100%' : '#000 100%'})`;
  return { scroller, content, style: fade.left || fade.right ? { maskImage: mask, WebkitMaskImage: mask } : undefined };
}

/** A window without room for the banks: every button in one row above the gauges, side to side as far as it fits and scrolling past that. */
function Strip({ c, size }: { c: Ctl; size: 'strip' | 'mini' }) {
  const { setup } = c;
  // what is changed often comes first (a long row scrolls, and what is cut off is the trim, which is chosen once)
  const clusters: { key: string; node: React.ReactNode }[] = [];
  if (setup.modes.length > 1) clusters.push({ key: 'mode', node: <ModeGroup c={c} size={size} /> });
  clusters.push({
    key: 'env',
    node: (
      <div className="flex gap-2.5">
        <RoadGroup c={c} size={size} />
        <HillGroup c={c} size={size} />
      </div>
    ),
  });
  clusters.push({ key: 'view', node: <ViewGroup c={c} size={size} /> });
  if (setup.loads.length > 1 || setup.canBrake) {
    clusters.push({
      key: 'run',
      node: (
        <div className="flex gap-2.5">
          <LoadGroup c={c} size={size} />
          <StopGroup c={c} size={size} />
        </div>
      ),
    });
  }
  if (c.trims.length > 1) clusters.push({ key: 'trim', node: <TrimGroup c={c} size={size} /> });
  const fade = useScrollFade();
  return (
    <div role="group" aria-label="Drive controls" className={`pointer-events-auto w-full max-w-[1000px] rounded-2xl ${BANK}`}>
      <div ref={fade.scroller} className={`hy-scroll flex overflow-x-auto px-3 ${size === 'mini' ? 'py-1.5' : 'py-2'}`} style={fade.style}>
        <div ref={fade.content} className="mx-auto flex shrink-0 items-end gap-3">
          {clusters.map((x) => (
            <div key={x.key} className="shrink-0">
              {x.node}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------------------------------- the result of a run

/**
 * A run's figures in one slim bar above the instruments when it ends: the time, the top speed, the peak pull, the energy, and the stop
 * or the sideways pull where the run has them. Run again; the next car to drive; hide it.
 */
function RunSummary({ vehicle }: { vehicle: Vehicle }) {
  const clock = useTechClock();
  const facts = useRuntime()?.launch?.drive ?? null;
  const setup = useDriveSetup(vehicle);
  const [hidden, setHidden] = React.useState(false);
  // a new run shows its figures again
  React.useEffect(() => setHidden(false), [setup.run.id, setup.mode.id, setup.load.id, setup.variant.id, setup.brake]);
  const done = clock.duration > 0 && clock.t >= clock.duration - 0.05 && !clock.playing;
  if (!done || hidden || !facts) return null;
  const s = facts.summary;
  const tiles: { label: string; value: string; unit: string; note?: string }[] = [];
  if (s.runTime !== null) tiles.push({ label: setup.run.label, value: f2(s.runTime), unit: 's', note: facts.nominal && setup.run.published ? 'published' : 'modelled' });
  tiles.push({ label: 'Top speed', value: f0(s.topKmh), unit: 'km/h' }, { label: 'Peak accel', value: f2(s.peakG), unit: 'g' }, { label: 'Energy', value: f0(s.energyWh), unit: 'Wh' });
  if (s.brakeM !== null) tiles.push({ label: `${f0(s.brakeFromKmh ?? 0)}–0 km/h`, value: f1(s.brakeM), unit: 'm' });
  if (s.peakLatG > 0.05) tiles.push({ label: 'Lateral', value: f2(s.peakLatG), unit: 'g' });
  const next = vehicles.find((v) => v.slug !== vehicle.slug && v.drive);
  return (
    <section aria-label="Run summary" className={`pointer-events-auto flex w-full max-w-[860px] flex-wrap items-center gap-x-4 gap-y-2 rounded-2xl px-3.5 py-2.5 ${BANK} ring-emerald-400/45`}>
      <h3 className="flex shrink-0 items-center gap-2 text-[10px] font-bold uppercase tracking-[0.16em] text-emerald-300">
        <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.9)]" />
        Run complete
      </h3>
      <dl className="flex min-w-0 flex-1 flex-wrap items-end justify-around gap-x-5 gap-y-1.5">
        {tiles.map((t) => (
          <div key={t.label} className="text-center leading-none">
            <dt className="truncate text-[8.5px] font-semibold uppercase tracking-[0.14em] text-slate-400">{t.label}</dt>
            <dd className="mt-1">
              <span className="tnum text-[20px] font-bold text-white">{t.value}</span>
              <span className="ml-1 text-[10px] font-semibold text-slate-400">{t.unit}</span>
            </dd>
            {t.note && <div className={`mt-0.5 text-[8px] font-semibold uppercase tracking-wider ${t.note === 'published' ? 'text-emerald-400' : 'text-slate-500'}`}>{t.note}</div>}
          </div>
        ))}
      </dl>
      <div className="flex shrink-0 items-center gap-1.5">
        <button
          type="button"
          onClick={() => {
            techClock.seek(0);
            techClock.play();
          }}
          className={`rounded-full px-3.5 py-1.5 text-[11px] font-bold tracking-wide ${CHOSEN.cyan} ${DFOCUS}`}
        >
          Run again
        </button>
        {next && (
          <Link href={`/showroom/${next.slug}?tab=drive`} title={`Drive the ${next.brand} ${next.model}`} className={`rounded-full px-3 py-1.5 text-[11px] font-semibold tracking-wide ${IDLE} ${DFOCUS}`}>
            Next car ›
          </Link>
        )}
        <button type="button" aria-label="Hide the summary" onClick={() => setHidden(true)} className={`rounded-full px-2 py-1 text-[13px] leading-none text-slate-400 hover:text-white ${DFOCUS}`}>
          ×
        </button>
      </div>
    </section>
  );
}

// ------------------------------------------------------------------------------------------- the cockpit

/**
 * The Drive tab's dock: the instruments (the speedometer, the tachometer and the gauges between them, `LaunchTools`) with the buttons that
 * set the run built in around them, and the run's figures above when it ends. The playback bar is the dock's next child (Showroom.tsx).
 */
export function DriveCockpit({ vehicle, vw, short }: { vehicle: Vehicle; vw: number; short: boolean }) {
  const form = cockpitForm(vw, short);
  const c = useControls(vehicle);
  return (
    <div className={`pointer-events-none flex w-full flex-col items-center gap-2.5 ${FONT}`}>
      <RunSummary vehicle={vehicle} />
      {form !== 'banks' && <Strip c={c} size={form === 'mini' ? 'mini' : 'strip'} />}
      {form === 'banks' ? (
        <div
          className="pointer-events-none grid w-full max-w-[1400px] items-stretch justify-center gap-3"
          // the gauges take what the banks leave, never more than their own width
          style={{ gridTemplateColumns: `${BANK_W}px minmax(0, 840px) ${BANK_W}px` }}
        >
          <LeftBank c={c} />
          <div className="flex min-w-0 items-end justify-center self-end">
            <LaunchTools vehicle={vehicle} inset={false} />
          </div>
          <RightBank c={c} />
        </div>
      ) : (
        <LaunchTools vehicle={vehicle} inset={false} />
      )}
    </div>
  );
}
