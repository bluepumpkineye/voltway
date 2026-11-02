'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore, type SettingsPage } from '@/store/vehicle-store';
import { useHaLocal } from '../harmonyos/shared';
import * as Ic from './icons';
import { useBy, BAR_H, STATUS_H } from './theme';
import { CarImage, Heading, Segmented, SideMenu, Tabs, ToggleRow, ValueRow } from './ui';

type SectionId = 'connection' | 'assist' | 'energy' | 'vehicle' | 'status';

const MENU: { id: SectionId; label: string; icon: React.ReactNode }[] = [
  { id: 'connection', label: 'DiLink', icon: <Ic.MenuDilink size={20} /> },
  { id: 'assist', label: 'DiPilot', icon: <Ic.MenuPilot size={20} /> },
  { id: 'energy', label: 'New energy', icon: <Ic.MenuEnergy size={20} /> },
  { id: 'vehicle', label: 'Vehicle settings', icon: <Ic.MenuCar size={20} /> },
  { id: 'status', label: 'Vehicle health', icon: <Ic.MenuHealth size={20} /> },
];

const TABS: Record<SectionId, string[]> = {
  connection: ['Connectivity', 'Audio', 'Cloud control', 'Display', 'Version', 'System', 'App management', 'Help'],
  assist: ['Driving assist', 'Safety assist', 'Parking assist'],
  energy: ['Energy management', 'Charge & discharge', 'Consumption'],
  vehicle: ['Smart chassis', 'Lights', 'Comfortable driving', 'Instrument', 'Cabin sensing', 'A/C', 'Seats', 'Doors & locks', 'Smart reminders'],
  status: ['Smart maintenance', 'Inspection', 'Vehicle info'],
};

/** The store's page ids the other skins use, onto this menu and the tab each opens. */
const ALIAS: Partial<Record<SettingsPage, [SectionId, number]>> = {
  connection: ['connection', 0], assist: ['assist', 0], energy: ['energy', 0], vehicle: ['vehicle', 0], status: ['status', 0],
  sound: ['connection', 1], display: ['connection', 3], system: ['connection', 5], assistant: ['connection', 2], personalise: ['connection', 3],
  lights: ['vehicle', 1], driving: ['vehicle', 2], doors: ['vehicle', 7], charging: ['energy', 1], scenes: ['connection', 2],
};

type PageProps = { vehicle: Vehicle; variant: Variant };

/**
 * Settings (s_0030-34, s_0096-99): a search box and five sections down the left (DiLink, DiPilot, New energy,
 * Vehicle settings, Vehicle health), the section's tabs along the top and the tab's controls under them, with
 * a picture at the right. The controls that have a counterpart in the 3D car (the headlamps, the drive mode,
 * the ambient light, the doors, the day and night mode) write the shared store; the rest keep their state on
 * the screen only, and a row that would open a deeper page says so.
 */
export function SettingsApp({ vehicle, variant }: PageProps) {
  const t = useBy();
  const { settingsPage, openSettings } = useVehicleStore();
  const [sec, startTab] = ALIAS[settingsPage] ?? ['connection', 0];
  const [tab, setTab] = React.useState(startTab);
  React.useEffect(() => setTab(startTab), [settingsPage, startTab]);
  const go = (id: string) => openSettings(id as SettingsPage);

  return (
    <div className="absolute inset-0" style={{ background: t.bg, color: t.text }}>
      <SideMenu items={MENU} value={sec} onChange={go} style={{ left: 26, top: STATUS_H + 10, width: 218 }} />
      <Tabs tabs={TABS[sec]} value={tab} onChange={setTab} className="absolute flex gap-[40px] overflow-x-auto" style={{ left: 290, right: 30, top: STATUS_H + 24, scrollbarWidth: 'none' }} />
      <div className="absolute overflow-y-auto pr-[30px]" style={{ left: 290, right: 0, top: STATUS_H + 82, bottom: BAR_H + 8, scrollbarWidth: 'none' }}>
        <Page sec={sec} tab={tab} vehicle={vehicle} variant={variant} />
      </div>
    </div>
  );
}

/** A switch row that keeps its state on the screen; `on` says whether it starts on. */
function Sw({ title, sub, id, start = false }: { title: string; sub?: string; id: string; start?: boolean }) {
  const { on, set } = useHaLocal();
  const key = start ? `${id}Off` : id;
  const v = start ? !on[key] : on[key];
  return <ToggleRow title={title} sub={sub} on={v} onChange={(n) => set(key, start ? !n : n)} />;
}

