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
    // the car's pages in the photographs are the light UI (blender/reference/avatr-06t/hmi); the home keeps its dark wallpaper
    defaultTheme: 'light',
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
    // the 06T's own seat: the bight at x 0.150, cushion centered in door aperture, backrest aligned with B-pillar
    driverEye: [0.22, 0.40, 1.17],
    // Seated driver view with wide-angle lens showing the cockpit, console, and seating area
    driverView: { back: 0.0, out: 0.0, lift: 0.0, fov: 56, look: [0.18, -0.035, 0.040] },
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
      // The three cabins Autohome photographed (series 8538, cat 3: photos 1-64, 116-160 and 65-115). The cabin is built in
      // the first; the others recolour its materials (INT_Leather_White_Perf's texture carries the white, so its colour
      // is the target divided by 0.58). The red cabin's seats have horizontal pleats the recolour does not model.
      {
        id: 'misty-purple-cotton-white',
        name: 'Misty Purple & Cotton White',
        nameZh: '暮紫/烟白',
        swatch: ['#7d798c', '#cbcac6'],
      },
      {
        id: 'tinted-charcoal',
        name: 'Tinted Charcoal',
        nameZh: '深紫',
        swatch: ['#3c3844', '#524d5d'],
        colors: {
          INT_Leather_White: '#524d5d',
          INT_Leather_White_Perf: '#6b6479',
          INT_Leather_Purple: '#3c3844',
          INT_Trim_Purple: '#4b4855',
          INT_Plastic_White: '#3f3d48',
          INT_Headliner: '#38373f',
          INT_Thread_White: '#595561',
        },
      },
      {
        id: 'kalypso-red',
        name: 'Kalypso Red',
        nameZh: '岱红',
        swatch: ['#272729', '#aa3f40'],
        colors: {
          INT_Leather_White: '#aa3f40',
          INT_Leather_White_Perf: '#d85354',
          INT_Leather_Purple: '#aa3f40',
          INT_Trim_Purple: '#9b3c3e',
          INT_Plastic_White: '#272729',
          INT_Headliner: '#212122',
          INT_Thread_White: '#a03f3f',
        },
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
  xray: {
    node: 'Avatr06T_Greenhouse',
    color: '#98a4b3',
    opacity: 0.34,
    hideCabin: ['int_headliner'],
    anatomy: {
      url: '/models/avatr-06t-xray.glb',
      note: "The X-ray view's parts are our own models, placed from the car's dimensions and Avatr's published CHN platform, CATL Shenxing 800 V 5C battery and Huawei DriveONE SiC powertrain layout. Figures on a card are Avatr's or Autohome's where stated; the shapes of the castings, cells and gears are illustrative.",
      parts: [
        {
          id: 'battery',
          system: 'battery',
          title: '82.16 kWh CATL Shenxing (神行) 800 V 5C pack',
          nodes: ['XR_Battery_Tray', 'XR_Battery_Lid', 'XR_Battery_Busbars', 'XR_Battery_Film'],
          basis: 'published',
          text: 'Co-developed on the CHN (Changan · CATL · Huawei) platform, the 06T uses CATL’s 82.16 kWh Shenxing (神行) 800 V supercharging battery pack with cell-to-pack integration and 24-hour cloud thermal monitoring.',
          facts: [
            { label: 'Capacity', value: '82.16 kWh' },
            { label: 'Battery partner', value: 'CATL Shenxing (神行) supercharging pack' },
            { label: 'Architecture', value: 'Full-domain 800 V SiC' },
            { label: '10 to 80 % DC charge', value: '15 min' },
          ],
          source: { label: 'Avatr Official Website — Avatr 06T', url: 'https://www.avatr.com/en/06T' },
        },
        {
          id: 'cells',
          system: 'battery',
          title: 'CATL Shenxing fast-ion cell array',
          nodes: [
            'XR_Battery_Cells_01', 'XR_Battery_Cells_02', 'XR_Battery_Cells_03', 'XR_Battery_Cells_04',
            'XR_Battery_Cells_05', 'XR_Battery_Cells_06', 'XR_Battery_Cells_07', 'XR_Battery_Cells_08',
            'XR_Battery_Cells_09', 'XR_Battery_Cells_10', 'XR_Battery_Cells_11', 'XR_Battery_Cells_12',
          ],
          basis: 'published',
          clip: 'battery',
          text: 'Fast-ion graphite anode and ultra-thin SEI film chemistry allow high-rate charging across a wide temperature band while delivering up to 650 km CLTC range.',
          facts: [
            { label: 'CLTC range', value: '650 km (RWD) · 600 km (Ultra AWD)' },
          ],
          source: { label: 'Avatr Official Website — Avatr 06T', url: 'https://www.avatr.com/en/06T' },
        },
        {
          id: 'cooling',
          system: 'battery',
          title: 'Integrated liquid thermal plate',
          nodes: ['XR_Battery_Plate'],
          basis: 'illustrative',
          text: 'Bottom-mounted serpentine liquid cooling and heating plate linked to the heat-pump cabin and drivetrain loop.',
        },
        {
          id: 'pdu',
          system: 'battery',
          title: '800 V high-voltage distribution unit',
          nodes: ['XR_Battery_PDU', 'XR_Battery_RearPort'],
          basis: 'published',
          text: 'High-voltage junction box routing 800 V power between the CATL pack and the Huawei DriveONE front and rear traction inverters.',
          source: { label: 'Avatr Official Website — Avatr 06T', url: 'https://www.avatr.com/en/06T' },
        },
        {
          id: 'rear-drive',
          system: 'drive',
          title: 'Huawei DriveONE rear 250 kW SiC permanent-magnet motor',
          nodes: ['XR_Drive_R'],
          basis: 'published',
          clip: 'rotor',
          text: 'Huawei DriveONE 800 V silicon-carbide permanent-magnet synchronous rear drive unit delivering 250 kW (340 PS) and 365 N·m with direct oil cooling.',
          facts: [
            { label: 'Rear peak power', value: '250 kW (340 PS)' },
            { label: 'Rear peak torque', value: '365 N·m' },
            { label: 'Drive system', value: 'Huawei DriveONE 800 V SiC' },
          ],
          source: { label: 'Avatr Official Website — Avatr 06T', url: 'https://www.avatr.com/en/06T' },
        },
        {
          id: 'front-drive',
          system: 'drive',
          title: 'Huawei DriveONE front 190 kW AC induction motor',
          nodes: ['XR_Drive_F'],
          basis: 'published',
          clip: 'rotor',
          text: 'On the Ultra AWD and Knight Edition, a 190 kW / 280 N·m front AC asynchronous motor joins the rear unit for 440 kW (598 PS) and 645 N·m combined, launching the shooting brake from 0 to 100 km/h in 3.9 seconds.',
          facts: [
            { label: 'Front peak power', value: '190 kW (258 PS) · 280 N·m' },
            { label: 'Combined AWD output', value: '440 kW (598 PS) · 645 N·m' },
            { label: '0–100 km/h', value: '3.9 s' },
          ],
          source: { label: 'Avatr Official Website — Avatr 06T', url: 'https://www.avatr.com/en/06T' },
        },
        {
          id: 'rotor',
          system: 'drive',
          title: '22,000 rpm oil-cooled rotor & flat-wire stator',
          nodes: ['XR_Drive_R_Rotor', 'XR_Drive_F_Rotor', 'XR_Drive_R_Stator', 'XR_Drive_F_Stator'],
          basis: 'published',
          clip: 'rotor',
          text: 'Flat-wire hairpin copper stator windings and oil-cooled rotors sustain repeated launches and a 210 km/h top speed.',
          facts: [
            { label: 'Top speed', value: '210 km/h' },
          ],
          source: { label: 'Avatr Official Website — Avatr 06T', url: 'https://www.avatr.com/en/06T' },
        },
        {
          id: 'inverter',
          system: 'drive',
          title: 'Huawei DriveONE 800 V SiC inverters & dynamic torque control',
          nodes: ['XR_Drive_R_Inverter', 'XR_Drive_F_Inverter'],
          basis: 'published',
          text: 'Silicon-carbide power modules with millisecond adaptive torque control to prevent wheelspin over wet paint lines and uneven pavement.',
          source: { label: 'Avatr Official Website — Avatr 06T', url: 'https://www.avatr.com/en/06T' },
        },
        {
          id: 'reducer',
          system: 'drive',
          title: 'Single-speed helical reduction gearsets',
          nodes: [
            'XR_Drive_R_Reducer', 'XR_Drive_R_Gears', 'XR_Drive_R_Pinion',
            'XR_Drive_F_Reducer', 'XR_Drive_F_Gears', 'XR_Drive_F_Pinion',
          ],
          basis: 'illustrative',
          clip: 'rotor',
          text: 'Low-noise helical reduction gearsets integrated into the front and rear DriveONE casings.',
        },
        {
          id: 'subframes',
          system: 'chassis',
          title: 'CHN platform aluminium subframes & crash rails',
          nodes: ['XR_Frame_SubF', 'XR_Frame_SubR', 'XR_Frame_CrashF', 'XR_Frame_CrashR'],
          basis: 'published',
          text: 'CHN architecture cast-aluminium subframes and dual-path front energy-absorbing rails spanning a 2,940 mm wheelbase.',
          facts: [
            { label: 'Platform', value: 'CHN (Changan · CATL · Huawei)' },
            { label: 'Wheelbase', value: '2,940 mm' },
          ],
          source: { label: 'Avatr Official Website — Avatr 06T', url: 'https://www.avatr.com/en/06T' },
        },
        {
          id: 'floor',
          system: 'chassis',
          title: 'Hot-formed steel & extruded aluminium floor grid',
          nodes: ['XR_Frame_Floor'],
          basis: 'published',
          text: 'Multi-chamber extruded aluminium side sills and hot-stamped cross-members surround the 82.16 kWh battery pack.',
          source: { label: 'Avatr Official Website — Avatr 06T', url: 'https://www.avatr.com/en/06T' },
        },
        {
          id: 'wishbones',
          system: 'suspension',
          title: 'Front virtual-kingpin double-wishbone & rear multi-link',
          nodes: [
            'XR_Susp_FL_UpperArm', 'XR_Susp_FL_LowerArm', 'XR_Susp_FR_UpperArm', 'XR_Susp_FR_LowerArm',
            'XR_Susp_RL_UpperArm', 'XR_Susp_RL_LowerArm', 'XR_Susp_RR_UpperArm', 'XR_Susp_RR_LowerArm',
            'XR_Susp_RL_ToeLink', 'XR_Susp_RR_ToeLink',
            'XR_Susp_FL_Knuckle', 'XR_Susp_FR_Knuckle', 'XR_Susp_RL_Knuckle', 'XR_Susp_RR_Knuckle',
          ],
          basis: 'published',
          clip: 'suspension',
          text: 'All-aluminium front double-wishbone and rear five-link independent suspension reduces unsprung mass for crisp turn-in.',
          facts: [
            { label: 'Front', value: 'Double wishbone, aluminium' },
            { label: 'Rear', value: 'Multi-link independent, aluminium' },
          ],
          source: { label: 'Avatr Official Website — Avatr 06T', url: 'https://www.avatr.com/en/06T' },
        },
        {
          id: 'springs',
          system: 'suspension',
          title: 'Air suspension & CDC dynamic damping',
          nodes: [
            'XR_Susp_FL_Spring', 'XR_Susp_FL_Damper', 'XR_Susp_FL_Rod',
            'XR_Susp_FR_Spring', 'XR_Susp_FR_Damper', 'XR_Susp_FR_Rod',
            'XR_Susp_RL_Spring', 'XR_Susp_RL_Damper', 'XR_Susp_RL_Rod',
            'XR_Susp_RR_Spring', 'XR_Susp_RR_Damper', 'XR_Susp_RR_Rod',
          ],
          basis: 'published',
          clip: 'suspension',
          text: 'Height-adjustable air springs and electronically controlled CDC dampers lower the body at highway speeds and raise clearance for steep ramps.',
          source: { label: 'Avatr Official Website — Avatr 06T', url: 'https://www.avatr.com/en/06T' },
        },
        {
          id: 'arb',
          system: 'suspension',
          title: 'Anti-roll bars & AWD half-shafts',
          nodes: [
            'XR_Susp_ARB_F', 'XR_Susp_ARB_R',
            'XR_Susp_FL_Halfshaft', 'XR_Susp_FR_Halfshaft', 'XR_Susp_RL_Halfshaft', 'XR_Susp_RR_Halfshaft',
          ],
          basis: 'illustrative',
          text: 'Front and rear anti-roll bars and splined half-shafts coupling the DriveONE units to the hubs.',
        },
        {
          id: 'rack',
          system: 'steering',
          title: 'DP-EPS electric power steering rack',
          nodes: ['XR_Steering_Rack', 'XR_Susp_FL_TieRod', 'XR_Susp_FR_TieRod'],
          basis: 'published',
          clip: 'steering',
          text: 'Dual-pinion electric power steering rack tuned for sporty shooting-brake handling and Huawei Qiankun ADS 3.0 lane-keeping precision.',
          source: { label: 'Avatr Official Website — Avatr 06T', url: 'https://www.avatr.com/en/06T' },
        },
        {
          id: 'brakes',
          system: 'brakes',
          title: 'Four-piston fixed front calipers & ventilated discs',
          scene: 'exterior',
          nodes: [
            'Avatr06T_Wheels_Caliper_FL', 'Avatr06T_Wheels_Caliper_FR', 'Avatr06T_Wheels_Caliper_RL', 'Avatr06T_Wheels_Caliper_RR',
            'Avatr06T_Star_Wheels_Caliper_FL', 'Avatr06T_Star_Wheels_Caliper_FR', 'Avatr06T_Star_Wheels_Caliper_RL', 'Avatr06T_Star_Wheels_Caliper_RR',
          ],
          basis: 'published',
          text: 'Fixed four-piston front calipers (in Silver Grey, Performance Yellow or Competition Red) and ventilated brake discs.',
          facts: [
            { label: 'Caliper options', value: 'Silver Grey · Performance Yellow · Competition Red' },
          ],
          source: { label: 'Avatr Official Website — Avatr 06T', url: 'https://www.avatr.com/en/06T' },
        },
        {
          id: 'wheels',
          system: 'brakes',
          title: '20-inch Cyclone / Star Spin forged wheels & staggered tyres',
          scene: 'exterior',
          nodes: [
            'Avatr06T_Wheels_FL', 'Avatr06T_Wheels_FR', 'Avatr06T_Wheels_RL', 'Avatr06T_Wheels_RR',
            'Avatr06T_Star_Wheels_FL', 'Avatr06T_Star_Wheels_FR', 'Avatr06T_Star_Wheels_RL', 'Avatr06T_Star_Wheels_RR',
          ],
          basis: 'published',
          clip: 'rotor',
          text: '20-inch Cyclone five-spoke or Star Spin forged five-spoke wheels with staggered 255/45 R20 front and 265/45 R20 rear tyres.',
          facts: [
            { label: 'Tyres', value: '255/45 R20 front · 265/45 R20 rear' },
          ],
          source: { label: 'Avatr Official Website — Avatr 06T', url: 'https://www.avatr.com/en/06T' },
        },
      ],
    },
  },
  // The clear panes keep the X-ray's ghost (the front glass of c1_0001..c1_0003 shows the cabin plainly). The privacy glass
  // (rear windows, backlight, glass roof) was drawn 55 % opaque: the cargo trim, the shelf and the headliner's lamps showed
  // through the backlight and the roof as grey shapes the owner read as bumps and body mixed into the glass (2026-10-28). The
  // photographed pane is dark with only the headrests' silhouettes in it (c1_0005, c1_0007), and it mirrors a dark ceiling.
  glass: { color: '#98a4b3', opacity: 0.34, privacy: 0.84, privacyReflect: 0.55 },
  // The slit lamp's lit bar is Avatr's cyan signature (c1_0009..0012: the grey car with its lamps awake), glowing a little
  // even with the lamps off; the projector units are the two pale lens plates (the parking sensors no longer light).
  lights: {
    // the halo and the white-hot core are two materials driven together (the core's own baked strength would clip to white)
    front: { material: 'M_LED_Cyan', aliases: ['M_LED_Cyan_Core'], color: '#b4f4ff', halo: '#2bb6ff', off: 0.7, on: 2.6 },
    projector: { material: 'M_Lamp_Lens' },
  },
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
