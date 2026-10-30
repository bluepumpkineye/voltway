/**
 * Where the Drive tab's cards go: a pure layout in screen pixels (no React, no DOM), so that it is checked in Node
 * (scripts/tech-tools/motion-test.mjs).
 *
 * A card floats beside the car, near the point it explains, and not over the car, the gauges, the caption or another card. For each
 * card a handful of places are tried (left of the car, right of it, above, below, and hugging the point) and the best is taken by
 * a score: how much of the card would lie outside the free part of the window, over the car's outline or over something to keep
 * clear, how far it is from its point, and a small bonus for the place it had a moment ago (so that it does not flip between two
 * as the camera moves). Nothing is drawn from a card to its point: standing next to the part is what says which it is, so the cards
 * stand close to it.
 */
export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface Pt {
  x: number;
  y: number;
}

export interface CardSpec {
  id: string;
  w: number;
  h: number;
  /** the points the card explains, on screen: the first decides where the card goes */
  targets: Pt[];
}

export interface LayoutScene {
  /** the part of the window the cards may use */
  safe: Rect;
  /** the car's outline */
  car: Rect;
  /** places to keep clear (the caption, the trim's figures while they show) */
  avoid: Rect[];
}

export interface Placed {
  id: string;
  rect: Rect;
  slot: Slot;
}

export type Slot = 'left' | 'right' | 'above' | 'below' | 'left-near' | 'right-near' | 'above-near' | 'below-near';

/** the space between a card and the car's outline or the point it is next to */
const GAP = 14;
/** the space between two cards that stand one over the other */
const STACK = 10;

const area = (r: Rect) => r.w * r.h;

export function overlap(a: Rect, b: Rect): number {
  const w = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
  const h = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
  return w > 0 && h > 0 ? w * h : 0;
}

/** How far a point is from a rectangle (0 inside it). */
export function distanceTo(r: Rect, p: Pt): number {
  const dx = Math.max(r.x - p.x, 0, p.x - (r.x + r.w));
  const dy = Math.max(r.y - p.y, 0, p.y - (r.y + r.h));
  return Math.hypot(dx, dy);
}

/** The rectangle moved to lie inside `bounds` (as far as it can: one larger than the bounds is put at their top left). */
export function clampInto(r: Rect, bounds: Rect): Rect {
  const x = Math.max(bounds.x, Math.min(r.x, bounds.x + bounds.w - r.w));
  const y = Math.max(bounds.y, Math.min(r.y, bounds.y + bounds.h - r.h));
  return { ...r, x, y };
}

function candidate(slot: Slot, card: CardSpec, car: Rect): Rect {
  const T = card.targets[0] ?? { x: car.x + car.w / 2, y: car.y + car.h / 2 };
  const { w, h } = card;
  switch (slot) {
    case 'left':
      return { x: car.x - GAP - w, y: T.y - h / 2, w, h };
    case 'right':
      return { x: car.x + car.w + GAP, y: T.y - h / 2, w, h };
    case 'above':
      return { x: T.x - w / 2, y: car.y - GAP - h, w, h };
    case 'below':
      return { x: T.x - w / 2, y: car.y + car.h + GAP, w, h };
    case 'left-near':
      return { x: T.x - GAP - w, y: T.y - h / 2, w, h };
    case 'right-near':
      return { x: T.x + GAP, y: T.y - h / 2, w, h };
    case 'above-near':
      return { x: T.x - w / 2, y: T.y - GAP - h, w, h };
    case 'below-near':
      return { x: T.x - w / 2, y: T.y + GAP, w, h };
  }
}

const SLOTS: Slot[] = ['left', 'right', 'above', 'below', 'left-near', 'right-near', 'above-near', 'below-near'];

/**
 * Place the cards one after another (the first is the one that matters most); `prev` is the slot each had in the last frame.
 * A card that fits nowhere is still placed, at the least bad of the places.
 */
export function layoutCards(cards: CardSpec[], scene: LayoutScene, prev: Record<string, Slot> = {}): Placed[] {
  const placed: Placed[] = [];
  for (const card of cards) {
    const T = card.targets[0] ?? { x: scene.car.x + scene.car.w / 2, y: scene.car.y + scene.car.h / 2 };
    // (a holder, not a variable: it is set inside a closure, which the compiler's flow analysis does not follow)
    const pick: { best: Placed | null; score: number } = { best: null, score: -Infinity };
    const consider = (slot: Slot, ideal: Rect) => {
      const rect = clampInto(ideal, scene.safe);
      const a = area(rect);
      const moved = Math.hypot(rect.x - ideal.x, rect.y - ideal.y);
      let score = 0;
      score -= (overlap(rect, scene.car) / a) * 1200;
      for (const av of scene.avoid) score -= (overlap(rect, av) / a) * 900;
      for (const p of placed) score -= (overlap(rect, p.rect) / a) * 1500;
      // a card squeezed against the edge of the window, far from where it wanted to be, is a poor one
      score -= moved * 0.6;
      score -= distanceTo(rect, T) * 0.5;
      if (prev[card.id] === slot) score += 35;
      if (score > pick.score) {
        pick.score = score;
        pick.best = { id: card.id, rect, slot };
      }
    };
    for (const slot of SLOTS) {
      const ideal = candidate(slot, card, scene.car);
      consider(slot, ideal);
      // a card that would lie over one already placed may stand above it or below it, in the same column
      for (const p of placed) {
        if (overlap(ideal, p.rect) <= 0) continue;
        consider(slot, { ...ideal, y: p.rect.y + p.rect.h + STACK });
        consider(slot, { ...ideal, y: p.rect.y - ideal.h - STACK });
      }
    }
    placed.push(pick.best as Placed);
  }
  return separate(placed, scene.safe);
}

/**
 * Two cards that still overlap in a column (the free height was short) are pushed apart, the upper one up and the lower one down by
 * half the overlap each (and back inside the safe part), a few times over, so that a stack uses the whole height it has.
 */
function separate(placed: Placed[], safe: Rect): Placed[] {
  const rects = placed.map((p) => ({ ...p.rect }));
  for (let pass = 0; pass < 6; pass++) {
    let moved = false;
    for (let i = 0; i < rects.length; i++) {
      for (let j = i + 1; j < rects.length; j++) {
        const a = rects[i];
        const b = rects[j];
        const across = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
        const down = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
        // cards closer than the gap are pushed apart as well as those that overlap
        if (across <= 0 || down + STACK <= 0) continue;
        const push = (down + STACK) / 2;
        const upper = a.y <= b.y ? a : b;
        const lower = upper === a ? b : a;
        upper.y -= push;
        lower.y += push;
        Object.assign(upper, clampInto(upper, safe));
        Object.assign(lower, clampInto(lower, safe));
        moved = true;
      }
    }
    if (!moved) break;
  }
  return placed.map((p, i) => ({ ...p, rect: rects[i] }));
}
