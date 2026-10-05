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
import { CarMenu, GLASS, SceneToggle, TabBar } from './Chrome';
import { DimensionChips, PaintSwatches, TrimSwatches } from './Swatches';

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

const TABS: ShowroomTab[] = ['colour', 'interior', 'dimensions'];
const DIMS: DimensionFocus[] = ['length', 'width', 'height'];

const NOTES: Record<ShowroomTab, string> = {
  colour:
    "Paint names are the maker's. Colours are matched to its published images under our studio lights, so they are approximate.",
  interior:
    "Cabin colourways follow the maker's options; which panel takes which colour is our model's, so colours are approximate. Drag to look around; the centre screen is live.",
  dimensions: "Figures are the manufacturer's published dimensions.",
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

  const tab = useVehicleStore((s) => s.tab);
  const paintId = useVehicleStore((s) => s.paintId);
  const trimId = useVehicleStore((s) => s.trimId);
  const sceneKind = useVehicleStore((s) => s.sceneKind);
  const dimension = useVehicleStore((s) => s.dimension);
  const variantId = useVehicleStore((s) => s.variantId);
  const { reset, setTab, setPaint, setTrim, setSceneKind, setDimension } = useVehicleStore.getState();

  const variant = vehicle.variants.find((v) => v.id === variantId) ?? flagshipVariant(vehicle);

  // The viewer mounts only once the URL's state is applied, so a deep link
  // opens on its own pose instead of flying there from the default.
  const [ready, setReady] = React.useState(false);
  React.useEffect(() => {
    reset(flagshipVariant(vehicle).id);
    const q = new URLSearchParams(window.location.search);
    const wantTab = q.get('tab') as ShowroomTab | null;
    if (wantTab && TABS.includes(wantTab) && (wantTab !== 'interior' || hasCabin)) setTab(wantTab);
    const wantDim = q.get('dim') as DimensionFocus | null;
    if (wantDim && DIMS.includes(wantDim)) setDimension(wantDim);
    const wantPaint = q.get('paint');
    if (wantPaint && spec.paints.some((p) => p.id === wantPaint)) setPaint(wantPaint);
    const wantTrim = q.get('trim');
    if (wantTrim && spec.trims.some((t) => t.id === wantTrim)) setTrim(wantTrim);
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
    if (sceneKind !== 'studio') q.set('scene', sceneKind);
    const s = q.toString();
    window.history.replaceState(null, '', s ? `?${s}` : window.location.pathname);
  }, [ready, tab, dimension, paintId, trimId, sceneKind, spec]);

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

      <div className="pointer-events-none absolute inset-x-0 bottom-0 z-20 flex flex-col items-center gap-3 px-3 pb-3 sm:pb-5">
        {tab === 'colour' && <PaintSwatches paints={spec.paints} selected={paintId} onSelect={setPaint} />}
        {tab === 'interior' && <TrimSwatches trims={spec.trims} selected={trimId} onSelect={setTrim} />}
        {tab === 'dimensions' && <DimensionChips items={dims} selected={dimension} onSelect={setDimension} />}
        <div className="pointer-events-auto">
          <TabBar
            tab={tab}
            onTab={setTab}
            disabled={hasCabin ? {} : { interior: 'The interior is not built yet' }}
          />
        </div>
        <p className={`max-w-[620px] rounded-2xl px-3.5 py-1.5 text-center text-[11px] leading-snug text-neutral-600 ${GLASS}`}>
          {NOTES[tab]}{' '}
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
