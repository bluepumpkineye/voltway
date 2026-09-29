import Link from 'next/link';
import { vehicles, bestRange, flagshipVariant } from '@/data/vehicles';

export const metadata = { title: 'Vehicles — Voltway' };

export default function VehiclesPage() {
  return (
    <main className="mx-auto max-w-[1600px] px-5 py-10">
      <h1 className="text-2xl font-semibold tracking-tight text-ink-100">Vehicles</h1>
      <p className="mt-2 max-w-2xl text-[14px] leading-relaxed text-ink-300">
        Seven cars from the current Chinese market. Range is shown on the cycle each
        manufacturer publishes it against, never converted between cycles.
      </p>

      <div className="mt-8 flex flex-col gap-3">
        {vehicles.map((v) => {
          const fv = flagshipVariant(v);
          const r = bestRange(v);
          return (
            <Link
              key={v.slug}
              href={`/vehicles/${v.slug}`}
              className="group grid items-center gap-5 rounded-2xl border hairline bg-ink-850 p-5 transition-colors hover:bg-ink-800 md:grid-cols-[220px_1fr_auto]"
            >
              <div className="flex items-center gap-4">
                <span
                  className="h-11 w-11 shrink-0 rounded-xl ring-1 ring-white/10"
                  style={{ background: v.assets.heroColor }}
                  aria-hidden
                />
                <div className="min-w-0">
                  <div className="text-[11px] uppercase tracking-[0.15em] text-ink-400">
                    {v.brand}
                  </div>
                  <div className="truncate text-[18px] font-medium text-ink-100">{v.model}</div>
                </div>
              </div>

              <p className="text-[13px] leading-relaxed text-ink-300">{v.tagline}</p>

              <dl className="tnum grid grid-cols-4 gap-6 text-right text-[13px]">
                <div>
                  <dt className="text-[11px] text-ink-500">Power</dt>
                  <dd className="text-ink-100">{fv.performance.powerKw} kW</dd>
                </div>
                <div>
                  <dt className="text-[11px] text-ink-500">Battery</dt>
                  <dd className="text-ink-100">{fv.battery.capacityKwh} kWh</dd>
                </div>
                <div>
                  <dt className="text-[11px] text-ink-500">{r?.cycle ?? 'Range'}</dt>
                  <dd className="text-ink-100">{r ? `${r.km} km` : '--'}</dd>
                </div>
                <div>
                  <dt className="text-[11px] text-ink-500">Screens</dt>
                  <dd className="text-ink-100">{v.cockpit.screens.length}</dd>
                </div>
              </dl>
            </Link>
          );
        })}
      </div>
    </main>
  );
}
