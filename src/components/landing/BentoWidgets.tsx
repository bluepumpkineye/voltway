'use client';

import React, { useEffect, useRef, useState } from 'react';
import styles from './bento.module.css';

/* ================================================================================================
   01 / X-RAY — Top-Down EV Chassis Cutaway with Interactive Scanner Beam
================================================================================================ */
export function XrayStage() {
  const stageRef = useRef<HTMLDivElement>(null);
  const [scanPct, setScanPct] = useState(50);
  const [isTracking, setIsTracking] = useState(false);

  // Automated gentle sweep when user is not hovering over the stage
  useEffect(() => {
    if (isTracking) return;
    const prefersReduced =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) {
      setScanPct(52);
      return;
    }

    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const elapsed = (now - start) / 1000;
      // Smooth sine sweep between 18% and 82%
      const next = 50 + Math.sin(elapsed * 0.85) * 32;
      setScanPct(next);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [isTracking]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const el = stageRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const rel = ((e.clientX - rect.left) / rect.width) * 100;
    setScanPct(Math.max(10, Math.min(90, rel)));
  };

  // Convert percentage to SVG coordinates (viewBox 0..420)
  const beamX = (scanPct / 100) * 420;
  const apertureWidth = 152;
  const clipLeft = Math.max(0, beamX - apertureWidth / 2);

  // Active subsystem label based on scan beam position
  const activeZone =
    scanPct < 33 ? 'FRONT INDUCTION MOTOR' : scanPct > 67 ? 'REAR DUAL-DRIVE UNIT' : 'CTB STRUCTURAL PACK';

  // Generate 2x8 cell module matrix for Cell-to-Body battery pack
  const cellCols = [132, 152, 172, 192, 212, 232, 252, 272];

  return (
    <div
      ref={stageRef}
      className={styles.xrayWrap}
      onMouseEnter={() => setIsTracking(true)}
      onMouseLeave={() => setIsTracking(false)}
      onMouseMove={handleMouseMove}
    >
      <div className={styles.xrayTopBar}>
        <span className={styles.xrayReadout}>
          <span className={styles.xrayReadoutAccent}>SCAN {Math.round(scanPct).toString().padStart(2, '0')}%</span>
          <span>{'//'} {activeZone}</span>
        </span>
        <span className={styles.darkGlassBadge}>
          <span className={styles.liveDotCyan} aria-hidden />
          3D Cutaway · Interactive
        </span>
      </div>

      <div className={styles.xraySvgFrame}>
        <svg className={styles.xraySvg} viewBox="0 0 420 164" fill="none" aria-label="EV chassis X-ray cutaway diagram">
          <defs>
            <linearGradient id="vw-xray-body" x1="20" y1="82" x2="400" y2="82" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#1E293B" />
              <stop offset="48%" stopColor="#28354D" />
              <stop offset="100%" stopColor="#182234" />
            </linearGradient>
            <linearGradient id="vw-xray-glass" x1="120" y1="44" x2="310" y2="120" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.16" />
              <stop offset="50%" stopColor="#0F172A" stopOpacity="0.88" />
              <stop offset="100%" stopColor="#38BDF8" stopOpacity="0.12" />
            </linearGradient>
            <linearGradient id="vw-xray-pack" x1="125" y1="82" x2="295" y2="82" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#FF5500" />
              <stop offset="50%" stopColor="#FF8A33" />
              <stop offset="100%" stopColor="#22D3EE" />
            </linearGradient>
            <linearGradient id="vw-xray-beam" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#22D3EE" stopOpacity="0" />
              <stop offset="45%" stopColor="#22D3EE" stopOpacity="0.16" />
              <stop offset="50%" stopColor="#FF7A33" stopOpacity="0.45" />
              <stop offset="55%" stopColor="#22D3EE" stopOpacity="0.16" />
              <stop offset="100%" stopColor="#22D3EE" stopOpacity="0" />
            </linearGradient>
            <filter id="vw-xray-glow" x="-25%" y="-25%" width="150%" height="150%">
              <feGaussianBlur stdDeviation="3.2" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <clipPath id="vw-xray-aperture">
              <rect x={clipLeft} y="4" width={apertureWidth} height="156" rx="4" />
            </clipPath>
          </defs>

          {/* Subtle chassis centerline & axle guide marks */}
          <line x1="14" y1="82" x2="406" y2="82" stroke="rgba(148,163,184,0.16)" strokeDasharray="3 4" strokeWidth="1" />
          <line x1="94" y1="16" x2="94" y2="148" stroke="rgba(148,163,184,0.12)" strokeDasharray="2 3" strokeWidth="1" />
          <line x1="326" y1="16" x2="326" y2="148" stroke="rgba(148,163,184,0.12)" strokeDasharray="2 3" strokeWidth="1" />

          {/* LAYER 1: EXTERIOR FASTBACK EV BODY SHELL */}
          <g>
            {/* Outer tires (dimmed under body shell) */}
            <rect x="74" y="21" width="40" height="14" rx="5" fill="#0F172A" stroke="rgba(148,163,184,0.28)" strokeWidth="1" />
            <rect x="74" y="129" width="40" height="14" rx="5" fill="#0F172A" stroke="rgba(148,163,184,0.28)" strokeWidth="1" />
            <rect x="306" y="21" width="40" height="14" rx="5" fill="#0F172A" stroke="rgba(148,163,184,0.28)" strokeWidth="1" />
            <rect x="306" y="129" width="40" height="14" rx="5" fill="#0F172A" stroke="rgba(148,163,184,0.28)" strokeWidth="1" />

            {/* Side mirrors */}
            <path d="M138 30 L146 21 L156 23 L152 32 Z" fill="#1E293B" stroke="rgba(148,163,184,0.45)" strokeWidth="1" />
            <path d="M138 134 L146 143 L156 141 L152 132 Z" fill="#1E293B" stroke="rgba(148,163,184,0.45)" strokeWidth="1" />

            {/* Aerodynamic body silhouette */}
            <path
              d="M36 52 C42 36, 62 30, 96 30 L322 30 C356 30, 382 37, 390 54 C394 64, 395 100, 390 110 C382 127, 356 134, 322 134 L96 134 C62 134, 42 128, 36 112 C31 98, 31 66, 36 52 Z"
              fill="url(#vw-xray-body)"
              stroke="rgba(148,163,184,0.42)"
              strokeWidth="1.25"
            />

            {/* Sculpted hood creases */}
            <path d="M52 54 C76 48, 108 46, 134 49" stroke="rgba(226,232,240,0.22)" strokeWidth="1" />
            <path d="M52 110 C76 116, 108 118, 134 115" stroke="rgba(226,232,240,0.22)" strokeWidth="1" />

            {/* Panoramic glass cabin canopy */}
            <path
              d="M126 45 C154 41, 268 41, 312 48 C322 52, 325 66, 325 82 C325 98, 322 112, 312 116 C268 123, 154 123, 126 119 C116 110, 116 54, 126 45 Z"
              fill="url(#vw-xray-glass)"
              stroke="rgba(148,163,184,0.34)"
              strokeWidth="1"
            />
            {/* Windshield & rear glass header ribs */}
            <path d="M168 43 C162 66, 162 98, 168 121" stroke="rgba(148,163,184,0.25)" strokeWidth="1" />
            <path d="M274 44 C280 66, 280 98, 274 120" stroke="rgba(148,163,184,0.25)" strokeWidth="1" />

            {/* Front LED DRL & Rear full-width taillight bar */}
            <path d="M39 54 C42 46, 48 42, 57 40" stroke="#E0F2FE" strokeWidth="2" strokeLinecap="round" opacity="0.8" />
            <path d="M39 110 C42 118, 48 122, 57 124" stroke="#E0F2FE" strokeWidth="2" strokeLinecap="round" opacity="0.8" />
            <path d="M387 52 C390 66, 390 98, 387 112" stroke="#FF5500" strokeWidth="2.2" strokeLinecap="round" opacity="0.85" />
          </g>

          {/* LAYER 2: X-RAY INTERNAL POWERTRAIN (CLIPPED TO SCAN ZONE) */}
          <g clipPath="url(#vw-xray-aperture)">
            {/* Dark translucent cutaway backing inside scan window */}
            <path
              d="M36 52 C42 36, 62 30, 96 30 L322 30 C356 30, 382 37, 390 54 C394 64, 395 100, 390 110 C382 127, 356 134, 322 134 L96 134 C62 134, 42 128, 36 112 C31 98, 31 66, 36 52 Z"
              fill="#070C17"
              fillOpacity="0.93"
              stroke="#22D3EE"
              strokeWidth="1.2"
              strokeOpacity="0.72"
            />

            {/* Structural aluminum subframe rails */}
            <path
              d="M74 46 L124 42 L296 42 L346 46 M74 118 L124 122 L296 122 L346 118"
              stroke="#38BDF8"
              strokeOpacity="0.45"
              strokeWidth="1.4"
            />

            {/* Illuminated brake rotors & wheel hubs */}
            {[
              [94, 28],
              [94, 136],
              [326, 28],
              [326, 136],
            ].map(([cx, cy], idx) => (
              <g key={idx}>
                <rect x={cx - 18} y={cy - 6} width="36" height="12" rx="4" fill="#0F172A" stroke="#22D3EE" strokeWidth="1" strokeOpacity="0.7" />
                <rect x={cx - 5} y={cy - 4} width="10" height="8" rx="2" fill="#FF5500" opacity="0.9" />
              </g>
            ))}

            {/* FRONT INDUCTION MOTOR + AXLE HALF-SHAFTS */}
            <g filter="url(#vw-xray-glow)">
              <line x1="94" y1="35" x2="94" y2="129" stroke="#22D3EE" strokeWidth="2.4" strokeOpacity="0.85" />
              <rect x="77" y="61" width="34" height="42" rx="7" fill="#0C2438" stroke="#22D3EE" strokeWidth="1.5" />
              <rect x="83" y="68" width="22" height="28" rx="3" fill="#22D3EE" fillOpacity="0.28" stroke="#7DD3FC" strokeWidth="1" />
              <line x1="87" y1="73" x2="101" y2="73" stroke="#22D3EE" strokeWidth="1.2" />
              <line x1="87" y1="82" x2="101" y2="82" stroke="#FF7A33" strokeWidth="1.5" />
              <line x1="87" y1="91" x2="101" y2="91" stroke="#22D3EE" strokeWidth="1.2" />
            </g>

            {/* REAR DUAL INDUCTION MOTOR + SiC INVERTER */}
            <g filter="url(#vw-xray-glow)">
              <line x1="326" y1="35" x2="326" y2="129" stroke="#FF7A33" strokeWidth="2.6" strokeOpacity="0.9" />
              <rect x="307" y="55" width="38" height="54" rx="8" fill="#24130D" stroke="#FF6B2B" strokeWidth="1.6" />
              <rect x="313" y="61" width="26" height="17" rx="3" fill="#FF5500" fillOpacity="0.34" stroke="#FF8A33" strokeWidth="1" />
              <rect x="313" y="86" width="26" height="17" rx="3" fill="#FF5500" fillOpacity="0.34" stroke="#FF8A33" strokeWidth="1" />
              <circle cx="326" cy="82" r="3.5" fill="#22D3EE" />
            </g>

            {/* HIGH-VOLTAGE ORANGE HARNESS BUSBARS */}
            <path d="M111 76 H125 M111 88 H125 M295 74 H307 M295 90 H307" stroke="#FF5500" strokeWidth="2.4" strokeLinecap="round" />

            {/* STRUCTURAL CELL-TO-BODY (CTB) BATTERY PACK */}
            <rect
              x="125"
              y="45"
              width="170"
              height="74"
              rx="8"
              fill="#0E1729"
              stroke="url(#vw-xray-pack)"
              strokeWidth="1.6"
            />
            {/* Central spine busbar */}
            <line x1="130" y1="82" x2="290" y2="82" stroke="#22D3EE" strokeWidth="1.5" strokeOpacity="0.85" />
            {/* Individual glowing battery cell modules (2 banks x 8 modules) */}
            {cellCols.map((x, idx) => (
              <g key={x}>
                <rect
                  x={x}
                  y="51"
                  width="14"
                  height="26"
                  rx="2.5"
                  fill={idx % 3 === 0 ? 'rgba(34, 211, 238, 0.34)' : 'rgba(255, 85, 0, 0.42)'}
                  stroke={idx % 3 === 0 ? '#22D3EE' : '#FF7A33'}
                  strokeWidth="1"
                />
                <rect
                  x={x}
                  y="87"
                  width="14"
                  height="26"
                  rx="2.5"
                  fill={idx % 3 === 1 ? 'rgba(34, 211, 238, 0.34)' : 'rgba(255, 85, 0, 0.42)'}
                  stroke={idx % 3 === 1 ? '#22D3EE' : '#FF7A33'}
                  strokeWidth="1"
                />
              </g>
            ))}
          </g>

          {/* SCANNER BEAM APERTURE & LASER LINE */}
          <g>
            <rect x={beamX - 28} y="6" width="56" height="152" fill="url(#vw-xray-beam)" />
            <line x1={beamX} y1="6" x2={beamX} y2="158" stroke="#22D3EE" strokeWidth="1.6" filter="url(#vw-xray-glow)" />
            {/* Scanner top/bottom reticle chevrons */}
            <polygon points={`${beamX - 5},4 ${beamX + 5},4 ${beamX},10`} fill="#22D3EE" />
            <polygon points={`${beamX - 5},160 ${beamX + 5},160 ${beamX},154`} fill="#FF6B2B" />
          </g>
        </svg>
      </div>

      <div className={styles.xrayFootRow}>
        <span>
          <strong className={styles.xrayChipOrange}>CTB</strong> · 800V Cell-to-Body
        </span>
        <span>
          <strong className={styles.xrayChipCyan}>DUAL</strong> · Front + Rear Induction
        </span>
      </div>
    </div>
  );
}

