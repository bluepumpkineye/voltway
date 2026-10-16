/**
 * The street scenes of the chassis demos (docs/tech-showcase.md, section 14): the Denza Z9's crab walk and compass
 * turn, the Xpeng G9L's rear-wheel-steering U-turn. Pure maths on top of kinematics.ts, like park.ts.
 *
 * A scene is a `StreetStage` (the road, its kerbs and footways, the painted lines, the parked cars, the lamps
 * and trees: what TechStreet draws) and a `Track` (the car's motion on it). The floor frame is the kinematics'
 * (x forward, y left, counter-clockwise from above); the car starts with its rear axle's middle at `start`,
 * heading +x. The road runs along x. "South" is the car's right (-y), the side of the kerb it docks at.
 *
 * What is the maker's and what is ours: the manoeuvres' angles and limits are published (the crab walk's 15
 * degrees at the front wheels and 10 at the rear, the compass turn about either front wheel, the G9L's 15 degrees
 * of rear steer and its 5.4 m turning radius); the street, the distances and the speeds are ours.
 */
import { Track, type Layout, type Motion, type Segment, type Vec2 } from './kinematics';
import { corners, footprint, gap, type BodyBox, type ParkStage, type Pose, type Rect } from './park';

const DEG = Math.PI / 180;

export type StreetPropKind = 'lamp' | 'tree' | 'bollard';

export interface StreetProp {
  kind: StreetPropKind;
  x: number;
  y: number;
  /** a lamp's arm reaches this way, rad (floor frame: toward the road) */
  yaw?: number;
}

export interface StreetCar {
  /** a vehicle slug, drawn as its stand-in model */
  slug: string;
  /** its footprint; the heading is the rect's yaw */
  rect: Rect;
}

export interface StreetLine {
  y: number;
  x0: number;
  x1: number;
  dash: boolean;
  /** metres; 0.12 if left out */
  width?: number;
}

export interface StreetStage {
  kind: 'street';
  /** the painted patch of ground, with room round the road; it fades out at its ends */
  ground: Rect;
  /** the carriageway between its kerbs (y), and how far the road reaches along x */
  road: { x0: number; x1: number; y0: number; y1: number };
  /** the footways beyond the kerbs, m wide (0: none) */
  footways: { south: number; north: number };
  lines: StreetLine[];
  /** painted bay boxes */
  bays: Rect[];
  cars: StreetCar[];
  props: StreetProp[];
  /** a wall across the road's end at x (a dead end), or null */
  wall: { x: number } | null;
  start: Pose;
  /** the camera's frame: the viewer's axes (z = -y), the radius to keep in view, the preferred look */
  frame: { cx: number; cz: number; radius: number; camera: { az: number; el: number } };
  /** the least gap between the body and a parked car or a kerb over the whole manoeuvre, m */
  clearance: number;
  /** the widest steering angle any wheel is set to, rad */
  maxSteer: number;
}

/** What the car's screen and the demo's panel read from the run, at any time. */
export interface ChassisReadout {
  /** the fastest wheel's speed, km/h */
  speed: number;
  /** the angles of the wheels (FL, FR, RL, RR), degrees, positive to the left */
  steer: [number, number, number, number];
  /** how far the car has turned since it started, degrees, positive to the left */
  turned: number;
  /** the direction the car travels in against the way it points, degrees, positive to the left; null when it is not on a straight line */
  travel: number | null;
  /** the part of the plan this is: its label ('crab', 'compass', 'u-turn', 'approach', 'leave') or null at rest */
  label: string | null;
  /** the front wheel the car is turning about, held still, while it does */
  held: Pivot | null;
}

export interface StreetRun {
  track: Track;
  stage: StreetStage;
  stops: number[];
  readout: (t: number) => ChassisReadout;
  /** the camera's frame, for the director */
  frame: StreetStage['frame'];
  /** what the manoeuvre needed, for the panel: the width of street it fits in, m, and the path it took */
  facts: { roadWidth: number; shift?: number; turn?: number; gap?: number; pivot?: Pivot };
}

/** A car standing in the scene: a stand-in of another modelled car (length and width in m). */
export interface StreetNeighbour {
  slug: string;
  length: number;
  width: number;
}

