'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { HY } from './theme';
import * as Ic from './icons';
import { Segmented } from './controls';
import { currentCarMode } from './Settings';

/**
 * Xiaomi Track Master (小米赛道大师), the SU7 Ultra's own app, after Xiaomi's
 * images of it: the delta to the best lap large on the left over the lap
 * list, the chassis with tyre pressures and temperatures in the middle, the
 * circuit on the right. Picking a track mode here sets the car's mode.
 *
 * The session is a demo: a simulated lap around an invented circuit, run at
 * 4x so a lap takes seconds. No real lap times or track data.
 */

// an invented circuit: a main straight, a long right-hander, esses, a hairpin
const CIRCUIT =
  'M60 200 L250 200 C300 200 322 172 302 146 L262 121 C236 106 236 86 258 80 L306 70 C338 64 342 38 314 34 L172 40 C142 43 132 62 150 80 C170 100 162 124 132 125 L84 126 C42 128 32 162 50 186 C54 195 57 200 60 200 Z';
const LAP_S = 63.5; // the demo lap's nominal time
const SPEED = 4; // demo playback rate

const SEED_LAPS = [67.91, 65.75, 67.26];

function lapStr(s: number): string {
  const m = Math.floor(s / 60);
  const r = s - m * 60;
  return `${String(m).padStart(2, '0')}:${r.toFixed(2).padStart(5, '0')}`;
}

