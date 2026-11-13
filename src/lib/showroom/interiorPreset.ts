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
