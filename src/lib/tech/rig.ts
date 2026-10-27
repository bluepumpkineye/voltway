import * as THREE from 'three';
import type { Vehicle } from '@/data/vehicles/schema';
import { CORNERS, layoutFrom, type Corner, type Layout, type Sample } from './kinematics';
import type { BodyBox } from './park';
import type { Chassis } from './ride';
import { splitMergedWheels } from './splitWheels';

/**
 * The car as a machine the tech demos can drive: wheels that steer and roll, a
 * body that heaves, pitches and rolls on them, and the whole car placed on the
 * floor.
 *
 * The export (blender/scripts/export_rx.py, split_wheels) ships every wheel design
 * as one node per corner, `<design>_Wheels_<FL|FR|RL|RR>`, and each corner's
 * brake caliper as `<design>_Wheels_Caliper_<tag>`. Each node's origin is the hub
 * centre. `prepareRig` rebuilds a fresh clone of the exterior into
 *
 *   root
 *   |- Sprung          every other node: the body, the doors, the glass ...
 *   `- Unsprung
 *      `- <design>_Wheels            the node the Wheels tab shows and hides
 *         `- <design>_steer_<tag>    yaws about the hub
 *            |- the wheel node        spins about its axle
 *            `- the caliper node      steers with the wheel, does not spin
 *
 * so the Wheels tab, which addresses `<design>_Wheels` by name, keeps working.
 * A car whose export merged the four wheels into one node (the SU7's) is cut into
 * the same corners in the browser (splitWheels.ts); a car with neither is not rigged.
 *
 * Frames: the viewer's (x forward, y up, z toward the passenger side). The
 * kinematics' frame (x forward, y left) differs by y = -z. Yaw is rotation about
 * +y, so a positive angle turns the car, or a wheel, to the left.
 */

const NODE = /^(.*_wheels)_(caliper_)?(fl|fr|rl|rr)$/i;

export interface RigWheel {
  corner: Corner;
  /** yaws about the hub's vertical axis */
  steer: THREE.Group;
  /** spins about the axle; q0 is its rest rotation (it sits in the build's wheel frame) */
  wheel: THREE.Object3D;
  q0: THREE.Quaternion;
  caliper?: THREE.Object3D;
  /** where the hub stands on a level road: the wheel's travel (`RigState.lift`) is added to its height */
  hub0: THREE.Vector3;
}

export interface PreparedRig {
  sprung: THREE.Group;
  unsprung: THREE.Group;
  wheels: RigWheel[];
  layout: Layout;
  /** the middle of the rear axle in the model's frame, kinematics axes (x forward, y left) */
  rac: { x: number; y: number };
  /** the body's extent from the rear axle's middle: behind, ahead, half its width (mirrors included) */
  body: BodyBox;
  /** where the body pitches and rolls from, model frame */
  pivot: THREE.Vector3;
}

/** The index of a corner in the kinematics' arrays. */
const INDEX: Record<Corner, number> = { FL: 0, FR: 1, RL: 2, RR: 3 };

/**
 * Rebuild a fresh clone of the exterior into the rig (see the file comment).
 * Leaves the scene alone, and returns null, when the wheels are not per-corner
 * nodes. Pure on its input apart from that: safe in a memo.
 */
