'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import type { CitySignal, SignalState } from '@/lib/tech/carpet';
import { techClock } from '@/lib/tech/clock';
import { getLayers } from '@/lib/tech/layers';
import { techSession } from '@/lib/tech/session';
import { STAGE_LAYER } from './StudioShowroom';

/**
 * A traffic signal for the street of Autonomous Drive's city scenes (src/lib/tech/scenes/trafficlight.ts): a mast on the footway with
 * an arm over the carriageway and a head over each lane, facing the car as it comes. The lamp that is lit is the signal's state at the
 * clock's time. While the car has the signal (the signal's `reach` from the car's nose to the mast) the sensors' corner marks stand
 * round the head over the car's lane: white for green, amber for amber and red. Road coordinates are the planner's (x along, y left);
 * the viewer's z is -y. It rolls with the road (TechCity puts it in the rolling group).
 */

const LAMP_ON: Record<SignalState, THREE.Color> = {
  red: new THREE.Color('#ff3b30'),
  amber: new THREE.Color('#ffb41f'),
  green: new THREE.Color('#34d27b'),
};
const LAMP_OFF = new THREE.Color('#252830');
const ORDER: SignalState[] = ['red', 'amber', 'green'];
const KERB = 0.15;
const HEAD_Y = 5.3;
const ARM_Y = 6.05;

function onStageLayer(o: THREE.Object3D | null) {
  o?.layers.set(STAGE_LAYER);
}

/** The ticks at the four corners of a rectangle in the plane across the street. */
function bracketGeometry(w: number, h: number, leg: number): THREE.BufferGeometry {
  const p: number[] = [];
  const seg = (ax: number, ay: number, bx: number, by: number) => p.push(0, ay, ax, 0, by, bx);
  for (const sx of [-1, 1]) {
    for (const sy of [-1, 1]) {
      const cx = (sx * w) / 2;
      const cy = (sy * h) / 2;
      seg(cx, cy, cx - sx * leg, cy);
      seg(cx, cy, cx, cy - sy * leg);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3));
  return g;
}

export function Signal({ signal }: { signal: CitySignal }) {
  const lamps = React.useRef<(THREE.Mesh | null)[]>([]);
  const glows = React.useRef<(THREE.Mesh | null)[]>([]);
  const marks = React.useRef<THREE.LineSegments | null>(null);
  const shown = React.useRef('');
  const markGeo = React.useMemo(() => bracketGeometry(0.78, 1.5, 0.24), []);
  React.useEffect(() => () => markGeo.dispose(), [markGeo]);
  const across = Math.max(...signal.heads);
  const armLen = Math.abs(across - signal.pole) + 0.45;
  const armMid = (signal.pole + across - 0.45) / 2;
  const hang = ARM_Y - HEAD_Y - 0.52;

  useFrame(() => {
    const t = techClock.t;
    const st = signal.state(t);
    signal.heads.forEach((_, h) => {
      ORDER.forEach((k, j) => {
        const on = k === st;
        const lamp = lamps.current[h * 3 + j];
        if (lamp) (lamp.material as THREE.MeshBasicMaterial).color.copy(on ? LAMP_ON[k] : LAMP_OFF);
        const glow = glows.current[h * 3 + j];
        if (glow) glow.visible = on;
      });
    });
    const m = marks.current;
    if (m) {
      const sensors = techSession.runtime?.sensors;
      const layers = getLayers();
      const ego = sensors?.ego(t);
      const d = ego && sensors ? signal.x - (ego.x + sensors.egoLength / 2) : Infinity;
      const seen = Boolean((layers.lidar || layers.vision) && d < signal.reach && d > -4);
      m.visible = seen;
      if (seen && st !== shown.current) {
        (m.material as THREE.LineBasicMaterial).color.set(st === 'green' ? '#ffffff' : '#f59e0b');
        shown.current = st;
      }
    }
  });

  const steel = '#9aa0a9';
  const housing = '#33373f';
  return (
    <group position={[signal.x, KERB, 0]}>
      <mesh position={[0, 3.1, -signal.pole]} ref={onStageLayer}>
        <cylinderGeometry args={[0.06, 0.085, 6.2, 12]} />
        <meshStandardMaterial color={steel} roughness={0.7} />
      </mesh>
      <mesh position={[0, ARM_Y, -armMid]} ref={onStageLayer}>
        <boxGeometry args={[0.12, 0.13, armLen]} />
        <meshStandardMaterial color={steel} roughness={0.7} />
      </mesh>
      {signal.heads.map((hy, h) => (
        <group key={h} position={[0, 0, -hy]}>
          <mesh position={[0.02, HEAD_Y + 0.52 + hang / 2, 0]} ref={onStageLayer}>
            <boxGeometry args={[0.07, hang, 0.07]} />
            <meshStandardMaterial color={steel} roughness={0.7} />
          </mesh>
          <mesh position={[0, HEAD_Y, 0]} ref={onStageLayer}>
            <boxGeometry args={[0.3, 1.04, 0.38]} />
            <meshStandardMaterial color={housing} roughness={0.55} />
          </mesh>
          {[0.31, 0, -0.31].map((dy, j) => (
            <group key={j} position={[-0.156, HEAD_Y + dy, 0]} rotation-y={-Math.PI / 2}>
              <mesh
                ref={(o) => {
                  lamps.current[h * 3 + j] = o;
                  onStageLayer(o);
                }}
              >
                <circleGeometry args={[0.115, 28]} />
                <meshBasicMaterial color={LAMP_OFF} toneMapped={false} />
              </mesh>
              <mesh
                position-z={0.004}
                visible={false}
                ref={(o) => {
                  glows.current[h * 3 + j] = o;
                  onStageLayer(o);
                }}
              >
                <circleGeometry args={[0.27, 28]} />
                <meshBasicMaterial color={LAMP_ON[ORDER[j]]} transparent opacity={0.2} blending={THREE.AdditiveBlending} depthWrite={false} toneMapped={false} />
              </mesh>
            </group>
          ))}
          {h === 0 && (
            <lineSegments
              ref={(o) => {
                marks.current = o;
                onStageLayer(o);
              }}
              geometry={markGeo}
              position={[-0.34, HEAD_Y, 0]}
              visible={false}
              renderOrder={7}
            >
              <lineBasicMaterial color="#ffffff" transparent opacity={0.9} depthWrite={false} toneMapped={false} />
            </lineSegments>
          )}
        </group>
      ))}
    </group>
  );
}
