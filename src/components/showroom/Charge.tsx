'use client';

import React from 'react';
import { PEAK_KW, SIM_SECONDS } from '@/lib/tech/charge';
import { useChargeReadout, useRuntime, type Runtime } from '@/lib/tech/session';
import { useVehicleStore } from '@/store/vehicle-store';
import { GLASS } from './Chrome';

const W = 600;
const H = 78;
/** the chart's top, kW */
const KW_MAX = 660;

const mmss = (s: number) => {
  const n = Math.round(s);
  return `${Math.floor(n / 60)}:${String(n % 60).padStart(2, '0')}`;
};

/**
 * The fast-charge demo's own panel, the showroom's and not the car's: the charging curve of the run (power against
 * the simulated minutes) with where the car is on it, and the numbers. The 620 kW peak and the ten minutes from 10 to
 * 80 % are the maker's, at best; the curve's shape between them is ours, and ten minutes play in fourteen seconds: the
 * panel says all three.
 */
export function ChargeTools() {
  const charge = useRuntime()?.charge;
  const r = useChargeReadout();
  const soc = useVehicleStore((s) => s.soc);

  const path = React.useMemo(() => {
    if (!charge) return { line: '', area: '' };
    const pts = charge.curve.filter((_, i) => i % 5 === 0 || i === charge.curve.length - 1);
    const xy = pts.map((p) => [(p.s / SIM_SECONDS) * W, H - 6 - (p.kw / KW_MAX) * (H - 10)] as const);
    const line = 'M' + xy.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join(' L');
    return { line, area: `${line} L${W} ${H} L0 ${H} Z` };
  }, [charge]);

  const sim = r ? Math.min(SIM_SECONDS, r.elapsed) : 0;
  const x = (sim / SIM_SECONDS) * W;
  const y = r ? H - 6 - (Math.max(r.kw, curveKw(charge, sim)) / KW_MAX) * (H - 10) : H;
  const peakY = H - 6 - (PEAK_KW / KW_MAX) * (H - 10);

  return (
    <div className={`pointer-events-auto w-full max-w-[620px] rounded-2xl px-3.5 py-2.5 ${GLASS}`}>
      <div className="flex items-baseline justify-between gap-3">
        <div className="flex items-baseline gap-1.5">
          <span className="tnum text-[28px] font-semibold leading-none tracking-tight text-neutral-900">{Math.round((r?.soc ?? soc) * 100)}</span>
          <span className="text-[12px] text-neutral-500">% charged</span>
        </div>
        <div className="tnum flex items-baseline gap-1">
          <span className="text-[22px] font-medium leading-none text-neutral-900">{Math.round(r?.kw ?? 0)}</span>
          <span className="text-[12px] text-neutral-500">kW</span>
        </div>
        <div className="tnum text-right text-[12px] leading-tight text-neutral-600">
          <div>{r ? mmss(r.elapsed) : '0:00'} charging</div>
          <div className="text-neutral-400">{r ? r.kwh.toFixed(1) : '0.0'} kWh added</div>
        </div>
      </div>
      <figure className="mt-1.5">
        <svg viewBox={`0 0 ${W} ${H}`} className="block h-[56px] w-full" role="img" aria-label="Charging power against time">
          <line x1="0" x2={W} y1={peakY} y2={peakY} stroke="#c9ccd2" strokeWidth="1" strokeDasharray="3 4" vectorEffect="non-scaling-stroke" />
          <path d={path.area} fill="#2f6bff" opacity="0.08" />
          <path d={path.line} fill="none" stroke="#8a8f98" strokeWidth="1.4" strokeOpacity="0.7" vectorEffect="non-scaling-stroke" />
          <clipPath id="chargeDone">
            <rect x="0" y="0" width={x} height={H} />
          </clipPath>
          <path d={path.line} fill="none" stroke="#2f6bff" strokeWidth="2.4" strokeLinejoin="round" vectorEffect="non-scaling-stroke" clipPath="url(#chargeDone)" />
          {r && r.elapsed > 0 && <circle cx={x} cy={y} r="4" fill="#2f6bff" vectorEffect="non-scaling-stroke" />}
        </svg>
        <figcaption className="mt-0.5 flex flex-wrap justify-between gap-x-3 text-[10.5px] leading-snug text-neutral-500">
          <span>Power, 10 to 80 % (simulated curve)</span>
          <span className="tnum">
            Peak {PEAK_KW} kW · 10 to 80 % in 10 min, at best <span className="text-neutral-400">published</span>
          </span>
        </figcaption>
      </figure>
    </div>
  );
}

function curveKw(charge: NonNullable<Runtime['charge']> | null | undefined, sim: number): number {
  if (!charge) return 0;
  const c = charge.curve;
  return c[Math.min(c.length - 1, Math.max(0, Math.round(sim)))]?.kw ?? 0;
}
