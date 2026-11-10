/**
 * Where the exploded view's labels stand. A label is a small pill in a column at one side of the picture, joined to the part it names
 * by a leader line, as on an engineering drawing: parts left of the middle of the free area get the left column, the others the
 * right, each column ordered by height and pushed apart so no two overlap. Pure geometry (no React, no three.js): the viewer
 * (viewer/XrayLabelDriver.tsx) projects the parts to the screen every frame, calls this and writes the result to the pills.
 */

export interface LabelAnchor {
  id: string;
  /** the part's point on the screen, px */
  x: number;
  y: number;
  /** the pill's own size, px */
  w: number;
  h: number;
  /** a label that has a say in which column it joins */
  prefer?: 'left' | 'right';
}

export interface LabelPlace {
  id: string;
  side: 'left' | 'right';
  /** the pill's top-left corner */
  px: number;
  py: number;
  /** where the leader meets the pill: the middle of the edge that faces the part */
  ex: number;
  ey: number;
}

export interface LabelArea {
  left: number;
  right: number;
  top: number;
  bottom: number;
}

const GAP = 6;

/** Push a column's pills apart, in order, then back up from the bottom if the last of them has run out of room. */
function pack(items: { id: string; y: number; h: number }[], top: number, bottom: number): Map<string, number> {
  const out = new Map<string, number>();
  let prev = top - GAP;
  const ys: number[] = [];
  for (const it of items) {
    const y = Math.max(it.y - it.h / 2, prev + GAP);
    ys.push(y);
    prev = y + it.h;
  }
  // too low: lift from the bottom up
  let limit = bottom;
  for (let i = items.length - 1; i >= 0; i--) {
    const max = limit - items[i].h;
    if (ys[i] > max) ys[i] = max;
    limit = ys[i] - GAP;
  }
  items.forEach((it, i) => out.set(it.id, Math.max(top, ys[i])));
  return out;
}

export function layoutLabels(anchors: LabelAnchor[], area: LabelArea): LabelPlace[] {
  const mid = (area.left + area.right) / 2;
  const left: LabelAnchor[] = [];
  const right: LabelAnchor[] = [];
  for (const a of anchors) (a.x < mid ? left : right).push(a);
  // balance: a column far longer than the other gives its extra pills (the ones nearest the middle) to it
  const spill = (from: LabelAnchor[], to: LabelAnchor[], dir: 1 | -1) => {
    while (from.length - to.length > 2) {
      from.sort((p, q) => dir * (q.x - p.x));
      const moved = from.pop();
      if (moved) to.push(moved);
    }
  };
  spill(left, right, 1);
  spill(right, left, -1);

  const out: LabelPlace[] = [];
  const place = (col: LabelAnchor[], side: 'left' | 'right') => {
    col.sort((p, q) => p.y - q.y);
    const ys = pack(col.map((c) => ({ id: c.id, y: c.y, h: c.h })), area.top, area.bottom);
    for (const c of col) {
      const py = ys.get(c.id) ?? c.y;
      const px = side === 'left' ? area.left : area.right - c.w;
      out.push({ id: c.id, side, px, py, ex: side === 'left' ? px + c.w : px, ey: py + c.h / 2 });
    }
  };
  place(left, 'left');
  place(right, 'right');
  return out;
}
