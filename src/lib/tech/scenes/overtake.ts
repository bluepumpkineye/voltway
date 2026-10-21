import type { ActorDef, ActorNow, Command, SceneFactory, World } from '../drive';

/**
 * Autonomous Drive on an expressway, "overtake" (the Luxeed RX, the Xiaomi SU7 Ultra, the NIO ES8): the car cruises at 100 km/h
 * in the middle lane of a three-lane road with other cars in every lane, the car ahead brakes, the car follows it, waits for a car
 * coming up fast in the left lane to go by, changes lane when the lane is clear and overtakes.
 *
 * The whole scenario (the traffic, the speeds, the braking, the decisions and when they come) is ours: no maker publishes one.
 * It is the planner as it was when the owner approved it (docs/tech-showcase.md section 12), moved here unchanged. No value imports.
 */

/** the lane's width, m (a Chinese expressway's lanes are 3.75 m) */
export const LANE = 3.75;
/** the set speed, m/s (100 km/h) */
export const CRUISE = 100 / 3.6;
/** the set speed while the car is overtaking, m/s (112 km/h) */
const OVERTAKE = 112 / 3.6;

/** the seconds of the run at which each thing is decided (the rest follows from the traffic) */
export const TIMES = {
  /** the car ahead starts to brake, and the car has finished doing so */
  leadBrake: 2.6,
  leadSlow: 6.0,
  /** the car does not think of changing lane before this */
  minDecide: 3.0,
  /** a lane change takes this long */
  lane: 4.0,
  end: 19.0,
} as const;

interface Role {
  id: string;
  lane: -1 | 0 | 1;
  /** where its middle is at the start, m ahead of the car's middle */
  gap: number;
  kmh: number;
  /** it brakes to this speed (km/h) between the two times */
  slows?: { to: number; from: number; until: number };
}

/**
 * The traffic, in the order the stand-ins are given: the car ahead (it brakes), one that comes up from behind in the left
 * lane, one that goes by the car's left early on, one that is passed on the right, one that follows on the right, and one far
 * ahead. Where each stands and how fast it goes is ours; the lane change's timing comes out of them.
 */
export const ROLES: Role[] = [
  { id: 'lead', lane: 0, gap: 62, kmh: 100, slows: { to: 74, from: TIMES.leadBrake, until: TIMES.leadSlow } },
  { id: 'fast', lane: 1, gap: -66, kmh: 130 },
  { id: 'early', lane: 1, gap: -22, kmh: 118 },
  { id: 'slow', lane: -1, gap: 30, kmh: 84 },
  { id: 'follow', lane: -1, gap: -30, kmh: 95 },
  { id: 'far', lane: -1, gap: 82, kmh: 90 },
];

/**
 * Is a car in the lane beside in the way of a lane change? `d` is where its middle is from ours (negative: behind), `half` the
 * two cars' half lengths added, `vc` and `ve` its speed and ours. One behind must not close within three seconds, and one
 * ahead must be well clear.
 */
export function inTheWay(d: number, half: number, vc: number, ve: number): boolean {
  return d < 0 ? -d - half - Math.max(0, vc - ve) * 3.2 < 9 : d - half < 12 + Math.max(0, ve - vc) * 2.2;
}

const STATES = ['cruising', 'following', 'waiting', 'changing', 'passing', 'done'] as const;

function say(phase: number, clear: boolean): string {
  switch (phase) {
    case 0:
      return 'Cruising with the traffic';
    case 1:
      return 'Car ahead is braking: easing off to follow';
    case 2:
      return clear ? 'Left lane clear' : 'Indicating left: a car is coming up fast, waiting';
    case 3:
      return 'Left lane clear: changing lane';
    case 4:
      return 'Overtaking the slower car';
    default:
      return 'Overtaken: back to the set speed';
  }
}

