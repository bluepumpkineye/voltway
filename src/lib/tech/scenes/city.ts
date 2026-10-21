import type { ActorDef, ActorNow, Command, SceneFactory, World } from '../drive';

/**
 * Autonomous Drive on a city street, "ghost probe and crossing" (the XPeng G9L): the car drives a two-lane street at 50 km/h
 * between parked cars; someone steps out from between two of them into its lane, and it brakes hard and waits for them to
 * clear it; further on, a car ahead stops at a zebra crossing for people on it, the car stops behind it, waits until the
 * crossing is clear and moves off.
 *
 * What it stands for: XPeng's G9L release describes its NGP test rides in Paris, with roundabouts, narrow streets, motorcycle
 * traffic, pedestrian crossings and complex right-of-way situations, and automatic emergency braking up to 150 km/h; Autohome's
 * table lists XNGP with city and expressway roads, assisted lane change, traffic-light recognition and hands-off detection.
 * The whole scenario (the street, who is where, their speeds, when they cross, what the car does and when) is ours: no maker
 * publishes one. No value imports.
 */

/** the set speed, m/s (50 km/h, the usual limit in a built-up street) */
const SET = 50 / 3.6;
/** a lane's width in a city street, m */
const LANE = 3.3;
/** across the street, m left of the car's lane: the kerbs, the footways, the line down the middle, the oncoming lane */
export const STREET = {
  nearKerb: -4.15,
  farKerb: 8.25,
  footway: 2.8,
  centre: 4.95,
  left: LANE,
  oncoming: 6.6,
  /** the cars parked along the near kerb */
  parked: -2.95,
} as const;
/** where the zebra crossing is, m along the street from the car's start (the middle of the stripes), and its length along the street */
export const CROSSING = { x: 115, length: 4 } as const;
/** the stop lines sit this far before the stripes, m */
const LINE_GAP = 1.2;
/** the street's repeating things (lamps, trees, buildings, the dashes) repeat every this many metres: the viewer rolls them by it */
const PERIOD = 24;

const END = 22;

/** when the person steps out from between the parked cars, and where */
const PROBE = { at: 1.5, x: 50, pace: 2.9 };

const STATES = ['cruising', 'following', 'yielding', 'waiting', 'moving-off', 'probe', 'probe-wait', 'clear'];
const MESSAGES = [
  'Driving the street at 50 km/h',
  'Following the car ahead',
  'People on the crossing: slowing to stop for them',
  'Waiting: the crossing is not clear',
  'Crossing clear: moving off',
  'Someone steps out between parked cars: braking hard',
  'Waiting for them to clear the lane',
  'The lane is clear again: back to the street speed',
];

/** what a car does on its own: holds a speed, brakes to a stop at `xStop` (a line), waits until `tGo`, goes again (all magnitudes; `dir` gives the sign) */
function stopAndGo(opts: { v0: number; xFrom: number; xStop: number; aDec: number; tGo: number; aAcc: number; vEnd: number; dir: 1 | -1 }) {
  const { v0, xFrom, xStop, aDec, tGo, aAcc, vEnd, dir } = opts;
  // it cruises until the braking distance is all that is left
  const brake = (v0 * v0) / (2 * aDec);
  const tb = Math.max(0, (Math.abs(xStop - xFrom) - brake) / v0);
  const tStop = tb + v0 / aDec;
  return (t: number) => {
    let v: number;
    if (t <= tb) v = v0;
    else if (t < tStop) v = v0 - aDec * (t - tb);
    else if (t < tGo) v = 0;
    else v = Math.min(vEnd, aAcc * (t - tGo));
    return v * dir;
  };
}

/** a person walking across the street: standing at `y0` until `from`, then at `pace` m/s to `y1`, where they stop */
function walker(y0: number, y1: number, from: number, pace: number) {
  const sign = Math.sign(y1 - y0);
  return (t: number) => y0 + sign * Math.min(Math.abs(y1 - y0), Math.max(0, t - from) * pace);
}

