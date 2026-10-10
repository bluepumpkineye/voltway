'use client';

import { create } from 'zustand';
import type { DriveMode } from '@/lib/performance';
import type { AnchorId, TechDevice } from '@/data/vehicles/schema';
import type { ParkSpeed, ParkStage } from '@/lib/tech/park';

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
  | 'track'
  // HarmonyOS apps (the Luxeed RX)
  | 'seats'
  | 'camera'
  | 'park';

/** The Settings app's side menu (HyperOS 设置, in the car's own order). */
export type SettingsPage =
  | 'vehicle'
  | 'lights'
  | 'doors'
  | 'driving'
  | 'assist'
  | 'charging'
  | 'connection'
  | 'display'
  // HarmonyOS Settings (the Luxeed RX): its own menu
  | 'energy'
  | 'status'
  | 'scenes'
  | 'personalise'
  | 'sound'
  | 'assistant'
  | 'system';

/** Light or dark UI, for the skins that have both (HarmonyOS). */
export type HmiTheme = 'dark' | 'light';

export type CameraMode = 'exterior' | 'transition' | 'interior';

/** Parked shows the parked desktop, drive the three-card driving desktop. */
export type Gear = 'P' | 'D';

export type Opening = 'doorFL' | 'doorFR' | 'doorRL' | 'doorRR' | 'frunk' | 'boot';

/** The showroom's bottom tabs (/showroom/[slug]). */
export type ShowroomTab = 'colour' | 'interior' | 'wheels' | 'dimensions' | 'xray' | 'tech';

/** Studio is the default; city is the HDRI world the car was baked under. */
export type ShowroomScene = 'studio' | 'city';

/** Which published dimension the Dimensions tab is showing. */
export type DimensionFocus = 'length' | 'width' | 'height';

