import React from 'react';
import * as THREE from 'three';
import { useThree } from '@react-three/fiber';
import type { Vehicle } from '@/data/vehicles/schema';

/**
 * The control-icon decals: standard automotive micro-icons on the keys the cabin model leaves blank (steering-wheel keys, the
 * driver's window switches, the wireless charger, the selector's Park / Start / Hazard).
 *
 * The cabin GLB carries them as tiny flat quads in one material, `M_Icons`, whose UVs point into an 8 x 4 atlas; the atlas is
 * drawn here, on a canvas, so it is crisp at any size and needs no image file. ICONS is the atlas's order and must match
 * blender/scripts/seal_polish.py. The decals sit 0.4 mm over the keys, win the depth test with a polygon offset, and glow a
 * little (emission 0.25) so a control reads as lit and engineered. Only cars listed in WITH_ICONS carry the quads.
 */
export const ICONS = [
  'vol_plus', 'vol_minus', 'mute', 'next', 'voice', 'phone', 'cruise', 'adas_distance',
  'lane', 'arrow_up', 'arrow_down', 'win_up', 'win_down', 'lock', 'fold', 'hazard',
  'charger', 'park', 'start', 'autohold', 'regen', 'defrost', 'fan', 'mode',
  'back', 'ok', 'camera', 'horn', 'boot', 'child', 'light', 'unused',
] as const;
export type IconName = (typeof ICONS)[number];

const COLS = 8;
const ROWS = 4;
const CELL = 128;
const WHITE = '#f4f2ec';
const AMBER = '#ffb02e';

type Ctx = CanvasRenderingContext2D;

function stroke(ctx: Ctx, color: string, w = 8) {
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = w;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
}

function speaker(ctx: Ctx, x = 38, y = 64) {
  ctx.beginPath();
  ctx.moveTo(x - 16, y - 12);
  ctx.lineTo(x - 4, y - 12);
  ctx.lineTo(x + 14, y - 28);
  ctx.lineTo(x + 14, y + 28);
  ctx.lineTo(x - 4, y + 12);
  ctx.lineTo(x - 16, y + 12);
  ctx.closePath();
  ctx.fill();
}

function arc(ctx: Ctx, x: number, y: number, r: number, a0: number, a1: number) {
  ctx.beginPath();
  ctx.arc(x, y, r, a0, a1);
  ctx.stroke();
}

function line(ctx: Ctx, ...p: number[]) {
  ctx.beginPath();
  ctx.moveTo(p[0], p[1]);
  for (let i = 2; i < p.length; i += 2) ctx.lineTo(p[i], p[i + 1]);
  ctx.stroke();
}

