import React from 'react';
import * as THREE from 'three';
import { useThree } from '@react-three/fiber';
import type { Vehicle } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';

/**
 * DriverClusterTextureGenerator: the driver's instrument cluster, redrawn crisp and live, for every car.
 *
 * One technical pipeline (a canvas at 2048 px wide in the quad's own aspect, mapped like the picture it replaces, redrawn when
 * the gear, charge, theme or driver assistance changes in the showroom's store) and a handful of brand layouts that share it:
 *
 *   gauge   a round speedometer between an ADAS lane view and the battery ring, P R N D stacked beside the dial
 *           (BYD Seal, Denza Z9, Luxeed RX)
 *   wide    minimal and horizontal: the gear row and a big numeral at the left, the ADAS car and lanes in the middle,
 *           a charge bar and range at the right (XPeng G9L, NIO ES8, Xiaomi SU7)
 *   calm    thin type on a quiet field: a light numeral, a hairline arc, the lane scene faint, gear and range below
 *           (Zeekr 7X, Voyah Passion S)
 *   strip   one slim band across the dash, 18:1 (Avatr 06T): speed and gear at the left, a light line with the car on it in the
 *           middle, charge and range at the right
 *
 * A brand is data (CLUSTER_BRANDS: layout, type, weight, accent override, labels); the accent otherwise comes from the car's
 * `cockpit.accentColor`. Every cabin GLB names its picture `INT_Display_screen_cluster`, so nothing here lists cars to attach to:
 * a car with no entry in CLUSTER_BRANDS keeps the picture the Blender export carries.
 */
const W = 2048;

export interface ClusterBrand {
  layout: 'gauge' | 'wide' | 'calm' | 'strip';
  font: string;
  /** weight of the big numerals */
  weight: number;
  /** replaces the cockpit's accent */
  accent?: string;
  /** the picture follows the HMI's light / dark theme (the Seal, as approved); every other cluster is a dark glass, as on the road */
  followTheme?: boolean;
  /** a word on the status line next to the mode (the system's name) */
  system?: string;
  /** show the four tyre-pressure chips (the gauge layout) */
  tyres?: boolean;
  /** what the range is measured to */
  cycle: string;
  /** an efficiency readout */
  efficiency?: string;
}

const SANS = "'Inter', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif";
const ROUND = "'Roboto', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif";
const LIGHT = "'Helvetica Neue', 'Segoe UI', 'Inter', Arial, sans-serif";

export const CLUSTER_BRANDS: Record<string, ClusterBrand> = {
  'byd-seal': { layout: 'gauge', font: SANS, weight: 700, followTheme: true, system: 'DiLink', tyres: true, cycle: 'CLTC', efficiency: '14.6 kWh/100km' },
  'denza-z9': { layout: 'gauge', font: LIGHT, weight: 500, accent: '#d6b27a', system: 'DiLink', tyres: true, cycle: 'CLTC', efficiency: '17.2 kWh/100km' },
  'luxeed-rx': { layout: 'gauge', font: SANS, weight: 600, system: 'HarmonyOS', tyres: false, cycle: 'CLTC', efficiency: '15.8 kWh/100km' },
  'xpeng-g9l': { layout: 'wide', font: ROUND, weight: 500, system: 'XOS', cycle: 'CLTC', efficiency: '16.4 kWh/100km' },
  'nio-es8': { layout: 'wide', font: LIGHT, weight: 300, system: 'NIO OS', cycle: 'CLTC', efficiency: '18.9 kWh/100km' },
  'xiaomi-su7-ultra': { layout: 'wide', font: SANS, weight: 700, accent: '#ff6700', system: 'HyperOS', cycle: 'CLTC', efficiency: '15.1 kWh/100km' },
  'zeekr-7x': { layout: 'calm', font: LIGHT, weight: 200, system: 'ZEEKR OS', cycle: 'CLTC', efficiency: '15.9 kWh/100km' },
  'voyah-passion-s': { layout: 'calm', font: LIGHT, weight: 300, accent: '#c9a96e', system: 'VOYAH', cycle: 'CLTC', efficiency: '16.8 kWh/100km' },
  'avatr-06t': { layout: 'strip', font: SANS, weight: 300, accent: '#b48cff', system: 'AVATR', cycle: 'CLTC', efficiency: '16.1 kWh/100km' },
};

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

