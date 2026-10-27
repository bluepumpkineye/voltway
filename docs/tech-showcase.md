# The Tech tab: demonstrating what a car's technology does

The showroom's sixth tab (`/showroom/[slug]?tab=tech&demo=<id>&device=<phone|dashboard>`). Each car lists
demonstrations (`Vehicle.tech`); the tab plays one at a time, started from a device the visitor holds
as the owner would (the maker's phone app, or the car's own screen), on a clock they can also pause,
replay, scrub and slow down. Every demonstration is a **simulation built from the maker's published
figures**, never its footage, and says so on screen.

The plan and the research behind it were approved on 2026-10-08 (kept outside the repo).
Status: Phase 1 (the motion rig and the tab) and Phase 2 (the Luxeed RX's "Park from your phone", with
its two devices) are built. Phase 3 (the mechanism demos) is under way, each behind its own source check and
the owner's approval of its reference photos: 3a, the 7X's Magic Carpet, is built and approved (section 9); 3b,
the SU7's aero and launch, has its sources and board (section 10): the owner accepts a launch with no launch screen;
3c, the 7X's fast charge, is built and approved (section 11); 3d (the RX's sensors, section 12) and the RX's swivel
screen and BOOST (3e, section 13) were approved by the owner on 2026-10-12 and are built (BOOST's enlarged screen, 2026-10-13);
the SU7's welcome sequence has a source (Xiaomi's page: the cluster flips up at start-up) and a board waiting for approval, the
7X's failed its source check, so it is not built (section 13); the SU7's diffuser is left out (section 10). Phase 4 (section 14) gives the Denza Z9 and the
Xpeng G9L their chassis demos (crab walk, compass turn, e³ parking, a rear-steered U-turn, nose-in parking) on a new street
environment that the parking lot shares. The camera on the Tech tab is free:
it orbits the stage's middle, zooms as close as on any tab and looks straight down (section 4).

## 1. What a demonstration is

A `TechDemoSpec` (`src/data/vehicles/schema.ts`) is what the visitor reads:

| Field | Meaning |
|-------|---------|
| `id`, `title`, `blurb` | the chip, and one line about what is shown |
| `driver` | the motion, a key of `DRIVERS` in `src/lib/tech/demos.ts` |
| `devices[]` | where it starts from: `phone` and/or `dashboard`; the first is shown to begin with. None: the playback bar alone (a rig test) |
| `claims[]` | every published number on screen, each with its source link |
| `simulated` | what is illustrative: "A simulation: the path, the speeds and the screens are ours..." |
| `devOnly` | offered only while developing (a test of the rig, left out of a production build) |

The tab hides itself for a car with no visible demonstration, and shows a notice for a car whose
model has no per-corner wheels yet.

**Rules.** A claim ships only with a source we have read (a maker page, Autohome's equipment
table, or press we name). Marketing figures differ by trim and generation: say which. Never invent
a feature. New geometry (a wing actuator, a plug, a swap station) gets reference photos approved
before modelling, as for openings and wheels. A device screen is rebuilt in code from the maker's
published screens (our own icons and art, text in English), after the owner has approved the reference
board; say on screen where a screen was drawn from a description and not a still.

## 2. How the car moves

Two routes, used together:

- **Code-driven** (`src/lib/tech/kinematics.ts`): anything that follows input or must scale across
  cars. A plan is a list of rigid motions, a translation (a straight line, a crab walk) or a
  rotation about a point (an arc, a compass turn, a four-wheel-steer turn). A wheel that rolls
  without sliding points along its own contact velocity, so every steering mode falls out of one
  rule. Checked against analytic Ackermann angles and rolled distance. The same plan drives any
  car that has a rig, from its measured wheelbase and track.
- **Baked Blender clips** (planned, Phase 3): mechanisms with authored timing (a wing, a charge
  flap and plug, a swap station). One glTF animation per demo, 30 fps, named `tech.<demo>`, cue
  points in a `*.cues.json` sidecar (glTF has no timeline markers). Constraints and drivers are
  sampled by the exporter; shader-node animation, particles and simulations are not carried.

## 3. The rig contract (Blender to web)

Everything that moves is its own glTF node with its origin at the pivot, as the doors are.

**Wheels** (done for the RX; the SU7 and 7X follow when their demos start). The export ships each
wheel design as one node per corner, `<Car>_<Design>_Wheels_<FL|FR|RL|RR>`, and each corner's
brake caliper as `<Car>_<Design>_Wheels_Caliper_<tag>` (`export_rx.split_wheels`, after the per-design
ambient-occlusion bake). Origin at the hub centre, local frame the build's wheel frame, so a node
spins about its axle. The caliper steers with the wheel and does not spin.

At load the viewer rebuilds a fresh clone of the exterior (`prepareRig`, `src/lib/tech/rig.ts`):

```
root
|- Sprung          every other node: body, doors, glass, the bonnet's struts
`- Unsprung
   `- <Car>_<Design>_Wheels            the node the Wheels tab shows and hides
      `- <Car>_<Design>_Wheels_steer_<tag>   yaws about the hub
         |- the wheel node                    spins about its axle
         `- the caliper node
```

so the Wheels tab, which addresses `<Car>_<Design>_Wheels` by name, keeps working. A car whose
wheels are still one merged node is simply not rigged. The rig also measures the body's extent from
the rear axle (`PreparedRig.body`), which the planners keep clear of obstacles.

**Frames.** The viewer's: +x forward, +y up, +z toward the passenger side. The kinematics' frame is
x forward, y left (y = -z), counter-clockwise from above, so a positive angle turns left. The car's
place on the floor is a `CarRoot` group around the exterior and its baked shadow; the body on its
springs (`heave`, `pitch`, `roll`) is the `Sprung` group.

**One state per car** (`CarRig.state`, like `Hinges` for the openings): position, heading, body
attitude, steer and spin per corner. The `TechDirector` (inside the Canvas) writes it from the
demo's clock every frame and asks for frames only while the clock runs, so an idle showroom still
renders 0 frames (measured on the Tech tab: 0 after it settles, and while paused).

## 4. The demonstration's parts

```
vehicle.tech[] --driver--> DRIVERS[...].build(ctx) --> BuiltDemo { track, stops, autoplay, stage }
                                                          |
   TechDirector (Canvas) --- clock (src/lib/tech/clock.ts) |   stops: the clock halts, waiting for a device
        |  writes the rig every frame                      |
        |  publishes Runtime {stage, sample(t), body} ---> techSession (src/lib/tech/session.ts)
        |  publishes the lot ---> store.techScene ---> TechStage (3D lot: asphalt, bays, neighbours)
        v
   devices (DOM): phone app, car's screen  -- read clock + session, start/pause via src/lib/tech/actions.ts
```

- `src/lib/tech/clock.ts`: the playhead, with **stops** (times a running clock halts at, waiting for the
  visitor) and `legOf` (which stretch of the demo, how far).
- `src/lib/tech/phase.ts`: `parkPhase` turns the clock into what a visitor says: ready, parking, paused,
  parked, leaving, done. Every device reads it, so they always agree.
- `src/lib/tech/actions.ts`: `startDemo`, `pauseDemo`, `resetDemo`. `startDemo` on another tab (the
  cabin's screen) sends the visitor out to the stage and the director plays as soon as it is built
  (`store.startTech` / `techIntent`).
- `src/lib/tech/preview.ts`: the same build, for a screen shown while no demo runs (the cabin's parking
  page, the vehicle page).
- Camera: `techStage` frames the stage circle, `deviceInset` keeps it clear of the devices (a column at the
  right of a wide window, a bar at the bottom of a narrow one) by sliding the picture (a view offset), so the
  visitor orbits about the stage and it stays in the free part of the window; the near plane follows the camera's
  distance (`ShowroomCameraRig`), because the exterior's 3 mm underlays z-fight from 25 m with a 2 cm near plane.
  The visitor's camera is free (2026-10-12; the owner asked for it on the Tech and Dashboard tabs): the `techWide` pose starts at
  the demo's own look but lets them zoom in as close as on any tab (the hero shot's limit, `exteriorFit`), out to 2.2 times the
  fit and from nearly straight above (`TOP_DOWN`) down to the floor, and turn all the way round. A demo with another floor to
  frame (a new centre, radius or look) re-frames the camera even if they had turned it (`ShowroomCameraRig` compares the floor);
  a resize still leaves a turned camera alone. The Dashboard tab's own free camera is `dashFront` and `dashRear`.

## 5. Park from your phone (Luxeed RX)

**The motion** (`src/lib/tech/park.ts`). A perpendicular reverse-in to the empty one of five bays, between
parked cars, and out again. The car stops in the lane just past the bay, heading +x, and reverses along one
arc of 90 degrees about a point on its right (rear-axle radius R = 5.2 m, so the RX's front wheels turn
about 35 and 27 degrees), then straight back; the way out is the same path forward and ends exactly where
it began. Bays are 2.7 m wide and the body keeps 44 cm from its neighbours (the published width, mirrors
folded in as the car does in reverse), the car stops 25 cm inside the bay mouth and 35 cm off its back
line. At the medium parking speed: 18 s in, a stop (the car parked, until the visitor asks), 18 s out.
The planner reports the least clearance (`stage.clearance`) for every car it is built for; the director
logs it in development.

**The stage** (`src/components/viewer/TechStage.tsx`). A canvas-textured patch of asphalt with the bays
and a lane arrow, faded out into the studio's white; wheel stops; and the parked cars: stand-in models of
the other modelled cars (`scripts/make-proxy.mjs`, about 65 KB and 20k triangles each: paint panels, glass,
tyres, rims; Draco), in neutral matte paint on their own baked floor shadows. The stand-ins must not use the
black underlays or the shadow shell (see the script's header).

**The devices** (`src/components/tech/`):

- *Phone* (`phone/HimaApp.tsx`): the maker's HIMA app. The vehicle page (model, range and charge, the
  car, quick controls, climate card you can use, location and battery, then the list with **Remote
  parking** in it; read off the app's own screens) and the remote-parking screen (Bluetooth and system
  check, the live top view, "Start parking in", pause, resume, "Start parking out"). Leaving the screen
  stops a moving car, as the real app does. If remote parking assist is off in the car, the screen says so and
  takes the visitor to the car's settings.
