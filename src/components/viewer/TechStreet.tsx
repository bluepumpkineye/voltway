'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { dressLot, type StreetProp, type StreetStage } from '@/lib/tech/street';
import { useVehicleStore } from '@/store/vehicle-store';
import { useDusk } from './Lights';
import { STAGE_LAYER } from './StudioShowroom';
import { Neighbour, TONES } from './TechStage';

/**
 * The street a chassis demo drives in (the Z9's crab walk and compass turn, the G9L's U-turn): the road with its
 * painted lines, raised footways and kerbs, a row of buildings behind the far footway, lamp posts, trees, bollards,
 * and the parked cars. The geometry is the stage the demo's planner made (src/lib/tech/street.ts); this only draws it.
 *
 * Everything but the parked cars is on the studio's stage layer, as TechStage's asphalt is: the studio's camera sees it, the
 * city world's does not, and the floor's mirror never reflects it.
 *
 * Kept in the studio's own language: matte, pale and a little abstract, a model of a street standing in the white
 * room, fading out at its ends and (the buildings) toward the top, so it reads as a place and never as a backdrop
 * photograph. Floor coordinates are the kinematics' (x forward, y left); the viewer's z is -y.
 */
export function TechStreet() {
  const street = useVehicleStore((s) => s.techStreet);
  if (!street) return null;
  return <Street street={street} />;
}

const ASPHALT = '#4b4e54';
const PAINT = '#f1efe8';
/** how far the road and footways fade out at their ends, m */
const FADE = 5;
/** the kerb's height, m */
const KERB = 0.15;

const smooth = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

function onStageLayer(o: THREE.Object3D | null) {
  o?.layers.set(STAGE_LAYER);
}

/**
 * The same planted strip, lamps, trees and buildings behind a parking lot's bays (the lot itself is TechStage's): a lot
 * and a street are one place. Seen from the lane, as the camera looks.
 */
export function TechLotDressing() {
  const lot = useVehicleStore((s) => s.techScene);
  const street = React.useMemo(() => (lot ? dressLot(lot) : null), [lot]);
  if (!street) return null;
  return (
    <group>
      <Footway street={street} side="south" />
      <Facade street={street} />
      <Props street={street} />
    </group>
  );
}

function Street({ street }: { street: StreetStage }) {
  return (
    <group>
      <Road street={street} />
      {street.footways.south > 0 && <Footway street={street} side="south" />}
      {street.footways.north > 0 && <Footway street={street} side="north" />}
      {street.footways.south > 0 && <Facade street={street} />}
      {street.wall && <DeadEnd street={street} />}
      <Props street={street} />
      {street.cars.map((c, i) => (
        <React.Suspense key={`${c.slug}-${i}-${c.rect.x.toFixed(1)}`} fallback={null}>
          <Neighbour n={c} tone={TONES[i % TONES.length]} />
        </React.Suspense>
      ))}
    </group>
  );
}

// ----------------------------------------------------------------------------------------------- the road

