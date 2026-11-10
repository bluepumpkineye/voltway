'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore, type SettingsPage } from '@/store/vehicle-store';
import { effectiveRange } from '@/lib/performance';
import * as Ha from '../harmonyos/icons';
import { useHaLocal } from '../harmonyos/shared';
import * as Ic from './icons';
import { useAv, BAR_H, STATUS_H } from './theme';
import { CarImage, Grid2, LinkCard, Section, Segmented, TabRow, ToggleCard } from './ui';
import { byModeOrder } from './Pages';

/* ---------------------------------------------------------------- the menu */

const MENU: { id: SettingsPage; label: string; icon: React.ReactNode }[] = [
  { id: 'vehicle', label: 'Vehicle control', icon: <Ic.MenuVehicle size={25} /> },
  { id: 'driving', label: 'Driving', icon: <Ic.MenuDriving size={25} /> },
  { id: 'sound', label: 'Sound', icon: <Ic.MenuSound size={25} /> },
  { id: 'lights', label: 'Lights', icon: <Ic.MenuLights size={25} /> },
  { id: 'energy', label: 'Energy', icon: <Ic.MenuEnergy size={25} /> },
  { id: 'assist', label: 'Assisted driving', icon: <Ic.MenuAssist size={25} /> },
  { id: 'scenes', label: 'Smart scenes', icon: <Ic.MenuScenes size={25} /> },
  { id: 'display', label: 'Display', icon: <Ic.MenuDisplay size={25} /> },
  { id: 'connection', label: 'Connections', icon: <Ic.MenuLink size={25} /> },
  { id: 'assistant', label: 'Smart assistant', icon: <Ic.MenuAssistant size={25} /> },
  { id: 'status', label: 'Vehicle status', icon: <Ic.MenuStatus size={25} /> },
  { id: 'system', label: 'System', icon: <Ic.MenuSystem size={25} /> },
];

/** The store's page ids the other skins use, onto this menu. */
const ALIAS: Partial<Record<SettingsPage, SettingsPage>> = { doors: 'vehicle', charging: 'energy', personalise: 'display' };

type PageProps = { vehicle: Vehicle; variant: Variant };

/**
 * The Settings app (c10_0020-33): "Settings" and the menu down the left in the car's order, a page beside it.
 * A page is a picture of the car or the cabin with tabs over it, and pale cards of switches, selectors and
 * links; a link says what it would open, as the showroom has no more screens than these.
 */
export function SettingsApp({ vehicle, variant }: PageProps) {
  const t = useAv();
  const { settingsPage, openSettings } = useVehicleStore();
  const page = ALIAS[settingsPage] ?? settingsPage;
  const ref = React.useRef<HTMLDivElement>(null);
  React.useEffect(() => {
    ref.current?.scrollTo({ top: 0 });
  }, [page]);

  const Page = (
    {
      vehicle: VehiclePage,
      driving: DrivingPage,
      sound: SoundPage,
      lights: LightsPage,
      energy: EnergyPage,
      assist: AssistPage,
      scenes: ScenesPage,
      display: DisplayPage,
      connection: ConnectionPage,
      assistant: AssistantPage,
      status: StatusPage,
      system: SystemPage,
    } as Partial<Record<SettingsPage, React.ComponentType<PageProps>>>
  )[page] ?? VehiclePage;

  return (
    <div className="absolute inset-0" style={{ background: t.bg, color: t.text }}>
      <h2 className="absolute text-[30px] font-medium leading-none" style={{ left: 44, top: 88 }}>Settings</h2>
      <nav className="absolute" style={{ left: 28, top: 138, width: 312, bottom: BAR_H }} aria-label="Settings">
        <div className="h-full overflow-y-auto pb-4" style={{ scrollbarWidth: 'none' }}>
          {MENU.map((m) => {
            const on = m.id === page;
            return (
              <button
                key={m.id}
                type="button"
                aria-current={on ? 'page' : undefined}
                onClick={() => openSettings(m.id)}
                className="mb-[17px] flex h-[70px] w-full items-center gap-[20px] rounded-[22px] px-[26px] text-left text-[19px] outline-none transition-colors focus-visible:ring-2 focus-visible:ring-[#2c46f2]"
                style={{ background: on ? t.segOn : 'transparent', color: t.text, boxShadow: on ? '0 2px 10px rgba(30,40,90,0.10)' : 'none' }}
              >
                <span className="shrink-0">{m.icon}</span>
                <span className="truncate">{m.label}</span>
              </button>
            );
          })}
        </div>
      </nav>
      <div ref={ref} className="absolute overflow-y-auto pb-6 pr-[40px]" style={{ left: 362, right: 0, top: STATUS_H - 4, bottom: BAR_H, scrollbarWidth: 'none' }}>
        <Page vehicle={vehicle} variant={variant} />
      </div>
    </div>
  );
}

