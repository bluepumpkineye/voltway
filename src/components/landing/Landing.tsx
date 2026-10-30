import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import type { Vehicle } from '@/data/vehicles/schema';
import { LINEUP, type Place } from '@/lib/landing/lineup';
import { showroomCars } from '@/lib/showroom/cars';
import { Wordmark } from './Wordmark';
import styles from './landing.module.css';

/** What the showroom does with each car, one line each (the showroom's own tabs). */
const WAYS: { name: string; line: string }[] = [
  { name: 'Colour', line: 'Change the paint and the trim and see it in daylight.' },
  { name: 'Interior', line: 'Sit inside and look around the cabin.' },
  { name: 'Dashboard', line: 'Use the screens and the instruments.' },
  { name: 'Wheels', line: 'Try the wheel designs the car is sold with.' },
  { name: 'Specifications', line: 'Dimensions, battery, charging and range, each on its own cycle.' },
  { name: 'X-ray', line: 'See through the body to the motors and the pack.' },
  { name: 'Charging', line: 'Watch a charge session and how the power flows.' },
  { name: 'Drive', line: 'Run a launch, a curve and a stop and read what the car does.' },
  { name: 'Tech', line: 'See how the technology works, with its claims and sources.' },
];

/** The small print that earns trust: each line is something the showroom itself says and does. */
const PROOF: { name: string; line: string }[] = [
  { name: 'Sourced figures', line: 'Specifications come from manufacturer filings and reporting. Each car lists its sources.' },
  { name: 'One test cycle at a time', line: 'Range is shown on its own cycle. CLTC and WLTP are never mixed.' },
  { name: 'Original 3D models', line: 'Every model is a reconstruction built for this project, not a manufacturer file.' },
  { name: 'Independent', line: 'Voltway is not affiliated with, endorsed by, or a partner of any manufacturer shown.' },
];

const num = (n: number) => n.toLocaleString('en-US');

/** The figures on a car's card: the best of its variants, so the card never mixes one variant's power with another's time. */
function stats(v: Vehicle): { name: string; value: string }[] {
  const out: { name: string; value: string }[] = [];
  const quick = Math.min(...v.variants.map((x) => x.performance.zeroTo100S ?? Infinity));
  if (Number.isFinite(quick)) out.push({ name: '0–100 km/h', value: `${quick.toFixed(quick < 10 ? 1 : 0)} s` });
  const power = Math.max(...v.variants.map((x) => x.performance.powerKw));
  if (Number.isFinite(power) && power > 0) out.push({ name: 'Peak power', value: `${num(Math.round(power))} kW` });
  const price = Math.min(...v.variants.map((x) => x.priceCny ?? Infinity));
  if (Number.isFinite(price)) out.push({ name: 'From', value: `¥${num(price)}` });
  return out;
}

/** The delay of a car's entrance: the back row first, the hero last. */
const DELAY = { back: 0.55, mid: 0.9, front: 1.3 } as const;

function Car({ place, v, i }: { place: Place; v: Vehicle; i: number }) {
  const name = `${v.brand} ${v.model}`;
  // the picture is trimmed with 6 px of room round the car: the mirror image starts two such margins up, so that the tyres meet theirs
  const lift = (12 / place.w) * 100;
  return (
    <li
      className={`${styles.slot} ${styles[place.row]}`}
      style={{ ['--x' as string]: place.x, ['--g' as string]: place.ground, ['--k' as string]: place.k }}
    >
      <Link
        href={`/showroom/${place.slug}`}
        className={styles.car}
        aria-label={`${name}: open the showroom`}
        style={{ ['--d' as string]: `${DELAY[place.row] + i * 0.07}s` }}
      >
        <span className={styles.shadow} aria-hidden />
        <Image className={styles.mirror} src={`/landing/${place.slug}.webp`} width={place.w} height={place.h} alt="" unoptimized style={{ marginTop: `-${lift}%` }} />
        <Image className={styles.pic} src={`/landing/${place.slug}.webp`} width={place.w} height={place.h} alt="" unoptimized priority />
        <span className={styles.tag}>
          <b>{v.brand}</b>
          <span>{v.model}</span>
        </span>
      </Link>
    </li>
  );
}

