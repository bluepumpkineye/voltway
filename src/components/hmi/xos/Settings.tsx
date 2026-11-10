'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import type { LightMode } from '@/lib/lights';
import * as Ic from '../dilink/icons';
import { XO } from './theme';
import { useXo } from './shared';
import { Sheet, Split } from './Split';
import { Segment, Slider, Switch } from './Pages';

/* ---------------------------------------------------------------- the menu */

const Mic = ({ size = 20 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <rect x="9" y="3.500" width="6" height="11" rx="3" /><path d="M5.500 11.500a6.500 6.500 0 0 0 13 0M12 18v3" />
  </svg>
);

const MENU: { label: string; icon: React.ReactNode }[] = [
  { label: 'Vehicle', icon: <Ic.CarSide size={20} /> },
  { label: 'Map', icon: <Ic.Pin size={20} /> },
  { label: 'Driver assist', icon: <Ic.Wheel size={20} /> },
  { label: 'Smart voice', icon: <Mic /> },
  { label: 'Sound', icon: <Ic.Volume size={20} /> },
  { label: 'Charging', icon: <Ic.Bolt size={20} /> },
  { label: 'Smart camera', icon: <Ic.Camera size={20} /> },
  { label: 'Display', icon: <Ic.Sun size={20} /> },
  { label: 'Device connection', icon: <Ic.Link size={20} /> },
];

/* --------------------------------------------------------------- small pieces */

/** A row with the switch at its left and a line of help under the title, as the car's settings lay them out. */
function TRow({ title, sub, on, onClick, arrow }: { title: string; sub?: string; on?: boolean; onClick?: () => void; arrow?: boolean }) {
  return (
    <div className="flex items-start gap-[14px] py-[9px]">
      {on !== undefined && <span className="mt-[2px]"><Switch on={on} onClick={onClick ?? (() => undefined)} label={title} /></span>}
      <div className="min-w-0 flex-1">
        <div className="text-[16px] leading-tight">{title}</div>
        {sub && <div className="mt-[3px] text-[12px] leading-snug" style={{ color: XO.text3 }}>{sub}</div>}
      </div>
      {arrow && <span className="pt-[2px] text-[20px] leading-none" style={{ color: XO.text3 }} aria-hidden>›</span>}
    </div>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return <div className="mb-[8px] mt-[14px] text-[13px]" style={{ color: XO.text3 }}>{children}</div>;
}

function SegRow({ label, options, value, onPick, minW = 96 }: { label: string; options: string[]; value: number; onPick: (i: number) => void; minW?: number }) {
  return (
    <div>
      <Label>{label}</Label>
      <Segment options={options} value={value} onPick={onPick} minW={minW} />
    </div>
  );
}

/** The tabs along the top of a page (Map, Driver assist). */
function PageTabs({ tabs, value, onPick, extra }: { tabs: string[]; value: number; onPick: (i: number) => void; extra?: React.ReactNode }) {
  return (
    <div className="mb-[14px] flex items-center gap-[30px] text-[16px]" role="tablist">
      {tabs.map((x, i) => (
        <button key={x} role="tab" aria-selected={value === i} type="button" onClick={() => onPick(i)} className="relative pb-[6px] focus:outline-none" style={{ color: value === i ? XO.text : XO.text3 }}>
          {x}
          {value === i && <span className="absolute inset-x-0 bottom-0 h-[2px] rounded-full" style={{ background: XO.text }} />}
        </button>
      ))}
      <span className="ml-auto">{extra}</span>
    </div>
  );
}

/** A photographic tile of the Vehicle page; the car's own are photographs, these are drawn / the car's render. */
function Tile({ label, sub, h, bg, onClick, children }: { label: string; sub?: string; h: number; bg: string; onClick: () => void; children?: React.ReactNode }) {
  return (
    <button type="button" onClick={onClick} className="relative block w-full overflow-hidden rounded-[10px] text-left text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-black/40" style={{ height: h, background: bg }}>
      {children}
      <span className="absolute left-[14px] top-[11px] text-[14px] leading-tight">{label}</span>
      {sub && <span className="absolute left-[14px] top-[30px] text-[10px] uppercase tracking-wider opacity-60">{sub}</span>}
    </button>
  );
}

/* ------------------------------------------------------------------ the page */

/**
 * Settings (c10_0030-48): the car panel stays at the left; the right panel is a sheet with the nine-item
 * menu down its left side and the page beside it. Vehicle is a grid of tiles that open deeper pages
 * (Driving mode, Unlock & welcome, Ambient lights, Lights, Doors & windows, Seats & steering wheel,
 * Maintenance), each with a back header; Map, Driver assist and the others are pages of switches and
 * selectors with tabs where the car has them. The controls the 3D car has (the modes, the lamps, the
 * doors, the ambient light) write the shared store.
 */
export function SettingsPage({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  const { val, setVal } = useXo();
  const page = val.setPage;
  const sub = val.subPage;
  const ref = React.useRef<HTMLDivElement>(null);
  React.useEffect(() => {
    ref.current?.scrollTo({ top: 0 });
  }, [page, sub]);

  return (
    <Split vehicle={vehicle}>
      <Sheet>
        <nav className="absolute flex flex-col" style={{ left: 12, top: 18, width: 168 }} aria-label="Settings">
          {MENU.map((m, i) => (
            <button
              key={m.label}
              type="button"
              aria-current={page === i ? 'page' : undefined}
              onClick={() => { setVal('setPage', i); setVal('subPage', 0); setVal('tab', 0); }}
              className="mb-[10px] flex h-[56px] items-center gap-[12px] rounded-[10px] px-[14px] text-left text-[14px] focus:outline-none focus-visible:ring-2 focus-visible:ring-black/30"
              style={{ background: page === i ? '#f7f7fc' : 'transparent', boxShadow: page === i ? '0 1px 5px rgba(30,30,70,0.12)' : undefined, color: page === i ? XO.text : XO.text2 }}
            >
              <span className="shrink-0">{m.icon}</span>
              <span className="truncate">{m.label}</span>
            </button>
          ))}
        </nav>
        <div ref={ref} className="absolute overflow-y-auto pr-[6px]" style={{ left: 200, right: 14, top: 18, bottom: 14, scrollbarWidth: 'none' }}>
          <Body page={page} sub={sub} vehicle={vehicle} variant={variant} />
        </div>
      </Sheet>
    </Split>
  );
}

function Back({ title }: { title: string }) {
  const { setVal } = useXo();
  return (
    <button type="button" onClick={() => setVal('subPage', 0)} className="mb-[14px] flex items-center gap-[10px] text-[17px] focus:outline-none">
      <Ic.Chev dir="l" size={16} /> {title}
    </button>
  );
}

function Body({ page, sub, vehicle, variant }: { page: number; sub: number; vehicle: Vehicle; variant: Variant }) {
  const { val, setVal, on, toggle, set, notify } = useXo();
  const {
    driveMode, modeId, setCarMode, ambientOn, ambientHue, ambientBrightness, setAmbient, soc, media, patchMedia,
    lightMode, setLightMode, locked, setLocked, openings, toggleOpening, setHmiScreen,
  } = useVehicleStore();
  const modes = vehicle.cockpit.driveModes ?? [];
  const current = modes.findIndex((m) => (modeId ? m.id === modeId : m.model === driveMode));
  const hasChassis = (vehicle.tech ?? []).some((d) => d.driver === 'uturn' || d.driver === 'park');
  const lampSel = lightMode === 'off' ? 0 : lightMode === 'position' ? 1 : lightMode === 'low' ? 2 : 3;
  const LAMPS: LightMode[] = ['off', 'position', 'low', 'auto'];

  /* ---- Vehicle ---- */
  if (page === 0 && sub === 0) {
    return (
      <div className="flex gap-[14px]">
        <div className="flex flex-1 flex-col gap-[14px]">
          <Tile label="Driving mode" sub={modes[current]?.label ?? 'Standard'} h={206} bg="linear-gradient(145deg,#6a5ca8,#3a2f6e)" onClick={() => setVal('subPage', 1)}>
            <span className="absolute inset-0 opacity-25" style={{ backgroundImage: 'repeating-conic-gradient(rgba(255,255,255,0.35) 0% 25%, transparent 0% 50%)', backgroundSize: '56px 56px' }} />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={`/hmi/${vehicle.slug}/car34.webp`} alt="" draggable={false} className="absolute max-w-none" style={{ width: 300, left: 40, top: 70 }} />
          </Tile>
          <Tile label="Lights" h={100} bg="linear-gradient(145deg,#8d99ab,#5d697c)" onClick={() => setVal('subPage', 4)}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={`/hmi/${vehicle.slug}/car34.webp`} alt="" draggable={false} className="absolute max-w-none" style={{ width: 250, left: 100, top: 10 }} />
          </Tile>
          <Tile label="Seats & steering wheel" h={99} bg="linear-gradient(145deg,#9a9fae,#6c7283)" onClick={() => setVal('subPage', 6)}>
            <svg className="absolute" style={{ right: 20, top: 14 }} width="110" height="74" viewBox="0 0 110 74" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M20 66h70M40 10c14 0 22 8 22 22l4 22H20" /></svg>
          </Tile>
          {hasChassis && (
            <Tile label="Rear-wheel steering" sub="Demonstration" h={99} bg="linear-gradient(145deg,#6f8aa8,#4c6685)" onClick={() => setHmiScreen('chassis')} />
          )}
        </div>
        <div className="flex flex-1 flex-col gap-[14px]">
          <Tile label="Unlock & welcome" h={94} bg="linear-gradient(145deg,#8a8378,#4f4a44)" onClick={() => setVal('subPage', 2)}>
            <span className="absolute right-[18px] top-[10px] h-[70px] w-[90px] opacity-50" style={{ background: 'repeating-linear-gradient(100deg, rgba(255,255,255,0.7) 0 3px, transparent 3px 11px)' }} />
          </Tile>
          <Tile label="Ambient light" h={96} bg="linear-gradient(145deg,#caa88a,#a9795a)" onClick={() => setVal('subPage', 3)}>
            <span className="absolute inset-y-0 right-0 w-[140px] opacity-55" style={{ background: 'repeating-linear-gradient(90deg, rgba(255,235,210,0.9) 0 6px, transparent 6px 18px)', maskImage: 'linear-gradient(90deg, transparent, #000)', WebkitMaskImage: 'linear-gradient(90deg, transparent, #000)' }} />
          </Tile>
          <Tile label="Doors & windows" h={100} bg="linear-gradient(145deg,#7a828f,#4c5361)" onClick={() => setVal('subPage', 5)}>
            <svg className="absolute" style={{ right: 16, top: 12 }} width="96" height="80" viewBox="0 0 96 80" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M20 70V18l50-8v60zM70 10l20 12v52L70 70" /></svg>
          </Tile>
          <Tile label="Maintenance" h={101} bg="linear-gradient(145deg,#8b8d97,#5a5c68)" onClick={() => setVal('subPage', 7)}>
            <svg className="absolute" style={{ right: 20, top: 16 }} width="84" height="76" viewBox="0 0 84 76" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M14 62 46 30M52 12a14 14 0 0 1 18 18l-8-2-4-8z" /></svg>
          </Tile>
        </div>
      </div>
    );
  }

  /* ---- Vehicle > Driving mode ---- */
  if (page === 0 && sub === 1) {
    const order = ['eco', 'standard', 'sport', 'off-road', 'custom'];
    const list = [...modes].sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id));
    return (
      <div>
        <Back title="Driving mode" />
        <div className="flex gap-[10px]">
          {list.map((m) => {
            const sel = (modeId ?? modes[current]?.id) === m.id;
            return (
              <button key={m.id} type="button" onClick={() => setCarMode(m.id, m.model)} aria-pressed={sel} className="flex h-[66px] flex-1 flex-col items-center justify-center gap-[5px] rounded-[10px] text-[12px] focus:outline-none focus-visible:ring-2 focus-visible:ring-black/30" style={{ background: sel ? XO.indigo : 'rgba(26,28,38,0.1)', color: sel ? '#fff' : XO.text }}>
                {m.id === 'eco' ? <Ic.Leaf size={20} /> : m.id === 'sport' ? <Ic.Bolt size={20} /> : m.id === 'custom' ? <Ic.User size={20} /> : <Ic.CarSide size={20} />}
                {m.label}
              </button>
            );
          })}
        </div>
        <SegRow label="Power response" options={['Eco', 'Comfort', 'Sport']} value={val.power} onPick={(i) => setVal('power', i)} minW={150} />
        <SegRow label="Steering assist" options={['Light', 'Moderate', 'Firm']} value={val.steer} onPick={(i) => setVal('steer', i)} minW={150} />
        <SegRow label="Brake pedal feel" options={['Smooth', 'Moderate', 'Sensitive']} value={val.brake} onPick={(i) => setVal('brake', i)} minW={150} />
        <SegRow label="Ride" options={['Comfort', 'Standard', 'Firm']} value={val.ride === 0 ? 1 : val.ride} onPick={(i) => setVal('ride', i)} minW={150} />
      </div>
    );
  }

  /* ---- Vehicle > Unlock & welcome ---- */
  if (page === 0 && sub === 2) {
    return (
      <div>
        <Back title="Unlock & welcome" />
        <Label>Door lock</Label>
        <TRow title="Locked" sub="Tap to unlock or lock the showroom car" on={locked} onClick={() => setLocked(!locked)} />
        <SegRow label="Unlock feedback" options={['Flash', 'Flash + beep', 'Flash + horn']} value={val.unlockFb === 0 && !on.unlockSet ? 1 : val.unlockFb} onPick={(i) => { setVal('unlockFb', i); set('unlockSet', true); }} minW={152} />
        <SegRow label="Lock feedback" options={['Flash', 'Flash + beep', 'Flash + horn']} value={val.lockFb === 0 && !on.lockSet ? 1 : val.lockFb} onPick={(i) => { setVal('lockFb', i); set('lockSet', true); }} minW={152} />
        <SegRow label="Opening a door from inside" options={['Single tap', 'Double tap']} value={val.doorTap === 0 && !on.tapSet ? 1 : val.doorTap} onPick={(i) => { setVal('doorTap', i); set('tapSet', true); }} minW={234} />
        <TRow title="Unlock automatically in P" sub="With the car in P, the doors unlock when you press the brake and hold the handle" on={on.autoUnlockP} onClick={() => toggle('autoUnlockP')} />
      </div>
    );
  }

  /* ---- Vehicle > Ambient light ---- */
  if (page === 0 && sub === 3) {
    return (
      <div>
        <Back title="Ambient light" />
        <div className="flex items-center gap-[14px]">
          <button type="button" aria-label="Ambient light" aria-pressed={ambientOn} onClick={() => setAmbient({ ambientOn: !ambientOn })} className="flex h-[40px] w-[40px] items-center justify-center rounded-[10px] text-white focus:outline-none" style={{ background: ambientOn ? XO.green : 'rgba(26,28,38,0.3)' }}><Ic.Power size={20} /></button>
          <Ic.Sun size={18} />
          <Slider value={Math.round(ambientBrightness * 100)} onChange={(n) => setAmbient({ ambientBrightness: n / 100 })} label="Ambient brightness" w={380} />
        </div>
        <div className="mt-[8px]"><TRow title="Crystal star band" sub="The field of lights across the dash" on={ambientOn} onClick={() => setAmbient({ ambientOn: !ambientOn })} /></div>
        <SegRow label="Mode" options={['Fixed brightness', 'Breathing', 'Follows speed', 'Music rhythm']} value={val.ambMode} onPick={(i) => setVal('ambMode', i)} minW={132} />
        <SegRow label="Colour" options={['Theme', 'Fixed', 'Cycling']} value={val.ambColour === 0 && !on.colSet ? 1 : val.ambColour} onPick={(i) => { setVal('ambColour', i); set('colSet', true); }} minW={170} />
        <div className="mt-[14px]"><Slider value={ambientHue} min={0} max={360} onChange={(n) => setAmbient({ ambientHue: n })} label="Ambient colour" w={380} /></div>
      </div>
    );
  }

  /* ---- Vehicle > Lights ---- */
  if (page === 0 && sub === 4) {
    return (
      <div>
        <Back title="Lights" />
        <Label>Headlamp control</Label>
        <div className="flex gap-[8px]">
          <div className="flex-1">
            <Segment options={['Off', 'Position', 'Low beam', 'Auto']} value={lampSel} onPick={(i) => setLightMode(LAMPS[i])} minW={104} />
          </div>
          <button type="button" aria-pressed={on.rearFog} onClick={() => toggle('rearFog')} className="h-[38px] rounded-[10px] px-4 text-[15px] focus:outline-none" style={{ background: on.rearFog ? '#fff' : 'rgba(26,28,38,0.08)', boxShadow: on.rearFog ? '0 1px 4px rgba(0,0,0,0.14)' : undefined }}>Rear fog</button>
        </div>
        <TRow title="Light-sword mode" sub="With the headlamps on, the daytime lights rise in brightness; a screen prompt asks you to turn it on" on={on.lightSword} onClick={() => toggle('lightSword')} />
        <TRow title="Smart high beam" sub="Switches between high and low beam by itself and dips for traffic" on={on.smartBeam} onClick={() => toggle('smartBeam')} />
        <Label>Reading lights</Label>
        <TRow title="Reading lights" on={on.reading} onClick={() => toggle('reading')} />
      </div>
    );
  }

  /* ---- Vehicle > Doors & windows ---- */
  if (page === 0 && sub === 5) {
    const door = (k: 'doorFL' | 'doorFR' | 'doorRL' | 'doorRR', label: string) => (
      <button key={k} type="button" aria-pressed={openings[k]} onClick={() => toggleOpening(k)} className="h-[48px] flex-1 rounded-[10px] text-[14px] focus:outline-none" style={{ background: openings[k] ? '#fff' : 'rgba(26,28,38,0.1)', boxShadow: openings[k] ? '0 1px 4px rgba(0,0,0,0.14)' : undefined }}>{label}</button>
    );
    const top = [
      { id: 'lock', label: 'Door lock', icon: locked ? <Ic.Lock size={20} /> : <Ic.Unlock size={20} />, active: !locked, fn: () => setLocked(!locked) },
      { id: 'frunk', label: 'Front trunk', icon: <Ic.CarSide size={20} />, active: openings.frunk, fn: () => toggleOpening('frunk') },
      { id: 'boot', label: 'Rear trunk', icon: <Ic.CarSide size={20} />, active: openings.boot, fn: () => toggleOpening('boot') },
      { id: 'port', label: 'Charge port cover', icon: <Ic.Bolt size={20} />, active: openings.charge, fn: () => toggleOpening('charge') },
    ];
    return (
      <div>
        <Back title="Doors & windows" />
        <div className="flex gap-[10px]">
          {top.map((x) => (
            <button key={x.id} type="button" aria-pressed={x.active} onClick={x.fn} className="flex h-[64px] flex-1 flex-col items-center justify-center gap-[4px] rounded-[10px] text-[12px] focus:outline-none" style={{ background: x.active ? '#fff' : 'rgba(26,28,38,0.1)', boxShadow: x.active ? '0 1px 4px rgba(0,0,0,0.14)' : undefined }}>
              {x.icon}{x.label}
            </button>
          ))}
        </div>
        <Label>Doors</Label>
        <div className="flex gap-[10px]">{door('doorFL', 'Front left')}{door('doorFR', 'Front right')}</div>
        <div className="mt-[10px] flex gap-[10px]">{door('doorRL', 'Rear left')}{door('doorRR', 'Rear right')}</div>
        <Label>Quick controls</Label>
        <div className="flex gap-[10px]">
          {[['child', 'Child lock'], ['shade', 'Sunshade']].map(([id, label]) => (
            <button key={id} type="button" aria-pressed={on[id]} onClick={() => toggle(id)} className="h-[64px] flex-1 rounded-[10px] px-4 text-left text-[14px] focus:outline-none" style={{ background: on[id] ? '#fff' : 'rgba(26,28,38,0.1)' }}>{label}</button>
          ))}
        </div>
      </div>
    );
  }

  /* ---- Vehicle > Seats & steering wheel ---- */
  if (page === 0 && sub === 6) {
    return (
      <div>
        <Back title="Seats & steering wheel" />
        <Label>Position</Label>
        <div className="grid grid-cols-2 gap-[10px]">
          {['Exterior mirror adjust', 'Interior mirror adjust', 'Steering wheel adjust', 'HUD adjust', 'Seat adjust'].map((x) => (
            <button key={x} type="button" onClick={() => notify(`${x} is not part of the showroom demo`)} className="h-[64px] rounded-[10px] px-4 text-left text-[14px] focus:outline-none" style={{ background: 'rgba(26,28,38,0.1)' }}>{x}</button>
          ))}
        </div>
        <Label>Safety belt</Label>
        <TRow title="Rear seat-belt reminder" arrow />
        <Label>Driver seat</Label>
        <TRow title="Adaptive fit" sub="The seat reads how your weight sits and adjusts the support so the load is more even" on={!on.fitOff} onClick={() => toggle('fitOff')} />
      </div>
    );
  }

  /* ---- Vehicle > Maintenance ---- */
  if (page === 0 && sub === 7) {
    return (
      <div>
        <Back title="Maintenance" />
        <TRow title="Wiper service mode" on={on.wiperService} onClick={() => toggle('wiperService')} />
        <TRow title="Suspension service mode" on={on.suspService} onClick={() => toggle('suspService')} />
        <TRow title="Pet mode" sub="After you leave, the car keeps the cabin temperature; do not leave a pet in the car for long" arrow />
        <TRow title="Rescue mode" sub="Guides the safe unlocking of the car for towing" arrow />
        <Label>Vehicle power off</Label>
        <button type="button" onClick={() => notify('The showroom car stays on')} className="flex h-[46px] items-center gap-2 rounded-[10px] px-6 text-[15px] focus:outline-none" style={{ background: 'rgba(26,28,38,0.12)' }}><Ic.Power size={17} /> Power off</button>
      </div>
    );
  }

  /* ---- Map ---- */
  if (page === 1) {
    const tab = val.tab;
    return (
      <div>
        <PageTabs tabs={['Navigation', 'Personalise', 'Safety']} value={tab} onPick={(i) => setVal('tab', i)} />
        {tab === 0 && (
          <>
            <Label>Route preference</Label>
            <div className="grid grid-cols-3 gap-[8px]">
              {['Smart pick', 'Highways first', 'No highways'].map((x, i) => (
                <button key={x} type="button" aria-pressed={val.route === i} onClick={() => setVal('route', i)} className="h-[40px] rounded-[10px] text-[14px] focus:outline-none" style={{ background: val.route === i ? '#fff' : 'rgba(26,28,38,0.1)', boxShadow: val.route === i ? '0 1px 4px rgba(0,0,0,0.14)' : undefined }}>{x}</button>
              ))}
            </div>
            <div className="mt-[8px] grid grid-cols-4 gap-[8px]">
              {['Avoid jams', 'Fewer tolls', 'Main roads', 'Fastest'].map((x, i) => (
                <button key={x} type="button" aria-pressed={val.route === i + 3} onClick={() => setVal('route', i + 3)} className="h-[40px] rounded-[10px] text-[14px] focus:outline-none" style={{ background: val.route === i + 3 ? '#fff' : 'rgba(26,28,38,0.1)', boxShadow: val.route === i + 3 ? '0 1px 4px rgba(0,0,0,0.14)' : undefined }}>{x}</button>
              ))}
            </div>
            <div className="mt-[10px]"><TRow title="Avoid restricted roads" on={on.avoidRestr} onClick={() => toggle('avoidRestr')} /></div>
            <TRow title="Licence plate" arrow />
            <TRow title="Parking recommendation" sub="When navigation nears the destination it suggests the nearest car parks" on={!on.parkRecOff} onClick={() => toggle('parkRecOff')} />
          </>
        )}
        {tab === 1 && (
          <>
            <TRow title="Day and night mode" sub="Follows the sunrise and sunset" on={!on.mapNightOff} onClick={() => toggle('mapNightOff')} />
            <TRow title="3D buildings" on={on.map3d} onClick={() => toggle('map3d')} />
            <TRow title="Heading-up by default" on={!on.northOff} onClick={() => toggle('northOff')} />
          </>
        )}
        {tab === 2 && (
          <>
            <TRow title="Speed-camera reminders" on={!on.camOff} onClick={() => toggle('camOff')} />
            <TRow title="Speed limit reminders" on={!on.limitOff} onClick={() => toggle('limitOff')} />
          </>
        )}
      </div>
    );
  }

  /* ---- Driver assist ---- */
  if (page === 2) {
    const tab = val.tab;
    return (
      <div>
        <PageTabs tabs={['Driving scenes', 'Parking scenes', 'Active safety']} value={tab} onPick={(i) => setVal('tab', i)} extra={<span className="text-[12px]" style={{ color: XO.text3 }}>Safety test · Help</span>} />
        <div className="mb-[8px] flex items-center justify-between rounded-[10px] px-[14px] py-[10px] text-[15px]" style={{ background: 'linear-gradient(90deg,#dfe9f6,#c8dcf2 60%,#b8d3ee)' }}>
          <span className="flex items-center gap-[10px]"><span className="rounded-[4px] px-[6px] py-[1px] text-[10px] font-semibold text-white" style={{ background: '#3a79d8' }}>Ultra</span>VLA 2.0</span>
          <span className="text-[11px]" style={{ color: XO.text2 }}>See what is new ›</span>
        </div>
        {tab === 0 && (
          <>
            <Label>Assisted driving function</Label>
            <Segment options={['Off', 'Lane-centring assist', 'Full-scene assisted driving']} value={val.pilot} onPick={(i) => setVal('pilot', i)} minW={176} />
            <Label>General settings</Label>
            <SegRow label="Voice broadcast mode" options={['Detailed', 'Concise']} value={val.voiceMode} onPick={(i) => setVal('voiceMode', i)} minW={258} />
            <div className="mt-[10px]"><TRow title="Assisted-driving lights" sub="The light strip shows what the assist is doing" on={!on.pilotLightOff} onClick={() => toggle('pilotLightOff')} /></div>
          </>
        )}
        {tab === 1 && (
          <>
            <Label>Parking function</Label>
            <TRow title="Assisted parking" sub="Parks the car in a perpendicular, parallel or angled space, and follows a learned route" on={on.assistPark} onClick={() => toggle('assistPark')} />
            <Label>Parking settings</Label>
            <TRow title="Keep the image when shifting to reverse" sub="The camera picture stays for a moment as you shift, so you can look" on={!on.keepImgOff} onClick={() => toggle('keepImgOff')} />
            <SegRow label="Parking prompt tone" options={['Voice', 'Sound']} value={val.parkTone} onPick={(i) => setVal('parkTone', i)} minW={300} />
          </>
        )}
        {tab === 2 && (
          <>
            <Label>Forward safety</Label>
            <TRow title="Forward collision warning" sub="Warns of a collision ahead and helps brake" on={!on.fcwOff} onClick={() => toggle('fcwOff')} />
            <SegRow label="Warning sensitivity" options={['Low', 'Medium', 'High']} value={val.fcw === 0 && !on.fcwSet ? 2 : val.fcw} onPick={(i) => { setVal('fcw', i); set('fcwSet', true); }} minW={150} />
            <TRow title="Emergency steering avoidance" sub="In an emergency, steers round the obstacle if it must" on={!on.esaOff} onClick={() => toggle('esaOff')} />
            <TRow title="Start-off collision avoidance" sub="Limits acceleration if there is an obstacle ahead as you pull away" on={!on.socaOff} onClick={() => toggle('socaOff')} />
          </>
        )}
      </div>
    );
  }

  /* ---- Smart voice ---- */
  if (page === 3) {
    return (
      <div>
        <Label>Smart voice</Label>
        <TRow title="Xiao P smart voice service" sub="The new voice service: dialogue backed by a large model" on={!on.voiceOff} onClick={() => toggle('voiceOff')} />
        <Label>Wake-up</Label>
        <TRow title="“Hello Xiao P” wake-up" sub="Say “Hello Xiao P” to wake the voice assistant" on={!on.wakeOff} onClick={() => toggle('wakeOff')} />
        <TRow title="“Xiao P+” smart wake-up" sub="Say “Xiao P+” and then the usual car commands, with no second wake" on={!on.wakePlusOff} onClick={() => toggle('wakePlusOff')} />
        <TRow title="Command wake-up" sub="Say a clear command (the windows, the climate) to wake and run it at once" on={!on.cmdWakeOff} onClick={() => toggle('cmdWakeOff')} />
        <Label>Personalise</Label>
        <TRow title="Xiao P stays on screen" sub="The mascot stays at the corner of the screen when the car is in P" on={!on.mascotOff} onClick={() => toggle('mascotOff')} />
      </div>
    );
  }

  /* ---- Sound ---- */
  if (page === 4) {
    return (
      <div>
        <Label>Volume</Label>
        <Slider value={media.volume} onChange={(n) => patchMedia({ volume: n })} label="Volume" w={400} />
        <SegRow label="Sound field" options={['Driver', 'Front', 'Whole car']} value={val.field === 0 && !on.fieldSet ? 1 : val.field} onPick={(i) => { setVal('field', i); set('fieldSet', true); }} minW={130} />
        <SegRow label="Sound effect" options={['Standard', 'Vocal', 'Concert']} value={val.fx} onPick={(i) => setVal('fx', i)} minW={130} />
        <div className="mt-[10px]"><TRow title="Speed-linked volume" on={!on.svOff} onClick={() => toggle('svOff')} /></div>
      </div>
    );
  }

  /* ---- Charging ---- */
  if (page === 5) {
    return (
      <div>
        <div className="flex items-end gap-6 rounded-[12px] px-6 py-4" style={{ background: XO.card }}>
          <span className="tnum text-[56px] font-light leading-none">{Math.round(soc * 100)}<span className="text-[24px]">%</span></span>
          <span className="pb-2 text-[16px]" style={{ color: XO.text2 }}>{variant.name}</span>
        </div>
        <SegRow label="Charge limit" options={['80%', '90%', '100%']} value={val.limit === 0 && !on.limSet ? 1 : val.limit} onPick={(i) => { setVal('limit', i); set('limSet', true); }} minW={130} />
        <div className="mt-[10px]"><TRow title="Scheduled charging" sub="Start charging at the off-peak time" on={on.sched} onClick={() => toggle('sched')} /></div>
        <TRow title="Discharge to the outside" sub="Stops at 20%" arrow />
      </div>
    );
  }

  /* ---- Smart camera ---- */
  if (page === 6) {
    return (
      <div>
        <TRow title="Dashcam recording" sub="Records the road ahead while you drive" on={!on.dashOff} onClick={() => toggle('dashOff')} />
        <TRow title="Sentry mode" sub="Watches the car while it is parked" on={on.sentry} onClick={() => toggle('sentry')} />
        <TRow title="360 view on shifting to reverse" on={!on.revViewOff} onClick={() => toggle('revViewOff')} />
        <div className="mt-[12px]">
          <button type="button" onClick={() => setHmiScreen('camera')} className="h-[44px] rounded-[10px] px-6 text-[15px] focus:outline-none" style={{ background: 'rgba(26,28,38,0.12)' }}>Open the 360 camera</button>
        </div>
      </div>
    );
  }

  /* ---- Display ---- */
  if (page === 7) {
    return (
      <div>
        <Label>Screen brightness</Label>
        <Slider value={val.brightness} min={30} onChange={(n) => setVal('brightness', n)} label="Screen brightness" w={400} />
        <SegRow label="Theme" options={['Light', 'Dark', 'Auto']} value={val.theme} onPick={(i) => setVal('theme', i)} minW={130} />
        <div className="mt-[10px]"><TRow title="Head-up display" on={on.hud} onClick={() => toggle('hud')} /></div>
      </div>
    );
  }

  /* ---- Device connection ---- */
  return (
    <div>
      <TRow title="Bluetooth" sub="Connected: iPhone" on={!on.btOff} onClick={() => toggle('btOff')} />
      <TRow title="WLAN" on={on.wlan} onClick={() => toggle('wlan')} />
      <TRow title="Hotspot" on={on.hotspot} onClick={() => toggle('hotspot')} />
      <Label>System</Label>
      <TRow title="Model" sub={`${vehicle.brand} ${vehicle.model} ${vehicle.year}`} />
      <TRow title="Operating system" sub={vehicle.cockpit.os} arrow />
      <TRow title="Software" sub="This is a showroom demonstration" arrow />
    </div>
  );
}

