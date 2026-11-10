import * as THREE from 'three';
import { Builder, cached, hex, placement, rng, smooth, type V3 } from './kit';
import { CELL, SIGN_WORDS, TILE, cellUV } from './textures';

/**
 * A row of buildings built as real volumes, not a painted wall: bays of windows set back in their reveals,
 * balconies and enclosed balconies with their air-conditioners, shopfronts with signboards, awnings and shutters,
 * curtain-wall towers, cornices, parapets and rooftop plant. Seeded, so a row is the same on every machine, and merged
 * into six geometries (rendered walls, tile-clad walls, brick, plain trim, the window and sign atlas, and the lit
 * windows of the evening) so a whole street costs six draw calls.
 *
 * The row's frame: x along the street from 0 to `length`, y up, the facade on the plane z = 0 facing +z (toward the street),
 * the buildings behind it at z < 0. The caller turns and places the row.
 */
export interface Row {
  stucco: THREE.BufferGeometry;
  tile: THREE.BufferGeometry;
  brick: THREE.BufferGeometry;
  trim: THREE.BufferGeometry;
  atlas: THREE.BufferGeometry;
  lit: THREE.BufferGeometry;
  /** the lit shop signs, for the evening */
  signLit: THREE.BufferGeometry;
  length: number;
  /** the tallest roof, m */
  height: number;
}

export interface RowSpec {
  length: number;
  seed: number;
  /** tallest roof allowed, m */
  maxHeight?: number;
  minHeight?: number;
  /** 'street' (shops below, flats above), 'lot' (taller blocks set well back), 'mixed' */
  style?: 'street' | 'lot';
}

const STUCCO = ['#f1e9db', '#e7dac4', '#d9d7d1', '#e9cfb2', '#cfd9d5', '#f3f1ed', '#dcbfa8', '#cbd5df', '#e4e0cf'];
const ACCENT = ['#8d6f5b', '#6d7f8c', '#a9835e', '#7d8f79', '#5e6672', '#b4694f'];
const TRIM = '#d1d2d4';
const SLAB = '#b8babd';
const ROOF = '#6e7378';

/** Occlusion by height: the foot of a wall is dirtier, shaded by the footway's traffic and its own plinth. */
function aoAt(y: number): number {
  return 0.74 + 0.26 * smooth(0, 3.4, y);
}

class Row$ {
  stucco = new Builder();
  tile = new Builder();
  brick = new Builder();
  trim = new Builder();
  atlas = new Builder();
  lit = new Builder();
  signLit = new Builder();
  r: () => number;
  constructor(seed: number) {
    this.r = rng(seed);
  }

  /** A wall rectangle, tinted, with the foot's occlusion in its corners, onto the builder of its material. */
  wall(b: Builder, o: V3, u: V3, v: V3, w: number, h: number, tint: V3, tile: number, ou: number, ov: number, extra = 1) {
    const c = (y: number): V3 => {
      const k = aoAt(y) * extra;
      return [tint[0] * k, tint[1] * k, tint[2] * k];
    };
    const y0 = o[1];
    const y1 = o[1] + u[1] * w;
    const y2 = y1 + v[1] * h;
    const y3 = o[1] + v[1] * h;
    b.rect(o, u, v, w, h, [c(y0), c(y1), c(y2), c(y3)], tile, ou, ov);
  }

  /** A front-facing wall rectangle on the facade plane (z = 0 or at z), uv in metres so the texture tiles. */
  front(b: Builder, x: number, y: number, w: number, h: number, tint: V3, tileM: number, z = 0, extra = 1) {
    if (w <= 1e-4 || h <= 1e-4) return;
    this.wall(b, [x, y, z], [1, 0, 0], [0, 1, 0], w, h, tint, tileM, x, y, extra);
  }

