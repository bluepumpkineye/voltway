'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import type { Vehicle } from '@/data/vehicles/schema';
import { flagshipVariant } from '@/data/vehicles/schema';
import { useVehicleStore, type CameraMode } from '@/store/vehicle-store';
import type { FixedShot } from '@/components/viewer/VehicleViewer';

const VehicleViewer = dynamic(
  () => import('@/components/viewer/VehicleViewer').then((m) => m.VehicleViewer),
  { ssr: false },
);

function vec(s: string | null, fallback: [number, number, number]): [number, number, number] {
  const p = (s ?? '').split(',').map(Number);
  return p.length === 3 && p.every(Number.isFinite) ? [p[0], p[1], p[2]] : fallback;
}

/** The viewer alone, full window, through the camera in the query string. */
export function ViewCapture({ vehicle }: { vehicle: Vehicle }) {
  const setCameraMode = useVehicleStore((s) => s.setCameraMode);
  const reset = useVehicleStore((s) => s.reset);
  const [shot, setShot] = React.useState<FixedShot | null>(null);

  React.useEffect(() => {
    reset(flagshipVariant(vehicle).id);
    const q = new URLSearchParams(window.location.search);
    const mode = (q.get('mode') ?? 'interior') as CameraMode;
    setCameraMode(mode);
    setShot({
      pos: vec(q.get('pos'), [-0.30, 1.14, -0.395]),
      target: vec(q.get('target'), [0.6, 0.95, -0.2]),
      fov: Number(q.get('fov') ?? 60),
    });
  }, [vehicle, reset, setCameraMode]);

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 9999, background: '#07080a' }}>
      {/* the dev-mode indicator would land in the capture */}
      <style>{'nextjs-portal{display:none!important}'}</style>
      {shot && (
        <VehicleViewer
          vehicle={vehicle}
          variant={flagshipVariant(vehicle)}
          className="h-full w-full"
          fixedShot={shot}
        />
      )}
    </div>
  );
}
