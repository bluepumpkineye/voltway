'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore, type Opening } from '@/store/vehicle-store';
import type { DriveMode } from '@/lib/performance';
import { LIGHT_MODES } from '@/lib/lights';
import {
  cx,
  Card,
  CardTitle,
  Row,
  Toggle,
  LockIcon,
  PlayIcon,
  PauseIcon,
  NextIcon,
  PrevIcon,
} from '../ui';
import { useBanyan } from './theme';
import { useBanyanLocal } from './shared';
import {
  QueenSeatIcon,
  Chassis4DIcon,
  AirSuspensionIcon,
  DolbyAtmosIcon,
  LightLowIcon,
} from './icons';

const AMBIENT_COLORS = [
  { name: 'Pure Cyan', hex: '#00C2A8', hue: 172 },
  { name: 'Skyline Blue', hex: '#0084FF', hue: 210 },
  { name: 'Executive Gold', hex: '#D4AF37', hue: 45 },
  { name: 'Aurora Green', hex: '#10B981', hue: 155 },
  { name: 'Sunset Amber', hex: '#F59E0B', hue: 35 },
  { name: 'Lavender Purple', hex: '#8B5CF6', hue: 270 },
  { name: 'Lunar White', hex: '#FFFFFF', hue: 0 },
];

/* ------------------------------------------------------------- ControlsPage */

