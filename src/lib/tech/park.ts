/**
 * "Park from your phone": the stage and the motion of a perpendicular reverse-in and the
 * way out again (docs/tech-showcase.md). Pure maths on top of kinematics.ts.
 *
 * The floor frame is the kinematics' (x forward, y left, counter-clockwise from above)
 * with the origin wherever the start pose says. The car begins in a lane, heading +x,
 * stopped just past the empty bay, which is on its right. It reverses in along one arc
 * about a point on its right and then straight back:
 *
 *            north (+y)
 *   lane       ->  car (heading +x) at E
 *   ----------------------------------   y = start.y - laneHalf (the bay mouths)
 *   |  bay  |  target bay  |  bay  |
 *   |  car  |   (empty)    |  car  |
 *
 * The reverse arc has its centre C = E + (0, -R): the rear axle's middle runs from E,
 * west and down, to (E.x - R, E.y - R) with the car now heading north, and the straight
 * reverse takes it the rest of the way in. Driving out is the same path run forward, and
 * ends exactly at E. At R = 5.2 m the front wheels of the RX (3.0 m wheelbase) turn about 35
 * and 27 degrees, inside what a car of that size can do, and the body keeps 44 cm from the
 * neighbours in bays 2.7 m wide.
 */
import { arc, Track, type Layout, type Motion, type Segment, type Vec2 } from './kinematics';

/** The car's body from the middle of its rear axle: metres behind it, ahead of it, and half its width. */
export interface BodyBox {
  rear: number;
  front: number;
  halfWidth: number;
}

export interface Pose {
  x: number;
  y: number;
  yaw: number;
}

/** An oriented rectangle: centre, heading (the long side) and size. */
export interface Rect {
  x: number;
  y: number;
  yaw: number;
  length: number;
  width: number;
}

export function corners(r: Rect): Vec2[] {
  const c = Math.cos(r.yaw);
  const s = Math.sin(r.yaw);
  const hl = r.length / 2;
  const hw = r.width / 2;
  return [
    [hl, hw],
    [-hl, hw],
    [-hl, -hw],
    [hl, -hw],
  ].map(([a, b]) => ({ x: r.x + c * a - s * b, y: r.y + s * a + c * b }));
}

/** The car's footprint when the middle of its rear axle is at `p`. */
export function footprint(p: Pose, body: BodyBox): Rect {
  const mid = (body.front - body.rear) / 2;
  return {
    x: p.x + Math.cos(p.yaw) * mid,
    y: p.y + Math.sin(p.yaw) * mid,
    yaw: p.yaw,
    length: body.rear + body.front,
    width: body.halfWidth * 2,
  };
}

function pointSegment(p: Vec2, a: Vec2, b: Vec2): number {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const k = Math.max(0, Math.min(1, ((p.x - a.x) * dx + (p.y - a.y) * dy) / (dx * dx + dy * dy || 1)));
  return Math.hypot(p.x - (a.x + k * dx), p.y - (a.y + k * dy));
}

function polygonDistance(A: Vec2[], B: Vec2[]): number {
  let best = Infinity;
  for (const [P, Q] of [[A, B], [B, A]] as const) {
    for (const p of P) {
      for (let i = 0; i < Q.length; i++) best = Math.min(best, pointSegment(p, Q[i], Q[(i + 1) % Q.length]));
    }
  }
  return best;
}

/** The distance between two rectangles; negative, by the depth of the overlap, when they overlap. */
export function gap(a: Rect, b: Rect): number {
  const A = corners(a);
  const B = corners(b);
  let depth = Infinity;
  for (const poly of [A, B]) {
    for (let i = 0; i < 2; i++) {
      // two edge normals are enough for a rectangle
      const e = { x: poly[(i + 1) % 4].x - poly[i].x, y: poly[(i + 1) % 4].y - poly[i].y };
      const n = { x: -e.y, y: e.x };
      const proj = (P: Vec2[]) => {
        const d = P.map((q) => (q.x * n.x + q.y * n.y) / Math.hypot(n.x, n.y));
        return [Math.min(...d), Math.max(...d)];
      };
      const [a0, a1] = proj(A);
      const [b0, b1] = proj(B);
      const overlap = Math.min(a1, b1) - Math.max(a0, b0);
      if (overlap <= 0) return polygonDistance(A, B);
      depth = Math.min(depth, overlap);
    }
  }
  return -depth;
}