/* ================================================================================================
   02 / DRIVE — Live Telemetry HUD Graph, G-Force Reticle & Mode Pills
================================================================================================ */
type DriveMode = 'launch' | 'curve' | 'stop';

interface DrivePreset {
  id: DriveMode;
  label: string;
  speedRange: string;
  metricBadge: string;
  gForce: string;
  gX: number; // reticle cx (center 40)
  gY: number; // reticle cy (center 40)
  curvePoints: [number, number][]; // 6 normalized control coordinates (x: 4..176, y: 10..72)
  accent: string;
}

const DRIVE_PRESETS: Record<DriveMode, DrivePreset> = {
  launch: {
    id: 'launch',
    label: 'Launch',
    speedRange: '0 → 100',
    metricBadge: '2.78 s',
    gForce: '1.28 G',
    gX: 40,
    gY: 64,
    curvePoints: [
      [4, 70],
      [34, 62],
      [68, 36],
      [104, 19],
      [140, 12],
      [176, 10],
    ],
    accent: '#FF5500',
  },
  curve: {
    id: 'curve',
    label: 'Curve',
    speedRange: '86 APEX',
    metricBadge: '1.12 G LAT',
    gForce: '1.12 G',
    gX: 62,
    gY: 42,
    curvePoints: [
      [4, 42],
      [36, 16],
      [72, 20],
      [108, 60],
      [144, 54],
      [176, 26],
    ],
    accent: '#0EA5E9',
  },
  stop: {
    id: 'stop',
    label: 'Stop',
    speedRange: '100 → 0',
    metricBadge: '33.2 m',
    gForce: '1.18 G',
    gX: 40,
    gY: 16,
    curvePoints: [
      [4, 12],
      [36, 17],
      [72, 31],
      [108, 49],
      [142, 63],
      [176, 70],
    ],
    accent: '#E11D48',
  },
};

