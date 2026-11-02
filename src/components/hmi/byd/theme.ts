import type React from 'react';
import { useVehicleStore, type HmiTheme } from '@/store/vehicle-store';

/**
 * BYD's DiLink in the Seal, as the car's centre screen draws it.
 *
 * Read off Autohome's photographs of the real Seal's screen (blender/reference/byd-seal-ev/hmi, series 6394,
 * cat 10 #23-40 dark and #90-101 light): a full-bleed wallpaper home with a row of glass capsules, every
 * other page on a black (night) or pale blue (day) ground, a small status bar with the music source and
 * the temperatures, a tall system bar along the bottom (back, home, settings, the fan, the driver's
 * temperature, the seat, the passenger's temperature, the demister, the apps, split screen, windows) and a
 * light pill for the chosen state. Sizes are in the HMI's 1280 x 800 space.
 */
export interface ByTheme {
  tone: HmiTheme;
  /** page ground behind an app */
  bg: string;
  text: string;
  text2: string;
  text3: string;
  /** a card on the ground, and the pill of the chosen menu row / segment */
  card: string;
  pill: string;
  pillText: string;
  /** the segmented control's track and its chosen segment */
  seg: string;
  segOn: string;
  segOnText: string;
  line: string;
  /** the chosen state: a switch that is on, the active tab, a button */
  accent: string;
  /** the bottom bar over a page */
  bar: string;
  barIcon: string;
}

export const BY: Record<HmiTheme, ByTheme> = {
  dark: {
    tone: 'dark',
    bg: 'radial-gradient(110% 90% at 70% 40%, #101820 0%, #06090d 70%)',
    text: 'rgba(255,255,255,0.93)',
    text2: 'rgba(255,255,255,0.62)',
    text3: 'rgba(255,255,255,0.38)',
    card: 'rgba(255,255,255,0.07)',
    pill: 'rgba(130,150,170,0.30)',
    pillText: '#fff',
    seg: 'rgba(255,255,255,0.10)',
    segOn: '#d9e1ea',
    segOnText: '#0a1018',
    line: 'rgba(255,255,255,0.10)',
    accent: '#3ccf8e',
    bar: '#06090d',
    barIcon: 'rgba(255,255,255,0.92)',
  },
  light: {
    tone: 'light',
    bg: 'linear-gradient(135deg, #eef4fb 0%, #dfeaf6 55%, #d2e2f3 100%)',
    text: '#17263a',
    text2: 'rgba(23,38,58,0.64)',
    text3: 'rgba(23,38,58,0.40)',
    card: 'rgba(255,255,255,0.6)',
    pill: 'rgba(255,255,255,0.85)',
    pillText: '#17263a',
    seg: 'rgba(120,150,190,0.16)',
    segOn: '#1f7bea',
    segOnText: '#fff',
    line: 'rgba(23,38,58,0.10)',
    accent: '#1f7bea',
    bar: '#e6eef8',
    barIcon: '#17263a',
  },
};

/** The theme in force: the store's, read once per render. */
export function useBy(): ByTheme {
  const tone = useVehicleStore((s) => s.hmiTheme);
  return BY[tone];
}

/** The status bar floats on the page; the system bar sits under it. */
export const STATUS_H = 62;
export const BAR_H = 90;

/** Style helper for a glass capsule over the wallpaper. */
export const glass = (a = 0.5, blur = 18): React.CSSProperties => ({
  background: `rgba(14,26,44,${a})`,
  backdropFilter: `blur(${blur}px) saturate(1.2)`,
  WebkitBackdropFilter: `blur(${blur}px) saturate(1.2)`,
});
