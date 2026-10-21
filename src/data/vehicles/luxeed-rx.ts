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
    // as the Control Centre and Settings > Driving list them (Autohome's photographs
    // of the screens; 运动+ is the strongest street mode, shown as Sport in the model)
    driveModes: [
      { id: 'eco', label: 'Eco', native: '节能', group: 'street', model: 'eco' },
      { id: 'comfort', label: 'Comfort', native: '舒适', group: 'street', model: 'comfort' },
      { id: 'sport', label: 'Sport', native: '运动', group: 'street', model: 'sport' },
      { id: 'sport-plus', label: 'Sport+', native: '运动+', group: 'street', model: 'sport' },
      { id: 'custom', label: 'Custom', native: '定制个性化', group: 'special', model: 'comfort' },
    ],
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
    // lit by the shared showroom hall, shaded by the cabin's occlusion atlas (docs/3d-pipeline.md, "The hall look")
    interiorProbeUrl: '/models/cabin-hall.hdr',
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
    // its shadow on the studio floor: blender/scripts/export_rx.py bake_ground_shadow(),
    // which prints the size and centre (the build's axes, metres)
    studioShadow: { url: '/models/luxeed-rx-shadow.webp', size: [8.069, 5.195], centre: [-0.028, 0] },
    // scripts/make-proxy.mjs: the neighbour in another car's parking stage
    proxyUrl: '/models/luxeed-rx-proxy.glb',
    heroColor: '#1B4D8F',
    // over the driver's seat, from the camera-matched cabin build
    driverEye: [-0.32, 0.41, 1.19],
  },
  // The maker's own palette (hima.auto/zhijie/rx): six paints, four cabin
  // colours. The build is Blue Morpho with the Red Shadow White cabin, so those
  // two are "as built"; every other value is matched by eye to the maker's
  // press images under our studio rig (hence "approximate" in the interface).
  // The wheels and the caliper colours are selectable (Wheels tab); the frunk
  // is a part that opens (openings), not an option.
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
    // The maker says the calipers come in "red, grey, yellow and other colours"
    // (the launch reports below). Orange is the colour the show cars wear in
    // the photographs, and the build's own. The values are the build's caliper
    // palette (carkit.materials.CALIPERS) as sRGB, so they are approximate.
    caliperMaterial: 'M_Caliper_Orange',
    calipers: [
      { id: 'orange', name: 'Orange', nameZh: '橙色', color: '#e56f1d' },
      { id: 'red', name: 'Red', nameZh: '红色', color: '#bf2724' },
      { id: 'grey', name: 'Grey', nameZh: '灰色', color: '#7c7d7e' },
      { id: 'yellow', name: 'Yellow', nameZh: '黄色', color: '#e2bf19' },
    ],
    // The maker's configuration page (hima.auto/zhijie/rx/configuration) lists four
    // wheels: the 20 in 'Starlight' (no photograph of it exists, so it is not built),
    // the 21 in 'Yufeng' and 'Sport' double five-spokes and the 22 in 'Fengying'
    // five-spoke. The first is what the model is built with; the others are nodes of
    // the same file. Traced from the Autohome photographs, which show the Yufeng
    // with red calipers and the Sport (also in a blue-accent finish) with
    // yellow-gold and orange ones.
    wheels: [
      { id: 'fengying', name: 'Fengying', size: '22"', tyres: '255/40 R22 front · 275/40 R22 rear', node: 'LuxeedRX_Fengying_Wheels', caliper: 'orange' },
      { id: 'yufeng', name: 'Yufeng', size: '21"', tyres: '255/45 R21 front · 275/45 R21 rear', node: 'LuxeedRX_Yufeng_Wheels', caliper: 'red' },
      {
        id: 'sport',
        name: 'Sport',
        size: '21"',
        tyres: '255/45 R21 front · 275/45 R21 rear',
        node: 'LuxeedRX_Sport_Wheels',
        accent: { material: 'M_Wheel_Accent', color: '#0c0c0e' },
        caliper: 'orange',
      },
      {
        id: 'sport-blue',
        name: 'Sport, blue accent',
        size: '21"',
        tyres: '255/45 R21 front · 275/45 R21 rear',
        node: 'LuxeedRX_Sport_Wheels',
        accent: { material: 'M_Wheel_Accent', color: '#1c58e8' },
        caliper: 'orange',
      },
    ],
    sources: [
      { label: 'HIMA - Luxeed RX: six paints, four interior colours', url: 'https://hima.auto/zhijie/rx/' },
      {
        label: 'IT之家 (30 Jul 2026) - RX road-test car: calipers in red, grey, yellow and other colours; 20-22 in wheels',
        url: 'https://www.ithome.com/0/983/889.htm',
      },
      {
        label: 'Phoenix Tech (9 Jul 2026) - over 20 colours planned; calipers in red, grey, yellow; 255/50 R20 to 275/40 R22 tyres',
        url: 'https://tech.ifeng.com/c/8ucC3FOGpbe',
      },
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
  // The lamps (docs/lights.md): the usual LED materials, and the headlamp's two projector lenses
  // (M_Lamp_Reflector at the front only) light with the low beam.
  lights: { projector: {} },
  // The 16.1 in centre screen is on a motor: 55 mm forward and back, up to 30 degrees to either side (the maker's
  // page, some trims only). It turns about the hub behind its middle (rx_interior.py: SCREEN_C, the arm's end).
  swivel: { cabinNode: 'LuxeedRX_Cabin', turnDeg: 30, travelM: 0.055, hub: [0.47, 0] },
  // Where the sensors are, for the sensor demo, in the exterior model's space. The roof lidar's window, the cameras and the
  // ultrasonic sensors are read off Autohome's photographs of the detail (board T3d); the solid-state lidars at the sides
  // are put at the fender gill, where one secondary source reports them (the photographs show cameras and a slot there),
  // and the rear one at the tail, where nothing says it is. The count of cameras is not published.
  sensors: {
    lidar: [0.16, 1.47, 0],
    sideLidar: [0.93, 0.86, 0.95],
    rearLidar: [-2.49, 0.95, 0],
    cameras: [
      { at: [0.2, 1.41, 0.045], mirror: true },
      { at: [0.93, 0.9, 0.95], mirror: true },
      { at: [2.42, 0.7, 0] },
      { at: [0.62, 1.02, 1.0], mirror: true },
      { at: [-2.49, 1.02, 0] },
      { at: [-2.49, 0.86, 0] },
    ],
    ultrasonic: [{ at: [2.32, 0.48, 0.74], mirror: true }],
    notes: {
      lidar: '896 lines, a wide and a tele light path',
      side: '2, solid-state, drawn from the fender gill',
      rear: '1, solid-state, drawn from the tail',
      ultrasonic: '12, as the maker counts them',
      cameras: 'as the photographs show them',
    },
  },
  // The DC socket's mouth (the left rear quarter above and behind the rear wheel, where the photographs show the flap;
  // the exact place is our estimate, snapped to the model's skin by a ray) and the direction out of it, in the viewer's
  // axes. The model has no flap, so the Charging tab draws a socket here.
  chargePort: { mouth: [-1.9, 1.06, -0.885], axis: [-0.0938, 0.463, -0.8814], depth: 0.02 },
  // The Charging tab (docs/tech-showcase.md section 11). Sources read 2026-10-16.
  charging: {
    window: { from: 30, to: 80, minutes: 15 },
    packKwh: 100.4,
    architectureV: 800,
    connector: 'GB/T',
    port: { side: 'left', published: false, where: 'Left rear quarter, as the photographs show' },
    claims: [
      {
        text: 'All variants support 800 V fast charging: a charge from 30 to 80 % takes about 15 minutes. The packs are an 81 kWh lithium iron phosphate and a 100 kWh ternary.',
        source: { label: 'CnEVPost, Luxeed launches the RX, 28 September 2026', url: 'https://cnevpost.com/2026/09/28/luxeed-launches-rx-suv/' },
      },
    ],
    simulated:
      'A simulation. Only the 15 minutes from 30 to 80 % and the 800 V are published: no peak power is, so the peak is derived from the window’s average power, and the curve is ours. The charge flap is on the left rear quarter in the photographs, but the model has none: the socket is drawn at a place we chose, and the pedestal and the gun (styled on a generic charging connector, not Luxeed’s or any maker’s) are ours. Fifteen minutes play in fourteen seconds.',
  },
  // The BOOST knob on the wheel's lower right, in the cabin model's space: found by casting a ray at the knob (a satin black
  // cap in a chrome ring, about 32 mm across) from the driver's eye.
  boost: { knob: [0.287, 0.953, -0.328] },
  // The Tech tab (docs/tech-showcase.md). "Park from your phone" first; the rig test drives the
  // wheels through every steering mode and is left out of a production build.
  tech: [
    {
      id: 'park',
      title: 'Park from your phone',
      blurb:
        'Step out, open the app and the car backs itself into a tight bay between two parked cars, then drives out again. Or start it from the car’s own screen.',
      driver: 'park',
      devices: ['phone', 'dashboard'],
      claims: [
        {
          text: 'Remote parking is standard equipment on the Luxeed RX.',
          source: { label: 'Autohome configuration table', url: 'https://car.autohome.com.cn/config/series/8684.html' },
        },
        {
          text: 'Huawei’s remote parking assist is driven from the phone app and copes with extremely narrow slots, in over 160 parking scenarios (stated for the AITO M9, the same Huawei system).',
          source: { label: 'MyDrivers (快科技), 5 June 2024', url: 'https://news.mydrivers.com/1/984/984237.htm' },
        },
        {
          text: 'The HIMA app’s remote control module lists remote parking among its functions.',
          source: { label: 'MyDrivers (快科技), 28 February 2025', url: 'https://news.mydrivers.com/1/1033/1033033.htm' },
        },
      ],
      simulated:
        'A simulation: the path, the speeds and the screens are ours, drawn from the maker’s published description of the function, not its footage or its software.',
    },
    {
      id: 'sensors',
      title: 'Autonomous Drive',
      blurb:
        'A three-lane road with traffic in every lane. The car’s lidars and ultrasonic sensors, drawn from where they sit, as the car ahead brakes, the car follows it, waits for the left lane to clear and overtakes.',
      driver: 'sensors',
      scenario: 'overtake',
      claims: [
        {
          text: 'The RX carries 38 sensors, among them the world’s highest-spec mass-produced 896-line dual-optical-path image-grade lidar and three high-precision solid-state lidars.',
          source: { label: 'HIMA, the Luxeed RX page', url: 'https://hima.auto/zhijie/rx/' },
        },
        {
          text: 'On the Ultra trims: one forward lidar in the roof housing, two solid-state lidars at the sides and one at the rear, five millimetre-wave radars and twelve ultrasonic sensors.',
          source: { label: 'Autohome (Chejiahao) and its configuration table', url: 'https://chejiahao.m.autohome.com.cn/info/25677033' },
        },
        {
          text: 'The 896-line lidar has a wide and a tele light path under independent control, and recognises a 14 cm box at 120 m.',
          source: { label: 'Huawei Qiankun, 4 March 2026', url: 'https://auto.huawei.com/cn/news/2026/2026-3-4-lidar' },
        },
        {
          text: 'Huawei’s Qiankun ADS Pro update does navigation-guided cruise assist that follows traffic and changes lane to overtake (announced for city roads, 20 April 2026).',
          source: { label: '10jqka (同花顺), 20 April 2026', url: 'https://news.10jqka.com.cn/20260420/c676114121.shtml' },
        },
        {
          text: 'The lidar’s window is in the black housing at the top of the windscreen, beside a pair of cameras; the front fender’s black gill carries cameras and a dark slot; a dual-lens unit sits under the tail badge.',
          source: { label: 'Autohome photo of the RX’s details', url: 'https://www.autohome.com.cn/cars/imgs-8684-78055-12-x/13535277.html' },
        },
      ],
      simulated:
        'A simulation. The road, the other cars, their speeds, the braking, the decisions and when they come are ours, and so is every cone’s angle and the reach it is drawn to: no field of view is published (the real lidar recognises a 14 cm box at 120 m). The side lidars are drawn from the fender gill, where one source reports them, and the rear one from where nothing says it is; the five radars are not drawn. A dot is a sensor a photograph shows; a ring is a position reported or not published. The other cars are the other models’ stand-ins in neutral paint.',
    },
    {
      id: 'boost',
      title: 'BOOST',
      blurb:
        'From the driver’s seat: press the BOOST knob on the wheel. Its ring lights and the car’s screen shows what the maker says BOOST changes, one step at a time.',
      driver: 'boost',
      view: 'cabin',
      claims: [
        {
          text: 'One press of BOOST raises instantaneous torque by 10 %, with its own throttle calibration, its own chassis tune, a three-screen linkage with a sport sound, and the seat belts and seat bolsters tightening at once. Some trims only.',
          source: { label: 'HIMA, the Luxeed RX page', url: 'https://hima.auto/zhijie/rx/' },
        },
        {
          text: 'The motor turns up to 21,000 rpm, the car reaches 251 km/h, the motor is 98.2 % efficient and its torque responds within 1 ms.',
          source: { label: 'HIMA, the Luxeed RX page', url: 'https://hima.auto/zhijie/rx/' },
        },
        {
          text: 'The BOOST knob is a round button at the lower right of the steering wheel; its ring is lit blue when BOOST is on.',
          source: { label: 'Autohome photos of the RX’s wheel (lit, and not)', url: 'https://www.autohome.com.cn/cars/imgs-8684-78916-10-x/13373093.html' },
        },
      ],
      simulated:
        'A simulation. The steps are the maker’s list; their order and timing are ours, and so is the screen the cabin shows: a stand-in, because the maker’s BOOST screens (the cluster, the centre screen and the head-up display change together) are not photographed. The lit ring is drawn over the model’s knob.',
    },
    {
      id: 'swivel',
      title: 'Swivel screen',
      blurb:
        'From the driver’s seat: the 16.1 in centre screen turns toward you, toward the passenger, and slides forward and back, as the four buttons of its direction dialog ask.',
      driver: 'swivel',
      view: 'cabin',
      claims: [
        {
          text: 'The 16.1 in centre screen moves four ways on a motor: 55 mm forward and back, and up to 30° to the left and right, so the driver and the front passenger are each in the best seat for it. Some trims only.',
          source: { label: 'HIMA, the Luxeed RX page', url: 'https://hima.auto/zhijie/rx/' },
        },
        {
          text: 'Its settings dialog has four buttons (centre and back, centre and forward, toward the driver, toward the passenger), a “follow on boarding” switch that turns it by who is in the seats, and the steering wheel’s right scroll wheel sets the angle.',
          source: { label: 'Autohome photo of the RX’s screen', url: 'https://www.autohome.com.cn/cars/imgs-8684-78916-10-x/13373056.html' },
        },
      ],
      simulated:
        'A simulation: the order of the presses and how fast the screen moves are ours (the maker publishes the 55 mm and the 30°, not a speed). The dialog is drawn from Autohome’s photograph, and the screen turns about a hub behind its middle.',
    },
    {
      id: 'rig-test',
      title: 'Rig test',
      blurb:
        'Front-wheel steering, a reverse, a crab walk, a compass turn about a front wheel and a four-wheel-steer turn, on the car’s own wheelbase and track.',
      driver: 'rig-test',
      claims: [],
      simulated: 'A kinematic test of the wheel rig, not a feature of the car.',
      devOnly: true,
    },
  ],
  sources: [
    { label: 'CnEVPost - Luxeed opens RX pre-orders', url: 'https://cnevpost.com/2026/08/20/luxeed-opens-pre-orders-rx-suv/' },
    { label: 'CarNewsChina - 586 hp, pre-orders Aug 20', url: 'https://carnewschina.com/2026/08/18/cherys-luxeed-rx-from-ex-ferrari-designer-586-hp-to-start-pre-orders-on-august-20/' },
    { label: 'Wikipedia - Luxeed RX', url: 'https://en.wikipedia.org/wiki/Luxeed_RX' },
  ],
  dataCaveat:
    'Pre-sales opened 20 August 2026. Torque, 0-100 and kerb weight are not yet published, and trim-level range figures may move before deliveries begin.',
};
