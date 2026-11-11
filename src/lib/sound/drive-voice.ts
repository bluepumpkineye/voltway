/**
 * What an electric car sounds like at a given speed, and how each car of the line-up differs (ours).
 *
 * The Drive tab's runs last 20 s and more, and every car runs its own: a pull, a long cruise, a brake, a slalom. A recording laid against
 * the clock cannot follow that (it is 9 s long, and a seek at every drift is the click), so the sound is made from what the car is doing,
 * frame by frame: three steady loops cut from the owner's recordings (scripts/tech-tools/cut-drive-loops.mjs) played at a pitch and a
 * level that follow the car's speed, its pull and its braking:
 *
 * - the **whine**, the motor's tone (the SU7 recording): its pitch follows the speed, its level the pull, and it thins out on the lift;
 * - the **bed**, the cabin and road drone (the long electric-car recording): it grows with speed and opens up from dull to bright;
 * - the **hiss**, wind and tyres (the Leaf recording): quiet below 60 km/h, a rush above 150.
 *
 * Nothing here touches the browser, so the mix can be checked in Node against every car's planned run (scripts/tech-tools/drive-sound-test.mjs).
 */

export interface DriveVoice {
  /** pitch of the motor tone against the recording's (1 = as recorded): a big, heavy car sings lower */
  pitch: number;
  /** level of the motor tone, the road drone and the wind and tyre hiss */
  whine: number;
  bed: number;
  hiss: number;
  /** how open the motor tone is under load, 1 = as recorded: a refined car is duller */
  open: number;
  /** a second motor tone at this ratio of the first and this share of its level: a car with more motors sings in more parts */
  parts?: { ratio: number; level: number };
}

const VOICES: Record<string, DriveVoice> = {
  // the SU7 Ultra: three motors, the line-up's fastest, and the recording is its own
  'xiaomi-su7-ultra': { pitch: 1.0, whine: 1.0, bed: 0.75, hiss: 1.0, open: 1.15, parts: { ratio: 2, level: 0.3 } },
  'zeekr-7x': { pitch: 0.94, whine: 0.9, bed: 0.85, hiss: 0.95, open: 1.0, parts: { ratio: 1.5, level: 0.22 } },
  'byd-seal': { pitch: 0.9, whine: 0.85, bed: 0.9, hiss: 1.0, open: 0.95 },
  // the Magic Carpet sedan, the refined ES8 and the big G9L: low, soft and a lot of road
  'voyah-passion-s': { pitch: 0.82, whine: 0.7, bed: 1.0, hiss: 0.8, open: 0.8 },
  'luxeed-rx': { pitch: 0.88, whine: 0.8, bed: 0.9, hiss: 0.9, open: 0.95, parts: { ratio: 1.5, level: 0.15 } },
  'nio-es8': { pitch: 0.74, whine: 0.65, bed: 1.1, hiss: 0.85, open: 0.75 },
  'avatr-06t': { pitch: 0.96, whine: 0.9, bed: 0.85, hiss: 1.0, open: 1.05, parts: { ratio: 1.5, level: 0.2 } },
  'xpeng-g9l': { pitch: 0.78, whine: 0.7, bed: 1.05, hiss: 0.9, open: 0.8 },
  // the Z9 GT: three motors like the SU7, but a grand tourer
  'denza-z9': { pitch: 0.86, whine: 0.8, bed: 1.0, hiss: 0.95, open: 0.9, parts: { ratio: 2, level: 0.25 } },
};

const GENERIC: DriveVoice = { pitch: 0.9, whine: 0.8, bed: 0.95, hiss: 0.9, open: 0.95 };

export function voiceOf(slug: string | null | undefined): DriveVoice {
  return (slug && VOICES[slug]) || GENERIC;
}

/** The loops' settings for one moment: what each layer should be doing now (the engine eases toward them). */
export interface DriveMix {
  /** playback rates: the motor tone, the road drone, the hiss */
  whineRate: number;
  bedRate: number;
  hissRate: number;
  /** levels, 0 and up (the loops are cut to a common level) */
  whine: number;
  parts: number;
  bed: number;
  hiss: number;
  /** low-pass cut-offs, Hz */
  whineCut: number;
  bedCut: number;
}

const clamp = (x: number, a: number, b: number) => Math.min(b, Math.max(a, x));

/**
 * The mix for a car at `speed` km/h pulling or braking at `g` (the run's longitudinal acceleration), in a run phase.
 *
 * An electric car is silent at a standstill and its tone rises with its speed; it sings loudest under power, thins when the
 * driver lifts, and sings again a little on regeneration. Wind and tyre noise grow with the square of the speed or more.
 */
export function driveMix(voice: DriveVoice, speed: number, g: number, phase?: string): DriveMix {
  const v = Math.max(0, Number.isFinite(speed) ? speed : 0);
  const a = Number.isFinite(g) ? g : 0;
  // the motor comes up out of silence over the first 40 km/h
  const rise = 1 - Math.exp(-v / 18);
  const power = clamp((a + 0.05) / 0.45, 0, 1);
  const regen = clamp(-a / 0.9, 0, 1);
  // a car that is turning at a walk (slalom, crab walk) still hums, and a stopped one is silent
  const load = 0.55 + 0.45 * power + 0.2 * regen;
  const whine = voice.whine * rise * load * (phase === 'stop' || phase === 'hold' ? 0 : 1);
  return {
    whineRate: voice.pitch * (0.55 + v / 180),
    bedRate: 0.9 + 0.25 * Math.min(1, v / 220),
    hissRate: 0.95 + 0.15 * Math.min(1, v / 250),
    whine,
    parts: voice.parts ? whine * voice.parts.level : 0,
    bed: voice.bed * Math.min(1.3, Math.pow(v / 110, 1.25)),
    hiss: voice.hiss * Math.min(1.5, 1.4 * Math.pow(v / 200, 2.2)),
    whineCut: clamp(1400 + 5200 * power * voice.open + 12 * v, 900, 9000),
    bedCut: clamp(350 + 40 * v, 500, 9000),
  };
}