type Ctx = CanvasRenderingContext2D;

function text(ctx: Ctx, brand: ClusterBrand, s: string, x: number, y: number, size: number, color: string, weight = 600, align: CanvasTextAlign = 'left') {
  ctx.font = `${weight} ${size}px ${brand.font}`;
  ctx.fillStyle = color;
  ctx.textAlign = align;
  ctx.textBaseline = 'alphabetic';
  ctx.fillText(s, x, y);
}

function roundRect(ctx: Ctx, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function glass(ctx: Ctx, w: number, h: number, p: Pal, s: ClusterState) {
  const bg = ctx.createLinearGradient(0, 0, 0, h);
  bg.addColorStop(0, p.bg0);
  bg.addColorStop(1, p.bg1);
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, w, h);
  const glow = ctx.createRadialGradient(w / 2, h * 0.55, 40, w / 2, h * 0.55, w * 0.34);
  glow.addColorStop(0, s.dark ? 'rgba(53,198,255,0.12)' : 'rgba(53,150,255,0.09)');
  glow.addColorStop(1, 'rgba(53,198,255,0)');
  ctx.fillStyle = glow;
  ctx.fillRect(0, 0, w, h);
}

function statusLine(ctx: Ctx, brand: ClusterBrand, w: number, h: number, p: Pal, s: ClusterState) {
  const k = h / 768;
  text(ctx, brand, '07:41', 64, 64 * k, 40 * k, p.ink, 600);
  text(ctx, brand, '24°C', 64 + 156 * k, 64 * k, 34 * k, p.dim, 500);
  text(ctx, brand, `${s.mode.toUpperCase()}${brand.system ? '  ·  ' + brand.system : ''}`, w / 2, 62 * k, 30 * k, p.accent, 700, 'center');
  for (let i = 0; i < 4; i++) {
    ctx.fillStyle = i < 3 ? p.ink : p.faint;
    ctx.fillRect(w - 250 * k + i * 18 * k, (62 - (i + 1) * 9) * k, 11 * k, (i + 1) * 9 * k);
  }
  ctx.beginPath();
  ctx.arc(w - 150 * k, 48 * k, 9 * k, 0, Math.PI * 2);
  ctx.fillStyle = p.accent;
  ctx.fill();
  text(ctx, brand, 'LTE', w - 120 * k, 62 * k, 26 * k, p.dim, 600);
  ctx.strokeStyle = p.faint;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(48, 92 * k);
  ctx.lineTo(w - 48, 92 * k);
  ctx.stroke();
}

function bottomLine(ctx: Ctx, brand: ClusterBrand, w: number, h: number, p: Pal, s: ClusterState) {
  const k = h / 768;
  ctx.strokeStyle = p.faint;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(48, h - 60 * k);
  ctx.lineTo(w - 48, h - 60 * k);
  ctx.stroke();
  text(ctx, brand, 'ODO 12,486 km', 64, h - 20 * k, 28 * k, p.dim, 600);
  text(ctx, brand, 'TRIP 0.0 km', w - 64, h - 20 * k, 28 * k, p.dim, 600, 'right');
  const chip = (x: number, label: string, on: boolean, color: string) => {
    roundRect(ctx, x, h - 50 * k, 150 * k, 40 * k, 20 * k);
    ctx.fillStyle = on ? color : p.faint;
    ctx.globalAlpha = on ? 0.9 : 0.8;
    ctx.fill();
    ctx.globalAlpha = 1;
    text(ctx, brand, label, x + 75 * k, h - 21 * k, 22 * k, on ? (s.dark ? '#02080d' : '#ffffff') : p.dim, 700, 'center');
  };
  const c0 = w / 2 - 237 * k;
  chip(c0, 'BELT', true, p.good);
  chip(c0 + 162 * k, 'LAMPS', s.lamps, p.accent);
  chip(c0 + 324 * k, 'ADAS', s.adas, p.accent);
}