export interface ParkBay {
  rect: Rect;
  /** the empty one the car goes into */
  target: boolean;
}

export interface ParkNeighbour {
  /** which car stands in the bay: a vehicle slug, shown as its stand-in model */
  slug: string;
  rect: Rect;
  /** nose toward the lane (true) or toward the back of the bay */
  noseOut: boolean;
  /** the bay's place in the row, counted from the empty one (-1 and 1 are its neighbours) */
  bay: number;
}

export interface ParkStage {
  kind: 'perpendicular';
  /** the painted ground: the lane and the row of bays, with room round them */
  asphalt: Rect;
  /** the lane's far edge (the side away from the bays) as a line, y */
  laneEdgeY: number;
  bays: ParkBay[];
  /** the wheel stops at the back of the bays */
  stops: Rect[];
  neighbours: ParkNeighbour[];
  start: Pose;
  parked: Pose;
  /** the middle of the rear axle on the way in, for drawing */
  pathIn: Vec2[];
  /** where the camera and every top view must reach */
  bounds: { min: Vec2; max: Vec2 };
  /** the least gap between the body and a neighbouring car over the whole manoeuvre, m */
  clearance: number;
  /** the widest steering angle, rad */
  maxSteer: number;
  /** the camera's preferred look at the stage */
  camera: { az: number; el: number };
  /** with a search (ParkOptions): when the drive along the row ends and when the bay has been seen, s; else null */
  search: { end: number; found: number } | null;
}

export interface ParkOptions {
  /** radius of the reverse arc at the rear axle's middle, m */
  radius?: number;
  /** the bays' width, m */
  pitch?: number;
  /** half the lane's width, m */
  laneHalf?: number;
  /** the cars in the other four bays, west to east: -2, -1, +1, +2 (length and width in m) */
  neighbours?: { slug: string; length: number; width: number; noseOut: boolean }[];
  /**
   * Park nose first instead of tail first (the Xpeng G9L's nose-in parking, which leaves the boot at the lane): the car
   * turns into a bay that lies ahead of it, on its rear-wheel steering, and reverses out.
   */
  noseIn?: boolean;
  /** the most the rear wheels steer, degrees (the nose-in turn uses it; the G9L publishes 15) */
  rearSteerDeg?: number;
  /**
   * Come along the lane from this far before the stop and find the bay on the way (the SU7's parking assist, as Xiaomi's
   * animation shows it): the car drives past the row at a walking pace, has seen the empty bay by the time its nose is
   * past it, and goes on to the stop, where the reverse begins. Tail first only.
   */
  search?: number;
}

export interface ParkPlan {
  track: Track;
  /** the clock stops here, with the car parked, until the visitor starts the way out */
  stops: number[];
  stage: ParkStage;
}

/** How briskly the car parks: the visitor's "parking speed" setting in the car. */
export type ParkSpeed = 'slow' | 'medium' | 'fast';

export const PARK_MOTION: Record<ParkSpeed, { vmax: number; accel: number; steerRate: number; dwell: number; steerMin: number }> = {
  slow: { vmax: 0.7, accel: 0.45, steerRate: 0.8, dwell: 0.25, steerMin: 0.5 },
  medium: { vmax: 1.0, accel: 0.55, steerRate: 0.9, dwell: 0.25, steerMin: 0.45 },
  fast: { vmax: 1.4, accel: 0.7, steerRate: 1.1, dwell: 0.2, steerMin: 0.4 },
};

/** The parking assist's pace (the SU7's demo, ours): a walking pace along the row, about 7 km/h, and a brisker reverse than the phone's. */
export const ASSIST_MOTION: Motion = { vmax: 1.9, accel: 0.9, steerRate: 1.2, dwell: 0.25, steerMin: 0.4 };

/**
 * The reverse-in and the way out, for a car whose rear axle's middle starts at `start`
 * (heading +x). Throws nothing: a geometry that does not fit comes back with a negative
 * `stage.clearance`, which the caller reports.
 *
 * With `noseIn` the car goes in head first (see ParkOptions): a car with rear-wheel steering turns about a point
 * ahead of its rear axle, so its nose swings into the bay and its tail out, and it needs far less room than a
 * front-steered car's wide forward arc; the planner picks the least turn that keeps 30 cm from the neighbours.
 */
