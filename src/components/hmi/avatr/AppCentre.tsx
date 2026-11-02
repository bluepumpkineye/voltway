'use client';

import React from 'react';
import type { Variant } from '@/data/vehicles/schema';
import { useVehicleStore } from '@/store/vehicle-store';
import { effectiveRange } from '@/lib/performance';
import * as Ha from '../harmonyos/icons';
import { AppIcon, APPS, type AppId } from '../harmonyos/appicons';
import { useHaLocal } from '../harmonyos/shared';
import * as Ic from './icons';
import { STATUS_H, BAR_H, glass } from './theme';
import { TabRow } from './ui';

const FREQUENT: AppId[] = ['settings', 'music', 'btmusic', 'market', 'butler', 'video'];
/** The apps the car lists after the frequent ones (c10_0039); the Luxeed RX's own (3D Flex Space, Sound Cube) are not here. */
const ALL: AppId[] = ['phone', 'guide', 'camera', 'calendar', 'weather', 'gallery', 'radio', 'usb', 'dashcam', 'life', 'account', 'health', 'search', 'care'];

/**
 * The App Centre (c10_0039-41): a full page on a deep blue blurred ground with its three tabs (App Centre,
 * Service Centre, Super Desktop) under the status bar. App Centre lists the frequent apps and all the
 * others in rows of six; Service Centre holds the glass service cards (calendar, frequent apps, weather,
 * energy, tips); Super Desktop asks for a Huawei account. The apps the showroom can open do; the others say so.
 */