/** A page's hero: the car or the cabin picture with the tabs above it. */
function Hero({ h = 330, children }: { h?: number; children?: React.ReactNode }) {
  return <div className="relative" style={{ height: h }}>{children}</div>;
}

function Tabs({ tabs, value, onChange }: { tabs: string[]; value: number; onChange: (i: number) => void }) {
  return <TabRow tabs={tabs} value={value} onChange={onChange} className="relative flex justify-center gap-[96px] pt-[16px]" />;
}

function CabinImage({ w = 520, left = 160, top = 0, opacity = 1 }: { w?: number; left?: number; top?: number; opacity?: number }) {
  const t = useAv();
  const { slug } = useHaLocal();
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={`/hmi/${slug}/cabin-climate-${t.tone}.webp`} alt="" draggable={false} className="absolute max-w-none" style={{ width: w, left, top, opacity }} />
  );
}

/* -------------------------------------------------------------- the pages */

function VehiclePage() {
  const t = useAv();
  const [tab, setTab] = React.useState(0);
  const { openings, toggleOpening, locked, setLocked } = useVehicleStore();
  const { on, toggle, set, notify } = useHaLocal();
  const tiles: { id: string; label: string; icon: React.ReactNode; active: boolean; fn: () => void }[] = [
    { id: 'charge', label: 'Charge port', icon: <Ic.Charge size={28} />, active: on.chargePort, fn: () => toggle('chargePort') },
    { id: 'trunk', label: 'Rear trunk', icon: <Ic.Trunk size={28} />, active: openings.boot, fn: () => toggleOpening('boot') },
    { id: 'lock', label: 'Door lock', icon: locked ? <Ic.LockShut size={28} /> : <Ic.LockOpen size={28} />, active: !locked, fn: () => setLocked(!locked) },
    { id: 'mirrors', label: 'Mirrors fold', icon: <Ha.MirrorFold size={28} />, active: on.mirrorFold, fn: () => toggle('mirrorFold') },
    { id: 'windows', label: 'Windows', icon: <Ha.WindowOpen size={28} />, active: on.windows, fn: () => toggle('windows') },
    { id: 'child', label: 'Child lock', icon: <Ha.ChildLock size={28} />, active: on.childLock, fn: () => toggle('childLock') },
  ];
  return (
    <div>
      <Tabs tabs={['Quick settings', 'Doors', 'Locks']} value={tab} onChange={setTab} />
      {tab === 0 && (
        <>
          <Hero h={330}><CarImage w={470} left={150} top={20} /></Hero>
          <div className="flex gap-[22px] pl-[22px]">
            {tiles.map((x) => (
              <button
                key={x.id}
                type="button"
                aria-pressed={x.active}
                onClick={x.fn}
                className="flex h-[118px] w-[118px] shrink-0 flex-col items-center justify-center gap-[10px] rounded-[20px] text-[14px] outline-none focus-visible:ring-2 focus-visible:ring-[#2c46f2]"
                style={{ background: x.active ? t.tileOn : t.tile, color: t.tileOnText }}
              >
                {x.icon}
                <span className="px-1 text-center leading-tight">{x.label}</span>
              </button>
            ))}
          </div>
          <Section title="Mirrors and steering wheel">
            <Grid2>
              <ToggleCard title="Fold on lock" sub="Fold when locked, unfold when unlocked" on={on.mirrorLock} onChange={(v) => set('mirrorLock', v)} />
              <ToggleCard title="Tilt down in reverse" sub="Shows the ground when reversing" on={on.mirrorReverse} onChange={(v) => set('mirrorReverse', v)} />
              <LinkCard title="Steering wheel custom key" />
              <LinkCard title="Exterior mirror adjustment" />
              <LinkCard title="Steering wheel adjustment" />
            </Grid2>
          </Section>
          <Section title="Seat posture">
            <Grid2>
              <LinkCard title="Restore passenger seat" sub="Position 1" />
            </Grid2>
          </Section>
        </>
      )}
      {tab === 1 && (
        <Section title="Doors" first>
          <Grid2>
            {([['doorFL', 'Front left door'], ['doorFR', 'Front right door'], ['doorRL', 'Rear left door'], ['doorRR', 'Rear right door'], ['boot', 'Rear trunk'], ['frunk', 'Front trunk']] as const).map(([k, label]) => (
              <ToggleCard key={k} title={label} sub={openings[k] ? 'Open' : 'Closed'} on={openings[k]} onChange={() => toggleOpening(k)} />
            ))}
          </Grid2>
        </Section>
      )}
      {tab === 2 && (
        <Section title="Car lock" first>
          <Grid2>
            <ToggleCard title="Unlock on approach" sub="Unlocks when the key is near" on={on.autoUnlock} onChange={(v) => set('autoUnlock', v)} info />
            <ToggleCard title="Lock on leaving" sub="Locks when the key moves away" on={on.autoLock || locked} onChange={(v) => { set('autoLock', v); notify(v ? 'The car will lock when you walk away' : 'Auto lock off'); }} info />
            <ToggleCard title="Lock on leaving: close windows" sub="Windows close when the car locks" on={on.lockWindows} onChange={(v) => set('lockWindows', v)} />
            <ToggleCard title="Child lock" sub="Rear doors open only from the outside" on={on.childLock} onChange={(v) => set('childLock', v)} />
          </Grid2>
        </Section>
      )}
    </div>
  );
}

