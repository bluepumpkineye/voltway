'use client';

import React from 'react';
import type { Vehicle, Variant } from '@/data/vehicles/schema';
import { useVehicleStore, type Opening } from '@/store/vehicle-store';
import { effectiveRange } from '@/lib/performance';
import { tapChargeFlap } from '@/lib/tech/actions';
import { useChargeReadout } from '@/lib/tech/session';
import { RIDE_LEVELS } from '@/lib/tech/ride';
import { useZk } from './theme';
import * as Ic from './icons';
import { useZkLocal } from './shared';

/* ------------------------------------------------------------ shared pieces */

function Pill({
  on, onClick, children, w, h = 44,
}: {
  on?: boolean;
  onClick: () => void;
  children: React.ReactNode;
  w?: number;
  h?: number;
}) {
  const t = useZk();
  return (
    <button
      type="button"
      aria-pressed={on}
      onClick={onClick}
      className="flex items-center justify-center gap-2 rounded-[4px] px-5 text-[16px] focus:outline-none focus-visible:ring-2 focus-visible:ring-black/30"
      style={{
        width: w,
        height: h,
        background: on ? t.cardOn : t.card,
        color: on ? t.text : t.text2,
        boxShadow: on ? `inset 0 0 0 1.5px ${t.red}` : undefined,
      }}
    >
      {children}
    </button>
  );
}

function Switch({ on, onClick, label }: { on: boolean; onClick: () => void; label: string }) {
  const t = useZk();
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      aria-label={label}
      onClick={onClick}
      className="relative h-[30px] w-[54px] shrink-0 rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-black/30"
      style={{ background: on ? t.accent : t.tone === 'light' ? '#c9cde0' : 'rgba(255,255,255,0.22)' }}
    >
      <span className="absolute top-[3px] h-[24px] w-[24px] rounded-full bg-white shadow transition-all" style={{ left: on ? 27 : 3 }} />
    </button>
  );
}

function Row({ label, children, sub }: { label: string; sub?: string; children: React.ReactNode }) {
  const t = useZk();
  return (
    <div className="flex items-center justify-between gap-6 rounded-[4px] px-5 py-[7px]" style={{ minHeight: 58, background: t.card }}>
      <div>
        <div className="text-[17px] leading-tight">{label}</div>
        {sub && (
          <div className="mt-[3px] text-[12px] leading-none" style={{ color: t.text3 }}>
            {sub}
          </div>
        )}
      </div>
      {children}
    </div>
  );
}

function Segment({ options, value, onPick, minW = 84 }: { options: string[]; value: number; onPick: (i: number) => void; minW?: number }) {
  const t = useZk();
  return (
    <div className="flex overflow-hidden rounded-[4px]" style={{ background: t.tone === 'light' ? '#dfe3f3' : 'rgba(255,255,255,0.10)' }}>
      {options.map((o, i) => (
        <button
          key={o}
          type="button"
          onClick={() => onPick(i)}
          className="h-[38px] px-3 text-[15px] focus:outline-none"
          style={{
            background: value === i ? (t.tone === 'light' ? '#fff' : 'rgba(255,255,255,0.18)') : 'transparent',
            boxShadow: value === i ? `inset 0 0 0 1.5px ${t.red}` : undefined,
            color: t.text,
            minWidth: minW,
          }}
        >
          {o}
        </button>
      ))}
    </div>
  );
}

/* -------------------------------------------------------------------- climate */

const Power = ({ size = 22 }: { size?: number }) => (
  <svg viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden>
    <path d="M12 3v9" />
    <path d="M6.500 6.500a8 8 0 1 0 11 0" />
  </svg>
);

/**
 * The climate page (c10_0027): a row of mode buttons across the top, "A/C" and "Fragrance" down
 * the left, each side's temperature with its neighbours above and below, a clay drawing of the
 * cabin in the middle (public/hmi/<slug>/cabin-climate-light|dark.webp) and the airflow strip
 * along the bottom: where the air goes, the fan's five steps, the rear seats, seat comfort.
 */
