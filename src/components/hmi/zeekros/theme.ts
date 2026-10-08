import { useVehicleStore, type HmiTheme } from '@/store/vehicle-store';

/**
 * ZEEKR OS in the car, as the 7X shows it.
 *
 * Read off Autohome's photographs of the car's screen (blender/reference/zeekr-7x/hmi, cat 10
 * #16-80): a light interface (a lavender-white sheet over a 3D showroom scene, black glyphs, an
 * orange accent, a red AUTO) and a dark one. The screen is 16:10; sizes are in the HMI's
 * 1280 x 800 space (the photographs measure about 0.88 HMI pixels to the photographed pixel).
 */
export interface ZeekrTheme {
  tone: HmiTheme;
  /** the sheet that slides up over the home scene, and a card on it */
  sheet: string;
  card: string;
  cardOn: string;
  text: string;
  text2: string;
  text3: string;
  line: string;
  /** the accent: the page indicator, the on state of a switch */
  accent: string;
  /** the red of AUTO and of the selected tab's outline */
  red: string;
  blue: string;
  green: string;
  /** the bottom bar over a sheet page and over the scene */
  bar: string;
  barScene: string;
  /** the pill buttons ("All off") */
  pill: string;
  pillText: string;
}

export const ZK: Record<HmiTheme, ZeekrTheme> = {
  light: {
    tone: 'light',
    sheet: '#eef0fb',
    card: 'rgba(255,255,255,0.72)',
    cardOn: '#ffffff',
    text: '#111318',
    text2: 'rgba(17,19,24,0.62)',
    text3: 'rgba(17,19,24,0.38)',
    line: 'rgba(17,19,24,0.10)',
    accent: '#ff5b24',
    red: '#c4162f',
    blue: '#2f6fe4',
    green: '#22a860',
    bar: '#eef0fb',
    barScene: 'rgba(238,240,250,0.58)',
    pill: '#15161a',
    pillText: '#ffffff',
  },
  dark: {
    tone: 'dark',
    sheet: '#15171e',
    card: 'rgba(255,255,255,0.08)',
    cardOn: 'rgba(255,255,255,0.18)',
    text: 'rgba(255,255,255,0.95)',
    text2: 'rgba(255,255,255,0.62)',
    text3: 'rgba(255,255,255,0.38)',
    line: 'rgba(255,255,255,0.10)',
    accent: '#ff6a33',
    red: '#ff4d5e',
    blue: '#5a8bff',
    green: '#35c46a',
    bar: '#15171e',
    barScene: 'rgba(16,18,24,0.62)',
    pill: '#f2f3f8',
    pillText: '#15161a',
  },
};

/** The theme in force: the store's, read once per render. */
export function useZk(): ZeekrTheme {
  const tone = useVehicleStore((s) => s.hmiTheme);
  return ZK[tone];
}

/** Layout of the 1280 x 800 screen: the status bar over the scene, the sheet, the bottom bar. */
export const STATUS_H = 50;
export const BAR_H = 62;
export const SHEET_TOP = 211;
export const SHEET_BOTTOM = 800 - BAR_H;