/** Lanes converging on the horizon with our car from behind and two cars ahead, in the box (x, y, bw, bh). */
function roadScene(ctx: Ctx, p: Pal, s: ClusterState, x: number, y: number, bw: number, bh: number, tyres: boolean, brand: ClusterBrand) {
  ctx.save();
  roundRect(ctx, x, y, bw, bh, 30 * (bh / 580));
  ctx.clip();
  const g = ctx.createLinearGradient(0, y, 0, y + bh);
  g.addColorStop(0, s.dark ? '#0a121b' : '#e4edf3');
  g.addColorStop(1, p.road);
  ctx.fillStyle = g;
  ctx.fillRect(x, y, bw, bh);
  const cx = x + bw / 2;
  const vy = y + bh * 0.21;
  const base = y + bh;
  const lane = (xb: number, color: string, w: number, dash = false) => {
    ctx.strokeStyle = color;
    ctx.lineWidth = w;
    ctx.setLineDash(dash ? [34, 26] : []);
    ctx.beginPath();
    ctx.moveTo(xb, base);
    ctx.lineTo(cx + (xb - cx) * 0.1, vy);
    ctx.stroke();
    ctx.setLineDash([]);
  };
  const half = bw * 0.355;
  lane(cx - half, s.adas ? p.accent : p.dim, 7);
  lane(cx + half, s.adas ? p.accent : p.dim, 7);
  lane(cx, p.faint, 4, true);
  if (s.adas) {
    const l = ctx.createLinearGradient(0, base, 0, vy);
    l.addColorStop(0, 'rgba(53,198,255,0.32)');
    l.addColorStop(1, 'rgba(53,198,255,0)');
    ctx.fillStyle = l;
    ctx.beginPath();
    ctx.moveTo(cx - half, base);
    ctx.lineTo(cx + half, base);
    ctx.lineTo(cx + half * 0.1, vy);
    ctx.lineTo(cx - half * 0.1, vy);
    ctx.closePath();
    ctx.fill();
  }
  const k = bh / 580;
  ctx.strokeStyle = s.adas ? 'rgba(53,198,255,0.55)' : p.faint;
  ctx.lineWidth = 3;
  for (let i = 0; i < 3; i++) {
    ctx.beginPath();
    ctx.ellipse(cx, y + bh * 0.72, (90 + i * 70) * k * (bw / 640), (26 + i * 18) * k, 0, Math.PI, Math.PI * 2);
    ctx.stroke();
  }
  const lead = (lx: number, ly: number, kk: number) => {
    roundRect(ctx, lx - 44 * kk, ly - 28 * kk, 88 * kk, 50 * kk, 12 * kk);
    ctx.fillStyle = s.dark ? '#43515f' : '#9fb0be';
    ctx.fill();
    ctx.fillStyle = '#ff5d5d';
    ctx.fillRect(lx - 38 * kk, ly - 12 * kk, 22 * kk, 7 * kk);
    ctx.fillRect(lx + 16 * kk, ly - 12 * kk, 22 * kk, 7 * kk);
  };
  lead(cx + bw * 0.04, y + bh * 0.38, 0.8 * k * 1.4);
  lead(cx - bw * 0.25, y + bh * 0.28, 0.5 * k * 1.4);
  ctx.save();
  ctx.translate(cx, y + bh * 0.78);
  ctx.scale(k * 1.15, k * 1.15);
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

  if (tyres) {
    const tyre = (tx: number, ty: number) => {
      roundRect(ctx, tx, ty, 132, 62, 14);
      ctx.fillStyle = s.dark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)';
      ctx.fill();
      ctx.strokeStyle = p.faint;
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.strokeStyle = p.dim;
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.arc(tx + 28, ty + 31, 15, Math.PI * 0.2, Math.PI * 1.8);
      ctx.stroke();
      text(ctx, brand, '2.5', tx + 100, ty + 42, 32, p.ink, 700, 'center');
    };
    tyre(x + 16, y + 16);
    tyre(x + bw - 148, y + 16);
    tyre(x + 16, y + bh - 78);
    tyre(x + bw - 148, y + bh - 78);
  }
}

