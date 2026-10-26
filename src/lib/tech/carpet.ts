import { Track, type Layout, type Motion, type Segment } from './kinematics';
import type { Pose } from './park';
import { simulateRide, type Hump, type RideMode, type RideRun } from './ride';

/**
 * The Magic Carpet demo's run (docs/tech-showcase.md): the car drives straight over three rubber speed humps
 * at about 16 km/h, and the body either rides them out (a passive suspension) or floats (the Magic Carpet).
 *
 * The car stays on the spot and the road rolls under it (`RigState.scroll`): the camera and the car's baked
 * shadow need not follow it, and the humps travel past the wheels exactly as the car's own distance says.
 * Everything here is ours (the humps' size, their spacing, the speed); the maker publishes none of it.
 */

/** A rubber hump about 5 cm high and 40 cm across (typical products), three of them 3.6 m apart. */
export const HUMP_HEIGHT = 0.05;
export const HUMP_LENGTH = 0.4;
export const HUMP_GAP = 3.6;
/** The run's cruising speed, m/s (16 km/h): near the bounce of the body, so a passive car is seen to bob. */
export const RUN_SPEED = 4.5;
/** Where the first hump lies, as a distance from the rear axle's start, m. */
const FIRST_HUMP = 14;
/** How far the rear axle goes, m. */
const RUN_LENGTH = 30;

const MOTION: Motion = { vmax: RUN_SPEED, accel: 1.6, steerRate: 1, dwell: 0, steerMin: 0.4 };

/** The road of the run, in distances from the rear axle's start. */
export interface RoadStage {
  humps: Hump[];
  /** the strip of road, from where it begins to where it ends, m (run distance) */
  from: number;
  to: number;
  /** how wide, m */
  width: number;
  /** the broken edge lines' period and dash, and the spacing of the tar joints, m (the default suits a slow run) */
  markings?: { period: number; length: number; joint: number };
  /** a road of several lanes (Autonomous Drive's): how many and how wide; it is drawn with dashed lane lines and solid edge lines, not the broken edge lines above */
  lanes?: { count: number; width: number };
  /** a city street (Autonomous Drive on the G9L): kerbs, footways, painted lines and crossings */
  city?: CityRoad;
}

/**
 * A street the car drives along, in the road's frame (x along it from the car's start, y across it, left of the car's lane
 * positive). The asphalt, the kerbs and the footways stand under the car; what repeats (`period`) is rolled by the rig as far
 * as its period; the crossings and the stop lines roll with the road.
 */
export interface CityRoad {
  nearKerb: number;
  farKerb: number;
  /** the width of each footway beyond a kerb, m */
  footway: number;
  /** the repeat of the lamps, trees, buildings and joints, m */
  period: number;
  /** painted lines along the street */
  lines: { y: number; dash: boolean; color: 'white' | 'yellow' }[];
  crossings: { x: number; length: number }[];
  stopLines: { x: number; y0: number; y1: number }[];
  /** traffic signals (the Seal's traffic-light scene): a mast on the footway with an arm over the carriageway */
  signals?: CitySignal[];
}

export type SignalState = 'green' | 'amber' | 'red';

/** A signal: its mast, the heads that hang from the arm (facing the car as it comes), and which lamp is lit at time t. */
export interface CitySignal {
  /** along the street, m */
  x: number;
  /** the mast's place across the street, m left of the car's lane (on the footway) */
  pole: number;
  /** where the heads hang across the street, m: the car's lane, and the one beside it */
  heads: number[];
  /** how far off the car has the signal, from its nose to the mast, m (ours: the cameras read a head from much further) */
  reach: number;
  state: (t: number) => SignalState;
}

export interface CarpetRun {
  track: Track;
  road: RoadStage;
  /** the same run with each suspension: the body and the wheels at any time, and the largest motions */
  modes: Record<RideMode, RideRun>;
  /** how far the road has rolled at time t, m */
  scroll: (t: number) => number;
  /** where the camera looks: the car at rest, and its preferred angle */
  frame: { cx: number; cz: number; radius: number; camera: { az: number; el: number } };
}

export interface CarpetOptions {
  /** the drive mode's stiffness against Comfort */
  stiffness: number;
}

/** The drive modes' stiffness against Comfort: ours, a visible difference and no more. */
export function stiffnessOf(modeId: string | null | undefined): number {
  switch (modeId) {
    case 'sport':
      return 1.25;
    case 'off-road':
    case 'offroad':
      return 1.1;
    case 'economy':
    case 'eco':
      return 1.05;
    default:
      return 1;
  }
}

export function planCarpet(
  layout: Layout,
  body: { rear: number; front: number; halfWidth: number },
  start: Pose,
  opts: CarpetOptions,
): CarpetRun {
  const plan: Segment[] = [{ kind: 'move', distance: RUN_LENGTH }];
  const track = new Track(layout, plan, MOTION, start);
  const humps: Hump[] = [0, 1, 2].map((i) => ({ x: FIRST_HUMP + i * HUMP_GAP, height: HUMP_HEIGHT, length: HUMP_LENGTH }));
  const travelled = (t: number) => track.sample(t).x - start.x;
  const radiusF = (layout.radius.FL + layout.radius.FR) / 2;
  const radiusR = (layout.radius.RL + layout.radius.RR) / 2;
  // both suspensions over the same road: the visitor compares them, and the chart draws both
  const car = { wheelbase: layout.wheelbase, radiusF, radiusR };
  const sim = (active: boolean) =>
    simulateRide(car, humps, travelled, track.duration, { active, stiffness: opts.stiffness });
  const length = body.rear + body.front;
  return {
    track,
    road: { humps, from: -12, to: RUN_LENGTH + 14, width: 5.2 },
    modes: { carpet: sim(true), passive: sim(false) },
    scroll: travelled,
    frame: {
      // the car at rest, in the viewer's frame (the rear axle is at start.x)
      cx: start.x + (body.front - body.rear) / 2,
      cz: -start.y,
      radius: length * 0.62,
      camera: { az: 72, el: 9 },
    },
  };
}
