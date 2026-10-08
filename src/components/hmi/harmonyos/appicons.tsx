import React from 'react';

/**
 * The coloured application icons of the App Centre, drawn here (the car's own
 * are the maker's artwork): a rounded square, a gradient and a simple glyph on
 * a 48 grid. The set and its order follow the App Centre in the photographs.
 */
export type AppId =
  | 'flex3d' | 'connect' | 'butler' | 'guide' | 'phone' | 'sound' | 'account' | 'video'
  | 'health' | 'btmusic' | 'calendar' | 'settings' | 'radio' | 'weather' | 'gallery' | 'usb'
  | 'camera' | 'dashcam' | 'market' | 'music' | 'life' | 'search' | 'care' | 'link';

export const APPS: { id: AppId; label: string }[] = [
  { id: 'flex3d', label: '3D Flex Space' },
  { id: 'connect', label: 'Connect' },
  { id: 'butler', label: 'Car Butler' },
  { id: 'guide', label: "Owner's Guide" },
  { id: 'phone', label: 'Phone' },
  { id: 'sound', label: 'Sound Cube' },
  { id: 'account', label: 'Account' },
  { id: 'video', label: 'Video' },
  { id: 'health', label: 'Health' },
  { id: 'btmusic', label: 'Bluetooth Music' },
  { id: 'calendar', label: 'Calendar' },
  { id: 'settings', label: 'Settings' },
  { id: 'radio', label: 'Radio' },
  { id: 'weather', label: 'Weather' },
  { id: 'gallery', label: 'Gallery' },
  { id: 'usb', label: 'USB Music' },
  { id: 'camera', label: 'Camera' },
  { id: 'dashcam', label: 'Dashcam' },
  { id: 'market', label: 'App Market' },
  { id: 'music', label: 'Music' },
  { id: 'life', label: 'Smart Life' },
  { id: 'search', label: 'Search' },
  { id: 'care', label: 'Cockpit Care' },
  { id: 'link', label: 'Cockpit Link' },
];

const W = '#fff';
const stroke = { fill: 'none', stroke: W, strokeWidth: 3, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };

