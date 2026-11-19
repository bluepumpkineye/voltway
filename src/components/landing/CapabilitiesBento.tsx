'use client';

import React, { useCallback, useRef, useState } from 'react';
import {
  ChargingStage,
  ColourStage,
  DashboardStage,
  DriveStage,
  InteriorStage,
  PAINT_SWATCHES,
  SpecificationsStage,
  TechStage,
  WheelsStage,
  XrayStage,
  type PaintSwatch,
} from './BentoWidgets';
import styles from './bento.module.css';

interface CapabilityCardSpec {
  id: string;
  index: string;
  title: string;
  description: string;
  telemetryTag: string;
  spanClass: string;
  dark?: boolean;
}

const CAPABILITIES: CapabilityCardSpec[] = [
  // Row 1 (matches Showroom tab order 01-03): 4 + 4 + 4 = 12 cols
  {
    id: 'colour',
    index: '01',
    title: 'Colour',
    description: 'Change the paint and the trim and see it in daylight.',
    telemetryTag: '5500K STUDIO',
    spanClass: styles.span4,
  },
  {
    id: 'interior',
    index: '02',
    title: 'Interior',
    description: 'Sit inside and look around the cabin.',
    telemetryTag: '360° CABIN',
    spanClass: styles.span4,
  },
  {
    id: 'dashboard',
    index: '03',
    title: 'Dashboard',
    description: 'Use the screens and the instruments.',
    telemetryTag: 'INTERACTIVE HMI',
    spanClass: styles.span4,
  },
  // Row 2 (matches Showroom tab order 04-06): 3 + 4 + 5 = 12 cols
  {
    id: 'wheels',
    index: '04',
    title: 'Wheels',
    description: 'Try the wheel designs the car is sold with.',
    telemetryTag: 'OEM ALLOYS',
    spanClass: styles.span3,
  },
  {
    id: 'specifications',
    index: '05',
    title: 'Specifications',
    description: 'Dimensions, battery, charging and range, each on its own cycle.',
    telemetryTag: 'CYCLE STRICT',
    spanClass: styles.span4,
  },
  {
    id: 'xray',
    index: '06',
    title: 'X-ray',
    description: 'See through the body to the motors and the pack.',
    telemetryTag: 'CTB CUTAWAY',
    spanClass: styles.span5,
    dark: true,
  },
  // Row 3 (matches Showroom tab order 07-09): 4 + 4 + 4 = 12 cols
  {
    id: 'charging',
    index: '07',
    title: 'Charging',
    description: 'Watch a charge session and how the power flows.',
    telemetryTag: '800V CURVE',
    spanClass: styles.span4,
  },
  {
    id: 'drive',
    index: '08',
    title: 'Drive',
    description: 'Run a launch, a curve and a stop and read what the car does.',
    telemetryTag: 'PHYSICS HUD',
    spanClass: styles.span4,
  },
  {
    id: 'tech',
    index: '09',
    title: 'Tech',
    description: 'See how the technology works, with its claims and sources.',
    telemetryTag: 'SENSOR SUITE',
    spanClass: styles.span4,
  },
];

interface TrustItem {
  status: string;
  name: string;
  line: string;
}

const TRUST_ITEMS: TrustItem[] = [
  {
    status: '01 // VERIFIED DATA',
    name: 'Sourced figures',
    line: 'Specifications come from manufacturer filings and reporting. Each car lists its sources.',
  },
  {
    status: '02 // STANDARDIZED',
    name: 'One test cycle at a time',
    line: 'Range is shown on its own cycle. CLTC and WLTP are never mixed.',
  },
  {
    status: '03 // BESPOKE MESH',
    name: 'Original 3D models',
    line: 'Every model is a reconstruction built for this project, not a manufacturer file.',
  },
  {
    status: '04 // UNSPONSORED',
    name: 'Independent',
    line: 'Voltway is not affiliated with, endorsed by, or a partner of any manufacturer shown.',
  },
];

