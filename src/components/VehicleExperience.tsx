'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import type { Vehicle } from '@/data/vehicles/schema';
import { flagshipVariant } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import {
  DRIVE_MODES, chargeMinutes10to80, effectivePowerKw, effectiveRange,
  effectiveZeroTo100, efficiencyKwhPer100km,
} from '@/lib/performance';
import { HmiSurface } from '@/components/hmi/HmiSurface';
import { HMI_W, HMI_H } from '@/components/hmi/ui';

// three.js has no business in the server bundle
const VehicleViewer = dynamic(
  () => import('@/components/viewer/VehicleViewer').then((m) => m.VehicleViewer),
  {
    ssr: false,
    loading: () => (
      <div className="grid-bg flex h-full w-full items-center justify-center rounded-2xl border hairline bg-ink-850">
        <div className="h-[3px] w-40 overflow-hidden rounded-full bg-ink-600">
          <div className="h-full w-1/3 rounded-full bg-ember-500 animate-sweep" />
        </div>
      </div>
    ),
  },
);

type ViewMode = 'exterior' | 'interior' | 'dashboard';

export function VehicleExperience({ vehicle }: { vehicle: Vehicle }) {
  const [view, setView] = React.useState<ViewMode>('exterior');
  const {
    variantId, setVariant, setCameraMode, driveMode, modeId, setDriveMode, soc, climate, reset,
  } = useVehicleStore();

  const variant =
    vehicle.variants.find((v) => v.id === variantId) ?? flagshipVariant(vehicle);

  // Reset when the visitor moves to a different car.
  React.useEffect(() => {
    reset(flagshipVariant(vehicle).id);
  }, [vehicle.slug, reset, vehicle]);

  const hasModel = Boolean(vehicle.assets.modelUrl);
  // an exterior-only model (no cabin built yet) has nothing to sit in
  const hasCabin = Boolean(vehicle.assets.interiorModelUrl);
  const available = (m: ViewMode) =>
    m === 'dashboard' || (m === 'interior' ? hasCabin : hasModel);

  // Deep links: /vehicles/<slug>?view=interior|dashboard opens that view.
  React.useEffect(() => {
    const v = new URLSearchParams(window.location.search).get('view');
    if ((v === 'exterior' || v === 'interior' || v === 'dashboard') && (v !== 'interior' || hasCabin)) {
      setView(v);
    }
  }, [hasCabin]);

  React.useEffect(() => {
    setCameraMode(view === 'dashboard' ? 'interior' : view);
  }, [view, setCameraMode]);

  const accent = vehicle.cockpit.accentColor;

  // one of the car's own modes, picked on its screen, with its published output
  const carMode = vehicle.cockpit.driveModes?.find((m) => m.id === modeId);
  const power = effectivePowerKw(variant, driveMode, carMode?.powerKw);
  const zero = effectiveZeroTo100(variant, driveMode, carMode?.powerKw);
  const range = effectiveRange(variant, driveMode, soc, climate);
  const eff = efficiencyKwhPer100km(variant, driveMode, climate);
  const charge = chargeMinutes10to80(variant);

  return (
    <div className="flex flex-col gap-3">
      {/* view + variant controls */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex rounded-full bg-ink-800 p-1 ring-1 ring-ink-600">
          {(['exterior', 'interior', 'dashboard'] as ViewMode[]).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setView(m)}
              disabled={!available(m)}
              title={m === 'interior' && hasModel && !hasCabin ? 'Interior not built yet' : undefined}
              aria-pressed={view === m}
              className={`rounded-full px-4 py-1.5 text-[13px] font-medium capitalize transition-colors disabled:cursor-not-allowed disabled:opacity-35 ${
                view === m ? 'bg-ink-600 text-ink-100' : 'text-ink-300 hover:text-ink-100'
              }`}
            >
              {m}
            </button>
          ))}
        </div>

        {vehicle.variants.length > 1 && (
          <div className="flex flex-wrap gap-1.5">
            {vehicle.variants.map((v) => (
              <button
                key={v.id}
                type="button"
                onClick={() => setVariant(v.id)}
                aria-pressed={v.id === variant.id}
                className={`rounded-full px-3.5 py-1.5 text-[13px] transition-colors ring-1 ${
                  v.id === variant.id
                    ? 'bg-ink-700 text-ink-100 ring-ink-500'
                    : 'text-ink-300 ring-ink-700 hover:bg-ink-800 hover:text-ink-100'
                }`}
              >
                {v.name}
              </button>
            ))}
          </div>
        )}

        <div className="ml-auto flex gap-1.5">
          {DRIVE_MODES.map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => setDriveMode(m.id)}
              aria-pressed={driveMode === m.id}
              className="rounded-full px-3.5 py-1.5 text-[13px] font-medium transition-all ring-1"
              style={
                driveMode === m.id
                  ? { background: `${accent}1f`, color: accent, borderColor: accent, boxShadow: `inset 0 0 0 1px ${accent}66` }
                  : { color: '#7c8798', borderColor: 'transparent' }
              }
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* stage */}
      <div className="grid gap-3 lg:grid-cols-[1fr_320px]">
        <div className="relative min-h-[420px] overflow-hidden rounded-2xl border hairline bg-ink-850 lg:min-h-[620px]">
          {view === 'dashboard' ? (
            <DashboardStage vehicle={vehicle} variant={variant} />
          ) : (
            <VehicleViewer vehicle={vehicle} variant={variant} className="h-full w-full" />
          )}

          {view === 'interior' && hasModel && (
            <p className="pointer-events-none absolute bottom-3 left-1/2 -translate-x-1/2 rounded-full bg-ink-900/80 px-4 py-1.5 text-[12px] text-ink-300 backdrop-blur">
              Drag to look around · the centre screen is live
            </p>
          )}
        </div>

        <aside className="flex flex-col gap-3">
          <Panel title="Live readout">
            <Readout
              label="Power"
              value={power}
              unit="kW"
              sub={`${Math.round(power * 1.341)} hp${carMode ? ` · ${carMode.label} mode` : ''}`}
              accent={accent}
            />
            <Readout label="0–100 km/h" value={zero ?? '—'} unit="s" accent={accent} />
            <Readout
              label="Range"
              value={range?.km ?? '—'}
              unit="km"
              sub={range ? `${range.cycle} basis · ${Math.round(soc * 100)}% charge` : undefined}
              accent={accent}
            />
            <Readout label="Consumption" value={eff ?? '—'} unit="kWh/100km" accent={accent} />
            {charge !== undefined && (
              <Readout label="DC charge 10–80%" value={charge} unit="min" accent={accent} />
            )}
          </Panel>

          <Panel title="Cockpit">
            <ul className="flex flex-col gap-2 px-4 pb-4">
              {vehicle.cockpit.screens.map((s) => (
                <li key={s.id} className="flex items-baseline justify-between gap-3 text-[13px]">
                  <span className="text-ink-300">{s.label}</span>
                  <span className="tnum shrink-0 text-ink-100">{s.diagonalIn}&Prime;</span>
                </li>
              ))}
              <li className="mt-1 flex items-baseline justify-between gap-3 border-t hairline pt-2 text-[13px]">
                <span className="text-ink-300">Operating system</span>
                <span className="shrink-0 text-ink-100">{vehicle.cockpit.os}</span>
              </li>
            </ul>
          </Panel>
        </aside>
      </div>
    </div>
  );
}

