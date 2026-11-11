/**
 * The scenery's textures, all painted on canvases (see kit.ts): tileable asphalt, paving, walls and grass; the leaf
 * cluster and the bark; the window and shop-sign atlas; soft shadows; and the painting helpers that wear a road
 * (paint, cracks, patches, oil, tyre tracks, manholes, drains, zebra bars, arrows).
 */
import * as THREE from 'three';
import { cached, clamp01, makeCanvas, rng, shade, smooth, tileNoise, toTexture, type Canvas2D } from './kit';

// ------------------------------------------------------------------------------------------------ the ground

/** The asphalt's colour before its detail (a mid-dark warm grey, as wet-dry tar looks in an overcast light). */
export const ASPHALT = '#4a4c52';
export const PAINT = '#f1efe8';
export const YELLOW = '#e5bf3f';

/** A tile of fine asphalt (aggregate, tar mottling), a linear multiplier around 0.5: x2 is 1. One tile is TILE.asphalt metres. */
export const TILE = { asphalt: 2.4, paving: 1.2, grass: 1.6, brick: 1.0, stucco: 2.0, concrete: 2.0 };

export function asphaltDetail(): THREE.CanvasTexture {
  return cached('asphaltDetail', () => {
    const S = 512;
    const { canvas, ctx } = makeCanvas(S, S);
    const mottle = tileNoise(S, 11, 6, 4, 0.58);
    const grain = tileNoise(S, 12, 3, 128, 0.5);
    const img = ctx.createImageData(S, S);
    for (let i = 0; i < S * S; i++) {
      const v = clamp01(0.5 + (mottle[i] - 0.5) * 0.36 + (grain[i] - 0.5) * 0.3);
      const g = Math.round(v * 255);
      img.data[i * 4] = g;
      img.data[i * 4 + 1] = g;
      img.data[i * 4 + 2] = g;
      img.data[i * 4 + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
    // the stones: light and dark chips, wrapped so the tile stays seamless
    const r = rng(77);
    for (let i = 0; i < 5200; i++) {
      const x = r() * S;
      const y = r() * S;
      const s = 0.8 + r() * 1.9;
      const light = r() > 0.46;
      ctx.fillStyle = light ? `rgba(255,255,255,${0.1 + r() * 0.22})` : `rgba(0,0,0,${0.12 + r() * 0.24})`;
      for (const [ox, oy] of [[0, 0], [S, 0], [-S, 0], [0, S], [0, -S]]) {
        if ((ox !== 0 && x > 4 && x < S - 4) || (oy !== 0 && y > 4 && y < S - 4)) continue;
        ctx.beginPath();
        ctx.ellipse(x + ox, y + oy, s, s * (0.6 + r() * 0.5), r() * 3, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    return toTexture(canvas, { repeat: true, srgb: false, aniso: 8 });
  });
}

/** Concrete paving slabs, 0.6 m, two by two to a tile: a pale grey, each slab its own tone, joints, wear and the odd stain. */
export function pavingTexture(): THREE.CanvasTexture {
  return cached('paving', () => {
    const S = 512;
    const { canvas, ctx } = makeCanvas(S, S);
    const noise = tileNoise(S, 31, 6, 4, 0.55);
    const fine = tileNoise(S, 32, 3, 128, 0.5);
    const r = rng(8);
    const slab = S / 2;
    const tones = [0.0, 0.025, -0.02, 0.04];
    const img = ctx.createImageData(S, S);
    for (let y = 0; y < S; y++) {
      for (let x = 0; x < S; x++) {
        const i = y * S + x;
        const sx = Math.floor(x / slab);
        const sy = Math.floor(y / slab);
        const t = tones[(sx + sy * 2) % tones.length];
        const v = clamp01(0.72 + t + (noise[i] - 0.5) * 0.14 + (fine[i] - 0.5) * 0.1);
        img.data[i * 4] = Math.round(v * 250);
        img.data[i * 4 + 1] = Math.round(v * 252);
        img.data[i * 4 + 2] = Math.round(v * 255);
        img.data[i * 4 + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
    // chips and pits
    for (let i = 0; i < 1400; i++) {
      ctx.fillStyle = r() > 0.5 ? 'rgba(255,255,255,0.16)' : 'rgba(40,44,52,0.18)';
      ctx.fillRect(r() * S, r() * S, 1 + r() * 2, 1 + r() * 2);
    }
    // joints: a dark core with a light lip
    for (const p of [0, slab]) {
      ctx.fillStyle = 'rgba(48,52,60,0.62)';
      ctx.fillRect(p - 1.5, 0, 3, S);
      ctx.fillRect(0, p - 1.5, S, 3);
      ctx.fillStyle = 'rgba(255,255,255,0.22)';
      ctx.fillRect(p + 1.5, 0, 1.5, S);
      ctx.fillRect(0, p + 1.5, S, 1.5);
    }
    ctx.fillStyle = 'rgba(48,52,60,0.62)';
    ctx.fillRect(S - 2, 0, 2, S);
    ctx.fillRect(0, S - 2, S, 2);
    // a stain or two, and the odd mended slab
    for (let i = 0; i < 4; i++) {
      const cx = r() * S;
      const cy = r() * S;
      const g = ctx.createRadialGradient(cx, cy, 2, cx, cy, 30 + r() * 30);
      g.addColorStop(0, 'rgba(70,64,56,0.20)');
      g.addColorStop(1, 'rgba(70,64,56,0)');
      ctx.fillStyle = g;
      ctx.fillRect(cx - 70, cy - 70, 140, 140);
    }
    return toTexture(canvas, { repeat: true, aniso: 8 });
  });
}

/** A yellow tactile strip (the blind path of Chinese footways): rows of bars across it, 0.6 m to a repeat along it. */
export function tactileTexture(): THREE.CanvasTexture {
  return cached('tactile', () => {
    const { canvas, ctx } = makeCanvas(128, 256);
    ctx.fillStyle = '#d9b43a';
    ctx.fillRect(0, 0, 128, 256);
    for (let row = 0; row < 8; row++) {
      for (let c = 0; c < 4; c++) {
        const x = 10 + c * 28;
        const y = 6 + row * 31;
        ctx.fillStyle = 'rgba(0,0,0,0.30)';
        ctx.fillRect(x + 2, y + 2, 20, 22);
        ctx.fillStyle = '#ecc84a';
        ctx.fillRect(x, y, 20, 22);
        ctx.fillStyle = 'rgba(255,255,255,0.35)';
        ctx.fillRect(x, y, 20, 4);
      }
    }
    ctx.fillStyle = 'rgba(90,72,10,0.5)';
    ctx.fillRect(0, 0, 4, 256);
    ctx.fillRect(124, 0, 4, 256);
    return toTexture(canvas, { repeat: true });
  });
}

export function grassTexture(): THREE.CanvasTexture {
  return cached('grass', () => {
    const S = 256;
    const { canvas, ctx } = makeCanvas(S, S);
    const n = tileNoise(S, 41, 5, 4, 0.55);
    const f = tileNoise(S, 42, 3, 64, 0.5);
    const img = ctx.createImageData(S, S);
    for (let i = 0; i < S * S; i++) {
      const v = n[i] * 0.6 + f[i] * 0.4;
      img.data[i * 4] = Math.round(58 + v * 46);
      img.data[i * 4 + 1] = Math.round(96 + v * 62);
      img.data[i * 4 + 2] = Math.round(48 + v * 28);
      img.data[i * 4 + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
    const r = rng(43);
    for (let i = 0; i < 2600; i++) {
      const x = r() * S;
      const y = r() * S;
      ctx.strokeStyle = r() > 0.5 ? 'rgba(160,200,110,0.30)' : 'rgba(24,52,22,0.32)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x + (r() - 0.5) * 4, y - 3 - r() * 4);
      ctx.stroke();
    }
    return toTexture(canvas, { repeat: true });
  });
}

// ------------------------------------------------------------------------------------------------ road wear

/** Where the tyres run: a darker, smoother pair of bands in each lane, drawn as soft strokes along x. */
export function paintTyreTracks(ctx: CanvasRenderingContext2D, x0: number, x1: number, laneY: number, laneW: number, ppm: number, seed = 1) {
  const r = rng(seed);
  for (const side of [-1, 1]) {
    const y = laneY + side * laneW * 0.24;
    for (let k = 0; k < 6; k++) {
      ctx.strokeStyle = `rgba(14,15,18,${0.03 + r() * 0.035})`;
      ctx.lineWidth = (0.22 + r() * 0.2) * ppm;
      ctx.beginPath();
      ctx.moveTo(x0, y + (r() - 0.5) * 0.25 * ppm);
      ctx.lineTo(x1, y + (r() - 0.5) * 0.25 * ppm);
      ctx.stroke();
    }
  }
  // the lane's middle is paler (oil-free, dried), the edges dirtier
  const g = ctx.createLinearGradient(0, laneY - laneW / 2, 0, laneY + laneW / 2);
  g.addColorStop(0, 'rgba(10,11,13,0.06)');
  g.addColorStop(0.5, 'rgba(255,255,255,0.012)');
  g.addColorStop(1, 'rgba(10,11,13,0.06)');
  ctx.fillStyle = g;
  ctx.fillRect(x0, laneY - laneW / 2, x1 - x0, laneW);
}

/** Hairline cracks that wander and branch, and a few longer tar-filled seams. */
export function paintCracks(ctx: CanvasRenderingContext2D, w: number, h: number, count: number, ppm: number, seed = 2) {
  const r = rng(seed);
  for (let i = 0; i < count; i++) {
    let x = r() * w;
    let y = r() * h;
    let a = r() * Math.PI * 2;
    const steps = 6 + Math.floor(r() * 16);
    const seam = r() > 0.8;
    ctx.strokeStyle = seam ? 'rgba(8,8,10,0.55)' : 'rgba(10,10,12,0.38)';
    ctx.lineWidth = Math.max(0.8, (seam ? 0.035 : 0.014) * ppm);
    ctx.beginPath();
    ctx.moveTo(x, y);
    for (let s = 0; s < steps; s++) {
      a += (r() - 0.5) * 0.9;
      const l = (0.1 + r() * 0.3) * ppm;
      x += Math.cos(a) * l;
      y += Math.sin(a) * l;
      ctx.lineTo(x, y);
      if (r() > 0.88) {
        // a branch
        const bx = x + Math.cos(a + 1.2) * l * 1.6;
        const by = y + Math.sin(a + 1.2) * l * 1.6;
        ctx.moveTo(x, y);
        ctx.lineTo(bx, by);
        ctx.moveTo(x, y);
      }
    }
    ctx.stroke();
  }
}

/** Mended patches: slightly darker, squared-off, with a light seam of tar round them. */
export function paintPatches(ctx: CanvasRenderingContext2D, w: number, h: number, count: number, ppm: number, seed = 3) {
  const r = rng(seed);
  for (let i = 0; i < count; i++) {
    const pw = (0.7 + r() * 2.4) * ppm;
    const ph = (0.5 + r() * 1.6) * ppm;
    const x = r() * (w - pw);
    const y = r() * (h - ph);
    ctx.fillStyle = `rgba(${r() > 0.35 ? '16,17,20' : '96,98,104'},${0.16 + r() * 0.12})`;
    ctx.fillRect(x, y, pw, ph);
    ctx.strokeStyle = 'rgba(6,6,8,0.4)';
    ctx.lineWidth = Math.max(1, 0.03 * ppm);
    ctx.strokeRect(x, y, pw, ph);
  }
}

/** Oil drips: dark, soft, a little iridescent at the edge. */
export function paintOil(ctx: CanvasRenderingContext2D, x: number, y: number, radius: number, strength = 0.4) {
  const g = ctx.createRadialGradient(x, y, radius * 0.1, x, y, radius);
  g.addColorStop(0, `rgba(6,7,10,${strength})`);
  g.addColorStop(0.7, `rgba(10,12,16,${strength * 0.45})`);
  g.addColorStop(1, 'rgba(10,12,16,0)');
  ctx.fillStyle = g;
  ctx.beginPath();
  ctx.ellipse(x, y, radius, radius * 0.7, 0.4, 0, Math.PI * 2);
  ctx.fill();
}

export function paintManhole(ctx: CanvasRenderingContext2D, x: number, y: number, radius: number, ppm: number) {
  ctx.save();
  ctx.fillStyle = 'rgba(20,21,24,0.85)';
  ctx.beginPath();
  ctx.arc(x, y, radius * 1.08, 0, Math.PI * 2);
  ctx.fill();
  const g = ctx.createRadialGradient(x - radius * 0.3, y - radius * 0.3, 1, x, y, radius);
  g.addColorStop(0, '#5b5e66');
  g.addColorStop(1, '#2b2d32');
  ctx.fillStyle = g;
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, Math.PI * 2);
  ctx.fill();
  // the lid's grid of ribs
  ctx.strokeStyle = 'rgba(160,164,172,0.30)';
  ctx.lineWidth = Math.max(1, 0.018 * ppm);
  for (let k = -2; k <= 2; k++) {
    ctx.beginPath();
    ctx.moveTo(x + k * radius * 0.34, y - radius * 0.9);
    ctx.lineTo(x + k * radius * 0.34, y + radius * 0.9);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x - radius * 0.9, y + k * radius * 0.34);
    ctx.lineTo(x + radius * 0.9, y + k * radius * 0.34);
    ctx.stroke();
  }
  ctx.strokeStyle = 'rgba(200,204,212,0.28)';
  ctx.lineWidth = Math.max(1, 0.025 * ppm);
  ctx.beginPath();
  ctx.arc(x, y, radius * 0.96, 0, Math.PI * 2);
  ctx.stroke();
  ctx.restore();
}

/** A rectangular storm drain along a kerb: a dark slot with cross bars. */
export function paintDrain(ctx: CanvasRenderingContext2D, x: number, y: number, len: number, wid: number, ppm: number) {
  ctx.fillStyle = 'rgba(8,9,11,0.92)';
  ctx.fillRect(x, y, len, wid);
  ctx.fillStyle = 'rgba(96,100,108,0.9)';
  const bars = Math.max(4, Math.round(len / (0.045 * ppm)));
  for (let i = 0; i < bars; i++) ctx.fillRect(x + (i + 0.3) * (len / bars), y + wid * 0.06, Math.max(1, (len / bars) * 0.42), wid * 0.88);
  ctx.strokeStyle = 'rgba(180,184,192,0.35)';
  ctx.lineWidth = Math.max(1, 0.015 * ppm);
  ctx.strokeRect(x, y, len, wid);
}

/**
 * Paint worn by traffic: draw the shape in white, then erode it with a speckle of the road's own colour so the stripe
 * is chipped and thin in places, and scuffed where tyres cross it.
 */
export function wearPaint(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, ppm: number, seed: number, wear = 0.35) {
  const r = rng(seed);
  const n = Math.round(w * h * 0.0018 * wear * 10);
  ctx.save();
  ctx.globalCompositeOperation = 'source-atop';
  for (let i = 0; i < n; i++) {
    ctx.fillStyle = `rgba(74,76,82,${0.25 + r() * 0.5})`;
    const s = 0.6 + r() * 2.2;
    ctx.fillRect(x + r() * w, y + r() * h, s * (1 + r() * 2), s);
  }
  ctx.restore();
}

/** The zebra bars across a street as chalky stripes with worn edges. */
export function paintZebra(ctx: CanvasRenderingContext2D, x0: number, y0: number, length: number, bandH: number, count: number, step: number, seed = 5) {
  const r = rng(seed);
  for (let i = 0; i < count; i++) {
    const y = y0 + i * step;
    ctx.fillStyle = `rgba(241,239,232,${0.9 + r() * 0.08})`;
    ctx.fillRect(x0, y, length, bandH);
    // tyre-polished middle of each bar and ragged ends
    const g = ctx.createLinearGradient(x0, 0, x0 + length, 0);
    g.addColorStop(0, 'rgba(74,76,82,0.45)');
    g.addColorStop(0.12, 'rgba(74,76,82,0)');
    g.addColorStop(0.88, 'rgba(74,76,82,0)');
    g.addColorStop(1, 'rgba(74,76,82,0.45)');
    ctx.fillStyle = g;
    ctx.fillRect(x0, y, length, bandH);
    wearPaint(ctx, x0, y, length, bandH, 1, seed + i, 0.5);
  }
}

/** A straight-ahead arrow (the way the lane goes), pointing +x, centred on (x, y), `len` long. */
export function paintArrow(ctx: CanvasRenderingContext2D, x: number, y: number, len: number, ppm: number, seed = 9) {
  const hw = 0.08 * ppm;
  const head = len * 0.36;
  const hh = 0.34 * ppm;
  ctx.fillStyle = PAINT;
  ctx.beginPath();
  ctx.moveTo(x - len / 2, y - hw);
  ctx.lineTo(x + len / 2 - head, y - hw);
  ctx.lineTo(x + len / 2 - head, y - hh);
  ctx.lineTo(x + len / 2, y);
  ctx.lineTo(x + len / 2 - head, y + hh);
  ctx.lineTo(x + len / 2 - head, y + hw);
  ctx.lineTo(x - len / 2, y + hw);
  ctx.closePath();
  ctx.fill();
  wearPaint(ctx, x - len / 2, y - hh, len, hh * 2, ppm, seed, 0.6);
}

/**
 * A strip of worn road paint of `w` x `h` metres (a lane dash, a zebra bar, a stop line), transparent where the paint has
 * gone: chipped along its edges, thin where wheels pass. 160 pixels to the metre along its length.
 */
export function paintStripTexture(color: string, w: number, h: number, seed: number, wear = 0.5): THREE.CanvasTexture {
  return cached(`strip-${color}-${w}-${h}-${seed}-${wear}`, () => {
    const ppm = Math.min(160, 1024 / w);
    const W = Math.round(w * ppm);
    const H = Math.max(8, Math.round(h * Math.min(ppm, 260)));
    const { canvas, ctx } = makeCanvas(W, H);
    const r = rng(seed);
    ctx.fillStyle = color;
    ctx.fillRect(0, 0, W, H);
    ctx.globalCompositeOperation = 'destination-out';
    // chips: small and many, a few big scuffs where the tyres crossed
    const n = Math.round(W * H * 0.012 * wear);
    for (let i = 0; i < n; i++) {
      ctx.fillStyle = `rgba(0,0,0,${0.35 + r() * 0.65})`;
      const s = 0.7 + r() * 2.4;
      ctx.fillRect(r() * W, r() * H, s * (1 + r() * 3), s);
    }
    for (let i = 0; i < 3 + Math.round(wear * 6); i++) {
      const g = ctx.createRadialGradient(r() * W, r() * H, 1, r() * W, r() * H, H * (0.5 + r() * 1.2));
      g.addColorStop(0, `rgba(0,0,0,${0.35 * wear + 0.1})`);
      g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, H);
    }
    // a ragged edge
    for (let i = 0; i < W / 3; i++) {
      ctx.fillStyle = 'rgba(0,0,0,0.85)';
      ctx.fillRect(r() * W, r() < 0.5 ? 0 : H - 2, 2 + r() * 5, 1 + r() * 1.5);
    }
    ctx.globalCompositeOperation = 'source-over';
    return toTexture(canvas, { repeat: true });
  });
}

/**
 * One repeat of a solid edge line of `period` x `width` metres, worn the way a motorway's is: the paint thinned in long stretches
 * (a slow noise along it), chipped, eroded in a few patches, scuffed by tyres, and crossed by tar cracks. A perfectly even line looks
 * as if it stood still under a moving car; this one has marks to show the road streaming past. Seamless along its length (a mark
 * that crosses an end is drawn at both ends), so the rolling scenes scroll it by shifting the texture.
 */
export function edgeLineTexture(color: string, period: number, width: number, seed: number): THREE.CanvasTexture {
  return cached(`edge-${color}-${period}-${width}-${seed}`, () => {
    const ppm = Math.min(100, 2048 / period);
    const W = Math.round(period * ppm);
    const H = Math.max(16, Math.round(width * 120));
    const { canvas, ctx } = makeCanvas(W, H);
    const r = rng(seed);
    const wrap = (draw: (dx: number) => void) => {
      draw(0);
      draw(W);
      draw(-W);
    };
    ctx.fillStyle = color;
    ctx.fillRect(0, 0, W, H);

    // thin paint: two octaves of noise along the line, each on a lattice that wraps
    const cellsA = Math.max(6, Math.round(period / 1.8));
    const cellsB = cellsA * 3;
    const latA = Array.from({ length: cellsA }, () => r());
    const latB = Array.from({ length: cellsB }, () => r());
    const lattice = (lat: number[], x: number) => {
      const u = (x / W) * lat.length;
      const i = Math.floor(u);
      const f = u - i;
      const s = f * f * (3 - 2 * f);
      return lat[i % lat.length] * (1 - s) + lat[(i + 1) % lat.length] * s;
    };
    ctx.globalCompositeOperation = 'destination-out';
    for (let x = 0; x < W; x += 2) {
      const n = lattice(latA, x) * 0.72 + lattice(latB, x) * 0.28;
      const thin = clamp01((n - 0.46) * 1.7);
      if (thin > 0) {
        ctx.fillStyle = `rgba(0,0,0,${thin * 0.62})`;
        ctx.fillRect(x, 0, 2, H);
      }
    }
    // chips everywhere, and a few stretches eroded to speckle where the tyres ride the line
    const chips = Math.round(W * H * 0.0042);
    for (let i = 0; i < chips; i++) {
      const s = 0.8 + r() * 2.2;
      const x = r() * W;
      const y = r() * H;
      const a = 0.4 + r() * 0.6;
      const w = s * (1 + r() * 3.5);
      wrap((dx) => {
        ctx.fillStyle = `rgba(0,0,0,${a})`;
        ctx.fillRect(x + dx, y, w, s);
      });
    }
    for (let k = 0; k < Math.round(period / 4.5); k++) {
      const x0 = r() * W;
      const len = (0.5 + r() * 1.7) * ppm;
      const y0 = r() * H * 0.4;
      const hh = H * (0.5 + r() * 0.5);
      for (let i = 0; i < len * hh * 0.28; i++) {
        const x = x0 + r() * len;
        const y = y0 + r() * hh;
        const s = 0.8 + r() * 2;
        const a = 0.35 + r() * 0.65;
        wrap((dx) => {
          ctx.fillStyle = `rgba(0,0,0,${a})`;
          ctx.fillRect(x + dx, y, s * (1 + r() * 2), s);
        });
      }
    }
    // a ragged edge, top and bottom
    for (let i = 0; i < W / 2.5; i++) {
      const x = r() * W;
      const top = r() < 0.5;
      const w = 2 + r() * 6;
      const h = 1 + r() * 1.8;
      wrap((dx) => {
        ctx.fillStyle = 'rgba(0,0,0,0.85)';
        ctx.fillRect(x + dx, top ? 0 : H - h, w, h);
      });
    }

    // what lies on the paint: tyre scuffs and tar cracks (drawn only where paint is left)
    ctx.globalCompositeOperation = 'source-atop';
    for (let k = 0; k < Math.round(period / 5); k++) {
      const x = r() * W;
      const y = H * (0.25 + 0.5 * r());
      const rx = (0.35 + r() * 1.3) * ppm;
      const ry = H * (0.28 + 0.3 * r());
      const a = 0.16 + r() * 0.22;
      wrap((dx) => {
        ctx.fillStyle = `rgba(34,34,38,${a})`;
        ctx.beginPath();
        ctx.ellipse(x + dx, y, rx, ry, 0, 0, Math.PI * 2);
        ctx.fill();
      });
    }
    ctx.lineCap = 'round';
    for (let k = 0; k < Math.round(period / 6); k++) {
      const x = r() * W;
      const slant = (r() - 0.5) * H * 1.6;
      wrap((dx) => {
        ctx.strokeStyle = `rgba(22,22,26,${0.7 + r() * 0.25})`;
        ctx.lineWidth = 1.4 + r() * 1.6;
        ctx.beginPath();
        ctx.moveTo(x + dx, -2);
        ctx.lineTo(x + dx + slant * 0.4 + (r() - 0.5) * 4, H * 0.35);
        ctx.lineTo(x + dx + slant * 0.75 + (r() - 0.5) * 4, H * 0.7);
        ctx.lineTo(x + dx + slant, H + 2);
        ctx.stroke();
      });
    }
    ctx.globalCompositeOperation = 'source-over';
    return toTexture(canvas, { repeat: true });
  });
}

// ------------------------------------------------------------------------------------------------ walls

function wallBase(S: number, seed: number, base: [number, number, number], mottle: number): Canvas2D & { noise: Float32Array } {
  const c = makeCanvas(S, S);
  const n = tileNoise(S, seed, 6, 4, 0.55);
  const f = tileNoise(S, seed + 1, 3, 96, 0.5);
  const img = c.ctx.createImageData(S, S);
  for (let i = 0; i < S * S; i++) {
    const v = 1 + (n[i] - 0.5) * mottle + (f[i] - 0.5) * mottle * 0.7;
    img.data[i * 4] = Math.round(clamp01(base[0] * v) * 255);
    img.data[i * 4 + 1] = Math.round(clamp01(base[1] * v) * 255);
    img.data[i * 4 + 2] = Math.round(clamp01(base[2] * v) * 255);
    img.data[i * 4 + 3] = 255;
  }
  c.ctx.putImageData(img, 0, 0);
  return { ...c, noise: n };
}

/** Rendered wall (light, a hair of grime and vertical streaks); the buildings tint it per building in their vertex colours. */
export function stuccoTexture(): THREE.CanvasTexture {
  return cached('stucco', () => {
    const S = 256;
    const { canvas, ctx } = wallBase(S, 51, [0.93, 0.92, 0.9], 0.2);
    const r = rng(52);
    for (let i = 0; i < 90; i++) {
      const x = r() * S;
      const g = ctx.createLinearGradient(0, 0, 0, S);
      g.addColorStop(0, 'rgba(60,56,50,0)');
      g.addColorStop(0.4 + r() * 0.3, `rgba(60,56,50,${0.05 + r() * 0.06})`);
      g.addColorStop(1, 'rgba(60,56,50,0)');
      ctx.fillStyle = g;
      ctx.fillRect(x, 0, 1 + r() * 3, S);
    }
    return toTexture(canvas, { repeat: true });
  });
}

/** Small ceramic tile cladding, 5 cm squares with grout, the common finish of Chinese apartment blocks. */
export function tileTexture(): THREE.CanvasTexture {
  return cached('tiles', () => {
    const S = 256;
    const { canvas, ctx } = wallBase(S, 61, [0.92, 0.91, 0.89], 0.14);
    const r = rng(62);
    const n = 16;
    const cell = S / n;
    for (let y = 0; y < n; y++) {
      for (let x = 0; x < n; x++) {
        ctx.fillStyle = `rgba(${r() > 0.5 ? '255,255,255' : '40,36,30'},${r() * 0.07})`;
        ctx.fillRect(x * cell, y * cell, cell, cell);
      }
    }
    ctx.strokeStyle = 'rgba(70,66,60,0.38)';
    ctx.lineWidth = 1.2;
    for (let i = 0; i <= n; i++) {
      ctx.beginPath();
      ctx.moveTo(i * cell, 0);
      ctx.lineTo(i * cell, S);
      ctx.moveTo(0, i * cell);
      ctx.lineTo(S, i * cell);
      ctx.stroke();
    }
    ctx.strokeStyle = 'rgba(255,255,255,0.18)';
    for (let i = 0; i <= n; i++) {
      ctx.beginPath();
      ctx.moveTo(i * cell + 1.3, 0);
      ctx.lineTo(i * cell + 1.3, S);
      ctx.stroke();
    }
    return toTexture(canvas, { repeat: true });
  });
}

export function brickTexture(): THREE.CanvasTexture {
  return cached('brick', () => {
    const S = 256;
    const { canvas, ctx } = makeCanvas(S, S);
    ctx.fillStyle = '#b9b2a6';
    ctx.fillRect(0, 0, S, S);
    const r = rng(71);
    const rows = 16;
    const rh = S / rows;
    const bw = S / 4;
    for (let y = 0; y < rows; y++) {
      const off = (y % 2) * (bw / 2);
      for (let x = -1; x < 5; x++) {
        const hue = 12 + r() * 10;
        const l = 38 + r() * 14;
        ctx.fillStyle = `hsl(${hue},${40 + r() * 14}%,${l}%)`;
        ctx.fillRect(x * bw + off + 1.5, y * rh + 1.5, bw - 3, rh - 3);
        ctx.fillStyle = `rgba(255,255,255,${0.04 + r() * 0.06})`;
        ctx.fillRect(x * bw + off + 1.5, y * rh + 1.5, bw - 3, 2);
        ctx.fillStyle = `rgba(0,0,0,${0.06 + r() * 0.08})`;
        ctx.fillRect(x * bw + off + 1.5, y * rh + rh - 3.5, bw - 3, 2);
      }
    }
    return toTexture(canvas, { repeat: true });
  });
}

export function concreteTexture(): THREE.CanvasTexture {
  return cached('concrete', () => {
    const S = 256;
    const { canvas, ctx } = wallBase(S, 81, [0.78, 0.79, 0.8], 0.22);
    ctx.strokeStyle = 'rgba(50,52,58,0.35)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(0, S / 2);
    ctx.lineTo(S, S / 2);
    ctx.moveTo(S / 2, 0);
    ctx.lineTo(S / 2, S);
    ctx.stroke();
    const r = rng(82);
    for (let i = 0; i < 70; i++) {
      ctx.fillStyle = `rgba(30,32,38,${r() * 0.06})`;
      ctx.fillRect(r() * S, r() * S * 0.5, 1 + r() * 2, 30 + r() * 120);
    }
    return toTexture(canvas, { repeat: true });
  });
}

// ------------------------------------------------------------------------------------------------ the window atlas

/** The atlas has COLS x ROWS cells; CELL names what is in them. A quad maps a whole cell. */
export const ATLAS = { cols: 8, rows: 4, cell: 128 };
export const CELL = {
  window: 0,
  windowSplit: 1,
  balconyDoor: 2,
  enclosed: 3,
  curtain: 4,
  shopGlass: 5,
  shopDoor: 6,
  shutter: 7,
  acUnit: 8,
  curtainDark: 9,
  windowWide: 10,
  slit: 11,
  sign0: 16,
} as const;

export const SIGN_WORDS = [
  ['茶饮', '#d6453a', '#fff3d6'],
  ['药房', '#1f9d62', '#ffffff'],
  ['超市', '#e8a21a', '#3a2a08'],
  ['面馆', '#b8322a', '#ffe9b8'],
  ['便利店', '#1f6fb8', '#ffffff'],
  ['理发', '#2c2f38', '#f2d27a'],
  ['手机', '#7a3fb6', '#ffffff'],
  ['眼镜', '#0f7f8c', '#ffffff'],
  ['烧烤', '#2a2118', '#f08a1c'],
  ['水果', '#6aa11b', '#fff7d9'],
  ['银行', '#c1272d', '#f6d36b'],
  ['餐厅', '#5a3a28', '#f5e1c0'],
  ['书店', '#2f4f7f', '#f2ecd5'],
  ['花店', '#d46a9a', '#ffffff'],
  ['咖啡', '#3b2a22', '#e8cfa5'],
  ['酒店', '#243b55', '#e9d28a'],
] as const;

function cellOrigin(i: number) {
  const { cols, cell } = ATLAS;
  return { x: (i % cols) * cell, y: Math.floor(i / cols) * cell };
}

function glassGradient(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, a: string, b: string) {
  const g = ctx.createLinearGradient(x, y, x + w * 0.4, y + h);
  g.addColorStop(0, a);
  g.addColorStop(1, b);
  ctx.fillStyle = g;
  ctx.fillRect(x, y, w, h);
  // a bright diagonal streak of sky
  ctx.save();
  ctx.beginPath();
  ctx.rect(x, y, w, h);
  ctx.clip();
  ctx.fillStyle = 'rgba(255,255,255,0.20)';
  ctx.beginPath();
  ctx.moveTo(x + w * 0.1, y + h);
  ctx.lineTo(x + w * 0.38, y + h);
  ctx.lineTo(x + w * 0.9, y);
  ctx.lineTo(x + w * 0.62, y);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

/**
 * The window atlas: residential windows, balcony doors, enclosed balconies, curtain-wall panels, shopfronts, a
 * shutter, an air-conditioner and sixteen shop signs. Frames are painted into the cells, so a quad carries its own
 * frame, glass and reflection; the building adds the depth (reveals) round it.
 */
export function windowAtlas(): THREE.CanvasTexture {
  return cached('windowAtlas', () => {
    const { cols, rows, cell } = ATLAS;
    const { canvas, ctx } = makeCanvas(cols * cell, rows * cell);
    const r = rng(91);
    const S = cell;
    const frame = (o: { x: number; y: number }, col: string, t = 7) => {
      ctx.fillStyle = col;
      ctx.fillRect(o.x, o.y, S, t);
      ctx.fillRect(o.x, o.y + S - t, S, t);
      ctx.fillRect(o.x, o.y, t, S);
      ctx.fillRect(o.x + S - t, o.y, t, S);
    };
    const cellFill = (i: number, col: string) => {
      const o = cellOrigin(i);
      ctx.fillStyle = col;
      ctx.fillRect(o.x, o.y, S, S);
      return o;
    };

    // 0 plain window: pale-blue reflective glass, light-grey aluminium frame, one fixed pane over a sliding one
    {
      const o = cellFill(CELL.window, '#e9ecef');
      glassGradient(ctx, o.x + 7, o.y + 7, S - 14, S - 14, '#9fb6c8', '#4e6478');
      ctx.fillStyle = '#dfe3e7';
      ctx.fillRect(o.x + S / 2 - 3, o.y + 7, 6, S - 14);
      ctx.fillStyle = 'rgba(0,0,0,0.25)';
      ctx.fillRect(o.x + S / 2 + 3, o.y + 7, 2, S - 14);
      frame(o, '#e4e7ea');
      ctx.fillStyle = 'rgba(0,0,0,0.3)';
      ctx.fillRect(o.x + 7, o.y + S - 9, S - 14, 2);
    }
    // 1 split window with a top transom
    {
      const o = cellFill(CELL.windowSplit, '#e9ecef');
      glassGradient(ctx, o.x + 7, o.y + 7, S - 14, S - 14, '#a4b9c9', '#566b7e');
      ctx.fillStyle = '#e1e5e8';
      ctx.fillRect(o.x + 7, o.y + S * 0.3, S - 14, 5);
      ctx.fillRect(o.x + S / 3, o.y + S * 0.3, 5, S - 14 - S * 0.23);
      ctx.fillRect(o.x + (2 * S) / 3, o.y + S * 0.3, 5, S - 14 - S * 0.23);
      frame(o, '#e4e7ea');
    }
    // 2 balcony door: full height sliding glass, dark interior glimpsed
    {
      const o = cellFill(CELL.balconyDoor, '#dfe3e6');
      glassGradient(ctx, o.x + 8, o.y + 8, S - 16, S - 16, '#8fa8bb', '#34475a');
      ctx.fillStyle = 'rgba(20,24,30,0.35)';
      ctx.fillRect(o.x + 8, o.y + 8, S - 16, S - 16);
      ctx.fillStyle = '#dfe3e6';
      ctx.fillRect(o.x + S / 2 - 3, o.y + 8, 6, S - 16);
      frame(o, '#d8dcdf', 8);
    }
    // 3 enclosed balcony: greenish glass over a frame with a drying rail and a glimpse of a box unit
    {
      const o = cellFill(CELL.enclosed, '#cfd5d6');
      glassGradient(ctx, o.x + 6, o.y + 6, S - 12, S - 12, '#8fb3a9', '#3b5a55');
      ctx.fillStyle = 'rgba(210,216,214,0.85)';
      for (let k = 1; k < 4; k++) ctx.fillRect(o.x + 6 + (k * (S - 12)) / 4 - 2, o.y + 6, 4, S - 12);
      ctx.fillRect(o.x + 6, o.y + S * 0.42, S - 12, 3);
      ctx.fillStyle = 'rgba(240,240,236,0.9)';
      ctx.fillRect(o.x + 18, o.y + S * 0.28, 34, 18);
      ctx.fillStyle = 'rgba(60,76,96,0.55)';
      ctx.fillRect(o.x + 64, o.y + S * 0.3, 28, 30);
      frame(o, '#c8cfd0', 6);
    }
    // 4 curtain wall panel: light blue-green glass with a spandrel strip
    {
      const o = cellFill(CELL.curtain, '#9aa6ae');
      glassGradient(ctx, o.x, o.y, S, S * 0.74, '#9cc3d2', '#3d6477');
      ctx.fillStyle = '#7f8e96';
      ctx.fillRect(o.x, o.y + S * 0.74, S, S * 0.26);
      ctx.fillStyle = 'rgba(255,255,255,0.12)';
      ctx.fillRect(o.x, o.y + S * 0.74, S, 3);
      ctx.fillStyle = '#c8d0d6';
      ctx.fillRect(o.x, o.y, 4, S);
      ctx.fillRect(o.x + S - 4, o.y, 4, S);
    }
    // 5 shopfront glass: bright interior, a display shelf, reflections
    {
      const o = cellFill(CELL.shopGlass, '#cfd4d8');
      glassGradient(ctx, o.x + 5, o.y + 5, S - 10, S - 10, '#d8e4ea', '#6d8494');
      ctx.fillStyle = 'rgba(255,238,200,0.55)';
      ctx.fillRect(o.x + 5, o.y + S * 0.18, S - 10, S * 0.5);
      for (let k = 0; k < 5; k++) {
        ctx.fillStyle = `hsla(${r() * 360},50%,55%,0.7)`;
        ctx.fillRect(o.x + 14 + k * 21, o.y + S * 0.5 - r() * 14, 14, 20 + r() * 14);
      }
      ctx.fillStyle = 'rgba(60,64,72,0.7)';
      ctx.fillRect(o.x + 5, o.y + S * 0.7, S - 10, 3);
      frame(o, '#6c727a', 5);
    }
    // 6 shop door: glass door with a push bar
    {
      const o = cellFill(CELL.shopDoor, '#b6bcc2');
      glassGradient(ctx, o.x + 14, o.y + 8, S - 28, S - 8, '#bcd0da', '#506879');
      ctx.fillStyle = 'rgba(255,238,200,0.4)';
      ctx.fillRect(o.x + 14, o.y + 8, S - 28, S * 0.45);
      ctx.fillStyle = '#8f969e';
      ctx.fillRect(o.x + S * 0.62, o.y + S * 0.42, 5, 40);
      frame(o, '#7b828a', 12);
    }
    // 7 roller shutter, closed
    {
      const o = cellFill(CELL.shutter, '#9ea3a8');
      for (let y = 0; y < S; y += 5) {
        ctx.fillStyle = y % 10 === 0 ? 'rgba(255,255,255,0.18)' : 'rgba(0,0,0,0.18)';
        ctx.fillRect(o.x, o.y + y, S, 3);
      }
      ctx.fillStyle = 'rgba(0,0,0,0.25)';
      ctx.fillRect(o.x, o.y, 5, S);
      ctx.fillRect(o.x + S - 5, o.y, 5, S);
    }
    // 8 air-conditioner outdoor unit: louvre side and a fan grille
    {
      const o = cellFill(CELL.acUnit, '#d8dcde');
      ctx.fillStyle = '#c4c9cc';
      ctx.fillRect(o.x, o.y, S, S);
      ctx.strokeStyle = 'rgba(70,76,82,0.55)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(o.x + S / 2, o.y + S / 2, S * 0.34, 0, Math.PI * 2);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(o.x + S / 2, o.y + S / 2, S * 0.16, 0, Math.PI * 2);
      ctx.stroke();
      for (let a = 0; a < 6.28; a += 0.52) {
        ctx.beginPath();
        ctx.moveTo(o.x + S / 2, o.y + S / 2);
        ctx.lineTo(o.x + S / 2 + Math.cos(a) * S * 0.34, o.y + S / 2 + Math.sin(a) * S * 0.34);
        ctx.stroke();
      }
      ctx.fillStyle = 'rgba(0,0,0,0.12)';
      ctx.fillRect(o.x, o.y + S - 10, S, 10);
    }
    // 9 dark office glass
    {
      const o = cellFill(CELL.curtainDark, '#2c3a45');
      glassGradient(ctx, o.x, o.y, S, S * 0.76, '#566f80', '#1d2c38');
      ctx.fillStyle = '#34414b';
      ctx.fillRect(o.x, o.y + S * 0.76, S, S * 0.24);
      ctx.fillStyle = '#9aa7b0';
      ctx.fillRect(o.x, o.y, 3, S);
      ctx.fillRect(o.x + S - 3, o.y, 3, S);
    }
    // 10 wide window with three panes
    {
      const o = cellFill(CELL.windowWide, '#e9ecef');
      glassGradient(ctx, o.x + 6, o.y + 6, S - 12, S - 12, '#a0b7c8', '#4f6579');
      ctx.fillStyle = '#e1e5e8';
      ctx.fillRect(o.x + S / 3 - 2, o.y + 6, 5, S - 12);
      ctx.fillRect(o.x + (2 * S) / 3 - 2, o.y + 6, 5, S - 12);
      frame(o, '#e4e7ea', 6);
    }
    // 11 narrow slit (stair core)
    {
      const o = cellFill(CELL.slit, '#e3e5e7');
      glassGradient(ctx, o.x + 30, o.y + 8, S - 60, S - 16, '#9eb4c4', '#4c6174');
      ctx.fillStyle = '#d5d9dc';
      ctx.fillRect(o.x + 30, o.y + S * 0.5, S - 60, 5);
    }

    // the signs, from cell 16: a coloured board, a pale border, the shop's name big and a small lamp strip
    SIGN_WORDS.forEach(([word, bg, fg], i) => {
      const o = cellOrigin(CELL.sign0 + i);
      ctx.fillStyle = bg;
      ctx.fillRect(o.x, o.y, S, S);
      const g = ctx.createLinearGradient(0, o.y, 0, o.y + S);
      g.addColorStop(0, 'rgba(255,255,255,0.20)');
      g.addColorStop(0.5, 'rgba(255,255,255,0)');
      g.addColorStop(1, 'rgba(0,0,0,0.22)');
      ctx.fillStyle = g;
      ctx.fillRect(o.x, o.y, S, S);
      ctx.strokeStyle = fg;
      ctx.globalAlpha = 0.85;
      ctx.lineWidth = 3;
      ctx.strokeRect(o.x + 5, o.y + 5, S - 10, S - 10);
      ctx.globalAlpha = 1;
      ctx.fillStyle = fg;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const size = word.length > 2 ? S * 0.34 : S * 0.46;
      ctx.font = `700 ${size}px "Microsoft YaHei","PingFang SC","Noto Sans CJK SC","Hiragino Sans GB",sans-serif`;
      ctx.fillText(word, o.x + S / 2, o.y + S / 2 + 2, S - 22);
    });
    return toTexture(canvas, { aniso: 8 });
  });
}

/** The uv rectangle of a cell, inset by half a texel so a neighbour's colour never bleeds in. */
export function cellUV(i: number): [number, number, number, number] {
  const { cols, rows, cell } = ATLAS;
  const col = i % cols;
  const row = Math.floor(i / cols);
  const e = 0.6 / (cols * cell);
  const f = 0.6 / (rows * cell);
  const u0 = col / cols + e;
  const u1 = (col + 1) / cols - e;
  // canvas row 0 is the top; the texture's v runs up
  const v1 = 1 - row / rows - f;
  const v0 = 1 - (row + 1) / rows + f;
  return [u0, v0, u1, v1];
}

/** The face of an expressway's overhead sign: green, a white border and rule, the road's name, two destinations and a lane arrow. */
export function gantrySign(): THREE.CanvasTexture {
  return cached('gantrySign', () => {
    const W = 1024;
    const H = 200;
    const { canvas, ctx } = makeCanvas(W, H);
    ctx.fillStyle = '#157a46';
    ctx.fillRect(0, 0, W, H);
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, 'rgba(255,255,255,0.10)');
    g.addColorStop(1, 'rgba(0,0,0,0.12)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = '#f4f6f4';
    ctx.lineWidth = 7;
    ctx.strokeRect(10, 10, W - 20, H - 20);
    ctx.fillStyle = '#f4f6f4';
    ctx.textBaseline = 'middle';
    const cjk = '"Microsoft YaHei","PingFang SC","Noto Sans CJK SC","Hiragino Sans GB",sans-serif';
    // every line is fitted to the room it has (a bold CJK fallback is wider than the font the sizes were drawn for)
    const fit = (text: string, weight: number, size: number, room: number) => {
      let px = size;
      for (; px > 18; px -= 2) {
        ctx.font = `${weight} ${px}px ${cjk}`;
        if (ctx.measureText(text).width <= room) break;
      }
    };
    ctx.textAlign = 'left';
    fit('G15 沈海高速', 700, 54, 360);
    ctx.fillText('G15 沈海高速', 48, 64);
    fit('Shenhai Expressway', 600, 34, 360);
    ctx.fillText('Shenhai Expressway', 50, 128);
    ctx.fillRect(498, 26, 4, H - 52);
    // the two places and their distances: names on the left of the column, distances right-aligned in their own room
    fit('温州 Wenzhou', 700, 46, 300);
    const nameSize = parseInt(ctx.font.match(/(\d+)px/)![1], 10);
    ctx.font = `700 ${nameSize}px ${cjk}`;
    ctx.fillText('宁波 Ningbo', 530, 62);
    ctx.fillText('温州 Wenzhou', 530, 134);
    ctx.textAlign = 'right';
    fit('290 km', 700, 42, 150);
    ctx.fillText('86 km', W - 40, 62);
    ctx.fillText('290 km', W - 40, 134);
    // a down arrow over the lane
    ctx.textAlign = 'left';
    ctx.beginPath();
    ctx.moveTo(430, 40);
    ctx.lineTo(466, 40);
    ctx.lineTo(466, 112);
    ctx.lineTo(486, 112);
    ctx.lineTo(448, 168);
    ctx.lineTo(410, 112);
    ctx.lineTo(430, 112);
    ctx.closePath();
    ctx.fill();
    return toTexture(canvas, { aniso: 8 });
  });
}

// ------------------------------------------------------------------------------------------------ trees

/**
 * A cluster of leaves on a transparent ground, lit from the upper left by its own painting: a solid dark core, leaves in three
 * tones over it, a soft light and shade. The tree is made of many cards of this, set on a ball, so the canopy has a ragged outline
 * and a full body from any side.
 */
export function leafCluster(kind: 'camphor' | 'plane' | 'ginkgo' | 'shrub' | 'cypress'): THREE.CanvasTexture {
  return cached(`leaf-${kind}`, () => {
    const S = 256;
    const { canvas, ctx } = makeCanvas(S, S);
    const r = rng(kind.length * 977 + 13);
    const pal =
      kind === 'ginkgo'
        ? { dark: '#8f6f10', mid: '#c99e1a', light: '#efcf3e', len: 28, wid: 24, n: 90, shape: 'fan' }
        : kind === 'plane'
          ? { dark: '#2f5320', mid: '#4b7f2a', light: '#86b845', len: 44, wid: 40, n: 40, shape: 'lobed' }
          : kind === 'shrub'
            ? { dark: '#234a28', mid: '#3a7234', light: '#6aa84a', len: 24, wid: 12, n: 120, shape: 'ellipse' }
            : kind === 'cypress'
              ? { dark: '#17402a', mid: '#25583a', light: '#44834f', len: 22, wid: 10, n: 150, shape: 'ellipse' }
              : { dark: '#17401f', mid: '#276a30', light: '#4f9a40', len: 34, wid: 15, n: 70, shape: 'ellipse' };
    // a solid ragged core, so the cluster has a body (the cards overlap into one full mass) and mipmaps keep its alpha
    ctx.fillStyle = pal.dark;
    for (let i = 0; i < 18; i++) {
      const a = r() * Math.PI * 2;
      const d = Math.sqrt(r()) * 0.3 * S;
      const rad = (0.12 + r() * 0.12) * S;
      ctx.beginPath();
      ctx.arc(S / 2 + Math.cos(a) * d, S / 2 + Math.sin(a) * d, rad, 0, Math.PI * 2);
      ctx.fill();
    }
    const leaf = (x: number, y: number, a: number, k: number, col: string) => {
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(a);
      ctx.fillStyle = col;
      ctx.beginPath();
      const l = pal.len * k;
      const w = pal.wid * k;
      if (pal.shape === 'fan') {
        ctx.moveTo(0, 0);
        ctx.quadraticCurveTo(-w, -l * 0.5, -w * 0.7, -l);
        ctx.lineTo(0, -l * 0.82);
        ctx.lineTo(w * 0.7, -l);
        ctx.quadraticCurveTo(w, -l * 0.5, 0, 0);
      } else if (pal.shape === 'lobed') {
        ctx.moveTo(0, 0);
        ctx.lineTo(-w * 0.55, -l * 0.25);
        ctx.lineTo(-w, -l * 0.45);
        ctx.lineTo(-w * 0.45, -l * 0.6);
        ctx.lineTo(-w * 0.35, -l);
        ctx.lineTo(0, -l * 0.72);
        ctx.lineTo(w * 0.35, -l);
        ctx.lineTo(w * 0.45, -l * 0.6);
        ctx.lineTo(w, -l * 0.45);
        ctx.lineTo(w * 0.55, -l * 0.25);
      } else {
        ctx.moveTo(0, 0);
        ctx.quadraticCurveTo(-w, -l * 0.5, 0, -l);
        ctx.quadraticCurveTo(w, -l * 0.5, 0, 0);
      }
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    };
    // leaves in three tones: dark through the body and round the rim, mid over it, light on the sunward side
    const layers: [string, number, number, number][] = [
      [pal.dark, 0.42, 0.0, 0.42],
      [pal.mid, 0.38, -0.05, 0.36],
      [pal.light, 0.2, -0.13, 0.28],
    ];
    layers.forEach(([col, share, bias, reach]) => {
      const n = Math.round(pal.n * share * 2);
      for (let i = 0; i < n; i++) {
        const a = r() * Math.PI * 2;
        const d = Math.sqrt(r()) * reach * S;
        const x = Math.min(S - 10, Math.max(10, S / 2 + Math.cos(a) * d + bias * S));
        const y = Math.min(S - 10, Math.max(10, S / 2 + Math.sin(a) * d + bias * S));
        // a tree's leaves fan out of the cluster's middle; a shrub's lie every way (a fan of them would read as a pom-pom)
        const turn = kind === 'shrub' ? r() * Math.PI * 2 : a + Math.PI / 2 + (r() - 0.5) * 1.5;
        leaf(x, y, turn, 0.85 + r() * 0.5, shade(col, 0.88 + r() * 0.24));
      }
    });
    // one soft light from the upper left over the painted part only, and a shade on the lower right
    ctx.globalCompositeOperation = 'source-atop';
    const lit = ctx.createRadialGradient(S * 0.36, S * 0.32, 4, S * 0.4, S * 0.38, S * 0.55);
    lit.addColorStop(0, 'rgba(255,250,190,0.30)');
    lit.addColorStop(1, 'rgba(255,250,190,0)');
    ctx.fillStyle = lit;
    ctx.fillRect(0, 0, S, S);
    const dim = ctx.createRadialGradient(S * 0.68, S * 0.72, 4, S * 0.64, S * 0.68, S * 0.5);
    dim.addColorStop(0, 'rgba(0,12,4,0.34)');
    dim.addColorStop(1, 'rgba(0,12,4,0)');
    ctx.fillStyle = dim;
    ctx.fillRect(0, 0, S, S);
    ctx.globalCompositeOperation = 'source-over';
    return toTexture(canvas, { aniso: 4 });
  });
}

/**
 * The body of a hedge or a shrub: a tile of small leaves lying every way, in four greens, over a dark ground, with slow patches of
 * light and shade. Opaque and tileable (a tile is about 0.9 m on the shrub, so a leaf is 4 to 6 cm), laid on the rounded mass
 * under the fringe of leaf cards.
 */
export function foliageMass(): THREE.CanvasTexture {
  return cached('foliage-mass', () => {
    const S = 256;
    const { canvas, ctx } = makeCanvas(S, S);
    const r = rng(4242);
    ctx.fillStyle = '#15321d';
    ctx.fillRect(0, 0, S, S);
    // drawn again a tile over wherever it crosses an edge, so the tile repeats without a seam
    const wrapped = (x: number, y: number, reach: number, draw: (px: number, py: number) => void) => {
      for (const dx of [-S, 0, S]) {
        for (const dy of [-S, 0, S]) {
          const px = x + dx;
          const py = y + dy;
          if (px < -reach || px > S + reach || py < -reach || py > S + reach) continue;
          draw(px, py);
        }
      }
    };
    // slow patches: a few lighter and darker clumps
    for (let i = 0; i < 30; i++) {
      const light = r() > 0.5;
      const rad = (0.08 + r() * 0.12) * S;
      wrapped(r() * S, r() * S, rad, (px, py) => {
        const g = ctx.createRadialGradient(px, py, 0, px, py, rad);
        g.addColorStop(0, light ? 'rgba(96,150,70,0.32)' : 'rgba(6,20,10,0.4)');
        g.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = g;
        ctx.fillRect(px - rad, py - rad, rad * 2, rad * 2);
      });
    }
    const leaf = (col: string, len: number, wid: number) => {
      const x = r() * S;
      const y = r() * S;
      const a = r() * Math.PI * 2;
      const k = 0.85 + r() * 0.35;
      wrapped(x, y, len, (px, py) => {
        ctx.save();
        ctx.translate(px, py);
        ctx.rotate(a);
        ctx.fillStyle = shade(col, 0.86 + r() * 0.28);
        ctx.beginPath();
        ctx.ellipse(0, 0, (len * k) / 2, (wid * k) / 2, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      });
    };
    for (let i = 0; i < 620; i++) leaf('#1f4a28', 21, 10);
    for (let i = 0; i < 560; i++) leaf('#2e6a30', 19, 9);
    for (let i = 0; i < 360; i++) leaf('#4c8c3c', 17, 8);
    for (let i = 0; i < 120; i++) leaf('#7db853', 15, 7);
    return toTexture(canvas, { repeat: true, aniso: 8 });
  });
}

export function barkTexture(): THREE.CanvasTexture {
  return cached('bark', () => {
    const W = 128;
    const H = 256;
    const { canvas, ctx } = makeCanvas(W, H);
    const r = rng(101);
    ctx.fillStyle = '#6a5d4b';
    ctx.fillRect(0, 0, W, H);
    for (let i = 0; i < 160; i++) {
      const x = r() * W;
      ctx.strokeStyle = `rgba(${r() > 0.5 ? '30,24,16' : '150,138,118'},${0.18 + r() * 0.25})`;
      ctx.lineWidth = 1 + r() * 2.5;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      let cx = x;
      for (let y = 0; y < H; y += 24) {
        cx += (r() - 0.5) * 6;
        ctx.lineTo(cx, y + 24);
      }
      ctx.stroke();
    }
    return toTexture(canvas, { repeat: true });
  });
}

// ------------------------------------------------------------------------------------------------ soft shadows

/** A round soft shadow with dapples where the sun comes through the leaves: a black, alpha-shaped decal. */
export function canopyShadow(): THREE.CanvasTexture {
  return cached('canopyShadow', () => {
    const S = 256;
    const { canvas, ctx } = makeCanvas(S, S);
    const n = tileNoise(S, 111, 5, 6, 0.55);
    const img = ctx.createImageData(S, S);
    for (let y = 0; y < S; y++) {
      for (let x = 0; x < S; x++) {
        const dx = (x - S / 2) / (S / 2);
        const dy = (y - S / 2) / (S / 2);
        const d = Math.hypot(dx, dy);
        const body = 1 - smooth(0.45, 1, d);
        const i = y * S + x;
        // light gets through toward the rim and in random gaps
        const gaps = smooth(0.42, 0.62, n[i]);
        const a = body * (0.42 + 0.3 * (1 - gaps)) * (0.78 + 0.22 * (1 - smooth(0.2, 0.9, d)));
        img.data[i * 4] = 8;
        img.data[i * 4 + 1] = 12;
        img.data[i * 4 + 2] = 10;
        img.data[i * 4 + 3] = Math.round(clamp01(a) * 255 * 0.82);
      }
    }
    ctx.putImageData(img, 0, 0);
    return toTexture(canvas);
  });
}

/** A tree pit in a footway: a square cast-iron grate round the trunk over dark soil, 1.4 m across. */
export function treePit(): THREE.CanvasTexture {
  return cached('treePit', () => {
    const S = 128;
    const { canvas, ctx } = makeCanvas(S, S);
    ctx.clearRect(0, 0, S, S);
    const r = rng(121);
    // a square of soil with a thin kerb of stone round it
    ctx.fillStyle = '#d3d5d9';
    ctx.fillRect(0, 0, S, S);
    ctx.fillStyle = '#3a3128';
    ctx.fillRect(7, 7, S - 14, S - 14);
    for (let i = 0; i < 160; i++) {
      ctx.fillStyle = r() > 0.5 ? 'rgba(120,98,70,0.5)' : 'rgba(20,16,12,0.5)';
      ctx.fillRect(8 + r() * (S - 16), 8 + r() * (S - 16), 1 + r() * 3, 1 + r() * 3);
    }
    // the grate: a frame, two inner rings of slots and an opening for the trunk
    ctx.strokeStyle = '#2b2d31';
    ctx.lineWidth = 4;
    ctx.strokeRect(11, 11, S - 22, S - 22);
    ctx.strokeStyle = 'rgba(70,74,82,0.9)';
    ctx.lineWidth = 3;
    for (const k of [0.22, 0.34]) {
      const m = S * k;
      ctx.strokeRect(m, m, S - 2 * m, S - 2 * m);
    }
    ctx.fillStyle = 'rgba(12,12,14,0.85)';
    ctx.fillRect(S / 2 - 9, S / 2 - 9, 18, 18);
    ctx.strokeStyle = 'rgba(70,74,82,0.9)';
    ctx.lineWidth = 2;
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2;
      ctx.beginPath();
      ctx.moveTo(S / 2 + Math.cos(a) * 12, S / 2 + Math.sin(a) * 12);
      ctx.lineTo(S / 2 + Math.cos(a) * 52, S / 2 + Math.sin(a) * 52);
      ctx.stroke();
    }
    return toTexture(canvas);
  });
}

/** A soft round contact shadow (a lamp post's foot, a bin, a bench): a plain radial fall-off. */
export function softDot(): THREE.CanvasTexture {
  return cached('softDot', () => {
    const S = 64;
    const { canvas, ctx } = makeCanvas(S, S);
    const g = ctx.createRadialGradient(S / 2, S / 2, 2, S / 2, S / 2, S / 2);
    g.addColorStop(0, 'rgba(6,8,10,0.72)');
    g.addColorStop(0.5, 'rgba(6,8,10,0.34)');
    g.addColorStop(1, 'rgba(6,8,10,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, S, S);
    return toTexture(canvas);
  });
}

/** A soft vertical fall-off, 1 at the bottom to 0 at the top: the shade a building throws on the footway at its foot, and its ambient darkening. */
export function footShade(): THREE.CanvasTexture {
  return cached('footShade', () => {
    const { canvas, ctx } = makeCanvas(4, 128);
    const g = ctx.createLinearGradient(0, 0, 0, 128);
    g.addColorStop(0, 'rgba(10,12,16,0)');
    g.addColorStop(1, 'rgba(10,12,16,0.5)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, 4, 128);
    return toTexture(canvas);
  });
}
