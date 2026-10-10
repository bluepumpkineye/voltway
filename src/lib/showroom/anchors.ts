import type { AnchorId, Vehicle } from '@/data/vehicles/schema';

export type V3 = [number, number, number];

/**
 * The showroom's named camera poses, derived from a car's published size and
 * the mesh the viewer actually loaded, so a new car needs no per-car camera
 * data. A pose is where the camera sits and looks, a field of view, and the
 * limits the visitor may orbit and zoom within while it is the current pose.
 *
 * Car axes (the viewer's glTF axes): +x forward, +y up, +z toward the
 * passenger side, so the driver's side is -z. Azimuth is measured from +x
 * toward the driver's side: 0 is the nose, 90 the driver's flank, 180 the tail.
 */
export interface AnchorPose {
  id: AnchorId;
  /** interior poses mount the cabin and clear the glass; exterior ones do not */
  mode: 'exterior' | 'interior';
  pos: V3;
  target: V3;
  /** vertical field of view, degrees */
  fov: number;
  /** camera-to-target distance limits, metres */
  minDistance: number;
  maxDistance: number;
  /** polar angle limits from +y, radians */
  minPolar: number;
  maxPolar: number;
  /** drag speed; negative turns the head instead of the world */
  rotateSpeed: number;
  /**
   * Pixels to lift the picture by, so the car centres in the space above the
   * controls instead of behind them. Done in the projection (a view offset),
   * not by tilting the camera, so perspective is unchanged.
   */
  liftPx: number;
  /** a further lift, as a fraction of the window's height: what a device at the bottom covers */
  liftFrac?: number;
}

/** The bottom dock (swatches, tabs, note) takes about this much of the screen. */
const LIFT_PX = 66;

/** What the viewer measured on the loaded model. The spec is the fallback. */
export interface CarFrame {
  /** longitudinal extent of the exterior mesh, m */
  xMin: number;
  xMax: number;
  /** centre of the front-left wheel */
  wheelFL?: V3;
  /**
   * the floor a tech demo uses: its centre and the radius to keep in view, m (viewer axes); the part
   * of the window a device covers, as fractions (right: of the width, bottom: of the height), which the
   * stage is framed clear of; and the demo's preferred look (azimuth and elevation, degrees)
   */
  stage?: {
    cx: number;
    cz: number;
    radius: number;
    inset?: { right: number; bottom: number };
    camera?: { az: number; el: number };
  };
}

/** The aspect ratio every exterior pose is composed for; narrower screens pull back. */
export const REF_ASPECT = 1.78;

const D2R = Math.PI / 180;

function dirFrom(azDeg: number, elDeg: number): V3 {
  const a = azDeg * D2R;
  const e = elDeg * D2R;
  return [Math.cos(a) * Math.cos(e), Math.sin(e), -Math.sin(a) * Math.cos(e)];
}

interface Shot {
  az: number;
  el: number;
  fov: number;
  /** breathing room around the car in the frame, as a multiple of its extent */
  margin: number;
  /** picture lift, as a multiple of the dock's height (see AnchorPose.liftPx) */
  lift: number;
}

// The side and front views carry the Dimensions tab's floor rulers, whose text
// lies on the floor: a little elevation opens it up, and the front view lifts
// the car further so the rulers ahead of the nose clear the dock.
const SHOTS: Record<
  'hero' | 'doorsL' | 'doorsR' | 'side' | 'front' | 'rear' | 'rear34' | 'xray' | 'frunk' | 'trunk' | 'techWide',
  Shot
> = {
  hero: { az: 36, el: 11, fov: 30, margin: 1.3, lift: 1 },
  // the Tech tab: far enough back for a car that drives about, a high three-quarter
  techWide: { az: 38, el: 26, fov: 30, margin: 3.0, lift: 1 },
  // an open door's card faces the tail, so a door is seen from behind it: the
  // rear three-quarter of its own side
  doorsL: { az: 124, el: 10, fov: 28, margin: 1.2, lift: 1 },
  doorsR: { az: -124, el: 10, fov: 28, margin: 1.2, lift: 1 },
  // an open bonnet and an open tailgate each want a higher, closer look
  frunk: { az: 28, el: 24, fov: 28, margin: 1.2, lift: 1 },
  trunk: { az: 150, el: 22, fov: 28, margin: 1.15, lift: 1 },
  // higher, so the cabin shows through the ghosted roof
  xray: { az: 40, el: 24, fov: 30, margin: 1.3, lift: 1 },
  side: { az: 90, el: 8, fov: 20, margin: 1.4, lift: 1.15 },
  front: { az: 0, el: 9, fov: 26, margin: 1.85, lift: 1.5 },
  rear: { az: 180, el: 9, fov: 26, margin: 1.85, lift: 1.5 },
  rear34: { az: -148, el: 12, fov: 30, margin: 1.3, lift: 1 },
};

export function frameFromSpec(vehicle: Vehicle): CarFrame {
  const L = vehicle.dimensions.lengthMm / 1000;
  return { xMin: -L / 2, xMax: L / 2 };
}

const POLAR_MIN = 0.18 * Math.PI;
const POLAR_MAX = 0.495 * Math.PI;

