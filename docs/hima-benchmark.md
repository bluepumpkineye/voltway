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

**In Blender** (Phase 2, a new `carkit/studio.py` extending `bake.py` and
`scene.py`)

- Per-vertex `_BAKEDAO` for the exterior from the existing machinery
  (`prepare`, `vertex_lighting`, `smooth`, `to_generic`) under a uniform white
  world; UV2 textures only where a triptych shows banding.
- A white cyclorama with a baked lightmap, exported as `showroom.glb`; a baked
  ground-shadow quad per car.
- The cabin re-baked under the studio, with the doors open once they open.
- `scene.studio_white()` for Cycles stills (384+ samples, adaptive threshold
  0.005, OptiX denoise, Khronos PBR Neutral) from the same camera anchors as
  the web, so photo, web and Cycles line up in the triptych QA.

**Decisions not taken, and why**

- `KHR_materials_variants`: three.js only supports it through a third-party
  plugin, and runtime parameter swaps are simpler and can be tweened.
- UV2 AO textures everywhere: per-vertex AO is already in the pipeline and
  costs no texture memory.
- Paid bakers or generators: ruled out by the project rules.

## 6. Roadmap and status

Decisions (owner, 2026-09-30): the white studio is the default scene with the
Shanghai and Beijing city worlds kept as a toggle; the Luxeed RX pilots every
Blender change; missing reference photos are found by us and **approved by the
owner before any modelling**.

| Phase | What | Status |
|---|---|---|
| 0 | This document | done |
| 1 | **Showroom shell** at `/showroom/[slug]`: both cars, today's GLBs. Bottom tab bar, camera anchors, paint and cabin-trim swatches (official palettes, sourced), dimension rulers, Studio / City toggle, URL state | done (2026-10-05) |
| 2 | **Studio look**: light-rig HDRs, studio set, exterior `_BAKEDAO`, ground shadow, cabin re-bake, Cycles studio stills and triptych QA. RX first, then SU7 | queued: after Phases 3 and 4, because the cabin re-bake wants the doors open |
| 3 | **Openings and wheels** (RX pilot): split doors and tailgate, jambs, sills, a modelled boot and frunk, wheel designs and caliper colours. References first | in progress (RX first): the four doors, the bonnet with its frunk and the tailgate with its boot open in the showroom (2026-10-06); the cabin is baked shut and open; the wheels and the SU7 (42 reference photos waiting for approval) are next |
| 4 | **X-ray, hotspots, space**: beltline split, ghost greenhouse, seat hotspots, mannequins, luggage, boot dimensions | the ghost greenhouse is built (the RX's X-ray tab, 2026-10-06); hotspots, mannequins, luggage and boot dimensions are still to do |
| 5 | **Compare, mobile, payload**: split-screen compare, portrait anchors, quality tier, meshopt / KTX2 export, ≤ 20 MB per car | planned |

Order (owner, 2026-10-05): the openings and the x-ray come before the studio look.

### Facts gathered for the later phases

- The Luxeed RX has a frunk and a 622 L boot with a 30 L hidden compartment;
  tyres are staggered (255 front, 275 rear); the calipers are six-piston at
  the front. The SU7 Ultra has a 559 L boot and a 105 L frunk. Both frunks
  are currently missing from the models.
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
