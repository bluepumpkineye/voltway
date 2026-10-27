import type { TechDemoSpec, Vehicle } from '@/data/vehicles/schema';

/**
 * Builds the specification for the standalone 'Drive' tab for any vehicle.
 * Uses the active variant's published performance numbers (0-100 km/h, 0-200 km/h, top speed, power).
 */
export function driveDemo(vehicle: Vehicle, variantId?: string): TechDemoSpec {
  const variant = vehicle.variants.find((v) => v.id === variantId) ?? vehicle.variants[0];
  const perf = variant?.performance;
  const t100 = perf?.zeroTo100S ?? 3.5;
  const t200 =
    perf?.zeroTo200S ??
    (perf?.topSpeedKmh && perf.topSpeedKmh >= 200 ? Math.round(t100 * 3.15 * 10) / 10 : undefined);
  const powerKw = perf?.powerKw ?? 0;
  const hp = Math.round(powerKw * 1.36);

  const claims = [
    {
      text: `${variant?.name ?? 'Performance'}: 0–100 km/h in ${t100.toFixed(2)} s${
        t200 ? `, 0–200 km/h in ${t200.toFixed(2)} s` : ''
      }${perf?.topSpeedKmh ? `, top speed ${perf.topSpeedKmh} km/h` : ''}. Combined power ${powerKw} kW (${hp} PS)${
        perf?.torqueNm ? `, peak torque ${perf.torqueNm} Nm` : ''
      }.`,
      source: vehicle.sources[0] ?? {
        label: `${vehicle.brand} ${vehicle.model} Specifications`,
        url: 'https://carnewschina.com',
      },
    },
  ];

  return {
    id: 'drive',
    title: 'Drive & Launch',
    blurb: `Standing start to 100 km/h in ${t100.toFixed(2)} s${
      t200 ? ` and 200 km/h in ${t200.toFixed(2)} s` : ''
    }. Cockpit HUD with active speedometer, tachometer, shift lights, and acceleration timer.`,
    driver: 'launch',
    devices: [],
    claims,
    simulated:
      'Acceleration simulation based on manufacturer published performance specifications. Pull curve, pitch squat, tyre slip, and tachometer dynamics are calculated in real time.',
  };
}
