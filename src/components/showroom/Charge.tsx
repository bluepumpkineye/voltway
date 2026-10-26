'use client';

import React from 'react';
import type { Vehicle } from '@/data/vehicles/schema';
import { flagshipVariant } from '@/data/vehicles/schema';
import { pauseDemo, tapChargeFlap } from '@/lib/tech/actions';
import { techClock, useTechClock } from '@/lib/tech/clock';
import { chargeFacts } from '@/lib/tech/charging';
import { runPhase } from '@/lib/tech/phase';
import { useChargeReadout, useRuntime, type Runtime } from '@/lib/tech/session';
import { useVehicleStore } from '@/store/vehicle-store';
import { FOCUS } from './Chrome';

const W = 500;
const H = 42;

const mmss = (s: number) => {
  const n = Math.round(s);
  return `${Math.floor(n / 60)}:${String(n % 60).padStart(2, '0')}`;
};

/**
 * How wide the floating tablet screen surface is in landscape mode.
 * 510px provides an authentic, widescreen landscape tablet surface (scaled down by 1/3 for a sleek, compact fit).
 */
export const CHARGE_COLUMN_W = 510;

/**
 * The Charging tab's Moveable Landscape Tablet Surface:
 * - Widescreen automotive tablet design (16:10 landscape aspect ratio).
 * - Reduced by 1/3 in footprint for balanced ergonomics on desktop and mobile.
 * - Mobile-friendly docking at the bottom of the screen with 3D car scene clearly on top.
 * - Draggable anywhere across the page with cursor-grab hand icon on hover over the bezel/header.
 * - Authoritative, modern precision typography (light/medium weights, tabular lining numbers, technical micro-copy).
 * - Central circular State of Charge progress meter with fine instrument ticks and glowing arc.
 * - Flanking telemetry panels (Time, Energy, Power, Range) with technical amber bars.
 * - Wide-aspect Simulated Power Curve oscilloscope and expandable specifications drawer.
 */
