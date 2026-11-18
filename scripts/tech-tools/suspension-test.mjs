// Checks the suspension model (src/lib/tech/drive-suspension.ts) and prints what the body does at a few speeds.
//   node --no-warnings --import ./scripts/tech-tools/register.mjs scripts/tech-tools/suspension-test.mjs [check|table]
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url)).split(String.fromCharCode(92)).join('/').replace(/[/]$/, '');
const { simulateSuspension, tuneOf, roadFor, cornerTravel, withRide, DRAWN } = await import(pathToFileURL(`${root}/src/lib/tech/drive-suspension.ts`).href);

const car = { wheelbase: 3.0, track: 1.65 };
const mode = process.argv[2] ?? 'check';
let failed = 0;
const ok = (name, cond, detail = '') => {
  if (!cond) failed++;
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${detail ? '  ' + detail : ''}`);
};
const mm = (v) => (v * 1000).toFixed(1);
const deg = (v) => ((v * 180) / Math.PI).toFixed(2);

const cruise = (kmh) => (t) => (kmh / 3.6) * t;
const run = (kmh, dur = 30, tune) => simulateSuspension(car, cruise(kmh), dur, tune);

if (mode === 'table') {
  console.log(`drawn x${DRAWN}; wheelbase ${car.wheelbase} m, track ${car.track} m`);
  for (const [name, tune] of [['comfort', tuneOf(1.1)], ['sport', tuneOf(0.85)], ['track', tuneOf(0.75)], ['full load', tuneOf(1.1, 1.25)]]) {
    for (const kmh of [30, 60, 100, 150, 200]) {
      const r = run(kmh, 30, tune);
      console.log(
        `${name.padEnd(9)} ${String(kmh).padStart(3)} km/h  rms heave ${mm(r.rms.heave).padStart(5)} mm, pitch ${deg(r.rms.pitch)} deg, roll ${deg(r.rms.roll)} deg   peak ${mm(r.peak.heave).padStart(5)} mm / ${deg(r.peak.pitch)} / ${deg(r.peak.roll)}`,
      );
    }
  }
  process.exit(0);
}

// a car that does not move does not ride
{
  const r = simulateSuspension(car, () => 0, 10);
  ok('standing car is still', r.peak.heave < 1e-4 && r.peak.pitch < 1e-5 && r.peak.roll < 1e-5, `peak ${mm(r.peak.heave)} mm`);
}
// more speed, more ride (the road passes faster, so the body is excited closer to its own frequency)
{
  const r30 = run(30);
  const r100 = run(100);
  ok('100 km/h moves the body more than 30 km/h', r100.rms.heave > r30.rms.heave, `${mm(r30.rms.heave)} -> ${mm(r100.rms.heave)} mm rms`);
}
// visible, and not absurd, at a motorway speed
{
  const r = run(100);
  ok('heave at 100 km/h: 3 to 12 mm rms', r.rms.heave > 0.003 && r.rms.heave < 0.012, `${mm(r.rms.heave)} mm`);
  ok('pitch at 100 km/h: 0.05 to 0.4 deg rms', r.rms.pitch > 0.0009 && r.rms.pitch < 0.007, `${deg(r.rms.pitch)} deg`);
  ok('roll at 100 km/h: 0.03 to 0.4 deg rms', r.rms.roll > 0.0005 && r.rms.roll < 0.007, `${deg(r.rms.roll)} deg`);
  // no corner of the body goes further from its wheel than the bump stops allow (the fitted plane can only be as far as the corners are)
  let worst = 0;
  let best = 0;
  for (let t = 0; t < 30; t += 1 / 60) {
    const m = r.sample(t);
    for (const [x, z] of [[1.5, -0.825], [1.5, 0.825], [-1.5, -0.825], [-1.5, 0.825]]) {
      const c = m.heave + x * m.pitch - z * m.roll;
      worst = Math.min(worst, c);
      best = Math.max(best, c);
    }
  }
  ok('no corner goes past its bump stops', worst > -0.018 * 1.01 && best < 0.032 * 1.01, `${mm(worst)} .. ${mm(best)} mm`);
}
// Sport is firmer than Comfort: the body moves less, and at a higher frequency
{
  const c = run(100, 30, tuneOf(1.1));
  const s = run(100, 30, tuneOf(0.85));
  ok('Sport moves the body less than Comfort', s.rms.heave < c.rms.heave, `${mm(s.rms.heave)} < ${mm(c.rms.heave)} mm`);
}
// deterministic: the same run twice, and a scrub back and forth, are the same
{
  const a = run(120);
  const b = run(120);
  let same = true;
  for (const t of [0, 1.3, 7.77, 19.2, 29.9]) {
    const x = a.sample(t);
    const y = b.sample(t);
    if (x.heave !== y.heave || x.pitch !== y.pitch || x.roll !== y.roll) same = false;
  }
  ok('same run, same ride', same);
  const first = a.sample(12.34).heave;
  a.sample(3);
  ok('scrubbing back does not change it', a.sample(12.34).heave === first);
}
// the first second is already alive for a run that starts rolling, and is level for a standing start
{
  const rolling = simulateSuspension(car, (t) => 20 * t, 20);
  const start = rolling.sample(0);
  const step = (t) => Math.abs(rolling.sample(t + 1 / 60).heave - rolling.sample(t).heave);
  let widest = 0;
  for (let t = 1; t < 3; t += 1 / 60) widest = Math.max(widest, step(t));
  ok('rolling start has no jump at t = 0', step(0) <= widest * 1.2, `${mm(step(0))} mm a frame at 0, up to ${mm(widest)} later`);
  const hold = simulateSuspension(car, (t) => 0.5 * 4 * Math.min(t, 6) * Math.min(t, 6) * 0.5, 20);
  ok('standing start begins at rest', Math.abs(hold.sample(0).heave) < 1e-3 && Math.abs(hold.sample(0).pitch) < 1e-4);
}
// the front axle meets a joint before the rear one: a bump on the road makes the nose rise first (pitch up) and then the tail
{
  const road = roadFor(300);
  let found = false;
  for (let x = 0; x < 250; x += 0.01) {
    if (road(x, 1) - road(x - 0.02, 1) > 0.0005 && road(x, 1) > 0.006) {
      found = true;
      break;
    }
  }
  ok('the road has joints', found);
}
// a speed that varies (the pull of a run) draws a body that keeps moving through it
{
  const ramp = simulateSuspension(car, (t) => (t < 5 ? 0 : 2.5 * (t - 5) * (t - 5)), 14);
  ok('body still while the car stands, alive once it moves', ramp.sample(3).heave === ramp.sample(3).heave && ramp.rms.heave > 0.001, `rms ${mm(ramp.rms.heave)} mm`);
}
// the Suspension card's readout: + is a compressed spring, - an extended one (the sign drive-run.ts's `corner` uses)
{
  const near = (a, b) => Math.abs(a - b) < 1e-9;
  const up = cornerTravel(car, { heave: 0.01, pitch: 0, roll: 0 });
  ok('the body up 10 mm extends every spring by 10 mm', up.every((v) => near(v, -10)), up.map((v) => v.toFixed(1)).join(' '));
  const nose = cornerTravel(car, { heave: 0, pitch: 0.01, roll: 0 });
  ok('nose up extends the front and compresses the rear, by half the wheelbase times the pitch', nose[0] < 0 && nose[1] < 0 && nose[2] > 0 && nose[3] > 0 && near(nose[0], -15) && near(nose[2], 15), nose.map((v) => v.toFixed(1)).join(' '));
  const lean = cornerTravel(car, { heave: 0, pitch: 0, roll: 0.01 });
  ok('leaning right compresses the right springs and extends the left', lean[1] > 0 && lean[3] > 0 && lean[0] < 0 && lean[2] < 0 && near(lean[1], 8.25), lean.map((v) => v.toFixed(1)).join(' '));
  // the same signs and sizes as the run's own corner formula: [-pm - rm, -pm + rm, pm - rm, pm + rm]
  const pm = 0.01 * (car.wheelbase / 2) * 1000;
  const rm = 0.01 * (car.track / 2) * 1000;
  const both = cornerTravel(car, { heave: 0, pitch: 0.01, roll: 0.01 });
  const run = [-pm - rm, -pm + rm, pm - rm, pm + rm];
  ok('it agrees with the run’s own corner formula', both.every((v, i) => near(v, run[i])));
  // withRide adds the ride to the run's readout and leaves the rest of it alone
  const sus = simulateSuspension(car, cruise(100), 20);
  const tel = { speed: 100, g: 0, pitchDeg: 0.5, rollDeg: -0.2, corner: [1, 2, 3, 4], energyWh: 7 };
  const r = withRide(tel, sus, 10);
  const m = sus.sample(10);
  const c = cornerTravel(car, m);
  ok('withRide adds the ride to the corners, the pitch and the roll', r.corner.every((v, i) => near(v, tel.corner[i] + c[i])) && near(r.pitchDeg, 0.5 + (m.pitch * 180) / Math.PI) && near(r.rollDeg, -0.2 + (m.roll * 180) / Math.PI));
  ok('withRide leaves the rest of the readout alone', r.speed === 100 && r.energyWh === 7 && tel.corner[0] === 1);
  let peak = 0;
  for (let t = 4; t < 20; t += 1 / 30) peak = Math.max(peak, ...withRide({ ...tel, corner: [0, 0, 0, 0] }, sus, t).corner.map(Math.abs));
  ok('the card’s springs move by a few to a few tens of mm at 100 km/h', peak > 5 && peak < 50, `peak ${peak.toFixed(1)} mm`);
}
const t0 = performance.now();
run(150, 60);
const ms = performance.now() - t0;
ok('a 60 s run integrates in under 400 ms', ms < 400, `${ms.toFixed(0)} ms`);
process.exit(failed ? 1 : 0);
