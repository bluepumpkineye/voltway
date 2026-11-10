import * as THREE from 'three';

/**
 * A double-wishbone (or the two A-arms of a multi-link) linkage, solved as the wheel rises and falls. The hardpoints are the corner's
 * `kin` extra (blender/scripts/carkit/anatomy/suspension.py, in the viewer's axes): each arm turns about the line through its two
 * body mounts; its outer end is a ball joint on the knuckle, whose length between the two joints is fixed. Given how far the hub has
 * travelled, `solve` finds the lower arm's angle that puts the hub there, then the upper arm's that keeps the knuckle's two joints
 * their own distance apart, and from the two joints the knuckle's pose. Pure maths on THREE vectors; checked by
 * scripts/xray-tools/wishbone-test.mjs.
 */

export type P3 = [number, number, number];

export interface Kin {
  LF: P3;
  LR: P3;
  LBJ: P3;
  UF: P3;
  UR: P3;
  UBJ: P3;
  H: P3;
  TI: P3;
  TO: P3;
  SB: P3;
  ST: P3;
  aim: Record<string, [P3, P3]>;
  front: boolean;
}

const v = (p: P3) => new THREE.Vector3(p[0], p[1], p[2]);

export interface Pose {
  /** each arm's angle about its axis, rad */
  lowerAngle: number;
  upperAngle: number;
  lowerQ: THREE.Quaternion;
  upperQ: THREE.Quaternion;
  /** the knuckle's rotation, and where the hub has gone */
  knuckleQ: THREE.Quaternion;
  hub: THREE.Vector3;
  /** the lower ball joint (the knuckle's pivot for the maps below) */
  lbj: THREE.Vector3;
}

export class Wishbone {
  readonly LF: THREE.Vector3;
  readonly LR: THREE.Vector3;
  readonly LBJ: THREE.Vector3;
  readonly UF: THREE.Vector3;
  readonly UR: THREE.Vector3;
  readonly UBJ: THREE.Vector3;
  readonly H: THREE.Vector3;
  readonly lowerAxis: THREE.Vector3;
  readonly upperAxis: THREE.Vector3;
  readonly span: number;
  private lastUpper = 0;
  private readonly tmp = new THREE.Vector3();
  private readonly q = new THREE.Quaternion();

  constructor(readonly kin: Kin) {
    this.LF = v(kin.LF);
    this.LR = v(kin.LR);
    this.LBJ = v(kin.LBJ);
    this.UF = v(kin.UF);
    this.UR = v(kin.UR);
    this.UBJ = v(kin.UBJ);
    this.H = v(kin.H);
    this.lowerAxis = this.LR.clone().sub(this.LF).normalize();
    this.upperAxis = this.UR.clone().sub(this.UF).normalize();
    this.span = this.UBJ.distanceTo(this.LBJ);
  }

  /** A point carried by the lower arm (the spring's foot, the lower ball joint), turned by `angle`. */
  onLower(p: THREE.Vector3, angle: number, out = new THREE.Vector3()): THREE.Vector3 {
    this.q.setFromAxisAngle(this.lowerAxis, angle);
    return out.copy(p).sub(this.LF).applyQuaternion(this.q).add(this.LF);
  }

  private upperPoint(angle: number, out: THREE.Vector3): THREE.Vector3 {
    this.q.setFromAxisAngle(this.upperAxis, angle);
    return out.copy(this.UBJ).sub(this.UF).applyQuaternion(this.q).add(this.UF);
  }

  /** The upper arm's angle that keeps the joints `span` apart with the lower one at `pl`; Newton from the last answer. */
  private solveUpper(pl: THREE.Vector3): number {
    let a = this.lastUpper;
    const f = (x: number) => this.upperPoint(x, this.tmp).distanceTo(pl) - this.span;
    for (let i = 0; i < 24; i++) {
      const y = f(a);
      if (Math.abs(y) < 1e-7) break;
      const h = 1e-4;
      const d = (f(a + h) - y) / h;
      if (Math.abs(d) < 1e-9) break;
      a -= Math.max(-0.2, Math.min(0.2, y / d));
    }
    this.lastUpper = a;
    return a;
  }

  private poseFor(lowerAngle: number): Pose {
    const lbj = this.onLower(this.LBJ, lowerAngle);
    const upperAngle = this.solveUpper(lbj);
    const ubj = this.upperPoint(upperAngle, new THREE.Vector3());
    const knuckleQ = new THREE.Quaternion().setFromUnitVectors(
      this.UBJ.clone().sub(this.LBJ).normalize(),
      ubj.clone().sub(lbj).normalize(),
    );
    const hub = this.H.clone().sub(this.LBJ).applyQuaternion(knuckleQ).add(lbj);
    return {
      lowerAngle,
      upperAngle,
      lowerQ: new THREE.Quaternion().setFromAxisAngle(this.lowerAxis, lowerAngle),
      upperQ: new THREE.Quaternion().setFromAxisAngle(this.upperAxis, upperAngle),
      knuckleQ,
      hub,
      lbj,
    };
  }

  /** The pose with the hub `travel` metres above its rest height (below, negative). */
  solve(travel: number): Pose {
    // the height of the hub falls or rises with the lower arm's angle, whichever way the axis points: find which, then bisect
    this.lastUpper = 0;
    const lim = 0.45;
    const yLo = this.poseFor(-lim).hub.y;
    const yHi = this.poseFor(lim).hub.y;
    const up = yHi > yLo ? 1 : -1;
    const want = this.H.y + travel;
    let lo = -lim;
    let hi = lim;
    this.lastUpper = 0;
    for (let i = 0; i < 36; i++) {
      const mid = (lo + hi) / 2;
      const y = this.poseFor(mid).hub.y;
      if ((y - want) * up < 0) lo = mid;
      else hi = mid;
    }
    this.lastUpper = 0;
    return this.poseFor((lo + hi) / 2);
  }

  /** A point carried by the knuckle (the tie rod's outer end, the half-shaft's), moved with the pose. */
  onKnuckle(p: THREE.Vector3, pose: Pose, out = new THREE.Vector3()): THREE.Vector3 {
    return out.copy(p).sub(this.LBJ).applyQuaternion(pose.knuckleQ).add(pose.lbj);
  }
}