  /** A window of an atlas cell, in its reveal, on the facade at x, y. */
  opening(b: Builder, x: number, y: number, w: number, h: number, cell: number, tint: V3, tileM: number, rv = 0.2, wallB = this.stucco, lit = false) {
    const wallTint = tint;
    const dark: V3 = [tint[0] * 0.62, tint[1] * 0.62, tint[2] * 0.62];
    // reveals
    wallB.rect([x, y, 0], [0, 0, -1], [0, 1, 0], rv, h, dark, tileM, 0, y);
    wallB.rect([x + w, y, -rv], [0, 0, 1], [0, 1, 0], rv, h, dark, tileM, 0, y);
    wallB.rect([x, y, 0], [1, 0, 0], [0, 0, -1], w, rv, [dark[0] * 0.8, dark[1] * 0.8, dark[2] * 0.8], tileM, x, 0);
    wallB.rect([x, y + h, -rv], [1, 0, 0], [0, 0, 1], w, rv, [dark[0] * 0.55, dark[1] * 0.55, dark[2] * 0.55], tileM, x, 0);
    const k = aoAt(y);
    const [u0, v0, u1, v1] = cellUV(cell);
    b.rect([x, y, -rv], [1, 0, 0], [0, 1, 0], w, h, [k, k, k], 0, 0, 0, [u0, v0, u1, v1]);
    void wallTint;
    if (lit) this.litQuad(x, y, w, h, -rv + 0.004);
  }

  litQuad(x: number, y: number, w: number, h: number, z: number) {
    const warm: V3 = this.r() > 0.35 ? [1, 0.85, 0.58] : [0.78, 0.9, 1];
    const k = 0.55 + this.r() * 0.45;
    this.lit.rect([x + 0.04, y + 0.04, z], [1, 0, 0], [0, 1, 0], w - 0.08, h - 0.08, [warm[0] * k, warm[1] * k, warm[2] * k], 0);
  }
}

function atlasQuad(row: Row$, x: number, y: number, z: number, w: number, h: number, cell: number, k = 1) {
  row.atlas.rect([x, y, z], [1, 0, 0], [0, 1, 0], w, h, [k, k, k], 0, 0, 0, cellUV(cell));
}

// ---------------------------------------------------------------------------------------------- the ground floor

/** Shopfronts along a stretch of facade: glass, a door, signboards, awnings and shutters. */
function shopfronts(row: Row$, x0: number, w: number, tint: V3, accent: V3, groundH: number, tileM: number) {
  const r = row.r;
  // modules 4 to 6.5 m wide
  const mods: number[] = [];
  let left = w;
  while (left > 0.1) {
    const m = left < 8.5 ? left : 4 + r() * 2.6;
    mods.push(m);
    left -= m;
  }
  let x = x0;
  const signH = 0.95;
  const plinth = 0.4;
  const glazeTop = groundH - signH - 0.28;
  for (const mw of mods) {
    const pier = 0.35;
    // plinth, piers and the lintel over the glazing
    row.front(row.trim, x, 0, mw, plinth, hex('#8d9096'), 0, 0.0);
    row.front(row.stucco, x, glazeTop, mw, groundH - glazeTop - signH, tint, tileM);
    row.front(row.stucco, x, plinth, pier, glazeTop - plinth, tint, tileM);
    row.front(row.stucco, x + mw - pier, plinth, pier, glazeTop - plinth, tint, tileM);
    const gx = x + pier;
    const gw = mw - 2 * pier;
    const shut = r() > 0.82;
    const rv = 0.14;
    // glazing: either a shutter, or glass with a door in it
    const darkTint: V3 = [tint[0] * 0.55, tint[1] * 0.55, tint[2] * 0.55];
    row.stucco.rect([gx, plinth, 0], [0, 0, -1], [0, 1, 0], rv, glazeTop - plinth, darkTint, 0);
    row.stucco.rect([gx + gw, plinth, -rv], [0, 0, 1], [0, 1, 0], rv, glazeTop - plinth, darkTint, 0);
    row.stucco.rect([gx, glazeTop, -rv], [1, 0, 0], [0, 0, 1], gw, rv, [darkTint[0] * 0.6, darkTint[1] * 0.6, darkTint[2] * 0.6], 0);
    if (shut) {
      atlasQuad(row, gx, plinth, -rv, gw, glazeTop - plinth, CELL.shutter, 0.9);
    } else {
      const doorW = Math.min(1.3, gw * 0.3);
      const doorAt = r() > 0.5 ? gx + 0.2 : gx + gw - doorW - 0.2;
      atlasQuad(row, gx, plinth, -rv, gw, glazeTop - plinth, CELL.shopGlass, 1);
      atlasQuad(row, doorAt, plinth, -rv + 0.01, doorW, glazeTop - plinth, CELL.shopDoor, 1);
      // warm interior at night
      row.litQuad(gx, plinth + 0.2, gw, glazeTop - plinth - 0.3, -rv + 0.006);
    }
    // the signboard on a shallow box
    const word = Math.floor(r() * SIGN_WORDS.length);
    const sx = x + 0.25;
    const sw = mw - 0.5;
    row.trim.box(sx - 0.05, groundH - signH - 0.05, 0, sw + 0.1, signH + 0.1, 0.16, hex('#4b4f57'), 0, ['+z']);
    atlasQuad(row, sx, groundH - signH, 0.162, sw, signH, CELL.sign0 + word, 1);
    row.signLit.rect([sx, groundH - signH, 0.166], [1, 0, 0], [0, 1, 0], sw, signH, hex('#fff2d8', 0.9), 0, 0, 0, cellUV(CELL.sign0 + word));
    // an awning over some of them
    if (r() > 0.55 && !shut) {
      const stripe = r() > 0.5;
      const a = r() > 0.5 ? hex('#c74a3c') : hex('#2f6aa8');
      const aw = gw;
      const n = stripe ? 8 : 1;
      for (let i = 0; i < n; i++) {
        const c: V3 = stripe ? (i % 2 ? [0.95, 0.94, 0.9] : a) : a;
        const sw2 = aw / n;
        row.trim.quad(
          [gx + i * sw2, glazeTop + 0.05, 0.05],
          [gx + (i + 1) * sw2, glazeTop + 0.05, 0.05],
          [gx + (i + 1) * sw2, glazeTop - 0.55, 1.35],
          [gx + i * sw2, glazeTop - 0.55, 1.35],
          c,
          [0, 0, 1, 1],
          true,
          [0, 0.8, 0.6],
        );
        row.trim.quad([gx + i * sw2, glazeTop - 0.55, 1.35], [gx + (i + 1) * sw2, glazeTop - 0.55, 1.35], [gx + (i + 1) * sw2, glazeTop - 0.75, 1.35], [gx + i * sw2, glazeTop - 0.75, 1.35], c, [0, 0, 1, 1]);
      }
    }
    // a pipe or a light box, now and then
    if (r() > 0.7) row.trim.box(x + mw - 0.2, 0.3, 0.0, 0.1, groundH, 0.1, hex('#9a9da3'), 0);
    x += mw;
  }
  void accent;
}

