'use client';

import React from 'react';
import * as THREE from 'three';
import { Html, useGLTF } from '@react-three/drei';
import { createPortal, useFrame, useThree, type ThreeEvent } from '@react-three/fiber';
import type { DriveCamera, Vehicle, XraySystem } from '@/data/vehicles/schema';
import { techClock } from '@/lib/tech/clock';
import { rigOf } from '@/lib/tech/rig';
import { lensAt } from '@/lib/tech/drive-beats';
import { driveLensPlan } from '@/lib/tech/drive-lens';
import { DRIVE_CAMERAS } from '@/lib/tech/drive-setup';
import { techSession } from '@/lib/tech/session';
import { AnatomyFx } from '@/lib/xray/fx';
import { assemblyLift, dimsOf } from '@/lib/xray/plan';
import { xrayOf } from '@/lib/xray/rig';
import { useVehicleStore } from '@/store/vehicle-store';
import { DRACO_PATH, useClonedScene } from './CarModel';
import { CarFollower } from './techRig';
import { GHOST, setGhost } from './xrayGhost';

/** The most see-through the Drive tab's lens makes the car (the ghost's level, 0..1), and how far its colour goes to the ghost's then. */
const LENS_MAX = 0.88;
const LENS_MIX = 0.55;
/** the elevation the camera lifts to, at least, while the lens reveals (degrees) */
const LENS_EL = 24;
/** the layer the Drive tab's hardware is on: seen by the camera, not by the floor's mirror */
const MIRROR_SKIP = 3;

/**
 * Runs the X-ray: aims the car's rig at the level the store says, steps it each frame, plays the clip that is on, and fades the
 * shell's ghost (the body firms up a little as it lifts away, and the studio's baked shadow, which belongs to the car on the floor,
 * fades with it). It asks for frames only while something moves, so a demand canvas stays idle at rest.
 */
