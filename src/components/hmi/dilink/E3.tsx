'use client';

import React from 'react';
import type { Vehicle } from '@/data/vehicles/schema';
import { startDemo, pauseDemo } from '@/lib/tech/actions';
import { CHASSIS, chassisAction, isChassisDriver } from '@/lib/tech/chassis';
import { useTechClock } from '@/lib/tech/clock';
import { useChassisReadout, useRuntime } from '@/lib/tech/session';
import type { Pivot } from '@/lib/tech/street';
import { useVehicleStore } from '@/store/vehicle-store';
import { DL } from './theme';
import * as Ic from './icons';
import { Glow, Segment } from './Pages';

/**
 * The e³ platform page of the Denza Z9's screen, in DiLink's own look (the light stage and the blue controls of the camera
 * and driving pages), for the three manoeuvres the platform is known for: the crab walk, the compass turn and e³ parking
 * (BYD China, Xchuxing, km77, The Autopian: docs/tech-showcase.md section 14). The car stands seen from above with its four
 * wheels turned as the demonstration turns them; the big figure is the numeric indicator km77 says the centre screen shows
 * in the crab walk (how far the front wheels are turned), and the manoeuvre's other figure in the other two; the compass
 * turn's choices (the wheel to pivot about, how far) are the screen's, as The Autopian describes parking; one button runs it.
 * The page itself is drawn for the showroom: the maker's screens for these functions are not photographed.
 */

const WHEELS = ['FL', 'FR', 'RL', 'RR'] as const;
const LABEL = { FL: 'Front left', FR: 'Front right', RL: 'Rear left', RR: 'Rear right' } as const;
const PIVOTS: Pivot[] = ['FL', 'FR'];
const ANGLES = [90, 180, 360];

/** The platform's five signature functions (BYD China, 22 August 2024); the showroom demonstrates three. */
const FUNCTIONS: { label: string; driver?: string }[] = [
  { label: 'Crab walk', driver: 'crab' },
  { label: 'Compass turn', driver: 'compass' },
  { label: 'e³ parking', driver: 'e3park' },
  { label: 'Extreme steering' },
  { label: 'Low-grip stabilisation' },
];

const signed = (a: number) => {
  const r = Math.round(a * 10) / 10;
  return (r > 0 ? '+' : r < 0 ? '−' : '') + Math.abs(r).toFixed(1);
};