export function Landing() {
  const cars = showroomCars();
  const bySlug = new Map(cars.map((v) => [v.slug, v]));
  const places = LINEUP.filter((p) => bySlug.has(p.slug));
  // the grid lists the cars in the showcase's order, with the ones that have no picture yet left out
  const pictured = new Set(places.map((p) => p.slug));
  const size = (slug: string) => LINEUP.find((p) => p.slug === slug) as Place;

  return (
    <div className={styles.page}>
      <header id="top" className={styles.hero}>
        <div className={styles.sky} aria-hidden>
          <i className={styles.cloud} />
          <i className={styles.cloud} />
          <i className={styles.cloud} />
        </div>
        <div className={styles.ridges} aria-hidden>
          <Ridges />
        </div>
        <div className={styles.lake} aria-hidden />
        <div className={styles.lakeRidges} aria-hidden>
          <Ridges />
        </div>

        <div className={styles.head}>
          <h1 className={styles.title}>
            <Wordmark className={styles.wordmark} />
          </h1>
          <p className={styles.eyebrow}>The Chinese EV showroom</p>
          <p className={styles.lede}>Choose a car to walk around, sit inside and drive.</p>
        </div>

        <div className={styles.scene}>
          <ul className={styles.fan} aria-label="Models">
            {places.map((p, i) => (
              <Car key={p.slug} place={p} v={bySlug.get(p.slug) as Vehicle} i={i} />
            ))}
          </ul>
        </div>
      </header>

      <main>
        <section id="models" className={`${styles.section} ${styles.models}`} aria-labelledby="models-h">
          <p className={styles.kicker}>The line-up</p>
          <h2 id="models-h" className={styles.h2}>
            Choose your model
          </h2>
          <p className={styles.sub}>
            {cars.length} cars, each with its own showroom. Open one to change the paint, step inside and run it down the road.
          </p>
          <ul className={styles.grid}>
            {cars
              .filter((v) => pictured.has(v.slug))
              .map((v) => {
                const place = size(v.slug);
                const name = `${v.brand} ${v.model}`;
                return (
                  <li key={v.slug}>
                    <Link href={`/showroom/${v.slug}`} className={styles.card} aria-label={`${name}: open the showroom`}>
                      <span className={styles.art}>
                        <Image src={`/landing/${v.slug}.webp`} width={place.w} height={place.h} alt="" unoptimized />
                      </span>
                      <span className={styles.body}>
                        <span className={styles.brand}>{v.brand}</span>
                        <span className={styles.name}>{v.model}</span>
                        <span className={styles.meta}>
                          {v.bodyStyle} · {v.year}
                        </span>
                        <dl className={styles.stats}>
                          {stats(v).map((s) => (
                            <div key={s.name}>
                              <dt>{s.name}</dt>
                              <dd>{s.value}</dd>
                            </div>
                          ))}
                        </dl>
                        <span className={styles.open}>
                          Open showroom
                          <svg width="14" height="10" viewBox="0 0 14 10" fill="none" aria-hidden>
                            <path d="M1 5h11M8.5 1.5 12.5 5l-4 3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        </span>
                      </span>
                    </Link>
                  </li>
                );
              })}
          </ul>
        </section>

        <section className={`${styles.section} ${styles.does}`} aria-labelledby="does-h">
          <p className={styles.kicker}>Inside the showroom</p>
          <h2 id="does-h" className={styles.h2}>
            What you can do with a car
          </h2>
          <ul className={styles.ways}>
            {WAYS.map((w) => (
              <li key={w.name}>
                <b>{w.name}</b>
                <span>{w.line}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className={`${styles.section} ${styles.trust}`} aria-label="How Voltway works">
          <ul className={styles.proof}>
            {PROOF.map((p) => (
              <li key={p.name}>
                <i aria-hidden />
                <b>{p.name}</b>
                <span>{p.line}</span>
              </li>
            ))}
          </ul>
        </section>
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

/** The two ridges of the far shore: pale, soft and low, so that the line-up reads against them. The lake draws the same ones upside down. */
function Ridges() {
  return (
    <svg viewBox="0 0 1600 200" preserveAspectRatio="none" aria-hidden>
      <defs>
        <linearGradient id="ridge-far" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#97aacc" />
          <stop offset="1" stopColor="#d9e0ee" />
        </linearGradient>
        <linearGradient id="ridge-near" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#8196bb" />
          <stop offset="1" stopColor="#cfd9ea" />
        </linearGradient>
      </defs>
      <path
        d="M0 200V118L70 96 150 116 240 70 320 106 410 62 500 100 590 84 680 124 780 112 880 126 980 90 1070 108 1160 58 1250 104 1340 78 1430 108 1510 88 1600 104V200Z"
        fill="url(#ridge-far)"
        opacity="0.8"
      />
      <path
        d="M0 200V150L90 128 190 144 300 112 400 140 520 120 640 150 760 142 860 154 980 136 1100 148 1210 112 1320 138 1430 120 1520 138 1600 128V200Z"
        fill="url(#ridge-near)"
        opacity="0.85"
      />
    </svg>
  );
}
