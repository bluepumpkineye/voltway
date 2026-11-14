import type { ActorDef, Command, SceneFactory, World } from '../drive';
import { stopAndGo } from './city';

/**
 * Autonomous Drive in a traffic jam, "queue ahead" (the Denza Z9): the car follows the traffic on a three-lane expressway at
 * 80 km/h with its adaptive cruise on. Far ahead a queue stands in every lane: the car in front brakes to join it, the Z9 slows
 * with it and stops behind it holding the gap, waits while the queue is stationary, and moves off when the queue does, following at
 * a safe distance.
 *
 * What it stands for: Autohome's table for the Denza Z9 (series 7838, read 2026-11-14) lists, on all five trims, the DiPilot
 * driver-assist system at level 2 on an NVIDIA Orin chip with two lidars, fourteen exterior cameras (a three-lens front unit), five
 * millimetre-wave radars and twelve ultrasonic sensors, full-speed adaptive cruise, lane centring, assisted lane change, ramp entry
 * and exit and traffic-light recognition, for city and expressway roads. The whole scenario here (the road, the queue, where it
 * stands, the speeds, the braking, when the jam clears, and how far off the lidars mark the stopped cars) is ours: BYD publishes
 * none of it. No value imports of anything that needs a browser.
 */

/** the lane's width, m */
const LANE = 3.75;
/** the set speed, m/s (80 km/h) */
const SET = 80 / 3.6;
/** the jam's cars stand bumper to bumper with this gap, m */
const BUMPER = 1.6;
/** the tail of the queue in the car's lane, m along the road from the car's start (the nearest stopped car's middle) */
const TAIL = 260;
/** the queue starts to move at these times, s, from the front of the jam to the back (a queue goes from the front) */
const GO = { front: 15.5, step: 0.8 } as const;
/** how far off the lidars mark a stopped car, m (the drawn reach: a lidar sees further) */
const SEEN = 200;
/** the jam's creeping speed once it moves, m/s (25 km/h) */
const CREEP = 25 / 3.6;

const END = 28;

const STATES = ['cruising', 'seen', 'braking', 'stopped', 'moving-off', 'following'] as const;
const MESSAGES = [
  'Following the traffic at 80 km/h',
  'Stopped traffic ahead: the lidars have it, easing off',
  'The car ahead is braking: slowing with it',
  'Stopped behind the queue: holding the gap',
  'The queue is moving: following the car ahead',
  'Following the queue at a safe distance',
];

