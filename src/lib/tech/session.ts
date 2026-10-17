/**
 * What the running demo shows to the devices of the Tech tab (the phone, the car's screen).
 *
 * The TechDirector (inside the Canvas) builds the demo from the car's measured wheels and
 * publishes it here; the devices are plain DOM outside the Canvas, so they read it from
 * here: the stage to draw as a top view, the car's pose at any time, the car's body.
 * Like the clock, it is a small vanilla store, not React state: the car's pose changes every
 * frame, and only the devices that draw it should wake.
 */
import React from 'react';
import { useTechClock } from './clock';
import type { RoadStage } from './carpet';
import type { ChargeReadout, ChargeRun } from './charge';
import type { LaunchRun } from './launch';
import type { SensorsRun } from './sensors';
import type { RideMode, RideRun } from './ride';
import type { Sample } from './kinematics';
import type { BodyBox, ParkStage } from './park';
import type { StreetRun, StreetStage } from './street';

export interface Runtime {
  demoId: string;
  /** the floor the demo is staged on, when it has one */
  stage: ParkStage | null;
  /** the middle of the rear axle at time t (floor frame, kinematics axes) */
  sample: (t: number) => Sample;
  /** the car's body from the rear axle, the published width */
  body: BodyBox;
  /** the road a treadmill demo rolls under the car (the Magic Carpet's humps), drawn by TechRoad */
  road?: RoadStage | null;
  /** the ride of a treadmill demo with each suspension (for the chart), and the one on show */
  ride?: { modes: Record<RideMode, RideRun>; mode: RideMode } | null;
  /** the launch's speed, pull and stopwatch at time t, and the published times it is checked against (its readout) */
  launch?: LaunchRun['launch'] | null;
  /** the fast-charge demo: the gun, the readout and the curve (the car's charging page, the pedestal, the chart) */
  charge?: Pick<ChargeRun, 'readout' | 'gun' | 'curve' | 'pedestal' | 'cableOut' | 'gunExit' | 'profile'> | null;
  /** the Autonomous Drive demo: the traffic, the car's own place among it and the readout at time t */
  sensors?: SensorsRun['scenario'] | null;
  /** a chassis demo (crab walk, compass turn, U-turn): the wheels' readout at time t, the street and what the manoeuvre needed */
  chassis?: { readout: StreetRun['readout']; facts: StreetRun['facts']; stage: StreetStage } | null;
}

type Listener = () => void;

class TechSession {
  runtime: Runtime | null = null;
  private subs = new Set<Listener>();

  set(r: Runtime | null) {
    this.runtime = r;
    for (const fn of this.subs) fn();
  }

  subscribe = (fn: Listener) => {
    this.subs.add(fn);
    return () => {
      this.subs.delete(fn);
    };
  };

  snapshot = () => this.runtime;
}

export const techSession = new TechSession();

/** The running demo, or null while there is none (no demo chosen, the model still loading). */
export function useRuntime(): Runtime | null {
  return React.useSyncExternalStore(techSession.subscribe, techSession.snapshot, () => null);
}

/** A chassis demo's readout at the clock's time (10 Hz while it runs), or null when no such demo is on. */
export function useChassisReadout(): ReturnType<NonNullable<Runtime['chassis']>['readout']> | null {
  const chassis = useRuntime()?.chassis;
  const clock = useTechClock();
  return chassis ? chassis.readout(clock.t) : null;
}

/** The Autonomous Drive demo's readout at the clock's time (10 Hz while it runs), or null when no such demo is on. */
export function useSensorsReadout(): ReturnType<NonNullable<Runtime['sensors']>['readout']> | null {
  const sensors = useRuntime()?.sensors;
  const clock = useTechClock();
  return sensors ? sensors.readout(clock.t) : null;
}

/** The Charging tab's readout at the clock's time (10 Hz while it runs), or null when no charge is on. */
export function useChargeReadout(): ChargeReadout | null {
  const charge = useRuntime()?.charge;
  const clock = useTechClock();
  return charge ? charge.readout(clock.t) : null;
}
