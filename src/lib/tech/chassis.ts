/**
 * The chassis demos' words (docs/tech-showcase.md, section 14): what each is called, what its start button says, and what
 * the one button does at each point of its run. Shared by the car's chassis page, the device column and the dock, so
 * they always agree. A demo with a stop (e³ parking waits, nose in the gap, for the driver to start the pivot) is read
 * as the parking demos are; one without is read as the Magic Carpet's run is.
 */
import type { ClockSnapshot } from './clock';
import { parkPhase, runPhase } from './phase';

export interface ChassisCopy {
  title: string;
  /** the button before the run */
  start: string;
  /** the button at the run's stop, when it has one */
  stop?: string;
  /** what the big figure on the car's screen is */
  figure: string;
  /** one line under the picture of the wheels */
  hint: string;
  /** what the car is doing while it runs */
  doing: string;
}

export const CHASSIS: Record<string, ChassisCopy> = {
  crab: {
    title: 'Crab walk',
    start: 'Slide to the kerb',
    figure: 'Crab angle',
    hint: 'All four wheels turn the same way and the car moves along a diagonal without turning. The front wheels take the angle; the rear ones follow as far as their ±10° allows.',
    doing: 'The car slides to the kerb',
  },
  compass: {
    title: 'Compass turn',
    start: 'Compass turn',
    figure: 'Turned',
    hint: 'One front wheel is held still and the car turns about it, the rear wheels splayed out and driven against each other.',
    doing: 'The car turns about its held wheel',
  },
  e3park: {
    title: 'e³ parking',
    start: 'Pull in',
    stop: 'Pivot',
    figure: 'Angle to the kerb',
    hint: 'The car pulls its nose into the gap and stops. The left front wheel is held and the car turns about it, so the tail swings in and it ends parallel to the kerb.',
    doing: 'The car pivots about its left front wheel',
  },
  uturn: {
    title: 'Rear-wheel steering',
    start: 'U-turn',
    figure: 'Turned',
    hint: 'The rear wheels steer against the fronts, so the car turns on a tighter circle than its front wheels alone would give.',
    doing: 'The car turns round',
  },
};

export const isChassisDriver = (driver: string) => driver in CHASSIS;

export type ChassisPhase = 'ready' | 'driving' | 'paused' | 'stopped' | 'done';

/** Where a chassis demo's run is. `stopped` is a run with a stop standing at it, waiting for the driver. */
export function chassisPhase(c: ClockSnapshot): ChassisPhase {
  if (c.stops.length) {
    const p = parkPhase(c);
    if (p === 'ready') return 'ready';
    if (p === 'parked') return 'stopped';
    if (p === 'done') return 'done';
    if (p === 'parking' || p === 'leaving') return 'driving';
    return 'paused';
  }
  return runPhase(c);
}

/** What the one button says and does at this point: start, pause, resume, the stop's own button, again. */
export function chassisAction(
  driver: string,
  c: ClockSnapshot,
  go: () => void,
  pause: () => void,
): { label: string; run: () => void } {
  const copy = CHASSIS[driver];
  switch (chassisPhase(c)) {
    case 'driving':
      return { label: 'Pause', run: pause };
    case 'paused':
      return { label: 'Resume', run: go };
    case 'stopped':
      return { label: copy?.stop ?? 'Go on', run: go };
    case 'done':
      return { label: 'Again', run: go };
    default:
      return { label: copy?.start ?? 'Start', run: go };
  }
}

/** What the guidance line says for a demo at this point. */
export function chassisCoach(driver: string, c: ClockSnapshot): string {
  const copy = CHASSIS[driver];
  switch (chassisPhase(c)) {
    case 'driving':
      return `${copy?.doing ?? 'The car moves'}. Watch the wheels on the car’s screen.`;
    case 'paused':
      return 'Paused. Resume, or go again from the top.';
    case 'stopped':
      return 'Nose in the gap. The pivot wheel is the left front one: press Pivot on the car’s screen.';
    case 'done':
      return 'Done. Go again from the top.';
    default:
      return driver === 'compass'
        ? 'Choose the wheel and the angle below, then start it on the car’s screen.'
        : `Start it on the car’s screen: ${copy?.start.toLowerCase() ?? 'go'}.`;
  }
}
