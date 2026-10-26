'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import type { Vehicle } from '@/data/vehicles/schema';
import type { CityRoad, RoadStage } from '@/lib/tech/carpet';
import { rigOf } from '@/lib/tech/rig';
import { useDusk } from './Lights';
import { STAGE_LAYER } from './StudioShowroom';
import { Signal } from './TechSignal';
import { lampGeometry, treeGeometry } from './TechStreet';

/**
 * The street of Autonomous Drive's city scene (src/lib/tech/scenes/city.ts): asphalt with a line along the parking strip, dashes
 * between the car's lane and the one beside it and a double yellow line down the middle; kerbs and footways on both sides; a row
 * of buildings behind each footway; lamps and trees; and a zebra crossing with its stop lines.
 *
 * Like the expressway (TechRoad's `Highway`) it is drawn so that a still car can drive down it however long the run is: the
 * asphalt, kerbs and footways stand under the car; what repeats (the dashes, the lamps, the trees, the buildings) is laid out over
 * one strip and rolled by the rig as far as its period and no further; the crossing and the stop lines roll with the road.
 * Kept in the studio's own language, as TechStreet is: matte, pale, a little abstract, fading out toward the top and the ends, so
 * it reads as a street model standing in the white room. Road coordinates are the planner's (x along, y left); the viewer's z is -y.
 */

const ASPHALT = '#4b4e54';
const PAINT = '#f1efe8';
const YELLOW = '#e3bf45';
const KERB = 0.15;
const HIGHWAY_FADE_END = 70;
const FADE_SIDE = 0.9;
/** the buildings' height, m */
const FACADE_H = 12.5;

const smooth = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

function onStageLayer(o: THREE.Object3D | null) {
  o?.layers.set(STAGE_LAYER);
}

