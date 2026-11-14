import { TURN_AT, type RingState } from '@/lib/tech/starring';

/**
 * The Avatr 06T's Star Ring and its two mirror screens, drawn onto canvases (src/components/viewer/StarRing.tsx puts them on the cabin's
 * screens). The ring's layout and light daytime look are read off Autohome's photographs of the car (c10_0001 and c10_0048): at the left the
 * car with its range, power meter and total mileage, a lamp row and the gear, the time and the temperature; a media card with the song's
 * name and a disc; a trip-energy readout; and at the right the weather and the time with a round clock. Ours: the speed numeral, the route
 * card, the mirror pictures, every number. Pure of the DOM but for the canvases it is given.
 */
type Ctx = CanvasRenderingContext2D;

const FONT = "'Inter', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif";
const INK = '#1c2030';
const DIM = '#767b90';
const ACCENT = '#5b6cff';
const RED = '#e5372f';
/** the share of the ring's width at each end left dark, under the mirror screens that overlap it */
const MARGIN = 0.034;
const GREEN = '#37b26c';

const rr = (ctx: Ctx, x: number, y: number, w: number, h: number, r: number) => {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
};

const text = (ctx: Ctx, s: string, x: number, y: number, size: number, weight: number, color: string, align: CanvasTextAlign = 'left') => {
  ctx.font = `${weight} ${size}px ${FONT}`;
  ctx.fillStyle = color;
  ctx.textAlign = align;
  ctx.textBaseline = 'alphabetic';
  ctx.fillText(s, x, y);
};

/** A wagon in side view, in the body blue of the photographed car; `x`, `y` the middle of its length, `len` its length. */
function car(ctx: Ctx, x: number, y: number, len: number) {
  const k = (px: number, py: number): [number, number] => [x - len / 2 + px * len, y - 0.14 * len + py * len];
  const poly = (pts: [number, number][], fill: string) => {
    ctx.beginPath();
    pts.map(([a, b]) => k(a, b)).forEach(([px, py], i) => (i ? ctx.lineTo(px, py) : ctx.moveTo(px, py)));
    ctx.closePath();
    ctx.fillStyle = fill;
    ctx.fill();
  };
  ctx.save();
  ctx.shadowColor = 'rgba(40,50,110,0.28)';
  ctx.shadowBlur = len * 0.05;
  ctx.shadowOffsetY = len * 0.03;
  poly([[0.02, 0.24], [0.02, 0.16], [0.07, 0.1], [0.16, 0.045], [0.52, 0.04], [0.7, 0.075], [0.88, 0.14], [0.985, 0.17], [0.985, 0.24]], '#8da6f2');
  ctx.restore();
  poly([[0.17, 0.07], [0.52, 0.065], [0.66, 0.092], [0.6, 0.135], [0.16, 0.135]], '#dfe8ff');
  for (const wx of [0.2, 0.8]) {
    const [cx, cy] = k(wx, 0.245);
    ctx.beginPath();
    ctx.arc(cx, cy, len * 0.052, 0, Math.PI * 2);
    ctx.fillStyle = '#272a36';
    ctx.fill();
    ctx.beginPath();
    ctx.arc(cx, cy, len * 0.028, 0, Math.PI * 2);
    ctx.fillStyle = '#c5cad8';
    ctx.fill();
  }
}

/** A right-turn arrow: a stem coming up from below, bending right, with a head. */
function turnArrow(ctx: Ctx, x: number, y: number, size: number, turn: 'right' | 'ahead') {
  ctx.save();
  ctx.translate(x, y);
  ctx.strokeStyle = ACCENT;
  ctx.fillStyle = ACCENT;
  ctx.lineWidth = size * 0.17;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.beginPath();
  if (turn === 'right') {
    ctx.moveTo(0, size * 0.5);
    ctx.lineTo(0, -size * 0.02);
    ctx.quadraticCurveTo(0, -size * 0.3, size * 0.28, -size * 0.3);
    ctx.lineTo(size * 0.4, -size * 0.3);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(size * 0.36, -size * 0.52);
    ctx.lineTo(size * 0.62, -size * 0.3);
    ctx.lineTo(size * 0.36, -size * 0.08);
    ctx.closePath();
    ctx.fill();
  } else {
    ctx.moveTo(0, size * 0.5);
    ctx.lineTo(0, -size * 0.3);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(-size * 0.24, -size * 0.28);
    ctx.lineTo(0, -size * 0.56);
    ctx.lineTo(size * 0.24, -size * 0.28);
    ctx.closePath();
    ctx.fill();
  }
  ctx.restore();
}

