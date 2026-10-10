'use client';

import React from 'react';

/**
 * Scales a fixed-size surface (the phone at 378 x 778, the car's screen at 1280 x 800) to the box
 * it sits in, keeping its proportions. The surface is authored at its own size and laid out once; only
 * the transform changes, so its text and hit areas stay exact at any scale.
 */
export function Fit({
  w,
  h,
  className,
  children,
  max = 1,
}: {
  w: number;
  h: number;
  className?: string;
  children: React.ReactNode;
  /** the largest scale: devices are never enlarged past their own size */
  max?: number;
}) {
  const box = React.useRef<HTMLDivElement>(null);
  const [scale, setScale] = React.useState(0);

  React.useLayoutEffect(() => {
    const el = box.current;
    if (!el) return;
    const fit = () => setScale(Math.min(el.clientWidth / w, el.clientHeight / h, max));
    fit();
    const ro = new ResizeObserver(fit);
    ro.observe(el);
    return () => ro.disconnect();
  }, [w, h, max]);

  // only the surface itself takes pointer events: the empty margin round it lets a drag through to the scene
  return (
    <div ref={box} className={`pointer-events-none relative ${className ?? ''}`}>
      <div
        className="absolute left-1/2 top-1/2"
        style={{
          width: w,
          height: h,
          transform: `translate(-50%, -50%) scale(${scale})`,
          visibility: scale > 0 ? 'visible' : 'hidden',
          pointerEvents: 'auto',
        }}
      >
        {children}
      </div>
    </div>
  );
}
