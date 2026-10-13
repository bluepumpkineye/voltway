'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import type { SensorSpec, Vehicle } from '@/data/vehicles/schema';
import { techClock } from '@/lib/tech/clock';
import { getLayers, subscribeLayers, type LayerId } from '@/lib/tech/layers';
import { rigOf } from '@/lib/tech/rig';
import { REACH, type SensorsState } from '@/lib/tech/sensors';
import { useRuntime, type Runtime } from '@/lib/tech/session';

/**
 * The sensor demo's scene (docs/tech-showcase.md section 12): the coverage each sensor group is drawn with, and the
 * pedestrian. Everything drawn here is an illustration, and the panel says so: no field of view is published, so the
 * cones' angles and the reach they are drawn to are ours; the solid-state lidars at the sides are drawn from the place
 * one source reports (the fender gill), and the rear one from where nothing says it is. The roof lidar's window, the
 * cameras and the ultrasonic sensors the photographs show are marked where the photographs put them.
 *
 * Mount once in the showroom's Canvas. It draws only while a sensor demo is on, and reads the demo's clock.
 */
export function TechSensors({ vehicle }: { vehicle: Vehicle }) {
  const runtime = useRuntime();
  const sensors = runtime?.sensors;
  const spec = vehicle.sensors;
  if (!sensors || !spec || !runtime) return null;
  return <Scene vehicle={vehicle} spec={spec} sensors={sensors} runtime={runtime} />;
}

type Sensors = NonNullable<Runtime['sensors']>;

const COLOR = {
  lidar: '#2f6bff',
  side: '#0fa594',
  rear: '#8b5cf6',
  ultrasonic: '#f59e0b',
  camera: '#ffffff',
} as const;

const DEG = Math.PI / 180;
/** the forward lidar's two light paths, the solid-state ones: angles are illustrative */
const FOV = { wide: 120 * DEG, tele: 26 * DEG, side: 110 * DEG, rear: 110 * DEG };
const FLOOR = 0.03;

/** the path of the car, half the width, m (the corridor the pedestrian must stay out of) */
const PATH_HALF = 1.15;

const STATE_COLOR: Record<SensorsState, string> = {
  scanning: '#ffffff',
  tracking: '#ffffff',
  risk: '#f59e0b',
  braking: '#ef4444',
  stopped: '#ef4444',
  clear: '#22c55e',
};

function Scene({ vehicle, spec, sensors, runtime }: { vehicle: Vehicle; spec: SensorSpec; sensors: Sensors; runtime: Runtime }) {
  const invalidate = useThree((s) => s.invalidate);
  React.useEffect(() => subscribeLayers(() => invalidate()), [invalidate]);
  const rig = rigOf(vehicle);
  const road = React.useRef<THREE.Group>(null);
  React.useEffect(() => {
    const g = road.current;
    if (!g) return;
    return rig.attachRoad(g, rig.rac.x);
  }, [rig]);
  const start = runtime.sample(0).x;
  const footprint = { xMin: start - runtime.body.rear, xMax: start + runtime.body.front, half: runtime.body.halfWidth };

  const mirrored = <T extends { at: [number, number, number]; mirror?: boolean }>(list: T[]) =>
    list.flatMap((s) => (s.mirror ? [s.at, [s.at[0], s.at[1], -s.at[2]] as [number, number, number]] : [s.at]));
  const [sx, sy, sz] = spec.sideLidar;

  return (
    <group>
      {/* the forward lidar: the wide path and the tele path, one unit */}
      <Fan layer="lidar" at={spec.lidar} yaw={0} range={REACH.wide} fov={FOV.wide} color={COLOR.lidar} alpha={0.2} hz={0.42} rings />
      <Fan layer="lidar" at={spec.lidar} yaw={0} range={REACH.tele} fov={FOV.tele} color={COLOR.lidar} alpha={0.18} hz={0.9} phase={1.3} />
      {/* the solid-state lidars: the sides, and the tail */}
      <Fan layer="side" at={[sx, sy, sz]} yaw={-90 * DEG} range={REACH.side} fov={FOV.side} color={COLOR.side} alpha={0.17} hz={0.5} />
      <Fan layer="side" at={[sx, sy, -sz]} yaw={90 * DEG} range={REACH.side} fov={FOV.side} color={COLOR.side} alpha={0.17} hz={0.5} phase={2} />
      <Fan layer="rear" at={spec.rearLidar} yaw={180 * DEG} range={REACH.rear} fov={FOV.rear} color={COLOR.rear} alpha={0.17} hz={0.5} phase={4} />

      <Pulses footprint={footprint} />
      <Corridor sensors={sensors} frontX={sensors.frontX} />

      {/* where the sensors are: filled, photographed; a ring, reported or not published */}
      <Marker layer="lidar" at={spec.lidar} color={COLOR.lidar} />
      <Marker layer="side" at={[sx, sy, sz]} color={COLOR.side} ring />
      <Marker layer="side" at={[sx, sy, -sz]} color={COLOR.side} ring />
      <Marker layer="rear" at={spec.rearLidar} color={COLOR.rear} ring />
      {mirrored(spec.cameras).map((p, i) => (
        <Marker key={`c${i}`} layer="cameras" at={p} color={COLOR.camera} small />
      ))}
      {mirrored(spec.ultrasonic).map((p, i) => (
        <Marker key={`u${i}`} layer="ultrasonic" at={p} color={COLOR.ultrasonic} small />
      ))}

      {/* the lane runs along the car's own centre line, and the road rolls under the car */}
      <group position-z={-rig.rac.y}>
        <group ref={road}>
          <Walker sensors={sensors} />
        </group>
      </group>
    </group>
  );
}