function clockFace(ctx: Ctx, x: number, y: number, r: number, clock: string) {
  const [hh, mm] = clock.split(':').map(Number);
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fillStyle = '#ffffff';
  ctx.fill();
  ctx.strokeStyle = '#c9cde0';
  ctx.lineWidth = r * 0.06;
  ctx.stroke();
  const hand = (deg: number, len: number, wd: number, col: string) => {
    const a = ((deg - 90) * Math.PI) / 180;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + Math.cos(a) * r * len, y + Math.sin(a) * r * len);
    ctx.strokeStyle = col;
    ctx.lineWidth = wd;
    ctx.lineCap = 'round';
    ctx.stroke();
  };
  hand((hh % 12) * 30 + mm * 0.5, 0.5, r * 0.09, INK);
  hand(mm * 6, 0.76, r * 0.06, INK);
  ctx.beginPath();
  ctx.arc(x, y, r * 0.07, 0, Math.PI * 2);
  ctx.fillStyle = ACCENT;
  ctx.fill();
}

/** The lit picture of the ring, left to right. */
function lit(ctx: Ctx, w: number, h: number, s: RingState) {
  const u = h / 100;
  // the mirror screens' inner edges lie over the ring's ends (the model's quads overlap by about 2.6 cm of the 1.08 m): nothing is
  // drawn in the margin, so no figure sits under a mirror. X is a place along the ring inside the margins, Wd a length along it.
  const S = 1 - 2 * MARGIN;
  const X = (f: number) => (MARGIN + f * S) * w;
  const Wd = (f: number) => f * S * w;
  const bg = ctx.createLinearGradient(0, 0, w, 0);
  bg.addColorStop(0, '#f7f7fd');
  bg.addColorStop(0.5, '#eef0fa');
  bg.addColorStop(1, '#e4e7f6');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, w, h);

  // ---- the car's zone: speed, car, lamps, range, power, gear
  text(ctx, String(Math.round(s.speed)), X(0.018), 56 * u, 50 * u, 600, INK);
  text(ctx, 'km/h', X(0.019), 71 * u, 13 * u, 500, DIM);
  car(ctx, X(0.14), 46 * u, Wd(0.092));
  if (s.belt) {
    // the seat-belt lamp, red as in the photograph: a seated figure with a diagonal strap
    ctx.fillStyle = RED;
    ctx.beginPath();
    ctx.arc(X(0.108), 13 * u, 3.4 * u, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = RED;
    ctx.lineWidth = 2.4 * u;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(X(0.108) - 4.6 * u, 24 * u);
    ctx.lineTo(X(0.108) + 3.4 * u, 18.5 * u);
    ctx.lineTo(X(0.108) + 3.4 * u, 26 * u);
    ctx.stroke();
  }
  if (s.brake) {
    ctx.strokeStyle = RED;
    ctx.lineWidth = 1.8 * u;
    ctx.beginPath();
    ctx.arc(X(0.158), 19 * u, 7.6 * u, 0, Math.PI * 2);
    ctx.stroke();
    text(ctx, 'P', X(0.158), 23.2 * u, 12 * u, 700, RED, 'center');
  }
  // the row at the foot: range, power, total mileage
  text(ctx, String(s.rangeKm), X(0.018), 92 * u, 17 * u, 600, INK);
  text(ctx, 'km', X(0.018) + 33 * u, 92 * u, 9.5 * u, 500, DIM);
  rr(ctx, X(0.018), 95.2 * u, Wd(0.046), 2.2 * u, 1.1 * u);
  ctx.fillStyle = '#d6d9e8';
  ctx.fill();
  rr(ctx, X(0.018), 95.2 * u, Wd(0.046) * 0.92, 2.2 * u, 1.1 * u);
  const g = ctx.createLinearGradient(X(0.018), 0, X(0.064), 0);
  g.addColorStop(0, GREEN);
  g.addColorStop(1, '#d7c24a');
  ctx.fillStyle = g;
  ctx.fill();
  const pw = Wd(0.05);
  text(ctx, `${Math.round(Math.abs(s.power) * 100)}%`, X(0.084), 92 * u, 17 * u, 600, INK);
  text(ctx, s.power < -0.02 ? 'REGEN' : 'PWR', X(0.084) + 46 * u, 92 * u, 8.5 * u, 600, DIM);
  rr(ctx, X(0.084), 95.2 * u, pw, 2.2 * u, 1.1 * u);
  ctx.fillStyle = '#d6d9e8';
  ctx.fill();
  const mid = X(0.084) + pw / 2;
  const span = (pw / 2) * Math.abs(s.power);
  rr(ctx, s.power >= 0 ? mid : mid - span, 95.2 * u, Math.max(span, 1.5 * u), 2.2 * u, 1.1 * u);
  ctx.fillStyle = s.power >= 0 ? ACCENT : GREEN;
  ctx.fill();
  text(ctx, '9', X(0.152), 92 * u, 17 * u, 600, INK);
  text(ctx, 'km', X(0.152) + 14 * u, 92 * u, 9.5 * u, 500, DIM);
  // gear, time, temperature
  const gx = X(0.2);
  rr(ctx, gx, 74 * u, 17 * u, 19 * u, 4 * u);
  ctx.strokeStyle = INK;
  ctx.lineWidth = 1.5 * u;
  ctx.stroke();
  text(ctx, s.gear, gx + 8.5 * u, 88.4 * u, 15 * u, 700, INK, 'center');
  text(ctx, s.clock, gx + 28 * u, 88.4 * u, 14 * u, 500, INK);
  text(ctx, '24.5°C', gx + 28 * u + 53 * u, 88.4 * u, 14 * u, 500, INK);

  // ---- the centre: the next turn of the route the centre screen has set, else the media card
  if (s.route) {
    const cx = X(0.292);
    turnArrow(ctx, cx, 50 * u, 38 * u, s.route.turn);
    const dist = s.route.dist;
    const label = dist >= 1000 ? `${(dist / 1000).toFixed(1)}` : `${Math.max(0, Math.round(dist / 10) * 10)}`;
    text(ctx, label, cx + 38 * u, 52 * u, 34 * u, 600, INK);
    text(ctx, dist >= 1000 ? 'km' : 'm', cx + 38 * u + label.length * 19 * u + 4 * u, 52 * u, 14 * u, 500, DIM);
    text(ctx, `Turn right onto ${s.route.road}`, cx + 38 * u, 68 * u, 11.5 * u, 500, INK);
    text(ctx, s.route.then, cx + 38 * u, 82 * u, 10 * u, 400, DIM);
    // the distance left to the turn, as a bar
    const bx = X(0.292);
    const bw = Wd(0.2);
    rr(ctx, bx, 94 * u, bw, 2.4 * u, 1.2 * u);
    ctx.fillStyle = '#d6d9e8';
    ctx.fill();
    rr(ctx, bx, 94 * u, Math.max(2.4 * u, bw * Math.min(1, 1 - s.route.dist / TURN_AT)), 2.4 * u, 1.2 * u);
    ctx.fillStyle = ACCENT;
    ctx.fill();
  } else {
    const mx = X(0.292);
    text(ctx, s.media.title, mx, 44 * u, 20 * u, 600, INK);
    text(ctx, s.media.artist, mx, 60 * u, 12 * u, 400, DIM);
    rr(ctx, mx, 78 * u, Wd(0.17), 2.4 * u, 1.2 * u);
    ctx.fillStyle = '#d6d9e8';
    ctx.fill();
    rr(ctx, mx, 78 * u, Math.max(2.4 * u, Wd(0.17) * s.media.progress), 2.4 * u, 1.2 * u);
    ctx.fillStyle = ACCENT;
    ctx.fill();
    const dx = X(0.495);
    const disc = ctx.createRadialGradient(dx - 4 * u, 46 * u, 2 * u, dx, 50 * u, 19 * u);
    disc.addColorStop(0, '#8fa2ff');
    disc.addColorStop(1, '#4a58d8');
    ctx.beginPath();
    ctx.arc(dx, 50 * u, 17 * u, 0, Math.PI * 2);
    ctx.fillStyle = disc;
    ctx.fill();
    text(ctx, '♪', dx, 58 * u, 22 * u, 600, '#ffffff', 'center');
  }

  // ---- the trip's energy
  const ex = X(0.57);
  text(ctx, 'THIS TRIP', ex, 26 * u, 9 * u, 600, DIM);
  text(ctx, '15.2', ex, 52 * u, 26 * u, 600, INK);
  text(ctx, 'kWh/100km', ex + 62 * u, 52 * u, 9.5 * u, 500, DIM);
  for (let i = 0; i < 14; i++) {
    const bh = (6 + 15 * Math.abs(Math.sin(i * 1.3 + 0.7))) * u;
    rr(ctx, ex + i * 8.2 * u, 84 * u - bh, 4.6 * u, bh, 1.6 * u);
    ctx.fillStyle = i > 10 ? ACCENT : '#c9cfee';
    ctx.fill();
  }

  // ---- the weather and the time
  const wx = X(0.72);
  text(ctx, '12°', wx, 54 * u, 40 * u, 500, INK);
  text(ctx, 'Beijing', wx, 70 * u, 11 * u, 500, INK);
  text(ctx, '21° / 8° · Haze', wx, 84 * u, 10 * u, 400, DIM);
  ctx.fillStyle = '#d3d7ea';
  ctx.fillRect(X(0.835), 24 * u, 1.4 * u, 52 * u);
  text(ctx, s.clock, X(0.85), 54 * u, 34 * u, 500, INK);
  text(ctx, 'Beijing', X(0.85), 70 * u, 11 * u, 500, INK);
  clockFace(ctx, X(0.953), 50 * u, 24 * u, s.clock);
}

