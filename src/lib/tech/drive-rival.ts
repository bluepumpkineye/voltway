import type { DriveSpec, Variant, Vehicle } from '../../data/vehicles/schema';
import { flagshipVariant } from '../../data/vehicles/schema';
import { pullTrack, roadEnv } from './drive-run';
import { timesOf } from './drive-setup';

/**
 * The car the Drive tab sets against the one on show (the chart's dashed curve, the stand-in drawn beside it): the scenario's
 * choice, the visitor's, or none. Its trim is the scenario's if the scenario names one for that car; the car's own base trim when
 * the rival is the car itself; else the rival's flagship. Its times are its published ones (and our estimate of its 0-200
 * where it has none, said so on the chart).
 */
export interface Rival {
  car: Vehicle;
  variant: Variant;
  t100: number;
  t200: number | undefined;
  published200: boolean;
  /** drives all four wheels: it holds the road better when it is wet */
  awd: boolean;
}

export function rivalOf(all: Vehicle[], self: Vehicle, spec: DriveSpec | undefined, slug: string | null | undefined): Rival | null {
  const car = slug ? all.find((v) => v.slug === slug) : undefined;
  if (!car) return null;
  const timed = car.variants.filter((v) => v.performance.zeroTo100S !== undefined);
  if (!timed.length) return null;
  const named = spec?.ghost?.slug === car.slug ? timed.find((v) => v.id === spec.ghost?.variantId) : undefined;
  const variant =
    named ?? (car.slug === self.slug ? timed.reduce((a, v) => (v.performance.powerKw < a.performance.powerKw ? v : a), timed[0]) : flagshipVariant(car));
  const { t100, t200, published200 } = timesOf(variant);
  return { car, variant, t100, t200, published200, awd: variant.drive === 'AWD' };
}

/** The road as the rival meets it: the same wet and the same hill as the car's, its own grip. */
export function rivalEnv(r: Rival, env: { wet: boolean; gradePct: number } | undefined) {
  return roadEnv(Boolean(env?.wet), r.awd, env?.gradePct ?? 0);
}

/** How far the rival has got along the road at time t, m, for a run from one speed to another. */
export function rivalTrack(r: Rival, from: number, to: number, env?: { wet: boolean; gradePct: number }): (t: number) => number {
  return pullTrack(r.t100, r.t200, from, to, rivalEnv(r, env));
}