export function E3Page({ vehicle }: { vehicle: Vehicle }) {
  const runtime = useRuntime();
  const readout = useChassisReadout();
  const clock = useTechClock();
  const chosenDemo = useVehicleStore((s) => s.techDemoId);
  const setTechDemo = useVehicleStore((s) => s.setTechDemo);
  const pivot = useVehicleStore((s) => s.compassPivot);
  const angle = useVehicleStore((s) => s.compassAngle);
  const setCompass = useVehicleStore((s) => s.setCompass);
  const available = useVehicleStore((s) => s.techAvailable);

  const demos = (vehicle.tech ?? []).filter((d) => isChassisDriver(d.driver));
  const spec = demos.find((d) => d.id === (runtime?.chassis ? runtime.demoId : chosenDemo)) ?? demos[0];
  const copy = spec ? CHASSIS[spec.driver] : undefined;
  if (!spec || !copy) return null;

  const action = chassisAction(spec.driver, clock, () => startDemo(spec.id, 'dashboard'), pauseDemo);
  const steer = readout?.steer ?? [0, 0, 0, 0];
  // the crab angle is the angle the front wheels are set to (held at the end of the slide); the others show how far the car has turned
  const figure = spec.driver === 'crab' ? Math.abs(steer[0]) : Math.abs(readout?.turned ?? 0);
  const held = readout?.held ?? null;
  const next = runtime?.chassis?.facts.pivot ?? (spec.driver === 'compass' ? pivot : spec.driver === 'e3park' ? 'FL' : null);

  return (
    <div className="absolute inset-0">
      <Glow x="30%" y="55%" c="rgba(40,110,255,0.22)" />

      {/* the car from above, on DiLink's light stage */}
      <div className="absolute overflow-hidden rounded-[10px]" style={{ left: 22, top: 54, width: 600, bottom: 14, background: 'linear-gradient(180deg,#e7edf6,#cfd9e8)' }}>
        <div className="absolute left-[18px] top-[14px] flex items-center gap-[10px]">
          <span className="flex h-[34px] w-[34px] items-center justify-center rounded-[9px] text-[16px] font-bold" style={{ background: 'linear-gradient(145deg,#e0243c,#a30f2a)', color: '#fff' }}>
            e³
          </span>
          <span className="text-[16px]" style={{ color: '#34405a' }}>{copy.title}</span>
        </div>
        <TopView vehicle={vehicle} steer={steer} travel={readout?.travel ?? null} held={held} next={next} />
        <p className="absolute bottom-[14px] left-[22px] right-[22px] text-[13px] leading-snug" style={{ color: '#52607c' }}>
          {copy.hint}
        </p>
      </div>

      <div className="absolute flex flex-col gap-[10px]" style={{ left: 640, right: 22, top: 54, bottom: 14 }}>
        <div role="tablist" aria-label="e³ manoeuvre" className="flex overflow-hidden rounded-[8px]" style={{ background: 'rgba(255,255,255,0.10)' }}>
          {demos.map((d) => {
            const on = d.id === spec.id;
            return (
              <button
                key={d.id}
                role="tab"
                aria-selected={on}
                type="button"
                onClick={() => setTechDemo(d.id)}
                className="h-[50px] flex-1 px-2 text-[16px] focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
                style={{ background: on ? 'linear-gradient(180deg, rgba(61,139,255,0.6), rgba(61,139,255,0.32))' : 'transparent', color: DL.text }}
              >
                {d.title}
              </button>
            );
          })}
        </div>

        <div className="flex items-end justify-between rounded-[8px] px-[22px] py-[16px]" style={{ background: DL.card }}>
          <div>
            <div className="text-[15px]" style={{ color: DL.text2 }}>{copy.figure}</div>
            <div className="tnum mt-[2px] flex items-baseline gap-[4px]">
              <span className="text-[84px] font-light leading-none">{Math.round(figure)}</span>
              <span className="text-[30px]" style={{ color: DL.text2 }}>°</span>
            </div>
          </div>
          <div className="text-right">
            <div className="tnum flex items-baseline justify-end gap-[6px]">
              <span className="text-[34px] font-light leading-none">{Math.round(readout?.speed ?? 0)}</span>
              <span className="text-[14px]" style={{ color: DL.text2 }}>km/h</span>
            </div>
            <div className="mt-[4px] text-[12px]" style={{ color: DL.text3 }}>fastest wheel</div>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-[10px]">
          {WHEELS.map((k, i) => (
            <div key={k} className="rounded-[8px] px-[14px] py-[10px]" style={{ background: held === k ? DL.cardOn : DL.card, boxShadow: held === k ? 'inset 0 0 0 1px rgba(140,190,255,0.7)' : undefined }}>
              <div className="text-[12px]" style={{ color: DL.text3 }}>{LABEL[k]}</div>
              <div className="tnum mt-[2px] text-[24px] font-light">{signed(steer[i])}°</div>
              {held === k && <div className="text-[11px]" style={{ color: DL.accent }}>held</div>}
            </div>
          ))}
        </div>

        {spec.driver === 'compass' && (
          <div className="flex flex-col gap-[10px] rounded-[8px] px-[18px] py-[14px]" style={{ background: DL.card }}>
            <div className="flex items-center justify-between gap-[12px]">
              <span className="text-[15px]">Pivot about</span>
              <Segment
                options={['Left front wheel', 'Right front wheel']}
                value={PIVOTS.indexOf(pivot)}
                onPick={(i) => setCompass(PIVOTS[i], angle)}
                minW={150}
              />
            </div>
            <div className="flex items-center justify-between gap-[12px]">
              <span className="text-[15px]">Turn through</span>
              <Segment options={ANGLES.map((a) => `${a}°`)} value={Math.max(0, ANGLES.indexOf(angle))} onPick={(i) => setCompass(pivot, ANGLES[i])} minW={96} />
            </div>
          </div>
        )}
        {spec.driver === 'crab' && (
          <div className="flex items-start gap-[12px] rounded-[8px] px-[18px] py-[14px] text-[14px] leading-snug" style={{ background: DL.card, color: DL.text2 }}>
            <Ic.Wheel size={26} />
            <span>Front wheels up to 15°, rear wheels up to ±10°, below 20 km/h. The figure is the angle the front wheels are set to.</span>
          </div>
        )}
        {spec.driver === 'e3park' && (
          <div className="flex items-start gap-[12px] rounded-[8px] px-[18px] py-[14px] text-[14px] leading-snug" style={{ background: DL.card, color: DL.text2 }}>
            <Ic.Wheel size={26} />
            <span>Pull the nose into the gap, then pivot about the left front wheel: the tail swings in and the car ends parallel to the kerb.</span>
          </div>
        )}

        <div className="mt-auto rounded-[8px] px-[18px] py-[12px]" style={{ background: DL.card }}>
          <div className="text-[12px]" style={{ color: DL.text3 }}>e³ platform · five signature functions</div>
          <div className="mt-[8px] flex flex-wrap gap-[8px]">
            {FUNCTIONS.map((f) => {
              const demo = f.driver ? demos.find((d) => d.driver === f.driver) : undefined;
              const on = demo?.id === spec.id;
              const common = 'rounded-[6px] px-[12px] py-[6px] text-[14px] focus:outline-none';
              return demo ? (
                <button
                  key={f.label}
                  type="button"
                  aria-pressed={on}
                  onClick={() => setTechDemo(demo.id)}
                  className={`${common} focus-visible:ring-2 focus-visible:ring-white/60`}
                  style={{ background: on ? 'linear-gradient(180deg, rgba(61,139,255,0.6), rgba(61,139,255,0.32))' : 'rgba(255,255,255,0.10)', color: DL.text }}
                >
                  {f.label}
                </button>
              ) : (
                <span key={f.label} className={common} style={{ background: 'rgba(255,255,255,0.05)', color: DL.text3 }} title="Not part of the showroom demonstration">
                  {f.label}
                </span>
              );
            })}
          </div>
        </div>

        <button
          type="button"
          disabled={!available}
          onClick={action.run}
          className="flex h-[68px] items-center justify-center rounded-[10px] text-[22px] font-medium transition-opacity focus:outline-none focus-visible:ring-2 focus-visible:ring-white/70 disabled:opacity-40"
          style={{ background: 'linear-gradient(180deg, rgba(61,139,255,0.95), rgba(36,100,225,0.95))', color: '#fff', boxShadow: '0 8px 22px rgba(30,90,220,0.35)' }}
        >
          {action.label}
        </button>
        <p className="text-center text-[11px]" style={{ color: DL.text3 }}>
          Drawn for this showroom from the maker’s published figures; the car’s own e³ screens are not photographed.
        </p>
      </div>
    </div>
  );
}

