# XPENG Cabin 360 benchmark: same-camera A/B for the Mona L05 cabin (2026-11-18)

The owner set https://xpeng.guru/lineup/xpeng-l05/#colours ("Cabin 360") as the render target for the Mona's interior.
We stay on live three.js; the panoramas are the **measuring stick**, not a replacement for the 3D cabin.

## What the target is

Ten equirectangular JPEGs (4096 x 2048, 0.55-0.92 MB), XPENG's own offline renders:
`https://xpeng.guru/wp-content/uploads/data/l05-interior-pano/xpeng_l05_interior_pano_<trim>_<front|back>.jpg?v=1`,
trims `dark-grey light-grey iris titanium-green star-purple`. The viewer is a ~10 KB WebGL script that draws one image on a
cube (yaw 0 = straight ahead). `front` = a camera at the driver's head, `back` = a camera at the rear-seat centre, so every
landmark seen in both can be triangulated. They are saved (gitignored, not redistributed) in
`blender/reference/xpeng-mona-l05/pano/`; re-download with the URL above (curl needs `--ssl-no-revoke`).

## Tools (all in the repo, run from the repo root)

| Tool | Use |
|---|---|
| `scripts/photo-tools/pano.cjs view <pano> <out.png> <yaw> <pitch> <fov> [W] [step] [marks]` | rectilinear view with a labelled angle grid; `pix <yaw> <pitch> <fov> <W> "x,y,name;..."` converts view pixels to pano angles (read the pixels off the image, let the tool do the maths) |
| `scripts/photo-tools/pano_solve.cjs <landmarks.json> <front\|back> [--use a,b]` | camera position from landmarks whose 3D position in OUR model is known; landmarks not in `--use` are held out and audit the model. `tri <landmarks.json> <cams.json>` triangulates a landmark read in both panos |
| `blender/scripts/mona_pano_dump.py` | builds the cabin, dumps every object's box (model coordinates) |
| `blender/scripts/mona_pano_ab.py` | `build <blend>` (4 min, whole car) then `render <blend> <front\|back> <out.png> [W] [samples]`: a Cycles equirect of OUR cabin from the solved camera, under the hall light, camera rays see a hazy grey |
| `scripts/photo-tools/pano_ab.cjs <target> <ours> <prefix> "name:yaw:pitch:fov,..."` | per view: target / ours / edge overlay (red target, cyan ours) / 50-50, plus tonal stats (luma p5 p50 p95, saturation, fine-detail energy `hf`) |

Data: `blender/scripts/mona_pano_landmarks.json` (readings), `mona_pano_cams.json` (poses). Sheets and equirect renders:
`blender/renders/pano_ab/` (gitignored).

## Method notes

