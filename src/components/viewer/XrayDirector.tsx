'use client';

import React from 'react';
import * as THREE from 'three';
import { Html, useGLTF } from '@react-three/drei';
import { createPortal, useFrame, useThree, type ThreeEvent } from '@react-three/fiber';
import type { Vehicle, XraySystem } from '@/data/vehicles/schema';
import { techClock } from '@/lib/tech/clock';
import { rigOf } from '@/lib/tech/rig';
import { techSession } from '@/lib/tech/session';
import { AnatomyFx } from '@/lib/xray/fx';
import { xrayOf } from '@/lib/xray/rig';
import { exitAt, exitPull } from '@/lib/tech/drive-exit';
import { chapterAt, planFor, SHOW_EXIT_S } from '@/lib/xray/show';
import { useVehicleStore } from '@/store/vehicle-store';
import { DRACO_PATH, useClonedScene } from './CarModel';
import { CarFollower } from './techRig';
import { GHOST, setGhost } from './xrayGhost';

/**
 * Runs the X-ray: aims the car's rig at the level the store says, steps it each frame, plays the clip that is on, and fades the
 * shell's ghost (the body firms up a little as it lifts away, and the studio's baked shadow, which belongs to the car on the floor,
 * fades with it). It asks for frames only while something moves, so a demand canvas stays idle at rest.
 *
 * On the tab's Play (`xrayShow`) it also dresses the run: the cabin goes, the body is the faintest pane, the motors' rotors spin and glow with
 * the load they are under (the run's own telemetry), the pack's cells run with the current, and the parts of the system the shot is on
 * stand out (src/lib/xray/show.ts).
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
  // the tab's Play: the run on the salt flat, the body a faint pane over the hardware
  const show = useVehicleStore((s) => s.tab === 'xray' && s.xrayShow) && Boolean(spec?.anatomy);
  const goal = !spec ? 0 : tab === 'xray' ? Math.min(1, level) : 0;

  React.useEffect(() => {
    // leaving the tab puts the car back at once; entering it eases in; a dragged slider is followed as it moves
    rig.setTarget(goal, performance.now(), goal === 0 || scrub);
    invalidate();
  }, [rig, goal, scrub, invalidate]);
  // the black glass underlays (the exterior's `*_Blackout` nodes: the dark frames of the windows, which the ghost leaves opaque) go while the show runs
  React.useEffect(() => {
    if (!show) return;
    const root = rig.roots.exterior;
    if (!root) return;
    const hidden: THREE.Object3D[] = [];
    root.traverse((o) => {
      if (o.visible && o.name.toLowerCase().endsWith('_blackout')) {
        o.visible = false;
        hidden.push(o);
      }
    });
    invalidate();
    return () => {
      for (const o of hidden) o.visible = true;
      invalidate();
    };
  }, [show, rig, invalidate]);
  // the system the shot is on stands out; when the show ends the parts are as the visitor's own pick (or none) leaves them
  const showSystem = React.useRef<XraySystem | null>(null);
  React.useEffect(() => {
    if (!show) return;
    return () => {
      showSystem.current = null;
      const st = useVehicleStore.getState();
      // the rotors stop, the glows go out
      rig.fx?.reset();
      rig.fx?.setFocus(st.xraySystem, []);
      invalidate();
    };
  }, [show, rig, invalidate]);

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
    // the show: the parts of the system the shot is on stand out, the others dim a little
    const run = techSession.runtime?.launch?.drive;
    if (show && run && techClock.duration > 0) {
      const sys = chapterAt(planFor(run, { events: run.events, duration: techClock.duration, exit: SHOW_EXIT_S }), techClock.t).system as XraySystem | null;
      if (sys !== showSystem.current) {
        showSystem.current = sys;
        rig.fx?.setFocus(sys, [], 0.5);
      }
    }
    // looking at one system (or the show): the shell goes fainter and the cabin steps aside
    const want = system !== null || partId !== null || show ? 1 : 0;
    focusK.current += (want - focusK.current) * Math.min(1, dt * 6);
    if (Math.abs(want - focusK.current) < 0.01) focusK.current = want;
    else invalidate();
    const cab = rig.roots.cabin;
    if (cab) cab.visible = !show && focusK.current < 0.5;
    // the show's live lights: each rotor spins with the car's speed and glows with the load its motor is under, the pack's cells run with the current
    let live = false;
    if (show && rig.fx) {
      const f = techSession.runtime?.launch?.drive;
      if (f) {
        const exitSpec = { duration: techClock.duration, exit: SHOW_EXIT_S };
        rig.fx.tagsOn = techClock.t < techClock.duration - SHOW_EXIT_S + 0.2;
        const tel = f.telemetry(Math.min(techClock.t, techClock.duration - SHOW_EXIT_S));
        const peak = Math.max(f.modePeakKw, 1);
        let motors = f.motors.map((m, j) => ({ id: m.id, label: m.label, share: tel.motorShare[j] ?? 0, kw: tel.motorKw[j] ?? 0, peakKw: peak * 0.55 }));
        let speed = tel.speed;
        let power = Math.abs(tel.powerKw) / peak;
        let regen = tel.powerKw < 0;
        if (techClock.t > techClock.duration - SHOW_EXIT_S) {
          // the exit: the car sets off again, the motors take the load of the pull and let go as it settles to its pace
          const ex = exitAt(exitSpec, techClock.t, exitPull.a0, f.telemetry(techClock.duration - SHOW_EXIT_S).speed / 3.6);
          speed = ex.v * 3.6;
          power = 0.12 + 0.6 * ex.pull * (ex.v > 0 ? 1 : 0);
          regen = false;
          motors = f.motors.map((m) => ({ id: m.id, label: m.label, share: m.share, kw: m.share * peak * 0.55 * ex.pull * (ex.v > 0 ? 1 : 0), peakKw: peak * 0.55 }));
        }
        // drawn at a pace that can be read (at the real speed a rotor is a blur): a rev a second or two, faster as the car is
        const omega = (2 * Math.PI * 2.6 * (1 - Math.exp(-Math.abs(speed) / 70))) / 2.5;
        const step = techClock.playing ? Math.min(dt, 0.1) : 0;
        rig.fx.live(step, motors, omega, Math.min(1, power), regen);
        rig.fx.liveBattery(step, power, regen);
        live = techClock.playing;
      }
    }
    GHOST.alpha.value = (0.17 + 0.2 * rig.exploded) * (1 - (show ? 0.72 : 0.6) * focusK.current);
    GHOST.rim.value = 0.5 - 0.1 * rig.exploded;
    GHOST.mix.value = 0.85;
    // the hardware is drawn only while it can be seen (in the X-ray tab it stays, as it always did)
    if (rig.roots.anatomy) rig.roots.anatomy.visible = tab === 'xray' || rig.active;
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
  const on = useVehicleStore((s) => s.tab === 'xray');
  if (!url || !on) return null;
  return (
    <React.Suspense fallback={null}>
      <CarFollower vehicle={vehicle}>
        <Anatomy vehicle={vehicle} url={url} />
      </CarFollower>
    </React.Suspense>
  );
}

function Anatomy({ vehicle, url }: { vehicle: Vehicle; url: string }) {
  const { scene } = useGLTF(url, DRACO_PATH);
  const model = useClonedScene(scene);
  const rig = xrayOf(vehicle);
  const car = rigOf(vehicle);
  const invalidate = useThree((s) => s.invalidate);
  const fx = React.useMemo(() => new AnatomyFx(model, rig, car), [model, rig, car]);

  React.useEffect(() => {
    model.traverse((o) => {
      if (o instanceof THREE.Mesh) {
        o.castShadow = false;
        o.receiveShadow = false;
      }
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
  // a tap picks a part in the tab, not while the show runs (its camera is the show's)
  const pickable = useVehicleStore((s) => s.tab === 'xray' && !s.xrayShow);

  return (
    <>
      <primitive object={model} {...(pickable ? pick : {})} />
      <Harness model={model} fx={fx} />
      <DriveTags fx={fx} />
    </>
  );
}

/** The show's tags: which motor, what it gives now, its share of the drive, pinned to its rotor (written by `AnatomyFx.live`). */
function DriveTags({ fx }: { fx: AnatomyFx }) {
  const on = useVehicleStore((s) => s.tab === 'xray' && s.xrayShow);
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
      { from: 'rear_l', to: 'inv_R', out: -1 },
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
