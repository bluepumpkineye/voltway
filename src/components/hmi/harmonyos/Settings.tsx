'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore, type SettingsPage } from '@/store/vehicle-store';
import { effectiveRange } from '@/lib/performance';
import * as Ic from './icons';
import { useHa, BAR_H, STATUS_H, type HaTheme } from './theme';
import { Wallpaper, useHaLocal } from './shared';
import { useWallpaper } from './Desktop';

/* ---------------------------------------------------------------- the menu */

const MENU: { id: SettingsPage; label: string; icon: React.ReactNode }[] = [
  { id: 'vehicle', label: 'Vehicle control', icon: <Ic.MenuVehicle size={27} /> },
  { id: 'lights', label: 'Lights', icon: <Ic.MenuLights size={27} /> },
  { id: 'energy', label: 'Energy', icon: <Ic.MenuEnergy size={27} /> },
  { id: 'driving', label: 'Driving', icon: <Ic.MenuDriving size={27} /> },
  { id: 'assist', label: 'Assisted driving', icon: <Ic.MenuAssist size={27} /> },
  { id: 'status', label: 'Vehicle status', icon: <Ic.MenuStatus size={27} /> },
  { id: 'scenes', label: 'Smart scenes', icon: <Ic.MenuScenes size={27} /> },
  { id: 'personalise', label: 'Desktop & personalisation', icon: <Ic.MenuPersonal size={27} /> },
  { id: 'display', label: 'Display', icon: <Ic.MenuDisplay size={27} /> },
  { id: 'connection', label: 'Connections', icon: <Ic.MenuLink size={27} /> },
  { id: 'sound', label: 'Sound', icon: <Ic.MenuSound size={27} /> },
  { id: 'assistant', label: 'Smart assistant', icon: <Ic.MenuAssistant size={27} /> },
  { id: 'system', label: 'System', icon: <Ic.MenuSystem size={27} /> },
];

/** The store's page ids the HyperOS skin uses, onto this menu. */
const ALIAS: Partial<Record<SettingsPage, SettingsPage>> = { doors: 'vehicle', charging: 'energy' };

/**
 * HarmonyOS Settings: the menu down the left in the car's order, a page beside
 * it. A page is a picture of the car (or the cabin) and pale cards of switches,
 * selectors and links; a link says what it would open, as the showroom has no
 * more screens than these.
 */
export function SettingsApp({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  const t = useHa();
  const { settingsPage, openSettings } = useVehicleStore();
  const page = ALIAS[settingsPage] ?? settingsPage;
  const ref = React.useRef<HTMLDivElement>(null);
  React.useEffect(() => {
    ref.current?.scrollTo({ top: 0 });
  }, [page]);

  const Page = (
    {
      vehicle: VehiclePage,
      lights: LightsPage,
      energy: EnergyPage,
      driving: DrivingPage,
      assist: AssistPage,
      status: StatusPage,
      scenes: ScenesPage,
      personalise: PersonalisePage,
      display: DisplayPage,
      connection: ConnectionPage,
      sound: SoundPage,
      assistant: AssistantPage,
      system: SystemPage,
    } as Partial<Record<SettingsPage, React.ComponentType<{ vehicle: Vehicle; variant: Variant }>>>
  )[page] ?? VehiclePage;

  return (
    <div className="absolute inset-0" style={{ background: t.bg, color: t.text, paddingTop: STATUS_H }}>
      <nav className="absolute flex flex-col" style={{ left: 24, top: STATUS_H, width: 316, bottom: BAR_H }} aria-label="Settings">
        <h2 className="mb-[10px] ml-[28px] mt-[2px] text-[30px] font-medium leading-none">Settings</h2>
        <div className="min-h-0 flex-1 overflow-y-auto pb-4" style={{ scrollbarWidth: 'none' }}>
          {MENU.map((m) => {
            const on = m.id === page;
            return (
              <button
                key={m.id}
                type="button"
                aria-current={on ? 'page' : undefined}
                onClick={() => openSettings(m.id)}
                className="flex h-[72px] w-full items-center gap-[22px] rounded-[26px] px-[28px] text-left text-[20px] outline-none transition-colors focus-visible:ring-2 focus-visible:ring-[#4a74ff]"
                style={{ background: on ? t.segOn : 'transparent', color: on ? t.tileOnText : t.text, opacity: on ? 1 : 0.9 }}
              >
                <span className="shrink-0">{m.icon}</span>
                <span className="truncate">{m.label}</span>
              </button>
            );
          })}
        </div>
      </nav>
      <div ref={ref} className="absolute overflow-y-auto pb-6 pr-[28px]" style={{ left: 372, right: 0, top: STATUS_H - 8, bottom: BAR_H, scrollbarWidth: 'none' }}>
        <Page vehicle={vehicle} variant={variant} />
      </div>
    </div>
  );
}

/* ----------------------------------------------------------------- controls */

function Switch({ on }: { on: boolean }) {
  const t = useHa();
  return (
    <span className="relative inline-block h-[30px] w-[54px] shrink-0 rounded-full transition-colors" style={{ background: on ? t.blue : t.tone === 'dark' ? 'rgba(255,255,255,0.22)' : 'rgba(21,22,26,0.14)' }}>
      <span className="absolute top-[3px] h-[24px] w-[24px] rounded-full bg-white transition-all" style={{ left: on ? 27 : 3, boxShadow: '0 1px 4px rgba(0,0,0,0.3)' }} />
    </span>
  );
}

/** A card with a switch: its title, a line under it and (optionally) an info mark. */
function ToggleCard({
  title, sub, on, onChange, info, span2,
}: {
  title: string;
  sub?: string;
  on: boolean;
  onChange: (v: boolean) => void;
  info?: boolean;
  span2?: boolean;
}) {
  const t = useHa();
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      onClick={() => onChange(!on)}
      className="flex min-h-[78px] items-center gap-[18px] rounded-[20px] px-[22px] py-[12px] text-left outline-none focus-visible:ring-2 focus-visible:ring-[#4a74ff]"
      style={{ background: t.card, gridColumn: span2 ? 'span 2' : undefined }}
    >
      <Switch on={on} />
      <span className="min-w-0 flex-1">
        <span className="block text-[19px] leading-snug">{title}</span>
        {sub && <span className="block text-[14px] leading-snug" style={{ color: t.text3 }}>{sub}</span>}
      </span>
      {info && <Ic.Info size={26} style={{ color: t.text2 }} />}
    </button>
  );
}

