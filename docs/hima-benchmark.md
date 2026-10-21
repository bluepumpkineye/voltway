# HIMA benchmark: what the target looks like and how we get there

The product target for Voltway is the showroom at
<https://hima.auto/3d-view/> (Huawei's HIMA 3D hall): a bright studio, a car
you can recolour, re-wheel, open, see through and measure. This document is
what we learned from taking that page apart, and the plan that follows from it.

It records **techniques only**. None of HIMA's models, textures, cubemaps,
icons or code are copied, redistributed or used as a reference for geometry;
every car in Voltway is still built from the photographs listed in
[`3d-pipeline.md`](3d-pipeline.md). What is quoted below was observed from the
public page on 2026-09-30 (the Luxeed S7 Ultra, a car Voltway does not model).

Status of the work is at the end (§6).

---

## 1. What HIMA's hall is

The page at `hima.auto/3d-view/` is a thin wrapper around an iframe. The hall
itself is a **PlayCanvas 2.22 (WebGL2)** app published from the PlayCanvas
Editor by a 3D-configurator vendor (WeShape3D). A car is chosen with
`?SN=<code>`; a car's dimensions, camera sets, wheel list, luggage combinations
and colour lists are JSON files, and the page switches cars by loading that
car's entity tree.

| Area | What it does |
|---|---|
| Scale of the project | ~8,600 registered assets for the whole hall: ~5,400 materials, ~1,000 models, ~380 animations, ~1,400 textures, 26 cubemaps, 35 prefab templates. One car is ~120 materials. |
| Weight | ~27 MB transferred for one car (59 GLBs ≈ 14 MB, 22 WebP ≈ 8 MB, PNG/JPG ≈ 3 MB, two wasm decoders ≈ 1 MB), ~455k triangles loaded including variants that are hidden, ~270 draw calls, ~160 MB of texture memory. |
| Rendering budget | Device pixel ratio capped at 1, 4× MSAA on the render target, ACES tone mapping, render-on-demand, no postprocessing. |
| Lights | **None.** Black ambient and no light entities. The car is lit by baked occlusion plus per-material cubemaps. |

## 2. How the look is made

1. **Flat albedo × baked occlusion.** Materials carry a plain colour (or a
   small noise map for paint flake). The shading from nearby surfaces is a
   baked AO texture on a second UV set: 2048² for the shell and for the cabin,
   512² for small parts, one for the boot. Because colour and occlusion are
   separate, any paint or trim colour can be swapped at runtime and still be
   shaded correctly.
2. **A studio light rig per material, not the white room.** The room looks
   white, but the paint does not reflect the room. Each material points at a
   small RGBM cubemap of a *dark* studio: black void, an overhead trapezoid
   softbox, a long horizon strip, two side panels. A dozen such cubemaps are
   shared across the car (paint, glass, black trim, chrome, cabin plastics).
   This is what produces the crisp stripe highlights down the flanks.
3. **Paint** is metalness 0.9, gloss 0.6, a 512² flake-noise diffuse map and a
   sheen lobe, with the reflection boosted (×2.2 on the body colour). **Glass**
   is real alpha blending (0.7–0.92 outside, 0.3 inside) with depth write off.
4. **Ground and set.** The car's shadow is a two-triangle quad carrying a
   baked AO alpha. The studio floor has a lightmap and a planar mirror
   (a second camera rendering the scene upside-down). The set itself is one
   modelled white cyclorama with an arch, concentric floor lines and AO baked
   into its textures.
5. **Colour options are whole-material swap sets.** Each paint is a list of
   `{ entity, materials[] }` pairs (the shell, both door skins, the handles,
   the wing...), and a trim colour is the same for the cabin. A switch
   cross-fades the materials over about a second. Wheels are entity groups
   that are shown or hidden; brake caliper colours are swap sets.

## 3. How the interaction is built