export function prepareRig(root: THREE.Object3D): PreparedRig | null {
  type Slot = { wheel?: THREE.Object3D; caliper?: THREE.Object3D };
  const scan = () => {
    const found = new Map<string, Map<Corner, Slot>>();
    root.traverse((o) => {
      const m = NODE.exec(o.name);
      if (!m) return;
      const corner = m[3].toUpperCase() as Corner;
      const design = m[1];
      const byCorner = found.get(design) ?? new Map();
      const slot = byCorner.get(corner) ?? {};
      if (m[2]) slot.caliper = o;
      else slot.wheel = o;
      byCorner.set(corner, slot);
      found.set(design, byCorner);
    });
    return [...found].filter(([, c]) => CORNERS.every((k) => c.get(k)?.wheel));
  };

  let complete = scan();
  // an export that merged the four wheels into one node (the SU7's) is cut here (splitWheels.ts)
  if (!complete.length && splitMergedWheels(root)) complete = scan();
  if (!complete.length) return null;

  // the first design measures the car: every design stands on the same four hubs
  const first = complete[0][1];
  const centres = {} as Record<Corner, { x: number; y: number }>;
  const radius = {} as Record<Corner, number>;
  for (const k of CORNERS) {
    const p = first.get(k)!.wheel!.position;
    centres[k] = { x: p.x, y: -p.z };
    radius[k] = p.y;
  }
  const layout = layoutFrom(centres, radius);
  if (layout.wheelbase < 1.5 || layout.wheelbase > 5) return null;

  const unsprung = new THREE.Group();
  unsprung.name = 'Unsprung';
  const wheels: RigWheel[] = [];
  for (const [design, corners] of complete) {
    const group = new THREE.Group();
    group.name = design;
    for (const k of CORNERS) {
      const { wheel, caliper } = corners.get(k)!;
      const steer = new THREE.Group();
      steer.name = `${design}_steer_${k}`;
      steer.position.copy(wheel!.position);
      steer.add(wheel!);
      wheel!.position.set(0, 0, 0);
      if (caliper) {
        steer.add(caliper);
        caliper.position.sub(steer.position);
      }
      group.add(steer);
      wheels.push({ corner: k, steer, wheel: wheel!, q0: wheel!.quaternion.clone(), caliper, hub0: steer.position.clone() });
    }
    unsprung.add(group);
  }

  // everything that is left rides on the springs
  const sprung = new THREE.Group();
  sprung.name = 'Sprung';
  for (const child of [...root.children]) sprung.add(child);
  root.add(sprung, unsprung);

  const front = (centres.FL.x + centres.FR.x) / 2;
  const rearX = (centres.RL.x + centres.RR.x) / 2;
  // the body's box: what a parking manoeuvre has to keep clear of its neighbours
  const box = new THREE.Box3().setFromObject(sprung);
  const prepared: PreparedRig = {
    sprung,
    unsprung,
    wheels,
    layout,
    rac: { x: rearX, y: (centres.RL.y + centres.RR.y) / 2 },
    body: { rear: rearX - box.min.x, front: box.max.x - rearX, halfWidth: (box.max.z - box.min.z) / 2 },
    pivot: new THREE.Vector3((front + rearX) / 2, 0.45, 0),
  };
  root.userData.rig = prepared;
  return prepared;
}

export interface RigState {
  /** the model's origin on the floor, m (viewer axes), and its heading, rad */
  x: number;
  z: number;
  yaw: number;
  /** the body on its springs: lift (m), pitch (rad, nose up positive), roll (rad, leaning right positive) */
  heave: number;
  pitch: number;
  roll: number;
  /** the ride height: the whole body's lift over its Standard height, m (the air suspension) */
  ride: number;
  /** each hub's lift over the level road, m: the wheel following a bump under the body */
  lift: [number, number, number, number];
  /** a demo that keeps the car still and rolls the road under it: how far the road has gone, m */
  scroll: number;
  steer: [number, number, number, number];
  spin: [number, number, number, number];
}

const AXLE = new THREE.Vector3(0, 0, 1);
const FORWARD = new THREE.Vector3(1, 0, 0);
const _qSpin = new THREE.Quaternion();
const _qBody = new THREE.Quaternion();
const _qPitch = new THREE.Quaternion();
const _qRoll = new THREE.Quaternion();
const _off = new THREE.Vector3();

/** One car's rig, shared by everything that draws it (the exterior, the shadow). */
export class CarRig {
  readonly state: RigState = {
    x: 0, z: 0, yaw: 0, heave: 0, pitch: 0, roll: 0, ride: 0, lift: [0, 0, 0, 0], scroll: 0,
    steer: [0, 0, 0, 0], spin: [0, 0, 0, 0],
  };
  private prepared: PreparedRig | null = null;
  /** groups that carry the car's place on the floor (the exterior's wrapper, the baked shadow) */
  private roots = new Set<THREE.Object3D>();
  /** roads that roll under the car (`RigState.scroll`), each with where it stands when it has not rolled, and the period of its pattern when it repeats */
  private roads = new Map<THREE.Object3D, { baseX: number; period?: number }>();

  /** The measured wheels, once an exterior with a rig is mounted. */
  get layout(): Layout | null {
    return this.prepared?.layout ?? null;
  }

  /** The rear axle's middle in the model frame: where a plan's start pose is. */
  get rac(): { x: number; y: number } {
    return this.prepared?.rac ?? { x: 0, y: 0 };
  }

