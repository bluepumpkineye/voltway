// Checks the Drive tab's motor sound (src/lib/sound/drive-voice.ts) against every car's own planned run, at 60 frames a second:
// nothing is missing once a run is past 9 s (the old recording ran out there), no value is not-a-number or jumps, the pitch follows
// the speed, and a car that is rolling is heard. `table <slug>` prints one car's mix per second.
//   node --no-warnings --import ./scripts/tech-tools/register.mjs scripts/tech-tools/drive-sound-test.mjs [check | table <slug> [run id]]
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url)).split(String.fromCharCode(92)).join('/').replace(/[/]$/, '');
const { vehicles, flagshipVariant } = await import(pathToFileURL(`${root}/src/data/vehicles/index.ts`).href);
const { planDrive } = await import(pathToFileURL(`${root}/src/lib/tech/drive-run.ts`).href);
const { driveSetup } = await import(pathToFileURL(`${root}/src/lib/tech/drive-setup.ts`).href);
const { driveMix, voiceOf } = await import(pathToFileURL(`${root}/src/lib/sound/drive-voice.ts`).href);

const FPS = 60;
let failed = 0;
const ok = (name, cond, detail = '') => {
  if (!cond) failed++;
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${detail ? '  ' + detail : ''}`);
};

function planOf(v, runId) {
  const wb = v.dimensions.wheelbaseMm / 1000;
  const half = (v.dimensions.widthMm / 1000) * 0.42;
  const layout = {
    wheelbase: wb,
    radius: { FL: 0.37, FR: 0.37, RL: 0.37, RR: 0.37 },
    wheels: { FL: { x: wb, y: half }, FR: { x: wb, y: -half }, RL: { x: 0, y: half }, RR: { x: 0, y: -half } },
  };
  const len = v.dimensions.lengthMm / 1000;
  const body = { rear: 1.0, front: len - 1.0, halfWidth: v.dimensions.widthMm / 2000 };
  const setup = driveSetup(v, { variantId: flagshipVariant(v).id, runId });
  const run = planDrive(layout, body, { x: 0, y: 0, yaw: 0 }, setup.input, { brake: setup.brake });
  return { run, setup };
}

/** the whole run as (t, speed, g, phase, mix) at the frame rate */
function frames(v, run) {
  const voice = voiceOf(v.slug);
  const out = [];
  const T = run.track.duration;
  for (let i = 0; i <= T * FPS; i++) {
    const t = i / FPS;
    const r = run.launch.readout(t);
    out.push({ t, speed: r.speed, g: r.g, phase: r.phase, m: driveMix(voice, r.speed, r.g, r.phase) });
  }
  return out;
}

const which = process.argv[2] ?? 'check';
if (which === 'table') {
  const v = vehicles.find((x) => x.slug === process.argv[3]);
  const { run, setup } = planOf(v, process.argv[4]);
  const f = frames(v, run);
  console.log(`${v.slug} [${setup.run.id}] ${run.track.duration.toFixed(1)} s`);
  console.log('  t   phase    km/h     g   whine  parts   bed   hiss   whRate  whCut');
  for (let t = 0; t <= run.track.duration; t += 1) {
    const x = f[Math.round(t * FPS)];
    console.log(
      `${t.toFixed(0).padStart(4)} ${String(x.phase).padEnd(7)} ${x.speed.toFixed(0).padStart(6)} ${x.g.toFixed(2).padStart(6)} ${x.m.whine.toFixed(2).padStart(6)} ${x.m.parts.toFixed(2).padStart(6)} ${x.m.bed.toFixed(2).padStart(6)} ${x.m.hiss.toFixed(2).padStart(6)} ${x.m.whineRate.toFixed(2).padStart(8)} ${x.m.whineCut.toFixed(0).padStart(7)}`,
    );
  }
  process.exit(0);
}

let runs = 0;
for (const v of vehicles) {
  const first = planOf(v, undefined);
  const ids = first.setup.runs.map((r) => r.id);
  for (const id of ids) {
    const { run, setup } = planOf(v, id);
    const f = frames(v, run);
    const tag = `${v.slug} / ${setup.run.id}`.padEnd(40);
    runs++;
    let bad = 0;
    let maxRate = 0;
    let minRate = 9;
    for (const x of f) {
      for (const [k, val] of Object.entries(x.m)) {
        if (!Number.isFinite(val) || ((k === 'whine' || k === 'bed' || k === 'hiss' || k === 'parts') && val < 0)) bad++;
      }
      maxRate = Math.max(maxRate, x.m.whineRate);
      minRate = Math.min(minRate, x.m.whineRate);
    }
    // the sound's level (the loops are cut to a common level, so the sum of squares is the loudness): present whenever the car rolls
    const level = (m) => Math.sqrt(m.whine ** 2 + m.parts ** 2 + m.bed ** 2 + m.hiss ** 2);
    let dropout = null;
    for (const x of f) {
      if (x.t > 9 && x.speed > 20 && level(x.m) < 0.2) {
        dropout = x;
        break;
      }
    }
    // no frame steps a level by more than a few tenths (the engine eases the rest), and the rate not by more than a few percent
    let stepL = 0;
    let stepR = 0;
    for (let i = 1; i < f.length; i++) {
      stepL = Math.max(stepL, Math.abs(level(f[i].m) - level(f[i - 1].m)));
      stepR = Math.max(stepR, Math.abs(f[i].m.whineRate / f[i - 1].m.whineRate - 1));
    }
    // the pitch follows the speed: fast is higher than slow
    const fast = f.filter((x) => x.speed > 90);
    const slow = f.filter((x) => x.speed > 15 && x.speed < 45);
    const pitchUp = !fast.length || !slow.length || Math.min(...fast.map((x) => x.m.whineRate)) > Math.max(...slow.map((x) => x.m.whineRate));
    // when the run stops the motor is silent
    const stopped = f.filter((x) => x.speed < 0.1);
    const quietStopped = stopped.every((x) => level(x.m) < 0.06);
    const good = bad === 0 && !dropout && stepL < 0.5 && stepR < 0.03 && pitchUp && quietStopped && run.track.duration >= 9;
    ok(
      tag,
      good,
      `${run.track.duration.toFixed(1)} s  rate ${minRate.toFixed(2)}-${maxRate.toFixed(2)}  worst level step ${stepL.toFixed(3)}  rate step ${(stepR * 100).toFixed(2)} %` +
        (dropout ? `  DROPOUT at ${dropout.t.toFixed(1)} s (${dropout.speed.toFixed(0)} km/h, ${dropout.phase})` : '') +
        (bad ? `  ${bad} bad values` : '') +
        (!pitchUp ? '  pitch does not follow speed' : '') +
        (!quietStopped ? '  not silent at a standstill' : ''),
    );
  }
}
console.log(`\n${runs} runs checked`);
if (failed) {
  console.log(`${failed} FAILED`);
  process.exit(1);
}
