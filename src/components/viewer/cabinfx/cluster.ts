import React from 'react';
import * as THREE from 'three';
import { useThree } from '@react-three/fiber';
import type { Vehicle } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';

/**
 * The driver's instrument cluster, redrawn crisp: a 2048 x 768 canvas (the Seal's 10.25 in cluster is 0.244 x 0.092 m, 2.65:1)
 * in the modern Chinese EV style: a digital speedometer on a 240 km/h arc, the P R N D stack, battery charge and range, an
 * ADAS lane-and-car view, tyre pressures and a status line. It is live: gear, charge, theme and driver assistance come from the
 * showroom's store, so a tap on the centre screen's gear selector moves the highlight in the cluster.
 *
 * It replaces the emissive picture the Blender export carries (a 1536 x 576 raster drawn from a photograph's layout). Only cars
 * listed in LIVE_CLUSTER get it: the Seal is the benchmark, the others follow once it is approved.
 */
const LIVE_CLUSTER = new Set(['byd-seal']);
const W = 2048;
const H = 768;
const FONT = "'Inter', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif";

export interface ClusterState {
  dark: boolean;
  gear: string;
  soc: number;
  speed: number;
  rangeKm: number;
  adas: boolean;
  lamps: boolean;
  mode: string;
  accent: string;
}

interface Pal {
  bg0: string;
  bg1: string;
  ink: string;
  dim: string;
  faint: string;
  accent: string;
  good: string;
  warn: string;
  road: string;
}

function palette(s: ClusterState): Pal {
  return s.dark
    ? { bg0: '#03060a', bg1: '#0c141d', ink: '#f2f6fa', dim: '#8d9aa8', faint: '#26323f', accent: s.accent, good: '#4ade80', warn: '#fbbf24', road: '#101a24' }
    : { bg0: '#dfe9f0', bg1: '#f3f6f9', ink: '#131b24', dim: '#5d6b78', faint: '#bccad6', accent: s.accent, good: '#16a34a', warn: '#d97706', road: '#e8eef3' };
}

