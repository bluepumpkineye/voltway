'use client';

import React from 'react';
import * as THREE from 'three';
import { useThree } from '@react-three/fiber';
import type { Vehicle } from '@/data/vehicles/schema';
import { hingesOf } from '@/lib/openings';

/**
 * The X-ray tab, as HIMA's showroom does it: the greenhouse (glass, roof,
 * pillars) is one pre-split node, and it takes a single pale ghost material in
 * place of its own; the doors drop out and the dark hull is hidden (CarModel),
 * so the cabin shows through. Every pane of glass elsewhere (the tailgate's)
 * goes to the same ghost in useGlass.
 */
export function useXray(root: THREE.Object3D, vehicle: Vehicle, active: boolean) {
  const invalidate = useThree((s) => s.invalidate);
  const hinges = hingesOf(vehicle);

  React.useEffect(() => {
    if (!hinges) return;
    hinges.setXray(active);
    invalidate();
    return () => hinges.setXray(false);
  }, [hinges, active, invalidate]);

  React.useEffect(() => {
    const spec = vehicle.xray;
    const node = spec ? root.getObjectByName(spec.node) : undefined;
    if (!spec || !node || !active) return;
    const ghost = new THREE.MeshPhysicalMaterial({
      color: spec.color,
      roughness: 0.2,
      metalness: 0,
      transparent: true,
      opacity: spec.opacity,
      depthWrite: false,
      side: THREE.DoubleSide,
      envMapIntensity: 0.7,
    });
    const was: [THREE.Mesh, THREE.Material | THREE.Material[]][] = [];
    node.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (!mesh.isMesh) return;
      was.push([mesh, mesh.material]);
      mesh.material = ghost;
    });
    invalidate();
    return () => {
      for (const [mesh, m] of was) mesh.material = m;
      ghost.dispose();
      invalidate();
    };
  }, [root, vehicle, active, invalidate]);
}

/** Cabin nodes that go while the X-ray tab is on (the headliner closes the view from above). */
export function useXrayCabin(root: THREE.Object3D, vehicle: Vehicle, active: boolean) {
  const invalidate = useThree((s) => s.invalidate);
  React.useEffect(() => {
    const nodes = (vehicle.xray?.hideCabin ?? [])
      .map((n) => root.getObjectByName(n))
      .filter((o): o is THREE.Object3D => !!o);
    if (!active || !nodes.length) return;
    nodes.forEach((o) => (o.visible = false));
    invalidate();
    return () => {
      nodes.forEach((o) => (o.visible = true));
      invalidate();
    };
  }, [root, vehicle, active, invalidate]);
}
