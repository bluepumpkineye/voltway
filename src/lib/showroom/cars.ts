import { vehicles, hasModel } from '@/data/vehicles';
import type { Vehicle } from '@/data/vehicles/schema';

/** A car opens in the showroom once it has a model and a set of options. */
export function showroomCars(): Vehicle[] {
  return vehicles.filter((v) => hasModel(v) && v.configurator);
}

/** The car the site opens on: the first of the showroom's cars. */
export function defaultCar(): Vehicle {
  return showroomCars()[0];
}

/** What the car menu lists. */
export function carMenu(): { slug: string; label: string }[] {
  return showroomCars().map((v) => ({ slug: v.slug, label: `${v.brand} ${v.model}` }));
}