/** The ring: dark glass until the light reaches it, a bright edge as it sweeps from the left end to the right. */
export function drawRing(ctx: Ctx, w: number, h: number, s: RingState) {
  ctx.save();
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = '#05060a';
  ctx.fillRect(0, 0, w, h);
  if (s.wake > 0) {
    const soft = 0.07 * w;
    const edge = s.wake * (w + soft);
    ctx.save();
    ctx.beginPath();
    ctx.rect(0, 0, Math.min(w, edge), h);
    ctx.clip();
    lit(ctx, w, h, s);
    ctx.restore();
    if (s.wake < 1) {
      const g = ctx.createLinearGradient(edge - soft, 0, edge, 0);
      g.addColorStop(0, 'rgba(180,200,255,0)');
      g.addColorStop(0.85, 'rgba(190,210,255,0.55)');
      g.addColorStop(1, 'rgba(255,255,255,0.95)');
      ctx.fillStyle = g;
      ctx.fillRect(Math.max(0, edge - soft), 0, Math.min(soft, w), h);
    }
  }
  ctx.restore();
}

/**
 * A mirror screen: the road behind (it is a camera's picture), when the car is in gear; dark glass otherwise. `dist` is how far the car has
 * driven, so the lane marks stream; `side` is -1 for the driver's (left) and 1 for the passenger's mirror, whose picture leans the other way.
 */