/** The car from above, nose up, with its wheels turned as the demonstration turns them. */
function TopView({
  vehicle,
  steer,
  travel,
  held,
  next,
}: {
  vehicle: Vehicle;
  steer: readonly number[];
  /** the way it travels against the way it points, degrees to the left; null when it is not on a straight line */
  travel: number | null;
  /** the wheel held still now */
  held: Pivot | null;
  /** the wheel the manoeuvre will pivot about, before it is held */
  next: Pivot | null;
}) {
  const d = vehicle.dimensions;
  const W = 600;
  const H = 632;
  const length = d.lengthMm / 1000;
  const S = 556 / length; // px per metre
  const cx = W / 2;
  const top = 58;
  const imgH = length * S;
  const imgW = imgH * (420 / 990);
  // the wheelbase's middle sits a little ahead of the middle of the car's length
  const cy = top + imgH * 0.49;
  const wb = (d.wheelbaseMm / 1000) * S;
  const track = (d.widthMm / 1000 - 0.3) * S;
  const wheelW = 0.27 * S;
  const wheelL = 0.72 * S;
  const pos = {
    FL: [cx - track / 2, cy - wb / 2],
    FR: [cx + track / 2, cy - wb / 2],
    RL: [cx - track / 2, cy + wb / 2],
    RR: [cx + track / 2, cy + wb / 2],
  } as const;
  const idx = { FL: 0, FR: 1, RL: 2, RR: 3 } as const;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="absolute inset-0 h-full w-full" role="img" aria-label="The car seen from above, with its wheels turned">
      {/* the way it travels */}
      {travel !== null && (
        <g transform={`translate(${cx} ${cy}) rotate(${-travel})`}>
          <line x1={0} y1={-imgH * 0.34} x2={0} y2={-imgH * 0.52} stroke={DL.accent} strokeWidth={6} strokeDasharray="12 9" strokeLinecap="round" />
          <path d={`M -16 ${-imgH * 0.52 + 8} L 0 ${-imgH * 0.52 - 16} L 16 ${-imgH * 0.52 + 8} Z`} fill={DL.accent} />
        </g>
      )}
      <image href={`/hmi/${vehicle.slug}/car-top.webp`} x={cx - imgW / 2} y={top} width={imgW} height={imgH} />
      {(['FL', 'FR', 'RL', 'RR'] as const).map((k) => {
        const [x, y] = pos[k];
        const on = held === k;
        const picked = !on && next === k;
        return (
          <g key={k} transform={`translate(${x} ${y}) rotate(${-steer[idx[k]]})`}>
            <rect x={-wheelW / 2} y={-wheelL / 2} width={wheelW} height={wheelL} rx={7} fill={on ? DL.accent : '#0b1020'} fillOpacity={on ? 0.9 : 0.78} stroke={DL.accent} strokeWidth={2.5} />
            {(on || picked) && <circle r={wheelW * 1.7} fill="none" stroke={DL.accent} strokeWidth={2.5} strokeDasharray="5 6" />}
          </g>
        );
      })}
    </svg>
  );
}
