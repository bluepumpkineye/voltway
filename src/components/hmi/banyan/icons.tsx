'use client';

import React from 'react';

const S = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.8,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
};

export function NomiFace({ mood = 'happy', size = 32 }: { mood?: string; size?: number }) {
  // NOMI's round AMOLED face with dynamic emotional eyes
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" className="inline-block select-none">
      <circle cx="20" cy="20" r="19" fill="#12151c" stroke="#00C2A8" strokeWidth="1.8" />
      {mood === 'happy' && (
        <>
          <path d="M12 17 Q15 13 18 17" stroke="#ffffff" strokeWidth="2.5" fill="none" strokeLinecap="round" />
          <path d="M22 17 Q25 13 28 17" stroke="#ffffff" strokeWidth="2.5" fill="none" strokeLinecap="round" />
          <path d="M16 25 Q20 28 24 25" stroke="#00C2A8" strokeWidth="2" fill="none" strokeLinecap="round" />
        </>
      )}
      {mood === 'listening' && (
        <>
          <circle cx="15" cy="18" r="3" fill="#ffffff" />
          <circle cx="25" cy="18" r="3" fill="#ffffff" />
          <ellipse cx="20" cy="26" rx="2.5" ry="3.5" fill="#00C2A8" />
        </>
      )}
      {mood === 'music' && (
        <>
          <path d="M12 18 Q15 15 18 18" stroke="#ffffff" strokeWidth="2.2" fill="none" strokeLinecap="round" />
          <path d="M22 18 Q25 15 28 18" stroke="#ffffff" strokeWidth="2.2" fill="none" strokeLinecap="round" />
          <path d="M28 10 L32 8 L32 14" stroke="#00C2A8" strokeWidth="1.5" fill="none" strokeLinecap="round" />
          <circle cx="30.5" cy="14" r="1.5" fill="#00C2A8" />
          <path d="M17 25 Q20 27 23 25" stroke="#00C2A8" strokeWidth="1.8" fill="none" strokeLinecap="round" />
        </>
      )}
      {mood === 'charging' && (
        <>
          <path d="M14 14 L17 19 L15 19 L18 24" stroke="#00C2A8" strokeWidth="2.2" fill="none" strokeLinecap="round" />
          <path d="M24 14 L27 19 L25 19 L28 24" stroke="#00C2A8" strokeWidth="2.2" fill="none" strokeLinecap="round" />
          <path d="M17 27 Q20 29 23 27" stroke="#ffffff" strokeWidth="1.8" fill="none" strokeLinecap="round" />
        </>
      )}
      {mood === 'sport' && (
        <>
          <path d="M13 16 L18 19" stroke="#EF4444" strokeWidth="2.4" strokeLinecap="round" />
          <path d="M27 16 L22 19" stroke="#EF4444" strokeWidth="2.4" strokeLinecap="round" />
          <path d="M17 26 Q20 25 23 26" stroke="#ffffff" strokeWidth="1.8" fill="none" strokeLinecap="round" />
        </>
      )}
      {mood === 'blink' && (
        <>
          <line x1="12" y1="18" x2="18" y2="18" stroke="#ffffff" strokeWidth="2.5" strokeLinecap="round" />
          <line x1="22" y1="18" x2="28" y2="18" stroke="#ffffff" strokeWidth="2.5" strokeLinecap="round" />
          <path d="M17 25 Q20 27 23 25" stroke="#00C2A8" strokeWidth="1.8" fill="none" strokeLinecap="round" />
        </>
      )}
    </svg>
  );
}

export function NioPowerSwapIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...S}>
      <rect x="3" y="5" width="18" height="14" rx="3" />
      <path d="M8 10 L12 10 L10 7" />
      <path d="M16 14 L12 14 L14 17" />
    </svg>
  );
}

