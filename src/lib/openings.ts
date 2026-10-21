import type * as THREE from 'three';
import type { OpeningId, OpeningSpec, Vehicle } from '@/data/vehicles/schema';
import type { Cue } from '@/lib/sound/cues';

/** A full swing, in seconds; a part that only has to finish a swing is quicker. */
const SWING_S = 0.95;

const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

/**
 * The swing of one car's openings, shared by the exterior and the cabin.
 *
 * Each part (a door's skin, its door card) is a glTF node whose origin sits on
 * the hinge, so opening is a rotation of that node about its own axis. One
 * instance per car holds the animated value, so both models read the same
 * number even when the cabin streams in while a door is mid-swing.
 */
export class Hinges {
  private progress = new Map<OpeningId, number>();
  private tween = new Map<OpeningId, { from: number; to: number; t0: number; dur: number; heard: boolean }>();
  private listeners = new Set<(id: OpeningId, cue: Cue) => void>();
  private parts = new Map<OpeningId, Set<THREE.Object3D>>();
  /** Nodes that exist only while the part is open (a door's painted frame). */
  private ajar = new Set<THREE.Object3D>();
  /** Nodes that go while the part is open (the shelf under a tailgate's glass). */
  private shut = new Map<OpeningId, Set<THREE.Object3D>>();
  /** The X-ray tab is on: parts marked `xrayHide` (the doors) are not drawn. */
  private xray = false;
  private followers = new Map<OpeningId, Set<(p: number) => void>>();
  /**
   * How far the cabin's light has moved from its shut bake to its open bake
   * (every door and the tailgate open): one uniform per part for its own
   * trim (a door card), one for the rest of the cabin (the most open part).
   */
  readonly lift = { cabin: { value: 0 }, door: new Map<OpeningId, { value: number }>() };

  liftOf(id: OpeningId) {
    let u = this.lift.door.get(id);
    if (!u) {
      u = { value: this.progress.get(id) ?? 0 };
      this.lift.door.set(id, u);
    }
    return u;
  }

  /** Call `fn` with an opening's swing (0 closed, 1 open) as it changes; also now. */
  follow(id: OpeningId, fn: (p: number) => void) {
    const set = this.followers.get(id) ?? new Set<(p: number) => void>();
    set.add(fn);
    this.followers.set(id, set);
    fn(this.progress.get(id) ?? 0);
    return () => {
      set.delete(fn);
    };
  }

  constructor(readonly specs: OpeningSpec[]) {}

  private apply(id: OpeningId) {
    const s = this.specs.find((x) => x.id === id);
    if (!s) return;
    const p = this.progress.get(id) ?? 0;
    this.liftOf(id).value = p;
    let most = 0;
    for (const v of this.progress.values()) most = Math.max(most, v);
    this.lift.cabin.value = most;
    for (const fn of this.followers.get(id) ?? []) fn(p);
    for (const o of this.shut.get(id) ?? []) o.visible = p < 0.002;
    const rad = ((s.deg * Math.PI) / 180) * p;
    const gone = this.xray && !!s.xrayHide;
    for (const o of this.parts.get(id) ?? []) {
      o.rotation[s.axis ?? 'y'] = rad;
      o.visible = !gone && (!this.ajar.has(o) || p > 0.002);
    }
  }

  /** Turn the X-ray tab on or off: the doors and their cards drop out or come back. */
  setXray(on: boolean) {
    this.xray = on;
    for (const s of this.specs) this.apply(s.id);
  }

  /** Put a node under an opening's control, at its current swing. */
  attach(id: OpeningId, o: THREE.Object3D, ajarOnly = false) {
    const set = this.parts.get(id) ?? new Set<THREE.Object3D>();
    set.add(o);
    if (ajarOnly) this.ajar.add(o);
    this.parts.set(id, set);
    this.apply(id);
  }

  detach(id: OpeningId, o: THREE.Object3D) {
    this.parts.get(id)?.delete(o);
    this.ajar.delete(o);
  }

  /** Hide a node while an opening is open (it does not move). */
  hideWhileOpen(id: OpeningId, o: THREE.Object3D) {
    const set = this.shut.get(id) ?? new Set<THREE.Object3D>();
    set.add(o);
    this.shut.set(id, set);
    this.apply(id);
    return () => {
      set.delete(o);
      o.visible = true;
    };
  }

  /**
   * Call `fn` at the moments a part makes a noise (src/lib/sound): when it starts to open (`release`), when it reaches the end
   * of its swing (`stop`) and when it closes (`shut`: the swing is over and the latch has caught).
   */
  listen(fn: (id: OpeningId, cue: Cue) => void) {
    this.listeners.add(fn);
    return () => {
      this.listeners.delete(fn);
    };
  }

  private emit(id: OpeningId, cue: Cue) {
    for (const fn of this.listeners) fn(id, cue);
  }

  /**
   * Aim an opening at open or closed; `snap` jumps there at once (a visitor who asked for less motion still hears the part
   * move). `quiet` is for putting the car in the state it was left in, which makes no noise.
   */
  aim(id: OpeningId, open: boolean, now: number, snap = false, quiet = false) {
    const to = open ? 1 : 0;
    const from = this.progress.get(id) ?? 0;
    if (snap) {
      const moved = this.tween.has(id) || from !== to;
      this.progress.set(id, to);
      this.tween.delete(id);
      this.apply(id);
      if (!quiet && moved) {
        if (open) {
          this.emit(id, 'release');
          this.emit(id, 'stop');
        } else this.emit(id, 'shut');
      }
      return;
    }
    const cur = this.tween.get(id);
    if (cur ? cur.to === to : from === to) return;
    this.tween.set(id, { from, to, t0: now, dur: SWING_S * Math.max(0.25, Math.abs(to - from)) * 1000, heard: false });
    if (open) this.emit(id, 'release');
  }

  /** Advance the swings; true while any is still moving. */
  step(now: number): boolean {
    let moving = false;
    for (const [id, tw] of this.tween) {
      const t = Math.min(1, (now - tw.t0) / tw.dur);
      this.progress.set(id, tw.from + (tw.to - tw.from) * ease(t));
      this.apply(id);
      // the stop and the latch are heard as the swing ends (its slow last few per cent): the thud lands as the part meets its seal
      if (!tw.heard && t >= 0.97) {
        tw.heard = true;
        this.emit(id, tw.to === 1 ? 'stop' : 'shut');
      }
      if (t >= 1) this.tween.delete(id);
      else moving = true;
    }
    return moving;
  }

  /** The first node under an opening's control (for where it is in the world), if any is attached. */
  partOf(id: OpeningId): THREE.Object3D | undefined {
    for (const o of this.parts.get(id) ?? []) return o;
    return undefined;
  }
}

const registry = new Map<string, Hinges>();

/** The car's hinges, or null when it has nothing that opens. */
export function hingesOf(vehicle: Vehicle): Hinges | null {
  if (!vehicle.openings?.length) return null;
  let h = registry.get(vehicle.slug);
  if (!h) {
    h = new Hinges(vehicle.openings);
    registry.set(vehicle.slug, h);
  }
  return h;
}
