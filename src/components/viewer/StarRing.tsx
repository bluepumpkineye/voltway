'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import type { Vehicle } from '@/data/vehicles/schema';
import { techClock } from '@/lib/tech/clock';
import { distanceAt, getStarRingRun } from '@/lib/tech/starring';
import { drawMirror, drawRing } from './starRingDraw';

type Ctx2 = CanvasRenderingContext2D;

interface Screen {
  mesh: THREE.Mesh;
  /** the material as the cabin had it, and what to put back */
  was: { material: THREE.Material | THREE.Material[]; map: THREE.Texture | null; intensity: number; emissive: THREE.Color } | null;
  mat: THREE.MeshPhysicalMaterial;
  tex: THREE.CanvasTexture;
  ctx: Ctx2;
  w: number;
  h: number;
  side: -1 | 1 | 0;
}

/** The picture's aspect (long side over short) from the quad's own geometry. */
function aspectOf(mesh: THREE.Mesh): number {
  const g = mesh.geometry;
  g.computeBoundingBox();
  const d = g.boundingBox!.getSize(new THREE.Vector3());
  const [a, b] = [d.x, d.y, d.z].sort((x, y) => y - x);
  return b > 1e-4 ? THREE.MathUtils.clamp(a / b, 1, 24) : 2;
}

function screenOf(root: THREE.Object3D, name: string, width: number, side: -1 | 1 | 0): Screen | null {
  const mesh = root.getObjectByName(name) as THREE.Mesh | undefined;
  if (!mesh || !mesh.isMesh) return null;
  const base = (Array.isArray(mesh.material) ? mesh.material[0] : mesh.material) as THREE.MeshPhysicalMaterial;
  const canvas = document.createElement('canvas');
  const aspect = aspectOf(mesh);
  canvas.width = width;
  canvas.height = Math.max(8, Math.round(width / aspect));
  const ctx = canvas.getContext('2d');
  if (!ctx) return null;
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  // the glTF's own addressing, as the picture it replaces
  tex.flipY = false;
  const first = base.emissiveMap;
  if (first) {
    tex.channel = first.channel;
    tex.offset.copy(first.offset);
    tex.repeat.copy(first.repeat);
    tex.rotation = first.rotation;
    tex.center.copy(first.center);
    tex.wrapS = first.wrapS;
    tex.wrapT = first.wrapT;
  }
  return { mesh, was: null, mat: base, tex, ctx, w: canvas.width, h: canvas.height, side };
}

/**
 * Lights the Avatr 06T's Star Ring and its two mirror screens while the Star Ring demo is on: the ring's emissive picture and the mirrors'
 * (which have none) are swapped for canvases drawn from the demo's clock, and put back when it goes. The 06T keeps the cabin it was
 * built with (its own cluster picture stays on the Interior tab), so this touches nothing else. It draws 15 times a second at most.
 */
export function StarRingDriver({ vehicle }: { vehicle: Vehicle }) {
  const scene = useThree((s) => s.scene);
  const live = React.useRef<{ ring: Screen; mirrors: Screen[]; key: number } | null>(null);

  const attach = React.useCallback(() => {
    const ring = screenOf(scene, 'screen_cluster', 4096, 0);
    if (!ring) return false;
    const mirrors = [screenOf(scene, 'screen_mirror_L', 512, -1), screenOf(scene, 'screen_mirror_R', 512, 1)].filter((m): m is Screen => Boolean(m));
    ring.was = { material: ring.mesh.material, map: ring.mat.emissiveMap, intensity: ring.mat.emissiveIntensity, emissive: ring.mat.emissive.clone() };
    ring.mat.emissiveMap = ring.tex;
    ring.mat.emissive.set('#ffffff');
    ring.mat.needsUpdate = true;
    for (const m of mirrors) {
      // the two mirror screens share one material: each gets its own
      m.was = { material: m.mesh.material, map: m.mat.emissiveMap, intensity: m.mat.emissiveIntensity, emissive: m.mat.emissive.clone() };
      const own = m.mat.clone();
      own.emissiveMap = m.tex;
      own.emissive.set('#ffffff');
      own.emissiveIntensity = 0.95;
      // the model's mirror quads lie in the ring's plane and overlap its ends by about 2.6 cm: with nothing to decide it the two flicker
      // against each other (a pale box over the ring's first figures). The mirror screen wins, as a screen set into the band's end would.
      own.polygonOffset = true;
      own.polygonOffsetFactor = -2;
      own.polygonOffsetUnits = -2;
      own.needsUpdate = true;
      m.mat = own;
      m.mesh.material = own;
    }
    live.current = { ring, mirrors, key: -1 };
    return true;
  }, [scene]);

  const detach = React.useCallback(() => {
    const l = live.current;
    if (!l) return;
    const w = l.ring.was;
    if (w) {
      l.ring.mat.emissiveMap = w.map;
      l.ring.mat.emissiveIntensity = w.intensity;
      l.ring.mat.emissive.copy(w.emissive);
      l.ring.mat.needsUpdate = true;
    }
    l.ring.tex.dispose();
    for (const m of l.mirrors) {
      if (m.was) m.mesh.material = m.was.material;
      m.mat.dispose();
      m.tex.dispose();
    }
    live.current = null;
  }, []);

  React.useEffect(() => detach, [detach]);

  useFrame(() => {
    if (vehicle.slug !== 'avatr-06t') return;
    const run = getStarRingRun();
    if (!run) {
      if (live.current) detach();
      return;
    }
    if (!live.current && !attach()) return;
    const l = live.current;
    if (!l) return;
    const t = techClock.t;
    const key = Math.floor(t * 15);
    if (key === l.key) return;
    l.key = key;
    const s = run.state(t);
    drawRing(l.ring.ctx, l.ring.w, l.ring.h, s);
    l.ring.tex.needsUpdate = true;
    const dist = distanceAt(t);
    for (const m of l.mirrors) {
      drawMirror(m.ctx, m.w, m.h, s.mirrors, dist, m.side === 0 ? 1 : m.side);
      m.tex.needsUpdate = true;
    }
  });
  return null;
}
