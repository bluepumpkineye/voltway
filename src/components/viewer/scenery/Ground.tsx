'use client';

import React from 'react';
import * as THREE from 'three';
import { useDusk } from '../Lights';
import { smooth, rng, withHaze } from './kit';
import { onStage, useHaze } from './Scenery';
import { ASPHALT, TILE, asphaltDetail, footShade, paintCracks, paintDrain, paintManhole, paintOil, paintPatches, paintTyreTracks, pavingTexture, tactileTexture } from './textures';

/**
 * The ground's shared pieces: how a road's base is painted (tyre tracks, mended patches, cracks, oil) and the two
 * materials that turn a painted canvas into asphalt and paving: unlit, so the studio's white stays white, with a tiled
 * detail texture multiplied over the painted map (the aggregate that a canvas of 50 pixels to the metre cannot hold), and with
 * the haze's distance fall-off.
 */

/** A road's base: asphalt colour, the lanes' tyre tracks, patches, cracks. Positions in canvas pixels; `lanes` are the strips the cars use. */
export function paintAsphaltBase(
  ctx: CanvasRenderingContext2D,
  cw: number,
  ch: number,
  ppm: number,
  lanes: { y: number; w: number }[],
  opts: { seed?: number; patches?: number; cracks?: number; wear?: number } = {},
) {
  const seed = opts.seed ?? 1;
  const L = cw / ppm;
  ctx.fillStyle = ASPHALT;
  ctx.fillRect(0, 0, cw, ch);
  // large soft tonal drift (older and newer surfacing, sun-bleached and shaded stretches)
  const r = rng(seed * 13 + 5);
  for (let i = 0; i < Math.round(L / 6); i++) {
    const x = r() * cw;
    const y = r() * ch;
    const rad = (2 + r() * 6) * ppm;
    const g = ctx.createRadialGradient(x, y, rad * 0.1, x, y, rad);
    const dark = r() > 0.5;
    g.addColorStop(0, dark ? 'rgba(10,11,14,0.14)' : 'rgba(150,152,158,0.10)');
    g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = g;
    ctx.fillRect(x - rad, y - rad, rad * 2, rad * 2);
  }
  const wear = opts.wear ?? 1;
  for (const lane of lanes) if (wear > 0) paintTyreTracks(ctx, 0, cw, lane.y, lane.w, ppm, seed + Math.round(lane.y));
  paintPatches(ctx, cw, ch, opts.patches ?? Math.round(L / 5), ppm, seed + 2);
  paintCracks(ctx, cw, ch, opts.cracks ?? Math.round(L * 0.9), ppm, seed + 3);
  // oil where cars wait: a few dark drips in the lanes
  for (let i = 0; i < Math.round(L / 9); i++) {
    const lane = lanes[Math.floor(r() * Math.max(1, lanes.length))] ?? { y: ch / 2, w: ch * 0.4 };
    paintOil(ctx, r() * cw, lane.y + (r() - 0.5) * lane.w * 0.5, (0.2 + r() * 0.4) * ppm, 0.12 + r() * 0.2);
  }
}

/**
 * Fades the two ends of a painted road to nothing, in place, over `fadeEnd` metres (the white behind takes over). The canvas may
 * be stretched: `lengthM` is the road's length along the canvas's x, whatever its pixels.
 */
export function fadeEdges(ctx: CanvasRenderingContext2D, cw: number, ch: number, ppm: number, fadeEnd: number, fadeSide = 0, lengthM = cw / ppm) {
  const f = Math.min(0.5, fadeEnd / lengthM);
  ctx.save();
  ctx.globalCompositeOperation = 'destination-in';
  const gx = ctx.createLinearGradient(0, 0, cw, 0);
  const stops = [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1];
  // s runs from 0 at the very end to 1 where the fade has finished; the same ramp at both ends, the right one mirrored
  for (const s of stops) gx.addColorStop(s * f, `rgba(0,0,0,${smooth(0, 1, s)})`);
  for (const s of stops) gx.addColorStop(1 - s * f, `rgba(0,0,0,${smooth(0, 1, s)})`);
  ctx.fillStyle = gx;
  ctx.fillRect(0, 0, cw, ch);
  if (fadeSide > 0) {
    const fs = Math.min(0.5, (fadeSide * ppm) / ch);
    const gy = ctx.createLinearGradient(0, 0, 0, ch);
    gy.addColorStop(0, 'rgba(0,0,0,0)');
    gy.addColorStop(fs, 'rgba(0,0,0,1)');
    gy.addColorStop(1 - fs, 'rgba(0,0,0,1)');
    gy.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = gy;
    ctx.fillRect(0, 0, cw, ch);
  }
  ctx.restore();
}

