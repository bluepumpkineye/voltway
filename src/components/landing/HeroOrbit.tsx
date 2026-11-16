'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Wordmark } from './Wordmark';
import type { LandingCar } from './types';
import styles from './landing.module.css';

const TWO_PI = Math.PI * 2;
const TRANSITION_MS = 720;
const AUTO_DRIFT_RAD_PER_SEC = -0.065;
const INITIAL_IDLE_DELAY_MS = 1600;
const RESUME_IDLE_DELAY_MS = 3800;

/** Evaluates cubic-bezier(0.22, 1, 0.36, 1) at t in [0, 1]. */
function easeOutExpoish(t: number): number {
  if (t <= 0) return 0;
  if (t >= 1) return 1;
  const x1 = 0.22;
  const y1 = 1.0;
  const x2 = 0.36;
  const y2 = 1.0;

  const sampleX = (u: number) => ((1 - 3 * x2 + 3 * x1) * u + (3 * x2 - 6 * x1)) * u * u + 3 * x1 * u * (1 - u) * (1 - u) + u * u * u;
  // Simplified exact Bezier polynomial for (0,0), (x1,y1), (x2,y2), (1,1):
  const bezier = (u: number, p1: number, p2: number) => {
    const inv = 1 - u;
    return 3 * inv * inv * u * p1 + 3 * inv * u * u * p2 + u * u * u;
  };
  const bezierDeriv = (u: number, p1: number, p2: number) => {
    const inv = 1 - u;
    return 3 * inv * inv * p1 + 6 * inv * u * (p2 - p1) + 3 * u * u * (1 - p2);
  };
  void sampleX;

  let u = t;
  for (let i = 0; i < 6; i++) {
    const err = bezier(u, x1, x2) - t;
    const d = bezierDeriv(u, x1, x2);
    if (Math.abs(err) < 1e-5 || Math.abs(d) < 1e-6) break;
    u = Math.min(1, Math.max(0, u - err / d));
  }
  return bezier(u, y1, y2);
}

function wrapAngle(rad: number): number {
  const m = ((rad % TWO_PI) + TWO_PI) % TWO_PI;
  return m > Math.PI ? m - TWO_PI : m;
}

function closestCarIndex(rotation: number, total: number): number {
  let bestIdx = 0;
  let bestCos = -Infinity;
  for (let i = 0; i < total; i++) {
    const angle = (i / total) * TWO_PI + rotation;
    const c = Math.cos(angle);
    if (c > bestCos) {
      bestCos = c;
      bestIdx = i;
    }
  }
  return bestIdx;
}

interface OrbitSlotMetrics {
  x: number;
  y: number;
  z: number;
  scale: number;
  opacity: number;
  blur: number;
  zIndex: number;
}

function computeSlotMetrics(index: number, total: number, rotation: number, radiusX: number, radiusY: number, radiusZ: number): OrbitSlotMetrics {
  const angle = (index / total) * TWO_PI + rotation;
  const sinA = Math.sin(angle);
  const cosA = Math.cos(angle);

  const x = sinA * radiusX;
  const z = cosA * radiusZ;
  const y = cosA * radiusY;

  // Normalized front-to-back depth: 0 at back (cos = -1), 1 at front (cos = +1)
  const depthT = (cosA + 1) * 0.5;
  const scale = 0.48 + (1.05 - 0.48) * Math.pow(depthT, 1.15);
  const opacity = 0.55 + (1.0 - 0.55) * Math.pow(depthT, 0.9);
  const blur = depthT < 0.72 ? ((0.72 - depthT) / 0.72) * 1.5 : 0;
  const zIndex = Math.round(depthT * 100) + 10;

  return { x, y, z, scale, opacity, blur, zIndex };
}

const num = (n: number) => n.toLocaleString('en-US');

