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
    // the car's screen is the light one in every photograph; dark is a showroom extra
    defaultTheme: 'light',
    accentColor: '#00B3A4',
    ambientLighting: true,
    screens: [
      { id: 'center', label: 'Centre touchscreen', diagonalIn: 16, role: 'center', interactive: true },
      { id: 'hud', label: 'AR head-up display', diagonalIn: 13, role: 'hud' },
      { id: 'cluster', label: 'Instrument cluster', diagonalIn: 13, role: 'cluster' },
    ],
  },
  assets: {
    // blender/scripts/export_zx.py web(): the exterior (the Ultra on 21 in wheels). The cabin
    // follows; until then the model is for the showroom only
    modelUrl: '/models/zeekr-7x.glb',
    showroomOnly: true,
    // the cabin (zx_interior*.py, the cream and taupe "purple/white" build) with its Cycles light
    // baked in: export_zx.web_full()
    interiorModelUrl: '/models/zeekr-7x-interior.glb',
    interiorProbeUrl: '/models/zeekr-7x-cabin.hdr',
    // the cream cabin lit by the daylight that comes through the glass reads darker than the
    // studio photographs of it (cream ~210 sRGB there, ~185 here): lifted in the viewer
    cabinGain: 1.3,
    // Poly Haven "Shanghai Riverside" (CC0), turned exactly as the SU7's: inside, the skyline is
    // ahead through the windscreen and the sun behind; outside, the world turns 147.6 deg so the
    // default camera has the golden-hour sun at its back (the sun measured off the HDRI)
    outside: {
      view: '/models/zeekr-7x-outside.jpg',
      light: '/models/zeekr-7x-outside-light.hdr',
      exteriorTurnDeg: 147.6,
      sun: { direction: [0.6959, 0.3477, 0.6284], color: '#ffdfae', intensity: 1.96 },
      ground: { height: 1.7, radius: 45 },
    },
    // its shadow on the studio floor: export_zx.bake_ground_shadow() prints the size and
    // centre (the build's axes, metres)
    studioShadow: { url: '/models/zeekr-7x-shadow.webp', size: [7.846, 5.05], centre: [0, 0] },
    // scripts/make-proxy.mjs: the neighbour in another car's parking stage
    proxyUrl: '/models/zeekr-7x-proxy.glb',
    heroColor: '#49749C',
    // over the driver's seat (the cabin's H-point (0.22, 0.37, 0.585) + 0.64 up, a little back)
    driverEye: [0.16, 0.385, 1.22],
  },
  // The maker's palette (Autohome's colour list for the 2026 car): six paints and four cabin
  // colourways. The build is Gorge Stone Blue (涧石蓝, the car of the studio photographs);
  // every other value is matched by eye to Autohome's swatches under our studio rig (hence
  // "approximate" in the interface). The English names are translations of the Chinese ones.
  // The Ultra's wheels and orange calipers are the only ones photographed; the wheel and
  // caliper choices the maker lists (19 and 20 in) have no photographs, so they are not built.
  configurator: {
    paintMaterial: 'M_Paint_ZX_Blue',
    paints: [
      { id: 'gorge-stone-blue', name: 'Gorge Stone Blue', nameZh: '涧石蓝', swatch: '#49749C' },
      {
        id: 'forest-green',
        name: 'Forest Green',
        nameZh: '森野绿',
        swatch: '#185454',
        finish: { color: '#2a5655', roughness: 0.42, metalness: 0.22, clearcoat: 0.35, clearcoatRoughness: 0.25 },
      },
      {
        id: 'night-purple',
        name: 'Night Purple',
        nameZh: '暗夜紫',
        swatch: '#594569',
        finish: { color: '#5a4a66', roughness: 0.42, metalness: 0.22, clearcoat: 0.35, clearcoatRoughness: 0.25 },
      },
      {
        id: 'glacier-silver',
        name: 'Glacier Silver',
        nameZh: '冰川银',
        swatch: '#C8C8C8',
        finish: { color: '#a3a8ae', roughness: 0.38, metalness: 0.5, clearcoat: 0.4, clearcoatRoughness: 0.2 },
      },
      {
        id: 'polar-night-black',
        name: 'Polar Night Black',
        nameZh: '极夜黑',
        swatch: '#16171a',
        finish: { color: '#141518', roughness: 0.32, metalness: 0.1, clearcoat: 0.8, clearcoatRoughness: 0.1 },
      },
      {
        id: 'polar-day-white',
        name: 'Polar Day White',
        nameZh: '极昼白',
        swatch: '#f3f3f1',
        finish: { color: '#dcdcd8', roughness: 0.36, metalness: 0.08, clearcoat: 0.6, clearcoatRoughness: 0.15 },
      },
    ],
    // The cabin colourways (紫/白, 黑/橙, 黑/灰, 黑/紫 on the maker's list). The build is the
    // cream and taupe cabin of the studio car (Autohome cat 3, 1-58); the others recolour its
    // leather, lower trim, dash top, carpet, headliner and stitching by material name, with
    // values read off the photographs of the orange (361-400), grey (121-154) and orchid
    // (233-280) cars: the leather everywhere it is cream here, black below it. They are
    // approximate: the interface says so.
    trims: [
      { id: 'purple-white', name: 'Purple and White', nameZh: '紫/白', swatch: ['#e9e6e8', '#6a4f7d'] },
      {
        id: 'black-orange',
        name: 'Black and Orange',
        nameZh: '黑/橙',
        swatch: ['#1b1b1d', '#d2661f'],
        colors: {
          INT_Leather_White: '#d06448',
          INT_Leather_Taupe: '#26272a',
          INT_Dash_Top: '#2a2b2e',
          INT_Carpet_Taupe: '#232426',
          INT_Headliner: '#3c3e41',
          INT_Thread_Cream: '#d06448',
        },
      },
      {
        id: 'black-grey',
        name: 'Black and Grey',
        nameZh: '黑/灰',
        swatch: ['#1b1b1d', '#8b8d91'],
        colors: {
          INT_Leather_White: '#87939b',
          INT_Leather_Taupe: '#34373a',
          INT_Dash_Top: '#2a2c2f',
          INT_Carpet_Taupe: '#26282a',
          INT_Headliner: '#34373a',
          INT_Thread_Cream: '#87939b',
        },
      },
      {
        id: 'black-purple',
        name: 'Black and Purple',
        nameZh: '黑/紫',
        swatch: ['#1b1b1d', '#6a4f7d'],
        colors: {
          INT_Leather_White: '#966a8c',
          INT_Leather_Taupe: '#2f3036',
          INT_Dash_Top: '#2a2b30',
          INT_Carpet_Taupe: '#242427',
          INT_Headliner: '#3b3438',
          INT_Thread_Cream: '#966a8c',
        },
      },
    ],
    caliperMaterial: 'M_Caliper_Orange',
    calipers: [{ id: 'orange', name: 'Orange', nameZh: '橙色', color: '#e56f1d' }],
    sources: [
      { label: 'Autohome - Zeekr 7X: colours and interiors', url: 'https://car.autohome.com.cn/pic/series/7777.html' },
    ],
  },
  // The four doors swing on their leading edge (the hinge: mid height, on the skin;
  // blender/scripts/zx_openings.py). The node origins are the hinges, and the cabin's door cards
  // turn about the same axes. Angles from the opening photographs (Autohome c3_0001-3, 18, 20,
  // 36-38); the sign is the swing direction (glTF y up).
  openings: [
    { id: 'doorFL', node: 'Zeekr7X_Door_FL', cardNode: 'int_door_L', frameNode: 'Zeekr7X_DoorFrame_FL', deg: -72, xrayHide: true },
    { id: 'doorFR', node: 'Zeekr7X_Door_FR', cardNode: 'int_door_R', frameNode: 'Zeekr7X_DoorFrame_FR', deg: 72, xrayHide: true },
    { id: 'doorRL', node: 'Zeekr7X_Door_RL', cardNode: 'int_rdoor_L', frameNode: 'Zeekr7X_DoorFrame_RL', deg: -66, xrayHide: true },
    { id: 'doorRR', node: 'Zeekr7X_Door_RR', cardNode: 'int_rdoor_R', frameNode: 'Zeekr7X_DoorFrame_RR', deg: 66, xrayHide: true },
    // The bonnet hinges on a lateral axis under its rear edge at the cowl and rises ~60 deg
    // (c12_0001); two gas struts hold it from the cowl's corners.
    {
      id: 'frunk',
      node: 'Zeekr7X_Bonnet',
      axis: 'z',
      deg: 60,
      struts: [
        { body: [1.25, 1.0, -0.73], moving: [1.52, 1.05, -0.73] },
        { body: [1.25, 1.0, 0.73], moving: [1.52, 1.05, 0.73] },
      ],
    },
    // The tailgate hangs from the roof's trailing edge (zx_gate.py: the hinge at the glass's top
    // edge) and swings up ~80 deg (c3_0047) on two gas struts at its sides. The cabin's liner
    // turns with it.
    {
      id: 'boot',
      node: 'Zeekr7X_Tailgate',
      cardNode: 'int_tailgate',
      axis: 'z',
      deg: -80,
      hidesOutside: ['int_cpillar', 'int_cpillar_flange', 'int_qtr_lower'],
      // the mounts sit inside the quarter panels and the hatch's skin, so a shut car shows no strut
      struts: [
        { body: [-2.05, 1.12, -0.7], moving: [-2.3, 1.0, -0.7] },
        { body: [-2.05, 1.12, 0.7], moving: [-2.3, 1.0, 0.7] },
      ],
    },
  ],
  // The X-ray tab: the roof, A-pillars, rails and every pane of glass above the belt turn to one
  // pale ghost (the Zeekr7X_Greenhouse node, split out in blender/scripts/zx_gate.py), the doors
  // and the dark hull are not drawn, and the cabin shows through with its headliner removed.
  xray: { node: 'Zeekr7X_Greenhouse', color: '#98a4b3', opacity: 0.34, hideCabin: ['int_headliner'] },
  // The lamps (docs/lights.md). The front LED is the usual M_LED_White. The tail lamp is one red lens
  // bar with no LED material under it, so the lens is the lit part, and it is dark as built.
  lights: { rear: { material: 'M_Lamp_RedLens', off: 0 } },
  sources: [
    { label: 'Paul Tan - 7X facelift, 900 V, 802 km', url: 'https://paultan.org/2025/10/22/zeekr-7x-facelift-revealed-900v-architecture-6c-dc-charging-802-km-cltc-795-ps-0-100-km-h-2-98-secs/' },
    { label: 'Wikipedia - Zeekr 7X', url: 'https://en.wikipedia.org/wiki/Zeekr_7X' },
  ],
};
