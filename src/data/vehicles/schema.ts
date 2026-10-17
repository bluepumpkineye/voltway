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
  /** 0-200 km/h in seconds, when the maker publishes it. */
  zeroTo200S?: number;
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
  /** The hue (0-360) the ambient light opens at, where the maker's is not the generic warm one. */
  ambientHue?: number;
  /** The theme the in-car UI opens in, where the maker's own is not the dark one (ZEEKR OS opens light). */
  defaultTheme?: 'dark' | 'light';
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
   * The model is built for the showroom only (/showroom/[slug]): the vehicle page
   * and the home page do not draw it in their own 3D viewer or call it ready.
   */
  showroomOnly?: boolean;
  /**
   * A multiplier on the cabin's baked light, 1 when unset (CarModel.tsx `CABIN_GAIN`): a pale
   * cabin lit by daylight through the glass reads darker than the studio photographs of it, and
   * this lifts it without re-baking.
   */
  cabinGain?: number;
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
  /**
   * The car's shadow on the studio floor, baked in Blender
   * (carkit.studio.ground_shadow): a WebP whose alpha is the shade. `size` and
   * `centre` are what the build printed, in the build's axes (x forward, y
   * left); without it the studio falls back to a projected contact shadow.
   */
  studioShadow?: { url: string; size: [number, number]; centre: [number, number] };
  /**
   * A stand-in of the exterior for a stage in which another car's demo parks it as a neighbour
   * (scripts/make-proxy.mjs): about 12k triangles, paint, glass, trim, tyres and rims under plain
   * material names.
   */
  proxyUrl?: string;
  heroColor: string;
}

export interface Source {
  label: string;
  url: string;
}

// ------------------------------------------------------------ configurator

/**
 * How a paint is finished, as the parameters of the exterior's clearcoated
 * paint material (a MeshPhysicalMaterial once glTF has loaded it). Anything
 * left out keeps the build's own value, so a finish only has to say what
 * differs from the car as built.
 */
export interface PaintFinish {
  /** The body colour as seen in daylight, sRGB hex (converted to linear on use). */
  color: string;
  roughness?: number;
  /** The shipped paint is dielectric; a metallic finish raises this a little. */
  metalness?: number;
  clearcoat?: number;
  clearcoatRoughness?: number;
  /** Lobe weight at grazing angles (the RX's blue-violet shift). Omit for none. */
  sheen?: { color: string; roughness?: number; weight?: number };
}

/**
 * One paint the car is sold in. The first entry of `paints` is the colour the
 * Blender build is painted in and carries no `finish`: choosing it restores the
 * material exactly as exported.
 */
export interface PaintOption {
  id: string;
  /** English display name; `nameZh` is the maker's own name. */
  name: string;
  nameZh?: string;
  /** CSS background for the swatch: a colour, or a gradient for a shifting paint. */
  swatch: string;
  finish?: PaintFinish;
}

/**
 * One cabin colourway. `colors` maps a cabin material's name (case-insensitive,
 * as exported: `INT_Leather_Accent`) to the colour factor it takes. The cabin's
 * lighting is baked as light only, never as albedo, so recolouring a material
 * is shaded correctly. The first entry is the cabin as built, with no `colors`.
 */
export interface TrimOption {
  id: string;
  name: string;
  nameZh?: string;
  /** Two-tone swatch: the main surface, then the accent. */
  swatch: [string, string];
  colors?: Record<string, string>;
}

/**
 * One colour the brake calipers are offered in. The first entry of `calipers`
 * is the colour the Blender build is painted in: choosing it restores the
 * material exactly as exported.
 */
export interface CaliperOption {
  id: string;
  /** English display name; `nameZh` is the maker's own. */
  name: string;
  nameZh?: string;
  /** The painted colour in daylight, sRGB hex: the swatch, and what the material takes. */
  color: string;
}

/**
 * One wheel design the car is offered with. Each is a node of the exterior GLB that
 * holds all four wheels; the viewer shows the chosen one and hides the rest. The first
 * entry of `wheels` is the design the model shows to begin with.
 */