const rectOf = (x0: number, x1: number, y0: number, y1: number): Rect => ({
  x: (x0 + x1) / 2,
  y: (y0 + y1) / 2,
  yaw: 0,
  length: x1 - x0,
  width: y1 - y0,
});

/** The car's wheels' angles and speed at time t, as the screens read them. */
function readoutOf(track: Track, plan: Segment[], labels: (string | null)[], layout?: Layout): (t: number) => ChassisReadout {
  // which front wheel a turn is held about, per segment
  const held = plan.map((seg) => {
    if (!layout || seg.kind !== 'turn' || !seg.steer) return null;
    for (const c of ['FL', 'FR'] as const) {
      if (Math.hypot(seg.about.x - layout.wheels[c].x, seg.about.y - layout.wheels[c].y) < 1e-6) return c;
    }
    return null;
  });
  return (t) => {
    const s = track.sample(t);
    const seg = plan[s.segment];
    const moving = s.phase === 'move';
    return {
      speed: s.speed * 3.6,
      steer: s.steer.map((a) => a / DEG) as ChassisReadout['steer'],
      turned: s.yaw / DEG,
      travel: moving && seg?.kind === 'move' ? (seg.angle ?? 0) / DEG : null,
      label: labels[s.segment] ?? null,
      held: held[s.segment] ?? null,
    };
  };
}

/** The camera's frame for a box of floor that must stay in view (viewer axes: z = -y). */
function frameOf(box: { x0: number; x1: number; y0: number; y1: number }, camera: { az: number; el: number }): StreetStage['frame'] {
  return {
    cx: (box.x0 + box.x1) / 2,
    cz: -((box.y0 + box.y1) / 2),
    radius: Math.hypot((box.x1 - box.x0) / 2, (box.y1 - box.y0) / 2) + 0.6,
    camera,
  };
}

/** The extent of everything the body sweeps over a track, and the least gap to the given rectangles. */
function sweep(track: Track, body: BodyBox, others: Rect[]) {
  const min = { x: Infinity, y: Infinity };
  const max = { x: -Infinity, y: -Infinity };
  let clearance = Infinity;
  for (let t = 0; t <= track.duration + 1e-6; t += 0.04) {
    const fp = footprint(track.sample(t), body);
    for (const c of corners(fp)) {
      min.x = Math.min(min.x, c.x);
      min.y = Math.min(min.y, c.y);
      max.x = Math.max(max.x, c.x);
      max.y = Math.max(max.y, c.y);
    }
    for (const o of others) clearance = Math.min(clearance, gap(fp, o));
  }
  return { min, max, clearance };
}

/** A lamp or a tree every `every` metres from x0 to x1 along y. */
function along(kind: StreetPropKind, x0: number, x1: number, every: number, y: number, yaw?: number, phase = 0): StreetProp[] {
  const out: StreetProp[] = [];
  for (let x = x0 + phase; x <= x1; x += every) out.push({ kind, x, y, yaw });
  return out;
}

/** Cars placed end to end along a kerb from x going toward `dir` (+1 east, -1 west), `gapM` apart, their right side `off` from the kerb line. */
function row(
  cars: StreetNeighbour[],
  x: number,
  dir: 1 | -1,
  kerbY: number,
  off: number,
  facing: 0 | 1,
  gapM = 0.6,
  fromKerb: 'south' | 'north' = 'south',
): StreetCar[] {
  const out: StreetCar[] = [];
  let edge = x;
  for (const c of cars) {
    const cx = edge + dir * (c.length / 2);
    const cy = fromKerb === 'south' ? kerbY + off + c.width / 2 : kerbY - off - c.width / 2;
    out.push({ slug: c.slug, rect: { x: cx, y: cy, yaw: facing ? Math.PI : 0, length: c.length, width: c.width } });
    edge += dir * (c.length + gapM);
  }
  return out;
}

/**
 * What stands behind a parking lot's bays (the RX's park demo, the G9L's nose-in parking): a raised planted strip beyond
 * the wheel stops with a lamp post and a tree here and there, and a row of buildings behind it. Drawn by the street's own
 * pieces (TechStreet.tsx), so a lot and a street are one place; the lot's asphalt, bays and cars stay TechStage's.
 */
