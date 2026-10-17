/**
 * Which groups of sensors the Autonomous Drive demo draws (src/components/viewer/TechSensors.tsx): the visitor switches them from the
 * demo's panel. A small vanilla store, like the clock: the 3D scene reads it every frame, the panel through a hook.
 */
import React from 'react';

export type LayerId = 'lidar' | 'side' | 'rear' | 'ultrasonic' | 'cameras' | 'surround';
export const LAYERS: LayerId[] = ['lidar', 'side', 'rear', 'surround', 'ultrasonic', 'cameras'];

type Layers = Record<LayerId, boolean>;
let snap: Layers = { lidar: true, side: true, rear: true, surround: true, ultrasonic: true, cameras: true };
const subs = new Set<() => void>();

export const getLayers = (): Layers => snap;

export function toggleLayer(id: LayerId) {
  snap = { ...snap, [id]: !snap[id] };
  for (const fn of subs) fn();
}

export const subscribeLayers = (fn: () => void) => {
  subs.add(fn);
  return () => {
    subs.delete(fn);
  };
};

export function useLayers(): Layers {
  return React.useSyncExternalStore(subscribeLayers, getLayers, getLayers);
}
