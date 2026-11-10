'use client';

import React from 'react';
import type { Vehicle, XrayBasis, XrayPart, XraySystem } from '@/data/vehicles/schema';
import { clipOf, CLIPS, playClip, stopClip } from '@/lib/xray/clips';
import { xrayOf } from '@/lib/xray/rig';
import { useVehicleStore } from '@/store/vehicle-store';
import { FOCUS, GLASS, PANEL } from './Chrome';

export const XRAY_COLUMN_W = 336;

const SYSTEMS: { id: XraySystem; label: string }[] = [
  { id: 'battery', label: 'Battery' },
  { id: 'drive', label: 'Motors' },
  { id: 'chassis', label: 'Chassis' },
  { id: 'suspension', label: 'Suspension' },
  { id: 'steering', label: 'Steering' },
  { id: 'brakes', label: 'Brakes and wheels' },
];

const BASIS: Record<XrayBasis, { label: string; tone: string }> = {
  published: { label: 'Figures published', tone: 'bg-emerald-500/12 text-emerald-800' },
  reported: { label: 'Figures reported', tone: 'bg-amber-500/14 text-amber-800' },
  illustrative: { label: 'Our drawing', tone: 'bg-neutral-900/8 text-neutral-600' },
};

/** The level the viewer is showing now (it eases to the store's), for the knob; re-renders only while it moves. */
function useShownLevel(vehicle: Vehicle): number {
  const rig = xrayOf(vehicle);
  const target = useVehicleStore((s) => s.xrayLevel);
  const [shown, setShown] = React.useState(rig.level);
  React.useEffect(() => {
    let raf = 0;
    let last = NaN;
    const loop = () => {
      if (rig.level !== last) {
        last = rig.level;
        setShown(rig.level);
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [rig, target]);
  return shown;
}

/** Re-render when the rig changes (a clip starts or stops). */
function useRigVersion(vehicle: Vehicle) {
  const rig = xrayOf(vehicle);
  return React.useSyncExternalStore(rig.subscribe, rig.getVersion, () => 0);
}

/**
 * The dock of the X-ray tab: the level, from solid through see-through to exploded, as a slider with a stop at each (a click on
 * a stop flies there; dragging follows the finger), the blueprint switch, and the chips of the systems the exploded view takes apart.
 */
export function XrayTools({ vehicle }: { vehicle: Vehicle }) {
  const anatomy = vehicle.xray?.anatomy;
  const level = useVehicleStore((s) => s.xrayLevel);
  const setLevel = useVehicleStore((s) => s.setXrayLevel);
  const blueprint = useVehicleStore((s) => s.xrayBlueprint);
  const setBlueprint = useVehicleStore((s) => s.setXrayBlueprint);
  const system = useVehicleStore((s) => s.xraySystem);
  const setSystem = useVehicleStore((s) => s.setXraySystem);
  const shown = useShownLevel(vehicle);
  const max = anatomy ? 2 : 1;
  const stops: { v: number; label: string; off?: string }[] = [
    { v: 0, label: 'Solid' },
    { v: 1, label: 'X-ray' },
    { v: 2, label: 'Exploded', off: anatomy ? undefined : 'The exploded view is not built for this car yet' },
  ];
  const systems = SYSTEMS.filter((s) => anatomy?.parts.some((p) => p.system === s.id));
  return (
    <div className="pointer-events-none flex w-full max-w-[640px] flex-col items-center gap-2">
      {anatomy && shown > 0.9 && (
        <div role="group" aria-label="Systems" className={`pointer-events-auto hy-scroll flex max-w-full gap-1 overflow-x-auto rounded-full p-1 ${GLASS}`}>
          <button
            type="button"
            aria-pressed={system === null}
            onClick={() => setSystem(null)}
            className={`shrink-0 rounded-full px-3 py-1.5 text-[11.5px] font-medium transition-colors ${FOCUS} ${system === null ? 'bg-neutral-900 text-white' : 'text-neutral-600 hover:text-neutral-900'}`}
          >
            All
          </button>
          {systems.map((s) => (
            <button
              key={s.id}
              type="button"
              aria-pressed={system === s.id}
              onClick={() => setSystem(system === s.id ? null : s.id)}
              className={`shrink-0 rounded-full px-3 py-1.5 text-[11.5px] font-medium transition-colors ${FOCUS} ${system === s.id ? 'bg-neutral-900 text-white' : 'text-neutral-600 hover:text-neutral-900'}`}
            >
              {s.label}
            </button>
          ))}
        </div>
      )}
      <div className="pointer-events-auto flex w-full items-center gap-3">
        <div className={`flex min-w-0 flex-1 flex-col gap-1 rounded-2xl px-4 pb-2 pt-2.5 ${GLASS}`}>
          <input
            type="range"
            min={0}
            max={max}
            step={0.01}
            value={Math.min(max, shown)}
            aria-label="Solid, X-ray or exploded"
            aria-valuetext={shown < 0.5 ? 'Solid' : shown < 1.5 ? 'X-ray' : 'Exploded'}
            onChange={(e) => setLevel(Number(e.target.value), true)}
            onPointerUp={() => setLevel(useVehicleStore.getState().xrayLevel, false)}
            onKeyUp={() => setLevel(useVehicleStore.getState().xrayLevel, false)}
            className={`h-1.5 w-full cursor-pointer accent-neutral-900 ${FOCUS}`}
          />
          <div className="relative flex justify-between text-[11px] font-medium">
            {stops.map((s) => (
              <button
                key={s.v}
                type="button"
                disabled={Boolean(s.off)}
                title={s.off}
                aria-pressed={Math.abs(level - s.v) < 0.25}
                onClick={() => setLevel(s.v, false)}
                className={`${FOCUS} rounded px-1 py-0.5 transition-colors disabled:opacity-35 ${Math.abs(shown - s.v) < 0.25 ? 'text-neutral-900' : 'text-neutral-500 hover:text-neutral-900'}`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
        <button
          type="button"
          aria-pressed={blueprint}
          onClick={() => setBlueprint(!blueprint)}
          title="Blueprint: the car as an engineering drawing"
          className={`flex shrink-0 items-center gap-2 rounded-full px-4 py-2.5 text-[12px] font-medium transition-colors ${FOCUS} ${blueprint ? 'bg-[#123a66] text-white shadow-sm' : `text-neutral-700 ${GLASS}`}`}
        >
          <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.2" aria-hidden>
            <rect x="1.5" y="1.5" width="13" height="13" rx="1" />
            <path d="M1.5 6h13M1.5 10.5h13M6 1.5v13M10.5 1.5v13" strokeWidth="0.7" />
          </svg>
          Blueprint
        </button>
      </div>
    </div>
  );
}

function Facts({ part }: { part: XrayPart }) {
  if (!part.facts?.length) return null;
  return (
    <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5 text-[12px]">
      {part.facts.map((f) => (
        <React.Fragment key={f.label}>
          <dt className="text-neutral-500">{f.label}</dt>
          <dd className="tnum text-right font-medium text-neutral-900">{f.value}</dd>
        </React.Fragment>
      ))}
    </dl>
  );
}

function PartCard({ vehicle, part, wide }: { vehicle: Vehicle; part: XrayPart; wide: boolean }) {
  useRigVersion(vehicle);
  const rig = xrayOf(vehicle);
  const setPart = useVehicleStore((s) => s.setXrayPart);
  const clip = clipOf(part.clip);
  const playing = Boolean(clip && rig.clip?.id === clip.id);
  const basis = BASIS[part.basis];
  return (
    <div>
      <button type="button" onClick={() => setPart(null)} className={`mb-2 text-[11.5px] text-neutral-500 hover:text-neutral-900 ${FOCUS}`}>
        ← All parts
      </button>
      {part.image && (
        <div className={`mb-3 aspect-[3/2] w-full overflow-hidden rounded-2xl ${wide ? 'max-h-[190px]' : 'max-h-[120px]'} bg-gradient-to-br from-neutral-100 to-neutral-200/70 ring-1 ring-black/[0.04]`}>
          {/* a render of our own model, from Blender: the card's picture, not the maker's */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={part.image} alt={`${part.title}: a rendering of our model of it`} width={640} height={420} loading="lazy" decoding="async" draggable={false} className="h-full w-full object-contain" />
        </div>
      )}
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-[16px] font-semibold leading-tight text-neutral-900">{part.title}</h3>
        <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${basis.tone}`}>{basis.label}</span>
      </div>
      <p className="mt-2 text-[12.5px] leading-relaxed text-neutral-700">{part.text}</p>
      <Facts part={part} />
      {part.source && (
        <a href={part.source.url} target="_blank" rel="noreferrer" className={`mt-3 block text-[11px] text-neutral-500 underline decoration-neutral-300 underline-offset-2 hover:text-neutral-900 ${FOCUS}`}>
          {part.source.label}
        </a>
      )}
      {clip && (
        <div className="mt-4 rounded-xl bg-neutral-900/[0.04] p-3">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-neutral-500">Short clip</div>
              <div className="truncate text-[12.5px] font-medium text-neutral-900">{clip.title}</div>
            </div>
            <button
              type="button"
              onClick={() => (playing ? stopClip(vehicle) : playClip(vehicle, clip.id))}
              className={`shrink-0 rounded-full bg-neutral-900 px-4 py-1.5 text-[12px] font-medium text-white ${FOCUS}`}
            >
              {playing ? 'Stop' : 'Play'}
            </button>
          </div>
          {playing && <ClipCaption vehicle={vehicle} id={clip.id} />}
        </div>
      )}
    </div>
  );
}

/** The caption and the progress of the clip that is playing, read on the wall clock. */
function ClipCaption({ vehicle, id }: { vehicle: Vehicle; id: string }) {
  const rig = xrayOf(vehicle);
  const [t, setT] = React.useState(0);
  React.useEffect(() => {
    let raf = 0;
    const loop = () => {
      setT(rig.clipTime(performance.now()) ?? 0);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [rig]);
  const def = CLIPS[id];
  return (
    <div className="mt-2.5">
      <p className="text-[12px] leading-snug text-neutral-700" aria-live="polite">{def.caption(t)}</p>
      <div className="mt-2 h-[3px] overflow-hidden rounded-full bg-neutral-900/10">
        <div className="h-full rounded-full bg-neutral-900" style={{ width: `${(100 * t) / def.dur}%` }} />
      </div>
    </div>
  );
}

function PartList({ vehicle }: { vehicle: Vehicle }) {
  const anatomy = vehicle.xray!.anatomy!;
  const system = useVehicleStore((s) => s.xraySystem);
  const groups = SYSTEMS.map((s) => ({ ...s, parts: anatomy.parts.filter((p) => p.system === s.id) })).filter((g) => g.parts.length && (!system || g.id === system));
  return (
    <div>
      <p className="text-[12.5px] leading-relaxed text-neutral-700">
        Slide to X-ray to see the hardware through the body, then on to Exploded to take it apart. Pick a part for what it does, and for a short clip of it working.
      </p>
      <div className="mt-3 space-y-3">
        {groups.map((g) => (
          <div key={g.id}>
            <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-neutral-500">{g.label}</div>
            <ul className="mt-1 space-y-0.5">
              {g.parts.map((p) => (
                <li key={p.id}>
                  <button
                    type="button"
                    onClick={() => {
                      useVehicleStore.setState({ xrayPart: p.id, xraySystem: p.system });
                    }}
                    className={`flex w-full items-center justify-between gap-2 rounded-lg px-2 py-1.5 text-left text-[12.5px] text-neutral-800 transition-colors hover:bg-neutral-900/[0.05] ${FOCUS}`}
                  >
                    <span className="truncate">{p.title}</span>
                    {p.clip && <span className="shrink-0 text-[10px] text-neutral-400">▶ clip</span>}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

/** The column at the right of a wide window (a sheet over the car on a narrow one): the parts, and the card of the one picked. */
export function XrayCard({ vehicle, wide }: { vehicle: Vehicle; wide: boolean }) {
  const anatomy = vehicle.xray?.anatomy;
  const partId = useVehicleStore((s) => s.xrayPart);
  const level = useVehicleStore((s) => s.xrayLevel);
  if (!anatomy) return null;
  const part = anatomy.parts.find((p) => p.id === partId) ?? null;
  // a narrow window has no room for a list beside the car: the card opens only for a picked part
  if (!wide && !part) return null;
  return (
    <aside
      className={`pointer-events-auto flex flex-col overflow-hidden rounded-3xl ${PANEL} ${wide ? 'h-full max-h-full' : 'max-h-[42vh]'}`}
      style={wide ? { width: XRAY_COLUMN_W } : undefined}
      aria-label="Parts"
    >
      <div className="hy-scroll min-h-0 flex-1 overflow-y-auto px-5 pb-3 pt-5">
        {part ? <PartCard vehicle={vehicle} part={part} wide={wide} /> : <PartList vehicle={vehicle} />}
        {level < 1 && <p className="mt-4 text-[11.5px] text-neutral-500">The parts show from X-ray on.</p>}
      </div>
      <p className="border-t border-black/[0.06] px-5 py-3 text-[10.5px] leading-snug text-neutral-500">{anatomy.note}</p>
    </aside>
  );
}

/**
 * The drawing's sheet, in blueprint mode: a thin frame round the picture and a title block in the corner, with the dimensions the
 * maker publishes, as on an engineering drawing. Over the canvas, under the menu and the panels.
 */
export function XrayBlueprintSheet({ vehicle }: { vehicle: Vehicle }) {
  const on = useVehicleStore((s) => s.xrayBlueprint);
  const level = useVehicleStore((s) => s.xrayLevel);
  if (!on) return null;
  const d = vehicle.dimensions;
  const what = level < 0.5 ? 'GENERAL ARRANGEMENT' : level < 1.5 ? 'GENERAL ARRANGEMENT, BODY SEEN THROUGH' : 'EXPLODED ASSEMBLY';
  const rows: [string, string][] = [
    ['WHEELBASE', `${d.wheelbaseMm.toLocaleString('en-US')} mm`],
    ['LENGTH', `${d.lengthMm.toLocaleString('en-US')} mm`],
    ['WIDTH', `${d.widthMm.toLocaleString('en-US')} mm`],
    ['HEIGHT', `${d.heightMm.toLocaleString('en-US')} mm`],
  ];
  return (
    <div className="pointer-events-none absolute inset-0 z-[4]" aria-hidden>
      <div className="absolute inset-2.5 border border-[#9bd1ff]/35" />
      <div className="absolute bottom-[18px] left-[18px] hidden w-[272px] border border-[#9bd1ff]/55 bg-[#0c2d52]/80 font-mono text-[#dff0ff] backdrop-blur-sm xl:block">
        <div className="border-b border-[#9bd1ff]/40 px-3 py-2">
          <div className="text-[13px] font-semibold tracking-[0.12em]">{`${vehicle.brand} ${vehicle.model}`.toUpperCase()}</div>
          <div className="mt-0.5 text-[10px] tracking-[0.1em] text-[#9bd1ff]">{what}</div>
        </div>
        <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 border-b border-[#9bd1ff]/40 px-3 py-2 text-[10px] tracking-[0.06em]">
          {rows.map(([k, v]) => (
            <React.Fragment key={k}>
              <span className="text-[#9bd1ff]">{k}</span>
              <span className="text-right">{v}</span>
            </React.Fragment>
          ))}
        </div>
        <div className="px-3 py-1.5 text-[9px] tracking-[0.1em] text-[#9bd1ff]">NOT TO SCALE · SHEET 1 OF 1 · PARTS ILLUSTRATIVE</div>
      </div>
    </div>
  );
}