| Feature | Technique |
|---|---|
| Camera | ~37 named camera anchors per car, each a pose; a button flies the camera to its anchor. There are four sets per car (landscape, portrait, foldable, tablet split). Orbit is limited per anchor. |
| Tabs | A bottom pill: Colour, Wheels, Interior, Space, Compare. Each tab selects an anchor and a swatch row above the pill; the active swatch has its name beside it. |
| Dimensions | Dimension-line models (floor rulers with arrowheads) shown on the first view; length and wheelbase on the floor, width and height on the front view. |
| Doors | Each door is its own entity: outer skin, handle, inner card, hinge pivot, and a box collider. Clicking it tweens the door −60° about the hinge and frames the camera; seat hotspots appear. |
| Boot | A baked clip with struts. The cargo bay is modelled and lit blue; mm arrows are modelled meshes with labels; luggage combinations are props. |
| X-ray ("outside") | The greenhouse exists twice: the painted version and a pre-split ghost twin (grey, 30 % alpha, no depth write). The lower body keeps its paint, the doors are hidden, and the interior shows through. |
| Space | Posed mannequins at 160 / 170 / 180 cm, doors removed, with seat hotspots. |
| Interior | A real-time camera at the driver's seat (FOV 45), not a panorama. |
| Compare | Split screen: two viewports, two cars, synchronised cameras; sub-tabs for colour, size (animated width/height rulers), space and interior. |

## 4. What this means for Voltway

What we already have, which HIMA also relies on:

- Flat-albedo paint (one clearcoated material per car) and a cabin whose bake
  is **light only** (`_BAKEDLIGHT`), so recolouring a trim at runtime is
  already shaded correctly.
- Image-based lighting, PMREM, drei, an HMI warped onto the screen, capture
  routes that screenshot the web viewer through a matched camera.

What is missing, in the order it blocks the target:

| Gap | Where it lives |
|---|---|
| Nothing in 3D is selectable: no paint, trim, wheel or anchor data in `schema.ts`; the store's `openings` is never read by the scene | web |
| The exterior is exported as 4 merged nodes: both doors, bonnet and glass are inside `*_Body`, and all four wheels are one node | `carkit/export.py` |
| Behind each door skin is only the black shadow hull: no jamb, shut face, sill or aperture; no boot and no frunk is modelled | Blender build |
| No white studio exists in Blender, and the cabin is baked under a city HDRI with the doors closed | Blender build |
| The reference photos cover exteriors and cabins only: none of open doors, jambs, the boot or other wheels | references |
| `/compare` is a static table, there is no split-screen, and mobile has no quality tier | web |

## 5. Rendering recipe: how we get the same look

We stay on **three.js and react-three-fiber**. Nothing HIMA does needs
PlayCanvas, and switching engines would throw away the HMI homography, the
capture routes and the cabin bake shader. Pixel streaming costs a GPU per
viewer and a Gaussian splat cannot be configured, so neither is on the table.

**One light rig, defined once.** `src/data/studio/rig.ts` lists the softboxes
and strips (position, size, intensity, colour) in the car's own axes. The web
draws it live with drei `Lightformer`s. In Blender the same list becomes
emissive planes over a black world, from which carkit renders the panoramic
HDRs (`carkit.bake.write_hdr`, never `Image.save`, which writes through the
sRGB curve) and the studio stills. Web and Cycles then agree by construction.

**On the web**

- Rig reflections go to materials by name rule: `m_paint*` takes the paint
  rig, chrome, aluminium, rim and glass the hard rig, `int_*` keep the cabin
  probe.
- Keep `THREE.NeutralToneMapping`: it is the Khronos PBR Neutral curve the
  Blender renders already use.
- drei `CameraControls` flies between anchors; `MeshReflectorMaterial` is the
  floor; a ground shadow replaces per-frame `ContactShadows`; render on demand.
- drei `Html` is used in screen space only. `Html transform` is wrong in a
  metre-scale scene (see the HMI notes in the README).
- Dimension labels are drawn into canvas textures with the site font. drei
  `Text` is not used because troika fetches its default font from a CDN.