function DrivingPage({ vehicle }: PageProps) {
  const [tab, setTab] = React.useState(0);
  const { modeId, setCarMode } = useVehicleStore();
  const { on, set } = useHaLocal();
  const modes = byModeOrder(vehicle.cockpit.driveModes ?? []);
  const cur = Math.max(0, modes.findIndex((m) => m.id === (modeId ?? 'comfort')));
  return (
    <div>
      <Tabs tabs={['Driving settings', 'Scene assist']} value={tab} onChange={setTab} />
      {tab === 0 ? (
        <>
          <Hero h={340}><CarImage w={470} left={150} top={30} glow="rgba(60,140,255,0.55)" /></Hero>
          <div className="mb-[12px] text-[19px]">Drive mode</div>
          <Segmented
            label="Drive mode"
            items={modes.map((m) => m.label.replace('Shooting Brake ', '').replace(' / Slippery', ''))}
            value={cur}
            onChange={(i) => setCarMode(modes[i].id, modes[i].model)}
            sub={{ [modes.findIndex((m) => m.id === 'comfort')]: '(recommended)' }}
          />
          <p className="mt-[12px] text-[13px]" style={{ opacity: 0.6 }}>Tap the chosen mode again to see what it changes.</p>
        </>
      ) : (
        <Section title="Scene assist" first>
          <Grid2>
            <ToggleCard title="Auto hold" sub="Holds the car at a stop without the pedal" on={on.autoHold} onChange={(v) => set('autoHold', v)} info />
            <ToggleCard title="Hill descent" sub="Holds a low speed on a steep descent" on={on.hillDescent} onChange={(v) => set('hillDescent', v)} info />
            <ToggleCard title="Car wash mode" sub="Neutral, mirrors folded" on={on.carWash} onChange={(v) => set('carWash', v)} />
            <ToggleCard title="Low-speed alert tone" sub="Sounds a pedestrian alert at low speed" on={!on.lowToneOff} onChange={(v) => set('lowToneOff', !v)} />
          </Grid2>
        </Section>
      )}
    </div>
  );
}

