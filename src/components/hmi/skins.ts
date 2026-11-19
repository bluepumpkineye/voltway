import type React from 'react';
import type { HmiSkin, Variant, Vehicle } from '@/data/vehicles/schema';

export type SurfaceProps = { vehicle: Vehicle; variant: Variant; className?: string };

/**
 * The car's operating system, one chunk each: a car loads the skin it wears, not all eight (together they are most of the
 * showroom's own code). HmiSurface draws them through next/dynamic; `preloadSkin` starts the fetch early, so the screen is
 * there by the time the Dashboard tab or the cabin asks for it.
 */
export const SKIN_LOADERS: Record<HmiSkin, () => Promise<React.ComponentType<SurfaceProps>>> = {
  hyperos: () => import('./hyperos/HyperOsSurface').then((m) => m.HyperOsSurface),
  harmonyos: () => import('./harmonyos/HarmonyOsSurface').then((m) => m.HarmonyOsSurface),
  zeekros: () => import('./zeekros/ZeekrOsSurface').then((m) => m.ZeekrOsSurface),
  dilink: () => import('./dilink/DilinkSurface').then((m) => m.DilinkSurface),
  xos: () => import('./xos/XosSurface').then((m) => m.XosSurface),
  banyan: () => import('./banyan/BanyanSurface').then((m) => m.BanyanSurface),
  avatr: () => import('./avatr/AvatrSurface').then((m) => m.AvatrSurface),
  byd: () => import('./byd/BydSurface').then((m) => m.BydSurface),
};

export function preloadSkin(skin: HmiSkin): void {
  void SKIN_LOADERS[skin]?.();
}
