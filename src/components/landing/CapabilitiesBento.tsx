import React from 'react';
import styles from './landing.module.css';

interface WayItem {
  id: string;
  name: string;
  line: string;
  badge?: string;
  accent?: boolean;
  swatches?: string[];
  icon: React.ReactNode;
}

const WAYS: WayItem[] = [
  {
    id: 'colour',
    name: 'Colour',
    line: 'Change the paint and the trim and see it in daylight.',
    accent: true,
    swatches: ['#FACC15', '#2DD4BF', '#991B1B', '#475569'],
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
        <path d="M12 18a4 4 0 0 0 4-4" opacity="0.65" />
      </svg>
    ),
  },
  {
    id: 'interior',
    name: 'Interior',
    line: 'Sit inside and look around the cabin.',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <path d="M7 18v-6a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v6" />
        <path d="M9 10V6a3 3 0 0 1 6 0v4" />
        <path d="M4 15c0 2.8 3.6 5 8 5s8-2.2 8-5" />
      </svg>
    ),
  },
  {
    id: 'dashboard',
    name: 'Dashboard',
    line: 'Use the screens and the instruments.',
    badge: 'Interactive UI',
    accent: true,
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <rect x="2.5" y="5" width="19" height="12" rx="2.5" />
        <path d="M8 20h8" />
        <path d="M7 13a5 5 0 0 1 10 0" />
        <path d="M12 13l2.2-2.2" />
      </svg>
    ),
  },
  {
    id: 'wheels',
    name: 'Wheels',
    line: 'Try the wheel designs the car is sold with.',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <circle cx="12" cy="12" r="9" />
        <circle cx="12" cy="12" r="2.5" />
        <path d="M12 3v6.5M19.8 7.5 14.2 10.7M19.8 16.5l-5.6-3.2M12 21v-6.5M4.2 16.5l5.6-3.2M4.2 7.5l5.6 3.2" />
      </svg>
    ),
  },
  {
    id: 'specifications',
    name: 'Specifications',
    line: 'Dimensions, battery, charging and range, each on its own cycle.',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <path d="M4 20V10M10 20V4M16 20v-7M20 20H3" />
        <path d="M19 6l-3 3M16 6h3v3" opacity="0.7" />
      </svg>
    ),
  },
  {
    id: 'xray',
    name: 'X-ray',
    line: 'See through the body to the motors and the pack.',
    badge: '3D Cutaway',
    accent: true,
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <rect x="6" y="7" width="12" height="10" rx="2" />
        <path d="M4 7h16M4 17h16" opacity="0.5" />
        <path d="M9 12h6M12 9v6" />
        <circle cx="6" cy="5" r="1.5" />
        <circle cx="18" cy="5" r="1.5" />
        <circle cx="6" cy="19" r="1.5" />
        <circle cx="18" cy="19" r="1.5" />
      </svg>
    ),
  },
  {
    id: 'charging',
    name: 'Charging',
    line: 'Watch a charge session and how the power flows.',
    accent: true,
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <path d="M13 2 4.5 13.5h6.5L10 22l9.5-11.5h-6.5L13 2z" />
      </svg>
    ),
  },
  {
    id: 'drive',
    name: 'Drive',
    line: 'Run a launch, a curve and a stop and read what the car does.',
    badge: 'Animated Physics',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <path d="M4 18c3-7 5-10 8-10s5 3 8 10" />
        <path d="M12 8V4M8 14h8" />
        <circle cx="12" cy="18" r="1.5" />
      </svg>
    ),
  },
  {
    id: 'tech',
    name: 'Tech',
    line: 'See how the technology works, with its claims and sources.',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <rect x="7" y="7" width="10" height="10" rx="2" />
        <path d="M10 10h4v4h-4z" />
        <path d="M9 3v4M15 3v4M9 17v4M15 17v4M3 9h4M3 15h4M17 9h4M17 15h4" />
      </svg>
    ),
  },
];

interface ProofItem {
  name: string;
  line: string;
  icon: React.ReactNode;
}

const PROOF: ProofItem[] = [
  {
    name: 'Sourced figures',
    line: 'Specifications come from manufacturer filings and reporting. Each car lists its sources.',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        <path d="m9 12 2 2 4-4" />
      </svg>
    ),
  },
  {
    name: 'One test cycle at a time',
    line: 'Range is shown on its own cycle. CLTC and WLTP are never mixed.',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </svg>
    ),
  },
  {
    name: 'Original 3D models',
    line: 'Every model is a reconstruction built for this project, not a manufacturer file.',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
        <path d="M3.27 6.96 12 12.01l8.73-5.05M12 22.08V12" />
      </svg>
    ),
  },
  {
    name: 'Independent',
    line: 'Voltway is not affiliated with, endorsed by, or a partner of any manufacturer shown.',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <circle cx="12" cy="12" r="10" />
        <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
      </svg>
    ),
  },
];

export function CapabilitiesBento() {
  return (
    <>
      <section id="capabilities" className={`${styles.section} ${styles.does}`} aria-labelledby="does-h">
        <p className={styles.kicker}>Inside the showroom</p>
        <h2 id="does-h" className={styles.h2}>
          What you can do with a car
        </h2>
        <ul className={styles.ways}>
          {WAYS.map((w) => (
            <li key={w.id} className={styles.bentoCard}>
              {/* Decorative corner telemetry graphic */}
              <svg className={styles.bentoTelemetry} width="96" height="64" viewBox="0 0 96 64" fill="none" aria-hidden>
                <path d="M12 58C30 58 40 24 62 24C74 24 82 14 92 10" stroke="currentColor" strokeWidth="1.25" strokeDasharray="3 3" />
                <circle cx="62" cy="24" r="2.5" fill="currentColor" />
                <circle cx="92" cy="10" r="2" fill="currentColor" />
              </svg>

              <div className={styles.bentoTop}>
                <span className={`${styles.bentoIcon} ${w.accent ? styles.bentoIconWarm : styles.bentoIconNeutral}`}>
                  {w.icon}
                </span>
                {w.badge && <span className={styles.bentoBadge}>{w.badge}</span>}
                {w.swatches && (
                  <span className={styles.bentoSwatches} aria-label="Sample exterior paint colours">
                    {w.swatches.map((hex) => (
                      <span key={hex} className={styles.bentoSwatchDot} style={{ backgroundColor: hex }} />
                    ))}
                  </span>
                )}
              </div>

              <b className={styles.bentoTitle}>{w.name}</b>
              <span className={styles.bentoCopy}>{w.line}</span>
            </li>
          ))}
        </ul>
      </section>

      <section id="methodology" className={`${styles.section} ${styles.trust}`} aria-label="How Voltway works">
        <ul className={styles.proof}>
          {PROOF.map((p) => (
            <li key={p.name} className={styles.proofItem}>
              <div className={styles.proofHead}>
                <i className={styles.proofBar} aria-hidden />
                <span className={styles.proofIcon}>{p.icon}</span>
              </div>
              <b>{p.name}</b>
              <span>{p.line}</span>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
