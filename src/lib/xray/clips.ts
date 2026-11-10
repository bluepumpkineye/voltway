import type { Vehicle, XraySystem } from '@/data/vehicles/schema';
import { xrayOf } from './rig';

/**
 * The short clips of the exploded view: a few seconds of one part working, looped, that the card of a part plays. They are
 * animations of the model, not footage: the rotor spins up while the stator's three phases chase round it, the pack's cells
 * charge in a wave and the current runs down the cables, a wheel rides over a bump on its linkage, the rack turns the wheels.
 * Each clip names the system it works on; while it plays the system is put back together in place (`XrayRig.assemble`), since a
 * linkage can only work as a linkage, and it comes apart again when the clip stops. What each clip moves is
 * viewer/XrayClips.tsx; this is the list, the lengths and the captions.
 */
export interface ClipDef {
  id: string;
  title: string;
  system: XraySystem;
  /** seconds of one loop */
  dur: number;
  /** what the viewer should see happening, at moment `t` of the loop */
  caption: (t: number) => string;
}

export const CLIPS: Record<string, ClipDef> = {
  rotor: {
    id: 'rotor',
    title: 'Torque, from rotor to wheel',
    system: 'drive',
    dur: 6,
    caption: (t) =>
      t < 1.2
        ? 'The inverter feeds the stator three phases of current, one after the other.'
        : t < 3.6
          ? 'The rotating field drags the rotor’s magnets round: it spins up.'
          : 'At full speed the rotor turns thousands of times a minute, and the gears carry its torque to the wheel.',
  },
  battery: {
    id: 'battery',
    title: 'The pack under load',
    system: 'battery',
    dur: 6,
    caption: (t) =>
      t < 2
        ? 'Every cell block gives up its charge in turn.'
        : t < 4
          ? 'The current runs through the busbars to the junction box.'
          : 'From there it goes down the cables to the three inverters.',
  },
  suspension: {
    id: 'suspension',
    title: 'A wheel over a bump',
    system: 'suspension',
    dur: 5,
    caption: (t) =>
      t < 1.7
        ? 'The wheel rises and the arms swing about their mounts, keeping it upright.'
        : t < 3.4
          ? 'The air spring is squeezed; the damper rod slides into its body and soaks up the movement.'
          : 'Then it drops, and the spring and damper push the wheel back to the road.',
  },
  steering: {
    id: 'steering',
    title: 'Turning the wheels',
    system: 'steering',
    dur: 6,
    caption: () => 'The rack slides sideways, and the tie rods turn each front wheel on its knuckle.',
  },
};

/** The clip a part names, or null. */
export function clipOf(id: string | undefined): ClipDef | null {
  return id ? (CLIPS[id] ?? null) : null;
}

/** Start a clip: put its system together in place, then play. */
export function playClip(vehicle: Vehicle, id: string) {
  const def = CLIPS[id];
  if (!def) return;
  const rig = xrayOf(vehicle);
  const now = performance.now();
  if (rig.clip && rig.clip.id !== id) rig.assemble(CLIPS[rig.clip.id]?.system ?? def.system, false, now);
  rig.assemble(def.system, true, now);
  rig.startClip(id, def.dur, now, true);
}

/** Stop the clip, if any, and let the system come apart again. */
export function stopClip(vehicle: Vehicle) {
  const rig = xrayOf(vehicle);
  const c = rig.clip;
  if (!c) return;
  rig.assemble(CLIPS[c.id]?.system ?? 'drive', false, performance.now());
  rig.stopClip();
}