export function ClimatePage({ vehicle }: { vehicle: Vehicle }) {
  const t = useZk();
  const { on, toggle, val, setVal, notify } = useZkLocal();
  const { climate, patchClimate } = useVehicleStore();
  const [img, setImg] = React.useState(true);
  const nudge = (key: 'driverTempC' | 'passengerTempC', d: number) => {
    const next = Math.min(32, Math.max(16, Math.round((climate[key] + d) * 2) / 2));
    patchClimate(climate.sync ? { driverTempC: next, passengerTempC: next } : { [key]: next });
  };
  const ghost = t.tone === 'light' ? 'rgba(17,19,24,0.06)' : 'rgba(255,255,255,0.10)';

  const top = (x: number, w: number, node: React.ReactNode, active: boolean, onClick: () => void, label: string) => (
    <button
      key={label}
      type="button"
      aria-label={label}
      aria-pressed={active}
      onClick={onClick}
      className="absolute flex h-[42px] items-center justify-center rounded-[3px] text-[16px] font-semibold focus:outline-none focus-visible:ring-2 focus-visible:ring-black/30"
      style={{
        left: x,
        top: 37,
        width: w,
        background: active ? t.cardOn : ghost,
        boxShadow: active ? `inset 0 0 0 1.5px ${t.red}` : undefined,
        color: t.text,
      }}
    >
      {node}
    </button>
  );

  const temp = (side: 'l' | 'r') => {
    const key = side === 'l' ? 'driverTempC' : 'passengerTempC';
    const v = climate[key];
    const small = (d: number) => (
      <button
        type="button"
        aria-label={`${side === 'l' ? 'Driver' : 'Passenger'} ${(v + d).toFixed(1)} degrees`}
        onClick={() => nudge(key, d)}
        className="tnum block text-[16px] leading-[34px] focus:outline-none"
        style={{ color: t.text3 }}
      >
        {(v + d).toFixed(1)}
        <span className="text-[9px]">°C</span>
      </button>
    );
    return (
      <div
        className={`absolute flex flex-col ${side === 'l' ? 'items-start' : 'items-end'}`}
        style={side === 'l' ? { left: 156, top: 138 } : { right: 33, top: 134 }}
      >
        {small(0.5)}
        <span className="tnum text-[33px] font-light leading-[40px]" aria-live="polite">
          {v.toFixed(1)}
          <span className="relative -top-[11px] text-[13px]">°C</span>
        </span>
        {small(-0.5)}
      </div>
    );
  };

  const modes: { id: number; label: string; icon: React.ReactNode }[] = [
    { id: 0, label: 'Face', icon: <Ic.AirFace size={26} /> },
    { id: 1, label: 'Face and feet', icon: <span className="flex"><Ic.AirFace size={20} /><Ic.AirFeet size={20} /></span> },
    { id: 2, label: 'Feet', icon: <Ic.AirFeet size={26} /> },
    { id: 3, label: 'Windscreen and feet', icon: <Ic.DefrostFront size={26} /> },
  ];
  const mark = (on: boolean, bottom: number) =>
    on ? <span className="absolute h-[3px] w-[14px] rounded-full" style={{ bottom, background: t.red }} /> : null;
  const stripBtn = (x: number, label: string, node: React.ReactNode, pressed: boolean, onClick: () => void) => (
    <button
      key={label}
      type="button"
      aria-label={label}
      aria-pressed={pressed}
      onClick={onClick}
      className="absolute top-0 flex h-full w-[70px] -translate-x-1/2 items-center justify-center focus:outline-none"
      style={{ left: x, color: pressed ? t.text : t.text2 }}
    >
      {node}
      {mark(pressed, 14)}
    </button>
  );

  return (
    <div className="absolute inset-0">
      {img && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={`/hmi/${vehicle.slug}/cabin-climate-${t.tone}.webp`}
          alt=""
          draggable={false}
          onError={() => setImg(false)}
          className="pointer-events-none absolute select-none"
          style={{ left: 166, top: 78, width: 1093, height: 355, objectFit: 'cover', objectPosition: 'center' }}
        />
      )}
      {top(155, 101, <Power />, climate.acOn, () => patchClimate({ acOn: !climate.acOn }), 'Climate power')}
      {top(355, 101, 'AUTO', climate.acOn && val.auto === 1, () => { patchClimate({ acOn: true }); setVal('auto', val.auto === 1 ? 0 : 1); }, 'Auto')}
      {top(469, 101, 'A/C', climate.acOn, () => patchClimate({ acOn: !climate.acOn }), 'A/C')}
      {top(582, 100, <Ic.Recirc size={26} />, on.recirc, () => toggle('recirc'), 'Recirculate')}
      {top(696, 98, 'ECO', on.eco, () => toggle('eco'), 'Eco')}
      {top(807, 103, <Ic.DefrostFront size={26} />, on.defrost, () => toggle('defrost'), 'Max demist')}
      {top(1154, 95, <Ic.Gear size={24} />, false, () => notify('Climate settings (showroom demo)'), 'Climate settings')}

      <span className="absolute" style={{ left: 124, top: 40, bottom: 12, width: 1, background: t.line }} aria-hidden />
      <span className="absolute w-[3px] rounded-full" style={{ left: 118, top: 173, height: 30, background: t.red }} aria-hidden />
      <button type="button" className="absolute flex w-[110px] -translate-y-1/2 flex-col items-center gap-[10px] focus:outline-none" style={{ left: 4, top: 190 }} onClick={() => notify('Air conditioning')}>
        <Ic.Fan size={34} />
        <span className="text-[15px] leading-none">A/C</span>
      </button>
      <button type="button" className="absolute flex w-[110px] -translate-y-1/2 flex-col items-center gap-[10px] focus:outline-none" style={{ left: 4, top: 340, color: t.text2 }} onClick={() => notify('Fragrance (showroom demo)')}>
        <Ic.Bulb size={32} />
        <span className="text-[15px] leading-none">Fragrance</span>
      </button>

      {temp('l')}
      {temp('r')}
      <button
        type="button"
        aria-pressed={climate.sync}
        onClick={() => patchClimate({ sync: !climate.sync })}
        className="absolute h-[29px] w-[70px] rounded-[3px] text-[14px] focus:outline-none"
        style={{ left: 157, top: 291, background: climate.sync ? t.cardOn : ghost, boxShadow: climate.sync ? `inset 0 0 0 1.5px ${t.red}` : undefined, color: t.text2 }}
      >
        Sync
      </button>


      <div className="absolute rounded-[3px]" style={{ left: 161, top: 429, width: 1082, height: 71, background: t.card }}>
        {modes.map((m, i) => stripBtn(55 + i * 83, m.label, m.icon, val.flow === m.id, () => setVal('flow', m.id)))}
        <Ic.Fan size={20} style={{ position: 'absolute', left: 367, top: 25, color: t.text2 }} />
        <div className="absolute flex gap-[6px]" style={{ left: 401, top: 33, width: 307 }} role="group" aria-label="Fan speed">
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              type="button"
              aria-label={`Fan speed ${n}`}
              onClick={() => patchClimate({ fanSpeed: n, acOn: true })}
              className="relative h-[5px] flex-1 rounded-full focus:outline-none"
              style={{ background: climate.acOn && n <= climate.fanSpeed ? t.accent : t.tone === 'light' ? '#d4d8e8' : 'rgba(255,255,255,0.18)' }}
            >
              <span className="absolute -inset-y-4 inset-x-0" />
            </button>
          ))}
        </div>
        <Ic.Fan size={30} style={{ position: 'absolute', left: 717, top: 20 }} />
        {stripBtn(
          790,
          'Rear climate',
          <span className="flex flex-col items-center gap-[2px]">
            <Power size={20} />
            <span className="text-[12px] leading-none">Rear</span>
          </span>,
          on.rear,
          () => toggle('rear'),
        )}
        {stripBtn(880, 'Driver seat heat', <Ic.SeatHeat size={26} />, climate.seatHeatDriver > 0, () => patchClimate({ seatHeatDriver: climate.seatHeatDriver > 0 ? 0 : 2 }))}
        {stripBtn(960, 'Passenger seat heat', <Ic.SeatAuto size={26} />, climate.seatHeatPassenger > 0, () => patchClimate({ seatHeatPassenger: climate.seatHeatPassenger > 0 ? 0 : 2 }))}
        {stripBtn(1040, 'Rear window demist', <Ic.DefrostRear size={26} />, on.defrostRear, () => toggle('defrostRear'))}
      </div>
    </div>
  );
}

