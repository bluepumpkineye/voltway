import type { ChargingSpec, TechDemoSpec, Vehicle } from '@/data/vehicles/schema';
import { flagshipVariant } from '@/data/vehicles/schema';
import { derivedPeakKw, type ChargePort, type ChargeProfile } from './charge';

/**
 * A car's charging as the Charging tab shows it: the maker's window and peak where it publishes them, the peak the
 * curve is drawn to otherwise, and the profile the run is planned from (src/lib/tech/charge.ts).
 */
export interface ChargeFacts {
  spec: ChargingSpec;
  profile: ChargeProfile;
  /** the peak the curve reaches, kW, and where it comes from: the maker, its C-rate times the pack, or our derivation */
  peak: { kw: number; source: 'published' | 'c-rate' | 'derived' };
  /** the window's average power, kW */
  averageKw: number;
  /** whether the car's model has a flap of its own that opens (the 7X's); the others get a socket drawn at the port */
  modelledFlap: boolean;
}

/** how long the whole run takes to play the charge, s: the charge itself is played in this time */
export const PLAY_SECONDS = 14;

const DEFAULT_PORT: ChargePort = { mouth: [-1.4, 1, -0.85], axis: [0, 0, -1], depth: 0.02 };

/** The charge port to draw the gun at: the car's own, or a stand-in on the driver's side. */
export function portOf(vehicle: Vehicle): ChargePort {
  return vehicle.chargePort ?? DEFAULT_PORT;
}

export function chargeFacts(vehicle: Vehicle): ChargeFacts | null {
  const spec = vehicle.charging;
  if (!spec) return null;
  const { from, to, minutes } = spec.window;
  const seconds = minutes * 60;
  const averageKw = (spec.packKwh * ((to - from) / 100) * 60) / minutes;
  const peak = spec.peakKw
    ? { kw: spec.peakKw, source: 'published' as const }
    : spec.cRate
      ? { kw: Math.round(spec.cRate * spec.packKwh), source: 'c-rate' as const }
      : { kw: derivedPeakKw(spec.packKwh, from / 100, to / 100, seconds), source: 'derived' as const };
  return {
    spec,
    profile: { kwh: spec.packKwh, from: from / 100, to: to / 100, seconds, peakKw: peak.kw },
    peak,
    averageKw,
    modelledFlap: Boolean(vehicle.openings?.some((o) => o.id === 'charge')),
  };
}

/**
 * The Charging tab's demonstration, as the same kind of object a Tech tab demo is, so the director, the clock and the
 * playback bar run it unchanged. The tab is the car's, not a feature the maker names, so it is built from the car's
 * charging figures and not listed in `Vehicle.tech`.
 */
export function chargeDemo(vehicle: Vehicle): TechDemoSpec | null {
  const f = chargeFacts(vehicle);
  if (!f) return null;
  const { from, to, minutes } = f.spec.window;
  return {
    id: 'charge',
    title: 'Fast charging',
    blurb: `The flap opens, a gun goes into the DC socket and the pack charges from ${from} to ${to} % in ${minutes} minutes at best. ${minutes} minutes play in ${PLAY_SECONDS} seconds.`,
    driver: 'charge',
    claims: f.spec.claims,
    simulated: f.spec.simulated,
  };
}

/** A car's published figures for the specification sheet: the window's time, and whether it is a window of 10 to 80. */
export function chargeSummary(vehicle: Vehicle): { window: string; minutes: number; peak: string } | null {
  const f = chargeFacts(vehicle);
  if (!f) return null;
  const { from, to, minutes } = f.spec.window;
  return {
    window: `${from}–${to} %`,
    minutes,
    peak: `${f.peak.kw} kW${f.peak.source === 'published' ? '' : ' (derived)'}`,
  };
}

/** The variant the charging figures are for: the flagship, as the rest of the showroom opens on. */
export function chargeVariant(vehicle: Vehicle) {
  return flagshipVariant(vehicle);
}