**In Blender** (Phase 2: `carkit/bake.py`, `carkit/studio.py`, `carkit/rig.py`;
how it works is in `docs/3d-pipeline.md`, "The studio look")

- Built (2026-10-06, both cars): per-vertex `_BAKEDAO` for the exterior (Cycles
  AO, every opening posed open) with a shader patch that multiplies the
  environment's light by it; a baked ground-shadow quad per car in place of
  `ContactShadows`; Cycles studio stills from the web's own rig
  (`src/data/studio/rig.ts` parsed into emissive panels) and camera anchors,
  which agree with the web view.
- Not built, on purpose: a baked cyclorama (the procedural cove already reads as
  a white room and costs no texture); a cabin re-bake under the studio (the
  daylight bake reads naturally through the windows, and a studio bake would
  need a second set of vertex light, +1 MB per cabin, and a lighting design for
  an interior the rig hardly reaches); per-material environment rules (the one
  rig serves paint, rims and glass; revisit if a triptych shows a rim or a
  lens going black).

**Decisions not taken, and why**

- `KHR_materials_variants`: three.js only supports it through a third-party
  plugin, and runtime parameter swaps are simpler and can be tweened.
- UV2 AO textures everywhere: per-vertex AO is already in the pipeline and
  costs no texture memory.
- Paid bakers or generators: ruled out by the project rules.

## 5b. The cabin: how HIMA's interior is made (observed 2026-10-19)

The first pass (§2) looked at the exterior. The interior was taken apart on 2026-10-19 on the Stelato S9 (the hall's
`?SN=50080100157`), through the page's own PlayCanvas runtime: every cabin material, its textures and its environment were
read in the live page. As in §1, this records **techniques and numbers only**; no texture, cubemap or model was saved or reused.
(The REA reverse-engineering MCP, github.com/morluto/rea, was asked for but could not be installed in the session: the permission
classifier blocked the npm install. Everything below came from the runtime directly, which is the evidence REA's web-page
tools would have reported.)

**The cabin is cheap.** 75 materials, **about 20 textures** and 10 shared environment maps for the whole interior; about 400k
triangles for shell, seats and door cards (shell 84k + 32k + 43k, seats about 100k, each door card 5-14k). Nothing in it is
exotic: PlayCanvas' standard metalness material, a flat tint on nearly every surface.

| What | How |
|---|---|
| Occlusion | **One 2048 x 2048 AO atlas for the whole cabin shell** on the second UV set, a second 2048 for the seats, a 1024 for the fabric parts. Every material of a part shares its atlas. It multiplies the environment's diffuse light and, with `occludeSpecular`, its reflections. This is what draws the seams, the shut lines, the crease under a visor. |
| Light | **No light entities, ambient black.** The cabin is lit by its environment alone: 10 small (512 x 512, RGBP) cubemaps, 44 of the 75 materials on the same one. That one is a **bright, even parking-hall panorama** (not the dark light-rig of the exterior): measured in linear light the ceiling band is about 1.0, the walls and floor about 0.27, the median 0.28, the 99th percentile 7.5, the brightest strip 55, the mean 0.53. Diffuse light is the normal-dependent irradiance of that hall times the AO; the reflections are its strips. |
| Leather | A flat tint (cream `#a3948b`), **metalness 0.3, gloss 0.45**, bump 0.7 with **one shared 512 grain normal map**. The partial metalness gives the leather a tinted, velvety sheen under the hall. |
| Wood, trim | A 512 grain texture used as colour *and* gloss, metalness 0.2, gloss 0.8; chrome and speaker rings are metalness 1 with a **reflectivity of 1.5 to 8**, an art-directed boost on top of the hall; piano black is clearcoat 0.15, gloss 0.85. |
| Stitching | Not geometry in the shell: thin **decal strips** with a 256 alpha texture, premultiplied blending, in the leather's own darker tint. |
| Ambient light | The orange strip is an **additive-blended glow plane** with a 1024 mask (`blend` additive-alpha, tint `#e6683e`, opacity 0.6), not an emissive tube. |
| Screens | Static pictures, 2048, as both colour and emissive (about 0.7). |
| Camera and tone | The seated camera is a real-time one at **45 degrees**, ACES, exposure 1, MSAA; the eye sits well behind the wheel, so the wheel is low in the picture and the dash fills the width. |