/** A card that would open a deeper page (the little corner mark); here it says so. */
function LinkCard({ title, sub, onClick }: { title: string; sub?: string; onClick?: () => void }) {
  const t = useHa();
  const { notify } = useHaLocal();
  return (
    <button
      type="button"
      onClick={onClick ?? (() => notify(`${title} is not part of the showroom demo`))}
      className="relative min-h-[78px] rounded-[20px] px-[22px] py-[14px] text-left outline-none focus-visible:ring-2 focus-visible:ring-[#4a74ff]"
      style={{ background: t.card }}
    >
      <span className="block text-[19px] leading-snug">{title}</span>
      {sub && <span className="block text-[14px] leading-snug" style={{ color: t.text3 }}>{sub}</span>}
      <span className="absolute bottom-[7px] right-[7px] h-0 w-0" style={{ borderStyle: 'solid', borderWidth: '0 0 11px 11px', borderColor: `transparent transparent ${t.text3} transparent`, opacity: 0.6 }} />
    </button>
  );
}

function Segmented({
  items, value, onChange, label,
}: {
  items: string[];
  value: number;
  onChange: (i: number) => void;
  label: string;
}) {
  const t = useHa();
  return (
    <div className="flex h-[58px] gap-[2px] rounded-[20px] p-[4px]" style={{ background: t.seg }} role="group" aria-label={label}>
      {items.map((x, i) => (
        <button
          key={x}
          type="button"
          aria-pressed={i === value}
          onClick={() => onChange(i)}
          className="flex-1 rounded-[16px] text-[18px] outline-none transition-colors focus-visible:ring-2 focus-visible:ring-[#4a74ff]"
          style={{ background: i === value ? t.segOn : 'transparent', color: i === value ? t.tileOnText : t.text, boxShadow: i === value ? '0 2px 8px rgba(0,0,0,0.10)' : 'none' }}
        >
          {x}
        </button>
      ))}
    </div>
  );
}

function Section({ title, info, children }: { title: string; info?: boolean; children: React.ReactNode }) {
  const t = useHa();
  return (
    <section className="mt-[26px]">
      <div className="mb-[12px] flex items-center justify-between text-[20px]">
        {title}
        {info && <Ic.Info size={26} style={{ color: t.text2 }} />}
      </div>
      {children}
    </section>
  );
}

const Grid2 = ({ children }: { children: React.ReactNode }) => <div className="grid grid-cols-2 gap-[14px]">{children}</div>;

/** The page's picture: the car, over a soft light. */
function Hero({ children, h = 300 }: { children?: React.ReactNode; h?: number }) {
  return <div className="relative" style={{ height: h }}>{children}</div>;
}

function CarImage({ w = 520, left = 250, top = 8, ghost = false }: { w?: number; left?: number; top?: number; ghost?: boolean }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src="/hmi/luxeed-rx/car34.webp"
      alt=""
      draggable={false}
      className="absolute max-w-none"
      style={{ width: w, left, top, opacity: ghost ? 0.35 : 1, filter: ghost ? 'grayscale(1) brightness(1.6) contrast(0.7)' : undefined }}
    />
  );
}

type PageProps = { vehicle: Vehicle; variant: Variant };

