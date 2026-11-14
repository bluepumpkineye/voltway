'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import type { NomiSpec, Vehicle } from '@/data/vehicles/schema';
import { techClock } from '@/lib/tech/clock';
import { getNomiRun, type Face, type NomiPose } from '@/lib/tech/nomi';

/** The node the rig makes: the head, its face and its eyes, its origin at the sphere's centre. */
export const NOMI_NODE = 'NomiHead';

const DEG = Math.PI / 180;
const REST: NomiPose = { yaw: 0, pitch: 0, face: 'idle' };

interface FaceCanvas {
  ctx: CanvasRenderingContext2D;
  tex: THREE.CanvasTexture;
  key: string;
}

/**
 * Hang NOMI's head on a pivot so it can turn and nod, and stand it clear of the centre screen.
 *
 * The cabin export keeps the head sphere, the face disc and the two eyes as nodes of their own, each with its geometry in the cabin's space.
 * They become children of a group at the sphere's centre, raised by `spec.lift` (the model has the sphere low enough for the centre screen
 * to hide it from the driver's seat), and a short neck of the pedestal's own material joins it to the pedestal. The face is a round
 * quad over the glass, with a canvas drawn live (the eyes of the model are tubes that cannot change shape: they are hidden). The
 * pivot's turn is the demo's (`NomiDriver`). Idempotent: a clone of an already rigged cabin returns its pivot.
 */
export function rigNomi(root: THREE.Object3D, spec: NomiSpec): THREE.Group | null {
  const done = root.getObjectByName(NOMI_NODE);
  if (done) return done as THREE.Group;
  const head = root.getObjectByName('int_nomi_head');
  if (!head) return null;
  const parts = ['int_nomi_head', 'int_nomi_face', 'int_nomi_eye_L', 'int_nomi_eye_R']
    .map((n) => root.getObjectByName(n))
    .filter((o): o is THREE.Object3D => Boolean(o));
  const pedestal = root.getObjectByName('int_nomi_pedestal') as THREE.Mesh | undefined;
  const parent = head.parent ?? root;

  const c = new THREE.Vector3(...spec.head);
  // drawn larger for the demo's sake, about the sphere's centre: raised so its underside stays where it was (on the neck)
  const k = spec.scale ?? 1;
  const pivot = new THREE.Group();
  pivot.name = NOMI_NODE;
  pivot.rotation.order = 'YZX';
  pivot.position.set(c.x, c.y + spec.lift + (k - 1) * spec.radius, c.z);
  pivot.scale.setScalar(k);
  parent.add(pivot);
  for (const o of parts) {
    o.position.sub(c);
    pivot.add(o);
  }
  // the model's eyes are two lit tubes: the drawn face replaces them
  for (const n of ['int_nomi_eye_L', 'int_nomi_eye_R']) {
    const eye = pivot.getObjectByName(n);
    if (eye) eye.visible = false;
  }

  // the neck: from inside the pedestal to inside the sphere
  const y0 = c.y - spec.radius - 0.004;
  const y1 = c.y + spec.lift + (k - 1) * spec.radius - spec.radius * k * 0.55;
  const neckMat = pedestal ? (Array.isArray(pedestal.material) ? pedestal.material[0] : pedestal.material).clone() : new THREE.MeshStandardMaterial({ color: '#1b1d21', roughness: 0.5 });
  const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.0125 * k, 0.0165 * k, y1 - y0, 24), neckMat);
  neck.name = 'int_nomi_neck';
  neck.position.set(c.x, (y0 + y1) / 2, c.z);
  neck.castShadow = neck.receiveShadow = false;
  parent.add(neck);

  // the face: a round quad lying on the glass, its right the passenger's side (z) and its top up
  const n = new THREE.Vector3(...spec.face.normal).normalize();
  const x = new THREE.Vector3(0, 1, 0).cross(n).normalize();
  const y = n.clone().cross(x);
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 256;
  const ctx = canvas.getContext('2d')!;
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  const quad = new THREE.Mesh(
    new THREE.CircleGeometry(spec.face.radius * 0.97, 48),
    new THREE.MeshBasicMaterial({ map: tex, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }),
  );
  quad.name = 'int_nomi_screen';
  quad.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, n));
  quad.position.set(spec.face.at[0] - c.x, spec.face.at[1] - c.y, spec.face.at[2] - c.z).addScaledVector(n, 0.0026);
  quad.raycast = () => {};
  pivot.add(quad);
  const fc: FaceCanvas = { ctx, tex, key: '' };
  pivot.userData.face = fc;
  drawFace(fc, 'idle', -1);
  return pivot;
}