export function drawMirror(ctx: Ctx, w: number, h: number, on: boolean, dist: number, side: -1 | 1) {
  ctx.save();
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = '#06070b';
  ctx.fillRect(0, 0, w, h);
  if (on) {
    const sky = ctx.createLinearGradient(0, 0, 0, h * 0.45);
    sky.addColorStop(0, '#cfe2ff');
    sky.addColorStop(1, '#eef4ff');
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, w, h * 0.45);
    const grass = ctx.createLinearGradient(0, h * 0.45, 0, h);
    grass.addColorStop(0, '#a9c9a0');
    grass.addColorStop(1, '#7ea274');
    ctx.fillStyle = grass;
    ctx.fillRect(0, h * 0.45, w, h * 0.55);
    // the road narrows to a vanishing point that leans toward the car's side
    const vx = w * (0.5 - side * 0.12);
    const vy = h * 0.45;
    ctx.fillStyle = '#4b5060';
    ctx.beginPath();
    ctx.moveTo(vx - w * 0.03, vy);
    ctx.lineTo(vx + w * 0.03, vy);
    ctx.lineTo(w * (0.5 + side * 0.02) + w * 0.62, h);
    ctx.lineTo(w * (0.5 + side * 0.02) - w * 0.62, h);
    ctx.closePath();
    ctx.fill();
    // dashes that run toward the viewer
    ctx.fillStyle = '#f4f5f8';
    for (let i = 0; i < 6; i++) {
      const p = (((i + (dist * 0.18) % 1) / 6) ** 2);
      const y = vy + (h - vy) * p;
      const lh = (h - vy) * (0.03 + 0.1 * p);
      const lw = w * (0.006 + 0.012 * p);
      const cx = vx + (w * (0.5 + side * 0.02) - vx) * p;
      ctx.fillRect(cx - lw / 2, y, lw, lh);
    }
    // a car following, small and a long way back
    const cx = vx + side * w * 0.02;
    rr(ctx, cx - w * 0.07, h * 0.55, w * 0.14, h * 0.13, h * 0.025);
    ctx.fillStyle = '#6b7488';
    ctx.fill();
    ctx.fillStyle = '#d33a35';
    ctx.fillRect(cx - w * 0.06, h * 0.6, w * 0.03, h * 0.02);
    ctx.fillRect(cx + w * 0.03, h * 0.6, w * 0.03, h * 0.02);
    // the car's own flank at the picture's inner edge, as a mirror shows it
    ctx.fillStyle = '#8da6f2';
    ctx.beginPath();
    ctx.moveTo(side > 0 ? 0 : w, h);
    ctx.lineTo(side > 0 ? 0 : w, h * 0.7);
    ctx.quadraticCurveTo(side > 0 ? w * 0.1 : w * 0.9, h * 0.75, side > 0 ? w * 0.18 : w * 0.82, h);
    ctx.closePath();
    ctx.fill();
  }
  ctx.restore();
}