// ---------------------------------------------------------------------------------------------- the building types

interface Block {
  x0: number;
  w: number;
  height: number;
  depth: number;
}

/** The roof: a slab, a parapet cap on the street front, and the plant standing on it. */
function roof(row: Row$, b: Block, tint: V3) {
  const r = row.r;
  const { x0, w, height: H, depth } = b;
  row.trim.box(x0, H - 0.02, -depth, w, 0.06, depth, hex(ROOF), 0, ['-y', '+z', '-z', '+x', '-x']);
  // the cap along the front, and short returns on the sides
  row.trim.box(x0 - 0.1, H, -0.35, w + 0.2, 0.9, 0.5, hex('#d6d5d1'), 0, ['-y'], 0.2);
  row.trim.box(x0 - 0.1, H, -depth, 0.3, 0.9, depth - 0.35, hex('#cfcdc9'), 0, ['-y']);
  row.trim.box(x0 + w - 0.2, H, -depth, 0.3, 0.9, depth - 0.35, hex('#cfcdc9'), 0, ['-y']);
  // plant: a stair head, water tanks, units
  const n = 2 + Math.floor(r() * 3);
  for (let i = 0; i < n; i++) {
    const px = x0 + 1.2 + r() * Math.max(0.5, w - 4);
    const pz = -2 - r() * (depth - 4);
    const k = r();
    if (k < 0.3) {
      row.trim.box(px, H + 0.9, pz, 3 + r() * 2, 2.6, 3, hex('#cbcac6'), 0, ['-y'], 0.1);
    } else if (k < 0.62) {
      const tank = new THREE.CylinderGeometry(0.9, 0.9, 1.7, 14);
      row.trim.add(tank, placement(px + 1, H + 1.75, pz), hex('#dfe3e6'));
      row.trim.add(new THREE.CylinderGeometry(0.2, 0.2, 0.8, 8), placement(px + 1, H + 0.9 + 0.4, pz), hex('#9aa0a6'));
      tank.dispose();
    } else if (k < 0.85) {
      for (let j = 0; j < 3; j++) row.trim.box(px + j * 1.1, H + 0.9, pz, 0.9, 0.7, 0.9, hex('#c4c8cc'), 0, ['-y'], 0.1);
    } else {
      // solar water heater rack
      for (let j = 0; j < 4; j++) row.trim.box(px + j * 0.6, H + 0.9, pz, 0.45, 0.6, 1.6, hex('#2a3c5a'), 0, ['-y'], 0.05);
    }
  }
  // a slim aerial
  if (r() > 0.55) row.trim.add(new THREE.CylinderGeometry(0.03, 0.05, 4.2, 5), placement(x0 + w * (0.2 + r() * 0.6), H + 3, -depth * 0.5), hex('#8a8f96'));
  void tint;
}

