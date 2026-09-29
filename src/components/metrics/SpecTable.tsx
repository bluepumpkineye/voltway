import type { Vehicle } from '@/data/vehicles/schema';
import { chargeMinutes10to80 } from '@/lib/performance';

/** Full variant-by-variant breakdown, rendered on the server. */
export function SpecTable({ vehicle }: { vehicle: Vehicle }) {
  const d = vehicle.dimensions;
  return (
    <section className="mt-10 grid gap-3 lg:grid-cols-[1fr_320px]">
      <div className="overflow-x-auto rounded-2xl border hairline bg-ink-850">
        <table className="w-full min-w-[720px] border-collapse text-left">
          <caption className="px-5 pt-4 pb-3 text-left text-[11px] font-medium uppercase tracking-[0.16em] text-ink-400">
            Variants
          </caption>
          <thead>
            <tr className="border-b hairline text-[11px] uppercase tracking-[0.14em] text-ink-400">
              <th scope="col" className="px-5 py-3 font-medium">Variant</th>
              <th scope="col" className="px-5 py-3 text-right font-medium">Drive</th>
              <th scope="col" className="px-5 py-3 text-right font-medium">Power</th>
              <th scope="col" className="px-5 py-3 text-right font-medium">Torque</th>
              <th scope="col" className="px-5 py-3 text-right font-medium">Battery</th>
              <th scope="col" className="px-5 py-3 text-right font-medium">Range</th>
              <th scope="col" className="px-5 py-3 text-right font-medium">10&ndash;80%</th>
            </tr>
          </thead>
          <tbody className="tnum text-[13px]">
            {vehicle.variants.map((v) => {
              const charge = chargeMinutes10to80(v);
              return (
                <tr key={v.id} className="border-b hairline last:border-0">
                  <th scope="row" className="px-5 py-3.5 font-normal text-ink-100">{v.name}</th>
                  <td className="px-5 py-3.5 text-right text-ink-200">{v.drive}</td>
                  <td className="px-5 py-3.5 text-right text-ink-200">{v.performance.powerKw} kW</td>
                  <td className="px-5 py-3.5 text-right text-ink-200">
                    {v.performance.torqueNm ? `${v.performance.torqueNm} Nm` : <span className="text-ink-600">&mdash;</span>}
                  </td>
                  <td className="px-5 py-3.5 text-right text-ink-200">
                    {v.battery.capacityKwh} kWh
                    <span className="ml-1.5 text-[11px] text-ink-500">{v.battery.chemistry}</span>
                  </td>
                  <td className="px-5 py-3.5 text-right text-ink-200">
                    {v.range.map((r) => (
                      <span key={r.cycle} className="ml-2 whitespace-nowrap">
                        {r.km} km
                        <span className="ml-1 text-[11px] text-ink-500">{r.cycle}</span>
                      </span>
                    ))}
                  </td>
                  <td className="px-5 py-3.5 text-right text-ink-200">
                    {charge !== undefined ? `${charge} min` : <span className="text-ink-600">&mdash;</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="rounded-2xl border hairline bg-ink-850 p-5">
        <h3 className="text-[11px] font-medium uppercase tracking-[0.16em] text-ink-400">
          Dimensions
        </h3>
        <dl className="tnum mt-3 flex flex-col gap-2 text-[13px]">
          <Dim label="Length" value={`${d.lengthMm} mm`} />
          <Dim label="Width" value={`${d.widthMm} mm`} />
          <Dim label="Height" value={`${d.heightMm} mm`} />
          <Dim label="Wheelbase" value={`${d.wheelbaseMm} mm`} />
          {d.kerbWeightKg && <Dim label="Kerb weight" value={`${d.kerbWeightKg} kg`} />}
          <Dim label="Body" value={vehicle.bodyStyle} />
        </dl>
      </div>
    </section>
  );
}

function Dim({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b hairline pb-2 last:border-0">
      <dt className="text-ink-400">{label}</dt>
      <dd className="text-ink-100">{value}</dd>
    </div>
  );
}
