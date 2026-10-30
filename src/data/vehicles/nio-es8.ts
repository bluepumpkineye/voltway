import type { Vehicle } from './schema';

export const nioEs8: Vehicle = {
  slug: 'nio-es8',
  brand: 'Nio',
  model: 'ES8',
  group: 'NIO',
  bodyStyle: 'SUV',
  year: 2025,
  tagline: 'Flagship smart electric 6-seater SUV with Banyan System and 3-minute Power Swap.',
  summary:
    'NIO’s 5,280 mm flagship luxury electric SUV built on the second-generation NT 2.0 platform. Powered by a 520 kW dual-motor intelligent AWD system launching from 0-100 km/h in 3.97s, it features an ultra-long 3,130 mm wheelbase, executive Zero-Gravity Lounge seating, intelligent dual-chamber air suspension, Banyan Smart Cockpit with NOMI Mate 2.0, and Aquila Super Sensing with roof Watchtower LiDAR.',
  dimensions: {
    lengthMm: 5280,
    widthMm: 2010,
    heightMm: 1800,
    wheelbaseMm: 3130,
    kerbWeightKg: 2560,
  },
  variants: [
    {
      id: '100kwh-executive-flagship-awd',
      name: '100 kWh Executive Flagship AWD',
      drive: 'AWD',
      battery: {
        capacityKwh: 100,
        chemistry: 'NMC',
        swappable: true,
        architectureV: 400,
        chargeMinutes10to80: 20,
      },
      performance: {
        powerKw: 520,
        torqueNm: 700,
        zeroTo100S: 3.97,
        motorCount: 2,
        topSpeedKmh: 200,
      },
      range: [{ cycle: 'CLTC', km: 605 }],
      priceCny: 446800,
    },
    {
      id: '75kwh-executive-awd',
      name: '75 kWh Executive AWD',
      drive: 'AWD',
      battery: {
        capacityKwh: 75,
        chemistry: 'NMC',
        swappable: true,
        architectureV: 400,
        chargeMinutes10to80: 20,
      },
      performance: {
        powerKw: 520,
        torqueNm: 700,
        zeroTo100S: 3.97,
        motorCount: 2,
        topSpeedKmh: 200,
      },
      range: [{ cycle: 'CLTC', km: 465 }],
      priceCny: 406800,
    },
  ],
  cockpit: {
    os: 'Banyan Smart Cockpit',
    skin: 'banyan',
    accentColor: '#00C2A8',
    ambientLighting: true,
    ambientHue: 172,
    defaultTheme: 'dark',
    driveModes: [
      { id: 'comfort', label: 'Comfort', native: '舒适', group: 'street', model: 'comfort' },
      { id: 'eco', label: 'Eco', native: '节能', group: 'street', model: 'eco' },
      { id: 'sport', label: 'Sport', native: '运动', group: 'street', model: 'sport' },
      { id: 'sport_plus', label: 'Sport+', native: '运动+', group: 'special', model: 'sport' },
      { id: 'snow', label: 'Snow', native: '雪地', group: 'special', model: 'comfort' },
      { id: 'sand', label: 'Sand', native: '沙地', group: 'special', model: 'comfort' },
      { id: 'wet', label: 'Wet / Slippery', native: '湿地', group: 'special', model: 'comfort' },
    ],
    screens: [
      { id: 'center', label: '15.6" AMOLED Central Display', diagonalIn: 15.6, role: 'center', interactive: true },
      { id: 'cluster', label: '10.2" HDR Digital Instrument Cluster', diagonalIn: 10.2, role: 'cluster' },
    ],
  },
  assets: {
    modelUrl: '/models/nio-es8.glb',
    showroomOnly: true,
    studioShadow: {
      url: '/models/nio-es8-shadow.webp',
      size: [8.60, 5.20],
      centre: [0.0, 0.0],
    },
    interiorModelUrl: '/models/nio-es8-interior.glb',
    // lit by the shared showroom hall, shaded by the cabin's occlusion atlas (docs/3d-pipeline.md, "The hall look")
    interiorProbeUrl: '/models/cabin-hall.hdr',
    outside: {
      view: '/models/nio-es8-outside.jpg',
      light: '/models/nio-es8-outside-light.hdr',
      exteriorTurnDeg: 189,
      sun: { direction: [0.65, 0.45, 0.61], color: '#fff5e6', intensity: 2.8 },
      ground: { height: -0.380, radius: 24.0 },
    },
    driverEye: [0.00, 0.41, 1.25],
    proxyUrl: '/models/nio-es8-proxy.glb',
    heroColor: '#3E4A57',
  },
  configurator: {
    paintMaterial: 'M_Paint_ES8_StarlightGrey',
    paints: [
      {
        id: 'starlight-grey',
        name: 'Starlight Grey',
        nameZh: '星澜灰',
        swatch: '#3E4A57',
        finish: { color: '#323b46', roughness: 0.28, metalness: 0.50, clearcoat: 1, clearcoatRoughness: 0.03 },
      },
      {
        id: 'cloud-white',
        name: 'Cloud White',
        nameZh: '云白',
        swatch: '#F2F4F7',
        finish: { color: '#e8ebf0', roughness: 0.26, metalness: 0.20, clearcoat: 1, clearcoatRoughness: 0.03 },
      },
      {
        id: 'deep-black',
        name: 'Deep Black',
        nameZh: '深空黑',
        swatch: '#141518',
        finish: { color: '#0c0d0f', roughness: 0.20, metalness: 0.15, clearcoat: 1, clearcoatRoughness: 0.03 },
      },
      {
        id: 'southern-star-blue',
        name: 'Southern Star Blue',
        nameZh: '南极星蓝',
        swatch: '#1E3A5F',
        finish: { color: '#152a45', roughness: 0.28, metalness: 0.60, clearcoat: 1, clearcoatRoughness: 0.03 },
      },
      {
        id: 'arctic-green',
        name: 'Arctic Green',
        nameZh: '极光绿',
        swatch: '#2B443B',
        finish: { color: '#1e322b', roughness: 0.28, metalness: 0.55, clearcoat: 1, clearcoatRoughness: 0.03 },
      },
      {
        id: 'sunlit-gold',
        name: 'Sunlit Gold',
        nameZh: '宇航金',
        swatch: '#A8987E',
        finish: { color: '#8e8068', roughness: 0.28, metalness: 0.65, clearcoat: 1, clearcoatRoughness: 0.03 },
      },
      {
        id: 'dawn-red',
        name: 'Dawn Orange',
        nameZh: '霞光橙',
        swatch: '#8C3A27',
        finish: { color: '#752f1e', roughness: 0.28, metalness: 0.55, clearcoat: 1, clearcoatRoughness: 0.03 },
      },
    ],
    trims: [
      {
        id: 'pamir-brown',
        name: 'Pamir Brown',
        nameZh: '帕米尔棕',
        swatch: ['#523626', '#261912'],
        colors: { INT_Leather_White: '#523626', INT_Leather_Brown: '#523626' },
      },
      {
        id: 'onyx-black',
        name: 'Onyx Black',
        nameZh: '曜石黑',
        swatch: ['#18191c', '#2b2d30'],
        colors: { INT_Leather_White: '#18191c', INT_Leather_Brown: '#18191c' },
      },
      {
        id: 'glacier-white',
        name: 'Glacier White',
        nameZh: '极光白',
        swatch: ['#e8ebf0', '#b5bac2'],
        colors: { INT_Leather_White: '#e8ebf0', INT_Leather_Brown: '#b5bac2' },
      },
      {
        id: 'tech-grey',
        name: 'Tech Grey',
        nameZh: '科技灰',
        swatch: ['#4a4e54', '#2a2c30'],
        colors: { INT_Leather_White: '#4a4e54', INT_Leather_Brown: '#2a2c30' },
      },
    ],
    // The all-new ES8 is shown on two 22 in wheels, both from photographs (Autohome series 4427, the maker's own close-up):
    // the standard twenty-opening diamond-cut wheel with red calipers on the Signature and Luxury cars, and the Lanyue
    // pack's mirror-polished forged wheel with Dawn Gold calipers (曙光金). Calipers are the maker's two colours.
    caliperMaterial: 'M_Caliper_Nio_Red',
    calipers: [
      { id: 'red', name: 'Red', nameZh: '红色', color: '#a61d1a' },
      { id: 'gold', name: 'Dawn Gold', nameZh: '曙光金', color: '#c99a3a' },
    ],
    wheels: [
      {
        id: 'multi-22',
        name: '22" Twenty-Spoke Diamond-Cut',
        nameZh: '22英寸二十辐切削轮圈',
        size: '22"',
        tyres: '265/40 R22',
        node: 'NioES8_Wheels',
        caliper: 'red',
      },
      {
        id: 'lanyue',
        name: '22" Lanyue Forged Mirror-Polished',
        nameZh: '22英寸锻造揽月轮圈',
        size: '22"',
        tyres: '265/40 R22',
        node: 'NioES8_Lanyue_Wheels',
        caliper: 'gold',
      },
    ],
    sources: [
      { label: 'NIO Official Website - All-New ES8', url: 'https://www.nio.cn/es8' },
      { label: 'Autohome - NIO ES8 Specifications & Wheel Catalog (Series 3954)', url: 'https://www.autohome.com.cn/3954/' },
    ],
  },
  openings: [
    { id: 'doorFL', node: 'NioES8_Door_FL', cardNode: 'int_door_L', frameNode: 'NioES8_DoorFrame_FL', deg: -72, xrayHide: true },
    { id: 'doorFR', node: 'NioES8_Door_FR', cardNode: 'int_door_R', frameNode: 'NioES8_DoorFrame_FR', deg: 72, xrayHide: true },
    { id: 'doorRL', node: 'NioES8_Door_RL', cardNode: 'int_rdoor_L', frameNode: 'NioES8_DoorFrame_RL', deg: -66, xrayHide: true },
    { id: 'doorRR', node: 'NioES8_Door_RR', cardNode: 'int_rdoor_R', frameNode: 'NioES8_DoorFrame_RR', deg: 66, xrayHide: true },
    {
      id: 'frunk',
      node: 'NioES8_Bonnet',
      axis: 'z',
      deg: 62,
    },
    {
      id: 'boot',
      node: 'NioES8_Tailgate',
      cardNode: 'int_tailgate',
      axis: 'z',
      deg: -78,
      hides: ['int_parcel_shelf', 'int_rear_sill'],
    },
  ],
  xray: { node: 'NioES8_Greenhouse', color: '#98a4b3', opacity: 0.34, hideCabin: ['int_headliner'] },
  lights: { projector: {} },
  sensors: {
    lidar: [0.55, 0.0, 1.76],
    sideLidar: [1.18, 0.94, 0.92],
    rearLidar: [-2.56, 0.0, 1.08],
    cameras: [
      { at: [2.62, 0.0, 0.92] },
      { at: [0.55, 0.52, 1.74], mirror: true },
      { at: [0.95, 0.96, 1.02], mirror: true },
      { at: [-2.56, 0.0, 1.08] },
      { at: [-2.18, 0.0, 1.62] },
    ],
    ultrasonic: [
      { at: [2.55, 0.42, 0.48], mirror: true },
      { at: [-2.52, 0.44, 0.51], mirror: true },
    ],
    surround: true,
  },
  chargePort: { mouth: [-1.835, 0.963, -0.912], axis: [-0.028, 0.257, -0.966], depth: 0.022 },
  charging: {
    window: { from: 10, to: 80, minutes: 20 },
    packKwh: 100,
    peakKw: 250,
    architectureV: 400,
    connector: 'GB/T',
    port: { side: 'left', published: true, where: 'Left rear quarter' },
    claims: [
      {
        text: 'Supports NIO Power Swap 3.0 station automated battery swapping in under 3 minutes, as well as 500 kW ultra-fast DC charging.',
        source: { label: 'NIO Official', url: 'https://www.nio.cn/es8' },
      },
    ],
    simulated: 'A simulation of NIO Power Swap battery swapping and high-speed DC charging.',
  },
  tech: [
    {
      id: 'primeride-4d',
      title: 'PrimeRide · Lane-Level 4D Smart Suspension',
      blurb:
        'Aquila LiDAR and camera road preview scans bumps ahead, while dual-chamber air springs and CDC dampers proactively adjust damping 500 times per second for a serene ride.',
      driver: 'carpet',
      devices: ['dashboard'],
      claims: [
        {
          text: 'The NIO PrimeRide intelligent chassis integrates intelligent dual-chamber air suspension with Continuous Damping Control (CDC®) and Lane-Level 4D Smart Suspension.',
          source: { label: 'NIO Official Website - All-New ES8', url: 'https://www.nio.com/es8' },
        },
        {
          text: 'Intelligent dual-chamber air suspension provides a total height adjustment range of 100 mm across 5 levels (+50 mm, +25 mm, 0 mm, -15 mm, -50 mm) and modulates air spring stiffness.',
          source: { label: 'NIO Official Website - All-New ES8', url: 'https://www.nio.com/es8' },
        },
        {
          text: 'Continuous Damping Control (CDC®) actively monitors chassis dynamics and adjusts damper valves up to 500 times per second in real time.',
          source: { label: 'NIO Official Website - All-New ES8', url: 'https://www.nio.com/es8' },
        },
        {
          text: 'Lane-Level 4D Smart Suspension leverages Aquila roof LiDAR, 8MP front cameras, and cloud road surface maps to predict road bumps up to 150 m ahead and prep the suspension.',
          source: { label: 'NIO Official Website - All-New ES8', url: 'https://www.nio.com/es8' },
        },
      ],
      simulated:
        'A simulation of speed hump traversal at 16 km/h. Toggle between PrimeRide 4D proactive damping and passive suspension to observe real-time body pitch and heave control. 5-level 100 mm air height adjustment and Easy Entry kneeling are interactive.',
    },
    {
      id: 'primeride-agility',
      title: 'PrimeRide · Front & Rear 5-Link Agility',
      blurb:
        'All-aluminum front virtual-kingpin and rear five-link suspension architecture enables exceptional wheel articulation for a tight 5.7 m turning radius in an executive flagship SUV.',
      driver: 'uturn',
      devices: ['dashboard'],
      params: { radiusM: 5.7, rearMaxDeg: 0 },
      claims: [
        {
          text: 'The all-new ES8 features front and rear five-link independent suspensions crafted with high-strength forged aluminum alloy.',
          source: { label: 'NIO Official Website - All-New ES8', url: 'https://www.nio.com/es8' },
        },
        {
          text: 'Front dual-wishbone / five-link geometry with virtual kingpins decouples steering from suspension loads, achieving an ultra-tight turning radius of 5.7 meters.',
          source: { label: 'Autohome - NIO ES8 Specifications', url: 'https://www.autohome.com.cn/' },
        },
      ],
      simulated:
        'A simulation of a 5.7 m radius street U-turn demonstrating front virtual-kingpin steering articulation. The street width, trajectory sweep, and real-time wheel angle telemetry are rendered live.',
    },
    {
      id: 'primeride-launch',
      title: 'PrimeRide · CDC® Anti-Pitch Launch',
      blurb:
        'Standing start launch from 0 to 100 km/h in 3.97 s: 480 kW dual motors unleash 850 N·m as CDC electronic damping stiffens to eliminate rear squat and nose lift.',
      driver: 'launch',
      devices: ['dashboard'],
      claims: [
        {
          text: 'Dual-motor intelligent all-wheel drive with 180 kW permanent magnet front motor and 300 kW induction rear motor delivers 480 kW (653 PS) and 850 N·m of peak torque.',
          source: { label: 'NIO Official Website - All-New ES8', url: 'https://www.nio.com/es8' },
        },
        {
          text: 'Accelerates from 0 to 100 km/h in 3.97 seconds, backed by high-performance 6-piston Brembo front calipers achieving 100-0 km/h braking in 34.3 meters.',
          source: { label: 'NIO Official Website - All-New ES8', url: 'https://www.nio.com/es8' },
        },
        {
          text: 'CDC® active damping works in synergy with torque vectoring to suppress longitudinal pitch and squat under maximum acceleration.',
          source: { label: 'NIO Official Website - All-New ES8', url: 'https://www.nio.com/es8' },
        },
      ],
      simulated:
        'A simulation of 0-100 km/h acceleration in 3.97 s on a rolling treadmill. CDC anti-squat pitch stabilization and G-force curves are calculated from published vehicle dynamics.',
    },
    {
      id: 'aquila',
      title: 'Aquila Super Sensing & ADAM',
      blurb:
        'Watchtower sensor layout featuring ultra-long-range 1550nm roof LiDAR, 8MP high-resolution cameras, and 1,016 TOPS computing power.',
      driver: 'sensors',
      scenario: 'overtake',
      claims: [
        {
          text: 'Aquila Super Sensing system integrates 33 high-performance sensing units including roof LiDAR and 8MP cameras.',
          source: { label: 'NIO Official', url: 'https://www.nio.cn/es8' },
        },
        {
          text: 'ADAM Supercomputing platform carries 4 NVIDIA DRIVE Orin X chips with a total computing power of 1,016 TOPS.',
          source: { label: 'NIO Official', url: 'https://www.nio.cn/es8' },
        },
      ],
      simulated: 'Simulated visualization of NIO Aquila Watchtower LiDAR and surround sensing fields in multi-lane traffic.',
    },
    {
      id: 'park',
      title: 'Remote Parking Assist · RPA',
      blurb:
        'Aquila Super Sensing with roof Watchtower LiDAR and 12 ultrasonic radars scans surroundings to autonomously steer, brake, and slide into narrow bays while controlled from the NIO mobile app.',
      driver: 'park',
      devices: ['phone', 'dashboard'],
      params: { search: 12 },
      claims: [
        {
          text: 'NIO Remote Parking Assist (RPA) enables drivers to stand outside the vehicle and park the ES8 into tight perpendicular, parallel, and diagonal parking bays via the NIO App.',
          source: { label: 'NIO Official - Banyan Smart System', url: 'https://www.nio.cn/es8' },
        },
        {
          text: 'Aquila 33-sensor array with ultralong-range roof LiDAR and 360-degree ultrasonic sensing maps the parking environment and spots free bays in real time.',
          source: { label: 'NIO Official - ES8 Specifications', url: 'https://www.nio.cn/es8' },
        },
      ],
      simulated:
        'A simulation of autonomous reverse-in parking. Watchtower LiDAR and surround cameras screen for available bays, lock onto the target slot with flashing indicators, and complete precise maneuvers while synchronized with the mobile app and dashboard.',
    },

    {
      id: 'nomi',
      title: 'NOMI Mate 2.0 AI Companion',
      blurb:
        'In-car emotional artificial intelligence with circular AMOLED display, expressive digital personality, and full voice control.',
      driver: 'swivel',
      view: 'cabin',
      claims: [
        {
          text: 'NOMI Mate 2.0 brings the smart cockpit alive with a circular AMOLED display and real-time emotive animations.',
          source: { label: 'NIO Official', url: 'https://www.nio.cn/es8' },
        },
      ],
      simulated: 'Cockpit view highlighting the NOMI Mate AI companion on the dashboard center.',
    },
  ],
  // The Drive tab's scenario (docs/tech-showcase.md section 19). The 100-0 distance is the 34.3 m of the 'primeride-launch' demo
  // above (NIO's page); the 480 kW and 850 N·m in that demo's text disagree with this file's 520 kW and 700 N·m and are left alone.
  drive: {
    id: 'reserve-power',
    title: 'Refined Reserve Power',
    blurb:
      'A strong, quiet pull and a surge from 80 to 140 km/h in a 5.3 m SUV, then a hard stop: little pitch, a great deal in reserve. Load it with a family and luggage and see what changes.',
    runs: [{ from: 80, to: 140 }],
    modes: ['eco', 'comfort', 'sport'],
    defaultMode: 'sport',
    loads: [
      { id: 'driver', label: 'Driver', payloadKg: 75 },
      { id: 'family', label: 'Five + luggage', payloadKg: 475 },
    ],
    overlays: ['suspension', 'brake', 'energy'],
    finish: 'brake',
    brake100M: 34.3,
    chassis: { airSuspension: true, squatDegPerG: 0.7 },
    ghost: { slug: 'denza-z9', variantId: '630-max-awd' },
    camera: 'hero',
    callouts: [
      { cue: 'launch', text: 'Launch. The damping stiffens against squat: the tail drops less than the pull alone would make it.' },
      { cue: 'target', text: 'Off the power, then the brakes.' },
      { cue: 'brake', text: 'Hard stop from the run’s speed. The motors recover some of the energy; the friction brakes do the rest.' },
    ],
    claims: [
      {
        text: '100–0 km/h braking in 34.3 m, with 6-piston Brembo front calipers.',
        source: { label: 'NIO Official Website, All-New ES8', url: 'https://www.nio.com/es8' },
      },
      {
        text: 'CDC® active damping works in synergy with torque vectoring to suppress longitudinal pitch and squat under maximum acceleration.',
        source: { label: 'NIO Official Website, All-New ES8', url: 'https://www.nio.com/es8' },
      },
      {
        text: 'Intelligent dual-chamber air suspension with Continuous Damping Control (CDC®) and a 100 mm height range across 5 levels.',
        source: { label: 'NIO Official Website, All-New ES8', url: 'https://www.nio.com/es8' },
      },
    ],
    simulated:
      'The 80–140 run, how much pitch the damping removes (0.7° per g, against 1.1° for a generic SUV), the load (five and luggage, 475 kg), the brake blend and the energy are ours.',
  },
  sources: [
    { label: 'NIO Official - All-New ES8', url: 'https://www.nio.cn/es8' },
    { label: 'Autohome - NIO ES8 Specs', url: 'https://www.autohome.com.cn/' },
  ],
};