/** Flats over shops: window bays, balconies, enclosed balconies, air-conditioners, a band of accent colour. */
function flats(row: Row$, b: Block, floors: number, material: 'stucco' | 'tile' | 'brick') {
  const r = row.r;
  const { x0, w, depth } = b;
  const tint = hex(STUCCO[Math.floor(r() * STUCCO.length)]);
  const accent = hex(ACCENT[Math.floor(r() * ACCENT.length)]);
  const wallB = material === 'brick' ? row.brick : material === 'tile' ? row.tile : row.stucco;
  const tileM = material === 'brick' ? TILE.brick : material === 'tile' ? 1.28 : TILE.stucco;
  const groundH = 4.4;
  const fh = 3.1;
  const H = groundH + floors * fh;
  b.height = H;

  shopfronts(row, x0, w, material === 'brick' ? hex('#b27a62') : tint, accent, groundH, tileM);
  // a ledge over the shops
  row.trim.box(x0 - 0.05, groundH, 0, w + 0.1, 0.18, 0.5, hex(SLAB), 0, ['-y'], 0.25);

  const bayW0 = 3.3;
  const n = Math.max(2, Math.round(w / bayW0));
  const bayW = w / n;
  const pattern = r();
  const tintMat: V3 = material === 'brick' ? [1, 0.98, 0.96] : tint;
  // a vertical accent: one bay column (the stairs) in the accent colour, with slit windows
  const stairBay = r() > 0.45 ? Math.floor(r() * n) : -1;
  for (let f = 0; f < floors; f++) {
    const y0 = groundH + 0.18 + f * fh;
    const h = fh - 0.18;
    for (let i = 0; i < n; i++) {
      const bx = x0 + i * bayW;
      const isStair = i === stairBay;
      const useAccent = isStair;
      const wt: V3 = useAccent ? accent : tintMat;
      const kind = isStair ? 'slit' : pattern < 0.4 ? (i % 2 ? 'balcony' : 'window') : pattern < 0.7 ? (i % 3 === 1 ? 'enclosed' : 'window') : 'window';
      // the opening
      let ow = bayW * 0.56;
      let oh = 1.45;
      let oy = y0 + 0.95;
      let cell: number = r() > 0.5 ? CELL.window : CELL.windowSplit;
      if (kind === 'balcony') {
        ow = bayW * 0.7;
        oh = h - 0.55;
        oy = y0 + 0.1;
        cell = CELL.balconyDoor;
      } else if (kind === 'enclosed') {
        ow = bayW * 0.76;
        oh = h - 0.5;
        oy = y0 + 0.1;
        cell = CELL.balconyDoor;
      } else if (kind === 'slit') {
        ow = Math.min(0.9, bayW * 0.3);
        oh = h - 1.0;
        oy = y0 + 0.5;
        cell = CELL.slit;
      } else if (bayW > 3.6 && r() > 0.5) {
        ow = bayW * 0.7;
        cell = CELL.windowWide;
      }
      const ox = bx + (bayW - ow) / 2;
      // the wall round the opening
      row.front(wallB, bx, y0, bayW, oy - y0, wt, tileM);
      row.front(wallB, bx, oy + oh, bayW, y0 + h - oy - oh, wt, tileM);
      row.front(wallB, bx, oy, ox - bx, oh, wt, tileM);
      row.front(wallB, ox + ow, oy, bx + bayW - ox - ow, oh, wt, tileM);
      row.opening(row.atlas, ox, oy, ow, oh, cell, wt, tileM, 0.2, wallB, r() > 0.52);
      // the sill
      row.trim.box(ox - 0.08, oy - 0.07, 0, ow + 0.16, 0.07, 0.24, hex(TRIM), 0, ['-y']);
      if (kind === 'balcony') {
        row.trim.box(bx + 0.08, y0 - 0.14, 0, bayW - 0.16, 0.14, 1.25, hex(SLAB), 0, ['-y'], 0.3);
        // a glass-and-rail parapet
        row.atlas.rect([bx + 0.08, y0, 1.25], [1, 0, 0], [0, 1, 0], bayW - 0.16, 1.0, [0.95, 0.97, 0.97], 0, 0, 0, cellUV(CELL.curtain));
        row.trim.box(bx + 0.06, y0 + 1.0, 1.18, bayW - 0.12, 0.05, 0.1, hex('#cfd3d6'), 0);
        row.trim.box(bx + 0.06, y0, 0, 0.05, 1.0, 1.25, hex('#cdd1d4'), 0, ['-x', '+z']);
        row.trim.box(bx + bayW - 0.11, y0, 0, 0.05, 1.0, 1.25, hex('#cdd1d4'), 0, ['+x', '+z']);
      } else if (kind === 'enclosed') {
        // a glassed-in balcony: a box of green glass standing out of the wall
        row.trim.box(bx + 0.1, y0 - 0.14, 0, bayW - 0.2, 0.14, 1.1, hex(SLAB), 0, ['-y'], 0.3);
        row.trim.box(bx + 0.1, y0 + h - 0.35, 0, bayW - 0.2, 0.06, 1.1, hex(SLAB), 0);
        atlasQuad(row, bx + 0.1, y0, 1.1, bayW - 0.2, h - 0.35, CELL.enclosed, 1);
        row.atlas.rect([bx + 0.1, y0, 1.1], [0, 0, -1], [0, 1, 0], 1.1, h - 0.35, [0.5, 0.62, 0.58], 0, 0, 0, cellUV(CELL.enclosed));
        row.atlas.rect([bx + bayW - 0.1, y0, 0], [0, 0, 1], [0, 1, 0], 1.1, h - 0.35, [0.5, 0.62, 0.58], 0, 0, 0, cellUV(CELL.enclosed));
      } else if (kind === 'window' && r() > 0.78) {
        // an air-conditioning unit on a bracket below the window
        const ax = ox + (r() > 0.5 ? 0.1 : ow - 0.9);
        row.trim.box(ax, oy - 0.62, 0.0, 0.8, 0.5, 0.34, hex('#d3d7da'), 0, ['+z'], 0.15);
        atlasQuad(row, ax, oy - 0.62, 0.342, 0.8, 0.5, CELL.acUnit, 0.95);
        row.trim.box(ax + 0.1, oy - 0.7, 0.0, 0.05, 0.1, 0.25, hex('#6a6e74'), 0);
        row.trim.box(ax + 0.65, oy - 0.7, 0.0, 0.05, 0.1, 0.25, hex('#6a6e74'), 0);
      }
    }
    // the floor line
    if (pattern > 0.25) row.trim.box(x0 - 0.02, groundH + 0.18 + f * fh - 0.02, 0, w + 0.04, 0.05, 0.07, hex(TRIM), 0, ['-y']);
  }
  // an accent band under the roof
  row.trim.box(x0 - 0.04, H - 0.5, 0, w + 0.08, 0.5, 0.14, accent, 0, ['-y'], 0.2);
  roof(row, b, tintMat);
  // the side walls, plain, to the height they stand above a lower neighbour
  const side = material === 'brick' ? row.brick : row.stucco;
  const sideTint: V3 = material === 'brick' ? [1, 0.97, 0.94] : [tint[0] * 0.95, tint[1] * 0.95, tint[2] * 0.95];
  const sc: V3 = [sideTint[0] * 0.9, sideTint[1] * 0.9, sideTint[2] * 0.9];
  side.rect([x0, 0, 0], [0, 0, -1], [0, 1, 0], depth, H, sc, tileM, 0, 0);
  side.rect([x0 + w, 0, -depth], [0, 0, 1], [0, 1, 0], depth, H, sc, tileM, 0, 0);
}

