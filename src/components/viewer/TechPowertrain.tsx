'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import type { Vehicle } from '@/data/vehicles/schema';
import { techClock } from '@/lib/tech/clock';
import { rigOf } from '@/lib/tech/rig';
import { techSession, useRuntime } from '@/lib/tech/session';
import { useVehicleStore } from '@/store/vehicle-store';
import { CarFollower } from './techRig';

/**
 * The Drive tab's X-ray camera: a schematic of what drives the car, drawn under the see-through body and riding with it. A flat
 * battery between the axles, a motor at each place the car has one (from the variant's layout: one at the front, one at the back,
 * two at the back), and the energy flowing between them as dots: out of the battery under power, back into it under the brakes.
 * The lights follow the run's own readout (src/lib/tech/drive-run.ts), so it is as true as the readout is.
 *
 * A schematic, said so on the panel: the maker publishes no layout of its packs and motors that this follows. The size and the
 * place of each part come from the wheelbase and the track measured off the model, nothing else.
 */
export function TechPowertrain({ vehicle }: { vehicle: Vehicle }) {
  const on = useVehicleStore((s) => s.tab === 'drive' && s.drive.cam === 'xray');
  if (!on) return null;
  return (
    <CarFollower vehicle={vehicle}>
      <Parts vehicle={vehicle} />
    </CarFollower>
  );
}

const AMBER = new THREE.Color('#f59e0b');
const GREEN = new THREE.Color('#10b981');
const FLOW_N = 9;

