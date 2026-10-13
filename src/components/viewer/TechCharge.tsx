'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { RoundedBox } from '@react-three/drei';
import { techClock } from '@/lib/tech/clock';
import type { ChargeReadout } from '@/lib/tech/charge';
import { useRuntime, type Runtime } from '@/lib/tech/session';

/**
 * The fast-charge demo's props: a plain, unbranded charging pedestal beside the car, the gun on its front face and the
 * gun's cable (src/lib/tech/charge.ts moves them with the demo's clock). None of it is Zeekr's or any maker's: the
 * gun is styled on the owner's photographs of a charging connector (a white shell, a black head and boot) and its face
 * is the 7X's DC inlet the other way round (the sockets' layout in blender/scripts/zx_charge.py, read off the
 * Autohome photographs c12_0048 and c12_0049). Mount once in the showroom's Canvas.
 */
export function TechCharge() {
  const charge = useRuntime()?.charge;
  if (!charge) return null;
  return <Props charge={charge} />;
}

type Charge = NonNullable<Runtime['charge']>;

const F = new THREE.Vector3();
const U = new THREE.Vector3();
const X = new THREE.Vector3();
const M4 = new THREE.Matrix4();

// the DC cup's contacts in the cup's radius (photograph c12_0049, x right and y down: right is rearward)
const DC_R = 0.0325;
const DC_BIG: [number, number, number][] = [[-0.29, -0.19, 0.32], [0.65, 0, 0.32]];
const DC_EARTH: [number, number, number][] = [[0.1, 0.5, 0.19]];
const DC_SIGNAL: [number, number, number][] = [
  [0.02, -0.84, 0.12], [0.32, -0.81, 0.12], [0.68, -0.74, 0.12], [0.32, -0.45, 0.12], [-0.16, 0.37, 0.12], [0.63, 0.55, 0.12],
];

const SHELL = '#ebe8e1';
const BLACK = '#18191c';

function Props({ charge }: { charge: Charge }) {
  const gun = React.useRef<THREE.Group>(null);
  const cable = React.useRef<THREE.Mesh>(null);
  const strip = React.useRef<THREE.MeshBasicMaterial>(null);
  const { pedestal, cableOut, gunExit } = charge;

  const screen = React.useMemo(() => {
    const c = document.createElement('canvas');
    c.width = 256;
    c.height = 384;
    const tex = new THREE.CanvasTexture(c);
    tex.colorSpace = THREE.SRGBColorSpace;
    return { c, tex };
  }, []);
  React.useEffect(() => () => screen.tex.dispose(), [screen]);
  const lastDraw = React.useRef(-1);

  const cableMat = React.useMemo(() => new THREE.MeshStandardMaterial({ color: '#121316', roughness: 0.6, metalness: 0 }), []);
  React.useEffect(() => () => cableMat.dispose(), [cableMat]);

  useFrame(({ clock }) => {
    const t = techClock.t;
    const g = charge.gun(t);
    const grp = gun.current;
    if (grp) {
      grp.position.set(...g.tip);
      F.set(...g.forward);
      U.set(...g.up);
      X.crossVectors(U, F).normalize();
      U.crossVectors(F, X);
      M4.makeBasis(X, U, F);
      grp.quaternion.setFromRotationMatrix(M4);
    }
    // the cable: from the pedestal's grommet to the gun's grip, drooping, never through the floor
    const mesh = cable.current;
    if (mesh && grp) {
      const exit = new THREE.Vector3(...g.tip)
        .addScaledVector(F, gunExit[0])
        .addScaledVector(U, gunExit[1]);
      const start = new THREE.Vector3(...cableOut);
      const dist = start.distanceTo(exit);
      const mid = start.clone().lerp(exit, 0.5);
      mid.y -= 0.12 + 0.3 * Math.min(1, dist / 1.4);
      const lead = start.clone().add(new THREE.Vector3(0, -0.04, 0.3));
      const tail = exit.clone().addScaledVector(U, -0.1).addScaledVector(F, -0.05);
      const curve = new THREE.CatmullRomCurve3([start, lead, mid, tail, exit], false, 'catmullrom', 0.5);
      const pts = curve.getPoints(40).map((p) => new THREE.Vector3(p.x, Math.max(p.y, 0.014), p.z));
      const old = mesh.geometry;
      mesh.geometry = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 48, 0.0115, 8, false);
      old.dispose();
    }
    // the light strip and the pedestal's screen
    const r = charge.readout(t);
    if (strip.current) strip.current.color.set(stripColour(r, clock.elapsedTime));
    if (Math.abs(t - lastDraw.current) > 0.09 || lastDraw.current < 0) {
      drawScreen(screen.c, r);
      screen.tex.needsUpdate = true;
      lastDraw.current = t;
    }
  });

  return (
    <>
      <group position={[pedestal.x, 0, pedestal.z]} rotation-y={pedestal.yaw}>
        {/* the shadow it stands in */}
        <mesh rotation-x={-Math.PI / 2} position-y={0.004} renderOrder={-0.4}>
          <planeGeometry args={[0.9, 0.8]} />
          <meshBasicMaterial map={shadowTexture()} transparent depthWrite={false} toneMapped={false} />
        </mesh>
        <mesh position={[0, 0.012, 0]}>
          <boxGeometry args={[0.46, 0.024, 0.36]} />
          <meshStandardMaterial color="#9ea2a8" roughness={0.6} />
        </mesh>
        <RoundedBox args={[0.34, 1.66, 0.23]} radius={0.035} smoothness={4} position={[0, 0.85, 0]}>
          <meshStandardMaterial color="#2b2d33" roughness={0.42} metalness={0.15} />
        </RoundedBox>
        {/* a lighter cap, a screen, the light strip, the cradle and the cable's grommet, all on the car-facing side */}
        <RoundedBox args={[0.345, 0.12, 0.235]} radius={0.03} smoothness={3} position={[0, 1.64, 0]}>
          <meshStandardMaterial color="#dcdcdc" roughness={0.5} />
        </RoundedBox>
        <mesh position={[0, 1.52, 0.1165]}>
          <boxGeometry args={[0.22, 0.012, 0.004]} />
          <meshBasicMaterial ref={strip} color="#9fb4ff" toneMapped={false} />
        </mesh>
        <mesh position={[0, 1.33, 0.1165]}>
          <planeGeometry args={[0.24, 0.36]} />
          <meshBasicMaterial map={screen.tex} toneMapped={false} />
        </mesh>
        <mesh position={[0, 1.1, 0.108]}>
          <boxGeometry args={[0.1, 0.1, 0.03]} />
          <meshStandardMaterial color="#0f1013" roughness={0.7} />
        </mesh>
        <mesh position={[cableOut[0] - pedestal.x, cableOut[1], cableOut[2] - pedestal.z - 0.003]} rotation-x={Math.PI / 2}>
          <cylinderGeometry args={[0.02, 0.02, 0.012, 16]} />
          <meshStandardMaterial color="#0f1013" roughness={0.7} />
        </mesh>
      </group>
      <mesh ref={cable} material={cableMat} frustumCulled={false}>
        <bufferGeometry />
      </mesh>
      <group ref={gun}>
        <Gun />
      </group>
    </>
  );
}

