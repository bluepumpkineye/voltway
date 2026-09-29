import type { Vehicle } from './schema';

export const nioEs7: Vehicle = {
  slug: 'nio-es7',
  brand: 'Nio',
  model: 'ES7',
  group: 'Nio',
  bodyStyle: 'SUV',
  year: 2025,
  tagline: 'Swap the pack in three minutes instead of charging it.',
  summary:
    'Sold as the EL7 in Europe, the ES7 is the clearest argument for battery swapping: three pack sizes, all interchangeable at a Nio Power Swap station in about three minutes. 480 kW and 850 Nm come as standard.',
  dimensions: { lengthMm: 4912, widthMm: 1987, heightMm: 1720, wheelbaseMm: 2960 },
  variants: [
    {
      id: 'std',
      name: 'Standard Range',
      drive: 'AWD',
      battery: { capacityKwh: 75, chemistry: 'NMC', swappable: true },
      performance: { powerKw: 480, torqueNm: 850, zeroTo100S: 3.9, topSpeedKmh: 200, motorCount: 2 },
      range: [{ cycle: 'CLTC', km: 485 }],
    },
    {
      id: 'lr',
      name: 'Long Range',
      drive: 'AWD',
      battery: { capacityKwh: 100, chemistry: 'NMC', swappable: true },
      performance: { powerKw: 480, torqueNm: 850, zeroTo100S: 3.9, topSpeedKmh: 200, motorCount: 2 },
      range: [{ cycle: 'CLTC', km: 620 }],
    },
  ],
  cockpit: {
    os: 'Banyan',
    skin: 'banyan',
    accentColor: '#00C2A8',
    ambientLighting: true,
    screens: [
      { id: 'center', label: 'AMOLED centre screen', diagonalIn: 12.8, role: 'center', interactive: true },
      { id: 'cluster', label: 'Instrument cluster', diagonalIn: 9.8, role: 'cluster' },
    ],
  },
  assets: { heroColor: '#3E4A57', driverEye: [-0.36, 0.42, 1.36] },
  sources: [
    { label: 'CarNewsChina - ES7 specs, 100 kWh, 620 km', url: 'https://carnewschina.com/2022/06/03/nio-es7-specs-unveiled-with-100-kwh-battery-and-620-km-range/' },
    { label: 'Wikipedia - Nio ES7', url: 'https://en.wikipedia.org/wiki/Nio_ES7' },
  ],
};
