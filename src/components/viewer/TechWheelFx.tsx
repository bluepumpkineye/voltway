'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import type { Vehicle } from '@/data/vehicles/schema';
import { techClock } from '@/lib/tech/clock';
import { launchActs, runShape, tagWindows, wheelKw, wheelLook } from '@/lib/tech/drive-beats';
import { rigOf } from '@/lib/tech/rig';
import { techSession } from '@/lib/tech/session';
import { clamp, EASE_OUT, fmt, presence, SPRINGS } from '@/lib/tech/motion';
import { useVehicleStore } from '@/store/vehicle-store';

/**
 * The Drive tab's lights on the car's own wheels: each wheel wears a ring of light that shows what its motor is doing. Cyan for
 * the front motor, amber for the rear, green when the motor feeds the battery, red when the brake works; the band running round
 * the ring goes the way the wheel turns, faster the more power. The ring hangs on the wheel's hub group (src/lib/tech/rig.ts), so
 * it steers with the wheel (the S-curve's turned wheels), rises with its travel and rides on the car wherever the car goes.
 *
 * At the launch the wheels are lit in turn, the front motor's, then the rear motors', then all (`launchActs`,
 * src/lib/tech/drive-beats.ts), so that the visitor sees where the drive goes; after that each ring follows its own motor. Where
 * a split is the point (an act, the S-curve, the brakes) a small tag with the wheel's own figure stands over the wheel.
 *
 * The split between motors is ours (the maker does not publish it), and the screen's tile says so.
 */
export function TechWheelFx({ vehicle }: { vehicle: Vehicle }) {
  const on = useVehicleStore((s) => s.tab === 'drive' && s.drive.cam !== 'cabin');
  const rig = rigOf(vehicle);
  const mounts = React.useSyncExternalStore(rig.subscribe, () => rig.mounts, () => 0);
  if (!on || !rig.wheels) return null;
  return <Lights key={mounts} vehicle={vehicle} />;
}

const CYAN = new THREE.Color('#38bdf8');
const AMBER = new THREE.Color('#fbbf24');
const GREEN = new THREE.Color('#34d399');
const RED = new THREE.Color('#ff4d4d');
const SEGMENTS = 44;
/** where the ring stands outboard of the hub, in tyre radii (the tyre's face is a little under 0.4) */
const OUT = 0.5;

/** A ring of short bars round the axle, in the plane of the wheel; the colour of each bar is set every frame. */
function ringGeometry(r0: number, r1: number): THREE.BufferGeometry {
  const pos = new Float32Array(SEGMENTS * 4 * 3);
  const col = new Float32Array(SEGMENTS * 4 * 4);
  const idx: number[] = [];
  const step = (Math.PI * 2) / SEGMENTS;
  for (let i = 0; i < SEGMENTS; i++) {
    const a0 = i * step + step * 0.1;
    const a1 = (i + 1) * step - step * 0.1;
    const v = [
      [r0 * Math.cos(a0), r0 * Math.sin(a0)],
      [r1 * Math.cos(a0), r1 * Math.sin(a0)],
      [r1 * Math.cos(a1), r1 * Math.sin(a1)],
      [r0 * Math.cos(a1), r0 * Math.sin(a1)],
    ];
    v.forEach(([x, y], k) => pos.set([x, y, 0], (i * 4 + k) * 3));
    idx.push(i * 4, i * 4 + 1, i * 4 + 2, i * 4, i * 4 + 2, i * 4 + 3);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.BufferAttribute(col, 4));
  g.setIndex(idx);
  return g;
}

