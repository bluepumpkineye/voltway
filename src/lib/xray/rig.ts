import * as THREE from 'three';
import type { Vehicle, XraySystem } from '@/data/vehicles/schema';

/**
 * The X-ray tab's one animated number and the parts it moves.
 *
 * `level` runs 0 (solid) to 1 (see-through) to 2 (exploded). The body is a ghost from 0 to 1 (the viewer's shader patch reads
 * `ghost`), and from 1 to 2 every part flies out: a part registered with `add` has an offset `ex` (relative to its parent, so a
 * group's offset carries its parts), and a window `t0`..`t1` of the exploded phase in which it travels (staggered, so the body
 * lifts first and the hardware follows). The module holds no React and no renderer: the viewer steps it each frame and reads
 * the numbers it wants (viewer/XrayDirector.tsx); the panel listens to `subscribe`.
 *
 * A system's own parts (the rotor out of the stator) are `child` movers: when a clip plays on a system the rig puts that
 * system's children back in place (`assemble`), so a linkage works on a linkage that is whole, then lets them out again.
 */

const clamp01 = (x: number) => Math.min(1, Math.max(0, x));
export const smooth = (x: number) => {
  const t = clamp01(x);
  return t * t * (3 - 2 * t);
};
const easeInOut = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

export interface Mover {
  node: THREE.Object3D;
  /** local rest position */
  rest: THREE.Vector3;
  /** the offset at full explode, relative to the parent */
  ex: THREE.Vector3;
  t0: number;
  t1: number;
  sys: string;
  child: boolean;
  src: string;
  /** the node's height belongs to something else (a wheel's: the car's rig sets it): the rig leaves it alone */
  keepY: boolean;
}

/** One motor's state in the Drive run, for the anatomy's live lights (fx.ts). */
export interface LiveMotor {
  id: string;
  label: string;
  share: number;
  kw: number;
  /** the power it can give, for the scale of its glow */
  peakKw: number;
}

export interface ClipState {
  id: string;
  /** wall-clock start, ms */
  t0: number;
  /** seconds */
  dur: number;
  loop: boolean;
  /** a clip that has finished and is holding its last frame */
  done: boolean;
}

export class XrayRig {
  /** the animated level, 0 solid, 1 see-through, 2 exploded */
  level = 0;
  /** where the level is going */
  target = 0;
  private tw: { from: number; to: number; t0: number; dur: number } | null = null;
  readonly movers: Mover[] = [];
  /** per system: how far its children are back in place (0 apart, 1 together), and where that is going */
  private asm = new Map<string, { v: number; from: number; to: number; t0: number }>();
  /** the system the visitor is looking at: the rest of the anatomy dims */
  focus: string | null = null;
  clip: ClipState | null = null;
  /** the scenes mounted for the view (the labels read their nodes), and the exterior materials the ghost patch took */
  roots: { anatomy?: THREE.Object3D; exterior?: THREE.Object3D; cabin?: THREE.Object3D } = {};
  ghostMats = new Set<THREE.Material>();
  /** the mounted anatomy's effects (clips, focus, live lights), see fx.ts; set by the viewer */
  fx: {
    update: (t: number | null, id: string | null, dt: number) => void;
    live: (dt: number, motors: LiveMotor[], wheelRev: number, power: number, regen: boolean) => void;
    liveBattery: (dt: number, power: number, regen: boolean) => void;
    setFocus: (system: XraySystem | null, partNodes: string[], dim?: number) => void;
    /** put every node a clip or the live lights moved back, and every glow out */
    reset: () => void;
    /** the motors' tags are shown */
    tagsOn: boolean;
  } | null = null;
  private levelFollowers = new Set<(ghost: number, exploded: number) => void>();
  private lastGhost = -1;
  private subs = new Set<() => void>();
  /** counts every change the panel could show */
  version = 0;

  subscribe = (fn: () => void) => {
    this.subs.add(fn);
    return () => {
      this.subs.delete(fn);
    };
  };

  getVersion = () => this.version;

  private changed() {
    this.version++;
    for (const fn of this.subs) fn();
  }

  /** The see-through amount, 0 solid to 1 ghost. */
  get ghost() {
    return clamp01(this.level);
  }

  /** The exploded phase, 0 together to 1 fully apart. */
  get exploded() {
    return clamp01(this.level - 1);
  }

  /** Aim the level at a value; `snap` jumps there at once (a slider being dragged, a tab being left). */
  setTarget(v: number, now: number, snap = false) {
    const to = Math.min(1, Math.max(0, v));
    if (snap) {
      this.level = to;
      this.target = to;
      this.tw = null;
      this.apply();
      this.changed();
      return;
    }
    if (to === this.target && (this.tw || this.level === to)) return;
    this.target = to;
    const dist = Math.abs(to - this.level);
    this.tw = dist < 1e-4 ? null : { from: this.level, to, t0: now, dur: 1000 * (0.55 + 1.15 * Math.min(1, dist)) };
    if (!this.tw) this.level = to;
    this.changed();
  }