/**
 * The marks a street wears that stream past a moving car: mended patches, cracks, oil, a few manholes and the drains along its
 * kerbs, on a transparent canvas of one repeat (`periodM` x `widthM`, `ppm` pixels to the metre, the top the far kerb). The
 * rolling scenes lay copies of it end to end, so it is seamless at the ends only if nothing crosses them: the marks are kept
 * inside.
 */
export function paintWearStrip(ctx: CanvasRenderingContext2D, periodM: number, widthM: number, ppm: number, seed: number, kerbs = true, intensity = 1) {
  const cw = periodM * ppm;
  const ch = widthM * ppm;
  const r = rng(seed);
  const inner = ctx.canvas;
  void inner;
  paintPatches(ctx, cw - 4 * ppm, ch, Math.round((periodM / 6) * intensity), ppm, seed + 1);
  paintCracks(ctx, cw - 2 * ppm, ch, Math.round(periodM * 0.7 * intensity), ppm, seed + 2);
  for (let i = 0; i < Math.round(periodM / 8); i++) paintOil(ctx, 2 * ppm + r() * (cw - 4 * ppm), r() * ch, (0.2 + r() * 0.4) * ppm, 0.1 + r() * 0.18);
  const mhs = [0.18, 0.55, 0.83];
  mhs.forEach((k, i) => paintManhole(ctx, 2 * ppm + k * (cw - 4 * ppm), ch * (0.3 + 0.22 * ((i * 5) % 3) * 0.5 + r() * 0.1), 0.32 * ppm, ppm));
  if (kerbs) {
    for (let x = 4 + r() * 4; x < periodM - 3; x += 16 + r() * 4) {
      paintDrain(ctx, x * ppm, ch - 0.36 * ppm, 0.8 * ppm, 0.32 * ppm, ppm);
      if (r() > 0.3) paintDrain(ctx, (x + 8) * ppm, 0.04 * ppm, 0.8 * ppm, 0.32 * ppm, ppm);
    }
  }
}

/** The painted road as an unlit material: the map over a plane of L x W metres, the aggregate detail tiled over it. */
export function asphaltMaterial(map: THREE.Texture, L: number, W: number): THREE.MeshBasicMaterial {
  return withHaze(
    new THREE.MeshBasicMaterial({
      map,
      transparent: true,
      depthWrite: false,
      toneMapped: false,
      polygonOffset: true,
      polygonOffsetFactor: -4,
      polygonOffsetUnits: -4,
    }),
    { height: false, distance: true, detail: { map: asphaltDetail(), repeat: new THREE.Vector2(L / TILE.asphalt, W / TILE.asphalt), strength: 0.9 } },
  );
}

/** Paving for a footway of L x W metres: the slab texture repeats every TILE.paving; unlit like the road, vertex alpha fades its ends. */
export function pavingMaterial(): THREE.MeshBasicMaterial {
  return withHaze(
    new THREE.MeshBasicMaterial({
      map: pavingTexture(),
      vertexColors: true,
      transparent: true,
      depthWrite: false,
      toneMapped: false,
      side: THREE.DoubleSide,
    }),
    { height: false, distance: true },
  );
}

/** The kerb's and the edge's faces: plain stone in vertex colours. */
export function stoneMaterial(): THREE.MeshBasicMaterial {
  return withHaze(new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, depthWrite: false, toneMapped: false, side: THREE.DoubleSide }), { height: false, distance: true });
}

// ---------------------------------------------------------------------------------------------- the footway

/** the kerb's height, m */
export const KERB_H = 0.15;

function geometryOf(pos: number[], idx: number[], col: number[], uv?: number[]) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 4));
  if (uv) g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  return g;
}

/**
 * A raised footway along one kerb (floor frame: x along, y left, the viewer's z is -y): its paved top, the kerb stone and its
 * face, the yellow tactile strip, the slab's outer edge, and the soft shade at the foot of the buildings. Strips of quads along x
 * whose alpha fades at both ends, so it lets go of the floor gently. `kerbY` is the road's edge; `side` says which way the footway
 * lies from it ('south': toward lower y).
 */
