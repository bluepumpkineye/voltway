'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import {
  DRIVE_MODES,
  effectivePowerKw,
  effectiveRange,
  effectiveZeroTo100,
  efficiencyKwhPer100km,
} from '@/lib/performance';
import {
  Card, CardTitle, Row, SegmentBar, Stepper, Tile, Toggle, cx,
  BoltIcon, LockIcon, NextIcon, PauseIcon, PlayIcon, PrevIcon,
} from './ui';

interface ScreenProps {
  vehicle: Vehicle;
  variant: Variant;
  accent: string;
}

const TRACKS = [
  { title: 'Neon Arterial', artist: 'Hong Kong Sunset', album: 'Night Drive' },
  { title: 'Bund at 3AM', artist: 'Shanghai Tape Club', album: 'Long Exposure' },
  { title: 'Gobi Transmission', artist: 'Silk Road Signal', album: 'Dust & Voltage' },
  { title: 'Pearl River Delta', artist: 'Nanfang', album: 'Humidity' },
];

/* ------------------------------------------------------------------- home */
/* The signature three-pane layout: vehicle, navigation, media side by side. */

export function HomeScreen({ variant, accent }: ScreenProps) {
  const { soc, driveMode, climate, openings, headlightsOn, media, setHmiScreen, patchMedia } =
    useVehicleStore();
  const range = effectiveRange(variant, driveMode, soc, climate);
  const track = TRACKS[media.trackIndex % TRACKS.length];
  const anyOpen = Object.values(openings).some(Boolean);

  return (
    <div className="grid h-full grid-cols-[1.06fr_1.28fr_0.92fr] gap-3">
      {/* vehicle pane */}
      <Card className="flex flex-col overflow-hidden">
        <CardTitle>Vehicle</CardTitle>
        <div className="relative flex flex-1 items-center justify-center px-4">
          <CarTopDown accent={accent} openings={openings} headlightsOn={headlightsOn} />
        </div>
        <div className="px-5 pb-4">
          <div className="flex items-baseline gap-2">
            <span className="tnum text-[40px] font-light leading-none text-white">
              {range ? range.km : '--'}
            </span>
            <span className="text-[15px] text-white/45">km remaining</span>
          </div>
          <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{ width: `${soc * 100}%`, background: accent }}
            />
          </div>
          <div className="mt-2 flex justify-between text-[13px] text-white/45">
            <span className="tnum">{Math.round(soc * 100)}%</span>
            <span className={cx(anyOpen && 'text-amber-300')}>
              {anyOpen ? 'Door open' : 'All closed'}
            </span>
          </div>
        </div>
      </Card>

      {/* navigation pane */}
      <Card className="relative flex flex-col overflow-hidden">
        <CardTitle>Navigation</CardTitle>
        <button
          type="button"
          onClick={() => setHmiScreen('nav')}
          className="relative flex-1 overflow-hidden focus:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
          aria-label="Open navigation"
        >
          <MapCanvas accent={accent} range={range?.km ?? 0} />
        </button>
        <div className="px-5 pb-4 pt-3">
          <div className="text-[17px] text-white/90">Xiaomi EV Factory</div>
          <div className="tnum text-[13px] text-white/45">
            Yizhuang, Beijing · 24 min · 18.4 km
          </div>
        </div>
      </Card>

      {/* media pane */}
      <Card className="flex flex-col overflow-hidden">
        <CardTitle>Now Playing</CardTitle>
        <div className="flex flex-1 flex-col items-center justify-center gap-4 px-5">
          <div
            className="flex h-[132px] w-[132px] items-center justify-center rounded-[20px] text-[44px] font-semibold"
            style={{
              background: `linear-gradient(145deg, ${accent}, ${accent}22)`,
              color: '#0a0b0d',
            }}
          >
            {track.title.charAt(0)}
          </div>
          <div className="w-full text-center">
            <div className="truncate text-[18px] font-medium text-white">{track.title}</div>
            <div className="truncate text-[14px] text-white/45">{track.artist}</div>
          </div>
        </div>
        <div className="flex items-center justify-center gap-5 pb-5">
          <button
            type="button"
            aria-label="Previous track"
            onClick={() => patchMedia({ trackIndex: (media.trackIndex + TRACKS.length - 1) % TRACKS.length })}
            className="text-white/60 transition-colors hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
          >
            <PrevIcon />
          </button>
          <button
            type="button"
            aria-label={media.playing ? 'Pause' : 'Play'}
            onClick={() => patchMedia({ playing: !media.playing })}
            className="flex h-14 w-14 items-center justify-center rounded-full transition-transform active:scale-95 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
            style={{ background: accent, color: '#0a0b0d' }}
          >
            {media.playing ? <PauseIcon /> : <PlayIcon />}
          </button>
          <button
            type="button"
            aria-label="Next track"
            onClick={() => patchMedia({ trackIndex: (media.trackIndex + 1) % TRACKS.length })}
            className="text-white/60 transition-colors hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
          >
            <NextIcon />
          </button>
        </div>
      </Card>
    </div>
  );
}

