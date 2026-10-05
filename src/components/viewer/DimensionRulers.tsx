'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import type { Vehicle } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import type { CarFrame } from '@/lib/showroom/anchors';
import { STAGE_LAYER } from './StudioShowroom';

/**
 * Floor rulers for the Dimensions tab: length and wheelbase along the driver's
 * side, width across the nose, height at the nose, each with its published
 * figure. The figures come from the vehicle's data (the maker's numbers); the
 * lines are placed from the mesh the viewer measured. Labels are painted into
 * canvas textures with the page's own font, so they need no font file.
 *
 * Everything is on the stage layer: invisible to the mirror and to the
 * contact-shadow pass, so the rulers never reflect or cast.
 */

const INK = '#2b3038';
const LINE = 0.016;
const TICK = 0.46;
const LIFT = 0.012;

const mmText = (v: number) => `${Math.round(v).toLocaleString('en-US')} mm`;

type P2 = [number, number]; // x, z on the floor

function useLabel(caption: string, value: string) {
  const invalidate = useThree((s) => s.invalidate);
  const [tex] = React.useState(() => {
    const c = document.createElement('canvas');
    c.width = 640;
    c.height = 176;
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 8;
    return t;
  });
  React.useEffect(() => {
    const family = getComputedStyle(document.body).fontFamily || 'sans-serif';
    const paint = () => {
      const c = tex.image as HTMLCanvasElement;
      const g = c.getContext('2d')!;
      g.clearRect(0, 0, c.width, c.height);
      g.textAlign = 'center';
      g.fillStyle = '#6b7280';
      g.font = `500 36px ${family}`;
      g.fillText(caption.toUpperCase(), c.width / 2, 46);
      g.fillStyle = INK;
      g.font = `600 84px ${family}`;
      g.fillText(value, c.width / 2, 140);
      tex.needsUpdate = true;
      invalidate();
    };
    paint();
    void document.fonts?.ready.then(paint);
  }, [tex, caption, value, invalidate]);
  React.useEffect(() => () => tex.dispose(), [tex]);
  return tex;
}

const stage = (o: THREE.Object3D | null) => {
  o?.layers.set(STAGE_LAYER);
};

/** A line on the floor between two points, `LINE` wide. */
function Bar({ a, b, y = LIFT, opacity = 1 }: { a: P2; b: P2; y?: number; opacity?: number }) {
  const dx = b[0] - a[0];
  const dz = b[1] - a[1];
  const len = Math.hypot(dx, dz);
  return (
    <mesh
      ref={stage}
      position={[(a[0] + b[0]) / 2, y, (a[1] + b[1]) / 2]}
      rotation-y={Math.atan2(-dz, dx)}
      userData={{ base: opacity }}
    >
      <boxGeometry args={[len, 0.004, LINE]} />
      <meshBasicMaterial color={INK} transparent toneMapped={false} depthWrite={false} />
    </mesh>
  );
}

/** A dashed line on the floor: the extension lines from the car out to a ruler. */
function Dashes({ a, b }: { a: P2; b: P2 }) {
  const ref = React.useRef<THREE.InstancedMesh>(null);
  const dash = 0.12;
  const gap = 0.1;
  const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
  const n = Math.max(1, Math.floor(len / (dash + gap)));
  React.useLayoutEffect(() => {
    const m = ref.current;
    if (!m) return;
    const o = new THREE.Object3D();
    const ang = Math.atan2(-(b[1] - a[1]), b[0] - a[0]);
    for (let i = 0; i < n; i++) {
      const t = ((i + 0.5) * (dash + gap)) / len;
      o.position.set(a[0] + (b[0] - a[0]) * t, LIFT, a[1] + (b[1] - a[1]) * t);
      o.rotation.set(0, ang, 0);
      o.updateMatrix();
      m.setMatrixAt(i, o.matrix);
    }
    m.instanceMatrix.needsUpdate = true;
    m.layers.set(STAGE_LAYER);
  }, [a, b, n, len]);
  return (
    <instancedMesh ref={ref} args={[undefined, undefined, n]} userData={{ base: 0.5 }}>
      <boxGeometry args={[dash, 0.004, LINE * 0.7]} />
      <meshBasicMaterial color={INK} transparent toneMapped={false} depthWrite={false} />
    </instancedMesh>
  );
}

/** A ruler: the line, a tick at each end, and dashed lines out from the car. */
function Ruler({ a, b, ext }: { a: P2; b: P2; ext?: [P2, P2] }) {
  const dx = b[0] - a[0];
  const dz = b[1] - a[1];
  const len = Math.hypot(dx, dz) || 1;
  const px = ((-dz / len) * TICK) / 2;
  const pz = ((dx / len) * TICK) / 2;
  return (
    <>
      <Bar a={a} b={b} />
      <Bar a={[a[0] - px, a[1] - pz]} b={[a[0] + px, a[1] + pz]} />
      <Bar a={[b[0] - px, b[1] - pz]} b={[b[0] + px, b[1] + pz]} />
      {ext && (
        <>
          <Dashes a={ext[0]} b={a} />
          <Dashes a={ext[1]} b={b} />
        </>
      )}
    </>
  );
}