export function HeroOrbit({ cars }: { cars: LandingCar[] }) {
  const total = cars.length;
  const stepAngle = TWO_PI / total;

  const [activeIndex, setActiveIndex] = useState(0);
  const activeIndexRef = useRef(0);

  const stageRef = useRef<HTMLDivElement>(null);
  const slotRefs = useRef<(HTMLLIElement | null)[]>([]);

  const rotRef = useRef(0);
  const dimsRef = useRef({ radiusX: 500, radiusY: 74, radiusZ: 220 });
  const animRef = useRef<{ active: boolean; from: number; to: number; startMs: number; durationMs: number }>({
    active: false,
    from: 0,
    to: 0,
    startMs: 0,
    durationMs: TRANSITION_MS,
  });
  const hoverPausedRef = useRef(false);
  const focusPausedRef = useRef(false);
  const reducedMotionRef = useRef(false);
  const lastInteractMsRef = useRef(0);
  const mountedMsRef = useRef(0);

  const dragRef = useRef<{
    pointerDown: boolean;
    dragging: boolean;
    startX: number;
    startRot: number;
    lastX: number;
    lastMs: number;
    velocityRadPerMs: number;
    suppressNextClick: boolean;
  }>({
    pointerDown: false,
    dragging: false,
    startX: 0,
    startRot: 0,
    lastX: 0,
    lastMs: 0,
    velocityRadPerMs: 0,
    suppressNextClick: false,
  });

  const applyPositions = useCallback(
    (rotation: number) => {
      const { radiusX, radiusY, radiusZ } = dimsRef.current;
      for (let i = 0; i < total; i++) {
        const el = slotRefs.current[i];
        if (!el) continue;
        const m = computeSlotMetrics(i, total, rotation, radiusX, radiusY, radiusZ);
        el.style.transform = `translate3d(${m.x.toFixed(2)}px, ${m.y.toFixed(2)}px, ${m.z.toFixed(2)}px) translate(-50%, -50%) scale(${m.scale.toFixed(4)})`;
        el.style.opacity = m.opacity.toFixed(3);
        el.style.filter = m.blur > 0.04 ? `blur(${m.blur.toFixed(2)}px)` : 'none';
        el.style.zIndex = String(m.zIndex);
      }
      const nextActive = closestCarIndex(rotation, total);
      if (nextActive !== activeIndexRef.current) {
        activeIndexRef.current = nextActive;
        setActiveIndex(nextActive);
      }
    },
    [total],
  );

  const animateToRotation = useCallback((targetRot: number, durationMs = TRANSITION_MS) => {
    const now = performance.now();
    lastInteractMsRef.current = now;
    if (reducedMotionRef.current) {
      animRef.current.active = false;
      rotRef.current = targetRot;
      applyPositions(targetRot);
      return;
    }
    animRef.current = {
      active: true,
      from: rotRef.current,
      to: targetRot,
      startMs: now,
      durationMs,
    };
  }, [applyPositions]);

  const rotateToIndex = useCallback(
    (index: number) => {
      const base = (index / total) * TWO_PI;
      const currentAtFront = -rotRef.current;
      const delta = wrapAngle(base - currentAtFront);
      animateToRotation(rotRef.current - delta);
    },
    [animateToRotation, total],
  );

  const stepOrbit = useCallback(
    (direction: 'prev' | 'next') => {
      const currentTarget = animRef.current.active ? animRef.current.to : rotRef.current;
      const snappedIdx = closestCarIndex(currentTarget, total);
      const targetIdx = direction === 'next' ? (snappedIdx + 1) % total : (snappedIdx - 1 + total) % total;
      const base = (targetIdx / total) * TWO_PI;
      const currentAtFront = -rotRef.current;
      let delta = wrapAngle(base - currentAtFront);
      // Guarantee forward/backward step direction even at wrap boundary
      if (direction === 'next' && delta <= 0.05) delta += TWO_PI;
      if (direction === 'prev' && delta >= -0.05) delta -= TWO_PI;
      if (Math.abs(delta) > Math.PI * 1.35) {
        delta = direction === 'next' ? stepAngle : -stepAngle;
      }
      animateToRotation(rotRef.current - delta);
    },
    [animateToRotation, stepAngle, total],
  );

  // Measure responsive ellipse radii
  useEffect(() => {
    const updateDims = () => {
      const vw = window.innerWidth;
      const stageWidth = stageRef.current?.clientWidth || vw;
      const isMobile = vw < 768;
      const radiusX = isMobile ? Math.min(stageWidth * 0.38, 250) : Math.min(vw * 0.42, 580, stageWidth * 0.44);
      const radiusY = isMobile ? 42 : vw < 1100 ? 64 : 78;
      const radiusZ = isMobile ? 140 : 220;
      dimsRef.current = { radiusX, radiusY, radiusZ };
      applyPositions(rotRef.current);
    };

    updateDims();
    const ro = new ResizeObserver(updateDims);
    if (stageRef.current) ro.observe(stageRef.current);
    window.addEventListener('resize', updateDims);
    return () => {
      ro.disconnect();
      window.removeEventListener('resize', updateDims);
    };
  }, [applyPositions]);

  // Animation loop: handles cubic-bezier transitions & gentle idle auto-drift
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    reducedMotionRef.current = mq.matches;
    const onMqChange = (e: MediaQueryListEvent) => {
      reducedMotionRef.current = e.matches;
    };
    mq.addEventListener('change', onMqChange);

    mountedMsRef.current = performance.now();
    let lastFrameMs = mountedMsRef.current;
    let rafId = 0;

    const tick = (now: number) => {
      const dtSec = Math.min(0.05, Math.max(0, (now - lastFrameMs) / 1000));
      lastFrameMs = now;

      if (animRef.current.active) {
        const elapsed = now - animRef.current.startMs;
        const t = Math.min(1, elapsed / animRef.current.durationMs);
        const eased = easeOutExpoish(t);
        rotRef.current = animRef.current.from + (animRef.current.to - animRef.current.from) * eased;
        applyPositions(rotRef.current);
        if (t >= 1) {
          animRef.current.active = false;
          rotRef.current = animRef.current.to;
          applyPositions(rotRef.current);
        }
      } else if (
        !dragRef.current.dragging &&
        !hoverPausedRef.current &&
        !focusPausedRef.current &&
        !reducedMotionRef.current
      ) {
        const sinceMount = now - mountedMsRef.current;
        const sinceInteract = lastInteractMsRef.current > 0 ? now - lastInteractMsRef.current : Infinity;
        if (sinceMount > INITIAL_IDLE_DELAY_MS && sinceInteract > RESUME_IDLE_DELAY_MS) {
          rotRef.current += AUTO_DRIFT_RAD_PER_SEC * dtSec;
          applyPositions(rotRef.current);
        }
      }

      rafId = requestAnimationFrame(tick);
    };

    rafId = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(rafId);
      mq.removeEventListener('change', onMqChange);
    };
  }, [applyPositions]);

  // Keyboard arrow navigation when hero is visible or focused
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
      const target = e.target as HTMLElement | null;
      if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT')) return;
      if (window.scrollY > window.innerHeight * 0.75) return;
      e.preventDefault();
      stepOrbit(e.key === 'ArrowRight' ? 'next' : 'prev');
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [stepOrbit]);

  // Horizontal drag / swipe support
  useEffect(() => {
    const onPointerMove = (e: PointerEvent) => {
      const d = dragRef.current;
      if (!d.pointerDown) return;
      const dx = e.clientX - d.startX;
      if (!d.dragging && Math.abs(dx) > 6) {
        d.dragging = true;
        animRef.current.active = false;
      }
      if (!d.dragging) return;

      const sensitivity = Math.PI / Math.max(240, dimsRef.current.radiusX * 1.15);
      const now = performance.now();
      const dt = Math.max(1, now - d.lastMs);
      const stepDelta = (e.clientX - d.lastX) * sensitivity;
      d.velocityRadPerMs = stepDelta / dt;
      d.lastX = e.clientX;
      d.lastMs = now;

      rotRef.current = d.startRot + dx * sensitivity;
      lastInteractMsRef.current = now;
      applyPositions(rotRef.current);
    };

    const onPointerUp = () => {
      const d = dragRef.current;
      if (!d.pointerDown) return;
      d.pointerDown = false;
      if (d.dragging) {
        d.dragging = false;
        d.suppressNextClick = true;
        window.setTimeout(() => {
          dragRef.current.suppressNextClick = false;
        }, 80);
        // Snap cleanly to nearest slot with gentle inertia
        const projected = rotRef.current + d.velocityRadPerMs * 160;
        const nearestIdx = closestCarIndex(projected, total);
        const base = (nearestIdx / total) * TWO_PI;
        const delta = wrapAngle(base - -rotRef.current);
        animateToRotation(rotRef.current - delta, 620);
      }
    };

    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);
    window.addEventListener('pointercancel', onPointerUp);
    return () => {
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
      window.removeEventListener('pointercancel', onPointerUp);
    };
  }, [animateToRotation, applyPositions, total]);

  const handleStagePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if (e.button !== 0 && e.pointerType === 'mouse') return;
    const target = e.target as HTMLElement;
    if (target.closest('[data-orbit-control]')) return;
    dragRef.current = {
      pointerDown: true,
      dragging: false,
      startX: e.clientX,
      startRot: rotRef.current,
      lastX: e.clientX,
      lastMs: performance.now(),
      velocityRadPerMs: 0,
      suppressNextClick: false,
    };
  };

  const activeCar = cars[activeIndex] ?? cars[0];

  return (
    <header
      id="top"
      className={styles.hero}
      onMouseEnter={() => {
        hoverPausedRef.current = true;
      }}
      onMouseLeave={() => {
        hoverPausedRef.current = false;
      }}
      onFocus={() => {
        focusPausedRef.current = true;
      }}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node | null)) {
          focusPausedRef.current = false;
        }
      }}
    >
      {/* X-Ray Play Sequence Atmosphere: Azure Sky, Two-Tier Hills, Haze & Glossy Salt Flat */}
      <div className={styles.sky} aria-hidden />
      <div className={styles.ridges} aria-hidden>
        <XrayHills />
      </div>
      <div className={styles.saltFloor} aria-hidden>
        <div className={styles.saltMirrorHills}>
          <XrayHills />
        </div>
        <SaltCracks />
        <div className={styles.saltHaze} />
      </div>

      {/* Tighter Header Block */}
      <div className={styles.head}>
        <h1 className={styles.title}>
          <Wordmark idPrefix="hero" className={styles.wordmark} />
        </h1>
        <p className={styles.eyebrow}>The Digital Showroom</p>
        <p className={styles.lede}>Choose a car to walk around, sit inside and drive.</p>
      </div>

      {/* Interactive 3D Elliptical Orbital Stage */}
      <div
        ref={stageRef}
        className={styles.orbitStage}
        onPointerDown={handleStagePointerDown}
        role="region"
        aria-roledescription="carousel"
        aria-label="Interactive 3D vehicle orbit"
      >
        {/* Subtle studio elliptical orbit floor ring */}
        <div className={styles.orbitRing} aria-hidden />
        <div className={styles.orbitSpotlight} aria-hidden />

        {/* Previous / Next Circular Glass Controls flanking the center car */}
        <button
          type="button"
          data-orbit-control
          className={`${styles.orbitNavBtn} ${styles.orbitNavPrev}`}
          onClick={() => stepOrbit('prev')}
          aria-label="Previous vehicle"
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden>
            <path d="M11 4 6 9l5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>

        <button
          type="button"
          data-orbit-control
          className={`${styles.orbitNavBtn} ${styles.orbitNavNext}`}
          onClick={() => stepOrbit('next')}
          aria-label="Next vehicle"
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden>
            <path d="M7 4l5 5-5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>

        <ul className={styles.orbitTrack} aria-label="Models in 3D orbit">
          {cars.map((car, i) => {
            const isActive = i === activeIndex;
            const initialMetrics = computeSlotMetrics(i, total, 0, 500, 74, 220);
            const name = `${car.brand} ${car.model}`;
            return (
              <li
                key={car.slug}
                ref={(el) => {
                  slotRefs.current[i] = el;
                }}
                className={`${styles.orbitSlot} ${isActive ? styles.orbitSlotActive : ''}`}
                style={{
                  transform: `translate3d(${initialMetrics.x}px, ${initialMetrics.y}px, ${initialMetrics.z}px) translate(-50%, -50%) scale(${initialMetrics.scale})`,
                  opacity: initialMetrics.opacity,
                  filter: initialMetrics.blur > 0.04 ? `blur(${initialMetrics.blur}px)` : 'none',
                  zIndex: initialMetrics.zIndex,
                }}
              >
                <Link
                  href={`/showroom/${car.slug}`}
                  className={styles.orbitCarLink}
                  aria-label={isActive ? `${name}: enter 3D showroom` : `${name}: focus in center spotlight`}
                  aria-current={isActive ? 'true' : undefined}
                  draggable={false}
                  onClick={(e) => {
                    if (dragRef.current.suppressNextClick) {
                      e.preventDefault();
                      return;
                    }
                    if (i !== activeIndexRef.current) {
                      e.preventDefault();
                      rotateToIndex(i);
                    }
                  }}
                >
                  <span className={styles.orbitPicWrap}>
                    <span className={styles.orbitShadow} style={{ ['--idx' as string]: i }} aria-hidden />
                    <span className={styles.orbitFloat} style={{ ['--idx' as string]: i }}>
                      <Image
                        className={styles.orbitMirror}
                        src={`/landing/${car.slug}.webp`}
                        width={car.imageW}
                        height={car.imageH}
                        alt=""
                        unoptimized
                        priority
                        draggable={false}
                      />
                      <Image
                        className={styles.orbitPic}
                        src={`/landing/${car.slug}.webp`}
                        width={car.imageW}
                        height={car.imageH}
                        alt={name}
                        unoptimized
                        priority
                        draggable={false}
                      />
                    </span>
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      </div>

      {/* Active Car HUD (Heads-Up Display) Panel */}
      <div className={styles.hudWrap} data-orbit-control>
        <div className={styles.hudCard} role="status" aria-live="polite">
          <div className={styles.hudIdentity}>
            <span className={styles.hudIndex} aria-label={`Model ${activeIndex + 1} of ${total}`}>
              <span className={styles.hudLiveDot} aria-hidden />
              <span className="tnum">
                {String(activeIndex + 1).padStart(2, '0')} / {String(total).padStart(2, '0')}
              </span>
            </span>
            <div className={styles.hudTitleGroup}>
              <span className={styles.hudBrand}>{activeCar.brand}</span>
              <span className={styles.hudSep} aria-hidden>
                ·
              </span>
              <span className={styles.hudModel}>{activeCar.model}</span>
            </div>
          </div>

          <div className={styles.hudTelemetry}>
            {activeCar.zeroTo100S !== null && (
              <span className={styles.hudPill}>
                <span className={styles.hudPillLabel}>0–100 km/h:</span>{' '}
                <strong className="tnum">{activeCar.zeroTo100S} s</strong>
              </span>
            )}
            <span className={styles.hudPill}>
              <span className={styles.hudPillLabel}>Peak Power:</span>{' '}
              <strong className="tnum">{num(Math.round(activeCar.powerKw))} kW</strong>
            </span>
            <span className={styles.hudPill}>
              <span className={styles.hudPillLabel}>Body:</span>{' '}
              <strong>{activeCar.bodyStyle}</strong>
            </span>
          </div>

          <Link href={`/showroom/${activeCar.slug}`} className={styles.hudCta}>
            <span>Enter 3D Showroom</span>
            <span className={styles.hudCtaArrow} aria-hidden>
              →
            </span>
          </Link>
        </div>

        {/* Quick dot selector below HUD for instant visual orbit orientation */}
        <div className={styles.orbitDots} role="tablist" aria-label="Select vehicle in orbit">
          {cars.map((car, i) => (
            <button
              key={car.slug}
              type="button"
              role="tab"
              aria-selected={i === activeIndex}
              aria-label={`${car.brand} ${car.model}`}
              className={`${styles.orbitDot} ${i === activeIndex ? styles.orbitDotActive : ''}`}
              onClick={() => rotateToIndex(i)}
            />
          ))}
        </div>
      </div>
    </header>
  );
}

/** X-Ray Play Sequence distant hills: two seeded silhouettes fading into the #b9dff2 horizon haze. */
function XrayHills() {
  return (
    <svg viewBox="0 0 1600 200" preserveAspectRatio="none" aria-hidden>
      <defs>
        <linearGradient id="xray-hill-far" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#6b97b8" />
          <stop offset="1" stopColor="#b9dff2" />
        </linearGradient>
        <linearGradient id="xray-hill-near" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#3f6a90" />
          <stop offset="1" stopColor="#b9dff2" />
        </linearGradient>
      </defs>
      <path
        d="M0 200V128L80 102 175 118 270 74 375 108 485 68 590 104 695 86 800 120 915 106 1025 124 1140 82 1255 106 1370 62 1485 98 1600 84V200Z"
        fill="url(#xray-hill-far)"
        opacity="0.92"
      />
      <path
        d="M0 200V152L105 130 220 146 340 114 465 142 595 122 720 152 840 138 965 154 1090 132 1215 148 1335 112 1465 140 1600 126V200Z"
        fill="url(#xray-hill-near)"
        opacity="0.96"
      />
    </svg>
  );
}

/** Procedural salt-flat cracks from XrayWorld.tsx drawn onto a perspective floor canvas. */
function SaltCracks() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const S = 512;
    const tile = document.createElement('canvas');
    tile.width = tile.height = S;
    const g = tile.getContext('2d');
    if (!g) return;

    const n = 9;
    const cell = S / n;
    const rnd = (i: number, j: number, k: number) => {
      const s = Math.sin(((i + n * 64) % n) * 12.9898 + ((j + n * 64) % n) * 78.233 + k * 37.719) * 43758.5453;
      return s - Math.floor(s);
    };
    const pt = (i: number, j: number) => ({
      x: (i + 0.15 + 0.7 * rnd(i, j, 1)) * cell,
      y: (j + 0.15 + 0.7 * rnd(i, j, 2)) * cell,
    });
    const line = (a: { x: number; y: number }, b: { x: number; y: number }, w: number, style: string) => {
      g.strokeStyle = style;
      g.lineWidth = w;
      g.beginPath();
      g.moveTo(a.x, a.y);
      const mx = (a.x + b.x) / 2 + (rnd(a.x | 0, a.y | 0, 3) - 0.5) * cell * 0.25;
      const my = (a.y + b.y) / 2 + (rnd(a.x | 0, a.y | 0, 4) - 0.5) * cell * 0.25;
      g.quadraticCurveTo(mx, my, b.x, b.y);
      g.stroke();
    };

    for (const ox of [-S, 0, S]) {
      for (const oy of [-S, 0, S]) {
        g.save();
        g.translate(ox, oy);
        for (let j = 0; j < n; j++) {
          for (let i = 0; i < n; i++) {
            const a = pt(i, j);
            for (const [di, dj] of [
              [1, 0],
              [0, 1],
            ]) {
              const b = pt(i + di, j + dj);
              const bb = { x: b.x + (i + di >= n ? S : 0), y: b.y + (j + dj >= n ? S : 0) };
              line(a, bb, 1.8, 'rgba(3, 12, 22, 0.52)');
              line({ x: a.x + 1.4, y: a.y + 1.4 }, { x: bb.x + 1.4, y: bb.y + 1.4 }, 0.9, 'rgba(160, 205, 235, 0.16)');
            }
          }
        }
        g.restore();
      }
    }

    const out = canvas.getContext('2d');
    if (!out) return;
    canvas.width = 1600;
    canvas.height = 900;
    const pat = out.createPattern(tile, 'repeat');
    if (!pat) return;
    out.clearRect(0, 0, canvas.width, canvas.height);
    out.fillStyle = pat;
    out.fillRect(0, 0, canvas.width, canvas.height);
  }, []);

  return <canvas ref={canvasRef} className={styles.saltCracksCanvas} aria-hidden />;
}
