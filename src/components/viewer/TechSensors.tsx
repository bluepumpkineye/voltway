'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import { getVehicle } from '@/data/vehicles';
import type { SensorSpec, Vehicle } from '@/data/vehicles/schema';
import { techClock } from '@/lib/tech/clock';
import { getLayers, subscribeLayers, type LayerId } from '@/lib/tech/layers';
import { rigOf } from '@/lib/tech/rig';
import { LANE, REACH, type Track, type TrafficCar } from '@/lib/tech/sensors';
import { useRuntime, type Runtime } from '@/lib/tech/session';
import { GroundShadow } from './StudioShowroom';
import { useStandIn } from './TechStage';

/**
 * Autonomous Drive's scene (docs/tech-showcase.md section 12): the coverage each sensor group is drawn with, the other
 * cars on the three lanes, and what the sensors make of them. Everything drawn here is an illustration, and the panel
 * says so: no field of view is published except the SU7's lidar (Hesai's 120 degrees), so the cones' angles and the reach
 * they are drawn to are ours; the RX's solid-state lidars at the sides are drawn from the place one source reports (the
 * fender gill), and the rear one from where nothing says it is. The roof lidar's window, the cameras and the ultrasonic
 * sensors the photographs show are marked where the photographs put them.
 *
 * The coverage is a child of the rig's root, so it goes with the car through its lane change; the traffic is in the road's
 * frame (the rig rolls it under the car like the humps of the Magic Carpet). Mount once in the showroom's Canvas. It
 * draws only while a sensor demo is on, and reads the demo's clock.
 */
export function TechSensors({ vehicle }: { vehicle: Vehicle }) {
  const runtime = useRuntime();
  const sensors = runtime?.sensors;
  const spec = vehicle.sensors;
  if (!sensors || !spec || !runtime) return null;
  return <Scene vehicle={vehicle} spec={spec} sensors={sensors} runtime={runtime} />;
}

type Scenario = NonNullable<Runtime['sensors']>;

const COLOR = {
  lidar: '#2f6bff',
  side: '#0fa594',
  rear: '#8b5cf6',
  surround: '#38a8ff',
  ultrasonic: '#f59e0b',
  camera: '#ffffff',
} as const;

const DEG = Math.PI / 180;
/** the RX's forward lidar's two light paths, and the solid-state ones: angles are illustrative */
const FOV = { wide: 120 * DEG, tele: 26 * DEG, side: 110 * DEG, rear: 110 * DEG, surround: 26 * DEG };
const FLOOR = 0.03;

/** the paint of the other cars: mid greys, as Xiaomi's animation draws them, so the car in the demo stays the one the eye follows */
const TRAFFIC_TONES = ['#5f656f', '#80868f', '#454a53', '#6f757e', '#8e949c', '#565c66'];

/** the colours of what the sensors make of a car */
const TRACK_COLOR: Record<Exclude<Track, 'out'>, string> = { tracked: '#ffffff', lead: '#7fd0ff', warn: '#f59e0b' };

function Scene({ vehicle, spec, sensors, runtime }: { vehicle: Vehicle; spec: SensorSpec; sensors: Scenario; runtime: Runtime }) {
  const invalidate = useThree((s) => s.invalidate);
  React.useEffect(() => subscribeLayers(() => invalidate()), [invalidate]);
  const rig = rigOf(vehicle);
  const road = React.useRef<THREE.Group>(null);
  React.useEffect(() => {
    const g = road.current;
    if (!g) return;
    return rig.attachRoad(g, rig.rac.x);
  }, [rig]);

  return (
    <group>
      <CarCoverage vehicle={vehicle} spec={spec} runtime={runtime} />
      {/* the lanes run along the car's own centre line at the start, and the road rolls under the car */}
      <group position-z={-rig.rac.y}>
        <group ref={road}>
          <LaneStrip sensors={sensors} />
          <LeadLink sensors={sensors} />
          {sensors.traffic.map((c, i) => (
            <React.Suspense key={c.id} fallback={null}>
              <Traffic car={c} tone={TRAFFIC_TONES[i % TRAFFIC_TONES.length]} />
            </React.Suspense>
          ))}
        </group>
      </group>
    </group>
  );
}

/**
 * Where the car's sensors look, drawn on the floor round the car: every group the car has, or only the groups `parts` names
 * (the parking assist draws the surround beams, the ultrasonic pulses and the camera dots, not the lidar). It is a child of the
 * rig's root, in the model's space, so it goes with the car wherever the demo takes it.
 */
