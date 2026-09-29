import Link from 'next/link';
import { vehicles, flagshipVariant, rangeOnCycle } from '@/data/vehicles';
import { chargeMinutes10to80 } from '@/lib/performance';

export const metadata = { title: 'Compare — Voltway' };

export default function ComparePage() {
  const rows = vehicles.map((v) => {
    const fv = flagshipVariant(v);
    return {
      v,
      fv,
      cltc: rangeOnCycle(fv, 'CLTC'),
      wltp: rangeOnCycle(fv, 'WLTP'),
      charge: chargeMinutes10to80(fv),
    };
  });

  return (
    <main className="mx-auto max-w-[1600px] px-5 py-10">
      <h1 className="text-2xl font-semibold tracking-tight text-ink-100">Compare</h1>
      <p className="mt-2 max-w-3xl text-[14px] leading-relaxed text-ink-300">
        Each car&rsquo;s highest-output variant. CLTC and WLTP sit in separate columns on
        purpose &mdash; CLTC typically reads 25&ndash;35% higher than WLTP for the same car,
        so a single blended &ldquo;range&rdquo; column would flatter the Chinese-market
        figures and mislead.
      </p>

      <div className="mt-8 overflow-x-auto rounded-2xl border hairline bg-ink-850">
        <table className="w-full min-w-[1000px] border-collapse text-left">
          <thead>
            <tr className="border-b hairline text-[11px] uppercase tracking-[0.14em] text-ink-400">
              <th scope="col" className="px-5 py-3.5 font-medium">Vehicle</th>
              <th scope="col" className="px-5 py-3.5 text-right font-medium">Power</th>
              <th scope="col" className="px-5 py-3.5 text-right font-medium">0&ndash;100</th>
              <th scope="col" className="px-5 py-3.5 text-right font-medium">Battery</th>
              <th scope="col" className="px-5 py-3.5 text-right font-medium">CLTC</th>
              <th scope="col" className="px-5 py-3.5 text-right font-medium">WLTP</th>
              <th scope="col" className="px-5 py-3.5 text-right font-medium">10&ndash;80%</th>
              <th scope="col" className="px-5 py-3.5 text-right font-medium">Screens</th>
            </tr>
          </thead>
          <tbody className="tnum text-[14px]">
            {rows.map(({ v, fv, cltc, wltp, charge }) => (
              <tr key={v.slug} className="border-b hairline last:border-0 transition-colors hover:bg-ink-800/60">
                <th scope="row" className="px-5 py-4 font-normal">
                  <Link href={`/vehicles/${v.slug}`} className="group flex items-center gap-3">
                    <span
                      className="h-8 w-8 shrink-0 rounded-lg ring-1 ring-white/10"
                      style={{ background: v.assets.heroColor }}
                      aria-hidden
                    />
                    <span>
                      <span className="block text-[11px] uppercase tracking-[0.14em] text-ink-400">
                        {v.brand}
                      </span>
                      <span className="block text-ink-100 group-hover:underline">{v.model}</span>
                    </span>
                  </Link>
                </th>
                <td className="px-5 py-4 text-right text-ink-100">{fv.performance.powerKw} kW</td>
                <td className="px-5 py-4 text-right text-ink-100">
                  {fv.performance.zeroTo100S ? `${fv.performance.zeroTo100S} s` : <span className="text-ink-500">not published</span>}
                </td>
                <td className="px-5 py-4 text-right text-ink-100">
                  {fv.battery.capacityKwh} kWh
                  <span className="ml-1.5 text-[11px] text-ink-500">{fv.battery.chemistry}</span>
                </td>
                <td className="px-5 py-4 text-right text-ink-100">
                  {cltc ? `${cltc} km` : <span className="text-ink-600">&mdash;</span>}
                </td>
                <td className="px-5 py-4 text-right text-ink-100">
                  {wltp ? `${wltp} km` : <span className="text-ink-600">&mdash;</span>}
                </td>
                <td className="px-5 py-4 text-right text-ink-100">
                  {charge !== undefined ? `${charge} min` : <span className="text-ink-600">&mdash;</span>}
                </td>
                <td className="px-5 py-4 text-right text-ink-100">{v.cockpit.screens.length}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="mt-4 text-[12px] leading-relaxed text-ink-500">
        A 10&ndash;80% time shown without a manufacturer figure behind it is derived from the
        pack&rsquo;s C-rate, or from peak charging power with a taper factor applied. Those are
        estimates and are marked as such on the vehicle page.
      </p>
    </main>
  );
}
