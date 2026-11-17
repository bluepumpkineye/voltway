// Checks the Drive tab's camera shake (src/lib/tech/drive-shake.ts).
//   node --no-warnings --import ./scripts/tech-tools/register.mjs scripts/tech-tools/shake-test.mjs
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url)).split(String.fromCharCode(92)).join('/').replace(/[/]$/, '');
const { SHAKE, shakeAmount, shakeAt, shakeLeave, firstMove } = await import(pathToFileURL(`${root}/src/lib/tech/drive-shake.ts`).href);

let failed = 0;
const ok = (name, cond, detail = '') => {
  if (!cond) failed++;
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${detail ? '  ' + detail : ''}`);
};
const deg = (r) => ((r * 180) / Math.PI).toFixed(2);

// the car moves first, then the camera shakes
ok('no shake before the delay', shakeAmount(0.5 + SHAKE.delayS - 0.01, 0.5, 120) === 0);
ok('the shake comes in smoothly', shakeAmount(0.5 + SHAKE.delayS + SHAKE.rampS / 2, 0.5, 120) > 0.4 && shakeAmount(0.5 + SHAKE.delayS + SHAKE.rampS / 2, 0.5, 120) < 0.6);
ok('full size after the ramp at speed', shakeAmount(20, 0.5, 120) === 1);
ok('no shake at a standstill however late', shakeAmount(20, 0.5, 0) === 0 && shakeAmount(20, 0.5, SHAKE.noneKmh) === 0);
ok('more speed, more shake', shakeAmount(20, 0, 30) < shakeAmount(20, 0, 50) && shakeAmount(20, 0, 50) < shakeAmount(20, 0, 80));

// the noise: Blender's strengths are peak to peak, so the angles stay within half of them either way
let tiltMax = 0;
let panMax = 0;
let tiltSq = 0;
let panSq = 0;
let n = 0;
for (let t = 0; t < 600; t += 1 / 60) {
  const s = shakeAt(t, 1);
  tiltMax = Math.max(tiltMax, Math.abs(s.tilt));
  panMax = Math.max(panMax, Math.abs(s.pan));
  tiltSq += s.tilt * s.tilt;
  panSq += s.pan * s.pan;
  n++;
}
const tiltCap = (SHAKE.tilt / 2) * SHAKE.gain;
const panCap = (SHAKE.pan / 2) * SHAKE.gain;
ok('tilt never past half its strength, at the gain', tiltMax <= tiltCap + 1e-9, `${deg(tiltMax)} deg of ${deg(tiltCap)}`);
ok('pan never past half its strength, at the gain', panMax <= panCap + 1e-9, `${deg(panMax)} deg of ${deg(panCap)}`);
ok('it reaches most of that', tiltMax > SHAKE.tilt * SHAKE.gain * 0.3 && panMax > SHAKE.pan * SHAKE.gain * 0.3);
ok('subtle: the pan stays under a degree, the tilt under a third', panMax < (1 * Math.PI) / 180 && tiltMax < (0.34 * Math.PI) / 180);
console.log(`      rms tilt ${deg(Math.sqrt(tiltSq / n))} deg, rms pan ${deg(Math.sqrt(panSq / n))} deg`);
ok('the pan is the bigger, in Blender’s ratio', Math.sqrt(panSq / n) / Math.sqrt(tiltSq / n) > 2 && Math.sqrt(panSq / n) / Math.sqrt(tiltSq / n) < 3.4);

// the two axes do not move together
{
  let sum = 0;
  let a = 0;
  let b = 0;
  for (let t = 0; t < 300; t += 1 / 30) {
    const s = shakeAt(t, 1);
    sum += s.tilt * s.pan;
    a += s.tilt * s.tilt;
    b += s.pan * s.pan;
  }
  const r = sum / Math.sqrt(a * b);
  ok('tilt and pan are not in step', Math.abs(r) < 0.35, `correlation ${r.toFixed(2)}`);
}

// smooth: no jump between frames
{
  let worst = 0;
  let sq = 0;
  let m = 0;
  for (let t = 0; t < 120; t += 1 / 60) {
    const step = Math.abs(shakeAt(t + 1 / 60, 1).pan - shakeAt(t, 1).pan);
    worst = Math.max(worst, step);
    sq += step * step;
    m++;
  }
  console.log(`      pan step at 60 fps: rms ${deg(Math.sqrt(sq / m))} deg, at most ${deg(worst)} deg`);
  ok('no jump between frames: a frame never moves more than 6 % of the pan’s full swing', worst < SHAKE.pan * SHAKE.gain * 0.06);
}

// the shake goes with the car: all of it near, none once it is lost in the haze
ok('all of it while the car is near', shakeLeave(0) === 1 && shakeLeave(SHAKE.leaveFromM) === 1);
ok('none once the car has gone', shakeLeave(SHAKE.leaveToM) === 0 && shakeLeave(150) === 0);
ok('it fades smoothly and never back up', [0, 20, 30, 40, 50, 60, 70, 80].every((x, i, a) => i === 0 || shakeLeave(x) <= shakeLeave(a[i - 1])));

// deterministic: a scrub back gives the same value
ok('same time, same shake', shakeAt(12.34, 0.7).pan === shakeAt(12.34, 0.7).pan && shakeAt(12.34, 0.7).tilt === shakeAt(12.34, 0.7).tilt);

// the first move
ok('a standing start moves at its first metre', Math.abs(firstMove((t) => (t < 2 ? 0 : 3 * (t - 2) * (t - 2)), 20) - 2.2) < 0.15);
ok('a run that begins at speed moves at once', firstMove((t) => 25 * t, 20) < 0.1);
ok('a run that never moves says so', firstMove(() => 0, 12) === 12);

process.exit(failed ? 1 : 0);