/** A soft ring of light, brightest at the tyre's edge: it gives the bars a glow to sit in. */
function haloTexture(): THREE.CanvasTexture {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const g = c.getContext('2d')!;
  const grad = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  grad.addColorStop(0, 'rgba(255,255,255,0)');
  grad.addColorStop(0.5, 'rgba(255,255,255,0)');
  grad.addColorStop(0.7, 'rgba(255,255,255,0.5)');
  grad.addColorStop(0.8, 'rgba(255,255,255,0.22)');
  grad.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

interface Light {
  corner: number;
  /** the hub group the light hangs on: a wheel design that is not showing has its own, hidden with it */
  hub: THREE.Object3D;
  ring: THREE.Mesh;
  halo: THREE.Mesh;
  radius: number;
  front: boolean;
  out: number;
}

/** A hub is on show when it and everything above it is visible. */
function shown(o: THREE.Object3D | null): boolean {
  for (let p = o; p; p = p.parent) if (!p.visible) return false;
  return true;
}

const tmp = new THREE.Vector3();
const outDir = new THREE.Vector3();
const toCam = new THREE.Vector3();
const quat = new THREE.Quaternion();

function Lights({ vehicle }: { vehicle: Vehicle }) {
  const rig = rigOf(vehicle);
  const tags = React.useRef<(HTMLDivElement | null)[]>([null, null, null, null]);
  const tagGroups = React.useRef<(THREE.Group | null)[]>([null, null, null, null]);

  const built = React.useMemo(() => {
    const wheels = rig.wheels;
    const layout = rig.layout;
    if (!wheels || !layout) return null;
    const tex = haloTexture();
    const lights: Light[] = [];
    const CORNER = { FL: 0, FR: 1, RL: 2, RR: 3 } as const;
    // every rim design has its own four hubs and only the one on show is visible: each hub wears its own lights
    for (const w of wheels) {
      const i = CORNER[w.corner];
      const radius = layout.radius[w.corner];
      const out = Math.sign(w.hub0.z) || (i % 2 === 0 ? -1 : 1);
      const ringMat = new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, depthWrite: false, side: THREE.DoubleSide, toneMapped: false });
      const ring = new THREE.Mesh(ringGeometry(radius * 0.99, radius * 1.13), ringMat);
      ring.position.z = out * radius * OUT;
      ring.renderOrder = 20;
      ring.frustumCulled = false;
      const haloMat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, toneMapped: false, color: 0x000000 });
      const halo = new THREE.Mesh(new THREE.PlaneGeometry(radius * 2.9, radius * 2.9), haloMat);
      halo.position.z = out * radius * (OUT - 0.04);
      halo.renderOrder = 19;
      halo.frustumCulled = false;
      lights.push({ corner: i, hub: w.steer, ring, halo, radius, front: i < 2, out });
    }
    return { lights, tex, steers: wheels };
  }, [rig]);

  // hang the lights on the hubs, and take them off when the exterior goes or the tab changes (the memo above only makes them: it
  // must stay pure, and development mounts twice; disposed geometry and materials are made again by three if they are drawn again)
  React.useEffect(() => {
    if (!built) return;
    for (const l of built.lights) l.hub.add(l.ring, l.halo);
    return () => {
      for (const l of built.lights) {
        l.hub.remove(l.ring, l.halo);
        l.ring.geometry.dispose();
        l.halo.geometry.dispose();
        (l.ring.material as THREE.Material).dispose();
        (l.halo.material as THREE.Material).dispose();
      }
      built.tex.dispose();
    };
  }, [built]);

  const memo = React.useRef<{ facts: unknown; duration: number; acts: ReturnType<typeof launchActs>; windows: ReturnType<typeof tagWindows> } | null>(null);
  const colour = React.useRef(new THREE.Color());
  const camera = useThree((st) => st.camera);

  useFrame(() => {
    const f = techSession.runtime?.launch?.drive;
    if (!f || !built) return;
    const t = techClock.t;
    const tel = f.telemetry(t);
    // read again when the run changes, or when the clock's length arrives after the run's facts
    if (!memo.current || memo.current.facts !== f || memo.current.duration !== techClock.duration) {
      const shape = runShape(f, techClock.duration);
      const acts = launchActs(f, shape.launch);
      memo.current = { facts: f, duration: techClock.duration, acts, windows: tagWindows(f, shape, acts) };
    }
    const { acts, windows } = memo.current;
    const look = wheelLook(f, tel, acts, t);
    const kw = wheelKw(f, tel);
    // the band goes round the way the wheel turns, and the faster the more energy has gone through
    const cycle = (tel.energyWh - tel.regenWh) / 38;

    for (const l of built.lights) {
      if (!shown(l.hub)) {
        l.ring.visible = l.halo.visible = false;
        continue;
      }
      const i = l.corner;
      // the colour: the motor's, turning green as it feeds the battery and red as the brakes work
      const c = colour.current;
      const base = l.front && f.motors.some((m) => m.axle === 'rear') ? CYAN : AMBER;
      c.copy(base);
      if (look.regen[i] > 0) c.lerp(GREEN, look.regen[i]);
      if (look.brake[i] > 0) c.lerp(RED, look.brake[i]);
      const intensity = look.lit[i] * (1 + 0.8 * look.kick);
      const phase = cycle * Math.PI * 2;
      const attr = l.ring.geometry.getAttribute('color') as THREE.BufferAttribute;
      for (let s = 0; s < SEGMENTS; s++) {
        const th = ((s + 0.5) / SEGMENTS) * Math.PI * 2;
        // the band: bright where cos is high, moving round with the energy
        const band = Math.pow(0.5 + 0.5 * Math.cos(th + phase), 3);
        // a lit ring is opaque colour: on the studio's pale floor a glow added to the picture would not show
        const a = clamp(intensity * (0.3 + 0.7 * band) * 1.5);
        for (let v = 0; v < 4; v++) attr.setXYZW(s * 4 + v, c.r, c.g, c.b, a);
      }
      attr.needsUpdate = true;
      (l.halo.material as THREE.MeshBasicMaterial).color.copy(c).multiplyScalar(Math.min(1, intensity) * 1.2);
      l.halo.visible = l.ring.visible = intensity > 0.004;
    }

    // the tags (one per corner)
    for (const l of built.lights.filter((x, k, all) => all.findIndex((y) => y.corner === x.corner) === k)) {
      const i = l.corner;
      const el = tags.current[i];
      const grp = tagGroups.current[i];
      if (!el || !grp) continue;
      const hub = built.steers.find((w) => ['FL', 'FR', 'RL', 'RR'][i] === w.corner && shown(w.steer));
      let facing = 1;
      if (hub) {
        hub.steer.getWorldPosition(tmp);
        grp.position.copy(tmp);
        // a tag stands over a wheel the camera can see: the far side's wheels are behind the car
        hub.steer.getWorldQuaternion(quat);
        outDir.set(0, 0, l.out).applyQuaternion(quat);
        toCam.copy(camera.position).sub(tmp).normalize();
        facing = clamp((toCam.dot(outDir) - 0.05) / 0.3);
      }
      let a = 0;
      let pop = 0;
      for (const w of windows[i]) {
        const p = presence(t, w.from, w.to, 0.3, SPRINGS.pop);
        if (p.visible) {
          a = Math.max(a, clamp(p.enter) * (1 - p.exit));
          pop = Math.max(pop, p.enter * (1 - p.exit));
        }
      }
      const regen = look.regen[i] > 0.5;
      const friction = look.brake[i] > 0.3;
      a *= facing;
      el.style.opacity = String(clamp(a));
      el.style.transform = `translateY(${(1 - EASE_OUT(clamp(a))) * 8}px) scale(${0.85 + 0.15 * pop})`;
      if (a > 0.01) {
        const dot = l.front && f.motors.some((m) => m.axle === 'rear') ? '#38bdf8' : '#fbbf24';
        const colourDot = friction ? '#ff4d4d' : regen ? '#34d399' : dot;
        const text = friction ? `${fmt(-tel.g, 2)} g · brake` : `${regen ? '−' : ''}${fmt(Math.abs(kw[i]))} kW`;
        if (el.dataset.text !== text) {
          el.dataset.text = text;
          el.lastElementChild!.textContent = text;
        }
        (el.firstElementChild as HTMLElement).style.background = colourDot;
      }
    }
  });

  if (!built) return null;
  return (
    <>
      {built.lights.filter((x, k, all) => all.findIndex((y) => y.corner === x.corner) === k).map((l) => (
        <group
          key={l.corner}
          ref={(g) => {
            tagGroups.current[l.corner] = g;
          }}
        >
          <Html center position={[0, l.radius * 1.25, l.out * l.radius * 0.9]} zIndexRange={[9, 0]} style={{ pointerEvents: 'none' }}>
            <div
              ref={(el) => {
                tags.current[l.corner] = el;
              }}
              style={{ opacity: 0 }}
              className="flex items-center gap-1.5 whitespace-nowrap rounded-full bg-neutral-950/80 px-2 py-0.5 text-[10px] font-medium text-white shadow-lg ring-1 ring-white/15 backdrop-blur-sm"
            >
              <span className="inline-block h-1.5 w-1.5 rounded-full" />
              <span className="tnum" />
            </div>
          </Html>
        </group>
      ))}
    </>
  );
}
