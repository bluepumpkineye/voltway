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
  // The maker's own palette (hima.auto/zhijie/rx): six paints, four cabin
  // colours. The build is Blue Morpho with the Red Shadow White cabin, so those
  // two are "as built"; every other value is matched by eye to the maker's
  // press images under our studio rig (hence "approximate" in the interface).
  // The wheels (21-inch double five-spoke is one of several), caliper colours
  // and the frunk are not selectable yet: they need new geometry (Phase 3).
  configurator: {
    paintMaterial: 'M_Paint_RX_ShiftBlue',
    paints: [
      {
        id: 'blue-morpho',
        name: 'Blue Morpho',
        nameZh: '闪蝶蓝',
        swatch: 'linear-gradient(135deg, #3b5cf2 0%, #5a4ff0 48%, #8e55e0 100%)',
      },
      {
        id: 'star-rose',
        name: 'Star Rose',
        nameZh: '星玫粉',
        swatch: '#dfb7aa',
        finish: { color: '#bd887d', roughness: 0.3, metalness: 0.45, clearcoat: 1, clearcoatRoughness: 0.04 },
      },
      {
        id: 'titanium-silver',
        name: 'Titanium Silver',
        nameZh: '钛空银',
        swatch: '#9b9ea3',
        finish: { color: '#7d8085', roughness: 0.32, metalness: 0.55, clearcoat: 1, clearcoatRoughness: 0.04 },
      },
      {
        id: 'aurora-green',
        name: 'Aurora Green',
        nameZh: '极光绿',
        swatch: '#276a68',
        finish: { color: '#17555a', roughness: 0.3, metalness: 0.25, clearcoat: 1, clearcoatRoughness: 0.04 },
      },
      {
        id: 'obsidian-black',
        name: 'Obsidian Black',
        nameZh: '曜石黑',
        swatch: '#1b1c1e',
        finish: { color: '#0c0d0f', roughness: 0.22, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.03 },
      },
      {
        id: 'warm-cloud-white',
        name: 'Warm Cloud White',
        nameZh: '暖云白',
        swatch: '#efede8',
        finish: { color: '#e8e5de', roughness: 0.3, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.04 },
      },
    ],
    // The cabin's seat leather is the white perforated texture, so a colourway
    // tints it; the accent leather and the stitching take the second colour.
    trims: [
      {
        id: 'red-shadow-white',
        name: 'Red Shadow White',
        nameZh: '赤影白',
        swatch: ['#ebe8e4', '#b3262e'],
      },
      {
        id: 'flash-gold-black',
        name: 'Flash Gold Black',
        nameZh: '闪金黑',
        swatch: ['#1a1a1c', '#d4a62a'],
        colors: { INT_Leather_White: '#19191c', INT_Leather_Accent: '#b8891a', INT_Thread_Accent: '#d4a62a' },
      },
      {
        id: 'warm-sand-brown',
        name: 'Warm Sand Brown',
        nameZh: '暖沙棕',
        swatch: ['#dbd1c4', '#5b2326'],
        colors: { INT_Leather_White: '#d9cfc2', INT_Leather_Accent: '#5b2326', INT_Thread_Accent: '#6e2c2f' },
      },
      {
        id: 'red-tea-orange',
        name: 'Red Tea Orange',
        nameZh: '赤茶橘',
        swatch: ['#c8692c', '#2b1b14'],
        colors: { INT_Leather_White: '#c1621f', INT_Leather_Accent: '#2b1b14', INT_Thread_Accent: '#3a2318' },
      },
    ],
    sources: [
      { label: 'HIMA - Luxeed RX: six paints, four interior colours', url: 'https://hima.auto/zhijie/rx/' },
    ],
  },
  // The four doors swing on their leading edge (the hinge: mid height, on the
  // skin; blender/scripts/rx_openings.py). The node origins are the hinges, and
  // the cabin's door cards turn about the same axes. Angles from the opening
  // photographs; the sign is the swing direction (glTF y up).
  openings: [
    { id: 'doorFL', node: 'LuxeedRX_Door_FL', cardNode: 'int_door_L', frameNode: 'LuxeedRX_DoorFrame_FL', deg: -75, xrayHide: true },
    { id: 'doorFR', node: 'LuxeedRX_Door_FR', cardNode: 'int_door_R', frameNode: 'LuxeedRX_DoorFrame_FR', deg: 75, xrayHide: true },
    { id: 'doorRL', node: 'LuxeedRX_Door_RL', cardNode: 'int_rdoor_L', frameNode: 'LuxeedRX_DoorFrame_RL', deg: -68, xrayHide: true },
    { id: 'doorRR', node: 'LuxeedRX_Door_RR', cardNode: 'int_rdoor_R', frameNode: 'LuxeedRX_DoorFrame_RR', deg: 68, xrayHide: true },
    // The bonnet hinges on a lateral axis under its rear edge and rises ~62 deg
    // (photographs 39-41); two gas struts hold it from the cowl corners.
    {
      id: 'frunk',
      node: 'LuxeedRX_Bonnet',
      axis: 'z',
      deg: 62,
      struts: [
        { body: [0.97, 0.93, -0.6], moving: [1.2, 1.0, -0.58] },
        { body: [0.97, 0.93, 0.6], moving: [1.2, 1.0, 0.58] },
      ],
    },
    // The tailgate hangs from the roof's trailing edge (rx_gate.py: the hinge
    // under the spoiler blade) and swings up ~78 deg (photographs 24-26) on two
    // gas struts at its sides. The cabin's liner turns with it; the parcel shelf
    // and the rear sill under the glass are not in the real boot, so they go.
    {
      id: 'boot',
      node: 'LuxeedRX_Tailgate',
      cardNode: 'int_tailgate',
      axis: 'z',
      deg: -78,
      hides: ['int_parcel_shelf', 'int_rear_sill'],
      hidesOutside: ['int_cpillar', 'int_cpillar_flange', 'int_qtr_lower'],
      struts: [
        { body: [-1.97, 1.26, -0.585], moving: [-2.34, 1.1, -0.6] },
        { body: [-1.97, 1.26, 0.585], moving: [-2.34, 1.1, 0.6] },
      ],
    },
  ],
  // The X-ray tab: the roof, A-pillars, rails and every pane of glass above the
  // belt turn to one pale ghost (the LuxeedRX_Greenhouse node, split out in
  // blender/scripts/rx_gate.py), the doors and the dark hull are not drawn, and
  // the cabin shows through with its headliner removed.
  xray: { node: 'LuxeedRX_Greenhouse', color: '#98a4b3', opacity: 0.34, hideCabin: ['int_headliner'] },
  sources: [
    { label: 'CnEVPost - Luxeed opens RX pre-orders', url: 'https://cnevpost.com/2026/08/20/luxeed-opens-pre-orders-rx-suv/' },
    { label: 'CarNewsChina - 586 hp, pre-orders Aug 20', url: 'https://carnewschina.com/2026/08/18/cherys-luxeed-rx-from-ex-ferrari-designer-586-hp-to-start-pre-orders-on-august-20/' },
    { label: 'Wikipedia - Luxeed RX', url: 'https://en.wikipedia.org/wiki/Luxeed_RX' },
  ],
  dataCaveat:
    'Pre-sales opened 20 August 2026. Torque, 0-100 and kerb weight are not yet published, and trim-level range figures may move before deliveries begin.',
};
