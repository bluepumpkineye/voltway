import type { ActorDef, ActorNow, Command, SceneFactory, World } from '../drive';
import type { SignalState } from '../carpet';
import { STREET, stopAndGo, walker } from './city';

/**
 * Autonomous Drive at a traffic light, "red light" (the BYD Seal): the car drives a two-lane street at 50 km/h behind another car; the
 * light at a signalled zebra crossing ahead turns amber and then red, the car ahead stops at the line and the Seal stops behind it,
 * people cross while the light is red, and when it turns green the car ahead goes and the Seal follows.
 *
 * What it stands for: Autohome's table lists traffic-light recognition and city roads for the Seal's DiPilot 300 trims (the 650 and
 * 600 AWD Smart Driving), with one roof lidar, eleven exterior cameras, five radars and twelve ultrasonic sensors. The whole scenario
 * (the street, the light's timing, who is where, the speeds, how far off the car sees the light, how it stops) is ours: BYD publishes
 * none of it. No value imports of anything that needs a browser.
 */

/** the set speed, m/s (50 km/h) */
const SET = 50 / 3.6;
const LANE = 3.3;
/** the street's repeating things repeat every this many metres (the viewer rolls them by it) */
const PERIOD = 24;
/** the zebra crossing, m along the street from the car's start (the middle of the stripes), and its length along the street */
export const CROSSING_LIGHT = { x: 143.2, length: 4 } as const;
/** the stop lines sit this far before the stripes, m */
const LINE_GAP = 1.2;
/** when the light changes, s: green until `amber`, amber until `red`, red until `green`, then green */
export const LIGHT = { amber: 3.6, red: 6.0, green: 17.4 } as const;
/** how far off the car has the light, m (the cameras read a signal head from much further; this is the drawn reach) */
export const RECOGNISE = 110;
/** the car waits this long after the light turns green before it moves off, s (the cars ahead go first) */
const REACTION = 1.2;

/** the signal's mast stands just past the crossing */
const MAST_X = CROSSING_LIGHT.x + CROSSING_LIGHT.length / 2 + 2.2;

const END = 27;

export function signalAt(t: number): SignalState {
  if (t < LIGHT.amber) return 'green';
  if (t < LIGHT.red) return 'amber';
  if (t < LIGHT.green) return 'red';
  return 'green';
}

const STATES = ['cruising', 'following', 'seen', 'amber', 'stopping', 'waiting', 'moving-off'];
const MESSAGES = [
  'Driving the street at 50 km/h',
  'Following the car ahead',
  'Traffic light recognised: green',
  'Light turned amber: the car will stop at the line',
  'Red light: stopping at the line',
  'Waiting at the red light',
  'Green light: moving off behind the car ahead',
];

