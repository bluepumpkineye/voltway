'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { RoundedBox } from '@react-three/drei';
import type { Vehicle } from '@/data/vehicles/schema';
import { techClock } from '@/lib/tech/clock';
import type { ChargePort, ChargeReadout } from '@/lib/tech/charge';
import { chargeFacts, portOf } from '@/lib/tech/charging';
import { useRuntime, type Runtime } from '@/lib/tech/session';
import { useVehicleStore } from '@/store/vehicle-store';

/**
 * The Charging tab's props: a plain, unbranded charging pedestal beside the car, the gun on its face and the gun's
 * cable (src/lib/tech/charge.ts moves them with the demo's clock). None of it is any maker's: the gun is styled on
 * the owner's photographs of a charging connector (a white shell, a black head and boot) and its face is the 7X's DC
 * inlet the other way round (the sockets' layout in blender/scripts/zx_charge.py, read off the Autohome photographs
 * c12_0048 and c12_0049). The 7X's model has a flap and a socket of its own; every other car gets a socket drawn at
 * its port while the flap is "open" (`Vehicle.chargePort`), the same inlet the gun is made for. Mount once in the
 * showroom's Canvas.
 */
export function TechCharge({ vehicle }: { vehicle: Vehicle }) {
  const charge = useRuntime()?.charge;
  if (!charge) return null;
  const facts = chargeFacts(vehicle);
  return <Props charge={charge} socket={facts && !facts.modelledFlap ? portOf(vehicle) : null} />;
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

function Props({ charge, socket }: { charge: Charge; socket: ChargePort | null }) {
  const gun = React.useRef<THREE.Group>(null);
  const cable = React.useRef<THREE.Mesh>(null);
  const strip = React.useRef<THREE.MeshBasicMaterial>(null);
  const socketStrip = React.useRef<THREE.MeshBasicMaterial>(null);
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
    const lit = stripColour(r, clock.elapsedTime);
    if (strip.current) strip.current.color.set(lit);
    if (socketStrip.current) socketStrip.current.color.set(lit);
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
        {/* the cable's grommet, in the pedestal's own frame (it is turned half way round for a port on the passenger's side) */}
        <mesh
          position={[pedestal.face * (cableOut[0] - pedestal.x), cableOut[1], pedestal.face * (cableOut[2] - pedestal.z) - 0.003]}
          rotation-x={Math.PI / 2}
        >
          <cylinderGeometry args={[0.02, 0.02, 0.012, 16]} />
          <meshStandardMaterial color="#0f1013" roughness={0.7} />
        </mesh>
      </group>
      <mesh ref={cable} material={cableMat} frustumCulled={false}>
        <bufferGeometry />
      </mesh>
      {socket && <Socket port={socket} strip={socketStrip} />}
      <group ref={gun}>
        <Gun />
      </group>
    </>
  );
}

/** The DC cup's contacts, in the cup's frame; the gun's face is the cup the other way round (`flip`). */
function contacts(flip: boolean) {
  const k = flip ? -1 : 1;
  const out: { x: number; y: number; r: number; long: number }[] = [];
  for (const [x, y, r] of DC_BIG) out.push({ x: k * x * DC_R, y: -y * DC_R, r: r * DC_R * 0.62, long: 0.016 });
  for (const [x, y, r] of DC_EARTH) out.push({ x: k * x * DC_R, y: -y * DC_R, r: r * DC_R * 0.6, long: 0.012 });
  for (const [x, y, r] of DC_SIGNAL) out.push({ x: k * x * DC_R, y: -y * DC_R, r: r * DC_R * 0.5, long: 0.008 });
  return out;
}

/**
 * A DC socket drawn on a car whose model has no flap: the seam of a flap that has opened, the dark pocket, the cup with
 * its contacts and the light strip above it, at the car's charge port. It grows out of the skin when the demo opens the
 * flap and shrinks back when it shuts. The size is a flap's, about 19 by 15 cm; the place is `Vehicle.chargePort`.
 */