export function dressLot(lot: ParkStage): StreetStage {
  const a = lot.asphalt;
  const x0 = a.x - a.length / 2 - 2;
  const x1 = a.x + a.length / 2 + 2;
  const target = lot.bays.find((b) => b.target) ?? lot.bays[0];
  const backY = target.rect.y - target.rect.length / 2;
  const y1 = lot.laneEdgeY;
  const foot = 3.0;
  const pitch = target.rect.width;
  const props: StreetProp[] = [
    ...along('lamp', x0 + 3, x1 - 3, 11, backY - 0.7, Math.PI / 2, 0),
    // a tree on the line between two bays, every second one
    ...along('tree', x0 + 2, x1 - 2, pitch * 2, backY - 1.8, undefined, (((target.rect.x - pitch / 2 - (x0 + 2)) % (pitch * 2)) + pitch * 2) % (pitch * 2)),
  ];
  return {
    kind: 'street',
    ground: rectOf(x0, x1, backY - foot, y1),
    road: { x0, x1, y0: backY, y1 },
    footways: { south: foot, north: 0 },
    lines: [],
    bays: [],
    cars: [],
    props,
    wall: null,
    start: lot.start,
    frame: frameOf({ x0, x1, y0: backY, y1 }, lot.camera),
    clearance: lot.clearance,
    maxSteer: lot.maxSteer,
  };
}

// ------------------------------------------------------------------------------------------------ crab walk

export interface CrabOptions {
  /** the crab angle: the direction the car travels in against the way it points, degrees (the brochure's maximum is 15) */
  angleDeg?: number;
  /** the most the rear wheels steer, degrees (published: 10 each way) */
  rearLimitDeg?: number;
  /** how far the car moves sideways, m */
  shift?: number;
  /** the cars parked along the kerb, nearest first on each side of the empty stretch */
  neighbours: StreetNeighbour[];
}

/** The crab walk's pace: a gentle 7 km/h, well inside the 20 km/h the mode allows (km77). */
export const CRAB_MOTION: Motion = { vmax: 2.0, accel: 0.8, steerRate: 0.9, dwell: 0.3, steerMin: 0.7 };

/**
 * The crab walk: the car stands in the road beside an empty stretch of kerb, turns all four wheels the same way, and
 * slides to the kerb without turning its body, ending parallel to it, a hand's breadth from the stone. The front
 * wheels take the crab angle, the rear ones their own limit (ten degrees), and the rolling follows from that.
 */