export const trafficLightScene: SceneFactory = (ctx) => {
  const { cars, mid } = ctx;
  const pick = (i: number) => cars[i % Math.max(cars.length, 1)] ?? { slug: '', length: 4.8, width: 1.85 };
  const lineX = CROSSING_LIGHT.x - CROSSING_LIGHT.length / 2 - LINE_GAP;
  const lineFar = CROSSING_LIGHT.x + CROSSING_LIGHT.length / 2 + LINE_GAP;

  const car = (id: string, i: number, x: number, speed: (t: number) => number, y: number, facing: 1 | -1 = 1): ActorDef => {
    const size = pick(i);
    return { id, kind: 'car', slug: size.slug, length: size.length, width: size.width - 0.08, gap: x - mid, speed, y: () => y, facing };
  };
  const person = (id: string, x: number, y: (t: number) => number): ActorDef => ({
    id,
    kind: 'person',
    slug: '',
    length: 0.5,
    width: 0.55,
    gap: x - mid,
    speed: () => 0,
    y,
  });

  // the car ahead in the car's lane and one beside it: both see the light change and stop at the line, and go a moment after green
  const leadLen = pick(0).length;
  const leadX0 = mid + 40;
  const lead = car(
    'lead',
    0,
    leadX0,
    stopAndGo({ v0: 46 / 3.6, xFrom: leadX0, xStop: lineX - 0.3 - leadLen / 2, aDec: 2.2, tGo: LIGHT.green + 0.5, aAcc: 1.8, vEnd: 40 / 3.6, dir: 1 }),
    0,
  );
  const besideLen = pick(1).length;
  const besideX0 = mid + 28;
  const beside = car(
    'beside',
    1,
    besideX0,
    stopAndGo({ v0: 46 / 3.6, xFrom: besideX0, xStop: lineX - 4.5 - besideLen / 2, aDec: 2.0, tGo: LIGHT.green + 0.3, aAcc: 1.8, vEnd: 42 / 3.6, dir: 1 }),
    STREET.left,
  );
  // one coming the other way, stopped at its own line on the far side
  const oncLen = pick(2).length;
  const oncX0 = 290;
  const oncoming = car(
    'oncoming',
    2,
    oncX0,
    stopAndGo({ v0: 50 / 3.6, xFrom: oncX0, xStop: lineFar + 0.3 + oncLen / 2, aDec: 2.2, tGo: LIGHT.green + 0.8, aAcc: 1.8, vEnd: 40 / 3.6, dir: -1 }),
    STREET.oncoming,
    -1,
  );

  // the cars along the near kerb (none near the crossing)
  const parked = [16, 44, 70, 96, 118, 168, 194, 222].map((x, i) => car(`parked-${i}`, 3 + i, x, () => 0, STREET.parked));

  // the people who cross while the light is red: they set out a while after it turned, and are across before it goes green
  const near = STREET.nearKerb - 0.3;
  const far = STREET.farKerb + 0.35;
  const X = CROSSING_LIGHT.x;
  const people = [
    person('person-1', X - 1.3, walker(near, far, 6.6, 1.5)),
    person('person-2', X + 0.1, walker(near, far, 7.2, 1.45)),
    person('person-3', X - 0.5, walker(far, near, 7.8, 1.45)),
    person('person-4', X + 1.0, walker(near, far, 8.6, 1.9)),
  ];

  const actors: ActorDef[] = [lead, beside, oncoming, ...parked, ...people];

  let phase = 0;
  let greenSince = -1;
  let latched = false;

  const command = (stopAt: number | null, note: string | null): Command => ({
    vSet: SET,
    aMax: 1.7,
    stopAt,
    state: STATES[phase],
    message: MESSAGES[phase],
    note,
    indicator: 0,
    lane: null,
    showLead: true,
    warn: [],
  });

  return {
    id: 'trafficlight',
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
        lines: [
          { y: -LANE / 2, dash: false, color: 'white' },
          { y: LANE / 2, dash: true, color: 'white' },
          { y: STREET.centre - 0.09, dash: false, color: 'yellow' },
          { y: STREET.centre + 0.09, dash: false, color: 'yellow' },
        ],
        crossings: [{ x: CROSSING_LIGHT.x, length: CROSSING_LIGHT.length }],
        stopLines: [
          { x: lineX, y0: STREET.parked + 1.3, y1: STREET.centre },
          { x: lineFar, y0: STREET.centre, y1: STREET.farKerb },
        ],
        // the mast stands on the near footway just past the crossing, its arm over both of the car's lanes
        signals: [
          {
            x: MAST_X,
            pole: STREET.nearKerb - 0.65,
            heads: [0, STREET.left],
            reach: RECOGNISE + (MAST_X - lineX),
            state: signalAt,
          },
        ],
      },
    },
    reach: { ahead: 48, behind: 26 },
    follow: { d0: 6, T: 1.2, stopGap: 3.8 },
    jerkUp: 4.5,
    initial: command(null, null),
    decide: (w: World) => {
      const s = signalAt(w.t);
      const toLine = lineX - w.nose;
      const seen = toLine < RECOGNISE && toLine > -6;
      const note = seen ? `Signal: ${s}` : null;
      let stopAt: number | null = null;

      if (s !== 'green' && toLine > -0.5 && toLine < RECOGNISE) {
        // amber or red ahead, and the line not yet passed: the car stops at it (the car ahead may stop it sooner)
        latched = true;
        greenSince = -1;
        stopAt = lineX - 0.2;
        phase = w.v < 0.25 && toLine < 16 ? 5 : s === 'amber' ? 3 : 4;
      } else if (latched && s === 'green') {
        // green again: a moment, then the car moves off behind the one ahead
        if (greenSince < 0) greenSince = w.t;
        if (w.t - greenSince < REACTION) {
          stopAt = lineX - 0.2;
          phase = 5;
        } else {
          phase = 6;
        }
        // past the crossing: back to the street
        if (w.nose > CROSSING_LIGHT.x + 6) {
          latched = false;
          phase = w.lead ? 1 : 0;
        }
      } else if (seen && s === 'green' && !latched) {
        phase = 2;
      } else {
        phase = w.lead && w.lead.gap < 45 ? 1 : 0;
      }
      return command(stopAt, note);
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

export type { ActorNow };