  /** The body's extent from the rear axle's middle (mirrors included in the width). */
  get body(): BodyBox {
    return this.prepared?.body ?? { rear: 1, front: 4, halfWidth: 1 };
  }

  get ready(): boolean {
    return this.prepared !== null;
  }

  private subs = new Set<() => void>();

  /** For React: tells when a rigged exterior is mounted or goes (see `ready`). */
  subscribe = (fn: () => void) => {
    this.subs.add(fn);
    return () => {
      this.subs.delete(fn);
    };
  };

  private changed() {
    for (const fn of this.subs) fn();
  }

  attach(p: PreparedRig): () => void {
    this.prepared = p;
    this.apply();
    this.changed();
    return () => {
      if (this.prepared === p) {
        this.prepared = null;
        this.changed();
      }
    };
  }

  attachRoot(g: THREE.Object3D): () => void {
    this.roots.add(g);
    this.apply();
    return () => {
      this.roots.delete(g);
    };
  }

  /**
   * A road that rolls under the car as the demo says (`RigState.scroll`); `baseX` is where it lies at rest. A strip of
   * repeating marks (lane dashes) gives its `period`: it then rolls only that far and starts again, so it can be short.
   */
  attachRoad(g: THREE.Object3D, baseX: number, period?: number): () => void {
    this.roads.set(g, { baseX, period });
    this.apply();
    return () => {
      this.roads.delete(g);
    };
  }

  /** The body's motion on its springs and the wheels following the road (src/lib/tech/ride.ts). */
  setChassis(c: Chassis | null) {
    const st = this.state;
    st.heave = c?.heave ?? 0;
    st.pitch = c?.pitch ?? 0;
    st.roll = c?.roll ?? 0;
    for (let i = 0; i < 4; i++) st.lift[i] = c?.lift[i] ?? 0;
  }

  /** Put the car where a sample of a plan says. */
  setSample(s: Sample) {
    const { rac } = this;
    const c = Math.cos(s.yaw);
    const n = Math.sin(s.yaw);
    // the model's origin sits at (-rac) in the rear axle's frame
    const ox = s.x + c * -rac.x - n * -rac.y;
    const oy = s.y + n * -rac.x + c * -rac.y;
    const st = this.state;
    st.x = ox;
    st.z = -oy;
    st.yaw = s.yaw;
    for (let i = 0; i < 4; i++) {
      st.steer[i] = s.steer[i];
      st.spin[i] = s.spin[i];
    }
  }

  /** Back to the car standing still, as the showroom shows it. */
  reset() {
    const st = this.state;
    st.x = st.z = st.yaw = st.heave = st.pitch = st.roll = st.ride = st.scroll = 0;
    st.lift.fill(0);
    st.steer.fill(0);
    st.spin.fill(0);
    this.apply();
  }

  /** Write the state to the scene. */
  apply() {
    const st = this.state;
    for (const g of this.roots) {
      g.position.set(st.x, 0, st.z);
      g.rotation.set(0, st.yaw, 0);
    }
    for (const [g, { baseX, period }] of this.roads) g.position.x = baseX - (period ? st.scroll % period : st.scroll);
    const p = this.prepared;
    if (!p) return;

    // the body: pitch about the lateral axis, roll about the long one, both about the pivot
    _qPitch.setFromAxisAngle(AXLE, st.pitch);
    _qRoll.setFromAxisAngle(FORWARD, st.roll);
    _qBody.copy(_qRoll).multiply(_qPitch);
    _off.copy(p.pivot).applyQuaternion(_qBody);
    p.sprung.quaternion.copy(_qBody);
    p.sprung.position.copy(p.pivot).sub(_off);
    p.sprung.position.y += st.heave + st.ride;

    for (const w of p.wheels) {
      const i = INDEX[w.corner];
      w.steer.rotation.set(0, st.steer[i], 0);
      w.steer.position.y = w.hub0.y + st.lift[i];
      // rolling forward turns the top of the tyre forward: that is negative about +z
      w.wheel.quaternion.copy(_qSpin.setFromAxisAngle(AXLE, -st.spin[i])).multiply(w.q0);
    }
  }
}

const rigs = new Map<string, CarRig>();

/** The car's rig (one per car, like its hinges). */
export function rigOf(vehicle: Vehicle): CarRig {
  let r = rigs.get(vehicle.slug);
  if (!r) {
    r = new CarRig();
    rigs.set(vehicle.slug, r);
  }
  return r;
}