export const overtakeScene: SceneFactory = (ctx) => {
  const { cars, egoLen } = ctx;
  const actors: ActorDef[] = ROLES.map((r, i) => {
    const size = cars[i % Math.max(cars.length, 1)] ?? { slug: '', length: 4.9, width: 1.9 };
    const v0 = r.kmh / 3.6;
    return {
      id: r.id,
      kind: 'car',
      slug: size.slug,
      length: size.length,
      width: size.width,
      gap: r.gap,
      // constant, or a linear ramp down while it brakes
      speed: (t: number) => {
        if (!r.slows) return v0;
        const { from, until, to } = r.slows;
        const v1 = to / 3.6;
        return t <= from ? v0 : t >= until ? v1 : v0 + ((v1 - v0) * (t - from)) / (until - from);
      },
      y: () => r.lane * LANE,
    };
  });
  const leadIndex = ROLES.findIndex((r) => r.id === 'lead');

  /** is the left lane clear to move into now? Cars behind must not close within three seconds, cars ahead must be far enough. */
  const inTheWayNow = (w: World): ActorNow[] =>
    w.actors.filter((c, j) => ROLES[j].lane === 1 && inTheWay(c.x - w.x, (c.def.length + egoLen) / 2, c.vx, w.v));

  let phase = 0; // 0 cruising, 1 following, 2 waiting, 3 changing, 4 passing, 5 done
  let t0 = -1; // when the lane change began

  const command = (clear: boolean, warn: string[], changeTo?: Command['changeTo']): Command => ({
    vSet: phase >= 3 ? OVERTAKE : CRUISE,
    aMax: phase >= 3 ? 1.9 : 1.2,
    state: STATES[phase],
    message: say(phase, clear),
    indicator: phase === 2 || phase === 3 ? 1 : 0,
    lane: phase === 3 ? { y: LANE, clear: true } : phase === 2 ? { y: LANE, clear } : null,
    showLead: phase <= 2,
    warn,
    changeTo,
  });

  return {
    id: 'overtake',
    duration: TIMES.end,
    v0: CRUISE,
    actors,
    // three lanes and their shoulders, long enough that its ends are out of sight; the markings stream by at the car's speed
    road: { humps: [], from: -140, to: 140, width: LANE * 3 + 3.2, lanes: { count: 3, width: LANE } },
    reach: { ahead: 62, behind: 36 },
    follow: { d0: 8, T: 1.55 },
    // the cars are told apart by lane: one overlaps the car's path if it is within 2.3 m of its middle
    inPath: (c, w) => Math.abs(c.y - w.e) <= 2.3,
    initial: command(false, []),
    decide: (w) => {
      const lead = w.lead;
      if (phase <= 1) {
        phase = lead && lead.gap < 70 && lead.v < w.v - 0.4 ? 1 : 0;
        if (w.t >= TIMES.minDecide && lead && lead.v < w.v - 2.5 && lead.gap < 52 && ROLES[lead.j].lane === 0) phase = 2;
      }
      let clear = false;
      let changeTo: Command['changeTo'];
      let warn: string[] = [];
      if (phase === 2) {
        const blockers = inTheWayNow(w);
        clear = blockers.length === 0;
        warn = blockers.map((b) => b.def.id);
        if (clear) {
          phase = 3;
          t0 = w.t;
          changeTo = { y: LANE, dur: TIMES.lane };
        }
      }
      if (phase === 3 && w.t >= t0 + TIMES.lane) phase = 4;
      if (phase === 4) {
        const L = w.actors[leadIndex];
        if (w.x - L.x > (L.def.length + egoLen) / 2 + 3) phase = 5;
      }
      return command(clear, warn, changeTo);
    },
    frame: {
      // the car and the lanes about it: the camera stands behind and above, a little to the left where the overtaking is
      cx: ctx.start.x + ctx.mid + 8,
      cz: -ctx.start.y - LANE * 0.35,
      radius: 16,
      camera: { az: 128, el: 34 },
    },
  };
};
