import type { CarDriveMode, DriveCamera, DriveSpec, Variant, Vehicle } from '../../data/vehicles/schema';

export type DriveSurface = 'dry' | 'wet';
import { DRIVE_MODES, effectivePowerKw, efficiencyKwhPer100km, type DriveMode } from '../performance';
import { driveTimes, runList, type DriveInput, type DriveMotor, type DriveRunInfo } from './drive-run';

/**
 * Turns a car, its trim and the visitor's choices (mode, load, run, a stop) into what the planner needs
 * (`DriveInput`, drive-run.ts). The figures are the variant's; the scenario (`Vehicle.drive`) says what is particular to
 * the car; what neither says is ours and is said on screen. A car with no scenario of its own gets the generic one: a
 * standing start, its 0-100 and 0-200 and a coast.
 */

/** the driver alone, kg: the load the maker's times are taken to be for (ours) */
export const DRIVER_KG = 75;
/** a kerb weight for the cars whose data has none; used only as a ratio, never shown */
const KERB_FALLBACK = 2300;

/** The Drive tab's cameras: where it looks from (azimuth about the car from its nose, elevation, degrees; the stage's look, anchors.ts). */
export const DRIVE_CAMERAS: Record<DriveCamera, { az: number; el: number; label: string }> = {
  hero: { az: 72, el: 8, label: 'Hero' },
  chase: { az: 158, el: 11, label: 'Chase' },
  side: { az: 90, el: 3, label: 'Side' },
  top: { az: 90, el: 80, label: 'Top' },
  // the cabin's camera is the driver's seat (the store's 'driver' anchor), its az and el are not used
  cabin: { az: 0, el: 0, label: 'Cabin' },
  xray: { az: 52, el: 24, label: 'X-ray' },
};

/** The cameras a car offers: all the outside ones, the seat where it has a cabin, the X-ray where it has a cabin to see through. */
export function camerasOf(vehicle: Vehicle): DriveCamera[] {
  const cams: DriveCamera[] = ['hero', 'chase', 'side', 'top'];
  if (vehicle.assets.interiorModelUrl) cams.push('cabin', 'xray');
  return cams;
}

export interface DriveSelection {
  variantId?: string | null;
  modeId?: string | null;
  loadId?: string | null;
  runId?: string | null;
  /** a stop after the run: null leaves it to the scenario */
  brake?: boolean | null;
  /** the road: dry (the maker's own run) or wet, and the hill in per cent (negative: downhill) */
  surface?: DriveSurface | null;
  grade?: number | null;
  /** the slug of the rival drawn beside the car, when there is one (src/lib/tech/drive-rival.ts) */
  rival?: string | null;
}

export interface DriveLoad {
  id: string;
  label: string;
  payloadKg: number;
}

export interface DriveSetup {
  spec: DriveSpec;
  /** the scenario is the car's own, not the generic one */
  own: boolean;
  variant: Variant;
  modes: CarDriveMode[];
  mode: CarDriveMode;
  loads: DriveLoad[];
  load: DriveLoad;
  runs: DriveRunInfo[];
  run: DriveRunInfo;
  input: DriveInput;
  /** the stop is on: the scenario's, or the visitor's */
  brake: boolean;
  /** the stop can be switched (a scenario with a manoeuvre ends in its own) */
  canBrake: boolean;
  camera: DriveCamera;
  kerbKg: number;
  massKg: number;
}

const GENERIC: DriveSpec = {
  id: 'launch',
  title: 'Drive & Launch',
  blurb: 'A standing start to 100 km/h and on to 200, on the car’s published times.',
  modes: [],
  defaultMode: '',
  overlays: ['power', 'energy'],
  finish: 'coast',
  callouts: [],
  claims: [],
  simulated: '',
};

/** The power the mode lets through and how stiff the body is in it: ours, shown as such. */
const SQUAT_BY_MODE: Record<DriveMode, number> = { eco: 1.15, comfort: 1.1, sport: 0.85, track: 0.75 };

/** The car's modes the scenario offers; the generic four where the car lists none of its own. */
function modesOf(vehicle: Vehicle, spec: DriveSpec): CarDriveMode[] {
  const own = vehicle.cockpit.driveModes;
  if (!own?.length) {
    return DRIVE_MODES.filter((m) => m.id !== 'track').map((m) => ({ id: m.id, label: m.label, group: 'street', model: m.id }));
  }
  const picked = spec.modes.map((id) => own.find((m) => m.id === id)).filter((m): m is CarDriveMode => Boolean(m));
  if (picked.length) return picked;
  // no list of its own: the street modes the car's screen shows
  return own.filter((m) => m.group === 'street').slice(0, 4);
}

/** How the motors share the drive when the car pulls straight: the layout and the motor count are the variant's, the split is ours. */
export function motorsOf(variant: Variant): DriveMotor[] {
  const n = variant.performance.motorCount;
  if (n >= 3) {
    return [
      { id: 'front', label: 'Front', axle: 'front', share: 0.25 },
      { id: 'rear-left', label: 'Rear left', axle: 'rear', side: 'left', share: 0.375 },
      { id: 'rear-right', label: 'Rear right', axle: 'rear', side: 'right', share: 0.375 },
    ];
  }
  if (n === 2 && variant.drive === 'AWD') {
    return [
      { id: 'front', label: 'Front', axle: 'front', share: 0.4 },
      { id: 'rear', label: 'Rear', axle: 'rear', share: 0.6 },
    ];
  }
  if (n === 2) {
    return [
      { id: 'rear-left', label: 'Rear left', axle: 'rear', side: 'left', share: 0.5 },
      { id: 'rear-right', label: 'Rear right', axle: 'rear', side: 'right', share: 0.5 },
    ];
  }
  if (variant.drive === 'FWD') return [{ id: 'front', label: 'Front', axle: 'front', share: 1 }];
  return [{ id: 'rear', label: 'Rear', axle: 'rear', share: 1 }];
}

