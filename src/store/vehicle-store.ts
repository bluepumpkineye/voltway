'use client';

import { create } from 'zustand';
import type { DriveMode } from '@/lib/performance';
import type { AnchorId } from '@/data/vehicles/schema';

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

/** The showroom's bottom tabs (/showroom/[slug]). */
export type ShowroomTab = 'colour' | 'interior' | 'dimensions' | 'xray';

/** Studio is the default; city is the HDRI world the car was baked under. */
export type ShowroomScene = 'studio' | 'city';

/** Which published dimension the Dimensions tab is showing. */
export type DimensionFocus = 'length' | 'width' | 'height';

/** Each tab opens on its own pose; the Dimensions chips pick theirs. */
const TAB_ANCHOR: Record<ShowroomTab, AnchorId> = {
  colour: 'hero',
  interior: 'driver',
  dimensions: 'side',
  xray: 'xray',
};
/** Where the camera goes to see a part open: the side its hinge is on. */
const OPENING_ANCHOR: Record<Opening, AnchorId> = {
  doorFL: 'doorsL',
  doorRL: 'doorsL',
  doorFR: 'doorsR',
  doorRR: 'doorsR',
  frunk: 'frunk',
  boot: 'trunk',
};
// Height uses the front view: beside the car it has free space for the ruler
// and its label, which the side view (nose and roof up to the screen edge) lacks.
const DIMENSION_ANCHOR: Record<DimensionFocus, AnchorId> = {
  length: 'side',
  width: 'front',
  height: 'front',
};

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

  // ---- the showroom
  tab: ShowroomTab;
  /** '' means the first option: the car as built */
  paintId: string;
  trimId: string;
  anchorId: AnchorId;
  sceneKind: ShowroomScene;
  dimension: DimensionFocus;

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
  setTab: (t: ShowroomTab) => void;
  setPaint: (id: string) => void;
  setTrim: (id: string) => void;
  /** Fly to a pose. The camera mode follows, so the cabin mounts and the glass clears. */
  setAnchor: (id: AnchorId) => void;
  setSceneKind: (s: ShowroomScene) => void;
  setDimension: (d: DimensionFocus) => void;
  reset: (variantId: string) => void;
}

const anchorState = (anchorId: AnchorId) => ({
  anchorId,
  cameraMode: anchorId === 'driver' ? ('interior' as const) : ('exterior' as const),
});

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

  tab: 'colour',
  paintId: '',
  trimId: '',
  anchorId: 'hero',
  sceneKind: 'studio',
  dimension: 'length',

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
    set((s) => {
      const openings = { ...s.openings, [o]: !s.openings[o] };
      // opening a part from outside brings it into frame (as HIMA's showroom
      // does); from the seat, or on another tab, the camera stays where it is
      if (!s.openings[o] && s.cameraMode === 'exterior' && s.tab === 'colour') {
        return { openings, ...anchorState(OPENING_ANCHOR[o]) };
      }
      return { openings };
    }),

  closeAllOpenings: () => set({ openings: { ...initialOpenings } }),

  setHeadlights: (headlightsOn) => set({ headlightsOn }),
  setLocked: (locked) => set({ locked }),
  setAdas: (adasActive) => set({ adasActive }),

  setTab: (tab) => set({ tab, dimension: 'length', ...anchorState(TAB_ANCHOR[tab]) }),
  setPaint: (paintId) => set({ paintId }),
  setTrim: (trimId) => set({ trimId }),
  setAnchor: (id) => set(anchorState(id)),
  setSceneKind: (sceneKind) => set({ sceneKind }),
  setDimension: (dimension) => set({ dimension, ...anchorState(DIMENSION_ANCHOR[dimension]) }),

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
      tab: 'colour',
      paintId: '',
      trimId: '',
      anchorId: 'hero',
      sceneKind: 'studio',
      dimension: 'length',
    }),
}));
