'use client';

import React from 'react';
import * as THREE from 'three';
import { Canvas, useThree } from '@react-three/fiber';
import { CameraControls, CameraControlsImpl, ContactShadows } from '@react-three/drei';
import type { Variant, Vehicle } from '@/data/vehicles/schema';
import { formatPower } from '@/data/vehicles/schema';
import { chargeMinutes10to80 } from '@/lib/performance';
import { showroomCars } from '@/lib/showroom/cars';
import { CarModel, CabinModel } from '@/components/viewer/CarModel';
import { GroundShadow, StudioShowroom, STUDIO_WHITE } from '@/components/viewer/StudioShowroom';
import { FOCUS, GLASS } from './Chrome';

type BottomTab = 'specs' | 'dimensions' | 'space' | 'color';

function getCarThumbnail(slug: string): string {
  const map: Record<string, string> = {
    'xiaomi-su7-ultra': '/hmi/xiaomi-su7-ultra/parked.webp',
    'luxeed-rx': '/hmi/luxeed-rx/car34.webp',
    'zeekr-7x': '/hmi/zeekr-7x/car34.webp',
    'denza-z9': '/hmi/denza-z9/car34.webp',
    'xpeng-g9l': '/hmi/xpeng-g9l/car34.webp',
    'avatr-06t': '/hmi/avatr-06t/car34.webp',
    'nio-es8': '/hmi/nio-es8/car34.webp',
    'voyah-passion-s': '/hmi/voyah-passion-s/car34.webp',
  };
  return map[slug] ?? '/hmi/luxeed-rx/car34.webp';
}

function formatPriceWan(priceCny?: number): string {
  if (!priceCny) return '–';
  const wan = (priceCny / 10000).toFixed(2);
  return `¥${wan} 万起`;
}

const mm = (v: number) => `${v.toLocaleString('en-US')} mm`;

interface Comparison3DShowroomProps {
  vehicleA: Vehicle;
  variantA: Variant;
  vehicleB: Vehicle;
  variantB: Variant;
  onSelectVehicleB: (slug: string) => void;
  onSelectVariantA?: (id: string) => void;
  onSelectVariantB?: (id: string) => void;
  onClose: () => void;
}