/** The gun, its nose's tip at the origin and the nose pointing +Z, the grip down (-Y). */
function Gun() {
  const pins = React.useMemo(() => {
    const out: { x: number; y: number; r: number; long: number }[] = [];
    for (const [x, y, r] of DC_BIG) out.push({ x: -x * DC_R, y: -y * DC_R, r: r * DC_R * 0.62, long: 0.016 });
    for (const [x, y, r] of DC_EARTH) out.push({ x: -x * DC_R, y: -y * DC_R, r: r * DC_R * 0.6, long: 0.012 });
    for (const [x, y, r] of DC_SIGNAL) out.push({ x: -x * DC_R, y: -y * DC_R, r: r * DC_R * 0.5, long: 0.008 });
    return out;
  }, []);
  return (
    <group>
      {/* the head: a black barrel, its face with the pins */}
      <mesh rotation-x={Math.PI / 2} position={[0, 0, -0.04]}>
        <cylinderGeometry args={[0.0275, 0.0275, 0.08, 36]} />
        <meshStandardMaterial color={BLACK} roughness={0.5} />
      </mesh>
      {pins.map((p, i) => (
        <mesh key={i} rotation-x={Math.PI / 2} position={[p.x, p.y, p.long / 2]}>
          <cylinderGeometry args={[p.r, p.r, p.long, 14]} />
          <meshStandardMaterial color={i < 2 ? '#b9923f' : '#8a8d92'} roughness={0.3} metalness={0.9} />
        </mesh>
      ))}
      {/* a collar, then the white shell */}
      <mesh rotation-x={Math.PI / 2} position={[0, 0, -0.088]}>
        <cylinderGeometry args={[0.034, 0.034, 0.016, 32]} />
        <meshStandardMaterial color={BLACK} roughness={0.5} />
      </mesh>
      <mesh rotation-x={Math.PI / 2} position={[0, 0.004, -0.15]}>
        <capsuleGeometry args={[0.039, 0.085, 8, 24]} />
        <meshStandardMaterial color={SHELL} roughness={0.42} />
      </mesh>
      {/* the grip, dropping down and back, with its ridges */}
      <group position={[0, -0.06, -0.19]} rotation-x={0.42}>
        <mesh position={[0, -0.05, 0]}>
          <capsuleGeometry args={[0.027, 0.1, 8, 20]} />
          <meshStandardMaterial color={SHELL} roughness={0.42} />
        </mesh>
        {[0, 1, 2, 3].map((i) => (
          <mesh key={i} position={[0, -0.03 - i * 0.024, 0.0215]} rotation-y={Math.PI / 2}>
            <capsuleGeometry args={[0.0035, 0.034, 4, 8]} />
            <meshStandardMaterial color="#d7d3ca" roughness={0.5} />
          </mesh>
        ))}
        <mesh position={[0, -0.13, 0]}>
          <cylinderGeometry args={[0.02, 0.022, 0.05, 20]} />
          <meshStandardMaterial color={BLACK} roughness={0.6} />
        </mesh>
      </group>
      {/* the latch on the shell's top, forward */}
      <mesh position={[0, 0.043, -0.11]}>
        <boxGeometry args={[0.02, 0.008, 0.04]} />
        <meshStandardMaterial color={BLACK} roughness={0.5} />
      </mesh>
    </group>
  );
}

