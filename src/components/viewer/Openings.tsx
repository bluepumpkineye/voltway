'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree, type ThreeEvent } from '@react-three/fiber';
import type { OpeningId, Vehicle } from '@/data/vehicles/schema';
import { hingesOf } from '@/lib/openings';
import { useVehicleStore } from '@/store/vehicle-store';

const reducedMotion = () =>
  typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

/**
 * Follows the store's `openings` (the HMI's door buttons, a tap on a door) and
 * swings the car's hinged nodes. Mount once inside the Canvas; it asks for
 * frames only while something is moving, so a demand canvas stays idle.
 */
export function OpeningsDriver({ vehicle }: { vehicle: Vehicle }) {
  const invalidate = useThree((s) => s.invalidate);
  const hinges = hingesOf(vehicle);

  React.useEffect(() => {
    if (!hinges) return;
    const follow = (open: Record<string, boolean>, snap: boolean) => {
      for (const s of hinges.specs) hinges.aim(s.id, !!open[s.id], performance.now(), snap);
      invalidate();
    };
    follow(useVehicleStore.getState().openings, true);
    return useVehicleStore.subscribe((s, prev) => {
      if (s.openings !== prev.openings) follow(s.openings, reducedMotion());
    });
  }, [hinges, invalidate]);

  useFrame(() => {
    if (hinges?.step(performance.now())) invalidate();
  });
  return null;
}

/** Put the car's hinged nodes (the exterior's, or the cabin's door cards) under the hinges. */
export function useHingedNodes(
  root: THREE.Object3D,
  vehicle: Vehicle,
  key: 'node' | 'cardNode' | 'frameNode',
) {
  const hinges = hingesOf(vehicle);
  React.useEffect(() => {
    if (!hinges) return;
    const taken: [OpeningId, THREE.Object3D][] = [];
    for (const s of hinges.specs) {
      const name = s[key];
      const o = name ? root.getObjectByName(name) : undefined;
      if (o) {
        hinges.attach(s.id, o, key === 'frameNode');
        taken.push([s.id, o]);
      }
    }
    return () => {
      for (const [id, o] of taken) hinges.detach(id, o);
    };
  }, [root, hinges, key]);
}

/**
 * The gas struts that hold a part open (the bonnet's): a barrel fixed to the
 * body and a rod on the part, each pointing at the other's mount, so they
 * follow the swing. Built here, not modelled: a strut is two cylinders.
 */
export function useStruts(root: THREE.Object3D, vehicle: Vehicle) {
  const hinges = hingesOf(vehicle);
  React.useEffect(() => {
    if (!hinges) return;
    const undo: (() => void)[] = [];
    const UP = new THREE.Vector3(0, 1, 0);
    const barrelMat = new THREE.MeshStandardMaterial({ color: '#1a1b1e', metalness: 0.55, roughness: 0.38 });
    const rodMat = new THREE.MeshStandardMaterial({ color: '#9a9ea5', metalness: 1, roughness: 0.28 });
    const made: THREE.Object3D[] = [];
    for (const s of hinges.specs) {
      const node = s.struts?.length ? root.getObjectByName(s.node) : undefined;
      if (!node || !s.struts) continue;
      const axis = s.axis ?? 'y';
      const hinge = node.position.clone();
      const rad = (s.deg * Math.PI) / 180;
      for (const st of s.struts) {
        const b = new THREE.Vector3(...st.body);
        const m0 = new THREE.Vector3(...st.moving);
        // the strut is as long as the gap it holds open: barrel and rod overlap a little
        const e1 = new THREE.Euler();
        e1[axis] = rad;
        const reach = m0.clone().sub(hinge).applyQuaternion(new THREE.Quaternion().setFromEuler(e1)).add(hinge).distanceTo(b);
        const BARREL = 0.46 * reach;
        const ROD = 0.54 * reach;
        const barrel = new THREE.Mesh(new THREE.CylinderGeometry(0.0135, 0.0135, BARREL, 12), barrelMat);
        const rod = new THREE.Mesh(new THREE.CylinderGeometry(0.0058, 0.0058, ROD, 10), rodMat);
        root.add(barrel, rod);
        made.push(barrel, rod);
        const rot = new THREE.Quaternion();
        const dir = new THREE.Vector3();
        const h = new THREE.Vector3();
        undo.push(
          hinges.follow(s.id, (p) => {
            const e = new THREE.Euler();
            e[axis] = rad * p;
            rot.setFromEuler(e);
            h.copy(m0).sub(hinge).applyQuaternion(rot).add(hinge);
            dir.copy(h).sub(b).normalize();
            barrel.quaternion.setFromUnitVectors(UP, dir);
            barrel.position.copy(b).addScaledVector(dir, BARREL / 2);
            rod.quaternion.copy(barrel.quaternion);
            rod.position.copy(h).addScaledVector(dir, -ROD / 2);
          }),
        );
      }
    }
    return () => {
      undo.forEach((u) => u());
      for (const o of made) {
        root.remove(o);
        (o as THREE.Mesh).geometry.dispose();
      }
      barrelMat.dispose();
      rodMat.dispose();
    };
  }, [root, hinges]);
}

