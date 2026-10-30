'use client';

import React from 'react';
import { Html } from '@react-three/drei';
import { getVehicle } from '@/data/vehicles';
import type { Vehicle } from '@/data/vehicles/schema';
import { rigOf } from '@/lib/tech/rig';
import { useRuntime } from '@/lib/tech/session';
import { GroundShadow } from './StudioShowroom';
import { useStandIn } from './TechStage';

/**
 * The Drive tab's rival: the stand-in of another car (scripts/make-proxy.mjs, in neutral paint, as the parked cars of the Tech tab)
 * in the next lane, moving by its own published pull (`BuiltDemo.rival`, which the director writes to `RigState.rival` each
 * frame). It starts abreast of the car; the one that is quicker pulls ahead, and the road rolls under both. The stand-in's wheels
 * do not turn and its body does not squat: it is a marker of where the other car is, not a second simulation, and the panel says so.
 */
export function TechRival({ vehicle }: { vehicle: Vehicle }) {
  const slug = useRuntime()?.rival?.slug;
  const rival = slug ? getVehicle(slug) : undefined;
  if (!rival?.assets.proxyUrl) return null;
  return (
    <React.Suspense fallback={null}>
      <Model vehicle={vehicle} rival={rival} url={rival.assets.proxyUrl} />
    </React.Suspense>
  );
}

function Model({ vehicle, rival, url }: { vehicle: Vehicle; rival: Vehicle; url: string }) {
  const place = React.useRef<import('three').Group>(null);
  const { model, centre } = useStandIn(url, '#aeb3bb');
  React.useEffect(() => {
    const g = place.current;
    return g ? rigOf(vehicle).attachRival(g) : undefined;
  }, [vehicle]);
  const shadow = rival.assets.studioShadow;
  return (
    <group ref={place}>
      {/* the group stands at the middle of the body: the model's origin is not it */}
      <group position={[-centre.x, 0, -centre.z]}>
        <primitive object={model} />
        {shadow && <GroundShadow shadow={shadow} />}
      </group>
      <Html center position={[0, 1.85, 0]} zIndexRange={[8, 0]} style={{ pointerEvents: 'none' }}>
        <span className="whitespace-nowrap rounded-full bg-white/85 px-2.5 py-0.5 text-[10px] font-medium text-neutral-700 shadow-sm ring-1 ring-black/[0.06]">
          {rival.brand} {rival.model}
        </span>
      </Html>
    </group>
  );
}
