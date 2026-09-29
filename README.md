# Voltway — Chinese EV Showcase

Explore Chinese electric vehicles in 3D, sit in the driver's seat, and use the
central infotainment screen the way you would in the car. Every control on the
dashboard changes what the vehicle reports back.

**Proof of concept: Xiaomi SU7 Ultra** — exterior, cockpit and a live HMI.
Six more cars are in the database with full specifications and cited sources.

## Running it

```bash
npm install
npm run dev
```

Then open <http://localhost:3000>. The built car is at `/vehicles/xiaomi-su7-ultra`.

## What's here

| Route | What it does |
|---|---|
| `/` | Landing page, vehicle grid |
| `/vehicles` | All seven cars |
| `/vehicles/[slug]` | Exterior orbit, interior view, live dashboard, spec tables, sources |
| `/compare` | Cross-vehicle table, CLTC and WLTP kept apart |

Each vehicle page has three views:

- **Exterior** — orbit the car, contact shadows, clamped so the camera can't go under the floor
- **Interior** — seated at the driver's eye point in a full cabin (its own GLB, streamed in behind the exterior), parked on the Shanghai riverside at golden hour: the cabin is lit by a Cycles bake of that daylight through the glass, you look out at the skyline, and the centre screen runs the live HMI at true 16.1″ scale
- **Dashboard** — the same HMI, flat and full size. The SU7 Ultra's is rebuilt from Xiaomi's own HyperOS screens: the parked desktop with the car, the three-card driving desktop, the dock with both climate zones, Settings with the car's real drive modes (Eco, Standard, Sport, M1 Slippery, M2 Novice, Drag race, Super power saving) and the Ultra's Track Master app

All three read one Zustand store, so switching to Sport updates the in-car
readout, the external metrics panel and the cabin lighting together.

## Data honesty

Two rules are enforced in the schema and the UI:

1. **Range cycles are never mixed.** CLTC typically reads 25–35% higher than
   WLTP for the same car. Every figure carries its cycle, and `/compare` gives
   them separate columns rather than one blended number.
2. **Modelled figures are labelled.** Manufacturers publish one range per
   variant on one cycle. The per-drive-mode spread in `lib/performance.ts` is
   derived from that figure to show the trade-off, and the UI says so. Charge
   times fall back to C-rate or peak power with a taper factor only when no
   manufacturer figure exists.

Sources are cited per vehicle in `src/data/vehicles/*.ts` and rendered on each
vehicle page.

## The 3D pipeline

The car is **built parametrically in Blender**, not scanned or generated.
Image-to-3D was tried first and could not produce usable car geometry.

**The working manual is [`docs/3d-pipeline.md`](docs/3d-pipeline.md)**. It
covers phases, quality gates, the interior workflow, the lighting bake, web
integration and every lesson that cost time. The reusable library is
`blender/scripts/carkit` (module map in its [README](blender/scripts/carkit/README.md)).
The SU7 modules below are that car's data plus calls into it.

