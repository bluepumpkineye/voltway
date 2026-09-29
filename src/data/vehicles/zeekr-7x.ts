import type { Vehicle } from './schema';

export const zeekr7x: Vehicle = {
  slug: 'zeekr-7x',
  brand: 'Zeekr',
  model: '7X',
  group: 'Geely',
  bodyStyle: 'SUV',
  year: 2026,
  tagline: '900 volts, 6C charging, ten minutes from 10 to 80 percent.',
  summary:
    'The 7X facelift is where Zeekr put its 900 V architecture to work. Six-C charging refills the 103 kWh pack in about ten minutes, and the dual-motor car reaches 100 km/h in under three seconds.',
  dimensions: { lengthMm: 4825, widthMm: 1930, heightMm: 1656, wheelbaseMm: 2925 },
  variants: [
    {
      id: 'std-rwd',
      name: 'Standard Range RWD',
      drive: 'RWD',
      battery: { capacityKwh: 75, chemistry: 'LFP', architectureV: 800, cRate: 5.5, chargeMinutes10to80: 10.5 },
      performance: { powerKw: 370, zeroTo100S: 5.4, motorCount: 1 },
      range: [{ cycle: 'CLTC', km: 620 }],
    },
    {
      id: 'lr-rwd',
      name: 'Long Range RWD',
      drive: 'RWD',
      battery: { capacityKwh: 103, chemistry: 'NMC', architectureV: 900, cRate: 6, chargeMinutes10to80: 10 },
      performance: { powerKw: 370, zeroTo100S: 5.1, motorCount: 1 },
      range: [{ cycle: 'CLTC', km: 802 }],
    },
    {
      id: 'awd',
      name: 'Performance AWD',
      drive: 'AWD',
      battery: { capacityKwh: 103, chemistry: 'NMC', architectureV: 900, cRate: 6, chargeMinutes10to80: 10 },
      performance: { powerKw: 585, zeroTo100S: 2.98, motorCount: 2 },
      range: [{ cycle: 'CLTC', km: 715 }],
    },
  ],
  cockpit: {
    os: 'ZEEKR OS',
    skin: 'zeekros',
    accentColor: '#00B3A4',
    ambientLighting: true,
    screens: [
      { id: 'center', label: 'Centre touchscreen', diagonalIn: 16, role: 'center', interactive: true },
      { id: 'hud', label: 'AR head-up display', diagonalIn: 13, role: 'hud' },
      { id: 'cluster', label: 'Instrument cluster', diagonalIn: 13, role: 'cluster' },
    ],
  },
  assets: { heroColor: '#0E3A46', driverEye: [-0.36, 0.42, 1.32] },
  sources: [
    { label: 'Paul Tan - 7X facelift, 900 V, 802 km', url: 'https://paultan.org/2025/10/22/zeekr-7x-facelift-revealed-900v-architecture-6c-dc-charging-802-km-cltc-795-ps-0-100-km-h-2-98-secs/' },
    { label: 'Wikipedia - Zeekr 7X', url: 'https://en.wikipedia.org/wiki/Zeekr_7X' },
  ],
};