/* ---------------------------------------------------------------- climate */

export function ClimateScreen({ accent }: ScreenProps) {
  const { climate, patchClimate } = useVehicleStore();
  return (
    <div className="grid h-full grid-cols-2 gap-3">
      <Card className="flex flex-col justify-center gap-8 p-6">
        <Stepper
          label="Driver"
          value={climate.driverTempC}
          min={16}
          max={30}
          unit="°C"
          accent={accent}
          onChange={(v) => patchClimate({ driverTempC: v })}
        />
        <div>
          <div className="mb-2 text-[13px] uppercase tracking-[0.16em] text-white/40">
            Driver seat heating
          </div>
          <SegmentBar
            label="Driver seat heating"
            value={climate.seatHeatDriver}
            max={3}
            accent={accent}
            onChange={(v) => patchClimate({ seatHeatDriver: v })}
          />
        </div>
      </Card>

      <Card className="flex flex-col justify-center gap-8 p-6">
        <Stepper
          label="Passenger"
          value={climate.passengerTempC}
          min={16}
          max={30}
          unit="°C"
          accent={accent}
          onChange={(v) => patchClimate({ passengerTempC: v })}
        />
        <div>
          <div className="mb-2 text-[13px] uppercase tracking-[0.16em] text-white/40">
            Passenger seat heating
          </div>
          <SegmentBar
            label="Passenger seat heating"
            value={climate.seatHeatPassenger}
            max={3}
            accent={accent}
            onChange={(v) => patchClimate({ seatHeatPassenger: v })}
          />
        </div>
      </Card>

      <Card className="col-span-2 divide-y divide-white/[0.06]">
        <Row label="Air conditioning" hint="Compressor draws from the traction pack">
          <Toggle
            label="Air conditioning"
            on={climate.acOn}
            accent={accent}
            onChange={(v) => patchClimate({ acOn: v })}
          />
        </Row>
        <div className="flex items-center gap-4 px-5 py-3.5">
          <span className="w-[168px] shrink-0 text-[17px] text-white/90">Fan speed</span>
          <div className="flex-1">
            <SegmentBar
              label="Fan speed"
              value={climate.fanSpeed}
              max={5}
              accent={accent}
              onChange={(v) => patchClimate({ fanSpeed: v })}
            />
          </div>
        </div>
        <Row label="Sync zones" hint="Mirror the driver's temperature to the passenger">
          <Toggle
            label="Sync zones"
            on={climate.sync}
            accent={accent}
            onChange={(v) => patchClimate({ sync: v })}
          />
        </Row>
      </Card>
    </div>
  );
}

/* ------------------------------------------------------------------ drive */

