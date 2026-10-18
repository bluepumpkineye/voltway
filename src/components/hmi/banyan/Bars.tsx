'use client';

import React from 'react';
import { useVehicleStore, type HmiScreen } from '@/store/vehicle-store';
import {
  cx,
  HomeIcon,
  ClimateIcon,
  NavIcon,
  MediaIcon,
  ControlsIcon,
  PlusIcon,
  MinusIcon,
} from '../ui';
import { useBanyan, TOP_BAR_H, BOTTOM_BAR_H } from './theme';
import { useBanyanLocal } from './shared';
import {
  NomiFace,
  QueenSeatIcon,
  Chassis4DIcon,
  NioPowerSwapIcon,
  DolbyAtmosIcon,
} from './icons';

export function StatusBar() {
  const t = useBanyan();
  const { nomiMood, speakNomi, nomiBubble } = useBanyanLocal();
  const [time, setTime] = React.useState('15:55');

  React.useEffect(() => {
    const update = () => {
      const now = new Date();
      setTime(
        `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`,
      );
    };
    update();
    const id = setInterval(update, 10000);
    return () => clearInterval(id);
  }, []);

  const onNomiClick = () => {
    const quotes = [
      'Hi! I am NOMI. All systems optimal!',
      'NIO Power Swap 3.0 station ready nearby!',
      'PanoCinema 7.1.4 Dolby Atmos tuned.',
      '4D Dynamic Chassis active and smoothing road.',
      'Queen Co-pilot seat zero-gravity available.',
    ];
    const quote = quotes[Math.floor(Math.random() * quotes.length)];
    speakNomi(quote, 'happy');
  };

  return (
    <div
      className="absolute inset-x-0 top-0 z-40 flex items-center justify-between px-6 select-none"
      style={{ height: TOP_BAR_H, background: t.barOverScene }}
    >
      {/* left status metrics */}
      <div className="flex items-center gap-4 text-[14px]">
        <span className="font-semibold text-white tracking-wide">{time}</span>
        <span className="text-white/40">|</span>
        <span className="text-white/80">24°C</span>
        <span className="flex items-center gap-1.5 rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-[11px] font-medium text-emerald-400 ring-1 ring-emerald-500/25">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          AQI 28 优
        </span>
      </div>

      {/* center: interactive NOMI avatar capsule */}
      <div className="relative flex items-center justify-center">
        <button
          type="button"
          onClick={onNomiClick}
          className="group flex items-center gap-2 rounded-full bg-white/[0.07] px-3 py-1 ring-1 ring-white/10 transition-all hover:bg-white/[0.12] hover:ring-[#00C2A8]/50 focus:outline-none"
          title="Tap to interact with NOMI Mate"
        >
          <NomiFace mood={nomiMood} size={24} />
          <span className="text-[12px] font-medium text-white/90 group-hover:text-[#00C2A8] transition-colors">
            NOMI
          </span>
        </button>

        {/* NOMI speech bubble popup */}
        {nomiBubble && (
          <div
            className="pointer-events-none absolute top-10 whitespace-nowrap rounded-2xl bg-[#0e131d]/95 px-4 py-2 text-[13px] font-medium text-white shadow-2xl ring-1 ring-[#00C2A8]/40 backdrop-blur-md transition-all duration-300"
            style={{ animation: 'nomiPop 250ms cubic-bezier(0.16, 1, 0.3, 1)' }}
          >
            <div className="flex items-center gap-2">
              <span className="text-[#00C2A8]">✨</span>
              <span>{nomiBubble}</span>
            </div>
          </div>
        )}
      </div>

      {/* right connectivity metrics */}
      <div className="flex items-center gap-4 text-[13px] text-white/70">
        <span className="flex items-center gap-1 text-[11px] font-semibold tracking-wider text-[#00C2A8]">
          5G
        </span>
        <svg width="18" height="12" viewBox="0 0 18 12" fill="currentColor">
          <rect x="1" y="8" width="2.5" height="4" rx="0.5" />
          <rect x="5.5" y="6" width="2.5" height="6" rx="0.5" />
          <rect x="10" y="3" width="2.5" height="9" rx="0.5" />
          <rect x="14.5" y="0" width="2.5" height="12" rx="0.5" />
        </svg>
        <span className="flex items-center gap-1 text-[11px] text-white/50" title="Dolby Atmos 7.1.4">
          <DolbyAtmosIcon size={16} />
          <span className="font-medium">Atmos</span>
        </span>
        <div className="flex items-center gap-1.5 rounded-full bg-white/[0.08] px-2.5 py-0.5 text-[12px] text-white/90">
          <span className="h-2 w-2 rounded-full bg-[#00C2A8]" />
          <span>Edward · ES8</span>
        </div>
      </div>
    </div>
  );
}

