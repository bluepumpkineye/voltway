import type { Vehicle } from './schema';

export const bydSeal: Vehicle = {
  slug: 'byd-seal',
  brand: 'BYD',
  model: 'Seal',
  group: 'BYD · Ocean',
  bodyStyle: 'Sedan',
  year: 2026,
  tagline: 'High-performance Ocean aesthetic electric sports sedan with e-Platform 3.0 Evo and God’s Eye LiDAR ADAS.',
  summary:
    'BYD’s 4,800 mm electric sports sedan featuring the Ocean X shark nose, double-U LED headlamps, stepped water-ripple light guide blades, and water-drop matrix through-type tail lamp. Built on e-Platform 3.0 Evo with 800V silicon carbide architecture, CTB cell-to-body battery integration, up to 650 km CLTC range, DiLink 100 intelligent cockpit with crystal gear selector, and God’s Eye (天神之眼) high-level smart driving with roof-mounted LiDAR.',
  dimensions: {
    lengthMm: 4800,
    widthMm: 1875,
    heightMm: 1460,
    wheelbaseMm: 2920,
    kerbWeightKg: 2080,
  },
  variants: [
    {
      id: '650-smart-driving',
      name: '650 Smart Driving (650智驾版)',
      drive: 'RWD',
      battery: {
        capacityKwh: 80.64,
        chemistry: 'LFP',
        architectureV: 800,
        cRate: 4.0,
        chargeMinutes10to80: 25,
      },
      performance: {
        powerKw: 230,
        torqueNm: 380,
        zeroTo100S: 5.9,
        motorCount: 1,
        topSpeedKmh: 240,
      },
      range: [{ cycle: 'CLTC', km: 650 }],
      priceCny: 189800,
    },
    {
      id: '600-four-wheel-drive-smart-driving',
      name: '600 AWD Smart Driving (600四驱智驾版)',
      drive: 'AWD',
      battery: {
        capacityKwh: 80.64,
        chemistry: 'LFP',
        architectureV: 800,
        cRate: 4.0,
        chargeMinutes10to80: 25,
      },
      performance: {
        powerKw: 390,
        torqueNm: 690,
        zeroTo100S: 3.8,
        motorCount: 2,
        topSpeedKmh: 240,
      },
      range: [{ cycle: 'CLTC', km: 600 }],
      priceCny: 239800,
    },
    {
      id: '510-smart-driving',
      name: '510 Smart Navigation (510智航版)',
      drive: 'RWD',
      battery: {
        capacityKwh: 61.44,
        chemistry: 'LFP',
        architectureV: 800,
        cRate: 3.5,
        chargeMinutes10to80: 25,
      },
      performance: {
        powerKw: 170,
        torqueNm: 380,
        zeroTo100S: 6.5,
        motorCount: 1,
        topSpeedKmh: 220,
      },
      range: [{ cycle: 'CLTC', km: 510 }],
      priceCny: 175800,
    },
  ],
  cockpit: {
    os: 'DiLink 100',
    skin: 'dilink',
    accentColor: '#1791FF',
    ambientLighting: true,
    defaultTheme: 'dark',
    driveModes: [
      { id: 'comfort', label: 'Comfort', native: '舒适', group: 'street', model: 'comfort' },
      { id: 'eco', label: 'Eco', native: '经济', group: 'street', model: 'eco' },
      { id: 'sport', label: 'Sport', native: '运动', group: 'street', model: 'sport' },
      { id: 'snow', label: 'Snow', native: '雪地', group: 'special', model: 'comfort' },
    ],
    screens: [
      { id: 'center', label: '15.6" 2.5K Floating Rotating Touchscreen', diagonalIn: 15.6, role: 'center', interactive: true },
      { id: 'cluster', label: '10.25" Full LCD Instrument Cluster', diagonalIn: 10.25, role: 'cluster' },
      { id: 'hud', label: '12" W-HUD Head-Up Display', diagonalIn: 12, role: 'hud' },
    ],
  },
  assets: {
    modelUrl: '/models/byd-seal.glb',
    showroomOnly: true,
    studioShadow: {
      url: '/models/byd-seal-shadow.webp',
      size: [7.832, 5.061],
      centre: [0.002, 0.0],
    },
    interiorModelUrl: '/models/byd-seal-interior.glb',
    interiorProbeUrl: '/models/cabin-hall.hdr',
    outside: {
      view: '/models/byd-seal-outside.jpg',
      light: '/models/byd-seal-outside-light.hdr',
      exteriorTurnDeg: 147.6,
      sun: { direction: [0.6959, 0.3477, 0.6284], color: '#ffdfae', intensity: 1.96 },
      ground: { height: 1.7, radius: 45 },
    },
    heroColor: '#66809F',
    driverEye: [0.06, 0.355, 1.12],
    proxyUrl: '/models/byd-seal-proxy.glb',
  },
  configurator: {
    paintMaterial: 'M_Paint_Seal_Blue',
    paints: [
      {
        id: 'arctic-blue',
        name: 'Arctic Blue',
        nameZh: '北冰蓝',
        swatch: '#66809F',
      },
      {
        id: 'mystic-green',
        name: 'Mystic Green',
        nameZh: '迷迭青',
        swatch: '#6E948B',
        finish: { color: '#628980', roughness: 0.28, metalness: 0.20, clearcoat: 0.85, clearcoatRoughness: 0.04 },
      },
      {
        id: 'aurora-white',
        name: 'Aurora White',
        nameZh: '极光白',
        swatch: '#F2F4F7',
        finish: { color: '#EFF1F5', roughness: 0.32, metalness: 0.08, clearcoat: 0.55 },
      },
      {
        id: 'atlantis-grey',
        name: 'Atlantis Grey',
        nameZh: '亚特兰蒂斯灰',
        swatch: '#4E555E',
        finish: { color: '#484F58', roughness: 0.35, metalness: 0.16, clearcoat: 0.48 },
      },
      {
        id: 'xuan-kong-black',
        name: 'Mystic Obsidian Black',
        nameZh: '玄空黑',
        swatch: '#121316',
        finish: { color: '#16171A', roughness: 0.30, metalness: 0.20, clearcoat: 0.60 },
      },
      {
        id: 'sky-purple',
        name: 'Sky Purple',
        nameZh: '天空紫',
        swatch: '#C6BED8',
        finish: { color: '#B6ABCC', roughness: 0.34, metalness: 0.12, clearcoat: 0.50 },
      },
    ],
    trims: [
      {
        id: 'sardine-coral-orange',
        name: 'Sardine Coral Orange',
        nameZh: '沙丁瑚橙',
        swatch: ['#D46A43', '#242629'],
        colors: {
          INT_Leather_Seat: '#C8623A',
          INT_Leather_Door: '#C8623A',
          INT_Leather_Perf: '#C8623A',
          INT_Thread_Seat: '#E27C55',
        },
      },
      {
        id: 'thomas-black',
        name: 'Thomas Black',
        nameZh: '陶玛斯黑',
        swatch: ['#1A1B1E', '#2D3035'],
        colors: {
          INT_Leather_Seat: '#202226',
          INT_Leather_Door: '#202226',
          INT_Leather_Perf: '#202226',
          INT_Thread_Seat: '#3A3D42',
        },
      },
    ],
    // Two wheels, both traced from Autohome photographs of the real car (series 6394): the five-paddle turbine of the
    // rear-drive 550 and 700 km cars, and the five-Y-spoke wheel the 650 km four-wheel-drive Performance (spec 56593)
    // wears with yellow-orange calipers. The turbine's calipers are not visible in any photograph; grey is the build's own.
    caliperMaterial: 'M_Caliper_Seal_Silver',
    calipers: [
      { id: 'silver', name: 'Silver Grey', nameZh: '银灰色', color: '#8a8e93' },
      { id: 'yellow', name: 'Performance Amber', nameZh: '性能橙黄', color: '#e9a410' },
    ],
    wheels: [
      {
        id: 'aero-19',
        name: '19-inch Five-Spoke Turbine Alloy',
        nameZh: '19英寸五辐涡轮铝合金轮毂',
        size: '19 in',
        tyres: '235/45 R19',
        node: 'BYDSeal_Wheels',
        caliper: 'silver',
      },
      {
        id: 'perf-19',
        name: '19-inch Five-Y-Spoke Performance',
        nameZh: '19英寸五辐Y形性能轮毂',
        size: '19 in',
        tyres: '235/45 R19',
        node: 'BYDSeal_Perf_Wheels',
        caliper: 'yellow',
      },
    ],
    sources: [
      { label: 'Autohome — 比亚迪 海豹 EV Specifications & Gallery (Series 6394)', url: 'https://www.autohome.com.cn/6394/' },
      { label: 'BYD Official — 海豹 EV Ocean Network Sports Sedan', url: 'https://www.byd.com/' },
    ],
  },
  openings: [
    { id: 'doorFL', node: 'BYDSeal_Door_FL', cardNode: 'int_door_L', frameNode: 'BYDSeal_DoorFrame_FL', deg: -72 },
    { id: 'doorFR', node: 'BYDSeal_Door_FR', cardNode: 'int_door_R', frameNode: 'BYDSeal_DoorFrame_FR', deg: 72 },
    { id: 'doorRL', node: 'BYDSeal_Door_RL', cardNode: 'int_rdoor_L', frameNode: 'BYDSeal_DoorFrame_RL', deg: -66 },
    { id: 'doorRR', node: 'BYDSeal_Door_RR', cardNode: 'int_rdoor_R', frameNode: 'BYDSeal_DoorFrame_RR', deg: 66 },
    {
      id: 'frunk',
      node: 'BYDSeal_Bonnet',
      axis: 'z',
      deg: 74,
      struts: [
        { body: [1.20, 0.86, -0.62], moving: [1.42, 0.90, -0.62] },
        { body: [1.20, 0.86, 0.62], moving: [1.42, 0.90, 0.62] },
      ],
    },
    {
      id: 'boot',
      node: 'BYDSeal_Tailgate',
      cardNode: 'int_tailgate',
      axis: 'z',
      deg: -80,
      struts: [
        { body: [-1.96, 0.88, -0.55], moving: [-2.20, 0.92, -0.55] },
        { body: [-1.96, 0.88, 0.55], moving: [-2.20, 0.92, 0.55] },
      ],
    },
  ],
  xray: { node: 'BYDSeal_Body', color: '#98a4b3', opacity: 0.34, hideCabin: ['int_headliner'] },
  tech: [
    {
      id: 'ctb-tech',
      title: 'CTB Cell-to-Body Technology',
      blurb:
        'The Blade Battery is structurally integrated into the vehicle body, acting as both the energy source and a structural component, yielding 40,500 Nm/deg torsional stiffness.',
      driver: 'ctb',
      devices: ['dashboard'],
      claims: [
        {
          text: 'BYD CTB (Cell to Body) battery integration makes the battery pack sandwich part of the vehicle platform floor, achieving 40,500 Nm/deg torsional rigidity and 50:50 front-rear axle weight distribution.',
          source: { label: 'BYD Official CTB Technology', url: 'https://www.byd.com/cn/tech/ctb' },
        },
      ],
      simulated:
        'A simulation demonstrating the high torsional rigidity and crash protection provided by CTB cell-to-body sandwich structure.',
    },
    {
      id: 'gods-eye-adas',
      title: 'God’s Eye (天神之眼) LiDAR ADAS',
      blurb:
        'Equipped with watchtower-mounted roof LiDAR, 5 millimeter-wave radars, 12 ultrasonic sensors, and 11 HD cameras for city & highway Navigation on Autopilot (NOA).',
      driver: 'godseye',
      devices: ['dashboard'],
      claims: [
        {
          text: 'The 2025/2026/2027 Seal EV features the God’s Eye (天神之眼) advanced driver assistance system (DiPilot 300) with roof-mounted LiDAR, enabling full-scenario highway and urban navigation assistance.',
          source: { label: 'Autohome — 比亚迪 海豹 EV Configuration', url: 'https://www.autohome.com.cn/6394/' },
        },
      ],
      simulated:
        'A simulation highlighting the sensor suite and multi-layer perception perception envelope around the vehicle.',
    },
    {
      id: 'park',
      title: 'Remote parking assist',
      blurb:
        'Step out and let the car park itself via your smartphone: God’s Eye surround sensors scan the area, identify the vacant bay with a flashing P, and reverse in.',
      driver: 'park',
      devices: ['phone', 'dashboard'],
      params: { search: 12 },
      claims: [
        {
          text: 'BYD DiPilot 300 supports automated valet parking and remote control parking (RPA) through the smartphone application.',
          source: { label: 'Autohome configuration table, BYD Seal', url: 'https://car.autohome.com.cn/config/spec/71666.html' },
        },
      ],
      simulated:
        'A simulation of DiPilot 300 remote parking: surround perception beams screen the lot, the target bay is locked with a glowing P, and the car reverses in smoothly.',
    },
  ],
  sensors: {
    lidar: [0.261, 1.4, 0],
    lidarFov: 120,
    cameras: [
      { at: [0.33, 1.335, 0.03], mirror: true },
      { at: [2.414, 0.505, 0] },
      { at: [0.7, 1.015, 0.965], mirror: true },
      { at: [-2.404, 0.545, 0] },
    ],
    ultrasonic: [
      { at: [2.391, 0.41, 0.335], mirror: true },
      { at: [2.242, 0.56, 0.74], mirror: true },
    ],
    surround: true,
  },
  chargePort: { mouth: [-1.58, 0.88, -0.85], axis: [-0.048, 0.4129, -0.9095], depth: 0.02 },
  charging: {
    window: { from: 10, to: 80, minutes: 25 },
    packKwh: 80.64,
    architectureV: 800,
    connector: 'GB/T',
    port: { side: 'left', published: true, where: 'Left rear quarter' },
    claims: [
      {
        text: 'Equipped with e-Platform 3.0 Evo full-domain 800V silicon carbide high-voltage platform, supporting high-power boost charging from 10% to 80% SoC in 25 minutes.',
        source: { label: 'Autohome — 比亚迪 海豹 EV Specifications', url: 'https://www.autohome.com.cn/6394/' },
      },
    ],
    simulated:
      'A simulation of 800V high-voltage boost fast charging. 25 minutes play in fourteen seconds.',
  },
  sources: [
    { label: 'Autohome — 比亚迪 海豹 EV Specifications & Gallery (Series 6394)', url: 'https://www.autohome.com.cn/6394/' },
    { label: 'BYD Official — 海豹 EV Ocean Network Sports Sedan', url: 'https://www.byd.com/' },
  ],
};
