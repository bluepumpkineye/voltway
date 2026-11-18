import type { Vehicle } from './schema';
import { ownPaints } from './own-paints';

/**
 * XPeng Mona L05 (小鹏MONA L05), the tenth car. Exterior first (2026-11-17): the body, wheels, lamps and tail are built
 * from Autohome's studio set for series 8662 (blender/reference/xpeng-mona-l05, local only; blender/scripts/mona_*.py).
 * The cabin, the HMI, the X-ray parts and the Tech demonstrations are not built yet, so the car is showroom-only.
 *
 * Figures: MIIT filing and launch coverage (Carnewschina 2026-10-29, CnEVPost 2026-10-15, Wikipedia as edited 2026-11-06).
 * The sources disagree on some figures; the ones used here are noted in `dataCaveat`.
 */
export const xpengMonaL05: Vehicle = {
  slug: 'xpeng-mona-l05',
  brand: 'XPeng',
  model: 'Mona L05',
  group: 'XPeng',
  bodyStyle: 'SUV',
  year: 2026,
  tagline: 'Mid-size fastback e-SUV with a 17.3" screen, a 26.8" HUD, a 702 L boot and Turing-chip driver assistance, from about RMB 145,000.',
  summary:
    'XPeng’s Mona L05 (小鹏MONA L05, launched 29 October 2026) is a 4,870 mm five-seat fastback SUV on a 2,940 mm wheelbase: a smooth, grille-less nose under slim smoked headlamps, a black-roofed greenhouse that ends in a ducktail lip, and a full-width tail light bar. A single 183 kW rear motor drives either a 58.2 or 71.1 kWh LFP battery (up to 635 km CLTC) or the 37.2 kWh Super Range Extender (1,310 km combined). Inside, a 17.3" centre screen and a 26.8" head-up display replace the instrument cluster, with a zero-gravity passenger seat and a 702 L boot (1,913 L folded) plus a 102 L frunk on the BEVs.',
  dimensions: {
    lengthMm: 5010,
    widthMm: 1930,
    heightMm: 1636,
    wheelbaseMm: 2940,
    kerbWeightKg: 1995,
  },
  variants: [
    {
      id: '635-ultra-se',
      name: 'EV 635 Ultra SE (纯电635 Ultra SE)',
      drive: 'RWD',
      battery: { capacityKwh: 71.1, chemistry: 'LFP', chargeMinutes10to80: 19 },
      performance: { powerKw: 183, torqueNm: 280, zeroTo100S: 6.8, motorCount: 1 },
      range: [{ cycle: 'CLTC', km: 635 }],
      priceCny: 176800,
    },
    {
      id: '635-max',
      name: 'EV 635 Max (纯电635 Max)',
      drive: 'RWD',
      battery: { capacityKwh: 71.1, chemistry: 'LFP', chargeMinutes10to80: 19 },
      performance: { powerKw: 183, torqueNm: 280, zeroTo100S: 6.8, motorCount: 1 },
      range: [{ cycle: 'CLTC', km: 635 }],
      priceCny: 164800,
    },
    {
      id: '535-max',
      name: 'EV 535 Max (纯电535 Max)',
      drive: 'RWD',
      battery: { capacityKwh: 58.2, chemistry: 'LFP', chargeMinutes10to80: 19 },
      performance: { powerKw: 183, torqueNm: 280, zeroTo100S: 7.3, motorCount: 1 },
      range: [{ cycle: 'CLTC', km: 535 }],
      priceCny: 149800,
    },
    {
      id: 'erev-1310-ultra-se',
      name: 'Super EREV 1310 Ultra SE (超级增程1310 Ultra SE)',
      drive: 'RWD',
      battery: { capacityKwh: 37.2, chemistry: 'LFP', chargeMinutes10to80: 15 },
      performance: { powerKw: 183, torqueNm: 280, motorCount: 1, topSpeedKmh: 180 },
      range: [{ cycle: 'CLTC', km: 310 }],
      priceCny: 166800,
    },
    {
      id: 'erev-1310-max',
      name: 'Super EREV 1310 Max (超级增程1310 Max)',
      drive: 'RWD',
      battery: { capacityKwh: 37.2, chemistry: 'LFP', chargeMinutes10to80: 15 },
      performance: { powerKw: 183, torqueNm: 280, motorCount: 1, topSpeedKmh: 180 },
      range: [{ cycle: 'CLTC', km: 310 }],
      priceCny: 154800,
    },
  ],
  cockpit: {
    os: 'XOS',
    skin: 'xos',
    accentColor: '#00D2FF',
    ambientLighting: true,
    ambientHue: 232,
    defaultTheme: 'dark',
    screens: [
      { id: 'center', label: '17.3" 3K Centre Touchscreen', diagonalIn: 17.3, role: 'center', interactive: true },
      { id: 'hud', label: '26.8" Head-Up Display (the instrument panel)', diagonalIn: 26.8, role: 'hud' },
      { id: 'rear', label: '17.3" Rear Ceiling Screen (optional)', diagonalIn: 17.3, role: 'rear' },
    ],
  },
  assets: {
    modelUrl: '/models/xpeng-mona-l05.glb',
    interiorModelUrl: '/models/xpeng-mona-l05-interior.glb',
    // lit by the shared showroom hall, shaded by the cabin's occlusion atlas (docs/3d-pipeline.md, "The hall look")
    interiorProbeUrl: '/models/cabin-hall.hdr',
    cabinGain: 0.85,
    showroomOnly: true,
    outside: {
      view: '/models/xpeng-mona-l05-outside.jpg',
      light: '/models/xpeng-mona-l05-outside-light.hdr',
      exteriorTurnDeg: 182.0,
      sun: { direction: [0.5785, 0.6134, 0.5376], color: '#fffbd2', intensity: 4.31 },
      ground: { height: 1.7, radius: 45 },
    },
    studioShadow: { url: '/models/xpeng-mona-l05-shadow.webp', size: [8.018, 5.798], centre: [0.066, 0] },
    heroColor: '#8c7c97',
    // the seat's eye = the bight (+0.03) + 0.03 (docs/3d-pipeline.md 3.1 rule 4); the Drive camera stands 12 cm behind it,
    // 6 cm ahead of the headrest's face (the first build kept the Voyah's [-0.28, ...] with seats 0.2 m too far back)
    driverEye: [0.06, 0.41, 1.24],
    // the Interior tab looks from between the front seats: from the driver's eye the wheel (0.4 m ahead) fills the picture
    driverView: { back: 0.14, out: -0.41, look: [0.142, -0.04, 0.0] },
  },
  configurator: {
    paintMaterial: 'M_Paint_MONA_Purple',
    paints: [
      {
        id: 'mona-purple',
        name: 'Purple',
        nameZh: '紫色',
        swatch: '#8c7c97',
        finish: { color: '#6f6079', roughness: 0.26, metalness: 0.32, clearcoat: 1, clearcoatRoughness: 0.03 },
      },
      {
        id: 'mona-white',
        name: 'White',
        nameZh: '白色',
        swatch: '#e8e8ea',
        finish: { color: '#d4d5d8', roughness: 0.24, metalness: 0.1, clearcoat: 1, clearcoatRoughness: 0.03 },
      },
      {
        id: 'mona-black',
        name: 'Black',
        nameZh: '黑色',
        swatch: '#17181a',
        finish: { color: '#0c0d0f', roughness: 0.2, metalness: 0.12, clearcoat: 1, clearcoatRoughness: 0.025 },
      },
      {
        id: 'mona-silver',
        name: 'Silver',
        nameZh: '银色',
        swatch: '#b9bec4',
        finish: { color: '#9aa0a8', roughness: 0.28, metalness: 0.58, clearcoat: 1, clearcoatRoughness: 0.03 },
      },
      {
        id: 'mona-green',
        name: 'Green',
        nameZh: '绿色',
        swatch: '#2c9a89',
        finish: { color: '#1f8372', roughness: 0.27, metalness: 0.42, clearcoat: 1, clearcoatRoughness: 0.03 },
      },
      {
        id: 'mona-grey',
        name: 'Grey',
        nameZh: '灰色',
        swatch: '#9aa3b0',
        finish: { color: '#818b99', roughness: 0.27, metalness: 0.46, clearcoat: 1, clearcoatRoughness: 0.03 },
      },
      ...ownPaints('matt-grey'),
    ],
    trims: [
      // The five interiors XPENG shows in its Cabin 360 (xpeng.guru, the Chinese car): two standard and three ROAM. The cabin is
      // built in the first, Light Grey. The colours are MEASURED from the panoramas (scripts/photo-tools/pano_probe.cjs, patch
      // means in the same views for all five; docs/xpeng-pano-benchmark.md), then set so the viewer displays about the same.
      // Only the dash, wheel, shells, seat leather, console/door leather and the piping accent change between them; the
      // panoramas show the other surfaces (pale seats and console, dark headliner) alike in the four non-dark trims.
      // The seat leather carries its colour in a baked texture, so its entry is a MULTIPLIER on that map (the seats' pale
      // leather (190, 199, 217) times it), not a colour. The green paint cannot be combined with Light Grey (the maker).
      {
        id: 'light-grey',
        name: 'Light Grey',
        nameZh: '气宇灰',
        swatch: ['#c8cfdb', '#363d45'],
      },
      {
        id: 'dark-grey',
        name: 'Dark Grey',
        nameZh: '深空灰',
        swatch: ['#565c64', '#2b3037'],
        colors: {
          INT_Dash_Lav: '#2b3037',
          INT_Band_Fabric: '#30353d',
          INT_Wheel_Fabric: '#1d2026',
          INT_Seat_Shell: '#1b1f24',
          INT_Leather_White: '#767877',
          INT_Leather_Smooth: '#51565e',
          INT_Piping_Accent: '#c9e04a',
        },
      },
      {
        id: 'iris',
        name: 'Iris (ROAM)',
        nameZh: '鸢尾紫',
        swatch: ['#c8cfdb', '#545462'],
        colors: {
          INT_Dash_Lav: '#3e414e',
          INT_Band_Fabric: '#464856',
          INT_Wheel_Fabric: '#4d4d5a',
          INT_Seat_Shell: '#4e4653',
          INT_Piping_Accent: '#a8aec6',
        },
      },
      {
        id: 'titanium-green',
        name: 'Titanium Green (ROAM)',
        nameZh: '钛荧绿',
        swatch: ['#c8cfdb', '#1a7a6c'],
        colors: {
          INT_Dash_Lav: '#21262e',
          INT_Band_Fabric: '#242932',
          INT_Wheel_Fabric: '#1e2228',
          INT_Seat_Shell: '#21262a',
          INT_Piping_Accent: '#1a7a6c',
        },
      },
      {
        id: 'star-purple',
        name: 'Star Purple (ROAM)',
        nameZh: '星脉紫',
        swatch: ['#c8cfdb', '#6a4aa8'],
        colors: {
          INT_Dash_Lav: '#21262e',
          INT_Band_Fabric: '#242932',
          INT_Wheel_Fabric: '#1e2228',
          INT_Seat_Shell: '#21262a',
          INT_Piping_Accent: '#6a4aa8',
        },
      },
    ],
    caliperMaterial: 'M_Caliper_Mona_Lime',
    calipers: [
      { id: 'mona_lime', name: 'Lime', nameZh: '青柠黄', color: '#c8e600' },
      { id: 'black', name: 'Black', color: '#17181a', metalness: 0, roughness: 0.3, ours: true },
      { id: 'silver', name: 'Silver', color: '#8a8e94', ours: true },
    ],
    wheels: [
      {
        id: 'blade20',
        name: '20" Diamond-Cut Five-V',
        nameZh: '20英寸多辐切削轮毂',
        size: '20"',
        tyres: '245/45 R20',
        node: 'XpengMonaL05_Wheels',
        caliper: 'mona_lime',
      },
    ],
    sources: [
      { label: 'Autohome - XPeng Mona L05 photographs (Series 8662)', url: 'https://car.autohome.com.cn/pic/series/8662.html' },
      { label: 'Carnewschina - Xpeng Mona L05 launched in China', url: 'https://carnewschina.com/2026/10/29/xpeng-mona-l05-launched-in-china-at-21720-usd/' },
    ],
  },
  openings: [
    { id: 'doorFL', node: 'XpengMonaL05_Door_FL', cardNode: 'int_door_L', frameNode: 'XpengMonaL05_DoorFrame_FL', deg: -75, xrayHide: true },
    { id: 'doorFR', node: 'XpengMonaL05_Door_FR', cardNode: 'int_door_R', frameNode: 'XpengMonaL05_DoorFrame_FR', deg: 75, xrayHide: true },
    { id: 'doorRL', node: 'XpengMonaL05_Door_RL', cardNode: 'int_rdoor_L', frameNode: 'XpengMonaL05_DoorFrame_RL', deg: -68, xrayHide: true },
    { id: 'doorRR', node: 'XpengMonaL05_Door_RR', cardNode: 'int_rdoor_R', frameNode: 'XpengMonaL05_DoorFrame_RR', deg: 68, xrayHide: true },
    { id: 'frunk', node: 'XpengMonaL05_Bonnet', axis: 'z', deg: 62 },
    {
      id: 'boot',
      node: 'XpengMonaL05_Tailgate',
      cardNode: 'int_tailgate',
      axis: 'z',
      deg: -78,
      hides: ['int_parcel_shelf', 'int_rear_sill'],
      hidesOutside: ['int_cpillar', 'int_cpillar_flange', 'int_qtr_lower'],
    },
  ],
  lights: { projector: { material: 'M_Lamp_Lens' } },
  charging: {
    window: { from: 10, to: 80, minutes: 19 },
    packKwh: 71.1,
    connector: 'GB/T',
    port: { side: 'right', published: false, where: 'Right rear quarter panel (as photographed)' },
    claims: [
      {
        text: 'The 58.2 and 71.1 kWh LFP packs charge 10 to 80 % in 19 minutes; the 37.2 kWh range-extender pack in 15 minutes.',
        source: { label: 'Wikipedia - XPeng Mona L05', url: 'https://en.wikipedia.org/wiki/XPeng_Mona_L05' },
      },
    ],
    simulated:
      'A simulation based on the published 10 to 80 % window (19 minutes on the BEV packs). XPeng’s peak charging power and pack voltage are not given in the coverage found, so the taper, the pedestal and the connector motion are illustrative.',
  },
  sources: [
    { label: 'Autohome - XPeng Mona L05 (Series 8662)', url: 'https://car.autohome.com.cn/pic/series/8662.html' },
    { label: 'Carnewschina - Xpeng Mona L05 launched in China at 21,720 USD', url: 'https://carnewschina.com/2026/10/29/xpeng-mona-l05-launched-in-china-at-21720-usd/' },
    { label: 'CnEVPost - Xpeng opens Mona L05 pre-sales', url: 'https://cnevpost.com/2026/10/15/xpeng-opens-mona-l05-pre-sales/' },
    { label: 'Wikipedia - XPeng Mona L05', url: 'https://en.wikipedia.org/wiki/XPeng_Mona_L05' },
  ],
  dataCaveat:
    'Launched 29 October 2026, so figures come from launch coverage and the MIIT filing and can still change. Prices are the launch guide prices in RMB (Carnewschina); the pre-sale prices were 15,000 to 20,000 RMB higher and a limited-time offer takes about 5,000 off. An entry "EV 560 Plus" trim (about RMB 144,800) is not listed because its battery is not published in the sources found. The 0-100 km/h times (6.8 s on the 71.1 kWh pack, 7.3 s on the 58.2 kWh) come from Wikipedia and could not be matched to trims with certainty. The EREV’s 310 km is its CLTC electric range; its 1,310 km is the combined figure. Peak charging power and pack voltage are not published in the coverage found. The 3D model is exterior-only for now.',
};
