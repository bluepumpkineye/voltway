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
      size: [8.14, 5.195],
      centre: [0.008, 0.0],
    },
    // the cabin (blender/scripts/g9l_interior*.py, the Bordeaux Red interior) with its Cycles light baked in:
    // export_g9l.web_cabin()
    interiorModelUrl: '/models/xpeng-g9l-interior.glb',
    // lit by the shared showroom hall, shaded by the cabin's occlusion atlas (docs/3d-pipeline.md, "The hall look")
    interiorProbeUrl: '/models/cabin-hall.hdr',
    // the Bordeaux leather under the hall reads lighter and pinker than the studio photographs of it (seat ~131,82,85
    // sRGB there, ~185,89,98 at gain 1): pulled down in the viewer
    cabinGain: 0.65,
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
    heroColor: '#3B2D66',
    // over the driver's seat (the cabin's H-point (0.20, 0.375, 0.69) + 0.59 up)
    driverEye: [0.18, 0.40, 1.28],
    proxyUrl: '/models/xpeng-g9l-proxy.glb',
  },
  // The maker's photographs (Autohome 8659) show dark, smoky glass all round, windscreen included: the X-ray's pale
  // ghost (the default for a front pane seen from outside) read as an open greenhouse, and made the body look taller. The
  // windscreen of c1_0002 reads 48,58,72 on a sampled box and the backlight of c1_0006 28,34,38; the viewer's read 125,120,122
  // and 119,117,118, mostly the white studio mirrored in the panes (more opacity alone made it brighter), so they mirror less
  glass: { color: '#0C1116', opacity: 0.85, privacy: 0.92, reflect: 0.28, privacyReflect: 0.16 },
  configurator: {
    paintMaterial: 'M_Paint_G9L_Purple',
    paints: [
      // Provence Purple as the studio photographs show it: the door's mid-tone reads 78,71,113 sRGB in c1_0004; the baked
      // base colour (#271E45) came out 53,43,87 in the viewer, a heavier, bluer indigo than the car's dusty violet, so the
      // finish lifts it to 75,65,110 (door) and 76,68,107 (sill) with a sharper coat
      {
        id: 'provence-purple',
        name: 'Provence Purple',
        nameZh: '普罗旺斯紫',
        swatch: '#3B2D66',
        finish: { color: '#3A3158', roughness: 0.34, metalness: 0.2, clearcoat: 0.7, clearcoatRoughness: 0.04 },
      },
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
      // The second wheel on the showroom cars (Autohome c1_0033-59, the green, white, purple and grey cars: the sidewalls read
      // 265/45 R21): a black gloss five-arm turbine with machined chamfers, traced from c1_0053. Left and right are mirror images.
      {
        id: 'turbine-21',
        name: '21-inch Turbine five-arm',
        size: '21 in',
        tyres: '265/45 R21',
        node: 'XpengG9L_Turbine_Wheels',
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
      // the mounts sit inside the C-pillar's sail (the tail's skin is at |y| 0.59 at the upper mount, 0.63 at the lower
      // one since the tail was tapered in), and a shut car shows no strut at all (Openings.tsx useStruts)
      struts: [
        { body: [-2.06, 1.52, -0.55], moving: [-2.27, 1.36, -0.55] },
        { body: [-2.06, 1.52, 0.55], moving: [-2.27, 1.36, 0.55] },
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
      devices: ['phone', 'dashboard'],
      params: { noseIn: 1, search: 12 },
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
    {
      id: 'sensors',
      title: 'Autonomous Drive',
      blurb:
        'A city street between parked cars: someone steps out and the car brakes hard for them; further on it stops behind a car at a zebra crossing, waits for the people on it and moves off. Its cameras’ views are drawn from where they sit.',
      driver: 'sensors',
      scenario: 'city',
      claims: [
        {
          text: 'The G9L runs XNGP, a level 2 system, on three in-house Turing chips (2,250 TOPS) on the top trims and two or one on the others; it has eleven exterior cameras with a stereo pair at the front, two in the cabin, twelve ultrasonic sensors and three millimetre-wave radars (seven on the top trims). The table lists no lidar.',
          source: { label: 'Autohome configuration table, XPeng G9L (read 21 October 2026)', url: 'https://car.autohome.com.cn/config/series/8659.html' },
        },
        {
          text: 'NGP, powered by VLA 2.0, was shown on test rides in Paris covering roundabouts, narrow streets, motorcycle traffic, pedestrian crossings and complex right-of-way situations.',
          source: { label: 'XPeng, the G9L launched in Europe (14 October 2026)', url: 'https://www.xpeng.com/pressroom/news/01a139c634a4a12024aa8a02829e00f8' },
        },
        {
          text: 'The G9L has automatic emergency braking at speeds of up to 150 km/h.',
          source: { label: 'XPeng, the G9L launched in Europe (14 October 2026)', url: 'https://www.xpeng.com/pressroom/news/01a139c634a4a12024aa8a02829e00f8' },
        },
        {
          text: 'A camera sits in the black divider at the middle of the grille and another above the rear plate; round ultrasonic sensors sit in the front and rear bumpers; a sensor pod sits at the top of the windscreen.',
          source: { label: 'Autohome photo gallery of the G9L (series 8659), detail photographs', url: 'https://www.autohome.com.cn/8659/' },
        },
      ],
      simulated:
        'A simulation. The street, the people, the other cars, their speeds, what the car does and when are ours: no maker publishes a scenario. No field of view is published, so every camera view’s angle and the reach it is drawn to are ours, and the side views are drawn from the mirrors, where the photographs show no camera. A dot is a sensor a photograph shows (the nose, the tail, the windscreen pod); the radars are not drawn (the table counts three or seven). The people are stylised figures and the other cars are the other models’ stand-ins in neutral paint.',
    },
  ],
  // Where the sensors are, for Autonomous Drive, in the exterior model's space. The G9L has no lidar. Read off Autohome's photographs
  // of the details (c12_0044, c12_0068, c1_0001, c1_0003) and set on the model's surface by a ray (about 5 to 10 cm good): the camera
  // in the grille's black divider (the model's black trim spans 0.37 to 0.53 m at the middle; the lens sits at its top, under the
  // plate), the camera above the rear plate (the model's machined badge at 0.88 m), the sensor pod behind the top of the windscreen
  // (the glass begins at x = 0.45), and the round ultrasonic sensors in the bumpers: a pair either side of the front plate, a pair
  // at the lower corners, and a pair at the rear corners. Eleven cameras and twelve ultrasonic sensors are counted; the ones the
  // photographs show are marked, the rest are not drawn. The four views (forward from the pod, wide from the nose, backward from
  // the tail, to each side from the mirror) are ours: no field of view is published.
  sensors: {
    views: [
      { at: [0.52, 1.66, 0], yaw: 0, fov: 52, reach: 48 },
      { at: [2.55, 0.5, 0], yaw: 0, fov: 120, reach: 16 },
      { at: [0.85, 1.2, 1.02], yaw: -90, fov: 100, reach: 16, mirror: true },
      { at: [-2.53, 0.9, 0], yaw: 180, fov: 110, reach: 24 },
    ],
    cameras: [{ at: [0.52, 1.66, 0] }, { at: [2.55, 0.5, 0] }, { at: [-2.53, 0.9, 0] }],
    ultrasonic: [
      { at: [2.515, 0.6, 0.45], mirror: true },
      { at: [2.38, 0.4, 0.8], mirror: true },
      { at: [-2.46, 0.48, 0.72], mirror: true },
    ],
    surround: true,
    notes: {
      vision: '11 exterior cameras, drawn as four views: forward, wide from the nose, backward, and to each side from the mirrors',
      ultrasonic: '12; the photographs show the pairs in the front and rear bumpers',
      cameras: '11; the photographs show the nose, the tail and the pod behind the windscreen',
    },
  },
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
  // The Drive tab's scenario (docs/tech-showcase.md section 19). Rear steering: up to 15 degrees either way, turning radius 5.4 m
  // (the sources of the 'rear-steer' demo above).
  drive: {
    id: 'authority-agility',
    title: 'Effortless Authority + Maneuverability',
    blurb:
      'A strong, progressive 0–100 in a big SUV, then a slow slalom in which the rear wheels steer against the front: watch the angles, and how little the front wheels need to turn.',
    modes: ['eco', 'standard', 'sport'],
    defaultMode: 'sport',
    loads: [
      { id: 'driver', label: 'Driver', payloadKg: 75 },
      { id: 'family', label: 'Five + luggage', payloadKg: 455 },
    ],
    overlays: ['steering', 'weight', 'motors', 'power'],
    finish: 'coast',
    manoeuvres: ['slalom'],
    chassis: { airSuspension: true, rearSteerMaxDeg: 15 },
    ghost: { slug: 'zeekr-7x', variantId: 'awd' },
    camera: 'hero',
    callouts: [
      { cue: 'launch', text: 'Launch. A big car, a smooth pull: the pull builds progressively and the body stays composed.' },
      { cue: 'target', text: '100 km/h. Now down to slalom pace.' },
      { cue: 'slalom', text: 'Rear-wheel steering. The rear wheels turn against the front ones, so the front wheels need far less angle for the same curve.' },
    ],
    claims: [
      {
        text: 'The G9L has a steer-by-wire rear axle that turns up to 15° in either direction.',
        source: { label: 'Gasgoo, G9L goes on sale', url: 'https://autonews.gasgoo.com/articles/ev/xpeng-g9l-goes-on-sale-with-bev-reev-powertrains-2100932123174563841' },
      },
      {
        text: 'Rear-wheel steering is standard across the range, and the minimum turning radius is 5.4 m.',
        source: { label: 'Xchuxing, G9L', url: 'https://www.xchuxing.com/article/174677' },
      },
    ],
    simulated:
      'The slalom (cones 12 m apart, 16 km/h), the rear wheels’ share of the steering (0.6 of the front, within their 15°), the load and the split between the two motors are ours.',
  },
  sources: [
    { label: 'Autohome - XPeng G9L Specifications (Series 8659)', url: 'https://www.autohome.com.cn/8659/' },
    { label: 'XPeng Official - G9L Flagship Intelligent Luxury SUV', url: 'https://www.xpeng.com/' },
  ],
};