// ------------------------------------------------------------- 3D Canvas
function SyncedCameraControls({
  id,
  angle,
  activeSourceRef,
  onUserUpdate,
}: {
  id: string;
  angle: { az: number; el: number; dist: number };
  activeSourceRef: React.MutableRefObject<string | null>;
  onUserUpdate: (source: string, az: number, el: number, dist: number) => void;
}) {
  const controlsRef = React.useRef<CameraControlsImpl>(null);
  const { gl, invalidate } = useThree();
  const angleRef = React.useRef(angle);
  angleRef.current = angle;

  React.useEffect(() => {
    const c = controlsRef.current;
    if (!c) return;
    const A = CameraControlsImpl.ACTION;
    c.mouseButtons.left = A.ROTATE;
    c.mouseButtons.right = A.NONE;
    c.mouseButtons.middle = A.NONE;
    c.mouseButtons.wheel = A.DOLLY;
    c.touches.one = A.TOUCH_ROTATE;
    c.touches.two = A.TOUCH_DOLLY;
    c.touches.three = A.NONE;
    c.draggingSmoothTime = 0.05;

    // Set initial camera pose
    c.setLookAt(0, 0.9, angle.dist, 0, 0.65, 0, false);
    c.rotateTo(angle.az, angle.el, false);
    c.dollyTo(angle.dist, false);
    invalidate();

    const dom = gl.domElement;
    const makeActive = () => {
      activeSourceRef.current = id;
    };

    dom.addEventListener('pointerdown', makeActive);
    dom.addEventListener('wheel', makeActive, { passive: true });
    dom.addEventListener('touchstart', makeActive, { passive: true });

    const onControl = () => {
      activeSourceRef.current = id;
      onUserUpdate(id, c.azimuthAngle, c.polarAngle, c.distance);
    };

    const onUpdate = () => {
      if (activeSourceRef.current === id) {
        const az = c.azimuthAngle;
        const el = c.polarAngle;
        const dist = c.distance;
        if (
          Math.abs(az - angleRef.current.az) > 0.0005 ||
          Math.abs(el - angleRef.current.el) > 0.0005 ||
          Math.abs(dist - angleRef.current.dist) > 0.002
        ) {
          onUserUpdate(id, az, el, dist);
        }
      }
    };

    const onRest = () => {
      if (activeSourceRef.current === id) {
        activeSourceRef.current = null;
      }
    };

    c.addEventListener('control', onControl);
    c.addEventListener('update', onUpdate);
    c.addEventListener('rest', onRest);

    return () => {
      dom.removeEventListener('pointerdown', makeActive);
      dom.removeEventListener('wheel', makeActive);
      dom.removeEventListener('touchstart', makeActive);
      c.removeEventListener('control', onControl);
      c.removeEventListener('update', onUpdate);
      c.removeEventListener('rest', onRest);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, gl, onUserUpdate, activeSourceRef, invalidate]);

  // Synchronize from companion canvas
  React.useEffect(() => {
    const c = controlsRef.current;
    if (!c) return;
    if (activeSourceRef.current === id) return;

    c.rotateTo(angle.az, angle.el, false);
    c.dollyTo(angle.dist, false);
    invalidate();
  }, [angle, id, invalidate, activeSourceRef]);

  return <CameraControls ref={controlsRef} minDistance={4.5} maxDistance={12} maxPolarAngle={Math.PI / 2 - 0.05} />;
}

function CarCanvas({
  id,
  vehicle,
  variant,
  paintId,
  angle,
  activeSourceRef,
  onUserUpdate,
}: {
  id: string;
  vehicle: Vehicle;
  variant: Variant;
  paintId?: string;
  angle: { az: number; el: number; dist: number };
  activeSourceRef: React.MutableRefObject<string | null>;
  onUserUpdate: (source: string, az: number, el: number, dist: number) => void;
}) {
  const studioShadow = vehicle.assets.studioShadow;
  const { interiorModelUrl, interiorProbeUrl } = vehicle.assets;

  return (
    <Canvas
      frameloop="demand"
      shadows
      dpr={[1, 2]}
      gl={{
        antialias: true,
        stencil: true,
        toneMapping: THREE.NeutralToneMapping,
        toneMappingExposure: 0.92,
      }}
      camera={{ fov: 30, near: 0.05, far: 180, position: [0, 1.2, 7.2] }}
      onCreated={({ gl }) => {
        gl.setClearColor(STUDIO_WHITE, 0);
      }}
      className="h-full w-full"
    >
      <StudioShowroom reflections={false} inside={false} />
      <React.Suspense fallback={null}>
        <CarModel
          vehicle={vehicle}
          variant={variant}
          url={vehicle.assets.modelUrl!}
          customPaintId={paintId}
          forceClearGlass
        />
        {interiorModelUrl && (
          <CabinModel
            vehicle={vehicle}
            variant={variant}
            url={interiorModelUrl}
            probeUrl={interiorProbeUrl}
          />
        )}
        {studioShadow ? (
          <GroundShadow shadow={studioShadow} />
        ) : (
          <ContactShadows position={[0, 0.002, 0]} opacity={0.5} scale={14} blur={2.8} far={3.2} resolution={1024} frames={1} />
        )}
      </React.Suspense>
      <SyncedCameraControls
        id={id}
        angle={angle}
        activeSourceRef={activeSourceRef}
        onUserUpdate={onUserUpdate}
      />
    </Canvas>
  );
}

// ------------------------------------------------------------- Main View
export function Comparison3DShowroom({
  vehicleA,
  variantA,
  vehicleB,
  variantB,
  onSelectVehicleB,
  onSelectVariantA,
  onSelectVariantB,
  onClose,
}: Comparison3DShowroomProps) {
  // Drawer state
  const [drawerOpen, setDrawerOpen] = React.useState(true);
  const [bottomTab, setBottomTab] = React.useState<BottomTab>('specs');
  const [specsMinimized, setSpecsMinimized] = React.useState(false);

  // Paints state for real-time 3D customization
  const [paintA, setPaintA] = React.useState<string>(vehicleA.configurator?.paints[0]?.id ?? '');
  const [paintB, setPaintB] = React.useState<string>(vehicleB.configurator?.paints[0]?.id ?? '');

  // Reset paint when vehicle changes
  React.useEffect(() => {
    setPaintB(vehicleB.configurator?.paints[0]?.id ?? '');
  }, [vehicleB.slug, vehicleB.configurator?.paints]);

  // Synchronized camera angle: az (azimuth), el (elevation), dist (distance)
  const [cameraAngle, setCameraAngle] = React.useState({ az: 0.62, el: 1.38, dist: 7.2 });
  const activeSourceRef = React.useRef<string | null>(null);

  const handleUserUpdate = React.useCallback((source: string, az: number, el: number, dist: number) => {
    activeSourceRef.current = source;
    setCameraAngle({ az, el, dist });
  }, []);

  const allCars = React.useMemo(() => showroomCars(), []);

  // Decision metrics extraction
  const pA = variantA.performance;
  const pB = variantB.performance;
  const bA = variantA.battery;
  const bB = variantB.battery;
  const dA = vehicleA.dimensions;
  const dB = vehicleB.dimensions;

  const minA = chargeMinutes10to80(variantA);
  const minB = chargeMinutes10to80(variantB);
  const rangeA = variantA.range[0]?.km ?? 0;
  const rangeB = variantB.range[0]?.km ?? 0;

  return (
    <div className="fixed inset-0 select-none overflow-hidden bg-[#f1f2f4] text-neutral-900">
      {/* 3D Split Screen Area */}
      <div className="absolute inset-0 flex flex-col md:flex-row">
        {/* Left Viewport: Vehicle A */}
        <div className="relative flex-1 h-1/2 md:h-full overflow-hidden">
          <CarCanvas
            id="left"
            vehicle={vehicleA}
            variant={variantA}
            paintId={paintA}
            angle={cameraAngle}
            activeSourceRef={activeSourceRef}
            onUserUpdate={handleUserUpdate}
          />

          {/* Model A Top Header Badge */}
          <div className="pointer-events-none absolute left-0 right-0 top-3 z-20 flex justify-center px-4">
            <div className="flex flex-col items-center">
              <h2 className="text-[17px] font-bold tracking-tight text-neutral-900 drop-shadow-xs">
                {vehicleA.brand} {vehicleA.model}
              </h2>
              <div className="flex items-center gap-1.5 text-[11px] font-medium text-neutral-500">
                <span>{vehicleA.group}</span>
                <span>·</span>
                <span>{vehicleA.bodyStyle}</span>
              </div>
              {vehicleA.variants.length > 1 && onSelectVariantA && (
                <div className="pointer-events-auto mt-1 flex items-center rounded-full bg-white/80 px-2.5 py-0.5 text-[11px] font-medium text-neutral-700 shadow-xs ring-1 ring-black/5 backdrop-blur-xs">
                  <select
                    value={variantA.id}
                    onChange={(e) => onSelectVariantA(e.target.value)}
                    aria-label={`Select variant for ${vehicleA.model}`}
                    className="bg-transparent text-[11px] font-medium text-neutral-800 outline-none cursor-pointer"
                  >
                    {vehicleA.variants.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.name} · {formatPriceWan(v.priceCny)}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Subtle Middle Seam Divider */}
        <div className="hidden md:block absolute inset-y-0 left-1/2 w-px bg-black/[0.08] z-10 pointer-events-none" />

        {/* Right Viewport: Vehicle B */}
        <div className="relative flex-1 h-1/2 md:h-full overflow-hidden">
          <CarCanvas
            id="right"
            vehicle={vehicleB}
            variant={variantB}
            paintId={paintB}
            angle={cameraAngle}
            activeSourceRef={activeSourceRef}
            onUserUpdate={handleUserUpdate}
          />

          {/* Model B Top Header Badge with Selector dropdown button */}
          <div className="pointer-events-none absolute left-0 right-0 top-3 z-20 flex justify-center px-4">
            <div className="flex flex-col items-center">
              <button
                type="button"
                onClick={() => setDrawerOpen((o) => !o)}
                className={`pointer-events-auto flex items-center gap-1.5 rounded-full px-3 py-1 transition-colors hover:bg-black/[0.06] ${FOCUS}`}
              >
                <h2 className="text-[17px] font-bold tracking-tight text-neutral-900 drop-shadow-xs">
                  {vehicleB.brand} {vehicleB.model}
                </h2>
                <svg
                  width="10"
                  height="6"
                  viewBox="0 0 10 6"
                  fill="none"
                  className={`text-neutral-700 transition-transform ${drawerOpen ? 'rotate-180' : ''}`}
                >
                  <path d="M1 1L5 5L9 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
              <div className="flex items-center gap-1.5 text-[11px] font-medium text-neutral-500">
                <span>{vehicleB.group}</span>
                <span>·</span>
                <span>{vehicleB.bodyStyle}</span>
              </div>
              {vehicleB.variants.length > 1 && onSelectVariantB && (
                <div className="pointer-events-auto mt-1 flex items-center rounded-full bg-white/80 px-2.5 py-0.5 text-[11px] font-medium text-neutral-700 shadow-xs ring-1 ring-black/5 backdrop-blur-xs">
                  <select
                    value={variantB.id}
                    onChange={(e) => onSelectVariantB(e.target.value)}
                    aria-label={`Select variant for ${vehicleB.model}`}
                    className="bg-transparent text-[11px] font-medium text-neutral-800 outline-none cursor-pointer"
                  >
                    {vehicleB.variants.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.name} · {formatPriceWan(v.priceCny)}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Top Left Back Button */}
      <div className="absolute left-3 top-3 z-30">
        <button
          type="button"
          onClick={onClose}
          aria-label="Exit comparison mode"
          className={`flex h-10 w-10 items-center justify-center rounded-full text-neutral-700 transition-transform active:scale-95 ${GLASS} ${FOCUS}`}
          title="Return to single car showroom"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
      </div>

      {/* Top Right Drawer Toggle Button */}
      <div className="absolute right-3 top-3 z-30">
        <button
          type="button"
          onClick={() => setDrawerOpen((o) => !o)}
          aria-expanded={drawerOpen}
          className={`flex items-center gap-2 rounded-full px-4 py-2 text-[12px] font-medium text-neutral-800 transition-colors ${GLASS} ${FOCUS}`}
        >
          <span>{drawerOpen ? '收起车型' : '选择车型'}</span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 6h16M4 12h16m-7 6h7" />
          </svg>
        </button>
      </div>

      {/* Right Drawer: 选择车型 (Select Model) - Exactly like HIMA screenshot */}
      <aside
        className={`fixed bottom-0 right-0 top-0 z-40 flex w-76 sm:w-84 flex-col bg-white/95 backdrop-blur-2xl ring-1 ring-black/[0.08] shadow-2xl transition-transform duration-300 ease-out ${
          drawerOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
        aria-label="Select comparison model"
      >
        {/* Drawer Header */}
        <div className="flex items-center justify-between border-b border-black/[0.06] px-5 py-4">
          <div className="flex items-center gap-2">
            <h3 className="text-[15px] font-bold text-neutral-900">选择车型</h3>
            <span className="rounded-full bg-black/[0.05] px-2 py-0.5 text-[10px] font-medium text-neutral-500">
              Select Model
            </span>
          </div>
          <button
            type="button"
            onClick={() => setDrawerOpen(false)}
            aria-label="Close model list"
            className={`rounded-full p-1.5 text-neutral-400 hover:bg-black/[0.05] hover:text-neutral-800 ${FOCUS}`}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Drawer Vehicle Card List */}
        <div className="min-h-0 flex-1 overflow-y-auto p-3 space-y-2.5">
          {allCars.map((car) => {
            const isSelected = car.slug === vehicleB.slug;
            const isCarA = car.slug === vehicleA.slug;
            const thumb = getCarThumbnail(car.slug);
            const price = car.variants[0]?.priceCny;

            return (
              <button
                key={car.slug}
                type="button"
                onClick={() => {
                  onSelectVehicleB(car.slug);
                }}
                className={`group flex w-full flex-col rounded-xl p-2.5 text-left transition-all ${FOCUS} ${
                  isSelected
                    ? 'bg-neutral-900 text-white shadow-md ring-2 ring-neutral-900 ring-offset-1'
                    : isCarA
                      ? 'bg-black/[0.02] text-neutral-500 opacity-60'
                      : 'bg-black/[0.03] text-neutral-800 hover:bg-black/[0.06]'
                }`}
              >
                {/* Vehicle Thumbnail Preview */}
                <div className="relative mb-2 flex h-24 w-full items-center justify-center overflow-hidden rounded-lg bg-white/70 p-2">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={thumb}
                    alt={`${car.brand} ${car.model}`}
                    className="max-h-full max-w-full object-contain transition-transform duration-300 group-hover:scale-105"
                  />
                  {isSelected && (
                    <span className="absolute right-2 top-2 flex h-5 w-5 items-center justify-center rounded-full bg-neutral-900 text-[10px] font-bold text-white shadow-sm">
                      ✓
                    </span>
                  )}
                  {isCarA && (
                    <span className="absolute left-2 top-2 rounded-full bg-black/60 px-2 py-0.5 text-[9px] font-semibold text-white backdrop-blur-xs">
                      Left Car (Current)
                    </span>
                  )}
                </div>

                {/* Car Info */}
                <div className="flex items-baseline justify-between gap-2">
                  <span className="truncate text-[13.5px] font-bold">
                    {car.brand} {car.model}
                  </span>
                  <span className={`shrink-0 text-[11px] font-semibold ${isSelected ? 'text-white/90' : 'text-neutral-900'}`}>
                    {formatPriceWan(price)}
                  </span>
                </div>
                <div className="mt-0.5 flex items-center justify-between text-[10.5px]">
                  <span className={isSelected ? 'text-white/70' : 'text-neutral-500'}>
                    {car.group} · {car.bodyStyle}
                  </span>
                  <span className={isSelected ? 'text-white/60' : 'text-neutral-400'}>
                    {car.year}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </aside>

      {/* Floating Bottom Section: Mode Selector Pills (HIMA Style) */}
      <div className="pointer-events-none absolute inset-x-0 bottom-4 z-30 flex flex-col items-center gap-3 px-3">
        {/* Floating Content Sheet according to Active Bottom Tab */}
        {bottomTab === 'specs' && (
          <div className="pointer-events-auto w-full max-w-3xl rounded-2xl p-4 shadow-xl ring-1 ring-black/[0.08] backdrop-blur-2xl bg-white/90 transition-all">
            <div className="flex items-center justify-between border-b border-black/[0.06] pb-2">
              <div className="flex items-center gap-2">
                <span className="text-[12px] font-bold uppercase tracking-wider text-neutral-800">
                  参数规格对比 · Specifications
                </span>
                <span className="rounded-full bg-black/[0.05] px-2 py-0.5 text-[10px] font-medium text-neutral-600">
                  4–6 Decision Dimensions
                </span>
              </div>
              <button
                type="button"
                onClick={() => setSpecsMinimized((m) => !m)}
                className={`text-[11px] font-medium text-neutral-500 hover:text-neutral-900 ${FOCUS}`}
              >
                {specsMinimized ? 'Expand Specs ↑' : 'Minimize Specs ↓'}
              </button>
            </div>

            {!specsMinimized && (
              <div className="mt-3 max-h-56 overflow-y-auto space-y-2 pr-1">
                {/* 1. Acceleration */}
                <div className="rounded-xl bg-black/[0.03] p-2.5">
                  <div className="flex items-center justify-between text-[11px] text-neutral-500">
                    <span className="font-semibold text-neutral-800">1. Acceleration (0–100 km/h)</span>
                    {pA.zeroTo100S && pB.zeroTo100S && (
                      <span className="tnum rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
                        {pA.zeroTo100S < pB.zeroTo100S
                          ? `${vehicleA.brand} is ${(pB.zeroTo100S - pA.zeroTo100S).toFixed(2)}s faster`
                          : `${vehicleB.brand} is ${(pA.zeroTo100S - pB.zeroTo100S).toFixed(2)}s faster`}
                      </span>
                    )}
                  </div>
                  <div className="mt-1 grid grid-cols-2 gap-4 text-[13px] font-bold">
                    <div className="tnum text-neutral-900">{pA.zeroTo100S ? `${pA.zeroTo100S} s` : '–'}</div>
                    <div className="tnum text-right text-neutral-900">{pB.zeroTo100S ? `${pB.zeroTo100S} s` : '–'}</div>
                  </div>
                  <div className="mt-1 flex items-center justify-between text-[10.5px] text-neutral-500">
                    <span>{formatPower(pA.powerKw)} · {pA.motorCount}M</span>
                    <span>{formatPower(pB.powerKw)} · {pB.motorCount}M</span>
                  </div>
                </div>

                {/* 2. Range */}
                <div className="rounded-xl bg-black/[0.03] p-2.5">
                  <div className="flex items-center justify-between text-[11px] text-neutral-500">
                    <span className="font-semibold text-neutral-800">2. Range & Battery (CLTC)</span>
                    {rangeA && rangeB && (
                      <span className="tnum rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
                        {rangeA > rangeB ? `+${rangeA - rangeB} km more range` : `+${rangeB - rangeA} km more range`}
                      </span>
                    )}
                  </div>
                  <div className="mt-1 grid grid-cols-2 gap-4 text-[13px] font-bold">
                    <div className="tnum text-neutral-900">{rangeA} km CLTC</div>
                    <div className="tnum text-right text-neutral-900">{rangeB} km CLTC</div>
                  </div>
                  <div className="mt-1 flex items-center justify-between text-[10.5px] text-neutral-500">
                    <span>{bA.capacityKwh} kWh ({bA.chemistry})</span>
                    <span>{bB.capacityKwh} kWh ({bB.chemistry})</span>
                  </div>
                </div>

                {/* 3. Charging Speed */}
                <div className="rounded-xl bg-black/[0.03] p-2.5">
                  <div className="flex items-center justify-between text-[11px] text-neutral-500">
                    <span className="font-semibold text-neutral-800">3. Charging Speed & Architecture</span>
                    {bA.swappable || bB.swappable ? (
                      <span className="rounded-full bg-sky-500/10 px-2 py-0.5 text-[10px] font-bold text-sky-800">
                        3-min Battery Swap
                      </span>
                    ) : minA && minB ? (
                      <span className="tnum rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
                        {minA < minB ? `${minB - minA} min quicker` : `${minA - minB} min quicker`}
                      </span>
                    ) : null}
                  </div>
                  <div className="mt-1 grid grid-cols-2 gap-4 text-[13px] font-bold">
                    <div className="tnum text-neutral-900">{minA ? `${minA} min (10–80%)` : '–'}</div>
                    <div className="tnum text-right text-neutral-900">{minB ? `${minB} min (10–80%)` : '–'}</div>
                  </div>
                  <div className="mt-1 flex items-center justify-between text-[10.5px] text-neutral-500">
                    <span>{bA.architectureV ? `${bA.architectureV}V architecture` : 'Standard'}</span>
                    <span>{bB.architectureV ? `${bB.architectureV}V architecture` : 'Standard'}</span>
                  </div>
                </div>

                {/* 4. Cockpit Software */}
                <div className="rounded-xl bg-black/[0.03] p-2.5">
                  <div className="flex items-center justify-between text-[11px] text-neutral-500">
                    <span className="font-semibold text-neutral-800">4. Cockpit Software & Displays</span>
                    <span className="rounded-full bg-black/[0.05] px-2 py-0.5 text-[10px] font-medium text-neutral-600">
                      {vehicleA.cockpit.screens.length} vs {vehicleB.cockpit.screens.length} Screens
                    </span>
                  </div>
                  <div className="mt-1 grid grid-cols-2 gap-4 text-[13px] font-bold">
                    <div className="text-neutral-900">{vehicleA.cockpit.os}</div>
                    <div className="text-right text-neutral-900">{vehicleB.cockpit.os}</div>
                  </div>
                  <div className="mt-1 flex items-center justify-between text-[10.5px] text-neutral-500">
                    <span>{vehicleA.cockpit.screens[0]?.diagonalIn}&quot; center display</span>
                    <span>{vehicleB.cockpit.screens[0]?.diagonalIn}&quot; center display</span>
                  </div>
                </div>

                {/* 5. Dimensions & Space */}
                <div className="rounded-xl bg-black/[0.03] p-2.5">
                  <div className="flex items-center justify-between text-[11px] text-neutral-500">
                    <span className="font-semibold text-neutral-800">5. Dimensions & Wheelbase</span>
                  </div>
                  <div className="mt-1 grid grid-cols-2 gap-4 text-[12px] font-semibold">
                    <div className="tnum text-neutral-900">{dA.lengthMm} × {dA.widthMm} × {dA.heightMm} mm</div>
                    <div className="tnum text-right text-neutral-900">{dB.lengthMm} × {dB.widthMm} × {dB.heightMm} mm</div>
                  </div>
                  <div className="mt-1 flex items-center justify-between text-[10.5px] text-neutral-500">
                    <span>Wheelbase: {mm(dA.wheelbaseMm)}</span>
                    <span>Wheelbase: {mm(dB.wheelbaseMm)}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Color Tab Swatches */}
        {bottomTab === 'color' && (
          <div className="pointer-events-auto flex w-full max-w-2xl justify-between gap-6 px-4 py-2">
            {/* Left Car Swatches */}
            <div className={`flex flex-col items-center rounded-2xl p-2.5 shadow-lg ${GLASS}`}>
              <div className="mb-1.5 text-[10.5px] font-semibold text-neutral-600">
                {vehicleA.brand} Paint
              </div>
              <div className="flex gap-2">
                {vehicleA.configurator?.paints.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setPaintA(p.id)}
                    title={p.name}
                    className={`h-7 w-7 rounded-full shadow-xs transition-transform hover:scale-110 ${FOCUS} ${
                      paintA === p.id ? 'ring-2 ring-neutral-900 ring-offset-2 scale-105' : 'ring-1 ring-black/10'
                    }`}
                    style={{ background: p.swatch }}
                  />
                ))}
              </div>
            </div>

            {/* Right Car Swatches */}
            <div className={`flex flex-col items-center rounded-2xl p-2.5 shadow-lg ${GLASS}`}>
              <div className="mb-1.5 text-[10.5px] font-semibold text-neutral-600">
                {vehicleB.brand} Paint
              </div>
              <div className="flex gap-2">
                {vehicleB.configurator?.paints.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setPaintB(p.id)}
                    title={p.name}
                    className={`h-7 w-7 rounded-full shadow-xs transition-transform hover:scale-110 ${FOCUS} ${
                      paintB === p.id ? 'ring-2 ring-neutral-900 ring-offset-2 scale-105' : 'ring-1 ring-black/10'
                    }`}
                    style={{ background: p.swatch }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Dimensions Tab Overlay */}
        {bottomTab === 'dimensions' && (
          <div className={`pointer-events-auto w-full max-w-xl rounded-2xl p-3 shadow-lg ${GLASS}`}>
            <div className="grid grid-cols-4 gap-2 text-center">
              <div>
                <div className="text-[10px] text-neutral-500">Length</div>
                <div className="mt-0.5 text-[11.5px] font-bold text-neutral-900">{dA.lengthMm} vs {dB.lengthMm} mm</div>
              </div>
              <div>
                <div className="text-[10px] text-neutral-500">Width</div>
                <div className="mt-0.5 text-[11.5px] font-bold text-neutral-900">{dA.widthMm} vs {dB.widthMm} mm</div>
              </div>
              <div>
                <div className="text-[10px] text-neutral-500">Height</div>
                <div className="mt-0.5 text-[11.5px] font-bold text-neutral-900">{dA.heightMm} vs {dB.heightMm} mm</div>
              </div>
              <div>
                <div className="text-[10px] text-neutral-500">Wheelbase</div>
                <div className="mt-0.5 text-[11.5px] font-bold text-neutral-900">{dA.wheelbaseMm} vs {dB.wheelbaseMm} mm</div>
              </div>
            </div>
          </div>
        )}

        {/* Space Tab Overlay */}
        {bottomTab === 'space' && (
          <div className={`pointer-events-auto w-full max-w-xl rounded-2xl p-3 shadow-lg ${GLASS}`}>
            <div className="grid grid-cols-2 gap-4 text-center">
              <div className="rounded-xl bg-black/[0.03] p-2">
                <div className="text-[11px] font-bold text-neutral-900">{vehicleA.brand} {vehicleA.model}</div>
                <div className="mt-1 text-[11px] text-neutral-600">{vehicleA.bodyStyle} · {mm(dA.wheelbaseMm)} legroom</div>
                <div className="mt-0.5 text-[10.5px] text-neutral-500">{vehicleA.cockpit.screens.length} Cabin Screens</div>
              </div>
              <div className="rounded-xl bg-black/[0.03] p-2">
                <div className="text-[11px] font-bold text-neutral-900">{vehicleB.brand} {vehicleB.model}</div>
                <div className="mt-1 text-[11px] text-neutral-600">{vehicleB.bodyStyle} · {mm(dB.wheelbaseMm)} legroom</div>
                <div className="mt-0.5 text-[10.5px] text-neutral-500">{vehicleB.cockpit.screens.length} Cabin Screens</div>
              </div>
            </div>
          </div>
        )}

        {/* Quick Camera Angle Presets */}
        <div className={`pointer-events-auto flex items-center gap-1 rounded-full p-1 shadow-md ${GLASS}`}>
          {[
            { label: '3/4 视角', az: 0.62, el: 1.38, dist: 7.2 },
            { label: '正前 Front', az: 0, el: 1.48, dist: 7.2 },
            { label: '正侧 Side', az: Math.PI / 2, el: 1.5, dist: 7.2 },
            { label: '正后 Rear', az: Math.PI, el: 1.48, dist: 7.2 },
          ].map((preset) => {
            const active =
              Math.abs(cameraAngle.az - preset.az) < 0.15 &&
              Math.abs(cameraAngle.el - preset.el) < 0.15;
            return (
              <button
                key={preset.label}
                type="button"
                onClick={() => {
                  activeSourceRef.current = null;
                  setCameraAngle({ az: preset.az, el: preset.el, dist: preset.dist });
                }}
                className={`rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors ${FOCUS} ${
                  active ? 'bg-neutral-900 text-white font-semibold' : 'text-neutral-600 hover:text-neutral-900'
                }`}
              >
                {preset.label}
              </button>
            );
          })}
        </div>

        {/* The 4 Bottom Pill Navigation Tabs (HIMA Style: 颜色, 尺寸, 空间, 参数) */}
        <div className={`pointer-events-auto flex items-center rounded-full p-1 shadow-lg ${GLASS}`}>
          {[
            { id: 'specs' as const, label: '参数 · Specs' },
            { id: 'dimensions' as const, label: '尺寸 · Dimensions' },
            { id: 'space' as const, label: '空间 · Space' },
            { id: 'color' as const, label: '颜色 · Color' },
          ].map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => {
                setBottomTab(t.id);
                if (t.id === 'specs') setSpecsMinimized(false);
              }}
              className={`rounded-full px-4 py-1.5 text-[12px] font-medium transition-colors ${FOCUS} ${
                bottomTab === t.id
                  ? 'bg-neutral-900 text-white shadow-sm font-semibold'
                  : 'text-neutral-600 hover:text-neutral-950'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