export function QueenSeatIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...S}>
      <path d="M6 4v9a4 4 0 0 0 4 4h7" />
      <path d="M17 17l4 3" />
      <circle cx="10" cy="7" r="1.5" />
      <path d="M4 19h16" />
    </svg>
  );
}

export function Chassis4DIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...S}>
      <path d="M12 3v4" />
      <path d="M9 7h6" />
      <path d="M10 7l4 4-4 4 4 4-2 2" />
      <path d="M12 21v-2" />
      <circle cx="6" cy="12" r="3" />
      <circle cx="18" cy="12" r="3" />
    </svg>
  );
}

export function AirSuspensionIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...S}>
      <path d="M4 14h16l-2-4H6z" />
      <circle cx="7" cy="17" r="2" />
      <circle cx="17" cy="17" r="2" />
      <path d="M12 3v5M9 5l3-3 3 3" />
      <path d="M12 21v-3M9 19l3 3 3-3" />
    </svg>
  );
}

export function FragranceIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...S}>
      <rect x="7" y="8" width="10" height="12" rx="3" />
      <path d="M10 8V5h4v3" />
      <path d="M12 2v1" />
      <path d="M9 14h6" />
      <path d="M12 11v6" />
    </svg>
  );
}

export function DolbyAtmosIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...S}>
      <path d="M3 7v10a2 2 0 0 0 2 2h2V5H5a2 2 0 0 0-2 2Z" />
      <path d="M21 7v10a2 2 0 0 1-2 2h-2V5h2a2 2 0 0 1 2 2Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

export function LightLowIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...S}>
      <path d="M12 5a7 7 0 0 0-7 7 7 7 0 0 0 7 7V5Z" />
      <path d="M16 8l4 2M16 12h5M16 16l4-2" />
    </svg>
  );
}

export function LightHighIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...S}>
      <path d="M12 5a7 7 0 0 0-7 7 7 7 0 0 0 7 7V5Z" />
      <path d="M16 8h5M16 12h5M16 16h5" />
    </svg>
  );
}

export function LightAutoIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...S}>
      <circle cx="12" cy="12" r="8" />
      <path d="M9 15l3-7 3 7M10 13h4" />
    </svg>
  );
}

export function AmbientLightIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...S}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
    </svg>
  );
}

export function SunroofIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...S}>
      <rect x="4" y="5" width="16" height="14" rx="2" />
      <line x1="4" y1="12" x2="20" y2="12" />
      <line x1="12" y1="5" x2="12" y2="19" />
    </svg>
  );
}

export function MirrorIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...S}>
      <path d="M5 8h8a4 4 0 0 1 4 4v0a4 4 0 0 1-4 4H5z" />
      <path d="M5 16l-2 3M17 12h3" />
    </svg>
  );
}

export function SeatVentIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...S}>
      <circle cx="12" cy="12" r="8" />
      <path d="M12 12l3-3M12 12l-3 3M12 12l-3-3M12 12l3 3" />
    </svg>
  );
}

export function SeatHeatIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...S}>
      <path d="M8 5c1 2-1 4 0 6M12 5c1 2-1 4 0 6M16 5c1 2-1 4 0 6" />
      <rect x="5" y="15" width="14" height="4" rx="1.5" />
    </svg>
  );
}

export function SeatMassageIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...S}>
      <path d="M4 12c2-2 4-2 6 0s4 2 6 0 4-2 6 0" />
      <path d="M4 16c2-2 4-2 6 0s4 2 6 0 4-2 6 0" />
      <circle cx="8" cy="7" r="1.5" />
      <circle cx="16" cy="7" r="1.5" />
    </svg>
  );
}

export function ChildLockIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...S}>
      <circle cx="12" cy="8" r="4" />
      <path d="M6 20v-2a6 6 0 0 1 12 0v2" />
      <path d="M12 13v3" />
    </svg>
  );
}

export function HazardIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...S}>
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" strokeWidth="2.5" />
    </svg>
  );
}

export function VolumeIcon({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...S}>
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
      <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
    </svg>
  );
}