function pointsToSmoothPath(pts: [number, number][]): string {
  if (pts.length < 2) return '';
  let d = `M ${pts[0][0].toFixed(1)} ${pts[0][1].toFixed(1)}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[Math.min(pts.length - 1, i + 2)];
    const cp1x = p1[0] + (p2[0] - p0[0]) / 6;
    const cp1y = p1[1] + (p2[1] - p0[1]) / 6;
    const cp2x = p2[0] - (p3[0] - p1[0]) / 6;
    const cp2y = p2[1] - (p3[1] - p1[1]) / 6;
    d += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;
  }
  return d;
}

export function DriveStage() {
  const [mode, setMode] = useState<DriveMode>('launch');
  const [interpPts, setInterpPts] = useState<[number, number][]>(DRIVE_PRESETS.launch.curvePoints);
  const currentPtsRef = useRef<[number, number][]>(DRIVE_PRESETS.launch.curvePoints);

  const preset = DRIVE_PRESETS[mode];

  // Smooth cross-browser SVG Bezier point interpolation when switching modes
  useEffect(() => {
    const from = currentPtsRef.current.map(([x, y]) => [x, y] as [number, number]);
    const to = DRIVE_PRESETS[mode].curvePoints;
    const duration = 360;
    const start = performance.now();
    let raf = 0;

    const animate = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const ease = 1 - Math.pow(1 - t, 3);
      const next = from.map(([fx, fy], idx) => [
        fx + (to[idx][0] - fx) * ease,
        fy + (to[idx][1] - fy) * ease,
      ]) as [number, number][];
      currentPtsRef.current = next;
      setInterpPts(next);
      if (t < 1) {
        raf = requestAnimationFrame(animate);
      }
    };

    raf = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf);
  }, [mode]);

  const linePath = pointsToSmoothPath(interpPts);
  const areaPath = `${linePath} L 176 76 L 4 76 Z`;
  const peakPt = interpPts[3];

  return (
    <div className={styles.driveWrap}>
      <div className={styles.driveTopBar}>
        <div className={styles.modePills} role="tablist" aria-label="Driving telemetry modes">
          {(['launch', 'curve', 'stop'] as DriveMode[]).map((m) => (
            <button
              key={m}
              type="button"
              role="tab"
              aria-selected={mode === m}
              className={`${styles.modePill} ${mode === m ? styles.modePillActive : ''}`}
              onClick={() => setMode(m)}
              onMouseEnter={() => setMode(m)}
            >
              {DRIVE_PRESETS[m].label}
            </button>
          ))}
        </div>

        <div className={styles.driveSpeedBlock} aria-live="polite">
          <span className={styles.driveSpeedVal}>{preset.speedRange}</span>
          <span className={styles.driveSpeedUnit}>km/h</span>
        </div>
      </div>

      <div className={styles.driveBody}>
        {/* Telemetry Curve HUD */}
        <div className={styles.driveChartCard}>
          <div className={styles.driveChartHead}>
            <span>TELEMETRY</span>
            <span className={styles.driveChartBadge} style={{ color: preset.accent }}>
              {preset.metricBadge}
            </span>
          </div>
          <svg className={styles.driveChartSvg} viewBox="0 0 180 78" fill="none" aria-hidden>
            <defs>
              <linearGradient id="vw-drive-fill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={preset.accent} stopOpacity="0.28" />
                <stop offset="100%" stopColor={preset.accent} stopOpacity="0.01" />
              </linearGradient>
            </defs>
            {/* Reference guide lines */}
            <line x1="4" y1="18" x2="176" y2="18" stroke="rgba(15,23,42,0.06)" strokeDasharray="2 3" />
            <line x1="4" y1="44" x2="176" y2="44" stroke="rgba(15,23,42,0.06)" strokeDasharray="2 3" />
            <line x1="4" y1="70" x2="176" y2="70" stroke="rgba(15,23,42,0.09)" />

            <path d={areaPath} fill="url(#vw-drive-fill)" />
            <path d={linePath} stroke={preset.accent} strokeWidth="2.3" strokeLinecap="round" fill="none" />

            {/* Highlighted telemetry point */}
            <line x1={peakPt[0]} y1={peakPt[1]} x2={peakPt[0]} y2="74" stroke={preset.accent} strokeWidth="1" strokeDasharray="2 2" opacity="0.5" />
            <circle cx={peakPt[0]} cy={peakPt[1]} r="6" fill={preset.accent} fillOpacity="0.2" />
            <circle cx={peakPt[0]} cy={peakPt[1]} r="3" fill={preset.accent} stroke="#ffffff" strokeWidth="1.5" />
          </svg>
        </div>

        {/* Circular G-Force Reticle */}
        <div className={styles.gReticleCard}>
          <svg className={styles.gReticleSvg} viewBox="0 0 80 80" fill="none" aria-label={`G-force reticle at ${preset.gForce}`}>
            <circle cx="40" cy="40" r="33" stroke="rgba(148,163,184,0.22)" strokeWidth="1" />
            <circle cx="40" cy="40" r="22" stroke="rgba(148,163,184,0.18)" strokeWidth="1" strokeDasharray="2 2" />
            <circle cx="40" cy="40" r="11" stroke="rgba(148,163,184,0.15)" strokeWidth="1" />
            <line x1="7" y1="40" x2="73" y2="40" stroke="rgba(148,163,184,0.18)" strokeWidth="1" />
            <line x1="40" y1="7" x2="40" y2="73" stroke="rgba(148,163,184,0.18)" strokeWidth="1" />
            {/* G vector line */}
            <line x1="40" y1="40" x2={preset.gX} y2={preset.gY} stroke={preset.accent} strokeWidth="1.75" strokeOpacity="0.7" />
            <circle className={styles.gReticleDot} cx={preset.gX} cy={preset.gY} r="7.5" fill={preset.accent} fillOpacity="0.25" />
            <circle className={styles.gReticleDot} cx={preset.gX} cy={preset.gY} r="3.6" fill={preset.accent} stroke="#ffffff" strokeWidth="1.2" />
          </svg>
          <span className={styles.gReticleVal} style={{ color: preset.accent }}>
            {preset.gForce}
          </span>
        </div>
      </div>
    </div>
  );
}

/* ================================================================================================
   03 / COLOUR — 5 Metallic Paint Spheres + Sculpted Fender Contour + 5500K Daylight
================================================================================================ */
export interface PaintSwatch {
  id: string;
  name: string;
  base: string;
  light: string;
  deep: string;
  glow: string;
}

export const PAINT_SWATCHES: PaintSwatch[] = [
  {
    id: 'sunburst-yellow',
    name: 'Sunburst Yellow',
    base: '#EAB308',
    light: '#FEF08A',
    deep: '#854D0E',
    glow: 'rgba(234, 179, 8, 0.16)',
  },
  {
    id: 'celadon-green',
    name: 'Celadon Green',
    base: '#4BA896',
    light: '#CCFBF1',
    deep: '#134E4A',
    glow: 'rgba(75, 168, 150, 0.17)',
  },
  {
    id: 'cinnabar-red',
    name: 'Cinnabar Red',
    base: '#C92A32',
    light: '#FDA4AF',
    deep: '#630D14',
    glow: 'rgba(201, 42, 50, 0.15)',
  },
  {
    id: 'titanium-grey',
    name: 'Titanium Grey',
    base: '#6B778C',
    light: '#E2E8F0',
    deep: '#1E293B',
    glow: 'rgba(100, 116, 139, 0.16)',
  },
  {
    id: 'midnight-blue',
    name: 'Midnight Blue',
    base: '#1E4080',
    light: '#93C5FD',
    deep: '#0A1733',
    glow: 'rgba(30, 64, 128, 0.17)',
  },
];

export function ColourStage({
  activePaint,
  onSelectPaint,
}: {
  activePaint: PaintSwatch;
  onSelectPaint: (paint: PaintSwatch) => void;
}) {
  return (
    <div className={styles.colourWrap}>
      <div className={styles.colourTopBar}>
        <span className={styles.daylightBadge}>
          <span className={styles.daylightSun} aria-hidden />
          5500K Daylight
        </span>
        <span className={styles.colourNameTag}>{activePaint.name}</span>
      </div>

      {/* Curved Sculpted Car Fender & Hood Silhouette Contour */}
      <div className={styles.fenderStage}>
        <svg className={styles.fenderSvg} viewBox="0 0 240 94" fill="none" aria-label={`Exterior finish preview in ${activePaint.name}`}>
          <defs>
            <linearGradient id="vw-paint-body" x1="20" y1="14" x2="215" y2="86" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor={activePaint.light} />
              <stop offset="34%" stopColor={activePaint.base} />
              <stop offset="78%" stopColor={activePaint.deep} />
              <stop offset="100%" stopColor={activePaint.base} />
            </linearGradient>
            <linearGradient id="vw-paint-sheen" x1="30" y1="18" x2="210" y2="52" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.85" />
              <stop offset="50%" stopColor="#FFFFFF" stopOpacity="0.22" />
              <stop offset="100%" stopColor="#FFFFFF" stopOpacity="0" />
            </linearGradient>
          </defs>

          {/* Soft daylight floor reflection ellipse */}
          <ellipse cx="122" cy="84" rx="94" ry="6" fill="rgba(15, 23, 42, 0.1)" />

          {/* Sculpted fastback fender / hood / shoulder panel */}
          <path
            d="M14 68 C22 44, 52 28, 102 22 C142 17, 178 14, 224 22 C228 36, 226 58, 218 70 L182 70 C177 51, 158 41, 138 44 C118 47, 104 59, 101 74 L24 74 C18 74, 13 72, 14 68 Z"
            fill="url(#vw-paint-body)"
            stroke="rgba(15,23,42,0.16)"
            strokeWidth="1"
            style={{ transition: 'fill 0.35s ease' }}
          />

          {/* Clearcoat studio specular ridge */}
          <path
            d="M28 56 C52 38, 96 28, 154 23 C182 21, 204 22, 218 26"
            stroke="url(#vw-paint-sheen)"
            strokeWidth="3.2"
            strokeLinecap="round"
          />

          {/* Lower character crease */}
          <path
            d="M34 65 C62 59, 86 52, 114 42 C146 31, 184 29, 216 33"
            stroke="rgba(255,255,255,0.34)"
            strokeWidth="1.2"
            strokeLinecap="round"
          />

          {/* Flush headlamp blade detail */}
          <path d="M22 60 C34 55, 48 53, 58 55" stroke="#FFFFFF" strokeWidth="2.4" strokeLinecap="round" opacity="0.92" />

          {/* Wheel arch rim hint */}
          <path d="M107 74 C111 56, 126 46, 144 46 C162 46, 174 56, 177 70" stroke="rgba(15,23,42,0.45)" strokeWidth="2" fill="none" />
          <circle cx="142" cy="72" r="14" fill="#0F172A" fillOpacity="0.86" stroke="rgba(148,163,184,0.4)" strokeWidth="1.5" />
          <circle cx="142" cy="72" r="5" fill="#94A3B8" fillOpacity="0.6" />
        </svg>
      </div>

      {/* 5 Realistic Metallic Paint Spheres */}
      <div className={styles.paintPalette} role="group" aria-label="Select exterior paint colour">
        {PAINT_SWATCHES.map((swatch) => {
          const isActive = swatch.id === activePaint.id;
          return (
            <button
              key={swatch.id}
              type="button"
              className={styles.paintSphereBtn}
              aria-label={swatch.name}
              aria-pressed={isActive}
              title={swatch.name}
              onClick={() => onSelectPaint(swatch)}
              onMouseEnter={() => onSelectPaint(swatch)}
            >
              <span
                className={`${styles.paintSphere} ${isActive ? styles.paintSphereActive : ''}`}
                style={{
                  background: `radial-gradient(circle at 32% 28%, ${swatch.light} 0%, ${swatch.base} 46%, ${swatch.deep} 100%)`,
                }}
              />
            </button>
          );
        })}
      </div>
    </div>
  );
}

/* ================================================================================================
   04 / DASHBOARD — Miniature Pillar-to-Pillar EV Glass Cockpit UI
================================================================================================ */
export function DashboardStage() {
  const [cabinTemp, setCabinTemp] = useState(21.5);

  const cycleTemp = () => {
    setCabinTemp((prev) => (prev >= 23 ? 19.5 : Number((prev + 0.5).toFixed(1))));
  };

  return (
    <div className={styles.cockpitWrap}>
      <div className={styles.cockpitTopLabel}>
        <span>PILLAR-TO-PILLAR HMI</span>
        <span className={styles.cockpitStatus}>NOA · ACTIVE</span>
      </div>

      <div className={styles.cockpitBezel}>
        <div className={styles.cockpitScreen}>
          {/* Left Pane: 3D ADAS Lane-Keep Visualization */}
          <div className={styles.cockpitPane}>
            <svg className={styles.adasSvg} viewBox="0 0 92 74" fill="none" aria-label="ADAS lane-keep visualization">
              <defs>
                <linearGradient id="vw-adas-lane" x1="46" y1="6" x2="46" y2="70" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" stopColor="#22D3EE" stopOpacity="0.06" />
                  <stop offset="100%" stopColor="#22D3EE" stopOpacity="0.28" />
                </linearGradient>
              </defs>
              {/* Perspective highway lane polygon */}
              <polygon points="36,8 56,8 82,70 10,70" fill="url(#vw-adas-lane)" />
              {/* Lane keep rails */}
              <line x1="36" y1="8" x2="10" y2="70" stroke="#22D3EE" strokeWidth="1.6" strokeOpacity="0.85" />
              <line x1="56" y1="8" x2="82" y2="70" stroke="#22D3EE" strokeWidth="1.6" strokeOpacity="0.85" />
              {/* Animated center lane markings */}
              <line className={styles.adasLaneDash} x1="46" y1="10" x2="46" y2="68" stroke="#E0F2FE" strokeWidth="1.3" strokeOpacity="0.65" />
              {/* Lead car bounding ghost */}
              <rect x="40" y="18" width="12" height="7" rx="2" fill="#38BDF8" fillOpacity="0.28" stroke="#38BDF8" strokeWidth="0.9" />
              {/* Ego EV rear silhouette */}
              <path d="M35 55 C36 48, 56 48, 57 55 L59 63 L33 63 Z" fill="#E2E8F0" />
              <line x1="36" y1="58" x2="56" y2="58" stroke="#FF5500" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <div className={styles.cockpitMiniSpeed}>
              <strong>108</strong>
              <span>km/h</span>
            </div>
          </div>

          {/* Center Pane: Vector Navigation Spline */}
          <div className={styles.cockpitPane}>
            <svg className={styles.navSvg} viewBox="0 0 104 74" fill="none" aria-label="Navigation map spline">
              {/* Subtle city grid */}
              <path d="M8 22 H96 M8 48 H96 M32 6 V68 M68 6 V68" stroke="rgba(148,163,184,0.12)" strokeWidth="1" />
              {/* Route spline glow */}
              <path d="M22 66 C26 44, 44 46, 54 32 C62 20, 74 20, 86 12" stroke="#FF5500" strokeWidth="4.5" strokeOpacity="0.22" strokeLinecap="round" fill="none" />
              <path d="M22 66 C26 44, 44 46, 54 32 C62 20, 74 20, 86 12" stroke="#FF6B2B" strokeWidth="2" strokeLinecap="round" fill="none" />
              {/* Turn pin & ego nav chevron */}
              <circle cx="86" cy="12" r="3.5" fill="#22D3EE" />
              <polygon points="54,26 59,36 54,33.5 49,36" fill="#FFFFFF" />
            </svg>
            <div className={styles.navEta}>
              <span className={styles.navEtaDot}>14 min</span>
              <span>12.4 km</span>
            </div>
          </div>

          {/* Right Pane: Media & HVAC Pills */}
          <div className={styles.cockpitWidgets}>
            <button
              type="button"
              className={styles.hvacPill}
              onClick={cycleTemp}
              aria-label={`Cabin climate ${cabinTemp} degrees Celsius, click to adjust`}
              style={{ cursor: 'pointer', textAlign: 'left' }}
            >
              <div className={styles.hvacTop}>
                <span>HVAC</span>
                <span style={{ color: '#38BDF8' }}>AUTO</span>
              </div>
              <span className={styles.hvacVal}>{cabinTemp.toFixed(1)}°C</span>
            </button>

            <div className={styles.hvacPill}>
              <div className={styles.hvacTop}>
                <span>MEDIA</span>
                <span style={{ color: '#FF7A33' }}>HI-RES</span>
              </div>
              <div className={styles.mediaBars} aria-hidden>
                <span className={styles.mediaBar} style={{ height: '7px', animationDelay: '0ms' }} />
                <span className={styles.mediaBar} style={{ height: '13px', animationDelay: '140ms' }} />
                <span className={styles.mediaBar} style={{ height: '9px', animationDelay: '280ms' }} />
                <span className={styles.mediaBar} style={{ height: '14px', animationDelay: '90ms' }} />
                <span className={styles.mediaBar} style={{ height: '6px', animationDelay: '210ms' }} />
                <span className={styles.mediaBar} style={{ height: '11px', animationDelay: '330ms' }} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ================================================================================================
   05 / CHARGING — 800V High-Power Charging Curve + Animated Power-Flow Busbar
================================================================================================ */
export function ChargingStage({ hovered }: { hovered: boolean }) {
  const [soc, setSoc] = useState(10);

  useEffect(() => {
    const target = hovered ? 80 : 10;
    const startVal = soc;
    if (startVal === target) return;

    const duration = hovered ? 1100 : 480;
    const start = performance.now();
    let raf = 0;

    const step = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const ease = 1 - Math.pow(1 - t, 3);
      setSoc(Math.round(startVal + (target - startVal) * ease));
      if (t < 1) raf = requestAnimationFrame(step);
    };

    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hovered]);

  // Compute dot position along charging power curve from 10% -> 80%
  const progress = (soc - 10) / 70; // 0..1
  const dotX = 16 + progress * 196;
  // Flat peak plateau until ~55% SoC, then gentle taper
  const dotY = progress < 0.55 ? 11 + progress * 4 : 13.2 + (progress - 0.55) * 44;

  return (
    <div className={styles.chargeWrap}>
      <div className={styles.chargeHeader}>
        <span className={styles.chargeArchTag}>800V SiC · 10% → 80%</span>
        <span className={styles.chargePeakBadge}>520 kW Peak</span>
      </div>

      {/* Charging Power Curve */}
      <div className={styles.chargeCurveBox}>
        <svg className={styles.chargeCurveSvg} viewBox="0 0 240 54" fill="none" aria-label="800V charging power curve">
          <defs>
            <linearGradient id="vw-charge-area" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#FF5500" stopOpacity="0.28" />
              <stop offset="100%" stopColor="#FF5500" stopOpacity="0.02" />
            </linearGradient>
          </defs>
          <line x1="8" y1="12" x2="232" y2="12" stroke="rgba(15,23,42,0.07)" strokeDasharray="2 3" />
          <line x1="8" y1="48" x2="232" y2="48" stroke="rgba(15,23,42,0.1)" />

          <path
            d="M12 48 L16 14 C24 10, 108 10, 134 15 C166 21, 198 31, 228 42 L228 48 Z"
            fill="url(#vw-charge-area)"
          />
          <path
            d="M12 48 L16 14 C24 10, 108 10, 134 15 C166 21, 198 31, 228 42"
            stroke="#FF5500"
            strokeWidth="2.1"
            strokeLinecap="round"
            fill="none"
          />

          {/* Live active point along curve */}
          <line x1={dotX} y1={dotY} x2={dotX} y2="48" stroke="#FF5500" strokeWidth="1" strokeDasharray="2 2" opacity="0.55" />
          <circle cx={dotX} cy={dotY} r="5.5" fill="#FF5500" fillOpacity="0.22" />
          <circle cx={dotX} cy={dotY} r="2.8" fill="#FF5500" stroke="#FFFFFF" strokeWidth="1.3" />
        </svg>
      </div>

      {/* Animated Power-Flow Busbar from Charger to Battery Pack */}
      <div className={styles.busbarRow}>
        <div className={styles.chargerNode}>
          <span>DC</span>
          <span className={styles.chargerNodeSub}>800V</span>
        </div>

        <div className={styles.busbarTrack} aria-hidden>
          <div className={styles.busbarRail}>
            <div className={styles.busbarGlow} />
          </div>
          <span className={styles.particle} />
          <span className={`${styles.particle} ${styles.particle2}`} />
          <span className={`${styles.particle} ${styles.particle3}`} />
        </div>

        <div className={styles.packWidget}>
          <div className={styles.packTop}>
            <span>SoC</span>
            <span className={styles.packRange}>{soc}%</span>
          </div>
          <div className={styles.packBarOuter}>
            <div className={styles.packBarFill} style={{ width: `${Math.max(12, soc)}%` }} />
            <div className={styles.packTicks} aria-hidden>
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ================================================================================================
   06 / SPECIFICATIONS — Clickable CLTC vs WLTP Comparison HUD
================================================================================================ */
type TestCycle = 'CLTC' | 'WLTP';

const CYCLE_DATA: Record<
  TestCycle,
  {
    rangeKm: number;
    barPct: number;
    consumption: string;
    standard: string;
  }
> = {
  CLTC: {
    rangeKm: 800,
    barPct: 80,
    consumption: '12.3 kWh/100km',
    standard: 'MIIT GB/T 38146',
  },
  WLTP: {
    rangeKm: 665,
    barPct: 66.5,
    consumption: '14.8 kWh/100km',
    standard: 'UNECE GTR No. 15',
  },
};

export function SpecificationsStage() {
  const [cycle, setCycle] = useState<TestCycle>('CLTC');
  const data = CYCLE_DATA[cycle];
  const isWltp = cycle === 'WLTP';

  return (
    <div className={styles.specWrap}>
      <div className={styles.specTopRow}>
        <div className={styles.cycleToggle} role="tablist" aria-label="Select range test cycle">
          <span className={`${styles.cycleThumb} ${isWltp ? styles.cycleThumbWltp : ''}`} aria-hidden />
          <button
            type="button"
            role="tab"
            aria-selected={cycle === 'CLTC'}
            className={`${styles.cycleBtn} ${cycle === 'CLTC' ? styles.cycleBtnActive : ''}`}
            onClick={() => setCycle('CLTC')}
            onMouseEnter={() => setCycle('CLTC')}
          >
            CLTC
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={cycle === 'WLTP'}
            className={`${styles.cycleBtn} ${cycle === 'WLTP' ? styles.cycleBtnActive : ''}`}
            onClick={() => setCycle('WLTP')}
            onMouseEnter={() => setCycle('WLTP')}
          >
            WLTP
          </button>
        </div>

        <span className={styles.cycleLockBadge}>NEVER MIXED</span>
      </div>

      <div className={styles.specPanel} aria-live="polite">
        <div className={styles.specBigRow}>
          <div>
            <span className={styles.specRangeVal}>{data.rangeKm}</span>
            <span className={styles.specRangeUnit}>km</span>
          </div>
          <span className={`${styles.specCyclePill} ${isWltp ? styles.specCyclePillWltp : ''}`}>
            {cycle} CYCLE
          </span>
        </div>

        <div>
          <div className={styles.specBarTrack}>
            <div
              className={`${styles.specBarFill} ${isWltp ? styles.specBarFillWltp : ''}`}
              style={{ width: `${data.barPct}%` }}
            />
          </div>
          <div className={styles.specRuler}>
            <span>0</span>
            <span>250</span>
            <span>500</span>
            <span>750</span>
            <span>1000 km</span>
          </div>
        </div>

        <div className={styles.specFootStats}>
          <span>{data.consumption}</span>
          <span>{data.standard}</span>
        </div>
      </div>
    </div>
  );
}

/* ================================================================================================
   07 / INTERIOR — 360° Spatial Cabin Gyroscope & Viewpoint Nodes
================================================================================================ */
type CabinView = 'driver' | 'rear' | 'canopy';

const CABIN_VIEWS: Record<CabinView, { label: string; angle: number; readout: string }> = {
  driver: { label: 'Driver', angle: -38, readout: 'POV 322° · COCKPIT' },
  rear: { label: 'Rear Cabin', angle: 145, readout: 'POV 145° · LOUNGE' },
  canopy: { label: 'Canopy', angle: -90, readout: 'POV 270° · GLASS ROOF' },
};

export function InteriorStage() {
  const [view, setView] = useState<CabinView>('driver');
  const active = CABIN_VIEWS[view];

  return (
    <div className={styles.gyroWrap}>
      <div className={styles.gyroHeader}>
        <span>360° SPATIAL GYRO</span>
        <span className={styles.gyroAngle}>{active.readout}</span>
      </div>

      <div className={styles.gyroStage}>
        <svg className={styles.gyroSvg} viewBox="0 0 240 132" fill="none" aria-label="360-degree cabin gyroscope diagram">
          <defs>
            <linearGradient id="vw-fov-cone" x1="120" y1="66" x2="120" y2="10" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#FF5500" stopOpacity="0.48" />
              <stop offset="100%" stopColor="#FF5500" stopOpacity="0.02" />
            </linearGradient>
          </defs>

          {/* Outer 3D Orbital Gyroscope Rings */}
          <g className={styles.gyroRingOuter}>
            <ellipse cx="120" cy="66" rx="92" ry="38" stroke="rgba(15,23,42,0.16)" strokeWidth="1.2" strokeDasharray="3 3" />
            <ellipse cx="120" cy="66" rx="82" ry="52" transform="rotate(-14 120 66)" stroke="rgba(15,23,42,0.12)" strokeWidth="1" />
            {/* Azimuth degree ticks */}
            <circle cx="28" cy="66" r="2.2" fill="#94A3B8" />
            <circle cx="212" cy="66" r="2.2" fill="#94A3B8" />
          </g>

          <g className={styles.gyroRingInner}>
            <ellipse cx="120" cy="66" rx="58" ry="54" transform="rotate(24 120 66)" stroke="rgba(255,85,0,0.34)" strokeWidth="1.25" />
          </g>

          {/* Active Camera Field-of-View Cone */}
          <g className={styles.gyroFovCone} style={{ transform: `rotate(${active.angle}deg)` }}>
            <path d="M120 66 L94 16 A56 56 0 0 1 146 16 Z" fill="url(#vw-fov-cone)" />
            <line x1="120" y1="66" x2="94" y2="16" stroke="#FF5500" strokeWidth="1.1" strokeOpacity="0.6" />
            <line x1="120" y1="66" x2="146" y2="16" stroke="#FF5500" strokeWidth="1.1" strokeOpacity="0.6" />
          </g>

          {/* Minimalist Cabin Wireframe Perspective in Center */}
          <g>
            {/* Cabin shell outline */}
            <path
              d="M84 54 C92 38, 148 38, 156 54 L162 82 C162 90, 152 94, 120 94 C88 94, 78 90, 78 82 Z"
              fill="rgba(255,255,255,0.88)"
              stroke="#0F172A"
              strokeWidth="1.4"
            />
            {/* Dashboard arc & steering yoke */}
            <path d="M90 56 C106 49, 134 49, 150 56" stroke="#475569" strokeWidth="1.3" />
            <circle cx="104" cy="59" r="5" stroke="#0F172A" strokeWidth="1.4" fill="none" />
            {/* Front seats */}
            <rect x="96" y="66" width="16" height="16" rx="4" stroke="#64748B" strokeWidth="1.2" fill="rgba(241,245,249,0.9)" />
            <rect x="128" y="66" width="16" height="16" rx="4" stroke="#64748B" strokeWidth="1.2" fill="rgba(241,245,249,0.9)" />
            {/* Center 360 camera anchor */}
            <circle cx="120" cy="66" r="4" fill="#FF5500" stroke="#FFFFFF" strokeWidth="1.5" />
          </g>
        </svg>
      </div>

      {/* 3 Interactive Viewpoint Nodes */}
      <div className={styles.viewNodes} role="tablist" aria-label="Cabin camera viewpoints">
        {(['driver', 'rear', 'canopy'] as CabinView[]).map((id) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={view === id}
            className={`${styles.viewNodeBtn} ${view === id ? styles.viewNodeActive : ''}`}
            onClick={() => setView(id)}
            onMouseEnter={() => setView(id)}
          >
            <span className={styles.viewNodeDot} aria-hidden />
            {CABIN_VIEWS[id].label}
          </button>
        ))}
      </div>
    </div>
  );
}

/* ================================================================================================
   08 / WHEELS — Multi-Spoke Forged Aero Rim + Perforated Disc + Fixed 10-o'clock Orange Caliper
================================================================================================ */
type WheelDesign = '20-aero' | '21-forged';

export function WheelsStage() {
  const [design, setDesign] = useState<WheelDesign>('21-forged');

  // Deterministic cross-drilled rotor holes (12 angles x 2 rings)
  const drillAngles = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330];
  // 5-spoke split Y or 5 directional aero blades
  const spokeAngles = [0, 72, 144, 216, 288];

  return (
    <div className={styles.wheelWrap}>
      <div className={styles.wheelHeader}>
        <div className={styles.wheelTags} role="tablist" aria-label="Wheel design options">
          <button
            type="button"
            role="tab"
            aria-selected={design === '20-aero'}
            className={`${styles.wheelTagBtn} ${design === '20-aero' ? styles.wheelTagActive : ''}`}
            onClick={() => setDesign('20-aero')}
            onMouseEnter={() => setDesign('20-aero')}
          >
            20&quot; Aero
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={design === '21-forged'}
            className={`${styles.wheelTagBtn} ${design === '21-forged' ? styles.wheelTagActive : ''}`}
            onClick={() => setDesign('21-forged')}
            onMouseEnter={() => setDesign('21-forged')}
          >
            21&quot; Forged
          </button>
        </div>
        <span className={styles.caliperTag}>6-PISTON</span>
      </div>

      <div className={styles.wheelStage}>
        <svg className={styles.wheelSvg} viewBox="0 0 160 160" fill="none" aria-label="Forged aero wheel with electric-orange brake caliper">
          <defs>
            <radialGradient id="vw-tire" cx="50%" cy="50%" r="50%">
              <stop offset="76%" stopColor="#1E293B" />
              <stop offset="88%" stopColor="#0F172A" />
              <stop offset="100%" stopColor="#070B14" />
            </radialGradient>
            <linearGradient id="vw-rotor-metal" x1="30" y1="30" x2="130" y2="130" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#CBD5E1" />
              <stop offset="50%" stopColor="#94A3B8" />
              <stop offset="100%" stopColor="#64748B" />
            </linearGradient>
            <linearGradient id="vw-spoke-finish" x1="20" y1="20" x2="140" y2="140" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#F8FAFC" />
              <stop offset="45%" stopColor="#94A3B8" />
              <stop offset="100%" stopColor="#334155" />
            </linearGradient>
          </defs>

          {/* Outer Tire Sidewall & Rim Barrel */}
          <circle cx="80" cy="80" r="72" fill="url(#vw-tire)" />
          <circle cx="80" cy="80" r="61" fill="#0B1120" stroke="#475569" strokeWidth="2.4" />

          {/* Perforated Ventilated Brake Disc (behind caliper & spokes) */}
          <circle cx="80" cy="80" r="46" fill="url(#vw-rotor-metal)" fillOpacity="0.34" stroke="#94A3B8" strokeWidth="1.4" />
          <circle cx="80" cy="80" r="36" stroke="rgba(148,163,184,0.38)" strokeWidth="0.9" strokeDasharray="4 3" />
          {drillAngles.map((deg) => {
            const rad = (deg * Math.PI) / 180;
            const x1 = Number((80 + Math.cos(rad) * 33).toFixed(2));
            const y1 = Number((80 + Math.sin(rad) * 33).toFixed(2));
            const x2 = Number((80 + Math.cos(rad + 0.14) * 40).toFixed(2));
            const y2 = Number((80 + Math.sin(rad + 0.14) * 40).toFixed(2));
            return (
              <g key={deg}>
                <circle cx={x1} cy={y1} r="1.2" fill="#0F172A" opacity="0.65" />
                <circle cx={x2} cy={y2} r="1.2" fill="#0F172A" opacity="0.65" />
              </g>
            );
          })}

          {/* FIXED ELECTRIC-ORANGE MULTI-PISTON BRAKE CALIPER AT 10-O'CLOCK POSITION */}
          <g>
            {/* Caliper body curving around the 9:30 -> 11:00 arc (10 o'clock) */}
            <path
              d="M36 69 C39 51, 51 39, 67 35 L72 47 C61 50, 52 58, 49 71 Z"
              fill="#FF5500"
              stroke="#FFB085"
              strokeWidth="1.2"
            />
            {/* Multi-piston structural ribs */}
            <line x1="45" y1="62" x2="54" y2="65" stroke="#7C2D12" strokeWidth="1.5" strokeLinecap="round" />
            <line x1="51" y1="53" x2="59" y2="57" stroke="#7C2D12" strokeWidth="1.5" strokeLinecap="round" />
            <line x1="59" y1="45" x2="65" y2="51" stroke="#7C2D12" strokeWidth="1.5" strokeLinecap="round" />
          </g>

          {/* ROTATING FORGED / AERO SPOKES LAYER (Spins smoothly on card hover!) */}
          <g className={styles.wheelRotorSpin}>
            {/* Machined outer rim lip */}
            <circle cx="80" cy="80" r="59" stroke="url(#vw-spoke-finish)" strokeWidth="2.8" fill="none" />

            {design === '21-forged' ? (
              /* 21" Forged Split Y-Spokes */
              spokeAngles.map((angle) => (
                <g key={angle} transform={`rotate(${angle} 80 80)`}>
                  <path
                    d="M77 65 L75 44 L66 23 L71 22 L80 41 L89 22 L94 23 L85 44 L83 65 Z"
                    fill="url(#vw-spoke-finish)"
                    stroke="#1E293B"
                    strokeWidth="0.9"
                    strokeLinejoin="round"
                  />
                  {/* Dark weight-reduction pocket */}
                  <path d="M80 48 L77 32 L83 32 Z" fill="#0F172A" opacity="0.55" />
                </g>
              ))
            ) : (
              /* 20" Directional Aero Turbine Blades */
              spokeAngles.map((angle) => (
                <g key={angle} transform={`rotate(${angle} 80 80)`}>
                  <path
                    d="M76 66 L70 24 C78 21, 88 22, 95 26 L84 66 Z"
                    fill="url(#vw-spoke-finish)"
                    stroke="#0F172A"
                    strokeWidth="1"
                  />
                  {/* Aero carbon insert blade */}
                  <path d="M77 56 L74 28 C79 27, 84 27, 88 29 L82 56 Z" fill="#1E293B" opacity="0.72" />
                </g>
              ))
            )}

            {/* Center Hub Cap & 5 Lug Bolts */}
            <circle cx="80" cy="80" r="15" fill="#0F172A" stroke="#CBD5E1" strokeWidth="1.6" />
            <circle cx="80" cy="80" r="6" fill="#1E293B" stroke="#FF5500" strokeWidth="1.2" />
            {spokeAngles.map((angle) => {
              const rad = ((angle - 90) * Math.PI) / 180;
              const lx = Number((80 + Math.cos(rad) * 10.5).toFixed(2));
              const ly = Number((80 + Math.sin(rad) * 10.5).toFixed(2));
              return <circle key={angle} cx={lx} cy={ly} r="1.7" fill="#CBD5E1" />;
            })}
          </g>
        </svg>
      </div>
    </div>
  );
}

/* ================================================================================================
   09 / TECH — LiDAR Sensor Point-Cloud & SoC Architecture Diagram
================================================================================================ */
const POINT_GRID_COLS = [84, 102, 120, 138, 156, 174, 192, 210, 228, 246];
const POINT_GRID_ROWS = [18, 34, 50, 66, 82, 98, 110];

// Detected spatial target clusters that pulse electric orange
const DETECTED_TARGETS = [
  { cx: 156, cy: 34, delayClass: '' },
  { cx: 192, cy: 66, delayClass: 'lidarTarget2' },
  { cx: 228, cy: 82, delayClass: 'lidarTarget3' },
  { cx: 138, cy: 82, delayClass: 'lidarTarget2' },
  { cx: 210, cy: 34, delayClass: '' },
];

export function TechStage() {
  return (
    <div className={styles.techWrap}>
      <div className={styles.techTopBar}>
        <div className={styles.citationRow}>
          <span className={styles.citationChip}>
            <span className={styles.citationDot} aria-hidden />
            MIIT Filing
          </span>
          <span className={styles.citationChip}>
            <span className={styles.citationDot} aria-hidden />
            OEM Whitepaper
          </span>
        </div>
        <span className={styles.socChip}>508 TOPS</span>
      </div>

      <div className={styles.lidarBox}>
        <svg className={styles.lidarSvg} viewBox="0 0 264 124" fill="none" aria-label="LiDAR point-cloud sensor and SoC diagram">
          <defs>
            <linearGradient id="vw-lidar-beam" x1="48" y1="62" x2="252" y2="62" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#FF5500" stopOpacity="0.48" />
              <stop offset="55%" stopColor="#FF7A33" stopOpacity="0.16" />
              <stop offset="100%" stopColor="#22D3EE" stopOpacity="0.02" />
            </linearGradient>
          </defs>

          {/* Concentric LiDAR range arcs */}
          <path d="M108 16 A74 74 0 0 1 108 108" stroke="rgba(148,163,184,0.16)" strokeWidth="1" strokeDasharray="2 3" />
          <path d="M158 10 A122 122 0 0 1 158 114" stroke="rgba(148,163,184,0.14)" strokeWidth="1" strokeDasharray="2 3" />
          <path d="M210 6 A172 172 0 0 1 210 118" stroke="rgba(148,163,184,0.12)" strokeWidth="1" strokeDasharray="2 3" />

          {/* Spatial Point-Cloud Grid Nodes */}
          {POINT_GRID_COLS.map((x) =>
            POINT_GRID_ROWS.map((y) => (
              <circle key={`${x}-${y}`} cx={x} cy={y} r="1.25" fill="rgba(148,163,184,0.36)" />
            )),
          )}

          {/* Animated LiDAR Radar Sweep Cone */}
          <g className={styles.lidarCone}>
            <path d="M48 62 L248 22 A210 210 0 0 1 248 102 Z" fill="url(#vw-lidar-beam)" />
            <line x1="48" y1="62" x2="252" y2="62" stroke="#FF6B2B" strokeWidth="1.2" strokeOpacity="0.78" />
          </g>

          {/* Detected Target Nodes pulsing in Electric Orange */}
          {DETECTED_TARGETS.map((t, i) => (
            <g
              key={i}
              className={`${styles.lidarTarget} ${t.delayClass ? styles[t.delayClass as keyof typeof styles] : ''}`}
              style={{ transformOrigin: `${t.cx}px ${t.cy}px` }}
            >
              <circle cx={t.cx} cy={t.cy} r="7.5" fill="rgba(255,85,0,0.2)" stroke="#FF5500" strokeWidth="0.9" strokeDasharray="2 2" />
              <circle cx={t.cx} cy={t.cy} r="2.7" fill="#FF5500" />
            </g>
          ))}

          {/* Compute SoC Architecture Core + Bus Traces */}
          <g>
            {/* Data traces from LiDAR turret to SoC */}
            <path d="M32 54 H44 M32 62 H44 M32 70 H44" stroke="#22D3EE" strokeWidth="1.2" strokeOpacity="0.7" />
            {/* SoC Package */}
            <rect x="6" y="42" width="26" height="40" rx="5" fill="#131F38" stroke="#38BDF8" strokeWidth="1.2" />
            <rect x="11" y="49" width="16" height="26" rx="2" fill="rgba(34,211,238,0.18)" stroke="#22D3EE" strokeWidth="0.8" />
            <text x="19" y="65" textAnchor="middle" fill="#E0F2FE" fontSize="6.5" fontFamily="monospace" fontWeight="700">
              SoC
            </text>
            {/* LiDAR Emitter Dome */}
            <circle cx="48" cy="62" r="7" fill="#0F172A" stroke="#FF5500" strokeWidth="1.5" />
            <circle cx="48" cy="62" r="2.6" fill="#FF6B2B" />
          </g>
        </svg>
      </div>
    </div>
  );
}
