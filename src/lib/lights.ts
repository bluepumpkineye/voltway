import type { LampSpec, LightsSpec } from '@/data/vehicles/schema';

/**
 * The car's lamps, as the showroom shows them (docs/lights.md).
 *
 * What a visitor sets is a few flags in the store: the headlamp switch of the car's screen, the high
 * beam, the brake. What the lamps DO is a set of levels that ramp toward those flags: how bright the
 * LED lines are, how far the beam reaches over the floor, how far the room has dimmed to dusk. This
 * file holds the flags' meaning (`lampTargets`) and the ramp (`LightsRig`), with no three.js in it, so
 * the numbers can be checked on their own; the viewer (components/viewer/Lights.tsx) only reads them.
 */

/**
 * The headlamp switch. 'auto' is the car deciding for itself: in a showroom that is dim by design, so
 * it lights the low beam. The visitor's high beam is a separate flag, on top of the low beam.
 */
export type LightMode = 'off' | 'position' | 'low' | 'auto';
export const LIGHT_MODES: LightMode[] = ['off', 'position', 'low', 'auto'];

/** What the lamps are doing, every level 0..1 unless it says otherwise. */
export interface LampLevels {
  /** the front LED line: 0 off, 0.45 the position (daytime-running) light, 0.8 low beam, 1 high beam */
  front: number;
  /** the projector lenses, which join in with the low beam */
  projector: number;
  /** the beam over the floor */
  beam: number;
  /** how far ahead of the lamps the beam reaches, m */
  reach: number;
  /** the tail lamps: 0 as the build is, 0.5 lit, 1 braking */
  rear: number;
  /** how far the room has dimmed to dusk, so the lamps have something to shine against */
  night: number;
}

export const NO_LIGHT: LampLevels = { front: 0, projector: 0, beam: 0, reach: 0, rear: 0, night: 0 };

export const isLowBeam = (mode: LightMode) => mode === 'low' || mode === 'auto';

/** What the lamps are heading for, given the switch, the high beam and the brake pedal. */
export function lampTargets(mode: LightMode, highBeam: boolean, braking: boolean): LampLevels {
  const low = isLowBeam(mode);
  const high = low && highBeam;
  return {
    front: mode === 'off' ? 0 : mode === 'position' ? 0.45 : high ? 1 : 0.8,
    projector: low ? (high ? 1 : 0.8) : 0,
    beam: high ? 1 : low ? 0.7 : 0,
    reach: high ? 12 : low ? 7 : 0,
    // the brake lights come on with the pedal, lamps or no lamps
    rear: braking ? 1 : mode === 'off' ? 0 : 0.5,
    night: mode === 'off' ? 0 : mode === 'position' ? 0.3 : high ? 1 : 0.85,
  };
}

// ------------------------------------------------------------------------ the ramp

/** An LED coming on is not a bulb warming up: it stutters up in a few tens of milliseconds. */
const WAKE: [number, number][] = [
  [0, 0],
  [0.05, 0.9],
  [0.11, 0.15],
  [0.18, 1],
  [0.26, 0.5],
  [0.38, 1],
];
const WAKE_END = WAKE[WAKE.length - 1][0];

/** The tail lamps wake up a beat after the front ones, as a car's do. */
const REAR_DELAY = 0.15;
/** The projectors a beat after the line. */
const PROJECTOR_DELAY = 0.1;

export function wake(t: number): number {
  if (t <= 0) return 0;
  if (t >= WAKE_END) return 1;
  for (let i = 1; i < WAKE.length; i++) {
    const [t1, v1] = WAKE[i];
    if (t <= t1) {
      const [t0, v0] = WAKE[i - 1];
      return v0 + ((v1 - v0) * (t - t0)) / (t1 - t0);
    }
  }
  return 1;
}

/** A level easing toward its goal with a time constant, `tau` seconds. */
const ease = (cur: number, goal: number, tau: number, dt: number) => {
  const next = cur + (goal - cur) * (1 - Math.exp(-dt / tau));
  return Math.abs(goal - next) < 0.002 ? goal : next;
};

/**
 * The lamps' levels as they are drawn, moving toward their goal a frame at a time. One instance serves
 * the page: there is one car on show, and the lamp materials, the glow, the floor and the stage all read
 * the same numbers. `step` says whether anything is still moving, so a demand canvas asks for frames
 * only while it is.
 */
export class LightsRig {
  readonly now: LampLevels = { ...NO_LIGHT };
  goal: LampLevels = { ...NO_LIGHT };
  /** seconds into a wake-up (negative: waiting for its turn), or null when the lamp is not waking up */
  private wakeFront: number | null = null;
  private wakeRear: number | null = null;
  /** counts every change, so a reader can tell whether it has to redraw */
  version = 0;

  /** Head for new levels; `snap` lands on them at once (reduced motion, a first mount). */
  aim(goal: LampLevels, snap = false) {
    this.goal = goal;
    if (snap) {
      Object.assign(this.now, goal);
      this.wakeFront = this.wakeRear = null;
      this.version++;
    }
  }

