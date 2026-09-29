import type { Vehicle } from './schema';

export const xiaomiSu7Ultra: Vehicle = {
  slug: 'xiaomi-su7-ultra',
  brand: 'Xiaomi',
  model: 'SU7 Ultra',
  group: 'Xiaomi EV',
  bodyStyle: 'Sedan',
  year: 2025,
  tagline: 'A Nürburgring weapon that costs less than a loaded Panamera.',
  summary:
    'Xiaomi took its first car and turned the wick up to 1,138 kW. Three motors, a carbon aero kit and a 1.98 s launch put it in hypercar company, yet it launched at RMB 529,900 — roughly a third of the pre-sale price Xiaomi first floated.',
  dimensions: {
    // production car; the 5,115 mm figure is the MIIT filing's alternative
    // with the longer rear overhang (1,108 vs 1,063 mm)
    lengthMm: 5070,
    widthMm: 1970,
    heightMm: 1465,
    wheelbaseMm: 3000,
    kerbWeightKg: 2360,
  },
  variants: [
    {
      id: 'tri-motor',
      name: 'Tri-Motor AWD',
      drive: 'AWD',
      battery: {
        capacityKwh: 93.7,
        chemistry: 'NMC',
        architectureV: 800,
      },
      performance: {
        powerKw: 1138,
        torqueNm: 1770,
        zeroTo100S: 1.98,
        topSpeedKmh: 350,
        motorCount: 3,
      },
      range: [{ cycle: 'CLTC', km: 630 }],
      priceCny: 529900,
    },
  ],
  cockpit: {
    os: 'Xiaomi HyperOS',
    skin: 'hyperos',
    accentColor: '#FF6A00',
    ambientLighting: true,
    screens: [
      { id: 'center', label: 'Central touchscreen', diagonalIn: 16.1, role: 'center', interactive: true },
      { id: 'cluster', label: 'Instrument cluster', diagonalIn: 7.1, role: 'cluster' },
      { id: 'hud', label: 'Head-up display', diagonalIn: 56, role: 'hud' },
    ],
    // Xiaomi: 5 street, 3 track and 2 special modes. Street and special as on
    // the car's Driving preferences screen (xiaomiev.com/ultra); track outputs
    // as launched: Endurance 816 PS, Qualifying 1,346 PS, 1,548 PS with Boost
    // or in Drag race.
    driveModes: [
      { id: 'eco', label: 'Eco', native: '经济', group: 'street', model: 'eco' },
      { id: 'standard', label: 'Standard', native: '标准', group: 'street', model: 'comfort' },
      { id: 'sport', label: 'Sport', native: '运动', group: 'street', model: 'sport' },
      { id: 'slippery', label: 'Slippery', native: '湿滑', slot: 'M1', group: 'street', model: 'eco' },
      { id: 'novice', label: 'Novice', native: '新手', slot: 'M2', group: 'street', model: 'eco' },
      { id: 'endurance', label: 'Endurance', native: '耐力赛', group: 'track', model: 'track', powerKw: 600, powerPs: 816 },
      { id: 'qualifying', label: 'Qualifying', native: '排位赛', group: 'track', model: 'track', powerKw: 990, powerPs: 1346 },
      { id: 'drift', label: 'Drift', native: '漂移', group: 'track', model: 'sport' },
      { id: 'drag', label: 'Drag race', native: '直线竞速', group: 'special', model: 'track', powerKw: 1138, powerPs: 1548 },
      { id: 'saver', label: 'Super power saving', native: '超级省电', group: 'special', model: 'eco' },
    ],
  },
  assets: {
    modelUrl: '/models/su7-ultra.glb',
    interiorModelUrl: '/models/su7-ultra-interior.glb',
    interiorProbeUrl: '/models/su7-ultra-cabin.hdr',
    // Poly Haven "Shanghai Riverside" (CC0). Inside, the skyline is ahead
    // through the windscreen and the sun behind; outside, the world turns
    // 147.6 deg so the default camera has the golden-hour sun at its back and
    // the skyline behind the car. The sun is measured off the HDRI: 20.4 deg
    // up, #ffdfae, irradiance 1.51 in the HDR's units (the sky gives 1.8).
    outside: {
      view: '/models/su7-ultra-outside.jpg',
      light: '/models/su7-ultra-outside-light.hdr',
      exteriorTurnDeg: 147.6,
      sun: { direction: [0.6959, 0.3477, 0.6284], color: '#ffdfae', intensity: 1.96 },
      ground: { height: 1.7, radius: 45 },
    },
    heroColor: '#F5C518',
    // over the driver's seat, from the camera-matched cabin build
    driverEye: [-0.30, 0.395, 1.14],
  },
  sources: [
    { label: 'CnEVPost — Xiaomi launches SU7 Ultra', url: 'https://cnevpost.com/2025/02/27/xiaomi-launches-su7-ultra/' },
    { label: 'CnEVPost — 630 km on 93.7 kWh pack', url: 'https://cnevpost.com/2024/12/05/xiaomi-su7-ultra-range-630-km-93-kwh-battery/' },
    { label: 'CarNewsChina — 1,526 hp, RMB 529,900', url: 'https://carnewschina.com/2025/02/27/xiaomi-su7-ultra-1526-hp-electric-sedan-started-sales-in-china-for-72830-usd/' },
    { label: 'Xiaomi — SU7 Ultra: drive modes, Track Master app', url: 'https://www.xiaomiev.com/ultra' },
    { label: 'Xiaomi — HyperOS smart cabin', url: 'https://www.xiaomiev.com/smartcabin' },
    { label: 'China PEV — mode outputs 816 / 1,346 / 1,548 PS', url: 'https://www.chinapev.com/xiaomi/xiaomi-su7-ultra-officially-launched-starting-at-rmb-529900-ignite-your-driving-passion/' },
    { label: 'CarNewsChina — MIIT filing: 5,070 mm, overhangs, 1,560 mm wing', url: 'https://carnewschina.com/2024/11/08/xiaomi-su7-ultra-declared-by-chinese-miit-powered-by-three-electric-motors/' },
    { label: 'ZOL — SU7 Ultra 2025 spec sheet (5070 × 1970 × 1465)', url: 'https://detail.zol.com.cn/2113/2112093/param.shtml' },
  ],
};
