/**
 * The car leaving: how a Drive run ends when the car is still moving at its last second. Instead of freezing the picture at speed, the clock runs
 * on for a few seconds (the exit) and the car carries on down the road, past a camera that stays where it is, until the haze has it.
 *
 * Used by the X-ray tab's Play (the car sets off from rest or carries on, and speeds up) and by the Drive tab (the car carries on at the speed it
 * was going). No React and no three.js; a pure function of the playhead, so a scrubbed run shows the same picture as a played one. What is drawn is
 * ours: a simple curve, drawn only so that the car leaves; it is not a measured run.
 */

/** The top speed the car reaches in Play's exit, m/s (about 210 km/h: it only has to be gone before the haze has it) */
export const EXIT_VMAX = 58;
/** how long a car that was standing waits after the run's end before it drives off, s */
const GO_AFTER = 0.3;
/** how far the car has to go to be lost in the haze, m: the Drive tab's exit lasts as long as that takes at the run's end speed */
const GONE_M = 110;

/** The pull of the car in Play's exit, m/s2, set by the run's director (viewer/TechDirector.tsx) from the car's own 0-100: the viewer's lights read it too. */
export const exitPull = { a0: 10 };

/** The exit of the run that is up, written by the run's director (viewer/TechDirector.tsx) and read by what draws it (the Drive tab's fog): the clock's whole length is `duration`, `exit` of it the exit, `v0` the speed at the run's end, `accel` the car speeds up in it (Play's; the Drive tab's after a run that ended standing) and does not just carry on. */
export const exitInfo = { duration: 0, exit: 0, v0: 0, show: false, accel: false };

export interface ExitState {
  /** metres the car has gone since the run's end */
  x: number;
  /** m/s */
  v: number;
  /** 0..1, how hard it is pulling now (the squat, the motors' load) */
  pull: number;
}

/**
 * The car leaving, `t` seconds into the clock (`run.duration` is the clock's end and `run.exit` how much of it is the exit): from rest (a run that
 * ends in a stop: it waits `GO_AFTER`) or from the speed it was going at the run's end `v0` (m/s). It approaches `vmax` exponentially at a0 m/s2 (Play:
 * 58 m/s, or more if it was faster); with `vmax` equal to `v0` it simply carries on at its speed (the Drive tab).
 */
export function exitAt(run: { duration: number; exit: number }, t: number, a0: number, v0 = 0, vmax?: number): ExitState {
  const s = t - (run.duration - run.exit);
  const moving = v0 >= 1;
  const u = s - (moving ? 0 : GO_AFTER);
  if (s <= 0) return { x: 0, v: v0, pull: 0 };
  if (u <= 0) return { x: moving ? v0 * s : 0, v: v0, pull: 0 };
  const top = vmax ?? Math.max(EXIT_VMAX, v0 * 1.15);
  const tau = top / a0;
  const e = Math.exp(-u / tau);
  return { x: top * u - (top - v0) * tau * (1 - e), v: top - (top - v0) * e, pull: ((top - v0) / top) * e };
}

/** How long the Drive tab's exit lasts for a car going `v0` m/s at the run's end: long enough to be lost in the haze (110 m), between 3.5 and 8 s. */
export function driveExitS(v0: number): number {
  return Math.min(8, Math.max(3.5, GONE_M / Math.max(v0, 1)));
}

/**
 * The speed at the run's end, m/s, from which the Drive tab's exit is the car carrying on at its speed (about 54 km/h): a car that is slower at the end (a
 * slalom or a crab walk, which end at 16 and 7 km/h, or a stop the visitor chose) speeds up and drives away instead, from the speed it has (or from rest).
 */
export const DRIVE_CARRY_MS = 15;
/** The Drive tab's exit after a run that ends slowly or standing: the car speeds up and drives away, s (about 110 m at the pull of its own 0-100). */
export const DRIVE_REST_EXIT_S = 6;

/**
 * How far into the exit the clock is, 0..1 over its first 1.5 s (a smooth ramp): the Drive tab's fog comes in with it, so that the car fades into the
 * studio's white as it leaves and the rest of the scene does not change at once.
 */
export function exitFog(run: { duration: number; exit: number }, t: number): number {
  const s = t - (run.duration - run.exit);
  if (run.exit <= 0 || s <= 0) return 0;
  const x = Math.min(1, s / 1.5);
  return x * x * (3 - 2 * x);
}

/** The car's distance from where it was at the run's end over which its sound fades, m: it is at full level to the first and gone at the second (the fog has it by about 110 m) */
const SOUND_NEAR_M = 8;
const SOUND_GONE_M = 100;

/**
 * How near the car sounds as it drives away in the exit, 1 beside the camera to 0 when it is lost in the haze: a function of the metres it has gone since
 * the run's end (`ExitState.x`), smoothed. The Drive tab's motor follows it (lib/sound/drive-engine.ts `update`): quieter and duller (the air takes the
 * highs) as the car recedes, silent when it is gone.
 */
export function soundProximity(x: number): number {
  const t = Math.min(1, Math.max(0, (x - SOUND_NEAR_M) / (SOUND_GONE_M - SOUND_NEAR_M)));
  return 1 - t * t * (3 - 2 * t);
}
