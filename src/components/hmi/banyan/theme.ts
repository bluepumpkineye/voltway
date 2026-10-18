import { useVehicleStore, type HmiTheme } from '@/store/vehicle-store';

/**
 * NIO Banyan Smart Cockpit design tokens and layout dimensions.
 *
 * Authored for the 15.6" AMOLED Central Display running NIO Banyan OS (NT2.0 platform).
 * Space is fixed at 1280 x 800 screen pixels and scaled dynamically to the 3D dashboard quad.
 */

export interface BanyanTheme {
  tone: HmiTheme;
  background: string;
  sheet: string;
  card: string;
  cardActive: string;
  cardHover: string;
  border: string;
  borderActive: string;
  text: string;
  textSecondary: string;
  textMuted: string;
  accent: string;
  accentGlow: string;
  blue: string;
  gold: string;
  emerald: string;
  red: string;
  bar: string;
  barOverScene: string;
  pill: string;
  pillActive: string;
}

export const BANYAN: Record<HmiTheme, BanyanTheme> = {
  dark: {
    tone: 'dark',
    background: '#0a0d14',
    sheet: '#0e121b',
    card: 'rgba(255, 255, 255, 0.055)',
    cardActive: 'rgba(0, 194, 168, 0.14)',
    cardHover: 'rgba(255, 255, 255, 0.09)',
    border: 'rgba(255, 255, 255, 0.08)',
    borderActive: 'rgba(0, 194, 168, 0.45)',
    text: 'rgba(255, 255, 255, 0.96)',
    textSecondary: 'rgba(255, 255, 255, 0.62)',
    textMuted: 'rgba(255, 255, 255, 0.38)',
    accent: '#00C2A8', // NIO signature pure cyan
    accentGlow: 'rgba(0, 194, 168, 0.28)',
    blue: '#0084FF',
    gold: '#D4AF37', // Executive edition accent
    emerald: '#10B981',
    red: '#EF4444',
    bar: 'rgba(14, 18, 27, 0.94)',
    barOverScene: 'rgba(10, 13, 20, 0.68)',
    pill: 'rgba(255, 255, 255, 0.08)',
    pillActive: '#00C2A8',
  },
  light: {
    tone: 'light',
    background: '#eef2f6',
    sheet: '#f4f6fa',
    card: 'rgba(255, 255, 255, 0.85)',
    cardActive: 'rgba(0, 194, 168, 0.15)',
    cardHover: '#ffffff',
    border: 'rgba(0, 0, 0, 0.08)',
    borderActive: '#00C2A8',
    text: '#11151c',
    textSecondary: 'rgba(17, 21, 28, 0.65)',
    textMuted: 'rgba(17, 21, 28, 0.40)',
    accent: '#00A38D',
    accentGlow: 'rgba(0, 163, 141, 0.22)',
    blue: '#0070D6',
    gold: '#B89228',
    emerald: '#059669',
    red: '#DC2626',
    bar: 'rgba(244, 246, 250, 0.94)',
    barOverScene: 'rgba(238, 242, 246, 0.72)',
    pill: 'rgba(0, 0, 0, 0.06)',
    pillActive: '#00A38D',
  },
};

export function useBanyan(): BanyanTheme {
  const tone = useVehicleStore((s) => s.hmiTheme);
  return BANYAN[tone] ?? BANYAN.dark;
}

export const TOP_BAR_H = 46;
export const BOTTOM_BAR_H = 88;
export const SHEET_TOP = 46;
