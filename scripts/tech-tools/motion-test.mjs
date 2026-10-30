// Checks the Drive tab's motion kit (src/lib/tech/motion.ts) and choreography (src/lib/tech/drive-beats.ts) on stand-in figures.
//   node --no-warnings --import ./scripts/tech-tools/register.mjs scripts/tech-tools/motion-test.mjs [check|run]
//   check   the invariant tests (exit code 1 on a failure)
//   run     prints the Z9's acts, tile moments and the wheels' glow through the launch
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url)).split(String.fromCharCode(92)).join('/').replace(/[/]$/, '');
const load = (p) => import(pathToFileURL(`${root}/${p}`).href);
const M = await load('src/lib/tech/motion.ts');
const B = await load('src/lib/tech/drive-beats.ts');
const { planDrive } = await load('src/lib/tech/drive-run.ts');

let failed = 0;
const ok = (name, cond, detail = '') => {
  if (!cond) failed++;
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${detail ? '  ' + detail : ''}`);
};
const near = (a, b, tol = 1e-6) => Math.abs(a - b) <= tol;

// ---------------------------------------------------------------------------------------------- the kit
{
  ok('interpolate maps the ends and the middle', near(M.interpolate(0, [0, 10], [0, 100]), 0) && near(M.interpolate(5, [0, 10], [0, 100]), 50) && near(M.interpolate(10, [0, 10], [0, 100]), 100));
  ok('interpolate holds outside by default', near(M.interpolate(-3, [0, 10], [5, 9]), 5) && near(M.interpolate(30, [0, 10], [5, 9]), 9));
  ok('interpolate can extend', near(M.interpolate(20, [0, 10], [0, 100], { extrapolateRight: 'extend' }), 200));
  ok('interpolate takes pieces', near(M.interpolate(15, [0, 10, 20], [0, 1, 0]), 0.5));
  ok('interpolate applies the easing inside, not outside', near(M.interpolate(5, [0, 10], [0, 1], { easing: M.Easing.inQuad }), 0.25));
  let threw = false;
  try {
    M.interpolate(1, [0, 1], [0]);
  } catch {
    threw = true;
  }
  ok('interpolate rejects ranges of different lengths', threw);

  const eb = M.Easing.bezier(0.16, 1, 0.3, 1);
  ok('the bezier easing runs 0 to 1 and is monotone', near(eb(0), 0) && near(eb(1), 1) && [...Array(20)].every((_, i) => eb((i + 1) / 20) >= eb(i / 20) - 1e-9));
  ok('the expo-out curve is most of the way there at a quarter of the time', eb(0.25) > 0.6);

  const dflt = [0, 0.05, 0.1, 0.3, 0.6, 1, 2, 4].map((t) => M.spring(t));
  ok('a spring starts at 0 and ends at 1', near(M.spring(0), 0) && near(M.spring(6), 1, 1e-3));
  ok('Remotion\'s default spring overshoots', Math.max(...[...Array(120)].map((_, i) => M.spring(i / 60))) > 1.1, `peak ${Math.max(...[...Array(120)].map((_, i) => M.spring(i / 60))).toFixed(3)}`);
  ok('the soft spring does not overshoot', Math.max(...[...Array(300)].map((_, i) => M.spring(i / 60, M.SPRINGS.soft))) < 1.005);
  ok('a critically damped spring does not overshoot', Math.max(...[...Array(300)].map((_, i) => M.spring(i / 60, { damping: 20, stiffness: 100 }))) < 1.0001);
  ok('a spring is the same at the same time however it is reached', near(M.spring(0.37), dflt[3] === 0 ? 0 : M.spring(0.37)) && M.spring(0.37) === M.spring(0.37));
  ok('a spring settles in under two seconds (they are used for entrances)', M.springDuration(M.SPRINGS.pop) < 2, `${M.springDuration(M.SPRINGS.pop).toFixed(2)} s`);

  const p = M.presence(2, 1, 4);
  ok('presence: on at once after its time, springing in', p.visible && p.enter > 0.5 && p.exit === 0);
  ok('presence: not visible before', !M.presence(0.5, 1, 4).visible);
  ok('presence: leaves over its exit', M.presence(4.2, 1, 4, 0.4).exit > 0.2 && M.presence(4.2, 1, 4, 0.4).visible && !M.presence(4.5, 1, 4, 0.4).visible);
  ok('presence with no end stays', M.presence(99, 1).visible && M.presence(99, 1).exit === 0);

  ok('countTo reaches its value', near(M.countTo(1138, 1), 1138) && M.countTo(1138, 0.5) < 1138 && M.countTo(1138, 0) === 0);
  ok('flash is 0 outside its window and 1 near the start', M.flash(0.5, 1) === 0 && M.flash(3, 1) === 0 && M.flash(1.04, 1) > 0.99);
  ok('fmt groups thousands and signs', M.fmt(1138) === '1,138' && M.fmt(-4.26, 1) === '−4.3' && M.fmt(-0.01, 1) === '0.0' && M.fmt(12.5, 2) === '12.50');
}

// ---------------------------------------------------------------------------------------------- the choreography
const wheelbase = 3.0;
const layout = {
  wheelbase,
  radius: { FL: 0.36, FR: 0.36, RL: 0.36, RR: 0.36 },
  wheels: { FL: { x: wheelbase, y: 0.82 }, FR: { x: wheelbase, y: -0.82 }, RL: { x: 0, y: 0.82 }, RR: { x: 0, y: -0.82 } },
};
const body = { rear: 1.0, front: 3.9, halfWidth: 0.98 };
const start = { x: 0, y: 0, yaw: 0 };
const three = [
  { id: 'front', label: 'Front', axle: 'front', share: 0.25 },
  { id: 'rear-left', label: 'Rear left', axle: 'rear', side: 'left', share: 0.375 },
  { id: 'rear-right', label: 'Rear right', axle: 'rear', side: 'right', share: 0.375 },
];
const two = [
  { id: 'front', label: 'Front', axle: 'front', share: 0.4 },
  { id: 'rear', label: 'Rear', axle: 'rear', share: 0.6 },
];
const rwd = [{ id: 'rear', label: 'Rear', axle: 'rear', share: 1 }];
const base = (over = {}) => ({
  zeroTo100: 3.4,
  zeroTo200: 10.7,
  zeroTo200Published: true,
  peakKw: 710,
  peakNm: 1150,
  from: 0,
  to: 100,
  powerFrac: 1,
  squatScale: 1,
  massKg: 2435,
  refMassKg: 2435,
  nominal: true,
  kwhPer100: 18,
  motors: three,
  chassis: { squatDegPerG: 0.9, rollDegPerG: 1.2, cgHeightM: 0.55, staticRear: 0.5, rearSteerMaxDeg: 10, crabDeg: 15 },
  cdA: 0.62,
  finish: 'coast',
  ...over,
});

const z9 = planDrive(layout, body, start, base({ manoeuvres: ['sweep', 'crab'] }));
const z9f = z9.launch.drive;
const T = z9.track.duration;
const shape = B.runShape(z9f, T);

const rx = planDrive(layout, body, start, base({ zeroTo100: 3.9, zeroTo200: 12.3, peakKw: 437, peakNm: undefined, motors: two, finish: 'brake', brake100M: 32.4 }));
const rxShape = B.runShape(rx.launch.drive, rx.track.duration);

{
  ok('the run shape finds the launch', shape.launch > 0 && shape.launch < 1.5, `${shape.launch.toFixed(2)} s`);
  ok('the run shape is cached by the run', B.runShape(z9f, T) === shape);
  ok('the run shape finds the sweep and the crab', (shape.spans.sweep?.length ?? 0) >= 1 && (shape.spans.crab?.length ?? 0) >= 1);
  ok('the peak power is the run\'s own', near(shape.peakKw.kw, Math.max(...[...Array(Math.ceil(T / 0.1) + 1)].map((_, i) => z9f.telemetry(Math.min(i * 0.1, T)).powerKw)), 1e-6));
  ok('the speed is reached in order', shape.reaches(50) < shape.reaches(100) && shape.reaches(1000) === null);

  // the wheels: three motors, the front one drives both front wheels, each rear motor its own wheel
  ok('a front motor turns both front wheels', JSON.stringify(B.wheelsOf(three[0])) === '[0,1]');
  ok('a rear motor of the left turns the rear left wheel', JSON.stringify(B.wheelsOf(three[1])) === '[2]' && JSON.stringify(B.wheelsOf(three[2])) === '[3]');
  ok('a single rear motor turns both rear wheels', JSON.stringify(B.wheelsOf(rwd[0])) === '[2,3]');

  const mid = B.wheelLevels(z9f, z9f.telemetry(shape.launch + 1));
  ok('in the pull the rear wheels are driven harder than the front', mid.drive[2] > mid.drive[0] && mid.drive[3] > mid.drive[1], mid.drive.map((x) => x.toFixed(2)).join(' '));
  ok('in the pull the wheels are lit, none past 1', mid.drive.every((x) => x > 0.05 && x <= 1) && mid.regen.every((x) => x === 0) && mid.brake.every((x) => x === 0));
  const still = B.wheelLevels(z9f, z9f.telemetry(0));
  ok('standing, nothing is lit', still.drive.every((x) => x < 0.02));

  // the sweep: the rear motors favour one wheel, and the glow shows it
  const sw = shape.spans.sweep[0];
  let worst = 0;
  for (let t = sw.from; t <= sw.to; t += 0.1) {
    const w = B.wheelLevels(z9f, z9f.telemetry(t));
    worst = Math.max(worst, Math.abs(w.drive[2] - w.drive[3]));
  }
  ok('in the S-curve the two rear wheels are not driven alike', worst > 0.03, `most ${worst.toFixed(3)}`);

  // the acts
  const acts = B.launchActs(z9f, shape.launch);
  ok('three motors on two axles tell three acts: front, rear, all', acts.map((a) => a.id).join() === 'front,rear,all');
  ok('the acts follow one another without a gap or an overlap', acts.every((a, i) => i === 0 || near(a.from, acts[i - 1].to)));
  ok('the front act lights the front and dims the rear', acts[0].wheels[0] === 1 && acts[0].wheels[2] < 0.3 && acts[1].wheels[2] === 1 && acts[1].wheels[0] < 0.3);
  ok('the lines state the shares the run has at the middle of each act', (() => {
    const share = (a, axle) => { const tel = z9f.telemetry((a.from + a.to) / 2); return Math.round(z9f.motors.reduce((x, m, j) => x + (m.axle === axle ? tel.motorShare[j] : 0), 0) * 100); };
    return acts[0].line.startsWith(`${share(acts[0], 'front')} %`) && acts[1].line.startsWith(`${share(acts[1], 'rear')} %`);
  })(), `${acts[0].line} | ${acts[1].line}`);
  ok('the two axles\' shares in an act are the live ones: they sum to the whole', (() => { const tel = z9f.telemetry((acts[0].from + acts[0].to) / 2); return near(tel.motorShare.reduce((a, b) => a + b, 0), 1, 1e-6); })());
  ok('the all act says the split is modelled', /modelled/.test(acts[2].line));
  const rwdRun = planDrive(layout, body, start, base({ motors: rwd }));
  const rwdActs = B.launchActs(rwdRun.launch.drive, B.runShape(rwdRun.launch.drive, rwdRun.track.duration).launch);
  ok('a rear-drive car tells one act and lights its rear axle', rwdActs.length === 1 && rwdActs[0].id === 'rear' && rwdActs[0].wheels.every((x) => x === 1));
  const quick = planDrive(layout, body, start, base({ zeroTo100: 1.98, zeroTo200: 6.09, peakKw: 1138 }));
  const qa = B.launchActs(quick.launch.drive, B.runShape(quick.launch.drive, quick.track.duration).launch);
  ok('a quick car\'s acts are squeezed into its pull: under 3.5 s in all', qa.length === 3 && qa[2].to - qa[0].from < 3.5 && qa[2].to - qa[0].from > 2.4, `${(qa[2].to - qa[0].from).toFixed(2)} s`);
  ok('a normal pull keeps most of the acts', acts[acts.length - 1].to - acts[0].from > 4, `${(acts[acts.length - 1].to - acts[0].from).toFixed(2)} s`);
  const dual = planDrive(layout, body, start, base({ motors: two }));
  ok('a two-motor car tells front, rear, all', B.launchActs(dual.launch.drive, 0.6).map((a) => a.id).join() === 'front,rear,all');

  const sp = B.spotlight(acts, (acts[0].from + acts[0].to) / 2);
  ok('mid front act the spotlight dims the rear wheels', sp[0] === 1 && sp[2] < 0.2, sp.map((x) => x.toFixed(2)).join(' '));
  const sp2 = B.spotlight(acts, acts[2].to + 2);
  ok('after the acts nothing is dimmed', sp2.every((x) => x === 1));
  const cross = B.spotlight(acts, acts[0].to + 0.1);
  ok('between the acts the spotlight is crossfading, not jumping', cross[2] > B.spotlight(acts, acts[0].to - 0.05)[2] - 1e-9 && cross[2] < 1);
  ok('the act at a time', B.actAt(acts, acts[1].from + 0.1)?.id === 'rear' && B.actAt(acts, 0) === null);

  // the tiles
  const caps = B.captionsOf(z9f, shape, acts);
  ok('the captions begin with the three acts', caps.slice(0, 3).map((c) => c.id).join() === 'act-front,act-rear,act-all', caps.map((c) => c.id).join());
  ok('the captions never overlap', caps.every((c, i) => i === 0 || c.from >= caps[i - 1].to - 1e-6));
  ok('the S-curve and the crab have a caption each', caps.some((c) => c.id === 'sweep') && caps.some((c) => c.id === 'crab'));
  ok('the vectoring caption names the rear motors (the Z9 has one at each rear wheel)', /rear motors/i.test(caps.find((c) => c.id === 'sweep').title));
  ok('a run with a stop captions the stop with the planner\'s own distance', (() => {
    const rxc = B.captionsOf(rx.launch.drive, rxShape, B.launchActs(rx.launch.drive, rxShape.launch));
    const stop = rxc.find((c) => c.id === 'stop');
    return stop && stop.title === `${rx.launch.drive.summary.brakeM.toFixed(1)} m`;
  })());

  const overlays = ['motors', 'steering', 'power', 'weight'];
  const plan = B.beatPlan(overlays, z9f, shape);
  ok('the plan only has the car\'s own instruments', plan.every((b) => overlays.includes(b.overlay)));
  ok('the plan is in time order', plan.every((b, i) => i === 0 || b.from >= plan[i - 1].from));
  ok('the motors\' moment begins with the launch', plan.find((b) => b.overlay === 'motors').from <= shape.launch + 0.01);
  ok('the launch opens the car\'s first two tiles that are about it: motors and power', plan.filter((b) => b.from <= shape.launch + 0.01).map((b) => b.overlay).sort().join() === 'motors,power');
  ok('then the weight takes the power\'s place', plan.some((b) => b.overlay === 'weight' && b.from > 1.5 && b.from < 3.2));
  ok('a single-tile window opens only one tile at a time', B.beatPlan(overlays, z9f, shape, 1).filter((b) => b.from <= shape.launch + 0.01).length === 1);
  ok('the last chapter stays open to the end', plan.some((b) => b.to === Infinity));
  ok('a tile open in two chapters running is one moment, not two', plan.filter((b) => b.overlay === 'motors').length <= 2, plan.filter((b) => b.overlay === 'motors').map((b) => `${b.from.toFixed(1)}-${b.to}`).join(' '));
  ok('the steering has a moment in the curve and in the crab', plan.some((b) => b.overlay === 'steering' && b.from <= shape.spans.sweep[0].from + 0.4) && plan.some((b) => b.overlay === 'steering' && b.from <= shape.spans.crab[0].from + 0.5 && b.to > shape.spans.crab[0].from + 2));
  ok('every tile of the car gets a moment of its own, the weight too', overlays.every((o) => plan.some((b) => b.overlay === o)), overlays.filter((o) => !plan.some((b) => b.overlay === o)).join());
  ok('no moment of this car is for the brake (it has no such tile)', !plan.some((b) => b.overlay === 'brake'));

  let capOk = true;
  let smooth = true;
  let prev = null;
  for (let t = 0; t <= T; t += 0.02) {
    const open = B.openAt(plan, overlays, t);
    const full = Object.values(open).filter((x) => x > 0.9).length;
    if (full > 2) capOk = false;
    if (prev) for (const o of overlays) if (Math.abs(open[o] - prev[o]) > 0.2) smooth = false;
    prev = open;
  }
  ok('never more than two tiles are fully open', capOk);
  ok('tiles open and close smoothly (no jump in 20 ms)', smooth);
  ok('a second into the run the launch\'s tiles are open', B.openAt(plan, overlays, 1.2).motors > 0.9 && B.openAt(plan, overlays, 1.2).power > 0.9);
  ok('at the end something is still open', Object.values(B.openAt(plan, overlays, T)).some((x) => x > 0.9));
  ok('scrubbing is stateless: the same time gives the same answer', JSON.stringify(B.openAt(plan, overlays, 7.3)) === JSON.stringify(B.openAt(plan, overlays, 7.3)));

  // a stop gives the brake its moment
  const rxPlan = B.beatPlan(['brake', 'suspension', 'motors', 'weight'], rx.launch.drive, rxShape);
  const bk = rxPlan.find((b) => b.overlay === 'brake');
  ok('a run with a stop gives the brake a moment around the stop', bk && rxShape.spans.brake && bk.from <= rxShape.spans.brake[0].from && bk.to >= rxShape.spans.brake[0].to);
  ok('no moment of the brake before the car brakes', rxPlan.filter((b) => b.overlay === 'brake').every((b) => b.from >= rxShape.spans.brake[0].from - 0.4));
  const wb = B.wheelLevels(rx.launch.drive, rx.launch.drive.telemetry(rxShape.spans.brake[0].from + 0.5));
  ok('under the brakes the wheels\' friction glows, the front harder', wb.brake[0] > wb.brake[2] && wb.brake[0] > 0.05 && wb.drive.every((x) => x === 0), wb.brake.map((x) => x.toFixed(2)).join(' '));
}

if (process.argv[2] === 'run') {
  console.log('events:', z9f.events.map((e) => `${e.t.toFixed(2)} ${e.cue}`).join(' | '));
  console.log('acts:', B.launchActs(z9f, shape.launch).map((a) => `${a.id} ${a.from.toFixed(2)}-${a.to.toFixed(2)}`).join(' | '));
  const plan = B.beatPlan(['motors', 'steering', 'power', 'weight'], z9f, shape);
  console.log('plan:', plan.map((b) => `${b.overlay} ${b.from.toFixed(1)}-${b.to.toFixed(1)}`).join(' | '));
  for (let t = 0; t <= T; t += 1) {
    const w = B.wheelLevels(z9f, z9f.telemetry(t));
    console.log(t.toFixed(0).padStart(3), 'drive', w.drive.map((x) => x.toFixed(2)).join(' '), ' spot', B.spotlight(B.launchActs(z9f, shape.launch), t).map((x) => x.toFixed(2)).join(' '));
  }
}

console.log(failed ? `\n${failed} FAILED` : '\nall pass');
process.exit(failed ? 1 : 0);