function gearStack(ctx: Ctx, brand: ClusterBrand, gx: number, y0: number, step: number, size: number, p: Pal, s: ClusterState) {
  ['P', 'R', 'N', 'D'].forEach((g, i) => {
    const gy = y0 + i * step;
    const on = g === s.gear;
    if (on) {
      roundRect(ctx, gx - size * 0.72, gy - size * 1.08, size * 1.44, size * 1.44, size * 0.3);
      ctx.fillStyle = g === 'R' ? (s.dark ? '#ff5d5d' : '#dc2626') : p.accent;
      ctx.fill();
    }
    text(ctx, brand, g, gx, gy, size, on ? (s.dark ? '#031018' : '#ffffff') : p.dim, 700, 'center');
  });
}

function gearRow(ctx: Ctx, brand: ClusterBrand, x0: number, y: number, step: number, size: number, p: Pal, s: ClusterState) {
  ['P', 'R', 'N', 'D'].forEach((g, i) => {
    const gx = x0 + i * step;
    const on = g === s.gear;
    text(ctx, brand, g, gx, y, on ? size * 1.25 : size, on ? (g === 'R' ? '#ff5d5d' : p.accent) : p.faint, on ? 700 : 500, 'center');
  });
}

// ------------------------------------------------------------------ layouts