- *Car screen* (`hmi/harmonyos/Park.tsx`): the cockpit's parking page (the 360 camera's "Park" button opens
  it): the top view, a live **rear camera** (`RearView.tsx`: a pinhole projection of the lot, with the
  planned path on the floor), and one button. Settings > Assisted driving > Parking assist opens the
  dialog with the **Remote parking assist** switch and the **Parking speed** (slower, medium, faster); the
  switch gates the phone, the speed sets how briskly the car moves (`PARK_MOTION`).
- Start from the cabin: the Interior tab's screen has the same page; "Start parking in" takes the visitor to
  the stage and the car parks. On the vehicle page the page offers a link to the showroom instead.
- A wide window shows the devices in a column at the right (a switch above them, a line of guidance under);
  a narrow one opens the phone nearly full screen and shrinks it to a bar of controls while the car moves.

**Sources** (also on the board `blender/reference/luxeed-rx/tech/_approval_boards/T1_*.jpg`, with
`_sources.md`). Shown with the demo: remote parking is standard on the RX (Autohome's table); Huawei's
remote parking assist is driven from the phone app and copes with extremely narrow slots, in over 160
scenarios (快科技, 2024-06-05, stated for the AITO M9, the same system); the HIMA app's remote control
module lists remote parking (快科技, 2025-02-28). The step-by-step flow (enable it in the car, choose the
slot, get out, connect, "start parking in", the pause conditions) is from an Autohome Q&A about the AITO M7
that says it contains AI-generated content, so it shapes the screens but is not quoted on screen. No still
of the app's remote-parking page was found; it is drawn from those steps in the vehicle page's style.

## 6. Adding a demonstration

1. Find the published claims and their sources (read the maker's page and Autohome's equipment
   table; mark anything from a search summary "verify" and do not show it). Find the screens the
   devices need and put them on a board for the owner to approve.
2. Add a driver to `DRIVERS` (a plan from the car's `Layout` and `body`, with stops where the visitor
   starts the next stretch; for a mechanism, a clip name).
3. Add a `TechDemoSpec` to the car's data file with its claims, sources, `devices` and the `simulated` note.
4. Build the device screens from the demo's phase (`parkPhase`-style) and start them with `startDemo`.
5. Run it in the Tech tab, then check: wheel angles against Ackermann, rolled distance against
   wheel circumference, `stage.clearance`, no clipping of the tyre against the hull at the demo's widest
   steer, idle frames 0, tsc, eslint and the build (in a copy of the project if another server shares `.next`).

Development handle: `window.__tech` = `{ rig, clock, built, invalidate, session }` (never set in a
production build). `built.track.sample(t)` is the plan at time t; `window.__store` is the zustand store.

## 7. Verified equipment (Autohome tables, read 2026-10-08)

Read in the browser pane (the tables are built by script): `car.autohome.com.cn/config/series/8684.html`
(Luxeed RX), `/series/7777.html` (Zeekr 7X), `/spec/70545.html` (SU7 Ultra). ● standard, ○ option.

| | SU7 Ultra | Luxeed RX | Zeekr 7X |
|---|---|---|---|
| Remote parking / assisted parking | ● / ● | ● / ● | ● / ● |
| Memory parking | ○ | ○ | ○ |
| Lidar | 1 Hesai AT128 (128 line, 200 m) | 1 (Max) or 4, one 896-line (Ultra) | 1 Hesai |
| Driver-assist system | Xiaomi HAD, 2x Orin, L2 | Qiankun ADS (Autohome lists ADS 5) | ZEEKR AD, Thor-U, L2 |
| Electric spoiler | ● in Autohome's table (absent on the Nurburgring Limited); **not on the maker's page**, which lists a fixed wing, a hand-adjusted wing and an active diffuser (section 10) | | |
| Active closing grille | ● | ● | ● |
| Power-closing doors / frameless doors | ● / ● | no / ● | ● / ● |
| Hidden electric handles | not checked | not checked | ● |
| Power tailgate (position memory) | ● (●) | ● (●), kick-sensing | ● (●) |
| Electric folding mirrors | ● (tilt in reverse) | ● (tilt in reverse) | ● |
| V2L | 3.5 kW | 6 kW | 6 kW |
| HUD | 56 in | 26 in (Ultra) | 36.21 in |
| 540-degree transparent chassis | ● | ● | ● |
| Air suspension (chambers) | dual-chamber | dual-chamber | single-chamber row; air + electromagnetic on the 4WD Ultra (verify) |

Unverified, so not for display: Huawei's slot-type list (parallel, perpendicular, angled, unmarked, very
narrow), the Denza Z9 GT's rear-wheel behaviour in the crab walk and its 11 cm parking margin, the millimetres of
each of the 7X's five ride heights, a 30 m road preview at up to 80 km/h for the Magic Carpet (its only source, a Sina
article, is gone). Settled in Phase 3: the SU7's wing is fixed or hand-adjusted and its active diffuser has two
positions, 0 and 32 degrees (maker's page); the 7X has five named heights over about 70 mm.

## 8. Status

| Piece | State |
|-------|-------|
| `src/lib/tech/kinematics.ts` | built; Ackermann angles and no-slip rolling checked in the live scene |
| `src/lib/tech/{rig,clock,demos,park,phase,session,actions,preview}.ts`, `viewer/{TechDirector,TechStage,techRig}.tsx` | built |
| Tech tab, chips, play / replay / scrub / speed (with the stop marked), facts panel | built (`showroom/Tech.tsx`) |
| RX per-corner wheel nodes (`export_rx.split_wheels`, `export_rx.web()`) | built, GLB re-exported |
| RX demos: Park from your phone; rig test (dev only) | built |
| Phone app, car's parking page, rear camera, Parking assist dialog, cabin start, vehicle-page link | built (tsc, eslint; production build in a copy) |
| Neighbour stand-ins (`scripts/make-proxy.mjs`, `public/models/*-proxy.glb`) | built for all three cars |
| Reference board for the phone and car screens | sent to the owner, awaiting approval (`blender/reference/luxeed-rx/tech`) |
| Idle frames 0 | measured on the Tech tab (0 once settled and while paused) |
| Frame time while playing | not measured (the browser pane was hidden) |
| Wheelhouse clearance at full lock | looked at at 35 degrees front lock (no clipping seen); not measured by raycast |
| The 7X's per-corner wheel nodes (`export_zx.split_wheels`, `export_zx.web()`) | built, GLB re-exported 2026-10-12 (hubs at wheelbase 2.926 m, track 1.65 m, radius 0.365 m) |
| Magic Carpet scene: ride model, wheel lift, rolling road, humps, both suspensions, chart | built, played through (real time), idle frames 0, wheelhouse clearance seen at the worst case |
| Magic Carpet screens (ZEEKR OS Quick settings, Driving with Suspension easy entry), device column and seat-belt control | built from board T3a, approved by the owner 2026-10-12; tsc, eslint, production build in a copy, looked at on a wide and a phone-sized window |
| Launch demo on the SU7 (`launch.ts`, `showroom/Launch.tsx`) and the browser-side wheel split (`splitWheels.ts`) | built; the owner accepts a launch with no launch screen; tsc, eslint, production build in a copy, looked at on a wide and a phone-sized window |
| 7X charge flap and port in the model (`zx_charge.py`, `Zeekr7X_ChargeFlap` / `Zeekr7X_ChargePort`), GLB re-exported 2026-10-12 | built from the photographs of board T3c, looked at in Cycles and in the viewer; the pocket's depth is ours |
| Fast-charge demo (`charge.ts`, `viewer/TechCharge.tsx`, `showroom/Charge.tsx`, the car's Vehicle charging page and Charge port cover tile) | built, approved by the owner (3c); flap, gun, readout and flow looked at; see section 11 |
| The park demo on the SU7 | its wheels are now cut in the browser (`splitWheels.ts`): the planner takes the car's own layout, body and published width; not offered yet |
| Free camera on the Tech tab (`showroom/anchors.ts` `techWide`, `ShowroomCameraRig.tsx`) | built 2026-10-12: zoom as close as the other tabs, up to 2.2 times the fit, from straight above to the floor; a new stage re-frames the camera |
| Autonomous Drive (was "What the car sees"; `sensors.ts`, `viewer/TechSensors.tsx`, `showroom/Sensors.tsx`, `layers.ts`; spec `Vehicle.sensors`) | rebuilt 2026-10-17 as a three-lane road with traffic (section 12), on the RX, the SU7 and the 06T; tsc, eslint, played through, idle frames 0, 60 fps in the pane; not yet seen by the owner |
| SU7 parking assist (`park.ts` `search`, `viewer/TechParkAssist.tsx`, `showroom/ParkAssist.tsx`) | built 2026-10-17 from Xiaomi's own animation (section 16); not yet seen by the owner |
| Swivel screen (`swivel.ts`, `viewer/ScreenSwivel.tsx`, `hmi/harmonyos/ScreenDirection.tsx`, `showroom/Swivel.tsx`; spec `Vehicle.swivel`) | built (3e, approved); the frame is cut out of the cabin's merged mesh in the browser, no re-export; see section 13 |
| BOOST demo (`boost.ts`, `viewer/BoostKnob.tsx`, `hmi/harmonyos/Boost.tsx`, `showroom/Boost.tsx`; spec `Vehicle.boost`) | built (3e, approved); the screen it shows is a stand-in; see section 13 |
| Welcome sequence of the SU7 (the cluster flips up at start-up) | source found (Xiaomi's page) and a reference board made 2026-10-13; waiting for the owner's approval of the photographs (section 13) |
| Welcome sequence of the 7X | NOT built: no published sequence found (section 13) |
| Street environment (`street.ts`, `viewer/TechStreet.tsx`), the lot's dressing (`dressLot`), proxies for the Z9 and the G9L | built; see section 14 |
| Z9: crab walk, compass turn, e³ parking; G9L: rear-wheel-steering U-turn, nose-in parking (`chassis.ts`, `hmi/chassis.tsx`, `showroom/Chassis.tsx`) | built, played through, idle frames 0, wheelhouse probe clean; not yet seen by the owner (section 14) |
| Drive tab: one scenario per car (`Vehicle.drive`, `drive-setup.ts`, `drive-run.ts`, `showroom/Drive.tsx`, `scripts/tech-tools/drive-test.mjs`) | built 2026-10-27, played through in the browser pane, tsc and eslint clean; not yet seen by the owner (section 19) |

## 9. Magic Carpet (Zeekr 7X), Phase 3a

A straight run at 16 km/h over three rubber speed humps, with the body riding on either a passive suspension or
the Magic Carpet, the visitor choosing the ride height. Registered in `zeekr-7x.ts` as `magic-carpet`, started from
the car's own screen (`devices: ['dashboard']`).

**Published** (each with its link on the demo's facts panel): the package is air suspension, CCD
electromagnetic dampers and the smart Magic Carpet, whose perception system (front camera and lidar) reads
the road ahead; the 4WD 7X carries it and the rear-drive ones can add it (CNY 20,000 in Autohome's table);
five ride heights that follow speed, geofencing, 230 mm clearance at most (Xinhua, 2025-11-03); about 70 mm of
adjustment (Tencent News, 2024-09-22); the car's screen names the five heights Very high, High, Standard, Low
and Very low and offers "Suspension easy entry" (Autohome photos of the 7X's own ZEEKR OS, board T3a).
**Ours**, said on screen: the humps (5 cm x 40 cm, 3.6 m apart, a typical rubber product; the Chinese standard
GA/T 487-2020 was not read), the speed, the body's motion, five equal steps over the 70 mm.

**The ride** (`src/lib/tech/ride.ts`, no imports, run it with Node): a half car (heave and pitch) on a spring and
a damper per axle, the wheels following the road through the tyre's envelope. Passive: 1.25 Hz bounce, damping 0.22.
Magic Carpet: softer air springs, light axle dampers and an actuator (limited to 4 kN an axle) that cancels
62 % of the force the road puts in and damps the body against the sky. Over the run the passive body moves 2.7 cm
(0.7 degrees of pitch) and the carpet 0.4 cm. The hump spacing is the body's bounce period at 16 km/h, the
worst case for a passive car.

**The scene.** The car stays on the spot and the road rolls under it (`RigState.scroll`,
`CarRig.attachRoad`): the camera and the baked shadow need no following. `carpet.ts` plans the run (a `Track` of 30 m
and both suspensions' rides); `demos.ts` hands it to the director as `BuiltDemo.treadmill`; the director writes
`RigState.heave/pitch/lift` (each hub's rise over the road) and `ride` (the ride height, eased as an air suspension
is); `viewer/TechRoad.tsx` draws the asphalt strip (dashed edge lines and tar joints, so the roll is seen) and the
humps, from the profile the ride model drives its wheels over. `showroom/Ride.tsx` is the showroom's own control
(not the car's): Magic Carpet / Passive, the ride-height chips while no screen offers them, and a chart of the body's
height through the run with both suspensions and the playhead. Store: `rideLevel` (0 to 4, 2 is Standard) and `carpetOn`.

**Checked** (2026-10-12): per-corner hubs; the run plays in real time and ends with the road 30 m on; wheel lift
peaks at 49.6 mm; at Very low with the 5 cm hump the tyre stays clear of the fender paint (looked at in a
full-resolution capture; the model has no wheelhouse liner, so nothing else can clip); idle frames 0 before and after.
**The car's screen** (`hmi/zeekros/Pages.tsx`, rebuilt from board T3a): Settings opens on Quick settings, the drive
modes in a row and the five heights (Very high ... Very low) in a column beside the car in side view (`public/hmi/zeekr-7x/car-side.webp`, rendered
by `export_zx.hmi_side_art`); Driving carries Suspension easy entry. The height is the store's `rideLevel`, the mode
`modeId`, so a tap on the screen moves the 3D car (air suspension easing, about a second). `TechDevices` has a carpet kit:
the screen opens on Settings (`homeScreen`), one Drive / Pause / Resume / Drive again button (`runPhase` in `phase.ts`),
and on a phone-sized window the slim bar goes to the top, because the chart panel stands where it sits for parking.
**Suspension easy entry:** with the switch on and the seat belt unbuckled (the showroom's own Unbuckle belt button, shown
while the car stands) the body kneels to Very low; the belt buckles again when the car drives.
**Not yet:** a lidar scan drawn on the road (an illustration); the existing 7X skin's other pages are unchanged.

## 10. SU7 Ultra aero and launch, Phase 3b

**Sources** (read on the maker's own page, `https://www.xiaomiev.com/ultra`, 2026-10-12; full table in
`blender/reference/xiaomi-su7-ultra/tech/_sources.md`). The wing does not move: the kit is "U-shaped air blades
and a big front lip", an **active rear diffuser that supports 0 and 32 degrees (adaptive)**, a **fixed** carbon wing
(1560 mm span, 240 mm chord) and a carbon wing with **three positions set by hand with tools** (176 kg of downforce,
whole car). 285 kg is the maximum, measured at 350 km/h by Xiaomi's lab. The 2024 launch coverage said the diffuser
went 0 to 16 degrees; the page now says 32. No switching speed is published. "2 seconds to 100": the footnote says the
figure excludes rollout and needs Pirelli P Zero Trofeo RS semi-slick tyres. CnEVPost's launch report (read in full on
2026-10-12) gives **1.98 s to 100 km/h and 6.09 s to 200 km/h**, three motors, 1,138 kW (1,548 PS), with no footnote.
The launch lock (300 km driven, a safety test, a qualifying lap: three press accounts that disagree) is not shown.
Reference: every photo of the diffuser shows it stowed (Autohome underside shots; the maker's video is stowed too);
there is no launch screen in any photo; the wheel's red button reads DRIVE MODE.

**The diffuser is not built.** A deployed diffuser would be a plain pivot at the panel's forward edge turned by the
published 32 degrees, with no photograph of the deployed state to check it against. The owner (2026-10-12) accepted a
launch with no launch screen, and on 2026-10-13 said to leave the diffuser out for now: it stays out until a photograph
of it deployed exists.

**The launch demo** (`launch` on the SU7, `src/lib/tech/launch.ts`, no imports of values, run it with Node): a
standing start on a road that rolls under the car (the same treadmill as the Magic Carpet). The pull is a plateau
that builds in 0.15 s and reaches 100 km/h exactly at the published 1.98 s (1.49 g), then falls with speed
(a = a0 (V100 / v)^p, p solved so that 200 km/h comes at the published 6.09 s, 0.4 g by then), eases off over
0.5 s and coasts 0.9 s: 8.1 s in all, 290 m of road, 204 km/h at the end. Ours: the shape of the pull, the body's
pitch (nose up 0.9 degrees per g through a 1.5 Hz, 0.35 damped response: 1.3 degrees at the plateau, 1.7 at the
overshoot), the tyres' slip (16 % at rest, fading with speed, and a short spin-up before the car moves). The wheels
are drawn turning at three turns a second at most (a wheel at the road's speed strobes at 60 frames a second); the
slip is seen in the first half second. There is no device: the demo starts from `showroom/Launch.tsx` (a Launch /
Pause / Resume / Launch again button, the speed, the pull in g, the stopwatch with both published times lit as they
are passed) and the playback bar. The readout is written to the page every frame by a requestAnimationFrame loop
while it runs, so it is as smooth as the car.

**The rig for a car with merged wheels** (`src/lib/tech/splitWheels.ts`): the SU7's export has one `SU7Ultra_Wheels`
node (a mesh a material, all four wheels in each). Re-exporting it would rebuild the whole body, so the browser cuts
it instead: every triangle goes to the corner it stands at, each corner gets a node at the middle of its tyre (the SU7
measures wheelbase 3.0001 m, radii 0.359 / 0.358 m, as published), calipers (which do not spin) get their own, and
the vertex buffers are shared with the original. It runs for the SU7 in every tab; the park demo could now run on it.

## 11. 7X fast charge, Phase 3c

*Since 2026-10-16 this is the Charging tab, for every car (section 15): the demo is no longer in `Vehicle.tech`, and the Tech tab's devices no longer start it.*

Approved by the owner on 2026-10-12, with two photographs of generic charging connectors for the gun (a white AC
plug with a black head, a blue portable unit): they are AC (Type 2 style) connectors, so they style the gun's shell,
grip and boot, and its face is the 7X's DC inlet the other way round (the owner was told). The demo `fast-charge`
(`zeekr-7x.ts`, `devices: ['dashboard']`, `params.packKwh` 103).

**Published** (read 2026-10-12, `blender/reference/zeekr-7x/tech/_sources.md`): 900 V motors, controllers and thermal
management across the refreshed range, 5.5C or 6C fast charging standard; the 103 kWh 6C Kirin pack at up to 620 kW
and 10 to 80 % in 10 minutes at best (Xinhua, 2025-11-03); the 4WD Ultra we model is a 103 kWh car. The flap's place and
look, the DC and AC sockets, the strip and the caps are the photographs'; the car's own "Charge port cover" tile and
Vehicle charging page are photographed (c10_0041, c10_0101). **Ours**, said on the demo's panel: the curve between the
two published figures (`chargeCurve`: 72 % to 100 % of the peak by 25 % charge, the plateau to 45 %, a taper whose end
power is solved so that 10 to 80 % takes exactly 600 s: 446 kW at 10 %, 620 kW, 192 kW at 80 %; 72.1 kWh added), the
pedestal, the gun and its cable, and the speed of the clock (ten minutes play in fourteen seconds).

**The run** (`src/lib/tech/charge.ts`, no value imports, run it with Node): 24.2 s, one stop. 0.4 s the flap opens (the
director writes the store's `openings.charge`; the hinge eases it; the light strip is lit); 1.4 s the gun leaves
the pedestal's cradle, turns through the car's front (a Catmull-Rom path, the nose swinging from pointing into
the pedestal to pointing into the car) and reaches the approach point 24 cm out at 4.4 s, then pushes in to 5.0 s;
5.4 to 19.4 s charging (the car's screen, the pedestal's screen and the panel read the readout; the director sets the
store's `soc` to the demo's, and puts it back when the demo goes); **stop** at 19.4 s (80 %): the clock waits for
the visitor, "Unplug" on the pill or the Charge port cover tile goes on; the gun is drawn out and goes home by 22.7 s, the
flap shuts at 23.0 s, the run ends at 24.2 s. The car does not move. The port's frame (mouth, outward axis, depth)
is `Vehicle.chargePort`, in the viewer's axes, from `zx_charge.frame()`.

**The props** (`viewer/TechCharge.tsx`): a plain unbranded pedestal ahead of the port on the car's left (x port + 0.55 m,
1.35 m out), a small screen drawn from the readout, a light strip that pulses green while charging, and the gun, built of
primitives (white shell, black head with the DC pins in the inlet's layout, grip with ridges, black boot) with its
cable a tube re-laid every frame between the pedestal's grommet and the grip (it droops, never through the floor).
**The devices:** the car's ZEEKR OS opens on Energy management > Vehicle charging (`hmiScreen: 'charge'`, rebuilt from c10_0101:
the "Charge port cover" tile that starts the demo and, at the stop, sends the gun home; the car with the battery
graphic, the charge limit, the charge left and the range; the schedule rows), and the Home chip "Charge flap" does the same.
Outside the Tech tab the flap is an ordinary opening (`openings.charge`; a tap on it, the chip, Settings > Vehicle).
**Not done:** the flap's arm (it turns about a plain hinge), the warning label's icons, the badge's exact Z, the pocket's depth
and its shape from the side, the AC cap's cord, a second charger style; the phone app has no charging screen in any photograph.

## 12. Autonomous Drive (was "What the car sees"), Phase 3d (2026-10-12), rebuilt 2026-10-17

Approved by the owner with board T3d (`blender/reference/luxeed-rx/tech/sensors`, `_sources.md`). The demo `sensors`
(`luxeed-rx.ts`, no device: the car's screen has no photographed page for it, so it starts from the demo's panel and the
playback bar, as the launch does).

**Published** (the maker's page, Autohome Chejiahao and its configuration table, Huawei's 2026-03-04 lidar release): 38
sensors; on the Ultra trims four lidars, ONE forward 896-line dual-optical-path (wide and tele, independently controlled)
image-grade lidar in the roof housing and THREE high-precision solid-state ones (two at the sides, one at the rear), five
millimetre-wave radars and twelve ultrasonic sensors; a 14 cm box recognised at 120 m; the CAS 5.0 anti-collision system.
**Photographed** (Autohome, the details): the lidar's window in the roof housing beside a pair of cameras, the front fender's
black gill with cameras and a dark slot, a small round sensor in the front corner's lower lip, the camera on the nose, the
mirror's camera, the dual-lens unit under the tail badge, the rear camera. **Not published**, so illustrative and said on the
panel: every field of view and the reach each cone is drawn to (the drawing is 18 m for the wide path, 45 m for the tele,
14 and 12 m for the side and rear lidars, 2.4 m for the ultrasonic ones; the real lidar sees to 120 m), the camera count, and
where the rear solid-state lidar is. The owner did not pick between the two ways to draw the three solid-state lidars, so
the safer one is built: coverage only, from the fender gill (where one secondary source reports the side pair) and from the tail
(where nothing says the rear one is), each marked with a RING, not a dot: a dot is a sensor a photograph shows. The five radars
are not drawn.

**Rebuilt 2026-10-17 (owner: rename it Autonomous Drive and put other cars on three lanes, "like the short clip from Xiaomi's website",
https://www.xiaomiauto.com/global/pilot; the same scene on the SU7).** The pedestrian is gone (nobody crosses an expressway); the demo is
now `sensors` on the RX, the SU7 and, because it uses the same driver, the Avatr 06T's "Huawei Qiankun ADS 3.0" entry (another
session's file, left as it is: only its scene changed). The clip (the page's `highway.mp4`, 5 s, 1920 x 823; frames read in the Browser
pane by seeking the video) shows a top-down, grey, desaturated three-lane road with dashed lane lines and solid edges, grey cars
passing in every lane, and the white SU7 in the middle with a blue forward beam, four diagonal beams from its corners, ripples at the
wheels and a big translucent ring with a grid that grows and fades. We took the look, not the footage.

**The run** (`src/lib/tech/sensors.ts`, no value imports, run it with Node `--experimental-strip-types`; the scratchpad's
`drive-test.mjs` prints the timeline): 19 s, the car on the spot and the road rolling under it, except sideways: the plan's lateral
offset and heading are the car's (`treadmill.lateral`, TechDirector), so it really changes lane. Six traffic cars (`ROLES`: where each
stands and how fast it goes), the other modelled cars' stand-ins in mid greys: the car ahead in the car's own lane (100 km/h, brakes
to 74 from 2.6 s to 6 s, brake lamps on), one that goes by on the left early, one that comes up fast from behind in the left lane
(130 km/h), one in the right lane that the car passes, one that follows it there, one far ahead. The car holds 100 km/h, follows the
one ahead (`aLead`: about 1.5 s of gap, a jerk limit), and when the car ahead is more than 2.5 m/s slower and within 52 m it
indicates left and WAITS until the left lane is clear (`inTheWay`: a car behind must not close within 3.2 s, one ahead must be 12 m
clear), then moves over (a raised cosine over 4 s, the front wheels' angle from the path's curvature, at most 4 degrees of heading)
and overtakes at 112 km/h. Phases: cruising, following, waiting, changing, passing, done. With the traffic as it is the timeline is:
following from 2.6 s, waiting from 4.6 s, the lane change from 8.4 s to 12.4 s, done at about 18.4 s; the closest any two bodies
come is the 1.8 m between neighbouring lanes. All of it is ours and the panel says so.

**The scene** (`viewer/TechSensors.tsx`): `CarCoverage` (a child of the rig's root, in the model's space, so it follows the car's
lane change): a flat sector on the floor for each lidar, fading outward, with its edges and a thin beam that sweeps; where the maker
publishes a field of view (the SU7's Hesai AT128, 120 degrees) one fan of that angle, else the RX's wide and tele paths; four diagonal
beams from the middle of the car for the surround cameras (`spec.surround`, Xiaomi's own look); pulses going out from the car's
outline (ultrasonic); the detection ring (`ScanRing`: two waves out to 34 m over a polar grid, fading, 3.4 s each); dots and rings
where the sensors are. In the road's frame (rolled under the car): the traffic (`useStandIn` in TechStage, the stand-in models in mid
greys, their baked floor shadows, two red bars for brake lamps), corner marks round each car the sensors have in reach (white,
blue for the one being followed, amber for the one in the way of the lane change), the left lane laid out amber then green while the
car means to move into it, and a line from the nose to the tail of the car being followed. The road (`viewer/TechRoad.tsx`,
`Highway`): 3 x 3.75 m lanes, solid edge lines, dashes of 6 m every 15 m and tar joints every 12.5 m that the rig rolls only as far as
their period (`CarRig.attachRoad(g, baseX, period)`), so the strip is 280 m long whatever the run. The panel (`showroom/Sensors.tsx`)
says what the car is doing (an indicator arrow while it means to change lane), the speed, the gap to the car ahead and how many cars
are in reach, with a switch for each group of sensors the car has.

**The SU7's sensors.** Published: one 128-line Hesai lidar of up to 200 m, eleven surround cameras (two 8 MP, nine 3 MP), twelve
ultrasonic sensors, two Orin X (508 TOPS), Xiaomi HAD at level 2, automatic lane change assist and lane centering standard, parking
memory optional (CarNewsChina's parameter table, read 2026-10-17); the lidar is the AT128 (Autohome's table, section 7), whose 120 x
25.4 degree field of view is on Hesai's page. The radars are not drawn: the same table says three, other reports say one 4D radar.
Photographed (Autohome series 7915 cat 12, read in the Browser pane; photo ids 12793838, 12793834, 12793846, 12793849): the lidar's
domed window in the black pod at the top of the windscreen with a pair of small cameras on the black tongue in front of it; a camera
on the underside of each mirror; a camera at the nose above the lip; round ultrasonic sensors in the front bumper's cheeks; the tail's
camera is the model's own. Their places come from the exported model's surfaces (the pod's top at (0.325, 1.402), the windscreen at
x = 0.5 is y = 1.264, the nose at x = 2.47, the cheek at x = 2.28 where z = 0.72, the tail at x = -2.50), about 2 to 3 cm good. The
four corner beams are drawn as Xiaomi's animation draws its sensors and are labelled so; they are not a measured coverage.

## 13. The RX's swivel screen and BOOST, Phase 3e (2026-10-12)

Approved by the owner with board T3e (`blender/reference/luxeed-rx/tech/motion`, `_sources.md`). Both demos have `view:
'cabin'`: the camera sits in the driver's seat (the Tech tab's director sets the anchor to `driver` and puts the wide shot
back when the demo is changed), the car's own screen is the live HMI pinned on the 3D `screen_main`, and the picture is
lifted clear of the panel at the foot of the window (`liftFrac` of the driver pose; a portrait window also opens the view
out, so the screen to the right of the seat is not cut off).

**Swivel screen** (`swivel.ts`, `ScreenSwivel.tsx`, `ScreenDirection.tsx`, `Swivel.tsx`). Published (the maker's page, some
trims only): the 16.1 in screen moves four ways, 55 mm forward and back and up to 30 degrees to either side. Photographed
(Autohome `hmi/_133_13373056.jpg`): the "centre screen direction adjust" dialog, with four buttons (centre and back, centre and
forward, toward the driver, toward the passenger), the "follow on boarding" switch (it turns the screen by who is in the front
seats) and the steering wheel's right scroll wheel for the angle. The dialog is built from that photograph on the HarmonyOS
skin (Settings > Display > Centre screen angle opens it; the demo opens it itself); not drawn: the row under the switch (the
photograph cuts it off) and the scroll wheel's steps. The cabin export merges the frame into one mesh per material, so the
frame's 522 triangles are cut out of the piano-lacquer mesh in the browser (`rigSwivel`, as `splitWheels.ts` does for the
wheels: those wholly inside a box round `screen_main`) and hung with the picture on a pivot at the hub (0.47 m, 0.0:
`Vehicle.swivel`); `ScreenDriver` turns it to the store's `screenTurn` and `screenSlide` (the dialog's four buttons are the four
corners; a turn keeps the slide it has), and the live HMI's corners are anchors on the pivot, so the HMI turns with it.
**Ours:** how fast it moves (26 degrees and 3 cm a second, easing out; none is published) and the order of the presses in the
run (driver at 1.2 s, passenger at 4.6 s, centre and forward at 8.6 s, centre and back at 12 s; 15.2 s). A press of a button
takes the screen from the demo (the clock pauses). Not modelled: the arm's movement behind the screen, the screen's own rear cover.

**BOOST** (`boost.ts`, `BoostKnob.tsx`, `hmi/harmonyos/Boost.tsx`, `Boost.tsx`). Published (the maker's page, some trims
only): one press raises instantaneous torque by 10 %, with its own throttle calibration, its own chassis tune, a three-screen
linkage with a sport sound, and the belts and seat bolsters tightening at once; the motor's up to 21,000 rpm, 251 km/h, 98.2 %
efficiency, torque response within 1 ms. Photographed: the BOOST knob, a round button at the wheel's lower right, its ring
lit blue (`hmi/_128_13373093.jpg`) and not (`_129_13372965.jpg`). The cabin's model already has the knob (a satin black cap in a
chrome ring, found 32 mm across at (0.287, 0.953, -0.328) by casting a ray at it); a blue ring is laid over it while BOOST is
on and a pale pulsing one before the first press, which is the thing to press (or the panel's button). **A stand-in:** the maker's
own three BOOST screens are not photographed, so the car's screen shows a page of the showroom's own while BOOST is on (the
five steps ticked off in turn, and the +10 % as two relative bars, because the torque itself is not published) and says so on its
face; the cluster and the head-up display are not changed. The run: pressed at 1.0 s, the five steps at 1.5, 2.3, 3.1, 3.9 and
4.7 s, pressed again at 8.2 s (10.6 s): the order and the timing are ours. **The enlarged screen** (the owner, 2026-10-13: the
BOOST page lives on the car's screen, so it should be big enough to read): the press that turns BOOST on brings the car's own
screen up beside the cabin (`BoostPopup`, `boostPopup` in the store): a column at the right of a wide window, half the width (at
most 760 px), the cabin's picture slid left of it (`shiftFrac` of the driver pose, as on the other tabs); a sheet over the cabin on
a tablet width, with its own "Show the cabin"; nothing on a phone, where the cabin's screen is as large as the window allows. It
can be closed ("Close"), stays closed for the rest of the run, and the panel's "Enlarge the screen" brings it back.

**The SU7's welcome sequence: source checked 2026-10-13, waiting for the owner's approval of the reference photographs (board
`blender/reference/xiaomi-su7-ultra/welcome/board_W_1.jpg`, `_sources.md` beside it).** Published (Xiaomi's own page, `mi.com/global/discover/article?id=3263`,
2024-04-17, read in the Browser pane): the SU7 has a 16.1 in 3K centre screen, a 56 in HUD "and a rotating dashboard for a
welcoming ceremony every time you start up"; "the dashboard display greets you as you start the car"; a Xiaomi tablet can be
added as a fifth screen. Reported (Chinese press, the launch coverage of Lei Jun's own drive): unlock, the driver's seat adjusting
and the 7.1 in cluster flipping up on its own, in one run. Photographed (Autohome series 7915, spec 70545, dashboard gallery): the
cluster lit, upright in its pocket on the dash top (#18, #19, #62, #67) and shut, a dark panel with the outline of the car on it
(#44, #6). Not found: any photograph or video of the greeting the cluster shows, of the flip in motion, of the HUD waking, or any
description of an exterior light show beyond a Q&A answer's "gradual fade-up on unlock" and a video title ("three welcome light
shows"): the exterior light choreography is therefore not drawn. What would be built, once the photographs are approved: the
cluster pivots from shut to upright when the visitor starts the car from the driver's seat (the cabin split out of the merged
mesh in the browser, as the RX's screen frame was), with a greeting on its screen that is the showroom's own stand-in and says so.

**The 7X's welcome sequence: not built.** The source check (2026-10-12, English and Chinese searches, the makers' pages and
Autohome) found no published sequence for it (the SU7's was found the next day, above). The 7X has a Stargate interactive light curtain at the
front that offers interactive lighting for scenarios, and concealed handles with night guidance, the phone or watch as a key
that unlocks as you walk up, and frameless powered doors with one-touch open and close (the automatic open and close is an
option); nothing says what the light curtain, the handles or the mirrors do on approach. Building one would be inventing it, so
it waits for a video or a manual page from the owner, or a decision to drop it.

## 14. The chassis demos and the street, Phase 4 (2026-10-13)

The Denza Z9 and the Xpeng G9L, the two cars added after Phase 3, had no cabin, no HMI skin and no opening parts yet (they have
all three since 2026-10-13/17: docs/3d-pipeline.md, the Z9 and G9L cabins), so
their demonstrations are the ones that need only their wheels: how the chassis moves. The rig took them as they came (both
GLBs ship per-corner wheel nodes). Built on the owner's request to "add the Crab Walk (the rig test's) to the Z9, add some
environment, think of the tech features of the two new models and build them".

| Car | Demo | Driver | Starts from |
|-----|------|--------|-------------|
| Denza Z9 | Crab walk | `crab` | the car's screen (the generic skin's chassis page) |
| Denza Z9 | Compass turn | `compass` | the car's screen; the dock picks the wheel (left or right front) and the angle (90, 180, 360) |
| Denza Z9 | e³ parking | `e3park` | the car's screen: Pull in, then Pivot at the stop |
| Xpeng G9L | Rear-wheel steering | `uturn` | the car's screen |
| Xpeng G9L | Nose-in parking | `park` with `params.noseIn` | the dock: a button standing for the voice command |

**What is published, and from where** (every source below was read in full on 2026-10-13; they are on each demo's facts panel).
The sources for the Z9 describe the **Z9 GT**, the shooting brake on the same e³ platform, and the showroom's Z9 is
listed as the sedan with the same two modes in its drive-mode list: check that the sedan has them.
- *Crab walk* (BYD China, 2024-08-22; Xchuxing 133019; km77): crab walk is one of e³'s five signature functions (with the compass
  turn, extreme steering, e³ parking and low-grip stabilisation); the front and rear wheels turn the same way and the car moves
  diagonally; the rear wheels steer at most ±10°, with the rear motors' differential the crab angle reaches 15°; km77 adds that the
  front wheels should not be turned more than 15° nor the car driven faster than 20 km/h, and that the centre screen shows a
  numeric indicator against over-turning.
- *Compass turn* (Xchuxing, km77, The Autopian): braking, torque vectoring and rear steering: one front wheel is locked as the
  pivot, the rear wheels splayed out and driven in opposite directions, any angle from 0 to 360° about either front wheel; Denza
  says the tyre wear is like a hard brake. The turning radius is 4.62 m (BYD).
- *e³ parking* (The Autopian, km77, Xchuxing): for a parallel space the driver pulls the nose in, chooses a front wheel to pivot
  about and turns an outline of the car on the screen; the inside rear wheel is driven forward, the outside one backward. Xchuxing says it
  was to arrive on the Z9 GT by OTA.
- *G9L rear steering* (Gasgoo's launch report; Xchuxing 174677; CarNewsChina 2026-08-11): steer-by-wire rear axle, up to 15° either
  way, standard across the range; turning radius 5.4 m (Wikipedia says 4.96 m; most reports say 5.4).
- *G9L nose-in parking* (Gasgoo): a new nose-in parking function makes the boot easier to reach, and voice commands from outside the car
  can direct parking manoeuvres.

**Ours, said on screen:** the streets, how far the car goes (2.25 m sideways in the crab walk), the pace (7 km/h in the crab walk, inside
the 20 km/h limit), the gap and the 30° of e³ parking (no source says how tight a gap the car can take), the front wheels' angles in the
G9L's U-turn (they follow from the geometry), the generic screen, the button standing for a voice command.

### The motion

`kinematics.ts` gained one thing: a segment may carry `steer` (the angles the wheels are really set to, per corner), for a car whose
rear wheels cannot do what a no-slip turn asks. A wheel off its own velocity rolls the part of the path that lies along its plane and
scrubs the rest (`roll = velocity . heading`). The crab walk uses it to put the front wheels at 15° and the rear ones at their 10° limit
(rolled distance checked: 24.01 against 23.92 turns); the compass turn uses it to splay the rear wheels at ±10° instead of the 90° a
turn about a front wheel would ask of them (the pivot wheel has no velocity and does not roll; the other front wheel rolls straight).
`src/lib/tech/street.ts` has the planners, with no value imports of three.js, checkable with Node (a transpile script and four test
files were used):

- `planCrab`: one move at 15° off the heading, 2.25 m sideways (8.7 m of travel), to 25 cm off the kerb stone; the empty stretch of kerb is 15.3 m between
  two pairs of parked cars; 7.5 s, 7 km/h.
- `planCompass`: approach 4.5 m, turn about the chosen front wheel, leave 7 m. The street is as wide as the sweep needs plus 40 cm each
  side, measured on the model: 7.4 m for 180° (the Z9's 4.62 m turning radius makes a turning circle of 9.2 m), 9.9 m
  for 360°; 21 s and 28 s. The wall of the dead end is 70 cm past the farthest the body reaches.
- `planPivotPark`: a 12 m arc in (the front wheels about 14° and 16°) to 30° off the kerb, a stop (the clock waits), then a turn about the left
  front wheel with the rear wheels splayed. The gap is 6.14 m for a 5.09 m car: 70 cm behind it, where the pivot swings the tail 39 cm
  back, and 35 cm ahead of it; the body comes within 19 cm of the stone as it swings and ends 40 cm off it. 12.2 s, the stop at 7.9 s.
- `planUTurn`: `rearSteerCentre` solves where the car turns about when its outer front wheel follows a circle of 5.4 m and its inner rear
  wheel is at 15° against the fronts (bisection): the fronts come out at 35.2° and 24.6°, the rears at 15° and 9.8°. The street is the sweep plus
  90 cm each side, 13.2 m; 22.7 s.
- `planPark` (park.ts) gained `noseIn` and `rearSteerDeg`: the car turns a quarter circle about a point to its right and a little
  ahead of the rear axle, on rear steering, then 60 cm straight in; the planner takes the smallest turn that keeps 30 cm from the
  neighbours (31 cm found; the front-steered forward arc needs a lane of nearly 9 m and still hit a neighbour by 47 cm, which is why the
  rear steering is used). The reverse-in the RX uses is unchanged (the same code path: 18 s in, a stop, 18 s out).

### The street

`StreetStage` (`street.ts`) is what the viewer draws: the road between kerbs (`road`), footways, painted lines and bays, parked cars
(stand-ins of the other modelled cars, `streetCars` in demos.ts, now including the Z9 and the G9L: `scripts/make-proxy.mjs denza-z9`,
`xpeng-g9l`, about 60 KB each), lamp posts, trees, bollards, an optional dead-end wall, and the camera's frame. `viewer/TechStreet.tsx` draws
it in the studio's own language, matte and pale, fading out at its ends: the road is one canvas texture (asphalt with grain, mended patches,
gutters, painted lines, manholes), each footway a strip of quads a kerb's height up with vertex alpha, so it fades with the road; behind the
far footway a plane of buildings (windows and shopfronts, painted on a canvas, fading toward the top into the white; hidden when the
camera has gone round behind it); the props are merged geometries with vertex colours, one draw call each; the cars are TechStage's
`Neighbour`. It takes the studio's dusk (`useDusk`) like the asphalt. The near footway has no trees and no lamps: the camera is on that
side and they would stand in front of the car. `TechLotDressing` puts the same planted strip, lamps, trees and buildings behind the bays
of a parking lot (`dressLot`), so the RX's park demo and the G9L's nose-in parking stand in a place too.
Store: `techStreet`, `compassPivot`, `compassAngle`, `HmiScreen 'chassis'`. Session: `Runtime.chassis` (readout, facts, stage) and
`useChassisReadout`.

### The screens

`hmi/chassis.tsx` is the generic skin's chassis page: the car from above with each wheel turned as the run sets it, the figure the
manoeuvre is about (crab angle, how far turned, angle to the kerb), the speed, the four angles and the one button. A pivot wheel
is filled while it is held and ringed while it is chosen. `lib/tech/chassis.ts` has the words and the button for each point of the run
(start, pause, resume, the stop's own button, again), shared by the page, the device column (`TechDevices`, which treats these demos
like the carpet's: one pill, and on a narrow window a bar) and the dock (`showroom/Chassis.tsx`: the angles, the speed, the street's
width, and the compass turn's choices). The page says it is drawn for the showroom: the maker's e³ and chassis screens are not photographed.
The G9L's XOS shows this generic page; the Z9's DiLink has its own e³ page since 2026-10-16 (section 15).

### Checked

tsc, eslint (src), production build in a copy of the project (passes), idle frames 0 on the Tech tab with a street, the whole run of each
demo clicked through in the pane (start, pause, the stop, again; a switch of demo; the compass turn's pivot and angle), a phone-sized
window (the screen as a sheet, then the bar), the RX's park demo with its new dressing. Wheelhouse clearance by a probe of the body's vertices
against each steered tyre (a cylinder about the axle) at the G9L's 35° front lock and the Z9's 15° crab: nothing but the invisible
`M_Shadow` shell comes into a tyre; no paint, trim or glass does.

### Not done, and considered

- The Z9's and G9L's own screens (DiLink 150, XOS Tianji), the outline you turn on the Z9's e³ parking screen, an app: no photographs.
- Tyre marks where the compass turn's rear wheels scrub; the crab walk in reverse and the parallel-parking use of the compass turn on a longer
  stretch; extreme steering (the Z9's 4.62 m: a no-slip turn on that radius asks about 20 to 30° of the rear wheels and they steer 10°, so the rest is the rear
  motors' differential, which is not modelled).
- G9L welcome mode (the air suspension lowers the body 30 mm: one source, Xchuxing 174677; a 3 cm change is also hard to see), the 5C charge (450 km in
  9 minutes, 10 to 80 % in as little as 11: needs a charge port in the model, with approved photographs), the 98 in digital-projection headlamps (one line
  in one launch report; what it projects is not said), VLA 2.0 (a list of capabilities and "six-second trajectory prediction", no behaviour to draw),
  the Z9 GT's megawatt charging (a port again).

## 15. Charging for every car, the Z9's e³ page and the new layout (2026-10-16)

Built on the owner's pre-launch review: "Charging section ... should be available across all other vehicles", then "make a new
section for charging for all cars, it's not only a tech demo".

**Charging is a tab, not a demo.** The 7X's `fast-charge` entry left `Vehicle.tech`; every car with charging figures has a
`Vehicle.charging` (`ChargingSpec` in `schema.ts`: the maker's window and its minutes, the peak where it is published or the
C-rate it publishes instead, the pack, the voltage, the connector, the port's side, cited claims and what is simulated) and a
`Vehicle.chargePort` (the socket's mouth and outward axis in the viewer's axes). `lib/tech/charging.ts` turns that into the
`ChargeFacts` the run is planned from and a `TechDemoSpec` (`chargeDemo`) so the director, the clock and the playback bar run it as
they run a Tech demo; the director plays it when the tab is `charging` (`isStageTab` in the store covers both stage tabs). The tab's
panel (`showroom/Charge.tsx`: the readout, the curve, the specifications, one button) stands in a column at the right of a wide
window and in the dock of a narrow one. `charge.ts` takes a `ChargeProfile` (pack, window, seconds, peak) instead of the 7X's
constants, and puts the pedestal on the side the port is on (`pedestal.face`: its face and the camera turn to the passenger's side
for the G9L).

| Car | Window | Peak | Source | Port |
|---|---|---|---|---|
| Zeekr 7X | 10 to 80 % in 10 min | 620 kW (published) | Xinhua 2025-11-03 | left rear quarter, flap modelled |
| Xiaomi SU7 Ultra | 10 to 80 % in 11 min | 5.2C x 93.7 kWh = 487 kW (electrive reads 490) | CarNewsChina 2024-12-05, electrive 2024-11-06 | left (CarNewsChina database); place ours |
| Xpeng G9L | 10 to 80 % in 12 min | 5C x 110 kWh = 550 kW | XPeng news (the refreshed G9: 5C, 12 min, up to 525 kW) | right rear (EVKX); place ours |
| Luxeed RX | 30 to 80 % in 15 min | derived from the window (257 kW) | CnEVPost 2026-09-28 | left rear quarter (photographs); place ours |
| Denza Z9 | 10 to 80 % in 19 min | derived (283 kW) | the data file's figure (Autohome configuration table); **not confirmed** | left rear quarter: **our choice, no source** |

**To confirm with the owner:** the Z9's 19 minutes and its port side (no source found; the Z9 GT's 1 MW flash charging is a
different car and is not used), the G9L's use of XPeng's G9 figures, and the SU7's side (one database).

**The socket of a car with no flap.** Only the 7X's model has a flap and a socket (`Zeekr7X_ChargeFlap`, `Zeekr7X_ChargePort`). For
the other four, `TechCharge.tsx` draws a `Socket` at `chargePort` while the demo's flap is "open": the seam of an opened flap, the dark
pocket, the DC cup with the contacts in the gun's layout and a light strip that follows the pedestal's. It grows out of the skin and
shrinks back; the exact place along the quarter is ours (the rule: behind the rear wheel's centre, at the height of the quarter's
shoulder; the RX's was read off a photograph, where the flap is above and behind the rear wheel). `chargePort` was found by casting a
ray along z at that (x, y) onto the exported model (the probe: a gltf-transform script, the normal from four neighbouring hits); the same
probe reproduces the 7X's published port to 2 cm on the skin and 0.01 in the axis.

**The Z9's e³ page.** `hmi/dilink/E3.tsx` replaces the generic chassis page inside the DiLink skin: the light stage of DiLink's camera
page with the car seen from above (`public/hmi/denza-z9/car-top.webp`) and its four wheels turned by the run, a manoeuvre selector
(Crab walk, Compass turn, e³ parking, in step with the Tech tab's chips through `techDemoId`), the big figure (the crab angle; how far
turned; the angle to the kerb), the speed, the four angles (the held wheel is lit), the compass turn's two choices (the wheel to pivot
about, 90, 180 or 360 degrees), a line of the published limits for the others, the platform's five signature functions (BYD China, three
of them demonstrated) and one button (`chassisAction`: start, Pause, Resume, Pivot at e³ parking's stop, Again). The G9L's XOS keeps the
generic page.

**The layout.** The showroom's main menu moved from the bottom to the top (`showroom/Chrome.tsx`: the car menu, the tabs, the scene
switch and an info button; one row from 1280 px up, two below). The Tech tab's demonstrations are a second row of it. What stood at the
foot is now only the tab's own controls: a tool card (trimmed of its footnotes, whose content is the demo's `simulated` text) and the
playback bar, whose "Simulation" button opens the demo's facts and sources. The long notes of each tab (and the independence
statement of the old footer) are behind the info button. The menu publishes its height as `--top-ui` (a panel hanging from under it
starts at `BELOW_TOP`) and as `uiTop` in the store, which the camera treats as it treats a device's inset. The Specifications tab (renamed from Dimensions on 2026-10-16; its id and `?tab=dimensions` stay) holds the
specification sheet (`showroom/Specs.tsx`), everything the retired vehicle page held; `/vehicles`, `/vehicles/[slug]` and `/compare`
redirect (`next.config.ts`), and the site's header and footer went with them.

### Glass (2026-10-16, later)

The owner asked for real glass on the windscreen and the front windows, then for the same tint an open door shows on the rear
glass (rear windows, backlight, a glass roof). All five exteriors have the same structure, so it is done in the viewer, with no
re-export: the clear glass is the material `M_Glass` (windscreen and front door glass), the privacy glass `M_Glass_Privacy`; the black
layers behind them are the `*_Blackout` node's `M_Black_Gloss` (underlay) and `M_Shadow` (shell).
- `viewer/clearGlass.ts`, `cullBehindClearGlass`: once per mount, takes out of those two meshes (on a copy of the geometry) the triangles
  whose centroid lies within 5 cm (underlay) or 7 cm (shell) of a pane's vertices; the hull elsewhere stays, so the body does not leak (the
  X-ray tab hides the whole node, which is why it does).
- `useGlass` (Openings.tsx): from outside, with the cabin mounted, `M_Glass` panes draw as the X-ray's ghost (`vehicle.xray`, else #98a4b3 at
  0.34) and privacy panes at 0.55 in their own dark tint, which is what an open door's pane already showed; the frit stays opaque; an open door's
  pane still clears as it swings.
- The cabin (preloaded already) is mounted as soon as the exterior is up (`exteriorUp`, `cabinReady` in the store; not on the Tech tab, whose
  demos move the car and not the cabin). A cabin has pieces a few millimetres outside the skin (the 7X's taupe jamb strip at the door's
  leading edge), so with every part shut (`shut`, kept by `OpeningsDriver` from `hinges.lift.cabin`) the cabin is drawn only where a pane is in
  front of it: each pane has a stencil writer (a copy of its mesh: no colour, no depth, render order 1) and the cabin's materials test the stencil
  (render order 2). The canvas asks for a stencil buffer. With a door open the mask is off and the cabin shows as before.
- Not covered: the cabins of the five cars were never checked from outside, so anything visible through a pane (a gap above a dash, the
  G9L's slit at the windscreen base) is now seen; the capture routes (`VehicleViewer`) get the same glass.

## 16. The SU7's parking assist (2026-10-17)

The owner asked for it in the SU7's Tech section along with the new scene. The source is the other video of Xiaomi's page
(`auto-parking.mp4`, 11.7 s: a row of perpendicular bays, grey parked cars, the white SU7 driving along the aisle with ripples at its
corners, the empty bay picked out with a blue P, the car pulling past it, swinging and reversing in nose out). Published: automatic
parking is standard and parking memory optional (CarNewsChina's table), and Xiaomi's one line, "takes care of the parking process for
easy and more manageable arrival". Nothing of the car's own parking screen is photographed, so the demo has no device and starts from
its panel (`showroom/ParkAssist.tsx`: Find a bay, Pause, Resume, Pull out, Again).

The motion is the Park from your phone planner with one addition: `ParkOptions.search` (tech entry `params: { search: 12 }`), a drive
of 12 m along the row before the stop, at `ASSIST_MOTION` (1.9 m/s at most), so the car starts 12 m before where the old demo began.
`ParkStage.search` gives the times the panel and the overlay use: the bay is "found" once the nose has passed its far edge (about 3.4 s)
and the drive ends at about 8.4 s; the reverse on one arc follows, the clock stops with the car parked (20.8 s), "Pull out" drives out
again to where the search ended (32.8 s in all; the clearance to the cars beside is the same 0.46 m). `viewer/TechParkAssist.tsx`
draws the overlay on top of the usual stage: `CarCoverage` with only the surround beams (8 m), the ultrasonic ripples and the
camera dots, a pale blue tile with the P on the empty bay from when it is found until the car backs toward it, and white corner marks
on each parked car as the nose comes within reach of it. Ours: the car park, the cars, the path, the speeds; the look follows Xiaomi's
animation, not the car's display.

Checked 2026-10-17: tsc, eslint; the RX's Park from your phone is unchanged (stops at 18.3 s, 0.46 m); played through in the Browser
pane (the real Find a bay button, the stop, the pull-out). Not checked: a production build (the tree is shared with other work in
progress), the nose-in parking of the G9L after the planner change (the search is ignored for it).

## 17. Autonomous Drive: one scene per car (2026-10-21)

**Owner request:** the Luxeed RX and the Avatr 06T showed the same scene (they used the same planner), so each gets its own, and the
XPeng G9L gets Autonomous Drive too, on a road not used by the others.

**The engine.** `src/lib/tech/sensors.ts` used to be one planner with the RX's overtake hard-wired. It is now a thin entry
(`planSensors(layout, body, start, { scene, cars })`) over `src/lib/tech/drive.ts`, a generic engine, and one file per scene in
`src/lib/tech/scenes/`. The engine does what the planner did: the car stays on the spot and the road rolls under it, the car holds a
set speed, follows what is ahead (a PD controller on the gap and the speed difference), changes lane on a raised cosine, dips and
rocks on its springs. A scene gives it a road, a list of road users (`ActorDef`: a car, a person or a box, each with a speed and a
lateral place as functions of time) and a `decide(world)` that answers every step with a `Command` (set speed, a place to stop at,
a lane change, the words for the readout, the actors to mark as a hazard). New in the engine: a stop-at-a-place controller (brakes
late and firmly, like a driver, with a harder emergency limit of 8 m/s^2), a standstill gap for things that do not move
(`follow.stopGap`), road users that face their way of travel (cars cutting in, cars coming the other way), people with a stride, and
actors the sensors cannot see until a time (`unseenUntil`). The panel reads the scene's own words (`SensorsReadout.message`, `note`).
The demo's data entry names its scene: `TechDemoSpec.scenario` ('overtake' | 'debris' | 'city').

**Regression:** the overtake scene is the old planner moved unchanged; it was checked by running the committed planner (`git show b7788d4:src/lib/tech/sensors.ts`) and the new engine side by side, and the largest difference in the car's position, speed and heading, every other car's
position, the states, the gaps and the tracked counts is 0 (timeline: following 2.8 s, waiting 5.0 s, lane change 8.35 s, done 18.9 s).

| Scene | Cars | What happens (all ours) |
|---|---|---|
| `overtake` | RX, SU7 Ultra, NIO ES8 | the section 12 run: the car ahead brakes, the car follows, waits for the left lane, overtakes |
| `debris` | Avatr 06T | expressway, 16.5 s: a slower car on the right drifts into the lane close ahead (the car eases off at 2.8 s, brakes at most 2.3 m/s^2, never closer than 25 m); a box lies in the lane 335 m on; the roof lidar marks it from 125 m (Huawei's "14 cm box at 120 m" for the 896-line lidar); the car checks the right lane, moves over at 9.1 s and goes round at 92 km/h while the car it was following swerves left; done at 13.6 s (2.5 m clear of the box) |
| `city` | XPeng G9L | street, 22 s: 50 km/h between parked cars; at 1.5 s a person steps out from behind them into the lane and the car stops from 50 km/h in about 2 s, 4 m short; then a zebra crossing: a car ahead and one beside stop for four people, the car stops 3.8 m behind the first, waits (about 3 s) until the crossing is clear and moves off; one more car comes the other way and stops at its own line |

**What is published, for the two new panels.** 06T: Avatr's page ("Huawei Qiankun ADS 3.0, 896-line roof LiDAR, ultra-wide surround
vision"; "end-to-end GOD and PDP network") and Huawei's 14 cm at 120 m (2026-03-04, the figure for its 896-line lidar). G9L: Autohome's
table for series 8659, read in the Browser pane 2026-10-21: XNGP, level 2; three Turing chips (2,250 TOPS) on the top trims, two or
one on the others; 11 exterior cameras with a stereo pair at the front, two in the cabin; 12 ultrasonic sensors; three millimetre-wave
radars (seven on two trims); no lidar row. XPeng's G9L release (2026-10-14; Paris, 2026-10-12): NGP on VLA 2.0 shown on test rides with
roundabouts, narrow streets, motorcycle traffic, pedestrian crossings and complex right-of-way; automatic emergency braking up to
150 km/h; the page says nothing about sensors. The table's tick marks (lane change, traffic lights, hands-off) are icons and could not
be read as text, so none is claimed.

**The G9L's sensors** (`xpeng-g9l.ts`, `SensorSpec`, now with `lidar` optional and a new `views`): read off Autohome photographs
(c12_0044 rear, c12_0068 and c1_0001/0003 front) and set on the model's surface with a ray (about 5 to 10 cm good; `scripts/tech-tools/glb-rays.mjs`
loads a Draco GLB and casts rays): the camera in the grille's black divider (2.55, 0.50, 0), the camera above the rear
plate (-2.53, 0.90, 0), the sensor pod behind the top of the windscreen (0.52, 1.66, 0), round ultrasonic sensors beside the front plate
(2.515, 0.60, +-0.45), at the lower front corners (2.38, 0.40, +-0.80) and at the rear corners (-2.46, 0.48, +-0.72). The four camera
views drawn (forward 52 degrees to 48 m from the pod, wide 120 degrees to 16 m from the nose, backward 110 degrees to 24 m from the
tail, and to each side 100 degrees to 16 m from the mirrors) are ours; the side ones are drawn from the mirrors because no photograph
shows a side camera (the small oval on the front wing is not claimed as one). The panel's new switch is "Camera views"; the marks on the
road users follow it where there is no lidar.

**The street** (`viewer/TechCity.tsx`, reusing TechStreet's lamp and tree): asphalt, kerbs and footways stand under the car; the dashes,
lamps, trees and the building facades repeat every 24 m and are rolled by the rig as far as that (`CarRig.attachRoad(g, base, period)`);
the zebra bars and the stop lines roll with the road. The far side's buildings hide when the camera is out beyond them (as TechStreet's
do). `RoadStage.city` (carpet.ts) carries the layout. People are stylised figures (`figure()` in TechSensors.tsx: capsules, limbs
swinging with the distance walked, so scrubbing the clock keeps the stride right); a box is a cardboard-coloured cuboid; both get the
sensors' marks (a ring on the floor for a person, corner brackets for the rest; amber and pulsing for a hazard).

Checked 2026-10-21: tsc, eslint; the engine's timelines printed and every actor's closest approach checked (`scripts/tech-tools/scene-test.mjs`, run with `node --no-warnings --import ./scripts/tech-tools/register.mjs scripts/tech-tools/scene-test.mjs city`: nobody
nearer than 1 m to a neighbouring car, 2.5 m from the box, 4 m from the person who steps out, 3.8 m behind the stopped car); played
through in the Browser pane (06T, G9L, RX). Not done: the SU7 and ES8 still play the overtake (the SU7's is the one the owner asked to
match Xiaomi's clip); a production build in a copy; the owner's look.

## 18. The Seal's God's Eye: a traffic-light scene and a roof lidar (2026-10-26)

**Owner request:** the Seal's two Tech chips (`ctb`, `godseye`) named drivers that did not exist. Research said CTB is a static structure with nothing to animate
and God's Eye is worth building: model the roof lidar from reference photos for approval, then the sensor spec and a traffic-light scene.
CTB is still a dead chip (left alone: not asked).

**What is published** (Autohome's table for the 2025 Seal, read 2026-10-26 at car.autohome.com.cn/config/spec/71666.html; the series page hides the
equipment rows): the 650 and 600 AWD Smart Driving trims run DiPilot 300 (level 2) on one Orin-X (254 TOPS): one lidar, eleven exterior cameras with a
stereo pair at the front, two in the cabin, twelve ultrasonic sensors, five mm-wave radars; traffic-light recognition is listed only for them. The 510 Smart
Navigation is DiPilot 100 (Orin-N, 84 TOPS, twelve cameras, no lidar, remote parking). BYD sells it as God's Eye, B = DiPilot 300 (Gasgoo). Not published:
the lidar's make or field of view (Hesai supplies BYD's lidars, no source ties a model to the Seal), so the 120 degree fan is ours and the panel says so.

**The lidar** (`blender/scripts/seal_lidar.py`, called from `seal_front.build_all`, material `M_Lidar_Window`): read from Autohome photographs of the
650 Smart Driving (spec 71665, kept in blender/reference/byd-seal-ev/lidar with `_sources.md`; indexes 16, 17, 18 of that listing, the silver car of the
same listing has none): a low black housing on the windscreen header, 0.275 m wide at the glass, 0.057 m high, 0.19 m long, raked front with one dark
trapezoid window, concave cheeks, the tail melting into the roof. Its front edge stands 2.6 cm ahead of the model's windscreen top edge (x 0.23, by ray);
the base sinks only 8 mm into the glass (the glass is clear: anything deeper shows inside the cabin). It is in `BYDSeal_Details`, so the showroom
car shows it whichever trim is chosen (the 510 has none: said in the demo's text). Comparison sheet: blender/renders/byd-seal-lidar-vs-photo.jpg.

**The sensors** (`byd-seal.ts` `sensors`, glTF axes): lidar window [0.261, 1.40, 0]; the camera pair behind the glass [0.33, 1.335, +-0.03]; the nose and
tail cameras are the model's own; a camera under each mirror [0.70, 1.015, +-0.965]; round ultrasonic sensors in the front bumper, a pair beside the
plate (+-0.335, z 0.41) and a pair at the upper corners (+-0.74, z 0.56), read off the front photograph (the nose camera's height came out at 0.505,
which is where the model has it). Four camera views are drawn (forward, wide from the nose, backward, to each side from the mirrors); every angle and
reach is ours. `lidarFov: 120` is now allowed to be ours (schema comment).

**The scene** (`src/lib/tech/scenes/trafficlight.ts`, scenario `trafficlight`, 27 s, ours throughout): 50 km/h behind another car on the G9L's street; the
light at a zebra crossing turns amber at 3.6 s and red at 6.0 s (green again at 17.4 s); the car recognises it from 110 m, stops behind the car ahead at the
line (waiting from 12.3 s), people cross while it is red, and it moves off 1.2 s after green behind the cars ahead. New: `CitySignal` in carpet.ts, drawn by
`viewer/TechSignal.tsx` (a mast and arm with a head over each lane, the lit lamp follows the clock, the sensors' corner marks stand round the head over the car's
lane while the car has it). `stopAndGo` and `walker` are now exported from `scenes/city.ts`. Checked: `scene-test.mjs trafficlight` (nearest car 1.4 m,
lead 3.75 m, people 3.2 m, accel -2.6 to 1.7 m/s^2), played in the Browser pane through amber, red, waiting, green and moving off; tsc and eslint clean.
Not done: a production build in a copy, the owner's look at the lidar and the scene, the 510's demo without a lidar (it shows the pod).

## 19. The Drive tab: one scenario per car (2026-10-27)

**Owner request:** the Drive tab played the same standing start for every car. Each car now has a scenario of its own, built from
what is particular to it (its motors, its chassis, its mode list), with the pull, the stop, the S-curve and the crab walk
simulated on the variant's published figures.

**The pieces.** `Vehicle.drive` (`DriveSpec`, schema.ts) is the car's scenario: its title and blurb, which of its own modes
(`cockpit.driveModes`) and loads it offers, which instrument cards explain it (`overlays`, the first leading), what follows the pull
(`finish`: coast, cruise or a stop; `manoeuvres`: sweep, slalom, crab), the 100-0 distance it is calibrated to, a chassis block
(squat and roll per g, centre of gravity, rear-wheel limit, crab angle, air suspension), the drag coefficient when one is
published, the rival the chart draws behind it, the camera it opens on, narrative callouts pinned to moments of the run, cited
claims and a note on what is simulated. A car without one gets the generic scenario (the Xpeng P7+ today).
`src/lib/tech/drive-setup.ts` turns a car, its trim and the visitor's choices into `DriveInput`; `src/lib/tech/drive-run.ts`
(`planDrive`, no value imports: run it under Node) is the planner; `drive` in `demos.ts` hands it to the director;
`showroom/Drive.tsx` is the panel; the GT7 cockpit HUD (`showroom/Launch.tsx`) is unchanged apart from reading the run's phase.
Store: `drive` (`DriveChoice`: run, mode, load, camera, stop, rival). URL: `?tab=drive&variant=&run=&mode=&load=`.

**The run** (all of it ours except the figures said below). The pull is the launch's (section 10: a plateau that builds in
0.15 s and reaches 100 km/h at the maker's time, then falls as a power-limited car's, a = a0 (V100 / v)^p with p solved so that 200 km/h
comes at its 0-200; where the maker has none, 3.15 times the 0-100 for a car that reaches 200 km/h, said on screen). New:
- **Mode and load.** A mode's time is the 0-100 scaled by the cube root of the share of the peak it lets through (the car's own published
  figure where it has one: the SU7 Ultra's Endurance, Qualifying and Drag race, else `lib/performance.ts`' factors) and a load's by
  the mass ratio to the 0.4; the 0-200 keeps the shape. The panel says "modelled" (a star on the chip) once either differs from the
  maker's own run (full power, driver alone: 75 kg is ours).
- **Rolling pulls** (80-160 on the Seal, 80-140 on the ES8, 100-200 on the SU7, 0-150 on the 7X) come from the same curve.
- **A stop**: calibrated so that 100-0 takes the published distance (RX 32.4 m, ES8 34.3 m; else 36 m, ours); the car lifts to the run's
  speed first so the stop starts from it. The brake blend (regeneration limited to 30 % of the peak power and 0.3 g, fading below 8 km/h)
  and the energy recovered are ours.
- **S-curve under power** (Z9, 06T): a sine path of 1.0 m over 130 m wavelength, two periods, while the car pushes on at 0.26 g to
  130 km/h (0.4 g lateral at most). The rear motors share the drive between the wheels by the lateral acceleration (outside wheel
  favoured, up to 70/30); the body rolls on its spring (1.3 to 1.7 degrees per g, ours) and the rig's `roll` is now written by the
  director (`Chassis.roll`).
- **Slalom** (G9L): two periods of 1.4 m over 24 m at 16 km/h. The wheels' angles come from one rule, a rotation about a point on
  the car's axis (`steerFor`: every wheel points along its own velocity), with the rear wheels turning against the front by 0.6 of
  its angle, within their 15 degrees; the fronts then need less angle than they would alone, which the card reads out.
- **Crab walk** (Z9): 1.8 m sideways at 7 km/h, the fronts at 15 degrees and the rears at their 10, as the Tech tab's crab walk.
- **Telemetry** per instant (`DriveTelemetry`): power and torque (scaled so that the maker's own run draws the variant's peak), the
  motors' shares and power, the rear axle's share of the weight (the transfer is a g times the centre of gravity's height over the
  wheelbase), pitch, roll, each corner's spring travel, energy used and recovered, the range that energy would have driven (at the
  car's ordinary consumption), drag, the wheels' angles. The split of the drive between the motors (a quarter to the front on three
  motors, 40 to 60 on two) is ours, as is every damping figure.

**The panel.** A column at the right of a wide window (a bar under the menu that opens over the car on a narrower one): the trim
(from the car's variants that have a time), the car's modes, the load (where the scenario has one), what follows the run, four
cameras (hero, chase, side, top: the stage's look, not rebuilding the run), the callout of the moment, the instrument cards, a speed
chart with a rival's published pull behind it, and, at the end of a run, a summary with a link to the rival's Drive tab. The playback
bar now stands on this tab as well (play, replay, scrub, speed) with the run's moments marked on it (launch, 100 km/h, peak, brake, stop,
S-curve, slalom, crab walk); a click on a mark goes there. The HUD's motor sound fades while the car brakes or crawls (`setGain`).

| Car | Scenario | After the pull | Leading instruments | Rival on the chart |
|---|---|---|---|---|
| SU7 Ultra | Precision Launch & Sustained Power | coast; 100-200 run; Eco to Drag race | power & torque, weight transfer, motors, energy | Seal AWD |
| Luxeed RX | Track-Bred Sprint + Stop | 100-0 in 32.4 m | braking, suspension, motors, weight | 7X AWD |
| BYD Seal | Balanced Performance Run | coast; 80-160 run | aero drag (Cd 0.219), power, energy | its own single-motor trim |
| Zeekr 7X | SUV Supercar Launch | 0-150, then a 120 km/h cruise; load toggle | weight, suspension, motors, power | G9L |
| Xpeng G9L | Effortless Authority + Maneuverability | slalom on the rear-wheel steering; load toggle | steering, weight, motors, power | 7X |
| Denza Z9 | Hyper-GT Launch + Vectoring Mastery | S-curve under power, then a crab walk | motors (torque vectoring), steering, power, weight | 06T |
| Avatr 06T | Shooting Brake Assault | S-curve under power | weight, suspension, motors, power | Z9 |
| Nio ES8 | Refined Reserve Power | 100-0 in 34.3 m; 80-140 run; load toggle | suspension, braking, weight, energy | Z9 |

**Figures from the brief that are not used, and why.** The scenario brief quoted figures that disagree with this repo's sourced
data or that this repo has no trim for; the repo's figures stay, and the scenarios pick up a new trim by themselves:
- SU7: the brief's Max AWD (3.08 s) is not in the data; the car here is the Ultra (1.98 s).
- 7X: the brief says 500 kW, 790 Nm and 3.7 s; this file has the refreshed 7X at 585 kW and 2.98 s (Paul Tan, 2025-10-22), and press
  quotes 475 kW and 3.8 s for the earlier Performance AWD.
- 06T: the tri-motor trim (712 kW, 2.78 s, one front and two rear motors; CarNewsChina, 2026-04-23, as the search summary read it)
  is not a variant here (pack and range reports disagree), so the motors drawn are a front and a rear one. Add it as a variant
  with a `motorCount` of 3 and the rear pair draws as two motors, and the S-curve shows the vectoring.
- RX: CnEVPost also says "as little as 3.6 s" for 0-100; this file has 3.9 s for the dual-motor car. Not changed.
- ES8: the brief says 34.9 m for 100-0; NIO's page (cited in the 'primeride-launch' demo) says 34.3 m, which is used. That demo's text
  also says 480 kW and 850 N·m against this file's 520 kW and 700 N·m: left alone, not asked.
- Seal: Cd 0.219 is CarNewsChina's database figure (the maker's page was not read), cited as such.
- Not built: an interior camera, an underbody or X-ray camera, a ghost car drawn beside the car (the chart has the rival's curve),
  wet or inclined roads, voice narration, a booking button, motor rpm (only the RX's 21,000 is published here and the gearing is not).

**Checked 2026-10-27:** tsc and eslint clean; `scripts/tech-tools/drive-test.mjs check` (the 0-100 and 0-200 reach the published times, the
new planner agrees with `planLaunch` within 0.3 km/h through a pull to 200, a mode and a load slow the car in the right order, the stop
is the published distance, the manoeuvres stay on the road and within the rear wheels' limits); `scripts/tech-tools/drive-cars.mjs`
plays every car's scenario headlessly; the SU7, Z9, G9L, ES8 and RX played through in the browser pane (desktop and a 390 px window),
mode, load, run and stop changed with the URL following. Not done: a production build in a copy, the owner's look.

