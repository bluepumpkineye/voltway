'use client';

import React from 'react';
import { techClock, useTechClock } from '@/lib/tech/clock';
import { corners, type Rect } from '@/lib/tech/park';
import { techSession, type Runtime } from '@/lib/tech/session';

/**
 * The car's rear camera, as the parking page shows it: the lot seen from the tail through a pinhole
 * camera pitched down at the floor, with the bay lines, the parked cars as plain boxes, the empty bay
 * picked out, and the path the car is about to take laid on the floor. It is projected from the same stage
 * and the same clock as everything else (the viewer, the top view), so the picture is the car's own.
 */
const W = 640;
const H = 400;
/** the camera: height above the floor, m; pitch down, rad; horizontal field of view */
const HEIGHT = 0.95;
const PITCH = (24 * Math.PI) / 180;
const F = W / 2 / Math.tan((104 * Math.PI) / 180 / 2);
const NEAR = 0.2;
const CAR_H = 1.5;

type V3 = [number, number, number];

interface Cam {
  c: V3;
  f: V3;
  r: V3;
  u: V3;
}

const dot = (a: V3, b: V3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a: V3, b: V3): V3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];

function camera(x: number, y: number, yaw: number, rear: number): Cam {
  const c = Math.cos(yaw);
  const s = Math.sin(yaw);
  const mount = -rear + 0.12;
  const f: V3 = [-c * Math.cos(PITCH), -s * Math.cos(PITCH), -Math.sin(PITCH)];
  const r: V3 = [-s, c, 0];
  const u = cross(r, f);
  return { c: [x + c * mount, y + s * mount, HEIGHT], f, r, u };
}

/** Camera-space coordinates of a point: right, up, depth. */
function toCam(cam: Cam, p: V3): V3 {
  const d: V3 = [p[0] - cam.c[0], p[1] - cam.c[1], p[2] - cam.c[2]];
  return [dot(d, cam.r), dot(d, cam.u), dot(d, cam.f)];
}

const screen = (q: V3): [number, number] => [W / 2 + (F * q[0]) / q[2], H / 2 - (F * q[1]) / q[2]];

/** A segment clipped to the near plane, in camera space; null when it is wholly behind it. */
function clipSegment(a: V3, b: V3): [V3, V3] | null {
  if (a[2] < NEAR && b[2] < NEAR) return null;
  let p = a;
  let q = b;
  if (p[2] < NEAR) p = lerpTo(p, q);
  else if (q[2] < NEAR) q = lerpTo(q, p);
  return [p, q];
}
function lerpTo(behind: V3, front: V3): V3 {
  const t = (NEAR - behind[2]) / (front[2] - behind[2]);
  return [behind[0] + (front[0] - behind[0]) * t, behind[1] + (front[1] - behind[1]) * t, NEAR];
}

/** The polyline's pieces in front of the camera, as an SVG path. */
function pathOf(cam: Cam, pts: V3[]): string {
  let d = '';
  let pen = false;
  for (let i = 0; i + 1 < pts.length; i++) {
    const seg = clipSegment(toCam(cam, pts[i]), toCam(cam, pts[i + 1]));
    if (!seg) {
      pen = false;
      continue;
    }
    const [p, q] = [screen(seg[0]), screen(seg[1])];
    d += pen ? ` L${q[0].toFixed(1)} ${q[1].toFixed(1)}` : `M${p[0].toFixed(1)} ${p[1].toFixed(1)} L${q[0].toFixed(1)} ${q[1].toFixed(1)}`;
    pen = true;
  }
  return d;
}

/** The convex outline of a box in view: its vertices in front of the camera and where its edges meet the near plane. */
function boxOutline(cam: Cam, r: Rect, height: number): [number, number][] | null {
  const ground = corners(r);
  const v: V3[] = [...ground.map((g): V3 => [g.x, g.y, 0]), ...ground.map((g): V3 => [g.x, g.y, height])];
  const q = v.map((p) => toCam(cam, p));
  const pts: V3[] = q.filter((p) => p[2] >= NEAR);
  const edges: [number, number][] = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]];
  for (const [i, j] of edges) {
    if ((q[i][2] >= NEAR) !== (q[j][2] >= NEAR)) pts.push(q[i][2] < NEAR ? lerpTo(q[i], q[j]) : lerpTo(q[j], q[i]));
  }
  if (pts.length < 3) return null;
  return hull(pts.map(screen));
}