// ------------------------------------------------------------------ coverage

/** A flat sector on the floor, fading outward, in the group's own frame (+x ahead). */
function fanGeometry(range: number, fov: number, color: THREE.Color, alpha: number): THREE.BufferGeometry {
  const n = 40;
  const pos: number[] = [0, 0, 0];
  const col: number[] = [color.r, color.g, color.b, alpha];
  for (let i = 0; i <= n; i++) {
    const a = -fov / 2 + (fov * i) / n;
    pos.push(range * Math.cos(a), 0, range * Math.sin(a));
    col.push(color.r, color.g, color.b, alpha * 0.1);
  }
  const idx: number[] = [];
  for (let i = 0; i < n; i++) idx.push(0, i + 1, i + 2);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 4));
  g.setIndex(idx);
  return g;
}

/** The sector's outline: the two edges up to the sensor, the far arc and two range rings. */
function outlineGeometry(range: number, fov: number, height: number, rings: boolean): THREE.BufferGeometry {
  const pts: number[] = [];
  const seg = (a: THREE.Vector3, b: THREE.Vector3) => pts.push(a.x, a.y, a.z, b.x, b.y, b.z);
  const at = (r: number, a: number) => new THREE.Vector3(r * Math.cos(a), 0, r * Math.sin(a));
  const top = new THREE.Vector3(0, height, 0);
  seg(top, at(range, -fov / 2));
  seg(top, at(range, fov / 2));
  const arc = (r: number) => {
    const n = 32;
    for (let i = 0; i < n; i++) seg(at(r, -fov / 2 + (fov * i) / n), at(r, -fov / 2 + (fov * (i + 1)) / n));
  };
  arc(range);
  if (rings) {
    arc(range / 3);
    arc((2 * range) / 3);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
  return g;
}

/** A thin sector: the sweep of a scanning lidar. */
function sweepGeometry(range: number, color: THREE.Color): THREE.BufferGeometry {
  const half = 1.6 * DEG;
  const pos = [0, 0, 0, range * Math.cos(-half), 0, range * Math.sin(-half), range * Math.cos(half), 0, range * Math.sin(half)];
  const col = [color.r, color.g, color.b, 0.95, color.r, color.g, color.b, 0.25, color.r, color.g, color.b, 0.25];
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 4));
  return g;
}