What this changes for Voltway (built for the Zeekr 7X, 2026-10-19; see `3d-pipeline.md`, "The hall look"):

1. The cabin is lit by a bright, even hall and shaded by a **texel occlusion atlas**, not a per-vertex light baked under the
   outdoor world. (§5 said a cabin re-bake was not worth it; the right change was not another bake but taking the sun out.)
2. The seated camera is 46 degrees, 12 cm behind the camera-matched eye.
3. Rolled out to all seven cars on 2026-10-19 (`3d-pipeline.md`, "The hall look": the SU7, RX, ES8, A06T, G9L and Z9 after the 7X).
   Still open: stitching decals, additive glow for the ambient strip, per-material reflectivity.

## 6. Roadmap and status

Decisions (owner, 2026-09-30): the white studio is the default scene with the
Shanghai and Beijing city worlds kept as a toggle; the Luxeed RX pilots every
Blender change; missing reference photos are found by us and **approved by the
owner before any modelling**.

| Phase | What | Status |
|---|---|---|
| 0 | This document | done |
| 1 | **Showroom shell** at `/showroom/[slug]`: both cars, today's GLBs. Bottom tab bar, camera anchors, paint and cabin-trim swatches (official palettes, sourced), dimension rulers, Studio / City toggle, URL state | done (2026-10-05) |
| 2 | **Studio look**: light-rig HDRs, studio set, exterior `_BAKEDAO`, ground shadow, cabin re-bake, Cycles studio stills and triptych QA. RX first, then SU7 | exterior occlusion, baked ground shadow and Cycles studio stills done for both cars (2026-10-06); cyclorama lightmap, cabin re-bake and per-material environments deliberately not built (see section 5) |
| 3 | **Openings and wheels** (RX pilot): split doors and tailgate, jambs, sills, a modelled boot and frunk, wheel designs and caliper colours. References first | openings done for both cars: the four doors, the bonnet with its frunk and the tailgate or trunk lid with its boot open in the showroom (RX 2026-10-06; SU7, from 42 approved photographs, 2026-10-06); the cabins are baked shut and open; the RX's three wheel designs (22 in Fengying, 21 in Yufeng, 21 in Sport and its blue accent) and its caliper colours are in the Wheels tab, and both cars' wheel faces are traced from the approved photographs (2026-10-07) |
| 4 | **X-ray, hotspots, space**: beltline split, ghost greenhouse, seat hotspots, mannequins, luggage, boot dimensions | the ghost greenhouse is built (the RX's X-ray tab, 2026-10-06); hotspots, mannequins, luggage and boot dimensions are still to do |
| 5 | **Compare, mobile, payload**: split-screen compare, portrait anchors, quality tier, meshopt / KTX2 export, ≤ 20 MB per car | planned |

Order (owner, 2026-10-05): the openings and the x-ray come before the studio look.

### Facts gathered for the later phases

- The Luxeed RX has a frunk and a 622 L boot with a 30 L hidden compartment;
  tyres are staggered (255 front, 275 rear); the calipers are six-piston at
  the front. The SU7 Ultra has a 559 L boot and a 105 L frunk. Both cars'
  frunks and boots are modelled now (without the stated volumes or the hidden
  compartment).
- Cars with a camera-matched cabin keep their own `driverEye`; the showroom's
  driver anchor reads it.

### Sources for the colour data

The paint and trim palettes in `src/data/vehicles/*.ts` cite their own
sources. In short:

- **Luxeed RX:** six paints and four interior colours from the maker's page,
  <https://hima.auto/zhijie/rx/>.
- **Xiaomi SU7 Ultra:** five paints from <https://www.xiaomiev.com/ultra>;
  interior pairings from Autohome's configuration table for the 2025 Ultra
  (<https://car.autohome.com.cn/config/spec/70545.html>), since Xiaomi's page
  does not list them. Two of those pairings appear only there.

Colour values are approximate: they are matched by eye to the makers'
imagery under our own studio rig, and the interface labels them as such.

## 7. Door sounds and the wheel view (2026-10-21)

Two things the owner asked for after looking at HIMA's hall (<https://hima.auto/3d-view/>), which we match in behaviour, not in assets.

**Sounds of the openings.** A door, the bonnet and the tailgate make a noise as they move: the handle and the door coming off its
seal as the part starts to open (`release`), and the thud and latch as it shuts (`shut`). The charge flap and the stop at the end of
an opening swing are silent (no recording). The first version was synthesised in code and the owner rejected it as fake (2026-10-21);
it was replaced the same day by the owner's own recordings, three files supplied for the purpose: `open-car-door.mp3` (a handle
click, then the door popping open), `car-door-shut.mp3` (one shut) and `car-door-closing-and-opening.mp3` (7.5 s: a shut at 0.75 s,
the handle and the door opening at 3.0 s, a second shut at 5.0 s). `scripts/tech-tools/cut-sounds.mjs` cuts five excerpts out of them
(two openings, three shuts) into `public/sounds/*.wav` (mono, 44.1 kHz, short fades, peak 0.7 for an opening and 0.92 for a shut); the
cut points were read off the loudness envelopes, and the long file's events were told apart by their shape and spectrum (a shut is a
broadband thump preceded by the door's swish; an opening is a click, then a bass pop 0.2 s later, like the single opening file). The
author could not listen: if a take is the wrong kind, change its times in the script and run it again. The owner said the same takes
may be used for the tailgate and the bonnet: they play pitched down (bonnet 0.86, tailgate 0.93; the recordings are bass-heavy and a
laptop speaker loses what goes lower). `src/lib/sound/engine.ts` plays them through the Web Audio API: the files are fetched when the
page loads and decoded when the context is made (on the first press or key, since browsers keep audio silent until then; a cue before
that is dropped); a take other than the last is chosen at random, each play is up to 3 per cent faster or slower; the same cue twice
within 70 ms is one; cues that pile up (Close all) are spread by 45 ms and quietened; a part is panned by where it is in the picture
and quietened by how far the camera is from it; from the seat the sound goes through a 1.4 kHz low-pass and is quieter. The timing comes
from the hinges (`Hinges.listen` in src/lib/openings.ts): `release` at the start of an opening swing, `shut` as the closing swing
ends (97 per cent of it, so the impact, which is 20 to 30 ms into each take, lands as the part meets its seal), nothing for the state
the car is put in when it mounts. A speaker button in the top bar (next to the info button) turns it off; the choice is kept in
`localStorage` (`voltway.sound`).
Licence: the three recordings are royalty-free sound effects from Pixabay (the owner downloaded them, 2026-10-21), used under the
Pixabay Content License, which allows free use, commercial use included, without attribution; the excerpts in `public/sounds/` are
edited cuts of them (the originals are not in the repository).

**The Wheels view.** HIMA's wheel anchor shows the front half of the car nearly side-on (a touch from the front), the wheel low and
large (about 30 per cent of the picture's height), the nose at the left. Ours was a close-up of the wheel and its arch. The pose in
`src/lib/showroom/anchors.ts` (`id === 'wheel'`) is now: azimuth 74 degrees, elevation 6, field of view 24; the camera orbits about the
wheel itself, and the picture is slid so that the wheel sits to the right of the middle (a view offset of 10 per cent of the width, as
the other poses slide for a device) with the nose in; the camera stands so that the picture is 45 per cent of the car's length tall,
and on a narrow window far enough back to keep the nose and the door in (the picture is at least 60 per cent of the car's length
wide). The visitor can still zoom in to the rim (minimum distance 1.3 m) and turn the car.
