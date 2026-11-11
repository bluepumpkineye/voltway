'use client';

import { DriveEngine, prefetchDriveLoops } from './drive-engine';

/**
 * The sound of a run on the Drive tab, and of the Tech tab's launch demo, behind one small controller (Launch.tsx).
 *
 * The motor is made frame by frame from what the car is doing (its speed, its pull, the phase of the run: drive-engine.ts and
 * drive-voice.ts), so nothing depends on how long a run lasts or on where the clock is. It used to lay one 9 s recording of an
 * SU7 against the clock and loop a piece of it with a seek: past 9 s the seek and the clock's drift correction fought each other,
 * and the sound stopped and clicked, on every car and on the 20 s runs especially (and the recording was the SU7's own, timed to
 * its 1.98 s pull, whichever car was driving).
 */
export class LaunchAudioController {
  private engine: DriveEngine | null = null;
  private slug: string | null = null;

  /** Choose the car whose voice it is (a different car makes a new motor). */
  setVehicle(slug: string) {
    if (this.slug === slug && this.engine) return;
    this.stop();
    this.slug = slug;
    if (typeof window === 'undefined') return;
    prefetchDriveLoops();
    const engine = new DriveEngine();
    engine.setVoice(slug);
    this.engine = engine;
  }

  /** The run is playing, at `speed` times real time (slow motion slows the sound with it). */
  play(speed = 1) {
    if (!this.engine) return;
    this.engine.setTimeScale(speed);
    this.engine.start();
  }

  /** The run is paused or over: the motor fades out. */
  pause() {
    this.engine?.stop();
  }

  /** The car, each frame: its speed (km/h), its pull (g) and what the run is doing. */
  frame(speed: number, g: number, phase?: string) {
    this.engine?.update(speed, g, phase);
  }

  setSpeed(speed: number) {
    this.engine?.setTimeScale(speed);
  }

  stop() {
    if (this.engine) {
      this.engine.dispose();
      this.engine = null;
    }
    this.slug = null;
  }

  dispose() {
    this.stop();
  }
}
