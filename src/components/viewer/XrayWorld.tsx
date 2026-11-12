'use client';

import React from 'react';
import * as THREE from 'three';
import { Environment, Lightformer, MeshReflectorMaterial } from '@react-three/drei';
import { useFrame, useThree } from '@react-three/fiber';
import { STUDIO_RIG, STUDIO_VOID } from '@/data/studio/rig';
import type { Vehicle } from '@/data/vehicles/schema';
import { rigOf } from '@/lib/tech/rig';
import { STAGE_LAYER } from './StudioShowroom';

/**
 * The X-ray tab's Play stands the car on a salt flat under a blue sky: a glossy dark floor that mirrors the car and the horizon, low
 * hills far off, a pale haze where the ground meets the sky, and cracks in the salt that stream past under the car as it drives. It
 * replaces the white studio for as long as the show runs (viewer/ShowroomViewer.tsx), and the car is lit by a cool version of the studio's
 * own softbox rig, so the metal reads steel-blue.
 *
 * Everything is procedural (no textures shipped), drawn unlit except the floor, and kept inside the camera's far plane (180 m).
 */

export const SKY_TOP = '#2b7bd0';
const SKY_MID = '#74bdee';
export const HAZE = '#b9dff2';
const FLOOR = '#07192b';
const FLOOR_R = 150;
/** one repeat of the salt's cracks, m */
const TILE = 24;
/** the cool tint the studio's panels are lit with here */
const COOL = '#cfe6ff';
/** where the haze starts to take the car and where it has it entirely, m from the camera (the shots stand within about 10 m, so they are clear) */
const FOG_NEAR = 22;
const FOG_FAR = 80;
const GAIN = 1.5;

export function XrayWorld({ vehicle, reflections }: { vehicle: Vehicle; reflections: boolean }) {
  const camera = useThree((s) => s.camera);
  React.useEffect(() => {
    camera.layers.enable(STAGE_LAYER);
  }, [camera]);
  return (
    <>
      {/* what the floor's mirror clears to */}
      <color attach="background" args={[HAZE]} />
      {/* the haze takes the car as it drives away (the show's exit): the car's materials fade into it with distance from the camera, from 22 m to 80 m */}
      <fog attach="fog" args={[HAZE, FOG_NEAR, FOG_FAR]} />
      <CoolRig />
      <Sky />
      <Hills radius={96} height={11} seed={3} top="#3f6a90" />
      <Hills radius={132} height={16} seed={7} top="#6b97b8" />
      {reflections ? <GlossFloor /> : <PlainFloor />}
      <HazeBand />
      <Salt vehicle={vehicle} />
    </>
  );
}

/** The studio's rig, drawn once into a cube map for the car's reflections and light, in a cool white. */
function CoolRig() {
  return (
    <Environment frames={1} resolution={256} environmentIntensity={GAIN}>
      <color attach="background" args={[STUDIO_VOID]} />
      {STUDIO_RIG.filter((p) => !p.id.startsWith('floor')).map((p) => (
        <Lightformer key={p.id} form={p.form} position={p.position} rotation={p.rotation} scale={p.size} intensity={p.intensity} color={COOL} />
      ))}
      {/* the sky overhead and the pale floor the car stands on, as the paint and the metal see them */}
      <Lightformer form="circle" position={[0, 9, 0]} rotation={[-Math.PI / 2, 0, 0]} scale={[60, 60]} intensity={0.9} color={SKY_TOP} />
      <Lightformer form="circle" position={[0, -1, 0]} rotation={[-Math.PI / 2, 0, 0]} scale={[120, 120]} intensity={0.35} color="#7fb4dc" />
    </Environment>
  );
}