  /** Put a node under the rig. Its position now is its rest position. */
  add(src: string, node: THREE.Object3D, ex: THREE.Vector3, t0: number, t1: number, sys: string, child = false, keepY = false) {
    this.movers.push({ node, rest: node.position.clone(), ex: ex.clone(), t0, t1, sys, child, src, keepY });
  }

  /** Take every node a source registered out again, back at its rest position. */
  remove(src: string) {
    for (let i = this.movers.length - 1; i >= 0; i--) {
      const m = this.movers[i];
      if (m.src !== src) continue;
      m.node.position.copy(m.rest);
      this.movers.splice(i, 1);
    }
    this.changed();
  }

  /** Put a system's children back in place (`on`), or let them out again, over about half a second. */
  assemble(sys: string, on: boolean, now: number) {
    const cur = this.asm.get(sys);
    const from = cur ? this.assembledOf(sys) : 0;
    this.asm.set(sys, { v: from, from, to: on ? 1 : 0, t0: now });
  }

  assembledOf(sys: string) {
    return this.asm.get(sys)?.v ?? 0;
  }

  /** Call `fn` with the ghost and exploded amounts whenever the ghost amount changes; also now. */
  followLevel(fn: (ghost: number, exploded: number) => void) {
    this.levelFollowers.add(fn);
    fn(this.ghost, this.exploded);
    return () => {
      this.levelFollowers.delete(fn);
    };
  }

  /** Advance the tweens; true while anything is still moving. */
  /** Put the level at a value at once, every frame if need be (the Drive tab's reveal follows the playhead): the panel hears only when the X-ray starts or stops. */
  setLevel(v: number) {
    const to = Math.min(1, Math.max(0, v));
    if (to === this.level && this.tw === null) return;
    this.level = to;
    this.target = to;
    this.tw = null;
    this.apply();
  }

  step(now: number): boolean {
    let moving = false;
    if (this.tw) {
      const t = clamp01((now - this.tw.t0) / this.tw.dur);
      this.level = this.tw.from + (this.tw.to - this.tw.from) * easeInOut(t);
      if (t >= 1) {
        this.level = this.tw.to;
        this.tw = null;
      } else moving = true;
    }
    for (const a of this.asm.values()) {
      if (a.v === a.to) continue;
      const t = clamp01((now - a.t0) / 550);
      a.v = a.from + (a.to - a.from) * smooth(t);
      if (t < 1) moving = true;
      else a.v = a.to;
    }
    this.apply();
    if (this.clip && !this.clip.done) moving = true;
    return moving;
  }

  /** Write every mover's position for the level (a wheel's height belongs to the car's rig: `keepY`). A clip then moves a node from where this put it. */
  apply() {
    const e = this.exploded;
    for (const m of this.movers) {
      const p = smooth((e - m.t0) / Math.max(1e-3, m.t1 - m.t0));
      const k = m.child ? p * (1 - this.assembledOf(m.sys)) : p;
      const pos = m.node.position;
      pos.x = m.rest.x + m.ex.x * k;
      if (!m.keepY) pos.y = m.rest.y + m.ex.y * k;
      pos.z = m.rest.z + m.ex.z * k;
    }
    if (this.ghost !== this.lastGhost) {
      this.lastGhost = this.ghost;
      for (const fn of this.levelFollowers) fn(this.ghost, e);
    }
    // the body is a ghost from the first hint of the level: the panel and the viewer's hooks hear when that starts and stops
    const on = this.level > 0.03;
    if (on !== this.active) {
      this.active = on;
      this.changed();
    }
  }

  /** The level is above zero: the X-ray is showing something (see `apply`). */
  active = false;

  // ------------------------------------------------------------------------------------------------ clips

  startClip(id: string, dur: number, now: number, loop = true) {
    this.clip = { id, t0: now, dur, loop, done: false };
    this.changed();
  }

  stopClip() {
    if (!this.clip) return;
    this.clip = null;
    this.changed();
  }

  /** Seconds into the playing clip (looped), or null when none plays. */
  clipTime(now: number): number | null {
    const c = this.clip;
    if (!c) return null;
    const s = (now - c.t0) / 1000;
    if (c.loop) return s % c.dur;
    if (s >= c.dur) {
      c.done = true;
      return c.dur;
    }
    return s;
  }
}

const rigs = new Map<string, XrayRig>();

/** The car's X-ray rig (one per car, like its hinges and its wheel rig). */
export function xrayOf(vehicle: Vehicle): XrayRig {
  let r = rigs.get(vehicle.slug);
  if (!r) {
    r = new XrayRig();
    rigs.set(vehicle.slug, r);
  }
  return r;
}
