import Link from 'next/link';
import { vehicles, bestRange, flagshipVariant } from '@/data/vehicles';

export default function HomePage() {
  const hero = vehicles[0];
  const heroVariant = flagshipVariant(hero);

  return (
    <main className="mx-auto max-w-[1600px] px-5 py-10">
      <section className="grid-bg relative overflow-hidden rounded-3xl border hairline bg-ink-850 px-8 py-14 sm:px-14 sm:py-20">
        <div className="relative max-w-2xl">
          <span className="inline-flex items-center gap-2 rounded-full bg-ember-500/10 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.16em] text-ember-400 ring-1 ring-ember-500/25">
            <span className="h-1.5 w-1.5 rounded-full bg-ember-500" />
            Proof of concept
          </span>
          <h1 className="mt-5 text-[clamp(2.2rem,5vw,3.6rem)] font-semibold leading-[1.05] tracking-tight text-ink-100">
            Sit inside the cars
            <br />
            China is building.
          </h1>
          <p className="mt-5 max-w-xl text-[15px] leading-relaxed text-ink-300">
            Seven electric vehicles, reconstructed in 3D. Open the door, take the driver&rsquo;s
            seat, and use the centre screen the way you would in the car &mdash; climate,
            drive modes, navigation, ambient lighting. Every control changes what the car
            reports back.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href={`/vehicles/${hero.slug}`}
              className="rounded-full bg-ember-500 px-6 py-3 text-[14px] font-semibold text-ink-900 transition-colors hover:bg-ember-400"
            >
              Open the {hero.model}
            </Link>
            <Link
              href="/compare"
              className="rounded-full px-6 py-3 text-[14px] font-medium text-ink-200 ring-1 ring-ink-600 transition-colors hover:bg-ink-800"
            >
              Compare all seven
            </Link>
          </div>
        </div>

        <dl className="relative mt-14 grid grid-cols-2 gap-6 sm:grid-cols-4 sm:gap-10">
          <Stat label="Peak power" value={`${heroVariant.performance.powerKw}`} unit="kW" />
          <Stat label="0&ndash;100 km/h" value={`${heroVariant.performance.zeroTo100S}`} unit="s" />
          <Stat label="Battery" value={`${heroVariant.battery.capacityKwh}`} unit="kWh" />
          <Stat
            label="Range"
            value={`${bestRange(hero)?.km ?? '--'}`}
            unit={`km ${bestRange(hero)?.cycle ?? ''}`}
          />
        </dl>
      </section>

      <section className="mt-12">
        <div className="flex items-baseline justify-between">
          <h2 className="text-lg font-semibold tracking-tight text-ink-100">The first batch</h2>
          <Link href="/vehicles" className="text-[13px] text-ink-300 hover:text-ink-100">
            All vehicles &rarr;
          </Link>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {vehicles.map((v) => {
            const fv = flagshipVariant(v);
            const r = bestRange(v);
            return (
              <Link
                key={v.slug}
                href={`/vehicles/${v.slug}`}
                className="group relative flex flex-col overflow-hidden rounded-2xl border hairline bg-ink-850 p-5 transition-colors hover:bg-ink-800"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-[11px] uppercase tracking-[0.15em] text-ink-400">
                      {v.brand}
                    </div>
                    <div className="mt-0.5 text-[19px] font-medium text-ink-100">{v.model}</div>
                  </div>
                  <span
                    className="h-8 w-8 shrink-0 rounded-lg ring-1 ring-white/10"
                    style={{ background: v.assets.heroColor }}
                    aria-hidden
                  />
                </div>

                <p className="mt-3 line-clamp-2 text-[13px] leading-relaxed text-ink-300">
                  {v.tagline}
                </p>

                <dl className="tnum mt-5 grid grid-cols-3 gap-2 border-t hairline pt-4 text-[12px]">
                  <div>
                    <dt className="text-ink-500">kW</dt>
                    <dd className="text-ink-100">{fv.performance.powerKw}</dd>
                  </div>
                  <div>
                    <dt className="text-ink-500">kWh</dt>
                    <dd className="text-ink-100">{fv.battery.capacityKwh}</dd>
                  </div>
                  <div>
                    <dt className="text-ink-500">{r?.cycle ?? 'Range'}</dt>
                    <dd className="text-ink-100">{r ? `${r.km} km` : '--'}</dd>
                  </div>
                </dl>

                {v.assets.modelUrl && (
                  <span className="mt-4 inline-flex w-fit items-center gap-1.5 rounded-full bg-signal-500/10 px-2.5 py-1 text-[11px] font-medium text-signal-400 ring-1 ring-signal-500/25">
                    <span className="h-1 w-1 rounded-full bg-signal-500" />
                    {v.assets.interiorModelUrl ? '3D cockpit ready' : '3D exterior ready'}
                  </span>
                )}
              </Link>
            );
          })}
        </div>
      </section>
    </main>
  );
}

function Stat({ label, value, unit }: { label: string; value: string; unit: string }) {
  return (
    <div>
      <dt className="text-[11px] uppercase tracking-[0.15em] text-ink-400">{label}</dt>
      <dd className="tnum mt-1.5 text-[30px] font-light leading-none text-ink-100">
        {value}
        <span className="ml-1.5 text-[13px] text-ink-400">{unit}</span>
      </dd>
    </div>
  );
}
