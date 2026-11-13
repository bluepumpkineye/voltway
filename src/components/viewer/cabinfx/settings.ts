import * as THREE from 'three';

/**
 * The cabin's look, as numbers: one mutable object that the interior post-processing (InteriorFx), the cabin's
 * shader patches (CarModel.hallLighting), the material upgrader (materials.ts), the camera rig and the debug panel
 * (DebugPanel.tsx, `?debug=true`) all read. Nothing here touches the exterior: every consumer is gated on the
 * Interior tab's seat, so switching tabs or Studio | City leaves the outside renders exactly as they were.
 *
 * `?cabinfx=0` in the address turns the whole upgrade off (for a before / after), `?debug=true` shows the panel.
 */

export type ToneMode = 'agx' | 'neutral' | 'aces';

export interface CabinFxSettings {
  /** master switch for every interior upgrade (post-processing, footwell, gloss environment, material pass) */
  enabled: boolean;
  tone: {
    mode: ToneMode;
    /** the renderer's exposure while the composer runs (three's toneMappingExposure) */
    exposure: number;
    /** after the curve (AgX pales saturated colours): the display-referred saturation and contrast put back */
    saturation: number;
    contrast: number;
  };
  /** N8AO, in metres: the cabin is ~2 m across, the library's defaults are for a scene 100x that */
  ao: {
    enabled: boolean;
    radius: number;
    distanceFalloff: number;
    intensity: number;
    samples: number;
    denoiseSamples: number;
    denoiseRadius: number;
    halfRes: boolean;
  };
  bloom: {
    enabled: boolean;
    /** in scene-referred linear light: only what is brighter than a lit surface (the ambient strips) glows */
    threshold: number;
    smoothing: number;
    intensity: number;
    radius: number;
  };
  /** emissive intensity of the ambient strips per unit of the HMI's brightness slider (they bloom above `bloom.threshold`) */
  ambientGain: number;
  /** the footwells and the dash overhang: light falls off toward the floor */
  footwell: { enabled: boolean; light: number; height: number };
  /** the cabin's gloss environment: crisp softboxes for chrome, piano black and screen glass */
  gloss: { softbox: boolean; envIntensity: number; chromeEnv: number };
  materials: {
    leatherNormal: number;
    leatherRoughness: number;
    leatherSheen: number;
    alcantaraSheen: number;
    /** swap the glTF's own leather grain for the procedural one, to compare */
    proceduralLeather: boolean;
  };
  /** the seat's field of view, degrees (0 = the pose's own) */
  fov: number;
}

export const FX_DEFAULTS: CabinFxSettings = {
  enabled: true,
  // AgX lifts the shadows and pales saturated colour (a Sardine Coral leather went salmon at 1.05 / 0.22 / 0.06): measured against the
  // Neutral render the cabin was calibrated in, 0.85-0.9 with the saturation and contrast put back keeps the leather's own colour
  tone: { mode: 'agx', exposure: 0.9, saturation: 0.3, contrast: 0.22 },
  ao: { enabled: true, radius: 0.28, distanceFalloff: 0.6, intensity: 2.4, samples: 16, denoiseSamples: 8, denoiseRadius: 10, halfRes: false },
  bloom: { enabled: true, threshold: 1.1, smoothing: 0.25, intensity: 0.55, radius: 0.6 },
  ambientGain: 4.0,
  footwell: { enabled: true, light: 0.38, height: 0.5 },
  gloss: { softbox: true, envIntensity: 1.5, chromeEnv: 1.5 },
  materials: { leatherNormal: 0.35, leatherRoughness: 0.62, leatherSheen: 0.15, alcantaraSheen: 1.0, proceduralLeather: false },
  fov: 0,
};

/**
 * The address is read when this module first loads, from the URL the page was LOADED with (the navigation entry) as well as
 * the current one: the showroom rewrites its query string as the visitor changes tabs, so `?debug=true` can be gone by the time
 * this chunk runs. A flag seen is kept for the browser session.
 */
function addresses(): URLSearchParams[] {
  const out = [new URLSearchParams(window.location.search)];
  try {
    const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined;
    if (nav?.name) out.push(new URL(nav.name).searchParams);
  } catch {
    /* no navigation timing: the current address is all there is */
  }
  return out;
}

function flag(name: string, on: string): boolean {
  if (typeof window === 'undefined') return false;
  try {
    if (addresses().some((q) => q.get(name) === on)) {
      window.sessionStorage.setItem('cabinfx:' + name, on);
      return true;
    }
    return window.sessionStorage.getItem('cabinfx:' + name) === on;
  } catch {
    return false;
  }
}

/** `?debug=true`: show the tuning panel. */
export const DEBUG_UI = flag('debug', 'true');

export const FX: CabinFxSettings = structuredClone(FX_DEFAULTS);
// `?cabinfx=0` turns the upgrade off for a before / after
if (typeof window !== 'undefined' && addresses().some((q) => q.get('cabinfx') === '0')) FX.enabled = false;

/**
 * Uniforms the cabin's patched shaders share, so a slider moves every material at once.
 * footwell: x = the cabin's floor height (metres, world), y = the height over which the light returns, z = the light left at the
 * floor, w = on (1) or off (0).
 */
export const FOOTWELL = { value: new THREE.Vector4(0, 0.5, 0.38, 1) };

const listeners = new Set<() => void>();
let version = 0;
let frame: () => void = () => {};

/** InteriorFx hands over the renderer's `invalidate`, so a slider asks for a frame under frameloop="demand". */
export function bindFrame(fn: () => void) {
  frame = fn;
  return () => {
    if (frame === fn) frame = () => {};
  };
}

/** Subscribers (the composer's props, the materials' tuning) re-read FX after this. */
export function touchFx() {
  FOOTWELL.value.z = FX.footwell.light;
  FOOTWELL.value.y = Math.max(0.05, FX.footwell.height);
  FOOTWELL.value.w = FX.enabled && FX.footwell.enabled ? 1 : 0;
  version++;
  for (const l of listeners) l();
  frame();
}

export function subscribeFx(fn: () => void) {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}

export const fxVersion = () => version;
touchFx();

/** window.__cabinFx in development: the live settings, for tuning from the console. */
if (typeof window !== 'undefined' && process.env.NODE_ENV !== 'production') {
  (window as unknown as { __cabinFx?: unknown }).__cabinFx = { FX, FOOTWELL, touchFx };
}
