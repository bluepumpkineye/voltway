import type { PlannedRun, Sample } from './kinematics';

/**
 * The Luxeed RX's BOOST demo (docs/tech-showcase.md section 13): from the driver's seat the BOOST knob on the steering wheel
 * is pressed, its ring lights blue (Autohome's photographs of the button lit and not, board T3e), and what the maker says
 * BOOST does is applied in turn on the car's screen; a second press ends it.
 *
 * Published (the maker's page, "some trims only"): one press of BOOST raises instantaneous torque by 10 %, with its own
 * throttle calibration (more linear), its own chassis tune, a three-screen linkage with a sport sound, and the seat
 * belts and seat bolsters tightening at once; the motor's up to 21,000 rpm, 251 km/h, 98.2 % efficiency and torque
 * response within 1 ms. Ours, said on the panel: the order and the timing of the steps, and the screen that lists them (a
 * stand-in: the maker's BOOST screens are not photographed, so nothing here is a copy of them). No value imports.
 */

/** the steps the maker lists, in the order the demo applies them, and when (s) */
export const STEPS = [
  { id: 'torque', label: 'Instantaneous torque', detail: '+10 %', t: 1.5 },
  { id: 'throttle', label: 'Throttle map', detail: 'Its own calibration, more linear', t: 2.3 },
  { id: 'chassis', label: 'Chassis', detail: 'Its own tune', t: 3.1 },
  { id: 'screens', label: 'Screens and sound', detail: 'Three-screen linkage, sport sound', t: 3.9 },
  { id: 'belts', label: 'Belts and seat bolsters', detail: 'Tighten at once', t: 4.7 },
] as const;
export type StepId = (typeof STEPS)[number]['id'];

/** the two presses of the knob, s, and the end of the run */
export const PRESS_ON = 1.0;
export const PRESS_OFF = 8.2;
export const T_END = 10.6;

export interface BoostState {
  /** BOOST is on (from the first press to the second) */
  on: boolean;
  /** how many of the steps have been applied */
  step: number;
}

export interface BoostRun {
  track: PlannedRun;
  state: (t: number) => BoostState;
}

export function planBoost(start: { x: number; y: number; yaw: number }): BoostRun {
  const track: PlannedRun = {
    duration: T_END,
    stats: { maxSteer: 0, bounds: { min: { x: start.x, y: start.y }, max: { x: start.x, y: start.y } } },
    sample: (): Sample => ({ ...start, steer: [0, 0, 0, 0], spin: [0, 0, 0, 0], speed: 0, segment: 0, phase: 'dwell' }),
    trace: () => [],
  };
  const state = (t: number): BoostState => {
    if (t < PRESS_ON || t >= PRESS_OFF) return { on: false, step: 0 };
    return { on: true, step: STEPS.filter((s) => t >= s.t).length };
  };
  return { track, state };
}