function Fan({
  layer, at, yaw, range, fov, color, alpha, hz, phase = 0, rings = false,
}: {
  layer: LayerId;
  at: [number, number, number];
  yaw: number;
  range: number;
  fov: number;
  color: string;
  alpha: number;
  hz: number;
  phase?: number;
  rings?: boolean;
}) {
  const root = React.useRef<THREE.Group>(null);
  const sweep = React.useRef<THREE.Mesh>(null);
  const c = React.useMemo(() => new THREE.Color(color), [color]);
  const geo = React.useMemo(
    () => ({
      fan: fanGeometry(range, fov, c, alpha),
      lines: outlineGeometry(range, fov, at[1] - FLOOR, rings),
      sweep: sweepGeometry(range, c),
    }),
    [range, fov, c, alpha, at, rings],
  );
  React.useEffect(
    () => () => {
      geo.fan.dispose();
      geo.lines.dispose();
      geo.sweep.dispose();
    },
    [geo],
  );
  useFrame(() => {
    const g = root.current;
    if (!g) return;
    g.visible = getLayers()[layer];
    if (sweep.current) {
      // the beam goes to and fro across the sector
      const a = (fov / 2) * 0.94 * Math.sin(Math.PI * 2 * hz * techClock.t + phase);
      sweep.current.rotation.y = -a;
    }
  });
  return (
    <group ref={root} position={[at[0], FLOOR, at[2]]} rotation-y={yaw}>
      <mesh geometry={geo.fan} renderOrder={5}>
        <meshBasicMaterial vertexColors transparent depthWrite={false} side={THREE.DoubleSide} toneMapped={false} />
      </mesh>
      <mesh ref={sweep} geometry={geo.sweep} position-y={0.004} renderOrder={6}>
        <meshBasicMaterial vertexColors transparent depthWrite={false} side={THREE.DoubleSide} toneMapped={false} />
      </mesh>
      <lineSegments geometry={geo.lines} renderOrder={6}>
        <lineBasicMaterial color={color} transparent opacity={0.4} depthWrite={false} toneMapped={false} />
      </lineSegments>
    </group>
  );
}

// -------------------------------------------------------------- ultrasonic

/** The outline of the car's footprint grown by d (a rounded rectangle), as `n` points per quarter turn. */
function offsetPath(fp: { xMin: number; xMax: number; half: number }, d: number, n = 8): [number, number][] {
  const out: [number, number][] = [];
  const corners: [number, number, number][] = [
    [fp.xMax, -fp.half, -90],
    [fp.xMax, fp.half, 0],
    [fp.xMin, fp.half, 90],
    [fp.xMin, -fp.half, 180],
  ];
  for (const [cx, cz, a0] of corners) {
    for (let i = 0; i <= n; i++) {
      const a = (a0 + (90 * i) / n) * DEG;
      out.push([cx + d * Math.cos(a), cz + d * Math.sin(a)]);
    }
  }
  return out;
}

const PULSES = 3;

/** Rings that go out from the car's outline, the ultrasonic sensors' close range (the count of twelve is published). */
function Pulses({ footprint }: { footprint: { xMin: number; xMax: number; half: number } }) {
  const root = React.useRef<THREE.Group>(null);
  const meshes = React.useRef<(THREE.Mesh | null)[]>([]);
  const N = 4 * 9;
  const geos = React.useMemo(
    () =>
      Array.from({ length: PULSES }, () => {
        const g = new THREE.BufferGeometry();
        g.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(N * 2 * 3), 3));
        const idx: number[] = [];
        for (let i = 0; i < N; i++) {
          const a = i * 2;
          const b = ((i + 1) % N) * 2;
          idx.push(a, a + 1, b, a + 1, b + 1, b);
        }
        g.setIndex(idx);
        return g;
      }),
    [N],
  );
  React.useEffect(() => () => geos.forEach((g) => g.dispose()), [geos]);
  useFrame(() => {
    const g = root.current;
    if (!g) return;
    g.visible = getLayers().ultrasonic;
    if (!g.visible) return;
    geos.forEach((geo, k) => {
      const ph = (techClock.t * 0.7 + k / PULSES) % 1;
      const d = 0.12 + ph * REACH.ultrasonic;
      const inner = offsetPath(footprint, d - 0.022);
      const outer = offsetPath(footprint, d + 0.022);
      const pos = geo.getAttribute('position') as THREE.BufferAttribute;
      for (let i = 0; i < N; i++) {
        pos.setXYZ(i * 2, inner[i][0], 0, inner[i][1]);
        pos.setXYZ(i * 2 + 1, outer[i][0], 0, outer[i][1]);
      }
      pos.needsUpdate = true;
      geo.computeBoundingSphere();
      const m = meshes.current[k];
      if (m) (m.material as THREE.MeshBasicMaterial).opacity = 0.7 * (1 - ph) * Math.min(1, ph * 8);
    });
  });
  return (
    <group ref={root} position-y={FLOOR + 0.004}>
      {geos.map((geo, k) => (
        <mesh
          key={k}
          ref={(m) => {
            meshes.current[k] = m;
          }}
          geometry={geo}
          renderOrder={6}
          frustumCulled={false}
        >
          <meshBasicMaterial color={COLOR.ultrasonic} transparent depthWrite={false} side={THREE.DoubleSide} toneMapped={false} />
        </mesh>
      ))}
    </group>
  );
}

