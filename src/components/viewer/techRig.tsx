'use client';

import React from 'react';
import type * as THREE from 'three';
import type { Vehicle } from '@/data/vehicles/schema';
import { rigOf, type PreparedRig } from '@/lib/tech/rig';
import { useVehicleStore } from '@/store/vehicle-store';

/**
 * Registers a mounted exterior with its car's rig (src/lib/tech/rig.ts).
 * `prepareRig` rebuilt the clone in a memo, which must stay pure; the
 * registration is the side effect, so it is made and undone here. The store
 * hears whether the model has the per-corner wheels the demos drive, so the
 * Tech tab can say so when it does not.
 */
export function useRigBinding(model: THREE.Object3D, vehicle: Vehicle) {
  React.useEffect(() => {
    const { setTechStatus } = useVehicleStore.getState();
    const prepared = model.userData.rig as PreparedRig | undefined;
    if (!prepared) {
      setTechStatus('none');
      return () => setTechStatus('loading');
    }
    const detach = rigOf(vehicle).attach(prepared);
    setTechStatus('ready');
    return () => {
      detach();
      setTechStatus('loading');
    };
  }, [model, vehicle]);
}

/**
 * The group that carries the car's place on the floor: the exterior and its
 * baked shadow stand in it, so a tech demo moves them together. At rest it is
 * the identity, and the showroom looks as it always did.
 */
export function CarRoot({ vehicle, children }: { vehicle: Vehicle; children: React.ReactNode }) {
  const ref = React.useRef<THREE.Group>(null);
  React.useEffect(() => {
    const g = ref.current;
    return g ? rigOf(vehicle).attachRoot(g) : undefined;
  }, [vehicle]);
  return <group ref={ref}>{children}</group>;
}