function layoutGauge(ctx: Ctx, brand: ClusterBrand, w: number, h: number, p: Pal, s: ClusterState) {
  const k = h / 768;
  statusLine(ctx, brand, w, h, p, s);
  const cx = w / 2;
  const cy = h * 0.553;
  const R = Math.min(268 * k, w * 0.13);
  const a0 = (135 * Math.PI) / 180;
  const sweep = (270 * Math.PI) / 180;
  const vMax = 240;
  const frac = Math.min(1, s.speed / vMax);
  ctx.lineCap = 'round';
  ctx.lineWidth = 22 * k;
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
    ctx.strokeStyle = v / vMax <= frac && s.speed > 0 ? p.ink : major ? p.dim : p.faint;
    ctx.lineWidth = (major ? 4 : 2) * k;
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(a) * (R - 34 * k), cy + Math.sin(a) * (R - 34 * k));
    ctx.lineTo(cx + Math.cos(a) * (R - (major ? 62 : 48) * k), cy + Math.sin(a) * (R - (major ? 62 : 48) * k));
    ctx.stroke();
    if (major) text(ctx, brand, String(v), cx + Math.cos(a) * (R - 96 * k), cy + Math.sin(a) * (R - 96 * k) + 12 * k, 30 * k, p.dim, 600, 'center');
  }
  text(ctx, brand, String(Math.round(s.speed)), cx, cy + 62 * k, 214 * k, p.ink, brand.weight, 'center');
  text(ctx, brand, 'km/h', cx, cy + 118 * k, 36 * k, p.dim, 600, 'center');

  gearStack(ctx, brand, cx + R + 128 * k, 218 * k, 92 * k, 52 * k, p, s);

  const bx = w - 318 * k;
  const by = 330 * k;
  const br = 118 * k;
  ctx.lineWidth = 20 * k;
  ctx.lineCap = 'round';
  ctx.strokeStyle = p.faint;
  ctx.beginPath();
  ctx.arc(bx, by, br, 0, Math.PI * 2);
  ctx.stroke();
  ctx.strokeStyle = s.soc < 0.2 ? p.warn : p.good;
  ctx.beginPath();
  ctx.arc(bx, by, br, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * s.soc);
  ctx.stroke();
  ctx.lineCap = 'butt';
  text(ctx, brand, String(Math.round(s.soc * 100)), bx - 8 * k, by + 30 * k, 92 * k, p.ink, 700, 'center');
  text(ctx, brand, '%', bx + 62 * k, by + 8 * k, 34 * k, p.dim, 600, 'center');
  ctx.fillStyle = p.good;
  ctx.beginPath();
  ctx.moveTo(bx + 12 * k, by - 78 * k);
  ctx.lineTo(bx - 18 * k, by - 38 * k);
  ctx.lineTo(bx - 2 * k, by - 38 * k);
  ctx.lineTo(bx - 12 * k, by - 8 * k);
  ctx.lineTo(bx + 22 * k, by - 52 * k);
  ctx.lineTo(bx + 5 * k, by - 52 * k);
  ctx.closePath();
  ctx.fill();
  text(ctx, brand, `${s.rangeKm}`, bx - 6 * k, 566 * k, 84 * k, p.ink, 700, 'center');
  text(ctx, brand, 'km', bx + 112 * k, 566 * k, 34 * k, p.dim, 600, 'center');
  text(ctx, brand, `RANGE · ${brand.cycle}`, bx, 612 * k, 26 * k, p.dim, 600, 'center');
  if (brand.efficiency) {
    roundRect(ctx, bx - 170 * k, 640 * k, 340 * k, 56 * k, 28 * k);
    ctx.fillStyle = p.faint;
    ctx.fill();
    text(ctx, brand, brand.efficiency, bx, 678 * k, 28 * k, p.ink, 600, 'center');
  }
  roadScene(ctx, p, s, 56, 112 * k, Math.min(640 * k, w * 0.31), 580 * k, brand.tyres !== false, brand);
  bottomLine(ctx, brand, w, h, p, s);
}

function layoutWide(ctx: Ctx, brand: ClusterBrand, w: number, h: number, p: Pal, s: ClusterState) {
  const k = h / 768;
  statusLine(ctx, brand, w, h, p, s);
  // left: the gear row and the speed
  gearRow(ctx, brand, 150 * k, 200 * k, 86 * k, 54 * k, p, s);
  text(ctx, brand, String(Math.round(s.speed)), w * 0.17, 520 * k, 330 * k, p.ink, brand.weight, 'center');
  text(ctx, brand, 'km/h', w * 0.17, 590 * k, 40 * k, p.dim, 500, 'center');
  // a thin speed bar under it
  const bw = w * 0.26;
  const bx = w * 0.17 - bw / 2;
  roundRect(ctx, bx, 628 * k, bw, 12 * k, 6 * k);
  ctx.fillStyle = p.faint;
  ctx.fill();
  roundRect(ctx, bx, 628 * k, Math.max(12 * k, bw * Math.min(1, s.speed / 240)), 12 * k, 6 * k);
  ctx.fillStyle = p.accent;
  ctx.fill();
  // middle: the road
  const rw = Math.min(w * 0.30, 700 * k);
  roadScene(ctx, p, s, w * 0.5 - rw / 2, 118 * k, rw, 560 * k, false, brand);
  // right: charge and range
  const rx = w * 0.80;
  text(ctx, brand, String(Math.round(s.soc * 100)), rx - 40 * k, 330 * k, 150 * k, p.ink, brand.weight, 'right');
  text(ctx, brand, '%', rx - 20 * k, 330 * k, 44 * k, p.dim, 500, 'left');
  const cw = w * 0.2;
  roundRect(ctx, rx - cw / 2 - 20 * k, 366 * k, cw, 22 * k, 11 * k);
  ctx.fillStyle = p.faint;
  ctx.fill();
  roundRect(ctx, rx - cw / 2 - 20 * k, 366 * k, Math.max(22 * k, cw * s.soc), 22 * k, 11 * k);
  ctx.fillStyle = s.soc < 0.2 ? p.warn : p.good;
  ctx.fill();
  text(ctx, brand, `${s.rangeKm}`, rx - 40 * k, 520 * k, 140 * k, p.ink, brand.weight, 'right');
  text(ctx, brand, 'km', rx - 20 * k, 520 * k, 44 * k, p.dim, 500, 'left');
  text(ctx, brand, `RANGE · ${brand.cycle}`, rx - 20 * k, 566 * k, 26 * k, p.dim, 600, 'center');
  if (brand.efficiency) text(ctx, brand, brand.efficiency, rx - 20 * k, 620 * k, 28 * k, p.dim, 500, 'center');
  bottomLine(ctx, brand, w, h, p, s);
}