function Road({ street }: { street: StreetStage }) {
  const { road, lines, bays } = street;
  const L = road.x1 - road.x0;
  const W = road.y1 - road.y0;
  const map = React.useMemo(() => {
    const PPM = Math.min(56, 3000 / L);
    const cw = Math.round(L * PPM);
    const ch = Math.round(W * PPM);
    const canvas = document.createElement('canvas');
    canvas.width = cw;
    canvas.height = ch;
    const ctx = canvas.getContext('2d')!;
    ctx.fillStyle = ASPHALT;
    ctx.fillRect(0, 0, cw, ch);
    const px = (x: number) => (x - road.x0) * PPM;
    const py = (y: number) => (road.y1 - y) * PPM;

    // the gutter along each kerb, and a few patches where the asphalt has been mended
    ctx.fillStyle = 'rgba(18,19,22,0.20)';
    ctx.fillRect(0, py(road.y0 + 0.4), cw, 0.4 * PPM);
    ctx.fillRect(0, 0, cw, 0.4 * PPM);
    let seed = 4242;
    const rnd = () => (seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296;
    for (let i = 0; i < Math.round(L / 3); i++) {
      ctx.fillStyle = `rgba(${rnd() > 0.5 ? '30,32,36' : '92,95,101'},${0.1 + rnd() * 0.12})`;
      const w = (0.6 + rnd() * 2.2) * PPM;
      const h = (0.3 + rnd() * 1.2) * PPM;
      ctx.fillRect(rnd() * (cw - w), rnd() * (ch - h), w, h);
    }

    // painted lines
    ctx.fillStyle = PAINT;
    for (const ln of lines) {
      const lw = (ln.width ?? 0.12) * PPM;
      if (!ln.dash) {
        ctx.fillRect(px(ln.x0), py(ln.y) - lw / 2, (ln.x1 - ln.x0) * PPM, lw);
      } else {
        for (let x = ln.x0; x < ln.x1; x += 5) ctx.fillRect(px(x), py(ln.y) - lw / 2, Math.min(2, ln.x1 - x) * PPM, lw);
      }
    }
    // bays: the outline of a box
    ctx.strokeStyle = PAINT;
    ctx.lineWidth = 0.1 * PPM;
    for (const b of bays) {
      ctx.strokeRect(px(b.x - b.length / 2), py(b.y + b.width / 2), b.length * PPM, b.width * PPM);
    }
    // a pair of manhole covers
    for (const [mx, my] of [[road.x0 + L * 0.31, (road.y0 + road.y1) / 2 + W * 0.18], [road.x0 + L * 0.72, (road.y0 + road.y1) / 2 - W * 0.12]]) {
      ctx.fillStyle = 'rgba(28,29,33,0.7)';
      ctx.beginPath();
      ctx.arc(px(mx), py(my), 0.32 * PPM, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = 'rgba(120,123,130,0.5)';
      ctx.lineWidth = 0.03 * PPM;
      ctx.stroke();
    }

    // grain, and the faded ends
    const img = ctx.getImageData(0, 0, cw, ch);
    const d = img.data;
    for (let y = 0; y < ch; y++) {
      for (let x = 0; x < cw; x++) {
        const i = (y * cw + x) * 4;
        const n = (rnd() - 0.5) * 8;
        d[i] += n;
        d[i + 1] += n;
        d[i + 2] += n;
        d[i + 3] = Math.round(255 * smooth(0, FADE, Math.min(x, cw - 1 - x) / PPM));
      }
    }
    ctx.putImageData(img, 0, 0);
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 8;
    return tex;
  }, [road, lines, bays, L, W]);
  React.useEffect(() => () => map.dispose(), [map]);
  const mat = React.useRef<THREE.MeshBasicMaterial>(null);
  useDusk((d) => mat.current?.color.copy(d.room));
  return (
    <mesh position={[(road.x0 + road.x1) / 2, 0.003, -(road.y0 + road.y1) / 2]} rotation-x={-Math.PI / 2} renderOrder={-0.5} ref={onStageLayer}>
      <planeGeometry args={[L, W]} />
      <meshBasicMaterial ref={mat} map={map} transparent depthWrite={false} toneMapped={false} polygonOffset polygonOffsetFactor={-4} polygonOffsetUnits={-4} />
    </mesh>
  );
}

// ------------------------------------------------------------------------------------------- footways

/**
 * A raised footway along one kerb: its top (paving, a pale stone along the kerb), the kerb's face and the slab's
 * outer edge. One strip of quads along x whose alpha fades at both ends, so it lets go of the floor gently.
 */
function Footway({ street, side }: { street: StreetStage; side: 'south' | 'north' }) {
  const { road } = street;
  const w = side === 'south' ? street.footways.south : street.footways.north;
  const ya = side === 'south' ? road.y0 - w : road.y1;
  const yb = side === 'south' ? road.y0 : road.y1 + w;
  const L = road.x1 - road.x0;

  const geo = React.useMemo(() => {
    const xs = [road.x0, road.x0 + FADE, road.x1 - FADE, road.x1];
    const al = [0, 1, 1, 0];
    const top = { pos: [] as number[], uv: [] as number[], col: [] as number[], idx: [] as number[] };
    const face = { pos: [] as number[], col: [] as number[], idx: [] as number[] };
    // the top: two vertices across for each column
    xs.forEach((x, i) => {
      for (const [y, v] of [[ya, 0], [yb, 1]] as const) {
        top.pos.push(x, KERB, -y);
        top.uv.push((x - road.x0) / L, v);
        top.col.push(1, 1, 1, al[i]);
      }
    });
    for (let i = 0; i < 3; i++) top.idx.push(i * 2, i * 2 + 2, i * 2 + 1, i * 2 + 1, i * 2 + 2, i * 2 + 3);
    // the faces: the kerb (road side) and the outer edge, each a strip from the floor to the top
    const kerbY = side === 'south' ? yb : ya;
    const outerY = side === 'south' ? ya : yb;
    for (const [y, shade] of [[kerbY, 0.93], [outerY, 0.78]] as const) {
      const base = face.pos.length / 3;
      xs.forEach((x, i) => {
        face.pos.push(x, 0, -y, x, KERB, -y);
        face.col.push(shade, shade, shade, al[i], shade, shade, shade, al[i]);
      });
      for (let i = 0; i < 3; i++) {
        const a = base + i * 2;
        face.idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3);
      }
    }
    const make = (pos: number[], idx: number[], col: number[], uv?: number[]) => {
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
      g.setAttribute('color', new THREE.Float32BufferAttribute(col, 4));
      if (uv) g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
      g.setIndex(idx);
      return g;
    };
    return { top: make(top.pos, top.idx, top.col, top.uv), face: make(face.pos, face.idx, face.col) };
  }, [road, side, ya, yb, L]);
  React.useEffect(
    () => () => {
      geo.top.dispose();
      geo.face.dispose();
    },
    [geo],
  );

  const paving = React.useMemo(() => {
    const PPM = Math.min(44, 3000 / L);
    const cw = Math.round(L * PPM);
    const ch = Math.round(w * PPM);
    const canvas = document.createElement('canvas');
    canvas.width = cw;
    canvas.height = ch;
    const ctx = canvas.getContext('2d')!;
    ctx.fillStyle = '#c9cbd0';
    ctx.fillRect(0, 0, cw, ch);
    // slabs: joints every 0.6 m along, every 0.6 m across
    ctx.strokeStyle = 'rgba(80,84,92,0.30)';
    ctx.lineWidth = Math.max(1, 0.012 * PPM);
    for (let x = 0; x < L; x += 0.6) {
      ctx.beginPath();
      ctx.moveTo(x * PPM, 0);
      ctx.lineTo(x * PPM, ch);
      ctx.stroke();
    }
    for (let y = 0; y < w; y += 0.6) {
      ctx.beginPath();
      ctx.moveTo(0, y * PPM);
      ctx.lineTo(cw, y * PPM);
      ctx.stroke();
    }
    // the kerb stone: a paler band along the road's edge
    ctx.fillStyle = '#dddfe3';
    const band = 0.2 * PPM;
    ctx.fillRect(0, side === 'south' ? ch - band : 0, cw, band);
    // a little tone from slab to slab
    let seed = 99;
    const rnd = () => (seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296;
    for (let i = 0; i < L * w * 0.25; i++) {
      ctx.fillStyle = `rgba(${rnd() > 0.5 ? '255,255,255' : '60,62,68'},0.05)`;
      ctx.fillRect(Math.floor((rnd() * L) / 0.6) * 0.6 * PPM, Math.floor((rnd() * w) / 0.6) * 0.6 * PPM, 0.6 * PPM, 0.6 * PPM);
    }
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 8;
    return tex;
  }, [L, w, side]);
  React.useEffect(() => () => paving.dispose(), [paving]);

  const top = React.useRef<THREE.MeshBasicMaterial>(null);
  const face = React.useRef<THREE.MeshBasicMaterial>(null);
  useDusk((d) => {
    top.current?.color.copy(d.room);
    face.current?.color.set('#c4c7cd').multiply(d.room);
  });
  return (
    <group ref={onStageLayer}>
      <mesh geometry={geo.top} ref={onStageLayer} renderOrder={-0.4}>
        <meshBasicMaterial ref={top} map={paving} vertexColors transparent depthWrite={false} toneMapped={false} side={THREE.DoubleSide} />
      </mesh>
      <mesh geometry={geo.face} ref={onStageLayer} renderOrder={-0.4}>
        <meshBasicMaterial ref={face} color="#c4c7cd" vertexColors transparent depthWrite={false} toneMapped={false} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
}

// ------------------------------------------------------------------------------------- the buildings

/**
 * A row of buildings behind the far footway: one painted plane, windows and shopfronts, fading out at its ends and toward
 * the top into the studio's white. It stands on the car's right (the kerb side), so a camera on the other side looks at it;
 * seen from behind it would only be in the way, so it is hidden when the camera is past it.
 */
function Facade({ street }: { street: StreetStage }) {
  const { road, footways } = street;
  const yF = road.y0 - footways.south - 0.05;
  const L = road.x1 - road.x0;
  const H = 13;
  const map = React.useMemo(() => {
    const PPM = Math.min(36, 3600 / L);
    const cw = Math.round(L * PPM);
    const ch = Math.round(H * PPM);
    const canvas = document.createElement('canvas');
    canvas.width = cw;
    canvas.height = ch;
    const ctx = canvas.getContext('2d')!;
    const fy = (m: number) => ch - m * PPM;
    // buildings of different tone, side by side
    let seed = 31337;
    const rnd = () => (seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296;
    const tones = ['#dedbd4', '#d3d2cf', '#e3e0da', '#cdcbc6', '#d9d6cf'];
    let x = 0;
    while (x < L) {
      const wB = 8 + rnd() * 9;
      const tone = tones[Math.floor(rnd() * tones.length)];
      const floors = 3 + Math.floor(rnd() * 3);
      ctx.fillStyle = tone;
      ctx.fillRect(x * PPM, fy(Math.min(H, 4.4 + floors * 3.2)), wB * PPM, Math.min(H, 4.4 + floors * 3.2) * PPM);
      // the shopfront
      ctx.fillStyle = 'rgba(60,66,76,0.55)';
      ctx.fillRect((x + 0.6) * PPM, fy(3.6), (wB - 1.2) * PPM, 3.0 * PPM);
      ctx.fillStyle = 'rgba(255,255,255,0.35)';
      ctx.fillRect((x + 0.6) * PPM, fy(3.7), (wB - 1.2) * PPM, 0.1 * PPM);
      // the windows
      for (let f = 0; f < floors; f++) {
        const yy = 4.4 + f * 3.2 + 0.7;
        for (let wx = x + 1.2; wx < x + wB - 1.6; wx += 2.6) {
          ctx.fillStyle = 'rgba(86,96,110,0.62)';
          ctx.fillRect(wx * PPM, fy(yy + 1.6), 1.4 * PPM, 1.6 * PPM);
          ctx.fillStyle = 'rgba(255,255,255,0.22)';
          ctx.fillRect(wx * PPM, fy(yy + 1.6), 1.4 * PPM, 0.12 * PPM);
        }
        ctx.fillStyle = 'rgba(40,44,52,0.10)';
        ctx.fillRect(x * PPM, fy(yy - 0.7), wB * PPM, 0.1 * PPM);
      }
      // party walls
      ctx.fillStyle = 'rgba(40,44,52,0.18)';
      ctx.fillRect(x * PPM, 0, 0.08 * PPM, ch);
      x += wB;
    }
    // the fade: the ends, and the top into the white
    ctx.globalCompositeOperation = 'destination-in';
    const gx = ctx.createLinearGradient(0, 0, cw, 0);
    const fx = Math.min(0.2, (FADE * 1.3) / L);
    gx.addColorStop(0, 'rgba(0,0,0,0)');
    gx.addColorStop(fx, 'rgba(0,0,0,1)');
    gx.addColorStop(1 - fx, 'rgba(0,0,0,1)');
    gx.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = gx;
    ctx.fillRect(0, 0, cw, ch);
    const gy = ctx.createLinearGradient(0, 0, 0, ch);
    gy.addColorStop(0, 'rgba(0,0,0,0)');
    gy.addColorStop(0.5, 'rgba(0,0,0,0.85)');
    gy.addColorStop(0.72, 'rgba(0,0,0,1)');
    gy.addColorStop(1, 'rgba(0,0,0,1)');
    ctx.fillStyle = gy;
    ctx.fillRect(0, 0, cw, ch);
    ctx.globalCompositeOperation = 'source-over';
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 8;
    return tex;
  }, [L]);
  React.useEffect(() => () => map.dispose(), [map]);
  const mesh = React.useRef<THREE.Mesh>(null);
  const mat = React.useRef<THREE.MeshBasicMaterial>(null);
  const camera = useThree((s) => s.camera);
  useFrame(() => {
    // the far side of the facade: hide it, the camera has gone round behind the buildings
    if (mesh.current) mesh.current.visible = camera.position.z < -yF;
  });
  useDusk((d) => mat.current?.color.copy(d.room));
  return (
    <mesh ref={(o) => { mesh.current = o; onStageLayer(o); }} position={[(road.x0 + road.x1) / 2, H / 2 + KERB, -yF]} rotation-y={Math.PI} renderOrder={-0.6}>
      <planeGeometry args={[L, H]} />
      <meshBasicMaterial ref={mat} map={map} transparent depthWrite={false} toneMapped={false} />
    </mesh>
  );
}

// ------------------------------------------------------------------------------------------- the dead end

function DeadEnd({ street }: { street: StreetStage }) {
  const { road, footways } = street;
  const x = street.wall!.x + 0.25;
  const y0 = road.y0 - footways.south;
  const y1 = road.y1 + footways.north;
  const mat = React.useRef<THREE.MeshStandardMaterial>(null);
  useDusk((d) => mat.current?.color.set('#d9d6d0').multiply(d.room));
  return (
    <group position={[x, 0, -(y0 + y1) / 2]}>
      {/* the wall, with a coping on top */}
      <mesh position={[0, 1.4, 0]} ref={onStageLayer}>
        <boxGeometry args={[0.5, 2.8, y1 - y0]} />
        <meshStandardMaterial ref={mat} color="#d9d6d0" roughness={0.95} />
      </mesh>
      <mesh position={[0, 2.86, 0]} ref={onStageLayer}>
        <boxGeometry args={[0.66, 0.12, y1 - y0 + 0.16]} />
        <meshStandardMaterial color="#b9b6b0" roughness={0.9} />
      </mesh>
    </group>
  );
}

// ------------------------------------------------------------------------------------------ the props

export function paint(g: THREE.BufferGeometry, hex: string): THREE.BufferGeometry {
  const c = new THREE.Color(hex);
  const n = g.getAttribute('position').count;
  const col = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) col.set([c.r, c.g, c.b], i * 3);
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  return g;
}

/** Non-indexed pieces with one colour each, merged into a single geometry (one draw call a prop). */
export function merged(parts: THREE.BufferGeometry[]): THREE.BufferGeometry {
  const flat = parts.map((p) => {
    const g = p.index ? p.toNonIndexed() : p;
    g.deleteAttribute('uv');
    return g;
  });
  return mergeGeometries(flat)!;
}

export function lampGeometry() {
  const pole = new THREE.CylinderGeometry(0.045, 0.07, 5.4, 10).translate(0, 2.7, 0);
  const foot = new THREE.CylinderGeometry(0.11, 0.14, 0.5, 10).translate(0, 0.25, 0);
  const arm = new THREE.BoxGeometry(1.5, 0.07, 0.07).translate(0.72, 5.42, 0);
  const head = new THREE.BoxGeometry(0.62, 0.09, 0.24).translate(1.4, 5.38, 0);
  const lens = new THREE.BoxGeometry(0.5, 0.02, 0.18).translate(1.4, 5.325, 0);
  return merged([paint(pole, '#9ea3ab'), paint(foot, '#8d9199'), paint(arm, '#9ea3ab'), paint(head, '#b9bdc4'), paint(lens, '#f5f1e4')]);
}

export function treeGeometry() {
  const trunk = new THREE.CylinderGeometry(0.07, 0.11, 2.3, 8).translate(0, 1.15, 0);
  const pit = new THREE.CylinderGeometry(0.55, 0.55, 0.03, 18).translate(0, 0.015, 0);
  const crown = (r: number, x: number, y: number, z: number, hex: string) => paint(new THREE.IcosahedronGeometry(r, 1).translate(x, y, z), hex);
  return merged([
    paint(trunk, '#7b7566'),
    paint(pit, '#8f9298'),
    crown(0.95, 0, 3.0, 0, '#b3c0ad'),
    crown(0.78, 0.5, 3.55, 0.2, '#a5b4a0'),
    crown(0.74, -0.42, 3.75, -0.25, '#bccab6'),
    crown(0.62, 0.08, 4.2, 0.15, '#aebdaa'),
  ]);
}

function bollardGeometry() {
  const post = new THREE.CylinderGeometry(0.09, 0.1, 0.85, 12).translate(0, 0.425, 0);
  const band = new THREE.CylinderGeometry(0.092, 0.092, 0.08, 12).translate(0, 0.66, 0);
  return merged([paint(post, '#8e9299'), paint(band, '#f1efe8')]);
}

function Props({ street }: { street: StreetStage }) {
  const geos = React.useMemo(() => ({ lamp: lampGeometry(), tree: treeGeometry(), bollard: bollardGeometry() }), []);
  const material = React.useMemo(() => new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.9, metalness: 0 }), []);
  React.useEffect(
    () => () => {
      for (const g of Object.values(geos)) g.dispose();
      material.dispose();
    },
    [geos, material],
  );
  useDusk((d) => material.color.copy(d.room));
  const { road } = street;
  // the lamps and the trees stand on the footways, which are a kerb's height up
  const height = (p: StreetProp) => (p.y < road.y0 || p.y > road.y1 ? KERB : 0);
  return (
    <group>
      {street.props.map((p, i) => (
        <mesh key={i} ref={onStageLayer} geometry={geos[p.kind]} material={material} position={[p.x, height(p), -p.y]} rotation-y={p.yaw ?? (i * 2.4) % (Math.PI * 2)} />
      ))}
    </group>
  );
}