```
blender/scripts/
  carkit/            the part catalogue and pipeline library (body loft, caps,
                     panels, lamps, aero, grilles, fittings, wheel presets,
                     interior sweeps/seats/wheel/door cards/trims, materials,
                     bake, export, QA: refmatch, leaks, web_capture, ...)
  su7_interior.py    the cabin, from hardpoints read off the camera-matched
                     press render (dash, screens, wheel, seats, console, door
                     cards, pillars, headliner, closing trims)
  su7_surface.py     master surface: C2 profile curves, a two-segment section
                     (centripetal Catmull-Rom, arc-length resampled) with a
                     real shoulder crease, twin hood crowns, lower-door
                     undercut; a piecewise profile with a crease at the cowl
  su7_nose.py        the wrapped nose and tail, parameterised by (w, v)
  su7_panels.py      panels with real shut lines (curved door edges), the
                     greenhouse (body-colour rails and C-pillar, glazing cut
                     to the window outlines), wheel openings and quarter light
                     cut by exact booleans, the recessed black U with its
                     yellow lower blade, shell, liners
  su7_front.py       headlamps, splitter, intake mesh, plate + lettering,
                     hood stripes, roof lidar - projected onto the body; parts
                     that wrap a corner are ray-cast onto the built meshes
  su7_rear.py        light bar, wing, ducktail, diffuser, wordmark
  su7_side.py        mirrors, flush handles, carbon skirts, side stripe and
                     script, fender vent, charge-flap shut line
  su7_wheels.py      forged five-hairpin wheels, carbon-ceramic brakes
  su7_materials.py   material library (+ export_safe() for the glTF path)
  su7_textures.py    carbon weave baked to real pixels
  scene_setup.py     studio light rig, floor, camera book, Cycles, colour
  build_su7.py       exterior entry point; UV pass; envelope + cabin checks
  export_gltf.py     rebuild, bake the cabin's lighting, export both GLBs
  rx_interior.py     the Luxeed RX cabin (white and red trim), from the
                     camera-matched press render
  export_rx.py       the Luxeed RX GLBs, baked cabin included (web_full)
  ref_match.py       camera-matched overlays against the reference photos
  surface_qa.py      zebra reflection-line renders and close QA cameras
```

To rebuild everything the web app loads, run this inside Blender (5.2, with the MCP addon):

```python
import sys; sys.path.append(r"<repo>/blender/scripts")
import export_gltf
export_gltf.web()   # exterior + interior GLBs, cabin probe, outside world, ~7 min
```