export function planCrab(layout: Layout, body: BodyBox, start: Pose, opts: CrabOptions): StreetRun {
  const beta = (opts.angleDeg ?? 15) * DEG;
  const rear = Math.min(beta, (opts.rearLimitDeg ?? 10) * DEG);
  const shift = opts.shift ?? 2.25;
  const hw = body.halfWidth;
  const dx = shift / Math.tan(beta);

  // the right-hand kerb, so that the car ends 25 cm off it; the parking lane is 2.4 m, the car starts a little outside it
  const kerbY = start.y - shift - hw - 0.25;
  const bayW = 2.4;
  const laneW = 3.2;
  const northY = kerbY + bayW + 2 * laneW;
  const bayX0 = start.x - 2.0;
  const bayX1 = start.x + dx + body.front + 0.9;

  const labels = ['crab'];
  const plan: Segment[] = [
    {
      kind: 'move',
      distance: shift / Math.sin(beta),
      angle: -beta,
      steer: [-beta, -beta, -rear, -rear],
      label: 'crab',
    },
  ];
  const track = new Track(layout, plan, CRAB_MOTION, start);

  const kids = opts.neighbours.length ? opts.neighbours : [{ slug: '', length: 4.8, width: 1.9 }];
  const pick = (i: number) => kids[i % kids.length];
  const behind = row([pick(0), pick(1)], bayX0, -1, kerbY, 0.25, 0);
  const ahead = row([pick(2), pick(3)], bayX1, 1, kerbY, 0.25, 0);
  // the other side of the street: a few cars facing the other way, well away from the manoeuvre
  const opposite = row(
    [pick(1), pick(0), pick(3)],
    start.x - 11,
    1,
    northY,
    0.25,
    1,
    4.5 + 1.2,
    'north',
  ).filter((c) => c.rect.x < bayX1 + 14);
  const cars = [...behind, ...ahead].filter((c) => c.slug);
  const decor = opposite.filter((c) => c.slug);

  const swept = sweep(track, body, cars.map((c) => c.rect));
  const kerbGap = swept.min.y - kerbY;
  const x0 = Math.min(...behind.map((c) => c.rect.x - c.rect.length / 2), bayX0 - 6) - 5;
  const x1 = Math.max(...ahead.map((c) => c.rect.x + c.rect.length / 2), bayX1 + 6) + 5;
  const foot = 3.2;

  const stage: StreetStage = {
    kind: 'street',
    ground: rectOf(x0, x1, kerbY - foot - 0.6, northY + foot + 0.6),
    road: { x0, x1, y0: kerbY, y1: northY },
    footways: { south: foot, north: foot },
    lines: [
      // the parking lane's edge, and the centre of the street
      { y: kerbY + bayW, x0: x0 + 1.5, x1: x1 - 1.5, dash: false },
      { y: kerbY + bayW + laneW, x0: x0 + 1.5, x1: x1 - 1.5, dash: true },
    ],
    // the stretch of kerb the car goes to is marked as a bay of its own
    bays: [rectOf(bayX0 + 0.3, bayX1 - 0.3, kerbY, kerbY + bayW)],
    cars: [...cars, ...decor],
    props: [
      // the trees stand on the far footway, behind the car as the camera sees it; the near one has lamps only
      ...along('lamp', x0 + 4, x1 - 3, 13, kerbY - 0.55, Math.PI / 2, 0),
      ...along('tree', x0 + 8, x1 - 3, 9.5, kerbY - 1.9),
    ],
    wall: null,
    start,
    frame: frameOf(
      { x0: start.x - body.rear - 1, x1: start.x + dx + body.front + 1, y0: kerbY - 0.4, y1: start.y + hw + 0.6 },
      { az: 62, el: 34 },
    ),
    clearance: Math.min(swept.clearance, kerbGap),
    maxSteer: track.stats.maxSteer,
  };
  return {
    track,
    stage,
    stops: [],
    readout: readoutOf(track, plan, labels, layout),
    frame: stage.frame,
    facts: { roadWidth: northY - kerbY, shift },
  };
}

// ---------------------------------------------------------------------------------------------- compass turn

export type Pivot = 'FL' | 'FR';

export interface CompassOptions {
  /** which front wheel the car turns about */
  pivot: Pivot;
  /** how far it turns, degrees (the maker says any angle up to 360) */
  angleDeg: number;
  /** how far the rear wheels splay, degrees (published: they steer 10 either way) */
  splayDeg?: number;
  neighbours: StreetNeighbour[];
}

/** The compass turn's pace: the rear wheels travel about 3.5 m for each radian, and the body goes at a walk. */
export const COMPASS_MOTION: Motion = { vmax: 1.7, accel: 0.9, steerRate: 0.9, dwell: 0.35, steerMin: 0.7 };

/**
 * The compass turn: the car drives up a narrow dead-end street, locks one front wheel and turns about it, the rear wheels
 * splayed out and driven in opposite directions, then drives out. The street is as wide as the turn needs, plus a
 * margin: the manoeuvre is measured on the model, not assumed. Only the pivot wheel is held; the other front wheel rolls
 * straight, the rear wheels roll the part of their path that lies along them and scrub the rest.
 */
