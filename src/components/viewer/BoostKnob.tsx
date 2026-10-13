'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import type { Vehicle } from '@/data/vehicles/schema';
import { pressBoost } from '@/lib/tech/actions';
import { techClock } from '@/lib/tech/clock';
import { useRuntime } from '@/lib/tech/session';
import { useVehicleStore } from '@/store/vehicle-store';

/**
 * The BOOST knob's light, in the BOOST demo (docs/tech-showcase.md section 13). The cabin's model has the knob (a satin black
 * cap in a chrome ring, on the steering wheel's lower right, where Autohome's photographs put it) but not its lit ring,
 * so a blue ring is laid over it while BOOST is on, as in the photograph of the button lit. Before the first press a
 * pale ring pulses over it, which is also the thing to press. Both face the camera: the camera sits at the seat and
 * can only turn its head. Mount once in the showroom's Canvas.
 */
export function BoostKnob({ vehicle }: { vehicle: Vehicle }) {
  const demo = useRuntime()?.demoId;
  const knob = vehicle.boost?.knob;
  const inside = useVehicleStore((s) => s.cameraMode === 'interior');
  if (demo !== 'boost' || !knob || !inside) return null;
  return <Knob at={knob} />;
}

const RING = new THREE.TorusGeometry(1, 0.075, 8, 40);
const PAD = new THREE.CircleGeometry(1, 20);

function Knob({ at }: { at: [number, number, number] }) {
  const root = React.useRef<THREE.Group>(null);
  const lit = React.useRef<THREE.Mesh>(null);
  const halo = React.useRef<THREE.Mesh>(null);
  const hint = React.useRef<THREE.Mesh>(null);
  const glow = React.useRef(0);
  const invalidate = useThree((s) => s.invalidate);
  React.useEffect(() => useVehicleStore.subscribe((s, p) => s.boostOn !== p.boostOn && invalidate()), [invalidate]);

  useFrame(({ camera }, dt) => {
    const g = root.current;
    if (!g) return;
    g.quaternion.copy(camera.quaternion);
    const on = useVehicleStore.getState().boostOn;
    const goal = on ? 1 : 0;
    const d = goal - glow.current;
    if (Math.abs(d) > 0.003) {
      glow.current += d * (1 - Math.exp(-Math.min(dt, 0.1) * 9));
      invalidate();
    } else glow.current = goal;
    const pulse = 0.5 + 0.5 * Math.sin(techClock.t * 6);
    if (lit.current) (lit.current.material as THREE.MeshBasicMaterial).opacity = glow.current * (0.8 + 0.2 * pulse);
    if (halo.current) (halo.current.material as THREE.MeshBasicMaterial).opacity = glow.current * (0.2 + 0.25 * pulse);
    if (hint.current) {
      // before the first press the ring invites it; once BOOST has been on it stays quiet
      const waiting = techClock.t < 0.9 && !techClock.playing;
      hint.current.visible = waiting;
      hint.current.scale.setScalar(0.0215 * (1 + 0.12 * pulse));
      if (waiting) invalidate();
    }
  });

  return (
    <group ref={root} position={at}>
      <mesh ref={lit} geometry={RING} scale={0.0165} renderOrder={10}>
        <meshBasicMaterial color="#4a74ff" transparent opacity={0} depthTest={false} toneMapped={false} />
      </mesh>
      <mesh ref={halo} geometry={RING} scale={0.0205} renderOrder={10}>
        <meshBasicMaterial color="#6f93ff" transparent opacity={0} depthTest={false} toneMapped={false} />
      </mesh>
      <mesh ref={hint} geometry={RING} scale={0.0215} renderOrder={10}>
        <meshBasicMaterial color="#ffffff" transparent opacity={0.9} depthTest={false} toneMapped={false} />
      </mesh>
      {/* the thing to press: a pad over the knob, drawn with nothing */}
      <mesh
        geometry={PAD}
        scale={0.026}
        onClick={(e) => {
          e.stopPropagation();
          pressBoost();
        }}
        onPointerOver={() => (document.body.style.cursor = 'pointer')}
        onPointerOut={() => (document.body.style.cursor = '')}
      >
        <meshBasicMaterial transparent opacity={0} depthWrite={false} depthTest={false} />
      </mesh>
    </group>
  );
}
