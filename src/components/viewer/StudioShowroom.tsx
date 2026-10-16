'use client';

import React from 'react';
import * as THREE from 'three';
import { Environment, Lightformer, MeshReflectorMaterial, useTexture } from '@react-three/drei';
import { useFrame, useThree } from '@react-three/fiber';
import { STUDIO_GAIN, STUDIO_RIG, STUDIO_VOID } from '@/data/studio/rig';
import type { VehicleAssets } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { useDusk } from './Lights';

/**
 * The white studio the showroom stands the car in (Phase 1 of
 * docs/hima-benchmark.md).
 *
 * Two separate things, as in the maker's own halls: what the room LOOKS like
 * (a bright white cove and floor, drawn unlit) and what the paint REFLECTS (the
 * dark rig of softboxes in src/data/studio/rig.ts, drawn into a cube map). The
 * room is on its own layer: the camera sees it, but neither the mirror pass nor
 * ContactShadows' depth pass does, which is what keeps the floor from
 * mirroring the dome and the shadow square from filling with the floor.
 */

/** Seen by the view camera only. */
export const STAGE_LAYER = 1;
const onStage = (o: THREE.Object3D | null) => {
  o?.layers.set(STAGE_LAYER);
};

/** The renderer's clear colour (alpha 0): what the mirror shows where nothing is. */
export const STUDIO_WHITE = '#f1f2f4';
const FLOOR = '#e9eaed';
const FLOOR_RADIUS = 22;
/** How much of the floor colour the reflection replaces. */
const MIRROR = 0.4;

export function StudioShowroom({ reflections, inside }: { reflections: boolean; inside: boolean }) {
  const camera = useThree((s) => s.camera);
  const scene = useThree((s) => s.scene);
  const background = React.useRef<THREE.Color>(null);
  React.useEffect(() => {
    camera.layers.enable(STAGE_LAYER);
  }, [camera]);

  // with the lamps on, the room goes toward dusk: the white of the walls, the floor and the light the car
  // reflects (src/components/viewer/Lights.tsx)
  useDusk((d) => {
    background.current?.set(STUDIO_WHITE).multiply(d.room);
    scene.environmentIntensity = STUDIO_GAIN * d.env;
  });

  return (
    <>
      {/*
        The mirror pass clears to this. The renderer's own clear colour cannot do
        it: it is alpha 0 (ContactShadows needs that), which clears the
        mirror's buffer to premultiplied black and darkens the whole floor.
        ContactShadows takes the background off for its own pass.
      */}
      <color ref={background} attach="background" args={[STUDIO_WHITE]} />
      <RigLight />
      <Cove />
      <Rings />
      {reflections && !inside ? <MirrorFloor /> : <PlainFloor />}
    </>
  );
}

/** The rig, drawn once into a cube map and used as the scene's image-based light. */
function RigLight() {
  return (
    <Environment frames={1} resolution={256} environmentIntensity={STUDIO_GAIN}>
      <color attach="background" args={[STUDIO_VOID]} />
      {STUDIO_RIG.map((p) => (
        <Lightformer
          key={p.id}
          form={p.form}
          position={p.position}
          rotation={p.rotation}
          scale={p.size}
          intensity={p.intensity}
          color={p.color ?? '#ffffff'}
        />
      ))}
    </Environment>
  );
}

/**
 * A uniform white light for the floor alone. The reflector tints its diffuse
 * colour by the reflection and is then lit like any standard material, so under
 * the dark rig the floor would come out grey; lit by a white of radiance 1 it
 * shows exactly its own colour.
 */
function useWhiteEnv() {
  const gl = useThree((s) => s.gl);
  const [env, setEnv] = React.useState<THREE.Texture | null>(null);
  // an effect, not a memo: a GPU-only render target made in a memo and disposed
  // by a StrictMode cleanup comes back empty
  React.useEffect(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    const white = new THREE.Scene();
    white.background = new THREE.Color(1, 1, 1);
    const rt = pmrem.fromScene(white, 0, 0.1, 10);
    pmrem.dispose();
    setEnv(rt.texture);
    return () => rt.dispose();
  }, [gl]);
  return env;
}

function PlainFloor() {
  const mat = React.useRef<THREE.MeshBasicMaterial>(null);
  useDusk((d) => mat.current?.color.set(FLOOR).multiply(d.room));
  return (
    <mesh rotation-x={-Math.PI / 2}>
      <circleGeometry args={[FLOOR_RADIUS, 128]} />
      <meshBasicMaterial ref={mat} color={FLOOR} toneMapped={false} />
    </mesh>
  );
}

/**
 * The floor with a soft mirror: the car faintly reflected, blurred, strongest
 * at its base. The mirror multiplies the floor colour, so the white of the
 * room stays white and only the car darkens it.
 */
