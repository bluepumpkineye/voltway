import type { Layout } from './kinematics';
import { simulate, type SceneFactory, type SensorsRun } from './drive';
import { cityScene } from './scenes/city';
import { trafficLightScene } from './scenes/trafficlight';
import { debrisScene } from './scenes/debris';
import { CRUISE, LANE, overtakeScene } from './scenes/overtake';

/**
 * Autonomous Drive (docs/tech-showcase.md section 12): the sensor demo of the Luxeed RX, the Xiaomi SU7 Ultra, the NIO ES8, the
 * Avatr 06T and the XPeng G9L. The car stays on the spot and the road rolls under it; its sensors' coverage is drawn from where
 * each one sits; the other road users move as a scene scripts them, and the car drives itself among them (src/lib/tech/drive.ts is
 * the engine, src/lib/tech/scenes the scenes). Each car plays the scene its entry in the data names (`TechDemoSpec.scenario`):
 *
 *  - `overtake`: an expressway, the car ahead brakes, the car follows, waits for the left lane and overtakes (RX, SU7, ES8)
 *  - `debris`: an expressway, a car cuts in, then something lies in the lane and the car goes round it (06T)
 *  - `city`: a street between parked cars, someone steps out, then a zebra crossing with people on it (G9L)
 *  - `trafficlight`: a street, a signalled zebra crossing: the light turns amber and red, the car stops behind the one ahead, people cross, green (Seal)
 *
 * Published (the makers, Autohome's configuration tables, Huawei, Hesai) is what each car's panel cites: how many of each sensor,
 * the SU7's lidar field of view, and so on. Ours, said on each panel: every scenario (the roads, the traffic, the speeds, the
 * decisions and when they come), every cone's angle and the reach it is drawn to (the real sensors see much further). The other cars
 * are other models' stand-ins in neutral paint. No value imports of anything that needs a browser: it runs under Node.
 */

export { CRUISE, LANE };
export type { Actor as TrafficCar, ActorKind, SensorsReadout, SensorsRun, Track } from './drive';

/** the drawn reach of the sensors (illustrative: the real ones see further), m */
export const REACH = { wide: 26, tele: 62, side: 18, rear: 30, ultrasonic: 2.4, surround: 22, scan: 34 } as const;

export type SceneId = 'overtake' | 'debris' | 'city' | 'trafficlight';

export const SCENES: Record<SceneId, SceneFactory> = { overtake: overtakeScene, debris: debrisScene, city: cityScene, trafficlight: trafficLightScene };

export interface SensorsOptions {
  /** which scene to play (default: the overtake) */
  scene?: SceneId;
  /** the other modelled cars' stand-ins (slug and size): a scene takes its cars from them in turn */
  cars?: { slug: string; length: number; width: number }[];
}

export function planSensors(
  layout: Layout,
  body: { rear: number; front: number; halfWidth: number },
  start: { x: number; y: number; yaw: number },
  opts: SensorsOptions = {},
): SensorsRun {
  const scene = SCENES[opts.scene ?? 'overtake'] ?? overtakeScene;
  return simulate(
    scene,
    { cars: opts.cars ?? [], egoLen: body.front + body.rear, egoWid: body.halfWidth * 2, mid: (body.front - body.rear) / 2, start },
    layout,
  );
}