export function FootwayStrip({ x0, x1, kerbY, foot, side, fade, shade = true }: { x0: number; x1: number; kerbY: number; foot: number; side: 'south' | 'north'; fade: number; shade?: boolean }) {
  const ya = side === 'south' ? kerbY - foot : kerbY;
  const yb = side === 'south' ? kerbY : kerbY + foot;
  const outerY = side === 'south' ? ya : yb;
  const L = x1 - x0;
  const geo = React.useMemo(() => {
    const f = Math.min(fade, L / 3);
    const xs = [x0, x0 + f, x1 - f, x1];
    const al = [0, 1, 1, 0];
    const top = { pos: [] as number[], uv: [] as number[], col: [] as number[], idx: [] as number[] };
    const face = { pos: [] as number[], col: [] as number[], idx: [] as number[] };
    const kerbTop = { pos: [] as number[], col: [] as number[], idx: [] as number[] };
    const tact = { pos: [] as number[], uv: [] as number[], col: [] as number[], idx: [] as number[] };
    const quads = (o: { idx: number[] }) => {
      for (let i = 0; i < 3; i++) o.idx.push(i * 2, i * 2 + 2, i * 2 + 1, i * 2 + 1, i * 2 + 2, i * 2 + 3);
    };
    xs.forEach((x, i) => {
      for (const y of [ya, yb]) {
        top.pos.push(x, KERB_H, -y);
        top.uv.push((x - x0) / TILE.paving, (y - ya) / TILE.paving);
        top.col.push(1, 1, 1, al[i]);
      }
    });
    quads(top);
    for (const [y, shadeK] of [[kerbY, 0.9], [outerY, 0.74]] as const) {
      const base = face.pos.length / 3;
      xs.forEach((x, i) => {
        face.pos.push(x, 0, -y, x, KERB_H, -y);
        face.col.push(0.8 * shadeK, 0.82 * shadeK, 0.85 * shadeK, al[i], shadeK, shadeK, shadeK, al[i]);
      });
      for (let i = 0; i < 3; i++) {
        const a = base + i * 2;
        face.idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3);
      }
    }
    {
      const inner = side === 'south' ? kerbY - 0.18 : kerbY + 0.18;
      xs.forEach((x, i) => {
        for (const y of [inner, kerbY]) {
          kerbTop.pos.push(x, KERB_H + 0.003, -y);
          kerbTop.col.push(0.86, 0.87, 0.9, al[i]);
        }
      });
      quads(kerbTop);
    }
    {
      const a0 = side === 'south' ? kerbY - 0.7 - 0.45 : kerbY + 0.7;
      const b0 = a0 + 0.45;
      xs.forEach((x, i) => {
        [a0, b0].forEach((y, k) => {
          tact.pos.push(x, KERB_H + 0.005, -y);
          tact.uv.push(k, (x - x0) / 0.6);
          tact.col.push(1, 1, 1, al[i]);
        });
      });
      quads(tact);
    }
    return {
      top: geometryOf(top.pos, top.idx, top.col, top.uv),
      face: geometryOf(face.pos, face.idx, face.col),
      kerb: geometryOf(kerbTop.pos, kerbTop.idx, kerbTop.col),
      tact: geometryOf(tact.pos, tact.idx, tact.col, tact.uv),
    };
  }, [x0, x1, side, ya, yb, kerbY, outerY, fade, L]);
  React.useEffect(
    () => () => {
      Object.values(geo).forEach((g) => g.dispose());
    },
    [geo],
  );
  const mats = React.useMemo(() => {
    const tactile = pavingMaterial();
    tactile.map = tactileTexture();
    return { top: pavingMaterial(), face: stoneMaterial(), kerb: stoneMaterial(), tactile };
  }, []);
  React.useEffect(
    () => () => {
      Object.values(mats).forEach((m) => m.dispose());
    },
    [mats],
  );
  useDusk((d) => {
    for (const m of Object.values(mats)) m.color.copy(d.room);
  });
  useHaze();
  return (
    <group ref={onStage}>
      <mesh geometry={geo.top} material={mats.top} ref={onStage} renderOrder={-0.4} />
      <mesh geometry={geo.face} material={mats.face} ref={onStage} renderOrder={-0.4} />
      <mesh geometry={geo.kerb} material={mats.kerb} ref={onStage} renderOrder={-0.39} />
      <mesh geometry={geo.tact} material={mats.tactile} ref={onStage} renderOrder={-0.39} />
      {shade && <FootShade x0={x0} x1={x1} y={outerY} side={side} fade={fade} />}
    </group>
  );
}

/** The soft shade at the foot of the buildings along the footway: ambient occlusion, painted. */
function FootShade({ x0, x1, y, side, fade }: { x0: number; x1: number; y: number; side: 'south' | 'north'; fade: number }) {
  const map = React.useMemo(() => footShade(), []);
  const mat = React.useMemo(
    () => new THREE.MeshBasicMaterial({ map, transparent: true, depthWrite: false, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -5, polygonOffsetUnits: -5 }),
    [map],
  );
  React.useEffect(() => () => mat.dispose(), [mat]);
  useDusk((d) => {
    mat.opacity = 1 - 0.5 * d.night;
  });
  const dir = side === 'south' ? 1 : -1;
  return (
    <mesh position={[(x0 + x1) / 2, KERB_H + 0.006, -(y + dir * 0.9)]} rotation-x={-Math.PI / 2} rotation-z={side === 'south' ? 0 : Math.PI} renderOrder={-0.38} ref={onStage} material={mat}>
      <planeGeometry args={[x1 - x0 - 2 * fade, 1.8]} />
    </mesh>
  );
}