function SoundPage() {
  const t = useAv();
  const [tab, setTab] = React.useState(0);
  const { val, setVal, on, set } = useHaLocal();
  return (
    <div>
      <Tabs tabs={['Sound effects', 'Features']} value={tab} onChange={setTab} />
      {tab === 0 ? (
        <>
          <Hero h={350}>
            <CabinImage w={520} left={190} top={-30} />
            <span className="absolute rounded-full px-[18px] py-[9px] text-[14px]" style={{ left: 340, top: 120, background: t.card }}>Drag the blue dot to adjust the sound field</span>
            <button type="button" className="absolute rounded-full px-[22px] py-[10px] text-[17px] outline-none" style={{ left: 86, top: 258, background: t.card }}>Custom ›</button>
            <span className="absolute text-[24px] font-semibold tracking-[0.14em]" style={{ left: 440, top: 258 }}>MERIDIAN</span>
            <button type="button" onClick={() => setVal('soundFx', 1)} className="absolute text-[15px] outline-none" style={{ right: 28, top: 268, color: t.blue }}>Reset</button>
          </Hero>
          <div className="mb-[12px] text-[19px]">Sound effect</div>
          <Segmented label="Sound effect" items={['Pure original', 'Luxury theatre', 'Premium enjoyment', 'Immersive cinema', 'Custom']} value={val.soundFx} onChange={(i) => setVal('soundFx', i)} />
          <p className="mt-[12px] text-[13px]" style={{ opacity: 0.6 }}>Tap Custom again to tune the sound effect.</p>
        </>
      ) : (
        <Section title="Sound features" first>
          <Grid2>
            <ToggleCard title="Speed-linked volume" sub="Raises the volume with road noise" on={on.speedVolume} onChange={(v) => set('speedVolume', v)} />
            <ToggleCard title="Touch sounds" sub="A tick when you tap the screen" on={on.touchSounds} onChange={(v) => set('touchSounds', v)} />
            <LinkCard title="Sound field position" sub="Driver, front row, all seats" />
            <LinkCard title="Equaliser" sub="Bass, mid, treble" />
          </Grid2>
        </Section>
      )}
    </div>
  );
}

