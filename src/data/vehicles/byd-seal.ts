import type { Vehicle } from './schema';

export const bydSeal: Vehicle = {
  slug: 'byd-seal',
  brand: 'BYD',
  model: 'Seal',
  group: 'BYD',
  bodyStyle: 'Sedan',
  year: 2025,
  tagline: 'The Blade pack as structure, not just cargo.',
  summary:
    "BYD's cell-to-body Seal makes the LFP Blade pack part of the shell itself. The AWD car hits 100 km/h in 3.8 s, and because BYD builds its own cells it undercuts nearly everything at the price.",
  dimensions: { lengthMm: 4800, widthMm: 1875, heightMm: 1460, wheelbaseMm: 2920 },
  variants: [
    {
      id: 'rwd',
      name: 'Design RWD',
      drive: 'RWD',
      battery: { capacityKwh: 82.5, chemistry: 'LFP', peakChargeKw: 150 },
      performance: { powerKw: 230, torqueNm: 360, zeroTo100S: 5.9, motorCount: 1 },
      range: [{ cycle: 'WLTP', km: 570 }],
    },
    {
      id: 'awd',
      name: 'Excellence AWD',
      drive: 'AWD',
      battery: { capacityKwh: 82.5, chemistry: 'LFP', peakChargeKw: 150 },
      performance: { powerKw: 390, torqueNm: 670, zeroTo100S: 3.8, motorCount: 2 },
      range: [{ cycle: 'WLTP', km: 520 }],
    },
  ],
  cockpit: {
    os: 'DiLink',
    skin: 'dilink',
    accentColor: '#0057B8',
    ambientLighting: true,
    screens: [
      { id: 'center', label: 'Rotating centre screen', diagonalIn: 15.6, role: 'center', interactive: true },
      { id: 'cluster', label: 'Instrument cluster', diagonalIn: 10.25, role: 'cluster' },
    ],
  },
  assets: { heroColor: '#1E5AA8', driverEye: [-0.35, 0.40, 1.16] },
  sources: [
    { label: 'EV Database - BYD Seal', url: 'https://ev-database.org/car/3102/BYD-SEAL-614-kWh-RWD-Comfort' },
    { label: 'EVSpecifications - Seal Excellence AWD', url: 'https://www.evspecifications.com/en/model/5eac3aa' },
  ],
};
