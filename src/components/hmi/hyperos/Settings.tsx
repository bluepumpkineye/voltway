'use client';

import React from 'react';
import type { Vehicle, Variant, CarDriveMode } from '@/data/vehicles/schema';
import { useVehicleStore, type SettingsPage, type Opening } from '@/store/vehicle-store';
import { chargeMinutes10to80, effectiveRange } from '@/lib/performance';
import { cx } from '../ui';
import { HY } from './theme';
import * as Ic from './icons';
import { Row, SectionLabel, Segmented, Slider, Switch } from './controls';

const MENU: { id: SettingsPage; label: string; icon: React.ReactNode }[] = [
  { id: 'vehicle', label: 'Vehicle control', icon: <Ic.MenuVehicle /> },
  { id: 'lights', label: 'Lights', icon: <Ic.MenuLights /> },
  { id: 'doors', label: 'Doors & locks', icon: <Ic.MenuDoors /> },
  { id: 'driving', label: 'Driving', icon: <Ic.MenuDriving /> },
  { id: 'assist', label: 'Assisted driving', icon: <Ic.MenuAssist /> },
  { id: 'charging', label: 'Charging', icon: <Ic.MenuCharging /> },
  { id: 'connection', label: 'Connections', icon: <Ic.MenuConnection /> },
  { id: 'display', label: 'Display', icon: <Ic.MenuDisplay /> },
];