/** A gradient dome that follows the camera, so it is always at infinity. */
function Sky() {
  const mesh = React.useRef<THREE.Mesh>(null);
  const camera = useThree((s) => s.camera);
  useFrame(() => mesh.current?.position.copy(camera.position));
  const mat = React.useMemo(
    () =>
      new THREE.ShaderMaterial({
        side: THREE.BackSide,
        depthWrite: false,
        fog: false,
        toneMapped: false,
        uniforms: { top: { value: new THREE.Color(SKY_TOP) }, mid: { value: new THREE.Color(SKY_MID) }, hor: { value: new THREE.Color(HAZE) } },
        vertexShader: 'varying vec3 vDir; void main() { vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
        fragmentShader: `uniform vec3 top; uniform vec3 mid; uniform vec3 hor; varying vec3 vDir;
          void main() {
            float h = clamp(vDir.y, 0.0, 1.0);
            vec3 c = mix(hor, mid, smoothstep(0.0, 0.2, h));
            c = mix(c, top, smoothstep(0.15, 0.75, h));
            gl_FragColor = vec4(c, 1.0);
            #include <colorspace_fragment>
          }`,
      }),
    [],
  );
  React.useEffect(() => () => mat.dispose(), [mat]);
  return (
    <mesh ref={mesh} renderOrder={-10} frustumCulled={false} material={mat}>
      <sphereGeometry args={[150, 32, 16]} />
    </mesh>
  );
}