function LightsPage() {
  const t = useAv();
  const [tab, setTab] = React.useState(0);
  const { ambientOn, ambientHue, ambientBrightness, setAmbient } = useVehicleStore();
  const { val, setVal, on, toggle } = useHaLocal();
  const hue = React.useRef<HTMLDivElement>(null);
  const pickHue = (e: React.PointerEvent) => {
    if (e.type === 'pointermove' && e.buttons === 0) return;
    const r = hue.current?.getBoundingClientRect();
    if (!r) return;
    setAmbient({ ambientHue: Math.round(Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)) * 360) });
  };
  return (
    <div>
      <Tabs tabs={['Interior lights', 'Exterior lights']} value={tab} onChange={setTab} />
      {tab === 0 ? (
        <>
          <Hero h={300}>
            <CabinImage w={560} left={150} top={-34} />
            <div className="absolute left-1/2 -translate-x-1/2" style={{ top: 236, width: 250 }}>
              <Segmented label="Ambient light" items={['Off', 'On', 'Auto']} value={ambientOn ? 1 : 0} onChange={(i) => setAmbient({ ambientOn: i > 0 })} />
            </div>
          </Hero>
          <Section title="Ambient light" first>
            <Segmented label="Effect" items={['Static', 'Breathing']} value={val.ambientFx} onChange={(i) => setVal('ambientFx', i)} />
            <Grid2>
              <div className="mt-[14px] rounded-[18px] px-[20px] py-[16px]" style={{ background: t.card }}>
                <div className="mb-[12px] text-[15px]" style={{ color: t.text2 }}>Brightness</div>
                <input type="range" min={0.1} max={1} step={0.05} value={ambientBrightness} onChange={(e) => setAmbient({ ambientBrightness: Number(e.target.value) })} aria-label="Ambient brightness" className="w-full accent-[#2c46f2]" />
              </div>
              <div className="mt-[14px] rounded-[18px] px-[20px] py-[16px]" style={{ background: t.card }}>
                <div className="mb-[12px] flex items-center justify-between text-[15px]" style={{ color: t.text2 }}>Colour <span style={{ color: t.blue }}>Custom</span></div>
                <div
                  ref={hue}
                  className="relative h-[22px] cursor-ew-resize touch-none rounded-full"
                  style={{ background: 'linear-gradient(90deg,#ff3b30,#ffcc00,#34c759,#00c7be,#007aff,#af52de,#ff3b30)' }}
                  onPointerDown={pickHue}
                  onPointerMove={pickHue}
                  role="slider"
                  tabIndex={0}
                  aria-label="Ambient colour"
                  aria-valuemin={0}
                  aria-valuemax={360}
                  aria-valuenow={ambientHue}
                >
                  <span className="absolute top-1/2 h-[26px] w-[26px] -translate-x-1/2 -translate-y-1/2 rounded-full border-[3px] border-white" style={{ left: `${(ambientHue / 360) * 100}%`, background: `hsl(${ambientHue} 90% 55%)`, boxShadow: '0 1px 6px rgba(0,0,0,0.35)' }} />
                </div>
              </div>
            </Grid2>
          </Section>
        </>
      ) : (
        <>
          <Hero h={330}><CarImage w={470} left={150} top={20} /></Hero>
          <div className="mb-[12px] text-[19px]">Headlamp control</div>
          <div className="flex gap-[14px]">
            <div className="flex-1">
              <Segmented label="Headlamps" items={['OFF', 'Position', 'Low beam', 'AUTO']} value={val.headlamp} onChange={(i) => setVal('headlamp', i)} />
            </div>
            <button type="button" aria-pressed={on.rearFog} onClick={() => toggle('rearFog')} className="h-[58px] w-[140px] rounded-[18px] text-[18px] outline-none" style={{ background: on.rearFog ? t.segOn : t.seg, color: t.text }}>
              Rear fog
            </button>
          </div>
          <p className="mt-[12px] text-[13px]" style={{ opacity: 0.6 }}>Lamps follow the 3D car on the Dashboard tab.</p>
        </>
      )}
    </div>
  );
}