/** A glass tower: curtain-wall panels floor by floor, a podium of shops, a crown. */
function tower(row: Row$, b: Block, floors: number) {
  const r = row.r;
  const { x0, w, depth } = b;
  const groundH = 5.2;
  const fh = 3.7;
  const H = groundH + floors * fh;
  b.height = H;
  const dark = r() > 0.5;
  const cell = dark ? CELL.curtainDark : CELL.curtain;
  const frame = hex(dark ? '#2b3036' : '#9aa4ab');
  const stone = hex('#c8c6c0');
  // the podium: a stone base with a tall glazed entrance and a canopy
  row.front(row.stucco, x0, 0, w, 0.5, hex('#7d8087'), 0);
  const entW = Math.min(w * 0.55, 9);
  const ex = x0 + (w - entW) / 2;
  row.front(row.stucco, x0, 0.5, ex - x0, groundH - 0.5, stone, TILE.stucco);
  row.front(row.stucco, ex + entW, 0.5, x0 + w - ex - entW, groundH - 0.5, stone, TILE.stucco);
  row.front(row.stucco, ex, groundH - 1.2, entW, 1.2, stone, TILE.stucco);
  atlasQuad(row, ex, 0.5, -0.25, entW, groundH - 1.7, CELL.shopGlass, 0.9);
  atlasQuad(row, ex + entW / 2 - 0.9, 0.5, -0.24, 1.8, groundH - 1.7, CELL.shopDoor, 0.9);
  row.litQuad(ex, 0.8, entW, groundH - 2.1, -0.245);
  row.trim.box(ex - 0.6, groundH - 1.35, 0, entW + 1.2, 0.18, 2.6, hex('#3c4148'), 0, ['-y'], 0.2);
  // the curtain wall
  const pw = 1.5;
  const n = Math.max(3, Math.round(w / pw));
  const cw = w / n;
  for (let f = 0; f < floors; f++) {
    const y = groundH + f * fh;
    for (let i = 0; i < n; i++) {
      const k = 0.92 + r() * 0.1;
      row.atlas.rect([x0 + i * cw, y, 0], [1, 0, 0], [0, 1, 0], cw, fh, [k, k, k], 0, 0, 0, cellUV(cell));
      if (r() > 0.78) row.litQuad(x0 + i * cw + 0.06, y + 0.15, cw - 0.12, fh * 0.7, 0.01);
    }
    // a slab edge each floor, and a thin cap
    row.trim.box(x0, y - 0.04, 0, w, 0.09, 0.1, frame, 0, ['-y']);
  }
  // vertical fins every few panels
  for (let i = 0; i <= n; i += 3) row.trim.box(x0 + i * cw - 0.04, groundH, 0, 0.08, floors * fh, 0.12, frame, 0, ['-z']);
  // the crown: a stepped top with a lit band
  row.trim.box(x0 + w * 0.12, H, -depth * 0.8, w * 0.76, 2.6, depth * 0.7, hex('#8b9298'), 0, ['-y'], 0.15);
  row.trim.box(x0 + w * 0.22, H + 2.6, -depth * 0.6, w * 0.56, 1.6, depth * 0.45, hex('#767e85'), 0, ['-y'], 0.15);
  row.trim.box(x0 + w * 0.42, H + 4.2, -depth * 0.4, 0.3, 6, 0.3, hex('#a8aeb4'), 0);
  roof(row, b, [1, 1, 1]);
  row.trim.rect([x0, H - 0.4, 0.02], [1, 0, 0], [0, 1, 0], w, 0.3, hex('#c8d4da'), 0);
  const sideC: V3 = hex(dark ? '#4a5560' : '#8fa0ab');
  const sc: V3 = [sideC[0] * 0.85, sideC[1] * 0.85, sideC[2] * 0.85];
  row.trim.rect([x0, 0, 0], [0, 0, -1], [0, 1, 0], depth, H, sc, 0);
  row.trim.rect([x0 + w, 0, -depth], [0, 0, 1], [0, 1, 0], depth, H, sc, 0);
}

