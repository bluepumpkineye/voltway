# carkit — the car part catalogue and pipeline library

Everything that is not one car's data. A car module (`su7_*.py`) holds that
car's hardpoints, curves and panel layout and calls into these modules. The
workflow is in [`docs/3d-pipeline.md`](../../../docs/3d-pipeline.md). Every
catalogue part is on the contact sheet at `blender/renders/catalogue/contact_sheet.png`
(`preview.contact_sheet()`).

```python
import sys; sys.path.append(r"<repo>/blender/scripts")
import carkit; carkit.reload()          # after editing any carkit module
```

## Module map

| Module | What it gives you |
|---|---|
| `geom` | `Curve` (natural cubic / PCHIP / linear), `Joined`, `catmull_rom` (centripetal, arc-length resampled), loops (`smooth_loop`, `round_rect`, `rounded_loop`), vector helpers, orientation helpers (`away_from`, `axial`, `radial`), `aerofoil` |
| `mesh` | `obj`, grids and strips, `revolve`, `text_mesh`, `orient`, `mirror_y`, `solidify`, `bevel`, `finish`, `tri_count` |
| `cut` | cutting prisms (`prism_y`, `prism_x`, `prism_dir`), `difference` (exact, hole-tolerant, then `weld`), `weld` (merge/dissolve the slivers a boolean leaves), `cut_arches`, `sheet_bvh` + `prune_off_sheet` (drop cutter faces an open sheet keeps) |
| `place` | `Placer`: ray-cast placement onto built meshes (`radial`, `along`), `on_surface` |
| `body.loft` | `LoftBody`: the flank surface from profile curves and a (w, v) section; `surface`, `surface_normal`, `section_v`, `v_at_z`, `v_along`, `surface_offset`. Optional `z_dome`/`y_dome`: a second crown inboard of the fender crown (hood domes over a lower centre, a groove between them for the hood's shut line; `Section.dome_groove`, `dome_flank`). Optional `y_glass`: the greenhouse's base half-width where it sits inside the plain step - a cabin tapering rearward on broad haunches (`Section.glass_mid`) |
| `body.caps` | `WrapCap`: nose and tail patches joined G1 to the flank |
| `body.model` | `CarBody`: loft + caps, `project`, `proud`, `side_point`, `dims_report` |
| `body.panels` | `build_panels(specs, butt_bevel=)` with shut lines (`butt_bevel=False`: no rounded rim where panels butt without a gap), `shadow_shell(nv=, inset=)`, `wheel_liners(inner_wall=, wall_z=)`, `underbody` |
| `body.fascia` | `split_nose`, `intake_tunnel`, `blade`, `valance`, … |
| `body.morph` | `from_donor()`: a donor car's curves rescaled to new main dimensions |
| `parts.lamps` | `lens`, `seals`, `band_between`, `projector` |
| `parts.aero` | `rear_wing`, `roof_spoiler`, `ducktail`, `splitter`, `diffuser`, `corner_fin`, `side_skirt` |
| `parts.grilles` | `diamond`, `hexagon`, `slats`, `dots` |
| `parts.fittings` | `mirror_head`, `mirror_cap` (big rear glass face, tapered nose, painted cap over a black underside), `flush_handle`, `vent`, `lidar_pod`, `text_badge`, `plate`, stripes and patches |
| `parts.wheels` | `PRESETS` (`su7_ultra_hairpin`, `aero_5window`, `turbine_10`, `y_spoke_5`, `twin_5`, `blade_5`, `multi_10`), `build_wheel`, `build_set`; `blade(split_hub=)` for a machined face that narrows to the hub. `rim_d` is the VISIBLE lip diameter (~17 mm radius over the bead seat) |
| `materials` | `build_library(paint=, rim=, caliper=)` with `PAINTS`, `RIMS`, `CALIPERS`; `export_safe()` (glass → opaque for glTF) |
| `textures` / `surfacemaps` | baked carbon weave; tileable leather, Alcantara, carpet, brushed and perforation maps (`TILE` sizes in metres) |
| `interior.sweep` | `Sweep` (sectioned sweeps with panels on section columns), `grid_mesh`, `tube`, `piping`, `stitches`, `smooth_path` |
| `interior.steering` | `wheel(col, lib, SPEC, centre, tilt)`; `SU7_ULTRA` and `LUXEED_RX` specs (hub `ring`, spoke pad `frame` / `pad_role`, U lower spoke `bottom_half`, `emblem`) |
| `interior.seat` | `seat(col, lib, SPEC, bight)`, `base`; `SU7_ULTRA_FRONT` and `LUXEED_RX_FRONT` specs (a centre `stripe`, a dark top `cap_from`) |
| `interior.door` | `DoorCard`: `band`, `carrier`, `belt_cap`, `armrest`, `curve` |
| `interior.cabin` | `headliner`, `edge_band` (tight pillars), `pillar_trim` (broad pillars, and any concave section: a greenhouse stepping in), `floor`, `sill`, `bulkhead`, `wall`, `wheelhouse_trim` |
| `interior.fittings` | `box`, `slab`, `screen_quad` (the HMI contract), `screen_material`, `round_slab`, `disc`, `plate_with_hole`, `ngon_cap`, `round_rect_xy`, `lights` (the render rig) |
| `interior.materials` | `build_library(accent=)`: Nappa, Alcantara, threads, satin, piano, chrome, brushed, carpet, speaker, **`INT_Ambient`** |
| `bake` | `prepare`, `vertex_lighting` (Cycles diffuse light per vertex), `smooth`, `to_generic` (`_BAKEDLIGHT`), `probe` / `probe_mix` (cabin reflection HDR), `thin_glass` (daylight through the glazing for cabin passes), `backdrop` / `backdrop_light` (the world outside for the viewer) |
| `export` | `bake_modifiers`, `join`, `merge_for_export(groups, protected)`, `export(..., draco, attributes)` |
| `build` | `fresh_collection`, `ensure_uvs` (world-space UVs), `report` |
| `scene` | studio rig, cameras, `world_gradient`, `hdri_world` (an HDRI file, turned and sun-clamped), `use_cycles`, `render` |
| `preview` | `contact_sheet()` |
| `qa.refmatch` | camera registry, `solve_side_camera`, `solve_camera` (general LM: points, rim circles, extra unknowns), `on_mesh`, `ray` / `on_plane` / `project`, `overlay`, `silhouette_report` |
| `qa.checks` | `envelope`, `cabin_clearance`, `budget`, `fingerprint` / `compare` (refactor proof) |
| `qa.zebra` | reflection-line renders |
| `qa.leaks` | exterior surfaces visible from the seats (`cameras`, `find`, `print_report`) |
| `qa.hmi_capture` | the app's HMI as a render texture (`capture(slug, query=)` in any state, `apply`, `restore_plain`) |
| `qa.web_capture` | the web viewer through a matched camera; `triptych` photo, web, Cycles; `patches` |
| `jev` | the decision layer on Jev (text-only, typed answers): `finder.find` (which part / builder / manual section fits a need), `triage.triage` / `guard` (known failure + fix; `known_failures.FAILURES`), `review.route` (notes → module, action, severity), `onboard.manifest` (spec text → feature checklist). Shell: `jev_cli.py`. See `docs/3d-pipeline.md` §8 |

## Conventions

- Axes: +X forward, +Y left (the driver's side for LHD), +Z up, metres. glTF
  arrives in three.js as (x, z, −y).
- Parts are built on the left and mirrored (`mesh.mirror_y`), unless they
  differ side to side (door cards: one per side, no mirror).
- Normals are set by `mesh.orient(me, outward_fn)`. A `Sweep` takes
  `outward=±1`, since its raw normal is T × (direction of increasing section
  index).
- Names the web app relies on are listed in `docs/3d-pipeline.md` section 4.
