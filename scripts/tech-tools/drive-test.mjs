// Checks the Drive tab's planner (src/lib/tech/drive-run.ts) on stand-in figures and prints a timeline.
//   node --no-warnings --import ./scripts/tech-tools/register.mjs scripts/tech-tools/drive-test.mjs [check|run] [options]
//   check            the regression and invariant tests (exit code 1 on a failure)
//   run <name>       print the timeline of one case: su7 | rx-stop | 7x | g9l | z9 | 06t | seal-roll
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url)).split(String.fromCharCode(92)).join('/').replace(/[/]$/, '');
const { planDrive, driveTimes, pullCurve, pullTrack, roadEnv, V100 } = await import(pathToFileURL(`${root}/src/lib/tech/drive-run.ts`).href);
const { planLaunch } = await import(pathToFileURL(`${root}/src/lib/tech/launch.ts`).href);

const wheelbase = 3.0;
const layout = {
  wheelbase,
  radius: { FL: 0.36, FR: 0.36, RL: 0.36, RR: 0.36 },
  wheels: { FL: { x: wheelbase, y: 0.82 }, FR: { x: wheelbase, y: -0.82 }, RL: { x: 0, y: 0.82 }, RR: { x: 0, y: -0.82 } },
};
const body = { rear: 1.0, front: 3.9, halfWidth: 0.98 };
const start = { x: 0, y: 0, yaw: 0 };
const three = [
  { id: 'f', label: 'Front', axle: 'front', share: 0.25 },
  { id: 'rl', label: 'Rear left', axle: 'rear', side: 'left', share: 0.375 },
  { id: 'rr', label: 'Rear right', axle: 'rear', side: 'right', share: 0.375 },
];
const two = [
  { id: 'f', label: 'Front', axle: 'front', share: 0.4 },
  { id: 'r', label: 'Rear', axle: 'rear', share: 0.6 },
];
const base = (over = {}) => ({
  zeroTo100: 1.98,
  zeroTo200: 6.09,
  zeroTo200Published: true,
  peakKw: 1138,
  peakNm: 1770,
  from: 0,
  to: 100,
  powerFrac: 1,
  squatScale: 1,
  massKg: 2435,
  refMassKg: 2435,
  nominal: true,
  kwhPer100: 18,
  motors: three,
  chassis: { squatDegPerG: 0.9, rollDegPerG: 1.4, cgHeightM: 0.55, staticRear: 0.5, rearSteerMaxDeg: 0, crabDeg: 15 },
  cdA: 0.62,
  finish: 'coast',
  ...over,
});

