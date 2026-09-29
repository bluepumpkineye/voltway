/**
 * Xiaomi HyperOS in the car, as the SU7 Ultra shows it.
 *
 * Read off Xiaomi's own screen images (xiaomiev.com/ultra, /smartcabin):
 * near-black ground, flat mid-grey panels, HyperOS blue for a selected
 * segment, green for the battery bar and lamp tell-tales, and the Ultra's
 * yellow only on Ultra things (the mode radar, Track Master). Sizes are in
 * the HMI's 1280 x 800 space (a 3K 16.1" panel at ~0.42 scale).
 */
export const HY = {
  bg: '#0c0d0f',
  panel: '#1b1c1f',
  panel2: '#26272b',
  panel3: '#313236',
  line: 'rgba(255,255,255,0.08)',
  text: 'rgba(255,255,255,0.93)',
  text2: 'rgba(255,255,255,0.58)',
  text3: 'rgba(255,255,255,0.36)',
  blue: '#2c7bff',
  green: '#34c46b',
  yellow: '#f5c518',
  red: '#ff4b4b',
  orange: '#ff8a1f',
} as const;

/** Bar heights: the status bar across the top, the dock along the bottom. */
export const STATUS_H = 44;
export const DOCK_H = 78;