function EnergyPage({ variant }: PageProps) {
  const t = useAv();
  const { driveMode, soc, climate } = useVehicleStore();
  const { on, toggle, set, val, setVal, notify } = useHaLocal();
  const range = effectiveRange(variant, driveMode, soc, climate);
  const pct = Math.round(soc * 100);
  return (
    <div>
      <Hero h={320}>
        <div className="absolute" style={{ left: 8, top: 34 }}>
          <div className="text-[14px]" style={{ color: t.text2 }}>Remaining range</div>
          <div><span className="tnum text-[40px] font-medium">{range ? range.km : '--'}</span> <span className="text-[15px]" style={{ color: t.text2 }}>km</span></div>
        </div>
        <CarImage w={430} left={190} top={56} />
        <div className="absolute flex items-center justify-center rounded-[10px] text-[30px] font-semibold" style={{ left: 336, top: 168, width: 170, height: 54, background: 'linear-gradient(90deg,rgba(120,190,80,0.85),rgba(190,215,110,0.75))', color: '#fff', boxShadow: '0 4px 14px rgba(60,120,40,0.35)' }}>
          {pct}<span className="text-[16px]">%</span>
        </div>
        <button type="button" onClick={() => { toggle('chargePort'); notify(on.chargePort ? 'Charge port closed' : 'Charge port open'); }} className="absolute flex items-center gap-[8px] rounded-full px-[22px] py-[12px] text-[17px] outline-none" style={{ right: 4, top: 118, background: t.segOn }}>
          <Ic.Charge size={22} /> {on.chargePort ? 'Close charge port' : 'Open charge port'}
        </button>
      </Hero>
      <Grid2>
        <ToggleCard title="Scheduled charging" sub="Every day 00:00 – 00:00" on={on.scheduledCharge} onChange={(v) => set('scheduledCharge', v)} />
        <div className="rounded-[18px] px-[20px] py-[14px]" style={{ background: t.card }}>
          <div className="text-[18px]">Charge limit</div>
          <div className="mt-[6px] flex items-center gap-[12px]">
            <input type="range" min={50} max={100} step={5} value={val.chargeLimit || 100} onChange={(e) => setVal('chargeLimit', Number(e.target.value))} aria-label="Charge limit" className="flex-1 accent-[#2c46f2]" />
            <span className="tnum text-[15px]">{val.chargeLimit || 100}%</span>
          </div>
        </div>
        <ToggleCard title="Release the charging gun when charging ends" on={on.gunRelease} onChange={(v) => set('gunRelease', v)} info />
        <LinkCard title="Stop discharging to the outside" sub="At 20%" />
      </Grid2>
    </div>
  );
}

function AssistPage() {
  return (
    <div>
      <Hero h={330}>
        <span className="absolute rounded-full" style={{ left: 190, top: 130, width: 440, height: 130, background: 'radial-gradient(ellipse at center, rgba(70,130,255,0.55), rgba(70,130,255,0) 70%)' }} />
        <CarImage w={430} left={196} top={52} />
      </Hero>
      <Grid2>
        <LinkCard title="Navigation assist" sub="Navigation and lane-cruise assist settings" tall />
        <LinkCard title="Parking assist" sub="Parking assist function settings" tall />
        <LinkCard title="Active safety" sub="Front, side and rear active-safety settings" tall />
        <LinkCard title="Surround view" sub="360° surround-view settings" tall />
      </Grid2>
    </div>
  );
}

function ScenesPage() {
  const t = useAv();
  return (
    <div>
      <div className="pt-[22px] text-[19px]">Quick scenes</div>
      <div className="flex flex-col items-center justify-center gap-[16px]" style={{ height: 420, color: t.text2 }}>
        <Ic.CarOutline size={54} style={{ opacity: 0.55 }} />
        <span className="text-[15px]">Not signed in to a Huawei account. Sign in from User Centre and try again.</span>
      </div>
    </div>
  );
}

