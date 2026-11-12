import * as THREE from 'three';
import type { CarRig } from '@/lib/tech/rig';
import type { XraySystem } from '@/data/vehicles/schema';
import { smooth, type LiveMotor, type XrayRig } from './rig';
import { Wishbone, type Kin, type P3 } from './wishbone';

/**
 * What the anatomy does when it is switched on: the clips of the exploded view (a rotor spinning up, the pack's cells lighting
 * in a wave, a wheel on its linkage, the steering turning), the dimming of the systems the visitor is not looking at, and the live
 * lights of the Drive tab (each motor's rotor and windings glow with its share of the output). One `AnatomyFx` per mounted anatomy: it
 * indexes the nodes by name, gives every mesh materials of its own (so one cell block can glow and its neighbour not) and keeps each
 * animated node's rest pose, so that stopping a clip puts everything back exactly.
 *
 * Moving the parts of a linkage is the linkage's own maths (wishbone.ts), not keyframes: the arms swing about their mounts, the knuckle
 * follows its two ball joints, the spring and damper aim from the tower to the arm, and the exterior's wheel rises with the hub.
 */

const Y = new THREE.Vector3(0, 1, 0);
const EMISSIVE_OFF = new THREE.Color(0, 0, 0);

interface Rest {
  position: THREE.Vector3;
  quaternion: THREE.Quaternion;
  scale: THREE.Vector3;
}

interface Corner {
  id: 'FL' | 'FR' | 'RL' | 'RR';
  index: number;
  group: THREE.Object3D;
  kin: Kin;
  wb: Wishbone;
}

interface Unit {
  id: string;
  rpm: number;
  rotor?: THREE.Object3D;
  pinion?: THREE.Object3D;
  gears?: THREE.Object3D;
  stator?: THREE.Object3D;
  angle: number;
}

const CORNER_INDEX = { FL: 0, FR: 1, RL: 2, RR: 3 } as const;

/**
 * Contact shading baked per vertex in Blender (carkit/anatomy/ao.py, the custom attribute `_XRAO`: 1 = open, 0 = shut). It darkens
 * the environment's light, diffuse and specular, where parts nearly touch (the gap between cells, a bolt's seat, the inside of a
 * casing); the lamps are left alone. GLTFLoader hands the attribute over as `_xrao` (lower-cased): it gets a GLSL-friendly name here,
 * and a mesh that came without one gets 1 (open) so that a material shared with a baked mesh never reads zeros.
 */
const AO_STRENGTH = 1.0;
function useVertexAo(g: THREE.BufferGeometry, mats: THREE.Material[]) {
  const raw = g.getAttribute('_xrao');
  if (raw) {
    g.setAttribute('xrAo', raw);
    g.deleteAttribute('_xrao');
  } else if (!g.getAttribute('xrAo')) {
    const n = g.getAttribute('position').count;
    g.setAttribute('xrAo', new THREE.BufferAttribute(new Float32Array(n).fill(1), 1));
  }
  for (const m of mats) {
    if (!(m instanceof THREE.MeshStandardMaterial) || m.userData.xrAo) continue;
    m.userData.xrAo = true;
    m.onBeforeCompile = (shader) => {
      shader.vertexShader = shader.vertexShader
        .replace('void main() {', 'attribute float xrAo;\nvarying float vXrAo;\nvoid main() {')
        .replace('#include <begin_vertex>', '#include <begin_vertex>\n\tvXrAo = xrAo;');
      shader.fragmentShader = shader.fragmentShader
        .replace('void main() {', 'varying float vXrAo;\nvoid main() {')
        .replace(
          '#include <aomap_fragment>',
          `#include <aomap_fragment>\n\tfloat xrOcc = mix( 1.0, vXrAo, ${AO_STRENGTH.toFixed(2)} );\n\treflectedLight.indirectDiffuse *= xrOcc;\n\treflectedLight.indirectSpecular *= mix( 1.0, xrOcc, 0.9 );`,
        );
    };
    m.customProgramCacheKey = () => 'xr-vertex-ao';
    m.needsUpdate = true;
  }
}