export function DriveScreen({ variant, accent }: ScreenProps) {
  const { driveMode, setDriveMode, soc, climate } = useVehicleStore();
  const power = effectivePowerKw(variant, driveMode);
  const zero = effectiveZeroTo100(variant, driveMode);
  const range = effectiveRange(variant, driveMode, soc, climate);
  const eff = efficiencyKwhPer100km(variant, driveMode, climate);

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="grid grid-cols-4 gap-3" style={{ height: 156 }}>
        {DRIVE_MODES.map((m) => (
          <Tile
            key={m.id}
            active={driveMode === m.id}
            accent={accent}
            icon={<BoltIcon />}
            label={m.label}
            sublabel={m.blurb}
            onClick={() => setDriveMode(m.id)}
          />
        ))}
      </div>

      <Card className="grid flex-1 grid-cols-4 divide-x divide-white/[0.06]">
        <Metric label="Power" value={power} unit="kW" sub={`${Math.round(power * 1.341)} hp`} />
        <Metric label="0–100 km/h" value={zero ?? '--'} unit="s" sub={variant.performance.torqueNm ? `${variant.performance.torqueNm} Nm` : ''} />
        <Metric
          label="Range"
          value={range?.km ?? '--'}
          unit="km"
          sub={range ? `${range.cycle} basis` : ''}
        />
        <Metric label="Consumption" value={eff ?? '--'} unit="kWh/100km" sub="Estimated" />
      </Card>

      <p className="px-1 text-[12px] leading-relaxed text-white/35">
        Manufacturers publish one range figure per variant on one test cycle. The per-mode
        spread shown here is modelled from that figure to illustrate the trade-off — it is not
        a separate homologated number.
      </p>
    </div>
  );
}

function Metric({
  label,
  value,
  unit,
  sub,
}: {
  label: string;
  value: number | string;
  unit: string;
  sub?: string;
}) {
  return (
    <div className="flex flex-col justify-center px-6">
      <span className="text-[13px] uppercase tracking-[0.16em] text-white/40">{label}</span>
      <span className="tnum mt-2 text-[46px] font-light leading-none text-white">{value}</span>
      <span className="mt-1.5 text-[14px] text-white/45">{unit}</span>
      {sub && <span className="tnum mt-0.5 text-[13px] text-white/30">{sub}</span>}
    </div>
  );
}

/* -------------------------------------------------------------------- nav */

