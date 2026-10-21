import type { ActorDef, Command, SceneFactory } from '../drive';
import { CRUISE, inTheWay, LANE } from './overtake';

/**
 * Autonomous Drive on an expressway, "debris and cut-in" (the Avatr 06T): the car cruises at 100 km/h in the middle lane of a
 * three-lane road; a slower car on its right moves into its lane close ahead and the car eases off to keep its distance; the car
 * it now follows swings out to the left round something lying in the lane (a box fallen off a lorry), which shows the car what
 * the lidar saw a moment before; it checks the right lane, moves over and drives past, and goes back to its set speed.
 *
 * What it stands for, as the maker words it: "end-to-end GOD (General Obstacle Detection) and PDP (Prediction Decision
 * Planning) network with 896-line roof LiDAR" (Avatr's page): an obstacle that is not a vehicle, seen and avoided, and a car
 * that is about to move in, predicted from its drift. The whole scenario (the road, the traffic, the box, the speeds, the moment
 * each thing is decided) is ours: no maker publishes one. No value imports except the constants of the overtake scene.
 */

const SET = CRUISE;
/** the speed the car takes round the object, m/s (92 km/h) */
const AROUND = 92 / 3.6;
/** the speed it eases to while a car is moving in, m/s (90 km/h) */
const EASE = 90 / 3.6;
/** where the box lies, m ahead of the car's middle at the start (the cars reach it after about twelve seconds) */
const BOX_AT = 335;
const BOX = { length: 0.75, width: 0.55 };
/** when the car on the right moves into the lane, and how long it takes; when it swings out left round the box */
const CUT = { at: 2.3, dur: 3.4 };
const SWERVE = { at: 9.3, dur: 2.5 };
const END = 16.5;

/** a smooth step from 0 to 1 over [from, from + dur] */
const rise = (t: number, from: number, dur: number) => {
  const u = Math.min(1, Math.max(0, (t - from) / dur));
  return (1 - Math.cos(Math.PI * u)) / 2;
};

