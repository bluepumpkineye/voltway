'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree, type ThreeEvent } from '@react-three/fiber';
import type { OpeningId, Vehicle } from '@/data/vehicles/schema';
import { hingesOf } from '@/lib/openings';
import { PART_OF, playCue } from '@/lib/sound/engine';
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
  const camera = useThree((s) => s.camera);
  const hinges = hingesOf(vehicle);

  React.useEffect(() => {
    if (!hinges) return;
    const follow = (open: Record<string, boolean>, snap: boolean, quiet = false) => {
      for (const s of hinges.specs) hinges.aim(s.id, !!open[s.id], performance.now(), snap, quiet);
      invalidate();
    };
    // the car is put in the state it was left in without a sound
    follow(useVehicleStore.getState().openings, true, true);
    return useVehicleStore.subscribe((s, prev) => {
      if (s.openings !== prev.openings) follow(s.openings, reducedMotion());
    });
  }, [hinges, invalidate]);

  // the noise each part makes: where it is in the picture pans it, how far it is from the camera quietens it, and from
  // the seat it is heard through the cabin (src/lib/sound)
  React.useEffect(() => {
    if (!hinges) return;
    const p = new THREE.Vector3();
    return hinges.listen((id, cue) => {
      const part = PART_OF[id];
      const node = hinges.partOf(id);
      let pan = 0;
      let near = 0.8;
      if (node) {
        node.getWorldPosition(p);
        near = 1 / (1 + 0.1 * p.distanceTo(camera.position));
        // in the camera's own axes (it looks down -z): how far to the right of the middle of the picture the part is
        p.applyMatrix4(camera.matrixWorldInverse);
        pan = p.z > -0.1 ? Math.sign(p.x || 1) : THREE.MathUtils.clamp((p.x / -p.z) * 1.2, -1, 1);
      }
      playCue(part, cue, { pan, near, inside: useVehicleStore.getState().cameraMode === 'interior' });
    });
  }, [hinges, camera]);

  useFrame(() => {
    if (hinges?.step(performance.now())) invalidate();
    // the cabin shows only through the clear glass while everything is shut (clearGlass.ts)
    useVehicleStore.getState().setShut(!hinges || hinges.lift.cabin.value < 0.002);
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
    // a rigged car (src/lib/tech/rig.ts) carries its body on a "Sprung" group, and the
    // struts ride with it, so the body can heave and pitch without leaving them behind
    const parent = root.getObjectByName('Sprung') ?? root;
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
        parent.add(barrel, rod);
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
            // a shut part has nothing to show: the mounts are meant to sit inside the body, and a strut that stands a
            // centimetre outside a reshaped skin read as a black post at the car's shoulder (the G9L's tail)
            barrel.visible = rod.visible = p > 0.004;
          }),
        );
      }
    }
    return () => {
      undo.forEach((u) => u());
      for (const o of made) {
        parent.remove(o);
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

/** The glass of a car with no X-ray of its own: the same pale ghost the X-ray tab draws. */
const GHOST_GLASS = { color: '#98a4b3', opacity: 0.34 };

/**
 * The pane's colour as the viewer shows it. The build's glass is tinted green,
 * as real glazing is, and with only the studio's whites around it that read as
 * olive (sRGB 15, 26, 10). The same darkness, kept cool and neutral, reads as glass.
 */
function coolGlass(hex: string): THREE.Color {
  const c = new THREE.Color(hex);
  const l = c.r * 0.2126 + c.g * 0.7152 + c.b * 0.0722;
  return c.setRGB(l * 0.92, l * 0.98, l * 1.12);
}

interface Pane {
  m: THREE.MeshStandardMaterial;
  privacy: boolean;
  /** the ceramic black band on the backlight: opaque, except in the X-ray */
  frit?: boolean;
  door?: OpeningId;
  /** the pane's own colour, which the X-ray tab swaps for the ghost's */
  color: THREE.Color;
  /** the pane's own specular intensity (a physical material's), which `Vehicle.glass.reflect` scales */
  spec?: number;
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
  /** the cabin is there to be seen: the clear glass (M_Glass) turns to the X-ray's ghost from outside */
  clearOutside = false,
) {
  const hinges = hingesOf(vehicle);
  const invalidate = useThree((s) => s.invalidate);
  const live = React.useRef({ inside, xray, clearOutside, repaint: () => {} });

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
        const specular = (own as THREE.MeshPhysicalMaterial).specularIntensity;
        if (specular !== undefined) own.userData.paneSpec ??= specular;
        const c = door ? (own.clone() as THREE.MeshStandardMaterial) : own;
        if (door) changed = true;
        panes.push({
          m: c,
          privacy: name.includes('privacy'),
          frit,
          door,
          color: coolGlass(own.userData.paneHex as string),
          spec: own.userData.paneSpec as number | undefined,
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
      // Seen from outside with the cabin behind them, the windscreen and the front windows are the X-ray's ghost, and the
      // privacy glass (the rear windows, the backlight, a glass roof) is tinted: the same dark pane an open door shows. The
      // frit, the black ceramic band round the backlight, stays black.
      const seeThrough = lv.clearOutside && !lv.inside && !lv.xray && !pane.frit;
      const g = vehicle.glass ?? vehicle.xray ?? GHOST_GLASS;
      pane.m.color.set(ghost ? ghost.color : seeThrough && !pane.privacy ? g.color : pane.color);
      const swing01 = Math.min(1, p * 1.6);
      const shut = pane.privacy ? (vehicle.glass?.privacy ?? kind.open) : g.opacity;
      const op = ghost
        ? ghost.opacity
        : pane.frit
          ? 1
          : lv.inside
            ? kind.inside
            : seeThrough
              ? shut - (shut - kind.open) * swing01
              : 1 - (1 - kind.open) * swing01;
      const transparent = op < 0.999;
      if (pane.m.transparent !== transparent) {
        pane.m.transparent = transparent;
        pane.m.needsUpdate = true;
      }
      pane.m.opacity = op;
      pane.m.depthWrite = !transparent;
      pane.m.envMapIntensity = lv.inside && !pane.frit ? 0 : 1;
      // scene.environment lights the glass, and three ignores a material's envMapIntensity then: the mirrored studio is
      // scaled through the pane's specular intensity instead (F0 and F90 both follow it)
      const phys = pane.m as THREE.MeshPhysicalMaterial;
      const reflect = pane.privacy ? (vehicle.glass?.privacyReflect ?? vehicle.glass?.reflect ?? 1) : (vehicle.glass?.reflect ?? 1);
      if (pane.spec !== undefined) phys.specularIntensity = pane.spec * (pane.frit || lv.inside ? 1 : reflect);
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
  }, [root, hinges, enabled, invalidate, vehicle.xray, vehicle.glass]);

  React.useEffect(() => {
    live.current.inside = inside;
    live.current.xray = xray;
    live.current.clearOutside = clearOutside;
    live.current.repaint();
    invalidate();
  }, [inside, xray, clearOutside, invalidate]);
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
  // the cabin comes in once the car is on screen: the windscreen and front windows show it from outside. Not on the Tech
  // tab, whose demos move the car and leave the cabin where it is (a demo of the cabin itself asks for it: cameraMode)
  const need = useVehicleStore(
    (s) =>
      s.cameraMode !== 'exterior' ||
      s.tab === 'xray' ||
      (s.exteriorUp && s.tab !== 'tech') ||
      Object.values(s.openings).some(Boolean),
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