export function CapabilitiesBento() {
  const cardRefs = useRef<(HTMLLIElement | null)[]>([]);
  const [gridHovered, setGridHovered] = useState(false);
  const [chargingHovered, setChargingHovered] = useState(false);
  const [activePaint, setActivePaint] = useState<PaintSwatch>(PAINT_SWATCHES[0]);

  const handleGridMouseMove = useCallback((e: React.MouseEvent<HTMLUListElement>) => {
    const clientX = e.clientX;
    const clientY = e.clientY;
    for (const card of cardRefs.current) {
      if (!card) continue;
      const rect = card.getBoundingClientRect();
      card.style.setProperty('--mouse-x', `${clientX - rect.left}px`);
      card.style.setProperty('--mouse-y', `${clientY - rect.top}px`);
    }
  }, []);

  const renderStage = (id: string) => {
    switch (id) {
      case 'xray':
        return <XrayStage />;
      case 'drive':
        return <DriveStage />;
      case 'colour':
        return <ColourStage activePaint={activePaint} onSelectPaint={setActivePaint} />;
      case 'dashboard':
        return <DashboardStage />;
      case 'charging':
        return <ChargingStage hovered={chargingHovered} />;
      case 'specifications':
        return <SpecificationsStage />;
      case 'interior':
        return <InteriorStage />;
      case 'wheels':
        return <WheelsStage />;
      case 'tech':
        return <TechStage />;
      default:
        return null;
    }
  };

  return (
    <>
      <section id="capabilities" className={styles.bentoSection} aria-labelledby="does-h">
        <div className={styles.headerRow}>
          <div>
            <p className={styles.kicker}>Inside the showroom</p>
            <h2 id="does-h" className={styles.heading}>
              What you can do with a car
            </h2>
          </div>
          <span className={styles.headerMeta}>
            <span className={styles.headerMetaDot} aria-hidden />
            09 INTERACTIVE MODULES
          </span>
        </div>

        <ul
          className={`${styles.bentoGrid} ${gridHovered ? styles.bentoGridActive : ''}`}
          onMouseEnter={() => setGridHovered(true)}
          onMouseLeave={() => setGridHovered(false)}
          onMouseMove={handleGridMouseMove}
        >
          {CAPABILITIES.map((card, i) => (
            <li
              key={card.id}
              ref={(el) => {
                cardRefs.current[i] = el;
              }}
              className={`${styles.card} ${card.spanClass} ${card.dark ? styles.cardDark : ''}`}
              onMouseEnter={card.id === 'charging' ? () => setChargingHovered(true) : undefined}
              onMouseLeave={card.id === 'charging' ? () => setChargingHovered(false) : undefined}
            >
              {card.id === 'colour' && (
                <div
                  className={styles.colourAmbient}
                  aria-hidden
                  style={{
                    background: `radial-gradient(85% 65% at 50% 24%, ${activePaint.glow} 0%, transparent 72%)`,
                  }}
                />
              )}

              {/* Top Zone (60%): Bespoke Interactive Visual Stage */}
              <div className={styles.stageZone}>{renderStage(card.id)}</div>

              {/* Bottom Zone (40%): Monospace Index, Bold Title & Description */}
              <div className={styles.copyZone}>
                <div className={styles.indexRow}>
                  <span className={styles.indexTag}>
                    <span className={styles.indexAccent}>/</span>
                    {card.index}
                  </span>
                  <span className={styles.telemetryHint}>{card.telemetryTag}</span>
                </div>
                <h3 className={styles.cardTitle}>{card.title}</h3>
                <p className={styles.cardDesc}>{card.description}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section id="methodology" className={styles.trustSection} aria-label="How Voltway works">
        <ul className={styles.trustStrip}>
          {TRUST_ITEMS.map((item) => (
            <li key={item.name} className={styles.trustCol}>
              <span className={styles.trustStatusPill}>{item.status}</span>
              <b className={styles.trustTitle}>{item.name}</b>
              <span className={styles.trustDesc}>{item.line}</span>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