export interface WheelOption {
  id: string;
  /** English display name; `nameZh` is the maker's own. */
  name: string;
  nameZh?: string;
  /** Rim diameter, and the tyres on it as the maker lists them. */
  size: string;
  tyres: string;
  /** The exterior GLB's node for the design. Designs that differ only in paint share one. */
  node: string;
  /**
   * The design's accent paint: a material of the exterior and the colour it takes (sRGB hex).
   * metalness and roughness, when given, are taken too: one model can then be a silver metal or a
   * gloss black (the Zeekr 7X's twin-fork); left out, the material keeps what it has (the RX's
   * Sport swaps the colour of a dielectric).
   */
  accent?: { material: string; color: string; metalness?: number; roughness?: number };
  /** The caliper colour it is shown with first (an id of `calipers`), as on the photographed cars. */
  caliper?: string;
}

/** The named camera poses the showroom flies between. */
export type AnchorId =
  | 'hero'
  | 'doorsL'
  | 'doorsR'
  | 'side'
  | 'front'
  | 'rear'
  | 'rear34'
  | 'wheel'
  | 'xray'
  | 'frunk'
  | 'trunk'
  | 'techWide'
  // the Dashboard tab: the car's screen beside the car, looking at one end of it
  | 'dashFront'
  | 'dashRear'
  | 'driver';

/**
 * What a car offers the showroom. Colour values are matched by eye to the
 * maker's published imagery under Voltway's studio rig, so the interface calls
 * them approximate; the names, and which options exist, are the maker's.
 */
export interface ConfiguratorSpec {
  /** Exact name of the paint material in the exterior GLB (case-insensitive). */
  paintMaterial: string;
  paints: PaintOption[];
  trims: TrimOption[];
  /** Exact name of the caliper material in the exterior GLB (case-insensitive). */
  caliperMaterial?: string;
  /** The colours the calipers come in, when the maker offers a choice. */
  calipers?: CaliperOption[];
  /** The wheel designs the car can be had with, when the model carries more than one. */
  wheels?: WheelOption[];
  /** Where the options come from, cited on the vehicle page. */
  sources: Source[];
}

/** The parts that swing open. */
export type OpeningId = 'doorFL' | 'doorFR' | 'doorRL' | 'doorRR' | 'frunk' | 'boot' | 'charge';

/** A gas strut holding a part open: fixed on the body, moving with the part. */
export interface StrutSpec {
  /** Body-side mount, in the exterior model's space (glTF, y up). */
  body: [number, number, number];
  /** Mount on the moving part, as it sits when the part is shut. */
  moving: [number, number, number];
}

/** One hinged part and the glTF nodes that carry it (nodes sit on the hinge). */
export interface OpeningSpec {
  id: OpeningId;
  /** The exterior GLB's node for the part, its origin on the hinge. */
  node: string;
  /** The cabin GLB's matching node (the door card), on the same hinge. */
  cardNode?: string;
  /** An exterior node shown only while the part is open (a door's painted frame). */
  frameNode?: string;
  /** Cabin nodes that go while the part is open (the shelf under the tailgate's glass). */
  hides?: string[];
  /** Cabin nodes that go while the part is open and the camera is outside (trims seen from inside). */
  hidesOutside?: string[];
  /** The part is not drawn while the X-ray tab is on (the doors). */
  xrayHide?: boolean;
  /** The node-local axis the hinge turns about (glTF, y up). Default 'y'. */
  axis?: 'x' | 'y' | 'z';
  /** How far it swings when open, in degrees; the sign is the direction. */
  deg: number;
  /** Gas struts that follow the swing (the bonnet's, the tailgate's). */
  struts?: StrutSpec[];
}

/**
 * The X-ray tab: the greenhouse (glass, roof, pillars) turns to one pale ghost,
 * the doors and the dark hull go, and the cabin shows through (the way the
 * HIMA showroom does it: a pre-split ghost twin of the upper body).
 */