/** Andrew's monotone chain. */
function hull(p: [number, number][]): [number, number][] {
  const s = [...p].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cr = (o: [number, number], a: [number, number], b: [number, number]) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lo: [number, number][] = [];
  for (const q of s) {
    while (lo.length >= 2 && cr(lo[lo.length - 2], lo[lo.length - 1], q) <= 0) lo.pop();
    lo.push(q);
  }
  const up: [number, number][] = [];
  for (const q of [...s].reverse()) {
    while (up.length >= 2 && cr(up[up.length - 2], up[up.length - 1], q) <= 0) up.pop();
    up.push(q);
  }
  return lo.slice(0, -1).concat(up.slice(0, -1));
}

const HORIZON = H / 2 - F * Math.tan(PITCH);

export function RearView({ runtime, className }: { runtime: Runtime | null; className?: string }) {
  const clock = useTechClock();
  const stage = runtime?.stage ?? null;
  const lines = React.useRef<SVGPathElement>(null);
  const route = React.useRef<SVGPathElement>(null);
  const bay = React.useRef<SVGPolygonElement>(null);
  const boxes = React.useRef<(SVGPolygonElement | null)[]>([]);
  const layer = React.useRef<SVGGElement>(null);

  const draw = React.useCallback(() => {
    const rt = techSession.runtime ?? runtime;
    if (!rt?.stage) return;
    const s = rt.sample(techClock.t);
    const cam = camera(s.x, s.y, s.yaw, rt.body.rear);
    const st = rt.stage;

    // bay lines
    let d = '';
    for (const b of st.bays) {
      const r = b.rect;
      const xa = r.x - r.width / 2;
      const xb = r.x + r.width / 2;
      const ya = r.y - r.length / 2;
      const yb = r.y + r.length / 2;
      d += pathOf(cam, [[xa, yb, 0], [xa, ya, 0], [xb, ya, 0], [xb, yb, 0]]);
    }
    lines.current?.setAttribute('d', d);

    // the way in, on the floor
    route.current?.setAttribute('d', pathOf(cam, st.pathIn.map((p): V3 => [p.x, p.y, 0])));

    // the empty bay
    const target = st.bays.find((b) => b.target)!.rect;
    const q = corners(target).map((c) => toCam(cam, [c.x, c.y, 0]));
    const ring = q.length === 4 && q.every((p) => p[2] >= NEAR) ? q.map((p) => screen(p).map((n) => n.toFixed(1)).join(',')).join(' ') : '';
    bay.current?.setAttribute('points', ring);

    // the parked cars, far ones first
    const order = st.neighbours
      .map((n, i) => ({ i, z: toCam(cam, [n.rect.x, n.rect.y, 0])[2] }))
      .sort((a, b) => b.z - a.z);
    for (const { i } of order) {
      const poly = boxOutline(cam, st.neighbours[i].rect, CAR_H);
      boxes.current[i]?.setAttribute('points', poly ? poly.map((p) => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ') : '');
      // keep far-to-near drawing order, inside the layer (the bumper stays on top)
      const el = boxes.current[i];
      if (el) layer.current?.appendChild(el);
    }
  }, [runtime]);

  React.useLayoutEffect(draw);
  React.useEffect(() => {
    if (!clock.playing) return;
    let raf = 0;
    const loop = () => {
      draw();
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [clock.playing, draw]);

  return (
    <svg className={className} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid slice" role="img" aria-label="The rear camera">
      <defs>
        <linearGradient id="rv-floor" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#4a4f57" />
          <stop offset="1" stopColor="#2c2f35" />
        </linearGradient>
        <linearGradient id="rv-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#1b1e24" />
          <stop offset="1" stopColor="#3a4048" />
        </linearGradient>
      </defs>
      <rect width={W} height={H} fill="url(#rv-sky)" />
      <rect y={HORIZON} width={W} height={H - HORIZON} fill="url(#rv-floor)" />
      <polygon ref={bay} fill="#4a74ff" fillOpacity={0.22} stroke="#4a74ff" strokeOpacity={0.9} strokeWidth={3} strokeLinejoin="round" />
      <path ref={lines} fill="none" stroke="#e8eaee" strokeOpacity={0.85} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round" />
      <path ref={route} fill="none" stroke="#6f95ff" strokeOpacity={0.9} strokeWidth={5} strokeDasharray="14 10" strokeLinecap="round" />
      <g ref={layer}>
        {(stage?.neighbours ?? []).map((n, i) => (
          <polygon key={i} ref={(el) => { boxes.current[i] = el; }} fill="#8d929b" fillOpacity={0.92} stroke="#2a2d33" strokeWidth={2} strokeLinejoin="round" />
        ))}
      </g>
      {/* the car's own bumper along the bottom edge */}
      <path d={`M0 ${H} L0 ${H - 34} Q${W / 2} ${H - 62} ${W} ${H - 34} L${W} ${H} Z`} fill="#15171b" />
    </svg>
  );
}
