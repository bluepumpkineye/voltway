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
import { visibleDemos } from '@/lib/tech/demos';
import { CarMenu, GLASS, SceneToggle, TabBar } from './Chrome';
import { CaliperSwatches, DimensionChips, PaintSwatches, TrimSwatches, WheelChips } from './Swatches';
import { TechChips, TechControls, TechFacts } from './Tech';
import { TechDevices, useDeviceColumn } from '@/components/tech/TechDevices';

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

const TABS: ShowroomTab[] = ['colour', 'interior', 'wheels', 'dimensions', 'xray', 'tech'];
const DIMS: DimensionFocus[] = ['length', 'width', 'height'];

const NOTES: Record<ShowroomTab, string> = {
  colour:
    "Paint names are the maker's. Colours are matched to its published images under our studio lights, so they are approximate.",
  interior:
    "Cabin colourways follow the maker's options; which panel takes which colour is our model's, so colours are approximate. Drag to look around; the centre screen is live.",
  wheels:
    "Wheel designs and tyre sizes are the maker's, modelled from published photographs. Caliper colours follow its options (red, grey, yellow and others) and are approximate.",
  dimensions: "Figures are the manufacturer's published dimensions.",
  xray: "The upper body is shown as a see-through shell, with the doors removed, so the cabin reads through it. A modelled view, not the maker's.",
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
  // a car with something to demonstrate
  const demos = React.useMemo(() => visibleDemos(vehicle), [vehicle]);
  const hasTech = demos.length > 0;

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
  const {
    reset, setTab, setPaint, setTrim, setCaliper, setWheel, setSceneKind, setDimension, setTechDemo, setTechSpeed,
    setTechAvailable, setTechDevice,
  } = useVehicleStore.getState();
  const techDevice = useVehicleStore((s) => s.techDevice);
  const demo = demos.find((d) => d.id === techDemoId) ?? demos[0];

  const variant = vehicle.variants.find((v) => v.id === variantId) ?? flagshipVariant(vehicle);

  // the devices of the Tech tab: the car's screen can start demos while the showroom is mounted (the dock
  // leaves their column clear on a wide window; the devices themselves frame the camera, see TechDevices)
  const col = useDeviceColumn(tab === 'tech' ? demo : undefined);
  React.useEffect(() => {
    setTechAvailable(true);
    return () => setTechAvailable(false);
  }, [setTechAvailable]);

  // The viewer mounts only once the URL's state is applied, so a deep link
  // opens on its own pose instead of flying there from the default.
  const [ready, setReady] = React.useState(false);
  React.useEffect(() => {
    reset(flagshipVariant(vehicle).id, vehicle.cockpit.defaultTheme);
    const q = new URLSearchParams(window.location.search);
    const wantTab = q.get('tab') as ShowroomTab | null;
    if (
      wantTab &&
      TABS.includes(wantTab) &&
      (wantTab !== 'interior' || hasCabin) &&
      (wantTab !== 'wheels' || hasWheelTab) &&
      (wantTab !== 'xray' || (hasCabin && vehicle.xray)) &&
      (wantTab !== 'tech' || hasTech)
    )
      setTab(wantTab);
    const wantDemo = q.get('demo');
    if (wantDemo && demos.some((d) => d.id === wantDemo)) setTechDemo(wantDemo);
    const wantDevice = q.get('device');
    if (wantDevice === 'phone' || wantDevice === 'dashboard') setTechDevice(wantDevice);
    const wantDim = q.get('dim') as DimensionFocus | null;
    if (wantDim && DIMS.includes(wantDim)) setDimension(wantDim);
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
    setReady(true);
    // the actions are stable store functions; the vehicle is fixed per mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // write the state back, so the address is always a link to what is on screen
  React.useEffect(() => {
    if (!ready) return;
    const q = new URLSearchParams();
    if (tab !== 'colour') q.set('tab', tab);
    if (tab === 'dimensions' && dimension !== 'length') q.set('dim', dimension);
    if (paintId && paintId !== spec.paints[0].id) q.set('paint', paintId);
    if (trimId && trimId !== spec.trims[0].id) q.set('trim', trimId);
    if (wheelId && spec.wheels && wheelId !== spec.wheels[0].id) q.set('wheel', wheelId);
    if (caliperId && spec.calipers && caliperId !== spec.calipers[0].id) q.set('caliper', caliperId);
    if (sceneKind !== 'studio') q.set('scene', sceneKind);
    if (tab === 'tech' && demo && demo.id !== demos[0].id) q.set('demo', demo.id);
    if (tab === 'tech' && demo?.devices && techDevice !== demo.devices[0]) q.set('device', techDevice);
    const s = q.toString();
    window.history.replaceState(null, '', s ? `?${s}` : window.location.pathname);
  }, [ready, tab, dimension, paintId, trimId, caliperId, wheelId, sceneKind, spec, demo, demos, techDevice]);

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

  return (
    <div className="fixed inset-0 select-none overflow-hidden bg-[#f1f2f4] text-neutral-900">
      {ready && <ShowroomViewer vehicle={vehicle} variant={variant} className="absolute inset-0" />}

      <div className="pointer-events-none absolute inset-x-0 top-0 z-20 flex items-start justify-between gap-3 p-3 sm:p-5">
        <CarMenu backHref={`/vehicles/${vehicle.slug}`} current={vehicle.slug} cars={cars} />
        {canCity && (
          <div className="pointer-events-auto">
            <SceneToggle scene={sceneKind} onScene={setSceneKind} />
          </div>
        )}
      </div>

      {ready && tab === 'tech' && demo && <TechDevices vehicle={vehicle} variant={variant} demo={demo} />}

      <div
        className="pointer-events-none absolute inset-x-0 bottom-0 z-20 flex flex-col items-center gap-3 px-3 pb-3 sm:pb-5"
        // on a wide window the devices stand in a column at the right: the dock centres in what is left
        style={tab === 'tech' && col.active && col.wide ? { paddingRight: col.colW + 40 } : undefined}
      >
        {tab === 'colour' && <PaintSwatches paints={spec.paints} selected={paintId} onSelect={setPaint} />}
        {tab === 'interior' && <TrimSwatches trims={spec.trims} selected={trimId} onSelect={setTrim} />}
        {tab === 'wheels' && spec.wheels && spec.wheels.length > 1 && (
          <WheelChips wheels={spec.wheels} selected={wheelId} onSelect={chooseWheel} />
        )}
        {tab === 'wheels' && spec.calipers && spec.calipers.length > 1 && (
          <CaliperSwatches calipers={spec.calipers} selected={caliperId} onSelect={setCaliper} />
        )}
        {tab === 'dimensions' && <DimensionChips items={dims} selected={dimension} onSelect={setDimension} />}
        {tab === 'tech' && demo && (
          <>
            {(col.wide || !col.active) && <TechFacts spec={demo} />}
            {demos.length > 1 && (col.wide || !col.active) && <TechChips demos={demos} selected={demo.id} onSelect={setTechDemo} />}
            <TechControls
              speed={techSpeed}
              onSpeed={setTechSpeed}
              disabled={
                techStatus === 'none'
                  ? "This model's wheels are not rigged for demonstrations yet"
                  : techStatus === 'loading'
                    ? 'Loading the model'
                    : undefined
              }
            />
          </>
        )}
        <div className="pointer-events-auto">
          <TabBar
            tab={tab}
            onTab={setTab}
            disabled={hasCabin ? {} : { interior: 'The interior is not built yet', xray: 'The interior is not built yet' }}
            hidden={[
              ...(vehicle.xray ? [] : ['xray' as const]),
              ...(hasWheelTab ? [] : ['wheels' as const]),
              ...(hasTech ? [] : ['tech' as const]),
            ]}
          />
        </div>
        <p className={`max-w-[620px] rounded-2xl px-3.5 py-1.5 text-center text-[11px] leading-snug text-neutral-600 ${GLASS} ${tab === 'tech' && col.active && !col.wide ? 'hidden' : ''}`}>
          {NOTES[tab]}
          {tab !== 'dimensions' && tab !== 'xray' && tab !== 'wheels' && tab !== 'tech' && vehicle.openings?.length
            ? ' Tap a door, the bonnet or the tailgate to open it.'
            : ''}{' '}
          <a
            href={`/vehicles/${vehicle.slug}#sources`}
            className="pointer-events-auto underline decoration-neutral-300 underline-offset-2 hover:text-neutral-800"
          >
            Sources
          </a>
        </p>
      </div>
    </div>
  );
}
