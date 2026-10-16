/**
 * XOS Tianji in the XPeng G9L, as the car's centre screen draws it.
 *
 * Read off Autohome's photographs of the car's screen (blender/reference/xpeng-g9l/hmi, cat 10
 * #19-56): a light interface, a pale lavender-grey ground with white translucent cards, dark ink, a
 * deep indigo for the cards that carry controls (personalisation, headlamps, brightness), a green for
 * the air conditioning's power. The map is the home; every other page is a sheet over it. Sizes are in
 * the HMI's 1280 x 800 space.
 */
export interface XosTheme {
  ground: string;
  /** a card, a chosen card, a tile that is on */
  card: string;
  cardOn: string;
  tile: string;
  text: string;
  text2: string;
  text3: string;
  line: string;
  /** the indigo of the control cards, the green of the AC power button, the purple of the chosen state */
  indigo: string;
  indigo2: string;
  green: string;
  purple: string;
  red: string;
}

export const XO: XosTheme = {
  ground: '#e9e9f1',
  card: 'rgba(255,255,255,0.55)',
  cardOn: '#ffffff',
  tile: 'rgba(130,134,152,0.26)',
  text: '#1a1c26',
  text2: 'rgba(26,28,38,0.62)',
  text3: 'rgba(26,28,38,0.38)',
  line: 'rgba(26,28,38,0.12)',
  indigo: '#1d1a3c',
  indigo2: '#2b2760',
  green: '#1fb56a',
  purple: '#7a5cf0',
  red: '#e0423a',
};

export const STATUS_H = 44;
export const BAR_H = 62;
