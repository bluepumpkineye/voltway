import type React from 'react';
import { useVehicleStore, type HmiTheme } from '@/store/vehicle-store';

/**
 * The Avatr 06T's HarmonyOS cockpit, as the car's centre screen draws it.
 *
 * Read off Autohome's photographs of the car's screen (blender/reference/avatr-06t/hmi, cat 10 #15-46 and
 * #75-96): a wallpaper home with a row of glass cards, and every page on a pale blue-grey frosted ground
 * (a deep blue blurred one for the App Centre), dark text, a royal-blue selected tab / switch / chip.
 * Sizes are in the HMI's 1280 x 800 space.
 */
export interface AvTheme {
  tone: HmiTheme;
  /** page ground behind an app */
  bg: string;
  text: string;
  text2: string;
  text3: string;
  /** a pale card on the ground, a tile, and a tile that is on */
  card: string;
  tile: string;
  tileOn: string;
  tileOnText: string;
  /** segmented-control track and its chosen segment */
  seg: string;
  segOn: string;
  line: string;
  blue: string;
  orange: string;
  red: string;
  green: string;
  /** the bottom bar over a page */
  bar: string;
  barIcon: string;
}

export const AV: Record<HmiTheme, AvTheme> = {
  light: {
    tone: 'light',
    bg: 'radial-gradient(120% 90% at 30% 20%, #dfe5f3 0%, #cbd3e8 55%, #bcc7e2 100%)',
    text: '#161b2e',
    text2: 'rgba(22,27,46,0.64)',
    text3: 'rgba(22,27,46,0.40)',
    card: 'rgba(255,255,255,0.46)',
    tile: 'rgba(255,255,255,0.5)',
    tileOn: 'rgba(255,255,255,0.95)',
    tileOnText: '#161b2e',
    seg: 'rgba(110,126,176,0.20)',
    segOn: 'rgba(255,255,255,0.92)',
    line: 'rgba(22,27,46,0.10)',
    blue: '#2c46f2',
    orange: '#e0582a',
    red: '#e5352f',
    green: '#2fae5f',
    bar: 'rgba(222,228,242,0.94)',
    barIcon: '#161b2e',
  },
  dark: {
    tone: 'dark',
    bg: 'radial-gradient(120% 90% at 30% 20%, #1c2540 0%, #10162b 55%, #0a0e1d 100%)',
    text: 'rgba(255,255,255,0.95)',
    text2: 'rgba(255,255,255,0.64)',
    text3: 'rgba(255,255,255,0.38)',
    card: 'rgba(255,255,255,0.08)',
    tile: 'rgba(255,255,255,0.10)',
    tileOn: 'rgba(236,240,252,0.94)',
    tileOnText: '#10162b',
    seg: 'rgba(255,255,255,0.10)',
    segOn: 'rgba(236,240,252,0.94)',
    line: 'rgba(255,255,255,0.10)',
    blue: '#6b86ff',
    orange: '#ff7a45',
    red: '#ff5a4f',
    green: '#35c46a',
    bar: 'rgba(10,14,30,0.88)',
    barIcon: 'rgba(255,255,255,0.94)',
  },
};

/** The theme in force: the store's, read once per render. */
export function useAv(): AvTheme {
  const tone = useVehicleStore((s) => s.hmiTheme);
  return AV[tone];
}

/** The status bar floats on the page; the bottom bar sits under it. */
export const STATUS_H = 66;
export const BAR_H = 72;

/** Style helper for a glass surface over the wallpaper. */
export const glass = (a = 0.34, blur = 20): React.CSSProperties => ({
  background: `rgba(8,14,36,${a})`,
  backdropFilter: `blur(${blur}px) saturate(1.2)`,
  WebkitBackdropFilter: `blur(${blur}px) saturate(1.2)`,
});