/** Each tab opens on its own pose; the Dimensions chips pick theirs. */
const TAB_ANCHOR: Record<ShowroomTab, AnchorId> = {
  colour: 'hero',
  interior: 'driver',
  wheels: 'wheel',
  dimensions: 'side',
  xray: 'xray',
  tech: 'techWide',
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
  /** HarmonyOS: the App Centre overlay over the current screen */
  appCentreOpen: boolean;
  hmiTheme: HmiTheme;
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
  caliperId: string;
  wheelId: string;
  anchorId: AnchorId;
  sceneKind: ShowroomScene;
  dimension: DimensionFocus;
  /** the Tech tab's demo ('' means the car's first); its clock lives in src/lib/tech/clock.ts */
  techDemoId: string;
  /** playback speed of the demo's clock */
  techSpeed: number;
  /**
   * the floor the running demo uses (viewer axes, m): the camera keeps it in view; `camera` is the
   * demo's preferred look (azimuth and elevation, degrees)
   */
  techStage: { cx: number; cz: number; radius: number; camera?: { az: number; el: number } } | null;
  /** the part of the window the Tech tab's devices cover, as fractions (right: of the width, bottom: of the height) */
  techInset: { right: number; bottom: number };
  /** the parking lot (or other staged floor) of the running demo, which the viewer draws round the car */
  techScene: ParkStage | null;
  /** whether the mounted exterior has the per-corner wheels the demos drive */
  techStatus: 'loading' | 'ready' | 'none';
  /** the device of the Tech tab on show: the phone, or the car's screen */
  techDevice: TechDevice;
  /** a device asked for the demo to start as soon as it is built (from another tab, or a link) */
  techIntent: boolean;
  /** the showroom is mounted, so the car's screen can start demos (the vehicle page has none) */
  techAvailable: boolean;
  /** the car's own parking settings (Settings > Assisted driving > Parking assist) */
  rpaEnabled: boolean;
  parkSpeed: ParkSpeed;

  setVariant: (id: string) => void;
  setDriveMode: (m: DriveMode) => void;
  /** Select one of the car's own modes (and the model mode behind it). */
  setCarMode: (id: string, model: DriveMode) => void;
  setSoc: (v: number) => void;
  setHmiScreen: (s: HmiScreen) => void;
  openSettings: (p: SettingsPage) => void;
  setClimateOpen: (v: boolean) => void;
  setAppCentreOpen: (v: boolean) => void;
  setHmiTheme: (t: HmiTheme) => void;
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
  setCaliper: (id: string) => void;
  setWheel: (id: string) => void;
  /** Fly to a pose. The camera mode follows, so the cabin mounts and the glass clears. */
  setAnchor: (id: AnchorId) => void;
  setSceneKind: (s: ShowroomScene) => void;
  setDimension: (d: DimensionFocus) => void;
  setTechDemo: (id: string) => void;
  setTechSpeed: (speed: number) => void;
  setTechStage: (stage: VehicleUiState['techStage']) => void;
  setTechScene: (scene: ParkStage | null) => void;
  setTechInset: (inset: VehicleUiState['techInset']) => void;
  setTechStatus: (status: VehicleUiState['techStatus']) => void;
  setTechDevice: (device: TechDevice) => void;
  setTechAvailable: (v: boolean) => void;
  setRpaEnabled: (v: boolean) => void;
  setParkSpeed: (v: ParkSpeed) => void;
  /**
   * Open a demonstration from a device and start it as soon as it is built: the car screen's Start
   * button in the cabin takes the visitor out to the stage, and the Tech tab's own devices (already
   * there) just play.
   */
  startTech: (demoId: string, device: TechDevice) => void;
  /** The director took the request. */
  clearTechIntent: () => void;
  reset: (variantId: string, hmiTheme?: HmiTheme) => void;
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

/** What opening the Tech tab changes elsewhere: a shut car, in the studio. */
const techTab = { openings: { ...initialOpenings }, sceneKind: 'studio' as const };

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
  appCentreOpen: false,
  hmiTheme: 'dark',
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
  caliperId: '',
  wheelId: '',
  anchorId: 'hero',
  sceneKind: 'studio',
  dimension: 'length',
  techDemoId: '',
  techSpeed: 1,
  techStage: null,
  techInset: { right: 0, bottom: 0 },
  techScene: null,
  techStatus: 'loading',
  techDevice: 'phone',
  techIntent: false,
  techAvailable: false,
  rpaEnabled: true,
  parkSpeed: 'medium',

  setVariant: (variantId) => set({ variantId }),
  setDriveMode: (driveMode) => set({ driveMode, modeId: null }),
  setCarMode: (modeId, driveMode) => set({ modeId, driveMode }),
  setSoc: (soc) => set({ soc: Math.min(1, Math.max(0, soc)) }),
  setHmiScreen: (hmiScreen) => set({ hmiScreen, climateOpen: false, appCentreOpen: false }),
  openSettings: (settingsPage) =>
    set({ hmiScreen: 'settings', settingsPage, climateOpen: false, appCentreOpen: false }),
  setClimateOpen: (climateOpen) => set({ climateOpen }),
  setAppCentreOpen: (appCentreOpen) => set({ appCentreOpen }),
  setHmiTheme: (hmiTheme) => set({ hmiTheme }),
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
      // the car is on the move in the Tech tab: its doors stay shut
      if (s.tab === 'tech') return {};
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

  setTab: (tab) =>
    set({
      tab,
      dimension: 'length',
      ...anchorState(TAB_ANCHOR[tab]),
      // the tech demos stage a shut car in the studio: nothing hangs open, the city's sun is not on its floor
      ...(tab === 'tech' ? techTab : {}),
    }),
  setPaint: (paintId) => set({ paintId }),
  setTrim: (trimId) => set({ trimId }),
  setCaliper: (caliperId) => set({ caliperId }),
  setWheel: (wheelId) => set({ wheelId }),
  setAnchor: (id) => set(anchorState(id)),
  setSceneKind: (sceneKind) => set({ sceneKind }),
  setDimension: (dimension) => set({ dimension, ...anchorState(DIMENSION_ANCHOR[dimension]) }),
  setTechDemo: (techDemoId) => set({ techDemoId }),
  setTechSpeed: (techSpeed) => set({ techSpeed }),
  setTechStage: (techStage) => set({ techStage }),
  setTechScene: (techScene) => set({ techScene }),
  setTechInset: (techInset) =>
    set((s) =>
      s.techInset.right === techInset.right && s.techInset.bottom === techInset.bottom ? {} : { techInset },
    ),
  setTechStatus: (techStatus) => set({ techStatus }),
  setTechDevice: (techDevice) => set({ techDevice }),
  setTechAvailable: (techAvailable) => set({ techAvailable }),
  setRpaEnabled: (rpaEnabled) => set({ rpaEnabled }),
  setParkSpeed: (parkSpeed) => set({ parkSpeed }),
  startTech: (techDemoId, techDevice) =>
    set({
      tab: 'tech',
      dimension: 'length',
      ...anchorState(TAB_ANCHOR.tech),
      ...techTab,
      techDemoId,
      techDevice,
      techIntent: true,
    }),
  clearTechIntent: () => set({ techIntent: false }),

  reset: (variantId, theme) =>
    set({
      variantId,
      driveMode: 'comfort',
      modeId: null,
      soc: 0.78,
      hmiScreen: 'home',
      settingsPage: 'driving',
      climateOpen: false,
      appCentreOpen: false,
      hmiTheme: theme ?? 'dark',
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
      caliperId: '',
      wheelId: '',
      anchorId: 'hero',
      sceneKind: 'studio',
      dimension: 'length',
      techDemoId: '',
      techSpeed: 1,
      techStage: null,
      techScene: null,
      techDevice: 'phone',
      techIntent: false,
      rpaEnabled: true,
      parkSpeed: 'medium',
    }),
}));