function text(ctx: CanvasRenderingContext2D, s: string, x: number, y: number, size: number, color: string, weight = 600, align: CanvasTextAlign = 'left') {
  ctx.font = `${weight} ${size}px ${FONT}`;
  ctx.fillStyle = color;
  ctx.textAlign = align;
  ctx.textBaseline = 'alphabetic';
  ctx.fillText(s, x, y);
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

/** Draws one frame of the cluster. Pure of the DOM but for the canvas it is given. */
export function drawCluster(ctx: CanvasRenderingContext2D, s: ClusterState): void {
  const p = palette(s);
  ctx.save();
  ctx.clearRect(0, 0, W, H);

  // ---- glass: a deep gradient with a soft centre glow and darker corners
  const bg = ctx.createLinearGradient(0, 0, 0, H);
  bg.addColorStop(0, p.bg0);
  bg.addColorStop(1, p.bg1);
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, W, H);
  const glow = ctx.createRadialGradient(1024, 420, 40, 1024, 420, 700);
  glow.addColorStop(0, s.dark ? 'rgba(53,198,255,0.13)' : 'rgba(53,150,255,0.10)');
  glow.addColorStop(1, 'rgba(53,198,255,0)');
  ctx.fillStyle = glow;
  ctx.fillRect(0, 0, W, H);

  // ---- status line
  text(ctx, '07:41', 64, 64, 40, p.ink, 600);
  text(ctx, '24°C', 220, 64, 34, p.dim, 500);
  text(ctx, s.mode.toUpperCase(), W / 2, 62, 30, p.accent, 700, 'center');
  // signal bars, bluetooth dot, and a lamp glyph
  for (let i = 0; i < 4; i++) {
    ctx.fillStyle = i < 3 ? p.ink : p.faint;
    ctx.fillRect(W - 250 + i * 18, 62 - (i + 1) * 9, 11, (i + 1) * 9);
  }
  ctx.beginPath();
  ctx.arc(W - 150, 48, 9, 0, Math.PI * 2);
  ctx.fillStyle = p.accent;
  ctx.fill();
  text(ctx, 'LTE', W - 120, 62, 26, p.dim, 600);
  ctx.strokeStyle = p.faint;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(48, 92);
  ctx.lineTo(W - 48, 92);
  ctx.stroke();

  // ---- speedometer: a 270 degree arc on 0..240 km/h, digits in the middle
  const cx = 1024;
  const cy = 424;
  const R = 268;
  const a0 = (135 * Math.PI) / 180;
  const sweep = (270 * Math.PI) / 180;
  const vMax = 240;
  const frac = Math.min(1, s.speed / vMax);
  ctx.lineCap = 'round';
  ctx.lineWidth = 22;
  ctx.strokeStyle = p.faint;
  ctx.beginPath();
  ctx.arc(cx, cy, R, a0, a0 + sweep);
  ctx.stroke();
  const arc = ctx.createLinearGradient(cx - R, cy + R, cx + R, cy - R);
  arc.addColorStop(0, '#35c6ff');
  arc.addColorStop(1, p.accent);
  ctx.strokeStyle = arc;
  ctx.beginPath();
  ctx.arc(cx, cy, R, a0, a0 + Math.max(0.012, sweep * frac));
  ctx.stroke();
  ctx.lineCap = 'butt';
  for (let v = 0; v <= vMax; v += 10) {
    const a = a0 + (v / vMax) * sweep;
    const major = v % 40 === 0;
    const r1 = R - 34;
    const r2 = R - (major ? 62 : 48);
    ctx.strokeStyle = v / vMax <= frac && s.speed > 0 ? p.ink : major ? p.dim : p.faint;
    ctx.lineWidth = major ? 4 : 2;
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(a) * r1, cy + Math.sin(a) * r1);
    ctx.lineTo(cx + Math.cos(a) * r2, cy + Math.sin(a) * r2);
    ctx.stroke();
    if (major) text(ctx, String(v), cx + Math.cos(a) * (R - 96), cy + Math.sin(a) * (R - 96) + 12, 30, p.dim, 600, 'center');
  }
  text(ctx, String(Math.round(s.speed)), cx, cy + 62, 214, p.ink, 700, 'center');
  text(ctx, 'km/h', cx, cy + 118, 36, p.dim, 600, 'center');

  // ---- gear stack: P R N D, the live gear lit
  const gx = 1424;
  const gears = ['P', 'R', 'N', 'D'];
  gears.forEach((g, i) => {
    const gy = 218 + i * 92;
    const on = g === s.gear;
    if (on) {
      roundRect(ctx, gx - 38, gy - 56, 76, 76, 16);
      ctx.fillStyle = g === 'R' ? s.dark ? '#ff5d5d' : '#dc2626' : p.accent;
      ctx.fill();
    }
    text(ctx, g, gx, gy, 52, on ? (s.dark ? '#031018' : '#ffffff') : p.dim, 700, 'center');
  });

  // ---- battery: ring, charge and range
  const bx = 1730;
  const by = 330;
  const br = 118;
  ctx.lineWidth = 20;
  ctx.lineCap = 'round';
  ctx.strokeStyle = p.faint;
  ctx.beginPath();
  ctx.arc(bx, by, br, 0, Math.PI * 2);
  ctx.stroke();
  const low = s.soc < 0.2;
  ctx.strokeStyle = low ? p.warn : p.good;
  ctx.beginPath();
  ctx.arc(bx, by, br, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * s.soc);
  ctx.stroke();
  ctx.lineCap = 'butt';
  text(ctx, String(Math.round(s.soc * 100)), bx - 8, by + 30, 92, p.ink, 700, 'center');
  text(ctx, '%', bx + 62, by + 8, 34, p.dim, 600, 'center');
  // charge bolt
  ctx.fillStyle = p.good;
  ctx.beginPath();
  ctx.moveTo(bx + 12, by - 78);
  ctx.lineTo(bx - 18, by - 38);
  ctx.lineTo(bx - 2, by - 38);
  ctx.lineTo(bx - 12, by - 8);
  ctx.lineTo(bx + 22, by - 52);
  ctx.lineTo(bx + 5, by - 52);
  ctx.closePath();
  ctx.fill();
  text(ctx, `${s.rangeKm}`, bx - 6, 566, 84, p.ink, 700, 'center');
  text(ctx, 'km', bx + 112, 566, 34, p.dim, 600, 'center');
  text(ctx, 'RANGE · CLTC', bx, 612, 26, p.dim, 600, 'center');
  roundRect(ctx, 1560, 640, 340, 56, 28);
  ctx.fillStyle = p.faint;
  ctx.fill();
  text(ctx, '14.6 kWh/100km', 1730, 678, 28, p.ink, 600, 'center');

  // ---- ADAS: a lane and the car in perspective, with tyre pressures at the corners
  drawRoad(ctx, p, s);

  // ---- bottom line
  ctx.strokeStyle = p.faint;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(48, 708);
  ctx.lineTo(W - 48, 708);
  ctx.stroke();
  text(ctx, 'ODO 12,486 km', 64, 748, 28, p.dim, 600);
  text(ctx, 'TRIP 0.0 km', W - 64, 748, 28, p.dim, 600, 'right');
  // seat belt, lamps and ADAS state as small chips
  const chip = (x: number, label: string, on: boolean, color: string) => {
    roundRect(ctx, x, 718, 150, 40, 20);
    ctx.fillStyle = on ? color : p.faint;
    ctx.globalAlpha = on ? 0.9 : 0.8;
    ctx.fill();
    ctx.globalAlpha = 1;
    text(ctx, label, x + 75, 747, 22, on ? (s.dark ? '#02080d' : '#ffffff') : p.dim, 700, 'center');
  };
  chip(822, 'BELT', true, p.good);
  chip(986, 'LAMPS', s.lamps, p.accent);
  chip(1150, 'ADAS', s.adas, p.accent);
  ctx.restore();
}

