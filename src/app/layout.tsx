import type { Metadata } from 'next';
import Link from 'next/link';
import './globals.css';

export const metadata: Metadata = {
  title: 'Voltway — The Chinese EV Showcase',
  description:
    'Explore the best Chinese electric vehicles in 3D, sit inside them, and use the actual dashboard.',
};

const NAV = [
  { href: '/', label: 'Overview' },
  { href: '/vehicles', label: 'Vehicles' },
  { href: '/compare', label: 'Compare' },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-ink-900 text-ink-100 antialiased">
        <header className="sticky top-0 z-50 border-b hairline bg-ink-900/85 backdrop-blur-xl">
          <div className="mx-auto flex h-14 max-w-[1600px] items-center gap-8 px-5">
            <Link href="/" className="group flex items-center gap-2.5">
              <span className="relative flex h-6 w-6 items-center justify-center">
                <span className="absolute inset-0 rounded-[7px] bg-ember-500/15 ring-1 ring-ember-500/40" />
                <span className="h-2 w-2 rounded-full bg-ember-500 transition-transform group-hover:scale-125" />
              </span>
              <span className="text-[15px] font-semibold tracking-tight">Voltway</span>
            </Link>

            <nav className="flex items-center gap-1">
              {NAV.map((n) => (
                <Link
                  key={n.href}
                  href={n.href}
                  className="rounded-md px-3 py-1.5 text-[13px] font-medium text-ink-300 transition-colors hover:bg-ink-700/60 hover:text-ink-100"
                >
                  {n.label}
                </Link>
              ))}
            </nav>

            <div className="ml-auto hidden items-center gap-2 sm:flex">
              <span className="h-1.5 w-1.5 rounded-full bg-signal-500 animate-pulse-soft" />
              <span className="text-[11px] font-medium uppercase tracking-[0.14em] text-ink-400">
                7 vehicles tracked
              </span>
            </div>
          </div>
        </header>

        {children}

        <footer className="border-t hairline px-5 py-8">
          <div className="mx-auto flex max-w-[1600px] flex-col gap-2 text-[11px] leading-relaxed text-ink-400">
            <p>
              Specifications are compiled from manufacturer filings and reporting, with sources
              cited on each vehicle. Range is shown on its own test cycle —{' '}
              <span className="text-ink-300">CLTC and WLTP are never mixed</span>, since CLTC
              typically reads 25–35% higher for the same car.
            </p>
            <p>
              3D models are original reconstructions built for this project. Voltway is an
              independent showcase and is not affiliated with, endorsed by, or a partner of any
              manufacturer shown.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
