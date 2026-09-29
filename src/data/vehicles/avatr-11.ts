import type { Vehicle } from './schema';

export const avatr11: Vehicle = {
  slug: 'avatr-11',
  brand: 'Avatr',
  model: '11',
  group: 'Changan x Huawei x CATL',
  bodyStyle: 'Coupe SUV',
  year: 2025,
  tagline: 'Three of China&rsquo;s heavyweights building one car.',
  summary:
    'Changan supplies the platform, CATL the cells, Huawei the cockpit and driver assistance. The result is a 425 kW coupe SUV with a triple-screen HarmonyOS dash and a 116.8 kWh pack good for 680 km CLTC.',
  dimensions: { lengthMm: 4880, widthMm: 1970, heightMm: 1601, wheelbaseMm: 2975 },
  variants: [
    {
      id: 'rwd',
      name: 'Single-Motor RWD',
      drive: 'RWD',
      battery: { capacityKwh: 90.38, chemistry: 'NMC', peakChargeKw: 240 },
      performance: { powerKw: 230, torqueNm: 370, motorCount: 1 },
      range: [{ cycle: 'CLTC', km: 555 }],
    },
    {
      id: 'awd',
      name: 'Dual-Motor AWD',
      drive: 'AWD',
      battery: { capacityKwh: 116.79, chemistry: 'NMC', peakChargeKw: 240 },
      performance: { powerKw: 425, torqueNm: 650, zeroTo100S: 3.98, motorCount: 2 },
      range: [{ cycle: 'CLTC', km: 680 }],
    },
  ],
  cockpit: {
    os: 'HarmonyOS Cockpit',
    skin: 'avatr',
    accentColor: '#7A5CFF',
    ambientLighting: true,
    screens: [
      { id: 'center', label: 'Centre touchscreen', diagonalIn: 15.6, role: 'center', interactive: true },
      { id: 'cluster', label: 'Driver display', diagonalIn: 10.25, role: 'cluster' },
      { id: 'passenger', label: 'Passenger display', diagonalIn: 10.25, role: 'passenger' },
    ],
  },
  assets: { heroColor: '#2B2F36', driverEye: [-0.36, 0.41, 1.28] },
  sources: [
    { label: 'Wikipedia - Avatr 11', url: 'https://en.wikipedia.org/wiki/Avatr_11' },
    { label: 'auto-data - Avatr 11 116 kWh AWD', url: 'https://www.auto-data.net/en/avatr-11-116-kwh-578hp-ultra-long-range-dual-motor-awd-49005' },
  ],
};