function layoutCalm(ctx: Ctx, brand: ClusterBrand, w: number, h: number, p: Pal, s: ClusterState) {
  const k = h / 768;
  // a quieter status line: time and temperature only
  text(ctx, brand, '07:41', 64, 64 * k, 38 * k, p.ink, 400);
  text(ctx, brand, '24°C', 64 + 150 * k, 64 * k, 32 * k, p.dim, 300);
  text(ctx, brand, `${s.mode.toUpperCase()}`, w / 2, 62 * k, 28 * k, p.accent, 500, 'center');
  text(ctx, brand, brand.system ?? '', w - 64, 62 * k, 28 * k, p.dim, 400, 'right');
  // the hairline arc and the light numeral, centre-left
  const cx = w * 0.36;
  const cy = h * 0.56;
  const R = Math.min(250 * k, w * 0.14);
  ctx.lineCap = 'round';
  ctx.lineWidth = 3 * k;
  ctx.strokeStyle = p.faint;
  ctx.beginPath();
  ctx.arc(cx, cy, R, (140 * Math.PI) / 180, (400 * Math.PI) / 180);
  ctx.stroke();
  ctx.lineWidth = 9 * k;
  ctx.strokeStyle = p.accent;
  const frac = Math.min(1, s.speed / 240);
  ctx.beginPath();
  ctx.arc(cx, cy, R, (140 * Math.PI) / 180, (140 * Math.PI) / 180 + Math.max(0.02, (260 * Math.PI) / 180 * frac));
  ctx.stroke();
  ctx.lineCap = 'butt';
  text(ctx, brand, String(Math.round(s.speed)), cx, cy + 74 * k, 240 * k, p.ink, brand.weight, 'center');
  text(ctx, brand, 'km/h', cx, cy + 130 * k, 34 * k, p.dim, 400, 'center');
  // the gear, a single large letter beside the arc
  text(ctx, brand, s.gear, cx + R + 90 * k, cy + 30 * k, 96 * k, s.gear === 'R' ? '#ff5d5d' : p.accent, 400, 'center');
  gearRow(ctx, brand, cx + R + 28 * k, cy + 84 * k, 46 * k, 24 * k, p, s);
  // the quiet lane scene at the right, then charge and range under it
  const rw = Math.min(w * 0.27, 600 * k);
  const rx = w * 0.70;
  ctx.globalAlpha = 0.9;
  roadScene(ctx, p, s, rx, 118 * k, rw, 380 * k, false, brand);
  ctx.globalAlpha = 1;
  text(ctx, brand, `${Math.round(s.soc * 100)}%`, rx + 10, 576 * k, 84 * k, p.ink, brand.weight, 'left');
  text(ctx, brand, `${s.rangeKm} km`, rx + rw, 576 * k, 56 * k, p.dim, 300, 'right');
  const cw = rw;
  roundRect(ctx, rx, 612 * k, cw, 8 * k, 4 * k);
  ctx.fillStyle = p.faint;
  ctx.fill();
  roundRect(ctx, rx, 612 * k, Math.max(8 * k, cw * s.soc), 8 * k, 4 * k);
  ctx.fillStyle = s.soc < 0.2 ? p.warn : p.good;
  ctx.fill();
  text(ctx, brand, `${brand.cycle}${brand.efficiency ? '  ·  ' + brand.efficiency : ''}`, rx + rw, 656 * k, 24 * k, p.dim, 400, 'right');
  text(ctx, brand, 'ODO 12,486 km', 64, h - 28 * k, 26 * k, p.dim, 300);
}

