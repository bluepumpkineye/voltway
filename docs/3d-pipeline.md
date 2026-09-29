# The 3D pipeline — how a car gets into Voltway

This is the working manual for building a car: exterior, cabin, bake and web
integration. It is written from the Xiaomi SU7 Ultra build (car #1). Most of
it is now library code (`blender/scripts/carkit`), so the next car is mostly
**data plus calls**. The lessons that cost the most time are called out where
they apply. The full list is at the end.

---

## 0. What a finished car is

| Output | What it is | Budget |
|---|---|---|
| `public/models/<car>.glb` | exterior, Draco | 150–400k tris (hero LOD), ≤ ~35 draw calls |
| `public/models/<car>-interior.glb` | the cabin, lighting baked into a vertex attribute | ~150–200k tris, ≤ ~40 draw calls, streamed in behind the exterior |
| `public/models/<car>-cabin.hdr` | reflection probe shot inside the cabin | 1024×512 Radiance HDR |
| `public/models/<car>-outside.jpg` | the world outside, as seen through the glass (tone mapped at build time) | 4096×2048 JPEG, ~1 MB |
| `public/models/<car>-outside-light.hdr` | the same world, linear, lighting the bodywork seen from inside | 512×256 HDR, ~0.4 MB |
| `public/hmi/<car>/*.webp` | the HMI's car images, rendered from the build (parked desktop, assisted-driving model) | ~130 KB |
| `src/data/vehicles/<car>.ts` | `assets.modelUrl`, `interiorModelUrl`, `interiorProbeUrl`, `interiorOutside`, `driverEye` | — |

The SU7 Ultra's figures:

- **Exterior:** 375k tris, 32 primitives, 2.4 MB.
- **Interior:** 170k tris, 38 primitives, 4.4 MB.
- **Probe:** 0.9 MB. **Outside:** 1.0 MB view + 0.4 MB light.

The Luxeed RX's (`export_rx.web_full()`, 2026-09-28):

- **Exterior:** 383k tris, 2.3 MB.
- **Interior:** 201k tris, 39 primitives, 21 materials, 4.9 MB; the bake stores 114k vertices, and every primitive carries `_BAKEDLIGHT`.
- **Probe:** 1.3 MB. **Outside:** 1.0 MB view + 1.6 MB light (1024 wide), the SU7's world, cabin only.

### Ground rules (from the project owner)

- **Allowed:**
  - Blender native, including Geometry Nodes and Node Wrangler.
  - Poly Haven HDRIs and textures.
  - Open-source workflows.
- **Not allowed:** paid generators (Rodin, Hunyuan3D, …) and photogrammetry.
- **Materials must survive glTF.** Anything that only works in Cycles gets baked, or it isn't used.
- **Every checkpoint is a lit render**, never an unlit viewport grab.
- **Build every feature from the reference photos, and invent nothing.**
  - No roof racks or random bars.
  - No whole-lamp emission.
  - No merging into one mesh with one material.
- **A phase does not start until the previous phase passes its quality gate.**

---

## 1. Code layout

```
blender/scripts/
  carkit/                 the reusable library (see carkit/README.md)
    geom mesh cut place   curves, mesh builders, booleans, placement
    body/                 LoftBody, WrapCap caps, CarBody, panels, fascia, morph
    parts/                lamps, aero, grilles, fittings, wheels (presets)
    interior/             Sweep, steering, seat, DoorCard, cabin trims, fittings, materials
    materials surfacemaps textures scene
    bake export build preview
    qa/                   refmatch, checks, zebra, leaks, hmi_capture, web_capture
    jev/                  the decision layer (section 8): finder, triage, review, onboard
  jev_cli.py              the decision layer from the shell
  su7_*.py                the SU7's DATA and thin calls into carkit
  su7_interior.py         the SU7 cabin
  build_su7.py            exterior entry point
  export_gltf.py          merge, bake, export (web())
  rx_interior.py          the RX cabin
  export_rx.py            the RX GLBs, in a background Blender (web(); web_full() with the cabin)
  ref_match.py            the SU7's solved cameras
```

Per car you write:

- `<car>_surface.py`: the profile curves
- `<car>_nose.py`: the caps and the CarBody
- `<car>_panels.py`: shut lines and openings
- `<car>_front.py`, `_rear.py` and `_side.py`: calls into `parts`
- `<car>_wheels.py`
- `<car>_materials.py`
- `<car>_interior.py`

The templates in `carkit/templates/` are skeletons for the first two. `carkit.body.morph.from_donor()` scales a donor car's curves onto new main dimensions to give a starting point.

---

## 2. Exterior, phase by phase

### A. References and cameras (gate: overlays within a few px)

1. Collect references into `blender/reference/<car>/`:
   - side, front, rear and 3/4 views
   - a cabin shot from the rear seat
   - details
2. **Solve the camera before measuring anything.** Use `refmatch.solve_side_camera()` from:
   - the wheel centres
   - the ground line
   - the wheelbase
   - one check point at another depth
3. Register the result with `refmatch.register()`.
4. Read hardpoints through the solved camera with `refmatch.on_plane()`, `ray()` and `project()`.

> Eyeballing a perspective photo put the SU7's lamps 182 mm and its wing 200 mm too high.

**The rear needs its own photographs.** A side photograph cannot see the tail face: its tail outline is formed where the surface faces the camera's ray, about 18° off rearward, so it bounds the corners in plan and says nothing about the centreline. The SU7's first rear was built from the side view alone and came out as a "big round bottom" (renders/rear). Rebuild it from 2–3 rear three-quarter shots (`reference/su7-ultra/rear/`):

- **Use a known size on the tail face as the ruler** and read ratios in each photo, averaging left and right views. A plate works, but check which plate: a show plate in a 440 × 140 mm holder, or a 480 × 140 mm NEV plate? Check it against a second official dimension in the same photo. The SU7's 1,560 mm wing span (MIIT) put its plate at 437 mm.
- **Distrust camera fits whose anchors all sit in one patch.** The flank's handles, charge door and wheel constrain a rear three-quarter camera poorly in distance versus focal length. Extrapolated to the tail, three such fits disagreed by 10–15 %, and a bundle adjustment over all of them did not converge. The plate ratios agreed across three photos to ~1 cm.
- **Check length and overhangs against the type-approval filing, not a launch article.** The Ultra is 5,070 mm (overhangs 1,007 / 1,063); 5,115 mm is the filing's alternative with a longer rear overhang.

### B. Master surface (gate: zebra renders continuous, dims within 10 mm)

- **`LoftBody`:** profile curves along x, plus a section in (w, v).
  - The profile curves are natural cubic splines (C2), not PCHIP. Highlights are iso-curvature bands, and a C1 curve breaks them.
  - The sections are centripetal Catmull-Rom, **resampled by arc length**. With rounded per-segment counts the surface slid along itself and sawtoothed every edge.
- **Nose and tail caps:** a `WrapCap` patch on each end, joined G1 to the flank.
  - A nose cannot be an x-loft: the bumper sits at two x values over its height.
- **`CarBody`:** projection and placement on the combined surface.

### C. Panels and openings (gate: shut lines 4 mm, no sheared quads)

- `body.panels.build_panels(specs, …)`: panels inset half a gap on every shared edge, over a dark shell.
- **Openings are exact booleans on the half sheet, before mirroring.**
  - `cut.cut_arches` for the wheel arches.
  - `cut.difference` for everything else.
- **An open sheet keeps pieces of the cutter.** Hole-tolerant exact booleans leave cutter faces on a sheet with no volume. Take `cut.sheet_bvh()` before the cut and run `cut.prune_off_sheet()` after it.
  - The SU7 quarter-light cut left a painted shelf across the rear cabin. From outside it is invisible; from the seats it is a sheet of paint.
- **A shut line that turns a corner is cut with `cut.slot()`.** It is a thin tube swept along a surface path, such as a trunk lid's edge running down the tail and over onto the deck. No single sweep direction suits a prism there. See `su7_panels.lid_edge_path`.
- **Butt panels where the real car has no line** (`gap=dict(x0=False)`). A cap/flank join is a construction seam, not a shut line. Left gapped, the SU7's quarter-to-tail join drew a line down the rear corner and across the decklid.
- **Every opening needs a dark back.** Give a vent, pod or recess a tunnel or pocket in the `shadow` material. Through the SU7's bigger rear vents, the corner's painted inner face showed as a yellow flap.
- **A cap panel's height limits are exact only on the centreline.** `cap_rows` picks each row's v at w = 0 and keeps it across the car. On a tail whose v rises toward the corners, a panel ending at z 0.35 in the middle ended at 0.43 at the join. Where a panel must reach below a bumper's edge, check that edge's height at w = 1 (`cap.point(1.0, v)`); the SU7 opened a black hole under each rear vent.
- **Overlapping panels on a wrapping corner need matching column density.** A panel standing 3 mm proud still dips under the one behind it if its columns span the corner as flat chords. `fascia.valance` now packs its columns toward the joint, as `cap_rows` does. Evenly spaced, the SU7's last bumper column chorded 50 mm of the corner, and a yellow tab showed through.

### D. Parts from the catalogue (gate: contact sheet reviewed)

| Module | Parts |
|---|---|
| `parts.lamps` | lens, seals, projector |
| `parts.aero` | rear wing, ducktail, splitter, diffuser, corner fin, side skirt |
| `parts.grilles` | diamond, hexagon, slats and dots meshes |
| `parts.fittings` | mirrors, flush handles, vents, badges, plate, lidar |
| `parts.wheels` | presets: `su7_ultra_hairpin`, `aero_5window`, `turbine_10`, `y_spoke_5`, `twin_5`, `multi_10` |

- **Placement:** anything that wraps a corner is ray-cast onto the built meshes (`Placer.radial`). Nearest-point projection spans the corner as a chord.
  - On a tail face, place analytically at a rear-elevation (y, z) (`TAIL.wv_at`): a radial cast from inside the corner shifts centreline points sideways by 5 cm.
- **Wings:** `aero.rear_wing(tip=dict(radius, drop))` curls the blade itself down at the tips. From every rear angle a flat bolted-on endplate read as a black slab.
- **Lettering:** `mesh.text_mesh(font=, resolution=4, spacing=, weight=)`.
  - Use the OFL fonts Blender ships (`datafiles/fonts`: Inter, Noto Sans CJK), so the glyph outlines baked into a shipped model are licensed to ship.
  - Keep the resolution at 4: Blender's default of 12 is ~3× the triangles a 30 mm badge needs.
  - `spacing` sets wide wordmarks; `weight` emboldens a regular face.
- **Review:** `preview.contact_sheet()` renders every catalogue part to `renders/catalogue/contact_sheet.png`.

### E. Materials (gate: patch values against the photo)

- **Library:** `materials.build_library(paint=, rim=, caliper=)`.
- **Paint** is a dielectric with a clearcoat. Solid colours get no flake, and orange peel sits at the micron scale.
- **Carbon** is baked to pixels (`textures.carbon_weave`), not a procedural checker. The checker exported as grey plastic.
- **Glass** has real transmission in Cycles. `materials.export_safe()` swaps it for dark opaque glass, because `KHR_materials_transmission` blanks the three.js frame.
- **Mirror glass** is `M_Mirror_Glass`, dim silvered glass. On polished chrome, the door mirrors read from inside as two white discs.
- **Tail lamps** are lit (`build_library(tail_lights=1.3)`, role `led_red_tail`), as in most rear photographs. Unlit, the SU7's tail read as a black band.
  - Keep the emission strength low. With Khronos PBR Neutral, a bright saturated red rolls off to salmon pink.
  - Retro-reflectors are `reflector`: red plastic that does not emit.

### F. QA (every phase)

- `build_su7.main()` prints the triangle count, the envelope violations and the cabin clearance.
- **Refactors must be bit-identical.**
  1. Take `build_su7.fingerprint()` before the change.
  2. Rebuild.
  3. Run `checks.compare()`.
  4. Re-baseline, on purpose, when the geometry is meant to change.
- Other checks:
  - `qa.zebra` for reflection lines
  - `ref_match.overlay(cam, tag)` for the outline and panel lines over the photo

---

## 3. Interior

### 3.1 Camera and hardpoints

1. Solve the cabin press render as a camera. The SU7 camera is `cabin_front`: (-0.714, 0, 1.390), pitched 25.4° down, f = 835 px at 1280×960, 12–18 px rms.
   - Fit it on trim edges, not glass edges: the residual lives there.
2. Read the hardpoints through that camera with `refmatch.on_plane(cam, u, v, plane)`:
   - screen
   - wheel centre and tilt
   - cluster
   - dash lip
   - band heights
   - console top
   - seat bights
3. Record them at the top of `<car>_interior.py`, with a comment saying where each came from.

The RX's cabin photo (`cabin_front`, a straight-on press render from between the front seats) shows almost no bodywork: only the A-pillars and the door belts. Its centre screen, of known size, fixed the depth, with the screen's position solved as extra unknowns (`rx_camsolve.solve_cabin`, 7.9 px). Where a feature sits on the centreline the ray alone cannot give its depth, since the camera is on the centreline too. The console was read on assumed heights and then checked against a second, oblique photo (`passenger34`, solved from points on the built cabin, 16 px).

### 3.2 Building blocks (`carkit.interior`)

| Block | Use it for |
|---|---|
| `Sweep(spine, section_fn, n, counts, outward=±1)` | Dash, console, armrests, seats. Fixed samples per section segment put every section control point on a grid column, so panels (`mesh(j0, j1)`), seams, `piping()` and `stitches()` land exactly on design lines. `outward` fixes the normal sign; the raw normal is T × (increasing section index). |
| `steering.wheel(col, lib, SPEC, centre, tilt)` | Rim segments (carbon or Alcantara), marker, hub, spokes, buttons and logo, all from a spec dict. |
| `seat.seat(col, lib, SPEC, bight)` | Cushion and backrest sweeps with panels, piping and stitching. A rear seat is the front spec rescaled. |
| `DoorCard(loft, x_front, x_rear, z_bottom, z_top, thickness)` | The body's own flank moved inward. It provides `band()` (upholstered panels), `carrier()`, `belt_cap()`, `armrest()` and `curve()` (paths for piping, handles and light guides). |
| `cabin.headliner`, `floor`, `sill`, `bulkhead`, `wall` | Offsets of the body loft, so the inside always agrees with the outside. |
| `cabin.edge_band` | A chord trim between two glass edges. Use it on **narrow, tight** pillars (A-pillar). An offset of the surface folds wherever the offset exceeds the radius of curvature: the first A-pillar came out twisted. |
| `cabin.pillar_trim` | An offset trim. Use it on **broad** pillars (C-pillar and sail). A chord across a broad sail cuts the corner and leaves an open cavity behind the trim. |
| `cabin.wheelhouse_trim` | The side trim behind a rear door: a wall over the arch, rolling onto an upper panel, with a closing strip to the door card. |
| `fittings` | Small parts every cabin needs: `box`, `slab`, `screen_quad` (the HMI contract), `round_slab`, `disc` (grilles, caps, rims), `plate_with_hole`, `ngon_cap` (a section's end), `lights` (the render rig). |
| `steering.LUXEED_RX`, `seat.LUXEED_RX_FRONT` | The RX's wheel (round hub in a chrome ring, framed brushed spoke pads, a U lower spoke, BOOST, the hexagon emblem) and seat (the SU7 bucket with a red centre `stripe` and a dark top `cap_from`). |

### 3.3 Closing the cabin: leak QA (gate: under 0.2% leak pixels per seat view)

From a seat, everything you see must be one of two things:

- interior trim
- exterior seen **through** glass (the hood, the mirrors)

Anything else shows as a sliver of paint in the web viewer.

```python
from carkit.qa import leaks as LK
cams = LK.cameras({"driver": (eye, aim, 24.0), ...})   # 6–8 seat views
rep = LK.find(cams, "SU7_Interior", ("SU7_Body", "SU7_Details", "SU7_Wheels"),
              see_through=("Glass", "Greenhouse_Black", "Roof_Rear_Black"),
              skip=("SU7Ultra_Shell_Shadow",), res=(240, 135))
LK.print_report(rep)      # gaps grouped by object and 10 cm cell
```

**Fixes the SU7 needed**, in the order the report found them:

1. Rear door cards: they did not exist at all.
2. `belt_cap`: the 5–7 cm slot between the card top and the glass.
3. `carrier` with a flange all round, so the card is a closed box. The slots at its edges showed the painted door.
4. B-pillar seal.
5. Footwell kick panels, running up to the belt outboard of the dash.
6. Dash top pad run up under the windscreen base. It had shown the cowl.
7. Headliner and A-pillars carried 2–3 cm past the glass headers.
8. Sail trim.
9. C-pillar as an offset trim.
10. Wheelhouse trims.
11. Parcel shelf and rear bulkhead.
12. The quarter-light boolean shelf (see 2C).

This took the SU7 from 2–4% leak pixels to about 0.1%. A magenta render (exterior materials flat magenta, glass hidden) shows the same gaps visually.

The RX (nine seat views, worst 7% to 0.14%) needed:

1. The rear wheelhouse trim moved inboard of the liner and above its top (7% → 2%).
2. The luggage area closed: the C-pillar trim carried down below the parcel shelf, and a sill trim from the shelf up to the rear glass's curved lower edge, which the painted tail cap wraps.
3. A flange from the C-pillar trim's front edge out to the skin.
4. An offset trim, not a chord, under the quarter light, where the greenhouse steps in (section 7).
5. Kick panels stepping in where the front liner narrows the footwell.

To find a stubborn leak, trace its rays: print what each hits in order. The RX's quarter-light rays reached paint inboard of the trim, which showed the trim was on the wrong side of the body's step.

### 3.4 Materials that read as photographed

- Trim is surface structure under soft light. `surfacemaps` makes periodic band-limited noise (FFT), with no seams.
  - Maps: leather grain, Alcantara, carpet, brushed metal, perforation.
  - They are sampled with world-space UVs in metres, via `build.ensure_uvs(force=…)` and a Mapping node at 1/TILE (it exports as `KHR_texture_transform`).
- **Nappa leather:**
  - roughness 0.40
  - clearcoat 0.12, coat roughness 0.25
  - grain normal map
- **Alcantara:**
  - roughness 0.94
  - sheen 0.85, exported as `KHR_materials_sheen`
  - fibre normal map
- **Accent colours** are back-solved from lit patches in the photos. The SU7 yellow is linear (0.48, 0.33, 0.058). With too little blue it rendered mustard.
- **Black carpet is not black paint:** albedo about 0.035.
- **Perforated Nappa (the RX's white):**
  - Its holes are about 1.1 mm on a 4 mm hex pitch (`rx_interior.perforation_maps`).
  - The catalogue's speaker perforation (2.4 mm holes) read as a pegboard on leather.
  - The holes are baked into the base colour as pixels, since a mask multiplied in the node tree does not survive glTF, and dimpled in the normal map.
- **Forged panel:** a generated flecked-stone image (`rx_interior.forged_image`) under a full clearcoat.
- **A dash's black glass band is not a mirror.** At screen-glass gloss it mirrored the sky through the side windows as a white slab. `INT_Band_Glass` (roughness 0.10, half coat) keeps the photos' soft reflections.
- **Spoke pads read as blank white under daylight in brushed aluminium.** The RX's are `gunmetal`.

### 3.5 Screens

- `screen_main` is a **contract** with the web app: one flat quad, a planar UV, facing the occupants.
- For renders:
  - `qa.hmi_capture.capture(slug)` screenshots the app's own HMI (`/capture/hmi/<slug>`).
  - `apply()` puts it on the quad as an emissive display.
  - `restore_plain()` puts the plain screen back before export, because the app draws the live DOM HMI there.
- The cluster ships its generated image (`su7_interior.cluster_image()`) as an emissive texture.

### 3.6 Render lighting, calibrated

The press render's "blacks" are lifted cool greys. For example, the dash face reads sRGB 54/57/66. That comes from soft overhead light, not light through the windows.

The cabin rig (`su7_interior.cabin_lights`) is:

- a roof softbox
- a back fill, kept out of glossy rays so it doesn't show in the mirror and screens
- two weak side fills

All four are invisible to the camera. Their powers are set by comparing patch values through the matched camera. A first rig at 10× read as a clay render.

Under daylight (3.7) the rig stays, at half power (`export_gltf.RIG_FILL = 0.5`), as a photographer's fill. Without it the pedals and the wheel hub sank to black; at full power the cabin read studio-lit again.

### 3.7 Daylight: the world outside

The cabin is baked under a real outdoor world, and the viewer shows the same world through the glass. The SU7 stands on the Shanghai riverside at golden hour (Poly Haven `shanghai_riverside`, CC0), set in `export_gltf.OUTSIDE`. The Luxeed RX stands in Beijing, on the paved square at Zhengyang Gate (Qianmen) on a clear spring morning (Poly Haven `zhengyang_gate`, CC0), set in `export_rx.OUTSIDE`. Before these, the view out was a dark studio gradient and the cabin read too dark.

1. **Pick the HDRI** from Poly Haven (`api.polyhaven.com/assets?t=hdris`), 4k `.hdr` into `blender/textures/hdri/`. Clear or low-contrast skies suit a vertex bake best.
2. **Turn it** with `scene.hdri_world(path, strength, rotation, clamp)`. Blender puts the image's centre column straight ahead (+X): a feature at image angle `a = (0.5 − u) · 360°` shows at `a − rotation`. Put the sun **behind** the car (in front it glares through the windscreen) and something worth seeing ahead. Check with a 16×16 Cycles render aimed at the brightest pixel's direction; the SU7's first guess was 180° out.
3. **Clamp the sun** (`clamp=8`): a clear-sky sun is ~40 000× the sky in a few pixels, and per-vertex it lands as hard-edged blotches.
4. **Let the daylight in:** wrap every cabin render and bake in `bake.thin_glass()`. As modelled, the glass passed **nothing**:
   - Principled glass tints what it transmits by its base colour, and ours is near-black (from outside, glass must read deep);
   - Cycles treats refraction as opaque to shadow rays, and with refractive caustics off a diffuse path through glass is dropped;
   - so `thin_glass` swaps in Fresnel-weighted Glossy over a tinted Transparent BSDF, with the light transmission of real glazing (`GLASS_VLT`: windscreen and front doors ≥ 70 % by GB 7258, privacy glass behind the B-pillar ~25 %).
   - The Fresnel node **inverts the IOR on back faces**. On a single-sided sheet seen from inside, the windscreen went totally reflective past 41° and mirrored the dash where the road should be. `thin_glass` feeds 1/IOR on back faces.
5. **Measure the sun** for the exterior's directional light with `bake.sun_from_hdri(path, clamp, rotation, turn)`. It returns the direction in the viewer's axes after the cabin's `rotation` and the exterior's `turn`, the sRGB colour, and the intensity (the brightest channel of the irradiance the clamp removes). Pick the exterior turn so the default camera, ahead-right of the car at azimuth −42.9°, has the sun at its back: turn = −42.9° − (image angle − rotation). The function reproduces the SU7's shipped sun to 1e-4. For Zhengyang Gate the sun is 37.8° up, #fffbd2, 4.31. The gate tower stands 67° from the sun and is backlit, so the default shot looks past the car to the Great Hall of the People instead.
6. **Hide the lookdev floor** (`Ground`) in `cabin_lighting()`: the HDRI has its own ground. The glossy studio floor mirrored the skyline under the car like a river, which the viewer never shows.
7. **Export the world twice** (`export_outside()`):
   - `bake.backdrop()`: the view out, as a JPEG tone mapped exactly as three.js does (× strength × exposure, `NeutralToneMapping`, sRGB). The viewer shows it as an sRGB `scene.background`, which three.js does not tone map again.
   - `bake.backdrop_light()`: 1024×512 linear HDR, clamped like the bake, to light the bodywork: the exterior's whole environment, and inside, what is seen through the glass. Lit by the JPEG, whose sky tops out at 1.0, the mirror housings' clear coat stayed near-black (sRGB 9–26 against ~100 in Cycles).
8. **Write HDRs with `bake.write_hdr()`, never `Image.save()`.** Blender 5.2 saves a float `.hdr` through the sRGB curve (0.18 → 0.461) even with the Raw view transform. The light HDR and the cabin probe shipped display-referred until they were rewritten with a plain RGBE writer (`bake.relinearise_hdr()` repairs old files).

---

## 4. Bake and export (`export_gltf.web()`)

three.js image-based light has **no occlusion**. Inside a closed cabin it lights the footwells like the dash top, and every glossy trim mirrors the studio. So the cabin ships with Cycles' light.

```python
import export_gltf as X
X.web()      # rebuild -> bake -> both GLBs, probe, outside view + light; ~7 min on an RTX 4060
```

An exterior-only car (the Luxeed RX until its cabin is built) exports without the MCP, in a background Blender that rebuilds from an empty scene and leaves the open session alone (about 1 minute):

```bash
blender -b --factory-startup --python-expr "import sys; sys.path.append(r'<repo>/blender/scripts'); import export_rx; export_rx.web()"
```

With its cabin, the RX builds, bakes and exports everything in the same background Blender (about 10 minutes on an RTX 4060):

```bash
blender -b --factory-startup --python-expr "import sys; sys.path.append(r'<repo>/blender/scripts'); import export_rx; export_rx.web_full()"
```

It follows the SU7's `web()` step for step (cabin lighting, `thin_glass` bake, probe, doors joined on their hinge, interior then exterior GLB, the outside world). Never run the bake in the open session: it holds Blender's main thread for minutes (section 7).

The RX's cabin is baked under its Beijing world and looks out on it, and since Sept 2026 its exterior stands in the same world, as the SU7's does. The studio-only exterior (`outside.exterior: false`, section 5) remains available for a car that needs it.

`materials.export_safe()` makes three fixes the exporter cannot, and every export runs it:

- **Transmission:** glass becomes opaque.
- **Procedural Metallic** (the paint flake) is set to 0. Left linked, the exporter omits `metallicFactor`, glTF reads that as 1.0, and the RX's paint came out solid dark metal. `export.check_paint()` fails the export if a paint ships metallic.
- **Sheen Weight** is folded into Sheen Tint. glTF sheen has no weight, so a 0.28 weight shipped at full strength and the RX read pastel lavender. Folded in, the web paint measures 98/80/168 against the photo's 103/92/166 and Cycles' 98/82/176 (same classifier).

Driving this from the Blender MCP:

- A call longer than about 3 minutes drops the socket ("No data received"), although Blender carries on.
- Queue the rebuild and bake (`build_su7.main`, `su7_interior.main`, `bake_cabin`) on a `bpy.app.timers` callback registered with **`persistent=True`**, and poll a state **file**. `build_su7.main()` starts from `read_homefile`, which drops ordinary timers mid-job and replaces `bpy.app.driver_namespace`.
- Then run `X.exports()` (`export_interior()`, `export_safe()`, `main()`, `export_outside()`) in a direct call. The glTF exporter fails inside a timer callback.
- Render any Cycles reference views **before** the exports: they merge and swap materials.

1. **`cabin_lighting()`:**
   - the OUTSIDE world (3.7) and the cabin rig at `RIG_FILL`
   - the HMI and cluster images on the screens
   - the **blackout** layer hidden, so light comes in through the glass (`Shell_Shadow`, `Greenhouse_Black` and `Roof_Rear_Black` are the dark underlay that makes the glass look deep from outside), and the lookdev `Ground`
   - the bake and the probe run inside `bake.thin_glass()`
2. **`bake.prepare()`:** apply modifiers and add a float colour attribute.
3. **`bake.vertex_lighting()`:** Cycles `DIFFUSE` with direct + indirect and **no colour**. That is the light each vertex receives, the same factor the render multiplies albedo by. It runs about 4 min at 256 spp for 97k vertices.
   - While it runs, `bake_overrides()` switches normal maps off (one texel of grain per vertex makes speckle).
   - It also sets **metallic to 0**: a metal has no diffuse closure, so without this the chrome baked black.
   - The result is stored × 0.25 (`STORE_SCALE`).
4. **`bake.smooth()`:** two passes of neighbour averaging to remove per-vertex Monte Carlo speckle.
5. **`bake.to_generic()`:** copy the result into a float3 attribute, `_BAKEDLIGHT`.
   - Blender 5.2's glTF exporter writes a colour attribute correctly for the **first material's primitive only** and fills the rest with white. That gave a flat, bright cabin.
   - Custom `_` attributes export intact per primitive.
6. **`bake.probe_mix()`:** an equirectangular HDR from between the front seats, with the render rig's lights at **30%** (`PROBE_LIGHT_MIX`).
   - One probe serves every surface, and from its position the roof softbox covers half the sky.
   - At full strength, pedals, console carbon and mirror all mirrored it white.
   - At zero, the leather and the wheel lost every highlight.
   - The mix renders the probe with and without the lights and blends the two.
7. **`export_interior()`:**
   - plain screen back on `screen_main`
   - world UVs
   - lights removed
   - front door cards joined into `int_door_L` and `int_door_R`, with the **origin on the hinge axis**
   - merge by material
   - Draco, with generic and colour quantisation at 14 bits (dark values band at 10)
8. **`export_safe()` + `main()`:** the exterior, with the blackout layer as its own node, `SU7Ultra_Blackout`.
9. **`export_outside()`:** the outside view JPEG and light HDR (3.7).

### Names the web app relies on

| Name | Kind | Used for |
|---|---|---|
| `screen_main` | node | the live HMI is warped onto it |
| `int_door_L`, `int_door_R` | node, origin on hinge | door cards |
| `SU7Ultra_Blackout` (`*_blackout`) | node | hidden in the cabin view |
| `SU7Ultra_Body`, `SU7Ultra_Wheels` | node | hidden in the cabin view on single-file cars |
| `*Ambient*` | material | emission driven by the HMI (colour, brightness, on/off) |
| `*led_white*` | material | headlamps |
| `INT_Screen` | material | screen backing |
| `M_Glass`, `M_Glass_Privacy` | material | a clear or privacy tint from inside |

---

## 5. Web integration (`src/components/viewer`)

- **`CarModel`:** the exterior. In the cabin view it:
  - hides the blackout node
  - makes the glass a tint with no depth write and no reflection: `M_Glass` (windscreen, front doors) at opacity 0.12, `M_Glass_Privacy` at 0.5. Blending happens on display values, not linear light, so these are lower than 1 − transmission; matched to the Cycles render (sky patch 96/114/132 against 96/116/131).
- **`OutsideWorld`** (a car with `assets.outside`): the same HDRI world outside and in.
  - **Outside**, the view JPEG is projected onto a `GroundedSkybox` dome (`outside.ground`), so the car stands on the plaza instead of floating over a panorama.
    - The dome and a shadow-only plane live on **layer 1**, which only the view camera sees. drei's `ContactShadows` renders every layer-0 object into its depth pass, and the dome's floor turned its whole 13 m square dark.
    - The light HDR, prefiltered by PMREM, is `scene.environment`, turned by `exteriorTurnDeg` via `scene.environmentRotation` so the default camera has the sun at its back.
    - The sun the HDR clamps away comes back as a shadow-casting `DirectionalLight` (`outside.sun`: measured direction, colour and irradiance).
  - **Inside**, the view is an sRGB `scene.background`, fading in over the last metre to the seat. The world turns back to the cabin bake's orientation, and the sun light goes off, because the bake already has it.
  - Which world applies is decided per frame from the camera's distance to the seat (`CABIN_RADIUS`), so the switch happens once the camera is inside.
  - **Build PMREM targets in an effect, not a memo.** They live on the GPU only. A memo'd one disposed by React StrictMode's dev effect cleanup came back empty: the car was lit by the sun alone, with black glass.
- **`StudioEnvironment`** (`VehicleViewer.tsx`): cars without an outside world get a studio (`RoomEnvironment`) outside and a dark gradient inside.
- **A world seen only from the cabin** (`outside.exterior: false`, the RX until Sept 2026): the studio stays outside, and `OutsideWorld` (`cabinOnly`) takes over the environment and background only once the camera is within `CABIN_RADIUS` of the seat. It never shows its dome or sun, and hands the environment's rotation back when the camera leaves.
- **`VehicleViewer`** clears with alpha 0 (`gl.setClearColor('#07080a', 0)`): `ContactShadows` clears its render target with the renderer's clear colour, and an opaque clear darkened its whole square.
- **`CabinModel`:** loads the interior GLB and the probe in their own Suspense boundary, preloaded behind the exterior. `bakedLighting()` patches each material:
  - **Baked light replaces image-based diffuse:** `iblIrradiance = π · L`, where L = `bakedLight × 4`. three.js divides by π, so diffuse = albedo × L, exactly as in Cycles. It goes into `iblIrradiance`, not `irradiance`, so sheen and multiscatter get it too.
  - **Specular occlusion:** reflections are scaled by `clamp((1.25 · luminance(π · L))^1.5, 0.05, 1)`. Open trim keeps its full reflection; a footwell keeps about a tenth.
  - **What the probe cannot do (measured 2026-09-25):** near-black leather gets almost all its brightness from reflections. In Cycles the SU7's dash top reads 125 with gloss and 9–17 without. The web matches Cycles where the probe's viewpoint sees what the surface sees: the driver's dash top is 108 vs 125, the seats match. It falls short on the passenger-side dash face (21 vs 69) and the console (18 vs 45). From between the seats, one probe sees the wrong part of the cabin for those spots (parallax).
    - Specular occlusion is already 1 there, so retuning it does nothing.
    - Adding the outside lookdev softboxes to the probe barely lifted those spots, and it mirrored the overhead box white in the console carbon.
    - The fix, if wanted, is a box-projected (parallax-corrected) probe lookup in `bakedLighting()`.
    - Measure with the `window.__specOcc` / `__patch` harness on the capture route, against a Cycles render made under `cabin_lighting()` inside `thin_glass()`.
    - The lookdev softboxes (`L_*`) light the cabin bake through the glass; without them the Cycles cabin reads about a quarter as bright.
  - **Direct lights are zeroed**, because the bake already contains them.
- **HMI:**
  - drei's `<Html transform>` builds a CSS 3D camera in *world units*. In metres, Chrome's float32 compositor drew the HMI a full screen-height above where layout and hit-testing put it.
  - `LiveScreen` instead projects the quad's four corners each frame and applies a 2D homography (`quadToCss`). It is exact, and clicks land.
- **Seated shot:** built from `assets.driverEye`, which is in Blender axes and mapped to glTF (x, z, −y). The camera pivots 15 cm ahead of the eye, so dragging turns the head.
- **The HMI itself** (`src/components/hmi`): one DOM tree at 1280×800, shown flat on the Dashboard view and warped onto `screen_main` in the cabin. A car whose OS has been rebuilt from its maker's screens gets its own skin (`cockpit.skin`); `hyperos/` is the SU7's, the others share the generic one. Build a skin from the maker's own screen images, not memory:
  - list what the real screens show (status bar, dock, desktops, settings pages, the car's own apps) and the names it uses, with sources in the vehicle data
  - the car's drive modes go in `cockpit.driveModes`, with published outputs where there are any (the page's power readout uses them)
  - images of the car inside the HMI are rendered from the build (`blender/renders/hmi`, `public/hmi/<car>/`); fade shadow-catcher alpha away from the car, or the studio rig's broad shadows reach the image edge as a hard rectangle
  - `/capture/hmi/<slug>?screen=&gear=&page=&mode=&climate=1` shows the HMI alone in a given state; `qa.hmi_capture.capture(slug, query={...})` screenshots it

### Judging the web result against the photo

```python
import ref_match
from carkit.qa import web_capture as W
p = W.capture_camera("xiaomi-su7-ultra", "cabin_front")    # headless Edge, ~30 s
W.triptych("cabin_front", p, "renders/interior/i06_cabin_front.png")   # photo | web | Cycles
W.patches(p, {"windscreen": (380, 170, 900, 260), ...})    # sRGB means per box
```

`/capture/view/<slug>?mode=&pos=&target=&fov=` renders the viewer alone through a locked camera. Needs `npm run dev`.

---

## 6. Gates checklist for a new car

- [ ] References in `blender/reference/<car>/`, with their licences noted
- [ ] Side, front and rear cameras solved; overlay within a few px
- [ ] Loft and caps: zebra continuous, dims within 10 mm, overhangs match the published figures
- [ ] Panels: 4 mm gaps, openings cut by exact booleans, `prune_off_sheet` on open sheets
- [ ] Parts from the catalogue, contact sheet reviewed; nothing invented
- [ ] Materials: patch values within ~10 sRGB of the photos
- [ ] Exterior at or under 400k tris, `fingerprint` baseline saved
- [ ] Cabin camera solved, hardpoints recorded with their sources
- [ ] Leak report under 0.2% on 6–8 seat views
- [ ] Render at the matched camera; patch values match the press render
- [ ] `web()`: all primitives carry `_BAKEDLIGHT`, sizes within budget
- [ ] Outside world chosen and turned (sun behind); web view out matches Cycles through the same camera
- [ ] Web triptych: photo | web | Cycles agree; HMI lands on the screen; clicks work
- [ ] HMI skin built from the maker's own screen images, with sources; the car's drive modes in the data
- [ ] Review notes routed (`jev_cli.py review`) and nothing at severity 2 or more left open before the owner sees a render
- [ ] Anything that cost time added to `carkit/jev/known_failures.py` as well as to section 7
- [ ] README and this document updated with anything that cost time

---

## 7. Lessons that cost real time

Exterior:

- A nose built as an x-loft gave a flat front plate and a "toy" face.
- Profiles must be C2, and sections resampled by arc length.
- Parts that wrap a corner must be ray-cast; nearest-point projection spans the corner as a chord.
- Booleans go on the half sheet before mirroring. Grid trimming shears quads.
- The history-dependent slope cache: nose and tail share one cache keyed `(front, round(v, 5))`, or values drift with call order and refactors stop being bit-identical.
- Light rigs start too hot. Calibrate with patch values, and use Khronos PBR Neutral in both Blender and three.js.
- A tail built from the side photograph alone is a guess. The side view sees the corners, not the face. The SU7's rear bulged 45 mm too far and was featureless where the car has a lid, a light bar, pods and a black lower bumper. Build every face from photographs that look at it (2.A).
- Check which plate is in a photo before using it as a ruler (2.A).
- Check dimensions against the type-approval filing. A figure quoted at launch can be the prototype's or an alternative's.

- An EXACT boolean that grazes a vertex leaves a sliver, and a Bevel modifier later in the stack turns it into vertices at 1e30 m (streaks metres off the car). `cut.difference` now welds. To find the object, scan the evaluated vertices for anything outside the car's envelope.
- **Greenhouse width, from behind (the RX, Sept 2026).** The owner saw thick C-pillars and a small rear window. The glass outline matched the rear photo; the pillars did not.
  - Measure it as a *sweep*: for each point of the photo's traced outline, cast the camera ray and, at every station x, compare the model's half-width at the ray's height with the ray's y. The worst station is where the model sticks out, and by how much. A plain silhouette report says only "too wide".
  - From behind the RX's cabin tapers rearward on broad haunches: the rear door glass and C-pillar sat up to 14 cm inside the model's at z 1.2-1.3. `LoftBody(y_glass=...)` insets the glass base there; the rear view's rays are now met within 2 cm.
  - Trust the camera whose scale is set near the feature. The rear camera's tyre track is beside the C-pillar; the front camera's scale at the A-pillar rests on an assumed mirror width.
- **Overhangs.** The front read "long and extended" to the owner. The side camera (2.5 px) had the nose 11-16 px ahead of the photo at the corners and the tail 6-17 px short; a clean profile (side_left_green) shows front and rear overhangs about equal, not 1080 / 940. The front 3/4 that argued for a broad, forward nose was solved with its front rim, and its front wheels are steered. Moving the face back 25 mm, rounding the corners (WRAP 60 % of the way to the SU7's) and giving the tail the 25 mm brought the side outline within 2-10 px.
- **A 3/4 photo's side.** With the nose pointing right in the frame, the photo shows the car's right side. Solved as the left, the forest photo fell into a mirror image (f < 0).
- **Cap edges.** `face(y, z)` below the nose cap's centreline bottom (z 0.277 on the RX) returns the centre point for every y: the chin strip had been built dead straight across with its ends 3 cm proud, and the lip bunched inside y +/-0.44. Sample from `CAP_LOW`.
- **Roof blade.** The side photo shows a dark slot under the roof's trailing blade, so the black band across the backlight's top starts at the blade's edge, not at the knee. The low rear photo cannot see behind the lip, so it had not argued against it.
- Lettering set with `spacing` came out half the photo's width (0.24 m for 0.46 m). Measure the built text object's extent against the photo.
- A wheel house open on its inboard side lets an arch seen from above look under the car and out through the far arch. Use `wheel_liners(inner_wall=True)` with `wall_z` above the floor, or the wall hangs below the sills.
- A rim's visible lip is about 17 mm larger in radius than the nominal bead seat (J flange). Built at the bead seat, the rim reads a size small under a balloon sidewall.
- Press photos often steer the front wheels towards the camera. Check a solved camera on the rear wheel, and don't compare front wheels in such a shot.
- A head-on rear camera solved at the tail is good there, but its heights 3 m further forward (mirrors, roof spoiler) read about 5 cm high. Take z from the side camera and only y from the rear one.
- Read what a photo band really is before modelling it. The RX's "black roof spoiler" was the glass's black frit band. Casting each band onto the model gives its x range, and the materials then fall on the existing surface.

- A hood with domes is a section with two crowns: the fender crown and the hood's dome, with a groove between them for the shut line. Moving the one crown inboard lowered the fender top by 8 cm, and the front 3/4 silhouette caught it. Use `LoftBody(z_dome=, y_dome=)`, and lower Z_ROOF by the valley's depth so the crowns, which form the side outline, stay put.
- A straight-on front photo read by casting onto the model gives a robust y and an unreliable x. The rays graze the hood, so 3 cm of height moves the hit 45 cm. An oblique camera cast onto a nose corner is biased by the cap's wrap: the RX intakes read 6 cm outboard in the front 3/4 view against the head-on view.
- The shadow shell sits only 2.5 mm under the skin by default. A concave feature (a groove) lets it poke through as black notches. Sink it (`inset=0.020`) and sample it finer.
- Two panels butting without a gap still show a line if the rim is bevelled (`butt_bevel=False`), and flicker if two triangulations of one surface cross. Lift one 0.5 mm so it laps the other.
- **The rear greenhouse, second pass (the RX, Sept 2026).** The owner's circles were a boxy painted C-pillar, a dark roof over the rear seats and a bumper hanging low behind the wheel. The fixes:
  - **Glass wedge.** The photos show the rear glass wrapping round each C-pillar as a dark wedge under the spoiler. The painted pillar stops at a crisp edge falling from just behind the side glass to the ducktail's corner (`rx_panels.Z_CEDGE`, cast from the side photo onto the loft). The wedge is a glass panel between that edge and the black band (`RX_Glass_Wedge`).
  - **Crowned rear top.** The side outline behind the spoiler stood 2-7 cm under a flat-topped section: the top is crowned there, the rail ~7 cm under the centreline (`Z_CREST`).
  - **Band finish.** The black band is glass-smooth; matte, on the crowned top it read as a rubber mat.
  - **Bumper.** Behind the wheel, the paint stops at the black lower bumper's top edge and the corners are cut up under its lower edge (`Z_BAND_TOP`, `Z_BAND_LO`).
- **Concave skin catches anything underneath.** A coarse grid's chords lie outside a concave surface, so the shadow shell (even 30 mm in) and a -3 mm underlay poked through the RX's C-pillar foot as black fins. Pull the shell in along rays from its core, by vertex and then by face centre (`rx_panels.clear_shell`), and grid underlays finely.
- **A boolean on a sheet whose Mirror modifier is on** bakes the mirror with the cut, so cut both sides. On an open sheet the EXACT solver also keeps the cutter's walls: bake, take `sheet_bvh`, cut, `prune_off_sheet`. The kept walls had hung under the RX's bumper as a black flap.
- **Read edges on contrast-stretched crops.** A light car against a white studio wall misread by ~5 px.

Interior and web:

- A dash-top slot, a missing belt cap or a short headliner shows as a paint sliver in the viewer. Run the leak finder, not your eyes.
- Blender 5.2 glTF exports `COLOR_0` for the first primitive only. Ship baked data as a custom `_ATTR`.
- Metals bake black under DIFFUSE; set metallic to 0 for the bake.
- A probe with the lights at full strength mirrors the softbox into every footwell; with none, the trim goes flat. Mix them at about 30%.
- A cabin lit only by lights placed inside it reads dark whatever the exposure. Bake it under a real world and let the light through the glass (3.7): modelled glass passes nothing to Cycles, and seen from inside a single-sided pane's Fresnel goes totally reflective.
- Without a daylight world, the studio outside is dark: dim the scene environment and the direct lights for the bodywork seen through the glass (`scene.environmentIntensity` skips materials with their own envMap, so the cabin keeps its probe).
- Tone-mapped images cannot light glossy surfaces: ship an HDR for lighting next to the JPEG for viewing.
- Image-based light cannot show local reflections. From inside, the mirror housings mirror the car's own yellow flank in Cycles; the web shows the sky there. Accept it.
- drei `Html transform` in a metre-scale scene is misdrawn by the compositor. Use the homography.
- A glTF node with several materials arrives as a Group of `<mesh>_N` children. Match node names on the Group, not the meshes.
- Blocking MCP calls time out. Queue long bakes on a **persistent** Blender timer (`read_homefile` drops the others), and export in a direct call.
- **Never bake in the owner's open Blender** (the RX, Sept 2026). The add-on runs code on Blender's main thread; a multi-minute bake froze the window, Windows logged it as hung and the session was lost. Bake and export in a background Blender: `export_rx.web_full()` under `blender -b --factory-startup`.
- **A cabin photo with no body lines in it still solves** if a part of known size is in view. The RX's straight-on press render shows only the A-pillars, the door belts and the centre screen; with the screen's size from the spec (16.1 in 16:10) and its centre and tilt as extra unknowns, the camera came out at 7.9 px (`rx_camsolve.solve_cabin`), and the dash, wheel and console read off it.
- **A greenhouse that steps in makes chord trims fail.** Where the RX's cabin tapers onto its haunches, the body section is a ledge and a rounded rise to the glass. A chord across it (`edge_band`) left the rise's inner wall in view from the rear seat, and moving the chord made it worse. An offset trim (`pillar_trim`, 14 mm in) follows the step.
- **Wheel liners stand inside the cabin's side walls.** The RX's rear liner rises to 0.93 m at |y| 0.70, above and inboard of a hump trim rolled over at 0.76. Put the hump inboard of the liner wall and above its top. Up front the liner narrows the footwell to |y| 0.69 at the toe board, so the kick panels step in there.
- **A panoramic roof is a frame, not a headliner.** The RX headliner was built as a front band (visors, overhead console, speakers), side rails and a rear band, with a reveal from each edge up to the glass so no gap shows the roof's paint beyond it. Since the owner asked for a painted roof over the rear seats (Sept 2026), the glass ends at the B-pillar and the headliner is one closed piece (`rx_interior.ROOF_OPENING`). Setting the flag back to True restores the frame.
- An empty full-size layer over a desktop swallows its taps. Make pass-through layers `pointer-events: none` and give their overlays `auto`.
- A Windows dev server can wedge on a locked `.next` chunk (`errno -4094`). Restart it.
- Blender 5.2's `Image.save()` writes float `.hdr` through the sRGB curve. Write RGBE yourself (`bake.write_hdr`).
- PMREM targets made in `useMemo` die under StrictMode's dev cleanup. Make them in an effect.
- drei `ContactShadows` sees every layer-0 object and clears with the renderer's clear colour. Put backdrops on another layer and clear with alpha 0.

---

## 8. Decision layer (Jev)

Jev (TypeSafe's "System One" model) answers typed questions about text or
JSON: a **choice** from a list, a **score** on a rubric, or a yes/no
**noul**. Each answer comes with probabilities. A call takes about 0.5 s and costs a
fraction of a cent (about $0.04 per million input tokens). It is the
pipeline's decision layer, not a modeller: geometry, `bpy` scripting,
measurement and looking at renders stay with code and the agent.

**Setup.**
- The key is `TYPESAFE_API_KEY`. `carkit.jev.client` finds it in the environment, in `JEV_ENV_FILE`, in the repo `.env`, or in `../Jev/.env`.
- The client uses only the standard library, so it runs in Blender's Python and in the shell.
- Every call is logged to `blender/jev_log/calls.jsonl` (answers, latency, tokens, but not the state). `jev_cli.py log` sums it up.

### What it is used for

| Tool | Question it answers | Measured (Sept 2026, jev-1.13) |
|---|---|---|
| `jev_cli.py find "<need>"` | Which carkit function or class, earlier-car builder or manual section fits this need? It searches about 530 entries read from the source with `ast`, ranks them with a Choice, then re-checks the top ones with a Noul. | 11/12 right in the top 5 and 10/12 at rank 1. About 1.5 s. |
| `jev_cli.py triage` and `triage.guard()` | Is this traceback or render symptom a failure we have already fixed? If so, it returns the fix from `known_failures.py`. `build_rx` wraps every module build in `guard`, so a known failure comes back with its fix in the error message. | 11/12. Both unrelated errors correctly came back "unknown". About 0.5 s. |
| `jev_cli.py review <car> notes.txt` | For each review note or piece of owner feedback: which module, what kind of fix (shape, position, missing, invented, material, render, ok) and how severe. | Module 9/10, action 7/7 after the criteria were rewritten. A 10-note plan takes about 2 s. |
| `jev_cli.py onboard spec.txt --car ... --parts` | For a new car's spec or press text: a feature checklist (roof lidar, flush handles, light bars, spoilers …) marked yes, no or "verify", with the part to start from for each. | Numbers come from regex in code. Jev reads only the features. |

### What it is not used for, and why

These follow from Jev's documented limits:
- It takes text only.
- It is weak at arithmetic, counting and reading numbers.
- It reads questions literally.
- It loses accuracy when the state carries detail the question doesn't need.

The cases:

- **Judging renders against photos.** Jev cannot see images. The agent writes what differs in words, and `review` routes those notes.
- **Numeric gates** (dimensions, silhouette px errors, tri budgets, leak %). A threshold in code is exact, and Jev would only add noise.
- **Guarding destructive `bpy` calls.** A regex on `read_homefile` or `objects.remove` is deterministic.
- **Planning the agent's own next step.** Writing the state costs as much as deciding.

### Writing questions that work

- One judgment per question. Combine the answers in code.
- Word each option around the thing being compared: "the model has X that the real car does not", not "not in the photo". A literal reading of the second sent an invented bar to "missing".
- Gate on both numbers. Take the Choice `confidence` and an absolute Noul re-check, and fall back to "unknown" or "verify" below the gate. A fallback costs one normal turn. A wrong fix costs more.
- Send the model only what the question needs: filter a scraped page to the lines about the car before `onboard`.
- `finder` is only as good as the docstrings it reads. `Placer.radial` never says "wrap a lamp round a corner", so a search for that finds its module, not the method. Write docstrings for the need, not only the mechanics.