export function planPark(layout: Layout, body: BodyBox, start: Pose, motion: Motion, opts: ParkOptions = {}): ParkPlan {
  const R = opts.radius ?? 5.2;
  const pitch = opts.pitch ?? 2.7;
  const neighbours = opts.neighbours ?? [];

  /** where the bays are, and the two stretches of the manoeuvre, for one way of doing it */
  interface Way {
    noseIn: boolean;
    laneHalf: number;
    mouthY: number;
    parkedY: number;
    bayX: number;
    backY: number;
    inSegs: Segment[];
    outSegs: Segment[];
  }

  // tail first: one reverse arc about a point on the car's right, then straight back; the car stops 25 cm short of the mouth
  const reverseWay = (): Way => {
    const laneHalf = opts.laneHalf ?? 3.3;
    const mouthY = start.y - laneHalf;
    const parkedY = mouthY - 0.25 - body.front;
    const back = start.y - R - parkedY; // the straight run after the arc
    return {
      noseIn: false,
      laneHalf,
      mouthY,
      parkedY,
      bayX: start.x - R,
      backY: parkedY - body.rear - 0.35,
      inSegs: [
        { ...arc(R, 90, 'right', true), label: 'reverse-arc' },
        { kind: 'move', distance: -back, label: 'reverse-in' },
      ],
      outSegs: [
        { kind: 'move', distance: back, label: 'out-straight' },
        { ...arc(R, 90, 'right'), label: 'out-arc' },
      ],
    };
  };

  // head first: a quarter turn about a point to the right of the car and a little ahead of its rear axle (the rear wheels steer
  // against the fronts, the inner one at its limit), then 60 cm straight in; back out the same way
  const noseWay = (cy: number): Way => {
    const rearMax = (opts.rearSteerDeg ?? 15) * (Math.PI / 180);
    const cx = (cy - Math.abs(layout.wheels.RR.y)) * Math.tan(rearMax);
    const forward = 0.6;
    const endX = start.x + cx + cy;
    const endY = start.y - cy + cx;
    const parkedY = endY - forward;
    const mouthY = parkedY + body.rear + 0.25;
    const about = { x: cx, y: -cy };
    return {
      noseIn: true,
      laneHalf: start.y - mouthY,
      mouthY,
      parkedY,
      bayX: endX,
      backY: parkedY - body.front - 0.35,
      inSegs: [
        { kind: 'turn', about, angle: -Math.PI / 2, label: 'nose-arc' },
        { kind: 'move', distance: forward, label: 'nose-in' },
      ],
      outSegs: [
        { kind: 'move', distance: -forward, label: 'out-straight' },
        { kind: 'turn', about, angle: Math.PI / 2, label: 'out-arc' },
      ],
    };
  };

  const assemble = (w: Way): ParkPlan => {
    const { noseIn, laneHalf, mouthY, parkedY, bayX, backY } = w;
    const depth = mouthY - backY;
    const bayCentreY = (mouthY + backY) / 2;
    // a search first drives the lane's length past the bays: the car then begins that far before the stop
    const approach = opts.search ?? 0;
    const searchSegs: Segment[] = approach > 0 ? [{ kind: 'move', distance: approach, label: 'search' }] : [];
    const origin = approach > 0 ? { ...start, x: start.x - approach } : start;
    const track = new Track(layout, [...searchSegs, ...w.inSegs, ...w.outSegs], motion, origin);
    const tIn = track.span(searchSegs.length + 1)?.tEnd ?? track.duration / 2;
    // the bay is seen once the nose has passed its far edge (the side sensors are in the front half of the car)
    let search: ParkStage['search'] = null;
    if (approach > 0) {
      const end = track.span(0)?.tEnd ?? 0;
      let found = end;
      for (let t = 0; t <= end; t += 0.02) {
        const targetX = noseIn ? bayX - pitch * 0.8 : bayX + pitch / 2 + 0.3;
        if (track.sample(t).x + body.front >= targetX) {
          found = t;
          break;
        }
      }
      search = { end, found };
    }

    // the bays: the empty one in the middle, the two with cars, and an empty one at each end
    const bays: ParkBay[] = [];
    for (let k = -2; k <= 2; k++) {
      bays.push({
        rect: { x: bayX + k * pitch, y: bayCentreY, yaw: Math.PI / 2, length: depth, width: pitch },
        target: k === 0,
      });
    }
    // the wheel stops: at the back of the bay, or (nose in) just ahead of the front tyres
    const stopY = noseIn ? parkedY - layout.wheelbase - layout.radius.FL - 0.12 : backY + 0.3;
    const stops: Rect[] = bays.map((b) => ({ x: b.rect.x, y: stopY, yaw: 0, length: Math.min(1.3, pitch * 0.5), width: 0.22 }));

    // the parked cars, each centred in its bay with its tail 35 cm off the back line;
    // the rectangle's heading is the car's (north when its nose is toward the lane)
    const cars: ParkNeighbour[] = [-2, -1, 1, 2].map((k, i) => {
      const n = neighbours[i] ?? { slug: '', length: 4.8, width: 1.9, noseOut: i % 2 === 1 };
      return {
        slug: n.slug,
        noseOut: n.noseOut,
        bay: k,
        rect: {
          x: bayX + k * pitch,
          y: backY + 0.35 + n.length / 2,
          yaw: n.noseOut ? Math.PI / 2 : -Math.PI / 2,
          length: n.length,
          width: n.width,
        },
      };
    });

    // how close the body comes to them over the whole manoeuvre, and how far everything reaches
    let clearance = Infinity;
    const box = () => ({ min: { x: Infinity, y: Infinity }, max: { x: -Infinity, y: -Infinity } });
    // what the camera and the top views must show (the cars and the car's swing), and the whole painted lot
    const action = box();
    const lot = box();
    const reach = (b: ReturnType<typeof box>, r: Rect) => {
      for (const c of corners(r)) {
        b.min.x = Math.min(b.min.x, c.x);
        b.min.y = Math.min(b.min.y, c.y);
        b.max.x = Math.max(b.max.x, c.x);
        b.max.y = Math.max(b.max.y, c.y);
      }
    };
    for (const b of bays) reach(lot, b.rect);
    for (const n of cars) reach(action, n.rect);
    reach(action, bays.find((b) => b.target)!.rect);
    for (let t = 0; t <= track.duration + 1e-6; t += 0.05) {
      const fp = footprint(track.sample(t), body);
      reach(action, fp);
      reach(lot, fp);
      for (const n of cars) clearance = Math.min(clearance, gap(fp, n.rect));
    }
    // the lane's far side, and a margin round the lot
    const northY = start.y + laneHalf;
    lot.max.y = Math.max(lot.max.y, northY);
    action.max.y = Math.max(action.max.y, start.y + body.halfWidth + 0.8);
    const pad = 1.4;
    const asphalt: Rect = {
      x: (lot.min.x + lot.max.x) / 2,
      y: (lot.min.y + lot.max.y) / 2,
      yaw: 0,
      length: lot.max.x - lot.min.x + pad * 2,
      width: lot.max.y - lot.min.y + pad * 2,
    };

    return {
      track,
      stops: [tIn],
      stage: {
        kind: 'perpendicular',
        asphalt,
        laneEdgeY: northY,
        bays,
        stops,
        neighbours: cars,
        start,
        parked: { x: bayX, y: parkedY, yaw: noseIn ? -Math.PI / 2 : Math.PI / 2 },
        pathIn: track.trace(0.12, tIn),
        bounds: action,
        clearance,
        maxSteer: track.stats.maxSteer,
        camera: noseIn ? { az: 118, el: 38 } : { az: 62, el: 38 },
        search,
      },
    };
  };

  if (!opts.noseIn) return assemble(reverseWay());
  let best: ParkPlan | null = null;
  for (let cy = 4.5; cy <= 9.01; cy += 0.25) {
    const plan = assemble(noseWay(cy));
    if (!best || plan.stage.clearance > best.stage.clearance) best = plan;
    if (plan.stage.clearance >= 0.3) return plan;
  }
  return best!;
}