function DisplayPage() {
  const t = useAv();
  const { hmiTheme, setHmiTheme } = useVehicleStore();
  const { val, setVal, on, set } = useHaLocal();
  const mode = on.dispAdaptive ? 0 : hmiTheme === 'dark' ? 1 : 2;
  const pick = (i: number) => {
    set('dispAdaptive', i === 0);
    if (i === 1) setHmiTheme('dark');
    else if (i === 2) setHmiTheme('light');
    else setHmiTheme(new Date().getHours() >= 7 && new Date().getHours() < 19 ? 'light' : 'dark');
  };
  const bar = (label: string, value: number, setter: (n: number) => void) => (
    <div className="rounded-[18px] px-[20px] py-[16px]" style={{ background: t.card }}>
      <div className="flex items-center justify-between text-[16px]">
        {label}
        <span className="rounded-full px-[14px] py-[4px] text-[14px] text-white" style={{ background: t.blue }}>Auto</span>
      </div>
      <div className="mt-[10px] flex items-center gap-[12px]">
        <Ic.Brightness size={20} />
        <input type="range" min={30} max={100} value={value} onChange={(e) => setter(Number(e.target.value))} aria-label={label} className="flex-1 accent-[#2c46f2]" />
        <span className="tnum text-[14px]" style={{ color: t.text2 }}>{value}%</span>
      </div>
    </div>
  );
  return (
    <div className="pt-[14px]">
      <Grid2>
        <div className="relative h-[190px] overflow-hidden rounded-[18px]" style={{ background: 'linear-gradient(180deg,#1b2650,#3a4a7e 55%,#10183a)' }}>
          <span className="absolute bottom-[10px] left-1/2 -translate-x-1/2 text-[16px] text-white">Wallpaper</span>
        </div>
        <div className="relative h-[190px] overflow-hidden rounded-[18px]" style={{ background: '#070810', color: '#fff' }}>
          <span className="absolute left-1/2 top-[56px] -translate-x-1/2 text-[34px] font-light">06:00</span>
          <span className="absolute bottom-[10px] left-1/2 -translate-x-1/2 text-[16px]">Screen saver</span>
        </div>
      </Grid2>
      <Section title="Display mode">
        <Segmented label="Display mode" items={['Adaptive', 'Dark', 'Light']} value={mode} onChange={pick} sub={{ 0: '(recommended)' }} />
      </Section>
      <Section title="Brightness">
        <Grid2>
          {bar('Centre screen', val.brightness, (n) => setVal('brightness', n))}
          {bar('Cluster screen', val.clusterBrightness, (n) => setVal('clusterBrightness', n))}
        </Grid2>
      </Section>
    </div>
  );
}

function ConnectionPage() {
  const { on, set } = useHaLocal();
  return (
    <div className="pt-[14px]">
      <Grid2>
        <ToggleCard title="Bluetooth" sub="Connected to “iPhone”" on={!on.btOff} onChange={(v) => set('btOff', !v)} />
        <ToggleCard title="WLAN" sub={on.wlan ? 'On' : 'Off'} on={on.wlan} onChange={(v) => set('wlan', v)} />
        <ToggleCard title="Hotspot" sub={on.hotspot ? 'On' : 'Off'} on={on.hotspot} onChange={(v) => set('hotspot', v)} />
        <ToggleCard title="Wireless charging" sub={on.wcOff ? 'Off' : 'On'} on={!on.wcOff} onChange={(v) => set('wcOff', !v)} />
        <LinkCard title="Huawei Share" />
      </Grid2>
      <Section title="Connected services">
        <Grid2>
          <LinkCard title="Super terminal" />
        </Grid2>
      </Section>
    </div>
  );
}

function AssistantPage() {
  const t = useAv();
  const { on, set } = useHaLocal();
  return (
    <div className="pt-[14px]">
      <div className="mb-[12px] text-[19px]">Smart voice</div>
      <Grid2>
        <div className="relative h-[168px] overflow-hidden rounded-[18px] px-[20px] py-[16px]" style={{ background: 'linear-gradient(135deg,#c3cde6,#aab7da)' }}>
          <div className="text-[18px]">Smart listening</div>
          <div className="text-[12px]" style={{ color: t.text2 }}>Listening time 30 s</div>
          <span className="absolute right-[22px] top-[40px] h-[86px] w-[86px] rounded-full border-[6px]" style={{ borderColor: 'rgba(255,255,255,0.7)' }} />
          <span className="absolute bottom-[16px] left-[20px]"><span className="inline-block"><Switch2 on={!on.listenOff} onChange={(v) => set('listenOff', !v)} /></span></span>
        </div>
        <div className="relative h-[168px] overflow-hidden rounded-[18px] px-[20px] py-[16px]" style={{ background: 'linear-gradient(135deg,#f4d9d6,#e2705f)' }}>
          <div className="text-[18px]">My assistant</div>
          <div className="text-[12px]" style={{ color: t.text2 }}>“Xiaota Xiaota” | Female voice</div>
          <span className="absolute -bottom-[34px] right-[20px] h-[110px] w-[110px] rounded-full" style={{ background: 'linear-gradient(160deg,#ff6a5a,#c4161c)' }} />
        </div>
        <ToggleCard title="Voice wake-up" sub="Wake the assistant by voice once on" on={!on.wakeOff} onChange={(v) => set('wakeOff', !v)} />
        <ToggleCard title="Smart no-wake" sub="Talk to the assistant without waking it" on={on.noWake} onChange={(v) => set('noWake', v)} />
        <ToggleCard title="Voice call announcement" sub="Announces incoming calls" on={!on.announceOff} onChange={(v) => set('announceOff', !v)} />
        <LinkCard title="Voice skills" />
        <LinkCard title="Smart recognition" />
        <LinkCard title="Dialect recognition" sub="After waking, speak in many dialects" />
      </Grid2>
    </div>
  );
}