export function planCompass(layout: Layout, body: BodyBox, start: Pose, opts: CompassOptions): StreetRun {
  const splay = (opts.splayDeg ?? 10) * DEG;
  const sign = opts.pivot === 'FL' ? 1 : -1;
  const angle = sign * opts.angleDeg * DEG;
  const approach = 4.5;
  const leave = 7.0;

  const labels = ['approach', 'compass', 'leave'];
  const plan: Segment[] = [
    { kind: 'move', distance: approach, label: 'approach' },
    { kind: 'turn', about: layout.wheels[opts.pivot], angle, steer: [0, 0, splay, -splay], label: 'compass' },
    { kind: 'move', distance: leave, label: 'leave' },
  ];
  const track = new Track(layout, plan, COMPASS_MOTION, start);
  const swept = sweep(track, body, []);

  // the street is as wide as the sweep needs, with 40 cm each side; the dead end is 60 cm past the farthest the body reaches
  const margin = 0.4;
  const y0 = swept.min.y - margin;
  const y1 = swept.max.y + margin;
  const wallX = swept.max.x + 0.7;
  const x0 = swept.min.x - 10;
  const x1 = wallX + 4;
  const foot = 3.0;
  const kids = opts.neighbours.length ? opts.neighbours : [{ slug: '', length: 4.8, width: 1.9 }];
  const pick = (i: number) => kids[i % kids.length];
  // parked cars along both kerbs, back where the street is not being used, and out of the car's way on its leaving line
  const cars = [
    ...row([pick(0), pick(1)], swept.min.x - 2.5, -1, y0, 0.25, 0),
    ...row([pick(2), pick(0)], swept.min.x - 2.5, -1, y1, 0.25, 1, 0.6, 'north'),
  ].filter((c) => c.slug);

  const stage: StreetStage = {
    kind: 'street',
    ground: rectOf(x0, x1, y0 - foot - 0.6, y1 + foot + 0.6),
    road: { x0, x1, y0, y1 },
    footways: { south: foot, north: foot },
    lines: [],
    bays: [],
    cars,
    props: [
      ...along('lamp', x0 + 4, wallX - 2, 12, y0 - 0.55, Math.PI / 2),
      ...along('tree', x0 + 8, wallX - 3, 9, y0 - 1.9),
      // bollards across the dead end
      ...[0.18, 0.5, 0.82].map((k) => ({ kind: 'bollard' as const, x: wallX - 0.45, y: y0 + k * (y1 - y0) })),
    ],
    wall: { x: wallX },
    start,
    frame: frameOf({ x0: swept.min.x - 1.8, x1: wallX + 1.2, y0: y0 - 0.9, y1: y1 + 0.9 }, { az: 122, el: 38 }),
    clearance: margin,
    maxSteer: track.stats.maxSteer,
  };
  return {
    track,
    stage,
    stops: [],
    readout: readoutOf(track, plan, labels, layout),
    frame: stage.frame,
    facts: { roadWidth: y1 - y0, turn: opts.angleDeg },
  };
}

// -------------------------------------------------------------------------------------- e³ parking

export interface PivotParkOptions {
  neighbours: StreetNeighbour[];
  /** how far the car is angled into the gap before it pivots, degrees */
  angleDeg?: number;
  /** how far the rear wheels splay, degrees (published: 10) */
  splayDeg?: number;
}

/** e³ parking's pace: the arc in at a walking pace, then the pivot as slowly as the compass turn. */
export const PIVOT_PARK_MOTION: Motion = { vmax: 1.3, accel: 0.7, steerRate: 0.9, dwell: 0.4, steerMin: 0.7 };

/**
 * e³ parking: parallel parking into a gap hardly longer than the car, by the compass turn. The car pulls its nose into the
 * gap, angled toward the kerb, and stops (the driver pivots about a front wheel on the screen); then the left front wheel is
 * held and the car turns about it, the rear wheels splayed and driven against each other, until it lies parallel to the kerb
 * and the tail has swung into the gap. The steps are the maker's (The Autopian's description of the Z9 GT); the gap, the
 * angle and the pace are ours. The pivot swings the tail 39 cm back of where the car ends and the nose hardly at all, so the
 * gap leaves 70 cm behind the car and 35 cm ahead of it (a gap a metre longer than the car, which keeps 30 cm from both
 * parked cars all the way), and the body comes within 19 cm of the kerb stone as it swings, ending 40 cm off it.
 */
