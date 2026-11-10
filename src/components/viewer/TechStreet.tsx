'use client';

import React from 'react';
import * as THREE from 'three';
import { dressLot, type StreetProp, type StreetPropKind, type StreetStage } from '@/lib/tech/street';
import { useVehicleStore } from '@/store/vehicle-store';
import { useDusk } from './Lights';
import { Neighbour, TONES } from './TechStage';
import { FootwayStrip, asphaltMaterial, fadeEdges, paintAsphaltBase } from './scenery/Ground';
import { rng } from './scenery/kit';
import { BuildingRow, Props, Trees, onStage, useHaze, type Spot } from './scenery/Scenery';
import { brickTexture, paintArrow, paintDrain, paintManhole, treePit, wearPaint, PAINT } from './scenery/textures';
import { PROP_DOT, type PropKind } from './scenery/props';

/**
 * The street a chassis demo drives in (the Z9's crab walk and compass turn, the G9L's U-turn): the road with its worn
 * paint, tyre tracks, patches, cracks, drains and manholes; raised paved footways with a kerb, a tactile strip and tree
 * pits; a row of real buildings (shopfronts and signboards below, flats, a tower or a mall above) behind the far footway;
 * lamps, street trees, hedges, benches, bins, a bus shelter, shared bikes, signs; and the parked cars. The geometry is the
 * stage the demo's planner made (src/lib/tech/street.ts); this only draws it, with the kit in ./scenery.
 *
 * Everything but the parked cars is on the studio's stage layer, as TechStage's asphalt is: the studio's camera sees it, the
 * city world's does not, and the floor's mirror never reflects it. Floor coordinates are the kinematics' (x forward, y left);
 * the viewer's z is -y.
 */
export function TechStreet() {
  const street = useVehicleStore((s) => s.techStreet);
  if (!street) return null;
  return <Street street={street} />;
}

/** how far the road and footways fade out at their ends, m */
const FADE = 5;
/** the kerb's height, m */
const KERB = 0.15;

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
      <Buildings street={street} south />
      <StreetProps street={street} />
    </group>
  );
}

function Street({ street }: { street: StreetStage }) {
  return (
    <group>
      <Road street={street} />
      {street.footways.south > 0 && <Footway street={street} side="south" />}
      {street.footways.north > 0 && <Footway street={street} side="north" />}
      <Buildings street={street} south={street.footways.south > 0} north={street.footways.north > 0} />
      {street.wall && <DeadEnd street={street} />}
      <StreetProps street={street} />
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
    const ctx = canvas.getContext('2d', { willReadFrequently: true })!;
    const px = (x: number) => (x - road.x0) * PPM;
    const py = (y: number) => (road.y1 - y) * PPM;

    // the lanes the tyres run in: the stretches between the painted lines and the kerbs wide enough for a car
    const cuts = [road.y0, ...lines.map((l) => l.y).sort((a, b) => a - b), road.y1];
    const lanes: { y: number; w: number }[] = [];
    for (let i = 0; i < cuts.length - 1; i++) {
      const w = cuts[i + 1] - cuts[i];
      if (w > 5.4) {
        lanes.push({ y: py(cuts[i] + w * 0.25), w: w * 0.5 * PPM }, { y: py(cuts[i] + w * 0.75), w: w * 0.5 * PPM });
      } else if (w > 2.9) lanes.push({ y: py(cuts[i] + w / 2), w: w * PPM });
    }
    paintAsphaltBase(ctx, cw, ch, PPM, lanes, { seed: Math.round(L * 7) });

    // the gutter along each kerb: a dirty band, and the concrete channel
    for (const y of [road.y0, road.y1]) {
      const dir = y === road.y0 ? 1 : -1;
      const g = ctx.createLinearGradient(0, py(y), 0, py(y) - dir * 0.9 * PPM);
      g.addColorStop(0, 'rgba(10,11,13,0.30)');
      g.addColorStop(1, 'rgba(10,11,13,0)');
      ctx.fillStyle = g;
      ctx.fillRect(0, dir > 0 ? py(y) - 0.9 * PPM : py(y), cw, 0.9 * PPM);
      ctx.fillStyle = 'rgba(122,125,131,0.34)';
      ctx.fillRect(0, dir > 0 ? py(y) - 0.32 * PPM : py(y), cw, 0.32 * PPM);
    }

    // the rest of what a street carries: drains at the kerb, manholes, a stop-and-go scuff
    const r = rng(Math.round(L * 3));
    for (let x = road.x0 + 7; x < road.x1 - 5; x += 15 + r() * 6) {
      paintDrain(ctx, px(x), py(road.y0 + 0.02) - 0.34 * PPM, 0.8 * PPM, 0.32 * PPM, PPM);
      if (r() > 0.4) paintDrain(ctx, px(x + 9), py(road.y1) + 0.02 * PPM, 0.8 * PPM, 0.32 * PPM, PPM);
    }
    const mid = (road.y0 + road.y1) / 2;
    for (const [mx, my] of [[road.x0 + L * 0.31, mid + W * 0.18], [road.x0 + L * 0.72, mid - W * 0.12], [road.x0 + L * 0.5, mid + W * 0.05]]) {
      paintManhole(ctx, px(mx), py(my), 0.32 * PPM, PPM);
    }

    // the paint, worn: solid and dashed lines, the bay boxes, an arrow in the lane
    ctx.fillStyle = PAINT;
    for (const ln of lines) {
      const lw = (ln.width ?? 0.12) * PPM;
      if (!ln.dash) {
        ctx.fillRect(px(ln.x0), py(ln.y) - lw / 2, (ln.x1 - ln.x0) * PPM, lw);
        wearPaint(ctx, px(ln.x0), py(ln.y) - lw / 2, (ln.x1 - ln.x0) * PPM, lw, PPM, Math.round(ln.y * 10), 0.45);
      } else {
        for (let x = ln.x0; x < ln.x1; x += 5) {
          const dl = Math.min(2, ln.x1 - x) * PPM;
          ctx.fillRect(px(x), py(ln.y) - lw / 2, dl, lw);
          wearPaint(ctx, px(x), py(ln.y) - lw / 2, dl, lw, PPM, Math.round(x * 3), 0.55);
        }
      }
    }
    ctx.strokeStyle = PAINT;
    ctx.lineWidth = 0.1 * PPM;
    for (const b of bays) {
      ctx.strokeRect(px(b.x - b.length / 2), py(b.y + b.width / 2), b.length * PPM, b.width * PPM);
      wearPaint(ctx, px(b.x - b.length / 2), py(b.y + b.width / 2), b.length * PPM, b.width * PPM, PPM, 77, 0.3);
    }
    if (lines.length) {
      // a straight-ahead arrow in the first travelling lane, away from the manoeuvre
      const travel = lines.find((l) => l.dash) ?? lines[0];
      paintArrow(ctx, px(road.x0 + L * 0.16), py(travel.y - 1.6), 3.4 * PPM, PPM);
    }
    fadeEdges(ctx, cw, ch, PPM, FADE);

    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 8;
    return tex;
  }, [road, lines, bays, L, W]);
  React.useEffect(() => () => map.dispose(), [map]);
  const mat = React.useMemo(() => asphaltMaterial(map, L, W), [map, L, W]);
  React.useEffect(() => () => mat.dispose(), [mat]);
  useDusk((d) => mat.color.copy(d.room));
  useHaze();
  return (
    <mesh position={[(road.x0 + road.x1) / 2, 0.003, -(road.y0 + road.y1) / 2]} rotation-x={-Math.PI / 2} renderOrder={-0.5} ref={onStage} material={mat}>
      <planeGeometry args={[L, W]} />
    </mesh>
  );
}

