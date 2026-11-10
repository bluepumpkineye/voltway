'use client';

import React from 'react';
import * as THREE from 'three';
import { useThree } from '@react-three/fiber';
import type { Vehicle } from '@/data/vehicles/schema';
import { hingesOf } from '@/lib/openings';
import type { PreparedRig } from '@/lib/tech/rig';
import { assemblyLift, cabinMove, CABIN_WINDOW, dimsOf, exteriorPlan, wheelMove } from '@/lib/xray/plan';
import { xrayOf } from '@/lib/xray/rig';

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
    ghost.userData.ghost = true;
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

/**
 * The Drive tab's X-ray camera: the whole exterior, not only the greenhouse, goes to the pale ghost (the wheels, which are what the
 * rig turns, and what already is a ghost stay as they are), so that the schematic motors and battery under the floor read through.
 */
export function useBodyGhost(root: THREE.Object3D, active: boolean) {
  const invalidate = useThree((s) => s.invalidate);
  React.useEffect(() => {
    if (!active) return;
    const ghost = new THREE.MeshPhysicalMaterial({
      color: '#98a4b3',
      roughness: 0.25,
      metalness: 0,
      transparent: true,
      opacity: 0.16,
      depthWrite: false,
      side: THREE.DoubleSide,
      envMapIntensity: 0.6,
    });
    ghost.userData.ghost = true;
    const was: [THREE.Mesh, THREE.Material | THREE.Material[]][] = [];
    root.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (!mesh.isMesh) return;
      // the wheels (and their calipers) stay solid; a pane or a body already in the ghost is left alone
      for (let p: THREE.Object3D | null = o; p; p = p.parent) if (/wheels/i.test(p.name)) return;
      const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      if (mats.every((m) => m.userData.ghost || m.name.toLowerCase().startsWith('m_glass'))) return;
      was.push([mesh, mesh.material]);
      mesh.material = ghost;
    });
    invalidate();
    return () => {
      for (const [mesh, m] of was) mesh.material = m;
      ghost.dispose();
      invalidate();
    };
  }, [root, active, invalidate]);
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

/**
 * The exploded view's moves for the exterior: the shell, the greenhouse, each door, the bonnet and the tail go where
 * src/lib/xray/plan.ts says, the wheels go out to their sides with their corners (the car's rig keeps their height), and
 * the whole unsprung group stands up with the assembly. Registered with the car's X-ray rig, undone on unmount.
 */
export function useXrayShell(root: THREE.Object3D, vehicle: Vehicle) {
  const invalidate = useThree((s) => s.invalidate);
  React.useEffect(() => {
    if (!vehicle.xray) return;
    const rig = xrayOf(vehicle);
    // a car without an exploded view still hands its scene to the blueprint
    rig.roots.exterior = root;
    if (!vehicle.xray.anatomy) {
      return () => {
        rig.roots.exterior = undefined;
      };
    }
    const d = dimsOf(vehicle);
    const plan = exteriorPlan(d, vehicle);
    root.traverse((o) => {
      const m = plan.find((p) => p.name.test(o.name));
      if (m) rig.add('shell', o, new THREE.Vector3(...m.ex), m.t0, m.t1, m.sys);
    });
    const prepared = root.userData.rig as PreparedRig | undefined;
    if (prepared) {
      for (const w of prepared.wheels) {
        const mv = wheelMove(w.corner, d);
        rig.add('wheels', w.steer, mv.ex, mv.t0, mv.t1, 'wheels', false, true);
      }
      rig.add('wheels', prepared.unsprung, new THREE.Vector3(0, assemblyLift(d, vehicle) + 0.04, 0), 0.1, 0.7, 'wheels');
    }
    rig.apply();
    invalidate();
    return () => {
      rig.remove('shell');
      rig.remove('wheels');
      rig.roots.exterior = undefined;
      invalidate();
    };
  }, [root, vehicle, invalidate]);
}

/** The cabin goes up as one piece, and its door cards (and the tail's liner) follow the exterior parts they belong to. */
export function useXrayCabinPlan(root: THREE.Object3D, vehicle: Vehicle) {
  const invalidate = useThree((s) => s.invalidate);
  React.useEffect(() => {
    if (!vehicle.xray) return;
    const rig = xrayOf(vehicle);
    rig.roots.cabin = root;
    if (!vehicle.xray.anatomy) {
      return () => {
        rig.roots.cabin = undefined;
      };
    }
    const d = dimsOf(vehicle);
    const cab = cabinMove(d, vehicle);
    rig.add('cabin', root, cab, CABIN_WINDOW.t0, CABIN_WINDOW.t1, 'cabin');
    const plan = exteriorPlan(d, vehicle);
    for (const s of vehicle.openings ?? []) {
      const card = s.cardNode ? root.getObjectByName(s.cardNode) : undefined;
      const mv = plan.find((p) => p.name.test(s.node));
      if (card && mv) rig.add('cabin', card, new THREE.Vector3(...mv.ex).sub(cab), mv.t0, mv.t1, 'cabin');
    }
    rig.apply();
    invalidate();
    return () => {
      rig.remove('cabin');
      rig.roots.cabin = undefined;
      invalidate();
    };
  }, [root, vehicle, invalidate]);
}
