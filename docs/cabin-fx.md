# Cabin FX: the interior upgrade system (2026-11-13)

The BYD Seal is the reference. Everything that improved it is a shared system, so no car re-implements it. Code: `src/components/viewer/cabinfx/`, `src/lib/showroom/interiorPreset.ts`; Blender: `blender/scripts/bpy_interior_polish.py` (shared) and `seal_polish.py` (the Seal's own layout, the pattern for every car).

## The five systems

| # | System | Where | What it does |
| --- | --- | --- | --- |
| 1 | `upgradeInteriorMaterials(scene, themeConfig)` + `retuneInteriorMaterials` | `cabinfx/materials.ts` | Standard to physical by material name: leather (grain normal, a roughness map tiled like the normal map, sheen), perforated leather (normal stronger by 1.25), Alcantara (sheen 1.0 / 0.8, roughness 0.85), screen glass and cluster glass (clearcoat 1.0, clearcoatRoughness 0.04), piano black (`#070707`, coat), chrome (metal 1, rough 0.08, env 1.5), brushed metal, the softbox gloss environment. `themeConfig` is the car's `configurator`: it names the materials the colour-theme switcher recolours, so the upgrader never writes `.color` and the sheen tint follows the live colour. The seat's windscreen and side glass get a thin coat and a little mirror in `useGlass` (Openings.tsx). |
| 2 | `interiorPostProcessing` + camera preset | `cabinfx/InteriorFx.tsx`, `cabinfx/settings.ts`, `lib/showroom/interiorPreset.ts` | N8AO (metres), AgX with saturation and contrast restored, bloom that only the ambient strips reach, the footwell falloff (in `CarModel.hallLighting`), the softbox environment, the seat lens (52 degrees, widening capped at 56) and a 110 degree head-turn limit. Mounted only in the seat on the Interior tab; the exterior never changes. |
| 3 | `DriverClusterTextureGenerator(brand, ...)` | `cabinfx/cluster.ts` | One canvas pipeline (2048 px wide, the quad's own aspect, mapped like the picture it replaces, live gear / charge / ADAS from the store) and three layouts: `gauge` (Seal, Z9, RX), `wide` (G9L, ES8, SU7), `calm` (7X, Voyah, 06T). A brand is data in `CLUSTER_BRANDS` (layout, type, weight, accent, system name, range cycle). Every cabin GLB names the picture `INT_Display_screen_cluster`, so there is nothing to wire per car. |
| 4 | `ButtonIconAtlas` + `applyInteriorDecals(scene, carId)` | `cabinfx/icons.ts` | One 8 x 4 atlas drawn on a canvas (`ICONS`, the same list as `bpy_interior_polish.ICONS`). A car gets icons when its cabin GLB carries `decal_*` nodes (material `M_Icons`); WHERE they sit is the car's mapping, written in Blender with `place_icons`. Decals sit 0.4 mm over the key, polygon offset -1, emission 0.25. A door card's decals hang under the card's node, so they swing with the door. Ambient spill ribbons (`M_Glow`, `cabinfx/spill.ts`) are the same mechanism. |
| 5 | `bpy_interior_polish.py` | `blender/scripts/` | `remove_helpers` (curve / wire / cutter leftovers, unapplied booleans), `bevel_hard_surfaces` (Bevel 2 segments, 2 mm, 35 degrees, clamped, then Weighted Normal keep-sharp, applied), `shade_smooth`, `collar_loop` / `rounded_rect_path` (2 mm dark collars), `icon_quad` / `place_icons`, `glow_ribbon`, `finish_decals` (joins decals into `decal_*` objects that `merge_for_export` keeps apart and `aoatlas` leaves out of the bake), `export_names_ok`, and `polish(col, bevel_pattern, smooth_pattern)` as the one call. |

## Locked defaults (the Seal's approved look, `cabinfx/settings.ts` FX_DEFAULTS)

| Group | Values |
| --- | --- |
| Tone | AgX, exposure 0.9, saturation 0.30, contrast 0.22 |
| N8AO | radius 0.28 m, distanceFalloff 0.6, intensity 2.4, 16 samples, denoise 8 samples / radius 10 |
| Bloom | threshold 1.1, smoothing 0.25, strength 0.55, radius 0.6; ambient strips x 4.0; spill on leather 1.1 |
| Footwell | light at the floor 0.25, over 0.55 m |
| Gloss | softbox room on, glass / piano env 1.5, chrome envMapIntensity 1.5 |
| Materials | leather normalScale 0.9, roughness 0.62, sheen 0.15; Alcantara sheen 1.0 |
| Camera | fov 52 (widening cap 56), head turn +/- 110 degrees |

`?debug=true` shows the lil-gui panel on any car; "copy values (JSON)" puts the current numbers on the clipboard, to paste into `FX_DEFAULTS`. `?cabinfx=0` turns everything off for a before / after. Both flags are read from the URL the page loaded with and kept for the session.

## Per-car presets (`CAR_PRESETS` in `cabinfx/settings.ts`)

Every cabin was matched to its photographs under the Neutral curve, and AgX moves a darker cabin up and a brighter one down by different amounts. Each car's exposure is the one at which the seat view's mean luma with the upgrade on is 1.03 x the mean with it off, the Seal's own relationship (measured by sweeping the exposure 0.70-0.94 in the browser, see the table; shadows deepen by the same footwell / AO / contrast treatment as the Seal).

| Car | Exposure | Why |
| --- | --- | --- |
| BYD Seal | 0.90 | the reference (126 -> 130) |
| Zeekr 7X | 1.00 | bright cream cabin, AgX holds whites down |
| XPeng G9L | 0.90 | lands on 1.03 at the default |
| Voyah Passion S | 0.90 | 1.015 at the default |
| Luxeed RX | 0.80 | dark cabin, AgX lifted it 8 % at 0.9 |
| NIO ES8 | 0.82 | |
| Denza Z9 | 0.90 | 1.03 at the default |
| Avatr 06T | 1.05 | extrapolated (0.987 at 0.94); the panel can refine it |
| Xiaomi SU7 | 0.83 | |

## What a new car needs

Automatic, from the shared code (nothing to do): materials, post-processing, footwell, gloss environment, camera preset, the cluster (give it an entry in `CLUSTER_BRANDS`), ambient colour (the car's `cockpit.ambientHue`), the colour-theme switcher, Studio / City.

Car-specific, in Blender (one `<car>_polish.py` called last from the car's cabin build, copy `seal_polish.py`):
1. `BP.polish(col, bevel_pattern, smooth_pattern)` for the car's hard surfaces and hero curves.
2. Collars where parts meet: `BP.collar_loop` (column / dash, screen mount, charge tray, key recesses).
3. Icons: `place_icons([(name, centre, up, normal, size, icon), ...])` at the car's own key positions, door packs, charge pad.
4. Ambient spill: `BP.glow_ribbon` along the car's light guide, if it has one.
5. `BP.finish_decals(col)` last. The car's export must go through `carkit.export.merge_for_export` (they all do) and `carkit.aoatlas`.
6. Re-export the cabin (background Blender, about 6 minutes) and check the cluster is not buried or hidden by the wheel hub (the Seal's quad was 11.5 mm behind the band glass: `seal_polish.fix_cluster`).

## Fleet status (2026-11-13)

Automatic on every car (web side, nothing per car): materials, the composer (N8AO, AgX, selective bloom on the light guides only), footwell, gloss environment, seat lens and head-turn limit, per-car exposure, the live cluster, the seat's glass, the colour-theme switcher, Studio / City, the debug panel.

| Car | Cluster | Blender polish (module) | Icons placed | Spill ribbon | Notes |
| --- | --- | --- | --- | --- | --- |
| BYD Seal | gauge, follows the HMI theme | `seal_polish.py` | 40+ (wheel, selector, charge pad, window / lock / mirror / boot keys on all doors) | yes, dash shelf | the reference |
| Zeekr 7X | calm, thin type | `zx_polish.py` | 14 (two wheel pods, five screen keys, charge pad; dark ink on the light keys) | no light guide on the dash | door switch pack is one moulded band: no keys to mark |
| XPeng G9L | wide, minimal | `g9l_polish.py` | 2 (the lower dials) | yes, under the purple slot | spoke pads are plain leather plates |
| Voyah Passion S | calm, champagne accent | `car_polish.py` (generic) | 0 (the wheel has no buttons) | no | the cabin was already near white before this work |
| Luxeed RX | gauge | `car_polish.py` | 1 (the BOOST dial) | no | |
| NIO ES8 | wide, light type | `car_polish.py` | 0 (the wheel has no buttons) | no | the NOMI head is untouched |
| Denza Z9 | gauge, champagne accent | `car_polish.py` | 0 | no | the cluster sits behind the wheel's rim from the seat; the wheel pods have keys to mark (a `z9_polish.py`) |
| Avatr 06T | strip (the cluster is a 1.08 x 0.06 m band) | none | 0 | no | the cabin ships with a baked light map; a re-export needs `export_a06t.web_cabin(lightmap=True)` and the owner's eye |
| Xiaomi SU7 | wide, orange accent | `car_polish.py` | 2 (the red dial, the brushed key) | no | |

To raise a car to the Seal's level: write its own `<car>_polish.py` from `seal_polish.py` (keys, charge pad, light-guide spill), drop its entry from `car_polish.CARS`, re-export.

## BYD Seal (reference)

`seal_polish.py`: cluster stood proud of the band glass with a bezel; key collars, screen-neck collar, column gasket ring, charge-tray collar; ADAS housing, wipers, B-pillar belt loops and webbing; icons on the 10 wheel keys, the 8 selector keys, the charge pad, the driver's window / lock / mirror / child keys, the other three doors' rockers, the boot switches; glow ribbon under the dash light guide; bevel + weighted normals on 31 hard surfaces; wheel window chamfers removed (they read as white wire strokes); the wheel plate pulled inside the rim (it poked a black diamond out of the leather).