export function ChargePanel({ vehicle, compact }: { vehicle: Vehicle; compact: boolean }) {
  const facts = React.useMemo(() => chargeFacts(vehicle), [vehicle]);
  const charge = useRuntime()?.charge;
  const r = useChargeReadout();
  const clock = useTechClock();
  const run = runPhase(clock);
  const soc = useVehicleStore((s) => s.soc);
  const [specsOpen, setSpecsOpen] = React.useState(false);
  const [timeStr, setTimeStr] = React.useState('09:16 PM');
  const variant = flagshipVariant(vehicle);

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

  // Live formatted clock
  React.useEffect(() => {
    const update = () => {
      const d = new Date();
      setTimeStr(d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    };
    update();
    const timer = setInterval(update, 10000);
    return () => clearInterval(timer);
  }, []);

  const profile = facts?.profile;
  const peakKw = profile?.peakKw ?? 1;
  const kwMax = peakKw * 1.08;
  const seconds = profile?.seconds ?? 1;

  const path = React.useMemo(() => {
    if (!charge) return { line: '', area: '' };
    const step = Math.max(1, Math.round(charge.curve.length / 140));
    const pts = charge.curve.filter((_, i) => i % step === 0 || i === charge.curve.length - 1);
    const xy = pts.map((p) => [(p.s / seconds) * W, H - 3 - (p.kw / kwMax) * (H - 6)] as const);
    const line = 'M' + xy.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join(' L');
    return { line, area: `${line} L${W} ${H} L0 ${H} Z` };
  }, [charge, seconds, kwMax]);

  if (!facts || !profile) return null;
  const { spec } = facts;

  const sim = r ? Math.min(seconds, r.elapsed) : 0;
  const x = (sim / seconds) * W;
  const y = r ? H - 3 - (Math.max(r.kw, curveKw(charge, sim)) / kwMax) * (H - 6) : H;
  const peakY = H - 3 - (peakKw / kwMax) * (H - 6);
  const shown = Math.round((r?.soc ?? soc) * 100);

  const isCharging = r?.phase === 'charging';
  const isCharged = r?.phase === 'charged';
  const isConnecting = r?.phase === 'connecting' || r?.phase === 'opening';

  // Range added estimation
  const rangeKm = variant.range?.[0]?.km ?? 600;
  const rangeAdded = Math.round(((r?.kwh ?? 0) / (spec.packKwh || 100)) * rangeKm);

  // Charging session progress ratios for technical bars
  const timeProgress = r ? Math.min(1, r.elapsed / Math.max(1, seconds)) : 0;
  const energyProgress = r ? Math.min(1, r.kwh / Math.max(1, spec.packKwh * ((spec.window.to - spec.window.from) / 100))) : 0;
  const powerProgress = r ? Math.min(1, r.kw / Math.max(1, peakKw)) : 0;
  const rangeProgress = Math.min(1, rangeAdded / (rangeKm * 0.7));

  const action =
    run === 'driving'
      ? { label: 'Pause', run: pauseDemo }
      : run === 'done'
        ? { label: 'Charge again', run: () => techClock.play() }
        : r?.phase === 'charged'
          ? { label: 'Unplug', run: () => techClock.play() }
          : run === 'ready'
            ? { label: 'Start charging', run: tapChargeFlap }
            : { label: 'Resume', run: () => techClock.play() };

  const phaseBadge = !r
    ? { text: 'STANDBY', color: 'text-neutral-400', bg: 'bg-white/[0.04] border-white/10' }
    : r.phase === 'charging'
      ? { text: 'ACTIVE CHARGING', color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/30' }
      : r.phase === 'charged'
        ? { text: 'SESSION COMPLETE', color: 'text-cyan-400', bg: 'bg-cyan-500/10 border-cyan-500/30' }
        : r.phase === 'connecting' || r.phase === 'opening'
          ? { text: 'CONNECTING', color: 'text-amber-300', bg: 'bg-amber-500/10 border-amber-500/30' }
          : { text: 'READY', color: 'text-sky-300', bg: 'bg-sky-500/10 border-sky-500/25' };

  const phaseNarrative = !r
    ? 'Initializing charger communication…'
    : r.phase === 'ready'
      ? `Parked at charger · Initial SoC ${Math.round(profile.from * 100)}%`
      : r.phase === 'opening'
        ? 'Charge port flap opening · Automated arm deploying'
        : r.phase === 'connecting'
          ? 'Engaging liquid-cooled DC fast-charge connector'
          : r.phase === 'charging'
            ? `High-voltage DC fast charging active · Target ${spec.window.to}%`
            : r.phase === 'charged'
              ? `Session complete · Charged to ${Math.round(profile.to * 100)}%`
              : r.phase === 'unplugging'
                ? 'Disengaging DC connector · Flap closing'
                : 'Connector stowed · Standby';

  const peakTag = facts.peak.source === 'published' ? 'published' : facts.peak.source === 'c-rate' ? `${spec.cRate}C × pack` : 'derived';
  const rows: { label: string; value: string; tag?: string }[] = [
    { label: 'Peak power', value: `${facts.peak.kw} kW`, tag: peakTag },
    { label: `${spec.window.from}–${spec.window.to} % window`, value: `${spec.window.minutes} min`, tag: 'published' },
    { label: 'Average power', value: `${Math.round(facts.averageKw)} kW`, tag: 'derived' },
    { label: 'Battery pack', value: `${spec.packKwh} kWh ${variant.battery.chemistry}` },
    ...(spec.architectureV ? [{ label: 'Architecture', value: `${spec.architectureV} V` }] : []),
    { label: 'Connector standard', value: `${spec.connector} DC` },
    { label: 'Charge port', value: spec.port.where, tag: spec.port.published ? 'published' : 'ours' },
  ];

  // Circle gauge math (viewBox 0 0 160 160, center 80, 80)
  const radius = 56;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - Math.min(100, Math.max(0, shown)) / 100);

  // Drag Event Handlers with Viewport Bounding
  const handlePointerDown = (e: React.PointerEvent) => {
    const target = e.target as HTMLElement;
    if (target.closest('button, a, input, select, textarea')) return;

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
    <div
      ref={tabletRef}
      role="region"
      aria-label="High-Power EV Charger Tablet Surface"
      style={{
        transform: `translate3d(${offset.x}px, ${offset.y}px, 0)`,
        transition: isDragging ? 'none' : 'transform 0.35s cubic-bezier(0.16, 1, 0.3, 1)',
      }}
      className={`pointer-events-auto absolute ${
        compact
          ? 'bottom-2 sm:bottom-3 left-1/2 -translate-x-1/2 w-[calc(100vw-16px)] max-w-[460px]'
          : 'top-[calc(var(--top-ui,56px)+12px)] right-5 w-[500px] lg:w-[516px] max-w-[calc(100vw-24px)]'
      } select-none`}
    >
      {/* Outer Landscape Tablet Enclosure (Bezel Drag Zone with Hand Cursor) */}
      <div
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
        onDoubleClick={resetPosition}
        className={`group relative overflow-hidden rounded-[22px] bg-gradient-to-b from-[#242b38] via-[#161c26] to-[#0d121a] p-1.5 sm:p-2 transition-shadow duration-300 ${
          isDragging
            ? 'cursor-grabbing shadow-[0_30px_70px_-15px_rgba(0,0,0,0.95),0_0_0_1.5px_rgba(6,182,212,0.5)_inset] scale-[1.006]'
            : 'cursor-grab shadow-[0_20px_50px_-15px_rgba(0,0,0,0.85),0_0_0_1px_rgba(255,255,255,0.12)_inset,0_1.5px_3px_rgba(255,255,255,0.2)_inset]'
        }`}
      >
        {/* Top Tablet Hardware Bezel: Sensor Dot, Grip Bar, and Reset */}
        <div className="relative mb-1 flex items-center justify-between px-2 pt-0.5">
          {/* Hardware Camera & Light Sensor Dot */}
          <div className="flex items-center gap-1 opacity-60">
            <div className="h-1 w-1 rounded-full bg-[#070b12] border border-white/20" />
            <div className="h-1.5 w-1.5 rounded-full bg-[#03060a] border border-cyan-500/40" />
          </div>

          {/* Minimal Physical Grip Pill (Hand Cursor Area, No Text) */}
          <div
            className="flex items-center justify-center py-0.5 px-2.5 rounded-full hover:bg-white/[0.08] transition-colors"
            title="Drag to reposition tablet · Double-click to reset"
          >
            <div className="h-0.5 w-10 rounded-full bg-white/25 group-hover:bg-cyan-400/60 transition-colors" />
          </div>

          {/* Reset button when moved */}
          <div className="w-14 text-right">
            {hasMoved && (
              <button
                type="button"
                onClick={resetPosition}
                className="inline-flex items-center gap-1 rounded-full bg-white/[0.08] hover:bg-white/15 px-1.5 py-0.5 text-[8.5px] font-medium tracking-wider text-neutral-300 hover:text-white transition-colors"
                title="Reset to default position"
              >
                <span>↺</span>
                <span>Reset</span>
              </button>
            )}
          </div>
        </div>

        {/* Inner Screen Surface (Landscape Aspect Ratio) */}
        <div className="relative overflow-hidden rounded-[16px] border border-white/[0.08] bg-[#060a12] shadow-[inset_0_0_40px_rgba(0,8,16,0.95)]">
          {/* Glass reflection gloss overlay */}
          <div
            className="pointer-events-none absolute inset-0 z-20 opacity-40 mix-blend-screen"
            style={{
              background:
                'linear-gradient(120deg, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0.02) 28%, transparent 48%, rgba(6,182,212,0.04) 100%)',
            }}
          />

          {/* Faint subtle cyber glow */}
          <div
            className="pointer-events-none absolute left-1/2 top-[44%] -translate-x-1/2 -translate-y-1/2 h-56 w-56 rounded-full opacity-25 blur-2xl transition-opacity duration-700"
            style={{
              background: isCharging
                ? 'radial-gradient(circle, #22c55e 0%, #06b6d4 40%, transparent 70%)'
                : 'radial-gradient(circle, #0ea5e9 0%, #1e293b 50%, transparent 70%)',
            }}
          />

          {/* 1. Header Bar: Authoritative Precision Top Bar (Drag Zone) */}
          <header className="relative z-10 flex cursor-grab active:cursor-grabbing items-center justify-between border-b border-white/[0.07] bg-[#080e18]/90 px-3 py-1.5 sm:px-4">
            <div className="flex items-center gap-2">
              <span className="font-mono text-[11px] font-medium tracking-wider text-cyan-300/90">{timeStr}</span>
              <span className="h-1 w-1 rounded-full bg-white/20" />
              <span className="font-mono text-[9px] tracking-[0.12em] uppercase text-neutral-400">
                {spec.architectureV ? `${spec.architectureV}V` : '800V'} DC
              </span>
            </div>

            <div className="flex items-center gap-1">
              <span className="text-amber-400 text-[10px]">⚡</span>
              <span className="text-[10px] sm:text-[11px] font-medium tracking-[0.16em] uppercase text-white truncate max-w-[170px] sm:max-w-none">
                HIGH-POWER DC CHARGER
              </span>
              <span className="hidden sm:inline text-[9px] font-normal tracking-[0.08em] uppercase text-neutral-400 ml-0.5">
                · {vehicle.brand} {vehicle.model}
              </span>
            </div>

            <div className="flex items-center gap-1.5">
              <span className="relative flex h-1.5 w-1.5">
                {isCharging && <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />}
                <span className={`relative inline-flex h-1.5 w-1.5 rounded-full ${isCharging ? 'bg-emerald-400' : isCharged ? 'bg-cyan-400' : isConnecting ? 'bg-amber-400' : 'bg-neutral-500'}`} />
              </span>
              <span className="font-mono text-[9px] font-medium tracking-wider text-neutral-300 uppercase">
                {spec.connector} DC
              </span>
            </div>
          </header>

          {/* 2. Main Stage: Widescreen Landscape 3-Column Gauges Layout */}
          <div className="relative z-10 p-2 sm:p-3">
            <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 sm:gap-3.5">
              {/* LEFT COLUMN: Session telemetry */}
              <div className="flex flex-col justify-between space-y-1.5 min-w-0">
                {/* Session header */}
                <div className="flex items-center justify-between">
                  <span className="text-[9px] font-medium tracking-[0.14em] uppercase text-cyan-300/90 truncate">
                    SESSION
                  </span>
                  <span className="text-cyan-400/80 font-mono text-[9px]">&gt;&gt;</span>
                </div>

                {/* Time Elapsed Card */}
                <div className="space-y-0.5">
                  <div className="flex items-center justify-between text-[8.5px] font-medium tracking-[0.08em] uppercase text-neutral-400">
                    <span className="truncate">ELAPSED</span>
                    <span className="font-mono text-[8px] text-neutral-500 lowercase">
                      {r ? `${Math.max(0, Math.round(r.left / 60))}m` : 'wait'}
                    </span>
                  </div>
                  <div className="relative flex h-6 sm:h-6.5 items-center justify-between overflow-hidden rounded bg-[#0b121d] px-2 border border-white/[0.08]">
                    <span className="z-10 font-mono text-[11.5px] sm:text-[12.5px] font-medium text-white tracking-wider tnum">
                      {r ? mmss(r.elapsed) : '0:00'}
                    </span>
                    <div
                      className="absolute inset-y-0 right-0 bg-gradient-to-l from-amber-500/80 to-amber-600/60 rounded-r transition-all duration-300"
                      style={{ width: `${Math.round(timeProgress * 65)}%` }}
                    />
                  </div>
                </div>

                {/* Energy Dispensed Card */}
                <div className="space-y-0.5">
                  <div className="text-[8.5px] font-medium tracking-[0.08em] uppercase text-neutral-400 truncate">
                    DISPENSED
                  </div>
                  <div className="relative flex h-6 sm:h-6.5 items-center justify-between overflow-hidden rounded bg-[#0b121d] px-2 border border-white/[0.08]">
                    <div className="z-10 flex items-baseline gap-1">
                      <span className="font-mono text-[11.5px] sm:text-[12.5px] font-medium text-white tracking-wider tnum">
                        {r ? r.kwh.toFixed(1) : '0.0'}
                      </span>
                      <span className="text-[8.5px] font-normal text-neutral-400 uppercase">kWh</span>
                    </div>
                    <div
                      className="absolute inset-y-0 right-0 bg-gradient-to-l from-amber-500/80 to-amber-600/60 rounded-r transition-all duration-300"
                      style={{ width: `${Math.round(energyProgress * 65)}%` }}
                    />
                  </div>
                </div>

                {/* Left Action Button: SESSION INFO */}
                <button
                  type="button"
                  onClick={() => setSpecsOpen((v) => !v)}
                  className={`group relative flex h-6 sm:h-6.5 w-full items-center justify-center rounded border border-cyan-500/30 bg-[#0d1724]/80 px-2 text-[9px] font-medium tracking-[0.12em] uppercase text-cyan-200 transition-all hover:border-cyan-400 hover:bg-cyan-500/15 hover:text-white ${FOCUS}`}
                >
                  <span className="truncate">{specsOpen ? 'CLOSE INFO' : 'SPECS / INFO'}</span>
                  <span className="absolute -bottom-0.5 left-1/2 -translate-x-1/2 border-x-2 border-t-2 border-x-transparent border-t-cyan-500/30 group-hover:border-t-cyan-400 transition-colors" />
                </button>
              </div>

              {/* CENTER COLUMN: Authoritative Circular Progress Meter */}
              <div className="relative flex flex-col items-center justify-center px-0.5">
                <div className="relative flex h-32 w-32 sm:h-38 sm:w-38 items-center justify-center">
                  <svg viewBox="0 0 160 160" className="h-full w-full -rotate-90 transform" role="img" aria-label="Charge progress gauge">
                    <defs>
                      <linearGradient id="meterGlowGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#10b981" />
                        <stop offset="65%" stopColor="#22c55e" />
                        <stop offset="100%" stopColor="#06b6d4" />
                      </linearGradient>
                      <filter id="meterGlowFilter" x="-20%" y="-20%" width="140%" height="140%">
                        <feDropShadow dx="0" dy="0" stdDeviation="3.5" floodColor="#10b981" floodOpacity="0.75" />
                        <feDropShadow dx="0" dy="0" stdDeviation="8" floodColor="#06b6d4" floodOpacity="0.45" />
                      </filter>
                    </defs>

                    {/* Dark track ring */}
                    <circle
                      cx="80"
                      cy="80"
                      r={radius}
                      fill="none"
                      stroke="#0f1926"
                      strokeWidth="8"
                    />

                    {/* Radial instrument tick marks ring */}
                    <circle
                      cx="80"
                      cy="80"
                      r={radius + 8}
                      fill="none"
                      stroke="rgba(255, 255, 255, 0.12)"
                      strokeWidth="1"
                      strokeDasharray="1.5 6"
                    />

                    {/* Progress arc */}
                    <circle
                      cx="80"
                      cy="80"
                      r={radius}
                      fill="none"
                      stroke="url(#meterGlowGrad)"
                      strokeWidth="8"
                      strokeLinecap="round"
                      strokeDasharray={circumference}
                      strokeDashoffset={strokeDashoffset}
                      filter="url(#meterGlowFilter)"
                      className="transition-all duration-300 ease-out"
                    />

                    {/* Inner bezel guide */}
                    <circle
                      cx="80"
                      cy="80"
                      r={radius - 8}
                      fill="none"
                      stroke="rgba(6, 182, 212, 0.1)"
                      strokeWidth="0.8"
                    />
                  </svg>

                  {/* Inside Center Readouts: Refined, Light, Authoritative */}
                  <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
                    {/* Status Pill */}
                    <div className={`mb-0.5 flex items-center gap-1 rounded-full px-2 py-0.2 border text-[8px] sm:text-[8.5px] font-medium tracking-[0.14em] uppercase ${phaseBadge.color} ${phaseBadge.bg}`}>
                      {isCharging && <span className="h-1 w-1 rounded-full bg-emerald-400 animate-pulse" />}
                      <span>{phaseBadge.text}</span>
                    </div>

                    {/* Giant Numeric Percentage: Elegant Light-Medium Weight */}
                    <div className="flex items-baseline justify-center leading-none mt-0.5">
                      <span className="font-light text-[36px] sm:text-[42px] tracking-tight text-white tnum drop-shadow-[0_2px_8px_rgba(0,0,0,0.8)]">
                        {shown}
                      </span>
                      <span className="text-[13px] sm:text-[14px] font-light text-cyan-400/80 ml-0.5">%</span>
                    </div>

                    {/* Technical Subtitle */}
                    <div className="text-[7.5px] sm:text-[8px] font-medium tracking-[0.2em] text-cyan-200/60 uppercase mt-0.5">
                      STATE OF CHARGE
                    </div>
                  </div>
                </div>
              </div>

              {/* RIGHT COLUMN: Power, Range & Primary Action */}
              <div className="flex flex-col justify-between space-y-1.5 min-w-0">
                {/* Power Card */}
                <div className="space-y-0.5">
                  <div className="flex items-baseline justify-between text-[8.5px] font-medium tracking-[0.08em] uppercase text-neutral-400">
                    <span className="truncate">POWER</span>
                    <span className="text-[8px] font-mono text-neutral-500 truncate">{peakKw}k</span>
                  </div>
                  <div className="relative flex h-6 sm:h-6.5 items-center justify-between overflow-hidden rounded bg-[#0b121d] px-2 border border-white/[0.08]">
                    <div className="z-10 flex items-baseline gap-1">
                      <span className="font-mono text-[11.5px] sm:text-[12.5px] font-medium text-white tracking-wider tnum">
                        {Math.round(r?.kw ?? 0)}
                      </span>
                      <span className="text-[8.5px] font-normal text-neutral-400 uppercase">kW</span>
                    </div>
                    <div
                      className="absolute inset-y-0 right-0 bg-gradient-to-l from-amber-500/80 to-amber-600/60 rounded-r transition-all duration-300"
                      style={{ width: `${Math.round(powerProgress * 65)}%` }}
                    />
                  </div>
                </div>

                {/* Range Added Card */}
                <div className="space-y-0.5">
                  <div className="text-[8.5px] font-medium tracking-[0.08em] uppercase text-neutral-400 truncate">
                    RANGE ADDED
                  </div>
                  <div className="relative flex h-6 sm:h-6.5 items-center justify-between overflow-hidden rounded bg-[#0b121d] px-2 border border-white/[0.08]">
                    <div className="z-10 flex items-baseline gap-1">
                      <span className="font-mono text-[11.5px] sm:text-[12.5px] font-medium text-emerald-300 tracking-wider tnum">
                        +{rangeAdded}
                      </span>
                      <span className="text-[8.5px] font-normal text-neutral-400 uppercase">km</span>
                    </div>
                    <div
                      className="absolute inset-y-0 right-0 bg-gradient-to-l from-amber-500/80 to-amber-600/60 rounded-r transition-all duration-300"
                      style={{ width: `${Math.round(rangeProgress * 65)}%` }}
                    />
                  </div>
                </div>

                {/* Right Action Button: Primary Technical Trigger */}
                <button
                  type="button"
                  onClick={action.run}
                  disabled={!r}
                  className={`group relative flex h-6 sm:h-6.5 w-full items-center justify-center rounded border border-white/30 bg-[#0d1724]/90 px-2 text-[9px] sm:text-[9.5px] font-medium tracking-[0.12em] uppercase text-white shadow-sm transition-all hover:border-emerald-400 hover:bg-emerald-500/20 hover:text-emerald-200 disabled:opacity-40 ${FOCUS}`}
                >
                  <span className="truncate">{action.label}</span>
                  <span className="absolute -bottom-0.5 left-1/2 -translate-x-1/2 border-x-2 border-t-2 border-x-transparent border-t-white/30 group-hover:border-t-emerald-400 transition-colors" />
                </button>
              </div>
            </div>

            {/* 3. Wide Oscilloscope Telemetry Strip (Horizontal Landscape Profile) */}
            <div className="mt-2 rounded-lg border border-white/[0.08] bg-[#080d16]/90 p-1.5 sm:p-2">
              <div className="flex items-center justify-between pb-0.5 text-[8.5px] sm:text-[9px]">
                <div className="flex items-center gap-1.5 font-medium tracking-[0.12em] uppercase text-neutral-400">
                  <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
                  <span>SIMULATED POWER CURVE</span>
                </div>
                <div className="flex items-center gap-1.5 font-mono text-[8.5px] text-neutral-400">
                  <span className="text-cyan-300 font-medium">{Math.round(r?.kw ?? 0)} kW live</span>
                  <span>·</span>
                  <span>Peak {facts.peak.kw} kW</span>
                </div>
              </div>

              <figure className="relative mt-0.5">
                <svg viewBox={`0 0 ${W} ${H}`} className="block h-[34px] sm:h-[38px] w-full" role="img" aria-label="Charging power against time">
                  <defs>
                    <linearGradient id="curveFillGrad" x1="0%" y1="0%" x2="0%" y2="1">
                      <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.28" />
                      <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.01" />
                    </linearGradient>
                  </defs>

                  {/* Precision grid lines */}
                  <line x1="0" x2={W} y1={H / 2} y2={H / 2} stroke="rgba(255,255,255,0.06)" strokeWidth="1" strokeDasharray="3 5" vectorEffect="non-scaling-stroke" />
                  <line x1="0" x2={W} y1={peakY} y2={peakY} stroke="rgba(56,189,248,0.4)" strokeWidth="1" strokeDasharray="3 4" vectorEffect="non-scaling-stroke" />

                  {/* Power curve area & guide path */}
                  <path d={path.area} fill="url(#curveFillGrad)" />
                  <path d={path.line} fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="1.2" vectorEffect="non-scaling-stroke" />

                  {/* Active clipped curve */}
                  <clipPath id="chargeActiveClip">
                    <rect x="0" y="0" width={x} height={H} />
                  </clipPath>
                  <path
                    d={path.line}
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="2.2"
                    strokeLinejoin="round"
                    vectorEffect="non-scaling-stroke"
                    clipPath="url(#chargeActiveClip)"
                  />

                  {/* Live scanning cursor */}
                  {r && r.elapsed > 0 && (
                    <>
                      <line x1={x} x2={x} y1={0} y2={H} stroke="#10b981" strokeWidth="1" strokeDasharray="2 2" strokeOpacity="0.7" vectorEffect="non-scaling-stroke" />
                      <circle cx={x} cy={y} r="3.5" fill="#10b981" stroke="#ffffff" strokeWidth="1.2" vectorEffect="non-scaling-stroke" />
                    </>
                  )}
                </svg>

                <div className="mt-0.5 flex justify-between font-mono text-[8px] sm:text-[8.5px] text-neutral-500">
                  <span>0:00 ({spec.window.from}%)</span>
                  <span className="text-cyan-400/80 font-medium">{spec.window.minutes} min ({spec.window.to}%)</span>
                </div>
              </figure>
            </div>

            {/* 4. Live Telemetry Narrative Status Bar */}
            <div className="mt-1.5 flex items-center justify-between rounded bg-[#080d15] px-2 py-1 border border-white/[0.05] text-[9px] sm:text-[9.5px]">
              <div className="flex items-center gap-1.5 truncate text-neutral-400">
                <span className="text-cyan-400/80 text-[9.5px]">ℹ</span>
                <span className="truncate">{phaseNarrative}</span>
              </div>
              <span className="shrink-0 font-mono text-[8.5px] text-neutral-500 ml-1.5">
                14s simulation
              </span>
            </div>

            {/* 5. Expandable Specifications Drawer */}
            {specsOpen && (
              <div className="mt-2 max-h-[36vh] overflow-y-auto rounded-lg border border-white/[0.1] bg-[#090f1a]/98 p-2.5 shadow-2xl backdrop-blur-md">
                <div className="flex items-center justify-between border-b border-white/[0.08] pb-1">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[9.5px] font-medium tracking-[0.14em] uppercase text-cyan-300">
                      SPECIFICATIONS
                    </span>
                    <span className="text-[8.5px] text-neutral-400 font-mono">({vehicle.brand} {vehicle.model})</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSpecsOpen(false)}
                    className="rounded px-1.5 py-0.5 text-[8.5px] font-medium text-neutral-400 hover:text-white hover:bg-white/10"
                  >
                    ✕ CLOSE
                  </button>
                </div>

                <dl className="mt-1.5 grid grid-cols-2 sm:grid-cols-3 gap-1.5 text-[9.5px]">
                  {rows.map((row) => (
                    <div key={row.label} className="min-w-0 rounded bg-[#060a12] p-1.5 border border-white/[0.05]">
                      <dt className="text-[8px] uppercase tracking-wider text-neutral-400 truncate">{row.label}</dt>
                      <dd className="font-mono text-[10.5px] font-medium text-white mt-0.5 tnum truncate">
                        {row.value}
                        {row.tag && (
                          <span className="ml-1 rounded bg-white/[0.06] px-1 py-0.2 text-[7.5px] font-sans text-neutral-300 border border-white/10">
                            {row.tag}
                          </span>
                        )}
                      </dd>
                    </div>
                  ))}
                </dl>

                {spec.claims && spec.claims.length > 0 && (
                  <div className="mt-2 border-t border-white/[0.08] pt-1.5">
                    <div className="text-[8.5px] font-medium tracking-[0.12em] uppercase text-neutral-400 mb-1">
                      Manufacturer Claims & Sources
                    </div>
                    <div className="space-y-1 max-h-24 overflow-y-auto pr-1">
                      {spec.claims.map((claim, idx) => (
                        <div key={idx} className="rounded bg-[#060a12] p-1 text-[8.5px] leading-relaxed text-neutral-300 border border-white/[0.05]">
                          <p>{claim.text}</p>
                          {claim.source && (
                            <a
                              href={claim.source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="mt-0.5 inline-flex items-center gap-0.5 text-[8px] font-medium text-cyan-400 hover:underline"
                            >
                              <span>↗ {claim.source.label}</span>
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function curveKw(charge: NonNullable<Runtime['charge']> | null | undefined, sim: number): number {
  if (!charge) return 0;
  const c = charge.curve;
  return c[Math.min(c.length - 1, Math.max(0, Math.round(sim)))]?.kw ?? 0;
}