function drawRoad(ctx: CanvasRenderingContext2D, p: Pal, s: ClusterState) {
  ctx.save();
  // clip to the left panel
  roundRect(ctx, 56, 112, 640, 580, 30);
  ctx.clip();
  const g = ctx.createLinearGradient(0, 112, 0, 692);
  g.addColorStop(0, s.dark ? '#0a121b' : '#e4edf3');
  g.addColorStop(1, p.road);
  ctx.fillStyle = g;
  ctx.fillRect(56, 112, 640, 580);
  const vx = 376;
  const vy = 232;
  // lane edges converge on the horizon
  const lane = (xb: number, color: string, w: number, dash = false) => {
    ctx.strokeStyle = color;
    ctx.lineWidth = w;
    ctx.setLineDash(dash ? [34, 26] : []);
    ctx.beginPath();
    ctx.moveTo(xb, 692);
    ctx.lineTo(vx + (xb - vx) * 0.1, vy);
    ctx.stroke();
    ctx.setLineDash([]);
  };
  lane(150, s.adas ? p.accent : p.dim, 7);
  lane(602, s.adas ? p.accent : p.dim, 7);
  lane(376, p.faint, 4, true);
  // the lane the car follows, lit when assistance is on
  if (s.adas) {
    const l = ctx.createLinearGradient(0, 692, 0, vy);
    l.addColorStop(0, 'rgba(53,198,255,0.32)');
    l.addColorStop(1, 'rgba(53,198,255,0)');
    ctx.fillStyle = l;
    ctx.beginPath();
    ctx.moveTo(150, 692);
    ctx.lineTo(602, 692);
    ctx.lineTo(vx + (602 - vx) * 0.1, vy);
    ctx.lineTo(vx + (150 - vx) * 0.1, vy);
    ctx.closePath();
    ctx.fill();
  }
  // radar rings ahead of the car
  ctx.strokeStyle = s.adas ? 'rgba(53,198,255,0.55)' : p.faint;
  ctx.lineWidth = 3;
  for (let i = 0; i < 3; i++) {
    ctx.beginPath();
    ctx.ellipse(376, 560, 90 + i * 70, 26 + i * 18, 0, Math.PI, Math.PI * 2);
    ctx.stroke();
  }
  // a lead car (a rounded block, tail lamps)
  const lead = (x: number, y: number, k: number) => {
    roundRect(ctx, x - 44 * k, y - 28 * k, 88 * k, 50 * k, 12 * k);
    ctx.fillStyle = s.dark ? '#43515f' : '#9fb0be';
    ctx.fill();
    ctx.fillStyle = '#ff5d5d';
    ctx.fillRect(x - 38 * k, y - 12 * k, 22 * k, 7 * k);
    ctx.fillRect(x + 16 * k, y - 12 * k, 22 * k, 7 * k);
  };
  lead(402, 322, 0.8);
  lead(246, 276, 0.5);
  // our car, from behind: a shaded body, glass, tail lamp bar
  ctx.save();
  ctx.translate(376, 598);
  const body = ctx.createLinearGradient(0, -80, 0, 70);
  body.addColorStop(0, s.dark ? '#e7eef5' : '#4a5a69');
  body.addColorStop(1, s.dark ? '#7a8998' : '#26323d');
  ctx.fillStyle = body;
  roundRect(ctx, -104, -48, 208, 112, 30);
  ctx.fill();
  ctx.fillStyle = s.dark ? '#0a121b' : '#dbe6ee';
  ctx.beginPath();
  ctx.moveTo(-76, -44);
  ctx.lineTo(-52, -82);
  ctx.lineTo(52, -82);
  ctx.lineTo(76, -44);
  ctx.closePath();
  ctx.fill();
  ctx.fillStyle = '#ff4d4d';
  roundRect(ctx, -92, -6, 184, 12, 6);
  ctx.fill();
  ctx.fillStyle = s.dark ? '#02080d' : '#101820';
  ctx.fillRect(-26, 28, 52, 22);
  ctx.restore();
  ctx.restore();

  // tyre pressures: four chips around the panel
  const tyre = (x: number, y: number) => {
    roundRect(ctx, x, y, 132, 62, 14);
    ctx.fillStyle = s.dark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)';
    ctx.fill();
    ctx.strokeStyle = p.faint;
    ctx.lineWidth = 2;
    ctx.stroke();
    // a tyre profile glyph
    ctx.strokeStyle = p.dim;
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.arc(x + 28, y + 31, 15, Math.PI * 0.2, Math.PI * 1.8);
    ctx.stroke();
    text(ctx, '2.5', x + 100, y + 42, 32, p.ink, 700, 'center');
  };
  tyre(72, 128);
  tyre(552, 128);
  tyre(72, 614);
  tyre(552, 614);
}

