// Plays every car's own Drive scenario on a stand-in rig built from its published wheelbase and prints the headline numbers.
//   node --no-warnings --import ./scripts/tech-tools/register.mjs scripts/tech-tools/drive-cars.mjs [slug] [run id] [mode id] [load id]
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url)).split(String.fromCharCode(92)).join('/').replace(/[/]$/, '');
const { vehicles, flagshipVariant } = await import(pathToFileURL(`${root}/src/data/vehicles/index.ts`).href);
const { planDrive } = await import(pathToFileURL(`${root}/src/lib/tech/drive-run.ts`).href);
const { driveSetup } = await import(pathToFileURL(`${root}/src/lib/tech/drive-setup.ts`).href);

const [slug, runId, modeId, loadId] = process.argv.slice(2);
for (const v of vehicles) {
  if (slug && v.slug !== slug) continue;
  const wb = v.dimensions.wheelbaseMm / 1000;
  const half = (v.dimensions.widthMm / 1000) * 0.42;
  const layout = {
    wheelbase: wb,
    radius: { FL: 0.37, FR: 0.37, RL: 0.37, RR: 0.37 },
    wheels: { FL: { x: wb, y: half }, FR: { x: wb, y: -half }, RL: { x: 0, y: half }, RR: { x: 0, y: -half } },
  };
  const len = v.dimensions.lengthMm / 1000;
  const body = { rear: 1.0, front: len - 1.0, halfWidth: v.dimensions.widthMm / 2000 };
  // the showroom opens on the flagship trim
  const setup = driveSetup(v, { variantId: flagshipVariant(v).id, runId, modeId, loadId });
  const run = planDrive(layout, body, { x: 0, y: 0, yaw: 0 }, setup.input, { brake: setup.brake });
  const d = run.launch.drive;
  const s = d.summary;
  const f = (x, n = 2) => (x === null || x === undefined ? '-' : Number(x).toFixed(n));
  console.log(`\n${v.slug}  [${setup.spec.title}]${setup.own ? '' : ' (generic)'}`);
  console.log(`  variant ${setup.variant.id}  mode ${setup.mode.id} (${(setup.input.powerFrac * 100).toFixed(0)} %)  load ${setup.load.id} (${setup.massKg} kg)  run ${setup.run.id}  brake ${setup.brake}`);
  console.log(`  chips: ${setup.runs.map((r) => `${r.label} ${r.time}s${r.published ? '*' : ''}`).join(' | ')}`);
  console.log(`  duration ${f(run.track.duration, 1)} s  run ${s.runTime} s  top ${f(s.topKmh, 0)} km/h  peak ${f(s.peakG)} g ${f(s.peakKw, 0)} kW  energy ${f(s.energyWh, 0)} Wh (regen ${f(s.regenWh, 0)}) = ${f(s.rangeKm)} km`);
  console.log(`  motors ${d.motors.map((m) => m.id).join(',')}  brake ${f(s.brakeM, 1)} m from ${f(s.brakeFromKmh, 0)} (${f(s.brakeS)} s)  lat ${f(s.peakLatG)} g  pitch ${f(s.peakPitchDeg)}  roll ${f(s.peakRollDeg)}  rear ${f(s.maxRearDeg, 1)}  front ${f(s.maxFrontDeg, 1)}  minR ${f(s.minRadius, 1)}`);
  console.log(`  events ${d.events.map((e) => `${e.t.toFixed(1)} ${e.cue}`).join(', ')}`);
}
