/**
 * What the devices of the Tech tab (the phone, the car's screen) ask of a demonstration,
 * whichever tab the visitor is on when they ask.
 */
import type { TechDevice } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { techClock } from './clock';
import { techSession } from './session';

/**
 * Start (or go on with) a demonstration from a device. On the Tech tab with the demo built it just
 * plays; anywhere else (the car's screen in the cabin) the showroom goes out to the stage first and the
 * director plays the demo as soon as it is built.
 */
export function startDemo(demoId: string, device: TechDevice) {
  const st = useVehicleStore.getState();
  if (st.tab === 'tech' && techSession.runtime?.demoId === demoId) {
    techClock.play();
    return;
  }
  st.startTech(demoId, device);
}

/** Stop where the car stands. */
export function pauseDemo() {
  techClock.pause();
}

/** Back to the car at rest, waiting for the device to start it again. */
export function resetDemo() {
  techClock.pause();
  techClock.seek(0);
}
