'use client';

import React from 'react';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import type { Vehicle } from '@/data/vehicles/schema';
import { isStageTab, useVehicleStore } from '@/store/vehicle-store';
import { techClock } from '@/lib/tech/clock';
import { chargeDemo } from '@/lib/tech/charging';
import { DRIVERS, visibleDemos } from '@/lib/tech/demos';
import type { PlannedRun } from '@/lib/tech/kinematics';
import { rideLevelsOf, RIDE_SPAN_MM } from '@/lib/tech/ride';
import { rigOf } from '@/lib/tech/rig';
import { techSession } from '@/lib/tech/session';
import { motionOk } from './configurator';

/**
 * Plays the Tech tab's demo: builds the motion for the chosen demo from the
 * car's measured wheels, runs the demo's clock, and writes each frame to the
 * car's rig (src/lib/tech/rig.ts). Mount once inside the Canvas.
 *
 * Like the openings' driver it renders on demand: it asks for a frame only while
 * the clock runs or has just been moved, so an idle showroom still draws nothing.
 *
 * It also publishes the running demo to the devices (src/lib/tech/session.ts) and the
 * lot the car drives in (the store's `techScene`, which TechStage draws).
 */
export function TechDirector({ vehicle }: { vehicle: Vehicle }) {
  const invalidate = useThree((s) => s.invalidate);
  const rig = rigOf(vehicle);
  const rigged = React.useSyncExternalStore(rig.subscribe, () => rig.ready, () => false);
  const tab = useVehicleStore((s) => s.tab);
  const demoId = useVehicleStore((s) => s.techDemoId);
  const parkSpeed = useVehicleStore((s) => s.parkSpeed);
  const carpetOn = useVehicleStore((s) => s.carpetOn);
  const rideLevel = useVehicleStore((s) => s.rideLevel);
  const modeId = useVehicleStore((s) => s.modeId);
  const easyEntry = useVehicleStore((s) => s.easyEntry);
  const beltOn = useVehicleStore((s) => s.beltOn);
  const compassPivot = useVehicleStore((s) => s.compassPivot);
  const compassAngle = useVehicleStore((s) => s.compassAngle);

  const demos = React.useMemo(() => visibleDemos(vehicle), [vehicle]);
  const charging = React.useMemo(() => chargeDemo(vehicle), [vehicle]);
  // the Tech tab plays the demo the visitor picked; the Charging tab plays the car's own charge
  const spec = tab === 'tech' ? (demos.find((d) => d.id === demoId) ?? demos[0]) : tab === 'charging' ? (charging ?? undefined) : undefined;

  const built = React.useMemo(() => {
    const driver = spec ? DRIVERS[spec.driver] : undefined;
    const layout = rig.layout;
    if (!spec || !driver || !rigged || !layout) return null;
    // the published width is the body's: the mirrors fold in to park
    const body = { ...rig.body, halfWidth: vehicle.dimensions.widthMm / 2000 };
    const b = driver.build({
      vehicle,
      layout,
      body,
      start: { x: rig.rac.x, y: rig.rac.y, yaw: 0 },
      speed: parkSpeed,
      ride: { carpet: carpetOn, modeId },
      params: spec.params ?? {},
      chassis: { pivot: compassPivot, angleDeg: compassAngle },
      scenario: spec.scenario,
    });
    return { spec, body, ...b, trailLine: b.trail ? trailOf(b.track) : null };
    // the rig is the same object for the car's life; `rigged` says when its wheels arrive
  }, [spec, rigged, rig, parkSpeed, carpetOn, modeId, vehicle, compassPivot, compassAngle]);

  // a demo starts from the top (or waits for a device to start it), and the camera takes in its floor
  React.useEffect(() => {
    if (!built) return;
    const { track, stage } = built;
    const st = useVehicleStore.getState();
    const soc0 = st.soc;
    const intent = st.techIntent;
    techClock.load(track.duration, { play: intent || (built.autoplay && motionOk()), stops: built.stops });
    if (intent) st.clearTechIntent();

    const { bounds } = stage ?? track.stats;
    const reach = stage ? 1.0 : Math.max(vehicle.dimensions.lengthMm / 1000, 4) * 0.6;
    const cx = (bounds.min.x + bounds.max.x) / 2;
    const cy = (bounds.min.y + bounds.max.y) / 2;
    const framing = built.frame ?? built.treadmill?.frame ?? {
      // the path is in the floor frame, which is the viewer's with y left = -z
      cx,
      cz: -cy,
      radius: Math.hypot(bounds.max.x - bounds.min.x, bounds.max.y - bounds.min.y) / 2 + reach,
      camera: stage?.camera,
    };
    st.setTechStage(framing);
    st.setTechScene(stage);
    st.setTechStreet(built.street?.stage ?? null);
    // a demo whose subject is in the cabin sits the camera in the driver's seat; the swivel screen's opens its
    // direction dialog on the car's screen, with the screen as the car stands
    if (built.spec.view === 'cabin') st.setAnchor('driver');
    if (built.swivel) {
      st.openSettings('display');
      st.setScreenDialog(true);
      st.setScreenPose('centre', 'rear');
    }
    if (built.boost) {
      st.setHmiScreen('home');
      st.setBoost(false, 0);
      st.setBoostPopup(false);
    }
    if (built.charge) {
      st.setHmiScreen('charge');
    }
    poseAt.current = NaN;
    techSession.set({
      demoId: built.spec.id,
      stage,
      sample: (t) => track.sample(t),
      body: built.body,
      road: built.treadmill?.road ?? null,
      ride: built.treadmill?.ride ?? null,
      launch: built.treadmill?.launch ?? null,
      charge: built.charge ?? null,
      sensors: built.sensors ? built.sensors.scenario : null,
      chassis: built.street ? { readout: built.street.readout, facts: built.street.facts, stage: built.street.stage } : null,
    });
    if (process.env.NODE_ENV !== 'production') {
      console.info(
        `[tech] ${built.spec.id}: ${track.duration.toFixed(1)} s, widest steer ${((track.stats.maxSteer * 180) / Math.PI).toFixed(1)} deg` +
          (stage
            ? `, clearance ${stage.clearance.toFixed(2)} m`
            : built.street
              ? `, street ${built.street.facts.roadWidth.toFixed(1)} m wide, clearance ${built.street.stage.clearance.toFixed(2)} m`
              : `, stage r ${framing.radius.toFixed(1)} m`),
      );
    }
    invalidate();
    return () => {
      techClock.load(0, false);
      techSession.set(null);
      const s = useVehicleStore.getState();
      if (built.charge) {
        // the demo's flap and charge level are not the visitor's
        s.setOpening('charge', false);
        s.setSoc(soc0);
        s.setHmiScreen('home');
      }
      if (built.sensors) s.setBraking(false);
      if (built.boost) {
        s.setBoost(false, 0);
        s.setBoostPopup(false);
      }
      if (built.swivel) {
        s.setScreenDialog(false);
        s.setScreenPose('centre', 'rear');
      }
      // back to the stage's wide shot when the visitor changes demo (leaving the tab sets the next tab's own)
      if (built.spec.view === 'cabin' && isStageTab(s.tab)) s.setAnchor('techWide');
      s.setTechStage(null);
      s.setTechScene(null);
      s.setTechStreet(null);
      rig.reset();
      invalidate();
    };
  }, [built, rig, vehicle.dimensions.lengthMm, invalidate]);

  // a seek or a press of play asks for the next frame
  React.useEffect(() => techClock.subscribe(() => invalidate()), [invalidate]);

  // the ride height the car's screen asks for: the air suspension takes a moment to get there. With easy entry on
  // and a belt unbuckled (the car is parked then: the Tech tab buckles up again when it drives) the body kneels
  const kneel = easyEntry && !beltOn;
  const spanMm = vehicle.slug === 'nio-es8' ? 100 : RIDE_SPAN_MM;
  const levels = React.useMemo(() => rideLevelsOf(spanMm), [spanMm]);
  const rideGoal = spec?.driver === 'carpet' ? (levels[kneel ? 0 : rideLevel]?.mm ?? 0) : 0;
  const ride = React.useRef(0);
  const poseAt = React.useRef(NaN);
  React.useEffect(() => invalidate(), [rideGoal, invalidate]);

  useFrame((_, dt) => {
    if (!built) return;
    if (techClock.playing) {
      const speed = useVehicleStore.getState().techSpeed;
      techClock.advance(Math.min(built.track.duration, techClock.t + Math.min(dt, 0.1) * speed), performance.now());
    }
    const s = built.track.sample(techClock.t);
    const tm = built.treadmill;
    if (tm) {
      // the car stays on the spot and the road rolls under it
      // (a demo whose car changes lane keeps its sideways place and heading: Autonomous Drive's)
      rig.setSample({ ...s, x: rig.rac.x, y: tm.lateral ? s.y : rig.rac.y, yaw: tm.lateral ? s.yaw : 0 });
      rig.state.scroll = tm.scroll(techClock.t);
      rig.setChassis(tm.chassis(techClock.t));
    } else {
      rig.setSample(s);
      rig.setChassis(null);
    }
    // 35 mm in about a second, easing in and out of it
    const goal = rideGoal / 1000;
    const dRide = goal - ride.current;
    const step = Math.min(Math.abs(dRide), Math.max(0.004, Math.abs(dRide) * 0.12 + 0.008) * Math.min(dt, 0.1) * 6);
    ride.current += Math.sign(dRide) * step;
    rig.state.ride = ride.current;
    rig.apply();
    const bo = built.boost;
    if (bo) {
      const b = bo.state(techClock.t);
      useVehicleStore.getState().setBoost(b.on, b.step);
    }
    const sn = built.sensors;
    if (sn) {
      // the brake lamps come on with the brakes
      const braking = sn.scenario.readout(techClock.t).braking;
      const st = useVehicleStore.getState();
      if (st.braking !== braking) st.setBraking(braking);
    }
    const sw = built.swivel;
    if (sw && (techClock.playing || techClock.t !== poseAt.current)) {
      // the screen is asked for what the demo's presses say; a press on the car's own screen pauses the clock and takes over
      poseAt.current = techClock.t;
      const p = sw.pose(techClock.t);
      useVehicleStore.getState().setScreenPose(p.turn, p.slide);
    }
    const ch = built.charge;
    if (ch) {
      // the flap and the charge level follow the clock; the store tells the hinges and the car's screens
      const st = useVehicleStore.getState();
      st.setOpening('charge', ch.flapOpen(techClock.t));
      const soc = Math.round(ch.readout(techClock.t).soc * 100) / 100;
      if (st.soc !== soc) st.setSoc(soc);
    }
    if (techClock.playing || Math.abs(goal - ride.current) > 1e-4) invalidate();
  });

  // window.__tech: poke the rig from the console (set steer / spin / heave, read the track)
  React.useEffect(() => {
    if (process.env.NODE_ENV === 'production') return;
    (globalThis as unknown as { __tech?: unknown }).__tech = { rig, clock: techClock, built, invalidate, session: techSession };
  }, [rig, built, invalidate]);

  return built?.trailLine ? <primitive object={built.trailLine} /> : null;
}

/** The path of the rear axle's middle as a line on the floor. */
function trailOf(track: PlannedRun): THREE.Line {
  const pts = track.trace(0.15);
  const pos = new Float32Array(pts.length * 3);
  pts.forEach((p, i) => pos.set([p.x, 0.007, -p.y], i * 3));
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const line = new THREE.Line(
    g,
    new THREE.LineBasicMaterial({ color: '#2563eb', transparent: true, opacity: 0.6, depthWrite: false, toneMapped: false }),
  );
  line.raycast = () => {};
  return line;
}
