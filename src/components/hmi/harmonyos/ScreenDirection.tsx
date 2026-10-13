'use client';

import React from 'react';
import { techClock } from '@/lib/tech/clock';
import { BUTTONS, afterPress, type ButtonId } from '@/lib/tech/swivel';
import { useVehicleStore } from '@/store/vehicle-store';
import * as Ic from './icons';
import { useHa } from './theme';

/**
 * The dialog Settings > Display > Centre screen angle opens (board T3e, tile 4: Autohome's photograph of "中控屏朝向调节"):
 * four buttons for the screen's four ways (centre and pulled back, centre and forward, toward the driver, toward the
 * passenger), the "follow on boarding" switch, and the steering wheel's scroll wheel that sets the angle. The buttons
 * write the shared store, which the motor in the 3D cabin (viewer/ScreenSwivel.tsx) and the Tech tab's demo follow.
 * A press while the demo is playing takes the screen from it (the demo pauses).
 *
 * Not drawn: the row under "follow on boarding", which the photograph cuts off (it is a voice-follow switch, its
 * text unreadable), and the scroll wheel's own steps (nothing in the photographs shows them).
 */
export function ScreenDirectionDialog({ onClose }: { onClose: () => void }) {
  const t = useHa();
  const turn = useVehicleStore((s) => s.screenTurn);
  const slide = useVehicleStore((s) => s.screenSlide);
  const setPose = useVehicleStore((s) => s.setScreenPose);
  const [follow, setFollow] = React.useState(true);

  const press = (id: ButtonId) => {
    techClock.pause();
    const next = afterPress({ turn, slide }, id);
    setPose(next.turn, next.slide);
  };
  // a turn button is lit whatever the slide; a centre button only at its own slide
  const on = (b: (typeof BUTTONS)[number]) => b.turn === turn && (b.slide === null || b.slide === slide);

  return (
    <div className="absolute inset-0 z-40" onClick={onClose}>
      <div className="absolute inset-0" style={{ background: 'rgba(0,0,0,0.32)' }} />
      <div
        role="dialog"
        aria-label="Centre screen direction"
        className="absolute"
        onClick={(e) => e.stopPropagation()}
        style={{ left: 150, top: 96, width: 980, height: 600, borderRadius: 40, background: t.panel, color: t.text, backdropFilter: 'blur(36px) saturate(1.3)', boxShadow: '0 30px 80px rgba(0,0,0,0.38)' }}
      >
        <button type="button" onClick={onClose} aria-label="Close" className="absolute left-[34px] top-[30px] grid h-[52px] w-[52px] place-items-center rounded-full outline-none focus-visible:ring-2 focus-visible:ring-[#4a74ff]" style={{ background: t.seg }}>
          <Ic.Close size={26} />
        </button>
        <h2 className="pt-[38px] text-center text-[28px] font-medium">Centre screen direction</h2>

        <div className="absolute" style={{ left: 54, top: 116, width: 520 }}>
          <div className="mb-[14px] pl-1 text-[20px]" style={{ color: t.text2 }}>Manual</div>
          <div className="grid grid-cols-2 gap-x-[16px] gap-y-[14px]" role="group" aria-label="Manual adjustment">
            {BUTTONS.map((b) => {
              const active = on(b);
              return (
                <button
                  key={b.id}
                  type="button"
                  aria-pressed={active}
                  onClick={() => press(b.id)}
                  className="h-[64px] rounded-full text-[21px] outline-none transition-colors focus-visible:ring-2 focus-visible:ring-[#4a74ff]"
                  style={{ background: active ? t.segOn : t.seg, color: active ? t.tileOnText : t.text }}
                >
                  {b.label}
                </button>
              );
            })}
          </div>

          <div className="mb-[14px] mt-[34px] pl-1 text-[20px]" style={{ color: t.text2 }}>Adaptive</div>
          <button
            type="button"
            role="switch"
            aria-checked={follow}
            onClick={() => setFollow((f) => !f)}
            className="flex w-full items-center gap-[20px] rounded-[22px] px-[24px] py-[18px] text-left outline-none focus-visible:ring-2 focus-visible:ring-[#4a74ff]"
            style={{ background: t.card }}
          >
            <span className="relative inline-block h-[34px] w-[60px] shrink-0 rounded-full transition-colors" style={{ background: follow ? t.blue : t.seg }}>
              <span className="absolute top-[3px] h-[28px] w-[28px] rounded-full bg-white transition-all" style={{ left: follow ? 29 : 3, boxShadow: '0 1px 4px rgba(0,0,0,0.3)' }} />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-[22px] leading-snug">Follow on boarding</span>
              <span className="block text-[15px] leading-snug" style={{ color: t.text3 }}>
                Turns by itself, according to who is in the driver’s and passenger’s seats when they get in
              </span>
            </span>
            <Ic.Info size={26} style={{ color: t.text2 }} />
          </button>
        </div>

        <div className="absolute flex flex-col items-center" style={{ left: 620, top: 130, width: 310 }}>
          <Wheel tone={t.tone} accent={t.blue} />
          <p className="mt-[22px] text-center text-[18px] leading-snug" style={{ color: t.text2 }}>
            Use the right-hand scroll wheel to adjust the screen angle
          </p>
        </div>
      </div>
    </div>
  );
}

/** The dialog's picture: the steering wheel, drawn flat, with the right scroll wheel marked. */
function Wheel({ tone, accent }: { tone: 'dark' | 'light'; accent: string }) {
  const rim = tone === 'dark' ? '#1a1b1f' : '#2b2c31';
  const spoke = tone === 'dark' ? '#cfcac4' : '#d6d2cc';
  return (
    <svg width="290" height="250" viewBox="0 0 290 250" aria-hidden>
      <path d="M38 96 C44 36 96 8 145 8 C194 8 246 36 252 96 L226 104 C218 62 186 38 145 38 C104 38 72 62 64 104 Z" fill={rim} />
      <path d="M38 96 C34 150 60 196 96 214 L110 190 C84 176 64 146 64 104 Z" fill={rim} />
      <path d="M252 96 C256 150 230 196 194 214 L180 190 C206 176 226 146 226 104 Z" fill={rim} />
      <path d="M118 188 L172 188 L164 236 L126 236 Z" fill="#8d8f96" />
      <path d="M52 110 C84 100 112 106 122 118 L116 148 C90 148 66 142 54 132 Z" fill={spoke} />
      <path d="M238 110 C206 100 178 106 168 118 L174 148 C200 148 224 142 236 132 Z" fill={spoke} />
      <circle cx="145" cy="120" r="38" fill={rim} stroke="#7d7f86" strokeWidth="3" />
      <path d="M135 104 L145 96 L155 104 L155 136 L145 144 L135 136 Z" fill="none" stroke="#c8cad0" strokeWidth="3" />
      <circle cx="218" cy="122" r="10" fill="none" stroke={accent} strokeWidth="3" />
      <circle cx="218" cy="122" r="3" fill={accent} />
    </svg>
  );
}