export function TrackMaster({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  const { modeId, driveMode, setCarMode } = useVehicleStore();
  const track = (vehicle.cockpit.driveModes ?? []).filter((m) => m.group === 'track');
  const current = currentCarMode(vehicle, modeId, driveMode);
  const selected = current?.group === 'track' ? current.id : null;

  const [running, setRunning] = React.useState(false);
  const [laps, setLaps] = React.useState<number[]>(SEED_LAPS);
  const [t, setT] = React.useState(0);
  const [beep, setBeep] = React.useState<'on' | 'off'>('on');
  const pathRef = React.useRef<SVGPathElement>(null);
  const carRef = React.useRef<SVGGElement>(null);
  const sim = React.useRef({ t: 0, pace: 1.0, last: 0 });

  const best = Math.min(...laps);

  // playback: the marker moves every frame; the numbers update ten times a second
  React.useEffect(() => {
    if (!running) return;
    let raf = 0;
    let prev = performance.now();
    let tick = 0;
    const loop = (now: number) => {
      const dt = Math.min(0.1, (now - prev) / 1000) * SPEED;
      prev = now;
      const s = sim.current;
      s.t += dt;
      const lapTime = LAP_S * s.pace;
      if (s.t >= lapTime) {
        const done = Math.round(lapTime * 100) / 100;
        s.t -= lapTime;
        s.pace = 0.985 + Math.random() * 0.05;
        setLaps((l) => [...l.slice(-5), done]);
      }
      placeCar(s.t / (LAP_S * s.pace));
      tick += dt;
      if (tick > 0.4) {
        tick = 0;
        setT(s.t);
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [running]);

  const placeCar = (f: number) => {
    const p = pathRef.current;
    const g = carRef.current;
    if (!p || !g) return;
    const len = p.getTotalLength();
    const a = p.getPointAtLength((f % 1) * len);
    const b = p.getPointAtLength(((f % 1) * len + 2) % len);
    const deg = (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI;
    g.setAttribute('transform', `translate(${a.x} ${a.y}) rotate(${deg})`);
  };
  React.useEffect(() => placeCar(0.62), []);

  const frac = running ? t / (LAP_S * sim.current.pace) : 0.62;
  const delta = running ? t - best * frac : 0.38;
  const lapNo = laps.length + 1;
  const heat = Math.min(1, 0.45 + laps.length * 0.06);

  return (
    <div className="absolute inset-0 flex flex-col gap-3 px-5 pb-2 pt-1" style={{ color: HY.text }}>
      {/* header: app name, track modes, Boost */}
      <div className="flex items-center gap-4">
        <span className="flex items-center gap-2 text-[20px] font-semibold">
          <Ic.AppTrack />
          Track Master
        </span>
        <div className="ml-4 w-[520px]">
          <Segmented
            label="Track mode"
            value={selected}
            height={48}
            tone={HY.yellow}
            options={track.map((m) => ({
              id: m.id,
              label: m.label,
              sub: m.powerPs ? `${m.powerPs.toLocaleString('en-US')} PS` : 'RWD bias',
            }))}
            onChange={(id) => {
              const m = track.find((x) => x.id === id);
              if (m) setCarMode(m.id, m.model);
            }}
          />
        </div>
        <span
          className="ml-auto flex items-center gap-1.5 rounded-full px-4 py-2 text-[13px] font-bold tracking-wide"
          style={{ background: selected === 'qualifying' ? HY.yellow : HY.panel2, color: selected === 'qualifying' ? '#111' : HY.text3 }}
          title="The Boost button on the steering wheel, in Qualifying"
        >
          <Ic.Boost size={16} /> BOOST 1,548 PS
        </span>
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-[330px_1fr_390px] gap-3">
        {/* delta and laps */}
        <div className="flex flex-col rounded-[22px] p-5" style={{ background: HY.panel }}>
          <span className="text-[13px]" style={{ color: HY.text2 }}>Delta to best</span>
          <span className="tnum mt-1 text-[56px] font-light leading-none" style={{ color: delta > 0 ? '#ff6b5b' : HY.green }}>
            {delta > 0 ? '+' : '−'}{Math.abs(delta).toFixed(2)}
          </span>
          <DeltaTrace seed={laps.length} live={running ? delta : null} />
          <div className="mt-4 flex flex-col gap-3">
            <LapRow title="Current" lap={`Lap ${lapNo}`} time={running ? lapStr(t) : '00:56.32'} tone={HY.yellow} />
            <LapRow title="Last" lap={`Lap ${lapNo - 1}`} time={lapStr(laps[laps.length - 1])} />
            <LapRow title="Best" lap={`Lap ${laps.indexOf(best) + 1}`} time={lapStr(best)} />
          </div>
          <button
            type="button"
            onClick={() => {
              if (!running) sim.current = { t: 0, pace: 1.0, last: 0 };
              setRunning(!running);
            }}
            className="mt-auto h-[50px] rounded-[14px] text-[16px] font-semibold focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
            style={{ background: running ? HY.panel3 : HY.yellow, color: running ? HY.text : '#111' }}
          >
            {running ? 'End session' : 'Start demo session'}
          </button>
        </div>

        {/* chassis */}
        <div className="flex flex-col rounded-[22px] p-5" style={{ background: HY.panel }}>
          <Chassis heat={heat} kwh={variant.battery.capacityKwh} />
          <div className="mt-auto grid grid-cols-4 gap-2">
            {[
              ['Battery', 38 + heat * 18],
              ['Motor F', 44 + heat * 26],
              ['Motor RL', 46 + heat * 24],
              ['Motor RR', 46 + heat * 25],
            ].map(([l, v]) => (
              <div key={l as string} className="rounded-[14px] px-3 py-2.5" style={{ background: HY.panel2 }}>
                <div className="text-[11.5px]" style={{ color: HY.text3 }}>{l}</div>
                <div className="tnum text-[18px]">{(v as number).toFixed(1)}°C</div>
                <div className="mt-1.5 h-[3px] rounded-full bg-white/10">
                  <div className="h-full rounded-full" style={{ width: `${Math.min(100, ((v as number) - 20) * 1.5)}%`, background: (v as number) > 65 ? HY.orange : HY.green }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* circuit */}
        <div className="flex flex-col rounded-[22px] p-5" style={{ background: HY.panel }}>
          <svg viewBox="0 0 370 240" className="w-full" role="img" aria-label="Circuit map, demo circuit">
            <path d={CIRCUIT} fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="12" strokeLinejoin="round" />
            <path ref={pathRef} d={CIRCUIT} fill="none" stroke="#fff" strokeWidth="3.5" strokeLinejoin="round" />
            <path d="M150 192 L150 208" stroke={HY.yellow} strokeWidth="3" />
            <g ref={carRef}>
              <circle r="11" fill={HY.yellow} fillOpacity="0.25" />
              <path d="M8 0 L-6 -6 L-3 0 L-6 6Z" fill={HY.yellow} />
            </g>
          </svg>
          <div className="mt-2 flex items-center justify-between text-[13px]" style={{ color: HY.text2 }}>
            <span className="flex items-center gap-1.5"><Ic.Flag size={16} /> Demo circuit · 3.2 km</span>
            <span className="tnum">Lap {lapNo}</span>
          </div>
          <div className="mt-auto">
            <div className="mb-2 text-[13px]" style={{ color: HY.text2 }}>Lap time beep</div>
            <Segmented
              label="Lap time beep"
              value={beep}
              height={44}
              tone={HY.yellow}
              options={[{ id: 'on', label: 'On' }, { id: 'off', label: 'Off' }]}
              onChange={setBeep}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function LapRow({ title, lap, time, tone }: { title: string; lap: string; time: string; tone?: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="leading-tight">
        <span className="block text-[12px]" style={{ color: HY.text3 }}>{title}</span>
        <span className="block text-[13px]" style={{ color: HY.text2 }}>{lap}</span>
      </span>
      <span className="tnum text-[26px] font-light" style={{ color: tone ?? HY.text }}>{time}</span>
    </div>
  );
}

/** The delta history as bars: red where the lap was slower, green where faster. */
function DeltaTrace({ seed, live }: { seed: number; live: number | null }) {
  const bars = React.useMemo(() => {
    const out: number[] = [];
    let v = 0.2;
    for (let i = 0; i < 28; i++) {
      v += Math.sin(i * 1.7 + seed) * 0.12 + (i > 18 ? 0.04 : -0.01);
      out.push(Math.max(-0.5, Math.min(0.6, v)));
    }
    return out;
  }, [seed]);
  const vals = live === null ? bars : [...bars.slice(1), live];
  return (
    <div className="mt-4 flex h-[54px] items-center gap-[3px]" aria-hidden>
      {vals.map((v, i) => (
        <span
          key={i}
          className="w-[7px] rounded-[2px]"
          style={{
            height: `${Math.max(8, Math.abs(v) * 88)}%`,
            background: v > 0 ? '#e0443a' : HY.green,
            opacity: 0.35 + (i / vals.length) * 0.65,
          }}
        />
      ))}
    </div>
  );
}

/** The chassis from above: tyre pressures at the corners, tyre heat as bars. */
function Chassis({ heat, kwh }: { heat: number; kwh: number }) {
  const tyre = (x: number, y: number, bar: string, t: number, left: boolean) => (
    <g key={`${x}-${y}`}>
      <rect x={x} y={y} width="26" height="54" rx="7" fill="none" stroke="rgba(255,255,255,0.75)" strokeWidth="2" />
      <text x={left ? x - 12 : x + 38} y={y - 6} textAnchor={left ? 'end' : 'start'} fontSize="17" fill="#fff" fontFamily="inherit">{bar}</text>
      <text x={left ? x - 12 : x + 38} y={y + 12} textAnchor={left ? 'end' : 'start'} fontSize="11" fill="rgba(255,255,255,0.45)" fontFamily="inherit">bar</text>
      {Array.from({ length: 6 }).map((_, i) => (
        <rect
          key={i}
          x={left ? x - 18 : x + 38}
          y={y + 22 + i * 6}
          width="8"
          height="4"
          rx="1"
          fill={i >= 6 - Math.round(t * 6) ? (t > 0.75 ? HY.yellow : HY.green) : 'rgba(255,255,255,0.15)'}
        />
      ))}
    </g>
  );
  return (
    <svg viewBox="0 0 300 330" className="mx-auto h-[380px]" role="img" aria-label="Chassis, tyre pressures and temperatures">
      {/* the car's outline from above */}
      <path d="M150 18 C188 18 206 40 208 76 L212 250 C212 292 190 312 150 312 C110 312 88 292 88 250 L92 76 C94 40 112 18 150 18Z" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="2" />
      {/* battery pack and the three motors */}
      <rect x="112" y="96" width="76" height="140" rx="8" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.3)" />
      <text x="150" y="170" textAnchor="middle" fontSize="11" fill="rgba(255,255,255,0.45)" fontFamily="inherit">{kwh} kWh</text>
      <rect x="132" y="52" width="36" height="26" rx="5" fill="none" stroke="rgba(255,255,255,0.45)" />
      <rect x="116" y="258" width="30" height="26" rx="5" fill="none" stroke="rgba(255,255,255,0.45)" />
      <rect x="154" y="258" width="30" height="26" rx="5" fill="none" stroke="rgba(255,255,255,0.45)" />
      <path d="M100 66 H132 M168 66 H200 M100 272 H116 M184 272 H200" stroke="rgba(255,255,255,0.3)" />
      {tyre(70, 38, '2.9', heat * 0.9, true)}
      {tyre(204, 38, '2.9', heat * 0.95, false)}
      {tyre(70, 246, '2.8', heat, true)}
      {tyre(204, 246, '2.8', heat * 1.05, false)}
    </svg>
  );
}
