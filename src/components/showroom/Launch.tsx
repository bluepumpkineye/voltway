'use client';

import React from 'react';
import type { Vehicle } from '@/data/vehicles/schema';
import { techClock, useTechClock } from '@/lib/tech/clock';
import { pauseDemo } from '@/lib/tech/actions';
import { runPhase } from '@/lib/tech/phase';
import { useRuntime } from '@/lib/tech/session';
import { useVehicleStore } from '@/store/vehicle-store';
import { LaunchAudioController } from '@/lib/sound/launch';

const FOCUS = 'outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:ring-offset-1 focus-visible:ring-offset-transparent';

/**
 * Gran Turismo 7 Racing Cockpit HUD:
 * - Left: Speedometer cluster (0-280 km/h, white ticks, odometer stopwatch timer, battery gauge, parking brake icon)
 * - Center: Arched comb rev/shift bar (52 vertical red-fill bars), digital speed & recommended gear badge,
 *           Torque Distribution arc (FRONT 35:65 REAR in GT7 racing yellow), vertical traction/G bar
 * - Right: Tachometer cluster (0-8 x1000 RPM, crimson redline arc, turbo/power subdial, headlight icon)
 * - Completely transparent background, floating directly over the 3D road
 */
export function LaunchTools({ vehicle, inset = true }: { vehicle?: Vehicle; inset?: boolean } = {}) {
  const launch = useRuntime()?.launch;
  const clock = useTechClock();
  const run = runPhase(clock);

  // Speedometer refs
  const centerSpeed = React.useRef<SVGTextElement>(null);
  const watch = React.useRef<SVGTSpanElement>(null);
  const needleSpeed = React.useRef<SVGGElement>(null);

  // Center HUD gear refs
  const gearDigit = React.useRef<SVGTextElement>(null);
  const gearBadge = React.useRef<SVGTextElement>(null);

  // Tachometer refs
  const needleRpm = React.useRef<SVGGElement>(null);
  const needlePower = React.useRef<SVGGElement>(null);

  // Acceleration Timer & G-meter refs
  const timerSeconds = React.useRef<SVGTextElement>(null);
  const timerTargetLabel = React.useRef<SVGTextElement>(null);
  const timerProgressArc = React.useRef<SVGPathElement>(null);
  const timerBadge = React.useRef<SVGTextElement>(null);
  const timerBadgeBg = React.useRef<SVGRectElement>(null);
  const gBarFill = React.useRef<SVGRectElement>(null);

  // Smooth RPM needle damping (eliminates flashing on gear upshifts)
  const smoothRpmRef = React.useRef(0);
  const lastPaintTimeRef = React.useRef(0);

  // Arched Rev Bars (52 lines across top)
  const revLedsRef = React.useRef<(SVGLineElement | null)[]>([]);

  // Marks ref
  const marks = React.useRef<(HTMLElement | null)[]>([]);
  const playing = clock.playing;

  const setInset = useVehicleStore((s) => s.setDeviceInset);
  const launchTarget = useVehicleStore((s) => s.launchTarget);
  const setLaunchTarget = useVehicleStore((s) => s.setLaunchTarget);
  const setDrive = useVehicleStore((s) => s.setDrive);
  const techSpeed = useVehicleStore((s) => s.techSpeed);

  const activeTarget = launch?.target ?? launchTarget;

  // Background launch sound player
  const playerRef = React.useRef<LaunchAudioController | null>(null);
  if (!playerRef.current) {
    playerRef.current = new LaunchAudioController();
  }
  const player = playerRef.current;

  // Set camera inset so 3D car remains comfortably framed above the cockpit HUD (the Drive tab sets its own, with its panel)
  React.useEffect(() => {
    if (!inset) return;
    setInset({ right: 0, bottom: 0.28 });
    return () => setInset({ right: 0, bottom: 0 });
  }, [setInset, inset]);

  // Set vehicle and active threshold target sound
  React.useEffect(() => {
    if (vehicle?.slug) {
      player.setVehicleAndTarget(vehicle.slug, activeTarget);
    }
  }, [player, vehicle?.slug, activeTarget]);

  // Handle play / pause / finish transitions
  React.useEffect(() => {
    if (!vehicle) return;
    if (playing) {
      player.play(techClock.t, techSpeed);
    } else {
      if (run === 'done') {
        player.pause();
        player.seek(0);
      } else {
        player.pause();
      }
    }
  }, [playing, run, vehicle, techSpeed, player]);

  // Follow scrubber seek while paused
  React.useEffect(() => {
    return techClock.subscribe(() => {
      if (!techClock.playing) {
        player.seek(techClock.t);
      }
    });
  }, [player]);

  // Follow techSpeed changes
  React.useEffect(() => {
    player.setSpeed(techSpeed);
  }, [player, techSpeed]);

  // Dispose audio controller on unmount
  React.useEffect(() => {
    return () => {
      player.dispose();
    };
  }, [player]);

  // While clock is not running, follow snapshots (scrub, pause)
  const still = playing ? 0 : clock.t;

  React.useEffect(() => {
    if (!launch) return;
    const paint = () => {
      const r = launch.readout(techClock.t);
      const roundedSpeed = Math.round(r.speed);
      const tSec = techClock.t;

      // 1. Mechanical needle flutter / oscillation at top speed: once the pull is over and the car holds its speed (a run
      // with phases says so itself; the Tech tab's launch is timed for the SU7's 1.98 s and 6.09 s)
      const holding = r.phase === 'ease' || r.phase === 'coast' || r.phase === 'cruise';
      const isPeakCruising = r.phase !== undefined ? holding && r.speed > 90 : (activeTarget === 100 && r.elapsed >= 2.05) || (activeTarget === 200 && r.elapsed >= 7.0);
      const flutterFactor = isPeakCruising ? (r.phase !== undefined ? Math.min(1, (r.speed - 90) / 10) : Math.min(1, (r.elapsed - (activeTarget === 100 ? 2.05 : 7.0)) * 3.5)) : 0;
      const needleFlutterSpeed = flutterFactor * (Math.sin(tSec * 35.2) * 0.85 + Math.sin(tSec * 53.7) * 0.5);
      const needleFlutterRpm = flutterFactor * (Math.sin(tSec * 43.1) * 1.4 + Math.sin(tSec * 68.4) * 0.7);

      // 2. Left Speedometer needle (0 to 280 km/h scale) with top-speed oscillation
      const baseAngleSpeed = -135 + (Math.min(280, Math.max(0, r.speed)) / 280) * 270;
      const angleSpeed = baseAngleSpeed + needleFlutterSpeed;
      if (needleSpeed.current) {
        needleSpeed.current.setAttribute('transform', `translate(140, 140) rotate(${angleSpeed.toFixed(1)})`);
      }

      // 3. Digital speed readout in center housing (with subtle flutter at peak speed)
      const digitalFlutter = flutterFactor > 0.4 ? Math.round(Math.sin(tSec * 16) * 0.9) : 0;
      const displayedSpeed = roundedSpeed + digitalFlutter;
      if (centerSpeed.current) centerSpeed.current.textContent = String(displayedSpeed);

      // 4. Stopwatch timer in odometer box
      if (watch.current) watch.current.textContent = `${r.elapsed < 10 ? '0' : ''}${r.elapsed.toFixed(2)} s`;

      // 5. Gear calculation & 4th to 5th gear shift at 204 km/h
      let gear = 1;
      let nextGear = 2;
      let rpmFraction = 0;

      if (activeTarget === 100) {
        // 0-100 run: 1st -> 2nd -> 3rd gear
        if (r.speed < 42) {
          gear = 1;
          nextGear = 2;
          rpmFraction = r.speed / 45;
        } else if (r.speed < 80) {
          gear = 2;
          nextGear = 3;
          rpmFraction = 0.52 + ((r.speed - 42) / 38) * 0.48;
        } else {
          gear = 3;
          nextGear = 4;
          rpmFraction = 0.65 + ((r.speed - 80) / 25) * 0.35;
        }
      } else {
        // 0-200+ run:
        // Under 50 km/h: 1st
        // 50-100 km/h: 2nd
        // 100-155 km/h: 3rd
        // 155-204 km/h: 4th gear!
        // Reaching 204 km/h: shifts from 4th to 5th gear, speed continues climbing up to ~213 km/h!
        if (r.speed < 50) {
          gear = 1;
          nextGear = 2;
          rpmFraction = r.speed / 52;
        } else if (r.speed < 100) {
          gear = 2;
          nextGear = 3;
          rpmFraction = 0.55 + ((r.speed - 50) / 50) * 0.45;
        } else if (r.speed < 155) {
          gear = 3;
          nextGear = 4;
          rpmFraction = 0.60 + ((r.speed - 100) / 55) * 0.40;
        } else if (r.speed < 204) {
          gear = 4;
          nextGear = 5;
          rpmFraction = 0.68 + ((r.speed - 155) / 49) * 0.32;
        } else {
          // 5th gear! Reached 204 km/h, gear shifts from 4 to 5!
          gear = 5;
          nextGear = 4; // in GT7 HUD, recommended shift shows in the red box
          rpmFraction = Math.min(0.97, 0.72 + ((r.speed - 204) / 10) * 0.25);
        }
      }

      if (gearDigit.current) gearDigit.current.textContent = String(gear);
      if (gearBadge.current) gearBadge.current.textContent = String(nextGear);

      // 6. Right Tachometer needle with smooth mechanical damping
      const now = typeof performance !== 'undefined' ? performance.now() : Date.now();
      const dt = lastPaintTimeRef.current ? Math.min(0.08, (now - lastPaintTimeRef.current) / 1000) : 0.016;
      lastPaintTimeRef.current = now;

      if (!playing || techClock.t < 0.05) {
        smoothRpmRef.current = rpmFraction;
      } else {
        // When gearing up: damp needle smoothly (rate 8.5) so it glides down realistically without flashing
        // When pulling/accelerating: follow promptly (rate 22)
        const lambda = rpmFraction < smoothRpmRef.current ? 8.5 : 22;
        smoothRpmRef.current += (rpmFraction - smoothRpmRef.current) * (1 - Math.exp(-lambda * dt));
      }
      const displayedRpmFraction = smoothRpmRef.current;

      const rpmVal = displayedRpmFraction * 8;
      const baseAngleRpm = -135 + (rpmVal / 8) * 270;
      const angleRpm = baseAngleRpm + needleFlutterRpm;
      if (needleRpm.current) {
        needleRpm.current.setAttribute('transform', `translate(700, 140) rotate(${angleRpm.toFixed(1)})`);
      }

      // 7. Arched Rev Lights Bar (52 vertical bars filling left to right in solid red)
      const totalBars = 52;
      const activeBars = Math.min(totalBars, Math.round(displayedRpmFraction * totalBars));
      for (let i = 0; i < totalBars; i++) {
        const el = revLedsRef.current[i];
        if (el) {
          if (i < activeBars) {
            el.setAttribute('stroke', '#ff1a2a');
            el.setAttribute('opacity', '1');
          } else {
            el.setAttribute('stroke', 'rgba(255, 255, 255, 0.22)');
            el.setAttribute('opacity', '0.6');
          }
        }
      }

      // 6. Sub-dial needle (Boost / Power kW: -1 to 2 bar / 0 to 1200 kW)
      if (needlePower.current) {
        const boostVal = Math.min(2, Math.max(-1, -1 + r.g * 1.9));
        const anglePow = -90 + ((boostVal + 1) / 3) * 180;
        needlePower.current.setAttribute('transform', `translate(700, 170) rotate(${anglePow.toFixed(1)})`);
      }

      // 7. Acceleration Timer & Milestone Gauge (GT7 Cockpit Typography)
      const runLabel = launch.drive?.runs.find((x) => x.id === launch.drive?.run)?.label ?? `0–${activeTarget}`;
      const targetTime = launch.marks.find((m) => m.speed === activeTarget)?.time ?? (activeTarget === 200 ? 6.09 : 1.98);
      const isReached = r.elapsed >= targetTime - 0.02;

      // Stopwatch digital time readout in GT7 HUD typography
      if (timerSeconds.current) {
        timerSeconds.current.textContent = `${r.elapsed < 10 ? '0' : ''}${r.elapsed.toFixed(2)}`;
      }

      // Left Target Label (0-100 or ✓ 100)
      if (timerTargetLabel.current) {
        timerTargetLabel.current.textContent = isReached ? `✓ ${activeTarget}` : runLabel;
        timerTargetLabel.current.setAttribute('fill', isReached ? '#6ee7b7' : '#94a3b8');
      }

      // Progress fraction along semicircular arc (sweeps smoothly 0 to 180 deg)
      const timerProgress = Math.min(1, Math.max(0, r.elapsed / targetTime));
      if (timerProgressArc.current) {
        if (timerProgress <= 0.005) {
          timerProgressArc.current.setAttribute('d', 'M 364 185 A 56 56 0 0 1 364 185');
          timerProgressArc.current.setAttribute('stroke', '#ffffff');
        } else {
          const currDeg = 180 - timerProgress * 180;
          const currRad = (currDeg * Math.PI) / 180;
          const currX = (420 - 56 * Math.cos(currRad)).toFixed(1);
          const currY = (185 - 56 * Math.sin(currRad)).toFixed(1);
          timerProgressArc.current.setAttribute('d', `M 364 185 A 56 56 0 0 1 ${currX} ${currY}`);
          timerProgressArc.current.setAttribute('stroke', isReached ? '#10b981' : '#ffffff');
        }
      }

      // Milestone status badge
      if (timerBadge.current && timerBadgeBg.current) {
        if (isReached) {
          timerBadge.current.textContent = `✓ ${activeTarget} KM/H IN ${targetTime.toFixed(2)}s`;
          timerBadge.current.setAttribute('fill', '#6ee7b7');
          timerBadgeBg.current.setAttribute('fill', 'rgba(6, 78, 59, 0.8)');
          timerBadgeBg.current.setAttribute('stroke', '#10b981');
        } else {
          timerBadge.current.textContent = `TARGET ${runLabel} KM/H`;
          timerBadge.current.setAttribute('fill', '#94a3b8');
          timerBadgeBg.current.setAttribute('fill', '#131924');
          timerBadgeBg.current.setAttribute('stroke', 'rgba(255, 255, 255, 0.2)');
        }
      }

      // 8. Vertical G-Force Level Bar
      const gVal = Math.max(0, r.g);
      if (gBarFill.current) {
        const barHeight = Math.min(52, Math.max(2, (gVal / 1.6) * 52));
        gBarFill.current.setAttribute('y', String(186 - barHeight));
        gBarFill.current.setAttribute('height', String(barHeight));
      }

      // 9. Threshold marks reached status: the chips are the scenario's runs, or the speeds of a plain launch
      if (launch.drive) {
        launch.drive.runs.forEach((run, i) => {
          const hit = run.id === launch.drive?.run && r.elapsed >= run.time - 1e-3;
          marks.current[i]?.setAttribute('data-reached', hit ? 'true' : 'false');
        });
      } else {
        launch.marks.forEach((m, i) => {
          marks.current[i]?.setAttribute('data-reached', r.elapsed >= m.time - 1e-3 ? 'true' : 'false');
        });
      }

      // 10. The motor's sound follows the car: it fades once the car is braking or crawling through a manoeuvre
      const quiet = r.phase === 'brake' || r.phase === 'decel' || r.phase === 'stop' || r.phase === 'slalom' || r.phase === 'crab';
      player.setGain(quiet ? Math.min(1, r.speed / 120) ** 2 : 1);

      // 11. Audio drift correction
      if (playing) {
        const audioTime = player.currentTime;
        if (Math.abs(audioTime - techClock.t) > 0.35) {
          player.seek(techClock.t);
        }
      }
    };

    paint();
    if (!playing) return;
    let raf = requestAnimationFrame(function loop() {
      paint();
      raf = requestAnimationFrame(loop);
    });
    return () => cancelAnimationFrame(raf);
  }, [launch, playing, still, vehicle?.slug, player, activeTarget]);

  const handleSelectTarget = (targetSpeed: number) => {
    if (activeTarget === targetSpeed) return;
    if (techClock.playing) {
      techClock.pause();
    }
    setLaunchTarget(targetSpeed);
  };

  // the Drive tab's runs are chosen by id (a rolling pull has no 0 to start from)
  const handleSelectRun = (id: string) => {
    if (launch?.drive?.run === id) return;
    if (techClock.playing) techClock.pause();
    setDrive({ run: id });
  };

  const action =
    run === 'driving'
      ? { label: 'Pause', run: pauseDemo }
      : run === 'paused'
        ? { label: 'Resume', run: () => techClock.play() }
        : run === 'done'
          ? { label: 'Launch again', run: () => techClock.play() }
          : { label: 'Launch', run: () => techClock.play() };

  // the chips: a scenario's runs (0–100, 0–200, 80–160 ...), or the speeds a plain launch passes; a time with a star is ours
  const chips: { key: string; label: string; time: number; published: boolean; selected: boolean; title: string; select: () => void }[] = launch?.drive
    ? launch.drive.runs.map((r) => ({
        key: r.id,
        label: r.label,
        time: r.time,
        published: r.published,
        selected: r.id === launch.drive?.run,
        title: `Run ${r.label} km/h: ${r.time.toFixed(2)} s ${r.published ? 'published' : 'modelled'}`,
        select: () => handleSelectRun(r.id),
      }))
    : (launch?.marks ?? []).map((m) => ({
        key: String(m.speed),
        label: `0–${m.speed}`,
        time: m.time,
        published: m.published !== false,
        selected: activeTarget === m.speed,
        title: `Target: 0–${m.speed} km/h (${m.time.toFixed(2)} s ${m.published !== false ? 'published' : 'modelled'})`,
        select: () => handleSelectTarget(m.speed),
      }));
  const hasMultipleMarks = chips.length > 1;

  return (
    <div className="pointer-events-auto flex w-full max-w-[840px] flex-col items-center select-none bg-transparent">
      {/* Gran Turismo 7 Exact Racing Cockpit Instrument Cluster */}
      <svg
        width="100%"
        viewBox="0 0 840 236"
        className="w-full max-w-[840px] overflow-visible drop-shadow-[0_8px_24px_rgba(0,0,0,0.85)]"
        aria-label="Gran Turismo 7 Racing Cockpit"
      >
        <defs>
          <filter id="gt7GlowRed" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* ============================================================ */}
        {/* 1. LEFT INSTRUMENT CLUSTER: SPEEDOMETER (0 - 280 KM/H)      */}
        {/* ============================================================ */}
        <g id="gt7Speedometer">
          {/* Subtle dark glass backing */}
          <circle cx="140" cy="140" r="95" fill="rgba(16, 20, 27, 0.65)" stroke="rgba(255, 255, 255, 0.12)" strokeWidth="1" />

          {/* Outer White Arc */}
          <path
            d="M 72.8 207.2 A 95 95 0 1 1 207.2 207.2"
            fill="none"
            stroke="#ffffff"
            strokeWidth="2.5"
            strokeLinecap="round"
          />

          {/* Speedometer Ticks */}
            <line x1="84.8" y1="195.2" x2="75.7" y2="204.3" stroke="#ffffff" strokeWidth="2.2" opacity="1" />
            <line x1="70.7" y1="189.2" x2="65.8" y2="192.7" stroke="#ffffff" strokeWidth="1" opacity="0.6" />
            <line x1="66.1" y1="175.6" x2="58" y2="179.5" stroke="#ffffff" strokeWidth="1.5" opacity="0.85" />
            <line x1="58.3" y1="163.5" x2="52.6" y2="165.2" stroke="#ffffff" strokeWidth="1" opacity="0.6" />
            <line x1="62.5" y1="148.7" x2="49.6" y2="150.2" stroke="#ffffff" strokeWidth="2.2" opacity="1" />
            <line x1="55.1" y1="135.2" x2="49.1" y2="134.9" stroke="#ffffff" strokeWidth="1" opacity="0.6" />
            <line x1="60.1" y1="121.8" x2="51.3" y2="119.8" stroke="#ffffff" strokeWidth="1.5" opacity="0.85" />
            <line x1="61.5" y1="107.5" x2="55.9" y2="105.2" stroke="#ffffff" strokeWidth="1" opacity="0.6" />
            <line x1="74" y1="98.5" x2="62.9" y2="91.6" stroke="#ffffff" strokeWidth="2.2" opacity="1" />
            <line x1="76.6" y1="83.4" x2="72.1" y2="79.4" stroke="#ffffff" strokeWidth="1" opacity="0.6" />
            <line x1="88.9" y1="75.9" x2="83.3" y2="68.9" stroke="#ffffff" strokeWidth="1.5" opacity="0.85" />
            <line x1="98.9" y1="65.6" x2="96" y2="60.4" stroke="#ffffff" strokeWidth="1" opacity="0.6" />
            <line x1="114.2" y1="66.4" x2="109.9" y2="54.1" stroke="#ffffff" strokeWidth="2.2" opacity="1" />
            <line x1="125.8" y1="56.2" x2="124.8" y2="50.3" stroke="#ffffff" strokeWidth="1" opacity="0.6" />
            <line x1="140" y1="58" x2="140" y2="49" stroke="#ffffff" strokeWidth="1.5" opacity="0.85" />
            <line x1="154.2" y1="56.2" x2="155.2" y2="50.3" stroke="#ffffff" strokeWidth="1" opacity="0.6" />
            <line x1="165.8" y1="66.4" x2="170.1" y2="54.1" stroke="#ffffff" strokeWidth="2.2" opacity="1" />
            <line x1="181.1" y1="65.6" x2="184" y2="60.4" stroke="#ffffff" strokeWidth="1" opacity="0.6" />
            <line x1="191.1" y1="75.9" x2="196.7" y2="68.9" stroke="#ffffff" strokeWidth="1.5" opacity="0.85" />
            <line x1="203.4" y1="83.4" x2="207.9" y2="79.4" stroke="#ffffff" strokeWidth="1" opacity="0.6" />
            <line x1="206" y1="98.5" x2="217.1" y2="91.6" stroke="#ffffff" strokeWidth="2.2" opacity="1" />
            <line x1="218.5" y1="107.5" x2="224.1" y2="105.2" stroke="#ffffff" strokeWidth="1" opacity="0.6" />
            <line x1="219.9" y1="121.8" x2="228.7" y2="119.8" stroke="#ffffff" strokeWidth="1.5" opacity="0.85" />
            <line x1="224.9" y1="135.2" x2="230.9" y2="134.9" stroke="#ffffff" strokeWidth="1" opacity="0.6" />
            <line x1="217.5" y1="148.7" x2="230.4" y2="150.2" stroke="#ffffff" strokeWidth="2.2" opacity="1" />
            <line x1="221.7" y1="163.5" x2="227.4" y2="165.2" stroke="#ffffff" strokeWidth="1" opacity="0.6" />
            <line x1="213.9" y1="175.6" x2="222" y2="179.5" stroke="#ffffff" strokeWidth="1.5" opacity="0.85" />
            <line x1="209.3" y1="189.2" x2="214.2" y2="192.7" stroke="#ffffff" strokeWidth="1" opacity="0.6" />
            <line x1="195.2" y1="195.2" x2="204.3" y2="204.3" stroke="#ffffff" strokeWidth="2.2" opacity="1" />

          {/* Speedometer Numbers (40, 80, 120, 160, 200, 240, 280) */}
            <text x="72.4" y="151.6" textAnchor="middle" fontSize="10.5" fontWeight="700" fill="#ffffff" fontFamily="'Chakra Petch', sans-serif">40</text>
            <text x="82.4" y="107.8" textAnchor="middle" fontSize="10.5" fontWeight="700" fill="#ffffff" fontFamily="'Chakra Petch', sans-serif">80</text>
            <text x="117.5" y="79.8" textAnchor="middle" fontSize="10.5" fontWeight="700" fill="#ffffff" fontFamily="'Chakra Petch', sans-serif">120</text>
            <text x="162.5" y="79.8" textAnchor="middle" fontSize="10.5" fontWeight="700" fill="#ffffff" fontFamily="'Chakra Petch', sans-serif">160</text>
            <text x="197.6" y="107.8" textAnchor="middle" fontSize="10.5" fontWeight="700" fill="#ffffff" fontFamily="'Chakra Petch', sans-serif">200</text>
            <text x="207.6" y="151.6" textAnchor="middle" fontSize="10.5" fontWeight="700" fill="#ffffff" fontFamily="'Chakra Petch', sans-serif">240</text>
            <text x="188.1" y="192.1" textAnchor="middle" fontSize="10.5" fontWeight="700" fill="#ffffff" fontFamily="'Chakra Petch', sans-serif">280</text>

          {/* Center Unit Label: km/h */}
          <text x="140" y="106" textAnchor="middle" fontSize="11" fontWeight="700" fill="#cbd5e1" fontFamily="'Chakra Petch', sans-serif">
            km/h
          </text>

          {/* Brake / Warning Circle Icon: (!) */}
          <g transform="translate(182, 132)">
            <circle cx="0" cy="0" r="8.5" fill="none" stroke="rgba(255, 255, 255, 0.45)" strokeWidth="1" />
            <text x="0" y="3.5" textAnchor="middle" fontSize="9" fontWeight="900" fill="rgba(255, 255, 255, 0.7)">
              !
            </text>
            <path d="M -11 -3 A 12 12 0 0 0 -11 3" fill="none" stroke="rgba(255, 255, 255, 0.45)" strokeWidth="1" />
            <path d="M 11 -3 A 12 12 0 0 1 11 3" fill="none" stroke="rgba(255, 255, 255, 0.45)" strokeWidth="1" />
          </g>

          {/* Fuel / Battery Sub-Arc */}
          <g transform="translate(140, 170)">
            <path d="M -22 0 A 22 22 0 0 1 22 0" fill="none" stroke="rgba(255, 255, 255, 0.3)" strokeWidth="2" />
            <text x="-28" y="3" textAnchor="middle" fontSize="9" fontWeight="700" fill="#94a3b8" fontFamily="'Chakra Petch', sans-serif">E</text>
            <text x="28" y="3" textAnchor="middle" fontSize="9" fontWeight="700" fill="#94a3b8" fontFamily="'Chakra Petch', sans-serif">F</text>
            {/* Pump Icon */}
            <path d="M -4 -8 L 4 -8 L 4 0 L -4 0 Z M 4 -6 L 7 -4 L 7 2" fill="none" stroke="#94a3b8" strokeWidth="1" />
          </g>

          {/* Odometer / Stopwatch Timer Capsule (Bottom of Dial) */}
          <g transform="translate(140, 204)">
            <rect x="-36" y="-9" width="72" height="18" rx="3" fill="#090d14" stroke="rgba(255, 255, 255, 0.28)" strokeWidth="0.8" />
            <text y="4" textAnchor="middle" fontSize="10.5" fontWeight="700" fill="#ffffff" fontFamily="'Chakra Petch', monospace" letterSpacing="0.5">
              <tspan ref={watch}>00.00 s</tspan>
            </text>
          </g>

          {/* White Tapered Speedometer Needle */}
          <g ref={needleSpeed} transform="translate(140, 140) rotate(-135)">
            <polygon points="-3,10 3,10 0.8,-88 -0.8,-88" fill="#ffffff" />
            <line x1="0" y1="8" x2="0" y2="-86" stroke="#1e293b" strokeWidth="0.8" />
          </g>

          {/* Center Hub */}
          <circle cx="140" cy="140" r="16" fill="#1b212d" stroke="#334155" strokeWidth="1.5" />
          <circle cx="140" cy="140" r="10" fill="#0d1117" />
          <circle cx="140" cy="140" r="4" fill="#ffffff" />
        </g>

        {/* Chevron bracket between Left and Center */}
        <g stroke="rgba(255, 255, 255, 0.35)" strokeWidth="1.5" fill="none">
          <polyline points="248,130 242,140 248,150" />
          <line x1="256" y1="125" x2="256" y2="155" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="1" />
          {/* Lower status icons */}
          <circle cx="256" cy="180" r="6" fill="none" stroke="rgba(255, 255, 255, 0.3)" strokeWidth="1" />
          <text x="256" y="183" textAnchor="middle" fontSize="6.5" fill="rgba(255, 255, 255, 0.4)">ABS</text>
        </g>

        {/* ============================================================ */}
        {/* 2. CENTER CLUSTER: ARMORED HOUSING, REV LIGHTS & TORQUE HUD */}
        {/* ============================================================ */}
        <g id="gt7CenterCluster">
          {/* Main Arched Trapezoid Background Housing */}
          <path
            d="M 284 38 Q 420 18 556 38 L 576 84 L 264 84 Z"
            fill="rgba(18, 22, 30, 0.82)"
            stroke="rgba(255, 255, 255, 0.16)"
            strokeWidth="1.2"
          />

          {/* Subtle concentric sonic radar ripples on the left and right wings */}
          <g stroke="rgba(255, 255, 255, 0.05)" strokeWidth="1" fill="none">
            <circle cx="270" cy="62" r="16" />
            <circle cx="270" cy="62" r="28" />
            <circle cx="570" cy="62" r="16" />
            <circle cx="570" cy="62" r="28" />
          </g>

          {/* Arched Top Comb of 52 Vertical Rev Bars */}
          <g id="gt7RevBars">
            <line
              key={0}
              ref={(el) => { revLedsRef.current[0] = el; }}
              x1="286"
              y1="38"
              x2="286"
              y2="50.5"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={1}
              ref={(el) => { revLedsRef.current[1] = el; }}
              x1="291.3"
              y1="36.8"
              x2="291.3"
              y2="49.3"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={2}
              ref={(el) => { revLedsRef.current[2] = el; }}
              x1="296.5"
              y1="35.6"
              x2="296.5"
              y2="48.1"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={3}
              ref={(el) => { revLedsRef.current[3] = el; }}
              x1="301.8"
              y1="34.5"
              x2="301.8"
              y2="47"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={4}
              ref={(el) => { revLedsRef.current[4] = el; }}
              x1="307"
              y1="33.4"
              x2="307"
              y2="45.9"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={5}
              ref={(el) => { revLedsRef.current[5] = el; }}
              x1="312.3"
              y1="32.3"
              x2="312.3"
              y2="44.8"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={6}
              ref={(el) => { revLedsRef.current[6] = el; }}
              x1="317.5"
              y1="31.4"
              x2="317.5"
              y2="43.9"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={7}
              ref={(el) => { revLedsRef.current[7] = el; }}
              x1="322.8"
              y1="30.4"
              x2="322.8"
              y2="42.9"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={8}
              ref={(el) => { revLedsRef.current[8] = el; }}
              x1="328"
              y1="29.5"
              x2="328"
              y2="42"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={9}
              ref={(el) => { revLedsRef.current[9] = el; }}
              x1="333.3"
              y1="28.7"
              x2="333.3"
              y2="41.2"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={10}
              ref={(el) => { revLedsRef.current[10] = el; }}
              x1="338.5"
              y1="27.9"
              x2="338.5"
              y2="40.4"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={11}
              ref={(el) => { revLedsRef.current[11] = el; }}
              x1="343.8"
              y1="27.2"
              x2="343.8"
              y2="39.7"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={12}
              ref={(el) => { revLedsRef.current[12] = el; }}
              x1="349.1"
              y1="26.5"
              x2="349.1"
              y2="39"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={13}
              ref={(el) => { revLedsRef.current[13] = el; }}
              x1="354.3"
              y1="25.8"
              x2="354.3"
              y2="38.3"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={14}
              ref={(el) => { revLedsRef.current[14] = el; }}
              x1="359.6"
              y1="25.3"
              x2="359.6"
              y2="37.8"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={15}
              ref={(el) => { revLedsRef.current[15] = el; }}
              x1="364.8"
              y1="24.7"
              x2="364.8"
              y2="37.2"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={16}
              ref={(el) => { revLedsRef.current[16] = el; }}
              x1="370.1"
              y1="24.2"
              x2="370.1"
              y2="36.7"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={17}
              ref={(el) => { revLedsRef.current[17] = el; }}
              x1="375.3"
              y1="23.8"
              x2="375.3"
              y2="36.3"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={18}
              ref={(el) => { revLedsRef.current[18] = el; }}
              x1="380.6"
              y1="23.4"
              x2="380.6"
              y2="35.9"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={19}
              ref={(el) => { revLedsRef.current[19] = el; }}
              x1="385.8"
              y1="23"
              x2="385.8"
              y2="35.5"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={20}
              ref={(el) => { revLedsRef.current[20] = el; }}
              x1="391.1"
              y1="22.7"
              x2="391.1"
              y2="35.2"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={21}
              ref={(el) => { revLedsRef.current[21] = el; }}
              x1="396.4"
              y1="22.5"
              x2="396.4"
              y2="35"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={22}
              ref={(el) => { revLedsRef.current[22] = el; }}
              x1="401.6"
              y1="22.3"
              x2="401.6"
              y2="34.8"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={23}
              ref={(el) => { revLedsRef.current[23] = el; }}
              x1="406.9"
              y1="22.2"
              x2="406.9"
              y2="34.7"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={24}
              ref={(el) => { revLedsRef.current[24] = el; }}
              x1="412.1"
              y1="22.1"
              x2="412.1"
              y2="34.6"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={25}
              ref={(el) => { revLedsRef.current[25] = el; }}
              x1="417.4"
              y1="22"
              x2="417.4"
              y2="34.5"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={26}
              ref={(el) => { revLedsRef.current[26] = el; }}
              x1="422.6"
              y1="22"
              x2="422.6"
              y2="34.5"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={27}
              ref={(el) => { revLedsRef.current[27] = el; }}
              x1="427.9"
              y1="22.1"
              x2="427.9"
              y2="34.6"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={28}
              ref={(el) => { revLedsRef.current[28] = el; }}
              x1="433.1"
              y1="22.2"
              x2="433.1"
              y2="34.7"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={29}
              ref={(el) => { revLedsRef.current[29] = el; }}
              x1="438.4"
              y1="22.3"
              x2="438.4"
              y2="34.8"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={30}
              ref={(el) => { revLedsRef.current[30] = el; }}
              x1="443.6"
              y1="22.5"
              x2="443.6"
              y2="35"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={31}
              ref={(el) => { revLedsRef.current[31] = el; }}
              x1="448.9"
              y1="22.7"
              x2="448.9"
              y2="35.2"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={32}
              ref={(el) => { revLedsRef.current[32] = el; }}
              x1="454.2"
              y1="23"
              x2="454.2"
              y2="35.5"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={33}
              ref={(el) => { revLedsRef.current[33] = el; }}
              x1="459.4"
              y1="23.4"
              x2="459.4"
              y2="35.9"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={34}
              ref={(el) => { revLedsRef.current[34] = el; }}
              x1="464.7"
              y1="23.8"
              x2="464.7"
              y2="36.3"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={35}
              ref={(el) => { revLedsRef.current[35] = el; }}
              x1="469.9"
              y1="24.2"
              x2="469.9"
              y2="36.7"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={36}
              ref={(el) => { revLedsRef.current[36] = el; }}
              x1="475.2"
              y1="24.7"
              x2="475.2"
              y2="37.2"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={37}
              ref={(el) => { revLedsRef.current[37] = el; }}
              x1="480.4"
              y1="25.3"
              x2="480.4"
              y2="37.8"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={38}
              ref={(el) => { revLedsRef.current[38] = el; }}
              x1="485.7"
              y1="25.8"
              x2="485.7"
              y2="38.3"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={39}
              ref={(el) => { revLedsRef.current[39] = el; }}
              x1="490.9"
              y1="26.5"
              x2="490.9"
              y2="39"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={40}
              ref={(el) => { revLedsRef.current[40] = el; }}
              x1="496.2"
              y1="27.2"
              x2="496.2"
              y2="39.7"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={41}
              ref={(el) => { revLedsRef.current[41] = el; }}
              x1="501.5"
              y1="27.9"
              x2="501.5"
              y2="40.4"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={42}
              ref={(el) => { revLedsRef.current[42] = el; }}
              x1="506.7"
              y1="28.7"
              x2="506.7"
              y2="41.2"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={43}
              ref={(el) => { revLedsRef.current[43] = el; }}
              x1="512"
              y1="29.5"
              x2="512"
              y2="42"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={44}
              ref={(el) => { revLedsRef.current[44] = el; }}
              x1="517.2"
              y1="30.4"
              x2="517.2"
              y2="42.9"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={45}
              ref={(el) => { revLedsRef.current[45] = el; }}
              x1="522.5"
              y1="31.4"
              x2="522.5"
              y2="43.9"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={46}
              ref={(el) => { revLedsRef.current[46] = el; }}
              x1="527.7"
              y1="32.3"
              x2="527.7"
              y2="44.8"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={47}
              ref={(el) => { revLedsRef.current[47] = el; }}
              x1="533"
              y1="33.4"
              x2="533"
              y2="45.9"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={48}
              ref={(el) => { revLedsRef.current[48] = el; }}
              x1="538.2"
              y1="34.5"
              x2="538.2"
              y2="47"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={49}
              ref={(el) => { revLedsRef.current[49] = el; }}
              x1="543.5"
              y1="35.6"
              x2="543.5"
              y2="48.1"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={50}
              ref={(el) => { revLedsRef.current[50] = el; }}
              x1="548.7"
              y1="36.8"
              x2="548.7"
              y2="49.3"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <line
              key={51}
              ref={(el) => { revLedsRef.current[51] = el; }}
              x1="554"
              y1="38"
              x2="554"
              y2="50.5"
              stroke="rgba(255, 255, 255, 0.22)"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
          </g>

          {/* Center Red Shift Indicator Pip */}
          <circle cx="420" cy="16" r="2.8" fill="#ff1a2a" filter="url(#gt7GlowRed)" />

          {/* Digital Speed (Left of Center Housing) */}
          <g transform="translate(406, 64)" textAnchor="end">
            <text ref={centerSpeed} y="0" fontSize="42" fontWeight="700" fill="#ffffff" fontFamily="'Chakra Petch', sans-serif" letterSpacing="-1.5">
              0
            </text>
            <text x="-4" y="14" fontSize="10.5" fontWeight="600" fill="#94a3b8" fontFamily="'Chakra Petch', sans-serif">
              km/h
            </text>
          </g>

          {/* Thin Vertical Center Divider Line */}
          <line x1="420" y1="36" x2="420" y2="76" stroke="rgba(255, 255, 255, 0.22)" strokeWidth="1.2" />

          {/* Gear Display & Recommended Gear Badge (Right of Center Housing) */}
          <g transform="translate(434, 66)">
            {/* Main Gear Digit */}
            <text ref={gearDigit} y="0" fontSize="44" fontWeight="700" fill="#ffffff" fontFamily="'Chakra Petch', sans-serif">
              1
            </text>

            {/* Recommended Shift / Boost Badge (Red Square with rounded corners) */}
            <rect x="34" y="-30" width="30" height="28" rx="3.5" fill="#ff1a2a" />
            <text ref={gearBadge} x="49" y="-10" textAnchor="middle" fontSize="21" fontWeight="900" fill="#ffffff" fontFamily="'Chakra Petch', sans-serif">
              4
            </text>

            {/* Sub-label under gear: AT */}
            <text x="49" y="12" textAnchor="middle" fontSize="9.5" fontWeight="700" fill="#94a3b8" fontFamily="'Chakra Petch', sans-serif">
              AT
            </text>
          </g>

          {/* Acceleration Timer Section */}
          <g transform="translate(420, 116)" textAnchor="middle">
            {/* Left Chevron Button (Target 100 km/h) - Spaced generously from title */}
            <g
              className="cursor-pointer transition-opacity hover:opacity-100"
              onClick={() => handleSelectTarget(100)}
              opacity={activeTarget === 100 ? 0.35 : 0.9}
            >
              <circle cx="-96" cy="-3" r="16" fill="transparent" />
              <circle cx="-96" cy="-3" r="6.5" fill="#1b212c" stroke="rgba(255, 255, 255, 0.45)" strokeWidth="0.8" />
              <polygon points="-98,-3 -94,-6 -94,0" fill="#ffffff" />
            </g>

            {/* Title Text (GT7 Typography: Title Case, Chakra Petch font, 30px clear margin to arrows) */}
            <text x="0" y="0" textAnchor="middle" fontSize="12" fontWeight="600" fill="#e2e8f0" letterSpacing="0.4" fontFamily="'Chakra Petch', sans-serif">
              Acceleration Timer
            </text>

            {/* Right Chevron Button (Target 200 km/h) - Spaced generously from title */}
            <g
              className="cursor-pointer transition-opacity hover:opacity-100"
              onClick={() => hasMultipleMarks && handleSelectTarget(200)}
              opacity={activeTarget === 200 || !hasMultipleMarks ? 0.35 : 0.9}
            >
              <circle cx="96" cy="-3" r="16" fill="transparent" />
              <circle cx="96" cy="-3" r="6.5" fill="#1b212c" stroke="rgba(255, 255, 255, 0.45)" strokeWidth="0.8" />
              <polygon points="98,-3 94,-6 94,0" fill="#ffffff" />
            </g>
          </g>

          {/* Acceleration Timer Semicircular Gauge (GT7 Cockpit Topography) */}
          <g id="timerGaugeSection">
            {/* Background Base Track Arc (GT7 Thick Vibrant Yellow) */}
            <path
              d="M 364 185 A 56 56 0 0 1 476 185"
              fill="none"
              stroke="#facc15"
              strokeWidth="5"
              strokeLinecap="round"
            />

            {/* Dynamic Active Progress Highlight Arc */}
            <path
              ref={timerProgressArc}
              d="M 364 185 A 56 56 0 0 1 364 185"
              fill="none"
              stroke="#ffffff"
              strokeWidth="6"
              strokeLinecap="round"
            />

            {/* Top Indicator Triangle ▲ (GT7 Signature Framing) */}
            <polygon points="417,144 423,144 420,139" fill="#ffffff" />

            {/* Bottom Indicator Triangle ▼ (GT7 Signature Framing) */}
            <polygon points="417,196 423,196 420,201" fill="#ffffff" />

            {/* Centered Cockpit HUD Typography: [0-100]  00.00  [SEC] matching FRONT 35:65 REAR */}
            <g transform="translate(420, 180)" textAnchor="middle">
              <text
                ref={timerTargetLabel}
                x="-44"
                y="-1"
                textAnchor="end"
                fontSize="11"
                fontWeight="700"
                fill="#94a3b8"
                fontFamily="'Chakra Petch', sans-serif"
              >
                0–{activeTarget}
              </text>
              <text
                ref={timerSeconds}
                x="0"
                y="2"
                textAnchor="middle"
                fontSize="28"
                fontWeight="700"
                fill="#ffffff"
                fontFamily="'Chakra Petch', sans-serif"
                letterSpacing="0.8"
              >
                00.00
              </text>
              <text
                x="44"
                y="-1"
                textAnchor="start"
                fontSize="11"
                fontWeight="700"
                fill="#94a3b8"
                fontFamily="'Chakra Petch', sans-serif"
              >
                SEC
              </text>
            </g>

            {/* Milestone Status Pill Badge */}
            <g transform="translate(420, 216)" textAnchor="middle">
              <rect
                ref={timerBadgeBg}
                x="-64"
                y="-9"
                width="128"
                height="18"
                rx="4"
                fill="#131924"
                stroke="rgba(255, 255, 255, 0.2)"
                strokeWidth="0.8"
              />
              <text
                ref={timerBadge}
                x="0"
                y="3.5"
                textAnchor="middle"
                fontSize="10"
                fontWeight="700"
                fill="#94a3b8"
                fontFamily="'Chakra Petch', sans-serif"
                letterSpacing="0.4"
              >
                TARGET 0–{activeTarget} KM/H
              </text>
            </g>
          </g>

          {/* Vertical Traction / Throttle Level Bar */}
          <g transform="translate(496, 134)">
            {/* Outer Container Pill */}
            <rect x="0" y="0" width="12" height="54" rx="3.5" fill="#131822" stroke="rgba(255, 255, 255, 0.45)" strokeWidth="1" />
            {/* Dynamic White Fill Bar */}
            <rect ref={gBarFill} x="1.5" y="48" width="9" height="4" rx="2" fill="#ffffff" />
            {/* Stability Icon Underneath: )|( */}
            <text x="6" y="66" textAnchor="middle" fontSize="10" fontWeight="700" fill="#94a3b8" fontFamily="'Chakra Petch', sans-serif">
              )|(
            </text>
          </g>
        </g>

        {/* Chevron bracket between Center and Right */}
        <g stroke="rgba(255, 255, 255, 0.35)" strokeWidth="1.5" fill="none">
          <polyline points="592,130 598,140 592,150" />
          <line x1="584" y1="125" x2="584" y2="155" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="1" />
        </g>

        {/* ============================================================ */}
        {/* 3. RIGHT INSTRUMENT CLUSTER: TACHOMETER (0 - 8 x1000 RPM)   */}
        {/* ============================================================ */}
        <g id="gt7Tachometer">
          {/* Subtle dark glass backing */}
          <circle cx="700" cy="140" r="95" fill="rgba(16, 20, 27, 0.65)" stroke="rgba(255, 255, 255, 0.12)" strokeWidth="1" />

          {/* Outer Base Arc */}
          <path
            d="M 632.8 207.2 A 95 95 0 1 1 767.2 207.2"
            fill="none"
            stroke="rgba(255, 255, 255, 0.3)"
            strokeWidth="2"
            strokeLinecap="round"
          />

          {/* Redline Arc (From 6.0 to 8.0 RPM on outer rim radius 95) */}
          <path
            d="M 787.8 103.6 A 95 95 0 0 1 767.2 207.2"
            fill="none"
            stroke="#ff1a2a"
            strokeWidth="4"
            strokeLinecap="round"
            filter="url(#gt7GlowRed)"
          />

          {/* Tachometer Ticks */}
            <line x1="644.8" y1="195.2" x2="635.7" y2="204.3" stroke="#ffffff" strokeWidth="2.2" opacity="1" />
            <line x1="633.2" y1="192.6" x2="628.5" y2="196.3" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="627.5" y1="184.4" x2="622.4" y2="187.5" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="622.8" y1="175.6" x2="617.4" y2="178.1" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="619.2" y1="166.3" x2="613.5" y2="168.1" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="623.5" y1="155.2" x2="610.7" y2="157.8" stroke="#ffffff" strokeWidth="2.2" opacity="1" />
            <line x1="615.3" y1="146.7" x2="609.3" y2="147.1" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="615.1" y1="136.7" x2="609.1" y2="136.4" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="616" y1="126.7" x2="610.1" y2="125.8" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="618.2" y1="116.9" x2="612.4" y2="115.3" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="627.9" y1="110.2" x2="615.9" y2="105.2" stroke="#ffffff" strokeWidth="2.2" opacity="1" />
            <line x1="625.8" y1="98.5" x2="620.6" y2="95.5" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="631.2" y1="90" x2="626.4" y2="86.5" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="637.6" y1="82.3" x2="633.2" y2="78.2" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="644.8" y1="75.4" x2="640.9" y2="70.8" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="656.7" y1="75.1" x2="649.4" y2="64.3" stroke="#ffffff" strokeWidth="2.2" opacity="1" />
            <line x1="661.4" y1="64.3" x2="658.7" y2="58.9" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="670.6" y1="60.3" x2="668.5" y2="54.6" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="680.2" y1="57.3" x2="678.8" y2="51.5" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="690" y1="55.6" x2="689.3" y2="49.6" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="700" y1="62" x2="700" y2="49" stroke="#ffffff" strokeWidth="2.2" opacity="1" />
            <line x1="710" y1="55.6" x2="710.7" y2="49.6" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="719.8" y1="57.3" x2="721.2" y2="51.5" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="729.4" y1="60.3" x2="731.5" y2="54.6" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="738.6" y1="64.3" x2="741.3" y2="58.9" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="743.3" y1="75.1" x2="750.6" y2="64.3" stroke="#ffffff" strokeWidth="2.2" opacity="1" />
            <line x1="755.2" y1="75.4" x2="759.1" y2="70.8" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="762.4" y1="82.3" x2="766.8" y2="78.2" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="768.8" y1="90" x2="773.6" y2="86.5" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="774.2" y1="98.5" x2="779.4" y2="95.5" stroke="#ffffff" strokeWidth="1" opacity="0.65" />
            <line x1="772.1" y1="110.2" x2="784.1" y2="105.2" stroke="#ff1a2a" strokeWidth="2.2" opacity="1" />
            <line x1="781.8" y1="116.9" x2="787.6" y2="115.3" stroke="#ff1a2a" strokeWidth="1" opacity="0.65" />
            <line x1="784" y1="126.7" x2="789.9" y2="125.8" stroke="#ff1a2a" strokeWidth="1" opacity="0.65" />
            <line x1="784.9" y1="136.7" x2="790.9" y2="136.4" stroke="#ff1a2a" strokeWidth="1" opacity="0.65" />
            <line x1="784.7" y1="146.7" x2="790.7" y2="147.1" stroke="#ff1a2a" strokeWidth="1" opacity="0.65" />
            <line x1="776.5" y1="155.2" x2="789.3" y2="157.8" stroke="#ff1a2a" strokeWidth="2.2" opacity="1" />
            <line x1="780.8" y1="166.3" x2="786.5" y2="168.1" stroke="#ff1a2a" strokeWidth="1" opacity="0.65" />
            <line x1="777.2" y1="175.6" x2="782.6" y2="178.1" stroke="#ff1a2a" strokeWidth="1" opacity="0.65" />
            <line x1="772.5" y1="184.4" x2="777.6" y2="187.5" stroke="#ff1a2a" strokeWidth="1" opacity="0.65" />
            <line x1="766.8" y1="192.6" x2="771.5" y2="196.3" stroke="#ff1a2a" strokeWidth="1" opacity="0.65" />
            <line x1="755.2" y1="195.2" x2="764.3" y2="204.3" stroke="#ff1a2a" strokeWidth="2.2" opacity="1" />

          {/* Tachometer Numbers (0, 1, 2, 3, 4, 5, 6, 7, 8) */}
            <text x="651.9" y="192.1" textAnchor="middle" fontSize="11" fontWeight="700" fill="#ffffff" fontFamily="'Chakra Petch', sans-serif">0</text>
            <text x="633.3" y="157.3" textAnchor="middle" fontSize="11" fontWeight="700" fill="#ffffff" fontFamily="'Chakra Petch', sans-serif">1</text>
            <text x="637.2" y="118" textAnchor="middle" fontSize="11" fontWeight="700" fill="#ffffff" fontFamily="'Chakra Petch', sans-serif">2</text>
            <text x="662.2" y="87.5" textAnchor="middle" fontSize="11" fontWeight="700" fill="#ffffff" fontFamily="'Chakra Petch', sans-serif">3</text>
            <text x="700" y="76" textAnchor="middle" fontSize="11" fontWeight="700" fill="#ffffff" fontFamily="'Chakra Petch', sans-serif">4</text>
            <text x="737.8" y="87.5" textAnchor="middle" fontSize="11" fontWeight="700" fill="#ffffff" fontFamily="'Chakra Petch', sans-serif">5</text>
            <text x="762.8" y="118" textAnchor="middle" fontSize="11" fontWeight="700" fill="#ff1a2a" fontFamily="'Chakra Petch', sans-serif">6</text>
            <text x="766.7" y="157.3" textAnchor="middle" fontSize="11" fontWeight="700" fill="#ff1a2a" fontFamily="'Chakra Petch', sans-serif">7</text>
            <text x="748.1" y="192.1" textAnchor="middle" fontSize="11" fontWeight="700" fill="#ff1a2a" fontFamily="'Chakra Petch', sans-serif">8</text>

          {/* Label: x1000rpm */}
          <text x="700" y="88" textAnchor="middle" fontSize="10.5" fontWeight="600" fill="#cbd5e1" fontFamily="'Chakra Petch', sans-serif">
            x1000rpm
          </text>

          {/* Headlight Icon: D / beam */}
          <g transform="translate(668, 128)" stroke="rgba(255, 255, 255, 0.45)" strokeWidth="1" fill="none">
            <path d="M 0 -7 A 7 7 0 0 1 0 7 Z" />
            <line x1="-3" y1="-5" x2="-8" y2="-7" />
            <line x1="-3" y1="-2" x2="-8" y2="-3" />
            <line x1="-3" y1="2" x2="-8" y2="3" />
            <line x1="-3" y1="5" x2="-8" y2="7" />
          </g>

          {/* Turbo Boost / Power Sub-Dial (-1 to 2 bar / x100 kPa) */}
          <g id="gt7TurboSubdial">
            <path
              d="M 678 170 A 22 22 0 0 1 722 170"
              fill="none"
              stroke="rgba(255, 255, 255, 0.25)"
              strokeWidth="1.5"
            />
            <line x1="684" y1="170" x2="679" y2="170" stroke="#94a3b8" strokeWidth="1" />
            <line x1="686.1" y1="162" x2="681.8" y2="159.5" stroke="#94a3b8" strokeWidth="1" />
            <line x1="692" y1="156.1" x2="689.5" y2="151.8" stroke="#94a3b8" strokeWidth="1" />
            <line x1="700" y1="154" x2="700" y2="149" stroke="#94a3b8" strokeWidth="1" />
            <line x1="708" y1="156.1" x2="710.5" y2="151.8" stroke="#94a3b8" strokeWidth="1" />
            <line x1="713.9" y1="162" x2="718.2" y2="159.5" stroke="#94a3b8" strokeWidth="1" />
            <line x1="716" y1="170" x2="721" y2="170" stroke="#94a3b8" strokeWidth="1" />

            {/* Scale numbers: -1, 0, 1, 2 */}
            <text x="674" y="178" textAnchor="middle" fontSize="7.5" fontWeight="700" fill="#94a3b8" fontFamily="'Chakra Petch', sans-serif">-1</text>
            <text x="682" y="156" textAnchor="middle" fontSize="7.5" fontWeight="700" fill="#94a3b8" fontFamily="'Chakra Petch', sans-serif">0</text>
            <text x="700" y="146" textAnchor="middle" fontSize="7.5" fontWeight="700" fill="#94a3b8" fontFamily="'Chakra Petch', sans-serif">1</text>
            <text x="724" y="160" textAnchor="middle" fontSize="7.5" fontWeight="700" fill="#94a3b8" fontFamily="'Chakra Petch', sans-serif">2</text>

            {/* Label: x100 kPa */}
            <text x="700" y="174" textAnchor="middle" fontSize="7.5" fontWeight="700" fill="#94a3b8" fontFamily="'Chakra Petch', sans-serif">
              x100
            </text>
            <text x="700" y="182" textAnchor="middle" fontSize="7.5" fontWeight="700" fill="#94a3b8" fontFamily="'Chakra Petch', sans-serif">
              kPa
            </text>

            {/* Dual swirl turbo icon */}
            <circle cx="700" cy="162" r="4.5" fill="none" stroke="#94a3b8" strokeWidth="1" strokeDasharray="6 3" />

            {/* Dynamic Sub-needle */}
            <g ref={needlePower} transform="translate(700, 170) rotate(-90)">
              <line x1="0" y1="2" x2="0" y2="-17" stroke="#ffffff" strokeWidth="1.2" strokeLinecap="round" />
            </g>
          </g>

          {/* White Tapered Tachometer Needle */}
          <g ref={needleRpm} transform="translate(700, 140) rotate(-135)">
            <polygon points="-3,10 3,10 0.8,-88 -0.8,-88" fill="#ffffff" />
            <line x1="0" y1="8" x2="0" y2="-86" stroke="#ff1a2a" strokeWidth="0.8" />
          </g>

          {/* Center Hub */}
          <circle cx="700" cy="140" r="16" fill="#1b212d" stroke="#334155" strokeWidth="1.5" />
          <circle cx="700" cy="140" r="10" fill="#0d1117" />
          <circle cx="700" cy="140" r="4" fill="#ff1a2a" filter="url(#gt7GlowRed)" />
        </g>
      </svg>

      {/* Floating Action Controls & Threshold Selectors */}
      <div className="mt-2 flex w-full max-w-[620px] items-center justify-between gap-3 px-2">
        <button
          type="button"
          onClick={action.run}
          disabled={!launch}
          className={`flex shrink-0 items-center gap-2 rounded-full bg-neutral-900/80 px-4 py-2 text-[12px] font-semibold text-white backdrop-blur-md ring-1 ring-white/15 shadow-lg transition-all hover:bg-neutral-800 hover:ring-cyan-400 active:scale-95 disabled:opacity-40 cursor-pointer ${FOCUS}`}
        >
          <span
            className={`inline-block h-2 w-2 rounded-full transition-colors ${
              playing ? 'bg-amber-400 animate-pulse' : run === 'done' ? 'bg-cyan-400' : 'bg-emerald-400'
            }`}
          />
          <span className="font-['Chakra_Petch',sans-serif] tracking-wide">{action.label}</span>
        </button>

        <div className="flex flex-wrap items-center justify-end gap-1.5">
          {chips.map((chip, i) =>
            hasMultipleMarks ? (
              <button
                key={chip.key}
                type="button"
                onClick={chip.select}
                className={`group flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[11px] backdrop-blur-md transition-all cursor-pointer font-['Chakra_Petch',sans-serif] ${FOCUS} ${
                  chip.selected
                    ? 'bg-cyan-500/20 text-cyan-200 ring-1 ring-cyan-400 font-bold shadow-[0_0_14px_rgba(0,229,255,0.3)]'
                    : 'bg-neutral-900/60 text-neutral-300 ring-1 ring-white/10 hover:bg-neutral-800/80 hover:text-white'
                }`}
                title={chip.title}
              >
                <span
                  ref={(el) => {
                    marks.current[i] = el;
                  }}
                  data-reached="false"
                  className="transition-colors data-[reached=true]:text-emerald-400 data-[reached=true]:font-bold"
                >
                  {chip.label}
                </span>
                <span className={chip.selected ? 'text-white' : 'text-neutral-400 font-normal'}>
                  {chip.time.toFixed(2)}s{chip.published ? '' : '*'}
                </span>
              </button>
            ) : (
              <div
                key={chip.key}
                title={chip.title}
                className="flex items-center gap-1.5 rounded-full bg-neutral-900/60 px-3 py-1.5 text-[11px] text-neutral-300 ring-1 ring-white/10 backdrop-blur-md font-['Chakra_Petch',sans-serif]"
              >
                <span
                  ref={(el) => {
                    marks.current[i] = el;
                  }}
                  data-reached="false"
                  className="data-[reached=true]:text-emerald-400 data-[reached=true]:font-semibold"
                >
                  {chip.label} km/h
                </span>
                <span className="text-white font-medium">
                  {chip.time.toFixed(2)}s{chip.published ? '' : '*'}
                </span>
              </div>
            ),
          )}
        </div>
      </div>
    </div>
  );
}