/** Turns and nods the rigged head to the pose the demo's clock asks for, and draws the face it has then. It asks for a frame only while a demo is on. */
export function NomiDriver({ vehicle }: { vehicle: Vehicle }) {
  const spec = vehicle.nomi;
  const scene = useThree((s) => s.scene);
  const pivot = React.useRef<THREE.Object3D | null>(null);

  useFrame(() => {
    if (!spec) return;
    if (!pivot.current || !pivot.current.parent) pivot.current = scene.getObjectByName(NOMI_NODE) ?? null;
    const node = pivot.current;
    if (!node) return;
    const run = getNomiRun();
    const p = run ? run.pose(techClock.t) : REST;
    node.rotation.y = p.yaw * DEG;
    node.rotation.z = p.pitch * DEG;
    const fc = node.userData.face as FaceCanvas | undefined;
    if (fc) drawFace(fc, p.face, run ? techClock.t : -1);
  });
  return null;
}

// ---------------------------------------------------------------- the face

const CYAN = '#8be9ff';
const ROSE = '#ff9fb8';

/** The face for this expression at time t (negative: no demo is running, so nothing moves). Redrawn only when it would look different. */
function drawFace(fc: FaceCanvas, face: Face, t: number) {
  const live = t >= 0;
  const blink = live && face === 'idle' && t % 3.4 < 0.11;
  const beat = live && (face === 'listening' || face === 'music') ? Math.floor(t * 14) : 0;
  const key = `${face}|${blink ? 1 : 0}|${beat}`;
  if (key === fc.key) return;
  fc.key = key;
  const { ctx, tex } = fc;
  const S = 256;
  ctx.clearRect(0, 0, S, S);
  const bg = ctx.createRadialGradient(S / 2, S / 2, S * 0.1, S / 2, S / 2, S * 0.52);
  bg.addColorStop(0, '#0b1016');
  bg.addColorStop(1, '#020305');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, S, S);
  ctx.lineCap = 'round';
  ctx.shadowColor = CYAN;
  ctx.shadowBlur = 14;
  ctx.strokeStyle = CYAN;
  ctx.fillStyle = CYAN;

  const ex = (side: -1 | 1) => S / 2 + side * S * 0.19;
  const ey = S * 0.46;
  // an open eye: a rounded upright oval
  const oval = (side: -1 | 1, w: number, h: number, dy = 0) => {
    ctx.beginPath();
    ctx.ellipse(ex(side), ey + dy, w, h, 0, 0, Math.PI * 2);
    ctx.fill();
  };
  // a happy eye: an arch, ^
  const arch = (side: -1 | 1, w: number, dy = 0) => {
    ctx.lineWidth = 15;
    ctx.beginPath();
    ctx.arc(ex(side), ey + w * 0.55 + dy, w, Math.PI * 1.12, Math.PI * 1.88);
    ctx.stroke();
  };

  if (face === 'idle') {
    if (blink) {
      ctx.lineWidth = 11;
      for (const s of [-1, 1] as const) {
        ctx.beginPath();
        ctx.moveTo(ex(s) - 22, ey);
        ctx.lineTo(ex(s) + 22, ey);
        ctx.stroke();
      }
    } else {
      oval(-1, 20, 31);
      oval(1, 20, 31);
    }
  } else if (face === 'hello' || face === 'happy') {
    arch(-1, 30);
    arch(1, 30);
    // cheeks
    ctx.shadowColor = ROSE;
    ctx.shadowBlur = 18;
    ctx.fillStyle = ROSE;
    for (const s of [-1, 1] as const) {
      ctx.globalAlpha = 0.55;
      ctx.beginPath();
      ctx.ellipse(ex(s) + s * 22, ey + 56, 17, 9, 0, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  } else if (face === 'listening') {
    oval(-1, 23, 34, -6);
    oval(1, 23, 34, -6);
    // a level meter under the eyes: the bars rise and fall with the voice
    ctx.lineWidth = 12;
    for (let i = 0; i < 7; i++) {
      const h = 10 + 26 * Math.abs(Math.sin(beat * 0.9 + i * 1.7)) * (1 - Math.abs(i - 3) * 0.14);
      const x = S / 2 + (i - 3) * 22;
      ctx.beginPath();
      ctx.moveTo(x, S * 0.78 - h / 2);
      ctx.lineTo(x, S * 0.78 + h / 2);
      ctx.stroke();
    }
  } else {
    // music: eyes bouncing on the beat, two notes drifting up
    const bob = Math.sin(beat * 0.45) * 7;
    arch(-1, 28, bob);
    arch(1, 28, bob);
    ctx.shadowBlur = 8;
    ctx.font = '600 56px system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.globalAlpha = 0.9;
    ctx.fillText('♪', S * 0.2, S * 0.78 - ((beat * 2) % 28));
    ctx.fillText('♫', S * 0.8, S * 0.7 - ((beat * 2 + 14) % 28));
    ctx.globalAlpha = 1;
  }
  tex.needsUpdate = true;
}
