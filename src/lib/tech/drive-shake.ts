/**
 * The Drive tab's camera shake: a little handheld unsteadiness on the picture while the car is at speed, so that the shot reads as filmed from a
 * moving platform and not from a tripod. No React and no three.js; a pure function of the playhead and the car's speed, so a scrubbed run shows the same
 * shake as a played one.
 *
 * The numbers are the owner's, from Blender's Noise modifier on the camera's rotation curves: strength 0.03 on the X rotation (the tilt, up and down) and
 * 0.08 on the Z rotation (the pan, side to side). A Noise modifier adds (noise - 0.5) x strength to the curve, in the curve's own unit, which for a rotation
 * is the radian: the strength is the peak-to-peak size of the noise, so the tilt wanders at most 0.015 rad (0.9 degrees) either way and the pan at most
 * 0.04 rad (2.3 degrees), and a typical moment is a third of that. That is what `noise` below makes: smooth, in -0.5 to 0.5, two octaves (the modifier's
 * depth 1), from a hashed lattice so that it needs no table and the same time always gives the same value.
 *
 * Drawn at `gain` (0.3) of that: the full strengths were tried first and found exaggerated, and nauseous (a pan of up to 2.3 degrees is a tenth of a 30 degree
 * frame), so the shake is the same noise at a third of the size. The strengths stay the owner's; the gain is ours, and one number.
 *
 * What the modifier does not say, and is ours: its scale (how long one wander lasts: here 0.55 s with a finer 0.23 s ripple on it), its seeds (the two axes
 * must not move together), and when it is on. "The car moves a bit before the camera shakes": the shake begins `DELAY_S` after the car's first move
 * and fades in over `RAMP_S`, and it follows the car's speed (nothing at a standstill, all of it from about 70 km/h), because what shakes a camera on
 * a real shoot is the platform it stands on.
 *
 * It is applied as a shift of the picture in the camera rig (viewer/ShowroomCameraRig.tsx), not a turn of the camera: for angles this small the two look
 * the same, and the orbit controls, which own the camera's pose, are left alone.
 */

export const SHAKE = {
  /** Blender's noise strengths, rad (peak to peak): the tilt (X rotation) and the pan (Z rotation) */
  tilt: 0.03,
  pan: 0.08,
  /** how much of the strengths is drawn: the owner's strengths at full size were exaggerated and nauseous */
  gain: 0.3,
  /** the shake begins this long after the car's first move, s, and takes this long to come to its full size */
  delayS: 1.2,
  rampS: 1.6,
  /** one wander of the noise lasts about this long, s, and the ripple on it about this */
  periodS: 0.55,
  rippleS: 0.23,
  /** the speed the shake is at its full size from, km/h, and the one under which there is none */
  fullKmh: 70,
  noneKmh: 8,
  /** as the car drives away in the exit the shake fades out between these distances from where the run ended, m (the haze has the car by about 110) */
  leaveFromM: 10,
  leaveToM: 80,
} as const;

/** The shake the camera rig draws now, set each frame by the run's director (viewer/TechDirector.tsx): rad of tilt and of pan. */
export const cameraShake = { tilt: 0, pan: 0 };

const frac = (n: number) => {
  const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};
const smooth = (x: number) => {
  const t = Math.min(1, Math.max(0, x));
  return t * t * (3 - 2 * t);
};
/** smooth value noise in -0.5 to 0.5: one random value per lattice point, `seed` apart for each axis, eased between them */
function lattice(x: number, seed: number): number {
  const i = Math.floor(x);
  const u = x - i;
  const e = u * u * (3 - 2 * u);
  const a = frac(i * 1.7 + seed) - 0.5;
  const b = frac((i + 1) * 1.7 + seed) - 0.5;
  return a + (b - a) * e;
}
/** two octaves (the second at 0.4 of the first), scaled so that the peak stays 0.5 */
function noise(t: number, seed: number): number {
  return (lattice(t / SHAKE.periodS, seed) + 0.4 * lattice(t / SHAKE.rippleS, seed + 41.3)) / 1.4;
}

/**
 * How much of the shake is on, 0 to 1, at `t` seconds with the car going `speedKmh`: nothing until `delayS` after `tMove`, the time the car first moved, then a
 * smooth rise over `rampS`, and in proportion to the speed.
 */
export function shakeAmount(t: number, tMove: number, speedKmh: number): number {
  const start = smooth((t - tMove - SHAKE.delayS) / SHAKE.rampS);
  const speed = smooth((speedKmh - SHAKE.noneKmh) / (SHAKE.fullKmh - SHAKE.noneKmh));
  return start * speed;
}

/**
 * How much of the shake is left when the car has driven `x` metres off from where the run ended (the exit, drive-exit.ts): all of it up to `leaveFromM`, none
 * from `leaveToM`, smooth between. 1 when there is no exit (`x` is 0).
 */
export function shakeLeave(x: number): number {
  return 1 - smooth((x - SHAKE.leaveFromM) / (SHAKE.leaveToM - SHAKE.leaveFromM));
}

/** The tilt and the pan of the camera, rad, at `t` when the shake is `amount` on. */
export function shakeAt(t: number, amount: number): { tilt: number; pan: number } {
  return { tilt: noise(t, 3.1) * SHAKE.tilt * SHAKE.gain * amount, pan: noise(t, 17.9) * SHAKE.pan * SHAKE.gain * amount };
}

/**
 * The first moment the car has moved: `distance(t)` is how far it has gone at `t`. A run that begins at speed gives 0. `duration` bounds the search; a run
 * that never moves gives `duration`.
 */
export function firstMove(distance: (t: number) => number, duration: number): number {
  const d0 = distance(0);
  for (let t = 0; t <= duration; t += 1 / 30) if (distance(t) - d0 > 0.3) return t;
  return duration;
}