// ------------------------------------------------------------------ markers

const SPHERE = new THREE.SphereGeometry(1, 14, 10);
const RING = new THREE.TorusGeometry(1, 0.16, 8, 28);

/** Where a sensor is: a dot where a photograph shows it, a ring where it is reported or not published at all. */
function Marker({ layer, at, color, ring = false, small = false }: { layer: LayerId; at: [number, number, number]; color: string; ring?: boolean; small?: boolean }) {
  const root = React.useRef<THREE.Group>(null);
  useFrame(({ camera }) => {
    const g = root.current;
    if (!g) return;
    g.visible = getLayers()[layer];
    if (ring) g.quaternion.copy(camera.quaternion);
  });
  const r = small ? 0.02 : ring ? 0.07 : 0.045;
  return (
    <group ref={root} position={at}>
      <mesh geometry={ring ? RING : SPHERE} scale={r} renderOrder={8}>
        <meshBasicMaterial color={color} depthTest={false} transparent opacity={ring ? 0.95 : 1} toneMapped={false} />
      </mesh>
    </group>
  );
}

// --------------------------------------------------------------- the corridor

/** The strip of road the car is about to cover: it goes amber and red as the pedestrian comes into it. */
function Corridor({ sensors, frontX }: { sensors: Sensors; frontX: number }) {
  const mesh = React.useRef<THREE.Mesh>(null);
  useFrame(() => {
    const m = mesh.current;
    if (!m) return;
    const t = techClock.t;
    const r = sensors.readout(t);
    const length = Math.min(Math.max(r.gap, 0.5), 30);
    m.scale.set(length, 1, 1);
    m.position.x = frontX + length / 2;
    const mat = m.material as THREE.MeshBasicMaterial;
    const hot = r.state === 'risk' || r.state === 'braking' || (r.state === 'stopped' && r.inPath);
    mat.color.set(hot ? (r.state === 'risk' ? '#f59e0b' : '#ef4444') : '#ffffff');
    mat.opacity = hot ? 0.3 : r.state === 'clear' ? 0 : 0.08;
  });
  return (
    <mesh ref={mesh} rotation-x={-Math.PI / 2} position-y={0.02} renderOrder={4}>
      <planeGeometry args={[1, PATH_HALF * 2]} />
      <meshBasicMaterial color="#ffffff" transparent opacity={0.08} depthWrite={false} toneMapped={false} />
    </mesh>
  );
}

// -------------------------------------------------------------- the pedestrian

const JACKET = '#6d7f96';
const TROUSERS = '#363b46';
const SKIN = '#d6bfae';

/** points on the figure's surface (its own frame, rest pose) that the lidar's returns land on */
function bodyPoints(): Float32Array {
  const pts: number[] = [];
  let seed = 4242;
  const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
  const onCylinder = (cx: number, cy: number, cz: number, r: number, h: number, n: number, sy = 1, sz = 1) => {
    for (let i = 0; i < n; i++) {
      const a = rnd() * Math.PI * 2;
      pts.push(cx + r * Math.cos(a) * sy, cy + (rnd() - 0.5) * h, cz + r * Math.sin(a) * sz);
    }
  };
  onCylinder(0, 1.2, 0, 0.17, 0.5, 80, 1, 0.75);
  for (let i = 0; i < 34; i++) {
    const a = rnd() * Math.PI * 2;
    const b = Math.acos(2 * rnd() - 1);
    pts.push(0.115 * Math.sin(b) * Math.cos(a), 1.64 + 0.115 * Math.cos(b), 0.115 * Math.sin(b) * Math.sin(a));
  }
  for (const x of [-0.09, 0.09]) onCylinder(x, 0.5, 0, 0.07, 0.8, 24);
  for (const x of [-0.23, 0.23]) onCylinder(x, 1.2, 0, 0.05, 0.5, 14);
  return new Float32Array(pts);
}

