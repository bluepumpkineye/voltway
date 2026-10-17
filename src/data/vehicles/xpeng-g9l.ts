import type { Vehicle } from './schema';

export const xpengG9l: Vehicle = {
  slug: 'xpeng-g9l',
  brand: 'XPeng',
  model: 'G9L',
  group: 'XPeng',
  bodyStyle: 'SUV',
  year: 2026,
  tagline: 'Flagship intelligent luxury SUV on 800V silicon carbide architecture.',
  summary:
    'The 2026 XPeng G9L is the brand’s flagship full-size luxury 5-seater SUV, offering both 800V 5C ultra-fast charging BEV and 1,602 km comprehensive range EREV variants, Hawkeye vision ADAS, and luxury chassis with dual-chamber air suspension.',
  dimensions: {
    lengthMm: 5120,
    widthMm: 1999,
    heightMm: 1782,
    wheelbaseMm: 3100,
    kerbWeightKg: 2740,
  },
  variants: [
    {
      id: '755-ultra-awd',
      name: '755 Ultra AWD Flagship',
      drive: 'AWD',
      battery: {
        capacityKwh: 110,
        chemistry: 'NMC',
        architectureV: 800,
        cRate: 5,
        chargeMinutes10to80: 12,
      },
      performance: {
        powerKw: 430,
        torqueNm: 695,
        zeroTo100S: 4.45,
        motorCount: 2,
        topSpeedKmh: 200,
      },
      range: [{ cycle: 'CLTC', km: 755 }],
      priceCny: 319800,
    },
    {
      id: '702-max-rwd',
      name: '702 Max RWD',
      drive: 'RWD',
      battery: {
        capacityKwh: 98,
        chemistry: 'NMC',
        architectureV: 800,
        cRate: 5,
        chargeMinutes10to80: 12,
      },
      performance: {
        powerKw: 270,
        torqueNm: 465,
        zeroTo100S: 6.8,
        motorCount: 1,
        topSpeedKmh: 200,
      },
      range: [{ cycle: 'CLTC', km: 702 }],
      priceCny: 241800,
    },
    {
      id: '660-ultra-awd',
      name: '660 Ultra AWD',
      drive: 'AWD',
      battery: {
        capacityKwh: 98,
        chemistry: 'NMC',
        architectureV: 800,
        cRate: 5,
        chargeMinutes10to80: 12,
      },
      performance: {
        powerKw: 430,
        torqueNm: 695,
        zeroTo100S: 4.6,
        motorCount: 2,
        topSpeedKmh: 200,
      },
      range: [{ cycle: 'CLTC', km: 660 }],
      priceCny: 289800,
    },
    {
      id: '1602-erev-ultra',
      name: '1602 EREV Ultra Flagship',
      drive: 'AWD',
      battery: {
        capacityKwh: 55.9,
        chemistry: 'LFP',
        architectureV: 800,
        cRate: 4,
        chargeMinutes10to80: 15,
      },
      performance: {
        powerKw: 370,
        torqueNm: 695,
        zeroTo100S: 4.9,
        motorCount: 2,
        topSpeedKmh: 200,
      },
      range: [{ cycle: 'CLTC', km: 1602 }],
      priceCny: 309800,
    },
  ],
  cockpit: {
    os: 'XOS Tianji',
    skin: 'xos',
    accentColor: '#00D2FF',
    ambientLighting: true,
    // the star-field band under the screen glows violet in the photographs (c10_0002, c10_0021)
    ambientHue: 262,
    defaultTheme: 'dark',
    driveModes: [
      { id: 'standard', label: 'Standard', native: '标准', group: 'street', model: 'comfort' },
      { id: 'eco', label: 'Eco', native: '节能', group: 'street', model: 'eco' },
      { id: 'sport', label: 'Sport', native: '运动', group: 'street', model: 'sport' },
      { id: 'off-road', label: 'Off-road', native: '脱困', group: 'special', model: 'comfort' },
      { id: 'custom', label: 'Custom', native: '个性化', group: 'special', model: 'comfort' },
    ],
    screens: [
      { id: 'center', label: 'Centre touchscreen', diagonalIn: 15.6, role: 'center', interactive: true },
      { id: 'passenger', label: 'Passenger entertainment screen', diagonalIn: 15.6, role: 'passenger' },
      { id: 'cluster', label: 'Instrument cluster', diagonalIn: 10.25, role: 'cluster' },
      { id: 'hud', label: 'AR head-up display', diagonalIn: 50, role: 'hud' },
    ],
  },
  assets: {
    modelUrl: '/models/xpeng-g9l.glb',
    showroomOnly: true,
    studioShadow: {
      url: '/models/xpeng-g9l-shadow.webp',
      size: [8.144, 5.195],
      centre: [0.012, 0.0],
    },
    // the cabin (blender/scripts/g9l_interior*.py, the Bordeaux Red interior) with its Cycles light baked in:
    // export_g9l.web_cabin()
    interiorModelUrl: '/models/xpeng-g9l-interior.glb',
    interiorProbeUrl: '/models/xpeng-g9l-cabin.hdr',
    // Poly Haven "Shanghai Riverside" (CC0), turned as the SU7's, the 7X's and the Z9's: inside, the skyline is ahead
    // through the windscreen and the sun behind; outside, the world turns 147.6 deg so the default camera has the
    // golden-hour sun at its back
    outside: {
      view: '/models/xpeng-g9l-outside.jpg',
      light: '/models/xpeng-g9l-outside-light.hdr',
      exteriorTurnDeg: 147.6,
      sun: { direction: [0.6959, 0.3477, 0.6284], color: '#ffdfae', intensity: 1.96 },
      ground: { height: 1.7, radius: 45 },
    },
    heroColor: '#4E2C3C',
    // over the driver's seat (the cabin's H-point (0.20, 0.375, 0.69) + 0.59 up)
    driverEye: [0.18, 0.40, 1.28],
    proxyUrl: '/models/xpeng-g9l-proxy.glb',
  },
  configurator: {
    paintMaterial: 'M_Paint_G9L_Purple',
    paints: [
      { id: 'provence-purple', name: 'Provence Purple', nameZh: '普罗旺斯紫', swatch: '#4E2C3C' },
      {
        id: 'everest-white',
        name: 'Everest White',
        nameZh: '珠峰白',
        swatch: '#FFFFFF',
        finish: { color: '#F2F2F2', roughness: 0.35, metalness: 0.12, clearcoat: 0.5 },
      },
      {
        id: 'tuscany-green',
        name: 'Tuscany Green',
        nameZh: '托斯卡纳绿',
        swatch: '#075138',
        finish: { color: '#0A3B2B', roughness: 0.36, metalness: 0.19, clearcoat: 0.45 },
      },
      {
        id: 'fjord-grey',
        name: 'Fjord Grey',
        nameZh: '峡湾灰',
        swatch: '#374450',
        finish: { color: '#3A444C', roughness: 0.38, metalness: 0.19, clearcoat: 0.4 },
      },
      {
        id: 'midnight-black',
        name: 'Midnight Black',
        nameZh: '极夜黑',
        swatch: '#141518',
        finish: { color: '#111214', roughness: 0.32, metalness: 0.05, clearcoat: 0.6 },
      },
    ],
    // The first colourway is the cabin as built (the purple car's Bordeaux Red interior, Autohome's spec 77790); the
    // others recolour its leathers, which panel takes which colour is ours.
    trims: [
      {
        id: 'bordeaux-red',
        name: 'Black / Bordeaux Red',
        nameZh: '黑色/波尔多红',
        swatch: ['#18191B', '#7E2530'],
      },
      {
        id: 'sahara-orange',
        name: 'Black / Sahara Orange',
        nameZh: '黑色/撒哈拉橙',
        swatch: ['#18191B', '#E57338'],
        colors: {
          INT_Leather_Seat: '#b04d1c',
          INT_Leather_Dash: '#9b4219',
          INT_Thread_Seat: '#e8a070',
          INT_Carpet_Black: '#26201d',
        },
      },
      {
        id: 'dawn-white',
        name: 'Black / Dawn White',
        nameZh: '黑色/拂晓白',
        swatch: ['#18191B', '#EAE6E1'],
        colors: {
          INT_Leather_Seat: '#d9d4cd',
          INT_Leather_Dash: '#cdc7bf',
          INT_Thread_Seat: '#9a948d',
          INT_Carpet_Black: '#3a3836',
        },
      },
      {
        id: 'meteorite-black',
        name: 'Meteorite Black',
        nameZh: '陨石黑',
        swatch: ['#141518', '#202125'],
        colors: {
          INT_Leather_Seat: '#26272a',
          INT_Leather_Dash: '#202124',
          INT_Thread_Seat: '#4a4b50',
          INT_Carpet_Black: '#1c1d1f',
        },
      },
    ],
    wheels: [
      {
        id: 'aero-22',
        name: '22-inch Aero five-spoke',
        nameZh: '22英寸低风阻轮毂',
        size: '22 in',
        tyres: '265/40 R22',
        node: 'XpengG9L_Wheels',
      },
    ],
    sources: [
      { label: 'Autohome - XPeng G9L Configuration & Specs (Series 8659)', url: 'https://www.autohome.com.cn/8659/' },
      { label: 'XPeng Official - G9L Flagship Intelligent Luxury SUV', url: 'https://www.xpeng.com/' },
    ],
  },
  // The four doors swing on their leading edge (the hinge: mid height, on the skin; blender/scripts/g9l_openings.py). The
  // node origins are the hinges, and the cabin's door cards turn about the same axes. The sign is the swing direction
  // (glTF y up): the left doors turn negative.
  openings: [
    { id: 'doorFL', node: 'XpengG9L_Door_FL', cardNode: 'int_door_L', frameNode: 'XpengG9L_DoorFrame_FL', deg: -70 },
    { id: 'doorFR', node: 'XpengG9L_Door_FR', cardNode: 'int_door_R', frameNode: 'XpengG9L_DoorFrame_FR', deg: 70 },
    { id: 'doorRL', node: 'XpengG9L_Door_RL', cardNode: 'int_rdoor_L', frameNode: 'XpengG9L_DoorFrame_RL', deg: -68 },
    { id: 'doorRR', node: 'XpengG9L_Door_RR', cardNode: 'int_rdoor_R', frameNode: 'XpengG9L_DoorFrame_RR', deg: 68 },
    // The bonnet hinges on a lateral axis under its rear edge at the cowl and rises about 62 deg (c12_0001); two gas
    // struts hold it from the cowl's corners (c12_0002). The frunk under it is blender/scripts/g9l_bays.py.
    {
      id: 'frunk',
      node: 'XpengG9L_Bonnet',
      axis: 'z',
      deg: 62,
      struts: [
        { body: [1.27, 1.10, -0.86], moving: [1.56, 1.215, -0.86] },
        { body: [1.27, 1.10, 0.86], moving: [1.56, 1.215, 0.86] },
      ],
    },
    // The tailgate is the whole rear above its smile shut line: the backlight with the spoiler, the lamp bar's
    // middle and the painted gate. It hangs from the roof's trailing edge (blender/scripts/g9l_gate.py) and swings
    // up about 82 deg on two gas struts at its sides (Autohome c3_0156/57). The cabin's liner turns with it.
    {
      id: 'boot',
      node: 'XpengG9L_Tailgate',
      cardNode: 'int_tailgate',
      axis: 'z',
      deg: -82,
      hidesOutside: ['int_cpillar', 'int_cpillar_flange'],
      // the mounts sit inside the C-pillar's sail (its walls are at y 0.64-0.72 there), so a shut car shows no strut
      struts: [
        { body: [-2.06, 1.52, -0.665], moving: [-2.27, 1.36, -0.665] },
        { body: [-2.06, 1.52, 0.665], moving: [-2.27, 1.36, 0.665] },
      ],
    },
  ],
  // The Tech tab (docs/tech-showcase.md, section 14).
  tech: [
    {
      id: 'rear-steer',
      title: 'Rear-wheel steering',
      blurb:
        'A U-turn on a street as wide as the turn needs: the rear wheels steer against the fronts, so the SUV turns on a circle much tighter than its five metres suggest.',
      driver: 'uturn',
      devices: ['dashboard'],
      params: { radiusM: 5.4, rearMaxDeg: 15 },
      claims: [
        {
          text: 'The G9L has a steer-by-wire rear axle that turns up to 15° in either direction.',
          source: { label: 'Gasgoo, G9L goes on sale', url: 'https://autonews.gasgoo.com/articles/ev/xpeng-g9l-goes-on-sale-with-bev-reev-powertrains-2100932123174563841' },
        },
        {
          text: 'Rear-wheel steering is standard across the range, and the minimum turning radius is 5.4 m.',
          source: { label: 'Xchuxing, G9L', url: 'https://www.xchuxing.com/article/174677' },
        },
        {
          text: 'Another benefit of the G9L is rear-wheel steering and a turning radius of 5.4 metres.',
          source: { label: 'CarNewsChina, 11 August 2026', url: 'https://carnewschina.com/2026/08/11/xpeng-g9l-revealed-price-with-rear-wheel-steering-755-km-range/' },
        },
      ],
      simulated:
        'A simulation. We draw the 5.4 m as the circle the outer front wheel follows (the sources do not say how it is measured; Wikipedia gives 4.96 m) and set the inner rear wheel at its 15° limit; the front wheels’ angles then follow from the geometry (about 35° and 25°), they are not published. The street, its width (the sweep of the turn plus 90 cm each side), the pace and the screen are ours.',
    },
    {
      id: 'nose-in',
      title: 'Nose-in parking',
      blurb:
        'The G9L takes a bay head first, which leaves the boot at the lane, and drives itself in and out. The button stands for the voice command that starts it from outside.',
      driver: 'park',
      params: { noseIn: 1 },
      claims: [
        {
          text: 'A new nose-in parking function makes the boot easier to reach, and voice commands from outside the car can direct parking manoeuvres.',
          source: { label: 'Gasgoo, G9L goes on sale', url: 'https://autonews.gasgoo.com/articles/ev/xpeng-g9l-goes-on-sale-with-bev-reev-powertrains-2100932123174563841' },
        },
        {
          text: 'The steer-by-wire rear axle turns up to 15° in either direction.',
          source: { label: 'Gasgoo, G9L goes on sale', url: 'https://autonews.gasgoo.com/articles/ev/xpeng-g9l-goes-on-sale-with-bev-reev-powertrains-2100932123174563841' },
        },
      ],
      simulated:
        'A simulation. The maker publishes that the car parks nose first and takes voice commands from outside; the path (a quarter turn about a point ahead of the rear axle on the rear steering, then straight in), the bay, the neighbours and the speed are ours. No voice interface is drawn: the button stands for the command.',
    },
  ],
  // The DC socket's mouth (the right rear quarter, behind the wheel: our estimate of the place, snapped to the model's skin
  // by a ray) and the direction out of it, in the viewer's axes. The model has no flap, so the Charging tab draws a socket here.
  chargePort: { mouth: [-1.7, 1.1, 0.9517], axis: [-0.0349, 0.2769, 0.9603], depth: 0.02 },
  // The Charging tab (docs/tech-showcase.md section 11). Sources read 2026-10-16.
  charging: {
    window: { from: 10, to: 80, minutes: 12 },
    cRate: 5,
    packKwh: 110,
    architectureV: 800,
    connector: 'GB/T',
    port: { side: 'right', published: true, where: 'Right rear quarter' },
    claims: [
      {
        text: 'XPeng’s refreshed G9 (the G9L’s predecessor) has 5C packs on a full-domain 800 V silicon-carbide platform, charging from 10 to 80 % in just 12 minutes, at up to 525 kW.',
        source: { label: 'XPeng news, G6 and G9 upgrade', url: 'https://www.xpeng.com/news/019762f4239996d25db58a02820b01b0' },
      },
      {
        text: 'The G9L’s DC charge port is on the right rear side.',
        source: { label: 'EVKX, XPENG G9L 91.9 kWh', url: 'https://evkx.net/models/xpeng/g9l/g9l_91.9_kwh_awd/' },
      },
    ],
    simulated:
      'A simulation. The 5C and the twelve minutes are XPeng’s for its 5C cars; the G9L’s own peak is not published, so it is drawn as 5C times the 110 kWh pack, and the curve between is ours. The model has no charge flap, so the socket is drawn at a place on the right rear quarter that we chose, and the pedestal and the gun (styled on a generic charging connector, not XPeng’s or any maker’s) are ours. Twelve minutes play in fourteen seconds.',
  },
  sources: [
    { label: 'Autohome - XPeng G9L Specifications (Series 8659)', url: 'https://www.autohome.com.cn/8659/' },
    { label: 'XPeng Official - G9L Flagship Intelligent Luxury SUV', url: 'https://www.xpeng.com/' },
  ],
};
