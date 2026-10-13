import type { PlannedRun, Sample } from './kinematics';

/**
 * The Luxeed RX's swivel screen demo (docs/tech-showcase.md section 13): the centre screen turns toward the driver,
 * then toward the passenger, comes back to the middle and slides forward and back, as the four buttons of its
 * "centre screen direction adjust" dialog (Autohome's photograph, board T3e) ask. The seat's view of it.
 *
 * Published (the maker's page): a 16.1 in screen, four ways, 55 mm forward and back, up to 30 degrees left and
 * right, "some trims only". Ours, said on the panel: the order of the presses, and how fast it moves (no speed is
 * published). No value imports: it runs under plain Node.
 */

/** Which way the motorised screen faces, and whether it stands pulled back (toward the driver) or forward. */
export type Turn = 'driver' | 'centre' | 'passenger';
export type Slide = 'rear' | 'front';

export interface ScreenPose {
  turn: Turn;
  slide: Slide;
}

/** which way each turn faces, in units of the full turn (toward the passenger is +, as the cabin model's y rotation) */
export const TURN_SIGN: Record<Turn, number> = { driver: -1, centre: 0, passenger: 1 };

/** the four buttons of the dialog, and the pose each sets (a turn keeps the slide it has) */
export const BUTTONS = [
  { id: 'centre-rear', label: 'Centre, rear', turn: 'centre', slide: 'rear' },
  { id: 'centre-front', label: 'Centre, front', turn: 'centre', slide: 'front' },
  { id: 'driver', label: 'Toward driver', turn: 'driver', slide: null },
  { id: 'passenger', label: 'Toward passenger', turn: 'passenger', slide: null },
] as const;
export type ButtonId = (typeof BUTTONS)[number]['id'];

/** the screen's speed (ours): the angle and the slide ease toward their goals at about this much a second */
export const MAX_TURN_RATE = 26; // deg/s
export const MAX_SLIDE_RATE = 0.03; // m/s

/** the presses of the run: when (s), which button */
export const PRESSES: { t: number; button: ButtonId }[] = [
  { t: 1.2, button: 'driver' },
  { t: 4.6, button: 'passenger' },
  { t: 8.6, button: 'centre-front' },
  { t: 12.0, button: 'centre-rear' },
];
export const T_END = 15.2;

export interface SwivelRun {
  track: PlannedRun;
  /** the pose the car's screen has been asked for at time t, and the button that asked (null before the first press) */
  pose: (t: number) => ScreenPose & { button: ButtonId | null };
}

/** The pose a press leaves, from the pose before it. */
export function afterPress(from: ScreenPose, button: ButtonId): ScreenPose {
  const b = BUTTONS.find((x) => x.id === button)!;
  return { turn: b.turn, slide: b.slide ?? from.slide };
}

export function planSwivel(start: { x: number; y: number; yaw: number }): SwivelRun {
  const track: PlannedRun = {
    duration: T_END,
    stats: { maxSteer: 0, bounds: { min: { x: start.x, y: start.y }, max: { x: start.x, y: start.y } } },
    sample: (): Sample => ({ ...start, steer: [0, 0, 0, 0], spin: [0, 0, 0, 0], speed: 0, segment: 0, phase: 'dwell' }),
    trace: () => [],
  };
  const pose = (t: number) => {
    let p: ScreenPose = { turn: 'centre', slide: 'rear' };
    let button: ButtonId | null = null;
    for (const press of PRESSES) {
      if (t < press.t) break;
      p = afterPress(p, press.button);
      button = press.button;
    }
    return { ...p, button };
  };
  return { track, pose };
}