function layoutStrip(ctx: Ctx, brand: ClusterBrand, w: number, h: number, p: Pal, s: ClusterState) {
  const u = h / 114; // a unit: the strip is about 114 px tall at 4096 wide
  const y = h * 0.66;
  // left: time, the numeral, the gear row
  text(ctx, brand, '07:41', w * 0.02, h * 0.42, 34 * u, p.ink, 400);
  text(ctx, brand, '24°C', w * 0.02, h * 0.82, 26 * u, p.dim, 300);
  text(ctx, brand, String(Math.round(s.speed)), w * 0.105, y + 8 * u, 84 * u, p.ink, brand.weight, 'center');
  text(ctx, brand, 'km/h', w * 0.128, y + 8 * u, 24 * u, p.dim, 400, 'left');
  gearRow(ctx, brand, w * 0.19, y + 4 * u, w * 0.012, 36 * u, p, s);
  // the middle: a hairline road with the car on it and the lane brackets, lit when assistance is on
  const x0 = w * 0.30;
  const x1 = w * 0.64;
  const cx = (x0 + x1) / 2;
  const line = ctx.createLinearGradient(x0, 0, x1, 0);
  line.addColorStop(0, 'rgba(255,255,255,0)');
  line.addColorStop(0.5, s.adas ? p.accent : p.dim);
  line.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.strokeStyle = line;
  ctx.lineWidth = 3 * u;
  ctx.beginPath();
  ctx.moveTo(x0, h * 0.58);
  ctx.lineTo(x1, h * 0.58);
  ctx.stroke();
  ctx.lineWidth = 2 * u;
  ctx.strokeStyle = s.adas ? p.accent : p.faint;
  for (const side of [-1, 1]) {
    ctx.beginPath();
    ctx.moveTo(cx + side * 200 * u, h * 0.15);
    ctx.lineTo(cx + side * 120 * u, h * 0.86);
    ctx.stroke();
  }
  roundRect(ctx, cx - 28 * u, h * 0.30, 56 * u, h * 0.50, 12 * u);
  ctx.fillStyle = s.dark ? '#e7eef5' : '#4a5a69';
  ctx.fill();
  ctx.fillStyle = '#ff4d4d';
  ctx.fillRect(cx - 22 * u, h * 0.62, 44 * u, 5 * u);
  text(ctx, brand, `${s.mode.toUpperCase()}`, cx + 260 * u, h * 0.46, 24 * u, p.accent, 600, 'left');
  // the right: charge bar and range
  const bx = w * 0.70;
  const bw = w * 0.14;
  text(ctx, brand, `${Math.round(s.soc * 100)}%`, bx, h * 0.52, 44 * u, p.ink, brand.weight, 'left');
  roundRect(ctx, bx, h * 0.66, bw, 8 * u, 4 * u);
  ctx.fillStyle = p.faint;
  ctx.fill();
  roundRect(ctx, bx, h * 0.66, Math.max(8 * u, bw * s.soc), 8 * u, 4 * u);
  ctx.fillStyle = s.soc < 0.2 ? p.warn : p.good;
  ctx.fill();
  text(ctx, brand, `${s.rangeKm} km`, w * 0.98, h * 0.52, 44 * u, p.ink, 300, 'right');
  text(ctx, brand, `${brand.cycle}  ·  ${brand.system ?? ''}`, w * 0.98, h * 0.84, 22 * u, p.dim, 400, 'right');
}