/** The seated pose, from the camera-matched cabin's eye point (build axes to glTF). */
function driverPose(vehicle: Vehicle): AnchorPose {
  const [x, y, z] = vehicle.assets.driverEye ?? [-0.38, 0.42, 1.18];
  const pos: V3 = [x, z, -y];
  return {
    id: 'driver',
    mode: 'interior',
    pos,
    // the camera pivots 15 cm ahead of the eye, so a drag turns the head
    // rather than swinging the eye across the cabin
    target: [pos[0] + 0.142, pos[1] - 0.038, pos[2] + 0.031],
    fov: 64,
    minDistance: 0.05,
    maxDistance: 0.3,
    minPolar: 0.2 * Math.PI,
    maxPolar: 0.74 * Math.PI,
    rotateSpeed: -0.32,
    liftPx: 0,
  };
}

export function resolveAnchor(
  id: AnchorId,
  vehicle: Vehicle,
  frame: CarFrame,
  aspect: number,
): AnchorPose {
  if (id === 'driver') return driverPose(vehicle);

  const H = vehicle.dimensions.heightMm / 1000;
  const W = vehicle.dimensions.widthMm / 1000;
  const L = frame.xMax - frame.xMin;
  const cx = (frame.xMin + frame.xMax) / 2;

  if (id === 'wheel') {
    const w: V3 = frame.wheelFL ?? [cx + L * 0.28, 0.36, -W * 0.42];
    const target: V3 = [w[0] - 0.12, w[1] + 0.02, w[2]];
    const d = dirFrom(64, 7);
    const dist = 2.7;
    return {
      id,
      mode: 'exterior',
      pos: [target[0] + d[0] * dist, target[1] + d[1] * dist, target[2] + d[2] * dist],
      target,
      fov: 24,
      minDistance: 1.3,
      maxDistance: 4.6,
      minPolar: POLAR_MIN,
      maxPolar: POLAR_MAX,
      rotateSpeed: 0.55,
      liftPx: LIFT_PX * 0.6,
    };
  }

  if (id === 'techWide') {
    // keep a circle of floor in view: the stage a demo uses, or a few metres round the car
    const st = frame.stage ?? { cx, cz: 0, radius: L * 0.9 };
    const s = SHOTS.techWide;
    const az = st.camera?.az ?? s.az;
    const el = st.camera?.el ?? s.el;
    // a device over the right of the window, or the bottom of it, leaves less to frame the stage in
    const inset = st.inset ?? { right: 0, bottom: 0 };
    const half = Math.tan((s.fov * D2R) / 2);
    const elv = el * D2R;
    // the circle must fit across what is left of the screen, and (foreshortened by the elevation, plus the car's height) up it
    const fitAcross = st.radius / (half * Math.max(aspect * (1 - inset.right), 0.3));
    const fitUp = (st.radius * Math.sin(elv) + H) / (half * Math.max(1 - inset.bottom, 0.3));
    const dist = 1.1 * Math.max(fitAcross, fitUp);
    const d = dirFrom(az, el);
    // the stage is centred in the free part of the window: the target goes to the right of it, by the
    // covered share of the half-width the camera sees at that distance (the camera's right is (dz, 0, -dx))
    const side = (inset.right * dist * half * Math.max(aspect, 0.3)) / (Math.hypot(d[0], d[2]) || 1);
    const target: V3 = [st.cx + d[2] * side, H * 0.3, st.cz - d[0] * side];
    return {
      id,
      mode: 'exterior',
      pos: [target[0] + d[0] * dist, target[1] + d[1] * dist, target[2] + d[2] * dist],
      target,
      fov: s.fov,
      minDistance: dist * 0.5,
      maxDistance: dist * 1.6,
      minPolar: POLAR_MIN,
      maxPolar: POLAR_MAX,
      rotateSpeed: 0.55,
      liftPx: LIFT_PX * s.lift,
      liftFrac: inset.bottom / 2,
    };
  }

  const s = SHOTS[id];
  const az = s.az * D2R;
  // the car's footprint projected across and along the line of sight
  const across = L * Math.abs(Math.sin(az)) + W * Math.abs(Math.cos(az));
  const depth = L * Math.abs(Math.cos(az)) + W * Math.abs(Math.sin(az));
  const el = s.el * D2R;
  const tall = H * Math.cos(el) + depth * Math.sin(el);
  const half = Math.tan((s.fov * D2R) / 2);

  const fitX = (across * s.margin) / (2 * half * REF_ASPECT);
  const fitY = (tall * s.margin) / (2 * half);
  // nearer parts of the car read bigger, so stand back by part of its half depth
  let dist = Math.max(fitX, fitY) + depth * 0.25;
  // a narrow window cannot hold the composed width: stand further back
  dist *= Math.max(1, REF_ASPECT / Math.max(aspect, 0.2));

  const target: V3 = [cx, H * 0.4, 0];
  const d = dirFrom(s.az, s.el);
  return {
    id,
    mode: 'exterior',
    pos: [target[0] + d[0] * dist, target[1] + d[1] * dist, target[2] + d[2] * dist],
    target,
    fov: s.fov,
    minDistance: dist * 0.62,
    maxDistance: dist * 1.45,
    minPolar: POLAR_MIN,
    maxPolar: POLAR_MAX,
    rotateSpeed: 0.55,
    liftPx: LIFT_PX * s.lift,
  };
}
