"""The failures that have already cost time, with their fixes.

One entry per failure: what it looks like (a traceback line or a symptom in a
render), why it happens, and the fix that worked. triage.py asks Jev which
entry a new error or render symptom is. Add an entry whenever something costs
real time; the lessons list in docs/3d-pipeline.md section 7 is the prose
version of this table.
"""

FAILURES = {
    # ---- Blender / MCP
    "mcp_no_ui_context": dict(
        looks_like="RuntimeError or AttributeError from bpy.ops: 'Context has no active_object', "
                   "'context is incorrect', 'poll() failed', operator needs a 3D view.",
        cause="Code run through the Blender MCP has no window/area context, so most bpy.ops fail.",
        fix="Build with bmesh or the data API (bpy.data, mesh.from_pydata, modifiers on the object) "
            "instead of bpy.ops; carkit.mesh has the builders."),
    "stale_module": dict(
        looks_like="KeyError, AttributeError or NameError for a name that does exist in the source file "
                   "(a material key, a new function), or an edit that has no effect.",
        cause="Blender keeps modules imported between runs, so the old version is used.",
        fix="Pop the module from sys.modules before importing (carkit.reload(); build_rx.parts() also "
            "pops rx_materials), or importlib.reload."),
    "mcp_call_timeout": dict(
        looks_like="The MCP call returns a timeout or the connection drops; a long render, bake or "
                   "build step (over about 3 minutes) was running.",
        cause="Blocking MCP calls are cut off after a few minutes.",
        fix="Split the work into shorter calls, lower samples/resolution for checks, and queue long "
            "bakes on a persistent Blender timer; export in a direct call."),
    "homefile_reset_lost_state": dict(
        looks_like="After a build with reset (read_homefile), scene cameras, the studio rig, timers or "
                   "registered reference cameras are missing; KeyError for a camera name.",
        cause="read_homefile wipes the scene, non-persistent timers and handlers.",
        fix="Re-run scene_setup.main() and re-register the cameras; use persistent timers."),
    "localized_node_name": dict(
        looks_like="nodes['Principled BSDF'] is None or KeyError on a shader node name.",
        cause="Node names are localized or renamed; names are not stable.",
        fix="Look nodes up by type: next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')."),
    "enum_identifier": dict(
        looks_like="TypeError: enum 'X' not found in (...) when setting a property.",
        cause="Enum identifiers change between Blender versions.",
        fix="Read the valid identifiers from bl_rna.properties[...].enum_items and pick from them."),
    # ---- carkit API misuse
    "curve_arithmetic": dict(
        looks_like="TypeError: unsupported operand type(s) for +: 'Curve' and 'float' (or -, *).",
        cause="geom.Curve objects are callables, not numbers.",
        fix="Wrap in a lambda (lambda x: C(x) + 0.01) or use Curve.mapped / offset helpers."),
    "polyline_three_tuples": dict(
        looks_like="ValueError: too many values to unpack (expected 2) around geom.polyline output.",
        cause="geom.polyline returns (x, y, z) 3-tuples.",
        fix="Unpack three values: for (_x, y, z) in pts."),
    "grid_outward_not_callable": dict(
        looks_like="TypeError: 'tuple' object is not callable (or 'Vector' object) inside mesh.grid.",
        cause="mesh.grid's outward argument must be a function of the point.",
        fix="Pass geom.axial(...), geom.radial(...) or geom.const((0, 1, 0))."),
    "cap_rows_returns_pair": dict(
        looks_like="Indexing or iteration error right after a cap_rows(...) call.",
        cause="cap_rows returns (rows, vs), not rows.",
        fix="rows, vs = cap_rows(...)."),
    "rounded_panel_centre": dict(
        looks_like="Error or misplaced part from rounded_panel with a 2D centre.",
        cause="rounded_panel expects a 3D centre (x, y, z).",
        fix="Pass the full (x, y, z) centre, e.g. from a face() or on_tail() helper."),
    # ---- geometry symptoms in renders
    "preview_left_visible": dict(
        looks_like="A grey band, doubled surface or odd reflection over glass or bodywork in a render, "
                   "that is not in the real model's parts.",
        cause="The preview skin collection (RX_Preview) was left visible to the render.",
        fix="Exclude the preview collection from the view layer before rendering (rx_preview.show(False))."),
    "shadow_shell_occludes": dict(
        looks_like="A recess or pocket (plate recess, vent) renders solid black or flat.",
        cause="The 7.2 mm inset shadow shell sits in front of anything recessed deeper than it.",
        fix="Keep pockets shallower than the shell (about 6 mm) or cut the shell there too."),
    "see_through_gap": dict(
        looks_like="The background shows through a hole at a panel junction or the corner where a "
                   "cap meets the flank.",
        cause="A panel stops short of the cap edge or the centre line.",
        fix="Run the panel to the cap limit (e.g. Z_HI) with top_to_centre, and put a black underlay "
            "behind glass-to-paint junctions."),
    "open_wheel_house": dict(
        looks_like="White or background-coloured streaks, or the far wheel, visible through a wheel "
                   "arch from a raised side view.",
        cause="The wheel liner is an arch shell open on its inboard side: the view runs under the car "
              "and out through the far arch.",
        fix="wheel_liners(..., inner_wall=True, wall_z just above the floor)."),
    "steered_wheels_in_photo": dict(
        looks_like="A solved camera fits the car but the projected FRONT rim ellipse is narrower or "
                   "offset from the photo's, while the rear wheel matches.",
        cause="The press photo has the front wheels steered towards the camera.",
        fix="Judge wheels on the rear one; do not change the camera or the wheel size for it."),
    "shell_pokes_through": dict(
        looks_like="Black triangles or notches on a shut line or in a hollow of the bodywork, where "
                   "ray casts hit the shadow shell before the paint.",
        cause="The shadow shell sits only ~2.5 mm under the skin by default; a concave feature (a groove "
              "between hood dome and fender crown) lets it poke through.",
        fix="Sink it: shadow_shell(..., inset=0.020) and a finer nv."),
    "fan_shading": dict(
        looks_like="Star or fan shaped shading streaks across a small flat part (pod, badge base).",
        cause="An n-gon or triangle fan with smoothed normals.",
        fix="Build it with rounded_panel (quad rings) or bevel the rim and use flat shading on the face."),
    "chord_across_corner": dict(
        looks_like="A part meant to follow a corner (lamp, trim) cuts straight across it or floats off it.",
        cause="Nearest-point projection spans a corner as a chord.",
        fix="Ray-cast onto the body (place.Placer.radial / along)."),
    "sheared_quads": dict(
        looks_like="Stretched or sheared quads, jagged shut lines after trimming a sheet.",
        cause="Trimming the grid instead of cutting it.",
        fix="Exact booleans on the half sheet before mirroring (carkit.cut), then prune_off_sheet."),
    "bevel_explodes_on_slivers": dict(
        looks_like="Streaks or spikes shooting far away from a panel in a render (metres off the car), "
                   "or a panel's evaluated vertices at huge coordinates (1e29) while its base mesh is fine.",
        cause="An EXACT boolean left a sliver (edge under 0.2 mm, zero-area face) and the Bevel modifier "
              "explodes on it.",
        fix="Weld after the boolean: carkit.cut.weld(ob) (cut.difference now does it); find the object "
            "by scanning evaluated vertices for coordinates outside the car's envelope."),
    "cap_bottom_collapses": dict(
        looks_like="A part placed along a nose or tail cap's lower edge comes out dead straight "
                   "across, bunched near the centreline, or hidden: every point at the edge lands on "
                   "the same centre point.",
        cause="The cap's bottom row tucks under; below its lowest point on the centreline "
              "WrapCap.wv_at finds no section and returns w = 0 for every y.",
        fix="Sample no lower than the cap's centreline bottom (rx_front.CAP_LOW = 0.280) and "
            "check the part's y extent after building."),
    "photo_side_mirrored": dict(
        looks_like="A 3/4 camera solve converges to a negative focal length, a camera on the "
                   "wrong side of the car, or a huge rms with every wheel point fitted.",
        cause="The photo shows the other side of the car: with the nose pointing RIGHT in the "
              "frame you are looking at the car's right side (-y).",
        fix="Check which way the nose points before writing correspondences; flip y on every "
            "model point and start the camera on that side."),
    "trim_chord_over_ledge": dict(
        looks_like="The leak report keeps finding paint just under a side window (RX_Quarter at the "
                   "quarter light) however far a pillar or sill trim is moved; tracing the rays shows "
                   "them reaching paint INBOARD of the trim.",
        cause="A chord trim (cabin.edge_band) spans a concave section - a ledge the greenhouse "
              "steps in by (LoftBody y_glass) and the rounded rise to the glass - so the rise's "
              "inner wall stands between the trim and the cabin.",
        fix="Use an offset trim there (cabin.pillar_trim, inset ~14 mm) that follows the section "
            "round the step, and run it onto the glass edge."),
    "wheel_liner_above_hump": dict(
        looks_like="The rear wheel liner (RX_Liner_R) shows behind the rear door card from both rows.",
        cause="The wheelhouse trim's hump rolled over below the liner's top (0.76 against 0.93 m) and "
              "outboard of its inner wall.",
        fix="cabin.wheelhouse_trim with y_hump inboard of the liner wall and z_hump above its top "
            "(RX: 0.672, 0.975); the same up front - kick panels step in where the front liner "
            "narrows the footwell."),
    "live_bake_hangs_blender": dict(
        looks_like="Blender disappears during a bake or a long render driven through the MCP socket; "
                   "Windows logs AppHangTransient for blender.exe.",
        cause="The add-on runs code on Blender's main thread: a multi-minute bake blocks the UI, "
              "Windows shows 'not responding' and the process is closed.",
        fix="Run bakes and exports in a background Blender (blender -b --factory-startup "
            "--python-expr ...; export_rx.web_full()), never in the user's open session."),
    "curvature_kink": dict(
        looks_like="Zebra stripes break or kink; a highlight shows a crease on a smooth surface.",
        cause="A profile curve is not C2 or sections are not resampled by arc length.",
        fix="Use natural cubic Curve/Joined profiles and arc-length resampling; check with qa.zebra."),
    "slope_cache_drift": dict(
        looks_like="Nose or tail geometry changes slightly between runs or after a refactor; the "
                   "fingerprint drifts though no data changed.",
        cause="A history-dependent slope cache keyed differently for nose and tail.",
        fix="Share one cache keyed (front, round(v, 5))."),
    # ---- materials, bake, export, web
    "lights_too_hot": dict(
        looks_like="Paint or panels render washed out, patch values far above the photo's.",
        cause="Light rigs start too hot.",
        fix="Calibrate with patch values against the photo; Khronos PBR Neutral in Blender and three.js."),
    "export_transmission": dict(
        looks_like="Glass or lamp lenses look different (opaque, black or missing) after glTF export.",
        cause="Transmission is not exported for the web pipeline.",
        fix="Use the export_safe glass settings (tinted, no transmission) and check in the web viewer."),
    "paint_exported_as_metal": dict(
        looks_like="A metallic (flaked) paint renders as dark solid metal in the web viewer, although "
                   "Cycles shows a coloured paint; the GLB's paint material has no metallicFactor.",
        cause="The flake mask drives Metallic procedurally; the glTF exporter omits metallicFactor and "
              "glTF reads a missing one as 1.0.",
        fix="materials.export_safe() before export (sets a procedural Metallic to 0); "
            "carkit.export.check_paint() fails the export if it happens again."),
    "sheen_full_strength": dict(
        looks_like="A paint with a sheen lobe reads pastel or washed-out (lavender, milky) in three.js, "
                   "much lighter than the Cycles render.",
        cause="glTF sheen has no weight: the exporter writes Sheen Tint alone, so a weight of 0.28 "
              "ships at 1.0.",
        fix="materials.export_safe() folds Sheen Weight into Sheen Tint before export."),
    "metal_bakes_black": dict(
        looks_like="Metal parts come out black in a diffuse/vertex light bake.",
        cause="DIFFUSE bakes ignore metallic surfaces.",
        fix="Set metallic to 0 for the bake, restore after."),
    "gltf_color0_first_only": dict(
        looks_like="Baked vertex colours are missing on all but one primitive after export.",
        cause="Blender 5.2 glTF exports COLOR_0 for the first primitive only.",
        fix="Ship baked data as a custom _ATTR attribute (_BAKEDLIGHT)."),
    "hdr_srgb_write": dict(
        looks_like="A saved .hdr is too bright/washed or gamma-shifted.",
        cause="Image.save() writes float .hdr through the sRGB curve in 5.2.",
        fix="Write RGBE yourself with bake.write_hdr."),
    "next_chunk_locked": dict(
        looks_like="Next.js dev server errno -4094 or a locked .next chunk on Windows.",
        cause="A wedged dev server holding the .next folder.",
        fix="Stop and restart the dev server."),
}

UNKNOWN = "unknown"