/**
 * Draws one frame of a brand's cluster into `ctx` (w x h pixels). Pure of the DOM but for the canvas it is given.
 * The first argument is the brand's data (CLUSTER_BRANDS[slug]); `s` is the live state.
 */
export function DriverClusterTextureGenerator(brand: ClusterBrand, ctx: Ctx, w: number, h: number, s: ClusterState): void {
  const p = palette({ ...s, accent: brand.accent ?? s.accent });
  ctx.save();
  ctx.clearRect(0, 0, w, h);
  glass(ctx, w, h, p, s);
  if (brand.layout === 'wide') layoutWide(ctx, brand, w, h, p, s);
  else if (brand.layout === 'calm') layoutCalm(ctx, brand, w, h, p, s);
  else if (brand.layout === 'strip') layoutStrip(ctx, brand, w, h, p, s);
  else layoutGauge(ctx, brand, w, h, p, s);
  ctx.restore();
}

// ----------------------------------------------------------------------- the hook

const CLUSTER_MATERIAL = /display_screen_cluster|screen_cluster/i;

function materialsOf(o: THREE.Mesh): THREE.Material[] {
  return Array.isArray(o.material) ? o.material : [o.material];
}

function stateOf(vehicle: Vehicle, brand: ClusterBrand): ClusterState {
  const s = useVehicleStore.getState();
  const cltc = vehicle.variants[0]?.range[0]?.km ?? 500;
  const mode = vehicle.cockpit.driveModes?.find((d) => d.id === s.driveMode)?.label ?? 'Comfort';
  return {
    dark: brand.followTheme ? s.hmiTheme !== 'light' : true,
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

/** The picture's aspect (long side over short) from the quad's own geometry. */
function aspectOf(mesh: THREE.Mesh): number {
  const g = mesh.geometry;
  g.computeBoundingBox();
  const d = g.boundingBox!.getSize(new THREE.Vector3());
  const [a, b] = [d.x, d.y, d.z].sort((x, y) => y - x);
  return b > 1e-4 ? THREE.MathUtils.clamp(a / b, 1.2, 24) : 2.65;
}

/**
 * Swaps the cluster's emissive picture for the live canvas. The mapping is copied from the picture it replaces, so the UVs of
 * the Blender quad stay as they were; the original comes back when the cabin unmounts.
 */
export function useLiveCluster(model: THREE.Object3D, vehicle: Vehicle, glow: number | null) {
  const invalidate = useThree((s) => s.invalidate);
  const brand = CLUSTER_BRANDS[vehicle.slug];
  const found = React.useMemo(() => {
    const mats: THREE.MeshStandardMaterial[] = [];
    let mesh: THREE.Mesh | null = null;
    if (!brand) return { mats, aspect: 2.65 };
    model.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      for (const mat of materialsOf(m)) {
        if (CLUSTER_MATERIAL.test(mat.name) && mat instanceof THREE.MeshStandardMaterial && !mats.includes(mat)) {
          mats.push(mat);
          mesh ??= m;
        }
      }
    });
    return { mats, aspect: mesh ? aspectOf(mesh) : 2.65 };
  }, [model, brand]);
  const slots = found.mats;

  React.useEffect(() => {
    if (!slots.length || !brand) return;
    const canvas = document.createElement('canvas');
    // an 18:1 strip needs twice the width to keep its type crisp
    canvas.width = found.aspect > 6 ? 2 * W : W;
    canvas.height = Math.round(canvas.width / found.aspect);
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
      DriverClusterTextureGenerator(brand, ctx, canvas.width, canvas.height, stateOf(vehicle, brand));
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
  }, [slots, brand, found.aspect, vehicle, invalidate]);

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
