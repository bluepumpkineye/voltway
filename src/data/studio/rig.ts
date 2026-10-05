/**
 * Voltway's studio light rig, defined once.
 *
 * The room the car stands in is white, but the paint does not reflect the
 * room: it reflects THIS, a dark studio with a handful of bright shapes in it.
 * That is what puts the crisp stripe highlights down the flanks and keeps the
 * colour of a dark paint from washing out under a white sky.
 *
 * The web draws the rig live (drei Lightformers into a cube map, see
 * StudioShowroom). Blender builds the same list as emissive planes over a black
 * world and renders its panoramas and studio stills from it (carkit.studio,
 * planned in docs/hima-benchmark.md), so the web view and the Cycles renders
 * agree by construction rather than by eye.
 *
 * Axes are the car's own, in metres, origin on the floor at the car's centre:
 * +x forward, +y up, +z toward the passenger side (the viewer's glTF axes).
 * Blender's equivalent of a point is (x, -z, y).
 *
 * A panel without `rotation` faces the origin with its local up along world
 * +y. A panel that has to face straight up or down must give a `rotation`
 * (Euler XYZ, radians), because "up" is undefined there.
 */
export type V3 = [number, number, number];

export interface RigPanel {
  id: string;
  /** rect: size is [width, height]; circle: size is [diameter, diameter]. */
  form: 'rect' | 'circle';
  position: V3;
  size: [number, number];
  /** Radiance multiplier on `color`. Values above 1 are fine: the cube is float. */
  intensity: number;
  color?: string;
  rotation?: V3;
}

/** The dark of the room between the panels, sRGB. */
export const STUDIO_VOID = '#22252a';

/** Overall gain on the rig as image-based light (the viewer's scene.environmentIntensity). */
export const STUDIO_GAIN = 1.4;

const FLAT: V3 = [-Math.PI / 2, 0, 0];

export const STUDIO_RIG: RigPanel[] = [
  // overhead key: one large soft box over the car, its long axis along it
  { id: 'top', form: 'rect', position: [0.2, 7.5, 0], rotation: FLAT, size: [9, 4.6], intensity: 4.2 },
  // a horizon strip down each flank: the signature stripe along the shoulder
  { id: 'strip-left', form: 'rect', position: [0, 2.3, -7], size: [12, 0.85], intensity: 7.5 },
  { id: 'strip-right', form: 'rect', position: [0, 2.3, 7], size: [12, 0.85], intensity: 7.5 },
  // broad side panels to roll a soft highlight over the doors and haunches
  { id: 'panel-left', form: 'rect', position: [-1.5, 3.2, -9], size: [5, 3.6], intensity: 1.8, color: '#f4f7ff' },
  { id: 'panel-right', form: 'rect', position: [-1.5, 3.2, 9], size: [5, 3.6], intensity: 1.8, color: '#f4f7ff' },
  // flags ahead of and behind the car for the bonnet and the tail
  { id: 'front', form: 'rect', position: [8, 2.6, 0], size: [6, 2.6], intensity: 2.2 },
  { id: 'rear', form: 'rect', position: [-8, 2.6, 0], size: [6, 2.6], intensity: 2.2 },
  // The white floor, in two zones. A flank seen from above mirrors the floor,
  // not the strips, so a uniform floor leaves it flat; a brighter zone near the
  // car over a dimmer far one gives the lower body a gradient that moves as the
  // camera does.
  { id: 'floor', form: 'circle', position: [0, -1, 0], rotation: FLAT, size: [120, 120], intensity: 0.55 },
  { id: 'floor-near', form: 'circle', position: [0, -0.98, 0], rotation: FLAT, size: [15, 15], intensity: 1.25 },
];