export function XrayDirector({ vehicle }: { vehicle: Vehicle }) {
  const rig = xrayOf(vehicle);
  const invalidate = useThree((s) => s.invalidate);
  const scene = useThree((s) => s.scene);
  const tab = useVehicleStore((s) => s.tab);
  const level = useVehicleStore((s) => s.xrayLevel);
  const scrub = useVehicleStore((s) => s.xrayScrub);
  const spec = vehicle.xray;
  // dev only: window.__xray is the car's X-ray rig, for reading its level and its movers
  React.useEffect(() => {
    if (process.env.NODE_ENV !== 'production') (window as unknown as { __xray?: unknown }).__xray = rig;
  }, [rig]);
  // fetch the anatomy once the page is quiet, so the tab opens on it
  const anatomyUrl = spec?.anatomy?.url;
  React.useEffect(() => {
    if (!anatomyUrl) return;
    const id = window.setTimeout(() => useGLTF.preload(anatomyUrl, DRACO_PATH), 3000);
    return () => window.clearTimeout(id);
  }, [anatomyUrl]);
  // the Drive tab's X-ray camera holds the see-through level, with the motors alive
  const driveXray = useVehicleStore((s) => s.tab === 'drive' && s.drive.cam === 'xray') && Boolean(spec?.anatomy);
  // on any other camera but the driver's seat the car stays solid, and the cards reveal its hardware (the lens: each card, as it opens, ghosts the
  // paint and lights the parts it is about, for a few seconds, then the car is solid again; drive-beats.ts `lensAt`)
  const lensOn = useVehicleStore((s) => s.tab === 'drive' && (s.drive.cam ?? vehicle.drive?.camera ?? 'hero') !== 'cabin' && s.drive.cam !== 'xray') && Boolean(spec?.anatomy);
  const goal = !spec ? 0 : tab === 'xray' ? (spec.anatomy ? level : Math.min(1, level)) : driveXray ? 1 : 0;

  React.useEffect(() => {
    // leaving the tab puts the car back at once; entering it eases in; a dragged slider is followed as it moves
    rig.setTarget(goal, performance.now(), goal === 0 || scrub);
    invalidate();
  }, [rig, goal, scrub, invalidate]);
  // the lens ends with the Drive tab (or its camera going to the driver's seat): the car is solid again and the parts are as they were
  const lensSystem = React.useRef<string | null>(null);
  const lensLifted = React.useRef(false);
  React.useEffect(() => {
    if (!lensOn) return;
    return () => {
      if (lensLifted.current) {
        lensLifted.current = false;
        const st = useVehicleStore.getState();
        const base = DRIVE_CAMERAS[(st.drive.cam ?? vehicle.drive?.camera ?? 'hero') as DriveCamera];
        if (base && st.techStage && st.tab === 'drive') st.setTechStage({ ...st.techStage, camera: { az: base.az, el: base.el } });
      }
      rig.setLevel(0);
      rig.fx?.setFocus(null, []);
      lensSystem.current = null;
      invalidate();
    };
  }, [lensOn, rig, invalidate, vehicle.drive?.camera]);

  // a part or a system picked: the camera flies to it, keeping the side it was looking from; unpicked, it goes back to the pose
  const controls = useThree((s) => s.controls) as unknown as {
    setLookAt: (px: number, py: number, pz: number, tx: number, ty: number, tz: number, smooth: boolean) => Promise<void>;
    getTarget: (v: THREE.Vector3) => THREE.Vector3;
    getPosition: (v: THREE.Vector3) => THREE.Vector3;
  } | null;
  const camera = useThree((s) => s.camera);
  const partId = useVehicleStore((s) => s.xrayPart);
  const system = useVehicleStore((s) => s.xraySystem);
  const focused = React.useRef(false);
  React.useEffect(() => {
    if (tab !== 'xray' || !controls || !spec?.anatomy) return;
    const parts = spec.anatomy.parts;
    const picked = parts.find((p) => p.id === partId);
    const names = picked ? [picked] : system ? parts.filter((p) => p.system === system) : [];
    if (!names.length) {
      if (focused.current) {
        focused.current = false;
        useVehicleStore.setState((s) => ({ anchorTick: s.anchorTick + 1 }));
      }
      return;
    }
    const box = new THREE.Box3();
    const part = new THREE.Box3();
    let any = false;
    for (const p of names) {
      const root = p.scene === 'exterior' ? rig.roots.exterior : rig.roots.anatomy;
      for (const n of p.nodes) {
        const o = root?.getObjectByName(n);
        if (!o) continue;
        o.updateWorldMatrix(true, true);
        box.union(part.setFromObject(o));
        any = true;
      }
    }
    if (!any || box.isEmpty()) return;
    const c = box.getCenter(new THREE.Vector3());
    const r = box.getSize(new THREE.Vector3()).length() / 2;
    const from = controls.getTarget(new THREE.Vector3());
    // From the side the camera is on, turned toward the end of the car the part is at (a rear motor is seen from behind and the side, the
    // pack from the side), and a little above: the layers of the exploded view are seen between, not through, each other.
    const side = controls.getPosition(new THREE.Vector3()).sub(from).z < 0 ? -1 : 1;
    const along = Math.max(-1, Math.min(1, (c.x - (rig.roots.anatomy?.position.x ?? 0)) / 2.0));
    const dir = new THREE.Vector3(along * 0.85, 0, side * 0.75).normalize().multiplyScalar(Math.cos(0.3)).setY(Math.sin(0.3));
    const fov = (camera as THREE.PerspectiveCamera).fov ?? 30;
    // near enough to read the part, far enough to keep the picture round it: its radius over the sine of the half angle, and a margin
    const dist = Math.min(15, Math.max(5, (r * 2.1) / Math.sin((fov * Math.PI) / 360)));
    focused.current = true;
    void controls.setLookAt(c.x + dir.x * dist, c.y + dir.y * dist, c.z + dir.z * dist, c.x, c.y, c.z, true);
    invalidate();
  }, [tab, controls, spec, partId, system, rig, camera, invalidate]);

  const focusK = React.useRef(0);
  const shadow = React.useRef<THREE.Mesh | null>(null);
  useFrame((_, dt) => {
    const now = performance.now();
    const moving = rig.step(now);
    // a clip plays on the anatomy once the parts are where this frame put them
    const clip = rig.clip;
    rig.fx?.update(clip ? rig.clipTime(now) : null, clip?.id ?? null, Math.min(dt, 0.1));
    // the Drive tab's lens: the level follows the cards (a pure function of the playhead), and the parts of the system it reveals stand out
    let lensSys: string | null = null;
    if (lensOn) {
      const lens = lensAt(driveLensPlan.plan, techClock.t);
      rig.setLevel(LENS_MAX * lens.k);
      lensSys = lens.k > 0.02 ? lens.system : null;
      if (lensSystem.current !== lensSys) {
        lensSystem.current = lensSys;
        rig.fx?.setFocus(lensSys as XraySystem | null, [], 0.34);
      }
      // the camera lifts to look down at the hardware while it is revealed (from the side the motors are behind the wheels), and goes back after
      const st = useVehicleStore.getState();
      const driveCam = (st.drive.cam ?? vehicle.drive?.camera ?? 'hero') as DriveCamera;
      const base = DRIVE_CAMERAS[driveCam];
      const lifted = lens.k > 0.3;
      if (base && st.techStage && lifted !== lensLifted.current) {
        lensLifted.current = lifted;
        st.setTechStage({ ...st.techStage, camera: { az: base.az, el: lifted ? Math.max(base.el, LENS_EL) : base.el } });
      }
    }
    // looking at one system: the shell goes fainter and the cabin steps aside
    const want = system !== null || partId !== null || lensSys !== null ? 1 : 0;
    focusK.current += (want - focusK.current) * Math.min(1, dt * 6);
    if (Math.abs(want - focusK.current) < 0.01) focusK.current = want;
    else invalidate();
    const cab = rig.roots.cabin;
    if (cab) cab.visible = focusK.current < 0.5;
    // the Drive tab's live lights: each rotor spins with the car's speed and glows with the load its motor is under
    let live = false;
    if ((driveXray || lensSys !== null) && rig.fx) {
      const f = techSession.runtime?.launch?.drive;
      if (f) {
        const tel = f.telemetry(techClock.t);
        const peak = Math.max(f.modePeakKw, 1);
        const motors = f.motors.map((m, j) => ({ id: m.id, label: m.label, share: tel.motorShare[j] ?? 0, kw: tel.motorKw[j] ?? 0, peakKw: peak * 0.55 }));
        // drawn at a pace that can be read (at the real speed a rotor is a blur): a rev a second or two, faster as the car is
        const omega = (2 * Math.PI * 2.6 * (1 - Math.exp(-Math.abs(tel.speed) / 70))) / 2.5;
        const step = techClock.playing ? Math.min(dt, 0.1) : 0;
        rig.fx.live(step, motors, omega, Math.min(1, Math.abs(tel.powerKw) / peak), tel.powerKw < 0);
        if (driveXray || lensSys === 'battery') rig.fx.liveBattery(step, Math.abs(tel.powerKw) / peak, tel.powerKw < 0);
        live = techClock.playing;
      }
    }
    // the Drive tab's lens keeps the car's own colour in the ghost and does not fade it as a picked system does
    GHOST.alpha.value = (0.17 + 0.2 * rig.exploded) * (1 - (lensOn ? 0.2 : 0.6) * focusK.current);
    GHOST.rim.value = 0.5 - 0.1 * rig.exploded;
    GHOST.mix.value = lensOn ? LENS_MIX : 0.85;
    // the hardware is drawn only while it can be seen (in the X-ray tab it stays, as it always did)
    if (rig.roots.anatomy) rig.roots.anatomy.visible = tab === 'xray' || driveXray || rig.active;
    setGhost(rig.ghostMats, rig.ghost);
    if (!shadow.current) shadow.current = (scene.getObjectByName('ground-shadow') as THREE.Mesh | undefined) ?? null;
    const mat = shadow.current?.material as THREE.MeshBasicMaterial | undefined;
    if (mat) mat.opacity = 1 - 0.8 * Math.min(1, rig.level);
    if (moving || live) invalidate();
  });
  return null;
}

