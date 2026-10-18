'use client';

import React from 'react';

export type NomiMood = 'happy' | 'listening' | 'music' | 'charging' | 'blink' | 'sport';

export interface BanyanContextValue {
  nomiMood: NomiMood;
  setNomiMood: (mood: NomiMood) => void;
  nomiBubble: string | null;
  speakNomi: (text: string, mood?: NomiMood) => void;
  queenSeatLounge: boolean;
  setQueenSeatLounge: (on: boolean) => void;
  fragrance: 'forest' | 'sunlight' | 'ocean' | 'off';
  setFragrance: (f: 'forest' | 'sunlight' | 'ocean' | 'off') => void;
  seatMassage: number; // 0=off, 1=wave, 2=pulse, 3=catwalk
  setSeatMassage: (m: number) => void;
  airQualityIonizer: boolean;
  setAirQualityIonizer: (on: boolean) => void;
  notification: string | null;
  notify: (msg: string) => void;
  brightness: number;
  setBrightness: (b: number) => void;
}

const BanyanContext = React.createContext<BanyanContextValue | null>(null);

export function BanyanProvider({ children }: { children: React.ReactNode }) {
  const [nomiMood, setNomiMood] = React.useState<NomiMood>('happy');
  const [nomiBubble, setNomiBubble] = React.useState<string | null>(null);
  const [queenSeatLounge, setQueenSeatLounge] = React.useState(false);
  const [fragrance, setFragrance] = React.useState<'forest' | 'sunlight' | 'ocean' | 'off'>('forest');
  const [seatMassage, setSeatMassage] = React.useState(0);
  const [airQualityIonizer, setAirQualityIonizer] = React.useState(true);
  const [notification, setNotification] = React.useState<string | null>(null);
  const [brightness, setBrightness] = React.useState(100);

  const bubbleTimer = React.useRef<number | undefined>(undefined);
  const speakNomi = React.useCallback((text: string, mood: NomiMood = 'happy') => {
    setNomiMood(mood);
    setNomiBubble(text);
    if (bubbleTimer.current) window.clearTimeout(bubbleTimer.current);
    bubbleTimer.current = window.setTimeout(() => {
      setNomiBubble(null);
      setNomiMood('happy');
    }, 3800);
  }, []);

  const notifTimer = React.useRef<number | undefined>(undefined);
  const notify = React.useCallback((msg: string) => {
    setNotification(msg);
    if (notifTimer.current) window.clearTimeout(notifTimer.current);
    notifTimer.current = window.setTimeout(() => setNotification(null), 2500);
  }, []);

  return (
    <BanyanContext.Provider
      value={{
        nomiMood,
        setNomiMood,
        nomiBubble,
        speakNomi,
        queenSeatLounge,
        setQueenSeatLounge,
        fragrance,
        setFragrance,
        seatMassage,
        setSeatMassage,
        airQualityIonizer,
        setAirQualityIonizer,
        notification,
        notify,
        brightness,
        setBrightness,
      }}
    >
      {children}
    </BanyanContext.Provider>
  );
}

export function useBanyanLocal(): BanyanContextValue {
  const ctx = React.useContext(BanyanContext);
  if (!ctx) throw new Error('useBanyanLocal must be used within BanyanProvider');
  return ctx;
}
