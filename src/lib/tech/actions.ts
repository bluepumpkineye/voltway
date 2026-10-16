/**
 * What the devices of the Tech tab (the phone, the car's screen) ask of a demonstration,
 * whichever tab the visitor is on when they ask.
 */
import type { TechDevice } from '@/data/vehicles/schema';
import { isStageTab, useVehicleStore } from '@/store/vehicle-store';
import { techClock } from './clock';
import { techSession } from './session';

/**
 * Start (or go on with) a demonstration from a device. On the Tech tab with the demo built it just
 * plays; anywhere else (the car's screen in the cabin) the showroom goes out to the stage first and the
 * director plays the demo as soon as it is built.
 */
export function startDemo(demoId: string, device: TechDevice) {
  const st = useVehicleStore.getState();
  if (isStageTab(st.tab) && techSession.runtime?.demoId === demoId) {
    techClock.play();
    return;
  }
  st.startTech(demoId, device);
}

/**
 * A tap on the car's own "charge port cover" (the Vehicle charging page's tile, the Home chip). On the Charging tab
 * it is what starts the charge and, at its stop, what sends the gun home; anywhere else it opens or shuts the
 * flap. Returns nothing: the screens read the demo's clock.
 */
export function tapChargeFlap() {
  const st = useVehicleStore.getState();
  if (isStageTab(st.tab) && techSession.runtime?.charge) {
    if (!techClock.playing) techClock.play();
    return;
  }
  st.toggleOpening('charge');
}

/**
 * A press of the RX's BOOST knob (on the wheel in the cabin, or the demo's own button): the run starts, from the top if it
 * has finished; a press during the run pauses it.
 */
export function pressBoost() {
  if (techClock.playing) {
    techClock.pause();
    return;
  }
  if (techClock.duration > 0 && techClock.t >= techClock.duration - 0.02) techClock.seek(0);
  techClock.play();
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
