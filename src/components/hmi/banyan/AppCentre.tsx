'use client';

import React from 'react';
import type { HmiScreen } from '@/store/vehicle-store';
import { useBanyanLocal } from './shared';

interface AppItem {
  id: string;
  name: string;
  category: string;
  iconBg: string;
  emoji: string;
  targetScreen?: HmiScreen;
}

const APPS: AppItem[] = [
  { id: 'power', name: 'NIO Power · 一键加电', category: 'Energy', iconBg: 'from-[#00C2A8] to-emerald-600', emoji: '⚡', targetScreen: 'charge' },
  { id: 'chassis', name: '4D Intelligent Chassis', category: 'Chassis', iconBg: 'from-blue-600 to-indigo-700', emoji: '🛞', targetScreen: 'chassis' },
  { id: 'queen', name: 'Queen Co-pilot Lounge', category: 'Comfort', iconBg: 'from-amber-500 to-yellow-600', emoji: '👑', targetScreen: 'seats' },
  { id: 'panocinema', name: 'PanoCinema 7.1.4', category: 'Audio', iconBg: 'from-purple-600 to-pink-600', emoji: '🎵', targetScreen: 'media' },
  { id: 'map', name: 'NIO Baidu Navigation', category: 'Travel', iconBg: 'from-sky-500 to-blue-600', emoji: '🗺️', targetScreen: 'nav' },
  { id: 'climate', name: 'Tri-Zone Climate & Fragrance', category: 'Cabin', iconBg: 'from-teal-500 to-emerald-600', emoji: '❄️', targetScreen: 'climate' },
  { id: 'settings', name: 'Vehicle Settings', category: 'System', iconBg: 'from-neutral-600 to-neutral-800', emoji: '⚙️', targetScreen: 'controls' },
  { id: 'niolife', name: 'NIO Life Lifestyle', category: 'Store', iconBg: 'from-red-500 to-rose-600', emoji: '🛍️' },
  { id: 'karaoke', name: 'Thunder KTV Karaoke', category: 'Entertainment', iconBg: 'from-orange-500 to-red-500', emoji: '🎤' },
  { id: 'bilibili', name: 'Bilibili In-Car Video', category: 'Video', iconBg: 'from-sky-400 to-blue-500', emoji: '📺' },
  { id: 'cloudmusic', name: 'NetEase Cloud Music', category: 'Audio', iconBg: 'from-rose-600 to-red-700', emoji: '🎧' },
  { id: 'wechat', name: 'WeChat In-Car Message', category: 'Communication', iconBg: 'from-green-500 to-emerald-600', emoji: '💬' },
];

export function AppCentre({
  onSelectScreen,
  onClose,
}: {
  onSelectScreen: (s: HmiScreen) => void;
  onClose: () => void;
}) {
  const { speakNomi } = useBanyanLocal();

  const handleLaunch = (app: AppItem) => {
    if (app.targetScreen) {
      onSelectScreen(app.targetScreen);
      onClose();
    } else {
      speakNomi(`Launching ${app.name}`);
    }
  };

  return (
    <div className="flex h-full flex-col p-8 select-none overflow-y-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-[26px] font-semibold text-white">Application Centre · 应用中心</h2>
          <span className="text-[13px] text-white/45">Banyan Smart Ecosystem · 蔚来智能生态</span>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-full bg-white/10 px-4 py-2 text-[13px] font-medium text-white hover:bg-white/20 transition-colors"
        >
          ✕ Close
        </button>
      </div>

      <div className="grid grid-cols-4 gap-5">
        {APPS.map((app) => (
          <button
            key={app.id}
            type="button"
            onClick={() => handleLaunch(app)}
            className="group flex flex-col items-center justify-center rounded-3xl bg-white/[0.045] p-5 ring-1 ring-white/[0.08] transition-all hover:bg-white/[0.09] hover:scale-105 active:scale-95 focus:outline-none"
          >
            <div
              className={`flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-tr ${app.iconBg} text-[34px] shadow-lg group-hover:shadow-[0_0_20px_rgba(0,194,168,0.3)] transition-all`}
            >
              {app.emoji}
            </div>
            <span className="mt-3 block text-center text-[15px] font-medium text-white/90 group-hover:text-white truncate w-full">
              {app.name}
            </span>
            <span className="mt-0.5 block text-center text-[11px] text-white/40">
              {app.category}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
