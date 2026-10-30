import React from 'react';

/**
 * The Voltway wordmark, drawn rather than set in a typeface: seven bold, square-cut letters that cannot change with a font that has not
 * loaded. Every letter stands on one baseline and under one cap line (the points of the V, W and A are cut flat across them, not left to
 * poke out), the stems are one weight, and the gaps are set by eye, not by the letters' boxes (the L's foot runs under the T's bar). The A
 * has no crossbar: its bar is a pulse, the one stroke in the accent. On the page the letters rise in one after the other and the pulse draws
 * last (landing.module.css; with reduced motion it is simply there).
 */
const CAP = 100;
/** the weight of a stem */
const S = 17;

const f = (n: number) => Math.round(n * 100) / 100;

/** Half the horizontal width of a bar that leans by `run` over the cap height. */
const half = (run: number) => (S / 2) * Math.sqrt(1 + (run / CAP) ** 2);

/**
 * A bar from (x0, y0) to (x1, y1) along its centre, cut flat across at both ends. It is always drawn from the top down, so that bars
 * which cross (the W's) are wound the same way and fill where they overlap instead of cancelling.
 */
function bar(x0: number, y0: number, x1: number, y1: number): string {
  if (y0 > y1) return bar(x1, y1, x0, y0);
  const h = half((x1 - x0) * (CAP / (y1 - y0)));
  return `M${f(x0 - h)} ${y0}L${f(x0 + h)} ${y0}L${f(x1 + h)} ${y1}L${f(x1 - h)} ${y1}Z`;
}

/** The centre, at the cap line, of a bar that leans to (bottomX, 100) and whose outer edge is at `edge` there. */
function topOf(edge: number, bottomX: number): number {
  let x = edge + S / 2;
  for (let i = 0; i < 6; i++) x = edge + half(bottomX - x);
  return x;
}

/** The centre, at the baseline, of a leg whose outer edge is at `edge` there and whose apex is at (apexX, 0). */
function footOf(edge: number, apexX: number): number {
  let x = edge + S / 2;
  for (let i = 0; i < 6; i++) x = edge + half(apexX - x);
  return x;
}

interface Letter {
  /** the letter's width, and the gap to the next one */
  w: number;
  gap: number;
  /** filled shapes */
  d: string;
  /** a stroked shape (the O's ring) */
  ring?: { r: number };
  pulse?: string;
}

const V = (() => {
  const w = 96;
  const x = topOf(0, w / 2);
  return { w, gap: 4, d: bar(x, 0, w / 2, CAP) + bar(w - x, 0, w / 2, CAP) };
})();

const O: Letter = { w: 100, gap: 10, d: '', ring: { r: 50 - S / 2 } };

const L: Letter = { w: 62, gap: -6, d: `M0 0H${S}V${CAP - S}H62V${CAP}H0Z` };

const T: Letter = { w: 92, gap: 6, d: `M0 0H92V${S}H${46 + S / 2}V${CAP}H${46 - S / 2}V${S}H0Z` };

const W = (() => {
  const w = 140;
  const x = topOf(0, w * 0.27);
  return { w, gap: 4, d: bar(x, 0, w * 0.27, CAP) + bar(w * 0.27, CAP, w / 2, 0) + bar(w / 2, 0, w * 0.73, CAP) + bar(w * 0.73, CAP, w - x, 0) };
})();

const A = (() => {
  const w = 104;
  const foot = footOf(0, w / 2);
  const legX = (y: number) => w / 2 + (foot - w / 2) * (y / CAP);
  const l = legX(72);
  const r = w - l;
  const c = w / 2;
  // flat, up the spike, down the deep one, flat: from leg to leg
  const pulse = `M${f(l)} 72H${f(c - 15)}L${f(c - 5)} 56L${f(c + 4)} 92L${f(c + 12)} 68H${f(r)}`;
  return { w, gap: 6, d: bar(w / 2, 0, foot, CAP) + bar(w / 2, 0, w - foot, CAP), pulse };
})();

const Y = (() => {
  const w = 100;
  // the arms lean by 0.76 and meet the stem a little below the middle
  const sx = 0.76;
  const a = S * Math.sqrt(1 + sx * sx);
  const yi = (w / 2 - a) / sx;
  const ym = (w / 2 - S / 2) / sx;
  const d = `M0 0H${f(a)}L${w / 2} ${f(yi)}L${f(w - a)} 0H${w}L${f(w / 2 + S / 2)} ${f(ym)}V${CAP}H${f(w / 2 - S / 2)}V${f(ym)}Z`;
  return { w, gap: 0, d };
})();

const LETTERS: Letter[] = [V, O, L, T, W, A, Y];

export function Wordmark({ className, label = 'Voltway' }: { className?: string; label?: string }) {
  let x = 0;
  const placed = LETTERS.map((l) => {
    const at = x;
    x += l.w + l.gap;
    return { ...l, at };
  });
  const width = x - LETTERS[LETTERS.length - 1].gap;
  return (
    <svg role="img" aria-label={label} viewBox={`0 0 ${width} ${CAP}`} className={className} data-wordmark fill="none">
      <defs>
        {/* one gradient across the whole word: each letter's own copy is shifted back by where the letter stands */}
        {placed.map((l, i) => (
          <linearGradient key={i} id={`wm-ink-${i}`} gradientUnits="userSpaceOnUse" x1={-l.at} y1="0" x2={width - l.at} y2="0">
            <stop offset="0" stopColor="#0a1120" />
            <stop offset="0.55" stopColor="#13294f" />
            <stop offset="1" stopColor="#2a64a6" />
          </linearGradient>
        ))}
        <linearGradient id="wm-pulse" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#ff8a3d" />
          <stop offset="1" stopColor="#ff5a1f" />
        </linearGradient>
      </defs>
      {placed.map((l, i) => (
        <g key={i} transform={`translate(${f(l.at)} 0)`}>
          <g data-letter style={{ ['--i' as string]: i }}>
            {l.d && <path d={l.d} fill={`url(#wm-ink-${i})`} />}
            {l.ring && <circle cx={l.w / 2} cy={CAP / 2} r={l.ring.r} stroke={`url(#wm-ink-${i})`} strokeWidth={S} />}
            {l.pulse && <path d={l.pulse} pathLength={1} data-pulse stroke="url(#wm-pulse)" strokeWidth={10} strokeLinejoin="miter" strokeLinecap="butt" />}
          </g>
        </g>
      ))}
    </svg>
  );
}
