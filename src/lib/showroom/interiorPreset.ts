/**
 * The Interior tab's camera preset, shared by every car (src/components/viewer/cabinfx/ is the look; this is the lens).
 *
 * `fov` is the seat's vertical field of view in degrees: 52, the low end of the 52-56 band the owner approved on the BYD Seal.
 * A car may still set its own `assets.driverView.fov`. On a portrait window the lens opens out so the centre screen is not cut
 * off, but never past `fovMax`, beyond which the doors, mirrors and the wheel's rim stretch toward the picture's edges.
 * `yawLimitDeg` is how far the visitor may turn their head either side of the pose's own look: the seat's eye is at the
 * headrest's front, so a turn past this puts the camera inside the driver's headrest.
 */
export const INTERIOR_PRESET = {
  fov: 52,
  fovMax: 56,
  yawLimitDeg: 110,
} as const;

/**
 * Cars left exactly as they were before the interior upgrade (cabinfx): no composer, no material or glass changes, no live cluster,
 * the old 46 degree seat lens and no head-turn limit. The Avatr 06T: its own render (the baked light map, the original cluster) is
 * better than the upgrade's, the owner's call on 2026-11-13.
 */
export const CABIN_FX_EXCLUDED: readonly string[] = ['avatr-06t'];

export const cabinFxExcluded = (slug: string): boolean => CABIN_FX_EXCLUDED.includes(slug);

/** The seat's lens and head-turn limit for a car: the shared preset, or what an excluded car always had. */
export function interiorPresetFor(slug: string): { fov: number; fovMax: number; yawLimitDeg: number | null } {
  return cabinFxExcluded(slug) ? { fov: 46, fovMax: 88, yawLimitDeg: null } : INTERIOR_PRESET;
}
