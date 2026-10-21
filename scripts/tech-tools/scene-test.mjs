// Plays an Autonomous Drive scene on a stand-in car and prints its timeline and every road user's closest approach.
//   node --no-warnings --import ./scripts/tech-tools/register.mjs scripts/tech-tools/scene-test.mjs <overtake|debris|city> [seconds between rows]
import { fileURLToPath, pathToFileURL } from 'node:url';
const root = fileURLToPath(new URL('../../', import.meta.url)).split(String.fromCharCode(92)).join('/').replace(/[/]$/, '');
const { simulate } = await import(pathToFileURL(`${root}/src/lib/tech/drive.ts`).href);
const scenes = {
  overtake: (await import(pathToFileURL(`${root}/src/lib/tech/scenes/overtake.ts`).href)).overtakeScene,
  debris: (await import(pathToFileURL(`${root}/src/lib/tech/scenes/debris.ts`).href)).debrisScene,
};
try { scenes.city = (await import(pathToFileURL(`${root}/src/lib/tech/scenes/city.ts`).href)).cityScene; } catch (e) { if (!/ENOENT|Cannot find/.test(String(e))) throw e; }

const which = process.argv[2] ?? 'debris';
const every = Number(process.argv[3] ?? 1);
const layout = { wheelbase: 2.95, radius: { FL: 0.38, FR: 0.38, RL: 0.38, RR: 0.38 } };
const body = { rear: 1.0, front: 3.9, halfWidth: 0.98 };
const start = { x: 0, y: 0, yaw: 0 };
const pool = [
  { slug: 'a', length: 4.9, width: 1.95 },
  { slug: 'b', length: 4.8, width: 1.9 },
  { slug: 'c', length: 5.0, width: 1.98 },
  { slug: 'd', length: 4.7, width: 1.92 },
];
const egoLen = body.front + body.rear;
const mid = (body.front - body.rear) / 2;
const run = simulate(scenes[which], { cars: pool, egoLen, egoWid: 1.96, mid, start }, layout);
const T = run.track.duration;
const tr = run.scenario.traffic;

console.log(`${which}: ${T.toFixed(1)} s, ${tr.length} actors`);
let last = '';
const ev = [];
for (let t = 0; t <= T; t += 0.05) {
  const r = run.scenario.readout(t);
  if (r.state !== last) { ev.push(`${t.toFixed(2)} ${r.state}`); last = r.state; }
}
console.log('states:', ev.join(' | '));
console.log('t     x(m)   v(km/h) y(m)  gap   ind  tracked  brake  message');
for (let t = 0; t <= T + 1e-6; t += every) {
  const r = run.scenario.readout(t);
  const e = run.scenario.ego(t);
  console.log(
    `${t.toFixed(1).padStart(4)} ${e.x.toFixed(0).padStart(6)} ${r.speed.toFixed(0).padStart(6)} ${e.y.toFixed(2).padStart(6)} ${(r.gap === null ? '-' : r.gap.toFixed(0)).padStart(5)} ${String(r.indicator).padStart(4)} ${String(r.tracked).padStart(6)} ${r.braking ? 'BRAKE' : '     '}  ${r.message}`,
  );
}
// the closest each actor comes to the car's body (rectangles, headings ignored): the larger of the gaps along and across
const rows = [];
for (const c of tr) {
  let best = Infinity, at = 0;
  for (let t = 0; t <= T; t += 0.02) {
    const e = run.scenario.ego(t);
    const gx = Math.abs(c.x(t) - e.x) - (c.length + run.scenario.egoLength) / 2;
    const gy = Math.abs(c.y(t) - e.y) - (c.width + 1.96) / 2;
    const s = Math.max(gx, gy);
    if (s < best) { best = s; at = t; }
  }
  rows.push(`${c.id.padEnd(10)} ${c.kind.padEnd(6)} closest ${best.toFixed(2)} m at ${at.toFixed(1)} s`);
}
console.log(rows.join('\n'));
let maxA = 0, minA = 0;
for (let t = 0; t < T; t += 0.02) {
  const a = (run.track.sample(t + 0.05).speed - run.track.sample(t).speed) / 0.05;
  maxA = Math.max(maxA, a); minA = Math.min(minA, a);
}
console.log(`accel range ${minA.toFixed(1)} .. ${maxA.toFixed(1)} m/s^2`);