function Socket({ port, strip }: { port: ChargePort; strip: React.RefObject<THREE.MeshBasicMaterial | null> }) {
  const group = React.useRef<THREE.Group>(null);
  const open = React.useRef(0);
  const pins = React.useMemo(() => contacts(false), []);
  // z along the axis out of the port, y as near to up as the skin allows
  const quat = React.useMemo(() => {
    const z = new THREE.Vector3(...port.axis).normalize();
    const y = new THREE.Vector3(0, 1, 0).addScaledVector(z, -z.y).normalize();
    const x = new THREE.Vector3().crossVectors(y, z).normalize();
    return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, z));
  }, [port]);
  const pos = React.useMemo(
    () => new THREE.Vector3(...port.mouth).addScaledVector(new THREE.Vector3(...port.axis), 0.006),
    [port],
  );

  useFrame((_, dt) => {
    const g = group.current;
    if (!g) return;
    const goal = useVehicleStore.getState().openings.charge ? 1 : 0;
    open.current += (goal - open.current) * Math.min(1, dt * 9);
    if (Math.abs(goal - open.current) < 0.004) open.current = goal;
    g.visible = open.current > 0.01;
    g.scale.setScalar(Math.max(open.current, 0.001));
  });

  return (
    <group ref={group} position={pos} quaternion={quat} visible={false}>
      <RoundedBox args={[0.19, 0.15, 0.004]} radius={0.03} smoothness={3} position={[0, 0, 0.002]}>
        <meshStandardMaterial color="#1c1e22" roughness={0.55} metalness={0.2} />
      </RoundedBox>
      <RoundedBox args={[0.17, 0.13, 0.006]} radius={0.026} smoothness={3} position={[0, 0, 0.004]}>
        <meshStandardMaterial color="#0b0c0f" roughness={0.8} />
      </RoundedBox>
      <mesh rotation-x={Math.PI / 2} position={[0, -0.008, 0.01]}>
        <cylinderGeometry args={[0.036, 0.036, 0.016, 32]} />
        <meshStandardMaterial color="#17191d" roughness={0.6} />
      </mesh>
      <mesh position={[0, -0.008, 0.0185]}>
        <torusGeometry args={[0.0345, 0.0035, 10, 40]} />
        <meshStandardMaterial color="#34373d" roughness={0.45} metalness={0.4} />
      </mesh>
      {pins.map((p, i) => (
        <mesh key={i} rotation-x={Math.PI / 2} position={[p.x, p.y - 0.008, 0.0185 - p.long / 2]}>
          <cylinderGeometry args={[p.r, p.r, p.long, 14]} />
          <meshStandardMaterial color={i < 2 ? '#b9923f' : '#8a8d92'} roughness={0.3} metalness={0.9} />
        </mesh>
      ))}
      <mesh position={[0, 0.058, 0.0075]}>
        <boxGeometry args={[0.1, 0.007, 0.003]} />
        <meshBasicMaterial ref={strip} color="#9fb4ff" toneMapped={false} />
      </mesh>
    </group>
  );
}