const LABEL_ASPECT = 176 / 640;

/** Text lying on the floor. `flip` reads from the driver's side, `turn` from ahead. */
function FloorLabel({ at, turn = 0, flip = false, caption, value }: {
  at: P2; turn?: number; flip?: boolean; caption: string; value: string;
}) {
  const tex = useLabel(caption, value);
  const w = 2.6;
  return (
    <group position={[at[0], LIFT + 0.002, at[1]]} rotation-y={turn}>
      <mesh ref={stage} rotation={[-Math.PI / 2, 0, flip ? Math.PI : 0]}>
        <planeGeometry args={[w, w * LABEL_ASPECT]} />
        <meshBasicMaterial map={tex} transparent toneMapped={false} depthWrite={false} />
      </mesh>
    </group>
  );
}

/** Text that always faces the camera: for the vertical (height) ruler. */
function SpriteLabel({ at, caption, value }: { at: [number, number, number]; caption: string; value: string }) {
  const tex = useLabel(caption, value);
  const w = 1.5;
  return (
    <sprite ref={stage} position={at} scale={[w, w * LABEL_ASPECT, 1]}>
      <spriteMaterial map={tex} transparent toneMapped={false} depthWrite={false} />
    </sprite>
  );
}

export function DimensionRulers({ vehicle, frame }: { vehicle: Vehicle; frame: CarFrame }) {
  const tab = useVehicleStore((s) => s.tab);
  const focus = useVehicleStore((s) => s.dimension);
  const invalidate = useThree((s) => s.invalidate);
  const group = React.useRef<THREE.Group>(null);
  const fade = React.useRef(0);
  const on = tab === 'dimensions';

  // fade the whole set in and out, asking for frames only while it moves
  useFrame((_, dt) => {
    const g = group.current;
    if (!g) return;
    const goal = on ? 1 : 0;
    const d = goal - fade.current;
    if (Math.abs(d) > 0.002) {
      fade.current += d * (1 - Math.exp(-dt * 7));
      invalidate();
    } else fade.current = goal;
    g.visible = fade.current > 0.01;
    if (!g.visible) return;
    g.traverse((o) => {
      const m = (o as THREE.Mesh).material as THREE.Material | undefined;
      if (m && 'opacity' in m) (m as THREE.MeshBasicMaterial).opacity = fade.current * ((o.userData.base as number) ?? 1);
    });
  });

  const d = vehicle.dimensions;
  const W = d.widthMm / 1000;
  const H = d.heightMm / 1000;
  const x1 = frame.xMax;
  const x0 = frame.xMin;
  const wheelX = frame.wheelFL?.[0] ?? x1 - 1;
  const wb = d.wheelbaseMm / 1000;
  const zWheelbase = -(W / 2 + 0.62);
  const zLength = -(W / 2 + 1.5);
  const xWidth = x1 + 0.6;
  const xHeight = x1 + 0.1;
  const zHeight = -(W / 2 + 0.55);

  return (
    <group ref={group} visible={false}>
      {focus === 'length' && (
        <>
          <Ruler a={[wheelX, zWheelbase]} b={[wheelX - wb, zWheelbase]} ext={[[wheelX, -W / 2], [wheelX - wb, -W / 2]]} />
          <FloorLabel at={[wheelX - wb / 2, zWheelbase - 0.5]} flip caption="Wheelbase" value={mmText(d.wheelbaseMm)} />
          <Ruler a={[x1, zLength]} b={[x0, zLength]} ext={[[x1, -W / 2], [x0, -W / 2]]} />
          <FloorLabel at={[(x0 + x1) / 2, zLength - 0.5]} flip caption="Length" value={mmText(d.lengthMm)} />
        </>
      )}
      {focus === 'width' && (
        <>
          <Ruler a={[xWidth, -W / 2]} b={[xWidth, W / 2]} ext={[[x1, -W / 2], [x1, W / 2]]} />
          {/* the text sits beside the end tick, level with the line, as on a drawing: below it, it is hidden by the controls */}
          <FloorLabel at={[xWidth, -(W / 2 + 1.15)]} turn={Math.PI / 2} caption="Width" value={mmText(d.widthMm)} />
        </>
      )}
      {focus === 'height' && (
        <>
          <mesh ref={stage} position={[xHeight, H / 2, zHeight]}>
            <boxGeometry args={[LINE, H, LINE]} />
            <meshBasicMaterial color={INK} transparent toneMapped={false} depthWrite={false} />
          </mesh>
          <Bar a={[xHeight, zHeight - TICK / 2]} b={[xHeight, zHeight + TICK / 2]} />
          <Bar a={[xHeight, zHeight - TICK / 2]} b={[xHeight, zHeight + TICK / 2]} y={H} />
          {/* out to the side, level with the middle of the ruler (the front view looks along -x, so its right is -z) */}
          <SpriteLabel at={[xHeight, H / 2, zHeight - 0.8]} caption="Height" value={mmText(d.heightMm)} />
        </>
      )}
    </group>
  );
}
