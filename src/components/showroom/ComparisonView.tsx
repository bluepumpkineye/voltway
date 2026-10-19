'use client';

import React from 'react';
import Link from 'next/link';
import type { Variant, Vehicle } from '@/data/vehicles/schema';
import { formatPower } from '@/data/vehicles/schema';
import { chargeMinutes10to80 } from '@/lib/performance';
import { showroomCars } from '@/lib/showroom/cars';
import { FOCUS, GLASS, PANEL } from './Chrome';

const num = (v: number) => v.toLocaleString('en-US');
const mm = (v: number) => `${v.toLocaleString('en-US')} mm`;

interface ComparisonViewProps {
  vehicleA: Vehicle;
  variantA: Variant;
  onVariantA: (id: string) => void;
  vehicleB: Vehicle;
  variantB: Variant;
  onSelectVehicleB: (slug: string) => void;
  onVariantB: (id: string) => void;
  onClose: () => void;
  compact: boolean;
  isMaximized?: boolean;
  onToggleMaximize?: () => void;
}

interface StatDelta {
  text: string;
  winner: 'A' | 'B' | 'tie' | 'none';
}

function Section({
  title,
  subtitle,
  badge,
  defaultOpen = true,
  children,
}: {
  title: string;
  subtitle?: string;
  badge?: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = React.useState(defaultOpen);
  return (
    <div className="border-t border-black/[0.07] pt-2.5">
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className={`flex w-full items-center justify-between gap-3 py-1.5 text-left transition-colors ${FOCUS}`}
      >
        <div className="flex items-center gap-2">
          <span className="text-[12px] font-semibold uppercase tracking-[0.1em] text-neutral-800">
            {title}
          </span>
          {badge && (
            <span className="rounded-full bg-black/[0.05] px-2 py-0.5 text-[10px] font-medium text-neutral-600">
              {badge}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 text-[11px] text-neutral-500">
          {!open && subtitle && <span className="tnum truncate max-w-[200px]">{subtitle}</span>}
          <svg
            className={`shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}
            width="9"
            height="6"
            viewBox="0 0 9 6"
            aria-hidden
          >
            <path
              d="M1 1l3.5 3.5L8 1"
              stroke="currentColor"
              strokeWidth="1.5"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      </button>
      {open && <div className="mt-2 space-y-3 pb-3">{children}</div>}
    </div>
  );
}

function CompareBar({
  valA,
  valB,
  better = 'higher',
}: {
  valA: number;
  valB: number;
  better?: 'higher' | 'lower';
}) {
  const max = Math.max(valA, valB, 0.001);
  const pctA = Math.round((valA / max) * 100);
  const pctB = Math.round((valB / max) * 100);

  const isAWinner = better === 'higher' ? valA > valB : valA < valB;
  const isBWinner = better === 'higher' ? valB > valA : valB < valA;

  return (
    <div className="mt-1 flex items-center gap-2">
      <div className="flex-1">
        <div className="flex h-1.5 w-full overflow-hidden rounded-full bg-black/[0.06]">
          <div
            className={`h-full rounded-full transition-all duration-300 ${
              isAWinner ? 'bg-neutral-900' : 'bg-neutral-400'
            }`}
            style={{ width: `${pctA}%` }}
          />
        </div>
      </div>
      <div className="flex-1">
        <div className="flex h-1.5 w-full overflow-hidden rounded-full bg-black/[0.06]">
          <div
            className={`h-full rounded-full transition-all duration-300 ${
              isBWinner ? 'bg-neutral-900' : 'bg-neutral-400'
            }`}
            style={{ width: `${pctB}%` }}
          />
        </div>
      </div>
    </div>
  );
}

function CompareMetricRow({
  label,
  valA,
  valB,
  unit = '',
  delta,
  numericA,
  numericB,
  better,
  hint,
}: {
  label: string;
  valA: React.ReactNode;
  valB: React.ReactNode;
  unit?: string;
  delta?: StatDelta;
  numericA?: number;
  numericB?: number;
  better?: 'higher' | 'lower';
  hint?: string;
}) {
  return (
    <div className="rounded-xl bg-black/[0.025] p-2.5 transition-colors hover:bg-black/[0.04]" title={hint}>
      <div className="flex items-center justify-between gap-2 text-[11px] text-neutral-500">
        <span className="font-medium tracking-tight text-neutral-600">{label}</span>
        {delta && delta.winner !== 'none' && (
          <span
            className={`tnum rounded-full px-2 py-0.5 text-[10px] font-semibold ${
              delta.winner === 'tie'
                ? 'bg-neutral-200/70 text-neutral-700'
                : 'bg-emerald-500/10 text-emerald-800 ring-1 ring-emerald-500/20'
            }`}
          >
            {delta.text}
          </span>
        )}
      </div>

      <div className="mt-1.5 grid grid-cols-2 gap-3 text-[13px]">
        <div className={`tnum truncate ${delta?.winner === 'A' ? 'font-semibold text-neutral-950' : 'text-neutral-700'}`}>
          {valA}
          {unit && <span className="ml-0.5 text-[11px] text-neutral-500">{unit}</span>}
        </div>
        <div className={`tnum truncate text-right ${delta?.winner === 'B' ? 'font-semibold text-neutral-950' : 'text-neutral-700'}`}>
          {valB}
          {unit && <span className="ml-0.5 text-[11px] text-neutral-500">{unit}</span>}
        </div>
      </div>

      {numericA !== undefined && numericB !== undefined && better && (
        <CompareBar valA={numericA} valB={numericB} better={better} />
      )}
    </div>
  );
}

export function ComparisonView({
  vehicleA,
  variantA,
  onVariantA,
  vehicleB,
  variantB,
  onSelectVehicleB,
  onVariantB,
  onClose,
  compact,
  isMaximized = false,
  onToggleMaximize,
}: ComparisonViewProps) {
  const [selectorOpen, setSelectorOpen] = React.useState(false);
  const selectorRef = React.useRef<HTMLDivElement>(null);

  // Available cars to compare against
  const allCars = React.useMemo(() => showroomCars(), []);
  const selectableCars = React.useMemo(() => allCars.filter((c) => c.slug !== vehicleA.slug), [allCars, vehicleA.slug]);

  // Close dropdown on outside click
  React.useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (selectorRef.current && !selectorRef.current.contains(e.target as Node)) {
        setSelectorOpen(false);
      }
    }
    if (selectorOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [selectorOpen]);

  // Decision metrics extraction
  const pA = variantA.performance;
  const pB = variantB.performance;
  const bA = variantA.battery;
  const bB = variantB.battery;
  const dA = vehicleA.dimensions;
  const dB = vehicleB.dimensions;

  const minA = chargeMinutes10to80(variantA);
  const minB = chargeMinutes10to80(variantB);

  const rangeA = variantA.range[0]?.km ?? 0;
  const rangeCycleA = variantA.range[0]?.cycle ?? 'CLTC';
  const rangeB = variantB.range[0]?.km ?? 0;
  const rangeCycleB = variantB.range[0]?.cycle ?? 'CLTC';

  // 1. Acceleration Delta
  const accelDelta = React.useMemo<StatDelta>(() => {
    if (!pA.zeroTo100S || !pB.zeroTo100S) return { text: '', winner: 'none' };
    const diff = Math.abs(pA.zeroTo100S - pB.zeroTo100S);
    if (diff < 0.05) return { text: 'Identical 0–100', winner: 'tie' };
    if (pA.zeroTo100S < pB.zeroTo100S) {
      return { text: `Model A is ${diff.toFixed(2)}s faster`, winner: 'A' };
    }
    return { text: `Model B is ${diff.toFixed(2)}s faster`, winner: 'B' };
  }, [pA.zeroTo100S, pB.zeroTo100S]);

  // 2. Range Delta
  const rangeDelta = React.useMemo<StatDelta>(() => {
    if (!rangeA || !rangeB) return { text: '', winner: 'none' };
    const diff = Math.abs(rangeA - rangeB);
    if (diff < 5) return { text: 'Similar Range', winner: 'tie' };
    if (rangeA > rangeB) {
      return { text: `Model A has +${diff} km`, winner: 'A' };
    }
    return { text: `Model B has +${diff} km`, winner: 'B' };
  }, [rangeA, rangeB]);

  // 3. Charging Speed Delta
  const chargeDelta = React.useMemo<StatDelta>(() => {
    if (!minA || !minB) return { text: '', winner: 'none' };
    const diff = Math.abs(minA - minB);
    if (diff < 1) return { text: 'Similar Charge Time', winner: 'tie' };
    if (minA < minB) {
      return { text: `Model A is ${diff.toFixed(0)} min quicker`, winner: 'A' };
    }
    return { text: `Model B is ${diff.toFixed(0)} min quicker`, winner: 'B' };
  }, [minA, minB]);

  // 4. Power Delta
  const powerDelta = React.useMemo<StatDelta>(() => {
    const diff = Math.abs(pA.powerKw - pB.powerKw);
    if (diff < 10) return { text: 'Equal Output', winner: 'tie' };
    if (pA.powerKw > pB.powerKw) {
      return { text: `Model A has +${diff} kW`, winner: 'A' };
    }
    return { text: `Model B has +${diff} kW`, winner: 'B' };
  }, [pA.powerKw, pB.powerKw]);

  // Wheelbase Delta
  const wheelbaseDelta = React.useMemo<StatDelta>(() => {
    const diff = Math.abs(dA.wheelbaseMm - dB.wheelbaseMm);
    if (diff < 10) return { text: 'Equal Wheelbase', winner: 'tie' };
    if (dA.wheelbaseMm > dB.wheelbaseMm) {
      return { text: `Model A +${diff} mm legroom`, winner: 'A' };
    }
    return { text: `Model B +${diff} mm legroom`, winner: 'B' };
  }, [dA.wheelbaseMm, dB.wheelbaseMm]);

  return (
    <div
      className={`pointer-events-auto flex max-h-full w-full flex-col overflow-hidden rounded-2xl ${GLASS} transition-all duration-300`}
    >
      {/* Top Header Bar */}
      <div className="shrink-0 border-b border-black/[0.08] px-4 py-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-neutral-900 text-[10px] font-bold text-white shadow-sm">
              ◫
            </span>
            <span className="text-[12px] font-semibold uppercase tracking-[0.1em] text-neutral-900">
              Split-Screen Comparison
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            {onToggleMaximize && !compact && (
              <button
                type="button"
                onClick={onToggleMaximize}
                title={isMaximized ? 'Dock to side' : 'Maximize split-screen'}
                className={`rounded-lg p-1.5 text-neutral-500 hover:bg-black/[0.05] hover:text-neutral-900 ${FOCUS}`}
              >
                {isMaximized ? (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M4 14h6m0 0v6m0-6L3 21M20 10h-6m0 0V4m0 6l7-7" />
                  </svg>
                ) : (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M15 3h6m0 0v6m0-6L14 10M9 21H3m0 0v-6m0 6l7-7" />
                  </svg>
                )}
              </button>
            )}

            <button
              type="button"
              onClick={onClose}
              title="Exit comparison mode"
              className={`rounded-lg p-1.5 text-neutral-500 hover:bg-black/[0.05] hover:text-neutral-900 ${FOCUS}`}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Dual Car Header Card (Split 50 / 50) */}
        <div className="mt-3 grid grid-cols-2 gap-3">
          {/* Column A: Current Car */}
          <div className="rounded-xl bg-black/[0.035] p-3">
            <div className="flex items-center justify-between">
              <span className="rounded-full bg-neutral-900 px-2 py-0.5 text-[9.5px] font-bold uppercase tracking-wider text-white">
                Current
              </span>
              <span className="text-[10.5px] text-neutral-500">
                {vehicleA.year} · {vehicleA.bodyStyle}
              </span>
            </div>
            <h3 className="mt-1 text-[15px] font-bold leading-tight tracking-tight text-neutral-900">
              {vehicleA.brand} {vehicleA.model}
            </h3>
            <p className="mt-0.5 truncate text-[11px] text-neutral-500">{vehicleA.group}</p>

            {/* Variant selector */}
            {vehicleA.variants.length > 1 && (
              <div className="mt-2 flex gap-1 overflow-x-auto rounded-lg bg-black/[0.04] p-0.5">
                {vehicleA.variants.map((v) => (
                  <button
                    key={v.id}
                    type="button"
                    onClick={() => onVariantA(v.id)}
                    className={`shrink-0 truncate rounded-md px-2 py-0.5 text-[10.5px] font-medium transition-colors ${FOCUS} ${
                      v.id === variantA.id
                        ? 'bg-white text-neutral-900 shadow-xs font-semibold'
                        : 'text-neutral-500 hover:text-neutral-800'
                    }`}
                  >
                    {v.name}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Column B: Selectable Car */}
          <div className="relative rounded-xl bg-black/[0.035] p-3" ref={selectorRef}>
            <div className="flex items-center justify-between">
              <button
                type="button"
                onClick={() => setSelectorOpen((o) => !o)}
                className={`flex items-center gap-1 rounded-full bg-neutral-200/80 px-2 py-0.5 text-[9.5px] font-bold uppercase tracking-wider text-neutral-800 hover:bg-neutral-300 transition-colors ${FOCUS}`}
              >
                <span>Select Model</span>
                <svg width="8" height="5" viewBox="0 0 8 5" fill="none">
                  <path d="M1 1L4 4L7 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>

              <Link
                href={`/showroom/${vehicleB.slug}?tab=dimensions`}
                className="text-[10.5px] font-medium text-neutral-600 hover:text-neutral-950 underline decoration-neutral-300 underline-offset-2"
                title={`Open ${vehicleB.brand} ${vehicleB.model} in 3D showroom`}
              >
                View in 3D →
              </Link>
            </div>

            <div className="mt-1 flex items-baseline justify-between gap-1">
              <h3 className="text-[15px] font-bold leading-tight tracking-tight text-neutral-900">
                {vehicleB.brand} {vehicleB.model}
              </h3>
              <span className="shrink-0 text-[10.5px] text-neutral-500">
                {vehicleB.year} · {vehicleB.bodyStyle}
              </span>
            </div>
            <p className="mt-0.5 truncate text-[11px] text-neutral-500">{vehicleB.group}</p>

            {/* Variant selector */}
            {vehicleB.variants.length > 1 && (
              <div className="mt-2 flex gap-1 overflow-x-auto rounded-lg bg-black/[0.04] p-0.5">
                {vehicleB.variants.map((v) => (
                  <button
                    key={v.id}
                    type="button"
                    onClick={() => onVariantB(v.id)}
                    className={`shrink-0 truncate rounded-md px-2 py-0.5 text-[10.5px] font-medium transition-colors ${FOCUS} ${
                      v.id === variantB.id
                        ? 'bg-white text-neutral-900 shadow-xs font-semibold'
                        : 'text-neutral-500 hover:text-neutral-800'
                    }`}
                  >
                    {v.name}
                  </button>
                ))}
              </div>
            )}

            {/* Model Selector Dropdown Popover */}
            {selectorOpen && (
              <div className={`absolute left-0 right-0 top-full z-50 mt-1 max-h-60 overflow-y-auto rounded-xl p-1.5 shadow-xl ${PANEL}`}>
                <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-neutral-400">
                  Select Comparison Vehicle
                </div>
                {selectableCars.map((car) => {
                  const isSelected = car.slug === vehicleB.slug;
                  return (
                    <button
                      key={car.slug}
                      type="button"
                      onClick={() => {
                        onSelectVehicleB(car.slug);
                        setSelectorOpen(false);
                      }}
                      className={`flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-left text-[12px] transition-colors ${
                        isSelected
                          ? 'bg-neutral-900 font-semibold text-white'
                          : 'text-neutral-700 hover:bg-black/[0.05]'
                      }`}
                    >
                      <div className="min-w-0 flex-1">
                        <div className="truncate">
                          {car.brand} {car.model}
                        </div>
                        <div className={`truncate text-[10px] ${isSelected ? 'text-white/70' : 'text-neutral-400'}`}>
                          {car.group} · {car.bodyStyle}
                        </div>
                      </div>
                      {isSelected && (
                        <span className="ml-2 text-[11px] text-white">✓</span>
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* 4 Headline Quick Decision Cards */}
        <div className="mt-3 grid grid-cols-4 gap-1.5 text-center">
          {/* Card 1: 0-100 */}
          <div className="rounded-xl bg-black/[0.035] px-1 py-1.5">
            <div className="text-[10px] font-medium text-neutral-500">0–100 km/h</div>
            <div className="mt-0.5 flex items-center justify-center gap-1 text-[11.5px] font-semibold text-neutral-900">
              <span className={accelDelta.winner === 'A' ? 'text-emerald-700 font-bold' : ''}>
                {pA.zeroTo100S ? `${pA.zeroTo100S}s` : '–'}
              </span>
              <span className="text-[9px] text-neutral-300">vs</span>
              <span className={accelDelta.winner === 'B' ? 'text-emerald-700 font-bold' : ''}>
                {pB.zeroTo100S ? `${pB.zeroTo100S}s` : '–'}
              </span>
            </div>
          </div>

          {/* Card 2: Range */}
          <div className="rounded-xl bg-black/[0.035] px-1 py-1.5">
            <div className="text-[10px] font-medium text-neutral-500">
              Range ({rangeCycleA === rangeCycleB ? rangeCycleA : `${rangeCycleA}/${rangeCycleB}`})
            </div>
            <div className="mt-0.5 flex items-center justify-center gap-1 text-[11.5px] font-semibold text-neutral-900">
              <span className={rangeDelta.winner === 'A' ? 'text-emerald-700 font-bold' : ''}>
                {rangeA ? `${rangeA}k` : '–'}
              </span>
              <span className="text-[9px] text-neutral-300">vs</span>
              <span className={rangeDelta.winner === 'B' ? 'text-emerald-700 font-bold' : ''}>
                {rangeB ? `${rangeB}k` : '–'}
              </span>
            </div>
          </div>

          {/* Card 3: Charge */}
          <div className="rounded-xl bg-black/[0.035] px-1 py-1.5">
            <div className="text-[10px] font-medium text-neutral-500">10–80% Charge</div>
            <div className="mt-0.5 flex items-center justify-center gap-1 text-[11.5px] font-semibold text-neutral-900">
              <span className={chargeDelta.winner === 'A' ? 'text-emerald-700 font-bold' : ''}>
                {minA ? `${minA}m` : '–'}
              </span>
              <span className="text-[9px] text-neutral-300">vs</span>
              <span className={chargeDelta.winner === 'B' ? 'text-emerald-700 font-bold' : ''}>
                {minB ? `${minB}m` : '–'}
              </span>
            </div>
          </div>

          {/* Card 4: Cockpit */}
          <div className="rounded-xl bg-black/[0.035] px-1 py-1.5">
            <div className="text-[10px] font-medium text-neutral-500">Cockpit OS</div>
            <div className="mt-0.5 truncate text-[11px] font-semibold text-neutral-900">
              {vehicleA.cockpit.skin} / {vehicleB.cockpit.skin}
            </div>
          </div>
        </div>
      </div>

      {/* Scrollable Content Body with 4-6 Decision-Driving Dimensions */}
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-2 space-y-4">
        {/* Dimension 1: Acceleration & Performance */}
        <Section
          title="1. Acceleration & Dynamics"
          badge={accelDelta.winner !== 'none' ? accelDelta.text : undefined}
          defaultOpen
        >
          <div className="space-y-2">
            <CompareMetricRow
              label="0–100 km/h Launch"
              valA={pA.zeroTo100S ? `${pA.zeroTo100S} s` : '–'}
              valB={pB.zeroTo100S ? `${pB.zeroTo100S} s` : '–'}
              numericA={pA.zeroTo100S}
              numericB={pB.zeroTo100S}
              better="lower"
              delta={accelDelta}
              hint="0-100 km/h acceleration time in seconds; lower is quicker."
            />

            {Boolean(pA.zeroTo200S || pB.zeroTo200S) && (
              <CompareMetricRow
                label="0–200 km/h"
                valA={pA.zeroTo200S ? `${pA.zeroTo200S} s` : 'Not published'}
                valB={pB.zeroTo200S ? `${pB.zeroTo200S} s` : 'Not published'}
                numericA={pA.zeroTo200S}
                numericB={pB.zeroTo200S}
                better="lower"
              />
            )}

            <CompareMetricRow
              label="Combined Peak Power"
              valA={`${num(pA.powerKw)} kW (${Math.round(pA.powerKw * 1.34102)} hp)`}
              valB={`${num(pB.powerKw)} kW (${Math.round(pB.powerKw * 1.34102)} hp)`}
              numericA={pA.powerKw}
              numericB={pB.powerKw}
              better="higher"
              delta={powerDelta}
            />

            <CompareMetricRow
              label="Peak Torque"
              valA={pA.torqueNm ? `${num(pA.torqueNm)} Nm` : 'Not published'}
              valB={pB.torqueNm ? `${num(pB.torqueNm)} Nm` : 'Not published'}
              numericA={pA.torqueNm}
              numericB={pB.torqueNm}
              better="higher"
            />

            <CompareMetricRow
              label="Top Speed"
              valA={pA.topSpeedKmh ? `${pA.topSpeedKmh} km/h` : '–'}
              valB={pB.topSpeedKmh ? `${pB.topSpeedKmh} km/h` : '–'}
              numericA={pA.topSpeedKmh}
              numericB={pB.topSpeedKmh}
              better="higher"
            />

            <CompareMetricRow
              label="Drive & Motor Count"
              valA={`${variantA.drive} · ${pA.motorCount} ${pA.motorCount === 1 ? 'motor' : 'motors'}`}
              valB={`${variantB.drive} · ${pB.motorCount} ${pB.motorCount === 1 ? 'motor' : 'motors'}`}
            />
          </div>

          <div className="rounded-xl border border-black/[0.05] bg-black/[0.02] p-2.5 text-[11.5px] leading-relaxed text-neutral-600">
            <span className="font-semibold text-neutral-800">Acceleration Takeaway: </span>
            {pA.zeroTo100S && pB.zeroTo100S ? (
              pA.zeroTo100S < pB.zeroTo100S ? (
                <>
                  <strong className="text-neutral-900">{vehicleA.brand} {vehicleA.model}</strong> holds a clear{' '}
                  <span className="font-semibold text-emerald-800">{(pB.zeroTo100S - pA.zeroTo100S).toFixed(2)}s launch lead</span>{' '}
                  with {formatPower(pA.powerKw)} output.
                </>
              ) : (
                <>
                  <strong className="text-neutral-900">{vehicleB.brand} {vehicleB.model}</strong> launches{' '}
                  <span className="font-semibold text-emerald-800">{(pA.zeroTo100S - pB.zeroTo100S).toFixed(2)}s quicker</span>{' '}
                  with {formatPower(pB.powerKw)}.
                </>
              )
            ) : (
              'Both models deliver instantaneous electric torque with multi-motor configurations.'
            )}
          </div>
        </Section>

        {/* Dimension 2: Range & Energy */}
        <Section
          title="2. Range & Endurance"
          badge={rangeDelta.winner !== 'none' ? rangeDelta.text : undefined}
          defaultOpen
        >
          <div className="space-y-2">
            <CompareMetricRow
              label={`Published Range (${rangeCycleA === rangeCycleB ? rangeCycleA : `${rangeCycleA} vs ${rangeCycleB}`})`}
              valA={`${num(rangeA)} km ${rangeCycleA}`}
              valB={`${num(rangeB)} km ${rangeCycleB}`}
              numericA={rangeA}
              numericB={rangeB}
              better="higher"
              delta={rangeDelta}
              hint="Tested under standard driving cycles. Never blend cycles."
            />

            <CompareMetricRow
              label="Battery Capacity"
              valA={`${bA.capacityKwh} kWh (${bA.chemistry})`}
              valB={`${bB.capacityKwh} kWh (${bB.chemistry})`}
              numericA={bA.capacityKwh}
              numericB={bB.capacityKwh}
              better="higher"
            />

            {Boolean(variantA.efficiencyKwhPer100km || variantB.efficiencyKwhPer100km) && (
              <CompareMetricRow
                label="Energy Consumption"
                valA={variantA.efficiencyKwhPer100km ? `${variantA.efficiencyKwhPer100km} kWh/100km` : 'Derived'}
                valB={variantB.efficiencyKwhPer100km ? `${variantB.efficiencyKwhPer100km} kWh/100km` : 'Derived'}
                numericA={variantA.efficiencyKwhPer100km}
                numericB={variantB.efficiencyKwhPer100km}
                better="lower"
              />
            )}
          </div>

          <div className="rounded-xl border border-black/[0.05] bg-black/[0.02] p-2.5 text-[11.5px] leading-relaxed text-neutral-600">
            <span className="font-semibold text-neutral-800">Range Takeaway: </span>
            {rangeA > rangeB ? (
              <>
                <strong className="text-neutral-900">{vehicleA.brand} {vehicleA.model}</strong> gives you{' '}
                <span className="font-semibold text-emerald-800">+{rangeA - rangeB} km more range</span> ({rangeA} km vs {rangeB} km), reducing highway charging stops.
              </>
            ) : rangeB > rangeA ? (
              <>
                <strong className="text-neutral-900">{vehicleB.brand} {vehicleB.model}</strong> leads long-distance range by{' '}
                <span className="font-semibold text-emerald-800">+{rangeB - rangeA} km</span> ({rangeB} km vs {rangeA} km), ideal for extended regional journeys.
              </>
            ) : (
              'Both vehicles provide identical endurance on the standard cycle.'
            )}
          </div>
        </Section>

        {/* Dimension 3: Charging Speed */}
        <Section
          title="3. Charging Speed & Pack Tech"
          badge={chargeDelta.winner !== 'none' ? chargeDelta.text : undefined}
          defaultOpen
        >
          <div className="space-y-2">
            <CompareMetricRow
              label="10–80% Fast Charge"
              valA={minA ? `${minA} min` : 'Not published'}
              valB={minB ? `${minB} min` : 'Not published'}
              numericA={minA}
              numericB={minB}
              better="lower"
              delta={chargeDelta}
            />

            <CompareMetricRow
              label="Voltage Architecture"
              valA={bA.architectureV ? `${bA.architectureV} V` : 'Standard'}
              valB={bB.architectureV ? `${bB.architectureV} V` : 'Standard'}
              numericA={bA.architectureV}
              numericB={bB.architectureV}
              better="higher"
            />

            <CompareMetricRow
              label="Peak Charging Power"
              valA={bA.peakChargeKw ? `${bA.peakChargeKw} kW` : (bA.cRate ? `${bA.cRate}C rate` : '–')}
              valB={bB.peakChargeKw ? `${bB.peakChargeKw} kW` : (bB.cRate ? `${bB.cRate}C rate` : '–')}
              numericA={bA.peakChargeKw}
              numericB={bB.peakChargeKw}
              better="higher"
            />

            <CompareMetricRow
              label="Battery Swapping"
              valA={bA.swappable ? 'Yes (3-min swap)' : 'No (Plug-in DC)'}
              valB={bB.swappable ? 'Yes (3-min swap)' : 'No (Plug-in DC)'}
            />
          </div>

          <div className="rounded-xl border border-black/[0.05] bg-black/[0.02] p-2.5 text-[11.5px] leading-relaxed text-neutral-600">
            <span className="font-semibold text-neutral-800">Charging Takeaway: </span>
            {bA.swappable || bB.swappable ? (
              bA.swappable ? (
                <><strong className="text-neutral-900">{vehicleA.brand}</strong> features autonomous 3-minute Power Swap station battery exchange, bypassing charging queues entirely.</>
              ) : (
                <><strong className="text-neutral-900">{vehicleB.brand}</strong> supports NIO battery swap stations for instantaneous 3-minute pack replacement.</>
              )
            ) : minA && minB ? (
              minA < minB ? (
                <><strong className="text-neutral-900">{vehicleA.brand}</strong> refills its pack {minB - minA} minutes faster on high-speed DC chargers.</>
              ) : (
                <><strong className="text-neutral-900">{vehicleB.brand}</strong> charges faster, regaining 10-80% in {minB} minutes.</>
              )
            ) : (
              'High-voltage 800V architectures allow rapid 10-minute top-ups at modern megawatt chargers.'
            )}
          </div>
        </Section>

        {/* Dimension 4: Cockpit Software */}
        <Section
          title="4. Cockpit Software & Displays"
          badge={`${vehicleA.cockpit.screens.length} vs ${vehicleB.cockpit.screens.length} Screens`}
          defaultOpen
        >
          <div className="space-y-2">
            <CompareMetricRow
              label="Operating System"
              valA={
                <span className="flex items-center gap-1.5 font-medium">
                  <span className="h-2 w-2 rounded-full" style={{ backgroundColor: vehicleA.cockpit.accentColor }} />
                  {vehicleA.cockpit.os}
                </span>
              }
              valB={
                <span className="flex items-center justify-end gap-1.5 font-medium">
                  <span className="h-2 w-2 rounded-full" style={{ backgroundColor: vehicleB.cockpit.accentColor }} />
                  {vehicleB.cockpit.os}
                </span>
              }
            />

            <CompareMetricRow
              label="Cabin Displays Count"
              valA={`${vehicleA.cockpit.screens.length} physical displays`}
              valB={`${vehicleB.cockpit.screens.length} physical displays`}
              numericA={vehicleA.cockpit.screens.length}
              numericB={vehicleB.cockpit.screens.length}
              better="higher"
            />

            <CompareMetricRow
              label="Main Center Display"
              valA={`${vehicleA.cockpit.screens.find((s) => s.role === 'center')?.diagonalIn ?? '–'}" screen`}
              valB={`${vehicleB.cockpit.screens.find((s) => s.role === 'center')?.diagonalIn ?? '–'}" screen`}
            />

            <CompareMetricRow
              label="HUD (Head-Up Display)"
              valA={vehicleA.cockpit.screens.find((s) => s.role === 'hud')?.diagonalIn ? `${vehicleA.cockpit.screens.find((s) => s.role === 'hud')?.diagonalIn}" projected` : 'None'}
              valB={vehicleB.cockpit.screens.find((s) => s.role === 'hud')?.diagonalIn ? `${vehicleB.cockpit.screens.find((s) => s.role === 'hud')?.diagonalIn}" projected` : 'None'}
            />

            <CompareMetricRow
              label="Passenger / Digital Mirrors"
              valA={vehicleA.cockpit.screens.some((s) => s.role === 'passenger' || s.role === 'mirror') ? 'Yes' : 'Standard'}
              valB={vehicleB.cockpit.screens.some((s) => s.role === 'passenger' || s.role === 'mirror') ? 'Yes' : 'Standard'}
            />
          </div>

          <div className="rounded-xl border border-black/[0.05] bg-black/[0.02] p-2.5 text-[11.5px] leading-relaxed text-neutral-600">
            <span className="font-semibold text-neutral-800">Cockpit Takeaway: </span>
            <strong className="text-neutral-900">{vehicleA.cockpit.os}</strong> vs{' '}
            <strong className="text-neutral-900">{vehicleB.cockpit.os}</strong>. Both feature native phone ecosystem continuity,
            rich 3D driving visualizers, and responsive touch interfaces.
          </div>
        </Section>

        {/* Dimension 5: Dimensions & Spatial Footprint */}
        <Section
          title="5. Dimensions & Cabin Space"
          badge={wheelbaseDelta.winner !== 'none' ? wheelbaseDelta.text : undefined}
          defaultOpen={false}
        >
          <div className="space-y-2">
            <CompareMetricRow
              label="Length × Width × Height"
              valA={`${dA.lengthMm} × ${dA.widthMm} × ${dA.heightMm} mm`}
              valB={`${dB.lengthMm} × ${dB.widthMm} × ${dB.heightMm} mm`}
            />

            <CompareMetricRow
              label="Wheelbase (Cabin Room)"
              valA={mm(dA.wheelbaseMm)}
              valB={mm(dB.wheelbaseMm)}
              numericA={dA.wheelbaseMm}
              numericB={dB.wheelbaseMm}
              better="higher"
              delta={wheelbaseDelta}
              hint="Wheelbase determines front and rear row legroom."
            />

            <CompareMetricRow
              label="Kerb Weight"
              valA={dA.kerbWeightKg ? `${num(dA.kerbWeightKg)} kg` : '–'}
              valB={dB.kerbWeightKg ? `${num(dB.kerbWeightKg)} kg` : '–'}
              numericA={dA.kerbWeightKg}
              numericB={dB.kerbWeightKg}
              better="lower"
            />

            {Boolean(variantA.priceCny || variantB.priceCny) && (
              <CompareMetricRow
                label="China Guide Price"
                valA={variantA.priceCny ? `¥${num(variantA.priceCny)}` : '–'}
                valB={variantB.priceCny ? `¥${num(variantB.priceCny)}` : '–'}
                numericA={variantA.priceCny}
                numericB={variantB.priceCny}
                better="lower"
                delta={
                  variantA.priceCny && variantB.priceCny
                    ? variantA.priceCny < variantB.priceCny
                      ? { text: `Model A is ¥${num(variantB.priceCny - variantA.priceCny)} lower`, winner: 'A' }
                      : { text: `Model B is ¥${num(variantA.priceCny - variantB.priceCny)} lower`, winner: 'B' }
                    : undefined
                }
              />
            )}
          </div>
        </Section>

        {/* Summary Decision Helper */}
        <div className="rounded-xl border border-black/[0.08] bg-black/[0.025] p-3 text-[12px]">
          <div className="text-[11px] font-bold uppercase tracking-wider text-neutral-800">
            Decision Summary
          </div>
          <div className="mt-2 grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <span className="font-semibold text-neutral-900">{vehicleA.brand} {vehicleA.model}</span>
              <p className="text-[11px] leading-relaxed text-neutral-600">{vehicleA.tagline}</p>
            </div>
            <div className="space-y-1 text-right">
              <span className="font-semibold text-neutral-900">{vehicleB.brand} {vehicleB.model}</span>
              <p className="text-[11px] leading-relaxed text-neutral-600">{vehicleB.tagline}</p>
            </div>
          </div>
        </div>
      </div>

      {compact && <div className="h-1" />}
    </div>
  );
}