const GLYPHS: Partial<Record<IconName, (ctx: Ctx) => void>> = {
  vol_plus(ctx) {
    stroke(ctx, WHITE, 8);
    speaker(ctx);
    arc(ctx, 56, 64, 22, -0.7, 0.7);
    line(ctx, 96, 40, 96, 64);
    line(ctx, 84, 52, 108, 52);
  },
  vol_minus(ctx) {
    stroke(ctx, WHITE, 8);
    speaker(ctx);
    arc(ctx, 56, 64, 22, -0.7, 0.7);
    line(ctx, 84, 52, 108, 52);
  },
  mute(ctx) {
    stroke(ctx, WHITE, 8);
    speaker(ctx);
    line(ctx, 80, 46, 108, 82);
    line(ctx, 108, 46, 80, 82);
  },
  next(ctx) {
    stroke(ctx, WHITE, 8);
    ctx.beginPath();
    ctx.moveTo(34, 34);
    ctx.lineTo(80, 64);
    ctx.lineTo(34, 94);
    ctx.closePath();
    ctx.fill();
    line(ctx, 96, 34, 96, 94);
  },
  voice(ctx) {
    stroke(ctx, WHITE, 8);
    ctx.beginPath();
    ctx.roundRect(50, 22, 28, 52, 14);
    ctx.fill();
    arc(ctx, 64, 62, 28, 0.15 * Math.PI, 0.85 * Math.PI);
    line(ctx, 64, 90, 64, 106);
    line(ctx, 46, 106, 82, 106);
  },
  phone(ctx) {
    stroke(ctx, WHITE, 8);
    // a handset: a thick arc with a pad at each end
    ctx.beginPath();
    ctx.arc(64, 64, 34, 0.15 * Math.PI, 0.85 * Math.PI, true);
    ctx.stroke();
    ctx.save();
    ctx.translate(36, 84);
    ctx.rotate(-0.7);
    ctx.fillRect(-12, -10, 24, 20);
    ctx.restore();
    ctx.save();
    ctx.translate(92, 84);
    ctx.rotate(0.7);
    ctx.fillRect(-12, -10, 24, 20);
    ctx.restore();
  },
  cruise(ctx) {
    stroke(ctx, WHITE, 8);
    arc(ctx, 64, 74, 40, 0.85 * Math.PI, 2.15 * Math.PI);
    line(ctx, 64, 74, 88, 46);
    ctx.beginPath();
    ctx.arc(64, 74, 7, 0, Math.PI * 2);
    ctx.fill();
  },
  adas_distance(ctx) {
    stroke(ctx, WHITE, 8);
    ctx.beginPath();
    ctx.roundRect(36, 62, 56, 36, 10);
    ctx.stroke();
    line(ctx, 46, 98, 46, 108);
    line(ctx, 82, 98, 82, 108);
    line(ctx, 40, 44, 88, 44);
    line(ctx, 50, 28, 78, 28);
  },
  lane(ctx) {
    stroke(ctx, WHITE, 8);
    line(ctx, 38, 106, 52, 22);
    line(ctx, 90, 106, 76, 22);
    ctx.setLineDash([12, 12]);
    line(ctx, 64, 106, 64, 24);
    ctx.setLineDash([]);
  },
  arrow_up(ctx) {
    stroke(ctx, WHITE, 8);
    ctx.beginPath();
    ctx.moveTo(64, 28);
    ctx.lineTo(98, 82);
    ctx.lineTo(30, 82);
    ctx.closePath();
    ctx.fill();
  },
  arrow_down(ctx) {
    stroke(ctx, WHITE, 8);
    ctx.beginPath();
    ctx.moveTo(64, 100);
    ctx.lineTo(98, 46);
    ctx.lineTo(30, 46);
    ctx.closePath();
    ctx.fill();
  },
  win_up(ctx) {
    stroke(ctx, WHITE, 7);
    line(ctx, 22, 104, 22, 54, 52, 22, 108, 22, 108, 104);
    line(ctx, 52, 88, 52, 52);
    line(ctx, 38, 66, 52, 52, 66, 66);
  },
  win_down(ctx) {
    stroke(ctx, WHITE, 7);
    line(ctx, 22, 104, 22, 54, 52, 22, 108, 22, 108, 104);
    line(ctx, 52, 52, 52, 88);
    line(ctx, 38, 74, 52, 88, 66, 74);
  },
  lock(ctx) {
    stroke(ctx, WHITE, 8);
    ctx.beginPath();
    ctx.roundRect(34, 58, 60, 46, 8);
    ctx.fill();
    arc(ctx, 64, 58, 20, Math.PI, 2 * Math.PI);
  },
  fold(ctx) {
    stroke(ctx, WHITE, 8);
    ctx.beginPath();
    ctx.roundRect(26, 40, 52, 44, 12);
    ctx.stroke();
    arc(ctx, 74, 78, 26, -0.3 * Math.PI, 0.6 * Math.PI);
    line(ctx, 98, 60, 104, 80, 84, 82);
  },
  hazard(ctx) {
    stroke(ctx, AMBER, 9);
    ctx.beginPath();
    ctx.moveTo(64, 20);
    ctx.lineTo(112, 104);
    ctx.lineTo(16, 104);
    ctx.closePath();
    ctx.stroke();
    stroke(ctx, AMBER, 6);
    ctx.beginPath();
    ctx.moveTo(64, 50);
    ctx.lineTo(88, 92);
    ctx.lineTo(40, 92);
    ctx.closePath();
    ctx.stroke();
  },
  charger(ctx) {
    stroke(ctx, WHITE, 8);
    ctx.beginPath();
    ctx.roundRect(40, 18, 48, 84, 10);
    ctx.stroke();
    arc(ctx, 64, 60, 14, 1.15 * Math.PI, 1.85 * Math.PI);
    arc(ctx, 64, 60, 26, 1.15 * Math.PI, 1.85 * Math.PI);
    arc(ctx, 64, 60, 38, 1.2 * Math.PI, 1.8 * Math.PI);
    ctx.beginPath();
    ctx.arc(64, 70, 5, 0, Math.PI * 2);
    ctx.fill();
  },
  park(ctx) {
    stroke(ctx, WHITE, 9);
    arc(ctx, 64, 64, 46, 0, Math.PI * 2);
    ctx.font = `700 64px 'Inter','Segoe UI',Arial,sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('P', 64, 68);
  },
  start(ctx) {
    stroke(ctx, AMBER, 10);
    arc(ctx, 64, 68, 38, -0.35 * Math.PI, 1.35 * Math.PI);
    line(ctx, 64, 20, 64, 64);
  },
  autohold(ctx) {
    stroke(ctx, AMBER, 8);
    arc(ctx, 64, 64, 46, 0, Math.PI * 2);
    ctx.font = `700 52px 'Inter','Segoe UI',Arial,sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('A', 64, 68);
  },
  regen(ctx) {
    stroke(ctx, WHITE, 8);
    ctx.beginPath();
    ctx.roundRect(18, 44, 76, 44, 8);
    ctx.stroke();
    line(ctx, 100, 56, 100, 76);
    line(ctx, 66, 50, 46, 66, 62, 66, 42, 84);
  },
  defrost(ctx) {
    stroke(ctx, WHITE, 8);
    line(ctx, 18, 100, 30, 36, 98, 36, 110, 100);
    for (const x of [44, 64, 84]) {
      ctx.beginPath();
      ctx.moveTo(x, 90);
      ctx.bezierCurveTo(x - 10, 78, x + 10, 68, x, 54);
      ctx.stroke();
    }
  },
  fan(ctx) {
    stroke(ctx, WHITE, 8);
    for (let k = 0; k < 3; k++) {
      ctx.save();
      ctx.translate(64, 64);
      ctx.rotate((k * 2 * Math.PI) / 3);
      ctx.beginPath();
      ctx.ellipse(0, -26, 14, 26, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  },
};

/** The atlas, drawn once: icons white (amber for the warnings) on transparent. */
export function buildIconAtlas(): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = COLS * CELL;
  canvas.height = ROWS * CELL;
  const ctx = canvas.getContext('2d')!;
  ICONS.forEach((name, i) => {
    ctx.save();
    ctx.translate((i % COLS) * CELL, Math.floor(i / COLS) * CELL);
    ctx.beginPath();
    ctx.rect(0, 0, CELL, CELL);
    ctx.clip();
    (GLYPHS[name] ?? ((c: Ctx) => {
      stroke(c, WHITE, 8);
      arc(c, 64, 64, 40, 0, Math.PI * 2);
    }))(ctx);
    ctx.restore();
  });
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 16;
  tex.flipY = false; // the glTF's own addressing: the quads' UVs were written for it
  tex.needsUpdate = true;
  return tex;
}

const WITH_ICONS = new Set(['byd-seal']);
const DECALS = /^m_icons$/i;

/** Dresses the cabin's `M_Icons` quads with the atlas: glowing glyphs over the keys, in front of them in depth. */
export function useIconDecals(model: THREE.Object3D, vehicle: Vehicle) {
  const invalidate = useThree((s) => s.invalidate);
  const wanted = WITH_ICONS.has(vehicle.slug);
  React.useEffect(() => {
    if (!wanted) return;
    const mats = new Set<THREE.MeshStandardMaterial>();
    model.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (!mesh.isMesh) return;
      for (const m of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
        if (DECALS.test(m.name) && m instanceof THREE.MeshStandardMaterial) mats.add(m);
      }
    });
    if (!mats.size) return;
    const atlas = buildIconAtlas();
    for (const m of mats) {
      m.map = atlas;
      m.emissiveMap = atlas;
      m.emissive.set('#ffffff');
      m.emissiveIntensity = 0.25;
      m.transparent = true;
      m.alphaTest = 0.02;
      m.depthWrite = false;
      m.polygonOffset = true;
      m.polygonOffsetFactor = -1;
      m.polygonOffsetUnits = -1;
      m.roughness = 0.6;
      m.metalness = 0;
      m.color.set('#ffffff');
      m.needsUpdate = true;
    }
    invalidate();
    return () => {
      for (const m of mats) {
        m.map = null;
        m.emissiveMap = null;
        m.needsUpdate = true;
      }
      atlas.dispose();
    };
  }, [model, wanted, invalidate]);
}