function MirrorFloor() {
  const white = useWhiteEnv();
  const tab = useVehicleStore((s) => s.tab);
  const invalidate = useThree((s) => s.invalidate);
  const mat = React.useRef<React.ElementRef<typeof MeshReflectorMaterial>>(null);

  // the Specifications tab writes on the floor: ease the reflection back so the
  // rulers and their labels read cleanly, and forward again on the other tabs
  useFrame((_, dt) => {
    const m = mat.current;
    if (!m) return;
    const goal = tab === 'dimensions' ? 0.1 : MIRROR;
    const d = goal - m.mirror;
    if (Math.abs(d) > 0.002) {
      m.mirror += d * (1 - Math.exp(-dt * 6));
      invalidate();
    } else m.mirror = goal;
  });
  useDusk((d) => mat.current?.color.set(FLOOR).multiply(d.room));

  if (!white) return <PlainFloor />;
  return (
    <mesh rotation-x={-Math.PI / 2}>
      <circleGeometry args={[FLOOR_RADIUS, 128]} />
      <MeshReflectorMaterial
        ref={mat}
        resolution={768}
        blur={[320, 90]}
        mixBlur={0.9}
        mixStrength={1}
        mirror={MIRROR}
        roughness={0.8}
        metalness={0}
        color={FLOOR}
        envMap={white}
        envMapIntensity={1}
      />
    </mesh>
  );
}

/**
 * The cyclorama: a floor edge that sweeps up into a wall and closes in a dome,
 * lit by nothing (a flat gradient, white at the top and a touch grey at the
 * floor so the car's space reads as a room rather than a void).
 */
function Cove() {
  const geometry = React.useMemo(() => {
    const fillet = 5;
    const wall = 13;
    const dome = 11;
    const pts: THREE.Vector2[] = [];
    for (let i = 0; i <= 14; i++) {
      const a = (i / 14) * (Math.PI / 2);
      pts.push(new THREE.Vector2(FLOOR_RADIUS + fillet * Math.sin(a), fillet * (1 - Math.cos(a))));
    }
    pts.push(new THREE.Vector2(FLOOR_RADIUS + fillet, wall));
    for (let i = 1; i <= 18; i++) {
      const b = (i / 18) * (Math.PI / 2);
      pts.push(new THREE.Vector2((FLOOR_RADIUS + fillet) * Math.cos(b), wall + dome * Math.sin(b)));
    }
    const g = new THREE.LatheGeometry(pts, 128);
    const pos = g.getAttribute('position');
    const colors = new Float32Array(pos.count * 3);
    const low = new THREE.Color('#e2e4e8');
    const mid = new THREE.Color('#eff1f3');
    const high = new THREE.Color('#fafbfc');
    const c = new THREE.Color();
    for (let i = 0; i < pos.count; i++) {
      const y = pos.getY(i);
      const k1 = THREE.MathUtils.smoothstep(y, 0, fillet + 3);
      const k2 = THREE.MathUtils.smoothstep(y, wall * 0.5, wall + dome);
      c.copy(low).lerp(mid, k1).lerp(high, k2);
      colors.set([c.r, c.g, c.b], i * 3);
    }
    g.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    return g;
  }, []);
  React.useEffect(() => () => geometry.dispose(), [geometry]);

  const mat = React.useRef<THREE.MeshBasicMaterial>(null);
  // the wall's colours are in the vertices; the material's own colour multiplies them
  useDusk((d) => mat.current?.color.copy(d.room));

  return (
    <mesh geometry={geometry} ref={onStage} renderOrder={-1}>
      <meshBasicMaterial ref={mat} vertexColors side={THREE.DoubleSide} toneMapped={false} depthWrite={false} />
    </mesh>
  );
}

/** Two faint concentric lines on the floor, as on a turntable. */
function Rings() {
  const rings: [number, number][] = [
    [4.3, 4.34],
    [7.6, 7.64],
  ];
  const mats = React.useRef<(THREE.MeshBasicMaterial | null)[]>([]);
  useDusk((d) => {
    for (const m of mats.current) m?.color.set('#c3c6cc').multiply(d.room);
  });
  return (
    <group rotation-x={-Math.PI / 2} position-y={0.004}>
      {rings.map(([a, b], i) => (
        <mesh key={a} ref={onStage}>
          <ringGeometry args={[a, b, 192]} />
          <meshBasicMaterial
            ref={(m: THREE.MeshBasicMaterial | null) => {
              mats.current[i] = m;
            }}
            color="#c3c6cc"
            transparent
            opacity={0.75}
            toneMapped={false}
            depthWrite={false}
          />
        </mesh>
      ))}
    </group>
  );
}

/**
 * The car's shadow on the floor, baked in Blender (carkit.studio.ground_shadow):
 * one textured quad whose alpha is the shade, in place of a shadow rendered
 * from the car every time. It shows what a projected shadow cannot: the dark
 * core under the sills, the tyres' contact and the soft fall-off of a white room,
 * all from the car's real geometry. The image's u runs along the car (x), its v
 * to the build's +y, which is the viewer's -z.
 */
export function GroundShadow({ shadow }: { shadow: NonNullable<VehicleAssets['studioShadow']> }) {
  const map = useTexture(shadow.url);
  React.useLayoutEffect(() => {
    map.colorSpace = THREE.SRGBColorSpace;
    map.anisotropy = 8;
    map.needsUpdate = true;
  }, [map]);
  const [cx, cy] = shadow.centre;
  return (
    <mesh position={[cx, 0.003, -cy]} rotation-x={-Math.PI / 2}>
      <planeGeometry args={shadow.size} />
      {/* a slight bias toward the camera, so the shadow stays over the floor at the Tech stage's distance too */}
      <meshBasicMaterial map={map} transparent depthWrite={false} toneMapped={false} polygonOffset polygonOffsetFactor={-6} polygonOffsetUnits={-6} />
    </mesh>
  );
}
