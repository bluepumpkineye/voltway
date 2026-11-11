/**
 * The weather of the Drive tab's wet road (ours): how far the room has gone toward a rainy, overcast day, 0 to 1, and where it is going.
 * The studio's white room is the sky of the scenes, so the rain dims it the way a dusk does (`duskOf`, Lights.tsx): the walls and the
 * floor go to a soft grey, the image-based light drops, the street lamps come on a little. The level eases, so the weather arrives
 * and clears over a second or so instead of switching.
 */
export const weather = { target: 0, level: 0 };

/** how much of a full dusk a full rain takes the room (the lamps and the room's grey follow it) */
export const RAIN_DIM = 0.42;

/** Steps the level toward its target; true while it is still moving. */
export function stepWeather(dt: number): boolean {
  const d = weather.target - weather.level;
  if (Math.abs(d) < 0.002) {
    weather.level = weather.target;
    return false;
  }
  weather.level += d * (1 - Math.exp(-dt * 2.2));
  return true;
}

// dev only: window.__weather, to read where the rain is (the viewer draws continuously while it is not at rest)
if (typeof window !== 'undefined' && process.env.NODE_ENV !== 'production') {
  (window as unknown as { __weather?: unknown }).__weather = weather;
}