/** The picture at the right of a page: the car on a faint light. */
function Side({ children }: { children?: React.ReactNode }) {
  return <div className="pointer-events-none absolute" style={{ left: 500, top: 0, width: 440, height: 360 }}>{children}</div>;
}

function Page({ sec, tab, vehicle }: PageProps & { sec: SectionId; tab: number }) {
  const t = useBy();
  const { on, set, val, setVal, notify } = useHaLocal();
  const { hmiTheme, setHmiTheme, modeId, setCarMode, openings, toggleOpening, locked, setLocked, ambientOn, setAmbient, soc } = useVehicleStore();

  if (sec === 'connection') {
    if (tab === 0) {
      return (
        <div className="relative max-w-[640px]">
          <ValueRow title="Bluetooth" value={on.btOff ? 'Off' : 'Connected: iPhone'} onClick={() => set('btOff', !on.btOff)} />
          <ValueRow title="Wireless network" value={on.wifiOff ? 'Off' : 'On'} onClick={() => set('wifiOff', !on.wifiOff)} />
          <ValueRow title="Personal hotspot" value={on.hotspot ? 'On' : 'Off'} onClick={() => set('hotspot', !on.hotspot)} />
          <Sw title="Mobile data" id="mobileData" start />
          <svg className="pointer-events-none absolute" style={{ left: 640, top: 40 }} width="260" height="260" viewBox="0 0 260 260" aria-hidden>
            <circle cx="130" cy="130" r="96" fill="none" stroke={t.text3} strokeWidth="2" />
            <circle cx="130" cy="130" r="64" fill="none" stroke={t.text3} strokeWidth="2" />
            <path d="M130 70l30 130h-60zM116 160h28M110 182h40" fill="none" stroke={t.accent} strokeWidth="5" strokeLinejoin="round" />
          </svg>
        </div>
      );
    }
    if (tab === 1) {
      return (
        <div className="max-w-[640px]">
          <Heading>Sound effect</Heading>
          <Segmented label="Sound effect" items={['Standard', 'Vocal', 'Dynamic', 'Concert']} value={val.soundFx} onChange={(i) => setVal('soundFx', i)} />
          <div className="mt-[16px]"><Sw title="Speed-linked volume" sub="Raises the volume as road noise rises" id="speedVol" start /></div>
          <Sw title="Navigation prompts lower the music" id="duck" start />
        </div>
      );
    }
    if (tab === 2) {
      return (
        <div className="max-w-[640px]">
          <Sw title="Remote control" sub="Let the phone app lock the car and set the climate" id="remote" start />
          <Sw title="Remote climate" id="remoteClimate" start />
          <Sw title="Remote lock and unlock" id="remoteLock" start />
        </div>
      );
    }
    if (tab === 3) {
      return (
        <div className="max-w-[640px]">
          <Heading>Day and night mode</Heading>
          <Segmented label="Day and night mode" items={['Auto', 'Day', 'Night']} value={on.dispAuto ? 0 : hmiTheme === 'light' ? 1 : 2} onChange={(i) => { set('dispAuto', i === 0); setHmiTheme(i === 1 ? 'light' : i === 2 ? 'dark' : new Date().getHours() >= 7 && new Date().getHours() < 19 ? 'light' : 'dark'); }} />
          <Heading>Brightness</Heading>
          <div className="flex items-center gap-[14px]"><Ic.Sun size={20} /><input type="range" min={30} max={100} value={val.brightness} onChange={(e) => setVal('brightness', Number(e.target.value))} aria-label="Brightness" className="w-[360px] accent-[#3ccf8e]" /><span className="tnum text-[15px]" style={{ color: t.text2 }}>{val.brightness}%</span></div>
          <div className="mt-[10px]"><Sw title="Screen off with the car" id="screenOff" /></div>
        </div>
      );
    }
    const rows: Record<number, [string, string][]> = {
      4: [['System update', 'Up to date'], ['Software version', 'Shown on the car only']],
      5: [['Language', 'English'], ['Date and time', 'Automatic'], ['Storage', 'Shown on the car only']],
      6: [['Installed apps', 'View'], ['Permissions', 'View']],
      7: [['Owner’s manual', 'Open'], ['Contact BYD', 'Open']],
    };
    return <div className="max-w-[640px]">{(rows[tab] ?? []).map(([a, b]) => <ValueRow key={a} title={a} value={b} />)}</div>;
  }

  if (sec === 'assist') {
    if (tab === 0) {
      return (
        <div className="relative max-w-[620px]">
          <Heading>Assisted driving mode</Heading>
          <Segmented label="Assisted driving mode" items={['Adaptive cruise', 'Lane centring']} value={val.pilotMode || 1} onChange={(i) => setVal('pilotMode', i)} />
          <p className="mt-[10px] text-[14px]" style={{ color: t.text2 }}>Adaptive cruise keeps the speed and the gap; lane centring also keeps the car in its lane.</p>
          <div className="mt-[10px]"><Sw title="Stalk lane change" sub="With lane centring on, the indicator stalk asks for a lane change" id="stalkLane" /></div>
          <Heading>Activation</Heading>
          <Segmented label="Activation" items={['Pull', 'Pull or tap']} value={val.stalkAct || 1} onChange={(i) => setVal('stalkAct', i)} />
          <Side>
            <span className="absolute rounded-[10px]" style={{ left: 160, top: 80, width: 200, height: 250, background: 'linear-gradient(160deg,rgba(63,150,230,0.5),rgba(63,150,230,0.05))', transform: 'skewX(-14deg)' }} />
            <CarImage w={360} left={90} top={120} />
          </Side>
        </div>
      );
    }
    const list: Record<number, [string, string, boolean][]> = {
      1: [['Forward collision warning', '', true], ['Automatic emergency braking', '', true], ['Blind-spot warning', '', true], ['Lane departure warning', '', true], ['Door-open warning', '', false]],
      2: [['Reversing radar', 'Sounds as the car nears an obstacle', true], ['Auto-fold mirrors when parking', '', false], ['Reverse camera guidelines', '', true]],
    };
    return <div className="max-w-[640px]">{(list[tab] ?? []).map(([a, b, d], i) => <Sw key={a} title={a} sub={b || undefined} id={`pilot${tab}${i}`} start={d} />)}</div>;
  }

  if (sec === 'energy') {
    if (tab === 0) {
      return (
        <div className="relative max-w-[620px]">
          <Heading>Energy regeneration</Heading>
          <Segmented label="Energy regeneration" items={['Standard', 'Larger']} value={val.regen} onChange={(i) => setVal('regen', i)} />
          <Heading>Range display</Heading>
          <Segmented label="Range display" items={['Standard', 'Dynamic']} value={val.rangeMode || 1} onChange={(i) => setVal('rangeMode', i)} />
          <Side>
            <CarImage w={380} left={50} top={90} dim />
            <span className="absolute flex h-[54px] w-[150px] items-center justify-center rounded-[8px] text-[24px] font-semibold text-white" style={{ left: 150, top: 150, background: 'linear-gradient(90deg,#2fb457,#7bd66a)', boxShadow: '0 4px 14px rgba(40,120,50,0.45)' }}>{Math.round(soc * 100)}%</span>
          </Side>
        </div>
      );
    }
    if (tab === 1) {
      return (
        <div className="max-w-[640px]">
          <Sw title="Scheduled charging" sub="Start charging at the off-peak time" id="sched" />
          <ValueRow title="Charge limit" value="100%" />
          <ValueRow title="Discharge to outside" value="Stop at 20%" />
        </div>
      );
    }
    return <div className="max-w-[640px]"><ValueRow title="Trip" value="0.0 km" /><ValueRow title="Energy used" value="4.9 kWh" /><ValueRow title="Average consumption" value="--" /></div>;
  }

  if (sec === 'vehicle') {
    const modes = (vehicle.cockpit.driveModes ?? []).filter((m) => m.group === 'street' || m.id === 'snow');
    const order = ['eco', 'comfort', 'sport', 'snow'];
    const list = [...modes].sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id));
    const cur = Math.max(0, list.findIndex((m) => m.id === (modeId ?? 'comfort')));
    if (tab === 0) {
      return (
        <div className="relative max-w-[600px]">
          <Heading>Steering assist mode</Heading>
          <Segmented label="Steering assist" items={['Comfort', 'Sport']} value={val.steerMode} onChange={(i) => setVal('steerMode', i)} />
          <Heading>Brake assist mode</Heading>
          <Segmented label="Brake assist" items={['Comfort', 'Sport']} value={val.brakeMode || 1} onChange={(i) => setVal('brakeMode', i)} />
          <div className="mt-[18px]"><Sw title="Comfort parking" id="comfortPark" start /></div>
          <Sw title="Electronic stability control off" id="escOff" />
          <Side><CarImage w={400} left={50} top={110} /></Side>
        </div>
      );
    }
    if (tab === 1) {
      return (
        <div className="max-w-[640px]">
          <Heading>Headlamps</Heading>
          <Segmented label="Headlamps" items={['Off', 'Position', 'Low beam', 'Auto']} value={val.headlamp} onChange={(i) => setVal('headlamp', i)} />
          <p className="mt-[10px] text-[13px]" style={{ color: t.text3 }}>Lamps follow the 3D car on the Dashboard tab.</p>
          <div className="mt-[14px]"><Sw title="Ambient lighting" id="ambientSw" start /></div>
          <ToggleRow title="Interior ambient light" on={ambientOn} onChange={(v) => setAmbient({ ambientOn: v })} />
          <Sw title="Welcome lights" sub="The lamps greet the driver on unlocking" id="welcome" start />
        </div>
      );
    }
    if (tab === 2) {
      return (
        <div className="max-w-[640px]">
          <Heading>Drive mode</Heading>
          <Segmented label="Drive mode" items={list.map((m) => (m.id === 'comfort' ? 'Normal' : m.label))} value={cur} onChange={(i) => setCarMode(list[i].id, list[i].model)} />
          <Heading>Regenerative braking</Heading>
          <Segmented label="Regenerative braking" items={['Standard', 'Larger']} value={val.regen} onChange={(i) => setVal('regen', i)} />
        </div>
      );
    }
    if (tab === 7) {
      return (
        <div className="max-w-[640px]">
          <ToggleRow title="Lock on leaving" sub="The car locks when the key moves away" on={locked} onChange={(v) => setLocked(v)} />
          <Sw title="Unlock on approach" id="unlockApproach" start />
          <ToggleRow title="Electric boot" sub={openings.boot ? 'Open' : 'Closed'} on={openings.boot} onChange={() => toggleOpening('boot')} />
          <Sw title="Fold mirrors when locked" id="mirrorFold" start />
          <Sw title="Close windows when locked" id="winLock" start />
        </div>
      );
    }
    const generic: Record<number, [string, string?][]> = {
      3: [['Show the head-up display'], ['Cluster driving data'], ['Navigation in the cluster']],
      4: [['Child presence detection', 'Warns if a child is left in the car'], ['Intrusion alert']],
      5: [['A/C on at start', 'Resumes the last setting'], ['Residual cooling'], ['Recirculation in tunnels']],
      6: [['Seat heating follows the A/C'], ['Driver seat memory']],
      8: [['Seat-belt reminder'], ['Speed reminder'], ['Rear-seat reminder']],
    };
    return <div className="max-w-[640px]">{(generic[tab] ?? []).map(([a, b], i) => <Sw key={a} title={a} sub={b} id={`veh${tab}${i}`} start={i === 0} />)}</div>;
  }

  // vehicle health
  if (tab === 0) {
    return (
      <div className="relative max-w-[600px]">
        <Sw title="Maintenance time" id="mTime" />
        <Sw title="Maintenance mileage" id="mDist" />
        <svg className="pointer-events-none absolute" style={{ left: 560, top: 40 }} width="200" height="200" viewBox="0 0 200 200" aria-hidden>
          <rect x="40" y="60" width="90" height="110" rx="14" fill="none" stroke={t.text3} strokeWidth="5" />
          <path d="M70 60V40h40l20 20M130 100l24 20M118 130a24 24 0 1 0 0.1 0" fill="none" stroke={t.accent} strokeWidth="5" strokeLinecap="round" />
        </svg>
      </div>
    );
  }
  if (tab === 1) {
    return (
      <div className="max-w-[640px]">
        <ValueRow title="One-tap vehicle check" value="Start" onClick={() => notify('The vehicle is healthy (showroom demo)')} />
        <ValueRow title="Tyre pressure" value="Normal" />
        <ValueRow title="12 V battery" value="Normal" />
      </div>
    );
  }
  return (
    <div className="max-w-[640px]">
      <ValueRow title="Model" value={`${vehicle.brand} ${vehicle.model}`} />
      <ValueRow title="Chassis number" value="Shown on the car only" />
    </div>
  );
}