export function ControlsPage({
  vehicle,
  variant,
  forceTab,
}: {
  vehicle: Vehicle;
  variant: Variant;
  forceTab?: string;
}) {
  const t = useBanyan();
  const {
    openings,
    toggleOpening,
    closeAllOpenings,
    headlightsOn,
    setHeadlights,
    lightMode,
    setLightMode,
    highBeam,
    setHighBeam,
    locked,
    setLocked,
    easyEntry,
    setEasyEntry,
  } = useVehicleStore();
  const { speakNomi } = useBanyanLocal();

  const initialTab =
    forceTab === 'lights' || forceTab === 'doors' || forceTab === 'mirrors'
      ? forceTab
      : 'quick';
  const [tab, setTab] = React.useState<'quick' | 'lights' | 'doors' | 'mirrors'>(initialTab);
  const [ambientHue, setAmbientHue] = React.useState(172);
  const [ambientBri, setAmbientBri] = React.useState(80);
  const [sunshade, setSunshade] = React.useState(false);
  const [autoFoldMirrors, setAutoFoldMirrors] = React.useState(true);
  const [childLock, setChildLock] = React.useState(false);

  const TABS = [
    { id: 'quick', label: 'Quick Controls · 快捷控制' },
    { id: 'lights', label: 'Exterior & Ambient Lights · 灯光' },
    { id: 'doors', label: 'Doors & Tailgate · 车门车窗' },
    { id: 'mirrors', label: 'Mirrors & Sunroof · 后视镜与天幕' },
  ] as const;

  return (
    <div className="flex h-full flex-col p-6 select-none">
      {/* Header Info */}
      <div className="flex items-center justify-between mb-3 text-[12px] text-white/40">
        <span>{vehicle.brand} {vehicle.model} · {variant.name}</span>
        <span>Vehicle Master Control</span>
      </div>

      {/* Subpage Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-white/[0.08] pb-4">
        {TABS.map((tb) => (
          <button
            key={tb.id}
            type="button"
            onClick={() => setTab(tb.id)}
            className={cx(
              'rounded-xl px-4 py-2 text-[14px] font-medium transition-all focus:outline-none',
              tab === tb.id
                ? 'bg-[#00C2A8] text-black font-semibold shadow-[0_0_15px_rgba(0,194,168,0.35)]'
                : 'bg-white/[0.06] text-white/70 hover:bg-white/[0.12]',
            )}
          >
            {tb.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto pt-5 min-h-0">
        {tab === 'quick' && (
          <div className="grid grid-cols-3 gap-4">
            <Card className="flex flex-col justify-between p-5">
              <span className="text-[13px] uppercase tracking-wider text-white/40">Headlamps</span>
              <div className="my-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span
                    className="flex h-11 w-11 items-center justify-center rounded-2xl"
                    style={{
                      background: headlightsOn ? '#00C2A8' : 'rgba(255,255,255,0.08)',
                      color: headlightsOn ? '#000000' : '#ffffff',
                    }}
                  >
                    <LightLowIcon size={22} />
                  </span>
                  <div>
                    <span className="text-[16px] font-medium text-white/95">Master Lights</span>
                    <span className="block text-[12px] text-white/45">
                      {headlightsOn ? 'Low Beam Active' : 'Off'}
                    </span>
                  </div>
                </div>
                <Toggle
                  label="Headlamps"
                  on={headlightsOn}
                  accent={t.accent}
                  onChange={(v) => {
                    setHeadlights(v);
                    speakNomi(v ? 'Headlamps on' : 'Headlamps off');
                  }}
                />
              </div>
              <div className="grid grid-cols-4 gap-1.5 pt-2 border-t border-white/[0.06]">
                {LIGHT_MODES.map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => {
                      setLightMode(m);
                      if (m !== 'off') setHeadlights(true);
                      else setHeadlights(false);
                    }}
                    className={cx(
                      'rounded-lg py-1.5 text-[11px] font-medium capitalize transition-all',
                      lightMode === m
                        ? 'bg-white/20 text-white ring-1 ring-white/30'
                        : 'bg-white/[0.04] text-white/50 hover:bg-white/[0.08]',
                    )}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </Card>

            <Card className="flex flex-col justify-between p-5">
              <span className="text-[13px] uppercase tracking-wider text-white/40">Central Locking</span>
              <div className="my-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span
                    className="flex h-11 w-11 items-center justify-center rounded-2xl"
                    style={{
                      background: locked ? '#00C2A8' : 'rgba(255,255,255,0.08)',
                      color: locked ? '#000000' : '#ffffff',
                    }}
                  >
                    <LockIcon />
                  </span>
                  <div>
                    <span className="text-[16px] font-medium text-white/95">Door Locks</span>
                    <span className="block text-[12px] text-white/45">
                      {locked ? 'All 4 Doors Locked' : 'Unlocked'}
                    </span>
                  </div>
                </div>
                <Toggle
                  label="Locking"
                  on={locked}
                  accent={t.accent}
                  onChange={(v) => {
                    setLocked(v);
                    speakNomi(v ? 'Doors secured' : 'Doors unlocked');
                  }}
                />
              </div>
              <button
                type="button"
                onClick={closeAllOpenings}
                className="w-full rounded-xl bg-white/[0.06] py-2 text-[12px] font-medium text-white/80 hover:bg-white/[0.12] transition-colors"
              >
                Close All Doors & Hatches
              </button>
            </Card>

            <Card className="flex flex-col justify-between p-5">
              <span className="text-[13px] uppercase tracking-wider text-white/40">Comfort Access</span>
              <div className="my-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span
                    className="flex h-11 w-11 items-center justify-center rounded-2xl"
                    style={{
                      background: easyEntry ? '#00C2A8' : 'rgba(255,255,255,0.08)',
                      color: easyEntry ? '#000000' : '#ffffff',
                    }}
                  >
                    <AirSuspensionIcon size={22} />
                  </span>
                  <div>
                    <span className="text-[16px] font-medium text-white/95">Easy Entry / Exit</span>
                    <span className="block text-[12px] text-white/45">Lowers air springs by 50 mm</span>
                  </div>
                </div>
                <Toggle
                  label="Easy Entry"
                  on={easyEntry}
                  accent={t.accent}
                  onChange={(v) => {
                    setEasyEntry(v);
                    speakNomi(v ? 'Easy Entry active' : 'Easy Entry disabled');
                  }}
                />
              </div>
              <div className="text-[11px] text-white/40">
                Automatically squats when parked for effortless ingress.
              </div>
            </Card>

            {/* Individual Door Opening Controls */}
            <Card className="col-span-3 p-5">
              <CardTitle className="p-0 mb-3">Individual Door & Hatch Controls</CardTitle>
              <div className="grid grid-cols-6 gap-3">
                {[
                  { id: 'frunk', label: 'Front Frunk', open: openings.frunk },
                  { id: 'doorFL', label: 'Driver FL', open: openings.doorFL },
                  { id: 'doorFR', label: 'Passenger FR', open: openings.doorFR },
                  { id: 'doorRL', label: 'Rear Left RL', open: openings.doorRL },
                  { id: 'doorRR', label: 'Rear Right RR', open: openings.doorRR },
                  { id: 'boot', label: 'Electric Tailgate', open: openings.boot },
                ].map((d) => (
                  <button
                    key={d.id}
                    type="button"
                    onClick={() => toggleOpening(d.id as Opening)}
                    className={cx(
                      'flex flex-col items-center justify-center rounded-2xl p-4 text-center transition-all',
                      d.open
                        ? 'bg-amber-400/20 text-amber-300 ring-1 ring-amber-400/50'
                        : 'bg-white/[0.05] text-white/70 hover:bg-white/[0.09]',
                    )}
                  >
                    <span className="mb-2 text-[20px]">{d.open ? '🔓' : '🔒'}</span>
                    <span className="text-[13px] font-medium text-white">{d.label}</span>
                    <span className="mt-0.5 text-[11px] text-white/40">
                      {d.open ? 'Open' : 'Closed'}
                    </span>
                  </button>
                ))}
              </div>
            </Card>
          </div>
        )}

        {tab === 'lights' && (
          <div className="grid grid-cols-2 gap-4">
            <Card className="p-6 space-y-4">
              <CardTitle className="p-0">Exterior Intelligent Lightbar (illumiBlade)</CardTitle>
              <div className="space-y-3">
                <Row label="High Beam">
                  <Toggle
                    label="High beam"
                    on={highBeam}
                    accent={t.accent}
                    onChange={(v) => setHighBeam(v)}
                  />
                </Row>
                <Row label="ADB Adaptive Matrix" hint="Auto anti-glare high beam tracking">
                  <Toggle label="ADB" on={true} accent={t.accent} onChange={() => {}} />
                </Row>
                <Row label="Courtesy Ground Projection" hint="NIO welcoming logo projection">
                  <Toggle label="Projection" on={true} accent={t.accent} onChange={() => {}} />
                </Row>
              </div>
            </Card>

            <Card className="p-6 space-y-4">
              <CardTitle className="p-0">256-Color Dynamic Ambient Light (氛围灯)</CardTitle>
              <div className="flex items-center gap-3 pt-2">
                {AMBIENT_COLORS.map((c) => (
                  <button
                    key={c.name}
                    type="button"
                    onClick={() => {
                      setAmbientHue(c.hue);
                      speakNomi(`Ambient light changed to ${c.name}`);
                    }}
                    style={{ background: c.hex }}
                    className={cx(
                      'h-9 w-9 rounded-full transition-transform hover:scale-110 shadow-md',
                      ambientHue === c.hue ? 'ring-4 ring-white scale-110' : 'opacity-80',
                    )}
                    title={c.name}
                  />
                ))}
              </div>
              <div className="pt-4 border-t border-white/[0.08]">
                <div className="flex justify-between text-[13px] text-white/70 mb-2">
                  <span>Brightness</span>
                  <span className="tnum font-medium text-white">{ambientBri}%</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="100"
                  value={ambientBri}
                  onChange={(e) => setAmbientBri(Number(e.target.value))}
                  className="w-full accent-[#00C2A8]"
                />
              </div>
            </Card>
          </div>
        )}

        {tab === 'doors' && (
          <div className="grid grid-cols-2 gap-4">
            <Card className="p-6 space-y-4">
              <CardTitle className="p-0">Power Soft-Close Doors & Hatches</CardTitle>
              <div className="space-y-3">
                <Row label="Soft-Close Electric Suction" hint="Automatic silent latching on all 4 doors">
                  <Toggle label="Soft close" on={true} accent={t.accent} onChange={() => {}} />
                </Row>
                <Row label="Child Safety Locks" hint="Disables rear inner door handles and window buttons">
                  <Toggle
                    label="Child lock"
                    on={childLock}
                    accent={t.accent}
                    onChange={(v) => {
                      setChildLock(v);
                      speakNomi(v ? 'Child safety lock engaged' : 'Child lock disengaged');
                    }}
                  />
                </Row>
              </div>
            </Card>

            <Card className="p-6 space-y-4">
              <CardTitle className="p-0">Electric Tailgate Configuration</CardTitle>
              <div className="space-y-3">
                <Row label="Foot Kick Sensor" hint="Hands-free tailgate opening">
                  <Toggle label="Kick sensor" on={true} accent={t.accent} onChange={() => {}} />
                </Row>
                <div className="pt-2">
                  <span className="text-[13px] text-white/70">Tailgate Height Memory</span>
                  <div className="mt-2 flex gap-2">
                    {['75%', '85%', '95%', '100%'].map((lvl) => (
                      <button
                        key={lvl}
                        type="button"
                        className="flex-1 rounded-xl bg-white/[0.06] py-2 text-[12px] font-medium text-white hover:bg-white/[0.12]"
                      >
                        {lvl}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}

        {tab === 'mirrors' && (
          <div className="grid grid-cols-2 gap-4">
            <Card className="p-6 space-y-4">
              <CardTitle className="p-0">Power Mirrors</CardTitle>
              <div className="space-y-3">
                <Row label="Auto-Fold on Lock" hint="Folds mirrors when vehicle locks">
                  <Toggle
                    label="Auto fold"
                    on={autoFoldMirrors}
                    accent={t.accent}
                    onChange={setAutoFoldMirrors}
                  />
                </Row>
                <Row label="Auto-Tilt in Reverse" hint="Angles curb mirror down while parking">
                  <Toggle label="Auto tilt" on={true} accent={t.accent} onChange={() => {}} />
                </Row>
                <Row label="Electrochromic Auto-Dimming" hint="Reduces headlight glare from behind">
                  <Toggle label="Auto dim" on={true} accent={t.accent} onChange={() => {}} />
                </Row>
              </div>
            </Card>

            <Card className="p-6 space-y-4">
              <CardTitle className="p-0">Panoramic Glass Roof & Sunshade</CardTitle>
              <div className="space-y-3">
                <Row label="Electric Sunshade" hint={sunshade ? 'Open' : 'Closed'}>
                  <Toggle
                    label="Sunshade"
                    on={sunshade}
                    accent={t.accent}
                    onChange={(v) => {
                      setSunshade(v);
                      speakNomi(v ? 'Sunshade opened' : 'Sunshade closed');
                    }}
                  />
                </Row>
                <Row label="Solar Heat Insulation (UV 99.9%)" hint="Multi-layer low-E coating">
                  <span className="text-[13px] text-emerald-400 font-medium">Optimal</span>
                </Row>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

/* -------------------------------------------------------------- ChassisPage */

export function ChassisPage({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  const { driveMode, setDriveMode, rideLevel, setRideLevel } = useVehicleStore();
  const { speakNomi } = useBanyanLocal();

  const LEVELS = [
    { level: 0, label: 'Very High', mm: '+50 mm', ground: '230 mm' },
    { level: 1, label: 'High', mm: '+25 mm', ground: '205 mm' },
    { level: 2, label: 'Standard', mm: '0 mm', ground: '180 mm' },
    { level: 3, label: 'Low', mm: '-15 mm', ground: '165 mm' },
    { level: 4, label: 'Very Low', mm: '-50 mm', ground: '130 mm' },
  ] as const;

  return (
    <div className="flex h-full flex-col p-6 select-none overflow-y-auto min-h-0">
      <div className="flex items-center justify-between mb-4 text-[12px] text-white/40">
        <span>{vehicle.brand} {vehicle.model} · {variant.name}</span>
        <span>Dual-Chamber Air Suspension & CDC</span>
      </div>

      <div className="grid grid-cols-[1.2fr_1fr] gap-6">
        {/* Left: Dual-Chamber Air Suspension Level Controller */}
        <Card className="p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <CardTitle className="p-0">Dual-Chamber Air Suspension (双腔空气悬架)</CardTitle>
                <span className="text-[12px] text-white/45">
                  5-Level Active Height Control · Continuous Damping Control (CDC)
                </span>
              </div>
              <span className="rounded-full bg-[#00C2A8]/15 px-3 py-1 text-[12px] font-bold text-[#00C2A8]">
                Ground: {LEVELS.find((l) => l.level === rideLevel)?.ground ?? '180 mm'}
              </span>
            </div>

            <div className="grid grid-cols-5 gap-2 my-6">
              {LEVELS.map((lvl) => {
                const active = rideLevel === lvl.level;
                return (
                  <button
                    key={lvl.level}
                    type="button"
                    onClick={() => {
                      setRideLevel(lvl.level);
                      speakNomi(`Air suspension adjusting to ${lvl.label} height`);
                    }}
                    className={cx(
                      'flex flex-col items-center justify-between rounded-2xl p-3.5 text-center transition-all',
                      active
                        ? 'bg-[#00C2A8] text-black font-semibold shadow-[0_0_15px_rgba(0,194,168,0.5)]'
                        : 'bg-white/[0.06] text-white/70 hover:bg-white/[0.12]',
                    )}
                  >
                    <span className="text-[12px] leading-tight font-medium">{lvl.label}</span>
                    <span className="my-2 text-[18px]">{lvl.mm}</span>
                    <span className="text-[10px] opacity-75">{lvl.ground}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex flex-col gap-2.5">
            <div className="rounded-2xl bg-white/[0.04] p-3.5 border border-white/[0.06]">
              <div className="flex items-center gap-3">
                <Chassis4DIcon size={22} />
                <div>
                  <span className="text-[13px] font-medium text-white">NIO 4D Dynamic Chassis</span>
                  <span className="block text-[11px] text-white/45">
                    Road preview via Aquila LiDAR and 8MP camera; predicts bumps 150m ahead
                  </span>
                </div>
              </div>
            </div>

            <div className="rounded-2xl bg-white/[0.04] p-3.5 border border-white/[0.06] flex items-center justify-between">
              <div>
                <span className="text-[13px] font-medium text-white">Front & Rear 5-Link Suspensions</span>
                <span className="block text-[11px] text-white/45">
                  Forged aluminum virtual kingpin geometry · 5.7 m turning radius
                </span>
              </div>
              <span className="rounded-full bg-[#00C2A8]/15 px-2.5 py-0.5 text-[11px] font-bold text-[#00C2A8]">
                5.7 m
              </span>
            </div>
          </div>
        </Card>

        {/* Right: Drive Mode Selector */}
        <Card className="p-6">
          <CardTitle className="p-0 mb-3">Drive Modes (驾驶模式)</CardTitle>
          <div className="grid grid-cols-2 gap-2.5">
            {(vehicle.cockpit.driveModes ?? []).map((m) => {
              const active = driveMode === m.id;
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => {
                    setDriveMode(m.id as DriveMode);
                    speakNomi(`Switched to ${m.label} mode!`);
                  }}
                  className={cx(
                    'flex flex-col items-start rounded-2xl p-4 transition-all',
                    active
                      ? 'bg-[#00C2A8] text-black shadow-[0_0_15px_rgba(0,194,168,0.4)]'
                      : 'bg-white/[0.06] text-white/80 hover:bg-white/[0.10]',
                  )}
                >
                  <span className="text-[16px] font-semibold">{m.label}</span>
                  <span className={cx('text-[11px] mt-0.5', active ? 'text-black/75' : 'text-white/40')}>
                    {m.native ?? m.id}
                  </span>
                </button>
              );
            })}
          </div>
        </Card>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- SeatsPage */

export function SeatsPage({ vehicle }: { vehicle: Vehicle }) {
  const { queenSeatLounge, setQueenSeatLounge, seatMassage, setSeatMassage, speakNomi } =
    useBanyanLocal();

  const MASSAGES = ['Off', 'Wave · 波浪', 'Pulse · 脉冲', 'Catwalk · 揉捏', 'Lumbar · 腰部舒缓'];

  return (
    <div className="flex h-full flex-col p-6 select-none overflow-y-auto min-h-0">
      <div className="flex items-center justify-between mb-4 text-[12px] text-white/40">
        <span>{vehicle.brand} {vehicle.model} Executive Seating Suite</span>
        <span>20-Way Power Adjustment with Ottoman</span>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Executive Queen Co-pilot Seat (女王副驾) */}
        <Card className="p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-400/20 text-amber-300">
                  <QueenSeatIcon size={24} />
                </span>
                <div>
                  <CardTitle className="p-0">Executive Queen Co-pilot Seat (女王副驾)</CardTitle>
                  <span className="text-[12px] text-white/45">
                    One-Touch Zero-Gravity Lounge · 160° Power Recline & Leg Rest
                  </span>
                </div>
              </div>
              <span
                className={cx(
                  'rounded-full px-3 py-1 text-[12px] font-bold',
                  queenSeatLounge ? 'bg-amber-400 text-black' : 'bg-white/10 text-white/50',
                )}
              >
                {queenSeatLounge ? 'Lounge Active' : 'Standard'}
              </span>
            </div>

            <div className="my-6 flex justify-center">
              <button
                type="button"
                onClick={() => {
                  setQueenSeatLounge(!queenSeatLounge);
                  speakNomi(
                    queenSeatLounge
                      ? 'Queen Seat returning to standard'
                      : 'Queen Seat zero-gravity lounge deployed! Enjoy your rest.',
                  );
                }}
                className={cx(
                  'w-full max-w-sm rounded-2xl py-4 text-[16px] font-semibold transition-all shadow-lg',
                  queenSeatLounge
                    ? 'bg-amber-400 text-black shadow-amber-400/30'
                    : 'bg-white/10 text-white hover:bg-white/15',
                )}
              >
                {queenSeatLounge ? 'Restore Standard Seating' : 'One-Touch Zero Gravity (一键零重力)'}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-[12px] text-white/70 border-t border-white/[0.08] pt-4">
            <div>
              <span className="block text-white/40">Power Leg Rest</span>
              <span className="font-medium text-white">68° Upward Extension</span>
            </div>
            <div>
              <span className="block text-white/40">Foot Rest Cushion</span>
              <span className="font-medium text-white">Integrated Heating</span>
            </div>
          </div>
        </Card>

        {/* 8-Point Stone Massage & Climate */}
        <Card className="p-6 flex flex-col justify-between">
          <div>
            <CardTitle className="p-0 mb-4">Hot Stone Massage & Air Cushion (8点SPA按摩)</CardTitle>
            <div className="grid grid-cols-2 gap-2 my-4">
              {MASSAGES.map((name, idx) => (
                <button
                  key={name}
                  type="button"
                  onClick={() => {
                    setSeatMassage(idx);
                    speakNomi(`Seat massage: ${name}`);
                  }}
                  className={cx(
                    'rounded-xl p-3 text-left transition-all',
                    seatMassage === idx
                      ? 'bg-[#00C2A8] text-black font-semibold'
                      : 'bg-white/[0.06] text-white/70 hover:bg-white/[0.10]',
                  )}
                >
                  <span className="text-[13px]">{name}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-3 border-t border-white/[0.08] pt-4">
            <Row label="3-Level Seat Ventilation">
              <span className="text-[13px] text-[#00C2A8] font-medium">Level 2 Active</span>
            </Row>
            <Row label="3-Level Seat Heating">
              <span className="text-[13px] text-amber-400 font-medium">Level 1 Warm</span>
            </Row>
          </div>
        </Card>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------- ClimatePage */

export function ClimatePage({ vehicle }: { vehicle: Vehicle }) {
  const t = useBanyan();
  const { climate, patchClimate } = useVehicleStore();
  const { fragrance, setFragrance, airQualityIonizer, setAirQualityIonizer, speakNomi } =
    useBanyanLocal();

  const FRAGRANCES = [
    { id: 'forest', name: 'Cedar Forest (沉香林海)' },
    { id: 'sunlight', name: 'Sunlit Citrus (晨露柑橘)' },
    { id: 'ocean', name: 'Pacific Breeze (太平洋微风)' },
    { id: 'off', name: 'Fragrance Off' },
  ] as const;

  return (
    <div className="flex h-full flex-col p-6 select-none overflow-y-auto min-h-0">
      <div className="flex items-center justify-between mb-4 text-[12px] text-white/40">
        <span>{vehicle.brand} {vehicle.model} Tri-Zone Heat Pump Climate</span>
        <span>PM2.5 Sensor · CN95 Bio-Filter</span>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <Card className="p-6 space-y-4">
          <CardTitle className="p-0">Tri-Zone Heat Pump Automatic Climate</CardTitle>
          <div className="flex items-center justify-around py-4 bg-white/[0.03] rounded-2xl">
            <div className="text-center">
              <span className="text-[12px] text-white/40">Driver</span>
              <div className="tnum text-[32px] font-light text-white">
                {climate.driverTempC.toFixed(1)}°C
              </div>
            </div>
            <div className="text-center">
              <span className="text-[12px] text-white/40">A/C Mode</span>
              <div className="text-[20px] font-medium text-[#00C2A8]">Auto Cool</div>
            </div>
            <div className="text-center">
              <span className="text-[12px] text-white/40">Passenger</span>
              <div className="tnum text-[32px] font-light text-white">
                {climate.passengerTempC.toFixed(1)}°C
              </div>
            </div>
          </div>
          <div className="space-y-3">
            <Row label="A/C Compressor">
              <Toggle
                label="AC"
                on={climate.acOn}
                accent={t.accent}
                onChange={(v) => patchClimate({ acOn: v })}
              />
            </Row>
            <Row label="Air Clean Ionizer & PM2.5 Purifier">
              <Toggle
                label="Ionizer"
                on={airQualityIonizer}
                accent={t.accent}
                onChange={setAirQualityIonizer}
              />
            </Row>
          </div>
        </Card>

        <Card className="p-6 space-y-4">
          <CardTitle className="p-0">Intelligent Fragrance System (智能香氛)</CardTitle>
          <div className="grid grid-cols-2 gap-2 pt-2">
            {FRAGRANCES.map((f) => (
              <button
                key={f.id}
                type="button"
                onClick={() => {
                  setFragrance(f.id);
                  speakNomi(`Fragrance selected: ${f.name}`);
                }}
                className={cx(
                  'rounded-xl p-3 text-left transition-all',
                  fragrance === f.id
                    ? 'bg-[#00C2A8] text-black font-semibold'
                    : 'bg-white/[0.06] text-white/70 hover:bg-white/[0.10]',
                )}
              >
                <span className="text-[13px]">{f.name}</span>
              </button>
            ))}
          </div>
          <div className="rounded-xl bg-white/[0.04] p-4 text-[12px] text-white/60">
            Selected cartridge released seamlessly through invisible micro-vents.
          </div>
        </Card>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ NavPage */

export function NavPage() {
  const { soc } = useVehicleStore();
  const { speakNomi } = useBanyanLocal();

  return (
    <div className="relative h-full w-full select-none overflow-hidden bg-[#080d14] p-6">
      <div className="absolute inset-0 opacity-20 pointer-events-none">
        <svg width="100%" height="100%">
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="0.8" />
          </pattern>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      <div className="relative z-10 flex h-full gap-4">
        <Card className="w-80 p-5 flex flex-col justify-between">
          <div>
            <CardTitle className="p-0 mb-3">NIO Navigation (百度地图·蔚来版)</CardTitle>
            <div className="rounded-xl bg-white/[0.06] p-3 text-[13px] text-white/80">
              📍 Current: Shanghai International Circuit
            </div>
            <div className="mt-4 space-y-2">
              <span className="text-[12px] text-white/40">Nearby Power Swap Stations</span>
              {[
                { name: 'Suzhou High-Speed Hub 3.0', dist: '1.8 km', packs: '14 packs' },
                { name: 'Kunshan Power Swap 3.0', dist: '6.2 km', packs: '9 packs' },
                { name: 'Hongqiao Terminal Swap', dist: '14.5 km', packs: '21 packs' },
              ].map((st) => (
                <button
                  key={st.name}
                  type="button"
                  onClick={() => speakNomi(`Routing to ${st.name}`)}
                  className="w-full flex items-center justify-between rounded-xl bg-white/[0.04] p-2.5 text-left text-[12px] hover:bg-white/[0.08]"
                >
                  <div>
                    <span className="block font-medium text-white">{st.name}</span>
                    <span className="text-[11px] text-[#00C2A8]">{st.packs} available</span>
                  </div>
                  <span className="text-white/40">{st.dist}</span>
                </button>
              ))}
            </div>
          </div>
          <div className="rounded-xl bg-[#00C2A8]/15 p-3 text-[12px] text-[#00C2A8] font-medium text-center">
            Reachable Range: ~{Math.round(soc * 605)} km (CLTC Ring)
          </div>
        </Card>

        {/* Map visualization area */}
        <div className="flex-1 rounded-[22px] bg-white/[0.02] ring-1 ring-white/[0.08] relative overflow-hidden flex items-center justify-center">
          <div className="relative flex flex-col items-center justify-center">
            <div className="h-64 w-64 rounded-full border border-[#00C2A8]/30 flex items-center justify-center animate-pulse">
              <div className="h-44 w-44 rounded-full border border-[#00C2A8]/60 flex items-center justify-center">
                <span className="h-4 w-4 rounded-full bg-[#00C2A8] shadow-[0_0_15px_#00C2A8]" />
              </div>
            </div>
            <span className="mt-4 text-[14px] font-medium text-white/70">
              NIO Navigation Active · Reachable Radius Shown
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- MediaPage */

export function MediaPage() {
  const { media, patchMedia } = useVehicleStore();

  return (
    <div className="flex h-full flex-col p-6 select-none justify-between">
      <div className="flex items-center gap-3">
        <DolbyAtmosIcon size={24} />
        <div>
          <CardTitle className="p-0">PanoCinema 7.1.4 Dolby Atmos (蔚来沉浸声)</CardTitle>
          <span className="text-[12px] text-white/45">
            23 High-Fidelity Speakers · 1000W Dirac Pro DSP Matrix
          </span>
        </div>
      </div>

      <div className="my-auto flex items-center justify-center gap-12">
        <div className="h-56 w-56 rounded-3xl bg-gradient-to-tr from-[#00C2A8] to-blue-600 flex items-center justify-center text-[54px] shadow-2xl">
          🎵
        </div>
        <div className="space-y-4">
          <span className="rounded-full bg-[#00C2A8]/20 px-3 py-1 text-[12px] font-bold text-[#00C2A8]">
            Master Tape Audio · 192kHz/24bit
          </span>
          <div className="text-[32px] font-semibold text-white">Neon Arterial</div>
          <div className="text-[18px] text-white/60">NIO Radio · 7.1.4 Surround Mix</div>
          <div className="flex items-center gap-4 pt-4">
            <button
              type="button"
              onClick={() => patchMedia({ trackIndex: Math.max(0, media.trackIndex - 1) })}
              className="flex h-12 w-12 items-center justify-center rounded-full bg-white/[0.08] text-white hover:bg-white/[0.15]"
            >
              <PrevIcon />
            </button>
            <button
              type="button"
              onClick={() => patchMedia({ playing: !media.playing })}
              className="flex h-16 w-16 items-center justify-center rounded-full bg-[#00C2A8] text-black shadow-xl hover:scale-105 active:scale-95 transition-all"
            >
              {media.playing ? <PauseIcon /> : <PlayIcon />}
            </button>
            <button
              type="button"
              onClick={() => patchMedia({ trackIndex: media.trackIndex + 1 })}
              className="flex h-12 w-12 items-center justify-center rounded-full bg-white/[0.08] text-white hover:bg-white/[0.15]"
            >
              <NextIcon />
            </button>
          </div>
        </div>
      </div>

      <div className="flex justify-between items-center border-t border-white/[0.08] pt-4 text-[13px] text-white/40">
        <span>Sound Field: Center All Passengers</span>
        <span>Acoustic Enhancement: Dirac Live Room Correction</span>
      </div>
    </div>
  );
}