/* -------------------------------------------------------------- the pages */

function VehiclePage() {
  const t = useHa();
  const { openings, toggleOpening, locked } = useVehicleStore();
  const { on, toggle, set, notify } = useHaLocal();
  const tiles: { id: string; label: string; icon: React.ReactNode; active: boolean; fn: () => void }[] = [
    { id: 'charge', label: 'Charge port', icon: <Ic.ChargePort size={30} />, active: on.chargePort, fn: () => toggle('chargePort') },
    { id: 'trunks', label: 'Front & rear trunk', icon: <Ic.TrunkRear size={30} />, active: openings.boot || openings.frunk, fn: () => toggleOpening('boot') },
    { id: 'doors', label: 'Doors', icon: <Ic.DoorLock size={30} />, active: openings.doorFL || openings.doorFR || openings.doorRL || openings.doorRR, fn: () => toggleOpening('doorFL') },
    { id: 'shade', label: 'Sunshade', icon: <Ic.Sunshade size={30} />, active: on.sunshade, fn: () => toggle('sunshade') },
    { id: 'windows', label: 'Windows', icon: <Ic.WindowOpen size={30} />, active: on.windows, fn: () => toggle('windows') },
    { id: 'mirrors', label: 'Fold mirrors', icon: <Ic.MirrorFold size={30} />, active: on.mirrorFold, fn: () => toggle('mirrorFold') },
  ];
  return (
    <div>
      <Hero h={330}><CarImage w={560} left={290} top={14} /></Hero>
      <div className="flex gap-[16px]">
        {tiles.map((x) => (
          <button
            key={x.id}
            type="button"
            aria-pressed={x.active}
            onClick={x.fn}
            className="relative flex h-[120px] w-[125px] shrink-0 flex-col items-center justify-center gap-[10px] rounded-[22px] text-[15px] outline-none focus-visible:ring-2 focus-visible:ring-[#4a74ff]"
            style={{ background: x.active ? t.segOn : t.tile, color: x.active ? t.tileOnText : t.text }}
          >
            {x.icon}
            <span className="px-2 text-center leading-tight">{x.label}</span>
          </button>
        ))}
      </div>
      <Section title="Car lock">
        <Grid2>
          <ToggleCard title="Unlock on approach" sub="Unlocks when the key is near" on={on.autoUnlock} onChange={(v) => set('autoUnlock', v)} info />
          <ToggleCard title="Lock on leaving" sub="Locks when the key moves away" on={on.autoLock || locked} onChange={(v) => { set('autoLock', v); notify(v ? 'The car will lock when you walk away' : 'Auto lock off'); }} info />
        </Grid2>
      </Section>
    </div>
  );
}

