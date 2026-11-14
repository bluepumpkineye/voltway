import type { PlannedRun, Sample } from './kinematics';

/**
 * The NIO ES8's NOMI demo (docs/tech-showcase.md section 28): NOMI is the round-faced companion that sits on the dashboard. The
 * car stands still and the camera is in the driver's seat; the demo plays three of the things NOMI is published to do, in turn:
 *
 *  - greets a door: it senses a door open and turns its head to it and greets (Baidu Baike on NOMI Mate 3.0; CnEVPost, 2021, for the
 *    first generation: it turns its face toward whoever opens a door and says hello);
 *  - turns toward a voice: its gaze goes to the sound (CHINA CASE, July 2025), and it nods in reply ("nods in silence", same page);
 *  - sways with music (Baidu Baike and CHINA CASE).
 *
 * Published too: a round AMOLED face (more than 200 expressions), two motors, one for each axis, near-silent brushless drive. The
 * travel is one source's: about 100 degrees across and 30 up and down (Baidu Baike); another says up to 340 degrees (CHINA CASE), so
 * the smaller is used. Ours, said on the panel: what happens in which order and when, every pose and its speed, the faces drawn
 * (a handful of the 200), the words. No value imports: it runs under plain Node.
 */

/** the head's travel, in total, degrees: one source's (the other says 340 across) */
export const SWEEP = { yaw: 100, pitch: 30 } as const;

/** the faces the demo draws */
export type Face = 'idle' | 'hello' | 'listening' | 'happy' | 'music';

export interface NomiPose {
  /** degrees; positive turns the face toward the passenger side, negative toward the driver */
  yaw: number;
  /** degrees; positive nods the face down */
  pitch: number;
  face: Face;
}

/** One of the three things the demo plays: when it starts and ends (s), what it is called, what the panel says while it runs. */
export interface Beat {
  id: 'door' | 'voice' | 'music';
  label: string;
  t0: number;
  t1: number;
  line: string;
}

export const BEATS: Beat[] = [
  { id: 'door', label: 'Greets the door', t0: 1.4, t1: 9.0, line: 'The front passenger door opens: NOMI turns its head to the door and greets' },
  { id: 'voice', label: 'Turns to a voice', t0: 9.0, t1: 17.0, line: 'The driver speaks: NOMI turns to face them, listens and nods back' },
  { id: 'music', label: 'Sways to music', t0: 17.0, t1: 27.0, line: 'Music plays: NOMI sways with it' },
];

export const T_END = 27.5;

const clamp = (x: number, a: number, b: number) => Math.min(b, Math.max(a, x));
const smooth = (x: number) => {
  const u = clamp(x, 0, 1);
  return u * u * (3 - 2 * u);
};

/** a pose reached between two times: `to` once t1 is passed, easing in and out between them */
function ramp(t: number, t0: number, t1: number, from: number, to: number): number {
  return from + (to - from) * smooth((t - t0) / (t1 - t0));
}

/** a short nod at t0: down and back up in `dur` seconds, `deg` degrees */
function nod(t: number, t0: number, dur: number, deg: number): number {
  const u = (t - t0) / dur;
  return u > 0 && u < 1 ? deg * Math.sin(Math.PI * u) ** 2 : 0;
}

/** the door's open time: it opens as NOMI turns and shuts when the greeting is over */
export const DOOR = { open: 2.0, shut: 7.2 } as const;
export const doorOpen = (t: number) => t >= DOOR.open && t < DOOR.shut;

/** how far to each side the passenger and the driver are from the head's straight-ahead, degrees (the head's travel is 50 each way) */
const TO_DOOR = 48;
const TO_DRIVER = -42;
const HALF = SWEEP.yaw / 2;

/** NOMI's pose at time t */
export function poseAt(t: number): NomiPose {
  let yaw = 0;
  let pitch = 0;
  let face: Face = 'idle';

  if (t < 9.6) {
    // the door: NOMI senses it a moment after it starts to open, turns, greets with two small nods, and comes back as the door shuts
    yaw = t < 7.9 ? ramp(t, 2.4, 3.7, 0, TO_DOOR) : ramp(t, 7.9, 9.2, TO_DOOR, 0);
    pitch = t > 3.7 && t < 7.9 ? nod(t, 4.2, 0.7, 7) + nod(t, 5.1, 0.7, 7) : 0;
    if (t >= 3.4 && t < 8.6) face = 'hello';
  } else if (t < 17.4) {
    // the driver's voice: the head goes to them, the face listens, then two nods and a smile
    yaw = t < 15.9 ? ramp(t, 9.8, 11.0, 0, TO_DRIVER) : ramp(t, 15.9, 17.2, TO_DRIVER, 0);
    pitch = nod(t, 13.4, 0.8, 9) + nod(t, 14.4, 0.8, 9);
    if (t >= 9.8 && t < 13.0) face = 'listening';
    else if (t >= 13.0 && t < 16.4) face = 'happy';
  } else {
    // the music: a sway that builds over a second and dies away, a small bob on each beat
    const on = smooth((t - 17.6) / 1.0) * (1 - smooth((t - 26.0) / 1.2));
    yaw = 14 * on * Math.sin(Math.PI * 2 * 0.5 * (t - 17.6));
    pitch = 3.5 * on * Math.sin(Math.PI * 2 * 1.0 * (t - 17.6));
    if (t >= 17.6 && t < 26.6) face = 'music';
  }
  return { yaw: clamp(yaw, -HALF, HALF), pitch: clamp(pitch, -SWEEP.pitch / 2, SWEEP.pitch / 2), face };
}

/** the beat the time is in, or null between them */
export function beatAt(t: number): Beat | null {
  return BEATS.find((b) => t >= b.t0 && t < b.t1) ?? null;
}

export interface NomiRun {
  /** the car stands still: a track that never moves, so the rig's wheels stay as they are */
  track: PlannedRun;
  pose: (t: number) => NomiPose;
  /** the front passenger door is open at time t */
  door: (t: number) => boolean;
  beat: (t: number) => Beat | null;
}

export function planNomi(start: { x: number; y: number; yaw: number }): NomiRun {
  const track: PlannedRun = {
    duration: T_END,
    stats: { maxSteer: 0, bounds: { min: { x: start.x, y: start.y }, max: { x: start.x, y: start.y } } },
    sample: (): Sample => ({ ...start, steer: [0, 0, 0, 0], spin: [0, 0, 0, 0], speed: 0, segment: 0, phase: 'dwell' }),
    trace: () => [],
  };
  return { track, pose: poseAt, door: doorOpen, beat: beatAt };
}

// ------------------------------------------------------------------ the run on show

/**
 * The demo that is playing, for the head's driver in the viewer (the director sets it when the demo is built and clears it when the
 * demo goes). A tiny vanilla holder, like the layers' store: the 3D scene reads it every frame.
 */
let active: NomiRun | null = null;
export const setNomiRun = (run: NomiRun | null) => {
  active = run;
};
export const getNomiRun = () => active;
