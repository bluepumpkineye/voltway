import type { Beat } from './drive-beats';

/**
 * The Drive tab's card plan, published by the cards (showroom/DriveMotion.tsx) for the viewer's X-ray lens (viewer/XrayDirector.tsx)
 * to follow: one plan, so the reveal of the car's hardware and the card that is about it never disagree. Empty when no run is up.
 * No React and no three.js; the lens itself is a pure function of this and the playhead (`lensAt`, drive-beats.ts).
 */
export const driveLensPlan: { plan: Beat[] } = { plan: [] };
