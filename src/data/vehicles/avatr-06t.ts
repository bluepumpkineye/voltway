import type { Vehicle } from './schema';

export const avatr06t: Vehicle = {
  slug: 'avatr-06t',
  brand: 'Avatr',
  model: '06T',
  group: 'Changan · CATL · Huawei',
  bodyStyle: 'Shooting Brake',
  year: 2025,
  tagline: 'Pure futuristic shooting-brake design with Huawei Qiankun ADS 3.0 & HarmonyOS Cockpit.',
  summary:
    'Avatr’s 4,940 mm luxury shooting brake combining iconic F-type split flying wing DRLs, star-ring rear light bars, 35.4" 4K Panoramic Star Ring Display, dual electronic exterior mirrors, Kunpeng EREV & 800V SiC EV architectures, and CATL Shenxing 5C supercharging.',
  dimensions: {
    lengthMm: 4940,
    widthMm: 1960,
    heightMm: 1455,
    wheelbaseMm: 2940,
    kerbWeightKg: 2260,
  },
  variants: [
    {
      id: '650-ultra-ev-awd',
      name: '650 Ultra Pure EV AWD Flagship',
      drive: 'AWD',
      battery: {
        capacityKwh: 82.16,
        chemistry: 'NMC',
        architectureV: 800,
        cRate: 5.0,
        chargeMinutes10to80: 15,
      },
      performance: {
        powerKw: 440,
        torqueNm: 645,
        zeroTo100S: 3.9,
        motorCount: 2,
        topSpeedKmh: 210,
      },
      range: [{ cycle: 'CLTC', km: 650 }],
      priceCny: 279900,
    },
    {
      id: '650-max-ev-rwd',
      name: '650 Max Pure EV RWD',
      drive: 'RWD',
      battery: {
        capacityKwh: 82.16,
        chemistry: 'NMC',
        architectureV: 800,
        cRate: 5.0,
        chargeMinutes10to80: 15,
      },
      performance: {
        powerKw: 250,
        torqueNm: 370,
        zeroTo100S: 6.0,
        motorCount: 1,
        topSpeedKmh: 200,
      },
      range: [{ cycle: 'CLTC', km: 650 }],
      priceCny: 239900,
    },
    {
      id: '1180-ultra-erev-awd',
      name: '1180 Ultra Kunpeng EREV AWD',
      drive: 'AWD',
      battery: {
        capacityKwh: 39.05,
        chemistry: 'LFP',
        architectureV: 800,
        cRate: 3.5,
        chargeMinutes10to80: 15,
      },
      performance: {
        powerKw: 314,
        torqueNm: 560,
        zeroTo100S: 4.9,
        motorCount: 2,
        topSpeedKmh: 190,
      },
      range: [{ cycle: 'CLTC', km: 1180 }],
      priceCny: 259900,
    },
  ],
  cockpit: {
    os: 'HarmonyOS 4 Cockpit',
    skin: 'avatr',
    accentColor: '#7A5CFF',
    ambientLighting: true,
    ambientHue: 275,
    defaultTheme: 'dark',
    driveModes: [
      { id: 'comfort', label: 'Comfort', native: '舒适', group: 'street', model: 'comfort' },
      { id: 'eco', label: 'Eco', native: '经济', group: 'street', model: 'eco' },
      { id: 'sport', label: 'Sport', native: '运动', group: 'street', model: 'sport' },
      { id: 'gt', label: 'Shooting Brake GT', native: '猎装GT', group: 'special', model: 'sport' },
      { id: 'snow', label: 'Snow / Slippery', native: '雪地', group: 'special', model: 'comfort' },
    ],
    screens: [
      { id: 'center', label: '15.6" 2.5K Floating Centre Touchscreen', diagonalIn: 15.6, role: 'center', interactive: true },
      { id: 'cluster', label: '35.4" 4K Panoramic Star Ring Display', diagonalIn: 35.4, role: 'cluster' },
      { id: 'mirror-l', label: '6.7" HD Left Electronic Rearview Mirror Display', diagonalIn: 6.7, role: 'mirror' },
      { id: 'mirror-r', label: '6.7" HD Right Electronic Rearview Mirror Display', diagonalIn: 6.7, role: 'mirror' },
    ],
  },
  assets: {
    modelUrl: '/models/avatr-06t.glb',
    showroomOnly: true,
    studioShadow: {
      url: '/models/avatr-06t-shadow.webp',
      size: [7.96, 5.08],
      centre: [0.0, 0.0],
    },
    interiorModelUrl: '/models/avatr-06t-interior.glb',
    // lit by the shared showroom hall, shaded by the cabin's occlusion atlas (docs/3d-pipeline.md, "The hall look")
    interiorProbeUrl: '/models/cabin-hall.hdr',
    outside: {
      view: '/models/avatr-06t-outside.jpg',
      light: '/models/avatr-06t-outside-light.hdr',
      exteriorTurnDeg: 189,
      sun: { direction: [0.65, 0.45, 0.61], color: '#fff5e6', intensity: 2.8 },
      ground: { height: -0.369, radius: 24.0 },
    },
    // 85 mm forward with the front seats (a06t_interior.FRONT_BIGHT_X): at the old x the eye stood inside the headrest
    driverEye: [-0.275, 0.41, 1.15],
    proxyUrl: '/models/avatr-06t-proxy.glb',
    heroColor: '#524660',
  },
  configurator: {
    paintMaterial: 'M_Paint_A06T_MistyPurple',
    paints: [
      {
        id: 'misty-purple',
        name: 'Misty Purple',
        nameZh: '云紫',
        swatch: '#524660',
        finish: { color: '#3c324b', roughness: 0.28, metalness: 0.55, clearcoat: 1, clearcoatRoughness: 0.03 },
      },
      {
        id: 'solar-bronze',
        name: 'Solar Bronze',
        nameZh: '鎏棕',
        swatch: '#7a6352',
        finish: { color: '#685140', roughness: 0.28, metalness: 0.65, clearcoat: 1, clearcoatRoughness: 0.03 },
      },
      {
        id: 'skylight-silk',
        name: 'Skylight Silk',
        nameZh: '晴蓝',
        swatch: '#829db0',
        finish: { color: '#647f93', roughness: 0.26, metalness: 0.45, clearcoat: 1, clearcoatRoughness: 0.03 },
      },
      {
        id: 'obsidian-black',
        name: 'Obsidian Black',
        nameZh: '曜黑',
        swatch: '#18191c',
        finish: { color: '#0d0d0f', roughness: 0.20, metalness: 0.1, clearcoat: 1, clearcoatRoughness: 0.03 },
      },
      {
        id: 'snow-white',
        name: 'Snow White',
        nameZh: '皓白',
        swatch: '#f0f2f5',
        finish: { color: '#e5e8ed', roughness: 0.28, metalness: 0.2, clearcoat: 1, clearcoatRoughness: 0.03 },
      },
    ],
    trims: [
      {
        id: 'misty-purple-cotton-white',
        name: 'Misty Purple & Cotton White',
        nameZh: '暮紫/烟白',
        swatch: ['#3e344e', '#dedad5'],
      },
      {
        id: 'deep-charcoal-slate',
        name: 'Deep Charcoal Slate',
        nameZh: '暮灰',
        swatch: ['#222327', '#4b4e54'],
        colors: { INT_Leather_White: '#4b4e54', INT_Leather_Purple: '#222327' },
      },
    ],
    caliperMaterial: 'M_Caliper_Silver_Grey',
    calipers: [
      { id: 'silver_grey', name: 'Silver Grey', nameZh: '银灰色', color: '#8e9297' },
      { id: 'yellow', name: 'Performance Yellow', nameZh: '性能黄', color: '#e8be14' },
      { id: 'red', name: 'Competition Red', nameZh: '竞技红', color: '#c42628' },
    ],
    wheels: [
      // The maker offers two wheels, both 20 in (Autohome's photographs of every trim show only these): the standard
      // Cyclone five-spoke on all trims, and the forged Star Spin five-spoke of the Knight edition (猎装骑士版). The 21 in
      // "Cyclone", the Aero Blade and the Radiant multi-spoke of the first build were never photographed on a real 06T.
      {
        id: 'turbine5',
        name: '20" Cyclone Five-Spoke',
        nameZh: '20英寸气旋五辐轮毂',
        size: '20"',
        tyres: '255/45 R20 front · 265/45 R20 rear',
        node: 'Avatr06T_Wheels',
        caliper: 'silver_grey',
      },
      {
        id: 'star5',
        name: '20" Star Spin Forged Five-Spoke',
        nameZh: '20英寸星旋五辐锻造轮毂',
        size: '20"',
        tyres: '255/45 R20 front · 265/45 R20 rear',
        node: 'Avatr06T_Star_Wheels',
        caliper: 'silver_grey',
      },
    ],
    sources: [
      { label: 'Avatr Official Website - Avatr 06T', url: 'https://www.avatr.com/en/06T' },
      { label: 'Autohome - Avatr 06T Specification and Configuration', url: 'https://www.autohome.com.cn/' },
    ],
  },
  openings: [
    { id: 'doorFL', node: 'Avatr06T_Door_FL', cardNode: 'int_door_L', frameNode: 'Avatr06T_DoorFrame_FL', deg: -75, xrayHide: true },
    { id: 'doorFR', node: 'Avatr06T_Door_FR', cardNode: 'int_door_R', frameNode: 'Avatr06T_DoorFrame_FR', deg: 75, xrayHide: true },
    { id: 'doorRL', node: 'Avatr06T_Door_RL', cardNode: 'int_rdoor_L', frameNode: 'Avatr06T_DoorFrame_RL', deg: -68, xrayHide: true },
    { id: 'doorRR', node: 'Avatr06T_Door_RR', cardNode: 'int_rdoor_R', frameNode: 'Avatr06T_DoorFrame_RR', deg: 68, xrayHide: true },
    {
      id: 'frunk',
      node: 'Avatr06T_Bonnet',
      axis: 'z',
      deg: 62,
    },
    {
      id: 'boot',
      node: 'Avatr06T_Tailgate',
      cardNode: 'int_tailgate',
      axis: 'z',
      deg: -78,
      hides: ['int_parcel_shelf', 'int_rear_sill'],
    },
  ],
  xray: { node: 'Avatr06T_Greenhouse', color: '#98a4b3', opacity: 0.34, hideCabin: ['int_headliner'] },
  // The clear panes keep the X-ray's ghost (the front glass of c1_0001..c1_0003 shows the cabin plainly). The privacy glass
  // (rear windows, backlight, glass roof) was drawn 55 % opaque: the cargo trim, the shelf and the headliner's lamps showed
  // through the backlight and the roof as grey shapes the owner read as bumps and body mixed into the glass (2026-10-28). The
  // photographed pane is dark with only the headrests' silhouettes in it (c1_0005, c1_0007), and it mirrors a dark ceiling.
  glass: { color: '#98a4b3', opacity: 0.34, privacy: 0.84, privacyReflect: 0.55 },
  lights: { projector: {} },
  sensors: {
    lidar: [0.18, 1.45, 0],
    sideLidar: [0.72, 0.65, 0.95],
    rearLidar: [-2.42, 0.96, 0],
    cameras: [
      { at: [2.45, 0.58, 0] },
      { at: [0.72, 0.65, 0.95], mirror: true },
      { at: [0.65, 0.98, 1.05], mirror: true },
      { at: [-2.42, 1.39, 0] },
      { at: [-2.46, 0.96, 0] },
    ],
    ultrasonic: [
      { at: [2.35, 0.45, 0.72], mirror: true },
      { at: [-2.38, 0.46, 0.72], mirror: true },
    ],
    surround: true,
  },
  chargePort: { mouth: [-1.92, 1.05, -0.87], axis: [-0.09, 0.46, -0.88], depth: 0.02 },
  charging: {
    window: { from: 10, to: 80, minutes: 15 },
    packKwh: 82.16,
    architectureV: 800,
    connector: 'GB/T',
    port: { side: 'left', published: true, where: 'Left rear quarter' },
    claims: [
      {
        text: 'The pure electric version supports 800 V high-voltage silicon carbide platform and CATL Shenxing 5C supercharging battery, replenishing 30-80% in 15 minutes.',
        source: { label: 'Avatr Official', url: 'https://www.avatr.com/en/06T' },
      },
    ],
    simulated: 'A simulation of 800 V high-speed charging based on CATL Shenxing battery specifications.',
  },
  tech: [
    {
      id: 'ads3',
      title: 'Huawei Qiankun ADS 3.0',
      blurb:
        'An expressway: a slower car moves into the lane close ahead and the car eases off; then something is lying in the lane, which the 896-line roof lidar marks well before the car reaches it, and the car checks the right lane and goes round it.',
      driver: 'sensors',
      scenario: 'debris',
      claims: [
        {
          text: 'Equipped with Huawei Qiankun ADS 3.0 autonomous driving system, 896-line high-precision roof LiDAR, and ultra-wide surround vision.',
          source: { label: 'Avatr Official', url: 'https://www.avatr.com/en/06T' },
        },
        {
          text: 'The system is built on an end-to-end GOD (General Obstacle Detection) network and a PDP (Prediction Decision Planning) network.',
          source: { label: 'Avatr Official', url: 'https://www.avatr.com/en/06T' },
        },
        {
          text: 'Huawei’s 896-line lidar recognises a 14 cm box at 120 m.',
          source: { label: 'Huawei Qiankun, 4 March 2026', url: 'https://auto.huawei.com/cn/news/2026/2026-3-4-lidar' },
        },
      ],
      simulated:
        'A simulation. The road, the other cars, the box, their speeds, what the car does and when are ours: no maker publishes a scenario. The box stands for the general obstacles the GOD network is described as detecting, and the cut-in for what the PDP network is described as predicting; the maker shows neither. The 14 cm at 120 m is Huawei’s figure for its 896-line lidar, used here as the distance at which the box is first marked; the beams’ angles and the reach they are drawn to are ours (no field of view is published). The other cars are the other models’ stand-ins in neutral paint.',
    },
    {
      id: 'star-ring',
      title: '35.4" Panoramic Star Ring Display',
      blurb: 'Surrounding cockpit with 35.4-inch 4K integrated star-ring display and dual 6.7-inch high-definition electronic rearview mirror screens.',
      driver: 'swivel',
      view: 'cabin',
      claims: [
        {
          text: 'The 35.4-inch 4K star-ring panoramic screen wraps across the front cowl, paired with dual electronic rearview mirror monitors.',
          source: { label: 'Avatr Official', url: 'https://www.avatr.com/en/06T' },
        },
      ],
      simulated: 'Cockpit view highlighting the panoramic wrap-around display and digital mirror screens.',
    },
    {
      id: 'park',
      title: 'Remote parking assist',
      blurb:
        'Step out, open the app and the car screens the bays with Qiankun ADS 3.0 sensors, identifies the vacant bay with a flashing P, and backs itself in between two parked cars. Or pull it out remotely.',
      driver: 'park',
      devices: ['phone', 'dashboard'],
      params: { search: 12 },
      claims: [
        {
          text: 'Equipped with Huawei Qiankun ADS 3.0, the Avatr supports Remote Parking Assist (RPA) and Valet Parking Assist (AVP), handling narrow spaces down to 0.4 m clearance.',
          source: { label: 'Avatr Official, Qiankun ADS 3.0', url: 'https://www.avatr.com' },
        },
      ],
      simulated:
        'A simulation of Qiankun ADS 3.0 remote parking: blue surround camera beams screen the bays, the target slot is marked with a flashing P, and the car reverses in smoothly.',
    },
  ],
  // The Drive tab's scenario (docs/tech-showcase.md section 19). Only the dual-motor and single-motor trims are in this file's
  // data, so the motors drawn are a front and a rear one. The tri-motor trim (one front and two rear motors, 712 kW, 2.78 s;
  // CarNewsChina, 23 April 2026) is not added: its pack and range reports disagree. Add it as a variant and the rear pair is
  // drawn as two motors by itself.
  drive: {
    id: 'shooting-brake',
    title: 'Shooting Brake Assault',
    blurb:
      'A wagon with a sports car’s pull: a 0–100 sprint, then an S-curve under power. Watch the body stay level, and set the car against the Denza Z9 on the chart.',
    modes: ['eco', 'comfort', 'sport', 'gt'],
    defaultMode: 'gt',
    overlays: ['suspension', 'motors', 'power'],
    finish: 'coast',
    manoeuvres: ['sweep'],
    ghost: { slug: 'denza-z9', variantId: '630-ultra-awd' },
    camera: 'chase',
    callouts: [
      { cue: 'launch', text: 'Launch. Weight moves to the rear axle; the long roof keeps the body level.' },
      { cue: 'sweep', text: 'S-curve under power. The body leans a little and the drive shifts between the axles.' },
    ],
    claims: [],
    simulated:
      'The S-curve, the roll and pitch of the body and the split of the drive between the two motors are ours.',
  },
  sources: [
    { label: 'Avatr Official - Avatr 06T', url: 'https://www.avatr.com/en/06T' },
    { label: 'Autohome - Avatr 06T Specs', url: 'https://www.autohome.com.cn/' },
  ],
};
