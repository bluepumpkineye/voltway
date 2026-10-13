'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import type { SwivelSpec, Vehicle } from '@/data/vehicles/schema';
import { MAX_SLIDE_RATE, MAX_TURN_RATE, TURN_SIGN } from '@/lib/tech/swivel';
import { useVehicleStore } from '@/store/vehicle-store';
import { motionOk } from './configurator';

/** The node the rig makes: the screen and its frame, its origin on the hub the screen turns about. */
export const SWIVEL_NODE = 'ScreenSwivel';

const DEG = Math.PI / 180;

/**
 * Hang the centre screen on a pivot, so it can turn and slide.
 *
 * The cabin export is one mesh per material with the screen's frame inside the black piano-lacquer one (only
 * `screen_main`, the picture, is a node of its own), so the frame's triangles are cut out here: those that lie
 * wholly in a box just round the picture, which holds the frame and nothing else (the arm behind it is longer than
 * the box, so it stays on the dash). The new mesh shares the cabin's vertex buffers, with the baked light, and its
 * own index. The frame and the picture then become children of a group at the hub, which `ScreenDriver` turns.
 * Idempotent: a clone of an already rigged cabin returns its pivot.
 */
export function rigSwivel(root: THREE.Object3D, spec: SwivelSpec): THREE.Group | null {
  const done = root.getObjectByName(SWIVEL_NODE);
  if (done) return done as THREE.Group;
  const screen = root.getObjectByName('screen_main') as THREE.Mesh | undefined;
  const cabin = root.getObjectByName(spec.cabinNode);
  if (!screen || !cabin) return null;

  screen.updateWorldMatrix(true, false);
  const box = new THREE.Box3().setFromObject(screen).expandByVector(new THREE.Vector3(0.035, 0.03, 0.03));

  const pivot = new THREE.Group();
  pivot.name = SWIVEL_NODE;
  pivot.position.set(spec.hub[0], 0, spec.hub[1]);

  const p = new THREE.Vector3();
  const frames: THREE.Mesh[] = [];
  const meshes = (cabin as THREE.Mesh).isMesh ? [cabin as THREE.Mesh] : (cabin.children.filter((c) => (c as THREE.Mesh).isMesh) as THREE.Mesh[]);
  for (const m of meshes) {
    const g = m.geometry;
    const pos = g.getAttribute('position');
    const idx = g.index;
    if (!pos || !idx) continue;
    m.updateWorldMatrix(true, false);
    const inside: number[] = [];
    const rest: number[] = [];
    for (let t = 0; t < idx.count; t += 3) {
      let all = true;
      for (let k = 0; k < 3 && all; k++) {
        p.fromBufferAttribute(pos, idx.getX(t + k)).applyMatrix4(m.matrixWorld);
        all = box.containsPoint(p);
      }
      const dst = all ? inside : rest;
      dst.push(idx.getX(t), idx.getX(t + 1), idx.getX(t + 2));
    }
    if (!inside.length) continue;
    const cut = (list: number[]) => {
      const n = new THREE.BufferGeometry();
      for (const name of Object.keys(g.attributes)) n.setAttribute(name, g.getAttribute(name));
      n.setIndex(new THREE.BufferAttribute(list.length > 65535 * 3 ? new Uint32Array(list) : new Uint16Array(list), 1));
      return n;
    };
    const frame = new THREE.Mesh(cut(inside), m.material);
    frame.name = 'int_screen_body';
    frame.position.set(-spec.hub[0], 0, -spec.hub[1]);
    frame.castShadow = frame.receiveShadow = false;
    frames.push(frame);
    m.geometry = cut(rest);
  }
  if (!frames.length) return null;

  const parent = screen.parent ?? root;
  parent.add(pivot);
  pivot.add(...frames);
  // the picture keeps its place in the world while it changes parent
  screen.position.set(-spec.hub[0], 0, -spec.hub[1]);
  pivot.add(screen);
  return pivot;
}

/**
 * Turns and slides the rigged screen to the pose the store asks for (the car's direction dialog, or the Tech tab's
 * demo). The speed is ours: the maker publishes the 55 mm and the 30 degrees, not how fast they are crossed. It
 * renders on demand: it asks for a frame only while the screen is on its way.
 */
export function ScreenDriver({ vehicle }: { vehicle: Vehicle }) {
  const spec = vehicle.swivel;
  const scene = useThree((s) => s.scene);
  const invalidate = useThree((s) => s.invalidate);
  const pivot = React.useRef<THREE.Object3D | null>(null);
  const turn = React.useRef(0);
  const slide = React.useRef(0);

  React.useEffect(() => useVehicleStore.subscribe((s, prev) => {
    if (s.screenTurn !== prev.screenTurn || s.screenSlide !== prev.screenSlide) invalidate();
  }), [invalidate]);

  useFrame((_, dt) => {
    if (!spec) return;
    if (!pivot.current || !pivot.current.parent) pivot.current = scene.getObjectByName(SWIVEL_NODE) ?? null;
    const node = pivot.current;
    if (!node) return;
    const s = useVehicleStore.getState();
    const goalTurn = TURN_SIGN[s.screenTurn] * spec.turnDeg * DEG;
    const goalSlide = s.screenSlide === 'front' ? spec.travelM : 0;
    const step = Math.min(dt, 0.1);
    let busy = false;
    const reach = (cur: number, goal: number, rate: number) => {
      const d = goal - cur;
      if (Math.abs(d) < 1e-5) return goal;
      busy = true;
      if (!motionOk()) return goal;
      // eases out: a share of the way left each frame, never faster than the rate
      const want = d * (1 - Math.exp(-step * 3.2));
      const cap = rate * step;
      return cur + Math.sign(d) * Math.min(Math.abs(d), Math.max(Math.abs(want), cap * 0.25), cap);
    };
    turn.current = reach(turn.current, goalTurn, MAX_TURN_RATE * DEG);
    slide.current = reach(slide.current, goalSlide, MAX_SLIDE_RATE);
    node.rotation.y = turn.current;
    node.position.x = spec.hub[0] + slide.current;
    if (busy) invalidate();
  });

  return null;
}
