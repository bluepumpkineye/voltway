import React from 'react';
import type { Vehicle } from '@/data/vehicles/schema';
import { LINEUP, type Place } from '@/lib/landing/lineup';
import { showroomCars } from '@/lib/showroom/cars';
import { Navbar } from './Navbar';
import { HeroOrbit } from './HeroOrbit';
import { LineupGrid } from './LineupGrid';
import { CapabilitiesBento } from './CapabilitiesBento';
import type { LandingCar } from './types';
import styles from './landing.module.css';

function toLandingCar(v: Vehicle, place: Place): LandingCar {
  const times = v.variants
    .map((x) => x.performance.zeroTo100S)
    .filter((n): n is number => typeof n === 'number' && Number.isFinite(n));
  const prices = v.variants
    .map((x) => x.priceCny)
    .filter((n): n is number => typeof n === 'number' && Number.isFinite(n));
  const cltc = v.variants
    .flatMap((x) => x.range)
    .filter((r) => r.cycle === 'CLTC')
    .map((r) => r.km);

  return {
    slug: v.slug,
    brand: v.brand,
    model: v.model,
    group: v.group,
    bodyStyle: v.bodyStyle,
    year: v.year,
    tagline: v.tagline,
    imageW: place.w,
    imageH: place.h,
    zeroTo100S: times.length ? Math.min(...times) : null,
    powerKw: Math.max(...v.variants.map((x) => x.performance.powerKw)),
    minPriceCny: prices.length ? Math.min(...prices) : null,
    maxCltcKm: cltc.length ? Math.max(...cltc) : null,
  };
}

export function Landing() {
  const cars = showroomCars();
  const placeBySlug = new Map(LINEUP.map((p) => [p.slug, p]));
  const landingCars = cars
    .filter((v) => placeBySlug.has(v.slug))
    .map((v) => toLandingCar(v, placeBySlug.get(v.slug) as Place));

  return (
    <div className={styles.page}>
      <Navbar carCount={landingCars.length} />

      <HeroOrbit cars={landingCars} />

      <main>
        <LineupGrid cars={landingCars} />
        <CapabilitiesBento />
      </main>

      <footer className={styles.foot}>
        <div className={styles.section}>
          <strong>Voltway</strong>
          <p style={{ margin: 0 }}>
            An independent showcase of Chinese electric cars. Brand names and models belong to their makers and are used here only to name the
            cars. Figures are compiled from public filings and reporting and can differ from a car as sold.
          </p>
          <p style={{ margin: 0 }}>
            <a href="#top">Back to the top</a>
          </p>
        </div>
      </footer>
    </div>
  );
}
