import { notFound } from 'next/navigation';
import Link from 'next/link';
import { vehicles, getVehicle, flagshipVariant } from '@/data/vehicles';
import { VehicleExperience } from '@/components/VehicleExperience';
import { SpecTable } from '@/components/metrics/SpecTable';

export function generateStaticParams() {
  return vehicles.map((v) => ({ slug: v.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const v = getVehicle(slug);
  if (!v) return { title: 'Not found — Voltway' };
  return { title: `${v.brand} ${v.model} — Voltway`, description: v.tagline };
}

export default async function VehiclePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const vehicle = getVehicle(slug);
  if (!vehicle) notFound();

  const fv = flagshipVariant(vehicle);

  return (
    <main className="mx-auto max-w-[1600px] px-5 py-8">
      <nav className="mb-5 flex items-center gap-2 text-[12px] text-ink-400">
        <Link href="/vehicles" className="hover:text-ink-200">Vehicles</Link>
        <span aria-hidden>/</span>
        <span className="text-ink-200">{vehicle.brand} {vehicle.model}</span>
      </nav>

      <header className="mb-6 flex flex-wrap items-end justify-between gap-5">
        <div>
          <div className="text-[11px] uppercase tracking-[0.16em] text-ink-400">
            {vehicle.group}
          </div>
          <h1 className="mt-1 text-[clamp(1.7rem,3.6vw,2.6rem)] font-semibold leading-tight tracking-tight text-ink-100">
            {vehicle.brand} {vehicle.model}
          </h1>
          <p className="mt-2 max-w-2xl text-[14px] leading-relaxed text-ink-300">
            {vehicle.summary}
          </p>
        </div>
        <dl className="tnum flex gap-8">
          <div>
            <dt className="text-[11px] uppercase tracking-[0.15em] text-ink-400">Peak</dt>
            <dd className="mt-1 text-[26px] font-light text-ink-100">
              {fv.performance.powerKw}<span className="ml-1 text-[13px] text-ink-400">kW</span>
            </dd>
          </div>
          <div>
            <dt className="text-[11px] uppercase tracking-[0.15em] text-ink-400">Battery</dt>
            <dd className="mt-1 text-[26px] font-light text-ink-100">
              {fv.battery.capacityKwh}<span className="ml-1 text-[13px] text-ink-400">kWh</span>
            </dd>
          </div>
        </dl>
      </header>

      {vehicle.dataCaveat && (
        <p className="mb-5 rounded-xl border border-warn-500/25 bg-warn-500/[0.07] px-4 py-3 text-[13px] leading-relaxed text-warn-500">
          {vehicle.dataCaveat}
        </p>
      )}

      <VehicleExperience vehicle={vehicle} />

      <SpecTable vehicle={vehicle} />

      <section className="mt-10">
        <h2 className="text-[11px] font-medium uppercase tracking-[0.16em] text-ink-400">
          Sources
        </h2>
        <ul className="mt-3 flex flex-col gap-1.5">
          {vehicle.sources.map((s) => (
            <li key={s.url}>
              <a
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[13px] text-ink-300 underline decoration-ink-600 underline-offset-4 transition-colors hover:text-ink-100"
              >
                {s.label}
              </a>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
