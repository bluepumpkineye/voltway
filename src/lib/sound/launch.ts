'use client';

import { soundOn, subscribeSound } from './engine';

/** Sound files for launch demos by vehicle slug and target threshold (km/h) */
const LAUNCH_SOUNDS: Record<string, Record<number, string>> = {
  'xiaomi-su7-ultra': {
    100: '/sounds/xiaomi-su7-launch-100.mp3',
    200: '/sounds/xiaomi-su7-launch-200.mp3',
  },
};

export class LaunchAudioController {
  private audio: HTMLAudioElement | null = null;
  private slug: string | null = null;
  private target: number | null = null;
  private unsub: (() => void) | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      this.unsub = subscribeSound(() => {
        if (this.audio) {
          this.audio.muted = !soundOn();
        }
      });
    }
  }

  setVehicleAndTarget(slug: string, target: number) {
    if (this.slug === slug && this.target === target && this.audio) {
      return;
    }
    this.stop();
    this.slug = slug;
    this.target = target;
    const url = LAUNCH_SOUNDS[slug]?.[target];
    if (url && typeof window !== 'undefined') {
      const el = new Audio(url);
      el.preload = 'auto';
      el.muted = !soundOn();
      this.audio = el;
    }
  }

  play(time = 0, speed = 1) {
    if (!this.audio) return;
    this.audio.muted = !soundOn();
    this.audio.playbackRate = speed;
    if (Math.abs(this.audio.currentTime - time) > 0.15) {
      try {
        this.audio.currentTime = time;
      } catch {
        // ignore seek error before metadata loaded
      }
    }
    this.audio.play().catch(() => {
      // autoplay block fallback
    });
  }

  pause() {
    if (this.audio && !this.audio.paused) {
      this.audio.pause();
    }
  }

  seek(time: number) {
    if (!this.audio) return;
    try {
      this.audio.currentTime = time;
    } catch {
      // ignore
    }
  }

  get currentTime(): number {
    return this.audio?.currentTime ?? 0;
  }

  setSpeed(speed: number) {
    if (this.audio) {
      this.audio.playbackRate = speed;
    }
  }

  stop() {
    if (this.audio) {
      this.audio.pause();
      try {
        this.audio.currentTime = 0;
      } catch {
        // ignore
      }
      this.audio = null;
    }
    this.slug = null;
    this.target = null;
  }

  dispose() {
    this.stop();
    if (this.unsub) {
      this.unsub();
      this.unsub = null;
    }
  }
}
