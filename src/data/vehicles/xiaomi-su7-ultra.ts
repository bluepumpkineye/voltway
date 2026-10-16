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
        // CnEVPost's launch report (27 Feb 2025): "0 to 200 km/h in 6.09 seconds"
        zeroTo200S: 6.09,
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
    // its shadow on the studio floor: blender/scripts/export_gltf.py bake_ground_shadow(),
    // which prints the size and centre (the build's axes, metres)
    studioShadow: { url: '/models/su7-ultra-shadow.webp', size: [8.071, 5.105], centre: [0.021, 0] },
    // scripts/make-proxy.mjs: the neighbour in another car's parking stage
    proxyUrl: '/models/su7-ultra-proxy.glb',
    heroColor: '#F5C518',
    // over the driver's seat, from the camera-matched cabin build
    driverEye: [-0.30, 0.395, 1.14],
  },
  // Paints: the five Xiaomi lists on xiaomiev.com/ultra. Interiors: Xiaomi's
  // own page only says the Ultra has its own cabin colours and stitching, so the
  // pairings come from Autohome's configuration table for the 2025 Ultra. Black
  // / Yellow and Black / Red are the two it links to photographed cars; Night
  // Black / Glacier Blue and Moon Grey / Black are listed there and nowhere on
  // Xiaomi's page, so treat those two as the least certain. The build is
  // Lightning Yellow with the Black / Yellow cabin ("as built"); every other
  // colour is matched by eye to the maker's imagery under our studio rig.
  configurator: {
    paintMaterial: 'M_Paint_Yellow',
    paints: [
      {
        id: 'lightning-yellow',
        name: 'Lightning Yellow',
        nameZh: '闪电黄',
        swatch: '#e8bd0f',
      },
      {
        id: 'space-silver',
        name: 'Space Silver',
        nameZh: '太空银',
        swatch: '#b7c0cc',
        finish: { color: '#9aa4b0', roughness: 0.3, metalness: 0.55, clearcoat: 1, clearcoatRoughness: 0.035 },
      },
      {
        id: 'parrot-green',
        name: 'Parrot Green',
        nameZh: '鹦鹉绿',
        swatch: '#0b5d70',
        finish: { color: '#064a5c', roughness: 0.28, metalness: 0.25, clearcoat: 1, clearcoatRoughness: 0.035 },
      },
      {
        id: 'obsidian-black',
        name: 'Obsidian Black',
        nameZh: '曜石黑',
        swatch: '#1a1b1d',
        finish: { color: '#0b0b0d', roughness: 0.22, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.03 },
      },
      {
        id: 'pearl-white',
        name: 'Pearl White',
        nameZh: '珍珠白',
        swatch: '#f1f1ee',
        finish: { color: '#ecece8', roughness: 0.3, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.035 },
      },
    ],
    // The cabin is black Alcantara and leather with one accent colour on the
    // seat panels, the stitching and the wheel marker.
    trims: [
      {
        id: 'black-yellow',
        name: 'Black / Yellow',
        nameZh: '黑色/黄色',
        swatch: ['#111113', '#d9a40a'],
      },
      {
        id: 'black-red',
        name: 'Black / Red',
        nameZh: '黑色/红色',
        swatch: ['#111113', '#b02a30'],
        colors: { INT_Leather_Accent: '#9c1f28', INT_Thread_Accent: '#b0222c' },
      },
      {
        id: 'night-glacier',
        name: 'Night Black / Glacier Blue',
        nameZh: '极夜黑/冰河蓝',
        swatch: ['#111113', '#0a6a84'],
        colors: { INT_Leather_Accent: '#0b6b84', INT_Thread_Accent: '#0f86a6' },
      },
      {
        id: 'moon-grey-black',
        name: 'Moon Grey / Black',
        nameZh: '月影灰/黑色',
        swatch: ['#7e7f83', '#111113'],
        colors: {
          INT_Alcantara: '#76787d',
          INT_Leather_Black: '#55575b',
          INT_Leather_Accent: '#111112',
          INT_Thread_Accent: '#2a2a2c',
        },
      },
    ],
    sources: [
      { label: 'Xiaomi - SU7 Ultra: five exterior colours', url: 'https://www.xiaomiev.com/ultra' },
      { label: 'Autohome - SU7 Ultra 2025 configuration table: interior colours', url: 'https://car.autohome.com.cn/config/spec/70545.html' },
    ],
  },
  // The four doors swing on their leading edge (the hinge: mid height, on the
  // skin; blender/scripts/su7_openings.py). The node origins are the hinges, and
  // the cabin's door cards turn about the same axes. Angles from the opening
  // photographs; the sign is the swing direction (glTF y up).
  openings: [
    { id: 'doorFL', node: 'SU7Ultra_Door_FL', cardNode: 'int_door_L', frameNode: 'SU7Ultra_DoorFrame_FL', deg: -75, xrayHide: true },
    { id: 'doorFR', node: 'SU7Ultra_Door_FR', cardNode: 'int_door_R', frameNode: 'SU7Ultra_DoorFrame_FR', deg: 75, xrayHide: true },
    { id: 'doorRL', node: 'SU7Ultra_Door_RL', cardNode: 'int_rdoor_L', frameNode: 'SU7Ultra_DoorFrame_RL', deg: -68, xrayHide: true },
    { id: 'doorRR', node: 'SU7Ultra_Door_RR', cardNode: 'int_rdoor_R', frameNode: 'SU7Ultra_DoorFrame_RR', deg: 68, xrayHide: true },
    // One clamshell bonnet, hinged on a lateral axis at the cowl and held up
    // near the vertical by two gas struts (photographs 33-42; su7_bays.py): its
    // underside is a painted inner panel with a honeycomb of hexagons.
    {
      id: 'frunk',
      node: 'SU7Ultra_Bonnet',
      axis: 'z',
      deg: 78,
      struts: [
        { body: [1.0, 0.78, -0.7], moving: [1.14, 0.9, -0.69] },
        { body: [1.0, 0.78, 0.7], moving: [1.14, 0.9, 0.69] },
      ],
    },
    // The trunk lid (deck, tail cap, wing and the lamps' inner halves) hangs just
    // behind the backlight and stands nearly upright, lifted on two gooseneck
    // arms that are drawn only while it is open (su7_trunk.py; photographs
    // 22-32). The cabin's felt liner turns with it.
    {
      id: 'boot',
      node: 'SU7Ultra_Trunk',
      cardNode: 'int_trunk',
      frameNode: 'SU7Ultra_TrunkArms',
      axis: 'z',
      deg: -82,
    },
  ],
  // The X-ray tab: the roof rail and the panes of glass above the belt turn to
  // one pale ghost (the SU7Ultra_Greenhouse node, split out in
  // blender/scripts/export_gltf.py), the doors and the dark hull are not drawn,
  // and the cabin shows through with its headliner removed.
  xray: { node: 'SU7Ultra_Greenhouse', color: '#98a4b3', opacity: 0.34, hideCabin: ['int_headliner'] },
  // The Tech tab (docs/tech-showcase.md section 10). Sources read 2026-10-12; the board is
  // blender/reference/xiaomi-su7-ultra/tech. No photograph or screen of a launch exists, so the demo starts
  // from the showroom's own controls and says so. The aero kit's active diffuser is not shown: no photograph
  // of it deployed exists, and the owner (2026-10-13) said to leave it out for now.
  tech: [
    {
      id: 'launch',
      title: 'Launch',
      blurb: 'A standing start to 100 km/h in 1.98 s and on to 200 km/h in 6.09 s. Watch the tail squat and the tyres bite.',
      driver: 'launch',
      devices: [],
      claims: [
        {
          text: 'Xiaomi words it “2 seconds to 100”. Its footnote says the 0 to 100 km/h figure excludes rollout and needs Pirelli P Zero Trofeo RS semi-slick tyres.',
          source: { label: 'Xiaomi, SU7 Ultra page', url: 'https://www.xiaomiev.com/ultra' },
        },
        {
          text: 'The launch report gives 1.98 s from 0 to 100 km/h and 6.09 s from 0 to 200 km/h, from three electric motors with 1,138 kW (1,548 PS) combined.',
          source: { label: 'CnEVPost, 27 February 2025', url: 'https://cnevpost.com/2025/02/27/xiaomi-launches-su7-ultra/' },
        },
        {
          text: 'The car rides on a closed twin-chamber air suspension.',
          source: { label: 'Xiaomi, SU7 Ultra page', url: 'https://www.xiaomiev.com/ultra' },
        },
      ],
      simulated:
        'A simulation. Only the two times are published: the pull’s shape between them, the tail’s squat and the tyres’ slip are ours. The 100 km/h time excludes rollout and needs Trofeo RS tyres. The wheels are drawn at three turns a second at most, so their spokes stay readable.',
    },
  ],
  // The DC socket's mouth (the left rear quarter, behind the wheel: our estimate of the place, snapped to the model's skin
  // by a ray) and the direction out of it, in the viewer's axes. The model has no flap, so the Charging tab draws a socket here.
  chargePort: { mouth: [-1.64, 0.95, -0.9107], axis: [-0.0552, 0.4189, -0.9064], depth: 0.02 },
  // The Charging tab (docs/tech-showcase.md section 11). Sources read 2026-10-16.
  charging: {
    window: { from: 10, to: 80, minutes: 11 },
    cRate: 5.2,
    packKwh: 93.7,
    architectureV: 800,
    connector: 'GB/T',
    port: { side: 'left', published: true, where: 'Left rear quarter' },
    claims: [
      {
        text: 'The 93.7 kWh CATL Qilin 2.0 pack supports a maximum charge rate of 5.2C and can complete a fast charge from 10 to 80 % in 11 minutes.',
        source: { label: 'CarNewsChina, 5 December 2024', url: 'https://carnewschina.com/2024/12/05/xiaomi-su7-ultra-will-have-up-to-630-km-range-plus-1-98-seconds-acceleration/' },
      },
      {
        text: 'At 5.2C the pack should peak at around 490 kW; the 11 minutes is what the car should be able to do, not a measured result.',
        source: { label: 'electrive, 6 November 2024', url: 'https://www.electrive.com/2024/11/06/xiaomi-su7-ultra-goes-on-pre-sale/' },
      },
      {
        text: 'The car’s DC charge port is on its left side.',
        source: { label: 'CarNewsChina database, SU7 Ultra parameters', url: 'https://db.carnewschina.com/xiaomi-auto/su7-ultra/2025/params' },
      },
    ],
    simulated:
      'A simulation. The 5.2C and the eleven minutes are published; the peak is that C-rate times the pack, and the curve between is ours. The model has no charge flap, so the socket is drawn at a place on the left rear quarter that we chose, and the pedestal and the gun (styled on a generic charging connector, not Xiaomi’s or any maker’s) are ours. Eleven minutes play in fourteen seconds.',
  },
  sources: [
    { label: 'CnEVPost — Xiaomi launches SU7 Ultra', url: 'https://cnevpost.com/2025/02/27/xiaomi-launches-su7-ultra/' },
    { label: 'CnEVPost — 630 km on 93.7 kWh pack', url: 'https://cnevpost.com/2024/12/05/xiaomi-su7-ultra-range-630-km-93-kwh-battery/' },
    { label: 'CarNewsChina — 1,526 hp, RMB 529,900', url: 'https://carnewschina.com/2025/02/27/xiaomi-su7-ultra-1526-hp-electric-sedan-started-sales-in-china-for-72830-usd/' },
    { label: 'Xiaomi — SU7 Ultra: drive modes, Track Master app, exterior colours', url: 'https://www.xiaomiev.com/ultra' },
    { label: 'Xiaomi — HyperOS smart cabin', url: 'https://www.xiaomiev.com/smartcabin' },
    { label: 'China PEV — mode outputs 816 / 1,346 / 1,548 PS', url: 'https://www.chinapev.com/xiaomi/xiaomi-su7-ultra-officially-launched-starting-at-rmb-529900-ignite-your-driving-passion/' },
    { label: 'CarNewsChina — MIIT filing: 5,070 mm, overhangs, 1,560 mm wing', url: 'https://carnewschina.com/2024/11/08/xiaomi-su7-ultra-declared-by-chinese-miit-powered-by-three-electric-motors/' },
    { label: 'ZOL — SU7 Ultra 2025 spec sheet (5070 × 1970 × 1465)', url: 'https://detail.zol.com.cn/2113/2112093/param.shtml' },
  ],
};