// ------------------------------------------------------------------------------------------- footways

/** A raised footway along one kerb of the street (the shared strip, ./scenery/Ground). */
function Footway({ street, side }: { street: StreetStage; side: 'south' | 'north' }) {
  const { road, footways } = street;
  return <FootwayStrip x0={road.x0} x1={road.x1} kerbY={side === 'south' ? road.y0 : road.y1} foot={side === 'south' ? footways.south : footways.north} side={side} fade={FADE} />;
}

// ------------------------------------------------------------------------------------- the buildings

/**
 * Rows of buildings behind the footways: real volumes (src/components/viewer/scenery/buildings.ts) with the street's length
 * in them, one on the south side (the car's right, where the camera looks across the road at it) and one on the north. A row is
 * hidden when the camera has gone round behind it: seen from there it would only stand between the camera and the car.
 */
function Buildings({ street, south = false, north = false }: { street: StreetStage; south?: boolean; north?: boolean }) {
  const { road, footways } = street;
  const L = road.x1 - road.x0;
  useHaze([9, 46], 1);
  const spec = React.useMemo(() => ({ length: L, seed: Math.round(L * 11) % 97, maxHeight: 34, minHeight: 15 }), [L]);
  const specN = React.useMemo(() => ({ length: L, seed: (Math.round(L * 11) % 97) + 5, maxHeight: 26, minHeight: 13 }), [L]);
  return (
    <>
      {south && <BuildingRow spec={spec} x={road.x1} y={KERB} z={-(road.y0 - footways.south - 0.05)} faces={-1} />}
      {north && <BuildingRow spec={specN} x={road.x0} y={KERB} z={-(road.y1 + footways.north + 0.05)} faces={1} />}
    </>
  );
}

// ------------------------------------------------------------------------------------------- the dead end

