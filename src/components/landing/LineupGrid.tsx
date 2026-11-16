'use client';

import React, { useMemo, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import type { LandingCar } from './types';
import styles from './landing.module.css';

type FilterKey = 'all' | 'sedans' | 'suvs' | 'shooting-brake';
type SortKey = 'featured' | 'fastest' | 'power';

const num = (n: number) => n.toLocaleString('en-US');

function matchesFilter(car: LandingCar, filter: FilterKey): boolean {
  if (filter === 'all') return true;
  if (filter === 'sedans') return car.bodyStyle === 'Sedan';
  if (filter === 'suvs') return car.bodyStyle === 'SUV' || car.bodyStyle === 'Coupe SUV';
  if (filter === 'shooting-brake') return car.bodyStyle === 'Shooting Brake';
  return true;
}

function cardStats(car: LandingCar): { name: string; value: string }[] {
  const out: { name: string; value: string }[] = [];
  if (car.zeroTo100S !== null) {
    out.push({ name: '0–100 km/h', value: `${car.zeroTo100S} s` });
  }
  out.push({ name: 'Peak power', value: `${num(Math.round(car.powerKw))} kW` });
  if (car.minPriceCny !== null) {
    out.push({ name: 'From', value: `¥${num(car.minPriceCny)}` });
  } else if (car.maxCltcKm !== null) {
    out.push({ name: 'CLTC range', value: `${num(car.maxCltcKm)} km` });
  }
  return out;
}

export function LineupGrid({ cars }: { cars: LandingCar[] }) {
  const [filter, setFilter] = useState<FilterKey>('all');
  const [sort, setSort] = useState<SortKey>('featured');

  const counts = useMemo(
    () => ({
      all: cars.length,
      sedans: cars.filter((c) => matchesFilter(c, 'sedans')).length,
      suvs: cars.filter((c) => matchesFilter(c, 'suvs')).length,
      'shooting-brake': cars.filter((c) => matchesFilter(c, 'shooting-brake')).length,
    }),
    [cars],
  );

  const visibleCars = useMemo(() => {
    const filtered = cars.filter((c) => matchesFilter(c, filter));
    if (sort === 'featured') return filtered;
    return [...filtered].sort((a, b) => {
      if (sort === 'fastest') {
        const ta = a.zeroTo100S ?? Infinity;
        const tb = b.zeroTo100S ?? Infinity;
        return ta - tb;
      }
      return b.powerKw - a.powerKw;
    });
  }, [cars, filter, sort]);

  const filters: { key: FilterKey; label: string }[] = [
    { key: 'all', label: `All Models (${counts.all})` },
    { key: 'sedans', label: 'Sedans' },
    { key: 'suvs', label: 'SUVs' },
    { key: 'shooting-brake', label: 'Shooting Brake' },
  ];

  const sorts: { key: SortKey; label: string }[] = [
    { key: 'featured', label: 'Featured' },
    { key: 'fastest', label: 'Fastest (0–100)' },
    { key: 'power', label: 'Most Powerful (kW)' },
  ];

  return (
    <section id="models" className={`${styles.section} ${styles.models}`} aria-labelledby="models-h">
      <div className={styles.sectionHeadRow}>
        <div>
          <p className={styles.kicker}>The line-up</p>
          <h2 id="models-h" className={styles.h2}>
            Choose your model
          </h2>
          <p className={styles.sub}>
            {cars.length} cars, each with its own showroom. Open one to change the paint, step inside and run it down the road.
          </p>
        </div>
      </div>

      {/* Interactive Filter & Sort Bar */}
      <div className={styles.controlsBar} role="toolbar" aria-label="Filter and sort models">
        <div className={styles.filterPills} role="group" aria-label="Filter by body style">
          {filters.map((f) => {
            const active = filter === f.key;
            return (
              <button
                key={f.key}
                type="button"
                aria-pressed={active}
                className={`${styles.filterPill} ${active ? styles.filterPillActive : ''}`}
                onClick={() => setFilter(f.key)}
              >
                {active && <span className={styles.filterDot} aria-hidden />}
                <span>{f.label}</span>
              </button>
            );
          })}
        </div>

        <div className={styles.sortGroup} role="group" aria-label="Sort models">
          <span className={styles.sortLabel}>Sort by:</span>
          <div className={styles.sortPills}>
            {sorts.map((s) => {
              const active = sort === s.key;
              return (
                <button
                  key={s.key}
                  type="button"
                  aria-pressed={active}
                  className={`${styles.sortPill} ${active ? styles.sortPillActive : ''}`}
                  onClick={() => setSort(s.key)}
                >
                  {s.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <ul className={styles.grid} key={`${filter}-${sort}`}>
        {visibleCars.map((v, idx) => {
          const name = `${v.brand} ${v.model}`;
          const rowStats = cardStats(v);
          return (
            <li key={v.slug} className={styles.gridItem} style={{ ['--item-i' as string]: idx }}>
              <Link href={`/showroom/${v.slug}`} className={styles.card} aria-label={`${name}: open the showroom`}>
                <span className={styles.art}>
                  <span className={styles.artBadge}>
                    {v.bodyStyle} · {v.year}
                  </span>
                  <Image src={`/landing/${v.slug}.webp`} width={v.imageW} height={v.imageH} alt="" unoptimized />
                </span>
                <span className={styles.body}>
                  <span className={styles.brand}>{v.brand}</span>
                  <span className={styles.name}>{v.model}</span>
                  <span className={styles.meta}>{v.tagline}</span>
                  <dl className={styles.stats}>
                    {rowStats.map((s) => (
                      <div key={s.name}>
                        <dt>{s.name}</dt>
                        <dd className="tnum">{s.value}</dd>
                      </div>
                    ))}
                  </dl>
                  <span className={styles.open}>
                    <span>Open showroom</span>
                    <svg width="14" height="10" viewBox="0 0 14 10" fill="none" aria-hidden>
                      <path
                        d="M1 5h11M8.5 1.5 12.5 5l-4 3.5"
                        stroke="currentColor"
                        strokeWidth="1.6"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </span>
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