/** A low commercial block: a long signboard, wide windows over it, a flat roof with a hoarding. */
function mall(row: Row$, b: Block, floors: number) {
  const r = row.r;
  const { x0, w, depth } = b;
  const tint = hex(STUCCO[Math.floor(r() * STUCCO.length)]);
  const groundH = 5;
  const fh = 3.8;
  const H = groundH + floors * fh;
  b.height = H;
  const accent = hex(ACCENT[Math.floor(r() * ACCENT.length)]);
  shopfronts(row, x0, w, tint, accent, groundH, TILE.stucco);
  row.trim.box(x0 - 0.05, groundH, 0, w + 0.1, 0.25, 0.7, hex('#cfd0d2'), 0, ['-y'], 0.3);
  for (let f = 0; f < floors; f++) {
    const y0 = groundH + 0.25 + f * fh;
    const h = fh - 0.25;
    // a band of wide windows with solid piers between
    const n = Math.max(2, Math.round(w / 4.6));
    const bw = w / n;
    for (let i = 0; i < n; i++) {
      const bx = x0 + i * bw;
      const ow = bw * 0.78;
      const ox = bx + (bw - ow) / 2;
      const oy = y0 + 0.8;
      const oh = h - 1.5;
      row.front(row.stucco, bx, y0, bw, oy - y0, tint, TILE.stucco);
      row.front(row.stucco, bx, oy + oh, bw, y0 + h - oy - oh, tint, TILE.stucco);
      row.front(row.stucco, bx, oy, ox - bx, oh, tint, TILE.stucco);
      row.front(row.stucco, ox + ow, oy, bx + bw - ox - ow, oh, tint, TILE.stucco);
      row.opening(row.atlas, ox, oy, ow, oh, CELL.windowWide, tint, TILE.stucco, 0.22, row.stucco, r() > 0.5);
    }
  }
  // a hoarding on the roof, lit
  const word = Math.floor(r() * SIGN_WORDS.length);
  const hw = Math.min(w * 0.6, 10);
  const hx = x0 + (w - hw) / 2;
  row.trim.box(hx - 0.1, H, -0.9, hw + 0.2, 2.6, 0.3, hex('#4b4f57'), 0, ['+z']);
  atlasQuad(row, hx, H + 0.1, -0.58, hw, 2.4, CELL.sign0 + word, 1);
  row.signLit.rect([hx, H + 0.1, -0.57], [1, 0, 0], [0, 1, 0], hw, 2.4, hex('#fff2d8', 0.9), 0, 0, 0, cellUV(CELL.sign0 + word));
  row.trim.box(x0 + w * 0.1, H - 0.02, -depth, w * 0.8, 0.06, depth, hex(ROOF), 0, ['-y', '+z', '-z', '+x', '-x']);
  roof(row, b, tint);
  row.stucco.rect([x0, 0, 0], [0, 0, -1], [0, 1, 0], depth, H, [tint[0] * 0.9, tint[1] * 0.9, tint[2] * 0.9], TILE.stucco, 0, 0);
  row.stucco.rect([x0 + w, 0, -depth], [0, 0, 1], [0, 1, 0], depth, H, [tint[0] * 0.9, tint[1] * 0.9, tint[2] * 0.9], TILE.stucco, 0, 0);
}

