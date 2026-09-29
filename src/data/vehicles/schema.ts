/**
 * The single source of truth for vehicle data.
 *
 * Range cycles are never blended. CLTC (China) is materially more optimistic
 * than WLTP (Europe) or EPA (US) — typically 25-35% higher for the same car —
 * so every range figure carries its cycle and the UI always renders the label.
 */

import type { DriveMode } from '@/lib/performance';

export type RangeCycle = 'CLTC' | 'WLTP' | 'EPA';

export type BatteryChemistry = 'LFP' | 'NMC' | 'NCM' | 'Semi-solid';

export type DriveLayout = 'RWD' | 'AWD' | 'FWD';

export interface RangeFigure {
  cycle: RangeCycle;
  km: number;
}

export interface BatterySpec {
  /** Usable capacity in kWh. */
  capacityKwh: number;
  chemistry: BatteryChemistry;
  /** Nominal pack voltage architecture, e.g. 800 or 900. */
  architectureV?: number;
  /** Peak DC charge rate as a C-rate multiple, e.g. 5.5 for "5.5C". */
  cRate?: number;
  /** Peak DC charging power in kW. */
  peakChargeKw?: number;
  /** Minutes for a 10-80% DC charge. */
  chargeMinutes10to80?: number;
  /** Battery swap support — currently Nio only. */
  swappable?: boolean;
}

export interface Performance {
  /** Combined peak system power in kW. */
  powerKw: number;
  /** Combined peak torque in Nm. */
  torqueNm?: number;
  /** 0-100 km/h in seconds. */
  zeroTo100S?: number;
  topSpeedKmh?: number;
  motorCount: 1 | 2 | 3;
}

export interface Variant {
  id: string;
  name: string;
  drive: DriveLayout;
  battery: BatterySpec;
  performance: Performance;
  /** One entry per published cycle. Never merge cycles into a single number. */
  range: RangeFigure[];
  /** Consumption in kWh/100km, on the cycle given. */
  efficiencyKwhPer100km?: number;
  priceCny?: number;
}

export interface Dimensions {
  lengthMm: number;
  widthMm: number;
  heightMm: number;
  wheelbaseMm: number;
  kerbWeightKg?: number;
}

/** A physical display in the cabin. Drives the cockpit build and the spec sheet. */
export interface ScreenSpec {
  id: string;
  label: string;
  /** Diagonal in inches. HUDs are quoted as projected size. */
  diagonalIn: number;
  role: 'center' | 'cluster' | 'hud' | 'passenger' | 'mirror' | 'rear';
  /** True for the one screen the HMI mounts to in 3D. Exactly one per vehicle. */
  interactive?: boolean;
}

export type HmiSkin = 'hyperos' | 'harmonyos' | 'banyan' | 'zeekros' | 'xos' | 'dilink' | 'avatr';

/** One of the car's own drive modes, named as its HMI names it. */
export interface CarDriveMode {
  id: string;
  label: string;
  /** The HMI's own label, e.g. 经济. */
  native?: string;
  /** A custom slot the mode sits in on the selector, e.g. M1. */
  slot?: string;
  group: 'street' | 'track' | 'special';
  /** The modelled mode behind it, for the power and range figures. */
  model: DriveMode;
  /** Peak output in this mode where the maker publishes one, kW. */
  powerKw?: number;
  /** The same figure as the maker quotes it, when in metric hp (PS). */
  powerPs?: number;
}

export interface Cockpit {
  os: string;
  skin: HmiSkin;
  screens: ScreenSpec[];
  /** Named accent used by the in-car UI and the ambient lighting in 3D. */
  accentColor: string;
  ambientLighting?: boolean;
  /** The car's drive modes as its HMI lists them; the generic four otherwise. */
  driveModes?: CarDriveMode[];
}