function DeadEnd({ street }: { street: StreetStage }) {
  const { road, footways } = street;
  const x = street.wall!.x + 0.25;
  const y0 = road.y0 - footways.south;
  const y1 = road.y1 + footways.north;
  const len = y1 - y0;
  const map = React.useMemo(() => {
    const t = brickTexture().clone();
    t.repeat.set(len / 1.0, 2.9 / 1.0);
    t.needsUpdate = true;
    return t;
  }, [len]);
  React.useEffect(() => () => map.dispose(), [map]);
  const mat = React.useRef<THREE.MeshStandardMaterial>(null);
  useDusk((d) => mat.current?.color.set('#e6dfd6').multiply(d.room));
  return (
    <group position={[x, 0, -(y0 + y1) / 2]}>
      {/* the wall, in brick, with a coping on top */}
      <mesh position={[0, 1.4, 0]} ref={onStage}>
        <boxGeometry args={[0.5, 2.8, len]} />
        <meshStandardMaterial ref={mat} map={map} color="#e6dfd6" roughness={0.95} />
      </mesh>
      <mesh position={[0, 2.86, 0]} ref={onStage}>
        <boxGeometry args={[0.66, 0.12, len + 0.16]} />
        <meshStandardMaterial color="#b9b6b0" roughness={0.9} />
      </mesh>
    </group>
  );
}

// ------------------------------------------------------------------------------------------ the props

const TREE_KIND: Partial<Record<StreetPropKind, 'camphor' | 'plane' | 'ginkgo' | 'hedge' | 'shrub'>> = {
  tree: 'camphor',
  plane: 'plane',
  ginkgo: 'ginkgo',
  hedge: 'hedge',
  shrub: 'shrub',
};
const PROP_KIND: Partial<Record<StreetPropKind, PropKind>> = {
  lamp: 'lamp',
  bollard: 'bollard',
  bench: 'bench',
  bin: 'bin',
  shelter: 'shelter',
  sign: 'sign',
  streetsign: 'streetsign',
  hydrant: 'hydrant',
  planter: 'planter',
  bikes: 'bikes',
  cone: 'cone',
  personA: 'personA',
  personB: 'personB',
  personC: 'personC',
  scooter: 'scooter',
};

/** Street furniture and trees: the planner's list (src/lib/tech/street.ts) sorted by kind and drawn instanced. */
function StreetProps({ street }: { street: StreetStage }) {
  const { road, props } = street;
  // the lamps and the trees stand on the footways, which are a kerb's height up
  const height = (p: StreetProp) => (p.y < road.y0 || p.y > road.y1 ? KERB : 0);
  const byKind = React.useMemo(() => {
    const m = new Map<StreetPropKind, Spot[]>();
    for (const p of props) {
      const list = m.get(p.kind) ?? [];
      list.push({ x: p.x, y: height(p), z: -p.y, yaw: p.yaw, scale: p.scale });
      m.set(p.kind, list);
    }
    return m;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props, road]);
  const trees = React.useMemo(() => (['tree', 'plane', 'ginkgo'] as const).flatMap((k) => byKind.get(k) ?? []), [byKind]);
  useHaze();
  return (
    <group>
      {(['tree', 'plane', 'ginkgo', 'hedge', 'shrub'] as const).map((k) => {
        const spots = byKind.get(k);
        if (!spots?.length) return null;
        const tint = k === 'ginkgo' ? undefined : undefined;
        return <Trees key={k} kind={TREE_KIND[k]!} spots={spots.map((s) => ({ ...s, tint }))} shadows={k !== 'hedge' && k !== 'shrub'} />;
      })}
      <TreePits spots={trees} />
      {(Object.keys(PROP_KIND) as StreetPropKind[]).map((k) => {
        const spots = byKind.get(k);
        if (!spots?.length) return null;
        const pk = PROP_KIND[k]!;
        return <Props key={k} kind={pk} spots={spots} dot={PROP_DOT[pk] ?? 0} />;
      })}
    </group>
  );
}

/** The cast-iron tree pits the trees stand in, flush with the paving. */
function TreePits({ spots }: { spots: Spot[] }) {
  const mesh = React.useRef<THREE.InstancedMesh>(null);
  const map = React.useMemo(() => treePit(), []);
  const mat = React.useMemo(() => new THREE.MeshBasicMaterial({ map, transparent: true, depthWrite: false, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 }), [map]);
  React.useEffect(() => () => mat.dispose(), [mat]);
  useDusk((d) => mat.color.copy(d.room));
  React.useLayoutEffect(() => {
    const o = new THREE.Object3D();
    spots.forEach((s, i) => {
      o.position.set(s.x, (s.y ?? 0) + 0.008, s.z);
      o.rotation.set(-Math.PI / 2, 0, 0);
      o.scale.set(1.35, 1.35, 1);
      o.updateMatrix();
      mesh.current?.setMatrixAt(i, o.matrix);
    });
    if (mesh.current) {
      mesh.current.count = spots.length;
      mesh.current.instanceMatrix.needsUpdate = true;
    }
  }, [spots]);
  if (!spots.length) return null;
  return (
    <instancedMesh ref={mesh} args={[undefined, undefined, spots.length]} frustumCulled={false} renderOrder={-0.37} onUpdate={onStage}>
      <planeGeometry args={[1, 1]} />
      <primitive object={mat} attach="material" />
    </instancedMesh>
  );
}
