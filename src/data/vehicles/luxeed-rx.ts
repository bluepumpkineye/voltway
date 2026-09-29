import type { Vehicle } from './schema';

export const luxeedRx: Vehicle = {
  slug: 'luxeed-rx',
  brand: 'Luxeed',
  model: 'RX',
  group: 'Chery x Huawei (HIMA)',
  bodyStyle: 'Coupe SUV',
  year: 2026,
  tagline: 'A five-screen HarmonyOS cockpit wrapped in ex-Ferrari sheetmetal.',
  summary:
    "Huawei's alliance with Chery aimed the RX squarely at the Xiaomi YU7. Werner Gruber, previously at Ferrari, shaped the body; Huawei supplied the Giant Whale battery platform, four LiDAR units and a Flying Wing cabin with a 3.4 m ambient light strip and a rotating 16.1-inch centre screen.",
  dimensions: { lengthMm: 5020, widthMm: 2007, heightMm: 1585, wheelbaseMm: 3000 },
  variants: [
    {
      id: 'rwd-long',
      name: 'Single-Motor RWD',
      drive: 'RWD',
      battery: { capacityKwh: 100.4, chemistry: 'NMC' },
      performance: { powerKw: 277, motorCount: 1 },
      range: [{ cycle: 'CLTC', km: 852 }],
      priceCny: 229800,
    },
    {
      id: 'awd',
      name: 'Dual-Motor AWD',
      drive: 'AWD',
      battery: { capacityKwh: 100.4, chemistry: 'NMC' },
      performance: { powerKw: 437, motorCount: 2 },
      range: [{ cycle: 'CLTC', km: 700 }],
      priceCny: 359800,
    },
  ],
  cockpit: {
    os: 'HarmonyOS Cockpit',
    skin: 'harmonyos',
    accentColor: '#C8102E',
    ambientLighting: true,
    screens: [
      { id: 'center', label: 'Rotating centre screen', diagonalIn: 16.1, role: 'center', interactive: true },
      { id: 'cluster', label: 'Instrument cluster', diagonalIn: 8.88, role: 'cluster' },
      { id: 'hud', label: 'Head-up display', diagonalIn: 26, role: 'hud' },
      { id: 'passenger', label: 'Passenger display', diagonalIn: 8.88, role: 'passenger' },
      { id: 'mirror-l', label: 'Electronic mirror (left)', diagonalIn: 6, role: 'mirror' },
      { id: 'mirror-r', label: 'Electronic mirror (right)', diagonalIn: 6, role: 'mirror' },
    ],
  },
  assets: {
    // blender/scripts/export_rx.py web_full(): the exterior, and the cabin
    // (rx_interior.py, the white and red trim) with its Cycles light baked in
    modelUrl: '/models/luxeed-rx.glb',
    interiorModelUrl: '/models/luxeed-rx-interior.glb',
    interiorProbeUrl: '/models/luxeed-rx-cabin.hdr',
    // Beijing: the paved square at Zhengyang Gate (Qianmen) on a clear spring
    // morning - Poly Haven "Zhengyang Gate" (Greg Zaal, CC0), turned as in
    // export_rx.OUTSIDE. Inside, the sun is behind-left and the gate tower
    // off the driver's side; outside, the world turns 182 deg so the default
    // camera has the sun at its back and the Great Hall of the People behind
    // the car (the gate tower, to its right-rear, is backlit: turned into the
    // default shot at 124 deg only its shaded wall showed). The sun is
    // carkit.bake.sun_from_hdri(clamp 8, rotation 189, turn 182): 37.8 deg up,
    // #fffbd2, 4.31 above the clamp.
    outside: {
      view: '/models/luxeed-rx-outside.jpg',
      light: '/models/luxeed-rx-outside-light.hdr',
      exteriorTurnDeg: 182.0,
      sun: { direction: [0.5785, 0.6134, 0.5376], color: '#fffbd2', intensity: 4.31 },
      ground: { height: 1.7, radius: 45 },
    },
    heroColor: '#1B4D8F',
    // over the driver's seat, from the camera-matched cabin build
    driverEye: [-0.32, 0.41, 1.19],
  },
  sources: [
    { label: 'CnEVPost - Luxeed opens RX pre-orders', url: 'https://cnevpost.com/2026/08/20/luxeed-opens-pre-orders-rx-suv/' },
    { label: 'CarNewsChina - 586 hp, pre-orders Aug 20', url: 'https://carnewschina.com/2026/08/18/cherys-luxeed-rx-from-ex-ferrari-designer-586-hp-to-start-pre-orders-on-august-20/' },
    { label: 'Wikipedia - Luxeed RX', url: 'https://en.wikipedia.org/wiki/Luxeed_RX' },
  ],
  dataCaveat:
    'Pre-sales opened 20 August 2026. Torque, 0-100 and kerb weight are not yet published, and trim-level range figures may move before deliveries begin.',
};