export function planPivotPark(layout: Layout, body: BodyBox, start: Pose, opts: PivotParkOptions): StreetRun {
  const alpha = (opts.angleDeg ?? 30) * DEG;
  const splay = (opts.splayDeg ?? 10) * DEG;
  const hw = body.halfWidth;
  const kids = opts.neighbours.length ? opts.neighbours : [{ slug: '', length: 4.8, width: 1.9 }];
  const pick = (i: number) => kids[i % kids.length];
  const labels = ['pull-in', 'pivot'];

  // a long, gentle arc in (a 12 m radius: the front wheels turn about 15 degrees), then the pivot about the left front wheel
  const R1 = 12;
  const plan: Segment[] = [
    { kind: 'turn', about: { x: 0, y: -R1 }, angle: -alpha, label: 'pull-in' },
    { kind: 'turn', about: layout.wheels.FL, angle: alpha, steer: [0, 0, splay, -splay], label: 'pivot' },
  ];
  const track = new Track(layout, plan, PIVOT_PARK_MOTION, start);
  const end = track.sample(track.duration);
  // the car ends parallel to the kerb, 40 cm off it; the gap is the car's length with 70 cm behind it and 35 ahead
  const kerbY = end.y - hw - 0.4;
  const gapX0 = end.x - body.rear - 0.7;
  const gapX1 = end.x + body.front + 0.35;
  const behind = row([pick(0), pick(1)], gapX0, -1, kerbY, 0.25, 0);
  const ahead = row([pick(2), pick(3)], gapX1, 1, kerbY, 0.25, 0);
  const cars = [...behind, ...ahead].filter((c) => c.slug);
  const swept = sweep(track, body, cars.map((c) => c.rect));
  const clearance = Math.min(swept.clearance, swept.min.y - kerbY);
  const bayW = 2.4;
  const northY = kerbY + bayW + 2 * 3.2;
  const x0 = Math.min(...cars.map((c) => c.rect.x - c.rect.length / 2), gapX0 - 8) - 6;
  const x1 = Math.max(...cars.map((c) => c.rect.x + c.rect.length / 2), gapX1 + 8) + 6;
  const foot = 3.2;
  const decor = row([pick(1), pick(0), pick(3)], start.x - 10, 1, northY, 0.25, 1, 5.7, 'north').filter((c) => c.slug && c.rect.x < gapX1 + 12);

  const stage: StreetStage = {
    kind: 'street',
    ground: rectOf(x0, x1, kerbY - foot - 0.6, northY + foot + 0.6),
    road: { x0, x1, y0: kerbY, y1: northY },
    footways: { south: foot, north: foot },
    lines: [
      { y: kerbY + bayW, x0: x0 + 1.5, x1: x1 - 1.5, dash: false },
      { y: kerbY + bayW + 3.2, x0: x0 + 1.5, x1: x1 - 1.5, dash: true },
    ],
    bays: [rectOf(gapX0 + 0.15, gapX1 - 0.15, kerbY, kerbY + bayW)],
    cars: [...cars, ...decor],
    props: [
      ...along('lamp', x0 + 4, x1 - 3, 13, kerbY - 0.55, Math.PI / 2, 0),
      ...along('tree', x0 + 8, x1 - 3, 9.5, kerbY - 1.9),
    ],
    wall: null,
    start,
    frame: frameOf({ x0: gapX0 - 2.5, x1: gapX1 + 2.5, y0: kerbY - 0.4, y1: Math.max(swept.max.y, start.y + hw) + 0.6 }, { az: 62, el: 36 }),
    clearance,
    maxSteer: track.stats.maxSteer,
  };
  return {
    track,
    stage,
    // the car stops with its nose in the gap, and waits for the driver to start the pivot
    stops: [track.span(0)?.tEnd ?? track.duration / 2],
    readout: readoutOf(track, plan, labels, layout),
    frame: stage.frame,
    facts: { roadWidth: northY - kerbY, turn: alpha / DEG, gap: gapX1 - gapX0, pivot: 'FL' },
  };
}

// ------------------------------------------------------------------------------------- rear-steer U-turn

export interface UTurnOptions {
  /** the published turning radius, m: here the circle the outer front wheel follows */
  radius: number;
  /** the most the rear wheels steer, degrees (published: 15 either way) */
  rearMaxDeg: number;
  neighbours: StreetNeighbour[];
}

export const UTURN_MOTION: Motion = { vmax: 2.2, accel: 0.9, steerRate: 0.8, dwell: 0.3, steerMin: 0.8 };