export function AppCentre({ variant }: { variant: Variant }) {
  const { setAppCentreOpen, setHmiScreen, openSettings, driveMode, soc, climate, patchMedia } = useVehicleStore();
  const { notify, setVal } = useHaLocal();
  const [tab, setTab] = React.useState(0);
  const range = effectiveRange(variant, driveMode, soc, climate);

  const open = (id: AppId, label: string) => {
    setAppCentreOpen(false);
    switch (id) {
      case 'settings': openSettings('vehicle'); return;
      case 'radio': setVal('media', 1); setHmiScreen('media'); return;
      case 'music':
      case 'btmusic':
      case 'usb': setVal('media', 0); patchMedia({ playing: true }); setHmiScreen('media'); return;
      case 'camera': setHmiScreen('camera'); return;
      case 'butler':
      case 'care': openSettings('status'); return;
      default:
        setAppCentreOpen(true);
        notify(`${label} is not part of the showroom demo`);
    }
  };

  const grid = (ids: { id: AppId; label: string }[]) => (
    <div className="grid grid-cols-6 gap-y-[26px]" style={{ width: 1000 }}>
      {ids.map((a) => (
        <button key={a.id} type="button" onClick={() => open(a.id, a.label)} className="flex flex-col items-center gap-[9px] rounded-[16px] outline-none focus-visible:ring-2 focus-visible:ring-white/70">
          <AppIcon id={a.id} size={76} />
          <span className="w-[150px] truncate text-center text-[15px] leading-none text-white/90">{a.label}</span>
        </button>
      ))}
    </div>
  );

  const card = (col: number, row: number, label: string, icon: React.ReactNode, body: React.ReactNode, onClick?: () => void) => (
    <div key={label} className="absolute" style={{ left: 196 + col * 302, top: 196 + row * 190, width: 274 }}>
      <button type="button" onClick={onClick} className="relative block h-[118px] w-full overflow-hidden rounded-[20px] text-left text-white outline-none focus-visible:ring-2 focus-visible:ring-white/70" style={glass(0.34, 18)}>
        {body}
      </button>
      <div className="mt-[10px] flex items-center justify-between px-[4px] text-[14px] text-white/85">
        <span className="flex items-center gap-[8px]"><span className="flex h-[20px] w-[20px] items-center justify-center rounded-full bg-white/20">{icon}</span>{label}</span>
        <Ic.LockOpen size={16} style={{ opacity: 0.6 }} />
      </div>
    </div>
  );

  const now = new Date();
  const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  return (
    <div className="absolute inset-0 z-10 overflow-hidden text-white" style={{ background: 'radial-gradient(70% 60% at 38% 78%, #3f6fc2 0%, rgba(63,111,194,0) 62%), radial-gradient(60% 50% at 82% 24%, #26467f 0%, rgba(38,70,127,0) 65%), linear-gradient(180deg,#0e1f45,#0a1633)' }}>
      <TabRow
        tabs={['App Centre', 'Service Centre', 'Super Desktop']}
        value={tab}
        onChange={setTab}
        onDark
        className="absolute flex gap-[88px]"
        style={{ left: 640, top: STATUS_H + 18, transform: 'translateX(-50%)' }}
      />
      {tab === 0 && (
        <div className="absolute overflow-y-auto" style={{ left: 196, top: STATUS_H + 78, bottom: BAR_H + 6, right: 40, scrollbarWidth: 'none' }}>
          <div className="mb-[14px] text-[16px] text-white/85">Frequent apps</div>
          {grid(FREQUENT.map((id) => APPS.find((a) => a.id === id)!))}
          <div className="mb-[14px] mt-[30px] text-[16px] text-white/85">All apps</div>
          {grid(ALL.map((id) => APPS.find((a) => a.id === id)!))}
          <div className="h-[20px]" />
        </div>
      )}
      {tab === 1 && (
        <>
          <div className="absolute text-[16px] text-white/85" style={{ left: 196, top: STATUS_H + 78 }}>All services</div>
          {card(0, 0, 'Calendar', <Ic.Compare size={12} />, (
            <>
              <span className="absolute left-[18px] top-[12px] text-[13px] opacity-80">{DAYS[now.getDay()]}</span>
              <span className="absolute left-[18px] top-[34px] text-[38px] font-light leading-none">{now.getDate()}</span>
            </>
          ))}
          {card(1, 0, 'Frequent apps card', <Ic.Grid size={12} />, (
            <>
              <span className="absolute left-[16px] top-[10px] text-[12px] opacity-80">Frequent apps</span>
              {(['music', 'video', 'market', 'guide'] as const).map((id, i) => (
                <span key={id} className="absolute" style={{ left: 14 + i * 64, top: 36 }}><AppIcon id={id} size={50} /></span>
              ))}
            </>
          ))}
          {card(2, 0, 'City weather', <Ha.Cloud size={12} />, (
            <>
              <span className="absolute left-[16px] top-[12px] text-[12px] opacity-80">Chaoyang</span>
              <span className="absolute left-[16px] top-[34px] text-[40px] font-light leading-none">19<span className="text-[16px]">°C</span></span>
              <span className="absolute right-[16px] top-[16px] text-[12px] leading-tight opacity-85">21°C / 9°C<br />Light pollution</span>
            </>
          ))}
          {card(0, 1, 'Energy card', <Ic.MenuEnergy size={12} />, (
            <>
              <span className="absolute left-[16px] top-[14px] leading-none"><span className="tnum text-[20px] font-semibold">{range ? range.km : '--'}</span><span className="ml-[2px] text-[11px]">km</span></span>
              <span className="absolute left-[16px] top-[40px] text-[11px] opacity-80">Remaining range</span>
              <span className="absolute left-[16px] top-[76px] text-[11px] opacity-80">-- kWh/100km</span>
              <span className="absolute right-[18px] top-[18px] flex h-[78px] w-[78px] items-center justify-center rounded-full text-[20px] font-medium" style={{ border: '5px solid rgba(255,255,255,0.25)', borderTopColor: '#8fe3a8', borderRightColor: '#8fe3a8' }}>{Math.round(soc * 100)}%</span>
            </>
          ))}
          {card(1, 1, 'Smart tips', <Ic.Bulb size={12} />, (
            <>
              <span className="absolute left-1/2 top-[14px] h-[40px] w-[40px] -translate-x-1/2 rounded-full" style={{ background: 'conic-gradient(from 20deg,#f0f4ff,#7f93c9,#f0f4ff)' }} />
              <span className="absolute inset-x-0 top-[66px] text-center text-[12px] opacity-85">Hello, welcome. Tips for you</span>
            </>
          ))}
        </>
      )}
      {tab === 2 && (
        <div className="absolute inset-0">
          <div className="absolute flex flex-col items-center text-center" style={{ left: 214, top: 280, width: 440 }}>
            <span className="flex h-[84px] w-[84px] items-center justify-center rounded-full bg-white/18"><Ic.User size={48} /></span>
            <div className="mt-[22px] text-[19px]">Tap to sign in</div>
            <p className="mt-[10px] text-[14px] leading-[1.6] text-white/70">Sign in with the account on your phone, and turn on Bluetooth and WLAN on both to link the car and the phone.</p>
            <button type="button" onClick={() => notify('Connecting a phone is not part of the showroom demo')} className="mt-[22px] rounded-full px-[26px] py-[10px] text-[15px] outline-none" style={{ background: 'rgba(255,255,255,0.14)' }}>Connect another Huawei phone</button>
          </div>
          <div className="absolute" style={{ left: 760, top: 270, width: 340, height: 220 }}>
            <span className="absolute left-0 top-[46px] h-[128px] w-[72px] rounded-[10px] bg-white/85" />
            <span className="absolute right-0 top-0 h-[170px] w-[250px] rounded-[10px] bg-white/70" style={{ boxShadow: '0 0 0 4px rgba(20,30,60,0.6)' }} />
            <span className="absolute bottom-[8px] right-[50px] rounded-full border px-[16px] py-[3px] text-[13px]" style={{ borderColor: 'rgba(255,255,255,0.5)' }}>HUAWEI HiCar</span>
          </div>
        </div>
      )}
    </div>
  );
}