export interface XraySpec {
  /** The exterior node that becomes the ghost. */
  node: string;
  /** Its colour (sRGB hex) and opacity. */
  color: string;
  opacity: number;
  /** Cabin nodes that go while it is on (the headliner shuts the view from above). */
  hideCabin?: string[];
}

/** A published fact a tech demo shows, with where it comes from. */
export interface TechClaim {
  text: string;
  source: Source;
}

/**
 * Where a visitor can start a demonstration from, as the car's owner would: the phone in their hand
 * (the maker's app), or the car's own screen.
 */
export type TechDevice = 'phone' | 'dashboard';

/**
 * One demonstration in the showroom's Tech tab (docs/tech-showcase.md). The
 * motion is code, `driver` names it in src/lib/tech/demos.ts; this is what the
 * visitor reads: the title, the published claims, and what is illustrative.
 */
export interface TechDemoSpec {
  id: string;
  title: string;
  /** one line about what the demo shows */
  blurb: string;
  /** the motion driver (src/lib/tech/demos.ts) */
  driver: string;
  /**
   * The devices the demo starts from, the first being the one shown to begin with. A demo with none
   * is started from the playback bar alone (a test of the rig).
   */
  devices?: TechDevice[];
  /** published facts shown with the demo, each cited */
  claims: TechClaim[];
  /** what is illustrative, shown with the demo: "A simulated path, not the maker's footage." */
  simulated: string;
  /** offered only while developing (a test of the rig, not a feature of the car) */
  devOnly?: boolean;
  /** numbers the demo's driver takes (the pack's size for the charge demo) */
  params?: Record<string, number>;
  /**
   * Where the camera is for the demo: the Tech tab's wide shot of the car on its stage when left out; 'cabin' puts
   * it in the driver's seat (the swivel screen's demo, whose subject is a part of the cabin).
   */
  view?: 'cabin';
}

/**
 * A car's fast charging, for the showroom's Charging tab (src/lib/tech/charging.ts). The window and the peak are the
 * maker's where it publishes them; a peak it does not publish is derived (from the C-rate it does, or from the
 * window's average power), and the tab says which.
 */
export interface ChargingSpec {
  /** the window the maker quotes, state of charge in per cent, and the minutes it takes at best */
  window: { from: number; to: number; minutes: number };
  /** the peak DC power, kW, when the maker publishes it */
  peakKw?: number;
  /** the maker's C-rate, when it is the peak that is published this way (the peak is then C x the pack) */
  cRate?: number;
  /** the pack the figures are for, kWh */
  packKwh: number;
  /** the voltage architecture */
  architectureV?: number;
  /** the DC connector standard */
  connector: string;
  /**
   * Where the port is. `published` says whether a source gives the side; the place along the car is ours either way
   * (the model has no flap, so the socket is drawn where `Vehicle.chargePort` puts it).
   */
  port: { side: 'left' | 'right'; published: boolean; where: string };
  /** published facts shown with the tab, each cited */
  claims: TechClaim[];
  /** what is illustrative */
  simulated: string;
}

/**
 * Where a car's sensors sit, for the sensor demo (docs/tech-showcase.md section 12), in the exterior model's space (glTF:
 * x forward, y up, z toward the passenger side). `mirror` puts a second one on the other side (z negated).
 */
export interface SensorSpec {
  /** the forward lidar's window, in the roof housing (photographed) */
  lidar: [number, number, number];
  /**
   * The forward lidar's field of view where the maker publishes one, degrees (the SU7's Hesai AT128: 120 by 25.4); the
   * drawing's reach is ours. Without it the demo draws the Luxeed RX's two paths (a wide and a tele one).
   */
  lidarFov?: number;
  /**
   * Where the solid-state lidars are drawn from, the passenger side's (mirrored for the driver's side). Reported at the
   * fenders by one secondary source; the photographs show cameras and a slot there, no marked lidar. Left out for a car
   * that has none.
   */
  sideLidar?: [number, number, number];
  /** the rear solid-state lidar: the maker does not say where it is. Left out for a car that has none. */
  rearLidar?: [number, number, number];
  /**
   * The surround cameras' coverage, drawn as the four diagonal beams of the maker's own animation (Xiaomi's, for the
   * SU7), from the middle of the car: illustrative, and the panel says so.
   */
  surround?: boolean;
  /** cameras and ultrasonic sensors that the photographs show, as far as they could be read off them */
  cameras: { at: [number, number, number]; mirror?: boolean }[];
  ultrasonic: { at: [number, number, number]; mirror?: boolean }[];
  /** what each switch on the demo's panel says it is (a tooltip): the maker's counts, where it gives them */
  notes?: Partial<Record<'lidar' | 'side' | 'rear' | 'ultrasonic' | 'cameras' | 'surround', string>>;
}