function parseJson<T>(raw: unknown): T | null {
  if (typeof raw !== 'string') return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export class AnatomyFx {
  private byName = new Map<string, THREE.Object3D>();
  private rest = new Map<THREE.Object3D, Rest>();
  private corners: Corner[] = [];
  private units: Unit[] = [];
  /** the Drive tab's tags beside the rotors, set by the viewer (viewer/XrayDirector.tsx) */
  tags = new Map<string, HTMLElement>();
  /** the harness reads this: how far the current has flowed along the cables (cycles), and how bright the pulses are */
  flow = { phase: 0, level: 0 };
  /** clips write the wheels through the car's rig, which needs to be told when they stop */
  private wheelsDirty = false;
  private lastClip = '';
  private lastClipT = 0;

  constructor(
    readonly root: THREE.Object3D,
    private readonly rig: XrayRig,
    private readonly car: CarRig | null,
  ) {
    // Materials are cloned (a clip lights one block of cells and not its neighbour, the focus dims one system) but shared as far as that
    // allows: a draw with a different material from the last costs a re-upload of the material's and the lights' uniforms, and with a
    // clone for every mesh the anatomy was 350 of them a frame. A material is shared by the meshes of one system that use it; those
    // that glow on their own (a stator, a rotor, a block of cells, the busbars, the plate) keep one for each.
    const own = /^XR_Drive_[A-Z]+_(Stator|Rotor)$|^XR_Battery_(Cells_\d+|Busbars|Plate)$/;
    const clones = new Map<string, THREE.Material>();
    const groupOf = (o: THREE.Object3D) => {
      let sys = 'x';
      let mine: string | undefined;
      for (let p: THREE.Object3D | null = o; p; p = p.parent) {
        if (!mine && own.test(p.name)) mine = p.name;
        const s = parseJson<{ sys?: string }>(p.userData?.xr)?.sys;
        if (s && sys === 'x') sys = s;
      }
      return mine ?? `sys:${sys}`;
    };
    root.traverse((o) => {
      if (o.name) this.byName.set(o.name, o);
      if (o instanceof THREE.Mesh) {
        const group = groupOf(o);
        const mats = (Array.isArray(o.material) ? o.material : [o.material]).map((m) => {
          const key = `${m.uuid}|${group}`;
          const hit = clones.get(key);
          const c: THREE.Material = hit ?? m.clone();
          if (!hit) clones.set(key, c);
          return c;
        });
        o.material = Array.isArray(o.material) ? mats : mats[0];
        useVertexAo(o.geometry, mats);
      }
    });
    for (const id of ['FL', 'FR', 'RL', 'RR'] as const) {
      const group = this.byName.get(`XR_Susp_${id}`);
      const kin = parseJson<Kin>(group?.userData?.kin);
      if (!group || !kin) continue;
      this.corners.push({ id, index: CORNER_INDEX[id], group, kin, wb: new Wishbone(kin) });
    }
    for (const id of ['F', 'R', 'RL', 'RR']) {
      const g = this.byName.get(`XR_Drive_${id}`);
      if (!g) continue;
      const meta = parseJson<{ rpm?: number }>(g.userData?.xr);
      this.units.push({
        id,
        rpm: meta?.rpm ?? 20000,
        rotor: this.byName.get(`XR_Drive_${id}_Rotor`),
        pinion: this.byName.get(`XR_Drive_${id}_Pinion`),
        gears: this.byName.get(`XR_Drive_${id}_Gears`),
        stator: this.byName.get(`XR_Drive_${id}_Stator`),
        angle: 0,
      });
    }
  }

  node(name: string) {
    return this.byName.get(name);
  }

  /** The drive units, with the rotor node of each, for the tags. */
  unitList(): { id: string; rotor?: THREE.Object3D }[] {
    return this.units.map((u) => ({ id: u.id, rotor: u.rotor }));
  }

  /** Every material under a node. */
  mats(name: string): THREE.MeshStandardMaterial[] {
    const out: THREE.MeshStandardMaterial[] = [];
    this.byName.get(name)?.traverse((o) => {
      if (!(o instanceof THREE.Mesh)) return;
      for (const m of Array.isArray(o.material) ? o.material : [o.material]) if (m instanceof THREE.MeshStandardMaterial) out.push(m);
    });
    return out;
  }

  /** The material of a given name under a node (a stator's phase U, the cells' wrap). */
  matNamed(node: string, material: string): THREE.MeshStandardMaterial[] {
    return this.mats(node).filter((m) => m.name === material);
  }

  private remember(o: THREE.Object3D) {
    if (!this.rest.has(o)) this.rest.set(o, { position: o.position.clone(), quaternion: o.quaternion.clone(), scale: o.scale.clone() });
  }

  private glow(ms: THREE.MeshStandardMaterial[], color: string | THREE.Color, k: number) {
    for (const m of ms) {
      m.emissive.set(color);
      m.emissiveIntensity = k;
    }
  }

  // ------------------------------------------------------------------------------------------ focus

  /**
   * The system the visitor is looking at stands out: the others go to a faint ghost. `part` (a node name list) is the part picked
   * inside it, which glows a little. `dimTo` is the opacity the others fall to.
   */
  setFocus(system: XraySystem | null, partNodes: string[], dimTo = 0.16) {
    const keep = new Set<THREE.Object3D>();
    for (const n of partNodes) this.byName.get(n)?.traverse((o) => keep.add(o));
    // materials are shared (see the constructor), so a part is lit with every mesh that shares its material
    const litMats = new Set<THREE.Material>();
    for (const o of keep) if (o instanceof THREE.Mesh) for (const m of Array.isArray(o.material) ? o.material : [o.material]) litMats.add(m);
    this.root.traverse((o) => {
      if (!(o instanceof THREE.Mesh)) return;
      let sys: string | undefined;
      for (let p: THREE.Object3D | null = o; p && !sys; p = p.parent) sys = parseJson<{ sys?: string }>(p.userData?.xr)?.sys;
      const dim = system !== null && sys !== undefined && sys !== system && sys !== 'root' && !(sys === 'suspension' && system === 'steering');
      for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
        const lit = litMats.has(m);
        if (!(m instanceof THREE.MeshStandardMaterial)) continue;
        const want = dim;
        if (m.transparent !== want) {
          m.transparent = want;
          m.needsUpdate = true;
        }
        m.opacity = want ? dimTo : 1;
        m.depthWrite = !want;
        // a picked part carries a soft glow, unless a clip is lighting its materials
        if (!this.rig.clip) {
          m.emissive.set(lit ? '#3b7bff' : '#000000');
          m.emissiveIntensity = lit ? 0.32 : 0;
        }
      }
    });
  }

  // ------------------------------------------------------------------------------------------ clips

  /** Advance the playing clip to `t` seconds into its loop (`dt` since the last call); `null` when none plays. */
  update(t: number | null, id: string | null, dt: number) {
    if (id && t !== null) {
      if (id !== this.lastClip) this.reset();
      this.lastClip = id;
      if (t < this.lastClipT) this.onLoop();
      this.lastClipT = t;
      if (id === 'rotor') this.rotorClip(t, dt);
      else if (id === 'battery') this.batteryClip(t);
      else if (id === 'suspension') this.suspensionClip(t);
      else if (id === 'steering') this.steeringClip(t);
    } else if (this.lastClip) {
      this.reset();
      this.lastClip = '';
      this.lastClipT = 0;
    }
  }

  private onLoop() {
    for (const u of this.units) u.angle = 0;
  }

  /** Put every node a clip moved, and every glow it lit, back. */
  reset() {
    for (const [o, r] of this.rest) {
      o.position.copy(r.position);
      o.quaternion.copy(r.quaternion);
      o.scale.copy(r.scale);
    }
    this.rest.clear();
    for (const u of this.units) u.angle = 0;
    this.root.traverse((o) => {
      if (!(o instanceof THREE.Mesh)) return;
      for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
        if (m instanceof THREE.MeshStandardMaterial && m.emissiveIntensity !== 0 && !m.userData.fxKeep) {
          m.emissive.copy(EMISSIVE_OFF);
          m.emissiveIntensity = 0;
        }
      }
    });
    if (this.car && this.wheelsDirty) {
      this.car.state.spin.fill(0);
      this.car.state.lift.fill(0);
      this.car.state.steer.fill(0);
      this.car.apply();
      this.wheelsDirty = false;
    }
    this.flow.level = 0;
    this.rig.apply();
  }

  /** The torque clip: the stator's three phases chase round, the rotors spin up, the gears and the wheels follow. */
  private rotorClip(t: number, dt: number) {
    const w = smooth(t / 3.6);
    const pulse = t;
    for (const u of this.units) {
      const speed = 2 * Math.PI * 2.6 * w * (u.rpm / 27200);
      u.angle += speed * dt;
      if (u.rotor) {
        this.remember(u.rotor);
        u.rotor.rotation.z = u.angle;
      }
      if (u.pinion) {
        this.remember(u.pinion);
        u.pinion.rotation.z = u.angle;
      }
      const ratio = u.id === 'F' || u.id === 'R' ? 4 : 2.5;
      if (u.gears) {
        this.remember(u.gears);
        // the output side turns the other way (external gears), the planetary's carrier the same way, slowly
        u.gears.rotation.z = (u.id === 'F' || u.id === 'R' ? 1 : -1) * (u.angle / ratio);
      }
      // the three phases, one after the other, round the stator
      const name = `XR_Drive_${u.id}_Stator`;
      ['U', 'V', 'W'].forEach((p, k) => {
        const a = Math.max(0, Math.sin(2 * Math.PI * (1.0 + 0.6 * w) * pulse - (k * 2 * Math.PI) / 3));
        this.glow(this.matNamed(name, `XR_Copper_${p}`), '#ff7a2a', 0.1 + 1.9 * a * a * (0.3 + 0.7 * w));
      });
      this.glow(this.matNamed(`XR_Drive_${u.id}_Rotor`, 'XR_Magnet_N'), '#ff3d3d', 0.25 + 0.7 * w);
      this.glow(this.matNamed(`XR_Drive_${u.id}_Rotor`, 'XR_Magnet_S'), '#3d6dff', 0.25 + 0.7 * w);
    }
    // the exterior's wheels turn with the output gears
    if (this.car) {
      this.wheelsDirty = true;
      const f = this.units.find((u) => u.id === 'F');
      const rl = this.units.find((u) => u.id === 'RL');
      const rr = this.units.find((u) => u.id === 'RR');
      const spin = (u: Unit | undefined, ratio: number) => (u ? u.angle / ratio : 0);
      this.car.state.spin[0] = this.car.state.spin[1] = spin(f, 4);
      this.car.state.spin[2] = spin(rl, 2.5);
      this.car.state.spin[3] = spin(rr, 2.5);
      this.car.apply();
    }
    this.flow.level = 0.4 + 0.6 * w;
  }

  /** The pack under load: the cell blocks light in a wave, the busbars glow, the current runs down the harness. */
  private batteryClip(t: number) {
    const dur = 6;
    const u = t / dur;
    for (let i = 1; i <= 12; i++) {
      const phase = 2 * Math.PI * (2 * u) - i * 0.52;
      const g = Math.max(0, Math.sin(phase));
      this.glow(this.mats(`XR_Battery_Cells_${String(i).padStart(2, '0')}`), '#58b2ff', 0.1 + 1.5 * g * g);
    }
    const bus = 0.5 + 0.5 * Math.sin(2 * Math.PI * u * 3);
    this.glow(this.mats('XR_Battery_Busbars'), '#ffa040', 0.3 + 1.2 * bus);
    this.glow(this.mats('XR_Battery_Plate'), '#4ac0ff', 0.12 + 0.2 * bus);
    this.flow.level = smooth(u * 2.5);
  }

  /** Each corner over a bump, the linkage solved: arms swing, the spring squeezes, the damper's rod slides, the wheel follows the hub. */
  private suspensionClip(t: number) {
    const T = 5;
    const phase = { FL: 0, RL: 0.3, FR: 0.5, RR: 0.8 } as const;
    for (const c of this.corners) {
      const x = (t / T + phase[c.id]) % 1;
      // a bump: up fast, down slower, with a small rebound
      const bump = x < 0.35 ? Math.sin((x / 0.35) * Math.PI) : x < 0.65 ? -0.35 * Math.sin(((x - 0.35) / 0.3) * Math.PI) : 0;
      this.poseCorner(c, 0.065 * bump);
    }
  }

  private poseCorner(c: Corner, travel: number) {
    const { wb, kin } = c;
    const H = wb.H;
    const pose = wb.solve(travel);
    const g = c.group;
    const name = (s: string) => this.byName.get(`XR_Susp_${c.id}_${s}`);
    const lower = name('LowerArm');
    const upper = name('UpperArm');
    const knuckle = name('Knuckle');
    if (lower) {
      this.remember(lower);
      lower.quaternion.copy(pose.lowerQ);
    }
    if (upper) {
      this.remember(upper);
      upper.quaternion.copy(pose.upperQ);
    }
    if (knuckle) {
      this.remember(knuckle);
      knuckle.quaternion.copy(pose.knuckleQ);
      knuckle.position.add(pose.hub).sub(H);
    }
    const aimOf = (n: THREE.Object3D) => parseJson<[P3, P3]>(n.userData?.aim);
    // the spring and damper: from the tower to the arm
    const st = new THREE.Vector3(...kin.ST);
    const sb = new THREE.Vector3(...kin.SB);
    const sbNow = wb.onLower(sb, pose.lowerAngle);
    const dir = sbNow.clone().sub(st);
    const len = dir.length();
    const len0 = sb.distanceTo(st);
    dir.normalize();
    const spring = name('Spring');
    const damper = name('Damper');
    const rod = name('Rod');
    if (spring) {
      this.remember(spring);
      spring.quaternion.setFromUnitVectors(Y, dir);
      spring.scale.set(1, len / len0, 1);
    }
    if (damper) {
      this.remember(damper);
      damper.quaternion.setFromUnitVectors(Y, dir);
    }
    if (rod) {
      this.remember(rod);
      rod.quaternion.setFromUnitVectors(Y, dir.clone().negate());
      rod.position.add(sbNow).sub(sb);
    }
    // the tie rod or toe link: from its fixed end to the knuckle's
    const tie = name(c.kin.front ? 'TieRod' : 'ToeLink');
    if (tie) {
      this.remember(tie);
      const ti = new THREE.Vector3(...kin.TI);
      const to = wb.onKnuckle(new THREE.Vector3(...kin.TO), pose);
      const d = to.clone().sub(ti);
      tie.quaternion.setFromUnitVectors(Y, d.clone().normalize());
      tie.scale.set(1, d.length() / new THREE.Vector3(...kin.TO).distanceTo(ti), 1);
    }
    // the half-shaft: from the drive unit's output to the knuckle
    const shaft = name('Halfshaft');
    const sa = shaft ? aimOf(shaft) : null;
    if (shaft && sa) {
      this.remember(shaft);
      const pin = new THREE.Vector3(...sa[0]);
      const pout = wb.onKnuckle(new THREE.Vector3(...sa[1]), pose);
      shaft.quaternion.setFromUnitVectors(Y, pout.clone().sub(pin).normalize());
    }
    void g;
    // the exterior's wheel rises with the hub
    if (this.car) {
      this.wheelsDirty = true;
      this.car.state.lift[c.index] = pose.hub.y - H.y;
      this.car.apply();
    }
  }

  /**
   * The wheels turn: the rack slides, the tie rods push the knuckles round, and the exterior's front wheels follow. The right wheel's angle
   * is solved from the rack's travel and the left's, so the two differ as a real linkage's do.
   */
  private steeringClip(t: number) {
    const fl = this.corners.find((c) => c.id === 'FL');
    const fr = this.corners.find((c) => c.id === 'FR');
    const rack = this.byName.get('XR_Steering_Rack');
    if (!fl || !fr || !rack) return;
    const dl = 0.24 * Math.sin((2 * Math.PI * t) / 6);
    const Z = new THREE.Vector3(0, 0, 1);
    const outer = (c: Corner, a: number) => {
      const H = c.wb.H;
      return new THREE.Vector3(...c.kin.TO).sub(H).applyAxisAngle(Y, a).add(H);
    };
    const TIl = new THREE.Vector3(...fl.kin.TI);
    const TIr = new THREE.Vector3(...fr.kin.TI);
    const L = (c: Corner) => new THREE.Vector3(...c.kin.TO).distanceTo(new THREE.Vector3(...c.kin.TI));
    // the rack's travel from the left tie rod: |TIl + r z - TOl'| = L
    const d = outer(fl, dl).sub(TIl);
    const root = Math.sqrt(Math.max(0, L(fl) ** 2 - d.x * d.x - d.y * d.y));
    const rr = Math.abs(d.z - root) < Math.abs(d.z + root) ? d.z - root : d.z + root;
    // the right wheel's angle: bisection on the tie rod's length
    const err = (a: number) => outer(fr, a).distanceTo(TIr.clone().addScaledVector(Z, rr)) - L(fr);
    let lo = -0.6;
    let hi = 0.6;
    for (let i = 0; i < 30; i++) {
      const mid = (lo + hi) / 2;
      if (err(lo) * err(mid) <= 0) hi = mid;
      else lo = mid;
    }
    const dr = (lo + hi) / 2;
    this.remember(rack);
    rack.position.addScaledVector(Z, rr);
    for (const [c, a, ti] of [[fl, dl, TIl], [fr, dr, TIr]] as const) {
      const kn = this.byName.get(`XR_Susp_${c.id}_Knuckle`);
      if (kn) {
        this.remember(kn);
        kn.quaternion.setFromAxisAngle(Y, a);
      }
      const tie = this.byName.get(`XR_Susp_${c.id}_TieRod`);
      if (tie) {
        this.remember(tie);
        const tiNow = ti.clone().addScaledVector(Z, rr);
        tie.position.addScaledVector(Z, rr);
        const dd = outer(c, a).sub(tiNow);
        tie.quaternion.setFromUnitVectors(Y, dd.clone().normalize());
        tie.scale.set(1, dd.length() / L(c), 1);
      }
      const shaft = this.byName.get(`XR_Susp_${c.id}_Halfshaft`);
      const sa = shaft ? parseJson<[P3, P3]>(shaft.userData?.aim) : null;
      if (shaft && sa) {
        this.remember(shaft);
        const pin = new THREE.Vector3(...sa[0]);
        const pout = new THREE.Vector3(...sa[1]).sub(c.wb.H).applyAxisAngle(Y, a).add(c.wb.H);
        shaft.quaternion.setFromUnitVectors(Y, pout.sub(pin).normalize());
      }
    }
    const rearRack = this.byName.get('XR_Steering_RearRack');
    const rl = this.corners.find((c) => c.id === 'RL');
    const rrCorner = this.corners.find((c) => c.id === 'RR');
    if (rearRack && rl && rrCorner) {
      const rShift = -rr * 0.42;
      const rAngleL = -dl * 0.42;
      const rAngleR = -dr * 0.42;
      this.remember(rearRack);
      rearRack.position.addScaledVector(Z, rShift);
      for (const [c, a] of [[rl, rAngleL], [rrCorner, rAngleR]] as const) {
        const kn = this.byName.get(`XR_Susp_${c.id}_Knuckle`);
        if (kn) {
          this.remember(kn);
          kn.quaternion.setFromAxisAngle(Y, a);
        }
        const toe = this.byName.get(`XR_Susp_${c.id}_ToeLink`);
        if (toe) {
          this.remember(toe);
          const ti = new THREE.Vector3(...c.kin.TI);
          const tiNow = ti.clone().addScaledVector(Z, rShift);
          toe.position.addScaledVector(Z, rShift);
          const dd = outer(c, a).sub(tiNow);
          toe.quaternion.setFromUnitVectors(Y, dd.clone().normalize());
          toe.scale.set(1, dd.length() / L(c), 1);
        }
      }
    }
    if (this.car) {
      this.wheelsDirty = true;
      this.car.state.steer[0] = dl;
      this.car.state.steer[1] = dr;
      if (rearRack) {
        this.car.state.steer[2] = -dl * 0.42;
        this.car.state.steer[3] = -dr * 0.42;
      }
      this.car.apply();
    }
  }

  // ------------------------------------------------------------------------------------------ Drive tab

  /**
   * The Drive tab's live lights: each motor's rotor spins with the car's wheels and glows with its share of the output, its windings
   * with the current it takes; `flow` carries the pulses on the cables, brighter as more power passes (and `regen` turns them round).
   * Called every frame by the viewer while the Drive tab's X-ray camera is on.
   */
  live(dt: number, motors: LiveMotor[], wheelRev: number, power: number, regen: boolean) {
    const byId = new Map(motors.map((m) => [m.id, m]));
    for (const u of this.units) {
      // the Drive run's motor ids are front, rear-left, rear-right (or rear); the anatomy's are F, RL, RR
      const key = u.id === 'F' ? 'front' : u.id === 'R' ? 'rear' : u.id === 'RL' ? 'rear-left' : 'rear-right';
      const m = byId.get(key) ?? (u.id !== 'F' ? byId.get('rear') : undefined);
      // seen on a perceptual curve: a motor at a tenth of its peak still reads as working
      const load = m ? Math.pow(Math.min(1, Math.abs(m.kw) / Math.max(1, m.peakKw)), 0.6) : 0;
      // the rotor turns with the wheel through the (illustrative) gearing, drawn slower than it is at speed so that it can be read
      const ratio = u.id === 'F' || u.id === 'R' ? 4 : 2.5;
      u.angle += wheelRev * ratio * dt;
      if (u.rotor) {
        this.remember(u.rotor);
        u.rotor.rotation.z = u.angle;
      }
      if (u.pinion) {
        this.remember(u.pinion);
        u.pinion.rotation.z = u.angle;
      }
      if (u.gears) {
        this.remember(u.gears);
        u.gears.rotation.z = (u.id === 'F' || u.id === 'R' ? 1 : -1) * (u.angle / ratio);
      }
      const ph = u.angle * 0.7;
      ['U', 'V', 'W'].forEach((p, k) => {
        const a = Math.max(0, Math.sin(ph - (k * 2 * Math.PI) / 3));
        this.glow(this.matNamed(`XR_Drive_${u.id}_Stator`, `XR_Copper_${p}`), regen ? '#3dffa0' : '#ff7a2a', 0.08 + 2.1 * load * a * a);
      });
      const rotorMats = (n: string) => this.matNamed(`XR_Drive_${u.id}_Rotor`, n);
      this.glow(rotorMats('XR_Magnet_N'), '#ff3d3d', 0.1 + 1.0 * load);
      this.glow(rotorMats('XR_Magnet_S'), '#3d6dff', 0.1 + 1.0 * load);
      // the tag beside the rotor: which motor, what it gives now, its share of the drive
      const tag = this.tags.get(u.id);
      if (tag && m) {
        const [name, kw, share] = [tag.children[0], tag.children[1], tag.children[2]];
        if (name) name.textContent = m.label;
        if (kw) kw.textContent = `${regen ? '−' : ''}${Math.round(Math.abs(m.kw))} kW`;
        if (share) share.textContent = `${Math.round(m.share * 100)}%`;
        tag.style.opacity = this.tagsOn ? '1' : '0';
        tag.style.setProperty('--load', String(load));
      }
    }
    this.flow.level = Math.min(1, power);
    this.flow.phase += dt * (regen ? -1 : 1) * (0.4 + 2.2 * Math.min(1, power));
  }

  /**
   * The pack, alive: its cell blocks light in a wave that runs faster and brighter as more power leaves it (or comes back, green, under
   * the brakes), and the busbars carry the load. `power` is the share of the peak, 0..1; the wave keeps a glow of its own at a cruise.
   */
  liveBattery(dt: number, power: number, regen: boolean) {
    // what is seen is how much, not how many kW: a cruise's few kilowatts still read as a pack at work
    const lvl = Math.pow(Math.min(1, Math.max(0, power)), 0.45);
    this.batteryPhase += dt * (0.8 + 4 * lvl) * (regen ? -1 : 1);
    const color = regen ? '#3dffa0' : '#58b2ff';
    for (let i = 1; i <= 12; i++) {
      const g = Math.max(0, Math.sin(this.batteryPhase - i * 0.52));
      this.glow(this.mats(`XR_Battery_Cells_${String(i).padStart(2, '0')}`), color, 0.18 + (0.25 + 1.3 * lvl) * g * g);
    }
    this.glow(this.mats('XR_Battery_Busbars'), regen ? '#3dffa0' : '#ffa040', 0.25 + 1.2 * lvl);
    this.glow(this.mats('XR_Battery_Plate'), color, 0.1 + 0.3 * lvl);
  }
  private batteryPhase = 0;
  /** the motors' tags are shown (the show hides them while the car drives away: they would float over nothing) */
  tagsOn = true;
}
