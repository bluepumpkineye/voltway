'use client';

import React from 'react';
import type { Vehicle } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';

/**
 * The labels of the exploded view, drawn over the picture: a pill for each part and a leader line from it to the part. React only
 * builds the elements; the viewer (viewer/XrayLabelDriver.tsx) writes their positions every frame through `labelLayer`, so the
 * pills glide with the parts as they fly out and as the camera turns, without a render of this component.
 */

export interface LabelEls {
  pill: HTMLButtonElement | null;
  path: SVGPathElement | null;
  dot: SVGCircleElement | null;
}

export const labelLayer: { current: { root: HTMLDivElement; els: Map<string, LabelEls> } | null } = { current: null };

export function XrayLabelLayer({ vehicle }: { vehicle: Vehicle }) {
  const parts = vehicle.xray?.anatomy?.parts ?? [];
  const selected = useVehicleStore((s) => s.xrayPart);
  const root = React.useRef<HTMLDivElement>(null);
  const els = React.useRef(new Map<string, LabelEls>());
  React.useEffect(() => {
    if (!root.current) return;
    labelLayer.current = { root: root.current, els: els.current };
    return () => {
      labelLayer.current = null;
    };
  }, []);
  const slot = (id: string) => {
    let e = els.current.get(id);
    if (!e) {
      e = { pill: null, path: null, dot: null };
      els.current.set(id, e);
    }
    return e;
  };
  const line = '#1b1f27';
  return (
    <div ref={root} className="pointer-events-none absolute inset-0 z-[5] overflow-hidden">
      <svg className="absolute inset-0 h-full w-full" aria-hidden>
        {parts.map((p) => (
          <g key={p.id}>
            <path ref={(el) => void (slot(p.id).path = el)} fill="none" stroke={line} strokeWidth={selected === p.id ? 1.6 : 1} strokeOpacity={0} />
            <circle ref={(el) => void (slot(p.id).dot = el)} r={selected === p.id ? 4.2 : 3} fill="#fff" stroke={line} strokeWidth={1.2} opacity={0} />
          </g>
        ))}
      </svg>
      {parts.map((p, i) => {
        const on = selected === p.id;
        return (
          <button
            key={p.id}
            ref={(el) => void (slot(p.id).pill = el)}
            type="button"
            tabIndex={-1}
            onClick={() => useVehicleStore.setState((s) => (s.xrayPart === p.id ? { xrayPart: null } : { xrayPart: p.id, xraySystem: p.system }))}
            className={`pointer-events-auto absolute left-0 top-0 flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-[11px] font-medium opacity-0 transition-colors shadow-[0_6px_18px_-8px_rgba(20,24,32,0.35)] ring-1 backdrop-blur-md ${
              on ? 'bg-neutral-900 text-white ring-neutral-900' : 'bg-white/90 text-neutral-800 ring-black/[0.08] hover:bg-white'
            }`}
          >
            <span className={`tnum text-[9.5px] ${on ? 'opacity-70' : 'opacity-45'}`}>{String(i + 1).padStart(2, '0')}</span>
            {p.title}
          </button>
        );
      })}
    </div>
  );
}
