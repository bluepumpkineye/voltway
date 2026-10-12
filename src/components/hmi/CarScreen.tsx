'use client';

import React from 'react';
import type { Variant, Vehicle } from '@/data/vehicles/schema';
import { HmiSurface } from './HmiSurface';

/** The HMI is authored at 1280 x 800; the bezel adds 14 px all round. */
const HMI_W = 1280;
const HMI_H = 800;
export const CAR_SCREEN_W = HMI_W + 28;
export const CAR_SCREEN_H = HMI_H + 28;

/**
 * The car's centre screen with its bezel, at the HMI's own size: a window onto the live HMI that the
 * Tech and Dashboard tabs stand beside the car. Scale it with `Fit`; it takes pointer events only on
 * itself, so a drag round it still turns the scene.
 */
export function CarScreen({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  return (
    <div
      className="relative rounded-[30px] bg-[#08090b] p-[14px] shadow-[0_30px_60px_-18px_rgba(10,12,18,0.55),0_0_0_2px_#24262c_inset]"
      style={{ width: CAR_SCREEN_W, height: CAR_SCREEN_H }}
    >
      <div className="relative overflow-hidden rounded-[18px]" style={{ width: HMI_W, height: HMI_H }}>
        <HmiSurface vehicle={vehicle} variant={variant} />
      </div>
    </div>
  );
}