// ---------------------------------------------------------------------------------------------- the row

/**
 * Builds a row `spec.length` metres long (the widths of its buildings add up to it exactly). Heights are drawn between
 * `minHeight` and `maxHeight`; a tower needs the room for it.
 */
export function buildRow(spec: RowSpec): Row {
  return cached(`row-${spec.length}-${spec.seed}-${spec.maxHeight ?? 0}-${spec.style ?? 'street'}`, () => {
    const row = new Row$(spec.seed);
    const r = row.r;
    const maxH = spec.maxHeight ?? 30;
    const minH = spec.minHeight ?? 13;
    const widths: number[] = [];
    let left = spec.length;
    while (left > 0.1) {
      const w = left < 22 ? left : 10 + r() * 11;
      if (left - w < 8 && left - w > 0.1) widths.push(left);
      else widths.push(w);
      left -= widths[widths.length - 1];
    }
    let x = 0;
    let tallest = 0;
    for (const w of widths) {
      const depth = spec.style === 'lot' ? 16 : 11 + r() * 5;
      const b: Block = { x0: x, w, height: 0, depth };
      const roll = r();
      const targetH = minH + r() * (maxH - minH);
      if (roll < 0.2 && w >= 11 && maxH >= 26) {
        tower(row, b, Math.max(5, Math.round((Math.min(maxH, targetH + 8) - 5.2) / 3.7)));
      } else if (roll < 0.36) {
        mall(row, b, 1 + Math.floor(r() * 2));
      } else {
        const material = roll < 0.55 ? 'brick' : roll < 0.8 ? 'tile' : 'stucco';
        flats(row, b, Math.max(3, Math.round((targetH - 4.4) / 3.1)), material);
      }
      tallest = Math.max(tallest, b.height);
      x += w;
    }
    const out: Row = {
      stucco: row.stucco.build(),
      tile: row.tile.build(),
      brick: row.brick.build(),
      trim: row.trim.build(),
      atlas: row.atlas.build(),
      lit: row.lit.build(),
      signLit: row.signLit.build(),
      length: spec.length,
      height: tallest + 10,
    };
    return out;
  });
}