let _shadow: THREE.CanvasTexture | null = null;
/** A soft ellipse for the pedestal's foot. */
function shadowTexture(): THREE.CanvasTexture {
  if (_shadow) return _shadow;
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const ctx = c.getContext('2d')!;
  const g = ctx.createRadialGradient(64, 64, 4, 64, 64, 62);
  g.addColorStop(0, 'rgba(20,22,28,0.5)');
  g.addColorStop(1, 'rgba(20,22,28,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 128, 128);
  _shadow = new THREE.CanvasTexture(c);
  return _shadow;
}

function stripColour(r: ChargeReadout, time: number): string {
  switch (r.phase) {
    case 'connecting':
      return Math.sin(time * 6) > 0 ? '#5a8bff' : '#2a3f7a';
    case 'charging': {
      const k = 0.55 + 0.45 * Math.sin(time * 2.2);
      return `rgb(${Math.round(40 * k)},${Math.round(230 * k)},${Math.round(120 * k)})`;
    }
    case 'charged':
      return '#33e07a';
    default:
      return '#9fb4ff';
  }
}

/** The pedestal's small screen: what a charger shows, drawn from the demo's own numbers. */
function drawScreen(c: HTMLCanvasElement, r: ChargeReadout) {
  const ctx = c.getContext('2d')!;
  const W = c.width;
  const H = c.height;
  ctx.fillStyle = '#0b0d12';
  ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#8b93a5';
  ctx.font = '600 20px system-ui, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('DC FAST CHARGE', W / 2, 36);
  const label =
    r.phase === 'ready' || r.phase === 'opening'
      ? 'Ready'
      : r.phase === 'connecting'
        ? 'Connecting…'
        : r.phase === 'charging'
          ? 'Charging'
          : r.phase === 'charged'
            ? 'Charged to 80 %'
            : 'Unplugged';
  ctx.fillStyle = r.phase === 'charging' || r.phase === 'charged' ? '#33e07a' : '#c9cfdd';
  ctx.font = '600 24px system-ui, sans-serif';
  ctx.fillText(label, W / 2, 78);
  ctx.fillStyle = '#ffffff';
  ctx.font = '700 84px system-ui, sans-serif';
  ctx.fillText(String(Math.round(r.kw)), W / 2, 190);
  ctx.fillStyle = '#8b93a5';
  ctx.font = '600 24px system-ui, sans-serif';
  ctx.fillText('kW', W / 2, 224);
  // the charge level
  ctx.fillStyle = '#1b2029';
  ctx.fillRect(28, 258, W - 56, 18);
  ctx.fillStyle = '#33e07a';
  ctx.fillRect(28, 258, (W - 56) * r.soc, 18);
  ctx.fillStyle = '#ffffff';
  ctx.font = '600 30px system-ui, sans-serif';
  ctx.fillText(`${Math.round(r.soc * 100)} %`, W / 2, 318);
  ctx.fillStyle = '#8b93a5';
  ctx.font = '500 20px system-ui, sans-serif';
  const mm = Math.floor(r.elapsed / 60);
  const ss = Math.floor(r.elapsed % 60);
  ctx.fillText(`${mm}:${String(ss).padStart(2, '0')}  ·  ${r.kwh.toFixed(1)} kWh`, W / 2, 354);
}
