import * as THREE from 'three';
import type { Vehicle } from '@/data/vehicles/schema';

/**
 * How the car's own parts come apart in the exploded view: the shell (paint, lamps, glass roof), the doors, the bonnet and the
 * tail, the wheels and the cabin. The anatomy GLB carries its own plan in each node (`xr` extra, written by
 * blender/scripts/carkit/anatomy/build.py); this is the rest, derived from the car's size by the node names every car's export
 * shares (`<Car>_Body`, `_Details`, `_Greenhouse`, `_Door_FL`..., `_Bonnet`, `_Trunk` or `_Tailgate`, the wheels' `steer` groups), so
 * a new car needs no list. All offsets are in the viewer's axes (x forward, y up, z toward the passenger's side), metres, relative
 * to where the part stands.
 */

export interface PlanMove {
  /** the node's name matches */
  name: RegExp;
  ex: [number, number, number];
  t0: number;
  t1: number;
  sys: string;
  /** which of the exterior's nodes it follows (a door card its door): the move is that node's less the cabin's own */
  follow?: boolean;
}

export interface Dims {
  /** the car's wheelbase, length and height, m */
  wheelbase: number;
  height: number;
}

export function dimsOf(vehicle: Vehicle): Dims {
  return { wheelbase: (vehicle.dimensions.wheelbaseMm ?? 2900) / 1000, height: vehicle.dimensions.heightMm / 1000 };
}

/** How far the whole assembly stands off the floor: the pack drops this far inside it, so the parts never go under the studio. */
export function assemblyLift(d: Dims, vehicle: Vehicle): number {
  return vehicle.xray?.anatomy?.lift?.assembly ?? 0.3;
}

/** The cabin's lift (the whole interior, as one piece). */
export function cabinLift(d: Dims, vehicle: Vehicle): number {
  return vehicle.xray?.anatomy?.lift?.cabin ?? 0.8 * (d.height / 1.465);
}

/** The shell's lift (paint, lamps, bumpers); the greenhouse goes higher. */
export function shellLift(d: Dims, vehicle: Vehicle): number {
  return vehicle.xray?.anatomy?.lift?.shell ?? 1.2 * (d.height / 1.465);
}

const v3 = (a: [number, number, number]) => new THREE.Vector3(a[0], a[1], a[2]);

/**
 * The exterior's nodes and where each goes. The paint shell lifts, the greenhouse (roof and glass) lifts further, each door goes out
 * to its own side and up, the bonnet goes forward and up, the tail back and up. Windows: the roof and the doors go first, the body
 * follows, the cabin and the hardware after.
 */
export function exteriorPlan(d: Dims, vehicle: Vehicle): PlanMove[] {
  const k = d.wheelbase / 3;
  const lift = shellLift(d, vehicle);
  const up = lift * 1.46;
  const doorUp = lift * 1.12;
  return [
    { name: /_Greenhouse$/i, ex: [0, up, 0], t0: 0.0, t1: 0.5, sys: 'shell' },
    { name: /_Door_FL$/i, ex: [0.18 * k, doorUp, -0.95], t0: 0.02, t1: 0.5, sys: 'shell' },
    { name: /_Door_FR$/i, ex: [0.18 * k, doorUp, 0.95], t0: 0.02, t1: 0.5, sys: 'shell' },
    { name: /_Door_RL$/i, ex: [-0.2 * k, doorUp, -0.95], t0: 0.02, t1: 0.5, sys: 'shell' },
    { name: /_Door_RR$/i, ex: [-0.2 * k, doorUp, 0.95], t0: 0.02, t1: 0.5, sys: 'shell' },
    { name: /_DoorFrame_FL$/i, ex: [0.18 * k, doorUp, -0.95], t0: 0.02, t1: 0.5, sys: 'shell' },
    { name: /_DoorFrame_FR$/i, ex: [0.18 * k, doorUp, 0.95], t0: 0.02, t1: 0.5, sys: 'shell' },
    { name: /_DoorFrame_RL$/i, ex: [-0.2 * k, doorUp, -0.95], t0: 0.02, t1: 0.5, sys: 'shell' },
    { name: /_DoorFrame_RR$/i, ex: [-0.2 * k, doorUp, 0.95], t0: 0.02, t1: 0.5, sys: 'shell' },
    { name: /_Bonnet$/i, ex: [0.95 * k, lift * 1.2, 0], t0: 0.05, t1: 0.55, sys: 'shell' },
    { name: /_(Trunk|Tailgate)$/i, ex: [-0.95 * k, lift * 1.2, 0], t0: 0.05, t1: 0.55, sys: 'shell' },
    { name: /_(TrunkArms|TailgateArms)$/i, ex: [-0.95 * k, lift * 1.2, 0], t0: 0.05, t1: 0.55, sys: 'shell' },
    { name: /_(Body|Details)$/i, ex: [0, lift, 0], t0: 0.1, t1: 0.6, sys: 'shell' },
  ];
}

/** Where a wheel's steer group goes: out to its side, along with its corner, up with the assembly. */
export function wheelMove(corner: 'FL' | 'FR' | 'RL' | 'RR', d: Dims): { ex: THREE.Vector3; t0: number; t1: number } {
  const k = d.wheelbase / 3;
  const front = corner[0] === 'F';
  const side = corner[1] === 'L' ? -1 : 1;
  return { ex: v3([(front ? 0.14 : -0.14) * k, 0, side * 1.0]), t0: 0.35, t1: 0.85 };
}

/** The whole cabin goes up as one piece; its door cards (and the tail's liner) follow their doors. */
export function cabinMove(d: Dims, vehicle: Vehicle): THREE.Vector3 {
  return v3([0, cabinLift(d, vehicle), 0]);
}

export const CABIN_WINDOW = { t0: 0.2, t1: 0.7 };