const ART: Record<AppId, { bg: string; g: React.ReactNode }> = {
  flex3d: {
    bg: 'linear-gradient(160deg,#233a8a,#0b1230)',
    g: (
      <>
        <text x="24" y="19" textAnchor="middle" fontSize="15" fontWeight="800" fill={W}>3D</text>
        <path d="M9 33c0-3 2-4.500 5-5l3-3h14l3 3c3 .5 5 2 5 5v1H9z" fill={W} />
        <circle cx="16" cy="35" r="3" fill="#0b1230" stroke={W} strokeWidth="1.500" />
        <circle cx="33" cy="35" r="3" fill="#0b1230" stroke={W} strokeWidth="1.500" />
      </>
    ),
  },
  connect: {
    bg: 'linear-gradient(160deg,#47d25a,#1f9d3d)',
    g: (
      <>
        <path d="M10 13h22a4 4 0 0 1 4 4v10a4 4 0 0 1-4 4H20l-8 6v-6h-2a4 4 0 0 1-4-4V17a4 4 0 0 1 4-4z" fill={W} />
        <path d="M30 20l8-4v14l-8-4z" fill="#27ad45" />
      </>
    ),
  },
  butler: {
    bg: 'linear-gradient(160deg,#4aa0ff,#1f62d6)',
    g: (
      <>
        <path d="M14 30c-4 0-6-3-5-6s4-4 6-4c1-5 6-8 11-6 3 1 5 3 6 5 4-1 8 2 7 6-.5 2-2.500 5-6 5z" fill="none" stroke={W} strokeWidth="2.600" />
        <path d="M14 32l2-5a3 3 0 0 1 3-2h10a3 3 0 0 1 3 2l2 5v4h-3v-2H17v2h-3z" fill={W} />
      </>
    ),
  },
  guide: {
    bg: 'linear-gradient(160deg,#7e8cf5,#5446d8)',
    g: (
      <>
        <rect x="12" y="8" width="24" height="32" rx="4" fill={W} />
        <path d="M24 17v14" stroke="#5446d8" strokeWidth="4" strokeLinecap="round" />
        <circle cx="24" cy="12.500" r="2.300" fill="#5446d8" />
      </>
    ),
  },
  phone: {
    bg: 'linear-gradient(160deg,#4cd964,#1fa33a)',
    g: <path d="M14 11l5 1 2 7-3 2c2 4 5 7 9 9l2-3 7 2 1 5c0 2-2 4-4 4C20 38 10 28 10 15c0-2 2-4 4-4z" fill={W} />,
  },
  sound: {
    bg: 'linear-gradient(160deg,#fff,#eceaf3)',
    g: (
      <>
        {[[9, 18, 12, '#ff5f6d'], [15, 12, 24, '#ffb347'], [21, 8, 32, '#4ac4ff'], [27, 14, 20, '#7b6dff'], [33, 18, 12, '#ff6bd5']].map(([x, y, h, c]) => (
          <rect key={String(x)} x={Number(x)} y={Number(y)} width="5" height={Number(h)} rx="2.500" fill={String(c)} />
        ))}
      </>
    ),
  },
  account: {
    bg: 'linear-gradient(160deg,#fff,#f0eeee)',
    g: (
      <>
        <circle cx="24" cy="24" r="14" fill="#e53935" />
        <circle cx="24" cy="20" r="5" fill={W} />
        <path d="M14.500 33c2-4 5-6 9.500-6s7.500 2 9.500 6" fill={W} />
      </>
    ),
  },
  video: {
    bg: 'linear-gradient(160deg,#ffb23d,#f27c0a)',
    g: <path d="M16 12l20 12-20 12zM16 12v24" fill={W} stroke={W} strokeWidth="2" strokeLinejoin="round" />,
  },
  health: {
    bg: 'linear-gradient(160deg,#ffb23d,#f27c0a)',
    g: (
      <>
        <path d="M24 38C10 28 8 20 12 15c3-3 8-2 12 3 4-5 9-6 12-3 4 5 2 13-12 23z" fill="none" stroke={W} strokeWidth="3" />
        <path d="M12 26h6l3-5 4 9 3-4h8" {...stroke} strokeWidth="2.400" />
      </>
    ),
  },
  btmusic: {
    bg: 'linear-gradient(160deg,#4aa6ff,#1b6ee0)',
    g: <path d="M16 15l16 18-8 7V8l8 7-16 18" {...stroke} strokeWidth="3.400" />,
  },
  calendar: {
    bg: 'linear-gradient(160deg,#fff,#eef0f6)',
    g: (
      <>
        <rect x="9" y="11" width="30" height="28" rx="5" fill="#d9e6fb" />
        <rect x="9" y="11" width="30" height="9" rx="4" fill="#4f8ef7" />
        <path d="M17 8v6M31 8v6" stroke="#3a74e0" strokeWidth="3" strokeLinecap="round" />
        {[0, 1, 2].map((r) => [0, 1, 2, 3].map((c) => (
          <rect key={`${r}${c}`} x={13 + c * 6.500} y={24 + r * 5} width="4" height="3" rx="1" fill="#6aa0f8" />
        )))}
      </>
    ),
  },
  settings: {
    bg: 'linear-gradient(160deg,#8a8ec8,#4b4e8c)',
    g: (
      <>
        <path d="M9 28l3-9a5 5 0 0 1 4.700-3.400h14.600A5 5 0 0 1 36 19l3 9v7h-5v-3H14v3H9z" fill={W} />
        <circle cx="15" cy="27" r="2" fill="#4b4e8c" />
        <circle cx="33" cy="27" r="2" fill="#4b4e8c" />
      </>
    ),
  },
  radio: {
    bg: 'linear-gradient(160deg,#ff5148,#d7231a)',
    g: (
      <>
        <circle cx="24" cy="23" r="3.600" fill={W} />
        <path d="M24 28v10M16.500 15.500a10.500 10.500 0 0 0 0 15M31.500 15.500a10.500 10.500 0 0 1 0 15M11.500 11a17 17 0 0 0 0 24M36.500 11a17 17 0 0 1 0 24" {...stroke} strokeWidth="2.600" />
      </>
    ),
  },
  weather: {
    bg: 'linear-gradient(160deg,#58b4ff,#2169d9)',
    g: (
      <>
        <circle cx="19" cy="19" r="7" fill="#ffd54a" />
        <path d="M17 36a7 7 0 0 1-1-13.900A9.500 9.500 0 0 1 34.500 24 6.300 6.300 0 0 1 34 36z" fill={W} />
      </>
    ),
  },
  gallery: {
    bg: 'linear-gradient(160deg,#fff,#f1f0f5)',
    g: (
      <>
        {[[0, '#ff6d6d'], [60, '#ffb347'], [120, '#6bd36b'], [180, '#4ac4ff'], [240, '#6c7bff'], [300, '#d46bff']].map(([a, c]) => (
          <ellipse key={String(a)} cx="24" cy="15" rx="6" ry="9" fill={String(c)} opacity="0.85" transform={`rotate(${a} 24 24)`} />
        ))}
      </>
    ),
  },
  usb: {
    bg: 'linear-gradient(160deg,#4aa6ff,#1b6ee0)',
    g: (
      <>
        <rect x="16" y="14" width="16" height="26" rx="4" fill="none" stroke={W} strokeWidth="3" />
        <rect x="19" y="7" width="10" height="9" rx="1.500" fill={W} />
        <rect x="21" y="21" width="6" height="10" rx="2" fill={W} />
      </>
    ),
  },
  camera: {
    bg: 'linear-gradient(160deg,#fff,#eeeeee)',
    g: (
      <>
        <path d="M8 16h7l2.500-4h13l2.500 4h7v21H8z" fill="#34353a" />
        <circle cx="24" cy="26" r="7.500" fill="#1a1b1f" stroke="#7c7f8a" strokeWidth="2" />
        <circle cx="24" cy="26" r="3.500" fill="#4a5f9a" />
      </>
    ),
  },
  dashcam: {
    bg: 'linear-gradient(160deg,#58b4ff,#1d6bdb)',
    g: (
      <>
        <rect x="11" y="14" width="26" height="18" rx="4" fill={W} />
        <circle cx="24" cy="23" r="5.500" fill="#2a74e6" />
        <path d="M24 32v7M17 39h14M18 8h12" {...stroke} strokeWidth="3" />
      </>
    ),
  },
  market: {
    bg: 'linear-gradient(160deg,#ff4d4d,#d81b2a)',
    g: (
      <>
        <path d="M11 17h26l-2 20H13z" fill={W} />
        <path d="M17 17a7 7 0 0 1 14 0" fill="none" stroke={W} strokeWidth="3" strokeLinecap="round" />
        <path d="M18 24c1 3 3 4.500 6 4.500s5-1.500 6-4.500" fill="none" stroke="#d81b2a" strokeWidth="3" strokeLinecap="round" />
      </>
    ),
  },
  music: {
    bg: 'linear-gradient(160deg,#fff,#f3f1f7)',
    g: (
      <>
        <circle cx="24" cy="24" r="16" fill="#6a7bff" />
        <circle cx="30" cy="30" r="9" fill="#ff6bd5" opacity="0.7" />
        <path d="M21 31V17l10-2v12" fill="none" stroke={W} strokeWidth="3" strokeLinecap="round" />
        <circle cx="18.500" cy="31" r="3" fill={W} />
        <circle cx="28.500" cy="29" r="3" fill={W} />
      </>
    ),
  },
  life: {
    bg: 'linear-gradient(160deg,#4aa6ff,#1b6ee0)',
    g: <path d="M12 38V22L24 11l12 11v16H27V28h-6v10z" fill="none" stroke={W} strokeWidth="3.400" strokeLinejoin="round" />,
  },
  search: {
    bg: 'linear-gradient(160deg,#5ab4ff,#2b83e8)',
    g: (
      <>
        <circle cx="21" cy="21" r="10" fill="none" stroke={W} strokeWidth="4" />
        <path d="M29 29l10 10" stroke={W} strokeWidth="4.500" strokeLinecap="round" />
      </>
    ),
  },
  care: {
    bg: 'linear-gradient(160deg,#58a6ff,#2166d8)',
    g: (
      <>
        <path d="M24 8l13 5v10c0 8-5.500 13-13 17-7.500-4-13-9-13-17V13z" fill={W} />
        <path d="M17 26l1.800-5a2 2 0 0 1 1.900-1.300h6.600a2 2 0 0 1 1.900 1.300L31 26v4h-2.500v-1.500h-9V30H17z" fill="#2166d8" />
      </>
    ),
  },
  link: {
    bg: 'linear-gradient(160deg,#2b4a9a,#101b46)',
    g: (
      <>
        <rect x="24" y="9" width="14" height="25" rx="3" fill="none" stroke={W} strokeWidth="3" />
        <path d="M8 24h12M15 18l-6 6 6 6" {...stroke} />
      </>
    ),
  },
};

export function AppIcon({ id, size = 78 }: { id: AppId; size?: number }) {
  const a = ART[id];
  return (
    <span
      className="inline-flex shrink-0 items-center justify-center"
      style={{
        width: size,
        height: size,
        borderRadius: size * 0.27,
        background: a.bg,
        boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.18), 0 2px 6px rgba(0,0,0,0.18)',
      }}
      aria-hidden
    >
      <svg viewBox="0 0 48 48" width={size} height={size}>{a.g}</svg>
    </span>
  );
}
