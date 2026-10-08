import React from 'react';
import { useVehicleStore, type HmiTheme } from '@/store/vehicle-store';

/**
 * Huawei HarmonyOS in the car, as the Luxeed RX shows it.
 *
 * Read off Autohome's photographs of the car's screens (blender/reference/
 * luxeed-rx/hmi): a light and a dark theme, frosted glass over a wallpaper on
 * the desktop, flat pale panels and a beige-white "on" state in the apps, blue
 * for the climate controls and red for the radio. Sizes are in the HMI's
 * 1280 x 800 space (the 16.1" panel is 16:10 and the photographs measure about
 * 0.88 HMI pixels to the photographed pixel).
 */
export interface HaTheme {
  tone: HmiTheme;
  /** page ground behind an app */
  bg: string;
  text: string;
  text2: string;
  text3: string;
  /** a flat tile or card in an app, and its pressed / selected state */
  tile: string;
  tileOn: string;
  tileOnText: string;
  /** a raised row inside a page (settings cards) */
  card: string;
  /** segmented-control track and its selected segment */
  seg: string;
  segOn: string;
  line: string;
  blue: string;
  red: string;
  green: string;
  /** the bottom bar over an app page */
  bar: string;
  /** the overlay panels (App Centre, volume) */
  panel: string;
  /** icons in the bottom bar over an app page */
  barIcon: string;
}

export const HA: Record<HmiTheme, HaTheme> = {
  dark: {
    tone: 'dark',
    bg: '#0a0b0e',
    text: 'rgba(255,255,255,0.95)',
    text2: 'rgba(255,255,255,0.62)',
    text3: 'rgba(255,255,255,0.38)',
    tile: 'rgba(255,255,255,0.11)',
    tileOn: '#ece3db',
    tileOnText: '#18181b',
    card: 'rgba(255,255,255,0.07)',
    seg: 'rgba(255,255,255,0.10)',
    segOn: '#ece3db',
    line: 'rgba(255,255,255,0.10)',
    blue: '#4a74ff',
    red: '#ff4a3f',
    green: '#35c46a',
    bar: 'rgba(8,9,13,0.80)',
    panel: 'rgba(38,36,40,0.94)',
    barIcon: 'rgba(255,255,255,0.92)',
  },
  light: {
    tone: 'light',
    bg: '#e9e7ea',
    text: '#15161a',
    text2: 'rgba(21,22,26,0.62)',
    text3: 'rgba(21,22,26,0.40)',
    tile: 'rgba(255,255,255,0.58)',
    tileOn: '#ffffff',
    tileOnText: '#15161a',
    card: 'rgba(255,255,255,0.62)',
    seg: 'rgba(120,118,128,0.16)',
    segOn: '#ffffff',
    line: 'rgba(21,22,26,0.10)',
    blue: '#2f56ee',
    red: '#e8322d',
    green: '#2fae5f',
    bar: 'rgba(236,234,237,0.92)',
    panel: 'rgba(240,238,241,0.95)',
    barIcon: 'rgba(21,22,26,0.88)',
  },
};

/** The theme in force: the store's, read once per render. */
export function useHa(): HaTheme {
  const tone = useVehicleStore((s) => s.hmiTheme);
  return HA[tone];
}

/** Bars: the status bar floats on the page; the bottom bar sits under it. */
export const STATUS_H = 66;
export const BAR_H = 65;
/** Page content lives between these two. */
export const BODY_TOP = STATUS_H;
export const BODY_BOTTOM = 800 - BAR_H;

/** The beige-white "on" colour of a tile over the dark desktop's glass. */
export const GLASS_ON = '#efe6de';

/** `rgba()` helper for the few computed fills. */
export function alpha(hex: string, a: number): string {
  const h = hex.replace('#', '');
  const n = parseInt(h.length === 3 ? h.split('').map((c) => c + c).join('') : h, 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`;
}

/** Style helper for a glass surface over the wallpaper. */
export const glass = (a = 0.14, blur = 22): React.CSSProperties => ({
  background: `rgba(255,255,255,${a})`,
  backdropFilter: `blur(${blur}px) saturate(1.2)`,
  WebkitBackdropFilter: `blur(${blur}px) saturate(1.2)`,
});
