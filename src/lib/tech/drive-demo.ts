import type { TechClaim, TechDemoSpec, Vehicle } from '@/data/vehicles/schema';
import { timesOf } from './drive-setup';

/**
 * Builds the specification for the standalone 'Drive' tab for any vehicle (docs/tech-showcase.md section 19).
 * The title, the facts and the note on what is simulated are the car's own scenario's (`Vehicle.drive`) where it has one;
 * the figures are the active variant's published performance (0-100 km/h, 0-200 km/h, top speed, power).
 */
export function driveDemo(vehicle: Vehicle, variantId?: string): TechDemoSpec {
  const variant = vehicle.variants.find((v) => v.id === variantId) ?? vehicle.variants[0];
  const perf = variant?.performance;
  const { t100, t200, published200 } = timesOf(variant);
  const powerKw = perf?.powerKw ?? 0;
  const hp = Math.round(powerKw * 1.36);
  const spec = vehicle.drive;

  const figures: TechClaim = {
    text: `${variant?.name ?? 'Performance'}: 0–100 km/h in ${t100.toFixed(2)} s${
      t200 && published200 ? `, 0–200 km/h in ${t200.toFixed(2)} s` : ''
    }${perf?.topSpeedKmh ? `, top speed ${perf.topSpeedKmh} km/h` : ''}. Combined power ${powerKw} kW (${hp} PS)${
      perf?.torqueNm ? `, peak torque ${perf.torqueNm} Nm` : ''
    }.`,
    source: vehicle.sources[0] ?? {
      label: `${vehicle.brand} ${vehicle.model} Specifications`,
      url: 'https://carnewschina.com',
    },
  };

  return {
    id: 'drive',
    title: spec?.title ?? 'Drive & Launch',
    blurb:
      spec?.blurb ??
      `Standing start to 100 km/h in ${t100.toFixed(2)} s${
        t200 ? ` and 200 km/h in ${t200.toFixed(2)} s` : ''
      }. Cockpit HUD with active speedometer, tachometer, shift lights, and acceleration timer.`,
    driver: 'drive',
    devices: [],
    claims: [figures, ...(spec?.claims ?? [])],
    simulated:
      (spec?.simulated ? `${spec.simulated} ` : '') +
      'The pull is built from the published performance figures; its shape, the body’s pitch and roll, tyre slip, how the motors share the drive, the brake blend and the energy are calculated in real time and are ours' +
      (t200 && !published200 ? ', and so is the 0–200 time, estimated from the 0–100' : '') +
      '.',
  };
}