/** The anatomy: mounted while the X-ray tab is on (and the car has one), riding with the car like the cabin does. */
export function XrayAnatomy({ vehicle }: { vehicle: Vehicle }) {
  const url = vehicle.xray?.anatomy?.url;
  // in the Drive tab on every camera but the driver's seat: the lens reveals it behind the cards
  const on = useVehicleStore((s) => s.tab === 'xray' || (s.tab === 'drive' && (s.drive.cam ?? vehicle.drive?.camera ?? 'hero') !== 'cabin'));
  if (!url || !on) return null;
  return (
    <React.Suspense fallback={null}>
      <CarFollower vehicle={vehicle}>
        <Anatomy vehicle={vehicle} url={url} />
      </CarFollower>
    </React.Suspense>
  );
}

interface Meta {
  sys?: string;
  id?: string;
  ex?: [number, number, number];
  t0?: number;
  t1?: number;
}

function metaOf(o: THREE.Object3D): Meta | null {
  const raw = o.userData?.xr;
  if (typeof raw !== 'string') return null;
  try {
    return JSON.parse(raw) as Meta;
  } catch {
    return null;
  }
}

function Anatomy({ vehicle, url }: { vehicle: Vehicle; url: string }) {
  const { scene } = useGLTF(url, DRACO_PATH);
  const model = useClonedScene(scene);
  const rig = xrayOf(vehicle);
  const car = rigOf(vehicle);
  const invalidate = useThree((s) => s.invalidate);
  const fx = React.useMemo(() => new AnatomyFx(model, rig, car), [model, rig, car]);

  React.useEffect(() => {
    const lift = assemblyLift(dimsOf(vehicle), vehicle);
    model.traverse((o) => {
      if (o instanceof THREE.Mesh) {
        o.castShadow = false;
        o.receiveShadow = false;
      }
      const meta = metaOf(o);
      if (!meta) return;
      if (o.name === 'XR_Anatomy') {
        rig.add('anatomy', o, new THREE.Vector3(0, lift, 0), 0.1, 0.7, 'root');
        return;
      }
      if (!meta.ex) return;
      const ex = new THREE.Vector3(...meta.ex);
      if (ex.lengthSq() < 1e-8) return;
      const child = !!o.parent && o.parent.name !== 'XR_Anatomy' && o.parent.name !== '';
      rig.add('anatomy', o, ex, meta.t0 ?? 0.3, meta.t1 ?? 0.9, meta.sys ?? 'x', child);
    });
    rig.roots.anatomy = model;
    rig.fx = fx;
    rig.apply();
    invalidate();
    return () => {
      fx.reset();
      rig.stopClip();
      rig.remove('anatomy');
      rig.roots.anatomy = undefined;
      if (rig.fx === fx) rig.fx = null;
      invalidate();
    };
  }, [model, rig, fx, vehicle, invalidate]);

  // In the Drive tab the hardware is left out of the floor's mirror: the mirror draws the scene a second time, and the hardware is
  // hundreds of draws (the run slowed to a crawl on a laptop's graphics). Its own layer, which the camera sees and the mirror's does not;
  // in the X-ray tab it stays on the default layer, so that the picks (and the exploded parts' reflections) work. The harness joined the model
  // before this runs (children's effects come first).
  const onDrive = useVehicleStore((s) => s.tab === 'drive');
  const viewCamera = useThree((s) => s.camera);
  React.useEffect(() => {
    viewCamera.layers.enable(MIRROR_SKIP);
    model.traverse((o) => o.layers.set(onDrive ? MIRROR_SKIP : 0));
    invalidate();
  }, [model, onDrive, viewCamera, invalidate]);

  // the system the visitor is looking at stands out, and the part picked glows a little
  const system = useVehicleStore((s) => s.xraySystem);
  const partId = useVehicleStore((s) => s.xrayPart);
  React.useEffect(() => {
    const part = vehicle.xray?.anatomy?.parts.find((p) => p.id === partId);
    fx.setFocus(system, part && part.scene !== 'exterior' ? part.nodes : []);
    invalidate();
  }, [fx, vehicle, system, partId, invalidate]);

  // a tap on a part picks it: its label's card opens (the parts' nodes are matched with the left and right corners folded together)
  const pick = React.useMemo(() => {
    const norm = (n: string) => n.replace(/_F[LR](?=_|$)/, '_FL').replace(/_R[LR](?=_|$)/, '_RL').replace(/\d+$/, '');
    const byNode = new Map<string, string>();
    for (const p of vehicle.xray?.anatomy?.parts ?? []) {
      if (p.scene === 'exterior') continue;
      for (const n of p.nodes) if (!byNode.has(norm(n))) byNode.set(norm(n), p.id);
    }
    const find = (o: THREE.Object3D | null) => {
      for (let n = o; n; n = n.parent) {
        const id = byNode.get(norm(n.name));
        if (id) return id;
      }
      return undefined;
    };
    return {
      onClick: (e: ThreeEvent<MouseEvent>) => {
        const id = find(e.object);
        const part = vehicle.xray?.anatomy?.parts.find((p) => p.id === id);
        if (!part) return;
        e.stopPropagation();
        useVehicleStore.setState((s) => (s.xrayPart === part.id ? { xrayPart: null } : { xrayPart: part.id, xraySystem: part.system }));
      },
      onPointerOver: (e: ThreeEvent<PointerEvent>) => {
        if (find(e.object)) document.body.style.cursor = 'pointer';
      },
      onPointerOut: () => {
        document.body.style.cursor = '';
      },
    };
  }, [vehicle]);
  const tab = useVehicleStore((s) => s.tab);

  return (
    <>
      <primitive object={model} {...(tab === 'xray' ? pick : {})} />
      <Harness model={model} fx={fx} />
      <DriveTags fx={fx} />
    </>
  );
}

