'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import type { Vehicle } from '@/data/vehicles/schema';
import { flagshipVariant } from '@/data/vehicles/schema';
import {
  useVehicleStore,
  type DimensionFocus,
  type ShowroomScene,
  type ShowroomTab,
} from '@/store/vehicle-store';
import { LIGHT_MODES, type LightMode } from '@/lib/lights';
import { visibleDemos } from '@/lib/tech/demos';
import { chargeDemo } from '@/lib/tech/charging';
import { BELOW_TOP, CarMenu, FOCUS, GLASS, InfoButton, SceneToggle, SoundToggle, TabBar } from './Chrome';
import { DashboardControls, DashboardScreen, useDashboardLayout } from './Dashboard';
import { CaliperSwatches, DimensionChips, PaintSwatches, TrimSwatches, WheelChips } from './Swatches';
import { CHARGE_COLUMN_W, ChargePanel } from './Charge';
import { COMPARE_COLUMN_W, SPECS_COLUMN_W, SpecsPanel } from './Specs';
import { showroomCars } from '@/lib/showroom/cars';
import { BoostPopup, BoostTools, boostColumnWidth } from './Boost';
import { ChassisTools, NoseInTools } from './Chassis';
import { LaunchTools } from './Launch';
import { ParkAssistTools } from './ParkAssist';
import { SensorsTools } from './Sensors';
import { SwivelTools } from './Swivel';
import { RideTools } from './Ride';
import { TechChips, TechControls } from './Tech';
import { TechDevices, activeDevice, useDeviceColumn } from '@/components/tech/TechDevices';
import { useWebGl } from './useWebGl';
import { isChassisDriver } from '@/lib/tech/chassis';

// three.js has no business in the server bundle
const ShowroomViewer = dynamic(
  () => import('@/components/viewer/ShowroomViewer').then((m) => m.ShowroomViewer),
  {
    ssr: false,
    loading: () => (
      <div className="absolute inset-0 grid place-items-center">
        <div className="h-[3px] w-40 overflow-hidden rounded-full bg-black/10">
          <div className="h-full w-1/3 rounded-full bg-neutral-800 animate-sweep" />
        </div>
      </div>
    ),
  },
);

const Comparison3DShowroom = dynamic(
  () => import('./Comparison3DShowroom').then((m) => m.Comparison3DShowroom),
  {
    ssr: false,
    loading: () => (
      <div className="fixed inset-0 grid place-items-center bg-[#f1f2f4]">
        <div className="h-[3px] w-40 overflow-hidden rounded-full bg-black/10">
          <div className="h-full w-1/3 rounded-full bg-neutral-800 animate-sweep" />
        </div>
      </div>
    ),
  },
);

const TABS: ShowroomTab[] = ['colour', 'interior', 'dashboard', 'wheels', 'dimensions', 'xray', 'charging', 'tech'];
const DIMS: DimensionFocus[] = ['length', 'width', 'height'];
/** the menu's height with its one row of tabs, px: the poses are composed for it */
const ONE_ROW = 56;

const TITLES: Record<ShowroomTab, string> = {
  colour: 'Colour',
  interior: 'Interior',
  dashboard: 'Dashboard',
  wheels: 'Wheels',
  dimensions: 'Specifications',
  xray: 'X-ray',
  charging: 'Charging',
  tech: 'Tech',
};

const NOTES: Record<ShowroomTab, string> = {
  colour:
    "Paint names are the maker's. Colours are matched to its published images under our studio lights, so they are approximate.",
  interior:
    "Cabin colourways follow the maker's options; which panel takes which colour is our model's, so colours are approximate. Drag to look around; the centre screen is live.",
  wheels:
    "Wheel designs and tyre sizes are the maker's, modelled from published photographs. Caliper colours follow its options (red, grey, yellow and others) and are approximate.",
  dashboard:
    "The car's own screen, live beside the car. Its headlamp controls switch the lamps; the glow, the beam on the floor and the dusk are our rendering of them, not the maker's footage.",
  dimensions:
    "Dimensions, performance, battery and range are the manufacturer's published figures, each range on its own test cycle; a figure marked estimated is derived, and one the maker has not published says so.",
  xray: "The upper body is shown as a see-through shell, with the doors removed, so the cabin reads through it. A modelled view, not the maker's.",
  charging:
    "The charging window and its minutes are the maker's where it publishes them. The curve between, a peak it does not publish, the charger and the gun are ours; the minutes play in fourteen seconds.",
  tech: "What the car's technology does. Each demonstration is a simulation built from the maker's published figures, not its footage.",
};