/**
 * A centre screen on a motorised mount (the Luxeed RX's): how it moves. The figures are the maker's
 * (docs/tech-showcase.md section 13); the hub is where the model's screen turns, and the cabin node is the mesh
 * the screen's frame is cut out of (the cabin is one merged mesh per material).
 */
export interface SwivelSpec {
  /** the cabin GLB's node whose meshes hold the screen's frame */
  cabinNode: string;
  /** how far it turns to either side, degrees */
  turnDeg: number;
  /** how far it slides forward and back, m */
  travelM: number;
  /** the vertical axis it turns about, as x and z in the cabin model's space (glTF: x forward, z toward the passenger side) */
  hub: [number, number];
}

/**
 * One lit part of a car, as the showroom lights it (docs/lights.md): which material of the exterior is
 * the LED the build models, and the light it gives. Anything left out takes the default of its end of the
 * car (src/lib/lights.ts), so a car whose export follows the usual material names needs none of this.
 */
export interface LampSpec {
  /** the exterior's material that is the lit part (case-insensitive) */
  material?: string;
  /** the light of the lamp itself, sRGB */
  color?: string;
  /** the glow round it, sRGB */
  halo?: string;
  /** emissive strength with the lamp off, when that is not what the build gave the material; fully lit */
  off?: number;
  on?: number;
}

/**
 * The lamps the showroom can switch on (the headlamp switch of the car's screen, the Dashboard tab). The
 * cars are built with their LED lines as materials of their own: the front line, the rear one, and where
 * modelled, the projector lenses. No light is added that the build does not have.
 */
export interface LightsSpec {
  front?: LampSpec;
  /** the projector lenses, when they are a material of their own that is at the front only */
  projector?: LampSpec;
  rear?: LampSpec;
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
  /** Paint and trim options for the showroom (see ConfiguratorSpec). */
  configurator?: ConfiguratorSpec;
  /** Parts that open in 3D (doors, bonnet, tailgate), see OpeningSpec. */
  openings?: OpeningSpec[];
  /** What the X-ray tab does to this car's model, see XraySpec. */
  xray?: XraySpec;
  /** The Tech tab's demonstrations, see TechDemoSpec. */
  tech?: TechDemoSpec[];
  /**
   * The DC charge port, for the Charging tab's gun: the mouth of the DC socket in the viewer's axes (x forward, y up,
   * z toward the passenger side), the direction pointing out of it, and how far a gun's nose goes in, m. A car whose
   * model has no flap gets a socket drawn at the mouth (src/components/viewer/TechCharge.tsx).
   */
  chargePort?: { mouth: [number, number, number]; axis: [number, number, number]; depth: number };
  /** The car's fast charging, for the Charging tab: the maker's figures and the port's side, see ChargingSpec. */
  charging?: ChargingSpec;
  /** Which parts of the exterior are the lamps, see LightsSpec. */
  lights?: LightsSpec;
  /** The BOOST knob on the steering wheel, in the cabin model's space (glTF), for the BOOST demo. */
  boost?: { knob: [number, number, number] };
  /** Where the sensors sit, when the car has a sensor demo, see SensorSpec. */
  sensors?: SensorSpec;
  /** The centre screen's mount, when it moves (the cabin's `screen_main` and its frame turn about the hub). */
  swivel?: SwivelSpec;
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