/** A ring of low hills, a silhouette that fades into the haze at its foot. Seeded, so every visit draws the same horizon. */
function Hills({ radius, height, seed, top }: { radius: number; height: number; seed: number; top: string }) {
  const geometry = React.useMemo(() => {
    const N = 240;
    const rnd = (n: number) => {
      const s = Math.sin(n * 127.1 + seed * 311.7) * 43758.5453;
      return s - Math.floor(s);
    };
    const p = [rnd(1) * 6.28, rnd(2) * 6.28, rnd(3) * 6.28, rnd(4) * 6.28];
    const lo = new THREE.Color(HAZE);
    const hi = new THREE.Color(top);
    const pos: number[] = [];
    const col: number[] = [];
    const idx: number[] = [];
    for (let i = 0; i <= N; i++) {
      const a = (i / N) * Math.PI * 2;
      const h = height * (0.38 + 0.3 * Math.abs(Math.sin(3 * a + p[0])) + 0.18 * Math.sin(7 * a + p[1]) * Math.sin(2 * a + p[3]) + 0.1 * Math.sin(17 * a + p[2]));
      const x = Math.cos(a) * radius;
      const z = Math.sin(a) * radius;
      pos.push(x, -0.5, z, x, Math.max(1, h), z);
      col.push(lo.r, lo.g, lo.b, hi.r, hi.g, hi.b);
      if (i < N) {
        const k = i * 2;
        idx.push(k, k + 1, k + 3, k, k + 3, k + 2);
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
    g.setIndex(idx);
    return g;
  }, [radius, height, seed, top]);
  React.useEffect(() => () => geometry.dispose(), [geometry]);
  return (
    <mesh geometry={geometry} frustumCulled={false}>
      <meshBasicMaterial vertexColors side={THREE.DoubleSide} fog={false} toneMapped={false} />
    </mesh>
  );
}

/** The floor with a strong mirror: the car, its hardware and the horizon in the dark salt. */
function GlossFloor() {
  return (
    <mesh rotation-x={-Math.PI / 2}>
      <circleGeometry args={[FLOOR_R, 96]} />
      <MeshReflectorMaterial
        resolution={768}
        blur={[260, 80]}
        mixBlur={0.8}
        mixStrength={1.15}
        mirror={0.62}
        roughness={0.55}
        metalness={0}
        color={FLOOR}
        envMapIntensity={0.25}
      />
    </mesh>
  );
}

function PlainFloor() {
  return (
    <mesh rotation-x={-Math.PI / 2}>
      <circleGeometry args={[FLOOR_R, 64]} />
      <meshBasicMaterial color="#15324d" toneMapped={false} />
    </mesh>
  );
}

/** The ground fades into the haze toward the horizon: a disc, clear at the car and the haze's colour at its rim. */
function HazeBand() {
  const map = React.useMemo(() => {
    const c = document.createElement('canvas');
    c.width = c.height = 256;
    const g = c.getContext('2d')!;
    const r = g.createRadialGradient(128, 128, 0, 128, 128, 128);
    r.addColorStop(0, 'rgba(185,223,242,0)');
    r.addColorStop(0.1, 'rgba(185,223,242,0)');
    r.addColorStop(0.32, 'rgba(185,223,242,0.45)');
    r.addColorStop(0.62, 'rgba(185,223,242,0.9)');
    r.addColorStop(1, 'rgba(185,223,242,1)');
    g.fillStyle = r;
    g.fillRect(0, 0, 256, 256);
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  }, []);
  React.useEffect(() => () => map.dispose(), [map]);
  return (
    <mesh rotation-x={-Math.PI / 2} position-y={0.006} renderOrder={-4} ref={onStage}>
      <circleGeometry args={[FLOOR_R, 96]} />
      <meshBasicMaterial map={map} transparent depthWrite={false} toneMapped={false} fog={false} />
    </mesh>
  );
}

/** Seen by the view camera only: the floor's mirror does not draw it. */
const onStage = (o: THREE.Object3D | null) => {
  o?.layers.set(STAGE_LAYER);
};

/**
 * Cracks in the salt: a tile of thin dark seams that repeats over the floor and is slid by the run's scroll (the rig's, the same as the
 * road's in the Drive tab), so the ground is seen to stream under a car that stands still on the spot.
 */
function Salt({ vehicle }: { vehicle: Vehicle }) {
  const rig = rigOf(vehicle);
  const map = React.useMemo(() => {
    const S = 1024;
    const c = document.createElement('canvas');
    c.width = c.height = S;
    const g = c.getContext('2d')!;
    const n = 9;
    const cell = S / n;
    const rnd = (i: number, j: number, k: number) => {
      const s = Math.sin(((i + n * 64) % n) * 12.9898 + ((j + n * 64) % n) * 78.233 + k * 37.719) * 43758.5453;
      return s - Math.floor(s);
    };
    const pt = (i: number, j: number) => ({ x: (i + 0.15 + 0.7 * rnd(i, j, 1)) * cell, y: (j + 0.15 + 0.7 * rnd(i, j, 2)) * cell });
    const line = (a: { x: number; y: number }, b: { x: number; y: number }, w: number, style: string) => {
      g.strokeStyle = style;
      g.lineWidth = w;
      g.beginPath();
      g.moveTo(a.x, a.y);
      const mx = (a.x + b.x) / 2 + (rnd(a.x | 0, a.y | 0, 3) - 0.5) * cell * 0.25;
      const my = (a.y + b.y) / 2 + (rnd(a.x | 0, a.y | 0, 4) - 0.5) * cell * 0.25;
      g.quadraticCurveTo(mx, my, b.x, b.y);
      g.stroke();
    };
    // every point joined to its right and lower neighbour, wrapping, and drawn at the four offsets so that the seams cross the tile's edge
    for (const ox of [-S, 0, S]) {
      for (const oy of [-S, 0, S]) {
        g.save();
        g.translate(ox, oy);
        for (let j = 0; j < n; j++) {
          for (let i = 0; i < n; i++) {
            const a = pt(i, j);
            for (const [di, dj] of [[1, 0], [0, 1]]) {
              const b = pt(i + di, j + dj);
              const bb = { x: b.x + (i + di >= n ? S : 0), y: b.y + (j + dj >= n ? S : 0) };
              line(a, bb, 2.4, 'rgba(3,12,22,0.42)');
              line({ x: a.x + 1.6, y: a.y + 1.6 }, { x: bb.x + 1.6, y: bb.y + 1.6 }, 1, 'rgba(160,205,235,0.1)');
            }
          }
        }
        g.restore();
      }
    }
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.repeat.set((FLOOR_R * 2) / TILE, (FLOOR_R * 2) / TILE);
    t.anisotropy = 8;
    return t;
  }, []);
  React.useEffect(() => () => map.dispose(), [map]);
  const invalidate = useThree((s) => s.invalidate);
  const last = React.useRef(NaN);
  useFrame(() => {
    const s = rig.state.scroll;
    if (s === last.current) return;
    last.current = s;
    map.offset.x = (s / TILE) % 1;
    invalidate();
  });
  return (
    <mesh rotation-x={-Math.PI / 2} position-y={0.004} renderOrder={-5} ref={onStage}>
      <planeGeometry args={[FLOOR_R * 2, FLOOR_R * 2]} />
      <meshBasicMaterial map={map} transparent depthWrite={false} toneMapped={false} fog={false} opacity={0.75} />
    </mesh>
  );
}