function cellTexture(): THREE.CanvasTexture {
  const c = document.createElement('canvas');
  c.width = 512;
  c.height = 256;
  const g = c.getContext('2d')!;
  g.fillStyle = '#222a35';
  g.fillRect(0, 0, c.width, c.height);
  g.strokeStyle = 'rgba(255,255,255,0.28)';
  g.lineWidth = 3;
  for (let i = 0; i <= 8; i++) {
    g.beginPath();
    g.moveTo((i * c.width) / 8, 0);
    g.lineTo((i * c.width) / 8, c.height);
    g.stroke();
  }
  for (let j = 0; j <= 4; j++) {
    g.beginPath();
    g.moveTo(0, (j * c.height) / 4);
    g.lineTo(c.width, (j * c.height) / 4);
    g.stroke();
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

interface MotorPart {
  id: string;
  mesh: THREE.Mesh;
  mat: THREE.MeshStandardMaterial;
  points: THREE.Points;
  from: THREE.Vector3;
  to: THREE.Vector3;
}

function Parts({ vehicle }: { vehicle: Vehicle }) {
  const rig = rigOf(vehicle);
  const ready = React.useSyncExternalStore(rig.subscribe, () => rig.ready, () => false);
  const group = React.useRef<THREE.Group>(null);

  // the facts of the run say which motors the car has; the layout says where its axles are
  const motors = useRuntime()?.launch?.drive?.motors;

  const built = React.useMemo(() => {
    const layout = ready ? rig.layout : null;
    if (!layout || !motors) return null;
    const { rac } = rig;
    const L = layout.wheelbase;
    const r0 = layout.radius.RL;
    const half = Math.abs(layout.wheels.FL.y - layout.wheels.FR.y) / 2;
    const zc = -rac.y;
    const bLen = Math.max(L - 0.7, 1);
    const bWid = Math.max(half * 2 - 0.4, 0.9);
    const bY = r0 * 0.6;

    const root = new THREE.Group();
    const tex = cellTexture();
    tex.repeat.set(1, 1);
    // drawn over the body and the cabin (no depth test): an X-ray sees through them to the parts under the floor
    const over = { depthTest: false, depthWrite: false, transparent: true } as const;
    const bMat = new THREE.MeshStandardMaterial({ color: '#2a323e', map: tex, roughness: 0.55, metalness: 0.25, emissive: AMBER, emissiveIntensity: 0, opacity: 0.85, ...over });
    const side = new THREE.MeshStandardMaterial({ color: '#1b212b', roughness: 0.6, metalness: 0.3, opacity: 0.85, ...over });
    const battery = new THREE.Mesh(new THREE.BoxGeometry(bLen, 0.12, bWid), [side, side, bMat, side, side, side]);
    battery.position.set(rac.x + L / 2, bY, zc);
    battery.renderOrder = 10;
    root.add(battery);

    const axleMat = new THREE.MeshStandardMaterial({ color: '#8b95a3', roughness: 0.5, metalness: 0.6, opacity: 0.9, ...over });
    const tracks: [number, number][] = [
      [rac.x, 0],
      [rac.x + L, 0],
    ];
    for (const [ax] of tracks) {
      const bar = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, half * 2 - 0.15, 10), axleMat);
      bar.rotation.x = Math.PI / 2;
      bar.position.set(ax, r0, zc);
      bar.renderOrder = 11;
      root.add(bar);
    }

    const out: MotorPart[] = [];
    for (const m of motors) {
      const x = m.axle === 'front' ? rac.x + L : rac.x;
      const sideZ = m.side === 'left' ? zc - half * 0.5 : m.side === 'right' ? zc + half * 0.5 : zc;
      const len = m.side ? 0.22 : Math.min(0.46, half * 0.45);
      const mat = new THREE.MeshStandardMaterial({ color: '#3b4452', roughness: 0.4, metalness: 0.55, emissive: AMBER, emissiveIntensity: 0, opacity: 0.92, ...over });
      const mesh = new THREE.Mesh(new THREE.CylinderGeometry(m.side ? 0.115 : 0.14, m.side ? 0.115 : 0.14, len, 24), mat);
      mesh.rotation.x = Math.PI / 2;
      mesh.position.set(x, r0, sideZ);
      mesh.renderOrder = 12;
      root.add(mesh);
      // the dots run from the battery's nearest edge to the motor
      const from = new THREE.Vector3(m.axle === 'front' ? rac.x + L / 2 + bLen / 2 - 0.05 : rac.x + L / 2 - bLen / 2 + 0.05, bY + 0.07, sideZ);
      const to = new THREE.Vector3(x, r0 + 0.14, sideZ);
      const pos = new Float32Array(FLOW_N * 3);
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
      const points = new THREE.Points(geo, new THREE.PointsMaterial({ size: 0.075, color: AMBER, transparent: true, opacity: 0.95, depthWrite: false, depthTest: false, toneMapped: false }));
      points.frustumCulled = false;
      points.renderOrder = 13;
      root.add(points);
      out.push({ id: m.id, mesh, mat, points, from, to });
    }
    return { root, battery: bMat, parts: out };
  }, [rig, ready, motors]);

  React.useEffect(() => {
    const g = group.current;
    if (!g || !built) return;
    g.add(built.root);
    return () => {
      g.remove(built.root);
      built.root.traverse((o) => {
        const mesh = o as THREE.Mesh;
        if (mesh.geometry) mesh.geometry.dispose();
      });
    };
  }, [built]);

  useFrame(() => {
    const f = techSession.runtime?.launch?.drive;
    if (!f || !built) return;
    const tel = f.telemetry(techClock.t);
    const peak = Math.max(f.modePeakKw, 1);
    const regen = tel.powerKw < 0;
    const col = regen ? GREEN : AMBER;
    const level = Math.min(1, Math.abs(tel.powerKw) / peak);
    built.battery.emissive.copy(col);
    built.battery.emissiveIntensity = 0.06 + 0.8 * level;
    // how far the dots have flowed: the energy that has passed, so a scrub or a pause puts them where they were
    const cycle = (tel.energyWh + tel.regenWh) / 80;
    f.motors.forEach((m, j) => {
      const part = built.parts.find((x) => x.id === m.id);
      if (!part) return;
      const kw = tel.motorKw[j];
      const own = Math.min(1, kw / (peak * 0.55));
      part.mat.emissive.copy(col);
      part.mat.emissiveIntensity = 0.05 + 1.4 * own;
      const attr = part.points.geometry.getAttribute('position') as THREE.BufferAttribute;
      for (let i = 0; i < FLOW_N; i++) {
        const u = (((cycle + i / FLOW_N) % 1) + 1) % 1;
        const t = regen ? 1 - u : u;
        attr.setXYZ(i, part.from.x + (part.to.x - part.from.x) * t, part.from.y + (part.to.y - part.from.y) * t, part.from.z + (part.to.z - part.from.z) * t);
      }
      attr.needsUpdate = true;
      const pm = part.points.material as THREE.PointsMaterial;
      pm.color.copy(col);
      pm.opacity = 0.15 + 0.85 * Math.min(1, own * 1.5);
    });
  });

  return <group ref={group} />;
}