/**
 * The pedestrian: a plain figure (capsules and a sphere, no face) that stands at the kerb, steps out and walks across.
 * It stands on the road's own group, so it comes toward the car as the road rolls; its sideways walk and its stride
 * are the plan's. The lidar's returns land on it as blue points once it is in the sensors' reach.
 */
function Walker({ sensors }: { sensors: Sensors }) {
  const root = React.useRef<THREE.Group>(null);
  const legs = React.useRef<(THREE.Group | null)[]>([]);
  const arms = React.useRef<(THREE.Group | null)[]>([]);
  const points = React.useRef<THREE.Points>(null);
  const bracket = React.useRef<THREE.LineSegments>(null);
  const cloud = React.useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(bodyPoints(), 3));
    return g;
  }, []);
  const box = React.useMemo(() => new THREE.EdgesGeometry(new THREE.BoxGeometry(0.8, 1.9, 0.62)), []);
  React.useEffect(
    () => () => {
      cloud.dispose();
      box.dispose();
    },
    [cloud, box],
  );

  useFrame(() => {
    const g = root.current;
    if (!g) return;
    const t = techClock.t;
    const p = sensors.pedestrian(t);
    const r = sensors.readout(t);
    g.position.set(sensors.pedX, 0, p.z);
    const swing = Math.sin(p.stride) * (p.walking ? 1 : 0);
    legs.current[0]?.rotation.set(swing * 0.5, 0, 0);
    legs.current[1]?.rotation.set(-swing * 0.5, 0, 0);
    arms.current[0]?.rotation.set(-swing * 0.42, 0, 0);
    arms.current[1]?.rotation.set(swing * 0.42, 0, 0);
    const seen = getLayers().lidar && p.ahead <= REACH.tele && p.ahead > -3;
    if (points.current) {
      points.current.visible = seen;
      const mat = points.current.material as THREE.PointsMaterial;
      // the returns shimmer with the sweeps
      mat.opacity = 0.6 + 0.4 * Math.abs(Math.sin(Math.PI * 2 * 0.9 * t));
      mat.size = p.ahead > REACH.wide ? 0.11 : 0.075;
    }
    if (bracket.current) {
      bracket.current.visible = seen;
      bracket.current.position.y = 0.95;
      (bracket.current.material as THREE.LineBasicMaterial).color.set(STATE_COLOR[r.state]);
    }
  });

  return (
    <group ref={root}>
      <mesh position-y={1.2} scale={[1, 1, 0.75]}>
        <capsuleGeometry args={[0.16, 0.42, 6, 14]} />
        <meshStandardMaterial color={JACKET} roughness={0.85} />
      </mesh>
      <mesh position-y={1.64}>
        <sphereGeometry args={[0.113, 16, 12]} />
        <meshStandardMaterial color={SKIN} roughness={0.8} />
      </mesh>
      {[-0.09, 0.09].map((x, i) => (
        <group key={x} ref={(o) => { legs.current[i] = o; }} position={[x, 0.92, 0]}>
          <mesh position-y={-0.42}>
            <capsuleGeometry args={[0.062, 0.66, 5, 10]} />
            <meshStandardMaterial color={TROUSERS} roughness={0.85} />
          </mesh>
        </group>
      ))}
      {[-0.23, 0.23].map((x, i) => (
        <group key={x} ref={(o) => { arms.current[i] = o; }} position={[x, 1.42, 0]}>
          <mesh position-y={-0.28}>
            <capsuleGeometry args={[0.045, 0.46, 5, 10]} />
            <meshStandardMaterial color={JACKET} roughness={0.85} />
          </mesh>
        </group>
      ))}
      <points ref={points} geometry={cloud} renderOrder={9}>
        <pointsMaterial color={COLOR.lidar} size={0.045} sizeAttenuation transparent depthTest={false} toneMapped={false} />
      </points>
      <lineSegments ref={bracket} geometry={box} renderOrder={9}>
        <lineBasicMaterial color="#ffffff" transparent opacity={0.95} depthTest={false} toneMapped={false} />
      </lineSegments>
    </group>
  );
}