/** Opacity of the car's panes: shut, open (a door's), and seen from the cabin. */
const PANE = {
  clear: { open: 0.14, inside: 0.12 },
  privacy: { open: 0.55, inside: 0.5 },
};

interface Pane {
  m: THREE.MeshStandardMaterial;
  privacy: boolean;
  /** the ceramic black band on the backlight: opaque, except in the X-ray */
  frit?: boolean;
  door?: OpeningId;
  /** the pane's own colour, which the X-ray tab swaps for the ghost's */
  color: THREE.Color;
}

/**
 * Cabin nodes the part's spec lists go while it is open: the shelf under a
 * tailgate's glass (`hides`), and trims whose edges only show from outside
 * (`hidesOutside`, which stay when the camera is in the cabin).
 */
export function useHiddenWhileOpen(root: THREE.Object3D, vehicle: Vehicle, inside: boolean) {
  const hinges = hingesOf(vehicle);
  const invalidate = useThree((s) => s.invalidate);
  const live = React.useRef({ inside, apply: () => {} });

  React.useEffect(() => {
    if (!hinges) return;
    const undo: (() => void)[] = [];
    for (const s of hinges.specs) {
      for (const name of s.hides ?? []) {
        const o = root.getObjectByName(name);
        if (o) undo.push(hinges.hideWhileOpen(s.id, o));
      }
      const outside = (s.hidesOutside ?? [])
        .map((n) => root.getObjectByName(n))
        .filter((o): o is THREE.Object3D => !!o);
      if (!outside.length) continue;
      let p = 0;
      const show = () => outside.forEach((o) => (o.visible = p < 0.002 || live.current.inside));
      live.current.apply = show;
      undo.push(
        hinges.follow(s.id, (v) => {
          p = v;
          show();
        }),
        () => outside.forEach((o) => (o.visible = true)),
      );
    }
    return () => undo.forEach((u) => u());
  }, [root, hinges]);

  React.useEffect(() => {
    live.current.inside = inside;
    live.current.apply();
    invalidate();
  }, [inside, invalidate]);
}

/**
 * The car's glass. It ships as dark opaque (a transmissive glTF material blanks
 * the three.js frame), so each state is a tint: from the cabin a see-through
 * one (the blackout layer is hidden too), and on a door that is opening the
 * pane clears as in the maker's photographs, so the cabin shows through it.
 * Each door gets glass materials of its own, so the windscreen is untouched;
 * one place decides every pane's opacity from "inside" and its door's swing.
 */
