import type { TechDemoSpec, Vehicle } from '@/data/vehicles/schema';
import { vehicles } from '@/data/vehicles';
import { arc, MOTION, Track, type Layout, type Segment } from './kinematics';
import { planPark, PARK_MOTION, type BodyBox, type ParkSpeed, type ParkStage, type Pose } from './park';

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
}

/** A demo's motion, built for one car. */
export interface BuiltDemo {
  track: Track;
  /** times the clock waits at for the visitor (the car parked, until they ask for the way out) */
  stops: number[];
  /** starts by itself when the demo opens (the rig test); the others wait for a device */
  autoplay: boolean;
  /** draw the path of the rear axle on the floor */
  trail: boolean;
  /** the lot the car drives in, when it has one */
  stage: ParkStage | null;
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

export const DRIVERS: Record<string, Driver> = { 'rig-test': rigTest, park };