- The cabin file alone is a sealed box (black leak fillers sit where the exterior's glass lets light and view in), so the
  harness builds the whole car and renders under `carkit.bake.thin_glass()` like the light bakes do.
- Poses are solved from OUR screen's four corners only (17.3 in, 0.383 x 0.215, top leaning forward 12 deg): front rms 0.51 deg,
  back 0.05 deg (centre line, y 0.001). Everything else is read RELATIVE to the screen. Triangulating the screen corners from
  both panos returns them within 2 cm of ours with 1-3 mm ray gaps, which validates the method.
- The solved front camera stands inside our driver headrest; the harness hides compact parts that contain the camera.
- Readings are by eye on a 2-degree grid (about +-0.2 deg, 3-10 mm at these distances).

## Hardpoint audit (target - ours, relative to the screen; x forward, y left, z up)

| Part | Result |
|---|---|
| Wheel centre (logo) | x +6 mm, z 0, **y -44 mm**: the real wheel is at y 0.366, ours 0.410 (DRIVER_Y). Both panos agree (41 and 52 mm when each is solved from the screen alone) |
| Driver eye point (the front camera) | (-0.158, 0.361, 1.304); our `driverEye` is (0.06, 0.41, 1.24), 0.22 m further forward |
| Passenger headrest (pillow) | about 17 cm further back (x -0.345 vs -0.173) and about 6 cm higher (z 1.256-1.438 vs 1.193-1.374); same size. The back camera's sheet agrees (real headrests larger and closer) |
| Eye to screen | 0.70 m real; 0.49 m with our `driverEye` |

**Resolved in Phase 2 (below):** it was the front cockpit group that stood too far back, not the seats.

## A/B statistics (12 matched views, our Cycles render vs the target, same camera)

- Fine-detail energy (`hf`): ours is about 0.5x the target (0.3-0.75), in every view.
- Deepest shadows: target luma p5 11-15, ours 27-35 (front views).
- Highlights: ours clip (dash p95 249 vs 148); saturation lower (0.08-0.15 vs 0.16-0.31, partly our lavender trim vs the
  target's light grey).
- Missing against the target: two-panel glass roof with blind, rear-vent console, seat-back pockets and handles, 3-seat rear bench
  (we have two seats and a centre piece), pleated door fabric, fine hex perforation, squircle wheel details, lime piping and
  stitching, the hazy outside plate.

## Next (Phase 2, by visual weight)

1. One more body anchor, then settle the seat/dash relationship.
2. Dash + screen + wheel, console bridge, seats, door cards, roof/rear; materials (perforation, woven inserts, piping, pleats).
3. Light: a 4096 bake that modulates the hall (the 06T light-map lesson, docs/3d-pipeline.md), a cabin-specific reflection probe,
   an outside plate; the five official trims coloured from the panoramas; a per-car cabin-FX preset.

## Phase 2, first slice (2026-11-18)

Built from the audit, in `blender/scripts/mona_interior.py` (each change is one constant or one small function) and
`src/data/vehicles/xpeng-mona-l05.ts`:

- **The front cockpit group moved forward by `FRONT_DX = 0.17`** (dash face, screen and its arm, wheel, console, chrome strip and
  ambient line; the dash's cowl end stays the body's, the ramp is re-fitted). Evidence, all relative to the screen: the real
  seats' headrests are about 17 cm and the real B-pillar's front edge 13 cm further back than ours, the real eye point is 0.70 m
  from the screen against our 0.49 m, while wheel, console and screen agree with each other (the console's pocket and lime slit
  overlay the target's to a few millimetres). One translation explains all of them, keeps the seats where the owner's seat rule
  put them, and explains why the Interior tab always had to look from between the seats (the wheel stood 10-15 cm too close to
  the eye). The three anchors disagree by +-5 cm (pillar 0.11, seat 0.17, eye 0.21); 0.17 is their middle. `0.0` undoes it.
  The panoramas' two cameras moved with the screen (`mona_pano_cams.json`): the front one now stands 13 cm AHEAD of our driver
  headrest, where a driver's eye is.
- **Wheel:** centre line y 0.366 (was 0.410); rim 0.148 radius (was 0.176: the panorama's rim is 0.30 m wide); the letter X (9 mm) is
  replaced by the XPENG emblem, 34 mm wide, from the nose trace (`build_wheel_emblem`). The A/B overlay now lands the emblem and
  rim on the target's.
- **Console lid** profile re-read from the front panorama (the pull tab is at x 0.147, z 0.915 on the centre line): smooth, no dip.
- **Colour:** the built interior is the real LIGHT GREY (dark steel dash and wheel, pale cool-grey leather, dark shells, lime
  piping), measured with `scripts/photo-tools/pano_probe.cjs` (twelve named patches, same views in all five trims). New material
  `INT_Piping_Accent` on the seat piping and the console slits so a trim recolours them together.
- **Five official trims** in the vehicle data (Light Grey as built, Dark Grey, Iris, Titanium Green, Star Purple). The real Dark
  Grey is an all-dark cabin (seats too), unlike the earlier two-tone guess; the piping accent is lime / lime / pale silver-lilac /
  teal / purple. Seat leather carries its colour in a texture, so its trim entry is a multiplier on that map.
- Viewer calibration: an albedo displays at about its own sRGB value on the Cabin FX path (leather 188 -> 193, dash 147 -> 155), so the
  panorama's colours are used directly, then checked with a per-material ID pass at the two solved cameras.

Not done yet: door-pod slits, seat-back pockets, pleated door fabric, the two-panel glass roof, the rear-vent console's detail, the
3-seat rear bench, per-material light (the viewer's light is flatter than the panorama's: dash top 2.5x its face there), the
outside plate, the per-car Cabin FX preset, glow on the slits.

### Verification (same day)

- **Viewer colour check**, a per-material ID pass at the back camera, all five trims (what the viewer displays / the panorama's patch):
  Light Grey (as built) leather 1.00, wheel 1.00-1.08, shells 1.00-1.08, console leather 1.02-1.06, dash 1.22 (from the rear the top
  pad dominates), headliner 1.2-1.3 (the alcantara's sheen). The first pass of the other four trims was off by up to 1.5x (dark
  seats too light, dark shells too dark); after one correction by the measured ratios Iris reads 0.89-1.05, Dark Grey's dash and
  console leather 1.02-1.09, Titanium Green's dash and wheel within 1.07-1.27 and 0.94-1.11. A last small pull-back on the dark
  shells and the Dark Grey seat leather was applied from the same model and not re-measured.
- **Same-camera A/B (12 views, Cycles hall render):** the back-row views now match the target's tonal profile (seats median 64 vs 70,
  deepest shadows 25 vs 23, door cards 67 vs 56-68, floor 133 vs 147); fine-detail energy is still about 0.5x; the console view is
  brighter than the target (median 211 vs 149) because our light is flatter.
- Cabin export: 1.70 MB GLB, one AO atlas, 536 s. Interior tab checked in the viewer; type-check and eslint clean on the vehicle data.
- The dev server on port 3000 returned 500 during the check (two servers share `.next`); 3001 served the page.

Another session committed the Mona (abbc961) while this ran; that commit holds the harness files and an earlier `mona_interior.py` /
vehicle file, and the later edits of this phase (palette corrections, headrest, FRONT_DX, console profile, trim values) are
uncommitted on top of it.

## Phase 2, second slice: geometry (2026-11-18)

All in `blender/scripts/mona_interior.py` (one export, 410 s, 1.78 MB) and the trim table in `xpeng-mona-l05.ts`. Targets read from
close-ups of the Cabin 360 panoramas (`pano.cjs rect`), checked with the same-camera sheets (`blender/renders/pano_ab/p3/`).

- **Console pockets (the default view's centre):** the cup pocket's bezel is now a thick satin-metal frame (about 14 mm, was a 3 mm
  tube) and its outline overlays the target's almost exactly; a pill pull tab sits on the lid behind it; the tray has a slim satin
  bezel and one dark slit along its pad (as in the photograph), and its pad is darker (albedo 0.46 -> 0.27: it displayed 225 against 175).
- **Rear console:** the rear block is 17% narrower (`_hw`) and floats 0.165 m above the carpet (`_console_bottom`); its bottom edge now
  lands on the target's to the pixel. The rear vent panel is a black pill with four silver pill buttons.
- **Door cards:** the upper cloth is a new material `INT_Door_Pleat` (the band's colour plus a fine vertical pleat normal map, 8 mm
  pitch, `pleat_map`; every trim recolours it with the band), and each armrest carries the dark slot with the thin lime line on its
  inboard face (`_door_armrest`). Door fine-detail energy 0.97 -> 1.48 (target 2.27).
- **Seats:** front backrests taper to the shoulders (half width 0.276 -> 0.212 over the height; they were a slab), raised rounded pockets
  on the front seat backs (`_seatback_pocket`, in the band's colour so they read against the shell), a middle headrest on the rear
  bench, bevels on the backrest's shell and top.
- Checked in the viewer: pockets, door pleats, seat. NOT checked in the viewer: the rear console and seat-back pockets (both dev servers
  returned 500 when another session's rebuilds collided with the shared `.next`); they are checked in the Cycles harness only.

Still open: the seats' overall form (the pale face is still two flat panels with a quilted look missing), the two-panel glass roof (needs
the exterior glass), pleats are a little strong/regular in the viewer (the normal strength is 1.0; 0.6 would be softer), glow on the lime
slits, per-material light, outside plate, the wheel's spoke pods and silver clamp, the screen's mount.
