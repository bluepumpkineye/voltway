'use client';

import React from 'react';
import { useVehicleStore } from '@/store/vehicle-store';
import * as Ic from './icons';
import { AppIcon, APPS, type AppId } from './appicons';
import { useHa } from './theme';
import { useHaLocal } from './shared';

const INDEX = ['#', 'C', 'D', 'H', 'L', 'R', 'S', 'T', 'U', 'X', 'Y', 'Z'];
const FREQUENT: AppId[] = ['settings', 'music', 'life', 'connect', 'market', 'flex3d', 'guide'];

/**
 * The App Centre: a panel over the screen with the apps in a grid (the first
 * row the frequent ones), an alphabet index down its side and a switch to the
 * Super Desktop. Apps the showroom can open do; the others say so.
 */
export function AppCentre() {
  const t = useHa();
  const { setAppCentreOpen, setHmiScreen, openSettings } = useVehicleStore();
  const { notify, setVal } = useHaLocal();
  const [tab, setTab] = React.useState<'apps' | 'super'>('apps');
  const close = () => setAppCentreOpen(false);

  const open = (id: AppId, label: string) => {
    switch (id) {
      case 'settings': openSettings('vehicle'); return;
      case 'radio': setVal('media', 1); setHmiScreen('media'); return;
      case 'music':
      case 'btmusic':
      case 'usb': setVal('media', 0); setHmiScreen('media'); return;
      case 'camera': setHmiScreen('camera'); return;
      case 'butler':
      case 'care': openSettings('status'); return;
      case 'flex3d': setHmiScreen('home'); return;
      default: notify(`${label} is not part of the showroom demo`);
    }
  };

  const grid = (ids: { id: AppId; label: string }[]) => (
    <div className="grid grid-cols-8 gap-x-[34px] gap-y-[22px]">
      {ids.map((a) => (
        <button
          key={a.id}
          type="button"
          onClick={() => open(a.id, a.label)}
          className="flex w-[78px] flex-col items-center gap-[9px] rounded-[16px] outline-none focus-visible:ring-2 focus-visible:ring-[#4a74ff]"
        >
          <AppIcon id={a.id} size={78} />
          <span className="w-[100px] truncate text-center text-[15px] leading-none" style={{ color: t.text }}>{a.label}</span>
        </button>
      ))}
    </div>
  );

  return (
    <div className="absolute inset-0 z-40" onClick={close}>
      <div className="absolute inset-0" style={{ background: 'rgba(0,0,0,0.22)' }} />
      <div
        className="absolute flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
        style={{
          left: 157, top: 197, width: 966, height: 540, borderRadius: 42,
          background: t.panel, color: t.text, backdropFilter: 'blur(36px) saturate(1.3)', boxShadow: '0 30px 80px rgba(0,0,0,0.35)',
        }}
      >
        <div className="relative shrink-0" style={{ height: 118 }}>
          <button type="button" aria-label="Close App Centre" onClick={close} className="absolute flex h-[52px] w-[52px] items-center justify-center rounded-full outline-none focus-visible:ring-2 focus-visible:ring-[#4a74ff]" style={{ left: 42, top: 34, background: t.seg }}>
            <Ic.Close size={26} />
          </button>
          <div className="absolute flex h-[52px] items-center rounded-full p-[3px]" style={{ left: '50%', top: 34, transform: 'translateX(-50%)', width: 510, background: t.seg }} role="tablist">
            {(['apps', 'super'] as const).map((k) => (
              <button
                key={k}
                role="tab"
                aria-selected={tab === k}
                type="button"
                onClick={() => setTab(k)}
                className="h-full flex-1 rounded-full text-[19px] outline-none"
                style={{ background: tab === k ? t.segOn : 'transparent', color: tab === k ? t.tileOnText : t.text2, boxShadow: tab === k ? '0 2px 8px rgba(0,0,0,0.12)' : 'none' }}
              >
                {k === 'apps' ? 'App Centre' : 'Super Desktop'}
              </button>
            ))}
          </div>
        </div>

        {tab === 'apps' ? (
          <div className="relative flex min-h-0 flex-1">
            <nav className="flex w-[62px] shrink-0 flex-col items-center justify-between pb-8 pt-1 text-[15px]" aria-hidden style={{ color: t.text2 }}>
              {INDEX.map((l, i) => (
                <span key={l} style={{ color: i === 0 ? t.blue : undefined }}>{l}</span>
              ))}
            </nav>
            <div className="min-w-0 flex-1 overflow-y-auto pb-8 pr-[44px]" style={{ scrollbarWidth: 'none' }}>
              {t.tone === 'dark' && <div className="mb-3 text-[17px]" style={{ color: t.text2 }}>Frequent apps</div>}
              {t.tone === 'dark' && grid(FREQUENT.map((id) => APPS.find((a) => a.id === id)!))}
              {t.tone === 'dark' && <div className="mb-3 mt-6 text-[17px]" style={{ color: t.text2 }}>All apps</div>}
              {grid(APPS)}
            </div>
          </div>
        ) : (
          <div className="flex flex-1 flex-col items-center justify-center gap-4 pb-12 text-center">
            <Ic.MenuLink size={58} style={{ color: t.text2 }} />
            <div className="text-[24px] font-medium">Super Desktop</div>
            <div className="max-w-[420px] text-[16px]" style={{ color: t.text2 }}>
              Pair a phone and its apps run on this screen, with the phone in your pocket. Not part of the showroom demo.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
