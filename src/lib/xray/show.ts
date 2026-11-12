/**
 * The X-ray tab's Play: a drive run on a salt flat, the body a faint pane and the hardware showing, told in six shots and a drive-away.
 *
 * The art direction is taken from a recording of a maker's showroom wall (its chassis film): a slow, low camera that stays on the hardware,
 * hard flies between shots (a whip, about a second), the wheels and the pack seen from the side as the ground streams past, then a long
 * pulled-back chase and a last three-quarter view as the car stops. Then the camera freezes, behind the car, and the car drives off and is lost in the haze. The pictures are our own 3D, drawn live for whichever car is open; nothing
 * here is the maker's footage.
 *
 * The shots are timed on the run's own moments (the pull, the pace it then holds, the brake: `DriveFacts.events`), so the camera is on the
 * front axle while the car pulls and on the brakes while it stops, whichever car and run. Everything here is a pure function of the plan
 * and the playhead, so a scrubbed run shows the same picture as a played one. No React and no three.js: the viewer turns a `Pose` into a camera
 * (viewer/XrayShow.tsx), the panel reads the chapters.
 */

/** Where the camera stands, in terms that scale with the car: the heading about it, the lift, the distance in car lengths, and where it looks. */
export interface Pose {
  /** azimuth about the car from its nose, degrees: 0 the front, 90 its left, 180 the tail (the Drive tab's convention) */
  az: number;
  /** elevation, degrees */
  el: number;
  /** distance in car lengths */
  d: number;
  /** where it looks: along the car in car lengths from its middle (+ toward the nose), height in car heights, sideways in car widths (+ the right) */
  u: number;
  h: number;
  lat: number;
}

/** What a shot is about, for the small title at the top of the picture and for which system's parts stand out. */
export interface Chapter {
  id: string;
  from: number;
  to: number;
  kicker: string;
  title: string;
  /** the X-ray system its parts are drawn brightest in (the others dim a little), null for the wide shots */
  system: 'drive' | 'battery' | 'suspension' | 'brakes' | null;
}

interface Key extends Pose {
  /** the run's second at which the camera is here */
  at: number;
  /** the move into this key is a fly (a whip between shots); otherwise a slow drift inside one shot */
  fly?: boolean;
}

export interface ShowPlan {
  /** the whole show, s: the run and the exit */
  dur: number;
  /** the run alone, s */
  runDur: number;
  keys: Key[];
  chapters: Chapter[];
}

/** a fly between shots, s */
const FLY = 0.95;

interface Shot {
  id: string;
  kicker: string;
  title: string;
  system: Chapter['system'];
  /** the shot's share of its stretch of the run, summing to 1 within a stretch */
  share: number;
  from: Pose;
  to: Pose;
}

const P = (az: number, el: number, d: number, u: number, h: number, lat = 0): Pose => ({ az, el, d, u, h, lat });

/** The stretch of the run each shot lives in: the pull (up to the speed it holds), the pace, the stop. */
const PULL: Shot[] = [
  // the car sets off, wide from its left; the camera creeps in
  { id: 'hardware', kicker: 'X-ray', title: 'Only the hardware', system: null, share: 0.4, from: P(104, 5, 1.75, 0.0, 0.28), to: P(96, 4, 1.45, 0.04, 0.26) },
  // low and close on the front axle as it pulls, swinging from the nose to the flank
  { id: 'front', kicker: 'Launch', title: 'Front axle', system: 'drive', share: 0.6, from: P(34, 8, 0.8, 0.3, 0.2), to: P(66, 7, 0.75, 0.27, 0.18) },
];
const PACE: Shot[] = [
  // along the pack, low, the ground streaming past
  { id: 'pack', kicker: 'Energy', title: 'Battery pack', system: 'battery', share: 1 / 3, from: P(64, 7, 1.0, 0.02, 0.14), to: P(86, 6, 0.95, -0.08, 0.14) },
  // behind the rear axle, on the drive units and the wheels
  { id: 'rear', kicker: 'Drive', title: 'Rear drive units', system: 'drive', share: 1 / 3, from: P(146, 10, 0.85, -0.3, 0.2), to: P(124, 9, 0.85, -0.28, 0.2) },
  // high and behind, pulling back as the car holds its speed
  { id: 'speed', kicker: 'Speed', title: 'Holding the pace', system: null, share: 1 / 3, from: P(171, 12, 1.35, 0.0, 0.3), to: P(176, 15, 2.0, 0.05, 0.32) },
];
const STOP: Shot[] = [
  // three-quarter from the front, the car coming to rest
  { id: 'stop', kicker: 'Stop', title: 'Brakes and regeneration', system: 'brakes', share: 1, from: P(30, 8, 1.55, 0.0, 0.28), to: P(52, 10, 1.65, 0.0, 0.28) },
];
/** The last shot of a run that does not end in a stop (its scenario ends in a manoeuvre of its own): the same view, named for what is on screen. */
const FINISH: Shot = { id: 'finish', kicker: 'Drive', title: 'On the move', system: null, share: 1, from: P(30, 8, 1.55, 0.0, 0.28), to: P(52, 10, 1.65, 0.0, 0.28) };
/** The last shot: the camera flies behind the stopped car, freezes there (it is the world's, it does not follow the car) and the car drives away from it. */
const EXIT: Shot = { id: 'exit', kicker: '', title: '', system: null, share: 1, from: P(171, 6, 1.2, 0.0, 0.24), to: P(171, 6, 1.2, 0.0, 0.24) };