/** The Drive tab's tags: which motor, what it gives now, its share of the drive, pinned to its rotor (written by `AnatomyFx.live`). */
function DriveTags({ fx }: { fx: AnatomyFx }) {
  const on = useVehicleStore((s) => s.tab === 'drive' && s.drive.cam === 'xray');
  if (!on) return null;
  return (
    <>
      {fx.unitList().map((u) =>
        u.rotor ? (
          <React.Fragment key={u.id}>
            {createPortal(
              <Html center zIndexRange={[12, 0]} style={{ pointerEvents: 'none' }}>
                <div
                  ref={(el) => {
                    if (el) fx.tags.set(u.id, el);
                    else fx.tags.delete(u.id);
                  }}
                  className="flex items-center gap-2 whitespace-nowrap rounded-full bg-neutral-950/75 px-2.5 py-1 text-[11px] font-medium text-white opacity-0 shadow-lg ring-1 ring-white/15 backdrop-blur-md"
                  style={{ boxShadow: '0 0 calc(var(--load, 0) * 22px) rgba(255,138,48,0.9)' }}
                >
                  <span className="text-[9.5px] uppercase tracking-[0.1em] text-white/60" />
                  <span className="tnum" />
                  <span className="tnum text-amber-300" />
                </div>
              </Html>,
              u.rotor,
            )}
          </React.Fragment>
        ) : null,
      )}
    </>
  );
}

