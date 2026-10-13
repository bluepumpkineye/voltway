import type { TechDemoSpec, Vehicle } from '@/data/vehicles/schema';
import { vehicles } from '@/data/vehicles';
import { arc, MOTION, Track, type Layout, type PlannedRun, type Segment } from './kinematics';
import { planCarpet, stiffnessOf, type CarpetRun, type RoadStage } from './carpet';
import { planCharge, type ChargeRun } from './charge';
import { planLaunch, type LaunchRun } from './launch';
import { planPark, PARK_MOTION, type BodyBox, type ParkSpeed, type ParkStage, type Pose } from './park';
import type { Chassis, RideMode } from './ride';
import { planBoost, type BoostRun } from './boost';
import { planSensors, type SensorsRun } from './sensors';
import { planSwivel, type SwivelRun } from './swivel';

/** The demos the visitor is offered: development-only ones are left out of a production build. */
export function visibleDemos(vehicle: Vehicle): TechDemoSpec[] {
  return (vehicle.tech ?? []).filter((d) => !d.devOnly || process.env.NODE_ENV !== 'production');
}

/** What a driver is given: the car as the rig measured it, and the visitor's settings. */
export interface DemoContext {
  vehicle: Vehicle;
  layout: Layout;
  /** from the rear axle's middle; the half width is the published body width (the mirrors fold in) */
  body: BodyBox;
  /** the rear axle's middle where the car stands in the showroom, heading +x */
  start: Pose;
  /** the car's own parking-speed setting */
  speed: ParkSpeed;
  /** the car's ride settings (the Magic Carpet demo): the control on, the drive mode's id */
  ride: { carpet: boolean; modeId: string | null };
  /** the numbers the demo's spec gives its driver (`TechDemoSpec.params`) */
  params: Record<string, number>;
}

/** A demo's motion, built for one car. */
export interface BuiltDemo {
  track: PlannedRun;
  /** times the clock waits at for the visitor (the car parked, until they ask for the way out) */
  stops: number[];
  /** starts by itself when the demo opens (the rig test); the others wait for a device */
  autoplay: boolean;
  /** draw the path of the rear axle on the floor */
  trail: boolean;
  /** the lot the car drives in, when it has one */
  stage: ParkStage | null;
  /** where the camera looks, when the demo has a view of its own (the charge port's side of the car) */
  frame?: CarpetRun['frame'];
  /** the fast-charge demo: the flap, the gun, the readout (the director opens the flap and sets the charge level) */
  charge?: ChargeRun;
  /** the BOOST demo: whether BOOST is on and how many of its steps have been applied at each time */
  boost?: BoostRun;
  /** the sensor demo: the pedestrian and the readout (the director publishes them, and sets the brake lamps) */
  sensors?: SensorsRun;
  /** the swivel screen's demo: the pose the car's screen is asked for at each time (the director writes it to the store) */
  swivel?: SwivelRun;
  /**
   * A demo that keeps the car on the spot and rolls a road under it (the Magic Carpet's run, the launch): the road,
   * how far it has rolled at time t, the body's motion on its springs and the wheels' travel, and the look the
   * camera takes. A run with a choice of suspensions (the Magic Carpet) also hands both for the chart; the launch
   * hands its readout.
   */
  treadmill?: {
    road: RoadStage;
    scroll: (t: number) => number;
    chassis: (t: number) => Chassis;
    frame: CarpetRun['frame'];
    ride?: { modes: CarpetRun['modes']; mode: RideMode };
    launch?: LaunchRun['launch'];
  };
}

/**
 * The motion of each tech demo, by the `driver` name a vehicle's `tech` entry gives
 * (TechDemoSpec in src/data/vehicles/schema.ts). A driver turns the car's measured
 * wheels into a plan; the same driver therefore drives any car that has a rig.
 */
export interface Driver {
  build: (ctx: DemoContext) => BuiltDemo;
}

const DEG = Math.PI / 180;

/** A test of the rig, not a feature of any car: every steering mode in one run. */
const rigTest: Driver = {
  build: ({ layout, start }) => {
    const L = layout;
    const plan: Segment[] = [
      { kind: 'move', distance: 2 },
      arc(4.5, 90, 'left'),
      arc(4.5, 90, 'left', true),
      { kind: 'move', distance: 2.5, angle: 12 * DEG },
      { kind: 'turn', about: L.wheels.FL, angle: 90 * DEG },
      { kind: 'turn', about: { x: L.wheelbase / 2, y: 4.5 }, angle: 60 * DEG },
      { kind: 'move', distance: -3 },
    ];
    return { track: new Track(layout, plan, MOTION, start), stops: [], autoplay: true, trail: true, stage: null };
  },
};