/* ----------------------------------------------------------------- controls */

// the car's own settings rail starts with Quick settings (c10_0033), then Vehicle, Lights, Driving ... Energy
// management; Display and System are the showroom's own
const PAGES = ['Quick settings', 'Vehicle', 'Lights', 'Driving', 'Energy management', 'Display', 'System'] as const;

const CLOSURES: { id: Opening; label: string }[] = [
  { id: 'doorFL', label: 'Front left door' },
  { id: 'doorFR', label: 'Front right door' },
  { id: 'doorRL', label: 'Rear left door' },
  { id: 'doorRR', label: 'Rear right door' },
  { id: 'frunk', label: 'Bonnet' },
  { id: 'boot', label: 'Tailgate' },
];

export function ControlsPage({ vehicle, variant, forcePage }: { vehicle: Vehicle; variant: Variant; forcePage?: (typeof PAGES)[number] }) {
  const t = useZk();
  const { val, setVal, on, toggle } = useZkLocal();
  // opened on a page of its own (the charging page the fast-charge demo shows), once, when it is mounted
  React.useEffect(() => {
    if (forcePage) setVal('setPage', PAGES.indexOf(forcePage));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [forcePage]);
  const {
    openings, toggleOpening, closeAllOpenings, locked, setLocked, headlightsOn, setHeadlights, ambientOn, ambientHue,
    ambientBrightness, setAmbient,
    hmiTheme, setHmiTheme,
  } = useVehicleStore();
  const page = val.setPage;

  let body: React.ReactNode;
  switch (PAGES[page]) {
    case 'Quick settings':
      body = <QuickSettings vehicle={vehicle} />;
      break;
    case 'Vehicle':
      body = (
        <div className="grid grid-cols-2 gap-[10px]">
          <Row label="Lock" sub={locked ? 'Locked' : 'Unlocked'}>
            <Switch on={locked} onClick={() => setLocked(!locked)} label="Lock" />
          </Row>
          <Row label="Close everything" sub="Doors, bonnet and tailgate">
            <Pill onClick={closeAllOpenings} h={36}>
              Close
            </Pill>
          </Row>
          {CLOSURES.map((c) => (
            <Row key={c.id} label={c.label} sub={openings[c.id] ? 'Open' : 'Closed'}>
              <Switch on={openings[c.id]} onClick={() => toggleOpening(c.id)} label={c.label} />
            </Row>
          ))}
          <Row label="Fold mirrors">
            <Switch on={on.mirrorsFold} onClick={() => toggle('mirrorsFold')} label="Fold mirrors" />
          </Row>
          <Row label="Charge flap" sub={openings.charge ? 'Open' : 'Closed'}>
            <Switch on={openings.charge} onClick={tapChargeFlap} label="Charge flap" />
          </Row>
        </div>
      );
      break;
    case 'Lights':
      body = (
        <div className="grid grid-cols-2 gap-[10px]">
          <Row label="Headlamps" sub={headlightsOn ? 'On' : 'Off'}>
            <Switch on={headlightsOn} onClick={() => setHeadlights(!headlightsOn)} label="Headlamps" />
          </Row>
          <Row label="Ambient light">
            <Switch on={ambientOn} onClick={() => setAmbient({ ambientOn: !ambientOn })} label="Ambient light" />
          </Row>
          <Row label="Ambient colour">
            <input type="range" min={0} max={360} value={ambientHue} aria-label="Ambient colour" onChange={(e) => setAmbient({ ambientHue: Number(e.target.value) })} className="w-[200px] cursor-pointer" style={{ accentColor: t.accent }} />
          </Row>
          <Row label="Ambient brightness">
            <input type="range" min={0} max={100} value={Math.round(ambientBrightness * 100)} aria-label="Ambient brightness" onChange={(e) => setAmbient({ ambientBrightness: Number(e.target.value) / 100 })} className="w-[200px] cursor-pointer" style={{ accentColor: t.accent }} />
          </Row>
          <Row label="Auto high beam">
            <Switch on={on.autoHighBeam} onClick={() => toggle('autoHighBeam')} label="Auto high beam" />
          </Row>
          <Row label="Welcome light show">
            <Switch on={on.welcome} onClick={() => toggle('welcome')} label="Welcome light show" />
          </Row>
        </div>
      );
      break;
    case 'Driving':
      body = <DrivingPage />;
      break;
    case 'Energy management':
      body = <ChargePage vehicle={vehicle} variant={variant} />;
      break;
    case 'Display':
      body = (
        <div className="flex flex-col gap-[10px]">
          <Row label="Display mode">
            <Segment options={['Light', 'Dark']} value={hmiTheme === 'light' ? 0 : 1} onPick={(i) => setHmiTheme(i === 0 ? 'light' : 'dark')} />
          </Row>
          <Row label="Screen brightness">
            <input type="range" min={30} max={100} value={val.brightness} aria-label="Screen brightness" onChange={(e) => setVal('brightness', Number(e.target.value))} className="w-[240px] cursor-pointer" style={{ accentColor: t.accent }} />
          </Row>
          <Row label="Adaptive brightness">
            <Switch on={on.adaptiveBrightness} onClick={() => toggle('adaptiveBrightness')} label="Adaptive brightness" />
          </Row>
          <Row label="Head-up display">
            <Switch on={on.hud} onClick={() => toggle('hud')} label="Head-up display" />
          </Row>
        </div>
      );
      break;
    default:
      body = (
        <div className="flex flex-col gap-[10px]">
          <Row label="Model" sub={`${vehicle.brand} ${vehicle.model} ${vehicle.year}`}>
            <span className="text-[15px]" style={{ color: t.text2 }}>
              {variant.name}
            </span>
          </Row>
          <Row label="Operating system">
            <span className="text-[15px]" style={{ color: t.text2 }}>
              {vehicle.cockpit.os}
            </span>
          </Row>
          <Row label="Sentry mode">
            <Switch on={on.sentry} onClick={() => toggle('sentry')} label="Sentry mode" />
          </Row>
          <Row label="Software" sub="This is a showroom demonstration">
            <span className="text-[15px]" style={{ color: t.text3 }}>
              Up to date
            </span>
          </Row>
        </div>
      );
  }

  return (
    <div className="absolute inset-0">
      <span className="absolute" style={{ left: 230, top: 30, bottom: 30, width: 1, background: t.line }} aria-hidden />
      <div className="absolute flex flex-col" style={{ left: 40, top: 30, width: 170 }}>
        {PAGES.map((p, i) => (
          <button
            key={p}
            type="button"
            onClick={() => setVal('setPage', i)}
            className="relative flex h-[56px] items-center text-left text-[17px] focus:outline-none"
            style={{ color: page === i ? t.text : t.text2 }}
          >
            {page === i && <span className="absolute -left-[12px] top-[14px] h-[28px] w-[3px] rounded-full" style={{ background: t.accent }} />}
            {p}
          </button>
        ))}
      </div>
      <div className="absolute overflow-hidden" style={{ left: 270, right: 60, top: 30, bottom: 24 }}>
        {body}
      </div>
    </div>
  );
}

/* ------------------------------------------------------- vehicle charging */

/**
 * Energy management > Vehicle charging, as the 7X draws it (c10_0101): the car with a battery graphic, the charge
 * limit, the charge left and the range it gives, the "Charge port cover" tile on the left, the schedule rows below.
 * While the Tech tab's fast-charge demo runs the page shows its numbers (the car's own page for a charge in progress
 * was not photographed: the live part is ours, said so on the demo's panel).
 */
function ChargePage({ vehicle, variant }: { vehicle: Vehicle; variant: Variant }) {
  const t = useZk();
  const { on, toggle, notify } = useZkLocal();
  const { driveMode, soc, climate, openings } = useVehicleStore();
  const live = useChargeReadout();
  const range = effectiveRange(variant, driveMode, soc, climate);
  const charging = live?.phase === 'charging';
  const limit = live ? 80 : 100;
  const pct = Math.round(soc * 100);
  const left = live ? Math.max(0, Math.round(live.left / 60)) : 0;
  const tab = (label: string, active?: boolean) => (
    <button
      key={label}
      type="button"
      onClick={active ? undefined : () => notify(`${label} (showroom demo)`)}
      className="relative h-[44px] text-[18px] focus:outline-none"
      style={{ color: active ? t.text : t.text2 }}
    >
      {label}
      {active && <span className="absolute inset-x-0 bottom-0 mx-auto h-[3px] w-[28px] rounded-full" style={{ background: t.red }} />}
    </button>
  );
  return (
    <div className="relative h-full">
      <div className="absolute flex items-center gap-[36px]" style={{ left: 40, top: 0 }}>
        {tab('Vehicle charging', true)}
        {tab('Power out')}
        {tab('Trip statistics')}
      </div>
      <button
        type="button"
        onClick={() => notify('Battery temperature control (showroom demo)')}
        className="absolute rounded-[4px] px-4 text-[14px] focus:outline-none"
        style={{ right: 0, top: 4, height: 36, background: t.card, color: t.text2 }}
      >
        Battery temperature control
      </button>
      {/* the Charge port cover tile: the car's own way to open the flap */}
      <button
        type="button"
        aria-pressed={openings.charge}
        onClick={tapChargeFlap}
        className="absolute flex flex-col items-center justify-center gap-[8px] rounded-[4px] text-[15px] focus:outline-none focus-visible:ring-2 focus-visible:ring-black/30"
        style={{
          left: 0, top: 150, width: 128, height: 96,
          background: openings.charge ? t.cardOn : t.card,
          color: openings.charge ? t.text : t.text2,
          boxShadow: openings.charge ? `inset 0 0 0 1.5px ${t.red}` : undefined,
        }}
      >
        <Ic.HsCharge size={28} />
        Charge port cover
      </button>
      {/* the car, side on, and the battery under it */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={`/hmi/${vehicle.slug}/car-side.webp`}
        alt=""
        aria-hidden
        draggable={false}
        className="pointer-events-none absolute"
        style={{ left: 170, top: 56, width: 520, opacity: 0.4, filter: 'grayscale(0.6)' }}
      />
      <div
        className="absolute rounded-[10px]"
        style={{ left: 250, top: 196, width: 340, height: 62, background: 'rgba(120,125,150,0.22)', boxShadow: `inset 0 0 0 2px ${t.line}` }}
        aria-label={`Battery ${pct} %`}
      >
        <span
          className="absolute inset-y-[5px] left-[5px] rounded-[6px]"
          style={{ width: `calc(${Math.max(0, Math.min(1, soc))} * (100% - 10px))`, background: t.green, transition: 'width 120ms linear' }}
        />
        <span className="absolute inset-0 flex items-center justify-center text-[22px] font-medium" style={{ color: '#fff', textShadow: '0 1px 3px rgba(0,0,0,0.35)' }}>
          {charging ? `${pct} %  ·  ${Math.round(live?.kw ?? 0)} kW` : `${pct} %`}
        </span>
      </div>
      <span className="absolute rounded-[3px] px-3 py-[3px] text-[13px]" style={{ left: 380, top: 164, background: t.card, color: t.text2 }}>
        Charge limit {limit}%
      </span>
      {/* what is left, and the range it gives */}
      <div className="absolute" style={{ left: 720, top: 150, width: 230 }}>
        {live && live.phase !== 'ready' ? (
          <>
            <div className="text-[15px]" style={{ color: t.text2 }}>
              {live.phase === 'charged' || live.phase === 'unplugging' || live.phase === 'done' ? 'Charged to the limit' : charging ? 'Charging' : 'Connecting'}
            </div>
            <div className="tnum mt-[6px] text-[40px] font-light leading-none">{charging || live.phase === 'charged' ? `${Math.round(live.kw)} kW` : '- kW'}</div>
            <div className="tnum mt-[8px] text-[15px]" style={{ color: t.text2 }}>
              {charging ? `${left} min to ${limit} %` : `${live.kwh.toFixed(1)} kWh added`}
            </div>
          </>
        ) : (
          <>
            <div className="text-[15px]" style={{ color: t.text2 }}>
              Remaining charge
            </div>
            <div className="tnum mt-[6px] text-[40px] font-light leading-none">{pct}%</div>
          </>
        )}
        <div className="tnum mt-[14px] text-[28px] font-light leading-none">{range ? `${range.km} km` : 'n/a'}</div>
        <div className="mt-[4px] text-[13px]" style={{ color: t.text3 }}>
          Estimated range
        </div>
      </div>
      <div className="absolute flex gap-[14px]" style={{ left: 0, right: 0, bottom: 0 }}>
        <div className="flex flex-1 items-center justify-between rounded-[4px] px-5" style={{ height: 62, background: t.card }}>
          <div>
            <div className="text-[16px]">Scheduled charging</div>
            <div className="text-[13px]" style={{ color: t.text3 }}>
              Every day 22:00 - 06:00
            </div>
          </div>
          <Switch on={on.scheduled} onClick={() => toggle('scheduled')} label="Scheduled charging" />
        </div>
        <div className="flex flex-1 items-center justify-between rounded-[4px] px-5" style={{ height: 62, background: t.card }}>
          <div>
            <div className="text-[16px]">Planned departure</div>
            <div className="text-[13px]" style={{ color: t.text3 }}>
              Not set
            </div>
          </div>
          <span style={{ color: t.text3 }}>›</span>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------ quick settings */

/** What the car's screen lists, top to bottom: Very high ... Very low. */
const RIDE_TOP_DOWN = [...RIDE_LEVELS].map((l, i) => ({ ...l, index: i })).reverse();

/**
 * Settings > Quick settings, as the 7X draws it (c10_0033, c10_0091): the drive modes in a row, the five
 * suspension heights in a column beside the car in side view, four shortcuts and Parking comfort below.
 * The height is the store's `rideLevel`, which the Tech tab's Magic Carpet demo shows on the 3D car.
 */
function QuickSettings({ vehicle }: { vehicle: Vehicle }) {
  const t = useZk();
  const { on, toggle, notify } = useZkLocal();
  const { driveMode, modeId, setCarMode, rideLevel, setRideLevel } = useVehicleStore();
  const modes = vehicle.cockpit.driveModes ?? [];
  const current = modes.findIndex((m) => (modeId ? m.id === modeId : m.model === driveMode));
  const label = (s: string) => (
    <div className="text-[15px]" style={{ color: t.text2 }}>
      {s}
    </div>
  );
  const shortcuts = [
    { id: 'mirrors', label: 'Rear-view mirrors', icon: <Ic.HsMirror size={26} />, run: () => notify('Mirror adjustment (showroom demo)') },
    { id: 'hud', label: 'Head-up display', icon: <Ic.Hud size={26} />, run: () => toggle('hud') },
    { id: 'wheel', label: 'Steering wheel', icon: <Ic.WheelP size={26} />, run: () => notify('Steering wheel adjustment (showroom demo)') },
    { id: 'stream', label: 'Streaming mirror', icon: <Ic.HsMirror size={26} />, run: () => notify('Streaming mirror (showroom demo)') },
  ];
  return (
    <div className="relative h-full">
      {label('Drive mode')}
      <div className="mt-[8px]">
        <Segment options={modes.map((m) => m.label)} value={current} onPick={(i) => setCarMode(modes[i].id, modes[i].model)} minW={112} />
      </div>
      <div className="absolute" style={{ left: 0, top: 96 }}>
        {label('Suspension height')}
        <div className="mt-[8px] flex flex-col gap-[3px]">
          {RIDE_TOP_DOWN.map((l) => (
            <Pill key={l.id} on={rideLevel === l.index} onClick={() => setRideLevel(l.index)} w={112} h={42}>
              {l.label}
            </Pill>
          ))}
        </div>
      </div>
      {/* the car, side on, with the floor's reflection */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/hmi/zeekr-7x/car-side.webp"
        alt=""
        aria-hidden
        draggable={false}
        className="pointer-events-none absolute object-contain"
        style={{ left: 150, top: 70, width: 700, height: 290 }}
      />
      <div className="absolute flex items-center gap-[14px]" style={{ left: 0, right: 0, bottom: 4 }}>
        {shortcuts.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={s.run}
            className="flex h-[70px] w-[132px] flex-col items-center justify-center gap-[6px] rounded-[4px] text-[13px] focus:outline-none focus-visible:ring-2 focus-visible:ring-black/30"
            style={{ background: t.card, color: t.text2 }}
          >
            {s.icon}
            {s.label}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-3 text-[15px]" style={{ color: t.text2 }}>
          <Switch on={on.parkComfort} onClick={() => toggle('parkComfort')} label="Parking comfort" />
          Parking comfort
        </div>
      </div>
    </div>
  );
}

/* ----------------------------------------------------------------- driving */

/**
 * Settings > Driving, as the 7X draws it (c10_0036): energy recovery, brake assist, Motion-sickness relief,
 * Suspension easy entry (the body lowers by itself once parked and a belt is unbuckled: the Tech tab's seat-belt
 * switch shows it), One-Pedal and Auto hold.
 */
function DrivingPage() {
  const t = useZk();
  const { val, setVal, on, toggle } = useZkLocal();
  const { easyEntry, setEasyEntry } = useVehicleStore();
  return (
    <div className="relative h-full">
      <div className="flex h-full flex-col gap-[10px] overflow-y-auto pr-2" style={{ width: 590, scrollbarWidth: 'none' }}>
        <div className="text-[15px]" style={{ color: t.text3 }}>
          Driving preferences
        </div>
        <Row label="Energy recovery level">
          <Segment options={['None', 'Low', 'Medium', 'High']} value={val.regenLevel} onPick={(i) => setVal('regenLevel', i)} minW={70} />
        </Row>
        <Row label="Brake assist" sub="Set it while the car is stationary">
          <Segment options={['Comfort', 'Standard', 'Sport']} value={val.brakeAssist} onPick={(i) => setVal('brakeAssist', i)} minW={84} />
        </Row>
        <Row label="Motion-sickness relief" sub="Adjusts how the car drives, for a more comfortable ride">
          <Switch on={on.motionRelief} onClick={() => toggle('motionRelief')} label="Motion-sickness relief" />
        </Row>
        <Row label="Suspension easy entry" sub="Once the car is parked and a seat belt is unbuckled, the suspension lowers by itself, so you and your passengers can get in and out easily.">
          <Switch on={easyEntry} onClick={() => setEasyEntry(!easyEntry)} label="Suspension easy entry" />
        </Row>
        <Row label="One-Pedal" sub="The accelerator pedal controls both acceleration and slowing down">
          <Switch on={on.onePedal} onClick={() => toggle('onePedal')} label="One-Pedal" />
        </Row>
        <Row label="Auto hold" sub="Keeps the car still by itself once it has stopped">
          <Switch on={on.autoHold} onClick={() => toggle('autoHold')} label="Auto hold" />
        </Row>
      </div>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/hmi/zeekr-7x/car34.webp"
        alt=""
        aria-hidden
        draggable={false}
        className="pointer-events-none absolute object-contain"
        style={{ right: -40, top: 70, width: 340, opacity: 0.96 }}
      />
    </div>
  );
}

/* -------------------------------------------------------------------- media */

const TRACKS = [
  { title: 'Neon Arterial', artist: 'Hong Kong Sunset', album: 'Night Drive', c: ['#6a5cff', '#ff7ab8'] },
  { title: 'Bund at 3AM', artist: 'Shanghai Tape Club', album: 'Long Exposure', c: ['#1d3a8a', '#4dc3ff'] },
  { title: 'Gobi Transmission', artist: 'Silk Road Signal', album: 'Dust & Voltage', c: ['#f08a3c', '#f4d35e'] },
  { title: 'Pearl River Delta', artist: 'Nanfang', album: 'Humidity', c: ['#12a67a', '#a3e635'] },
];

export function MediaPage() {
  const t = useZk();
  const { media, patchMedia } = useVehicleStore();
  const { val, setVal } = useZkLocal();
  const track = TRACKS[media.trackIndex % TRACKS.length];
  const [pos, setPos] = React.useState(0.18);
  React.useEffect(() => {
    if (!media.playing) return;
    const id = window.setInterval(() => setPos((p) => (p + 0.004) % 1), 500);
    return () => window.clearInterval(id);
  }, [media.playing]);
  const go = (d: number) => patchMedia({ trackIndex: (media.trackIndex + d + TRACKS.length) % TRACKS.length });
  return (
    <div className="absolute inset-0">
      <div className="absolute flex gap-3" style={{ left: 60, top: 26 }}>
        {['Online music', 'Bluetooth', 'Radio'].map((s, i) => (
          <Pill key={s} on={val.mediaSource === i} onClick={() => setVal('mediaSource', i)} h={38}>
            {s}
          </Pill>
        ))}
      </div>
      <div
        className="absolute grid place-items-center rounded-[10px]"
        style={{ left: 60, top: 88, width: 290, height: 290, background: `linear-gradient(140deg, ${track.c[0]}, ${track.c[1]})`, boxShadow: '0 12px 30px rgba(60,60,110,0.25)' }}
      >
        <Ic.Music size={96} style={{ color: 'rgba(255,255,255,0.88)' }} />
      </div>
      <div className="absolute" style={{ left: 400, top: 96, width: 520 }}>
        <div className="text-[34px] font-light leading-tight">{track.title}</div>
        <div className="mt-2 text-[18px]" style={{ color: t.text2 }}>
          {track.artist} · {track.album}
        </div>
        <div className="mt-10 h-[4px] w-full rounded-full" style={{ background: t.line }}>
          <div className="h-full rounded-full" style={{ width: `${pos * 100}%`, background: t.text }} />
        </div>
        <div className="mt-2 flex justify-between text-[13px]" style={{ color: t.text3 }}>
          <span className="tnum">{Math.floor(pos * 215 / 60)}:{String(Math.floor((pos * 215) % 60)).padStart(2, '0')}</span>
          <span className="tnum">3:35</span>
        </div>
        <div className="mt-8 flex items-center gap-10">
          <button type="button" aria-label="Previous" onClick={() => go(-1)} className="focus:outline-none"><Ic.Prev size={34} /></button>
          <button
            type="button"
            aria-label={media.playing ? 'Pause' : 'Play'}
            onClick={() => patchMedia({ playing: !media.playing })}
            className="grid h-[64px] w-[64px] place-items-center rounded-full focus:outline-none"
            style={{ background: t.pill, color: t.pillText }}
          >
            {media.playing ? <Ic.Pause size={28} /> : <Ic.Play size={28} />}
          </button>
          <button type="button" aria-label="Next" onClick={() => go(1)} className="focus:outline-none"><Ic.Next size={34} /></button>
        </div>
      </div>
      <div className="absolute flex flex-col gap-[8px]" style={{ left: 980, top: 26, width: 240 }}>
        {TRACKS.map((tr, i) => (
          <button
            key={tr.title}
            type="button"
            onClick={() => patchMedia({ trackIndex: i, playing: true })}
            className="flex h-[58px] items-center gap-3 rounded-[4px] px-3 text-left focus:outline-none"
            style={{ background: i === media.trackIndex % TRACKS.length ? t.cardOn : t.card, boxShadow: i === media.trackIndex % TRACKS.length ? `inset 0 0 0 1.5px ${t.red}` : undefined }}
          >
            <span className="h-[38px] w-[38px] shrink-0 rounded-[6px]" style={{ background: `linear-gradient(140deg, ${tr.c[0]}, ${tr.c[1]})` }} />
            <span className="min-w-0">
              <span className="block truncate text-[15px] leading-tight">{tr.title}</span>
              <span className="block truncate text-[12px] leading-tight" style={{ color: t.text3 }}>{tr.artist}</span>
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- nav and camera */

export function NavPage() {
  const t = useZk();
  const { notify } = useZkLocal();
  const land = t.tone === 'light' ? '#e4ebf1' : '#1b2430';
  return (
    <div className="absolute inset-0 overflow-hidden" style={{ background: land }}>
      <svg viewBox="0 0 1280 740" preserveAspectRatio="xMidYMid slice" className="absolute inset-0 h-full w-full" aria-hidden>
        <rect width="1280" height="740" fill={land} />
        <path d="M0 520 C 240 470 400 260 640 250 S 1040 120 1280 90 L1280 0 L0 0Z" fill={t.tone === 'light' ? '#cde4c9' : '#1d3a2d'} opacity="0.7" />
        <path d="M900 740 C 980 640 1100 600 1280 590 L1280 740Z" fill={t.tone === 'light' ? '#c4dcef' : '#16314a'} opacity="0.8" />
        <path d="M-20 640 C 280 560 440 380 660 350 S 980 210 1300 160" fill="none" stroke="#fff" strokeWidth="26" opacity="0.9" />
        <path d="M-20 640 C 280 560 440 380 660 350 S 980 210 1300 160" fill="none" stroke="#2d7df6" strokeWidth="9" strokeLinecap="round" />
        <path d="M180 0 L430 740M780 0 L700 740M1060 0 L1180 740M0 300 L1280 420" stroke="#fff" strokeWidth="14" opacity="0.8" />
        <circle cx="660" cy="350" r="14" fill="#2d7df6" stroke="#fff" strokeWidth="4" />
      </svg>
      <button
        type="button"
        onClick={() => notify('Search (showroom demo)')}
        className="absolute flex items-center gap-3 rounded-[6px] px-5 text-left text-[17px] focus:outline-none"
        style={{ left: 40, top: 70, height: 56, width: 440, background: t.cardOn, color: t.text2 }}
      >
        <Ic.NavArrow size={30} />
        Where to?
      </button>
    </div>
  );
}

export function CameraPage({ vehicle }: { vehicle: Vehicle }) {
  const t = useZk();
  const [pair, setPair] = React.useState(0);
  const feeds = pair === 0 ? [['Front', 'Parked: clear'], ['Rear', 'Parked: clear']] : [['Left', 'Mirror camera'], ['Right', 'Mirror camera']];
  const panel = t.tone === 'light' ? '#dfe3f2' : '#1c202a';
  const feed = (label: string, sub: string, y: number) => (
    <div key={label} className="absolute overflow-hidden rounded-[4px]" style={{ left: 530, top: y, width: 710, height: 316, background: t.tone === 'light' ? '#cfd6e6' : '#222733' }}>
      <svg viewBox="0 0 710 316" width="710" height="316" aria-hidden>
        <path d="M0 316 L190 130 L520 130 L710 316Z" fill={t.tone === 'light' ? '#b7c0d6' : '#2d3445'} />
        <path d="M0 150 L710 150" stroke={t.line} strokeWidth="2" />
        <path d="M250 316 L300 200M460 316 L410 200" stroke="#7ac27e" strokeWidth="5" strokeLinecap="round" opacity="0.8" />
      </svg>
      <span className="absolute left-4 top-3 text-[15px]" style={{ color: t.text2 }}>{label}</span>
      <span className="absolute bottom-3 left-4 text-[13px]" style={{ color: t.text3 }}>{sub}</span>
    </div>
  );
  return (
    <div className="absolute inset-0">
      <div className="absolute grid place-items-center overflow-hidden rounded-[4px]" style={{ left: 40, top: 62, width: 460, height: 640, background: panel }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={`/hmi/${vehicle.slug}/car-top.webp`}
          alt=""
          draggable={false}
          onError={(e) => {
            e.currentTarget.style.display = 'none';
          }}
          style={{ height: 470, width: 'auto', filter: 'brightness(1.3) saturate(0.92)' }}
        />
        <div className="absolute bottom-4 flex gap-2">
          <Pill on={pair === 0} onClick={() => setPair(0)} h={34}>Front / Rear</Pill>
          <Pill on={pair === 1} onClick={() => setPair(1)} h={34}>Left / Right</Pill>
        </div>
      </div>
      {feed(feeds[0][0], feeds[0][1], 62)}
      {feed(feeds[1][0], feeds[1][1], 386)}
    </div>
  );
}