function Switch2({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  const t = useAv();
  return (
    <button type="button" role="switch" aria-checked={on} aria-label="Smart listening" onClick={() => onChange(!on)} className="relative inline-block h-[30px] w-[54px] rounded-full outline-none" style={{ background: on ? t.blue : 'rgba(22,27,46,0.2)' }}>
      <span className="absolute top-[3px] h-[24px] w-[24px] rounded-full bg-white transition-all" style={{ left: on ? 27 : 3 }} />
    </button>
  );
}

function StatusPage() {
  const t = useAv();
  const tyre = (txt: string, style: React.CSSProperties) => (
    <span className="absolute rounded-full px-[12px] py-[4px] text-[14px]" style={{ background: t.card, ...style }}>{txt}</span>
  );
  return (
    <div>
      <Hero h={330}>
        <CarImage w={430} left={196} top={52} />
        {tyre('3.1 bar', { left: 174, top: 46 })}
        {tyre('3.0 bar', { left: 660, top: 54 })}
        {tyre('3.0 bar', { left: 196, top: 266 })}
        {tyre('3.0 bar', { left: 640, top: 266 })}
      </Hero>
      <Grid2>
        <LinkCard title="Distance to next service" sub="-- km  -- days" />
        <LinkCard title="Driven with you" sub="9 km" />
        <LinkCard title="Vehicle check" sub="Vehicle maintenance and check settings" />
        <LinkCard title="Road rescue" sub="Call the rescue centre after a fault or accident" />
      </Grid2>
    </div>
  );
}

function SystemPage({ vehicle }: PageProps) {
  const t = useAv();
  return (
    <div className="pt-[14px]">
      <div className="mb-[12px] text-[19px]">About</div>
      <Grid2>
        <div className="flex h-[168px] flex-col items-center justify-center rounded-[18px]" style={{ background: 'linear-gradient(135deg,#d6ddef,#b8c4e2)' }}>
          <div className="text-[26px] font-medium">HarmonySpace</div>
          <div className="mt-[4px] text-[13px]" style={{ color: t.text2 }}>5.0.0.106</div>
        </div>
        <div className="flex flex-col gap-[14px]">
          <LinkCard title={`My ${vehicle.brand.toUpperCase()} ${vehicle.model.replace('Avatr ', '')}`} sub="Chassis number: shown on the car only" tall />
          <LinkCard title="More system information" sub="HMS Core and others" />
        </div>
      </Grid2>
      <Section title="Update and reset">
        <Grid2>
          <LinkCard title="System update" sub="Current vehicle version REV0.8.5" />
          <LinkCard title="Reset" sub="Reset system settings and clear user data" />
        </Grid2>
      </Section>
      <Section title="Privacy">
        <Grid2>
          <LinkCard title="Permission management" />
          <LinkCard title="Privacy statement" />
        </Grid2>
      </Section>
    </div>
  );
}