/**
 * An HDRI world around the car. Both files are equirectangular and carry the
 * cabin's orientation (the one the cabin bake was lit in):
 *   view   an sRGB JPEG tone mapped at build time (carkit.bake.backdrop): the
 *          view through the glass, and the backdrop outside
 *   light  a linear HDR of the same world with the sun clamped out
 *          (carkit.bake.backdrop_light): image-based light for the bodywork
 * Each view is composed on its own, as a photographer would: outside, the
 * world is turned by `exteriorTurnDeg` so the default camera has the sun at
 * its back and the skyline behind the car.
 */
export interface OutsideWorld {
  view: string;
  light: string;
  exteriorTurnDeg: number;
  /**
   * The sun clamped out of `light`, as the exterior's directional light:
   * direction toward the sun in the viewer's axes (exterior orientation),
   * and its irradiance, both measured off the HDRI.
   */
  sun: { direction: [number, number, number]; color: string; intensity: number };
  /** Where the HDRI was shot from, and the dome its ground is projected on, m. */
  ground: { height: number; radius: number };
  /**
   * false: the world is only the view out of the cabin (and the light the
   * cabin was baked under); outside, the car stays in the studio. Default true.
   */
  exterior?: boolean;
}

export interface VehicleAssets {
  /** Path under /public/models, omitted until the model is built. */
  modelUrl?: string;
  /**
   * The cabin as its own GLB, streamed in behind the exterior. Its lighting is
   * baked in Blender (Cycles) into COLOR_0, see blender/scripts/carkit/bake.py.
   */
  interiorModelUrl?: string;
  /** Equirectangular HDR shot from inside the cabin: what the trim reflects. */
  interiorProbeUrl?: string;
  /** The world the car stands in, in both views (export_gltf.OUTSIDE), or
   * only through the cabin's glass (`exterior: false`). */
  outside?: OutsideWorld;
  /**
   * Seated eye position in metres, in the build's axes [x forward, y left, z up]
   * (Blender); the viewer maps it to glTF's [x, z, -y].
   */
  driverEye?: [number, number, number];
  heroColor: string;
}

export interface Source {
  label: string;
  url: string;
}

export interface Vehicle {
  slug: string;
  brand: string;
  model: string;
  /** Parent group or alliance, e.g. "Chery x Huawei (HIMA)". */
  group: string;
  bodyStyle: 'Sedan' | 'SUV' | 'Coupe SUV' | 'Shooting Brake';
  /** Model year or launch year. */
  year: number;
  tagline: string;
  summary: string;
  dimensions: Dimensions;
  variants: Variant[];
  cockpit: Cockpit;
  assets: VehicleAssets;
  sources: Source[];
  /** Set when a car is too new for reliable data on some fields. */
  dataCaveat?: string;
}

/**
 * The variant a vehicle page opens on: the halo trim.
 *
 * Highest power wins, then the bigger pack. Without the tie-break a car whose
 * trims share an output (the Nio ES7 is 480 kW on every pack) would show its
 * smallest battery and shortest range, which reads as a worse car than it is.
 */
export function flagshipVariant(vehicle: Vehicle): Variant {
  return vehicle.variants.reduce((best, v) => {
    if (v.performance.powerKw !== best.performance.powerKw) {
      return v.performance.powerKw > best.performance.powerKw ? v : best;
    }
    return v.battery.capacityKwh > best.battery.capacityKwh ? v : best;
  });
}

/** Longest published range for a vehicle, with its cycle preserved. */
export function bestRange(vehicle: Vehicle): RangeFigure | undefined {
  const all = vehicle.variants.flatMap((v) => v.range);
  if (all.length === 0) return undefined;
  return all.reduce((best, r) => (r.km > best.km ? r : best));
}

/** Range on one cycle only, so comparison tables never mix standards. */
export function rangeOnCycle(variant: Variant, cycle: RangeCycle): number | undefined {
  return variant.range.find((r) => r.cycle === cycle)?.km;
}

export function formatPower(kw: number): string {
  return `${kw} kW (${Math.round(kw * 1.34102)} hp)`;
}
