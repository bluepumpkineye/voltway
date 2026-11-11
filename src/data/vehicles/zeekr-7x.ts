import type { Vehicle } from './schema';

export const zeekr7x: Vehicle = {
  slug: 'zeekr-7x',
  brand: 'Zeekr',
  model: '7X',
  group: 'Geely',
  bodyStyle: 'SUV',
  year: 2026,
  tagline: '900 volts, 6C charging, ten minutes from 10 to 80 percent.',
  summary:
    'The 7X facelift is where Zeekr put its 900 V architecture to work. Six-C charging refills the 103 kWh pack in about ten minutes, and the dual-motor car reaches 100 km/h in under three seconds.',
  dimensions: { lengthMm: 4825, widthMm: 1930, heightMm: 1656, wheelbaseMm: 2925 },
  variants: [
    {
      id: 'std-rwd',
      name: 'Standard Range RWD',
      drive: 'RWD',
      battery: { capacityKwh: 75, chemistry: 'LFP', architectureV: 800, cRate: 5.5, chargeMinutes10to80: 10.5 },
      performance: { powerKw: 370, zeroTo100S: 5.4, motorCount: 1, topSpeedKmh: 210 },
      range: [{ cycle: 'CLTC', km: 620 }],
    },
    {
      id: 'lr-rwd',
      name: 'Long Range RWD',
      drive: 'RWD',
      battery: { capacityKwh: 103, chemistry: 'NMC', architectureV: 900, cRate: 6, chargeMinutes10to80: 10 },
      performance: { powerKw: 370, zeroTo100S: 5.1, motorCount: 1, topSpeedKmh: 210 },
      range: [{ cycle: 'CLTC', km: 802 }],
    },
    {
      id: 'awd',
      name: 'Performance AWD',
      drive: 'AWD',
      battery: { capacityKwh: 103, chemistry: 'NMC', architectureV: 900, cRate: 6, chargeMinutes10to80: 10 },
      performance: { powerKw: 585, zeroTo100S: 2.98, motorCount: 2, topSpeedKmh: 210 },
      range: [{ cycle: 'CLTC', km: 715 }],
    },
  ],
  cockpit: {
    os: 'ZEEKR OS',
    skin: 'zeekros',
    // the car's screen is the light one in every photograph; dark is a showroom extra
    defaultTheme: 'light',
    accentColor: '#00B3A4',
    ambientLighting: true,
    // as Quick settings lists them (Autohome's photographs of the car's screen, c10_0033)
    driveModes: [
      { id: 'comfort', label: 'Comfort', native: '舒适', group: 'street', model: 'comfort' },
      { id: 'economy', label: 'Economy', native: '经济', group: 'street', model: 'eco' },
      { id: 'sport', label: 'Sport', native: '运动', group: 'street', model: 'sport' },
      { id: 'snow', label: 'Snow', native: '雪地', group: 'street', model: 'comfort' },
      { id: 'off-road', label: 'Off-road', native: '越野', group: 'street', model: 'comfort' },
      { id: 'custom', label: 'Custom', native: '个性化', group: 'special', model: 'comfort' },
    ],
    screens: [
      { id: 'center', label: 'Centre touchscreen', diagonalIn: 16, role: 'center', interactive: true },
      { id: 'hud', label: 'AR head-up display', diagonalIn: 13, role: 'hud' },
      { id: 'cluster', label: 'Instrument cluster', diagonalIn: 13, role: 'cluster' },
    ],
  },
  assets: {
    // blender/scripts/export_zx.py web(): the exterior (the Ultra on 21 in wheels). The cabin
    // follows; until then the model is for the showroom only
    modelUrl: '/models/zeekr-7x.glb',
    showroomOnly: true,
    // the cabin (zx_interior*.py, the cream and taupe "purple/white" build) with its Cycles light
    // baked in: export_zx.web_full()
    interiorModelUrl: '/models/zeekr-7x-interior.glb',
    interiorProbeUrl: '/models/cabin-hall.hdr',
    // the cream cabin lit by the daylight that comes through the glass reads darker than the
    // studio photographs of it (cream ~210 sRGB there, ~185 here): lifted in the viewer
    cabinGain: 1.3,
    // Poly Haven "Shanghai Riverside" (CC0), turned exactly as the SU7's: inside, the skyline is
    // ahead through the windscreen and the sun behind; outside, the world turns 147.6 deg so the
    // default camera has the golden-hour sun at its back (the sun measured off the HDRI)
    outside: {
      view: '/models/zeekr-7x-outside.jpg',
      light: '/models/zeekr-7x-outside-light.hdr',
      exteriorTurnDeg: 147.6,
      sun: { direction: [0.6959, 0.3477, 0.6284], color: '#ffdfae', intensity: 1.96 },
      ground: { height: 1.7, radius: 45 },
    },
    // its shadow on the studio floor: export_zx.bake_ground_shadow() prints the size and
    // centre (the build's axes, metres)
    studioShadow: { url: '/models/zeekr-7x-shadow.webp', size: [7.846, 5.05], centre: [0, 0] },
    // scripts/make-proxy.mjs: the neighbour in another car's parking stage
    proxyUrl: '/models/zeekr-7x-proxy.glb',
    heroColor: '#49749C',
    // over the driver's seat (the cabin's H-point (0.22, 0.37, 0.585) + 0.64 up, a little back)
    driverEye: [0.16, 0.385, 1.22],
  },
  // The maker's palette (Autohome's colour list for the 2026 car): six paints and four cabin
  // colourways. The build is Gorge Stone Blue (涧石蓝, the car of the studio photographs);
  // every other value is matched by eye to Autohome's swatches under our studio rig (hence
  // "approximate" in the interface). The English names are translations of the Chinese ones.
  configurator: {
    paintMaterial: 'M_Paint_ZX_Blue',
    paints: [
      { id: 'gorge-stone-blue', name: 'Gorge Stone Blue', nameZh: '涧石蓝', swatch: '#49749C' },
      {
        id: 'forest-green',
        name: 'Forest Green',
        nameZh: '森野绿',
        swatch: '#185454',
        finish: { color: '#2a5655', roughness: 0.42, metalness: 0.22, clearcoat: 0.35, clearcoatRoughness: 0.25 },
      },
      {
        id: 'night-purple',
        name: 'Night Purple',
        nameZh: '暗夜紫',
        swatch: '#594569',
        finish: { color: '#5a4a66', roughness: 0.42, metalness: 0.22, clearcoat: 0.35, clearcoatRoughness: 0.25 },
      },
      {
        id: 'glacier-silver',
        name: 'Glacier Silver',
        nameZh: '冰川银',
        swatch: '#C8C8C8',
        finish: { color: '#a3a8ae', roughness: 0.38, metalness: 0.5, clearcoat: 0.4, clearcoatRoughness: 0.2 },
      },
      {
        id: 'polar-night-black',
        name: 'Polar Night Black',
        nameZh: '极夜黑',
        swatch: '#16171a',
        finish: { color: '#141518', roughness: 0.32, metalness: 0.1, clearcoat: 0.8, clearcoatRoughness: 0.1 },
      },
      {
        id: 'polar-day-white',
        name: 'Polar Day White',
        nameZh: '极昼白',
        swatch: '#f3f3f1',
        finish: { color: '#dcdcd8', roughness: 0.36, metalness: 0.08, clearcoat: 0.6, clearcoatRoughness: 0.15 },
      },
    ],
    // The cabin colourways (紫/白, 黑/橙, 黑/灰, 黑/紫 on the maker's list). The build is the
    // cream and taupe cabin of the studio car (Autohome cat 3, 1-58); the others recolour its
    // leather, lower trim, dash top, carpet, headliner and stitching by material name, with
    // values read off the photographs of the orange (361-400), grey (121-154) and orchid
    // (233-280) cars: the leather everywhere it is cream here, black below it. They are
    // approximate: the interface says so.
    trims: [
      { id: 'purple-white', name: 'Purple and White', nameZh: '紫/白', swatch: ['#e9e6e8', '#6a4f7d'] },
      {
        id: 'black-orange',
        name: 'Black and Orange',
        nameZh: '黑/橙',
        swatch: ['#1b1b1d', '#d2661f'],
        colors: {
          INT_Leather_White: '#d06448',
          INT_Leather_Taupe: '#26272a',
          INT_Dash_Top: '#2a2b2e',
          INT_Carpet_Taupe: '#232426',
          INT_Headliner: '#3c3e41',
          INT_Thread_Cream: '#d06448',
        },
      },
      {
        id: 'black-grey',
        name: 'Black and Grey',
        nameZh: '黑/灰',
        swatch: ['#1b1b1d', '#8b8d91'],
        colors: {
          INT_Leather_White: '#87939b',
          INT_Leather_Taupe: '#34373a',
          INT_Dash_Top: '#2a2c2f',
          INT_Carpet_Taupe: '#26282a',
          INT_Headliner: '#34373a',
          INT_Thread_Cream: '#87939b',
        },
      },
      {
        id: 'black-purple',
        name: 'Black and Purple',
        nameZh: '黑/紫',
        swatch: ['#1b1b1d', '#6a4f7d'],
        colors: {
          INT_Leather_White: '#966a8c',
          INT_Leather_Taupe: '#2f3036',
          INT_Dash_Top: '#2a2b30',
          INT_Carpet_Taupe: '#242427',
          INT_Headliner: '#3b3438',
          INT_Thread_Cream: '#966a8c',
        },
      },
    ],
    // The Ultra and the 103 kWh Max are photographed with orange calipers (the build's own), the
    // 75 kWh Max and the other trims with silver ones.
    caliperMaterial: 'M_Caliper_Orange',
    calipers: [
      { id: 'orange', name: 'Orange', nameZh: '橙色', color: '#e56f1d' },
      { id: 'silver', name: 'Silver', nameZh: '银色', color: '#8d9399' },
    ],
    // The wheels Autohome's configuration lists with the car: 255/50 R19 (standard), 265/45 R20
    // (+ CNY 11,000) and 265/40 R21 (+ CNY 20,000). No page names the designs. The 21 in six-Y is
    // what the model is built with (the Ultra's); the 20 in multi-spoke and the 20 in twin-fork,
    // in two finishes of one model, are nodes of the same file, traced from Autohome's photographs
    // of the 75 kWh Max. The 19 in cover is not built.
    wheels: [
      { id: 'six-y', name: 'Six-Y', size: '21"', tyres: '265/40 R21', node: 'Zeekr7X_Wheels', caliper: 'orange' },
      { id: 'multi-spoke', name: 'Multi-spoke', size: '20"', tyres: '265/45 R20', node: 'Zeekr7X_Multi_Wheels', caliper: 'silver' },
      {
        id: 'twin-fork',
        name: 'Twin-fork',
        size: '20"',
        tyres: '265/45 R20',
        node: 'Zeekr7X_Fork_Wheels',
        accent: { material: 'M_Wheel_Accent', color: '#c9ccd1', metalness: 1, roughness: 0.3 },
        caliper: 'silver',
      },
      {
        id: 'twin-fork-black',
        name: 'Twin-fork, gloss black',
        size: '20"',
        tyres: '265/45 R20',
        node: 'Zeekr7X_Fork_Wheels',
        accent: { material: 'M_Wheel_Accent', color: '#0d0d0e', metalness: 0, roughness: 0.12 },
        caliper: 'silver',
      },
    ],
    sources: [
      { label: 'Autohome - Zeekr 7X: colours and interiors', url: 'https://car.autohome.com.cn/pic/series/7777.html' },
      { label: 'Autohome - Zeekr 7X: wheels and brakes (75 kWh Max)', url: 'https://car.autohome.com.cn/pic/series/7777-12.html' },
    ],
  },
  // The four doors swing on their leading edge (the hinge: mid height, on the skin;
  // blender/scripts/zx_openings.py). The node origins are the hinges, and the cabin's door cards
  // turn about the same axes. Angles from the opening photographs (Autohome c3_0001-3, 18, 20,
  // 36-38); the sign is the swing direction (glTF y up).
  openings: [
    { id: 'doorFL', node: 'Zeekr7X_Door_FL', cardNode: 'int_door_L', frameNode: 'Zeekr7X_DoorFrame_FL', deg: -72, xrayHide: true },
    { id: 'doorFR', node: 'Zeekr7X_Door_FR', cardNode: 'int_door_R', frameNode: 'Zeekr7X_DoorFrame_FR', deg: 72, xrayHide: true },
    { id: 'doorRL', node: 'Zeekr7X_Door_RL', cardNode: 'int_rdoor_L', frameNode: 'Zeekr7X_DoorFrame_RL', deg: -66, xrayHide: true },
    { id: 'doorRR', node: 'Zeekr7X_Door_RR', cardNode: 'int_rdoor_R', frameNode: 'Zeekr7X_DoorFrame_RR', deg: 66, xrayHide: true },
    // The bonnet hinges on a lateral axis under its rear edge at the cowl and rises ~60 deg
    // (c12_0001); two gas struts hold it from the cowl's corners.
    {
      id: 'frunk',
      node: 'Zeekr7X_Bonnet',
      axis: 'z',
      deg: 60,
      struts: [
        { body: [1.25, 1.0, -0.73], moving: [1.52, 1.05, -0.73] },
        { body: [1.25, 1.0, 0.73], moving: [1.52, 1.05, 0.73] },
      ],
    },
    // The charge flap on the left rear quarter hinges at its front edge and swings out about 105 degrees
    // (c12_0048; zx_charge.py). The pocket behind it, the light strip, the badge and the dust caps are one
    // node, shown only while it is open.
    { id: 'charge', node: 'Zeekr7X_ChargeFlap', frameNode: 'Zeekr7X_ChargePort', deg: -105 },
    // The tailgate hangs from the roof's trailing edge (zx_gate.py: the hinge at the glass's top
    // edge) and swings up ~80 deg (c3_0047) on two gas struts at its sides. The cabin's liner
    // turns with it.
    {
      id: 'boot',
      node: 'Zeekr7X_Tailgate',
      cardNode: 'int_tailgate',
      axis: 'z',
      deg: -80,
      hidesOutside: ['int_cpillar', 'int_cpillar_flange', 'int_qtr_lower'],
      // the mounts sit inside the quarter panels and the hatch's skin, so a shut car shows no strut
      struts: [
        { body: [-2.05, 1.12, -0.7], moving: [-2.3, 1.0, -0.7] },
        { body: [-2.05, 1.12, 0.7], moving: [-2.3, 1.0, 0.7] },
      ],
    },
  ],
  // The X-ray tab: the roof, A-pillars, rails and every pane of glass above the belt turn to one
  // pale ghost (the Zeekr7X_Greenhouse node, split out in blender/scripts/zx_gate.py), the doors
  // and the dark hull are not drawn, and the cabin shows through with its headliner removed.
  xray: {
    node: 'Zeekr7X_Greenhouse',
    color: '#98a4b3',
    opacity: 0.34,
    hideCabin: ['int_headliner'],
    anatomy: {
      url: '/models/zeekr-7x-xray.glb',
      note: "The X-ray view's parts are our own models, placed from the car's dimensions and Zeekr's published SEA (浩瀚) 900 V architecture, 6C Qilin / Golden Brick battery and mega-cast rear underbody layout. Figures on a card are Zeekr's or Autohome's where stated; the shapes of the castings, cells and gears are illustrative.",
      parts: [
        {
          id: 'battery',
          system: 'battery',
          title: '103 kWh 6C Qilin / 75 kWh 5.5C Golden Brick 900 V pack',
          nodes: ['XR_Battery_Tray', 'XR_Battery_Lid', 'XR_Battery_Busbars', 'XR_Battery_Film'],
          basis: 'published',
          text: 'Built on Zeekr’s 900 V high-voltage architecture, the 7X offers either CATL’s 103 kWh 6C Qilin (麒麟) ternary pack or Zeekr’s in-house 75 kWh 5.5C Golden Brick (金砖) LFP pack, charging from 10 % to 80 % in as little as 10 minutes.',
          facts: [
            { label: 'Capacity', value: '103 kWh 6C Qilin (NMC) · 75 kWh 5.5C Golden Brick (LFP)' },
            { label: 'Architecture', value: 'Full-stack 900 V high-voltage system' },
            { label: '10 to 80 % DC charge', value: '10 min (6C / 5.5C ultra-fast charge)' },
            { label: 'CLTC range', value: 'Up to 802 km (103 kWh RWD) · 715 km (AWD)' },
          ],
          source: { label: 'Zeekr Official — 极氪 7X Specifications', url: 'https://www.zeekr.cn/' },
        },
        {
          id: 'cells',
          system: 'battery',
          title: '6C Qilin / 5.5C Golden Brick cell-to-pack array',
          nodes: [
            'XR_Battery_Cells_01', 'XR_Battery_Cells_02', 'XR_Battery_Cells_03', 'XR_Battery_Cells_04',
            'XR_Battery_Cells_05', 'XR_Battery_Cells_06', 'XR_Battery_Cells_07', 'XR_Battery_Cells_08',
            'XR_Battery_Cells_09', 'XR_Battery_Cells_10', 'XR_Battery_Cells_11', 'XR_Battery_Cells_12',
          ],
          basis: 'published',
          clip: 'battery',
          text: 'Third-generation cell-to-pack (CTP 3.0) structure with low-resistance dual-tab electrodes and eight-fold thermal safety protection designed for 6C peak charging currents.',
          facts: [
            { label: 'Max charge multiplier', value: '6C (103 kWh) / 5.5C (75 kWh)' },
          ],
          source: { label: 'Zeekr Official — 极氪 7X Specifications', url: 'https://www.zeekr.cn/' },
        },
        {
          id: 'cooling',
          system: 'battery',
          title: 'Multi-functional interlayer liquid cooling',
          nodes: ['XR_Battery_Plate'],
          basis: 'published',
          text: 'High-flow liquid cooling plates and elastic thermal interlayers remove heat directly from the large cell surfaces during 6C ultra-fast charging.',
          source: { label: 'Zeekr Official — 极氪 7X Specifications', url: 'https://www.zeekr.cn/' },
        },
        {
          id: 'pdu',
          system: 'battery',
          title: '900 V high-voltage distribution unit',
          nodes: ['XR_Battery_PDU', 'XR_Battery_RearPort'],
          basis: 'published',
          text: 'High-voltage junction box rated for 900 V operation, feeding the front and rear silicon-carbide traction inverters and Zeekr V3 liquid-cooled supercharging port.',
          facts: [
            { label: 'Platform voltage', value: '900 V class' },
          ],
          source: { label: 'Zeekr Official — 极氪 7X Specifications', url: 'https://www.zeekr.cn/' },
        },
        {
          id: 'rear-drive',
          system: 'drive',
          title: 'Rear 370 kW 900 V SiC permanent-magnet motor',
          nodes: ['XR_Drive_R'],
          basis: 'published',
          clip: 'rotor',
          text: 'Zeekr’s high-output 900 V silicon-carbide permanent-magnet rear drive unit produces 370 kW (503 PS) on its own, giving even the single-motor RWD models a 5.1-second 0–100 km/h sprint.',
          facts: [
            { label: 'Rear peak power', value: '370 kW (503 PS)' },
            { label: 'Semiconductor', value: '900 V SiC MOSFET' },
          ],
          source: { label: 'Autohome — 极氪7X Specifications', url: 'https://www.autohome.com.cn/' },
        },
        {
          id: 'front-drive',
          system: 'drive',
          title: 'Front 215 kW asynchronous induction motor',
          nodes: ['XR_Drive_F'],
          basis: 'published',
          clip: 'rotor',
          text: 'On the 103 kWh Ultra AWD, a 215 kW front AC asynchronous motor joins the 370 kW rear motor for a combined 585 kW (795 PS), launching the SUV from 0 to 100 km/h in 2.98 seconds.',
          facts: [
            { label: 'Front peak power', value: '215 kW (292 PS)' },
            { label: 'Combined AWD output', value: '585 kW (795 PS)' },
            { label: '0–100 km/h (Ultra AWD)', value: '2.98 s' },
          ],
          source: { label: 'Autohome — 极氪7X Specifications', url: 'https://www.autohome.com.cn/' },
        },
        {
          id: 'rotor',
          system: 'drive',
          title: 'Oil-cooled flat-wire stator & high-speed rotor',
          nodes: ['XR_Drive_R_Rotor', 'XR_Drive_F_Rotor', 'XR_Drive_R_Stator', 'XR_Drive_F_Stator'],
          basis: 'published',
          clip: 'rotor',
          text: 'Cascading oil-cooled flat-wire stators and high-speed rotors sustain repeated full-power launches and a 230 km/h top speed.',
          facts: [
            { label: 'Top speed', value: '230 km/h' },
          ],
          source: { label: 'Zeekr Official — 极氪 7X Specifications', url: 'https://www.zeekr.cn/' },
        },
        {
          id: 'inverter',
          system: 'drive',
          title: '900 V silicon-carbide (SiC) dual inverters',
          nodes: ['XR_Drive_R_Inverter', 'XR_Drive_F_Inverter'],
          basis: 'published',
          text: 'High-voltage SiC power modules with millisecond slip control and off-road traction modes.',
          source: { label: 'Zeekr Official — 极氪 7X Specifications', url: 'https://www.zeekr.cn/' },
        },
        {
          id: 'reducer',
          system: 'drive',
          title: 'Coaxial helical reduction gearsets',
          nodes: [
            'XR_Drive_R_Reducer', 'XR_Drive_R_Gears', 'XR_Drive_R_Pinion',
            'XR_Drive_F_Reducer', 'XR_Drive_F_Gears', 'XR_Drive_F_Pinion',
          ],
          basis: 'illustrative',
          clip: 'rotor',
          text: 'Single-speed helical reduction gears coupling the front and rear motors to the axle differentials.',
        },
        {
          id: 'subframes',
          system: 'chassis',
          title: 'SEA architecture subframes & one-piece mega-cast rear underbody',
          nodes: ['XR_Frame_SubF', 'XR_Frame_SubR', 'XR_Frame_CrashF', 'XR_Frame_CrashR'],
          basis: 'published',
          text: 'Built on Geely’s Sustainable Experience Architecture (SEA / 浩瀚架构), featuring a one-piece mega-cast aluminium rear underbody that replaces dozens of stamped welds while increasing rear impact stiffness.',
          facts: [
            { label: 'Platform', value: 'SEA (浩瀚架构)' },
            { label: 'Rear structure', value: 'One-piece mega-cast aluminium rear underbody' },
            { label: 'Wheelbase', value: '2,925 mm' },
          ],
          source: { label: 'Zeekr Official — 极氪 7X Specifications', url: 'https://www.zeekr.cn/' },
        },
        {
          id: 'floor',
          system: 'chassis',
          title: '2,000 MPa dome-arch safety cage & extruded side sills',
          nodes: ['XR_Frame_Floor'],
          basis: 'published',
          text: 'Multi-cell extruded aluminium side sills pair with a 2,000 MPa ultra-high-strength hot-formed steel safety cage across the cabin and B-pillars.',
          facts: [
            { label: 'Hot-formed steel', value: '2,000 MPa dome-arch safety cage' },
          ],
          source: { label: 'Zeekr Official — 极氪 7X Specifications', url: 'https://www.zeekr.cn/' },
        },
        {
          id: 'wishbones',
          system: 'suspension',
          title: 'Front double-wishbone & rear five-link suspension',
          nodes: [
            'XR_Susp_FL_UpperArm', 'XR_Susp_FL_LowerArm', 'XR_Susp_FR_UpperArm', 'XR_Susp_FR_LowerArm',
            'XR_Susp_RL_UpperArm', 'XR_Susp_RL_LowerArm', 'XR_Susp_RR_UpperArm', 'XR_Susp_RR_LowerArm',
            'XR_Susp_RL_ToeLink', 'XR_Susp_RR_ToeLink',
            'XR_Susp_FL_Knuckle', 'XR_Susp_FR_Knuckle', 'XR_Susp_RL_Knuckle', 'XR_Susp_RR_Knuckle',
          ],
          basis: 'published',
          clip: 'suspension',
          text: 'All-aluminium front double-wishbone and rear five-link independent suspension geometry tuned for both high-speed stability and rough-road travel.',
          facts: [
            { label: 'Front', value: 'Double wishbone, aluminium' },
            { label: 'Rear', value: 'Five-link independent, aluminium' },
          ],
          source: { label: 'Zeekr Official — 极氪 7X Specifications', url: 'https://www.zeekr.cn/' },
        },
        {
          id: 'springs',
          system: 'suspension',
          title: 'Zeekr Magic Carpet (魔毯) air suspension & CCD dampers',
          nodes: [
            'XR_Susp_FL_Spring', 'XR_Susp_FL_Damper', 'XR_Susp_FL_Rod',
            'XR_Susp_FR_Spring', 'XR_Susp_FR_Damper', 'XR_Susp_FR_Rod',
            'XR_Susp_RL_Spring', 'XR_Susp_RL_Damper', 'XR_Susp_RL_Rod',
            'XR_Susp_RR_Spring', 'XR_Susp_RR_Damper', 'XR_Susp_RR_Rod',
          ],
          basis: 'published',
          clip: 'suspension',
          text: 'Five-level height-adjustable air springs (up to 230 mm ground clearance in off-road mode, 70 mm total travel) paired with CCD electromagnetic dampers that read road bumps ahead via the roof LiDAR and stereo cameras.',
          facts: [
            { label: 'Ride height range', value: '70 mm travel · up to 230 mm ground clearance' },
            { label: 'Damping', value: 'CCD electromagnetic + Magic Carpet preview' },
          ],
          source: { label: 'Zeekr Official — 极氪 7X Specifications', url: 'https://www.zeekr.cn/' },
        },
        {
          id: 'arb',
          system: 'suspension',
          title: 'Anti-roll bars & heavy-duty half-shafts',
          nodes: [
            'XR_Susp_ARB_F', 'XR_Susp_ARB_R',
            'XR_Susp_FL_Halfshaft', 'XR_Susp_FR_Halfshaft', 'XR_Susp_RL_Halfshaft', 'XR_Susp_RR_Halfshaft',
          ],
          basis: 'illustrative',
          text: 'Front and rear stabilizer bars and high-articulation constant-velocity half-shafts.',
        },
        {
          id: 'rack',
          system: 'steering',
          title: 'Variable-ratio electric power steering rack',
          nodes: ['XR_Steering_Rack', 'XR_Susp_FL_TieRod', 'XR_Susp_FR_TieRod'],
          basis: 'published',
          clip: 'steering',
          text: 'Speed-sensitive variable-ratio electric power steering rack mounted on the front subframe.',
          source: { label: 'Zeekr Official — 极氪 7X Specifications', url: 'https://www.zeekr.cn/' },
        },
        {
          id: 'brakes',
          system: 'brakes',
          title: 'Akebono four-piston fixed front calipers & ventilated discs',
          scene: 'exterior',
          nodes: [
            'Zeekr7X_Wheels_Caliper_FL', 'Zeekr7X_Wheels_Caliper_FR', 'Zeekr7X_Wheels_Caliper_RL', 'Zeekr7X_Wheels_Caliper_RR',
            'Zeekr7X_Multi_Wheels_Caliper_FL', 'Zeekr7X_Multi_Wheels_Caliper_FR', 'Zeekr7X_Multi_Wheels_Caliper_RL', 'Zeekr7X_Multi_Wheels_Caliper_RR',
            'Zeekr7X_Fork_Wheels_Caliper_FL', 'Zeekr7X_Fork_Wheels_Caliper_FR', 'Zeekr7X_Fork_Wheels_Caliper_RL', 'Zeekr7X_Fork_Wheels_Caliper_RR',
          ],
          basis: 'published',
          text: 'Akebono fixed four-piston front calipers and ventilated brake discs stop the 7X from 100 to 0 km/h in 34.9 metres.',
          facts: [
            { label: 'Front calipers', value: 'Akebono fixed 4-piston' },
            { label: '100–0 km/h braking', value: '34.9 m' },
          ],
          source: { label: 'Zeekr Official — 极氪 7X Specifications', url: 'https://www.zeekr.cn/' },
        },
        {
          id: 'wheels',
          system: 'brakes',
          title: '19-inch / 20-inch / 21-inch forged wheels & 265-section tyres',
          scene: 'exterior',
          nodes: [
            'Zeekr7X_Wheels_FL', 'Zeekr7X_Wheels_FR', 'Zeekr7X_Wheels_RL', 'Zeekr7X_Wheels_RR',
            'Zeekr7X_Multi_Wheels_FL', 'Zeekr7X_Multi_Wheels_FR', 'Zeekr7X_Multi_Wheels_RL', 'Zeekr7X_Multi_Wheels_RR',
            'Zeekr7X_Fork_Wheels_FL', 'Zeekr7X_Fork_Wheels_FR', 'Zeekr7X_Fork_Wheels_RL', 'Zeekr7X_Fork_Wheels_RR',
          ],
          basis: 'published',
          clip: 'rotor',
          text: 'Available with 19-inch aero wheels (255/50 R19), 20-inch multi-spoke wheels (265/45 R20), or 21-inch forged twin-five-spoke wheels (265/40 R21).',
          facts: [
            { label: 'Wheel options', value: '19" Aero · 20" Multi-Spoke · 21" Forged' },
          ],
          source: { label: 'Zeekr Official — 极氪 7X Specifications', url: 'https://www.zeekr.cn/' },
        },
      ],
    },
  },
  // The lamps (docs/lights.md). The front LED is the usual M_LED_White. The tail lamp is one red lens
  // bar with no LED material under it, so the lens is the lit part, and it is dark as built.
  lights: { rear: { material: 'M_Lamp_RedLens', off: 0 } },
  sensors: {
    lidar: [0.62, 0.0, 1.62],
    cameras: [
      { at: [2.40, 0.0, 0.88] },
      { at: [0.62, 0.48, 1.60], mirror: true },
      { at: [1.02, 0.95, 0.98], mirror: true },
      { at: [-2.40, 0.0, 1.02] },
    ],
    ultrasonic: [
      { at: [2.36, 0.40, 0.45], mirror: true },
      { at: [-2.36, 0.42, 0.48], mirror: true },
    ],
    surround: true,
  },

  // The Tech tab (docs/tech-showcase.md). Sources read 2026-10-12; the board is blender/reference/zeekr-7x/tech.
  tech: [
    {
      id: 'park',
      title: 'Haohan Smart Driving · Remote Parking',
      blurb:
        'Roof-mounted LiDAR, HD surround cameras, and 12 ultrasonic radars scan the environment to spot tight parking spaces, project docking vectors, and reverse in autonomously via the Zeekr app.',
      driver: 'park',
      devices: ['phone', 'dashboard'],
      params: { search: 12 },
      claims: [
        {
          text: 'Zeekr Haohan Smart Driving 2.0 features full-scenario Remote Parking Assist (RPA) and Memory Parking, supporting over 150 parking scenario types.',
          source: { label: 'Zeekr Official Website', url: 'https://www.zeekr.cn/' },
        },
        {
          text: 'Using high-resolution roof LiDAR, millimeter-wave radar, and ultrasonic sensors, the vehicle maps bays and obstacles in real time with centimeter accuracy.',
          source: { label: 'Xinhua News - Zeekr 7X Technology', url: 'https://www.news.cn/' },
        },
      ],
      simulated:
        'A simulation of autonomous reverse-in parking. The sensor suite sweeps the parking lane, identifies vacant slots, marks the target bay with flashing indicators, and guides the vehicle in safely while mirrored on the phone and center screen.',
    },

    {
      id: 'magic-carpet',
      title: 'Magic Carpet',
      blurb:
        'Three speed humps at 16 km/h. Choose the ride height, then watch a passive suspension bob over them and the Magic Carpet float.',
      driver: 'carpet',
      claims: [
        {
          text: 'The Zeekr Magic Carpet air suspension package is air suspension, CCD electromagnetic dampers and a smart Magic Carpet: the 4WD 7X carries it, rear-drive versions can add it (CNY 20,000 on the 75 kWh and 103 kWh MAX).',
          source: { label: 'Autohome launch article, 23 September 2024', url: 'https://chejiahao.autohome.com.cn/info/17026490' },
        },
        {
          text: 'The smart Magic Carpet is a perception system (front camera and lidar) with the suspension system, adjusting the suspension from the road ahead within milliseconds.',
          source: { label: 'Yiche, 25 September 2024', url: 'https://www.yiche.com/zhai/2126677/' },
        },
        {
          text: 'The refreshed 7X’s closed air suspension has five ride heights that follow speed, with geofencing, and up to 230 mm of ground clearance.',
          source: { label: 'Xinhua, 3 November 2025', url: 'https://www.news.cn/auto/20251103/050868441a0d4dff9a28a523841721a0/c.html' },
        },
        {
          text: 'The ride height can be changed by about 70 mm.',
          source: { label: 'Tencent News, 22 September 2024', url: 'https://news.qq.com/rain/a/20240922A05JVD00' },
        },
        {
          text: 'The car’s own screen names the five heights Very high, High, Standard, Low and Very low, next to the drive mode.',
          source: { label: 'Autohome photo of the 7X’s screen', url: 'https://www.autohome.com.cn/cars/imgs-7777-75350-10-x/12708776.html' },
        },
        {
          text: 'Suspension easy entry lowers the body by itself once the car is parked and a seat belt is unbuckled.',
          source: { label: 'Autohome photo of the 7X’s screen', url: 'https://www.autohome.com.cn/cars/imgs-7777-75350-10-x/12708773.html' },
        },
      ],
      simulated:
        'A simulation. The humps, the speed and the body’s motion are ours: the maker publishes no response curves. The five heights are equal steps over its roughly 70 mm, and “passive” is a plain suspension of our own, not a Zeekr car.',
      devices: ['dashboard'],
    },
  ],
  // The DC socket's mouth and the direction pointing out of it, in the viewer's axes (zx_charge.py: the cup centred 3 cm
  // ahead of the flap's middle, 2 cm under the skin), for the Charging tab's gun. The flap and the socket are modelled.
  chargePort: { mouth: [-1.4583, 0.982, -0.8458], axis: [-0.038, 0.1642, -0.9857], depth: 0.022 },
  // The Charging tab (docs/tech-showcase.md section 11). Sources read 2026-10-12.
  charging: {
    window: { from: 10, to: 80, minutes: 10 },
    peakKw: 620,
    packKwh: 103,
    architectureV: 900,
    connector: 'GB/T',
    port: { side: 'left', published: true, where: 'Left rear quarter, under one flap' },
    claims: [
      {
        text: 'The refreshed 7X carries 900 V motors, controllers and thermal management across the range, with 5.5C or 6C ultra-fast charging as standard.',
        source: { label: 'Xinhua, 3 November 2025', url: 'https://www.news.cn/auto/20251103/050868441a0d4dff9a28a523841721a0/c.html' },
      },
      {
        text: 'The 103 kWh 6C Kirin pack charges at up to 620 kW, and from 10 to 80 % in 10 minutes at best. The 75 kWh 5.5C pack adds 425 km in 10 minutes.',
        source: { label: 'Xinhua, 3 November 2025', url: 'https://www.news.cn/auto/20251103/050868441a0d4dff9a28a523841721a0/c.html' },
      },
      {
        text: 'The charge port is on the left rear quarter under one flap: a DC socket and an AC socket in one housing, a light strip above them and two dust caps on cords.',
        source: { label: 'Autohome photo of the 7X, flap open', url: 'https://www.autohome.com.cn/cars/imgs-7777-75350-12-x/12781350.html' },
      },
      {
        text: 'The car’s own screen has a “Charge port cover” tile for the flap, and a Vehicle charging page with the charge limit, the charge left and the range.',
        source: { label: 'Autohome photo of the 7X’s screen', url: 'https://www.autohome.com.cn/cars/imgs-7777-75350-10-x/12161296.html' },
      },
    ],
    simulated:
      'A simulation. Only the 620 kW peak and the ten minutes are published, and the ten minutes are the best case. The curve between them, the pedestal and the gun (styled on a generic charging connector, not a Zeekr or any maker’s) are ours, and ten minutes play in fourteen seconds.',
  },
  // The Drive tab's scenario (docs/tech-showcase.md section 19). The figures are this file's (the refreshed 7X: 795 PS and
  // 2.98 s, Paul Tan); other sources quote the earlier 7X Performance at 475 kW and 3.8 s, which is not this trim.
  drive: {
    id: 'suv-launch',
    title: 'SUV Supercar Launch',
    blurb:
      'Full power from a standstill to 100 and 150 km/h, then an easing into a 120 km/h cruise. Add a family and luggage and watch the pull, the squat and the ride height change.',
    runs: [{ from: 0, to: 150 }],
    defaultRun: '0-150',
    modes: ['economy', 'comfort', 'sport'],
    defaultMode: 'sport',
    loads: [
      { id: 'driver', label: 'Driver', payloadKg: 75 },
      { id: 'family', label: 'Family + luggage', payloadKg: 455 },
    ],
    overlays: ['suspension', 'motors', 'power'],
    finish: 'cruise',
    cruiseKmh: 120,
    chassis: { airSuspension: true, squatDegPerG: 1.0 },
    ghost: { slug: 'xpeng-g9l', variantId: '755-ultra-awd' },
    camera: 'hero',
    callouts: [
      { cue: 'launch', text: 'Launch. Two motors, full power: the tail squats and the air suspension holds the body level.' },
      { cue: 'pull', text: '100 km/h in under three seconds with the driver alone.' },
      { cue: 'target', text: '150 km/h. Off the power.' },
      { cue: 'cruise', text: 'Cruising at 120 km/h: the body is level, the motors are idling along.' },
    ],
    claims: [
      {
        text: 'The refreshed 7X reaches 100 km/h in 2.98 s.',
        source: { label: 'Paul Tan, 7X facelift, 22 October 2025', url: 'https://paultan.org/2025/10/22/zeekr-7x-facelift-revealed-900v-architecture-6c-dc-charging-802-km-cltc-795-ps-0-100-km-h-2-98-secs/' },
      },
      {
        text: 'The Magic Carpet air suspension package is air suspension, CCD electromagnetic dampers and a smart Magic Carpet: the 4WD 7X carries it.',
        source: { label: 'Autohome launch article, 23 September 2024', url: 'https://chejiahao.autohome.com.cn/info/17026490' },
      },
    ],
    simulated:
      'The 0–150 time, the load (a family of five and luggage, 455 kg), the squat, the split between the two motors and the energy are ours; the 7X’s kerb weight is not in our data, so the load is a ratio of an assumed 2.3 t.',
  },
  sources: [
    { label: 'Paul Tan - 7X facelift, 900 V, 802 km', url: 'https://paultan.org/2025/10/22/zeekr-7x-facelift-revealed-900v-architecture-6c-dc-charging-802-km-cltc-795-ps-0-100-km-h-2-98-secs/' },
    { label: 'Wikipedia - Zeekr 7X', url: 'https://en.wikipedia.org/wiki/Zeekr_7X' },
  ],
};