export function CityStreet({ road, city, vehicle }: { road: RoadStage; city: CityRoad; vehicle: Vehicle }) {
  const rig = rigOf(vehicle);
  const repeating = React.useRef<THREE.Group>(null);
  const rolling = React.useRef<THREE.Group>(null);
  React.useEffect(() => {
    const a = repeating.current;
    const b = rolling.current;
    if (!a || !b) return;
    const offA = rig.attachRoad(a, rig.rac.x, city.period);
    const offB = rig.attachRoad(b, rig.rac.x);
    return () => {
      offA();
      offB();
    };
  }, [rig, city.period, road]);

  const length = road.to - road.from;
  const yc = (city.nearKerb + city.farKerb) / 2;
  const width = city.farKerb - city.nearKerb;
  const P = city.period;
  const mark = { polygonOffset: true, polygonOffsetFactor: -6, polygonOffsetUnits: -6, toneMapped: false, depthWrite: false } as const;

  const asphalt = React.useMemo(() => {
    const W = 1536;
    const H = 128;
    const canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d')!;
    ctx.fillStyle = ASPHALT;
    ctx.fillRect(0, 0, W, H);
    const img = ctx.getImageData(0, 0, W, H);
    const d = img.data;
    let seed = 4711;
    const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296) - 0.5;
    for (let y = 0; y < H; y++) {
      const dy = (Math.min(y, H - 1 - y) / H) * width;
      for (let x = 0; x < W; x++) {
        const dx = (Math.min(x, W - 1 - x) / W) * length;
        const i = (y * W + x) * 4;
        const n = rnd() * 6;
        d[i] += n;
        d[i + 1] += n;
        d[i + 2] += n;
        d[i + 3] = Math.round(255 * smooth(0, FADE_SIDE, dy) * smooth(0, HIGHWAY_FADE_END, dx));
      }
    }
    ctx.putImageData(img, 0, 0);
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 8;
    return tex;
  }, [length, width]);
  React.useEffect(() => () => asphalt.dispose(), [asphalt]);

  // the dashes down the lane line, and the lamps and trees, laid out over the strip at their repeat
  const slots = React.useMemo(() => {
    const out: number[] = [];
    const n = Math.ceil(length / 2 / P) + 1;
    for (let k = -n; k <= n; k++) out.push(k * P);
    return out;
  }, [length, P]);
  const dashPeriod = 6;
  const dashSlots = React.useMemo(() => {
    const out: number[] = [];
    // the strip rolls by P, which the dash period divides
    for (let x = -Math.ceil(length / 2 / P) * P - P; x <= length / 2 + P; x += dashPeriod) out.push(x);
    return out;
  }, [length, P]);

  const dashes = React.useMemo(() => city.lines.filter((l) => l.dash), [city.lines]);
  const solids = React.useMemo(() => city.lines.filter((l) => !l.dash), [city.lines]);
  const dashMesh = React.useRef<THREE.InstancedMesh>(null);
  React.useLayoutEffect(() => {
    const d = dashMesh.current;
    if (!d) return;
    const m = new THREE.Matrix4();
    let i = 0;
    for (const l of dashes) for (const x of dashSlots) d.setMatrixAt(i++, m.makeTranslation(x + 1, -l.y, 0));
    d.count = i;
    d.instanceMatrix.needsUpdate = true;
  }, [dashes, dashSlots]);

  const lamps = React.useRef<THREE.InstancedMesh>(null);
  const trees = React.useRef<THREE.InstancedMesh>(null);
  const geos = React.useMemo(() => ({ lamp: lampGeometry(), tree: treeGeometry() }), []);
  const propMaterial = React.useMemo(() => new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.9, metalness: 0 }), []);
  React.useEffect(
    () => () => {
      geos.lamp.dispose();
      geos.tree.dispose();
      propMaterial.dispose();
    },
    [geos, propMaterial],
  );
  useDusk((d) => propMaterial.color.copy(d.room));
  const nearLamp = city.nearKerb - 0.5;
  const farLamp = city.farKerb + 0.5;
  const nearTree = city.nearKerb - city.footway * 0.55;
  const farTree = city.farKerb + city.footway * 0.55;
  React.useLayoutEffect(() => {
    const o = new THREE.Object3D();
    const L = lamps.current;
    if (L) {
      let i = 0;
      // a lamp on each side, the far ones half a repeat along, their arms over the street
      for (const x of slots) {
        o.position.set(x + P * 0.25, KERB, -nearLamp);
        o.rotation.set(0, Math.PI / 2, 0);
        o.updateMatrix();
        L.setMatrixAt(i++, o.matrix);
        o.position.set(x + P * 0.75, KERB, -farLamp);
        o.rotation.set(0, -Math.PI / 2, 0);
        o.updateMatrix();
        L.setMatrixAt(i++, o.matrix);
      }
      L.count = i;
      L.instanceMatrix.needsUpdate = true;
    }
    const T = trees.current;
    if (T) {
      let i = 0;
      for (const x of slots) {
        o.position.set(x + P * 0.5, KERB, -nearTree);
        o.rotation.set(0, (x * 0.37) % 6.28, 0);
        o.updateMatrix();
        T.setMatrixAt(i++, o.matrix);
        o.position.set(x + P * 0.02, KERB, -farTree);
        o.rotation.set(0, (x * 0.53) % 6.28, 0);
        o.updateMatrix();
        T.setMatrixAt(i++, o.matrix);
      }
      T.count = i;
      T.instanceMatrix.needsUpdate = true;
    }
  }, [slots, P, nearLamp, farLamp, nearTree, farTree]);

  // the zebra bars (along the street, side by side across it) and the stop lines
  const bars = React.useMemo(() => {
    const out: { x: number; y: number; length: number }[] = [];
    for (const c of city.crossings) for (let y = city.nearKerb + 0.55; y < city.farKerb - 0.4; y += 1.0) out.push({ x: c.x, y, length: c.length });
    return out;
  }, [city]);
  const barMesh = React.useRef<THREE.InstancedMesh>(null);
  React.useLayoutEffect(() => {
    const b = barMesh.current;
    if (!b) return;
    const m = new THREE.Matrix4();
    bars.forEach((bar, i) => b.setMatrixAt(i, m.makeTranslation(bar.x, -bar.y, 0)));
    b.count = bars.length;
    b.instanceMatrix.needsUpdate = true;
  }, [bars]);

  return (
    // the street's middle line is the car's own centre line at the start
    <group position-z={-rig.rac.y}>
      <mesh position={[rig.rac.x, 0.002, -yc]} rotation-x={-Math.PI / 2} renderOrder={-0.5} ref={onStageLayer}>
        <planeGeometry args={[length, width]} />
        <meshBasicMaterial map={asphalt} transparent polygonOffset polygonOffsetFactor={-4} polygonOffsetUnits={-4} depthWrite={false} toneMapped={false} />
      </mesh>
      {/* the solid lines: the strip's edge and the double yellow */}
      {solids.map((l, i) => (
        <mesh key={i} position={[rig.rac.x, 0.003, -l.y]} rotation-x={-Math.PI / 2} renderOrder={-0.4} ref={onStageLayer}>
          <planeGeometry args={[length * 0.8, l.color === 'yellow' ? 0.1 : 0.14]} />
          <meshBasicMaterial color={l.color === 'yellow' ? YELLOW : PAINT} transparent opacity={0.92} {...mark} />
        </mesh>
      ))}
      <Kerbs city={city} length={length} x={rig.rac.x} />
      <group position-x={rig.rac.x}>
        <Footways city={city} length={length} />
      </group>
      {/* what repeats: rolled by its period */}
      <group ref={repeating}>
        <instancedMesh ref={dashMesh} args={[undefined, undefined, Math.max(1, dashes.length * dashSlots.length)]} rotation-x={-Math.PI / 2} position-y={0.003} renderOrder={-0.4} frustumCulled={false} onUpdate={onStageLayer}>
          <planeGeometry args={[2, 0.14]} />
          <meshBasicMaterial color={PAINT} transparent opacity={0.92} {...mark} />
        </instancedMesh>
        <instancedMesh ref={lamps} args={[geos.lamp, propMaterial, slots.length * 2]} frustumCulled={false} onUpdate={onStageLayer} />
        <instancedMesh ref={trees} args={[geos.tree, propMaterial, slots.length * 2]} frustumCulled={false} onUpdate={onStageLayer} />
        <Facade side="near" city={city} length={length + 2 * P} period={P} rigY={rig.rac.y} />
        <Facade side="far" city={city} length={length + 2 * P} period={P} rigY={rig.rac.y} />
      </group>
      {/* what rolls with the road: the crossing and its stop lines */}
      <group ref={rolling}>
        <instancedMesh ref={barMesh} args={[undefined, undefined, Math.max(1, bars.length)]} rotation-x={-Math.PI / 2} position-y={0.0035} renderOrder={-0.35} frustumCulled={false} onUpdate={onStageLayer}>
          <planeGeometry args={[city.crossings[0]?.length ?? 4, 0.5]} />
          <meshBasicMaterial color={PAINT} transparent opacity={0.94} {...mark} />
        </instancedMesh>
        {city.stopLines.map((l, i) => (
          <mesh key={i} position={[l.x, 0.0036, -(l.y0 + l.y1) / 2]} rotation-x={-Math.PI / 2} renderOrder={-0.34} ref={onStageLayer}>
            <planeGeometry args={[0.38, l.y1 - l.y0]} />
            <meshBasicMaterial color={PAINT} transparent opacity={0.94} {...mark} />
          </mesh>
        ))}
        {(city.signals ?? []).map((sg, i) => (
          <Signal key={i} signal={sg} />
        ))}
      </group>
    </group>
  );
}

