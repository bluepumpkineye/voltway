'use client';

import { create } from 'zustand';
import type { DriveMode } from '@/lib/performance';

export type HmiScreen =
  | 'home'
  | 'climate'
  | 'drive'
  | 'nav'
  | 'media'
  | 'adas'
  | 'controls'
  // HyperOS apps
  | 'settings'
  | 'track';

/** The Settings app's side menu (HyperOS 设置, in the car's own order). */
export type SettingsPage =
  | 'vehicle'
  | 'lights'
  | 'doors'
  | 'driving'
  | 'assist'
  | 'charging'
  | 'connection'
  | 'display';

export type CameraMode = 'exterior' | 'transition' | 'interior';

/** Parked shows the parked desktop, drive the three-card driving desktop. */
export type Gear = 'P' | 'D';

export type Opening = 'doorFL' | 'doorFR' | 'doorRL' | 'doorRR' | 'frunk' | 'boot';

export interface ClimateState {
  driverTempC: number;
  passengerTempC: number;
  fanSpeed: number; // 0-5
  acOn: boolean;
  seatHeatDriver: number; // 0-3
  seatHeatPassenger: number;
  sync: boolean;
}

export interface MediaState {
  playing: boolean;
  trackIndex: number;
  volume: number; // 0-100
}

export interface VehicleUiState {
  variantId: string;
  driveMode: DriveMode;
  /**
   * The car's own name for the selected mode (Vehicle.cockpit.driveModes),
   * when the HMI picked one; null when the generic mode buttons did.
   */
  modeId: string | null;
  soc: number; // 0-1

  hmiScreen: HmiScreen;
  settingsPage: SettingsPage;
  climateOpen: boolean;
  gear: Gear;
  cameraMode: CameraMode;

  regen: 'gentle' | 'standard' | 'custom';
  sportSound: 'off' | 'electronic' | 'classic' | 'scifi';
  rideHeight: 'low' | 'standard' | 'high';

  climate: ClimateState;
  media: MediaState;

  ambientOn: boolean;
  ambientHue: number; // 0-360
  ambientBrightness: number; // 0-1

  openings: Record<Opening, boolean>;
  headlightsOn: boolean;
  locked: boolean;

  adasActive: boolean;

  setVariant: (id: string) => void;
  setDriveMode: (m: DriveMode) => void;
  /** Select one of the car's own modes (and the model mode behind it). */
  setCarMode: (id: string, model: DriveMode) => void;
  setSoc: (v: number) => void;
  setHmiScreen: (s: HmiScreen) => void;
  openSettings: (p: SettingsPage) => void;
  setClimateOpen: (v: boolean) => void;
  setGear: (g: Gear) => void;
  setRegen: (v: VehicleUiState['regen']) => void;
  setSportSound: (v: VehicleUiState['sportSound']) => void;
  setRideHeight: (v: VehicleUiState['rideHeight']) => void;
  setCameraMode: (m: CameraMode) => void;
  patchClimate: (p: Partial<ClimateState>) => void;
  patchMedia: (p: Partial<MediaState>) => void;
  setAmbient: (p: Partial<Pick<VehicleUiState, 'ambientOn' | 'ambientHue' | 'ambientBrightness'>>) => void;
  toggleOpening: (o: Opening) => void;
  closeAllOpenings: () => void;
  setHeadlights: (on: boolean) => void;
  setLocked: (v: boolean) => void;
  setAdas: (v: boolean) => void;
  reset: (variantId: string) => void;
}

const initialClimate: ClimateState = {
  driverTempC: 22,
  passengerTempC: 22,
  fanSpeed: 2,
  acOn: true,
  seatHeatDriver: 0,
  seatHeatPassenger: 0,
  sync: true,
};

const initialOpenings: Record<Opening, boolean> = {
  doorFL: false,
  doorFR: false,
  doorRL: false,
  doorRR: false,
  frunk: false,
  boot: false,
};

/**
 * One store behind the HMI, the 3D scene and the metrics panel.
 *
 * Everything the user touches on the dashboard writes here, so switching to
 * Sport updates the power readout, the range figure and the cabin lighting
 * together rather than each surface keeping its own copy.
 */
export const useVehicleStore = create<VehicleUiState>((set) => ({
  variantId: '',
  driveMode: 'comfort',
  modeId: null,
  soc: 0.78,

  hmiScreen: 'home',
  settingsPage: 'driving',
  climateOpen: false,
  gear: 'P',
  cameraMode: 'exterior',

  regen: 'standard',
  sportSound: 'off',
  rideHeight: 'standard',

  climate: initialClimate,
  media: { playing: true, trackIndex: 0, volume: 42 },

  ambientOn: true,
  ambientHue: 28,
  ambientBrightness: 0.7,

  openings: { ...initialOpenings },
  headlightsOn: false,
  locked: true,
  adasActive: false,

  setVariant: (variantId) => set({ variantId }),
  setDriveMode: (driveMode) => set({ driveMode, modeId: null }),
  setCarMode: (modeId, driveMode) => set({ modeId, driveMode }),
  setSoc: (soc) => set({ soc: Math.min(1, Math.max(0, soc)) }),
  setHmiScreen: (hmiScreen) => set({ hmiScreen, climateOpen: false }),
  openSettings: (settingsPage) => set({ hmiScreen: 'settings', settingsPage, climateOpen: false }),
  setClimateOpen: (climateOpen) => set({ climateOpen }),
  setGear: (gear) => set({ gear }),
  setRegen: (regen) => set({ regen }),
  setSportSound: (sportSound) => set({ sportSound }),
  setRideHeight: (rideHeight) => set({ rideHeight }),
  setCameraMode: (cameraMode) => set({ cameraMode }),

  patchClimate: (p) =>
    set((s) => {
      const next = { ...s.climate, ...p };
      // temperature sync mirrors the driver's setting to the passenger
      if (next.sync && p.driverTempC !== undefined) {
        next.passengerTempC = p.driverTempC;
      }
      if (next.sync && p.passengerTempC !== undefined) {
        next.driverTempC = p.passengerTempC;
      }
      return { climate: next };
    }),

  patchMedia: (p) => set((s) => ({ media: { ...s.media, ...p } })),

  setAmbient: (p) => set((s) => ({ ...s, ...p })),

  toggleOpening: (o) =>
    set((s) => ({ openings: { ...s.openings, [o]: !s.openings[o] } })),

  closeAllOpenings: () => set({ openings: { ...initialOpenings } }),

  setHeadlights: (headlightsOn) => set({ headlightsOn }),
  setLocked: (locked) => set({ locked }),
  setAdas: (adasActive) => set({ adasActive }),

  reset: (variantId) =>
    set({
      variantId,
      driveMode: 'comfort',
      modeId: null,
      soc: 0.78,
      hmiScreen: 'home',
      settingsPage: 'driving',
      climateOpen: false,
      gear: 'P',
      regen: 'standard',
      sportSound: 'off',
      rideHeight: 'standard',
      cameraMode: 'exterior',
      climate: { ...initialClimate },
      media: { playing: true, trackIndex: 0, volume: 42 },
      ambientOn: true,
      ambientHue: 28,
      ambientBrightness: 0.7,
      openings: { ...initialOpenings },
      headlightsOn: false,
      locked: true,
      adasActive: false,
    }),
}));