/** The run's least length (`DriveSelection.minRunS`) when it is played on the X-ray tab, s: the longer run gives each shot and each card time to be read (a run is about 3 s longer than this, and with the exit the show is about 30 s) */
export const SHOW_RUN_S = 22;
/** The drive-away that ends the show, s, after the run's own stop */
export const SHOW_EXIT_S = 5.5;
/** the exit's camera starts to fly this long before the run's end, while the car is still stopped, s */
const EXIT_LEAD = 1.3;

const clamp01 = (x: number) => Math.min(1, Math.max(0, x));
const smooth = (x: number) => x * x * (3 - 2 * x);
const cubic = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const mix = (a: number, b: number, k: number) => a + (b - a) * k;

/** The run's moments the plan is built on: the seconds at which each cue happens (`DriveFacts.events`), and how long the show is in all (`exit` of it after the run). */
export interface RunMoments {
  events: { cue: string; t: number }[];
  /** the whole show: the run and the exit */
  duration: number;
  /** the exit's length, s */
  exit: number;
}

const cache = new WeakMap<object, ShowPlan>();

/**
 * The shots laid on this run: the pull (to the moment the target speed is reached) holds the wide and the front axle, the pace holds the pack,
 * the rear and the chase in thirds, the brake holds the last, and the exit (a frozen camera, the car driving away) closes it. A run with no cue
 * falls back to shares of its length. `key` is what the run is known by (its facts object): the plan is made once for it.
 */
export function planFor(key: object, run: RunMoments): ShowPlan {
  const hit = cache.get(key);
  if (hit) return hit;
  const dur = Math.max(run.duration, 1);
  const runDur = Math.max(dur - run.exit, 1);
  const at = (cue: string) => run.events.find((e) => e.cue === cue)?.t;
  const stopAt = runDur - EXIT_LEAD;
  const brake = Math.min(at('brake') ?? runDur * 0.8, stopAt - 2);
  // the pull ends where the run's target speed is reached (`target`; the car then holds it, from `cruise`)
  let pace = at('target') ?? at('cruise') ?? runDur * 0.3;
  // the pull is at least five seconds of picture, and the pace at least six
  pace = Math.min(Math.max(pace, 5), brake - 6);
  const shots: { shot: Shot; from: number; to: number }[] = [];
  const lay = (list: Shot[], a: number, b: number) => {
    let t = a;
    for (const s of list) {
      const e = t + (b - a) * s.share;
      shots.push({ shot: s, from: t, to: e });
      t = e;
    }
  };
  lay(PULL, 0, pace);
  lay(PACE, pace, brake);
  // a run with no brake cue ends moving: its last shot is not the stop
  lay(at('brake') === undefined ? [FINISH] : STOP, brake, stopAt);
  lay([EXIT], stopAt, dur);

  const keys: Key[] = [];
  const chapters: Chapter[] = [];
  shots.forEach(({ shot, from, to }, i) => {
    // a fly into the shot over its first second; the shot's own drift to its end pose
    if (i === 0) keys.push({ at: 0, ...shot.from });
    else keys.push({ at: from + FLY, ...shot.from, fly: true });
    keys.push({ at: to, ...shot.to });
    chapters.push({ id: shot.id, from, to, kicker: shot.kicker, title: shot.title, system: shot.system });
  });
  const plan = { dur, runDur, keys, chapters };
  cache.set(key, plan);
  return plan;
}

// ------------------------------------------------------------------------------------------- the cards