It writes `public/models/su7-ultra.glb` (exterior),
`su7-ultra-interior.glb` (the cabin, with Cycles lighting baked per vertex),
`su7-ultra-cabin.hdr` (the cabin's reflection probe), and
`su7-ultra-outside.jpg` / `su7-ultra-outside-light.hdr` (the world outside the
glass, from a Poly Haven HDRI: the view out and the light on the bodywork seen
from inside).

`build_su7.main()` prints the evaluated triangle count and fails loudly -
"geometry outside the car's envelope" - if any modifier throws a vertex off the
car, which is how every stray line and spike in this project first showed up.
With the interior on it also lists any cockpit part that comes within 12 mm of
the body's skin.

To check the body against the side photograph:

```python
import ref_match
ref_match.overlay("side_turntable", "check")   # -> renders/match/*_overlay.png
```

The overlay draws the model's outline (magenta) and every panel boundary
(cyan) over the photo, through the photographer's own camera.

### What decides whether it reads as the SU7 Ultra

**Match the photographer's camera before measuring anything.** The showroom
side photo is a ~50 mm lens at 6.6 m, so the nose and tail - a metre further
from the lens than the wheels - come out 12 % small, and a feature's height
depends on how far across the car it sits. Hardpoints read off photos by eye
put the headlamps 182 mm and the wing 200 mm too high, and the model was being
compared, orthographic, against a perspective photo - which is why its front
read long. `ref_match.py` solves the camera from the wheelbase, both wheel
centres and the ground line (all land within 0.2 px), renders the model
through it, and overlays the outline and panel lines on the photo. Published
figures agree: the MIIT declaration gives 1007 mm front and 1108 mm rear
overhang, which the model matches to 7 mm.

**The front is low.** The top of the car at the headlamps is 0.73 m off the
ground, level with the top of the front tyre; the windscreen base sits at
x = 0.945, z = 0.97. The first build carried the hood forward at 0.90 m and
stood the nose up as a tall face - a "long nose" by volume, not by length.

**A nose cannot be an x-loft.** On the SU7 the bumper is at x = 2.52 when
z = 0.40 and at 2.557 when z = 0.60, so a surface parameterised by station x
cannot describe it. Forcing it to ended the car in a flat plate, and every front
part had to be a box bolted to it - that is what produced the slatted-grille
face. The ends now have their own (w, v) patch in `su7_nose.py`, joined to the
flank along the real bumper shut line.

**Build from the reference, never invent.** The production Ultra has a closed
nose (no upper grille), sliver lamps slanted up 85 mm toward the outside, a
black "U" below the plate and no canards. The hardpoints in `su7_nose`,
`su7_front`, `su7_rear` and `su7_wheels` come from a breakdown of the reference
photographs, and the code comments mark which values are measured.

**Curvature, not just slope, must be continuous.** A highlight is an
iso-curvature band, so a merely-C1 profile (PCHIP) breaks it into straight
segments at every control point. The profile curves are natural cubic splines
(C2), and the section uses centripetal Catmull-Rom, which cannot cusp or loop.

**Paint is a dielectric with a coat.** Metallic 0, base specular nearly off,
colour in the base, gloss in a clearcoat at roughness 0.035. The SU7 Ultra
yellow is a solid colour, so there is no flake.

**Light it like a car, and calibrate the lights.** A car is a mirror with
colour in it. The rig has a 9 m flank strip, a top box, kickers and wheel
bounces - with powers set so a lit panel's radiance sits near its albedo at
exposure 0. Khronos PBR Neutral is the view transform in Blender, and three.js
uses the identical `NeutralToneMapping`, so the web view matches the renders.

**Shut lines and openings are geometry.** Panels are inset by half a gap on
every shared edge over a dark shell; intakes are booleaned through the fascia
and backed by unlit tunnels; the lamps sit proud of the body with a seal band.

### Things that cost real debugging time

- **A flat front plate** - see above. The root cause of the "toy" front.
- **Clamping panel rows up to the wheel arch** collapsed 786 of the quarter
  panel's 1428 faces to zero area; Solidify with even offset then divided by
  the near-zero angles and threw vertices 150 mm off the body. Each column now
  spreads its rows between its own lower bound and the top.
- **The nose remap saturated at the fender crowns** - the join ring is not
  monotone in height there - and left the whole top of the nose unbuilt, which
  read as a black slot above each headlamp.
- **Bevel with arc mitres went singular** where the cap rows converge on the
  centreline and threw vertices to x = -1.4e20. The caps carry no bevel.
- **The shadow shell ran straight through the wheels** and hid the inner
  spokes behind a flat grey disc. It now has its own wheel openings.
- **Orange peel at the wrong scale** (1.1 mm cells, 1.2 mm bump) acted as a
  very rough clearcoat and smeared every softbox across whole panels; the
  yellow read as cream. Real orange peel is microns high over 3-5 mm.
- **The first light rig was ~5x too hot.** Khronos Neutral desaturates
  anything past its peak toward white, which also read as cream.
- **Wheel placement matrices with determinant -1** silently invert winding.
  Wheels are placed with proper rotations.
- **`bpy.ops` from outside the UI** (the MCP runs code from a timer) has no
  active object; `object.join` and the glTF exporter both need an explicit
  `context.temp_override`.
- **`KHR_materials_transmission` blanks the frame in three.js.** Glass renders
  with real transmission in Cycles; `export_safe()` swaps it for dark opaque
  glass before export.
- **A procedural carbon Checker** exported as 0.8 grey plastic. The weave is
  baked to real pixels, on world-space UVs so a tow is 3 mm on every part.
- **Nearest-point projection across a corner.** Where the nose cap meets the
  fender at an angle, neighbouring headlamp points snapped to different
  surfaces and the lens spanned the corner as a flat chord; the body poked
  through it. Anything that wraps a corner is now ray-cast from inside the
  corner onto the built meshes.
- **The cap met the flank at up to 16 degrees.** Its height blend ignored the
  flank's slope at the join. The blend now leaves the join along the flank's
  own tangent (G1), which the zebra render confirms.
- **Trimming panels to the wheel arch in the grid** left the two columns either
  side of the opening's edge with different row spacings; the sheared quads
  showed as a line up the fender, and a curved door edge made the solver
  oscillate and tear the shut line. Wheel openings and the quarter light are
  now cut by exact booleans.
- **Rounded per-segment sample counts** made the section slide along itself as
  x changed - the surface was discontinuous in x and every window edge came out
  sawtoothed. Sections are resampled by arc length.
- **The hood's normal flipped downward** on the centreline, where the old
  "point away from the centreline" test is a coin toss; the stripes were offset
  into the hood and vanished after 0.4 m.
- **Hood grain** was Monte Carlo noise in the top light's reflection, not
  orange peel: gone at 1024 samples. The adaptive threshold is now 0.005.

### Reference imagery

`blender/reference/su7-ultra/` holds CC-licensed photographs from Wikimedia
Commons, used as modelling reference. They are not redistributed with the app.

| File | Source | Licence |
|---|---|---|
| `side.jpg` | Xiaomi SU7 Ultra yellow showroom side view 2026 (dllu) | CC BY-SA 4.0 |
| `front.jpg` / `rear.jpg` | Xiaomi SU7 Ultra front/rear view, April 2025 | CC BY-SA 4.0 |
| `front34.jpg` | Xiaomi SU7 Ultra grey front | CC BY 4.0 |
| `interior.jpg` | Interior of Xiaomi SU7 Max, 2024-04-13 | CC BY-SA 4.0 |
| `ultra001.jpg` | Xiaomi SU7 Ultra 001 | CC0 |
| `side_turntable.png` | Showroom side view supplied by the project owner | reference only |

## Mounting the HMI in 3D

The dashboard is a **real React DOM tree** warped onto the screen quad, not a
canvas texture — so the text stays crisp and the buttons are genuinely
clickable in the cabin.

- Every frame the quad's four corners are projected and the 1280×800 surface
  is mapped onto them with a 2D homography (`quadToCss` in
  `src/components/viewer/CarModel.tsx`). drei's `<Html transform>` was used
  before, but it builds a CSS 3D camera in world units. In a metre-scale
  scene Chrome's compositor drew the HMI a full screen-height above where
  layout and hit-testing put it.
- The screen's orientation is derived from its **face normal**, not from vertex
  order — the glTF exporter reindexes meshes, and assuming corner 0 is
  bottom-left rotates the UI by 90°.

The HMI also stops pointer events at its own surface: drei's HTML sits inside
the R3F React tree, so without that a tap on the screen reaches OrbitControls
and drags the camera.

## Performance

Exterior: **2.4 MB GLB** (Draco), 375k triangles, 32 draw calls. The cabin is
a separate **4.4 MB GLB** (170k triangles, 38 draw calls) plus a 0.9 MB HDR
probe, and the outside world adds a 1.0 MB JPEG and a 0.4 MB HDR. All of it is
preloaded behind the exterior view, so going inside is instant.
The app loads Draco through the local decoder in `public/draco/`.

## Known limits

- Only the SU7 Ultra has a 3D model. Other cars show a labelled fallback.
- The exterior is a parametric reconstruction from photographs, not a scan.
  Its outline, door and window lines match the side photograph through the
  matched camera, but the surfacing is not class-A.
- The cabin's lighting is baked, so it is static. The ambient light guides
  glow but do not light the trim, and reflections come from one probe shot
  between the front seats.
- Door toggles change the status graphic only. The painted doors are merged
  into the body, so a door card swinging alone would pass through its own
  door; opening both needs the exterior doors split into their own nodes.
- Navigation and media content is illustrative, not a live service. The
  playlist and album art are invented, and Track Master's circuit, lap times
  and temperatures are a demo session, not real track data.
- Only the SU7 Ultra's HMI is rebuilt from its maker's screens (HyperOS). The
  other cars share a generic skin until theirs are built.
- From inside, the mirror housings reflect the sky where Cycles shows the car's
  own flank: image-based light has no local reflections.

## Stack

Next.js 15 (App Router) · TypeScript · React Three Fiber + drei · Zustand ·
Tailwind v4 · Blender 5.2 for the model pipeline.