export function NavScreen({ variant, accent }: ScreenProps) {
  const { soc, driveMode, climate } = useVehicleStore();
  const range = effectiveRange(variant, driveMode, soc, climate);
  return (
    <div className="grid h-full grid-cols-[1fr_360px] gap-3">
      <Card className="relative overflow-hidden">
        <MapCanvas accent={accent} range={range?.km ?? 0} detailed />
      </Card>
      <div className="flex flex-col gap-3">
        <Card className="p-5">
          <div className="text-[13px] uppercase tracking-[0.16em] text-white/40">Destination</div>
          <div className="mt-2 text-[21px] text-white">Xiaomi EV Factory</div>
          <div className="text-[14px] text-white/45">Yizhuang, Beijing</div>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div>
              <div className="tnum text-[30px] font-light text-white">24</div>
              <div className="text-[13px] text-white/40">min</div>
            </div>
            <div>
              <div className="tnum text-[30px] font-light text-white">18.4</div>
              <div className="text-[13px] text-white/40">km</div>
            </div>
          </div>
        </Card>
        <Card className="flex-1 p-5">
          <div className="text-[13px] uppercase tracking-[0.16em] text-white/40">Range ring</div>
          <p className="mt-2 text-[14px] leading-relaxed text-white/55">
            The shaded circle is how far the car can go on the charge it has now, in the mode
            it is in. Change drive mode or turn the air conditioning off and it grows.
          </p>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="tnum text-[38px] font-light text-white">{range?.km ?? '--'}</span>
            <span className="text-[14px] text-white/45">km · {range?.cycle}</span>
          </div>
        </Card>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ media */

export function MediaScreen({ accent }: ScreenProps) {
  const { media, patchMedia, ambientOn, ambientHue, ambientBrightness, setAmbient } =
    useVehicleStore();
  const track = TRACKS[media.trackIndex % TRACKS.length];

  return (
    <div className="grid h-full grid-cols-[1.15fr_1fr] gap-3">
      <Card className="flex flex-col items-center justify-center gap-6 p-6">
        <div
          className="flex h-[190px] w-[190px] items-center justify-center rounded-[26px] text-[64px] font-semibold"
          style={{ background: `linear-gradient(145deg, ${accent}, ${accent}22)`, color: '#0a0b0d' }}
        >
          {track.title.charAt(0)}
        </div>
        <div className="text-center">
          <div className="text-[24px] font-medium text-white">{track.title}</div>
          <div className="text-[15px] text-white/45">
            {track.artist} · {track.album}
          </div>
        </div>
        <div className="flex items-center gap-7">
          <button
            type="button"
            aria-label="Previous track"
            onClick={() => patchMedia({ trackIndex: (media.trackIndex + TRACKS.length - 1) % TRACKS.length })}
            className="text-white/60 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
          >
            <PrevIcon />
          </button>
          <button
            type="button"
            aria-label={media.playing ? 'Pause' : 'Play'}
            onClick={() => patchMedia({ playing: !media.playing })}
            className="flex h-16 w-16 items-center justify-center rounded-full active:scale-95 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
            style={{ background: accent, color: '#0a0b0d' }}
          >
            {media.playing ? <PauseIcon /> : <PlayIcon />}
          </button>
          <button
            type="button"
            aria-label="Next track"
            onClick={() => patchMedia({ trackIndex: (media.trackIndex + 1) % TRACKS.length })}
            className="text-white/60 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
          >
            <NextIcon />
          </button>
        </div>
        <div className="flex w-full items-center gap-4 px-4">
          <span className="text-[13px] text-white/40">Vol</span>
          <input
            type="range"
            min={0}
            max={100}
            value={media.volume}
            onChange={(e) => patchMedia({ volume: Number(e.target.value) })}
            aria-label="Volume"
            className="h-1.5 flex-1 cursor-pointer appearance-none rounded-full bg-white/12"
            style={{ accentColor: accent }}
          />
          <span className="tnum w-9 text-right text-[13px] text-white/55">{media.volume}</span>
        </div>
      </Card>

      <Card className="flex flex-col p-6">
        <div className="text-[13px] uppercase tracking-[0.16em] text-white/40">
          Ambient lighting
        </div>
        <p className="mt-2 text-[14px] text-white/45">
          Changes the light strips in the cabin behind you.
        </p>

        <div className="mt-5 flex items-center justify-between">
          <span className="text-[17px] text-white/90">Enabled</span>
          <Toggle
            label="Ambient lighting"
            on={ambientOn}
            accent={accent}
            onChange={(v) => setAmbient({ ambientOn: v })}
          />
        </div>

        <div className="mt-6">
          <div className="mb-2 text-[13px] text-white/40">Colour</div>
          <input
            type="range"
            min={0}
            max={360}
            value={ambientHue}
            onChange={(e) => setAmbient({ ambientHue: Number(e.target.value) })}
            aria-label="Ambient colour"
            disabled={!ambientOn}
            className="h-3 w-full cursor-pointer appearance-none rounded-full disabled:opacity-40"
            style={{
              background:
                'linear-gradient(to right, #ff0000, #ffff00, #00ff00, #00ffff, #0000ff, #ff00ff, #ff0000)',
            }}
          />
        </div>

        <div className="mt-6">
          <div className="mb-2 text-[13px] text-white/40">Brightness</div>
          <input
            type="range"
            min={0}
            max={100}
            value={Math.round(ambientBrightness * 100)}
            onChange={(e) => setAmbient({ ambientBrightness: Number(e.target.value) / 100 })}
            aria-label="Ambient brightness"
            disabled={!ambientOn}
            className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-white/12 disabled:opacity-40"
            style={{ accentColor: accent }}
          />
        </div>

        <div
          className="mt-auto h-16 rounded-[16px] transition-all duration-300"
          style={{
            background: ambientOn
              ? `hsl(${ambientHue} 90% ${28 + ambientBrightness * 34}%)`
              : 'rgba(255,255,255,0.05)',
            boxShadow: ambientOn
              ? `0 0 44px -8px hsl(${ambientHue} 95% 55% / ${ambientBrightness})`
              : 'none',
          }}
        />
      </Card>
    </div>
  );
}

/* ------------------------------------------------------------------- adas */

export function AdasScreen({ vehicle, accent }: ScreenProps) {
  const { adasActive, setAdas } = useVehicleStore();
  return (
    <div className="grid h-full grid-cols-[1fr_320px] gap-3">
      <Card className="relative flex items-center justify-center overflow-hidden">
        <PerceptionView accent={accent} active={adasActive} />
      </Card>
      <div className="flex flex-col gap-3">
        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-[17px] text-white/90">Assisted driving</span>
            <Toggle label="Assisted driving" on={adasActive} accent={accent} onChange={setAdas} />
          </div>
          <p className="mt-3 text-[14px] leading-relaxed text-white/45">
            {adasActive
              ? 'Perception active. Surrounding vehicles, lane lines and the planned path are being tracked.'
              : 'Switch on to see the car&rsquo;s view of the road around it.'}
          </p>
        </Card>
        <Card className="flex-1 divide-y divide-white/[0.06]">
          <Row label="Cameras" hint="Surround vision">
            <span className="tnum text-[17px] text-white/70">11</span>
          </Row>
          <Row label="Radar" hint="Millimetre wave">
            <span className="tnum text-[17px] text-white/70">3</span>
          </Row>
          <Row label="Ultrasonic" hint="Close-range parking">
            <span className="tnum text-[17px] text-white/70">12</span>
          </Row>
          <Row label="Cockpit OS" hint={vehicle.cockpit.os}>
            <span className="text-[15px] text-white/70">{vehicle.cockpit.skin}</span>
          </Row>
        </Card>
      </div>
    </div>
  );
}

/* --------------------------------------------------------------- controls */

export function ControlsScreen({ accent }: ScreenProps) {
  const {
    openings, toggleOpening, closeAllOpenings,
    headlightsOn, setHeadlights, locked, setLocked, soc, setSoc,
  } = useVehicleStore();

  const doors: { id: keyof typeof openings; label: string }[] = [
    { id: 'doorFL', label: 'Driver door' },
    { id: 'doorFR', label: 'Passenger door' },
    { id: 'doorRL', label: 'Rear left' },
    { id: 'doorRR', label: 'Rear right' },
    { id: 'frunk', label: 'Frunk' },
    { id: 'boot', label: 'Boot' },
  ];

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="grid grid-cols-3 gap-3" style={{ height: 150 }}>
        {doors.slice(0, 3).map((d) => (
          <Tile
            key={d.id}
            active={openings[d.id]}
            accent={accent}
            icon={<LockIcon />}
            label={d.label}
            sublabel={openings[d.id] ? 'Open' : 'Closed'}
            onClick={() => toggleOpening(d.id)}
          />
        ))}
      </div>
      <div className="grid grid-cols-3 gap-3" style={{ height: 150 }}>
        {doors.slice(3).map((d) => (
          <Tile
            key={d.id}
            active={openings[d.id]}
            accent={accent}
            icon={<LockIcon />}
            label={d.label}
            sublabel={openings[d.id] ? 'Open' : 'Closed'}
            onClick={() => toggleOpening(d.id)}
          />
        ))}
      </div>

      <Card className="flex-1 divide-y divide-white/[0.06]">
        <Row label="Headlights" hint="Changes the lamps on the car behind you">
          <Toggle label="Headlights" on={headlightsOn} accent={accent} onChange={setHeadlights} />
        </Row>
        <Row label="Central locking" hint={locked ? 'Locked' : 'Unlocked'}>
          <Toggle label="Central locking" on={locked} accent={accent} onChange={setLocked} />
        </Row>
        <div className="flex items-center gap-4 px-5 py-3.5">
          <span className="w-[168px] shrink-0 text-[17px] text-white/90">
            Charge level
            <span className="tnum ml-2 text-white/45">{Math.round(soc * 100)}%</span>
          </span>
          <input
            type="range"
            min={5}
            max={100}
            value={Math.round(soc * 100)}
            onChange={(e) => setSoc(Number(e.target.value) / 100)}
            aria-label="State of charge"
            className="h-1.5 flex-1 cursor-pointer appearance-none rounded-full bg-white/12"
            style={{ accentColor: accent }}
          />
        </div>
        <div className="px-5 py-3.5">
          <button
            type="button"
            onClick={closeAllOpenings}
            className="rounded-full px-5 py-2.5 text-[15px] font-medium ring-1 ring-white/15 transition-colors hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
          >
            Close everything
          </button>
        </div>
      </Card>
    </div>
  );
}

/* -------------------------------------------------------------- graphics */

function CarTopDown({
  accent,
  openings,
  headlightsOn,
}: {
  accent: string;
  openings: Record<string, boolean>;
  headlightsOn: boolean;
}) {
  const doorFill = (open: boolean) => (open ? '#f59e0b' : 'rgba(255,255,255,0.16)');
  return (
    <svg viewBox="0 0 200 340" className="h-full max-h-[280px] w-auto" role="img" aria-label="Vehicle status, seen from above">
      <defs>
        <linearGradient id="carbody" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={accent} stopOpacity="0.45" />
          <stop offset="100%" stopColor={accent} stopOpacity="0.14" />
        </linearGradient>
      </defs>
      <path
        d="M100 8c26 0 44 22 50 54 6 30 8 76 8 108s-2 78-8 108c-6 32-24 54-50 54s-44-22-50-54c-6-30-8-76-8-108s2-78 8-108C56 30 74 8 100 8Z"
        fill="url(#carbody)"
        stroke={accent}
        strokeOpacity="0.5"
        strokeWidth="1.5"
      />
      <path d="M70 96h60v66H70z" fill="rgba(255,255,255,0.07)" />
      <rect x="34" y="108" width="14" height="52" rx="4" fill={doorFill(openings.doorFL)} />
      <rect x="152" y="108" width="14" height="52" rx="4" fill={doorFill(openings.doorFR)} />
      <rect x="34" y="176" width="14" height="48" rx="4" fill={doorFill(openings.doorRL)} />
      <rect x="152" y="176" width="14" height="48" rx="4" fill={doorFill(openings.doorRR)} />
      <rect x="76" y="18" width="48" height="14" rx="5" fill={doorFill(openings.frunk)} />
      <rect x="76" y="300" width="48" height="14" rx="5" fill={doorFill(openings.boot)} />
      {headlightsOn && (
        <>
          <path d="M62 10 34 -34h132L138 10Z" fill="#fff8e1" opacity="0.13" />
          <circle cx="74" cy="20" r="5" fill="#fff8e1" />
          <circle cx="126" cy="20" r="5" fill="#fff8e1" />
        </>
      )}
    </svg>
  );
}

function MapCanvas({
  accent,
  range,
  detailed = false,
}: {
  accent: string;
  range: number;
  detailed?: boolean;
}) {
  // range ring scales with the live estimate so the map answers "how far?"
  const r = Math.max(28, Math.min(230, range * 0.34));
  return (
    <svg viewBox="0 0 640 400" className="h-full w-full" role="img" aria-label="Navigation map with range ring">
      <rect width="640" height="400" fill="#0a1018" />
      {Array.from({ length: 13 }).map((_, i) => (
        <line key={`h${i}`} x1="0" y1={i * 32} x2="640" y2={i * 32} stroke="#16202c" strokeWidth="1" />
      ))}
      {Array.from({ length: 21 }).map((_, i) => (
        <line key={`v${i}`} x1={i * 32} y1="0" x2={i * 32} y2="400" stroke="#16202c" strokeWidth="1" />
      ))}
      <path d="M0 260 L180 250 L300 190 L430 176 L640 150" stroke="#1e3a52" strokeWidth="16" fill="none" strokeLinecap="round" />
      <path d="M120 400 L160 250 L210 120 L250 0" stroke="#1e3a52" strokeWidth="12" fill="none" strokeLinecap="round" />
      <path d="M420 400 L444 220 L470 60" stroke="#1e3a52" strokeWidth="10" fill="none" strokeLinecap="round" />

      <circle cx="300" cy="230" r={r} fill={accent} fillOpacity="0.07" stroke={accent} strokeOpacity="0.4" strokeDasharray="6 7" strokeWidth="1.5" />

      <path d="M300 230 L360 200 L430 176 L520 162" stroke={accent} strokeWidth="5" fill="none" strokeLinecap="round" />
      <circle cx="300" cy="230" r="9" fill={accent} />
      <circle cx="300" cy="230" r="17" fill={accent} fillOpacity="0.22" />
      <circle cx="520" cy="162" r="7" fill="#fff" />

      {detailed && (
        <>
          <text x="316" y="222" fill="#7c8798" fontSize="13" fontFamily="system-ui">You</text>
          <text x="486" y="150" fill="#dee3ea" fontSize="13" fontFamily="system-ui">Factory</text>
          <text x="20" y="386" fill="#4a5563" fontSize="12" fontFamily="system-ui">
            Range ring · {range} km
          </text>
        </>
      )}
    </svg>
  );
}

function PerceptionView({ accent, active }: { accent: string; active: boolean }) {
  return (
    <svg viewBox="0 0 620 400" className="h-full w-full" role="img" aria-label="Assisted driving perception view">
      <defs>
        <linearGradient id="road" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#141a22" />
          <stop offset="100%" stopColor="#0a0e13" />
        </linearGradient>
      </defs>
      <rect width="620" height="400" fill="#070a0e" />
      <path d="M170 400 L275 120 L345 120 L450 400Z" fill="url(#road)" />
      {active && (
        <>
          <path d="M310 400 L310 130" stroke={accent} strokeOpacity="0.28" strokeWidth="3" strokeDasharray="22 20" />
          <path d="M196 400 L282 130" stroke="#dee3ea" strokeOpacity="0.30" strokeWidth="2.5" />
          <path d="M424 400 L338 130" stroke="#dee3ea" strokeOpacity="0.30" strokeWidth="2.5" />
          <path d="M262 330 L358 330 L372 396 L248 396Z" fill={accent} fillOpacity="0.20" stroke={accent} strokeWidth="2" />
          <rect x="286" y="196" width="48" height="34" rx="6" fill="#1d2733" stroke="#4a5563" strokeWidth="1.5" />
          <rect x="222" y="234" width="52" height="38" rx="6" fill="#1d2733" stroke="#4a5563" strokeWidth="1.5" />
          <rect x="352" y="176" width="42" height="30" rx="6" fill="#1d2733" stroke="#4a5563" strokeWidth="1.5" />
          <circle cx="310" cy="150" r="4" fill={accent}>
            <animate attributeName="opacity" values="1;0.15;1" dur="1.6s" repeatCount="indefinite" />
          </circle>
        </>
      )}
      {!active && (
        <text x="310" y="210" textAnchor="middle" fill="#4a5563" fontSize="16" fontFamily="system-ui">
          Perception off
        </text>
      )}
    </svg>
  );
}