export function CarCoverage({
  vehicle, spec, runtime, parts, surroundReach = REACH.surround,
}: {
  vehicle: Vehicle;
  spec: SensorSpec;
  runtime: Runtime;
  parts?: LayerId[];
  /** how far the surround beams are drawn, m (a car park wants them short) */
  surroundReach?: number;
}) {
  const rig = rigOf(vehicle);
  const car = React.useRef<THREE.Group>(null);
  React.useEffect(() => {
    const g = car.current;
    if (!g) return;
    // the coverage is drawn in the model's space and rides on the car's place on the floor
    return rig.attachRoot(g);
  }, [rig]);
  // the coverage is in the model's space, where the car stands at rest: the rear axle's middle there, not where a demo starts it
  const { rac } = rig;
  const footprint = { xMin: rac.x - runtime.body.rear, xMax: rac.x + runtime.body.front, half: runtime.body.halfWidth };
  const middle = React.useMemo<[number, number, number]>(
    () => [rac.x + (runtime.body.front - runtime.body.rear) / 2, 0, -rac.y],
    [rac.x, rac.y, runtime.body.front, runtime.body.rear],
  );
  const surroundAt = React.useMemo<[number, number, number]>(() => [middle[0], 0.7, middle[2]], [middle]);
  const side = spec.sideLidar;
  const sideOther = React.useMemo<[number, number, number] | null>(() => (side ? [side[0], side[1], -side[2]] : null), [side]);
  const tail = spec.rearLidar;
  const has = (id: LayerId) => !parts || parts.includes(id);
  // a car shown with a fixed set of groups (the parking assist) has no switches to turn them off
  const sw = (id: LayerId): LayerId | null => (parts ? null : id);

  const mirrored = <T extends { at: [number, number, number]; mirror?: boolean }>(list: T[]) =>
    list.flatMap((s) => (s.mirror ? [s.at, [s.at[0], s.at[1], -s.at[2]] as [number, number, number]] : [s.at]));

  return (
    <group ref={car}>
      {/* the forward lidar: the RX's wide path and tele path, one unit; where the maker publishes a field of view, that one */}
      {has('lidar') &&
        (spec.lidarFov ? (
          <Fan layer={sw('lidar')} at={spec.lidar} yaw={0} range={REACH.wide * 1.3} fov={spec.lidarFov * DEG} color={COLOR.lidar} alpha={0.2} hz={0.5} rings />
        ) : (
          <>
            <Fan layer={sw('lidar')} at={spec.lidar} yaw={0} range={REACH.wide} fov={FOV.wide} color={COLOR.lidar} alpha={0.2} hz={0.42} rings />
            <Fan layer={sw('lidar')} at={spec.lidar} yaw={0} range={REACH.tele} fov={FOV.tele} color={COLOR.lidar} alpha={0.18} hz={0.9} phase={1.3} />
          </>
        ))}
      {/* the solid-state lidars: the sides, and the tail */}
      {has('side') && side && sideOther && (
        <>
          <Fan layer={sw('side')} at={side} yaw={-90 * DEG} range={REACH.side} fov={FOV.side} color={COLOR.side} alpha={0.17} hz={0.5} />
          <Fan layer={sw('side')} at={sideOther} yaw={90 * DEG} range={REACH.side} fov={FOV.side} color={COLOR.side} alpha={0.17} hz={0.5} phase={2} />
        </>
      )}
      {has('rear') && tail && <Fan layer={sw('rear')} at={tail} yaw={180 * DEG} range={REACH.rear} fov={FOV.rear} color={COLOR.rear} alpha={0.17} hz={0.5} phase={4} />}
      {/* the surround cameras: four diagonal beams from the middle of the car, as the maker's own animation draws them */}
      {has('surround') &&
        spec.surround &&
        [-40, 40, -140, 140].map((deg) => (
          <Fan key={deg} layer={sw('surround')} at={surroundAt} yaw={deg * DEG} range={surroundReach} fov={FOV.surround} color={COLOR.surround} alpha={0.2} hz={0} />
        ))}

      {has('lidar') && <ScanRing at={middle} layer={sw('lidar')} />}
      {has('ultrasonic') && <Pulses footprint={footprint} layer={sw('ultrasonic')} />}

      {/* where the sensors are: filled, photographed; a ring, reported or not published */}
      {has('lidar') && <Marker layer={sw('lidar')} at={spec.lidar} color={COLOR.lidar} />}
      {has('side') && side && sideOther && (
        <>
          <Marker layer={sw('side')} at={side} color={COLOR.side} ring />
          <Marker layer={sw('side')} at={sideOther} color={COLOR.side} ring />
        </>
      )}
      {has('rear') && tail && <Marker layer={sw('rear')} at={tail} color={COLOR.rear} ring />}
      {has('cameras') &&
        mirrored(spec.cameras).map((p, i) => <Marker key={`c${i}`} layer={sw('cameras')} at={p} color={COLOR.camera} small />)}
      {has('ultrasonic') &&
        mirrored(spec.ultrasonic).map((p, i) => <Marker key={`u${i}`} layer={sw('ultrasonic')} at={p} color={COLOR.ultrasonic} small />)}
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
  /** the switch that shows it; null for one that is always drawn */
  layer: LayerId | null;
  at: [number, number, number];
  yaw: number;
  range: number;
  fov: number;
  color: string;
  alpha: number;
  /** how often the beam goes to and fro across the sector; 0 for a beam that does not sweep */
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
      lines: outlineGeometry(range, fov, Math.max(at[1] - FLOOR, 0), rings),
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
    g.visible = layer ? getLayers()[layer] : true;
    if (sweep.current && hz > 0) {
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
      {hz > 0 && (
        <mesh ref={sweep} geometry={geo.sweep} position-y={0.004} renderOrder={6}>
          <meshBasicMaterial vertexColors transparent depthWrite={false} side={THREE.DoubleSide} toneMapped={false} />
        </mesh>
      )}
      <lineSegments geometry={geo.lines} renderOrder={6}>
        <lineBasicMaterial color={color} transparent opacity={0.4} depthWrite={false} toneMapped={false} />
      </lineSegments>
    </group>
  );
}

// ---------------------------------------------------------------- scan ring

const SCAN_PERIOD = 3.4;

/** A polar grid on a transparent square: rings at quarters of the radius and a spoke every fifteen degrees. */
function gridTexture(): THREE.CanvasTexture {
  const S = 512;
  const c = document.createElement('canvas');
  c.width = c.height = S;
  const ctx = c.getContext('2d')!;
  const R = S / 2 - 2;
  ctx.translate(S / 2, S / 2);
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 1.6;
  for (const f of [0.25, 0.5, 0.75, 1]) {
    ctx.globalAlpha = f === 1 ? 0.9 : 0.45;
    ctx.beginPath();
    ctx.arc(0, 0, R * f, 0, Math.PI * 2);
    ctx.stroke();
  }
  ctx.globalAlpha = 0.35;
  for (let a = 0; a < 24; a++) {
    const th = (a * Math.PI * 2) / 24;
    ctx.beginPath();
    ctx.moveTo(Math.cos(th) * R * 0.08, Math.sin(th) * R * 0.08);
    ctx.lineTo(Math.cos(th) * R, Math.sin(th) * R);
    ctx.stroke();
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4;
  return t;
}

/**
 * The detection ring of Xiaomi's own animation: a wave that goes out from the car over a polar grid and fades, now and
 * again. It stands for the sensors' reach all round the car (drawn to REACH.scan: the real reach is longer), so it follows
 * the lidar's switch.
 */
function ScanRing({ at, layer }: { at: [number, number, number]; layer: LayerId | null }) {
  const groups = React.useRef<(THREE.Group | null)[]>([]);
  const mats = React.useRef<{ grid: THREE.MeshBasicMaterial | null; ring: THREE.MeshBasicMaterial | null }[]>([
    { grid: null, ring: null },
    { grid: null, ring: null },
  ]);
  const map = React.useMemo(() => gridTexture(), []);
  React.useEffect(() => () => map.dispose(), [map]);
  useFrame(() => {
    const on = layer ? getLayers()[layer] : true;
    for (let k = 0; k < 2; k++) {
      const g = groups.current[k];
      if (!g) continue;
      g.visible = on;
      if (!on) continue;
      const p = (techClock.t / SCAN_PERIOD + k * 0.5) % 1;
      const r = 2.2 + p * (REACH.scan - 2.2);
      g.scale.set(r, 1, r);
      const fade = Math.min(1, p * 6) * (1 - p) ** 1.4;
      if (mats.current[k].grid) mats.current[k].grid!.opacity = 0.34 * fade;
      if (mats.current[k].ring) mats.current[k].ring!.opacity = 0.7 * fade;
    }
  });
  return (
    <group position={[at[0], FLOOR + 0.01, at[2]]}>
      {[0, 1].map((k) => (
        <group
          key={k}
          ref={(g) => {
            groups.current[k] = g;
          }}
        >
          <mesh rotation-x={-Math.PI / 2} renderOrder={4}>
            <planeGeometry args={[2, 2]} />
            <meshBasicMaterial
              ref={(m) => {
                mats.current[k].grid = m;
              }}
              map={map}
              color={COLOR.lidar}
              transparent
              depthWrite={false}
              toneMapped={false}
            />
          </mesh>
          <mesh rotation-x={-Math.PI / 2} renderOrder={5}>
            <ringGeometry args={[0.985, 1, 96]} />
            <meshBasicMaterial
              ref={(m) => {
                mats.current[k].ring = m;
              }}
              color={COLOR.lidar}
              transparent
              depthWrite={false}
              toneMapped={false}
            />
          </mesh>
        </group>
      ))}
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

/** Rings that go out from the car's outline, the ultrasonic sensors' close range (the count is published). */
function Pulses({ footprint, layer }: { footprint: { xMin: number; xMax: number; half: number }; layer: LayerId | null }) {
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
    g.visible = layer ? getLayers()[layer] : true;
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
function Marker({ layer, at, color, ring = false, small = false }: { layer: LayerId | null; at: [number, number, number]; color: string; ring?: boolean; small?: boolean }) {
  const root = React.useRef<THREE.Group>(null);
  useFrame(({ camera }) => {
    const g = root.current;
    if (!g) return;
    g.visible = layer ? getLayers()[layer] : true;
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

// ------------------------------------------------------------------ the traffic

/** The four corners of a rectangle as line segments (an L at each), `leg` long, centred, on the floor. */
export function cornerBrackets(length: number, width: number, leg: number): Float32Array {
  const pts: number[] = [];
  for (const sx of [-1, 1]) {
    for (const sz of [-1, 1]) {
      const x = (sx * length) / 2;
      const z = (sz * width) / 2;
      pts.push(x, 0, z, x - sx * leg, 0, z, x, 0, z, x, 0, z - sz * leg);
    }
  }
  return new Float32Array(pts);
}

/**
 * One of the other cars: another modelled car's stand-in in neutral paint, on the baked floor shadow of the real one.
 * Round its feet, brackets that say how the sensors see it: white when it is in reach, blue for the car being followed,
 * amber for a car in the way of the lane change. Its brake lamps are two red bars.
 */
function Traffic({ car, tone }: { car: TrafficCar; tone: string }) {
  const vehicle = getVehicle(car.slug);
  const url = vehicle?.assets.proxyUrl;
  if (!vehicle || !url) return null;
  return <TrafficModel car={car} tone={tone} url={url} shadow={vehicle.assets.studioShadow} />;
}

function TrafficModel({ car, tone, url, shadow }: { car: TrafficCar; tone: string; url: string; shadow: Parameters<typeof GroundShadow>[0]['shadow'] | undefined }) {
  const { model, centre } = useStandIn(url, tone);
  const root = React.useRef<THREE.Group>(null);
  const lamps = React.useRef<THREE.Group>(null);
  const brackets = React.useRef<THREE.LineSegments>(null);
  const outer = React.useRef<THREE.LineSegments>(null);
  const geo = React.useMemo(() => {
    const make = (grow: number, leg: number) => {
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.BufferAttribute(cornerBrackets(car.length + 0.5 + grow, car.width + 0.5 + grow, leg), 3));
      return g;
    };
    return { inner: make(0, Math.min(1.1, car.length * 0.2)), outer: make(0.34, Math.min(1.5, car.length * 0.28)) };
  }, [car.length, car.width]);
  React.useEffect(
    () => () => {
      geo.inner.dispose();
      geo.outer.dispose();
    },
    [geo],
  );
  useFrame(() => {
    const g = root.current;
    if (!g) return;
    const t = techClock.t;
    g.position.set(car.x(t), 0, -car.y(t));
    if (lamps.current) lamps.current.visible = car.braking(t);
    const tr = car.track(t);
    const sensed = tr !== 'out';
    const lit = sensed && getLayers().lidar;
    if (brackets.current) {
      brackets.current.visible = lit;
      if (lit) {
        const m = brackets.current.material as THREE.LineBasicMaterial;
        m.color.set(TRACK_COLOR[tr as Exclude<Track, 'out'>]);
        m.opacity = tr === 'tracked' ? 0.55 : 1;
      }
    }
    if (outer.current) {
      outer.current.visible = lit && tr !== 'tracked';
      if (outer.current.visible) (outer.current.material as THREE.LineBasicMaterial).color.set(TRACK_COLOR[tr as Exclude<Track, 'out'>]);
    }
  });
  const red = { color: '#ff3a2e', toneMapped: false } as const;
  return (
    <group ref={root}>
      {/* the model's origin is not the middle of the body: the middle is the car's place */}
      <group position={[-centre.x, 0, -centre.z]}>
        <primitive object={model} />
        {shadow && <GroundShadow shadow={shadow} />}
      </group>
      <group ref={lamps} visible={false}>
        {[-1, 1].map((s) => (
          <mesh key={s} position={[-car.length / 2 + 0.02, 0.93, s * (car.width / 2 - 0.3)]}>
            <boxGeometry args={[0.07, 0.1, 0.5]} />
            <meshBasicMaterial {...red} />
          </mesh>
        ))}
      </group>
      <lineSegments ref={brackets} geometry={geo.inner} position-y={0.04} renderOrder={7} visible={false}>
        <lineBasicMaterial color="#ffffff" transparent opacity={0.55} depthWrite={false} toneMapped={false} />
      </lineSegments>
      <lineSegments ref={outer} geometry={geo.outer} position-y={0.04} renderOrder={7} visible={false}>
        <lineBasicMaterial color="#ffffff" transparent opacity={0.8} depthWrite={false} toneMapped={false} />
      </lineSegments>
    </group>
  );
}

// ----------------------------------------------------- the left lane and the link

/**
 * The left lane, laid out while the car means to move into it: amber while a car is in the way, green once it is clear.
 * Drawn in the road's frame, from behind the car to ahead of it.
 */
function LaneStrip({ sensors }: { sensors: Scenario }) {
  const mesh = React.useRef<THREE.Mesh>(null);
  useFrame(() => {
    const m = mesh.current;
    if (!m) return;
    const t = techClock.t;
    const r = sensors.readout(t);
    const show = r.indicator === 1 && getLayers().lidar;
    m.visible = show;
    if (!show) return;
    const e = sensors.ego(t);
    const back = 32;
    const front = 18;
    m.scale.set(back + front, 1, 1);
    m.position.set(e.x + (front - back) / 2, 0.022, -LANE);
    const mat = m.material as THREE.MeshBasicMaterial;
    mat.color.set(r.leftClear ? '#22c55e' : '#f59e0b');
    mat.opacity = (r.leftClear ? 0.3 : 0.28 + 0.1 * Math.sin(t * 7)) * (r.state === 'changing' ? 0.75 : 1);
  });
  return (
    <mesh ref={mesh} rotation-x={-Math.PI / 2} renderOrder={4} visible={false}>
      <planeGeometry args={[1, LANE - 0.5]} />
      <meshBasicMaterial color="#f59e0b" transparent opacity={0.18} depthWrite={false} toneMapped={false} />
    </mesh>
  );
}

/** A line along the floor from the car's nose to the tail of the car it is following. */
function LeadLink({ sensors }: { sensors: Scenario }) {
  const mesh = React.useRef<THREE.Mesh>(null);
  useFrame(() => {
    const m = mesh.current;
    if (!m) return;
    const t = techClock.t;
    const r = sensors.readout(t);
    const lead = r.gap !== null ? sensors.traffic.find((c) => c.track(t) === 'lead') : undefined;
    m.visible = !!lead && getLayers().lidar;
    if (!lead || r.gap === null) return;
    const e = sensors.ego(t);
    const x0 = e.x + sensors.egoLength / 2;
    const x1 = lead.x(t) - lead.length / 2;
    m.scale.set(Math.max(x1 - x0, 0.1), 1, 1);
    m.position.set((x0 + x1) / 2, 0.05, -(e.y + lead.y(t)) / 2);
    (m.material as THREE.MeshBasicMaterial).opacity = r.state === 'following' ? 0.8 : 0.45;
  });
  return (
    <mesh ref={mesh} rotation-x={-Math.PI / 2} renderOrder={7} visible={false}>
      <planeGeometry args={[1, 0.1]} />
      <meshBasicMaterial color="#7fd0ff" transparent opacity={0.8} depthWrite={false} toneMapped={false} />
    </mesh>
  );
}
