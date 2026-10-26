import type { Vehicle } from './schema';

export const denzaZ9: Vehicle = {
  slug: 'denza-z9',
  brand: 'Denza',
  model: 'Z9',
  group: 'BYD · Denza',
  bodyStyle: 'Sedan',
  year: 2025,
  tagline: 'D-segment luxury executive flagship sedan on the e³ tri-motor & DiSus-A platform.',
  summary:
    'Denza’s 5,220 mm three-box flagship executive sedan pairing the Corona (日冕) dual-layer headlamp signature and Time Hourglass (时光沙漏) rear light bars with BYD’s e³ platform, independent rear-wheel steering (±10°), DiSus-A dual-chamber air suspension, and DiLink 150 quad-screen cabin.',
  dimensions: {
    lengthMm: 5220,
    widthMm: 1990,
    heightMm: 1500,
    wheelbaseMm: 3125,
    kerbWeightKg: 2780,
  },
  variants: [
    {
      id: '630-max-awd',
      name: '630 Quad-Motor Max AWD',
      drive: 'AWD',
      battery: {
        capacityKwh: 100.0,
        chemistry: 'LFP',
        architectureV: 800,
        cRate: 5.0,
        chargeMinutes10to80: 19,
      },
      performance: {
        powerKw: 710,
        torqueNm: 1150,
        zeroTo100S: 3.4,
        motorCount: 3,
        topSpeedKmh: 240,
      },
      range: [{ cycle: 'CLTC', km: 630 }],
      priceCny: 354800,
    },
    {
      id: '630-ultra-awd',
      name: '630 Tri-Motor Ultra AWD Flagship',
      drive: 'AWD',
      battery: {
        capacityKwh: 100.0,
        chemistry: 'LFP',
        architectureV: 800,
        cRate: 5.0,
        chargeMinutes10to80: 19,
      },
      performance: {
        powerKw: 710,
        torqueNm: 1150,
        zeroTo100S: 3.4,
        motorCount: 3,
        topSpeedKmh: 240,
      },
      range: [{ cycle: 'CLTC', km: 630 }],
      priceCny: 384800,
    },
    {
      id: '1100-ultra-phev',
      name: '1100 DM-i Tri-Motor Ultra AWD',
      drive: 'AWD',
      battery: {
        capacityKwh: 38.5,
        chemistry: 'LFP',
        architectureV: 800,
        cRate: 3.5,
        chargeMinutes10to80: 19,
      },
      performance: {
        powerKw: 640,
        torqueNm: 1035,
        zeroTo100S: 3.6,
        motorCount: 3,
        topSpeedKmh: 230,
      },
      range: [{ cycle: 'CLTC', km: 1100 }],
      priceCny: 334800,
    },
  ],
  cockpit: {
    os: 'DiLink 150',
    skin: 'dilink',
    accentColor: '#9C82E8',
    ambientLighting: true,
    defaultTheme: 'dark',
    driveModes: [
      { id: 'comfort', label: 'Comfort', native: '舒适', group: 'street', model: 'comfort' },
      { id: 'eco', label: 'Eco', native: '经济', group: 'street', model: 'eco' },
      { id: 'sport', label: 'Sport', native: '运动', group: 'street', model: 'sport' },
      { id: 'compass', label: 'e³ Compass Turn', native: '易三方圆规掉头', group: 'special', model: 'sport' },
      { id: 'crab', label: 'Intelligent Crab Walk', native: '智能蟹行', group: 'special', model: 'comfort' },
    ],
    screens: [
      { id: 'center', label: '17.3" 2.5K Floating Centre Display', diagonalIn: 17.3, role: 'center', interactive: true },
      { id: 'passenger', label: '13.2" 2.5K Co-Pilot Entertainment Display', diagonalIn: 13.2, role: 'passenger' },
      { id: 'cluster', label: '13.2" 3D Instrument Cluster', diagonalIn: 13.2, role: 'cluster' },
      { id: 'hud', label: '50" AR Head-Up Display', diagonalIn: 50, role: 'hud' },
    ],
  },
  assets: {
    modelUrl: '/models/denza-z9.glb',
    showroomOnly: true,
    studioShadow: {
      url: '/models/denza-z9-shadow.webp',
      size: [8.246, 5.16],
      centre: [0.008, 0.0],
    },
    // the cabin (blender/scripts/z9_interior*.py, the Pamir Brown Nappa interior) with its Cycles light
    // baked in: export_z9.web_cabin()
    interiorModelUrl: '/models/denza-z9-interior.glb',
    // lit by the shared showroom hall, shaded by the cabin's occlusion atlas (docs/3d-pipeline.md, "The hall look")
    interiorProbeUrl: '/models/cabin-hall.hdr',
    // Poly Haven "Shanghai Riverside" (CC0), turned exactly as the SU7's and the 7X's: inside, the skyline is
    // ahead through the windscreen and the sun behind; outside, the world turns 147.6 deg so the default camera
    // has the golden-hour sun at its back
    outside: {
      view: '/models/denza-z9-outside.jpg',
      light: '/models/denza-z9-outside-light.hdr',
      exteriorTurnDeg: 147.6,
      sun: { direction: [0.6959, 0.3477, 0.6284], color: '#ffdfae', intensity: 1.96 },
      ground: { height: 1.7, radius: 45 },
    },
    heroColor: '#3B384E',
    // over the driver's seat (the cabin's H-point (0.08, 0.36, 0.52) + 0.66 up, a little back)
    driverEye: [0.10, 0.36, 1.18],
    proxyUrl: '/models/denza-z9-proxy.glb',
  },
  configurator: {
    paintMaterial: 'M_Paint_Z9_Purple',
    paints: [
      {
        id: 'dark-night-purple',
        name: 'Dark Night Purple',
        nameZh: '暗夜紫',
        swatch: '#3B384E',
      },
      {
        id: 'starry-black',
        name: 'Starry Night Black',
        nameZh: '繁星黑',
        swatch: '#16171B',
        finish: { color: '#141518', roughness: 0.32, metalness: 0.08, clearcoat: 0.6 },
      },
      {
        id: 'aurora-silver',
        name: 'Aurora Silver',
        nameZh: '极光银',
        swatch: '#B9BFC8',
        finish: { color: '#B4BAC3', roughness: 0.36, metalness: 0.19, clearcoat: 0.45 },
      },
      {
        id: 'moonlight-white',
        name: 'Haoyue Pearl White',
        nameZh: '皓月白',
        swatch: '#ECEEF2',
        finish: { color: '#EAECEF', roughness: 0.35, metalness: 0.12, clearcoat: 0.5 },
      },
      {
        id: 'skyline-blue',
        name: 'Clear Sky Blue',
        nameZh: '晴空蓝',
        swatch: '#5E7691',
        finish: { color: '#566E89', roughness: 0.37, metalness: 0.18, clearcoat: 0.45 },
      },
    ],
    trims: [
      {
        id: 'pamir-brown',
        name: 'Pamir Brown Nappa',
        nameZh: '帕米尔棕',
        swatch: ['#232126', '#6E4730'],
      },
      {
        id: 'prague-red',
        name: 'Prague Red Nappa',
        nameZh: '布拉格红',
        swatch: ['#1E1C21', '#6D232A'],
        colors: {
          INT_Leather_Seat: '#74252d',
          INT_Leather_Dash: '#6a2229',
          INT_Leather_Door: '#6e2329',
          INT_Thread_Seat: '#b3535d',
          INT_Carpet_Mauve: '#2a1517',
        },
      },
      {
        id: 'cloud-purple',
        name: 'Cloud Purple & Porcelain',
        nameZh: '云烟紫',
        swatch: ['#4B4358', '#CFCAD6'],
        colors: {
          INT_Leather_Seat: '#d4cdd8',
          INT_Leather_Dash: '#5c5069',
          INT_Leather_Door: '#cfc8d4',
          INT_Thread_Seat: '#8d8199',
          INT_Carpet_Mauve: '#403848',
        },
      },
    ],
    wheels: [
      {
        id: 'multi-spoke-21',
        name: '21-inch Multi-Spoke Machined Alloy',
        nameZh: '21英寸多辐豪华精车轮毂',
        size: '21 in',
        tyres: '255/40 R21 · 275/40 R21',
        node: 'DenzaZ9_Wheels',
      },
    ],
    sources: [
      { label: 'Autohome — 腾势Z9 Configuration & Gallery (Series 7838)', url: 'https://www.autohome.com.cn/7838/' },
      { label: 'Denza Official — Z9 Executive Flagship Sedan', url: 'https://www.denza.com/' },
    ],
  },
  // The four doors swing on their leading edge (the hinge: mid height, on the skin; blender/scripts/z9_openings.py). The
  // node origins are the hinges, and the cabin's door cards turn about the same axes. The sign is the swing direction
  // (glTF y up): the left doors turn negative.
  openings: [
    { id: 'doorFL', node: 'DenzaZ9_Door_FL', cardNode: 'int_door_L', frameNode: 'DenzaZ9_DoorFrame_FL', deg: -72 },
    { id: 'doorFR', node: 'DenzaZ9_Door_FR', cardNode: 'int_door_R', frameNode: 'DenzaZ9_DoorFrame_FR', deg: 72 },
    { id: 'doorRL', node: 'DenzaZ9_Door_RL', cardNode: 'int_rdoor_L', frameNode: 'DenzaZ9_DoorFrame_RL', deg: -66 },
    { id: 'doorRR', node: 'DenzaZ9_Door_RR', cardNode: 'int_rdoor_R', frameNode: 'DenzaZ9_DoorFrame_RR', deg: 66 },
    // The bonnet hinges on a lateral axis under its rear edge at the cowl and stands about 76 deg open (c12_0001/2); two
    // thin gas struts hold it from the cowl's corners (c12_0064). The frunk under it is blender/scripts/z9_bays.py.
    {
      id: 'frunk',
      node: 'DenzaZ9_Bonnet',
      axis: 'z',
      deg: 76,
      struts: [
        { body: [1.05, 0.9, -0.7], moving: [1.3, 0.935, -0.7] },
        { body: [1.05, 0.9, 0.7], moving: [1.3, 0.935, 0.7] },
      ],
    },
    // The boot lid is the whole short rear above the bumper's top edge: the decklid, the upper tail, the gate and the middle of
    // the two lamps. It hangs from the backlight's base (blender/scripts/z9_gate.py) and swings up about 80 deg (Autohome
    // c3_0179/229/230, where two black swan-neck arms hold it: drawn here as two struts at the opening's front corners).
    // The cabin's liner turns with it.
    {
      id: 'boot',
      node: 'DenzaZ9_Tailgate',
      cardNode: 'int_tailgate',
      axis: 'z',
      deg: -80,
      struts: [
        { body: [-2.12, 0.93, -0.62], moving: [-2.4, 0.98, -0.62] },
        { body: [-2.12, 0.93, 0.62], moving: [-2.4, 0.98, 0.62] },
      ],
    },
  ],
  // The Tech tab (docs/tech-showcase.md, section 14). Every source below describes the Z9 GT, the shooting brake on the same
  // e³ platform: the showroom's Z9 is listed with the same two modes in its drive-mode list, but check that the sedan has them.
  sensors: {
    lidar: [0.65, 0.0, 1.45],
    cameras: [
      { at: [2.55, 0.0, 0.85] },
      { at: [0.65, 0.48, 1.42], mirror: true },
      { at: [1.05, 0.96, 0.96], mirror: true },
      { at: [-2.55, 0.0, 0.98] },
    ],
    ultrasonic: [
      { at: [2.50, 0.40, 0.42], mirror: true },
      { at: [-2.48, 0.42, 0.46], mirror: true },
    ],
    surround: true,
  },
  tech: [
    {
      id: 'crab',
      title: 'Crab walk',
      blurb:
        'Beside an empty stretch of kerb, all four wheels turn the same way and the car slides to the stone along a diagonal, without turning its body.',
      driver: 'crab',
      devices: ['phone', 'dashboard'],
      claims: [
        {
          text: 'Crab walk is one of the e³ platform’s five signature functions, with the compass turn, extreme steering, e³ parking and low-grip stabilisation; the platform pairs three motors driving independently with independent dual-motor rear-wheel steering.',
          source: { label: 'BYD China, 22 August 2024', url: 'https://www.byd.com/cn/news/2024/detail543' },
        },
        {
          text: 'The front and rear wheels turn the same way and the whole car moves diagonally. The rear wheels steer up to ±10°; with the rear motors’ differential, the crab angle reaches 15°.',
          source: { label: 'Xchuxing, Z9 GT drive', url: 'https://www.xchuxing.com/article/133019' },
        },
        {
          text: 'In use the front wheels should not be turned more than 15° nor the car driven faster than 20 km/h, and the centre screen shows a numeric indicator that keeps the driver from turning too far.',
          source: { label: 'km77, Denza Z9 GT first drive', url: 'https://www.km77.com/coches/denza/z9gt/informacion/denza-z9gt-2025-impresiones-de-conduccion' },
        },
      ],
      simulated:
        'A simulation. The angles are the published ones (front wheels 15°, rear wheels at their 10° limit); the street, the 2.25 m the car slides, its pace (7 km/h, inside the 20 km/h limit) and the screen are ours, and the sources describe the Z9 GT, which shares this platform.',
    },
    {
      id: 'compass',
      title: 'Compass turn',
      blurb:
        'Up a dead-end street, one front wheel is held still and the car turns about it, the rear wheels splayed and driven against each other, and drives out. Pick the wheel and the angle.',
      driver: 'compass',
      devices: ['dashboard'],
      claims: [
        {
          text: 'The compass turn is one of the e³ platform’s signature functions, alongside the crab walk and extreme steering; the car’s turning radius is 4.62 m.',
          source: { label: 'BYD China, 22 August 2024', url: 'https://www.byd.com/cn/news/2024/detail543' },
        },
        {
          text: 'It combines braking, torque vectoring and rear-wheel steering: one front wheel is locked as the pivot and the rear wheels, splayed outward, are driven in opposite directions so that the car turns about it, through any angle from 0 to 360° and about either front wheel.',
          source: { label: 'Xchuxing, Z9 GT drive', url: 'https://www.xchuxing.com/article/133019' },
        },
        {
          text: 'The car turns like a compass about one front wheel; Denza says the tyre wear from the manoeuvre is similar to that of a hard brake or hard acceleration.',
          source: { label: 'km77, Denza Z9 GT first drive', url: 'https://www.km77.com/coches/denza/z9gt/informacion/denza-z9gt-2025-impresiones-de-conduccion' },
        },
        {
          text: 'For parallel parking the driver pulls the nose into the space, chooses a front wheel to pivot about and turns an outline of the car on the screen; the inside rear wheel is driven forward and the outside one backward.',
          source: { label: 'The Autopian, Z9 GT parking', url: 'https://theautopian.com/denza-z9-gt-parking-2' },
        },
      ],
      simulated:
        'A simulation. The pivot, the splayed rear wheels (drawn at their published ±10°, so the tyres scrub sideways as they do on the car) and the angle choices are the maker’s; the dead-end street, its width (the sweep of the turn plus 40 cm each side), the pace and the screen are ours. The parallel-parking use of the turn is the next demonstration.',
    },
    {
      id: 'e3-parking',
      title: 'e³ parking',
      blurb:
        'Parallel parking into a gap hardly a metre longer than the car: the nose goes in, the car pivots about a front wheel, and the tail swings in behind it.',
      driver: 'e3park',
      devices: ['phone', 'dashboard'],
      claims: [
        {
          text: 'e³ parking is one of the e³ platform’s five signature functions; it combines the compass turn with smart parking for tight kerbside spaces and dead ends, and on the Z9 GT it was to arrive later by over-the-air update.',
          source: { label: 'Xchuxing, Z9 GT drive', url: 'https://www.xchuxing.com/article/133019' },
        },
        {
          text: 'For parallel parking the driver pulls the car’s nose into the space, chooses a front wheel to pivot about and turns an outline of the car on the screen; the car then slides its rear into the space, the inside rear wheel driven forward and the outside one backward, the rear steering helping.',
          source: { label: 'The Autopian, Z9 GT parking', url: 'https://theautopian.com/denza-z9-gt-parking-2' },
        },
        {
          text: 'The car turns like a compass about one of its front wheels (the function is called e³ parking); Denza says the tyre wear from the manoeuvre is similar to that of a hard brake or hard acceleration.',
          source: { label: 'km77, Denza Z9 GT first drive', url: 'https://www.km77.com/coches/denza/z9gt/informacion/denza-z9gt-2025-impresiones-de-conduccion' },
        },
      ],
      simulated:
        'A simulation. The steps (nose in, pivot about a front wheel, tail swings in) are described by the sources; the gap (a metre longer than the car), the 30° the car is angled to the kerb, the 40 cm it ends from the stone, the pace and the screen are ours: no published figure says how tight a gap the car can take. The outline you turn on the real car’s screen is not drawn; the pivot is the left front wheel and the car chooses the angle.',
    },
  ],
  // The DC socket's mouth (the left rear quarter, behind the wheel: our estimate of the side and the place, snapped to the
  // model's skin by a ray) and the direction out of it, in the viewer's axes. The model has no flap, so the Charging tab
  // draws a socket here.
  chargePort: { mouth: [-1.7, 0.95, -0.9326], axis: [-0.048, 0.4129, -0.9095], depth: 0.02 },
  // The Charging tab (docs/tech-showcase.md section 11). The 10 to 80 % time is the figure in this file's variants (the
  // Autohome configuration table); NOT confirmed against the maker, and the Z9 GT's flash charging (1,000 V, about
  // 1 MW) is another car's and is not used.
  charging: {
    window: { from: 10, to: 80, minutes: 19 },
    packKwh: 100,
    architectureV: 800,
    connector: 'GB/T',
    port: { side: 'left', published: false, where: 'Left rear quarter (our choice: no source gives it)' },
    claims: [
      {
        text: 'The configuration table lists the Z9’s pack and its fast-charge time from 10 to 80 %.',
        source: { label: 'Autohome — 腾势Z9 Specifications (Series 7838)', url: 'https://www.autohome.com.cn/7838/' },
      },
    ],
    simulated:
      'A simulation. The 19 minutes from 10 to 80 % is the configuration table’s; no peak power is published for this car, so the peak is derived from the window’s average power and the curve is ours. No source says which side the charge port is on, and the model has none: the socket is drawn on the left rear quarter at a place we chose, and the pedestal and the gun (styled on a generic charging connector, not Denza’s or any maker’s) are ours. Nineteen minutes play in fourteen seconds.',
  },
  sources: [
    { label: 'Autohome — 腾势Z9 Specifications (Series 7838)', url: 'https://www.autohome.com.cn/7838/' },
    { label: 'Denza Official — Z9 Executive Flagship Sedan', url: 'https://www.denza.com/' },
  ],
};