/** One ring of a corrugated cable sheath, tileable along u (x): a raised crest and a dark root. Used as bump and as colour. */
function sheathTexture() {
  const c = document.createElement('canvas');
  c.width = 64;
  c.height = 4;
  const g = c.getContext('2d')!;
  const grad = g.createLinearGradient(0, 0, 64, 0);
  grad.addColorStop(0, '#5a5a5a');
  grad.addColorStop(0.5, '#ffffff');
  grad.addColorStop(1, '#5a5a5a');
  g.fillStyle = grad;
  g.fillRect(0, 0, 64, 4);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = THREE.RepeatWrapping;
  t.wrapT = THREE.RepeatWrapping;
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4;
  return t;
}

/**
 * The high-voltage harness: three orange cables from the pack's junction box and rear connector to the three inverters, drawn from
 * the connectors' own positions (the `ports` extras of the anatomy) every frame, so they stretch as the parts fly apart. Pulses
 * run along them, faster and brighter with the current (`fx.flow`: a clip sets it, the Drive tab's live lights too).
 */
function Harness({ model, fx }: { model: THREE.Object3D; fx: AnatomyFx }) {
  const built = React.useMemo(() => {
    const ports = new Map<string, { node: THREE.Object3D; local: THREE.Vector3 }>();
    model.traverse((o) => {
      const raw = o.userData?.ports;
      if (typeof raw !== 'string') return;
      try {
        const d = JSON.parse(raw) as Record<string, [number, number, number]>;
        for (const [k, p] of Object.entries(d)) ports.set(k, { node: o, local: new THREE.Vector3(...p) });
      } catch {
        /* a port list that does not parse is left out */
      }
    });
    const defs = [
      { from: 'pdu_l', to: 'inv_F', out: 1 },
      { from: 'rear_l', to: 'inv_RL', out: -1 },
      { from: 'rear_r', to: 'inv_RR', out: -1 },
    ].filter((d) => ports.has(d.from) && ports.has(d.to));
    const group = new THREE.Group();
    group.name = 'XR_Harness';
    // a corrugated sheath: one ring pattern (a canvas, drawn once) as bump and as colour, repeated along each cable by its length
    const ring = sheathTexture();
    const mat = new THREE.MeshStandardMaterial({ color: '#ff7a24', roughness: 0.46, metalness: 0, bumpMap: ring, bumpScale: 1.6, map: ring });
    const dotMat = new THREE.PointsMaterial({
      size: 0.06,
      color: '#ffe2b0',
      transparent: true,
      opacity: 0,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      toneMapped: false,
    });
    const N = 9;
    const cables = defs.map((d) => {
      const mesh = new THREE.Mesh(new THREE.BufferGeometry(), mat);
      mesh.frustumCulled = false;
      const pts = new THREE.Points(
        new THREE.BufferGeometry().setAttribute('position', new THREE.BufferAttribute(new Float32Array(N * 3), 3)),
        dotMat,
      );
      pts.frustumCulled = false;
      group.add(mesh, pts);
      return { ...d, mesh, pts, a: new THREE.Vector3(NaN, 0, 0), b: new THREE.Vector3(NaN, 0, 0), curve: null as THREE.CatmullRomCurve3 | null };
    });
    return { ports, group, cables, mat, dotMat, N };
  }, [model]);

  React.useEffect(() => {
    model.add(built.group);
    return () => {
      model.remove(built.group);
      for (const c of built.cables) {
        c.mesh.geometry.dispose();
        c.pts.geometry.dispose();
        const m = c.mesh.material as THREE.MeshStandardMaterial;
        if (m !== built.mat) {
          m.map?.dispose();
          m.dispose();
        }
      }
      built.mat.map?.dispose();
      built.mat.dispose();
      built.dotMat.dispose();
    };
  }, [model, built]);

  const tmpA = React.useMemo(() => new THREE.Vector3(), []);
  const tmpB = React.useMemo(() => new THREE.Vector3(), []);
  const invalidate = useThree((s) => s.invalidate);
  useFrame((_, dt) => {
    const { ports, cables, N, dotMat } = built;
    model.updateWorldMatrix(true, false);
    let moved = false;
    for (const c of cables) {
      const pa = ports.get(c.from)!;
      const pb = ports.get(c.to)!;
      pa.node.updateWorldMatrix(true, false);
      pb.node.updateWorldMatrix(true, false);
      tmpA.copy(pa.local);
      tmpB.copy(pb.local);
      model.worldToLocal(pa.node.localToWorld(tmpA));
      model.worldToLocal(pb.node.localToWorld(tmpB));
      if (!c.curve || c.a.distanceToSquared(tmpA) > 1e-8 || c.b.distanceToSquared(tmpB) > 1e-8) {
        c.a.copy(tmpA);
        c.b.copy(tmpB);
        const mid = tmpA.clone().add(tmpB).multiplyScalar(0.5);
        mid.y += 0.16;
        c.curve = new THREE.CatmullRomCurve3(
          [tmpA.clone(), tmpA.clone().add(new THREE.Vector3(0.1 * c.out, 0.02, 0)), mid, tmpB.clone().add(new THREE.Vector3(0, 0.12, 0)), tmpB.clone()],
          false,
          'centripetal',
        );
        c.mesh.geometry.dispose();
        c.mesh.geometry = new THREE.TubeGeometry(c.curve, 140, 0.0125, 12, false);
        // one ring every 9 mm along the cable: the texture's repeat follows the curve's length (each cable has a material of its own)
        const len = c.curve.getLength();
        let own = c.mesh.material as THREE.MeshStandardMaterial;
        if (!own.userData.own) {
          own = own.clone();
          own.userData.own = true;
          const map = own.map!.clone();
          map.needsUpdate = true;
          own.map = map;
          own.bumpMap = map;
          c.mesh.material = own;
        }
        own.map!.repeat.set(len / 0.009, 1);
        moved = true;
      }
      // the pulses
      const attr = c.pts.geometry.getAttribute('position') as THREE.BufferAttribute;
      for (let i = 0; i < N; i++) {
        const u = (((fx.flow.phase + i / N) % 1) + 1) % 1;
        const p = c.curve.getPointAt(u);
        attr.setXYZ(i, p.x, p.y, p.z);
      }
      attr.needsUpdate = true;
    }
    fx.flow.phase += dt * (0.5 + 1.6 * fx.flow.level);
    dotMat.opacity = Math.min(1, fx.flow.level * 1.4);
    if (moved || fx.flow.level > 0.01) invalidate();
  });
  return null;
}
