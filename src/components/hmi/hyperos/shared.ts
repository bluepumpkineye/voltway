'use client';

import React from 'react';

/**
 * The demo playlist. Invented artists and titles, with generated cover art
 * (no real album covers ship). `tint` colours the music card, as HyperOS
 * tints it from the cover.
 */
export const TRACKS = [
  {
    title: 'Neon Arterial', artist: 'Hong Kong Sunset', duration: 214,
    art: 'radial-gradient(circle at 30% 25%, #ff9ec7, transparent 55%), radial-gradient(circle at 75% 70%, #7b4dff, transparent 60%), linear-gradient(145deg, #3a1f6e, #120a24)',
    tint: '#4a2a7a',
  },
  {
    title: 'Bund at 3AM', artist: 'Shanghai Tape Club', duration: 187,
    art: 'radial-gradient(circle at 70% 30%, #ffd36b, transparent 50%), radial-gradient(circle at 25% 75%, #ff5f45, transparent 55%), linear-gradient(160deg, #5a1d14, #1a0906)',
    tint: '#6a2a18',
  },
  {
    title: 'Gobi Transmission', artist: 'Silk Road Signal', duration: 243,
    art: 'radial-gradient(circle at 40% 35%, #8fe3ff, transparent 50%), radial-gradient(circle at 70% 80%, #1f8fff, transparent 60%), linear-gradient(150deg, #0d3450, #04121d)',
    tint: '#123e5e',
  },
  {
    title: 'Pearl River Delta', artist: 'Nanfang', duration: 199,
    art: 'radial-gradient(circle at 65% 30%, #b6ff9e, transparent 50%), radial-gradient(circle at 30% 70%, #1fbf8f, transparent 60%), linear-gradient(150deg, #0f4032, #04150f)',
    tint: '#14493a',
  },
];

export function mmss(s: number): string {
  const m = Math.floor(s / 60);
  return `${m}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
}

const DAYS = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];

/**
 * The time, ticking. Empty until mounted: the HMI is also server-rendered
 * (the capture route), and a server clock would not match the browser's.
 */
export function useClock() {
  const [now, setNow] = React.useState<Date | null>(null);
  React.useEffect(() => {
    setNow(new Date());
    const id = window.setInterval(() => setNow(new Date()), 15_000);
    return () => window.clearInterval(id);
  }, []);
  if (!now) return { hm: '', day: '', date: '' };
  return {
    hm: `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`,
    day: DAYS[now.getDay()],
    date: `${now.getMonth() + 1}/${now.getDate()}`,
  };
}