export const debrisScene: SceneFactory = (ctx) => {
  const { cars, egoLen, mid } = ctx;
  const pick = (i: number) => cars[i % Math.max(cars.length, 1)] ?? { slug: '', length: 4.9, width: 1.9 };
  const car = (id: string, i: number, gap: number, kmh: number, y: (t: number) => number): ActorDef => {
    const size = pick(i);
    return { id, kind: 'car', slug: size.slug, length: size.length, width: size.width, gap, speed: () => kmh / 3.6, y };
  };
  const actors: ActorDef[] = [
    // the car on the right that moves in, and then swings out to the left round the box
    car('cutter', 0, 38, 93, (t) => -LANE + LANE * rise(t, CUT.at, CUT.dur) + LANE * rise(t, SWERVE.at, SWERVE.dur)),
    // one that comes up fast behind in the left lane and goes by, one far ahead in the left lane
    car('fast', 1, -80, 122, () => LANE),
    car('left-far', 2, 75, 108, () => LANE),
    // the right lane: one far behind, one far ahead
    car('right-back', 3, -62, 96, () => -LANE),
    car('right-far', 4, 125, 88, () => -LANE),
    // the box
    {
      id: 'box',
      kind: 'box',
      slug: '',
      length: BOX.length,
      width: BOX.width,
      gap: BOX_AT,
      speed: () => 0,
      y: () => 0,
      // the 896-line lidar recognises a 14 cm box at 120 m (Huawei): the sensors have it from there
      reach: 125,
    },
  ];
  const J = Object.fromEntries(actors.map((a, j) => [a.id, j]));

  // 0 cruising, 1 a car is moving in, 2 following it, 3 the object is seen, 4 changing lane, 5 passing it, 6 done
  let phase = 0;
  let t0 = -1;
  const STATES = ['cruising', 'cutting-in', 'following', 'sighted', 'changing', 'passing', 'done'];
  const MESSAGES = [
    'Cruising with the traffic',
    'A car on the right is moving into the lane: easing off to keep the gap',
    'Following the car that moved in',
    'Object on the road ahead, not a vehicle: planning a way round it',
    'Right lane clear: steering round the object',
    'Passing the object',
    'Past the object: back to the set speed',
  ];

  const command = (clear: boolean, warn: string[], changeTo?: Command['changeTo']): Command => ({
    // the car eases off as soon as it sees the other car drifting toward its lane, before the car is in it
    vSet: phase >= 4 ? AROUND : phase === 1 ? EASE : SET,
    aMax: phase >= 4 ? 1.4 : 1.2,
    state: STATES[phase],
    message: MESSAGES[phase],
    note: phase === 3 ? (clear ? 'Right lane clear' : 'Right lane: checking') : phase === 1 ? 'Predicted from its drift across the lane line' : null,
    indicator: phase === 3 || phase === 4 ? -1 : 0,
    lane: phase === 3 ? { y: -LANE, clear } : phase === 4 ? { y: -LANE, clear: true } : null,
    showLead: phase <= 2,
    warn,
    changeTo,
  });

  return {
    id: 'debris',
    duration: END,
    v0: SET,
    actors,
    road: { humps: [], from: -140, to: 140, width: LANE * 3 + 3.2, lanes: { count: 3, width: LANE } },
    reach: { ahead: 62, behind: 36 },
    follow: { d0: 8, T: 1.55 },
    // the box is the car's business only when it is close (it has been told to go round it long before); the rest by width
    inPath: (c, w) =>
      c.def.kind === 'box' ? Math.abs(c.y - w.e) <= 1.9 && c.x - w.nose < 40 : Math.abs(c.y - w.e) <= (c.def.width + w.egoWid) / 2 + 0.3,
    initial: command(false, []),
    decide: (w) => {
      const box = w.actors[J.box];
      const cutter = w.actors[J.cutter];
      const boxGap = box.x - w.nose - box.def.length / 2;
      const inLane = Math.abs(box.y - w.e) < 2.0;
      let clear = false;
      let changeTo: Command['changeTo'];
      let warn: string[] = [];

      if (phase <= 2) {
        // a car moving into the lane ahead: close, not yet in it, drifting toward it (its drift is what the car predicts from)
        const dy = cutter.y - w.e;
        const ahead = cutter.x - w.nose;
        const toward = Math.sign(dy) * cutter.vy < -0.3;
        if (toward && Math.abs(dy) > 0.45 && Math.abs(dy) < LANE * 0.95 && ahead > 0 && ahead < 60) phase = 1;
        else phase = w.lead && w.lead.j === J.cutter ? 2 : 0;
        // the object is seen
        if (inLane && boxGap < 125) phase = 3;
      }
      if (phase === 3) {
        warn = ['box'];
        const blockers = w.actors.filter((c) => c.def.kind === 'car' && Math.abs(c.y - -LANE) < 1.6 && inTheWay(c.x - w.x, (c.def.length + egoLen) / 2, c.vx, w.v));
        clear = blockers.length === 0;
        // it decides to go round once it is near enough to be sure it is staying, and the lane is clear
        if (boxGap < 100 && clear) {
          phase = 4;
          t0 = w.t;
          changeTo = { y: -LANE, dur: 3.6 };
        }
      }
      if (phase === 4) {
        warn = ['box'];
        if (w.t >= t0 + 3.6) phase = 5;
      }
      if (phase === 5) {
        warn = ['box'];
        if (w.x - box.x > (egoLen + box.def.length) / 2 + 2) phase = 6;
      }
      return command(clear, warn, changeTo);
    },
    frame: {
      cx: ctx.start.x + mid + 10,
      cz: -ctx.start.y + LANE * 0.1,
      radius: 17,
      camera: { az: 128, el: 34 },
    },
  };
};