function LightsPage() {
  const t = useHa();
  const [tab, setTab] = React.useState<'inside' | 'outside'>('outside');
  const { ambientOn, ambientHue, ambientBrightness, setAmbient, setHeadlights } = useVehicleStore();
  const { val, setVal, on, set } = useHaLocal();
  const [zone, setZone] = React.useState(0);
  const sq = React.useRef<HTMLDivElement>(null);
  const pick = (e: React.PointerEvent) => {
    if (e.type === 'pointermove' && e.buttons === 0) return;
    const r = sq.current?.getBoundingClientRect();
    if (!r) return;
    const x = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width));
    setAmbient({ ambientHue: Math.round(x * 360), ambientOn: true });
  };
  const tabs = (
    <div className="mb-2 flex justify-center gap-[80px] text-[20px]" role="tablist">
      {([['inside', 'Interior'], ['outside', 'Exterior']] as const).map(([k, l]) => (
        <button key={k} role="tab" aria-selected={tab === k} type="button" onClick={() => setTab(k)} className="relative pb-2 outline-none" style={{ color: tab === k ? t.blue : t.text }}>
          {l}
          {tab === k && <span className="absolute inset-x-0 bottom-0 h-[2px]" style={{ background: t.blue }} />}
        </button>
      ))}
    </div>
  );
  if (tab === 'outside') {
    return (
      <div>
        {tabs}
        <Hero h={250}><CarImage w={430} left={190} top={4} /></Hero>
        <Section title="Headlamps">
          <div className="grid gap-[10px]" style={{ gridTemplateColumns: '1fr 1fr 1fr 1fr 150px' }}>
            {['Off', 'Position', 'Low beam', 'Auto'].map((l, i) => (
              <button key={l} type="button" aria-pressed={val.headlamp === i} onClick={() => { setVal('headlamp', i); setHeadlights(i >= 2); }} className="flex h-[58px] items-center justify-center rounded-[18px] text-[17px] outline-none" style={{ background: val.headlamp === i ? t.segOn : t.seg, color: val.headlamp === i ? t.tileOnText : t.text }}>{l}</button>
            ))}
            <button type="button" aria-pressed={on.rearFog} onClick={() => set('rearFog', !on.rearFog)} className="flex h-[58px] items-center justify-center rounded-[18px] text-[17px] outline-none" style={{ background: on.rearFog ? t.segOn : t.seg, color: on.rearFog ? t.tileOnText : t.text }}>Rear fog</button>
          </div>
        </Section>
        <Section title="Smart lights">
          <Grid2>
            <ToggleCard title="High beam assist" sub="Adjusts the high beam to the light around" on={on.autoHighBeam} onChange={(v) => set('autoHighBeam', v)} />
            <ToggleCard title="Low beam assist" sub="Adjusts the low beam to the road ahead" on={on.autoLowBeam} onChange={(v) => set('autoLowBeam', v)} />
            <ToggleCard title="Turn signal auto-off" sub="Cancels the signal after the turn" on={on.turnSignalOff} onChange={(v) => set('turnSignalOff', v)} span2 />
          </Grid2>
        </Section>
      </div>
    );
  }
  const zones = ['Surround light', 'Auxiliary light', 'Accent light'];
  return (
    <div>
      {tabs}
      <Hero h={250}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={`/hmi/luxeed-rx/cabin-seats-${t.tone}.webp`} alt="" draggable={false} className="absolute max-w-none" style={{ left: 120, top: -10, width: 560, opacity: 0.9 }} />
        <div className="absolute inset-x-[100px] bottom-0 h-[10px] rounded-full opacity-90" style={{ background: ambientOn ? `hsl(${ambientHue} 95% 55%)` : 'transparent', filter: 'blur(6px)' }} />
      </Hero>
      <div className="mb-[18px] flex items-center justify-between gap-3">
        <span className="rounded-full px-6 py-3 text-[17px]" style={{ background: t.seg }}>Theme</span>
        <span className="rounded-full px-6 py-3 text-[17px]" style={{ background: t.segOn, color: t.tileOnText }}>Custom</span>
        <button type="button" aria-pressed={!ambientOn} onClick={() => setAmbient({ ambientOn: !ambientOn })} className="flex items-center gap-3 rounded-full px-6 py-3 text-[17px] text-white outline-none" style={{ background: t.blue }}>
          <Ic.Close size={16} />{ambientOn ? 'Turn ambient light off' : 'Turn ambient light on'}
        </button>
        <span className="rounded-full px-6 py-3 text-[17px]" style={{ background: t.seg }}>Sync</span>
      </div>
      <div className="flex gap-[22px]">
        <div className="flex w-[150px] shrink-0 flex-col gap-[10px]">
          {zones.map((z, i) => (
            <button key={z} type="button" aria-pressed={zone === i} onClick={() => setZone(i)} className="h-[64px] rounded-[16px] text-[17px] outline-none" style={{ background: zone === i ? t.segOn : t.seg, color: zone === i ? t.tileOnText : t.text }}>{z.split(' ')[0]}</button>
          ))}
        </div>
        <div
          ref={sq}
          className="relative h-[200px] w-[320px] shrink-0 cursor-crosshair touch-none overflow-hidden rounded-[18px]"
          style={{ background: 'linear-gradient(to top,#fff,transparent 70%),linear-gradient(to right,#f33,#fc3,#6f3,#3fc,#39f,#93f,#f3c,#f33)' }}
          onPointerDown={pick}
          onPointerMove={pick}
          role="slider"
          tabIndex={0}
          aria-label="Ambient colour"
          aria-valuenow={ambientHue}
          aria-valuemin={0}
          aria-valuemax={360}
          onKeyDown={(e) => {
            if (e.key === 'ArrowRight') setAmbient({ ambientHue: (ambientHue + 10) % 360 });
            if (e.key === 'ArrowLeft') setAmbient({ ambientHue: (ambientHue + 350) % 360 });
          }}
        >
          <span className="absolute top-[40%] h-[30px] w-[30px] -translate-x-1/2 -translate-y-1/2 rounded-full border-[3px] border-white" style={{ left: `${(ambientHue / 360) * 100}%`, background: `hsl(${ambientHue} 95% 55%)`, boxShadow: '0 2px 8px rgba(0,0,0,0.35)' }} />
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-[12px]">
          <div className="flex h-[62px] items-center gap-3 rounded-[18px] px-4" style={{ background: t.card }}>
            <Ic.MenuLights size={26} style={{ color: t.text2 }} />
            <input type="range" min={0} max={1} step={0.05} value={ambientBrightness} aria-label="Ambient brightness" onChange={(e) => setAmbient({ ambientBrightness: Number(e.target.value) })} className="flex-1 accent-[#4a74ff]" />
            <span className="tnum w-8 text-right text-[17px]" style={{ color: t.text2 }}>{Math.round(ambientBrightness * 10)}</span>
          </div>
          <div className="flex gap-[10px]">
            {[0, 1, 2].map((i) => (
              <button key={i} type="button" aria-label="Save colour" className="flex h-[60px] flex-1 items-center justify-center rounded-[16px] outline-none" style={{ background: t.seg }}><Ic.Plus size={24} /></button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function EnergyPage({ variant }: PageProps) {
  const t = useHa();
  const { soc, driveMode, climate, setHmiScreen } = useVehicleStore();
  const { on, set, toggle, notify } = useHaLocal();
  const range = effectiveRange(variant, driveMode, soc, climate);
  return (
    <div>
      <Hero h={300}>
        <div className="absolute left-[24px] top-[48px]">
          <div className="flex items-center gap-2 text-[17px]" style={{ color: t.text2 }}>Remaining range <span className="rounded-[5px] px-1.5 text-[11px] font-bold" style={{ background: t.seg }}>{range?.cycle ?? 'CLTC'}</span></div>
          <div className="tnum mt-1 text-[48px] font-medium leading-none">{range?.km ?? '--'}<span className="ml-1 text-[19px] font-normal">km</span></div>
        </div>
        <CarImage w={520} left={210} top={20} ghost />
        <div className="absolute flex h-[78px] w-[250px] items-center justify-center overflow-hidden rounded-[8px]" style={{ left: 400, top: 168, background: 'linear-gradient(90deg,#0f6b72 var(--p), rgba(255,255,255,0.18) var(--p))', ['--p' as string]: `${Math.round(soc * 100)}%` }}>
          <span className="tnum text-[34px] font-medium text-white">{Math.round(soc * 100)}%</span>
        </div>
        <button type="button" onClick={() => { toggle('chargePort'); notify(on.chargePort ? 'Charge port closed' : 'Charge port open'); }} className="absolute right-0 top-[42px] flex h-[56px] items-center gap-3 rounded-full px-6 text-[18px] outline-none" style={{ background: t.segOn, color: t.tileOnText }}>
          <Ic.ChargePort size={24} />{on.chargePort ? 'Close charge port' : 'Open charge port'}
        </button>
      </Hero>
      <Grid2>
        <ToggleCard title="Scheduled charging" sub="Every day 00:00 to 06:00" on={on.scheduled} onChange={(v) => set('scheduled', v)} />
        <LinkCard title="Charging protection" sub="Set the charging limit and the current limit" onClick={() => setHmiScreen('settings')} />
        <ToggleCard title="Reverse power supply" sub="Powers a connected device once on" on={on.v2l} onChange={(v) => set('v2l', v)} />
        <ToggleCard title="Smart battery health management" on={on.batteryHealth} onChange={(v) => set('batteryHealth', v)} info />
        <ToggleCard title="Super power saving" sub="Limits some functions to extend the range" on={on.saver} onChange={(v) => set('saver', v)} info />
        <ToggleCard title="Delayed in-car power off" sub="After power-off, the cabin stays powered for a while" on={on.delayOff} onChange={(v) => set('delayOff', v)} />
      </Grid2>
    </div>
  );
}

function DrivingPage({ vehicle }: PageProps) {
  const t = useHa();
  const { modeId, setCarMode } = useVehicleStore();
  const { val, setVal } = useHaLocal();
  const modes = vehicle.cockpit.driveModes ?? [];
  const idx = Math.max(0, modes.findIndex((m) => m.id === (modeId ?? 'comfort')));
  const hue = ['#35c46a', '#4a74ff', '#ff9a3d', '#ff4a3f', '#a35cff'][idx] ?? '#4a74ff';
  return (
    <div>
      <Hero h={320}>
        <div className="absolute rounded-full" style={{ left: 250, top: 40, width: 560, height: 240, background: `radial-gradient(ellipse, ${hue}66, transparent 68%)`, filter: 'blur(26px)' }} />
        <CarImage w={560} left={250} top={30} />
      </Hero>
      <Section title="Drive mode" info>
        <Segmented
          label="Drive mode"
          items={modes.map((m) => (m.id === 'comfort' ? 'Comfort (recommended)' : m.label))}
          value={idx}
          onChange={(i) => setCarMode(modes[i].id, modes[i].model)}
        />
      </Section>
      <Section title="Suspension height" info>
        <Segmented
          label="Suspension height"
          items={['Lowest', 'Low', 'Standard (recommended)', 'High', 'Highest']}
          value={val.rideHeight}
          onChange={(i) => setVal('rideHeight', i)}
        />
      </Section>
      <div className="mt-[26px] text-[14px]" style={{ color: t.text3 }}>
        Air suspension: 100 mm of travel in five steps and a sixth for loading, as published.
      </div>
    </div>
  );
}

function AssistPage() {
  const { set } = useHaLocal();
  return (
    <div>
      <Hero h={300}>
        <svg className="absolute inset-0" width="860" height="300" viewBox="0 0 860 300" aria-hidden>
          <path d="M20 20 L540 270 M840 130 L430 300" stroke="#3d86ff" strokeWidth="5" strokeLinecap="round" opacity="0.8" />
        </svg>
        <CarImage w={520} left={200} top={10} />
      </Hero>
      <Grid2>
        <LinkCard title="Assisted driving" sub="Lead-vehicle and lane-cruise assist settings" />
        <LinkCard title="Parking assist" sub="Remote parking assist and parking speed" onClick={() => set('parkDialog', true)} />
        <LinkCard title="Active safety" sub="Front, side and rear active safety settings" />
        <LinkCard title="Surround view" sub="360° surround view settings" />
        <LinkCard title="Other settings" />
        <LinkCard title="Exam and guide" />
      </Grid2>
    </div>
  );
}

function StatusPage() {
  const t = useHa();
  return (
    <div>
      <Hero h={330}>
        <CarImage w={560} left={260} top={34} ghost />
        {[['3.0 bar', 320, 18], ['3.1 bar', 700, 18], ['3.0 bar', 300, 236], ['3.1 bar', 720, 236]].map(([l, x, y], i) => (
          <span key={i} className="tnum absolute rounded-full px-3 py-[3px] text-[14px]" style={{ left: Number(x), top: Number(y), background: t.seg }}>{l}</span>
        ))}
        {[[360, 170], [330, 215], [760, 160], [740, 215]].map(([x, y], i) => (
          <span key={i} className="absolute h-[54px] w-[54px] -translate-x-1/2 -translate-y-1/2 rounded-full border-[6px]" style={{ left: Number(x), top: Number(y), borderColor: 'rgba(58,134,255,0.75)' }} />
        ))}
      </Hero>
      <Grid2>
        <LinkCard title="Distance to next service" sub="19,901 km or 351 days" />
        <LinkCard title="Maintenance check" sub="Vehicle service and check settings" />
        <LinkCard title="With you for" sub="99 km" />
        <LinkCard title="Trip protection" sub="In an emergency, passenger details are sent to the rescue service" />
        <LinkCard title="Roadside rescue" sub="Call the rescue centre for help with the vehicle" />
      </Grid2>
    </div>
  );
}

function ScenesPage() {
  const { on, toggle, set } = useHaLocal();
  const cards: [string, string, string][] = [
    ['nap', 'Nap mode', 'Quiet rest and guided relaxation'],
    ['pet', 'Pet care mode', 'Windows close and the air conditioning keeps the cabin comfortable'],
    ['carWash', 'Car-wash mode', 'Closes the windows and mirrors, locks the charge port'],
    ['sentry', 'Sentry mode', 'Watches the car while it is parked'],
    ['vlog', 'In-car vlog', 'Mounts for action cameras and a camera app on the screen'],
  ];
  return (
    <div className="pt-4">
      <div className="mb-3 text-[20px]">Smart scenes</div>
      <Grid2>
        {cards.map(([id, t1, t2]) => (
          <ToggleCard key={id} title={t1} sub={t2} on={on[id]} onChange={() => (id === 'vlog' ? set(id, !on[id]) : toggle(id))} />
        ))}
      </Grid2>
    </div>
  );
}

function PersonalisePage() {
  const t = useHa();
  const wp = useWallpaper(t.tone);
  const { setHmiScreen } = useVehicleStore();
  const { on, set, notify } = useHaLocal();
  return (
    <div className="pt-1">
      <div className="mb-3 text-[20px]">Theme</div>
      <div className="grid gap-[16px]" style={{ gridTemplateColumns: '1fr 1fr' }}>
        <div className="relative h-[190px] overflow-hidden rounded-[22px]" style={{ boxShadow: `0 0 0 3px ${t.blue}` }}>
          <Wallpaper id={wp.id} className="absolute inset-0 h-full w-full" />
          <span className="absolute right-3 top-3 rounded-[8px] bg-black/55 px-2 py-0.5 text-[13px] text-white">Current theme</span>
        </div>
        <button type="button" onClick={() => notify('More themes are not part of the showroom demo')} className="flex h-[190px] flex-col items-center justify-center gap-3 rounded-[22px] text-[18px] outline-none" style={{ background: t.seg }}>
          <Ic.Plus size={30} />Add theme
        </button>
      </div>
      <div className="mt-[18px] flex justify-center">
        <span className="rounded-full px-14 py-3 text-[18px] text-white" style={{ background: t.blue, opacity: 0.55 }}>Current theme</span>
      </div>
      <Section title="Personalise">
        <Grid2>
          <LinkCard title="Wallpaper" sub="Switch with the arrows on the desktop" onClick={() => { setHmiScreen('home'); }} />
          <LinkCard title="Screen saver" />
        </Grid2>
      </Section>
      <Section title="Permissions">
        <Grid2>
          <ToggleCard title="Online theme service" on={on.onlineTheme} onChange={(v) => set('onlineTheme', v)} info />
        </Grid2>
      </Section>
    </div>
  );
}

function DisplayPage() {
  const t: HaTheme = useHa();
  const { setHmiTheme } = useVehicleStore();
  const { on, set, val, setVal } = useHaLocal();
  const mode = val.dispMode;
  const choose = (i: number) => {
    setVal('dispMode', i);
    if (i === 1) setHmiTheme('dark');
    else if (i === 2) setHmiTheme('light');
    else {
      // adaptive: by the hour
      const h = new Date().getHours();
      setHmiTheme(h >= 7 && h < 18 ? 'light' : 'dark');
    }
  };
  const bright = (label: string, key: string, auto: string) => (
    <div className="rounded-[22px] p-[14px]" style={{ background: t.card }}>
      <div className="mb-3 flex items-center justify-between">
        <span className="text-[16px]" style={{ color: t.text2 }}>{label}</span>
        <button type="button" aria-pressed={on[auto]} onClick={() => set(auto, !on[auto])} className="rounded-full px-5 py-1.5 text-[15px] outline-none" style={{ background: on[auto] ? t.blue : t.seg, color: on[auto] ? '#fff' : t.text }}>Auto</button>
      </div>
      <div className="flex h-[54px] items-center gap-3 rounded-full px-4" style={{ background: t.seg }}>
        <Ic.BrightnessA size={24} style={{ color: t.text2 }} />
        <input type="range" min={20} max={100} value={val[key]} aria-label={label} onChange={(e) => setVal(key, Number(e.target.value))} className="flex-1 accent-[#4a74ff]" />
        <span className="tnum w-12 text-right text-[16px]" style={{ color: t.text2 }}>{val[key]}%</span>
      </div>
    </div>
  );
  return (
    <div className="pt-1">
      <div className="mb-3 text-[20px]">Display mode</div>
      <Segmented label="Display mode" items={['Adaptive (recommended)', 'Dark', 'Light']} value={mode} onChange={choose} />
      <Section title="Brightness">
        <Grid2>
          {bright('Centre screen', 'brightness', 'adaptiveBrightness')}
          {bright('Instrument cluster', 'clusterBrightness', 'adaptiveBrightnessCluster')}
        </Grid2>
      </Section>
      <Section title="Advanced display settings">
        <Grid2>
          <ToggleCard title="Head-up display" on={on.hud} onChange={(v) => set('hud', v)} />
          <LinkCard title="Centre screen angle" sub="Turns toward the driver or the passenger" />
          <ToggleCard title="Eye comfort" sub="Off" on={on.eye} onChange={(v) => set('eye', v)} />
          <ToggleCard title="Lyrics on the cluster" sub="Where the app supports it" on={on.lyrics} onChange={(v) => set('lyrics', v)} />
        </Grid2>
      </Section>
    </div>
  );
}

function ConnectionPage() {
  const { on, set, val, setVal } = useHaLocal();
  return (
    <div className="pt-1">
      <Grid2>
        <ToggleCard title="Bluetooth" sub={on.bt ?? true ? 'On' : 'Off'} on={on.bt ?? true} onChange={(v) => set('bt', v)} />
        <ToggleCard title="NearLink" sub={on.nearlink ? 'On' : 'Off'} on={on.nearlink} onChange={(v) => set('nearlink', v)} />
        <ToggleCard title="WLAN" sub={on.wlan ?? true ? 'On' : 'Off'} on={on.wlan ?? true} onChange={(v) => set('wlan', v)} />
        <ToggleCard title="Hotspot" sub={on.hotspot ? 'On' : 'Off'} on={on.hotspot} onChange={(v) => set('hotspot', v)} />
        <LinkCard title="Wireless charging" sub="On" />
        <ToggleCard title="Share" on={on.share} onChange={(v) => set('share', v)} />
      </Grid2>
      <Section title="Connected services">
        <Grid2>
          <ToggleCard title="ETC" on={on.etc} onChange={(v) => set('etc', v)} />
          <LinkCard title="Super Device" />
        </Grid2>
      </Section>
      <Section title="Carrier">
        <Segmented label="Carrier" items={['Auto', 'Carrier A', 'Carrier B']} value={val.carrier} onChange={(i) => setVal('carrier', i)} />
      </Section>
    </div>
  );
}

function SoundPage() {
  const t = useHa();
  const { val, setVal, on, set, notify } = useHaLocal();
  const fx = val.soundFx;
  return (
    <div>
      <Hero h={300}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={`/hmi/luxeed-rx/cabin-seats-${t.tone}.webp`} alt="" draggable={false} className="absolute max-w-none" style={{ left: 140, top: -20, width: 560 }} />
        <div className="absolute left-1/2 top-[8px] -translate-x-1/2 text-[13px] font-semibold tracking-[0.2em]" style={{ color: t.text3 }}>SOUND SYSTEM</div>
        <button type="button" onClick={() => notify('Preview plays a sample (showroom demo)')} className="absolute left-[330px] top-[238px] flex h-[40px] items-center gap-2 rounded-full px-5 text-[16px] outline-none" style={{ background: t.seg }}>Preview <Ic.Play size={14} /></button>
        <span className="absolute left-[310px] top-[262px] rounded-full px-8 py-2 text-[17px]" style={{ background: t.seg }}>Smart sound field</span>
      </Hero>
      <Section title="Sound effect">
        <Segmented label="Sound effect" items={['Pure', 'Concert hall', 'Cinema', 'Sound Cube']} value={fx} onChange={(i) => setVal('soundFx', i)} />
      </Section>
      <div className="mt-[16px]">
        <Grid2>
          <LinkCard title="Equaliser" sub="Classic" />
          <ToggleCard title="Custom surround" sub="Adjust voice and background" on={on.surround} onChange={(v) => set('surround', v)} />
        </Grid2>
      </div>
    </div>
  );
}

function AssistantPage() {
  const t = useHa();
  const { on, set } = useHaLocal();
  return (
    <div className="pt-1">
      <div className="mb-3 text-[20px]">Smart voice</div>
      <Grid2>
        <div className="relative h-[130px] overflow-hidden rounded-[22px] p-[18px]" style={{ background: t.card }}>
          <div className="text-[19px]">Smart listening</div>
          <div className="text-[14px]" style={{ color: t.text3 }}>Listening time 10 s</div>
          <span className="absolute -bottom-6 right-6 h-[110px] w-[110px] rounded-full border-[12px]" style={{ borderColor: t.seg }} />
        </div>
        <div className="relative h-[130px] overflow-hidden rounded-[22px] p-[18px]" style={{ background: 'linear-gradient(135deg,#f4e3df,#ef8d70)' }}>
          <div className="text-[19px] text-[#3a1a14]">My Xiaoyi</div>
          <div className="text-[14px] text-[#3a1a14]/70">Set the wake word and the reply voice</div>
          <span className="absolute -bottom-12 -right-8 h-[130px] w-[130px] rounded-full" style={{ background: '#e8432d' }} />
        </div>
        <ToggleCard title="Voice wake-up" sub="Wake with the wake word" on={on.voiceWake ?? true} onChange={(v) => set('voiceWake', v)} />
        <ToggleCard title="Wake-free" sub="No wake word; just talk to Xiaoyi" on={on.wakeFree} onChange={(v) => set('wakeFree', v)} />
        <LinkCard title="Cooperative wake" />
        <ToggleCard title="Announce incoming calls" sub="The call is read out" on={on.callVoice ?? true} onChange={(v) => set('callVoice', v)} />
        <LinkCard title="Voice skills" />
        <LinkCard title="Voiceprint" />
        <ToggleCard title="Speak freely in dialect" sub="Xiaoyi talks the way you do" on={on.dialect} onChange={(v) => set('dialect', v)} />
        <ToggleCard title="Concise replies" sub="Shorter spoken answers" on={on.concise ?? true} onChange={(v) => set('concise', v)} />
      </Grid2>
    </div>
  );
}

function SystemPage({ vehicle }: PageProps) {
  const t = useHa();
  const { on, set, notify } = useHaLocal();
  return (
    <div className="pt-1">
      <div className="mb-3 text-[20px]">About</div>
      <Grid2>
        <div className="flex h-[210px] flex-col items-center justify-center rounded-[22px]" style={{ background: t.tone === 'dark' ? 'linear-gradient(160deg,#2a2a33,#15161b)' : 'linear-gradient(160deg,#fff,#d9d6e2)' }}>
          <div className="text-[34px] font-semibold tracking-tight">HarmonyOS</div>
          <div className="tnum text-[17px]" style={{ color: t.text2 }}>Cockpit 4.0</div>
        </div>
        <div className="grid gap-[14px]">
          <LinkCard title={`My ${vehicle.brand} ${vehicle.model}`} sub="Chassis number: shown on the car only" />
          <LinkCard title="More system information" sub="Storage, service components and more" />
        </div>
      </Grid2>
      <Section title="Update and reset">
        <Grid2>
          <LinkCard title="System update" sub="Showroom build: no updates" onClick={() => notify('You are up to date (showroom demo)')} />
          <LinkCard title="Reset" sub="Restore the settings to default and clear user data" />
        </Grid2>
      </Section>
      <Section title="Privacy">
        <Grid2>
          <ToggleCard title="In-car privacy protection" sub="Turns off the microphones, the cameras and remote location view" on={on.privacy} onChange={(v) => set('privacy', v)} />
          <LinkCard title="One-tap trace removal" sub="Choose what to clear, then clear it" />
        </Grid2>
      </Section>
    </div>
  );
}
