'use client';

import React from 'react';

/** The phone's screen, in the app's own pixels. */
export const PHONE_W = 360;
export const PHONE_H = 760;
/** with its bezel */
export const DEVICE_W = PHONE_W + 18;
export const DEVICE_H = PHONE_H + 18;

/**
 * A smartphone: a dark bezel round a 360 x 760 screen, a camera island and the side keys. A generic
 * handset, not any maker's. The surface swallows pointer events like the car's screen does, so a tap on
 * the glass is not read by the 3D scene behind it as the start of a drag.
 */
export function PhoneFrame({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="relative rounded-[50px] bg-[#0b0c0f] p-[9px] shadow-[0_30px_60px_-18px_rgba(10,12,18,0.55),0_0_0_1.5px_#2a2c33_inset,0_0_0_1px_rgba(255,255,255,0.05)]"
      style={{ width: DEVICE_W, height: DEVICE_H }}
      onPointerDown={(e) => e.stopPropagation()}
      onPointerUp={(e) => e.stopPropagation()}
      onPointerMove={(e) => e.stopPropagation()}
      onWheel={(e) => e.stopPropagation()}
    >
      {/* the side keys */}
      <span className="absolute -right-[3px] top-[150px] h-14 w-[3px] rounded-r bg-[#1b1c21]" aria-hidden />
      <span className="absolute -left-[3px] top-[120px] h-9 w-[3px] rounded-l bg-[#1b1c21]" aria-hidden />
      <span className="absolute -left-[3px] top-[170px] h-14 w-[3px] rounded-l bg-[#1b1c21]" aria-hidden />
      <div className="relative overflow-hidden rounded-[41px] bg-white" style={{ width: PHONE_W, height: PHONE_H }}>
        {children}
        {/* the camera island, over the status bar */}
        <span className="pointer-events-none absolute left-1/2 top-[9px] z-50 h-[22px] w-[22px] -translate-x-1/2 rounded-full bg-[#0b0c0f]" aria-hidden />
      </div>
    </div>
  );
}
