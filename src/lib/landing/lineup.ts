/**
 * The landing page's line-up: where each car stands in the fan and which picture it is (public/landing/<slug>.webp, rendered by
 * scripts/landing-shots.mjs from the car's own model, from the angle of its place). Positions are fractions of the scene: `x` across
 * (0.5 is the middle), `ground` down the hero (where the tyres meet the water), `k` the picture's width as a fraction of the scene's
 * reference width (CSS --u). The fan is a V: the hero car in front, a row of four behind it in an arc, a row of four behind them. The cars face outward (the left ones have their noses to the left), with room between them, and the hero faces the camera.
 */
export type Row = 'front' | 'mid' | 'back';

export interface Place {
  slug: string;
  row: Row;
  x: number;
  ground: number;
  k: number;
  /** the picture's size in pixels */
  w: number;
  h: number;
}

export const LINEUP: Place[] = [
  // the back row, smallest, on the pale water by the horizon
  { slug: 'avatr-06t', row: 'back', x: 0.205, ground: 0.5, k: 0.14, w: 972, h: 568 },
  { slug: 'byd-seal', row: 'back', x: 0.38, ground: 0.475, k: 0.13, w: 890, h: 632 },
  { slug: 'denza-z9', row: 'back', x: 0.62, ground: 0.475, k: 0.13, w: 905, h: 613 },
  { slug: 'luxeed-rx', row: 'back', x: 0.795, ground: 0.5, k: 0.14, w: 967, h: 570 },
  // the middle row, in an arc, noses outward
  { slug: 'nio-es8', row: 'mid', x: 0.105, ground: 0.725, k: 0.18, w: 1026, h: 562 },
  { slug: 'xpeng-g9l', row: 'mid', x: 0.285, ground: 0.685, k: 0.172, w: 990, h: 606 },
  { slug: 'voyah-passion-s', row: 'mid', x: 0.715, ground: 0.685, k: 0.172, w: 995, h: 564 },
  { slug: 'zeekr-7x', row: 'mid', x: 0.895, ground: 0.725, k: 0.18, w: 1023, h: 555 },
  // the hero, facing the camera
  { slug: 'xiaomi-su7-ultra', row: 'front', x: 0.5, ground: 0.855, k: 0.225, w: 718, h: 671 },
];
