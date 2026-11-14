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
      // The Pro and Max trims' 20 in wheel (Autohome series 7838, specs 69563 / 69564; the tyre reads 255/45 R20 in the
      // photographs): six machined Y spokes. Traced from the rear wheel of imgs-7838-69563-1-x/10963307.
      {
        id: 'six-y-20',
        name: '20-inch Six-Y-Spoke Machined Alloy',
        nameZh: '20英寸六辐Y形精车轮毂',
        size: '20 in',
        tyres: '255/45 R20',
        node: 'DenzaZ9_Pro_Wheels',
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
  xray: {
    node: 'DenzaZ9_Greenhouse',
    color: '#98a4b3',
    opacity: 0.34,
    hideCabin: ['int_headliner'],
    anatomy: {
      url: '/models/denza-z9-xray.glb',
      note: "The X-ray view's parts are our own models, placed from the car's dimensions and Denza's published e³ (易三方) tri-motor, CTB Blade Battery and dual-motor rear-wheel steering layout. Figures on a card are Denza's or Autohome's where stated; the shapes of the castings, cells and gears are illustrative.",
      parts: [
        {
          id: 'battery',
          system: 'battery',
          title: '100 kWh e³ CTB Blade Battery pack',
          nodes: ['XR_Battery_Tray', 'XR_Battery_Lid', 'XR_Battery_Busbars', 'XR_Battery_Film'],
          basis: 'published',
          text: "Denza's 100 kWh LFP Blade Battery pack is integrated into the e³ (易三方) platform floor using Cell-to-Body (CTB) architecture, where the pack lid serves directly as the cabin floor to maximise rear-cabin legroom and structural stiffness.",
          facts: [
            { label: 'Capacity', value: '100 kWh' },
            { label: 'Chemistry', value: 'BYD LFP Blade Battery (LiFePO₄)' },
            { label: 'Integration', value: 'e³ CTB (Cell-to-Body) structural pack' },
            { label: 'CLTC range', value: 'Up to 630 km' },
          ],
          source: { label: 'Autohome — 腾势Z9 Specifications (Series 7838)', url: 'https://www.autohome.com.cn/7838/' },
        },
        {
          id: 'cells',
          system: 'battery',
          title: 'Transverse LFP Blade cell array',
          nodes: [
            'XR_Battery_Cells_01', 'XR_Battery_Cells_02', 'XR_Battery_Cells_03', 'XR_Battery_Cells_04',
            'XR_Battery_Cells_05', 'XR_Battery_Cells_06', 'XR_Battery_Cells_07', 'XR_Battery_Cells_08',
            'XR_Battery_Cells_09', 'XR_Battery_Cells_10', 'XR_Battery_Cells_11', 'XR_Battery_Cells_12',
          ],
          basis: 'published',
          clip: 'battery',
          text: 'Full-width transverse LFP Blade cells packed without intermediate module enclosures, acting as structural cross-beams between the side sills.',
          facts: [
            { label: 'Cell layout', value: 'Transverse sill-to-sill Blade array' },
          ],
          source: { label: 'BYD China — e³ Platform Launch, 22 August 2024', url: 'https://www.byd.com/cn/news/2024/detail543' },
        },
        {
          id: 'cooling',
          system: 'battery',
          title: 'Dual-layer direct refrigerant thermal plate',
          nodes: ['XR_Battery_Plate'],
          basis: 'published',
          text: 'Direct refrigerant cooling and heating plates regulate the Blade Battery across extreme temperatures and sustain high-current dual-gun fast charging.',
          facts: [
            { label: 'Thermal management', value: 'Direct refrigerant cooling & pulse self-heating' },
          ],
          source: { label: 'Denza Official — Z9 Executive Flagship Sedan', url: 'https://www.denza.com/' },
        },
        {
          id: 'pdu',
          system: 'battery',
          title: '800 V dual-gun supercharging junction box',
          nodes: ['XR_Battery_PDU', 'XR_Battery_RearPort'],
          basis: 'published',
          text: 'High-voltage distribution unit feeding all three e³ inverters and supporting 800 V dual-gun DC fast charging from 10 % to 80 % in 19 minutes.',
          facts: [
            { label: '10 to 80 % DC charge', value: '19 min' },
            { label: 'Architecture', value: '800 V high-voltage platform' },
          ],
          source: { label: 'Autohome — 腾势Z9 Specifications (Series 7838)', url: 'https://www.autohome.com.cn/7838/' },
        },
        {
          id: 'rear-drive',
          system: 'drive',
          title: 'e³ twin rear permanent-magnet motors (2 × 240 kW)',
          nodes: ['XR_Drive_RL', 'XR_Drive_RR'],
          basis: 'published',
          clip: 'rotor',
          text: 'Two independent 240 kW permanent-magnet synchronous motors sit coaxially on the rear axle, each driving one rear wheel directly. During a compass turn or e³ parking, the inside rear motor drives forward while the outside rear motor drives in reverse.',
          facts: [
            { label: 'Power per motor', value: '240 kW × 2 (480 kW rear total)' },
            { label: 'Torque per motor', value: '360 N·m × 2' },
            { label: 'Control', value: 'Independent left/right torque vectoring & counter-rotation' },
          ],
          source: { label: 'BYD China — e³ Platform Launch, 22 August 2024', url: 'https://www.byd.com/cn/news/2024/detail543' },
        },
        {
          id: 'front-drive',
          system: 'drive',
          title: 'e³ front 230 kW AC asynchronous motor',
          nodes: ['XR_Drive_F'],
          basis: 'published',
          clip: 'rotor',
          text: 'A 230 kW / 430 N·m AC induction motor on the front axle pairs with the twin rear units for a combined 710 kW (965 PS) and 1,150 N·m, accelerating the 5.22-metre flagship sedan from 0 to 100 km/h in 3.4 seconds.',
          facts: [
            { label: 'Front peak power', value: '230 kW (313 PS) · 430 N·m' },
            { label: 'Combined tri-motor output', value: '710 kW (965 PS) · 1,150 N·m' },
            { label: '0–100 km/h', value: '3.4 s' },
          ],
          source: { label: 'Autohome — 腾势Z9 Specifications (Series 7838)', url: 'https://www.autohome.com.cn/7838/' },
        },
        {
          id: 'rotor',
          system: 'drive',
          title: 'High-speed rotors & flat-wire stators',
          nodes: [
            'XR_Drive_RL_Rotor', 'XR_Drive_RR_Rotor', 'XR_Drive_F_Rotor',
            'XR_Drive_RL_Stator', 'XR_Drive_RR_Stator', 'XR_Drive_F_Stator',
          ],
          basis: 'published',
          clip: 'rotor',
          text: 'Oil-cooled flat-wire stators and high-speed rotors across all three drive units allow continuous high-power output and 240 km/h top speed.',
          facts: [
            { label: 'Top speed', value: '240 km/h' },
          ],
          source: { label: 'Autohome — 腾势Z9 Specifications (Series 7838)', url: 'https://www.autohome.com.cn/7838/' },
        },
        {
          id: 'inverter',
          system: 'drive',
          title: '800 V silicon-carbide (SiC) tri-motor inverters',
          nodes: ['XR_Drive_RL_Inverter', 'XR_Drive_RR_Inverter', 'XR_Drive_F_Inverter'],
          basis: 'published',
          text: 'Three independent SiC power inverters coordinated by BYD’s Xuanji (璇玑) architecture adjust wheel torque in milliseconds for low-grip stability and tyre-blowout control at up to 140 km/h.',
          facts: [
            { label: 'Power electronics', value: '800 V SiC MOSFET × 3' },
            { label: 'Vehicle brain', value: 'Xuanji (璇玑) VMC coordination' },
          ],
          source: { label: 'BYD China — e³ Platform Launch, 22 August 2024', url: 'https://www.byd.com/cn/news/2024/detail543' },
        },
        {
          id: 'reducer',
          system: 'drive',
          title: 'Twin-rear planetary & front helical gearsets',
          nodes: [
            'XR_Drive_RL_Reducer', 'XR_Drive_RL_Gears', 'XR_Drive_RL_Pinion',
            'XR_Drive_RR_Reducer', 'XR_Drive_RR_Gears', 'XR_Drive_RR_Pinion',
            'XR_Drive_F_Reducer', 'XR_Drive_F_Gears', 'XR_Drive_F_Pinion',
          ],
          basis: 'illustrative',
          clip: 'rotor',
          text: 'Compact coaxial planetary gearsets on the twin rear motors leave space between the rear hubs for both motors and the dual rear-steering actuators.',
        },
        {
          id: 'subframes',
          system: 'chassis',
          title: 'e³ front & rear subframes',
          nodes: ['XR_Frame_SubF', 'XR_Frame_SubR', 'XR_Frame_CrashF', 'XR_Frame_CrashR'],
          basis: 'published',
          text: 'High-rigidity front and rear subframes engineered to cradle the twin rear drive units and dual rear-wheel steering actuators within a 3,125 mm wheelbase.',
          facts: [
            { label: 'Wheelbase', value: '3,125 mm' },
            { label: 'Length × Width', value: '5,220 × 1,990 mm' },
          ],
          source: { label: 'Autohome — 腾势Z9 Specifications (Series 7838)', url: 'https://www.autohome.com.cn/7838/' },
        },
        {
          id: 'floor',
          system: 'chassis',
          title: 'CTB structural floor & side sills',
          nodes: ['XR_Frame_Floor'],
          basis: 'published',
          text: 'Extruded aluminium side sills and cross-members bonded to the CTB Blade Battery pack form the primary load path along the cabin floor.',
          source: { label: 'Denza Official — Z9 Executive Flagship Sedan', url: 'https://www.denza.com/' },
        },
        {
          id: 'wishbones',
          system: 'suspension',
          title: 'Front double-wishbone & rear five-link suspension',
          nodes: [
            'XR_Susp_FL_UpperArm', 'XR_Susp_FL_LowerArm', 'XR_Susp_FR_UpperArm', 'XR_Susp_FR_LowerArm',
            'XR_Susp_RL_UpperArm', 'XR_Susp_RL_LowerArm', 'XR_Susp_RR_UpperArm', 'XR_Susp_RR_LowerArm',
            'XR_Susp_FL_Knuckle', 'XR_Susp_FR_Knuckle', 'XR_Susp_RL_Knuckle', 'XR_Susp_RR_Knuckle',
          ],
          basis: 'published',
          clip: 'suspension',
          text: 'Forged-aluminium front double-wishbone and rear five-link independent suspension geometry designed to accommodate ±10° of rear-wheel steering angle.',
          facts: [
            { label: 'Front', value: 'Double wishbone, forged aluminium' },
            { label: 'Rear', value: 'Five-link with active rear-steer knuckles' },
          ],
          source: { label: 'Autohome — 腾势Z9 Specifications (Series 7838)', url: 'https://www.autohome.com.cn/7838/' },
        },
        {
          id: 'springs',
          system: 'suspension',
          title: 'DiSus-A (云辇-A) dual-chamber air suspension & CDC',
          nodes: [
            'XR_Susp_FL_Spring', 'XR_Susp_FL_Damper', 'XR_Susp_FL_Rod',
            'XR_Susp_FR_Spring', 'XR_Susp_FR_Damper', 'XR_Susp_FR_Rod',
            'XR_Susp_RL_Spring', 'XR_Susp_RL_Damper', 'XR_Susp_RL_Rod',
            'XR_Susp_RR_Spring', 'XR_Susp_RR_Damper', 'XR_Susp_RR_Rod',
          ],
          basis: 'published',
          clip: 'suspension',
          text: 'BYD’s DiSus-A intelligent air body control system pairs dual-chamber air springs with continuously variable CDC electromagnetic dampers to adjust ride height, stiffness and pitch in real time.',
          facts: [
            { label: 'Air suspension', value: 'DiSus-A (云辇-A) dual-chamber air springs' },
            { label: 'Dampers', value: 'Continuously variable CDC dampers' },
          ],
          source: { label: 'Autohome — 腾势Z9 Specifications (Series 7838)', url: 'https://www.autohome.com.cn/7838/' },
        },
        {
          id: 'arb',
          system: 'suspension',
          title: 'Anti-roll bars & tri-motor half-shafts',
          nodes: [
            'XR_Susp_ARB_F', 'XR_Susp_ARB_R',
            'XR_Susp_FL_Halfshaft', 'XR_Susp_FR_Halfshaft', 'XR_Susp_RL_Halfshaft', 'XR_Susp_RR_Halfshaft',
          ],
          basis: 'illustrative',
          text: 'Front and rear anti-roll bars and high-angle constant-velocity half-shafts transmitting up to 1,150 N·m to the four hubs.',
        },
        {
          id: 'rack',
          system: 'steering',
          title: 'Front rack & e³ independent dual-motor rear-wheel steering (±10°)',
          nodes: [
            'XR_Steering_Rack', 'XR_Steering_RearRack',
            'XR_Susp_FL_TieRod', 'XR_Susp_FR_TieRod',
            'XR_Susp_RL_ToeLink', 'XR_Susp_RR_ToeLink',
          ],
          basis: 'published',
          clip: 'steering',
          text: 'The e³ platform pairs the front electric steering rack with two independent rear-axle steering actuators that can steer the rear wheels up to ±10° in phase (for a 15° crab walk), counter-phase (for a 4.62 m turning radius), or splayed inward/outward (for compass turns and e³ parking).',
          facts: [
            { label: 'Rear steering angle', value: '±10° independent left/right control' },
            { label: 'Min turning radius', value: '4.62 m' },
            { label: 'Crab walk angle', value: 'Up to 15° diagonal travel' },
          ],
          source: { label: 'BYD China — e³ Platform Launch, 22 August 2024', url: 'https://www.byd.com/cn/news/2024/detail543' },
        },
        {
          id: 'brakes',
          system: 'brakes',
          title: 'Perforated ventilated discs & multi-piston calipers',
          scene: 'exterior',
          nodes: [
            'DenzaZ9_Wheels_Caliper_FL', 'DenzaZ9_Wheels_Caliper_FR', 'DenzaZ9_Wheels_Caliper_RL', 'DenzaZ9_Wheels_Caliper_RR',
            'DenzaZ9_Pro_Wheels_Caliper_FL', 'DenzaZ9_Pro_Wheels_Caliper_FR', 'DenzaZ9_Pro_Wheels_Caliper_RL', 'DenzaZ9_Pro_Wheels_Caliper_RR',
          ],
          basis: 'published',
          text: 'High-performance ventilated brake discs and multi-piston calipers coordinated with e³ rear-wheel toe-in braking for shorter stopping distances and compass-turn pivot locking.',
          facts: [
            { label: 'Braking coordination', value: 'IPB brake-by-wire + e³ rear toe-in stability' },
          ],
          source: { label: 'Denza Official — Z9 Executive Flagship Sedan', url: 'https://www.denza.com/' },
        },
        {
          id: 'wheels',
          system: 'brakes',
          title: '21-inch Starlight / 20-inch Multi-Spoke wheels',
          scene: 'exterior',
          nodes: [
            'DenzaZ9_Wheels_FL', 'DenzaZ9_Wheels_FR', 'DenzaZ9_Wheels_RL', 'DenzaZ9_Wheels_RR',
            'DenzaZ9_Pro_Wheels_FL', 'DenzaZ9_Pro_Wheels_FR', 'DenzaZ9_Pro_Wheels_RL', 'DenzaZ9_Pro_Wheels_RR',
          ],
          basis: 'published',
          clip: 'rotor',
          text: 'Staggered 255/40 R21 front and 275/40 R21 rear tyres on the 21-inch Starlight wheel, or 255/45 R20 front and 275/45 R20 rear on the 20-inch Multi-Spoke wheel.',
          facts: [
            { label: '21" tyres', value: '255/40 R21 front · 275/40 R21 rear' },
            { label: '20" tyres', value: '255/45 R20 front · 275/45 R20 rear' },
          ],
          source: { label: 'Autohome — 腾势Z9 Specifications (Series 7838)', url: 'https://www.autohome.com.cn/7838/' },
        },
      ],
    },
  },
  // The Tech tab (docs/tech-showcase.md, section 14). Every source below describes the Z9 GT, the shooting brake on the same
  // e³ platform: the showroom's Z9 is listed with the same two modes in its drive-mode list, but check that the sedan has them.
  // The sensors of the God's Eye demo, in the glTF model's axes (x forward, y up, z toward the passenger side), measured on the model
  // with rays on 2026-11-14 (the earlier values here were in Blender's axes and lay outside the car). Autohome (series 7838) lists
  // two lidars: the front photographs show a dark module in each outer bumper pocket, where the model has them, but no source says
  // that is where the lidars are, and the car has no roof lidar (the 2026 Z9 GT's is on the roof: another car). Only the sensors the
  // model shows are placed; the counts the table gives are in `notes`.
  sensors: {
    frontLidar: [2.329, 0.35, 0.68],
    lidarFov: 120,
    cameras: [{ at: [0.62, 1.19, 0] }],
    ultrasonic: [{ at: [2.48, 0.385, 0.36], mirror: true }],
    surround: true,
    notes: {
      front: 'Two lidars (Autohome). Drawn from the dark module in each outer bumper pocket, which the front photographs show; no source says that is where they sit. The 120° fan is ours.',
      cameras: 'Fourteen outside, with a three-lens unit at the windscreen, and one or two in the cabin (Autohome); only the windscreen unit is marked',
      ultrasonic: 'Twelve (Autohome); the pair beside the plate is marked',
      surround: 'The surround cameras, drawn as four diagonal beams (ours)',
    },
  },
  tech: [
    {
      id: 'gods-eye',
      title: 'God’s Eye (天神之眼) · Traffic jam',
      blurb:
        'On an expressway the Z9 follows the traffic with its adaptive cruise. A queue is standing far ahead: the lidars mark it long before the car in front brakes, the Z9 slows with that car, stops behind it holding the gap, waits, and moves off when the queue does.',
      driver: 'sensors',
      scenario: 'queue',
      claims: [
        {
          text: 'On every trim the driver-assist system is listed as DiPilot, level 2, on an NVIDIA Orin chip, with two lidars, fourteen exterior cameras (a three-lens unit at the front) and one or two in the cabin, five millimetre-wave radars and twelve ultrasonic sensors.',
          source: { label: 'Autohome configuration table, Denza Z9 (series 7838), read 2026-11-14', url: 'https://car.autohome.com.cn/config/series/7838.html' },
        },
        {
          text: 'The same table lists full-speed adaptive cruise, lane centring, assisted lane change, ramp entry and exit, traffic-light recognition and assisted, remote and memory parking as standard.',
          source: { label: 'Autohome configuration table, Denza Z9 (series 7838), read 2026-11-14', url: 'https://car.autohome.com.cn/config/series/7838.html' },
        },
        {
          text: 'BYD sells this family of systems as God’s Eye: the China-market Z9 GT, on the same platform, carries “God’s Eye 5.0”, and its city navigation assistant is announced for Europe in 2027.',
          source: { label: 'CarNewsChina, 13 October 2026', url: 'https://carnewschina.com/2026/10/13/denza-z9-gt-to-become-first-byd-car-with-gods-eye-autonomous-navigation-in-europe/' },
        },
      ],
      simulated:
        'A simulation. The expressway, the queue, where it stands, every speed, when the jam clears and how far off the lidars mark the stopped cars are ours: BYD publishes no scenario. Autohome names the system DiPilot and the sources found do not say which God’s Eye tier the sedan carries; the 120° fans, their reach, the four surround beams and the pulses are ours; the two lidars are drawn from the dark module in each outer bumper pocket that the front photographs show, which no source confirms as their place. The other cars are the other models’ stand-ins.',
    },
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
  // The Drive tab's scenario (docs/tech-showcase.md section 19). Crab walk: front wheels 15 degrees, rear wheels at most 10 (the
  // 'crab' demo above); the sources describe the Z9 GT, which shares the platform.
  drive: {
    id: 'hyper-gt',
    title: 'Hyper-GT Launch + Vectoring Mastery',
    blurb:
      'A three-motor launch, an S-curve under power where the two rear motors share the drive to turn the car, then a crab walk on the rear-wheel steering.',
    modes: ['eco', 'comfort', 'sport'],
    defaultMode: 'sport',
    overlays: ['motors', 'steering', 'power'],
    finish: 'coast',
    manoeuvres: ['sweep', 'crab'],
    chassis: { airSuspension: true, rearSteerMaxDeg: 10, crabDeg: 15 },
    ghost: { slug: 'avatr-06t', variantId: '650-ultra-ev-awd' },
    camera: 'chase',
    callouts: [
      { cue: 'launch', text: 'Launch. Three motors pull together; weight moves to the rear axle.' },
      { cue: 'sweep', text: 'Torque vectoring. In the curve the rear motors favour the outside wheel and push the car round.' },
      { cue: 'crab', text: 'Crab walk. All four wheels turn the same way and the car slides sideways. The rear wheels stop at 10°; the rear motors’ differential does the rest.' },
      { cue: 'stop', text: 'Parked.' },
    ],
    claims: [
      {
        text: 'The e³ platform pairs three motors driving independently with independent dual-motor rear-wheel steering.',
        source: { label: 'BYD China, 22 August 2024', url: 'https://www.byd.com/cn/news/2024/detail543' },
      },
      {
        text: 'In a crab walk the rear wheels steer up to ±10°; with the rear motors’ differential, the crab angle reaches 15°.',
        source: { label: 'Xchuxing, Z9 GT drive', url: 'https://www.xchuxing.com/article/133019' },
      },
    ],
    simulated:
      'The S-curve, the crab’s pace (7 km/h) and shift (1.8 m), and how far the rear motors favour the outside wheel are ours. The sources describe the Z9 GT, which shares this platform.',
  },
  sources: [
    { label: 'Autohome — 腾势Z9 Specifications (Series 7838)', url: 'https://www.autohome.com.cn/7838/' },
    { label: 'Denza Official — Z9 Executive Flagship Sedan', url: 'https://www.denza.com/' },
  ],
};