/**
 * The centre a car turns about when its outer front wheel follows a circle of this radius and its inner rear wheel
 * is set at the rear steering's limit, opposite to the fronts: the centre's place (x ahead of the rear axle, y to
 * the left) in the car's frame, for a left turn. Solved by bisection: the outer wheel's distance grows with y.
 */
export function rearSteerCentre(layout: Layout, radius: number, rearMax: number): Vec2 {
  const { FR, RL } = layout.wheels;
  const tan = Math.tan(rearMax);
  const at = (cy: number) => {
    const cx = (cy - RL.y) * tan;
    return { cx, d: Math.hypot(FR.x - cx, cy - FR.y) };
  };
  let lo = 0.5;
  let hi = 40;
  for (let i = 0; i < 60; i++) {
    const mid = (lo + hi) / 2;
    if (at(mid).d < radius) lo = mid;
    else hi = mid;
  }
  const cy = (lo + hi) / 2;
  return { x: at(cy).cx, y: cy };
}

/**
 * The U-turn of a car with rear-wheel steering: it drives up in the right-hand lane, turns left through a half circle
 * with the rear wheels steering against the fronts (so the turn is tighter than the front wheels alone would make it),
 * and drives off the other way in the opposite lane. The road is as wide as the sweep needs plus a margin.
 */
export function planUTurn(layout: Layout, body: BodyBox, start: Pose, opts: UTurnOptions): StreetRun {
  const centre = rearSteerCentre(layout, opts.radius, opts.rearMaxDeg * DEG);
  const approach = 4.0;
  const leave = 8.0;
  const labels = ['approach', 'u-turn', 'leave'];
  const plan: Segment[] = [
    { kind: 'move', distance: approach, label: 'approach' },
    { kind: 'turn', about: centre, angle: Math.PI, label: 'u-turn' },
    { kind: 'move', distance: leave, label: 'leave' },
  ];
  const track = new Track(layout, plan, UTURN_MOTION, start);
  const swept = sweep(track, body, []);

  const margin = 0.9;
  const y0 = swept.min.y - margin;
  const y1 = swept.max.y + margin;
  const x0 = swept.min.x - 12;
  const x1 = swept.max.x + 12;
  const foot = 3.2;
  const kids = opts.neighbours.length ? opts.neighbours : [{ slug: '', length: 4.8, width: 1.9 }];
  const pick = (i: number) => kids[i % kids.length];
  // parked cars along both kerbs at the two ends, clear of the sweep
  const cars = [
    ...row([pick(0), pick(1)], swept.min.x - 1.5, -1, y0, 0.25, 0),
    ...row([pick(2), pick(0)], swept.max.x + 1.5, 1, y1, 0.25, 1, 0.6, 'north'),
    ...row([pick(1)], swept.max.x + 1.5, 1, y0, 0.25, 0),
    ...row([pick(3), pick(2)], swept.min.x - 1.5, -1, y1, 0.25, 1, 0.6, 'north'),
  ].filter((c) => c.slug);

  const stage: StreetStage = {
    kind: 'street',
    ground: rectOf(x0, x1, y0 - foot - 0.6, y1 + foot + 0.6),
    road: { x0, x1, y0, y1 },
    footways: { south: foot, north: foot },
    lines: [{ y: (y0 + y1) / 2, x0: x0 + 1.5, x1: x1 - 1.5, dash: true }],
    bays: [],
    cars,
    props: [
      ...along('lamp', x0 + 3, x1 - 3, 13, y0 - 0.55, Math.PI / 2),
      ...along('tree', x0 + 7, x1 - 3, 9.5, y0 - 1.9),
    ],
    wall: null,
    start,
    frame: frameOf({ x0: swept.min.x - 0.4, x1: swept.max.x + 0.4, y0: y0 - 0.3, y1: y1 + 0.3 }, { az: 64, el: 40 }),
    clearance: margin,
    maxSteer: track.stats.maxSteer,
  };
  return {
    track,
    stage,
    stops: [],
    readout: readoutOf(track, plan, labels, layout),
    frame: stage.frame,
    facts: { roadWidth: y1 - y0, turn: 180 },
  };
}