/** The HMI, flat and full size, scaled to whatever space it is given. */
function DashboardStage({ vehicle, variant }: { vehicle: Vehicle; variant: ReturnType<typeof flagshipVariant> }) {
  const wrap = React.useRef<HTMLDivElement>(null);
  const [scale, setScale] = React.useState(0.5);

  React.useEffect(() => {
    const el = wrap.current;
    if (!el) return;
    const fit = () => {
      const { width, height } = el.getBoundingClientRect();
      setScale(Math.min(width / HMI_W, height / HMI_H) * 0.965);
    };
    fit();
    const ro = new ResizeObserver(fit);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return (
    <div ref={wrap} className="grid-bg flex h-full w-full items-center justify-center overflow-hidden p-3">
      <div
        style={{
          width: HMI_W * scale,
          height: HMI_H * scale,
          // scaling the whole surface keeps every hit target proportional
        }}
        className="relative overflow-hidden rounded-[26px] ring-1 ring-ink-600 shadow-2xl"
      >
        <div style={{ transform: `scale(${scale})`, transformOrigin: 'top left' }}>
          <HmiSurface vehicle={vehicle} variant={variant} />
        </div>
      </div>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border hairline bg-ink-850">
      <h3 className="px-4 pt-3.5 pb-2 text-[11px] font-medium uppercase tracking-[0.16em] text-ink-400">
        {title}
      </h3>
      {children}
    </section>
  );
}

function Readout({
  label,
  value,
  unit,
  sub,
  accent,
}: {
  label: string;
  value: number | string;
  unit: string;
  sub?: string;
  accent: string;
}) {
  return (
    <div className="border-t hairline px-4 py-3 first:border-t-0">
      <div className="text-[12px] text-ink-400">{label}</div>
      <div className="mt-1 flex items-baseline gap-1.5">
        <span className="tnum text-[26px] font-light leading-none" style={{ color: accent }}>
          {value}
        </span>
        <span className="text-[12px] text-ink-400">{unit}</span>
      </div>
      {sub && <div className="tnum mt-1 text-[11px] text-ink-500">{sub}</div>}
    </div>
  );
}