export function BottomBar({
  screen,
  onScreen,
  appCentreOpen,
  onToggleApps,
}: {
  screen: HmiScreen;
  onScreen: (s: HmiScreen) => void;
  appCentreOpen: boolean;
  onToggleApps: () => void;
}) {
  const t = useBanyan();
  const { climate, patchClimate } = useVehicleStore();
  const { speakNomi } = useBanyanLocal();

  const changeTemp = (delta: number, isDriver: boolean) => {
    if (isDriver) {
      const val = Math.min(28, Math.max(16, Math.round((climate.driverTempC + delta) * 2) / 2));
      patchClimate({ driverTempC: val });
      speakNomi(`Cabin temperature set to ${val}°C`);
    } else {
      const val = Math.min(28, Math.max(16, Math.round((climate.passengerTempC + delta) * 2) / 2));
      patchClimate({ passengerTempC: val });
    }
  };

  const isHome = screen === 'home' && !appCentreOpen;

  return (
    <div
      className="absolute inset-x-0 bottom-0 z-40 flex items-center justify-between px-6 select-none shadow-[0_-10px_25px_rgba(0,0,0,0.4)]"
      style={{ height: BOTTOM_BAR_H, background: t.bar }}
    >
      {/* 1. Left Navigation Group: Home & Vehicle Controls */}
      <div className="flex items-center gap-3">
        {/* Signature Circular NIO Home Button */}
        <button
          type="button"
          onClick={() => {
            if (appCentreOpen) onToggleApps();
            onScreen('home');
          }}
          className={cx(
            'flex h-14 w-14 items-center justify-center rounded-full transition-all duration-200 focus:outline-none',
            isHome
              ? 'bg-[#00C2A8] text-black shadow-[0_0_20px_rgba(0,194,168,0.5)]'
              : 'bg-white/[0.08] text-white hover:bg-white/[0.14]',
          )}
          aria-label="Home"
        >
          <HomeIcon />
        </button>

        {/* Vehicle Controls Button */}
        <button
          type="button"
          onClick={() => {
            if (appCentreOpen) onToggleApps();
            onScreen('controls');
          }}
          className={cx(
            'flex h-12 items-center gap-2 rounded-2xl px-4 text-[14px] font-medium transition-all duration-200 focus:outline-none',
            screen === 'controls' && !appCentreOpen
              ? 'bg-[#00C2A8]/15 text-[#00C2A8] ring-1 ring-[#00C2A8]/50'
              : 'bg-white/[0.06] text-white/80 hover:bg-white/[0.10]',
          )}
        >
          <ControlsIcon />
          <span>Controls</span>
        </button>

        {/* 4D Chassis & Air Suspension */}
        <button
          type="button"
          onClick={() => {
            if (appCentreOpen) onToggleApps();
            onScreen('chassis');
          }}
          className={cx(
            'flex h-12 items-center gap-2 rounded-2xl px-4 text-[14px] font-medium transition-all duration-200 focus:outline-none',
            screen === 'chassis' && !appCentreOpen
              ? 'bg-[#00C2A8]/15 text-[#00C2A8] ring-1 ring-[#00C2A8]/50'
              : 'bg-white/[0.06] text-white/80 hover:bg-white/[0.10]',
          )}
        >
          <Chassis4DIcon size={20} />
          <span>4D Chassis</span>
        </button>
      </div>

      {/* 2. Center Climate Quick Pills */}
      <div className="flex items-center gap-3 rounded-2xl bg-white/[0.05] p-1.5 ring-1 ring-white/10">
        {/* Driver Temp Stepper */}
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => changeTemp(-0.5, true)}
            className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/[0.06] text-white/70 hover:bg-white/[0.12] active:scale-95"
          >
            <MinusIcon />
          </button>
          <span className="tnum px-2 text-[17px] font-semibold text-white">
            {climate.driverTempC.toFixed(1)}°
          </span>
          <button
            type="button"
            onClick={() => changeTemp(0.5, true)}
            className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/[0.06] text-white/70 hover:bg-white/[0.12] active:scale-95"
          >
            <PlusIcon />
          </button>
        </div>

        {/* Climate Master button */}
        <button
          type="button"
          onClick={() => {
            if (appCentreOpen) onToggleApps();
            onScreen('climate');
          }}
          className={cx(
            'flex h-10 items-center gap-2 rounded-xl px-3.5 text-[13px] font-medium transition-all',
            screen === 'climate' && !appCentreOpen
              ? 'bg-[#00C2A8] text-black font-semibold'
              : 'bg-white/[0.08] text-white/90 hover:bg-white/[0.14]',
          )}
        >
          <ClimateIcon />
          <span>Auto {climate.acOn ? 'A/C' : 'Fan'}</span>
        </button>

        {/* Passenger Temp Stepper */}
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => changeTemp(-0.5, false)}
            className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/[0.06] text-white/70 hover:bg-white/[0.12] active:scale-95"
          >
            <MinusIcon />
          </button>
          <span className="tnum px-2 text-[17px] font-semibold text-white">
            {climate.passengerTempC.toFixed(1)}°
          </span>
          <button
            type="button"
            onClick={() => changeTemp(0.5, false)}
            className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/[0.06] text-white/70 hover:bg-white/[0.12] active:scale-95"
          >
            <PlusIcon />
          </button>
        </div>
      </div>

      {/* 3. Right App Shortcuts: Queen Seat, Power/Charging, Nav, Media, Apps */}
      <div className="flex items-center gap-2">
        {/* Queen Co-pilot Seat */}
        <button
          type="button"
          onClick={() => {
            if (appCentreOpen) onToggleApps();
            onScreen('seats');
          }}
          className={cx(
            'flex h-12 w-12 items-center justify-center rounded-2xl transition-all duration-200 focus:outline-none',
            screen === 'seats' && !appCentreOpen
              ? 'bg-[#00C2A8]/15 text-[#00C2A8] ring-1 ring-[#00C2A8]/50'
              : 'bg-white/[0.06] text-white/80 hover:bg-white/[0.10]',
          )}
          title="Queen Co-pilot Seat Zero Gravity"
        >
          <QueenSeatIcon size={20} />
        </button>

        {/* NIO Power & Charging */}
        <button
          type="button"
          onClick={() => {
            if (appCentreOpen) onToggleApps();
            onScreen('charge');
          }}
          className={cx(
            'flex h-12 w-12 items-center justify-center rounded-2xl transition-all duration-200 focus:outline-none',
            screen === 'charge' && !appCentreOpen
              ? 'bg-[#00C2A8]/15 text-[#00C2A8] ring-1 ring-[#00C2A8]/50'
              : 'bg-white/[0.06] text-white/80 hover:bg-white/[0.10]',
          )}
          title="NIO Power Swap & DC Charging"
        >
          <NioPowerSwapIcon size={20} />
        </button>

        {/* Navigation */}
        <button
          type="button"
          onClick={() => {
            if (appCentreOpen) onToggleApps();
            onScreen('nav');
          }}
          className={cx(
            'flex h-12 w-12 items-center justify-center rounded-2xl transition-all duration-200 focus:outline-none',
            screen === 'nav' && !appCentreOpen
              ? 'bg-[#00C2A8]/15 text-[#00C2A8] ring-1 ring-[#00C2A8]/50'
              : 'bg-white/[0.06] text-white/80 hover:bg-white/[0.10]',
          )}
          title="Navigation & Map"
        >
          <NavIcon />
        </button>

        {/* PanoCinema Media */}
        <button
          type="button"
          onClick={() => {
            if (appCentreOpen) onToggleApps();
            onScreen('media');
          }}
          className={cx(
            'flex h-12 w-12 items-center justify-center rounded-2xl transition-all duration-200 focus:outline-none',
            screen === 'media' && !appCentreOpen
              ? 'bg-[#00C2A8]/15 text-[#00C2A8] ring-1 ring-[#00C2A8]/50'
              : 'bg-white/[0.06] text-white/80 hover:bg-white/[0.10]',
          )}
          title="PanoCinema Audio"
        >
          <MediaIcon />
        </button>

        {/* Application Launcher Drawer */}
        <button
          type="button"
          onClick={onToggleApps}
          className={cx(
            'flex h-12 w-12 items-center justify-center rounded-2xl transition-all duration-200 focus:outline-none',
            appCentreOpen
              ? 'bg-[#00C2A8] text-black shadow-[0_0_15px_rgba(0,194,168,0.4)]'
              : 'bg-white/[0.06] text-white/80 hover:bg-white/[0.10]',
          )}
          title="All Applications"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <rect x="3" y="3" width="7" height="7" rx="2" />
            <rect x="14" y="3" width="7" height="7" rx="2" />
            <rect x="3" y="14" width="7" height="7" rx="2" />
            <rect x="14" y="14" width="7" height="7" rx="2" />
          </svg>
        </button>
      </div>
    </div>
  );
}