// ----------------------------------------------------------------------- the hook

const CLUSTER_MATERIAL = /display_screen_cluster|screen_cluster/i;

function materialsOf(o: THREE.Mesh): THREE.Material[] {
  return Array.isArray(o.material) ? o.material : [o.material];
}

function stateOf(vehicle: Vehicle): ClusterState {
  const s = useVehicleStore.getState();
  const cltc = vehicle.variants[0]?.range[0]?.km ?? 500;
  const mode = vehicle.cockpit.driveModes?.find((d) => d.id === s.driveMode)?.label ?? 'Comfort';
  return {
    dark: s.hmiTheme !== 'light',
    gear: s.gear,
    soc: s.soc,
    speed: 0,
    rangeKm: Math.round(cltc * s.soc * 0.92),
    adas: s.adasActive,
    lamps: s.lightMode !== 'off',
    mode,
    accent: vehicle.cockpit.accentColor ?? '#1791FF',
  };
}

/**
 * Swaps the cluster's emissive picture for the live canvas. The mapping is copied from the picture it replaces, so the UVs of
 * the Blender quad stay as they were; the original comes back when the cabin unmounts.
 */
export function useLiveCluster(model: THREE.Object3D, vehicle: Vehicle, glow: number | null) {
  const invalidate = useThree((s) => s.invalidate);
  const live = LIVE_CLUSTER.has(vehicle.slug);
  const slots = React.useMemo(() => {
    const out: THREE.MeshStandardMaterial[] = [];
    if (!live) return out;
    model.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (!mesh.isMesh) return;
      for (const m of materialsOf(mesh)) {
        if (CLUSTER_MATERIAL.test(m.name) && m instanceof THREE.MeshStandardMaterial && !out.includes(m)) out.push(m);
      }
    });
    return out;
  }, [model, live]);

  React.useEffect(() => {
    if (!slots.length) return;
    const canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 8;
    tex.flipY = false; // the glTF's own addressing, as the picture it replaces
    const first = slots[0].emissiveMap;
    if (first) {
      tex.channel = first.channel;
      tex.offset.copy(first.offset);
      tex.repeat.copy(first.repeat);
      tex.rotation = first.rotation;
      tex.center.copy(first.center);
      tex.wrapS = first.wrapS;
      tex.wrapT = first.wrapT;
    }
    const was = slots.map((m) => ({ map: m.emissiveMap, intensity: m.emissiveIntensity }));
    const paint = () => {
      drawCluster(ctx, stateOf(vehicle));
      tex.needsUpdate = true;
      invalidate();
    };
    paint();
    slots.forEach((m) => {
      m.emissiveMap = tex;
      m.emissive.set('#ffffff');
      m.needsUpdate = true;
    });
    let key = '';
    const unsub = useVehicleStore.subscribe((s) => {
      const k = [s.gear, s.soc, s.hmiTheme, s.adasActive, s.lightMode, s.driveMode].join('|');
      if (k === key) return;
      key = k;
      paint();
    });
    return () => {
      unsub();
      slots.forEach((m, i) => {
        m.emissiveMap = was[i].map;
        m.emissiveIntensity = was[i].intensity;
        m.needsUpdate = true;
      });
      tex.dispose();
    };
  }, [slots, vehicle, invalidate]);

  // a display is lit: a little over 1.0 in the seat, so the bloom can lift the digits; as built elsewhere
  const built = React.useMemo(() => slots.map((m) => m.emissiveIntensity), [slots]);
  React.useEffect(() => {
    if (!slots.length) return;
    slots.forEach((m, i) => {
      m.emissiveIntensity = glow ?? built[i];
    });
    invalidate();
  }, [slots, built, glow, invalidate]);
}