export const cityScene: SceneFactory = (ctx) => {
  const { cars, mid } = ctx;
  const pick = (i: number) => cars[i % Math.max(cars.length, 1)] ?? { slug: '', length: 4.8, width: 1.85 };
  const lineX = CROSSING.x - CROSSING.length / 2 - LINE_GAP;
  const lineFar = CROSSING.x + CROSSING.length / 2 + LINE_GAP;

  const car = (id: string, i: number, x: number, speed: (t: number) => number, y: number, facing: 1 | -1 = 1): ActorDef => {
    const size = pick(i);
    return { id, kind: 'car', slug: size.slug, length: size.length, width: size.width - 0.08, gap: x - mid, speed, y: () => y, facing };
  };
  const person = (id: string, x: number, y: (t: number) => number, unseenUntil?: number): ActorDef => ({
    id,
    kind: 'person',
    slug: '',
    length: 0.5,
    width: 0.55,
    gap: x - mid,
    speed: () => 0,
    y,
    unseenUntil,
  });

  // the car ahead in the car's lane and the one in the left lane: both stop at the line for the people on the crossing, and go
  // when it is clear. The one in the lane beside stops a little short of the line, as a second car would.
  const leadLen = pick(0).length;
  const leadX0 = mid + 40;
  const lead = car(
    'lead',
    0,
    leadX0,
    stopAndGo({ v0: 46 / 3.6, xFrom: leadX0, xStop: lineX - 0.3 - leadLen / 2, aDec: 2.2, tGo: 15.8, aAcc: 1.8, vEnd: 40 / 3.6, dir: 1 }),
    0,
  );
  const leftLen = pick(1).length;
  const leftX0 = mid + 30;
  const beside = car(
    'beside',
    1,
    leftX0,
    stopAndGo({ v0: 46 / 3.6, xFrom: leftX0, xStop: lineX - 4.5 - leftLen / 2, aDec: 2.0, tGo: 15.0, aAcc: 1.8, vEnd: 42 / 3.6, dir: 1 }),
    STREET.left,
  );
  // one coming the other way, which stops at its own line on the far side
  const oncLen = pick(2).length;
  const oncX0 = 244;
  const oncoming = car(
    'oncoming',
    2,
    oncX0,
    stopAndGo({ v0: 50 / 3.6, xFrom: oncX0, xStop: lineFar + 0.3 + oncLen / 2, aDec: 2.2, tGo: 17.2, aAcc: 1.8, vEnd: 40 / 3.6, dir: -1 }),
    STREET.oncoming,
    -1,
  );

  // the cars along the near kerb, with the gap between two of them where the person steps out
  const parked = [12, PROBE.x - 5, PROBE.x + 5, 74, 92, 140, 163, 190].map((x, i) => car(`parked-${i}`, 3 + i, x, () => 0, STREET.parked));

  // the people on the crossing: two from the car's side, one from the far side, and one who hurries to catch them up
  const near = STREET.nearKerb - 0.3;
  const far = STREET.farKerb + 0.35;
  const people = [
    person('person-1', CROSSING.x - 1.3, walker(near, far, 2.6, 1.5)),
    person('person-2', CROSSING.x + 0.1, walker(near, far, 3.2, 1.45)),
    person('person-3', CROSSING.x - 0.5, walker(far, near, 4.2, 1.45)),
    person('person-4', CROSSING.x + 1.0, walker(near, far, 9.0, 1.7)),
  ];
  // the one who steps out of the gap from the footway behind the parked cars, and runs across: the sensors do not see them until
  // they are between the cars
  const probe = person('probe', PROBE.x, walker(STREET.nearKerb - 0.9, far, PROBE.at, PROBE.pace), PROBE.at + 0.4);

  const actors: ActorDef[] = [lead, beside, oncoming, ...parked, ...people, probe];
  const J = Object.fromEntries(actors.map((a, j) => [a.id, j]));
  const peopleIds = people.map((p) => p.id);

  /** is someone on, or about to step onto, the crossing in the half of it the car uses? */
  const onCrossing = (w: World): ActorNow[] =>
    peopleIds
      .map((id) => w.actors[J[id]])
      .filter((p) => {
        // in the car's half of the street, or just stepped off the near kerb (not someone going away to it along the far side of the lane)
        const onRoad = (p.y > -2.2 && p.y < STREET.centre + 0.6) || (p.y > STREET.nearKerb - 0.25 && p.y <= -2.2 && p.vy > 0.3);
        // someone coming from the far side who will be in the car's half within a few seconds
        const coming = p.y >= STREET.centre + 0.6 && p.y < STREET.farKerb + 0.2 && p.vy < -0.3 && p.y - STREET.centre < 4.2;
        return onRoad || coming;
      });

  /** someone stepping into the car's path from the side, within braking distance: the person who steps out */
  const stepsOut = (w: World): ActorNow | null => {
    const p = w.actors[J.probe];
    if (w.t < PROBE.at + 0.4) return null;
    const dy = p.y - w.e;
    const ahead = p.x - w.nose;
    const toward = Math.sign(dy) * p.vy < -0.4 && Math.abs(dy) < 4.6;
    const inLane = Math.abs(dy) < 1.9 && Math.abs(p.vy) > 0.4;
    return ahead > 0 && ahead < 45 && (toward || inLane) ? p : null;
  };

  let phase = 1;
  let clearSince = -1;
  let probeSeen = false;
  let probeDone = -1;

  const command = (stopAt: number | null, warn: string[]): Command => ({
    // a person stepping into the lane: no more speed, and the stop below does the rest
    vSet: phase === 5 || phase === 6 ? 0 : SET,
    aMax: 1.9,
    stopAt,
    state: STATES[phase],
    message: MESSAGES[phase],
    note: phase === 2 || phase === 3 ? 'Giving way on the zebra crossing' : phase === 5 || phase === 6 ? 'Not seen until they stepped out' : null,
    indicator: 0,
    lane: null,
    showLead: phase <= 1,
    warn,
  });

  return {
    id: 'city',
    duration: END,
    v0: SET,
    actors,
    road: {
      humps: [],
      from: -140,
      to: 140,
      width: STREET.farKerb - STREET.nearKerb,
      city: {
        nearKerb: STREET.nearKerb,
        farKerb: STREET.farKerb,
        footway: STREET.footway,
        period: PERIOD,
        // the line along the parking strip, the dashes between the car's lane and the one beside it, and the double yellow
        // line down the middle
        lines: [
          { y: -LANE / 2, dash: false, color: 'white' },
          { y: LANE / 2, dash: true, color: 'white' },
          { y: STREET.centre - 0.09, dash: false, color: 'yellow' },
          { y: STREET.centre + 0.09, dash: false, color: 'yellow' },
        ],
        crossings: [{ x: CROSSING.x, length: CROSSING.length }],
        stopLines: [
          { x: lineX, y0: STREET.parked + 1.3, y1: STREET.centre },
          { x: lineFar, y0: STREET.centre, y1: STREET.farKerb },
        ],
      },
    },
    reach: { ahead: 48, behind: 26 },
    follow: { d0: 6, T: 1.2, stopGap: 3.8 },
    jerkUp: 4.5,
    initial: command(null, []),
    decide: (w) => {
      const crossers = onCrossing(w);
      const probeNow = stepsOut(w);
      const warn: string[] = [];
      let stopAt: number | null = null;

      if (probeNow) {
        // someone steps out of a gap between parked cars: stop short of where they are
        probeSeen = true;
        stopAt = probeNow.x - 4.8;
        warn.push('probe');
        phase = w.v < 0.3 ? 6 : 5;
        clearSince = -1;
      } else if (probeSeen && probeDone < 0) {
        // they are out of the lane and moving away: the car goes on
        probeDone = w.t;
        phase = 7;
      } else if (crossers.length && w.nose < lineX + 0.2) {
        // the car plans its stop at the line from afar; it says it is giving way once it is coming up to the crossing
        stopAt = lineX - 0.2;
        warn.push(...crossers.map((c) => c.def.id));
        clearSince = -1;
        const toLine = lineX - w.nose;
        if (toLine < 48) phase = w.v < 0.25 && toLine < 14 ? 3 : 2;
        else phase = w.lead && w.lead.gap < 45 ? 1 : 0;
      } else if (phase === 2 || phase === 3 || phase === 4) {
        // the crossing has just cleared: a moment, then the car moves off behind the one ahead
        if (clearSince < 0) clearSince = w.t;
        phase = w.t - clearSince < 2.2 ? 4 : w.lead ? 1 : 0;
      } else if (phase === 7) {
        if (w.t - probeDone > 2.5) phase = w.lead ? 1 : 0;
      } else {
        phase = w.lead && w.lead.gap < 45 ? 1 : 0;
      }
      // past the crossing: back to cruising
      if (phase === 4 && w.nose > CROSSING.x + 6) phase = 0;
      return command(stopAt, warn);
    },
    frame: {
      // the street is wide: the camera stands behind and above on the car's left, looking at the car and the street ahead of it
      cx: ctx.start.x + mid + 13,
      cz: -ctx.start.y - 1.2,
      radius: 17,
      camera: { az: 136, el: 33 },
    },
  };
};
