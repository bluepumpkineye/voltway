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
import type { Sample } from './kinematics';
import type { BodyBox, ParkStage } from './park';

export interface Runtime {
  demoId: string;
  /** the floor the demo is staged on, when it has one */
  stage: ParkStage | null;
  /** the middle of the rear axle at time t (floor frame, kinematics axes) */
  sample: (t: number) => Sample;
  /** the car's body from the rear axle, the published width */
  body: BodyBox;
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
