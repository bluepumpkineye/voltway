/**
 * DiLink 150 in the Denza Z9, as the car's centre screen draws it.
 *
 * Read off Autohome's photographs of the car's screen (blender/reference/denza-z9/hmi, cat 10 #29-100):
 * a bright home (a pale sky over curved white dunes with the car standing on them and a row of cards
 * along the bottom), and every other page on a deep blue-black ground lit by blue gradients, white text,
 * a bright blue accent for the chosen state. The screen is 16:10; sizes are in the HMI's 1280 x 800 space.
 */
export interface DilinkTheme {
  /** the dark ground of every page but the home, and a card on it */
  ground: string;
  card: string;
  cardOn: string;
  text: string;
  text2: string;
  text3: string;
  line: string;
  /** the chosen state: the blue of a selected tab, a switch that is on */
  accent: string;
  accent2: string;
  /** a warm state (the hazard key's red, a heated seat) */
  warm: string;
  green: string;
  /** the bottom bar, on the home and over a page */
  barHome: string;
  barPage: string;
}

export const DL: DilinkTheme = {
  ground: '#0a0f1b',
  card: 'rgba(255,255,255,0.075)',
  cardOn: 'rgba(76,140,255,0.28)',
  text: 'rgba(255,255,255,0.96)',
  text2: 'rgba(255,255,255,0.64)',
  text3: 'rgba(255,255,255,0.38)',
  line: 'rgba(255,255,255,0.12)',
  accent: '#3d8bff',
  accent2: '#35d6c8',
  warm: '#ff6a4d',
  green: '#34d27b',
  barHome: 'rgba(238,244,255,0.55)',
  barPage: '#0a0f1b',
};

export const STATUS_H = 40;
export const BAR_H = 58;