/** The gun, its nose's tip at the origin and the nose pointing +Z, the grip down (-Y). */
function Gun() {
  const pins = React.useMemo(() => contacts(true), []);
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

/** The pedestal's screen: modern high-tech EV Charger terminal display matching the showroom UI. */
function drawScreen(c: HTMLCanvasElement, r: ChargeReadout) {
  const ctx = c.getContext('2d')!;
  const W = c.width;
  const H = c.height;

  // Screen background with deep dark cyber-blue gradient
  const bgGrad = ctx.createLinearGradient(0, 0, 0, H);
  bgGrad.addColorStop(0, '#09131f');
  bgGrad.addColorStop(0.5, '#060c14');
  bgGrad.addColorStop(1, '#03060a');
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, W, H);

  // Subtle screen frame & glass border
  ctx.strokeStyle = 'rgba(6, 182, 212, 0.25)';
  ctx.lineWidth = 2;
  ctx.strokeRect(3, 3, W - 6, H - 6);

  // Header Bar
  ctx.fillStyle = 'rgba(6, 182, 212, 0.8)';
  ctx.font = '700 11px system-ui, sans-serif';
  ctx.textAlign = 'left';
  ctx.fillText('09:16', 14, 22);

  ctx.fillStyle = '#ffffff';
  ctx.font = '600 11px system-ui, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('⚡ DC FAST CHARGER', W / 2, 22);

  ctx.fillStyle = r.phase === 'charging' ? '#10b981' : '#38bdf8';
  ctx.font = '600 10px system-ui, sans-serif';
  ctx.textAlign = 'right';
  ctx.fillText('800V DC', W - 14, 22);

  // Header divider
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(10, 28);
  ctx.lineTo(W - 10, 28);
  ctx.stroke();

  // Central Circular Charge Progress Meter
  const cx = W / 2;
  const cy = 138;
  const rad = 58;

  // Dark circular track
  ctx.strokeStyle = '#0e1724';
  ctx.lineWidth = 9;
  ctx.beginPath();
  ctx.arc(cx, cy, rad, 0, 2 * Math.PI);
  ctx.stroke();

  // Active glowing progress arc
  const startAngle = -Math.PI / 2;
  const endAngle = startAngle + 2 * Math.PI * Math.min(1, Math.max(0, r.soc));
  ctx.save();
  ctx.strokeStyle = r.phase === 'charging' ? '#10b981' : r.phase === 'charged' ? '#06b6d4' : '#38bdf8';
  ctx.lineWidth = 9;
  ctx.lineCap = 'round';
  ctx.shadowColor = r.phase === 'charging' ? '#10b981' : '#06b6d4';
  ctx.shadowBlur = 10;
  ctx.beginPath();
  ctx.arc(cx, cy, rad, startAngle, endAngle);
  ctx.stroke();
  ctx.restore();

  // Inside the Circular Gauge
  const isCharging = r.phase === 'charging';
  const isCharged = r.phase === 'charged';
  const statusText =
    isCharging ? 'ACTIVE' : isCharged ? 'COMPLETE' : r.phase === 'connecting' ? 'CONNECTING' : 'READY';

  // Status badge pill
  ctx.fillStyle = isCharging ? 'rgba(16, 185, 129, 0.15)' : 'rgba(6, 182, 212, 0.15)';
  ctx.fillRect(cx - 36, cy - 38, 72, 16);
  ctx.strokeStyle = isCharging ? 'rgba(16, 185, 129, 0.4)' : 'rgba(6, 182, 212, 0.4)';
  ctx.lineWidth = 1;
  ctx.strokeRect(cx - 36, cy - 38, 72, 16);

  ctx.fillStyle = isCharging ? '#34d399' : '#38bdf8';
  ctx.font = '600 9px system-ui, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(statusText, cx, cy - 26);

  // Large numeric percentage (Clean, Light, Authoritative)
  ctx.fillStyle = '#ffffff';
  ctx.font = '300 50px system-ui, -apple-system, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(`${Math.round(r.soc * 100)}`, cx, cy + 18);

  // Subtitle
  ctx.fillStyle = 'rgba(165, 243, 252, 0.7)';
  ctx.font = '500 8.5px system-ui, sans-serif';
  ctx.fillText('STATE OF CHARGE', cx, cy + 34);

  // Telemetry Cards: Power
  ctx.fillStyle = '#0f1b2b';
  ctx.fillRect(16, 218, W - 32, 42);
  ctx.strokeStyle = 'rgba(6, 182, 212, 0.2)';
  ctx.lineWidth = 1;
  ctx.strokeRect(16, 218, W - 32, 42);

  // Orange power bar fill
  const powerFraction = Math.min(1, r.kw / 350);
  ctx.fillStyle = 'rgba(245, 158, 11, 0.85)';
  ctx.fillRect(W - 18 - Math.round((W - 120) * powerFraction), 221, Math.round((W - 120) * powerFraction), 36);

  ctx.fillStyle = '#94a3b8';
  ctx.font = '600 9px system-ui, sans-serif';
  ctx.textAlign = 'left';
  ctx.fillText('CHARGING POWER', 26, 235);

  ctx.fillStyle = '#ffffff';
  ctx.font = '600 17px -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif';
  ctx.fillText(`${Math.round(r.kw)} kW`, 26, 252);

  // Bottom 2 columns: Time & Energy
  const cardW = (W - 38) / 2;
  // Left: Time elapsed
  ctx.fillStyle = '#0b131f';
  ctx.fillRect(16, 268, cardW, 40);
  ctx.strokeRect(16, 268, cardW, 40);

  ctx.fillStyle = '#94a3b8';
  ctx.font = '500 8.5px system-ui, sans-serif';
  ctx.textAlign = 'left';
  ctx.fillText('TIME ELAPSED', 24, 283);

  const mm = Math.floor(r.elapsed / 60);
  const ss = Math.floor(r.elapsed % 60);
  ctx.fillStyle = '#ffffff';
  ctx.font = '600 13.5px monospace, sans-serif';
  ctx.fillText(`${mm}:${String(ss).padStart(2, '0')}`, 24, 300);

  // Right: Energy dispensed
  ctx.fillStyle = '#0b131f';
  ctx.fillRect(16 + cardW + 6, 268, cardW, 40);
  ctx.strokeRect(16 + cardW + 6, 268, cardW, 40);

  ctx.fillStyle = '#94a3b8';
  ctx.font = '500 8.5px system-ui, sans-serif';
  ctx.textAlign = 'left';
  ctx.fillText('ENERGY ADDED', 24 + cardW + 6, 283);

  ctx.fillStyle = '#38bdf8';
  ctx.font = '600 13.5px monospace, sans-serif';
  ctx.fillText(`${r.kwh.toFixed(1)} kWh`, 24 + cardW + 6, 300);

  // Bottom Ticker / Status Bar
  ctx.fillStyle = 'rgba(255, 255, 255, 0.04)';
  ctx.fillRect(16, 318, W - 32, 20);
  ctx.fillStyle = isCharging ? '#34d399' : '#38bdf8';
  ctx.font = '600 9px system-ui, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(
    isCharging ? '● ULTRA-FAST LIQUID-COOLED DC' : isCharged ? '● CHARGE COMPLETE' : '● READY TO CONNECT',
    W / 2,
    332,
  );
}

