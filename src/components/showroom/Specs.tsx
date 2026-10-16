'use client';

import React from 'react';
import type { Variant, Vehicle } from '@/data/vehicles/schema';
import { chargeMinutes10to80 } from '@/lib/performance';
import type { DimensionFocus } from '@/store/vehicle-store';
import { FOCUS, GLASS } from './Chrome';

/** How wide the specification column is, px, on a window wide enough to stand it beside the car. */
export const SPECS_COLUMN_W = 392;

const mm = (v: number) => `${v.toLocaleString('en-US')} mm`;
const num = (v: number) => v.toLocaleString('en-US');
const NOT_PUBLISHED = <span className="text-neutral-400">not published</span>;

function Section({
  title,
  summary,
  defaultOpen = false,
  children,
}: {
  title: string;
  /** shown beside the title while the section is shut */
  summary?: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = React.useState(defaultOpen);
  return (
    <section className="border-t border-black/[0.06]">
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className={`flex w-full items-center justify-between gap-3 py-2.5 text-left ${FOCUS}`}
      >
        <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-neutral-500">{title}</span>
        <span className="flex min-w-0 items-center gap-2 text-[12px] text-neutral-500">
          {!open && summary && <span className="tnum truncate">{summary}</span>}
          <svg className={`shrink-0 transition-transform ${open ? 'rotate-180' : ''}`} width="9" height="6" viewBox="0 0 9 6" aria-hidden>
            <path d="M1 1l3.5 3.5L8 1" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
      </button>
      {open && <div className="pb-3">{children}</div>}
    </section>
  );
}

function Row({ label, children, hint }: { label: string; children: React.ReactNode; hint?: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-1 text-[13px]" title={hint}>
      <dt className="text-neutral-500">{label}</dt>
      <dd className="tnum text-right text-neutral-900">{children}</dd>
    </div>
  );
}

/**
 * The Dimensions tab's specification sheet: the car's published dimensions (a row picks the ruler drawn on the car), and
 * what the old vehicle page held, now beside the car: performance, battery and range, charging, the cabin's screens,
 * the sources. Range stays on its own cycle (CLTC and WLTP are never mixed), and a figure the maker does not publish
 * says so. A column at the right of a wide window; in the dock of a narrow one.
 */
export function SpecsPanel({
  vehicle,
  variant,
  onVariant,
  dimension,
  onDimension,
  sources,
  onCharging,
  compact,
}: {
  vehicle: Vehicle;
  variant: Variant;
  onVariant: (id: string) => void;
  dimension: DimensionFocus;
  onDimension: (d: DimensionFocus) => void;
  sources: { label: string; url: string }[];
  /** open the Charging tab, when the car has one */
  onCharging?: () => void;
  compact: boolean;
}) {
  const d = vehicle.dimensions;
  const p = variant.performance;
  const b = variant.battery;
  const published = b.chargeMinutes10to80 !== undefined;
  const minutes = chargeMinutes10to80(variant);
  const ch = vehicle.charging && Math.abs(vehicle.charging.packKwh - b.capacityKwh) < 1 ? vehicle.charging : undefined;
  const bigScreens = vehicle.cockpit.screens;

  const dims: { id: DimensionFocus; label: string; value: number }[] = [
    { id: 'length', label: 'Length', value: d.lengthMm },
    { id: 'width', label: 'Width', value: d.widthMm },
    { id: 'height', label: 'Height', value: d.heightMm },
  ];

  return (
    <div className={`pointer-events-auto flex max-h-full w-full flex-col overflow-hidden rounded-2xl ${GLASS}`}>
      <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-1 pt-3">
        <header>
          <div className="text-[11px] uppercase tracking-[0.12em] text-neutral-500">
            {vehicle.group} · {vehicle.bodyStyle} · {vehicle.year}
          </div>
          <h2 className="mt-0.5 text-[17px] font-semibold leading-tight tracking-tight text-neutral-900">
            {vehicle.brand} {vehicle.model}
          </h2>
          <p className="mt-1 text-[12px] leading-snug text-neutral-600">{vehicle.tagline}</p>
        </header>

        {vehicle.variants.length > 1 && (
          <div role="group" aria-label="Variant" className="mt-3 flex gap-1 overflow-x-auto rounded-full bg-black/[0.04] p-0.5">
            {vehicle.variants.map((v) => (
              <button
                key={v.id}
                type="button"
                aria-pressed={v.id === variant.id}
                onClick={() => onVariant(v.id)}
                title={v.name}
                className={`shrink-0 whitespace-nowrap rounded-full px-3 py-1 text-[11.5px] font-medium transition-colors ${FOCUS} ${
                  v.id === variant.id ? 'bg-white text-neutral-900 shadow-sm' : 'text-neutral-500 hover:text-neutral-800'
                }`}
              >
                {v.name}
              </button>
            ))}
          </div>
        )}

        {/* the headline figures, at a glance */}
        <dl className="tnum mt-3 grid grid-cols-4 gap-2 text-center">
          {[
            { k: 'Power', v: num(p.powerKw), u: 'kW' },
            { k: '0–100', v: p.zeroTo100S ? `${p.zeroTo100S}` : '–', u: p.zeroTo100S ? 's' : '' },
            { k: variant.range[0]?.cycle ?? 'Range', v: variant.range[0] ? num(variant.range[0].km) : '–', u: variant.range[0] ? 'km' : '' },
            { k: 'Battery', v: `${b.capacityKwh}`, u: 'kWh' },
          ].map((s) => (
            <div key={s.k} className="rounded-xl bg-black/[0.04] px-1 py-2">
              <dt className="text-[10.5px] text-neutral-500">{s.k}</dt>
              <dd className="mt-0.5 text-[18px] font-light leading-none text-neutral-900">
                {s.v}
                <span className="ml-0.5 text-[10.5px] text-neutral-500">{s.u}</span>
              </dd>
            </div>
          ))}
        </dl>

        <div className="mt-2">
          <Section title="Dimensions" summary={`${d.lengthMm.toLocaleString('en-US')} × ${d.widthMm.toLocaleString('en-US')} × ${d.heightMm.toLocaleString('en-US')} mm`} defaultOpen>
            <p className="mb-1 text-[11px] text-neutral-500">Pick one to see it drawn on the car.</p>
            <div role="group" aria-label="Dimension drawn on the car" className="flex flex-col gap-1">
              {dims.map((x) => (
                <button
                  key={x.id}
                  type="button"
                  aria-pressed={dimension === x.id}
                  onClick={() => onDimension(x.id)}
                  className={`flex items-baseline justify-between rounded-xl px-3 py-2 text-[13px] transition-colors ${FOCUS} ${
                    dimension === x.id ? 'bg-neutral-900 text-white' : 'bg-black/[0.04] text-neutral-800 hover:bg-black/[0.07]'
                  }`}
                >
                  <span>{x.label}</span>
                  <span className="tnum">{mm(x.value)}</span>
                </button>
              ))}
            </div>
            <dl className="mt-2">
              <Row label="Wheelbase">{mm(d.wheelbaseMm)}</Row>
              <Row label="Kerb weight">{d.kerbWeightKg ? `${d.kerbWeightKg.toLocaleString('en-US')} kg` : NOT_PUBLISHED}</Row>
            </dl>
          </Section>

          <Section title="Performance" summary={`${num(p.powerKw)} kW${p.zeroTo100S ? ` · ${p.zeroTo100S} s` : ''}`} defaultOpen>
            <dl>
              <Row label="Peak power">{num(p.powerKw)} kW <span className="text-neutral-400">({Math.round(p.powerKw * 1.34102)} hp)</span></Row>
              <Row label="Peak torque">{p.torqueNm ? `${p.torqueNm.toLocaleString('en-US')} Nm` : NOT_PUBLISHED}</Row>
              <Row label="0–100 km/h">{p.zeroTo100S ? `${p.zeroTo100S} s` : NOT_PUBLISHED}</Row>
              {p.zeroTo200S && <Row label="0–200 km/h">{p.zeroTo200S} s</Row>}
              <Row label="Top speed">{p.topSpeedKmh ? `${p.topSpeedKmh} km/h` : NOT_PUBLISHED}</Row>
              <Row label="Drive">{variant.drive}, {p.motorCount} {p.motorCount === 1 ? 'motor' : 'motors'}</Row>
            </dl>
          </Section>

          <Section title="Battery, range and charging" summary={`${b.capacityKwh} kWh${variant.range[0] ? ` · ${variant.range[0].km} km ${variant.range[0].cycle}` : ''}`}>
            <dl>
              <Row label="Pack">{b.capacityKwh} kWh <span className="text-neutral-400">{b.chemistry}</span></Row>
              {b.architectureV && <Row label="Architecture">{b.architectureV} V</Row>}
              {variant.range.map((r) => (
                <Row key={r.cycle} label={`Range, ${r.cycle}`} hint="Each cycle is shown on its own: CLTC reads 25–35% higher than WLTP for the same car.">
                  {num(r.km)} km
                </Row>
              ))}
              {variant.efficiencyKwhPer100km && <Row label="Consumption">{variant.efficiencyKwhPer100km} kWh/100 km</Row>}
              {ch ? (
                <Row label={`Fast charge ${ch.window.from}–${ch.window.to} %`}>{ch.window.minutes} min</Row>
              ) : (
                <Row
                  label="Fast charge 10–80 %"
                  hint={published ? undefined : 'Not a published figure: derived from the pack’s C-rate or its peak charging power, with a taper allowed for.'}
                >
                  {minutes !== undefined ? (
                    <>
                      {minutes} min {!published && <span className="text-neutral-400">estimated</span>}
                    </>
                  ) : (
                    NOT_PUBLISHED
                  )}
                </Row>
              )}
              {b.peakChargeKw && <Row label="Peak charging">{b.peakChargeKw} kW</Row>}
              {b.swappable && <Row label="Battery swap">Yes</Row>}
            </dl>
            {onCharging && (
              <button
                type="button"
                onClick={onCharging}
                className={`mt-2 w-full rounded-xl bg-black/[0.05] px-3 py-2 text-left text-[12px] font-medium text-neutral-800 hover:bg-black/[0.08] ${FOCUS}`}
              >
                Watch it charge <span aria-hidden>→</span>
              </button>
            )}
          </Section>

          <Section title="Cabin" summary={`${vehicle.cockpit.os} · ${bigScreens.length} screens`}>
            <dl>
              <Row label="System">{vehicle.cockpit.os}</Row>
              {bigScreens.map((s) => (
                <Row key={s.id} label={s.label}>
                  {s.diagonalIn} in
                </Row>
              ))}
            </dl>
          </Section>

          {variant.priceCny && (
            <Section title="Price" summary={`¥${variant.priceCny.toLocaleString('en-US')}`}>
              <dl>
                <Row label={variant.name}>¥{variant.priceCny.toLocaleString('en-US')}</Row>
              </dl>
              <p className="text-[11px] text-neutral-500">Guide price in China, in yuan.</p>
            </Section>
          )}

          <Section title="About the car">
            <p className="text-[12px] leading-relaxed text-neutral-600">{vehicle.summary}</p>
            {vehicle.dataCaveat && (
              <p className="mt-2 rounded-xl border border-amber-500/25 bg-amber-400/10 px-3 py-2 text-[12px] leading-snug text-amber-900">
                {vehicle.dataCaveat}
              </p>
            )}
          </Section>

          <Section title="Sources" summary={`${sources.length}`}>
            <ul className="space-y-1 text-[12px]">
              {sources.map((s) => (
                <li key={s.url}>
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-neutral-600 underline decoration-neutral-300 underline-offset-2 hover:text-neutral-950"
                  >
                    {s.label}
                  </a>
                </li>
              ))}
            </ul>
          </Section>
        </div>
      </div>
      {compact && <div className="h-1" />}
    </div>
  );
}