export function useGlass(
  root: THREE.Object3D,
  vehicle: Vehicle,
  inside: boolean,
  enabled: boolean,
  xray = false,
) {
  const hinges = hingesOf(vehicle);
  const invalidate = useThree((s) => s.invalidate);
  const live = React.useRef({ inside, xray, repaint: () => {} });

  React.useEffect(() => {
    if (!enabled) return;
    const lv = live.current;
    const doorOf = new Map<string, OpeningId>();
    for (const s of hinges?.specs ?? []) doorOf.set(s.node, s.id);
    const panes: Pane[] = [];
    const swapped: [THREE.Mesh, THREE.Material | THREE.Material[]][] = [];
    const swing = new Map<OpeningId, number>();
    root.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (!mesh.isMesh) return;
      let door: OpeningId | undefined;
      for (let n: THREE.Object3D | null = mesh; n && !door; n = n.parent) door = doorOf.get(n.name);
      const was = mesh.material;
      let changed = false;
      const own = (Array.isArray(was) ? was : [was]).map((m) => {
        const name = m.name.toLowerCase();
        const frit = name === 'm_frit_black';
        if (!name.startsWith('m_glass') && !frit) return m;
        // the pane's own colour is read once and kept: the X-ray overwrites it,
        // and an effect that runs again must not mistake the ghost for the glass
        const own = m as THREE.MeshStandardMaterial;
        own.userData.paneHex ??= '#' + own.color.getHexString();
        const c = door ? (own.clone() as THREE.MeshStandardMaterial) : own;
        if (door) changed = true;
        panes.push({
          m: c,
          privacy: name.includes('privacy'),
          frit,
          door,
          color: new THREE.Color(own.userData.paneHex as string),
        });
        return c;
      });
      if (changed) {
        swapped.push([mesh, was]);
        mesh.material = Array.isArray(was) ? own : own[0];
      }
    });
    const paint = (pane: Pane) => {
      const kind = pane.privacy ? PANE.privacy : PANE.clear;
      const p = pane.door ? (swing.get(pane.door) ?? 0) : 0;
      const ghost = lv.xray ? vehicle.xray : undefined;
      pane.m.color.set(ghost ? ghost.color : pane.color);
      const op = ghost
        ? ghost.opacity
        : pane.frit
          ? 1
          : lv.inside
            ? kind.inside
            : 1 - (1 - kind.open) * Math.min(1, p * 1.6);
      const transparent = op < 0.999;
      if (pane.m.transparent !== transparent) {
        pane.m.transparent = transparent;
        pane.m.needsUpdate = true;
      }
      pane.m.opacity = op;
      pane.m.depthWrite = !transparent;
      pane.m.envMapIntensity = lv.inside && !pane.frit ? 0 : 1;
    };
    lv.repaint = () => panes.forEach(paint);
    const undo: (() => void)[] = [];
    for (const id of new Set(panes.map((x) => x.door).filter(Boolean) as OpeningId[])) {
      undo.push(
        hinges!.follow(id, (p) => {
          swing.set(id, p);
          for (const x of panes) if (x.door === id) paint(x);
        }),
      );
    }
    lv.repaint();
    invalidate();
    return () => {
      undo.forEach((u) => u());
      for (const [mesh, was] of swapped) {
        const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
        mesh.material = was;
        for (const m of mats) if (!(Array.isArray(was) ? was : [was]).includes(m)) m.dispose();
      }
      lv.repaint = () => {};
    };
  }, [root, hinges, enabled, invalidate, vehicle.xray]);

  React.useEffect(() => {
    live.current.inside = inside;
    live.current.xray = xray;
    live.current.repaint();
    invalidate();
  }, [inside, xray, invalidate]);
}

/**
 * Tap a hinged part to open or close it. Only those parts are pickable:
 * raycasting a 400k-triangle car on every pointer move would stall the page.
 */
export function useOpeningPicks(root: THREE.Object3D, vehicle: Vehicle, key: 'node' | 'cardNode') {
  const toggle = useVehicleStore((s) => s.toggleOpening);
  const byName = React.useMemo(() => {
    const m = new Map<string, OpeningId>();
    for (const s of vehicle.openings ?? []) {
      const n = s[key];
      if (n) m.set(n, s.id);
    }
    return m;
  }, [vehicle, key]);

  React.useEffect(() => {
    if (byName.size === 0) return;
    const none = () => {};
    root.traverse((o) => {
      if (!(o as THREE.Mesh).isMesh) return;
      for (let n: THREE.Object3D | null = o; n; n = n.parent) if (byName.has(n.name)) return;
      (o as THREE.Mesh).raycast = none;
    });
  }, [root, byName]);

  return React.useMemo(() => {
    if (byName.size === 0) return {};
    const find = (o: THREE.Object3D | null) => {
      for (let n = o; n; n = n.parent) {
        const id = byName.get(n.name);
        if (id) return id;
      }
      return undefined;
    };
    return {
      onClick: (e: ThreeEvent<MouseEvent>) => {
        const id = find(e.object);
        if (!id) return;
        e.stopPropagation();
        toggle(id);
      },
      onPointerOver: (e: ThreeEvent<PointerEvent>) => {
        if (find(e.object)) document.body.style.cursor = 'pointer';
      },
      onPointerOut: () => {
        document.body.style.cursor = '';
      },
    };
  }, [byName, toggle]);
}

/**
 * Whether the cabin should be in the scene: from inside, or while a door is
 * open (you look into it). It stays a moment after the last door shuts so the
 * closing swing is not cut off.
 */
export function useCabinWanted() {
  const need = useVehicleStore(
    (s) => s.cameraMode !== 'exterior' || s.tab === 'xray' || Object.values(s.openings).some(Boolean),
  );
  const [hold, setHold] = React.useState(false);
  React.useEffect(() => {
    if (need) {
      setHold(true);
      return;
    }
    const t = window.setTimeout(() => setHold(false), 1600);
    return () => window.clearTimeout(t);
  }, [need]);
  return need || hold;
}
