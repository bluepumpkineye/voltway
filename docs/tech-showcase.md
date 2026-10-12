# The Tech tab: demonstrating what a car's technology does

The showroom's sixth tab (`/showroom/[slug]?tab=tech&demo=<id>&device=<phone|dashboard>`). Each car lists
demonstrations (`Vehicle.tech`); the tab plays one at a time, started from a device the visitor holds
as the owner would (the maker's phone app, or the car's own screen), on a clock they can also pause,
replay, scrub and slow down. Every demonstration is a **simulation built from the maker's published
figures**, never its footage, and says so on screen.

The plan and the research behind it were approved on 2026-10-08 (kept outside the repo).
Status: Phase 1 (the motion rig and the tab) and Phase 2 (the Luxeed RX's "Park from your phone", with
its two devices) are built; the other demos are Phase 3.

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
| Electric spoiler | ● (absent on the Nurburgring Limited) | | |
| Active closing grille | ● | ● | ● |
| Power-closing doors / frameless doors | ● / ● | no / ● | ● / ● |
| Hidden electric handles | not checked | not checked | ● |
| Power tailgate (position memory) | ● (●) | ● (●), kick-sensing | ● (●) |
| Electric folding mirrors | ● (tilt in reverse) | ● (tilt in reverse) | ● |
| V2L | 3.5 kW | 6 kW | 6 kW |
| HUD | 56 in | 26 in (Ultra) | 36.21 in |
| 540-degree transparent chassis | ● | ● | ● |
| Air suspension (chambers) | dual-chamber | dual-chamber | single-chamber row; air + electromagnetic on the 4WD Ultra (verify) |

Unverified, so not for display: the SU7 Ultra wing's step angles (sources say three steps; active
diffuser 0-16 degrees in two steps per Xiaomi's pre-sale description), the 7X's five ride heights,
Huawei's slot-type list (parallel, perpendicular, angled, unmarked, very narrow), the Denza Z9 GT's
rear-wheel behaviour in the crab walk and its 11 cm parking margin.

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
| The demo on the SU7 and 7X | when their wheels are split (the planner takes the car's own layout, body and published width) |
