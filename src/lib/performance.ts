import type { Variant, RangeCycle } from '@/data/vehicles/schema';

export type DriveMode = 'eco' | 'comfort' | 'sport' | 'track';

export const DRIVE_MODES: { id: DriveMode; label: string; blurb: string }[] = [
  { id: 'eco', label: 'Eco', blurb: 'Power capped, regen raised' },
  { id: 'comfort', label: 'Comfort', blurb: 'Balanced daily setup' },
  { id: 'sport', label: 'Sport', blurb: 'Full power, firmer damping' },
  { id: 'track', label: 'Track', blurb: 'Everything off the leash' },
];

/**
 * How each mode trades power against range.
 *
 * `power` caps deliverable output; `range` scales consumption. These are
 * modelled, not manufacturer-published - a car maker quotes one range figure
 * per variant on one test cycle, so the per-mode spread here is an
 * illustration of the trade-off rather than a specification. The UI says so.
 */
const MODE_FACTORS: Record<DriveMode, { power: number; range: number }> = {
  eco: { power: 0.6, range: 1.08 },
  comfort: { power: 0.85, range: 1.0 },
  sport: { power: 1.0, range: 0.88 },
  track: { power: 1.0, range: 0.78 },
};

export interface ClimateLoad {
  acOn: boolean;
  fanSpeed: number; // 0-5
}

/** Climate draw, as a multiplier on range. HVAC is the biggest cabin load. */
export function climateRangeFactor({ acOn, fanSpeed }: ClimateLoad): number {
  if (!acOn) return 1.0;
  return 1 - (0.035 + fanSpeed * 0.006);
}

/**
 * Peak power in a mode. `publishedKw` is the maker's figure for one of the
 * car's own modes (Vehicle.cockpit.driveModes) and wins over the model.
 */
export function effectivePowerKw(variant: Variant, mode: DriveMode, publishedKw?: number): number {
  if (publishedKw) return Math.min(publishedKw, variant.performance.powerKw);
  return Math.round(variant.performance.powerKw * MODE_FACTORS[mode].power);
}

/** 0-100 scales roughly with the inverse cube root of the power ratio. */
export function effectiveZeroTo100(
  variant: Variant,
  mode: DriveMode,
  publishedKw?: number,
): number | undefined {
  const base = variant.performance.zeroTo100S;
  if (base === undefined) return undefined;
  const ratio = publishedKw
    ? Math.min(1, publishedKw / variant.performance.powerKw)
    : MODE_FACTORS[mode].power;
  return Math.round((base / Math.cbrt(ratio)) * 100) / 100;
}

export interface RangeEstimate {
  km: number;
  cycle: RangeCycle;
  /** True when the figure has been modelled away from the published number. */
  modelled: boolean;
}

export function effectiveRange(
  variant: Variant,
  mode: DriveMode,
  soc: number,
  climate: ClimateLoad,
): RangeEstimate | undefined {
  const published = variant.range[0];
  if (!published) return undefined;
  const factor = MODE_FACTORS[mode].range * climateRangeFactor(climate);
  return {
    km: Math.round(published.km * factor * soc),
    cycle: published.cycle,
    modelled: factor !== 1 || soc !== 1,
  };
}

/** Consumption implied by the pack size and the range on offer. */
export function efficiencyKwhPer100km(
  variant: Variant,
  mode: DriveMode,
  climate: ClimateLoad,
): number | undefined {
  const published = variant.range[0];
  if (!published) return undefined;
  const factor = MODE_FACTORS[mode].range * climateRangeFactor(climate);
  const km = published.km * factor;
  if (km <= 0) return undefined;
  return Math.round((variant.battery.capacityKwh / km) * 100 * 10) / 10;
}

/**
 * Minutes for a 10-80% DC charge.
 *
 * Uses the manufacturer figure when there is one. Otherwise it falls back to
 * the C-rate, and failing that to the peak charging power with a 0.72 factor
 * to account for the taper - real packs do not hold peak power across the
 * whole window.
 */
export function chargeMinutes10to80(variant: Variant): number | undefined {
  const b = variant.battery;
  if (b.chargeMinutes10to80 !== undefined) return b.chargeMinutes10to80;
  if (b.cRate) return Math.round((0.7 / b.cRate) * 60 * 10) / 10;
  if (b.peakChargeKw) {
    const avgKw = b.peakChargeKw * 0.72;
    return Math.round(((b.capacityKwh * 0.7) / avgKw) * 60 * 10) / 10;
  }
  return undefined;
}

/** Power delivered over the launch, for the acceleration chart. */
export function accelerationCurve(
  variant: Variant,
  mode: DriveMode,
  points = 40,
): { t: number; kmh: number }[] {
  const zero100 = effectiveZeroTo100(variant, mode);
  if (zero100 === undefined) return [];
  const out: { t: number; kmh: number }[] = [];
  const tMax = zero100 * 2.4;
  for (let i = 0; i <= points; i++) {
    const t = (i / points) * tMax;
    // traction-limited off the line, then power-limited: v ~ t^0.62
    const kmh = 100 * Math.pow(t / zero100, 0.62);
    out.push({ t: Math.round(t * 100) / 100, kmh: Math.round(Math.min(kmh, 350)) });
  }
  return out;
}

export function formatRange(est: RangeEstimate | undefined): string {
  if (!est) return '--';
  return `${est.km} km`;
}