export const queueScene: SceneFactory = (ctx) => {
  const { cars, mid } = ctx;
  const pick = (i: number) => cars[i % Math.max(cars.length, 1)] ?? { slug: '', length: 4.8, width: 1.85 };

  const car = (id: string, i: number, x: number, speed: (t: number) => number, lane: -1 | 0 | 1): ActorDef => {
    const size = pick(i);
    return { id, kind: 'car', slug: size.slug, length: size.length, width: size.width - 0.08, gap: x - mid, speed, y: () => lane * LANE };
  };
  /** a car that is in the queue from the start: it stands still until `tGo`, then pulls away to the creeping speed */
  const queued = (id: string, i: number, x: number, lane: -1 | 0 | 1, tGo: number) =>
    car(id, i, x, (t) => (t < tGo ? 0 : Math.min(CREEP, 1.3 * (t - tGo))), lane);
  const spacing = (a: number, b: number) => (pick(a).length + pick(b).length) / 2 + BUMPER;

  // the car's own lane: three stopped cars (the nearest, the tail, is what the lead stops behind), and the lead, which comes up
  // behind them at the traffic's speed, stops, and goes on a moment after the car in front of it
  const lane0 = [
    queued('q0-front', 6, TAIL + spacing(4, 5) + spacing(5, 6), 0, GO.front),
    queued('q0-mid', 5, TAIL + spacing(4, 5), 0, GO.front + GO.step),
    queued('q0-tail', 4, TAIL, 0, GO.front + 2 * GO.step),
  ];
  const leadX0 = mid + 64;
  const lead = car(
    'lead',
    0,
    leadX0,
    stopAndGo({ v0: SET, xFrom: leadX0, xStop: TAIL - spacing(4, 0), aDec: 2.6, tGo: GO.front + 3 * GO.step, aAcc: 1.2, vEnd: CREEP, dir: 1 }),
    0,
  );

  // the lane on the right: the same jam, a car that is braking to join it
  const rTail = TAIL - 14;
  const rightQueue = [
    queued('qr-0', 7, rTail + spacing(7, 8) + spacing(8, 9), -1, GO.front + 0.4),
    queued('qr-1', 8, rTail + spacing(8, 9), -1, GO.front + 1.2),
    queued('qr-2', 9, rTail, -1, GO.front + 2.0),
  ];
  const rX0 = mid + 38;
  const rLead = car(
    'right-lead',
    1,
    rX0,
    stopAndGo({ v0: SET, xFrom: rX0, xStop: rTail - spacing(1, 9), aDec: 2.6, tGo: GO.front + 2.9, aAcc: 1.1, vEnd: CREEP, dir: 1 }),
    -1,
  );

  // the lane on the left: a car just ahead of the Z9 that brakes for its own queue
  const lTail = TAIL - 6;
  const leftQueue = [
    queued('ql-0', 3, lTail + spacing(3, 2), 1, GO.front + 0.2),
    queued('ql-1', 2, lTail, 1, GO.front + 1.0),
  ];
  const lX0 = mid + 22;
  const lLead = car(
    'left-lead',
    2,
    lX0,
    stopAndGo({ v0: 78 / 3.6, xFrom: lX0, xStop: lTail - spacing(2, 1), aDec: 2.3, tGo: GO.front + 1.5, aAcc: 1.1, vEnd: CREEP, dir: 1 }),
    1,
  );

  const actors: ActorDef[] = [lead, ...lane0, rLead, ...rightQueue, lLead, ...leftQueue];

  let phase = 0;
  let stopped = false;
  let braked = false;
  let seenAt = -1;

  const command = (note: string | null, warn: string[]): Command => ({
    vSet: SET,
    aMax: 1.3,
    state: STATES[phase],
    message: MESSAGES[phase],
    note,
    indicator: 0,
    lane: null,
    showLead: true,
    warn,
  });

  return {
    id: 'queue',
    duration: END,
    v0: SET,
    actors,
    road: { humps: [], from: -140, to: 140, width: LANE * 3 + 3.2, lanes: { count: 3, width: LANE } },
    // the lidars mark the stopped cars a long way ahead, so the marks are drawn that far
    reach: { ahead: SEEN + 20, behind: 36 },
    follow: { d0: 7, T: 1.5, stopGap: 5.5 },
    inPath: (c, w) => Math.abs(c.y - w.e) <= 2.3,
    initial: command(null, []),
    decide: (w: World) => {
      const toTail = TAIL - pick(4).length / 2 - w.nose;
      const lead = w.lead;
      const going = w.t >= GO.front + 3 * GO.step;
      if (toTail < SEEN && seenAt < 0) seenAt = w.t;
      // once the car ahead has begun to brake the car is slowing with it until it has stopped
      if (lead && lead.v < w.v - 1.2 && !going) braked = true;
      if (w.v < 0.25 && lead && lead.v < 0.25) {
        stopped = true;
        phase = 3;
      } else if (stopped && lead && (going || lead.v > 0.4)) {
        phase = lead.v < CREEP * 0.8 || w.v < CREEP * 0.8 ? 4 : 5;
      } else if (braked && !stopped) {
        phase = 2;
      } else if (seenAt >= 0 && !stopped) {
        phase = 1;
      } else {
        phase = stopped ? 5 : 0;
      }
      const marked = phase === 1 || phase === 2;
      const note = toTail > 0 && !going && !stopped ? `Stopped cars ${Math.round(toTail)} m ahead` : null;
      return command(note, marked ? ['q0-tail'] : []);
    },
    frame: {
      // behind and above, a little to the left where the lane beside is: the same view the overtake has
      cx: ctx.start.x + mid + 8,
      cz: -ctx.start.y - LANE * 0.35,
      radius: 17,
      camera: { az: 128, el: 34 },
    },
  };
};