/** What each shot is about, in order of preference: the cards it takes (each card once). Ours; the cards are the Drive tab's. */
const ABOUT: Record<string, string[]> = {
  hardware: [],
  front: ['power', 'motors'],
  pack: ['energy'],
  rear: ['motors', 'suspension'],
  speed: ['aero', 'suspension'],
  stop: ['brake', 'energy'],
  finish: ['suspension', 'energy'],
  exit: [],
};
/** The cards the show can show for any car: they read the run's own telemetry. The drag and the steering come only where the car's scenario lists them (their figures need its own numbers). */
const ANY_CARD = ['power', 'motors', 'energy', 'suspension', 'brake'];
/** how long a card stays, s, and the least between two cards' openings, s: one or two are on screen, and each can be read */
const CARD_HOLD = 5.4;
const CARD_GAP = 3.5;

/** The cards the show uses for a car: the ones its scenario lists, and the ones every car has. */
export function showCards<T extends string>(own: readonly T[]): T[] {
  const all = [...own, ...ANY_CARD.filter((c) => !own.includes(c as T))];
  return all as T[];
}

export interface CardBeat {
  overlay: string;
  from: number;
  to: number;
}

/**
 * When each card is on screen: each shot takes the cards it is about, a second after its start (so the camera has landed), and the cards are
 * spaced out so that two are never opened within `CARD_GAP` of each other and each stays `CARD_HOLD` (the first of two overlaps the next for

 * about a second and a half). None opens in the last stretch, where the car stops and drives away. A pure function of the plan.
 */
export function showBeats(overlays: readonly string[], plan: ShowPlan): CardBeat[] {
  const used = new Set<string>();
  const want: { overlay: string; at: number }[] = [];
  for (const ch of plan.chapters) {
    const room = ch.to - ch.from;
    const prefs = (ABOUT[ch.id] ?? []).filter((o) => overlays.includes(o) && !used.has(o));
    const n = Math.min(prefs.length, room >= 8 ? 2 : 1);
    for (let i = 0; i < n; i++) {
      used.add(prefs[i]);
      want.push({ overlay: prefs[i], at: ch.from + 1 + (i * (room - 1)) / n });
    }
  }
  // (a card the scenario lists that no shot is about, the steering, is left out: its figures need a curve the run does not have)
  want.sort((a, b) => a.at - b.at);
  // a card needs three seconds at the least before the car stops and drives away: if the cards do not all fit at the usual spacing they are packed closer
  const last = plan.runDur - EXIT_LEAD - 3;
  const place = (gap: number) => {
    const out: CardBeat[] = [];
    let free = 0;
    for (const w of want) {
      const from = Math.max(w.at, free);
      if (from > last) continue;
      out.push({ overlay: w.overlay, from, to: Math.min(from + CARD_HOLD, plan.runDur - EXIT_LEAD) });
      free = from + gap;
    }
    return out;
  };
  const beats = [CARD_GAP, 3.0, 2.6].map(place).reduce((best, cur) => (cur.length > best.length ? cur : best));
  return beats;
}

/** The camera at second `t` of the run: a slow drift inside a shot (eased a little at each end), a cubic whip into the next. */
export function poseAt(plan: ShowPlan, t: number): Pose {
  const { keys } = plan;
  const x = Math.min(Math.max(t, 0), plan.dur);
  let i = 0;
  while (i < keys.length - 2 && x > keys[i + 1].at) i++;
  const a = keys[i];
  const b = keys[i + 1];
  const p = clamp01((x - a.at) / Math.max(b.at - a.at, 1e-6));
  const k = b.fly ? cubic(p) : 0.55 * p + 0.45 * smooth(p);
  return { az: mix(a.az, b.az, k), el: mix(a.el, b.el, k), d: mix(a.d, b.d, k), u: mix(a.u, b.u, k), h: mix(a.h, b.h, k), lat: mix(a.lat, b.lat, k) };
}

export function chapterAt(plan: ShowPlan, t: number): Chapter {
  return plan.chapters.find((c) => t >= c.from && t < c.to) ?? plan.chapters[plan.chapters.length - 1];
}

/** How far a chapter's title is shown at second `t`: in over its first half second after the fly, out over its last, as a function of the playhead. */
export function titleK(c: Chapter, t: number, first: boolean): number {
  const s = t - c.from - (first ? 0.2 : FLY * 0.6);
  const e = c.to - t;
  return clamp01(s / 0.5) * clamp01(e / 0.5);
}