export function Showroom({
  vehicle,
  cars,
}: {
  vehicle: Vehicle;
  cars: { slug: string; label: string }[];
}) {
  const spec = vehicle.configurator!;
  const hasCabin = Boolean(vehicle.assets.interiorModelUrl);
  const canCity = Boolean(vehicle.assets.outside);
  // a car with something to choose at its wheels (one design, one caliper colour is no choice)
  const hasWheelTab = (spec.wheels?.length ?? 0) > 1 || (spec.calipers?.length ?? 0) > 1;
  // a car with something to demonstrate, and one with charging figures
  const demos = React.useMemo(() => visibleDemos(vehicle), [vehicle]);
  const hasTech = demos.length > 0;
  const charging = React.useMemo(() => chargeDemo(vehicle), [vehicle]);
  const hasCharging = charging !== null;

  const tab = useVehicleStore((s) => s.tab);
  const techDemoId = useVehicleStore((s) => s.techDemoId);
  const techSpeed = useVehicleStore((s) => s.techSpeed);
  const techStatus = useVehicleStore((s) => s.techStatus);
  const paintId = useVehicleStore((s) => s.paintId);
  const trimId = useVehicleStore((s) => s.trimId);
  const caliperId = useVehicleStore((s) => s.caliperId);
  const wheelId = useVehicleStore((s) => s.wheelId);
  const sceneKind = useVehicleStore((s) => s.sceneKind);
  const dimension = useVehicleStore((s) => s.dimension);
  const variantId = useVehicleStore((s) => s.variantId);
  const compareSlug = useVehicleStore((s) => s.compareSlug);
  const compareVariantId = useVehicleStore((s) => s.compareVariantId);
  const {
    reset, setTab, setPaint, setTrim, setCaliper, setWheel, setSceneKind, setDimension, setTechDemo, setTechSpeed,
    setTechAvailable, setTechDevice, setLightMode, setHighBeam, setLightsView, setVariant, setDeviceInset, setUiTop,
    setCompareSlug, setCompareVariantId,
  } = useVehicleStore.getState();
  const techDevice = useVehicleStore((s) => s.techDevice);
  const demo = demos.find((d) => d.id === techDemoId) ?? demos[0];
  const lightMode = useVehicleStore((s) => s.lightMode);
  const highBeam = useVehicleStore((s) => s.highBeam);
  const lightsView = useVehicleStore((s) => s.lightsView);
  // the Dashboard tab's screen: a column at the right of a wide window, a sheet over the car on a narrower one
  const dash = useDashboardLayout();
  // the BOOST demo's enlarged screen: a column at the right of a wide window, a sheet over the cabin on a narrower one
  const boostUp = useVehicleStore((s) => s.boostPopup) && demo?.driver === 'boost' && tab === 'tech' && dash.screenFits;
  const boostSheet = boostUp && !dash.wide;
  const [screenOpen, setScreenOpen] = React.useState(false);
  const closeScreen = React.useCallback(() => setScreenOpen(false), []);
  const [specsOpen, setSpecsOpen] = React.useState(false);
  const webgl = useWebGl();

  const variant = vehicle.variants.find((v) => v.id === variantId) ?? flagshipVariant(vehicle);

  const allShowroomCars = React.useMemo(() => showroomCars(), []);
  const otherCars = React.useMemo(() => allShowroomCars.filter((c) => c.slug !== vehicle.slug), [allShowroomCars, vehicle.slug]);
  const compareVehicle = compareSlug
    ? (allShowroomCars.find((c) => c.slug === compareSlug) ?? otherCars[0])
    : otherCars[0];
  const compareVariant = compareVehicle
    ? (compareVehicle.variants.find((v) => v.id === compareVariantId) ?? flagshipVariant(compareVehicle))
    : undefined;
  const isComparing = Boolean(compareSlug);
  const [compareMaximized, setCompareMaximized] = React.useState(false);

  // the devices of the Tech tab: the car's screen can start demos while the showroom is mounted (the dock
  // leaves their column clear on a wide window; the devices themselves frame the camera, see TechDevices)
  const col = useDeviceColumn(tab === 'tech' ? demo : undefined);
  React.useEffect(() => {
    setTechAvailable(true);
    return () => setTechAvailable(false);
  }, [setTechAvailable]);

  // The menu at the top publishes its height, so a panel that hangs from under it (a screen's column, a sheet) starts below it
  const root = React.useRef<HTMLDivElement>(null);
  const top = React.useRef<HTMLElement>(null);
  React.useEffect(() => {
    const el = top.current;
    const host = root.current;
    if (!el || !host) return;
    const f = () => {
      const h = Math.ceil(el.getBoundingClientRect().height);
      host.style.setProperty('--top-ui', `${h}px`);
      // what the menu takes beyond its one row, for the camera (a Tech demo's second row, a phone's wrapped tabs)
      setUiTop(Math.max(0, h - ONE_ROW) / Math.max(window.innerHeight, 1));
    };
    f();
    const ro = new ResizeObserver(f);
    ro.observe(el);
    window.addEventListener('resize', f);
    return () => {
      ro.disconnect();
      window.removeEventListener('resize', f);
      setUiTop(0);
    };
  }, [setUiTop]);

  // The viewer mounts only once the URL's state is applied, so a deep link
  // opens on its own pose instead of flying there from the default.
  const [ready, setReady] = React.useState(false);
  React.useEffect(() => {
    reset(flagshipVariant(vehicle).id, vehicle.cockpit.defaultTheme);
    if (vehicle.cockpit.ambientHue !== undefined) {
      useVehicleStore.getState().setAmbient({ ambientHue: vehicle.cockpit.ambientHue });
    }
    const q = new URLSearchParams(window.location.search);
    const wantTab = q.get('tab') as ShowroomTab | null;
    if (
      wantTab &&
      TABS.includes(wantTab) &&
      (wantTab !== 'interior' || hasCabin) &&
      (wantTab !== 'wheels' || hasWheelTab) &&
      (wantTab !== 'xray' || (hasCabin && vehicle.xray)) &&
      (wantTab !== 'charging' || hasCharging) &&
      (wantTab !== 'tech' || hasTech)
    )
      setTab(wantTab);
    const wantDemo = q.get('demo');
    if (wantDemo && demos.some((d) => d.id === wantDemo)) setTechDemo(wantDemo);
    const wantDevice = q.get('device');
    if (wantDevice === 'phone' || wantDevice === 'dashboard') setTechDevice(wantDevice);
    // the lamps: the switch, the high beam, and which end of the car the Dashboard tab looks at
    const wantLights = q.get('lights') as LightMode | null;
    if (wantLights && LIGHT_MODES.includes(wantLights)) setLightMode(wantLights);
    if (q.get('high') === '1') setHighBeam(true);
    if (wantTab === 'dashboard' && q.get('view') === 'rear') setLightsView('rear');
    const wantDim = q.get('dim') as DimensionFocus | null;
    if (wantDim && DIMS.includes(wantDim)) setDimension(wantDim);
    const wantVariant = q.get('variant');
    if (wantVariant && vehicle.variants.some((v) => v.id === wantVariant)) setVariant(wantVariant);
    const wantPaint = q.get('paint');
    if (wantPaint && spec.paints.some((p) => p.id === wantPaint)) setPaint(wantPaint);
    const wantTrim = q.get('trim');
    if (wantTrim && spec.trims.some((t) => t.id === wantTrim)) setTrim(wantTrim);
    const wantWheel = q.get('wheel');
    if (wantWheel && spec.wheels?.some((w) => w.id === wantWheel)) setWheel(wantWheel);
    const wantCaliper = q.get('caliper');
    if (wantCaliper && spec.calipers?.some((c) => c.id === wantCaliper)) setCaliper(wantCaliper);
    const wantScene = q.get('scene') as ShowroomScene | null;
    if (wantScene === 'city' && canCity) setSceneKind('city');
    const wantCompare = q.get('compare');
    if (wantCompare && wantCompare !== vehicle.slug && allShowroomCars.some((c) => c.slug === wantCompare)) {
      setCompareSlug(wantCompare);
      const wantCVariant = q.get('cvariant');
      if (wantCVariant) setCompareVariantId(wantCVariant);
    }
    setReady(true);
    // the actions are stable store functions; the vehicle is fixed per mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // write the state back, so the address is always a link to what is on screen
  React.useEffect(() => {
    if (!ready) return;
    const q = new URLSearchParams();
    if (tab !== 'colour') q.set('tab', tab);
    if (lightMode !== 'off') q.set('lights', lightMode);
    if (highBeam) q.set('high', '1');
    if (tab === 'dashboard' && lightsView === 'rear') q.set('view', 'rear');
    if (tab === 'dimensions' && dimension !== 'length') q.set('dim', dimension);
    if (tab === 'dimensions' && variant.id !== flagshipVariant(vehicle).id) q.set('variant', variant.id);
    if (compareSlug) {
      q.set('compare', compareSlug);
      if (compareVariantId) q.set('cvariant', compareVariantId);
    }
    if (paintId && paintId !== spec.paints[0].id) q.set('paint', paintId);
    if (trimId && trimId !== spec.trims[0].id) q.set('trim', trimId);
    if (wheelId && spec.wheels && wheelId !== spec.wheels[0].id) q.set('wheel', wheelId);
    if (caliperId && spec.calipers && caliperId !== spec.calipers[0].id) q.set('caliper', caliperId);
    if (sceneKind !== 'studio') q.set('scene', sceneKind);
    if (tab === 'tech' && demo && demo.id !== demos[0].id) q.set('demo', demo.id);
    // the device on show, not the visitor's last pick (a demo with no phone is not "device=phone")
    if (tab === 'tech' && demo?.devices) {
      const on = activeDevice(demo, techDevice);
      if (on && on !== demo.devices[0]) q.set('device', on);
    }
    const s = q.toString();
    window.history.replaceState(null, '', s ? `?${s}` : window.location.pathname);
  }, [ready, tab, dimension, variant.id, vehicle, paintId, trimId, caliperId, wheelId, sceneKind, spec, demo, demos, techDevice, lightMode, highBeam, lightsView, compareSlug, compareVariantId]);

  // A design comes with the caliper colour it is photographed in - unless the caliper
  // was chosen on purpose, i.e. is not the colour the design it replaces came with.
  const chooseWheel = (id: string) => {
    const wheels = spec.wheels ?? [];
    const prev = wheels.find((w) => w.id === wheelId) ?? wheels[0];
    const next = wheels.find((w) => w.id === id);
    setWheel(id);
    const now = caliperId || spec.calipers?.[0].id;
    if (next?.caliper && now === (prev?.caliper ?? spec.calipers?.[0].id)) setCaliper(next.caliper);
  };

  const d = vehicle.dimensions;
  const mm = (v: number) => `${v.toLocaleString('en-US')} mm`;
  const dims: { id: DimensionFocus; label: string; value: string }[] = [
    { id: 'length', label: 'Length', value: mm(d.lengthMm) },
    { id: 'width', label: 'Width', value: mm(d.widthMm) },
    { id: 'height', label: 'Height', value: mm(d.heightMm) },
  ];

  // The columns of a wide window: the specification sheet of the Specifications tab (id `dimensions`, kept so links still work) and the Charging tab's panel stand at
  // the right, as the car's screen does, and the camera frames the car in what is left (the device inset). On a
  // narrower one the sheet opens over the car, and the charging panel sits in the dock.
  const specsCol = Math.min(SPECS_COLUMN_W, Math.round(dash.vw * 0.4));
  const compareCol = Math.min(COMPARE_COLUMN_W, Math.round(dash.vw * 0.58));
  const currentSpecsCol = isComparing ? compareCol : specsCol;
  const chargeCol = Math.min(CHARGE_COLUMN_W, Math.round(dash.vw * 0.4));
  const specsColumn = tab === 'dimensions' && dash.wide;
  const chargeColumn = tab === 'charging' && dash.wide;
  React.useEffect(() => {
    if (tab === 'dimensions') {
      if (dash.wide && !compareMaximized) setDeviceInset({ right: Math.min(0.62, (currentSpecsCol + 28) / dash.vw), bottom: 0 });
      else setDeviceInset({ right: 0, bottom: 0 });
    } else if (tab === 'charging') {
      if (dash.wide) setDeviceInset({ right: Math.min(0.5, (chargeCol + 28) / dash.vw), bottom: 0.04 });
      else setDeviceInset({ right: 0, bottom: 0.48 });
    } else return;
    return () => setDeviceInset({ right: 0, bottom: 0 });
  }, [tab, dash.wide, dash.vw, currentSpecsCol, chargeCol, compareMaximized, setDeviceInset]);
  // the sheet gives way to the column when the window grows wide, and shuts when the tab is left
  React.useEffect(() => {
    if (dash.wide || tab !== 'dimensions') setSpecsOpen(false);
  }, [dash.wide, tab]);

  // what the dock and the demonstrations' menu leave clear at the right
  const rightPad =
    tab === 'tech' && col.active && col.wide
      ? col.colW + 40
      : boostUp && dash.wide
        ? boostColumnWidth(dash.vw) + 40
        : tab === 'dashboard' && dash.wide
          ? dash.colW + 40
          : specsColumn && !compareMaximized
            ? currentSpecsCol + 40
            : chargeColumn
              ? chargeCol + 40
              : 0;

  const sources = [...vehicle.sources, ...(vehicle.configurator?.sources ?? [])].filter(
    (s, i, all) => all.findIndex((o) => o.url === s.url) === i,
  );
  const hint =
    (tab === 'colour' || tab === 'interior') && vehicle.openings?.length
      ? 'Tap a door, the bonnet or the tailgate to open it.'
      : undefined;
  const playing =
    tab === 'tech'
      ? demo
      : tab === 'charging' && dash.wide
        ? (charging ?? undefined)
        : undefined;

  if (ready && isComparing && compareVehicle && compareVariant) {
    return (
      <Comparison3DShowroom
        vehicleA={vehicle}
        variantA={variant}
        vehicleB={compareVehicle}
        variantB={compareVariant}
        onSelectVehicleB={(slug) => setCompareSlug(slug)}
        onSelectVariantA={(id) => setVariant(id)}
        onSelectVariantB={(id) => setCompareVariantId(id)}
        onClose={() => setCompareSlug(null)}
      />
    );
  }

  return (
    <div ref={root} className="fixed inset-0 select-none overflow-hidden bg-[#f1f2f4] text-neutral-900">
      {ready && webgl && <ShowroomViewer vehicle={vehicle} variant={variant} className="absolute inset-0" />}
      {webgl === false && (
        <div className="absolute inset-0 grid place-items-center px-6 text-center">
          <p className="max-w-sm text-[13px] leading-relaxed text-neutral-600">
            The showroom draws the cars in 3D and this browser has WebGL turned off or does not support it. Turn on hardware acceleration, or try another browser.
          </p>
        </div>
      )}

      {/* the menu and the dock stay hidden until the address's state is applied: a deep link never flashes the Colour tab */}
      <header ref={top} className={`pointer-events-none absolute inset-x-0 top-0 z-40 px-3 pt-3 sm:px-5 sm:pt-4 ${ready ? '' : 'invisible'}`}>
        <div className="flex flex-wrap items-center gap-x-2 gap-y-2 xl:grid xl:grid-cols-[1fr_auto_1fr]">
          <div className="order-1 xl:order-none xl:justify-self-start">
            <CarMenu current={vehicle.slug} cars={cars} tab={tab} />
          </div>
          <div className="order-3 flex w-full justify-center xl:order-none xl:w-auto">
            <TabBar
              tab={tab}
              onTab={setTab}
              disabled={hasCabin ? {} : { interior: 'The interior is not built yet', xray: 'The interior is not built yet' }}
              hidden={[
                ...(vehicle.xray ? [] : ['xray' as const]),
                ...(hasWheelTab ? [] : ['wheels' as const]),
                ...(hasCharging ? [] : ['charging' as const]),
                ...(hasTech ? [] : ['tech' as const]),
              ]}
            />
          </div>
          <div className="order-2 ml-auto flex items-center gap-2 xl:order-none xl:justify-self-end">
            <button
              type="button"
              onClick={() => setCompareSlug(otherCars[0]?.slug ?? null)}
              className={`pointer-events-auto flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[12px] font-medium text-neutral-800 transition-colors ${GLASS} ${FOCUS}`}
              title="Compare side-by-side with another model"
            >
              <span>◫</span>
              <span>Compare</span>
            </button>
            {canCity && <SceneToggle scene={sceneKind} onScene={setSceneKind} />}
            {Boolean(vehicle.openings?.length) && <SoundToggle />}
            <InfoButton title={TITLES[tab]} note={NOTES[tab]} hint={hint} sources={sources} />
          </div>
        </div>
        {/* the Tech tab's demonstrations: a second row of the menu, clear of the devices' column */}
        {tab === 'tech' && demo && demos.length > 1 && !boostSheet && (
          <div className="mt-2 flex justify-center" style={rightPad ? { paddingRight: rightPad } : undefined}>
            <TechChips demos={demos} selected={demo.id} onSelect={setTechDemo} />
          </div>
        )}
      </header>

      {ready && tab === 'tech' && demo && <TechDevices vehicle={vehicle} variant={variant} demo={demo} />}
      {ready && tab === 'tech' && demo?.driver === 'boost' && <BoostPopup vehicle={vehicle} variant={variant} />}
      {ready && tab === 'dashboard' && (
        <DashboardScreen vehicle={vehicle} variant={variant} open={screenOpen} onClose={closeScreen} />
      )}
      {ready && specsColumn && (
        <aside
          className={`pointer-events-none absolute z-10 flex ${BELOW_TOP} ${
            compareMaximized ? 'inset-x-4 sm:inset-x-8 bottom-3 justify-center' : 'bottom-3 right-4'
          }`}
          style={compareMaximized ? undefined : { width: currentSpecsCol }}
          aria-label={isComparing ? 'Vehicle Comparison' : 'Specifications'}
        >
          <div className={compareMaximized ? 'w-full max-w-5xl flex h-full' : 'w-full flex h-full'}>
            <SpecsPanel
              vehicle={vehicle}
              variant={variant}
              onVariant={setVariant}
              dimension={dimension}
              onDimension={setDimension}
              sources={sources}
              onCharging={hasCharging ? () => setTab('charging') : undefined}
              compact={false}
              compareVehicle={compareVehicle}
              compareVariant={compareVariant}
              onSelectCompareVehicle={setCompareSlug}
              onCompareVariant={setCompareVariantId}
              isComparing={isComparing}
              onToggleComparing={(on) => {
                setCompareSlug(on ? (compareSlug ?? otherCars[0]?.slug ?? null) : null);
                if (!on) setCompareMaximized(false);
              }}
              isMaximized={compareMaximized}
              onToggleMaximize={() => setCompareMaximized((m) => !m)}
            />
          </div>
        </aside>
      )}
      {ready && tab === 'dimensions' && !dash.wide && specsOpen && (
        <aside className={`pointer-events-none absolute inset-x-2 bottom-[84px] z-10 flex ${BELOW_TOP}`} aria-label={isComparing ? 'Vehicle Comparison' : 'Specifications'}>
          <SpecsPanel
            vehicle={vehicle}
            variant={variant}
            onVariant={setVariant}
            dimension={dimension}
            onDimension={setDimension}
            sources={sources}
            onCharging={hasCharging ? () => setTab('charging') : undefined}
            compact
            compareVehicle={compareVehicle}
            compareVariant={compareVariant}
            onSelectCompareVehicle={setCompareSlug}
            onCompareVariant={setCompareVariantId}
            isComparing={isComparing}
            onToggleComparing={(on) => {
              setCompareSlug(on ? (compareSlug ?? otherCars[0]?.slug ?? null) : null);
            }}
          />
        </aside>
      )}
      {ready && tab === 'charging' && (
        <div className="pointer-events-none fixed inset-0 z-20 overflow-hidden" aria-label="Charging">
          <ChargePanel vehicle={vehicle} compact={!dash.wide} />
        </div>
      )}

      <div
        className={`pointer-events-none absolute inset-x-0 bottom-0 z-20 flex flex-col items-center gap-3 px-3 pb-3 sm:pb-5 ${ready ? '' : 'invisible'}`}
        // on a wide window the devices stand in a column at the right: the dock centres in what is left
        style={rightPad ? { paddingRight: rightPad } : undefined}
      >
        {tab === 'colour' && <PaintSwatches paints={spec.paints} selected={paintId} onSelect={setPaint} />}
        {tab === 'interior' && <TrimSwatches trims={spec.trims} selected={trimId} onSelect={setTrim} />}
        {tab === 'wheels' && spec.wheels && spec.wheels.length > 1 && (
          <WheelChips wheels={spec.wheels} selected={wheelId} onSelect={chooseWheel} />
        )}
        {tab === 'wheels' && spec.calipers && spec.calipers.length > 1 && (
          <CaliperSwatches calipers={spec.calipers} selected={caliperId} onSelect={setCaliper} />
        )}
        {tab === 'dimensions' && specsColumn && (
          <div className="pointer-events-none flex max-w-full flex-wrap items-center justify-center gap-2">
            {!isComparing && <DimensionChips items={dims} selected={dimension} onSelect={setDimension} />}
            <button
              type="button"
              aria-pressed={isComparing}
              onClick={() => {
                if (isComparing) {
                  setCompareSlug(null);
                  setCompareMaximized(false);
                } else {
                  setCompareSlug(otherCars[0]?.slug ?? null);
                }
              }}
              className={`pointer-events-auto flex items-center gap-1.5 rounded-full px-4 py-2 text-[12px] font-medium transition-colors ${FOCUS} ${
                isComparing
                  ? 'bg-neutral-900 text-white shadow-sm'
                  : `text-neutral-700 ${GLASS}`
              }`}
            >
              <span>◫</span>
              <span>{isComparing ? 'Exit Comparison' : 'Compare with another model'}</span>
            </button>
          </div>
        )}
        {tab === 'dimensions' && !specsColumn && (
          <div className="pointer-events-none flex max-w-full flex-wrap items-center justify-center gap-2">
            {/* the open sheet has the dimensions in it: the chips would stand over its foot */}
            {!specsOpen && <DimensionChips items={dims} selected={dimension} onSelect={setDimension} />}
            <button
              type="button"
              aria-pressed={specsOpen && !isComparing}
              onClick={() => {
                if (isComparing) {
                  setCompareSlug(null);
                  setSpecsOpen(true);
                } else {
                  setSpecsOpen((v) => !v);
                }
              }}
              className={`pointer-events-auto rounded-full px-4 py-2 text-[12px] font-medium transition-colors ${FOCUS} ${
                specsOpen && !isComparing
                  ? 'bg-neutral-900 text-white shadow-sm'
                  : `text-neutral-700 ${GLASS}`
              }`}
            >
              {specsOpen && !isComparing ? 'Hide specifications' : 'Specifications'}
            </button>
            <button
              type="button"
              aria-pressed={isComparing}
              onClick={() => {
                if (isComparing) {
                  setCompareSlug(null);
                  setSpecsOpen(false);
                } else {
                  setCompareSlug(otherCars[0]?.slug ?? null);
                  setSpecsOpen(true);
                }
              }}
              className={`pointer-events-auto flex items-center gap-1.5 rounded-full px-4 py-2 text-[12px] font-medium transition-colors ${FOCUS} ${
                isComparing
                  ? 'bg-neutral-900 text-white shadow-sm'
                  : `text-neutral-700 ${GLASS}`
              }`}
            >
              <span>◫</span>
              <span>{isComparing ? 'Close Compare' : 'Compare'}</span>
            </button>
          </div>
        )}
        {tab === 'dashboard' && (
          <DashboardControls screenFits={dash.screenFits} wide={dash.wide} screenOpen={screenOpen} onScreen={setScreenOpen} />
        )}
        {tab === 'tech' && demo && (
          <>
            {demo.driver === 'carpet' && <RideTools vehicle={vehicle} showHeights={!col.active} />}
            {demo.driver === 'launch' && <LaunchTools vehicle={vehicle} />}
            {demo.driver === 'swivel' && <SwivelTools />}
            {demo.driver === 'sensors' && <SensorsTools vehicle={vehicle} />}
            {demo.driver === 'boost' && !boostSheet && <BoostTools />}
            {isChassisDriver(demo.driver) && <ChassisTools driver={demo.driver} />}
            {demo.driver === 'park' && demo.params?.noseIn === 1 && <NoseInTools />}
            {demo.driver === 'park' && (demo.params?.search ?? 0) > 0 && <ParkAssistTools />}
          </>
        )}
        {playing && (
          <TechControls
            speed={techSpeed}
            onSpeed={setTechSpeed}
            spec={playing}
            disabled={
              techStatus === 'none'
                ? "This model's wheels are not rigged for demonstrations yet"
                : techStatus === 'loading'
                  ? 'Loading the model'
                  : undefined
            }
          />
        )}
      </div>
    </div>
  );
}