  /** Move `dt` seconds on; true while anything is still moving. */
  step(dt: number): boolean {
    dt = Math.min(Math.max(dt, 0), 0.1);
    const n = this.now;
    const g = this.goal;
    const before = `${n.front}|${n.projector}|${n.beam}|${n.reach}|${n.rear}|${n.night}`;

    // a wake-up starts from its first moment: the frame that finds the switch (after a long idle, a long
    // one) does not eat the first of the stutter
    let startedFront = false;
    let startedRear = false;
    if (this.wakeFront === null && g.front > 0.3 && n.front < 0.05) {
      this.wakeFront = 0;
      startedFront = true;
    }
    if (this.wakeRear === null && g.rear > 0.3 && n.rear < 0.05) {
      this.wakeRear = -REAR_DELAY;
      startedRear = true;
    }
    if (g.front < 0.05) this.wakeFront = null;
    if (g.rear < 0.05) this.wakeRear = null;

    if (this.wakeFront !== null) {
      if (!startedFront) this.wakeFront += dt;
      n.front = g.front * wake(this.wakeFront);
      n.projector = g.projector * wake(this.wakeFront - PROJECTOR_DELAY);
      if (this.wakeFront >= WAKE_END + PROJECTOR_DELAY) this.wakeFront = null;
    } else {
      n.front = ease(n.front, g.front, 0.1, dt);
      n.projector = ease(n.projector, g.projector, 0.1, dt);
    }
    if (this.wakeRear !== null) {
      if (!startedRear) this.wakeRear += dt;
      n.rear = g.rear * wake(this.wakeRear);
      if (this.wakeRear >= WAKE_END) this.wakeRear = null;
    } else {
      // brake lights jump on and fade off a little slower
      n.rear = ease(n.rear, g.rear, g.rear > n.rear ? 0.05 : 0.16, dt);
    }
    n.beam = ease(n.beam, g.beam, 0.22, dt);
    n.reach = ease(n.reach, g.reach, 0.35, dt);
    n.night = ease(n.night, g.night, 0.45, dt);

    const after = `${n.front}|${n.projector}|${n.beam}|${n.reach}|${n.rear}|${n.night}`;
    if (after !== before) this.version++;
    return (
      this.wakeFront !== null ||
      this.wakeRear !== null ||
      n.front !== g.front ||
      n.projector !== g.projector ||
      n.beam !== g.beam ||
      n.reach !== g.reach ||
      n.rear !== g.rear ||
      n.night !== g.night
    );
  }
}

/** The page's lamps: one car is on show at a time. */
export const lightsRig = new LightsRig();

// -------------------------------------------------------------- what a car's lamps are

/** The lamps' defaults: the exports name their lit parts alike (docs/3d-pipeline.md, materials). */
export interface LampLook {
  material: string;
  /** the lamp's own light, sRGB */
  color: string;
  /** the colour of the glow round it, sRGB */
  halo: string;
  /** the material's emissive strength with the lamp off, when it is not the build's own; and fully lit */
  off?: number;
  on: number;
}

export const DEFAULT_LIGHTS: { front: LampLook; rear: LampLook; projector?: LampLook } = {
  // cool white, as photographed: a pure white core, a blue-white halo
  front: { material: 'M_LED_White', color: '#eaf2ff', halo: '#8fb6ff', off: 0.15, on: 1.7 },
  // a deep red: the more it is driven, the more a saturated red rolls toward pink, so the core stays red
  // and the halo carries the light
  rear: { material: 'M_LED_Red_Tail', color: '#ff1a0f', halo: '#ff1608', on: 2.4 },
};

export interface ResolvedLights {
  front: LampLook;
  rear: LampLook;
  projector?: LampLook;
}

const merge = (base: LampLook, over?: LampSpec): LampLook => ({ ...base, ...(over ?? {}) } as LampLook);

/** A car's lamps: the defaults, with whatever its data says differently. */
export function lightsOf(spec: LightsSpec | undefined): ResolvedLights {
  return {
    front: merge(DEFAULT_LIGHTS.front, spec?.front),
    rear: merge(DEFAULT_LIGHTS.rear, spec?.rear),
    projector: spec?.projector
      ? merge({ material: 'M_Lamp_Reflector', color: '#eaf2ff', halo: '#8fb6ff', on: 2.6 }, spec.projector)
      : undefined,
  };
}

/** The emissive strength a front lamp shows at a level (0 as the build is, 1 lit as far as it goes). */
export function frontEmissive(look: LampLook, level: number): number {
  const off = look.off ?? 0;
  return off + (look.on - off) * level;
}

/**
 * The emissive strength of a tail lamp: `built` is what the export gave the material (the tail lamps are
 * lit a little in the build, as in most photographs), `level` runs 0 as built, 0.5 lit, 1 braking.
 */
export function rearEmissive(look: LampLook, built: number, level: number): number {
  const off = look.off ?? built;
  const brake = look.on * 1.45;
  return level < 0.5 ? off + (look.on - off) * (level / 0.5) : look.on + (brake - look.on) * ((level - 0.5) / 0.5);
}
