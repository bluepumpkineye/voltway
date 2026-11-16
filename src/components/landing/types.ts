import type { Vehicle } from '@/data/vehicles/schema';

export interface LandingCar {
  slug: string;
  brand: string;
  model: string;
  group: string;
  bodyStyle: Vehicle['bodyStyle'];
  year: number;
  tagline: string;
  imageW: number;
  imageH: number;
  zeroTo100S: number | null;
  powerKw: number;
  minPriceCny: number | null;
  maxCltcKm: number | null;
}
