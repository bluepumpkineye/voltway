import type { Vehicle } from './schema';

export const xpengP7Plus: Vehicle = {
  slug: 'xpeng-p7-plus',
  brand: 'XPeng',
  model: 'P7+',
  group: 'XPeng',
  bodyStyle: 'Shooting Brake',
  year: 2025,
  tagline: 'Lidar deleted, cameras only, and priced to prove a point.',
  summary:
    'The P7+ is XPeng betting that vision-only autonomy is good enough. A five-metre shooting brake on the same 3 m wheelbase as cars costing twice as much, with 725 km CLTC from a 76.3 kWh LFP pack.',
  dimensions: { lengthMm: 5056, widthMm: 1937, heightMm: 1512, wheelbaseMm: 3000 },
  variants: [
    {
      id: 'std',
      name: '602 Long Range',
      drive: 'RWD',
      battery: { capacityKwh: 60.7, chemistry: 'LFP', cRate: 3 },
      performance: { powerKw: 180, torqueNm: 450, motorCount: 1 },
      range: [{ cycle: 'CLTC', km: 615 }],
    },
    {
      id: 'max',
      name: '725 Ultra Long Range',
      drive: 'RWD',
      battery: { capacityKwh: 76.3, chemistry: 'LFP', cRate: 5 },
      performance: { powerKw: 230, torqueNm: 450, motorCount: 1 },
      range: [{ cycle: 'CLTC', km: 725 }],
    },
  ],
  cockpit: {
    os: 'XOS Tianji',
    skin: 'xos',
    accentColor: '#00D2FF',
    ambientLighting: true,
    screens: [
      { id: 'center', label: 'Centre touchscreen', diagonalIn: 15.6, role: 'center', interactive: true },
      { id: 'cluster', label: 'Instrument cluster', diagonalIn: 10.2, role: 'cluster' },
    ],
  },
  assets: { heroColor: '#B8BDC4', driverEye: [-0.36, 0.40, 1.20] },
  sources: [
    { label: 'CarNewsChina - P7+ battery and range', url: 'https://carnewschina.com/2025/11/09/5-1-meter-xpeng-p7-erev-battery-and-range-info-exposed-ahead-of-launch/' },
    { label: 'EVKX - P7+ 60.7 kWh RWD', url: 'https://evkx.net/models/xpeng/p7plus/p7plus_60.7_kwh_rwd/' },
  ],
};