/**
 * The cars in the other four bays (west to east): the other modelled cars beside the empty bay, the demo's own
 * car, in another colour, and one of the others at the ends. Nose in and out alternate, as a real row of bays has.
 */
function neighboursOf(vehicle: Vehicle) {
  const others = vehicles.filter((v) => v.slug !== vehicle.slug && v.assets.proxyUrl);
  const self = vehicles.filter((v) => v.slug === vehicle.slug && v.assets.proxyUrl);
  const row = [self[0] ?? others[0], others[0], others[1] ?? others[0], others[1] ?? others[0]];
  return row
    .filter(Boolean)
    .map((v, i) => ({
      slug: v.slug,
      length: v.dimensions.lengthMm / 1000,
      width: v.dimensions.widthMm / 1000,
      noseOut: i % 2 === 1,
    }));
}

/** Park from your phone: a reverse-in to a bay between two parked cars, and the way out again. */
const park: Driver = {
  build: ({ vehicle, layout, body, start, speed }) => {
    const plan = planPark(layout, body, start, PARK_MOTION[speed], { neighbours: neighboursOf(vehicle) });
    return { track: plan.track, stops: plan.stops, autoplay: false, trail: false, stage: plan.stage };
  },
};

/** Magic Carpet: three speed humps at 16 km/h, ridden out by a passive suspension or floated over by the carpet. */
const carpet: Driver = {
  build: ({ layout, body, start, ride }) => {
    const run = planCarpet(layout, body, start, { stiffness: stiffnessOf(ride.modeId) });
    return {
      track: run.track,
      stops: [],
      autoplay: false,
      trail: false,
      stage: null,
      treadmill: {
        road: run.road,
        scroll: run.scroll,
        chassis: run.modes[ride.carpet ? 'carpet' : 'passive'].sample,
        frame: run.frame,
        ride: { modes: run.modes, mode: ride.carpet ? 'carpet' : 'passive' },
      },
    };
  },
};

/**
 * A standing start to 100 km/h on the car's published time, on a road that rolls under it: the tail squats, the
 * nose comes up, the wheels spin a little ahead of the road. Our shape throughout (launch.ts says which parts).
 */
const launch: Driver = {
  build: ({ vehicle, layout, body, start }) => {
    const perf = vehicle.variants[0]?.performance;
    const run = planLaunch(layout, body, start, { zeroTo100: perf?.zeroTo100S ?? 3, zeroTo200: perf?.zeroTo200S });
    return {
      track: run.track,
      stops: [],
      autoplay: false,
      trail: false,
      stage: null,
      treadmill: { road: run.road, scroll: run.scroll, chassis: run.chassis, frame: run.frame, launch: run.launch },
    };
  },
};

/**
 * Fast charge: the flap opens, a gun comes off its pedestal and goes into the DC socket, the car charges from 10 to 80 %
 * on the published ten minutes (played in fourteen seconds), the gun goes home and the flap shuts.
 */
const charge: Driver = {
  build: ({ vehicle, layout, body, start, params }) => {
    const port = vehicle.chargePort ?? { mouth: [-1.4, 1, -0.85], axis: [0, 0, -1], depth: 0.02 };
    const run = planCharge(layout, body, start, { port, kwh: params.packKwh ?? 100 });
    return { track: run.track, stops: run.stops, autoplay: false, trail: false, stage: null, frame: run.frame, charge: run };
  },
};

/**
 * What the car sees: the sensors' coverage is drawn, a pedestrian steps off the kerb ahead, and the car brakes to a stop
 * short of them. The scenario is ours (sensors.ts); the road rolls under the car like the launch's.
 */
const sensors: Driver = {
  build: ({ layout, body, start }) => {
    const run = planSensors(layout, body, start);
    return {
      track: run.track,
      stops: [],
      autoplay: false,
      trail: false,
      stage: null,
      sensors: run,
      treadmill: { road: run.road, scroll: run.scroll, chassis: run.chassis, frame: run.frame },
    };
  },
};

/** The RX's BOOST, from the driver's seat: the knob is pressed, its effects are applied in turn, and it is pressed again. */
const boost: Driver = {
  build: ({ start }) => {
    const run = planBoost(start);
    return { track: run.track, stops: [], autoplay: false, trail: false, stage: null, boost: run };
  },
};

/** The RX's swivel screen, seen from the driver's seat: the car stands still, the screen is pressed through its four ways. */
const swivel: Driver = {
  build: ({ start }) => {
    const run = planSwivel(start);
    return { track: run.track, stops: [], autoplay: false, trail: false, stage: null, swivel: run };
  },
};

export const DRIVERS: Record<string, Driver> = { 'rig-test': rigTest, park, carpet, launch, charge, swivel, sensors, boost };