/** The two kerbs: a low stone strip along each side of the carriageway. */
function Kerbs({ city, length, x }: { city: CityRoad; length: number; x: number }) {
  return (
    <>
      {[city.nearKerb - 0.1, city.farKerb + 0.1].map((y) => (
        <mesh key={y} position={[x, KERB / 2, -y]} ref={onStageLayer}>
          <boxGeometry args={[length, KERB, 0.2]} />
          <meshStandardMaterial color="#c9ccd2" roughness={0.9} />
        </mesh>
      ))}
    </>
  );
}

/** A footway on each side, a kerb's height up, paved in a pale grey. */
function Footways({ city, length }: { city: CityRoad; length: number }) {
  const mat = React.useMemo(() => new THREE.MeshStandardMaterial({ color: '#b9bcc3', roughness: 0.95 }), []);
  React.useEffect(() => () => mat.dispose(), [mat]);
  const base = React.useMemo(() => new THREE.Color('#b9bcc3'), []);
  useDusk((d) => mat.color.copy(base).multiply(d.room));
  return (
    <>
      {[city.nearKerb - 0.2 - city.footway / 2, city.farKerb + 0.2 + city.footway / 2].map((y) => (
        <mesh key={y} position={[0, KERB / 2 - 0.004, -y]} material={mat} ref={onStageLayer}>
          <boxGeometry args={[length, KERB, city.footway]} />
        </mesh>
      ))}
    </>
  );
}