/** The maker's 0-200 where it has one; else ours from the 0-100 (a car that reaches 200 km/h), flagged as an estimate. */
export function timesOf(variant: Variant) {
  const perf = variant.performance;
  const t100 = perf.zeroTo100S ?? 3.5;
  const published200 = perf.zeroTo200S !== undefined;
  const t200 =
    perf.zeroTo200S ?? (perf.topSpeedKmh && perf.topSpeedKmh >= 200 ? Math.round(t100 * 3.15 * 10) / 10 : undefined);
  return { t100, t200, published200 };
}

export function driveSetup(vehicle: Vehicle, sel: DriveSelection = {}): DriveSetup {
  const own = Boolean(vehicle.drive);
  const spec = vehicle.drive ?? GENERIC;
  const variant = vehicle.variants.find((v) => v.id === sel.variantId) ?? vehicle.variants[0];
  const perf = variant.performance;
  const { t100, t200, published200 } = timesOf(variant);

  const modes = modesOf(vehicle, spec);
  const fullPower = (m: CarDriveMode) => effectivePowerKw(variant, m.model, m.powerKw) / perf.powerKw;
  const standard =
    modes.find((m) => m.id === spec.defaultMode) ??
    modes.reduce((best, m) => (fullPower(m) > fullPower(best) ? m : best), modes[0]);
  const mode = modes.find((m) => m.id === sel.modeId) ?? standard;
  const powerFrac = Math.min(1, fullPower(mode));

  const loads: DriveLoad[] = spec.loads?.length ? spec.loads : [{ id: 'driver', label: 'Driver', payloadKg: DRIVER_KG }];
  const load = loads.find((l) => l.id === sel.loadId) ?? loads[0];
  const kerbKg = vehicle.dimensions.kerbWeightKg ?? KERB_FALLBACK;
  const refMassKg = kerbKg + DRIVER_KG;
  const massKg = kerbKg + load.payloadKg;
  const env = { wet: sel.surface === 'wet', gradePct: sel.grade ?? 0 };
  // the maker's run is full power, the driver alone, dry and level
  const nominal = powerFrac >= 0.999 && Math.abs(massKg - refMassKg) < 1 && !env.wet && env.gradePct === 0;

  const c = spec.chassis ?? {};
  const suv = vehicle.bodyStyle === 'SUV' || vehicle.bodyStyle === 'Coupe SUV';
  const d = vehicle.dimensions;
  const area = spec.aero?.areaM2 ?? 0.85 * (d.widthMm / 1000) * (d.heightMm / 1000);
  const cdA = (spec.aero?.cd ?? 0.27) * area;
  const manoeuvres = spec.manoeuvres?.length ? spec.manoeuvres : undefined;

  const base: Omit<DriveInput, 'from' | 'to'> = {
    zeroTo100: t100,
    zeroTo200: t200,
    zeroTo200Published: published200,
    peakKw: perf.powerKw,
    peakNm: perf.torqueNm,
    powerFrac,
    squatScale: SQUAT_BY_MODE[mode.model],
    massKg,
    refMassKg,
    nominal,
    kwhPer100: efficiencyKwhPer100km(variant, 'comfort', { acOn: false, fanSpeed: 0 }),
    motors: motorsOf(variant),
    chassis: {
      squatDegPerG: c.squatDegPerG ?? (suv ? 1.1 : 0.9),
      rollDegPerG: c.rollDegPerG ?? (suv ? 1.7 : 1.3),
      cgHeightM: c.cgHeightM ?? (suv ? 0.62 : 0.55),
      staticRear: c.staticRear ?? 0.5,
      rearSteerMaxDeg: c.rearSteerMaxDeg ?? 0,
      crabDeg: c.crabDeg ?? 15,
    },
    cdA,
    finish: spec.finish,
    cruiseKmh: spec.cruiseKmh,
    brake100M: spec.brake100M,
    manoeuvres,
    runs: spec.runs,
    env,
  };

  const shown = driveTimes(t100, t200, powerFrac, massKg / refMassKg);
  const runs = runList(base, shown.t100, shown.t200);
  const wanted = sel.runId ?? spec.defaultRun;
  const run = runs.find((r) => r.id === wanted) ?? runs[0];

  // a scenario that ends in a manoeuvre ends in its own stop; the others take the visitor's choice, else the scenario's
  const canBrake = !(manoeuvres && run.to <= 150);
  const brake = canBrake && (sel.brake ?? spec.finish === 'brake');

  return {
    spec,
    own,
    variant,
    modes,
    mode,
    loads,
    load,
    runs,
    run,
    input: { ...base, from: run.from, to: run.to },
    brake,
    canBrake,
    camera: spec.camera ?? 'hero',
    kerbKg,
    massKg,
  };
}