/** HyperOS Settings (设置): the side menu in the car's order, a page beside it. */
export function SettingsApp({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  const { settingsPage, openSettings } = useVehicleStore();
  const Page = {
    vehicle: VehiclePage,
    lights: LightsPage,
    doors: DoorsPage,
    driving: DrivingPage,
    assist: AssistPage,
    charging: ChargingPage,
    connection: ConnectionPage,
    display: DisplayPage,
  }[settingsPage];

  return (
    <div className="absolute inset-0 flex gap-6 px-6 pb-2 pt-2" style={{ color: HY.text }}>
      <nav className="flex w-[228px] shrink-0 flex-col gap-1" aria-label="Settings">
        <h2 className="mb-4 ml-3 mt-1 text-[30px] font-normal">Settings</h2>
        {MENU.map((m) => {
          const on = m.id === settingsPage;
          return (
            <button
              key={m.id}
              type="button"
              aria-current={on ? 'page' : undefined}
              onClick={() => openSettings(m.id)}
              className="flex h-[50px] items-center gap-3 rounded-[14px] px-4 text-left text-[16px] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
              style={{ background: on ? HY.panel3 : 'transparent', fontWeight: on ? 600 : 400 }}
            >
              <span style={{ color: on ? '#fff' : HY.text2 }}>{m.icon}</span>
              {m.label}
            </button>
          );
        })}
      </nav>
      <div className="hy-scroll relative min-w-0 flex-1 overflow-y-auto pr-2">
        <Page vehicle={vehicle} variant={variant} />
      </div>
    </div>
  );
}

type PageProps = { vehicle: Vehicle; variant: Variant };

/* --------------------------------------------------- driving preferences */

/**
 * The radar HyperOS draws beside the drive modes: 6 qualities, a yellow
 * shape per mode. An illustration of each mode's character, not measured.
 */
const AXES = ['Power', 'Agility', 'Economy', 'Comfort', 'Clearance', 'Stability'];
const PROFILE: Record<string, number[]> = {
  eco: [0.45, 0.5, 0.95, 0.8, 0.6, 0.75],
  standard: [0.65, 0.65, 0.75, 0.85, 0.65, 0.8],
  sport: [0.9, 0.85, 0.5, 0.55, 0.5, 0.8],
  slippery: [0.4, 0.45, 0.7, 0.8, 0.7, 0.95],
  novice: [0.35, 0.45, 0.8, 0.85, 0.65, 0.9],
  endurance: [0.7, 0.85, 0.6, 0.35, 0.35, 0.9],
  qualifying: [0.95, 0.95, 0.3, 0.3, 0.3, 0.85],
  drift: [0.85, 1.0, 0.35, 0.35, 0.35, 0.5],
  drag: [1.0, 0.6, 0.25, 0.35, 0.35, 0.85],
  saver: [0.3, 0.4, 1.0, 0.75, 0.6, 0.8],
};

/**
 * Which of the car's modes is showing: the one picked on the screen, else
 * the street mode the page's generic buttons map to (Comfort is Standard).
 * The generic Track has no car mode of its own, so nothing is claimed.
 */
export function currentCarMode(vehicle: Vehicle, modeId: string | null, driveMode: string): CarDriveMode | undefined {
  const modes = vehicle.cockpit.driveModes ?? [];
  return (
    modes.find((m) => m.id === modeId) ??
    modes.find((m) => m.model === driveMode && m.group === 'street' && !m.slot)
  );
}

function DrivingPage({ vehicle }: PageProps) {
  const { modeId, driveMode, setCarMode, regen, setRegen } = useVehicleStore();
  const modes = vehicle.cockpit.driveModes ?? [];
  const street = modes.filter((m) => m.group === 'street');
  const special = modes.filter((m) => m.group === 'special');
  const current = currentCarMode(vehicle, modeId, driveMode);

  return (
    <div className="grid grid-cols-[1fr_300px] gap-8 pt-14">
      <div className="flex flex-col">
        <SectionLabel info>Drive mode</SectionLabel>
        <Segmented
          label="Drive mode"
          value={current?.group === 'street' ? current.id : null}
          options={street.map((m) => ({ id: m.id, label: m.slot ?? m.label, sub: m.slot ? m.label : undefined }))}
          onChange={(id) => {
            const m = street.find((x) => x.id === id);
            if (m) setCarMode(m.id, m.model);
          }}
        />
        <div className="my-7 h-px" style={{ background: HY.line }} />
        <SectionLabel>Driving scene modes</SectionLabel>
        <div className="grid grid-cols-2 gap-3">
          {special.map((m) => {
            const on = current?.id === m.id;
            return (
              <button
                key={m.id}
                type="button"
                aria-pressed={on}
                onClick={() => setCarMode(m.id, m.model)}
                className="flex h-[104px] flex-col justify-between rounded-[18px] p-4 text-left transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
                style={{ background: on ? HY.blue : HY.panel2 }}
              >
                {m.id === 'drag' ? <Ic.Rocket size={24} /> : <Ic.Leaf size={24} />}
                <span className="flex items-end justify-between">
                  <span className="text-[16px] font-medium">{m.label}</span>
                  {m.id === 'drag' && (
                    <span className="rounded-full px-3 py-1 text-[12px]" style={{ background: 'rgba(255,255,255,0.14)' }}>
                      Tutorial
                    </span>
                  )}
                </span>
              </button>
            );
          })}
        </div>
        <div className="my-7 h-px" style={{ background: HY.line }} />
        <SectionLabel>Driving habits</SectionLabel>
        <div className="mb-3 flex items-center gap-1.5 text-[15px]" style={{ color: HY.text }}>
          Regenerative braking <Ic.Info size={17} style={{ color: HY.text2 }} />
        </div>
        <Segmented
          label="Regenerative braking"
          value={regen}
          options={[
            { id: 'gentle', label: 'Gentle' },
            { id: 'standard', label: 'Standard' },
            { id: 'custom', label: 'Custom' },
          ]}
          onChange={setRegen}
        />
        <p className="mt-2 text-[12.5px]" style={{ color: HY.text3 }}>
          Stronger regeneration slows the car more when you lift off.
        </p>
      </div>

      <div className="flex flex-col items-center">
        <Radar values={PROFILE[current?.id ?? 'standard'] ?? PROFILE.standard} />
        {current?.powerPs && (
          <div className="mt-2 text-center">
            <div className="tnum text-[26px] font-light" style={{ color: HY.yellow }}>
              {current.powerPs.toLocaleString('en-US')} PS
            </div>
            <div className="text-[12px]" style={{ color: HY.text3 }}>{current.label} · published peak</div>
          </div>
        )}
      </div>
    </div>
  );
}

function Radar({ values }: { values: number[] }) {
  const cx0 = 150, cy0 = 150, R = 96;
  const pt = (i: number, r: number) => {
    const a = -Math.PI / 2 + (i * Math.PI * 2) / 6;
    return [cx0 + Math.cos(a) * r, cy0 + Math.sin(a) * r];
  };
  const poly = (r: (i: number) => number) => values.map((_, i) => pt(i, r(i)).join(',')).join(' ');
  return (
    <svg viewBox="0 0 300 300" className="w-[300px]" role="img" aria-label="Drive mode character">
      <defs>
        <radialGradient id="hy-radar" cx="50%" cy="50%" r="50%">
          <stop offset="0" stopColor={HY.yellow} stopOpacity="0.05" />
          <stop offset="1" stopColor={HY.yellow} stopOpacity="0.45" />
        </radialGradient>
        <filter id="hy-glow" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="4" />
        </filter>
      </defs>
      {[0.33, 0.66, 1].map((k) => (
        <polygon key={k} points={poly(() => R * k)} fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="1" />
      ))}
      {values.map((_, i) => {
        const [x, y] = pt(i, R);
        return <line key={i} x1={cx0} y1={cy0} x2={x} y2={y} stroke="rgba(255,255,255,0.08)" />;
      })}
      <polygon points={poly((i) => R * values[i])} fill="none" stroke={HY.yellow} strokeWidth="6" opacity="0.5" filter="url(#hy-glow)" className="hy-radar" />
      <polygon points={poly((i) => R * values[i])} fill="url(#hy-radar)" stroke={HY.yellow} strokeWidth="2.5" className="hy-radar" />
      {AXES.map((a, i) => {
        const [x, y] = pt(i, R + 26);
        return (
          <text key={a} x={x} y={y + 4} textAnchor="middle" fontSize="13" fill="rgba(255,255,255,0.7)" fontFamily="inherit">
            {a}
          </text>
        );
      })}
    </svg>
  );
}

/* --------------------------------------------------------- vehicle control */

function VehiclePage() {
  const { sportSound, setSportSound, rideHeight, setRideHeight } = useVehicleStore();
  const [fold, setFold] = React.useState(false);
  return (
    <div className="flex flex-col gap-7 pt-14">
      <div>
        <SectionLabel info>Sport sound</SectionLabel>
        <Segmented
          label="Sport sound"
          value={sportSound}
          options={[
            { id: 'off', label: 'Off' },
            { id: 'electronic', label: 'Electronic' },
            { id: 'classic', label: 'Classic' },
            { id: 'scifi', label: 'Sci-fi' },
          ]}
          onChange={setSportSound}
        />
        <p className="mt-2 text-[12.5px]" style={{ color: HY.text3 }}>
          A simulated engine note that follows the throttle, in the cabin and through a 40 W speaker at the rear.
        </p>
      </div>
      <div>
        <SectionLabel>Air suspension height</SectionLabel>
        <Segmented
          label="Air suspension height"
          value={rideHeight}
          options={[
            { id: 'low', label: 'Low' },
            { id: 'standard', label: 'Standard' },
            { id: 'high', label: 'High' },
          ]}
          onChange={setRideHeight}
        />
      </div>
      <Row label="Fold mirrors" hint="Also folds on locking">
        <Switch label="Fold mirrors" on={fold} onChange={setFold} />
      </Row>
    </div>
  );
}

/* ------------------------------------------------------------------ lights */

const AMBIENT_SWATCHES = [
  { hue: 48, label: 'Ultra yellow' },
  { hue: 28, label: 'Amber' },
  { hue: 0, label: 'Red' },
  { hue: 205, label: 'Ice blue' },
  { hue: 230, label: 'Blue' },
  { hue: 275, label: 'Violet' },
  { hue: 150, label: 'Green' },
];

function LightsPage() {
  const { headlightsOn, setHeadlights, ambientOn, ambientHue, ambientBrightness, setAmbient } = useVehicleStore();
  return (
    <div className="flex flex-col gap-7 pt-14">
      <div>
        <SectionLabel>Headlights</SectionLabel>
        <Segmented
          label="Headlights"
          value={headlightsOn ? 'on' : 'off'}
          options={[
            { id: 'off', label: 'Off' },
            { id: 'on', label: 'Low beam' },
          ]}
          onChange={(v) => setHeadlights(v === 'on')}
        />
      </div>
      <Row label="Ambient lighting" hint="The light guides along the dash and doors">
        <Switch label="Ambient lighting" on={ambientOn} onChange={(v) => setAmbient({ ambientOn: v })} />
      </Row>
      <div className={cx(!ambientOn && 'pointer-events-none opacity-40')}>
        <SectionLabel>Colour</SectionLabel>
        <div className="flex gap-3" role="radiogroup" aria-label="Ambient colour">
          {AMBIENT_SWATCHES.map((s) => {
            const on = Math.abs(s.hue - ambientHue) < 6;
            return (
              <button
                key={s.hue}
                type="button"
                role="radio"
                aria-checked={on}
                aria-label={s.label}
                onClick={() => setAmbient({ ambientHue: s.hue })}
                className="h-[46px] w-[46px] rounded-full transition-transform focus:outline-none"
                style={{
                  background: `hsl(${s.hue} 92% 58%)`,
                  boxShadow: on ? `0 0 0 3px ${HY.bg}, 0 0 0 5px #fff` : 'none',
                  transform: on ? 'scale(1.05)' : undefined,
                }}
              />
            );
          })}
        </div>
        <div className="mt-6">
          <SectionLabel>Brightness</SectionLabel>
          <Slider
            label="Ambient brightness"
            value={Math.round(ambientBrightness * 100)}
            onChange={(v) => setAmbient({ ambientBrightness: v / 100 })}
            tone={`hsl(${ambientHue} 85% 55%)`}
          />
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------- doors, locks */

const DOORS: { id: Opening; label: string }[] = [
  { id: 'frunk', label: 'Frunk' },
  { id: 'boot', label: 'Boot' },
  { id: 'doorFL', label: 'Driver door' },
  { id: 'doorFR', label: 'Passenger door' },
  { id: 'doorRL', label: 'Rear left door' },
  { id: 'doorRR', label: 'Rear right door' },
];

function DoorsPage() {
  const { openings, toggleOpening, closeAllOpenings, locked, setLocked } = useVehicleStore();
  return (
    <div className="flex flex-col gap-4 pt-14">
      <Row label="Central locking" hint={locked ? 'Locked' : 'Unlocked'}>
        <Switch label="Central locking" on={locked} onChange={setLocked} />
      </Row>
      <div className="grid grid-cols-3 gap-3">
        {DOORS.map((d) => {
          const open = openings[d.id];
          return (
            <button
              key={d.id}
              type="button"
              aria-pressed={open}
              onClick={() => toggleOpening(d.id)}
              className="flex h-[96px] flex-col justify-between rounded-[18px] p-4 text-left transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
              style={{ background: open ? HY.blue : HY.panel2 }}
            >
              <Ic.MenuDoors size={22} />
              <span className="flex items-baseline justify-between">
                <span className="text-[16px] font-medium">{d.label}</span>
                <span className="text-[12.5px]" style={{ color: open ? 'rgba(255,255,255,0.85)' : HY.text3 }}>
                  {open ? 'Open' : 'Closed'}
                </span>
              </span>
            </button>
          );
        })}
      </div>
      <button
        type="button"
        onClick={closeAllOpenings}
        className="mt-2 self-start rounded-full px-6 py-3 text-[15px] focus:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
        style={{ background: HY.panel2 }}
      >
        Close all
      </button>
    </div>
  );
}

/* ------------------------------------------------------- assisted driving */

function AssistPage() {
  const { adasActive, setAdas } = useVehicleStore();
  const [lane, setLane] = React.useState(true);
  const [signs, setSigns] = React.useState(true);
  return (
    <div className="flex flex-col gap-4 pt-14">
      <Row label="Xiaomi HAD navigate on autopilot" hint="City and highway NOA, parking to parking">
        <Switch label="Navigate on autopilot" on={adasActive} onChange={setAdas} />
      </Row>
      <Row label="Lane change assist" hint="Changes lane on the indicator">
        <Switch label="Lane change assist" on={lane} onChange={setLane} />
      </Row>
      <Row label="Speed limit recognition" hint="Shows the limit on the driving desktop">
        <Switch label="Speed limit recognition" on={signs} onChange={setSigns} />
      </Row>
      <div className="mt-3 grid grid-cols-4 gap-3">
        {[
          ['1', 'LiDAR'],
          ['11', 'Cameras'],
          ['3', 'Radars'],
          ['12', 'Ultrasonic'],
        ].map(([n, l]) => (
          <div key={l} className="rounded-[18px] px-5 py-4" style={{ background: HY.panel }}>
            <div className="tnum text-[30px] font-light">{n}</div>
            <div className="text-[13px]" style={{ color: HY.text2 }}>{l}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- charging */

function ChargingPage({ variant }: PageProps) {
  const { soc, setSoc, driveMode, climate } = useVehicleStore();
  const [limit, setLimit] = React.useState(90);
  const [v2l, setV2l] = React.useState(false);
  const range = effectiveRange(variant, driveMode, soc, climate);
  const dc = chargeMinutes10to80(variant);
  return (
    <div className="flex flex-col gap-6 pt-14">
      <div className="flex items-end gap-4">
        <span className="tnum text-[60px] font-extralight leading-none">{Math.round(soc * 100)}%</span>
        <span className="mb-2 text-[16px]" style={{ color: HY.text2 }}>
          {range ? `${range.km} km ${range.cycle}` : ''}
        </span>
      </div>
      <div className="h-[16px] overflow-hidden rounded-full" style={{ background: HY.panel2 }}>
        <div className="h-full rounded-full" style={{ width: `${soc * 100}%`, background: HY.green }} />
      </div>
      <div>
        <SectionLabel>Charge limit · {limit}%</SectionLabel>
        <Slider label="Charge limit" value={limit} min={50} max={100} onChange={setLimit} tone={HY.green} />
      </div>
      <div>
        <SectionLabel>Current charge (showroom demo) · {Math.round(soc * 100)}%</SectionLabel>
        <Slider label="Current charge" value={Math.round(soc * 100)} min={5} max={100} onChange={(v) => setSoc(v / 100)} />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-[18px] px-5 py-4" style={{ background: HY.panel }}>
          <div className="text-[13px]" style={{ color: HY.text2 }}>DC fast charge 10-80%</div>
          <div className="tnum mt-1 text-[28px] font-light">{dc !== undefined ? `${dc} min` : '--'}</div>
        </div>
        <Row label="Vehicle to load" hint="Power devices from the car" className="!py-4">
          <Switch label="Vehicle to load" on={v2l} onChange={setV2l} />
        </Row>
      </div>
    </div>
  );
}

/* ------------------------------------------------------ connections, display */

function ConnectionPage() {
  const [bt, setBt] = React.useState(true);
  const [wifi, setWifi] = React.useState(true);
  const [carplay, setCarplay] = React.useState(false);
  return (
    <div className="flex flex-col gap-4 pt-14">
      <Row label="Bluetooth"><Switch label="Bluetooth" on={bt} onChange={setBt} /></Row>
      <Row label="Wi-Fi"><Switch label="Wi-Fi" on={wifi} onChange={setWifi} /></Row>
      <Row label="Xiaomi HyperConnect" hint="Your Xiaomi phone joins the car when you sit in"><Switch label="HyperConnect" on onChange={() => {}} /></Row>
      <Row label="Apple CarPlay" hint="Wireless"><Switch label="Apple CarPlay" on={carplay} onChange={setCarplay} /></Row>
    </div>
  );
}

function DisplayPage() {
  const [bright, setBright] = React.useState(72);
  const [theme, setTheme] = React.useState<'auto' | 'dark'>('dark');
  return (
    <div className="flex flex-col gap-7 pt-14">
      <div>
        <SectionLabel>Brightness</SectionLabel>
        <Slider label="Screen brightness" value={bright} onChange={setBright} />
      </div>
      <div>
        <SectionLabel>Appearance</SectionLabel>
        <Segmented label="Appearance" value={theme} options={[{ id: 'auto', label: 'Auto' }, { id: 'dark', label: 'Dark' }]} onChange={setTheme} />
      </div>
    </div>
  );
}