/** One painted strip of buildings (shopfronts, windows, party walls), a repeat long, fading into the studio's white toward the top. */
function facadeTexture(period: number): THREE.CanvasTexture {
  const PPM = 36;
  const cw = Math.round(period * PPM);
  const ch = Math.round(FACADE_H * PPM);
  const canvas = document.createElement('canvas');
  canvas.width = cw;
  canvas.height = ch;
  const ctx = canvas.getContext('2d')!;
  const fy = (m: number) => ch - m * PPM;
  const tones = ['#dedbd4', '#d3d2cf', '#e3e0da', '#cdcbc6', '#d9d6cf'];
  // buildings whose widths add up to the repeat
  const widths = [period * 0.4, period * 0.28, period * 0.32];
  let x = 0;
  widths.forEach((wB, b) => {
    const floors = 3 + (b % 2);
    const top = Math.min(FACADE_H, 4.4 + floors * 3.2);
    ctx.fillStyle = tones[(b * 2) % tones.length];
    ctx.fillRect(x * PPM, fy(top), wB * PPM, top * PPM);
    ctx.fillStyle = 'rgba(60,66,76,0.55)';
    ctx.fillRect((x + 0.6) * PPM, fy(3.6), (wB - 1.2) * PPM, 3.0 * PPM);
    ctx.fillStyle = 'rgba(255,255,255,0.35)';
    ctx.fillRect((x + 0.6) * PPM, fy(3.7), (wB - 1.2) * PPM, 0.1 * PPM);
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
    ctx.fillStyle = 'rgba(40,44,52,0.18)';
    ctx.fillRect(x * PPM, 0, 0.08 * PPM, ch);
    x += wB;
  });
  // the fade into the white at the top
  ctx.globalCompositeOperation = 'destination-in';
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
  tex.wrapS = THREE.RepeatWrapping;
  return tex;
}

/**
 * The buildings behind a footway, seen from the street: one long plane whose painted strip repeats every `period` (the group
 * rolls by it, so the windows stream past). The one on the far side would stand between the camera and the car when the camera is
 * out beyond it, so it is hidden then, as TechStreet's is.
 */
function Facade({ side, city, length, period, rigY }: { side: 'near' | 'far'; city: CityRoad; length: number; period: number; rigY: number }) {
  const map = React.useMemo(() => {
    const t = facadeTexture(period);
    t.repeat.set(length / period, 1);
    return t;
  }, [period, length]);
  React.useEffect(() => () => map.dispose(), [map]);
  const mesh = React.useRef<THREE.Mesh>(null);
  const mat = React.useRef<THREE.MeshBasicMaterial>(null);
  // where the buildings stand across the street (m left of the car's lane), and which way they face
  const y = side === 'near' ? city.nearKerb - 0.2 - city.footway - 0.1 : city.farKerb + 0.2 + city.footway + 0.1;
  const zWorld = -rigY - y;
  useFrame(({ camera }) => {
    const m = mesh.current;
    if (!m) return;
    m.visible = side === 'near' ? camera.position.z < zWorld : camera.position.z > zWorld;
  });
  useDusk((d) => mat.current?.color.copy(d.room));
  return (
    <mesh ref={(o) => { mesh.current = o; onStageLayer(o); }} position={[0, FACADE_H / 2 + KERB, -y]} rotation-y={side === 'near' ? Math.PI : 0} renderOrder={-0.6}>
      <planeGeometry args={[length, FACADE_H]} />
      <meshBasicMaterial ref={mat} map={map} transparent depthWrite={false} toneMapped={false} />
    </mesh>
  );
}
