import { create } from 'zustand';

/**
 * What the showroom's loading card is waiting for besides the network (the card also follows the loaders' own progress,
 * viewer/ViewerLoading.tsx): a change the visitor asked for, until the scene has settled.
 *
 * Changing the tab or the scene mounts a new set of objects and compiles their shaders the first time they are drawn, which on
 * a modest graphics chip blocks the page for a second or more. The card is meant to be on screen for that, so the change is
 * applied only after the card has been painted (`runWithCard`), and the card goes once the frames are coming steadily again
 * (viewer/ViewerLoading.tsx, SwitchSettle).
 */
export interface Switching {
  label: string;
  /** a later request replaces an earlier one: only its own token may end it */
  token: number;
  /** the change has been made (the frames that follow are the ones that are counted) */
  applied: boolean;
}

interface LoadingUi {
  switching: Switching | null;
  /**
   * The car is not yet drawn steadily: from the page opening until the first frames come without a stall. The car on screen is
   * not enough: its shaders compile on its first frame, which holds the page after the model has arrived.
   */
  booting: boolean;
  begin: (label: string) => number;
  markApplied: (token: number) => void;
  end: (token?: number) => void;
  setBooting: (on: boolean) => void;
}

let next = 0;

export const useLoadingStore = create<LoadingUi>((set, get) => ({
  switching: null,
  booting: true,
  setBooting: (booting) => set((s) => (s.booting === booting ? s : { booting })),
  begin: (label) => {
    const token = ++next;
    set({ switching: { label, token, applied: false } });
    return token;
  },
  markApplied: (token) => {
    const s = get().switching;
    if (s && s.token === token) set({ switching: { ...s, applied: true } });
  },
  end: (token) => {
    const s = get().switching;
    if (s && (token === undefined || s.token === token)) set({ switching: null });
  },
}));

/**
 * Show the card, let the browser paint it, then make the change. The card fades in after a short delay (CSS, so that it keeps
 * running while the page is blocked), and the change that asked for it ends it as soon as it has settled, which for a light
 * change is before the card has appeared at all.
 */
export function runWithCard(label: string, apply: () => void): void {
  const { begin, markApplied, end } = useLoadingStore.getState();
  const token = begin(label);
  let done = false;
  const go = () => {
    if (done) return;
    done = true;
    try {
      apply();
      markApplied(token);
    } catch (e) {
      end(token);
      throw e;
    }
  };
  if (typeof window === 'undefined') return go();
  // after the frame that paints the card; the timer is for a page in the background, which is never given its frame
  window.requestAnimationFrame(() => window.setTimeout(go, 0));
  window.setTimeout(go, 150);
}
