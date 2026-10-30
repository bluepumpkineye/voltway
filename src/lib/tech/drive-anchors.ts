/**
 * Where on the car each instrument of the Drive tab belongs. A card floats next to the part of the car it explains: the suspension's
 * at the tyre's arch (the spring is over it), the brake's at the disc, the steering's at the wheel's edge, the motors' at the hubs they
 * turn, the power's and the energy's at the pack under the floor, the drag's at the roof.
 *
 * The points are in the model's frame (x forward, y up, z toward the passenger side, the rear axle at `rearX`), the frame of
 * everything that rides with the car (`CarFollower`, viewer/techRig.tsx). The viewer (viewer/TechAnchors.tsx) turns them into
 * screen points each frame, on the side of the car the camera is on, and publishes them here; the cards (showroom/DriveMotion.tsx)
 * read them. The module holds no React: the geometry is pure and checked in scripts/tech-tools/motion-test.mjs.
 */
import type { DriveOverlay } from '../../data/vehicles/schema';
import type { DriveFacts, DriveTelemetry } from './drive-run';

export type AnchorName = 'archFront' | 'archRear' | 'hubFront' | 'hubRear' | 'discFront' | 'edgeFront' | 'edgeRear' | 'battery' | 'batteryRear' | 'roof';

export const ANCHORS: readonly AnchorName[] = ['archFront', 'archRear', 'hubFront', 'hubRear', 'discFront', 'edgeFront', 'edgeRear', 'battery', 'batteryRear', 'roof'];

/** What the car's measured geometry gives, in metres, in the model's frame. */
export interface CarGeometry {
  /** the rear axle's x, and the wheelbase */
  rearX: number;
  wheelbase: number;
  /** the middle of the rear axle across the car (z) */
  midZ: number;
  /** half the track, and a wheel's radius */
  halfTrack: number;
  radius: number;
  /** half the body's width at the doors (the mirrors left out), and its height */
  halfBody: number;
  height: number;
  /** the body's extent along the car (x), for its box on screen */
  xMin: number;
  xMax: number;
}

/** A point of the car, `side` +1 the passenger's and -1 the driver's. */
export function anchorLocal(name: AnchorName, g: CarGeometry, side: 1 | -1): [number, number, number] {
  const z = g.midZ + side * g.halfTrack;
  const out = side * 0.14;
  const r = g.radius;
  const front = g.rearX + g.wheelbase;
  switch (name) {
    case 'hubFront':
      return [front, r, z + out];
    case 'hubRear':
      return [g.rearX, r, z + out];
    // the top of the tyre, where the arch and the spring are above it
    case 'archFront':
      return [front, r * 1.95, z + side * 0.1];
    case 'archRear':
      return [g.rearX, r * 1.95, z + side * 0.1];
    case 'discFront':
      return [front + 0.04, r * 0.85, z + out];
    // the leading and trailing edges of the tyres, low
    case 'edgeFront':
      return [front + r * 1.02, r * 0.6, z + out];
    case 'edgeRear':
      return [g.rearX - r * 1.02, r * 0.6, z + out];
    // the pack lies under the floor between the axles: the sill is the part of the car over it
    case 'battery':
      return [g.rearX + g.wheelbase * 0.5, 0.28, g.midZ + side * g.halfBody];
    case 'batteryRear':
      return [g.rearX + g.wheelbase * 0.28, 0.28, g.midZ + side * g.halfBody];
    case 'roof':
      return [g.rearX + g.wheelbase * 0.42, g.height * 0.995, g.midZ];
  }
}

/** The eight corners of the car's box, for its outline on screen. */
export function boxCorners(g: CarGeometry): [number, number, number][] {
  const out: [number, number, number][] = [];
  for (const x of [g.xMin, g.xMax]) for (const y of [0, g.height]) for (const s of [-1, 1]) out.push([x, y, g.midZ + s * g.halfBody]);
  return out;
}

/**
 * Where an instrument points, at this moment of the run. The suspension's follows the load: the tail squats in the pull (the rear
 * arch) and the nose dives under the brakes (the front). The motors point at the axles that have one; a steering with rear wheels
 * points at both ends.
 */
export function targetsOf(overlay: DriveOverlay, facts: DriveFacts, tel: DriveTelemetry): AnchorName[] {
  switch (overlay) {
    case 'suspension':
      return [tel.g < -0.25 ? 'archFront' : 'archRear'];
    case 'brake':
      return ['discFront'];
    case 'steering':
      return facts.rearSteerMaxDeg > 0 ? ['edgeFront', 'edgeRear'] : ['edgeFront'];
    case 'motors': {
      const front = facts.motors.some((m) => m.axle === 'front');
      const rear = facts.motors.some((m) => m.axle === 'rear');
      return front && rear ? ['hubFront', 'hubRear'] : front ? ['hubFront'] : ['hubRear'];
    }
    case 'power':
      return ['battery'];
    case 'energy':
      return ['batteryRear'];
    case 'aero':
      return ['roof'];
  }
}

// ------------------------------------------------------------------------------------------- what the viewer publishes

export interface ScreenPt {
  x: number;
  y: number;
  /** in front of the camera and inside the window (a point behind the camera is not drawn) */
  ok: boolean;
}

export interface ScreenRect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface AnchorFrame {
  /** counts each publication, so that a reader can tell when there is a new one */
  version: number;
  /** the window the points are in, px */
  width: number;
  height: number;
  /** the side of the car the camera is on */
  side: 1 | -1;
  /** the car's outline on screen */
  box: ScreenRect;
  pts: Record<AnchorName, ScreenPt>;
}

/** The latest frame of anchors on screen, or null while there is none (no car, or a camera that is inside it). */
export const driveAnchors: { frame: AnchorFrame | null } = { frame: null };
