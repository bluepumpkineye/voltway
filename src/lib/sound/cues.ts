/**
 * The noises an opening makes as it moves (src/lib/openings.ts emits them, src/lib/sound/engine.ts plays them): `release` when it
 * starts to open (the handle, the latch letting go, the door coming off its seal), `stop` when it reaches the end of its swing,
 * `shut` when it closes and the latch catches.
 */
export type Cue = 'release' | 'stop' | 'shut';

/** which part of the car makes the noise */
export type Part = 'door' | 'hood' | 'tailgate' | 'flap';
