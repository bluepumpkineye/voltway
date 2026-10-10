'use client';

import React from 'react';
import { techClock, useTechClock } from '@/lib/tech/clock';
import { footprint, gap, type Rect } from '@/lib/tech/park';
import { techSession, useRuntime, type Runtime } from '@/lib/tech/session';

/**
 * The lot from above, as a parking app and a car's parking page draw it: the painted bays, the parked cars,
 * the empty bay the car is going into, the path the car will take, and the car itself, moving with the
 * demo's clock. Drawn from the same stage the viewer draws (src/lib/tech/park.ts), so the two always agree.
 *
 * The scene is authored in floor metres, north up; the car is moved by the frame loop (its group's
 * transform is written directly, not through React) while the clock runs.
 */
export type TopTheme = 'light' | 'dark';

const LOOK = {
  light: {
    ground: '#dcdde2',
    line: '#ffffff',
    car: '#f6f6f8',
    carEdge: '#b9bcc4',
    glass: '#8f95a1',
    target: '#2f6bff',
    path: '#2f6bff',
    near: '#ff9a3d',
    close: '#ff4a3f',
  },
  dark: {
    ground: '#1d2025',
    line: '#9ba1ad',
    car: '#5a606b',
    carEdge: '#2c3037',
    glass: '#262a31',
    target: '#4a74ff',
    path: '#6f95ff',
    near: '#ff9a3d',
    close: '#ff4a3f',
  },
} as const;

/** A parked car seen from above: the body, and darker panes front and back. Drawn along +x. */
function CarShape({ r, look }: { r: Rect; look: (typeof LOOK)[TopTheme] }) {
  const { length: L, width: W } = r;
  return (
    <g transform={`translate(${r.x} ${r.y}) rotate(${(r.yaw * 180) / Math.PI})`}>
      <rect x={-L / 2} y={-W / 2} width={L} height={W} rx={W * 0.32} fill={look.car} stroke={look.carEdge} strokeWidth={0.05} />
      {/* windscreen and rear window, and the roof between them */}
      <rect x={L * 0.12} y={-W * 0.38} width={L * 0.16} height={W * 0.76} rx={0.12} fill={look.glass} />
      <rect x={-L * 0.34} y={-W * 0.36} width={L * 0.13} height={W * 0.72} rx={0.12} fill={look.glass} />
      <rect x={-L * 0.2} y={-W * 0.34} width={L * 0.31} height={W * 0.68} rx={0.2} fill={look.car} stroke={look.carEdge} strokeWidth={0.03} opacity={0.9} />
    </g>
  );
}

/** The sprite of our own car from above (the cabin's art), 420 x 969 px, nose up. */
const SPRITE = { src: '/hmi/luxeed-rx/car-top.webp', aspect: 420 / 969 };

export function ParkTopView({
  theme = 'light',
  className,
  showPath = true,
  /** the empty bay is picked out in blue */
  selected = true,
  /** extra metres of ground to show round the action */
  margin = 0.9,
  /** the car art, when it is not the Luxeed's */
  sprite = SPRITE,
  /** what to draw while no demo is running (the lot as it stands, before the Tech tab has built it) */
  preview = null,
}: {
  theme?: TopTheme;
  className?: string;
  showPath?: boolean;
  selected?: boolean;
  margin?: number;
  sprite?: { src: string; aspect: number };
  preview?: Runtime | null;
}) {
  const live = useRuntime();
  const rt = live ?? preview;
  const stage = rt?.stage ?? null;
  const clock = useTechClock();
  const look = LOOK[theme];
  const car = React.useRef<SVGGElement>(null);
  const halo = React.useRef<SVGRectElement>(null);

  const place = React.useCallback(() => {
    const r = techSession.runtime ?? preview;
    const g = car.current;
    if (!r || !g) return;
    const s = r.sample(techClock.t);
    const fp = footprint(s, r.body);
    const deg = (s.yaw * 180) / Math.PI;
    // the sprite points north, which is a heading of 90 degrees; the floor is drawn with y up (see the group's flip)
    g.setAttribute('transform', `translate(${fp.x} ${fp.y}) rotate(${deg - 90})`);
    // a ring round the car that warms as it nears a parked car
    const h = halo.current;
    if (h && r.stage) {
      let min = Infinity;
      for (const n of r.stage.neighbours) min = Math.min(min, gap(fp, n.rect));
      const c = min < 0.5 ? look.close : min < 0.9 ? look.near : 'none';
      h.setAttribute('stroke', c);
      h.setAttribute('opacity', c === 'none' ? '0' : '0.9');
    }
  }, [look, preview]);

  // draw at every render (a pause, a seek, a new demo), and every frame while the clock runs
  React.useLayoutEffect(place);
  React.useEffect(() => {
    if (!clock.playing) return;
    let raf = 0;
    const loop = () => {
      place();
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [clock.playing, place]);

  if (!stage || !rt) return <div className={className} />;

  const b = stage.bounds;
  const x0 = b.min.x - margin;
  const x1 = b.max.x + margin;
  const y0 = b.min.y - margin;
  const y1 = b.max.y + margin;
  const L = rt.body.rear + rt.body.front;
  const spriteH = L;
  const spriteW = spriteH * sprite.aspect;
  const target = stage.bays.find((bay) => bay.target)!.rect;

  return (
    <svg
      className={className}
      viewBox={`${x0} ${-y1} ${x1 - x0} ${y1 - y0}`}
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="The car and the bays from above"
    >
      <rect x={x0} y={-y1} width={x1 - x0} height={y1 - y0} fill={look.ground} />
      <g transform="scale(1 -1)">
        {/* the bays, open at the lane */}
        {stage.bays.map((bay, i) => {
          const r = bay.rect;
          const xa = r.x - r.width / 2;
          const xb = r.x + r.width / 2;
          const ya = r.y - r.length / 2;
          const yb = r.y + r.length / 2;
          return (
            <path key={i} d={`M${xa} ${yb} L${xa} ${ya} L${xb} ${ya} L${xb} ${yb}`} fill="none" stroke={look.line} strokeWidth={0.09} strokeLinecap="butt" opacity={theme === 'dark' ? 0.7 : 1} />
          );
        })}
        {stage.neighbours.map((n, i) => (
          <CarShape key={i} r={n.rect} look={look} />
        ))}
        {selected && (
          <rect
            x={target.x - target.width / 2 + 0.12}
            y={target.y - target.length / 2 + 0.12}
            width={target.width - 0.24}
            height={target.length - 0.24}
            rx={0.28}
            fill={look.target}
            fillOpacity={0.16}
            stroke={look.target}
            strokeWidth={0.1}
          />
        )}
        {showPath && (
          <polyline
            points={stage.pathIn.map((p) => `${p.x},${p.y}`).join(' ')}
            fill="none"
            stroke={look.path}
            strokeWidth={0.16}
            strokeDasharray="0.5 0.36"
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity={0.85}
          />
        )}
        {/* the ring that warms near a parked car */}
        <g ref={car}>
          <g transform="scale(1 -1)">
            <rect
              ref={halo}
              x={-spriteW / 2 - 0.12}
              y={-spriteH / 2 - 0.12}
              width={spriteW + 0.24}
              height={spriteH + 0.24}
              rx={0.5}
              fill="none"
              strokeWidth={0.12}
              opacity={0}
            />
            <image href={sprite.src} x={-spriteW / 2} y={-spriteH / 2} width={spriteW} height={spriteH} preserveAspectRatio="xMidYMid meet" />
          </g>
        </g>
      </g>
    </svg>
  );
}
