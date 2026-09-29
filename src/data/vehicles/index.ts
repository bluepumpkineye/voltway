export * from './schema';

import type { Vehicle } from './schema';
import { xiaomiSu7Ultra } from './xiaomi-su7-ultra';
import { luxeedRx } from './luxeed-rx';
import { zeekr7x } from './zeekr-7x';
import { xpengP7Plus } from './xpeng-p7-plus';
import { bydSeal } from './byd-seal';
import { avatr11 } from './avatr-11';
import { nioEs7 } from './nio-es7';

/** Ordered as the showcase presents them: the car we have built first. */
export const vehicles: Vehicle[] = [
  xiaomiSu7Ultra,
  luxeedRx,
  zeekr7x,
  xpengP7Plus,
  bydSeal,
  avatr11,
  nioEs7,
];

export const vehiclesBySlug: Record<string, Vehicle> = Object.fromEntries(
  vehicles.map((v) => [v.slug, v]),
);

export function getVehicle(slug: string): Vehicle | undefined {
  return vehiclesBySlug[slug];
}

/** Only cars with a built 3D model can open the interactive viewer. */
export function hasModel(v: Vehicle): boolean {
  return Boolean(v.assets.modelUrl);
}