let failed = 0;
const ok = (name, cond, detail = '') => {
  if (!cond) failed++;
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${detail ? '  ' + detail : ''}`);
};
const near = (a, b, tol) => Math.abs(a - b) <= tol;

function table(run, every = 1) {
  const d = run.launch.drive;
  const T = run.track.duration;
  console.log(`duration ${T.toFixed(1)} s, ${(run.scroll(T)).toFixed(0)} m, lateral ${run.lateral}`);
  console.log('events:', d.events.map((e) => `${e.t.toFixed(2)} ${e.cue}(${e.label})`).join(' | '));
  console.log('marks:', run.launch.marks.map((m) => `${m.speed}@${m.time}${m.published ? '*' : ''}`).join(' '));
  console.log(' t     phase    km/h     g   latG  kW    Nm  rear%  pitch roll  steerF steerR  y(m)  yaw  motors(share)             Wh   regen');
  for (let t = 0; t <= T + 1e-6; t += every) {
    const r = d.telemetry(t);
    const s = run.track.sample(t);
    console.log(
      `${t.toFixed(1).padStart(4)} ${r.phase.padEnd(7)} ${r.speed.toFixed(0).padStart(6)} ${r.g.toFixed(2).padStart(6)} ${r.latG.toFixed(2).padStart(5)} ${r.powerKw.toFixed(0).padStart(5)} ${(r.torqueNm ?? 0).toFixed(0).padStart(5)} ${(r.axleRear * 100).toFixed(0).padStart(4)} ${r.pitchDeg.toFixed(2).padStart(6)} ${r.rollDeg.toFixed(2).padStart(5)} ${r.steerFront.toFixed(1).padStart(6)} ${r.steerRear.toFixed(1).padStart(6)} ${s.y.toFixed(2).padStart(6)} ${((s.yaw * 180) / Math.PI).toFixed(1).padStart(5)}  ${r.motorShare.map((x) => x.toFixed(2)).join('/').padEnd(16)} ${r.energyWh.toFixed(0).padStart(6)} ${r.regenWh.toFixed(0).padStart(5)}`,
    );
  }
  console.log('summary:', JSON.stringify(d.summary, (k, v) => (typeof v === 'number' ? Math.round(v * 100) / 100 : v)));
}

const which = process.argv[2] ?? 'check';
if (which === 'run') {
  const name = process.argv[3] ?? 'su7';
  const cases = {
    su7: base({ to: 200 }),
    'rx-stop': base({ zeroTo100: 3.9, zeroTo200: 12.3, peakKw: 437, peakNm: undefined, motors: two, finish: 'brake', brake100M: 32.4 }),
    '7x': base({ zeroTo100: 2.98, zeroTo200: 9.4, peakKw: 585, motors: two, to: 150, finish: 'cruise', cruiseKmh: 120 }),
    g9l: base({ zeroTo100: 4.45, zeroTo200: 14, peakKw: 430, peakNm: 695, motors: two, chassis: { squatDegPerG: 1.1, rollDegPerG: 1.3, cgHeightM: 0.62, staticRear: 0.5, rearSteerMaxDeg: 15, crabDeg: 15 }, manoeuvres: ['slalom'] }),
    z9: base({ zeroTo100: 3.4, zeroTo200: 10.7, peakKw: 710, peakNm: 1150, chassis: { squatDegPerG: 0.9, rollDegPerG: 1.2, cgHeightM: 0.55, staticRear: 0.5, rearSteerMaxDeg: 10, crabDeg: 15 }, manoeuvres: ['sweep', 'crab'] }),
    '06t': base({ zeroTo100: 3.9, zeroTo200: 12.3, peakKw: 440, peakNm: 645, motors: two, manoeuvres: ['sweep'] }),
    'seal-roll': base({ zeroTo100: 3.8, zeroTo200: 12, peakKw: 390, peakNm: 690, motors: two, from: 80, to: 160, nominal: true }),
  };
  const run = planDrive(layout, body, start, cases[name]);
  table(run, Number(process.argv[4] ?? 1));
  process.exit(0);
}

// 1. the maker's own run reaches its published times
{
  const r = planDrive(layout, body, start, base({ to: 200 }));
  const m = r.launch.marks;
  const m100 = m.find((x) => x.speed === 100);
  const m200 = m.find((x) => x.speed === 200);
  ok('0-100 at the published 1.98 s', near(m100.time, 1.98, 0.03), `got ${m100.time}`);
  ok('0-200 at the published 6.09 s', near(m200.time, 6.09, 0.05), `got ${m200.time}`);
  ok('both marks are the maker\'s own', m100.published && m200.published);
  ok('the summary\'s run time is the 0-200 crossing, not the end of the carry', near(r.launch.drive.summary.runTime, m200.time, 0.02), `${r.launch.drive.summary.runTime} vs ${m200.time}`);
}

// 2. the old launch planner and the new one agree on the pull (they share its model)
{
  const old = planLaunch(layout, body, start, { zeroTo100: 1.98, zeroTo200: 6.09, targetSpeed: 200 });
  const neu = planDrive(layout, body, start, base({ to: 200 }));
  let worst = 0;
  for (let t = 0; t <= 7; t += 0.05) {
    worst = Math.max(worst, Math.abs(old.launch.readout(t).speed - neu.launch.readout(t).speed));
  }
  ok('speed within 1.5 km/h of planLaunch through the pull to 200', worst < 1.5, `worst ${worst.toFixed(2)} km/h`);
}

// 3. mode and load slow the car, in the right order
{
  const time = (powerFrac, mass) => {
    const { t100 } = driveTimes(1.98, 6.09, powerFrac, mass / 2435);
    return t100;
  };
  const full = time(1, 2435);
  ok('eco is slower than sport', time(0.6, 2435) > full);
  ok('a full cabin is slower than the driver alone', time(1, 2900) > full);
  ok('a full cabin costs less than 0.4 s here', time(1, 2900) - full < 0.4, `${(time(1, 2900) - full).toFixed(2)} s`);
  const r = planDrive(layout, body, start, base({ powerFrac: 0.6, nominal: false }));
  const m100 = r.launch.marks.find((x) => x.speed === 100);
  ok('the planner follows driveTimes in eco', near(m100.time, time(0.6, 2435), 0.04), `got ${m100.time}, want ${time(0.6, 2435).toFixed(2)}`);
  ok('a changed mode is no longer the maker\'s figure', !m100.published);
}

// 4. a rolling pull's time comes from the same curve
{
  const r = planDrive(layout, body, start, base({ zeroTo100: 3.8, zeroTo200: 12, from: 80, to: 160, nominal: true }));
  const m = r.launch.marks.find((x) => x.speed === 160);
  const c = pullCurve(3.8, 12, 80, 160);
  ok('80-160 matches pullCurve', near(m.time, c.time, 0.05), `${m.time} vs ${c.time.toFixed(2)}`);
  ok('a rolling pull is ours, not the maker\'s', !m.published);
  ok('80-160 takes longer than 80-100 and less than 0-160', m.time > 1 && m.time < 12);
}

// 5. the stop is calibrated to the published distance and the brake blend is sensible
{
  const r = planDrive(layout, body, start, base({ zeroTo100: 3.9, zeroTo200: 12.3, peakKw: 437, motors: two, finish: 'brake', brake100M: 32.4 }));
  const s = r.launch.drive.summary;
  ok('the stop starts from 100 km/h', near(s.brakeFromKmh, 100, 0.6), `from ${s.brakeFromKmh?.toFixed(1)} km/h`);
  ok('100-0 in the published 32.4 m', near(s.brakeM, 32.4, 1), `got ${s.brakeM?.toFixed(1)} m`);
  ok('the stop takes 2 to 4 s', s.brakeS > 2 && s.brakeS < 4, `${s.brakeS?.toFixed(2)} s`);
  ok('the car ends at rest', r.launch.readout(r.track.duration).speed < 0.5);
  ok('the motors recover some energy', s.regenWh > 5, `${s.regenWh.toFixed(0)} Wh`);
  let peakRegen = 0;
  let minPitch = 0;
  for (let t = 0; t <= r.track.duration; t += 0.05) {
    const x = r.launch.drive.telemetry(t);
    if (x.phase === 'brake' && x.g < -0.9) peakRegen = Math.max(peakRegen, x.regenFrac);
    minPitch = Math.min(minPitch, x.pitchDeg);
  }
  ok('the friction brakes do most of a hard stop', peakRegen > 0.05 && peakRegen < 0.5, `regen at most ${(peakRegen * 100).toFixed(0)} % at full braking`);
  ok('the nose dips', minPitch < -0.8, `${minPitch.toFixed(2)} deg`);
}

// 6. energy is plausible: a 0-100 pull on a 1138 kW car at 18 kWh/100 km
{
  const r = planDrive(layout, body, start, base({}));
  const s = r.launch.drive.summary;
  ok('peak power is the variant\'s, not beyond it', s.peakKw <= 1138 + 1 && s.peakKw > 700, `${s.peakKw.toFixed(0)} kW`);
  ok('a 0-100 pull uses between 0.1 and 0.6 kWh', s.energyWh > 100 && s.energyWh < 600, `${s.energyWh.toFixed(0)} Wh`);
  ok('peak acceleration is about 1.4 g', near(s.peakG, 1.45, 0.2), `${s.peakG.toFixed(2)} g`);
}

// 7. the manoeuvres
{
  const z9 = planDrive(layout, body, start, base({ zeroTo100: 3.4, zeroTo200: 10.7, peakKw: 710, chassis: { squatDegPerG: 0.9, rollDegPerG: 1.2, cgHeightM: 0.55, staticRear: 0.5, rearSteerMaxDeg: 10, crabDeg: 15 }, manoeuvres: ['sweep', 'crab'] }));
  const s = z9.launch.drive.summary;
  ok('a manoeuvre run moves the car sideways', z9.lateral);
  ok('the sweep leans the body a degree or so', s.peakRollDeg > 0.3 && s.peakRollDeg < 3, `${s.peakRollDeg.toFixed(2)} deg`);
  ok('the sweep stays under 0.5 g', s.peakLatG > 0.1 && s.peakLatG < 0.5, `${s.peakLatG.toFixed(2)} g`);
  ok('the rear wheels stay within their 10 degrees', s.maxRearDeg <= 10.2, `${s.maxRearDeg.toFixed(1)} deg`);
  const ev = z9.launch.drive.events.map((e) => e.cue);
  ok('the events come in order: launch, sweep, crab, stop', ['launch', 'sweep', 'crab', 'stop'].every((c, i, a) => ev.includes(c) && (i === 0 || ev.indexOf(c) > ev.indexOf(a[i - 1]))), ev.join(' '));
  let maxY = 0;
  let endY = 0;
  for (let t = 0; t <= z9.track.duration; t += 0.05) {
    const y = z9.track.sample(t).y;
    maxY = Math.max(maxY, Math.abs(y));
    endY = y;
  }
  ok('the crab ends 1.8 m to the left', near(endY, 1.8, 0.05), `${endY.toFixed(2)} m`);
  ok('the car stays on the 7.6 m road', maxY + 0.98 < 3.8, `${(maxY + 0.98).toFixed(2)} m`);
  let vecMax = 0;
  for (let t = 0; t <= z9.track.duration; t += 0.05) {
    const x = z9.launch.drive.telemetry(t);
    vecMax = Math.max(vecMax, Math.abs(x.motorShare[1] - x.motorShare[2]));
  }
  ok('the rear motors differ by more than 10 points in the S-curve', vecMax > 0.05, `${(vecMax * 100).toFixed(0)} points`);

  const g9 = planDrive(layout, body, start, base({ zeroTo100: 4.45, zeroTo200: 14, peakKw: 430, motors: two, chassis: { squatDegPerG: 1.1, rollDegPerG: 1.3, cgHeightM: 0.62, staticRear: 0.5, rearSteerMaxDeg: 15, crabDeg: 15 }, manoeuvres: ['slalom'] }));
  const g = g9.launch.drive.summary;
  ok('the slalom turns the rear wheels against the front', g.maxRearDeg > 3 && g.maxRearDeg <= 15.2, `${g.maxRearDeg.toFixed(1)} deg`);
  let helped = 0;
  for (let t = 0; t <= g9.track.duration; t += 0.05) {
    const x = g9.launch.drive.telemetry(t);
    if (Math.abs(x.frontOnly) > 3) helped = Math.max(helped, Math.abs(x.frontOnly) - Math.abs(x.steerFront));
  }
  ok('the front wheels turn less than they would alone', helped > 2, `${helped.toFixed(1)} deg less`);

  const none = planDrive(layout, body, start, base({ zeroTo100: 3.9, zeroTo200: 12.3, peakKw: 440, motors: two, manoeuvres: ['sweep'], to: 200 }));
  ok('a 0-200 run skips the manoeuvres', !none.lateral);
}

// 8. a wheel's angle follows the one rule: Ackermann at the front, straight at the back (no rear steering)
{
  const r = planDrive(layout, body, start, base({ manoeuvres: ['sweep'] }));
  let worst = 0;
  for (let t = 0; t <= r.track.duration; t += 0.05) {
    const [fl, fr, rl, rr] = r.track.sample(t).steer;
    worst = Math.max(worst, Math.abs(rl), Math.abs(rr));
    if (Math.abs(fl) > 0.01 && Math.sign(fl) !== Math.sign(fr)) ok('the front wheels turn the same way', false);
  }
  ok('no rear steering on a car without it', worst < 0.02, `${((worst * 180) / Math.PI).toFixed(2)} deg`);
}

// 9. the cruise settles on its speed
{
  const r = planDrive(layout, body, start, base({ zeroTo100: 2.98, zeroTo200: 9.4, peakKw: 585, motors: two, to: 150, finish: 'cruise', cruiseKmh: 120 }));
  const end = r.launch.readout(r.track.duration).speed;
  ok('the 7X-style run ends cruising at 120 km/h', near(end, 120, 1.5), `${end.toFixed(1)} km/h`);
  ok('it passed 150 km/h on the way', r.launch.drive.summary.topKmh > 149);
}


// 10. a wet road and a hill
{
  const t100 = (over) => planDrive(layout, body, start, base(over)).launch.marks.find((x) => x.speed === 100).time;
  const flat = t100({});
  const wet = t100({ env: { wet: true, gradePct: 0 } });
  const up = t100({ env: { wet: false, gradePct: 6 } });
  const down = t100({ env: { wet: false, gradePct: -6 } });
  ok('a wet road slows an all-wheel-drive car that was grip-limited', wet > flat + 1, `${flat} -> ${wet} s`);
  ok('wet 0-100 is about what 0.72 g gives (3.9 to 4.4 s)', wet > 3.9 && wet < 4.6, `${wet} s`);
  ok('uphill is slower than level and downhill is quicker', up > flat && down < flat, `${down} < ${flat} < ${up}`);
  ok('a 6 % hill costs a 1.98 s car less than 0.2 s', up - flat < 0.2, `${(up - flat).toFixed(2)} s`);
  const stop = (over) => planDrive(layout, body, start, base({ finish: 'brake', brake100M: 34, ...over })).launch.drive.summary;
  const dry = stop({});
  const wetStop = stop({ env: { wet: true, gradePct: 0 } });
  const upStop = stop({ env: { wet: false, gradePct: 6 } });
  const downStop = stop({ env: { wet: false, gradePct: -6 } });
  ok('the dry stop is the published 34 m', near(dry.brakeM, 34, 1), `${dry.brakeM?.toFixed(1)} m`);
  ok('the wet stop is much longer (50 to 62 m)', wetStop.brakeM > 50 && wetStop.brakeM < 62, `${wetStop.brakeM?.toFixed(1)} m`);
  ok('uphill the stop is shorter, downhill longer', upStop.brakeM < dry.brakeM && downStop.brakeM > dry.brakeM, `${upStop.brakeM?.toFixed(1)} < ${dry.brakeM?.toFixed(1)} < ${downStop.brakeM?.toFixed(1)}`);
  ok('a 6 % climb draws more energy than the level', planDrive(layout, body, start, base({ env: { wet: false, gradePct: 6 } })).launch.drive.summary.energyWh > planDrive(layout, body, start, base({})).launch.drive.summary.energyWh);
  const e = roadEnv(true, false, 0);
  ok('a rear-driven car holds less on a wet road', e.cap < roadEnv(true, true, 0).cap, `${e.cap.toFixed(2)} vs ${roadEnv(true, true, 0).cap.toFixed(2)} m/s2`);
}

// 11. the rival's track
{
  const track = pullTrack(3.8, 12, 0, 100);
  ok('the rival has not moved before the line', track(0.3) === 0);
  let worst = 0;
  const c = pullCurve(3.8, 12, 0, 100);
  for (let t = 0.7; t < 4; t += 0.1) {
    const dt = 0.01;
    const v = ((track(t + dt) - track(t - dt)) / (2 * dt)) * 3.6;
    // its speed is the curve's
    const k = Math.min(c.v.length - 1, Math.round((t - 0.6) / c.dt));
    worst = Math.max(worst, Math.abs(v - c.v[k]));
  }
  ok('its speed follows the pull curve', worst < 3, `worst ${worst.toFixed(2)} km/h`);
  ok('it holds the speed it reached', near((track(12) - track(11)) * 3.6, 100, 1.5), `${((track(12) - track(11)) * 3.6).toFixed(1)} km/h`);
  const own = planDrive(layout, body, start, base({ zeroTo100: 1.98, zeroTo200: 6.09 })).scroll;
  ok('the quicker car is ahead of it at 5 s', own(5) > track(5), `${own(5).toFixed(1)} m against ${track(5).toFixed(1)} m`);
}

console.log(failed ? `\n${failed} FAILED` : '\nall passed');
process.exit(failed ? 1 : 0);
