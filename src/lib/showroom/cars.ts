import { vehicles, hasModel } from '@/data/vehicles';
import type { Vehicle } from '@/data/vehicles/schema';

/** A car opens in the showroom once it has a model and a set of options. */
export function showroomCars(): Vehicle[] {
  return vehicles.filter((v) => hasModel(v) && v.configurator);
}

/** What the car menu lists. */
export function carMenu(): { slug: string; label: string }[] {
  return showroomCars().map((v) => ({ slug: v.slug, label: `${v.brand} ${v.model}` }));
}
