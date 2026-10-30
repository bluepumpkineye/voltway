import React from 'react';

/**
 * The Voltway wordmark, drawn as strokes rather than set in a typeface: seven letters of one weight, square-cut and a little wide, so
 * that it reads as a mark at any size and cannot change with a font that has not loaded. The A has no crossbar: its bar is a pulse, the
 * one stroke in the accent. On the page the strokes draw themselves on, letter by letter, and the pulse lights last (landing.module.css;
 * with reduced motion it is simply there).
 */
const LETTERS: { d: string; w: number; pulse?: string }[] = [
  { d: 'M0 0 L35 100 L70 0', w: 70 }, // V
  { d: 'M40 0 H40 M0 50 C0 18 18 0 40 0 C62 0 80 18 80 50 C80 82 62 100 40 100 C18 100 0 82 0 50 Z', w: 80 }, // O
  { d: 'M0 0 V100 H54', w: 54 }, // L
  { d: 'M0 0 H70 M35 0 V100', w: 70 }, // T
  { d: 'M0 0 L25 100 L51 28 L77 100 L102 0', w: 102 }, // W
  { d: 'M0 100 L40 0 L80 100', w: 80, pulse: 'M14 74 H31 L40 46 L48 86 L55 66 H66' }, // A
  { d: 'M0 0 L35 50 L70 0 M35 50 V100', w: 70 }, // Y
];

const GAP = 30;
const STROKE = 12;

export function Wordmark({ className, label = 'Voltway' }: { className?: string; label?: string }) {
  let x = STROKE / 2;
  const placed = LETTERS.map((l) => {
    const at = x;
    x += l.w + GAP;
    return { ...l, at };
  });
  const width = x - GAP + STROKE / 2;
  return (
    <svg
      role="img"
      aria-label={label}
      viewBox={`0 ${-STROKE} ${width + STROKE / 2} ${100 + STROKE * 2}`}
      className={className}
      data-wordmark
      fill="none"
    >
      <defs>
        {/* one gradient across the whole word: each letter's own copy is shifted back by where the letter stands */}
        {placed.map((l, i) => (
          <linearGradient key={i} id={`wm-ink-${i}`} gradientUnits="userSpaceOnUse" x1={-l.at} y1="0" x2={width - l.at} y2="0">
            <stop offset="0" stopColor="#0b1322" />
            <stop offset="0.6" stopColor="#15305a" />
            <stop offset="1" stopColor="#2b66a8" />
          </linearGradient>
        ))}
        <linearGradient id="wm-pulse" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#ff8a3d" />
          <stop offset="1" stopColor="#ff5a1f" />
        </linearGradient>
      </defs>
      {placed.map((l, i) => (
        <g key={i} transform={`translate(${l.at} 0)`}>
          <path d={l.d} pathLength={1} data-stroke style={{ ['--i' as string]: i }} stroke={`url(#wm-ink-${i})`} strokeWidth={STROKE} strokeLinejoin="miter" strokeLinecap="butt" />
          {l.pulse && <path d={l.pulse} pathLength={1} data-pulse stroke="url(#wm-pulse)" strokeWidth={STROKE - 1} strokeLinejoin="miter" strokeLinecap="butt" />}
        </g>
      ))}
    </svg>
  );
}
