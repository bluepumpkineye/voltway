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
7X's failed its source check, so it is not built (section 13); the SU7's diffuser is left out (section 10). The camera on the Tech tab is free:
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
narrow), the millimetres of
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
| Sensor demo "What the car sees" (`sensors.ts`, `viewer/TechSensors.tsx`, `showroom/Sensors.tsx`, `layers.ts`; spec `Vehicle.sensors`) | built (3d, approved); tsc, eslint, production build in a copy, looked at on a wide and a phone-sized window, idle frames 0; see section 12 |
| Swivel screen (`swivel.ts`, `viewer/ScreenSwivel.tsx`, `hmi/harmonyos/ScreenDirection.tsx`, `showroom/Swivel.tsx`; spec `Vehicle.swivel`) | built (3e, approved); the frame is cut out of the cabin's merged mesh in the browser, no re-export; see section 13 |
| BOOST demo (`boost.ts`, `viewer/BoostKnob.tsx`, `hmi/harmonyos/Boost.tsx`, `showroom/Boost.tsx`; spec `Vehicle.boost`) | built (3e, approved); the screen it shows is a stand-in; see section 13 |
| Welcome sequence of the SU7 (the cluster flips up at start-up) | source found (Xiaomi's page) and a reference board made 2026-10-13; waiting for the owner's approval of the photographs (section 13) |
| Welcome sequence of the 7X | NOT built: no published sequence found (section 13) |

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

## 12. What the RX sees, Phase 3d (2026-10-12)

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

**The run** (`src/lib/tech/sensors.ts`, no value imports, run it with Node): 8 s, the car on the spot and the road rolling
under it like the launch's. It cruises at 50 km/h; a pedestrian (a plain figure of capsules, no face) stands at the kerb 46 m
ahead, is tracked by the tele path from the start, steps off at 1.6 s with 24 m to go, is judged to be in the car's way at
1.95 s and the car brakes at 2.2 s at 8 m/s^2 to a stop 3.6 m short of them at about 4.1 s, the nose dipping about 0.9 degrees on
its springs and the brake lamps on (the store's `braking`); the pedestrian crosses and the path clears. All of it is ours
and the panel says so. **The scene** (`viewer/TechSensors.tsx`): a flat sector on the floor for each lidar, fading outward, with
its edges, range rings (the forward wide path only) and a thin beam that sweeps to and fro on the demo's clock; three pulses that
go out from the car's outline (the ultrasonic sensors); a strip in front of the car that goes amber and red as the pedestrian
comes into it; blue returns on the pedestrian and a box that is white, amber, red and green by the state. A switch for each
group of sensors on the panel (`layers.ts`).

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
