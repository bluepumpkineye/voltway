"""Merge the Zeekr 7X build for the draw-call budget and export it to the web app.

    zeekr-7x.glb              exterior, ~380k tris, Draco, ambient occlusion per vertex
    zeekr-7x-shadow.webp      its shadow on the studio floor

Machinery in carkit.export, as for the SU7 (export_gltf.py) and the RX (export_rx.py).
The 7X lives in the showroom only (no vehicle-page viewer): vehicle data has
`assets.showroomOnly`. Nodes:

    Zeekr7X_Body        the painted shell, glass, the lamps' surrounds
    Zeekr7X_Details     fascia, lamps, trim, mirrors, badges
    Zeekr7X_Wheels      the four wheels (21 in six-Y, the Ultra's); its origin is the
                        front-left wheel's centre (the showroom's camera rig reads it)
    Zeekr7X_Multi_Wheels, Zeekr7X_Fork_Wheels
                        the two 20 in designs (zx_wheels), hidden until chosen
    Zeekr7X_Blackout    the black glass underlay and inner shadow shell
                        (the viewer hides any "*_blackout" node inside)

Runs without the MCP, in a background Blender that starts from an empty scene, so the
open session is left alone:

    blender -b --factory-startup --python-expr
        "import sys; sys.path.append(r'<repo>/blender/scripts');
         import export_zx; export_zx.web()"         # exterior only, ~3 min
"""
import os
import sys

import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

from carkit import export as _X                  # noqa: E402

MODELS = os.path.normpath(os.path.join(_HERE, "..", "..", "public", "models"))
DEST = os.path.join(MODELS, "zeekr-7x.glb")
DEST_SHADOW = os.path.join(MODELS, "zeekr-7x-shadow.webp")

BLACKOUT = ("ZX_Shell_Shadow", "ZX_Shell_Shadow_F", "ZX_Shell_Shadow_R",
            "ZX_Greenhouse_Black", "ZX_Roof_Rear_Black")
# the exterior's ambient occlusion (carkit.bake.ambient_occlusion): how far a surface
# looks for shade
AO_DISTANCE = 1.0
# the published size in metres (length, width, height): the studio stills' framing
DIMS = (4.825, 1.930, 1.656)

# joined name -> collection
GROUPS = [
    ("Zeekr7X_Body", "ZX_Body"),
    ("Zeekr7X_Wheels", "ZX_Wheels"),
    ("Zeekr7X_Details", "ZX_Details"),
    ("Zeekr7X_Blackout", "ZX_Blackout"),
]
# the other wheel designs (zx_wheels.DESIGNS): built beside the default for the export only, each a
# node of its own; the viewer shows one at a time
WHEEL_GROUPS = [
    ("Zeekr7X_Multi_Wheels", "ZX_Wheels_Multi"),
    ("Zeekr7X_Fork_Wheels", "ZX_Wheels_Fork"),
]

# The wheels ship one NODE PER CORNER, so the showroom's tech demos can steer, roll and lift them
# (src/lib/tech/rig.ts); the RX does the same (export_rx.CORNERS). Per design: <node>_<tag> holds
# everything that turns with the wheel (tyre, rim, face, disc) and <node>_Caliper_<tag> the caliper,
# which steers but does not spin. Each node's origin is the hub centre, its local frame the wheel's
# own (the build's wheel empty carries the placement), so a node spins about its axle. The viewer
# groups the four of a design back under <node>.
CORNERS = ("FL", "FR", "RL", "RR")


def _corner_col(cname, kind, tag):
    """The collection of one corner's wheel ('W') or caliper ('C') parts."""
    return "%s_%s_%s" % (cname, kind, tag)


def wheels_split():
    return bpy.data.collections.get(_corner_col(GROUPS[1][1], "W", "FL")) is not None


def split_wheels():
    """Re-collect every wheel design's parts by corner (see CORNERS). Once, after the ambient
    occlusion has been baked (it is per design, with the four wheels together) and before the
    merge."""
    if wheels_split():
        return
    for _, cname in [GROUPS[1]] + WHEEL_GROUPS:
        src = bpy.data.collections.get(cname)
        if src is None:
            continue
        for ob in list(src.objects):
            if ob.type != 'MESH':
                continue
            # a part is named <prefix><Part>_<tag> and parented to the corner's empty
            who = (ob.parent.name if ob.parent is not None else ob.name).split(".")[0]
            tag = who.rsplit("_", 1)[-1]
            if tag not in CORNERS:
                raise RuntimeError("wheel part %s has no corner (%s)" % (ob.name, who))
            kind = "C" if "_Caliper_" in ob.name else "W"
            name = _corner_col(cname, kind, tag)
            dst = bpy.data.collections.get(name) or bpy.data.collections.new(name)
            if dst.name not in bpy.context.scene.collection.children:
                bpy.context.scene.collection.children.link(dst)
            src.objects.unlink(ob)
            dst.objects.link(ob)


def wheel_corner_groups(options=True):
    """(node, collection) per corner of the default design, and of the others."""
    out = []
    for node, cname in [GROUPS[1]] + (WHEEL_GROUPS if options else []):
        for tag in CORNERS:
            out.append(("%s_%s" % (node, tag), _corner_col(cname, "W", tag)))
            out.append(("%s_Caliper_%s" % (node, tag), _corner_col(cname, "C", tag)))
    return out


def split_blackout():
    """Move the blackout layer into its own collection (its own glTF node)."""
    col = bpy.data.collections.get("ZX_Blackout") or bpy.data.collections.new("ZX_Blackout")
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for n in BLACKOUT:
        ob = bpy.data.objects.get(n)
        if ob is None:
            raise RuntimeError("blackout object %s missing from the build" % n)
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        col.objects.link(ob)
    return col


def check_transmission():
    """KHR_materials_transmission blanks the three.js frame: after export_safe()
    no exported material may transmit."""
    bad = []
    for _, cname in GROUPS:
        col = bpy.data.collections.get(cname)
        for o in (col.objects if col else ()):
            for m in (o.data.materials if o.type == 'MESH' else ()):
                if m is None or not m.use_nodes:
                    continue
                b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                t = b.inputs.get("Transmission Weight") if b else None
                if t is not None and (t.is_linked or t.default_value > 0.0):
                    bad.append(m.name)
    if bad:
        raise RuntimeError("transmissive materials left: %s" % sorted(set(bad)))


def prepare_exterior():
    """Everything the exterior needs before it is merged and exported: the blackout layer split
    off, the bay under the bonnet, the doors, the bonnet and the hatch made hinged nodes, the
    hull opened behind them, the greenhouse its own node. Once per build (ZX_Tailgate marks it
    done); the cabin's open-state bake wants the parts split, so web_full() calls it before that
    bake. The cabin's boot and hatch liner must be built first (they read the whole tail cap)."""
    if bpy.data.objects.get("ZX_Tailgate") is not None:
        return
    import zx_materials as MB
    MB.export_safe()
    split_blackout()
    check_transmission()
    import zx_openings as OP
    import zx_bays as BY
    import zx_gate as RG
    BY.build_frunk()          # the bay under the bonnet, then the bonnet as a hinged node
    BY.split_bonnet()
    BY.open_hull()
    OP.cut_underlay()         # the windows out of the black underlay: it must not stay behind
    RG.cut_underlay()         # the backlight's footprint too
    RG.build_seal()           # a black bead behind the hatch's shut line
    OP.split_doors()          # a hinged node per door (the cabin's cards: join_doors)
    OP.open_hull()            # the hull behind them, so the cabin shows when one is open
    RG.split_tail()           # the hatch: skin, backlight, lamp bar, lettering - one node
    RG.open_hull()            # the hull behind it
    RG.split_greenhouse()     # roof, rails and glass above the belt: the X-ray's ghost
    import zx_charge as CH
    CH.build()                # the charge flap (a hinged node), its port and caps (shown while it is open)


def exterior_groups(options=True):
    """Every exterior group; options=False leaves out the extra wheel designs."""
    import zx_openings as OP
    import zx_bays as BY
    import zx_gate as RG
    import zx_charge as CH
    if wheels_split():
        core = [g for g in GROUPS if g != GROUPS[1]]
        return (core + wheel_corner_groups(options) + OP.door_groups() + BY.bonnet_groups()
                + [RG.GROUP, RG.GREENHOUSE_GROUP] + CH.groups())
    return (GROUPS + OP.door_groups() + BY.bonnet_groups() + [RG.GROUP, RG.GREENHOUSE_GROUP] + CH.groups()
            + (WHEEL_GROUPS if options else []))


def exterior_meshes(options=False):
    """The car's meshes; with options=False the extra wheel designs are not among them (they
    stand where the default wheels do, so the car's own shadow and occlusion leave them out)."""
    return [o for _, cname in exterior_groups(options) for o in
            (bpy.data.collections[cname].objects if cname in bpy.data.collections else ())
            if o.type == 'MESH']


def build_wheel_options(lib):
    """The other wheel designs (zx_wheels), one collection each, on the car's own material library
    - before prepare_exterior(): rebuilding the library after it would undo export_safe(). Their
    ambient occlusion is baked one design at a time (bake_exterior_ao), since they stand in the
    same place."""
    if bpy.data.collections.get(WHEEL_GROUPS[0][1]) is not None:
        return
    import zx_surface as S
    import zx_wheels as ZW
    from carkit import build as B
    cols = []
    for (_, cname), name in zip(WHEEL_GROUPS, [n for n in ZW.DESIGNS if n != ZW.DEFAULT]):
        col = B.fresh_collection(cname)
        ZW.build_design(col, S, lib, name)
        cols.append(col)
    B.ensure_uvs(cols)
    return cols


def open_all(on=True):
    """Every door, the bonnet and the hatch swung open (or shut again)."""
    import zx_openings as OP
    import zx_bays as BY
    import zx_gate as RG
    for key, d in OP.DOORS.items():
        OP.set_angle(key, d["deg"] if on else 0.0, card=False)
    BY.set_bonnet(BY.HOOD_DEG if on else 0.0)
    RG.set_hatch(RG.OPEN_DEG if on else 0.0, card=False)
    import zx_charge as CH
    if bpy.data.objects.get(CH.FLAP) is not None:
        CH.set_flap(CH.OPEN_DEG if on else 0.0)


def interior_objects():
    col = bpy.data.collections.get("ZX_Interior")
    return list(col.all_objects) if col else []


def bake_exterior_ao(samples=512):
    """Ambient occlusion per vertex on every exterior mesh (_BAKEDAO). Before the merge,
    where the parts have their own names. The cabin is left out, so the result does not
    depend on whether this build made one."""
    from carkit import bake as BK
    prepare_exterior()
    hide = [o for o in (bpy.data.objects.get("Ground"),) if o is not None] + interior_objects()
    extra = [(cname, [o for o in bpy.data.collections[cname].objects if o.type == 'MESH'])
             for _, cname in WHEEL_GROUPS if cname in bpy.data.collections]
    # with every opening OPEN: the jambs, the bay under the bonnet and the boot are inside a
    # closed car and would bake black, and the outer skins do not change
    open_all(True)
    try:
        # the car with its own wheels, the other designs not there ...
        stats = BK.ambient_occlusion(exterior_meshes(), samples=samples, distance=AO_DISTANCE,
                                     hide=hide + [o for _, ms in extra for o in ms])
        # ... then each other design alone in the default wheels' place
        own = [o for o in bpy.data.collections[GROUPS[1][1]].objects if o.type == 'MESH']
        for cname, ms in extra:
            gone = own + [o for c, other in extra if c != cname for o in other]
            BK.ambient_occlusion(ms, samples=samples, distance=AO_DISTANCE, hide=hide + gone)
        return stats
    finally:
        open_all(False)


def bake_ground_shadow():
    """The car's shadow on the studio floor (carkit.studio), as the WebP the showroom
    lays under it. Its size and centre are printed: they go in the vehicle data
    (assets.studioShadow). Run on the merged exterior."""
    from carkit import studio
    png = os.path.normpath(os.path.join(os.path.dirname(DEST_SHADOW), "..", "..", "blender",
                                        "renders", "zeekr-7x-shadow.png"))
    os.makedirs(os.path.dirname(png), exist_ok=True)
    info = studio.ground_shadow(png, exterior_meshes(), hide=interior_objects())
    studio.to_webp(png, DEST_SHADOW)
    print("studioShadow:", info)
    return info


def stills(shots=("hero", "side", "front", "rear34"), samples=256, res=(1920, 1080), out_dir=None):
    """Cycles stills of the car in the web's studio (carkit.rig), the reference the web
    view is checked against (docs/3d-pipeline.md, studio stills). Fresh build, exterior
    only, as the web ships it:

        blender -b --factory-startup --python-expr "import sys;
            sys.path.append(r'<repo>/blender/scripts'); import export_zx; export_zx.stills()"

    Written to blender/renders/studio/zeekr-7x_<shot>.png (gitignored)."""
    sys.modules.pop("build_zx", None)
    import build_zx
    from carkit import rig, studio
    build_zx.main(reset=True, scene=False)
    prepare_exterior()
    open_all(False)
    rig.drop_lookdev()
    png = os.path.join(rig.RENDER_DIR, "zeekr-7x-shadow.png")
    os.makedirs(rig.RENDER_DIR, exist_ok=True)
    info = studio.ground_shadow(png, exterior_meshes())
    rig.build_studio(shadow=(png, info["size"], info["centre"]))
    d = out_dir or rig.RENDER_DIR
    return [rig.still(s, os.path.join(d, "zeekr-7x_%s.png" % s), dims=DIMS, res=res, samples=samples)
            for s in shots]


def clean_degenerate(objs, dist=1e-7, area=1e-12):
    """Dissolve collapsed geometry (the grid builders leave zero-area faces where a
    strip pinches to a point): the glTF exporter calls such a mesh "not valid"."""
    import bmesh
    n = 0
    for o in objs:
        if o.type != 'MESH':
            continue
        _X.bake_modifiers(o)             # the triangulation too: that is what the exporter checks
        bm = bmesh.new()
        bm.from_mesh(o.data)
        before = len(bm.faces)
        bmesh.ops.dissolve_degenerate(bm, dist=dist, edges=bm.edges[:])
        bad = [f for f in bm.faces if f.calc_area() < area]
        if bad:
            bmesh.ops.delete(bm, geom=bad, context='FACES')
        n += before - len(bm.faces)
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()
        # whatever else the exporter would call invalid is repaired here, and named in the log
        print("validate %s:" % o.name, o.data.validate(verbose=True))
    print("degenerate faces removed:", n)
    return n


def main(draco=True, ao=True, ao_samples=512, shadow=True):
    """The exterior (the scene must hold a fresh build_zx.main())."""
    prepare_exterior()
    open_all(False)           # every part at its hinge, as the closed car
    if ao:
        bake_exterior_ao(ao_samples)
    split_wheels()            # one node per corner, after the per-design AO bake
    groups = exterior_groups()
    merged = _X.merge_for_export(groups)
    clean_degenerate(merged)
    if shadow:
        bake_ground_shadow()
    return _X.export(DEST, groups, "Zeekr7X_Body", draco=draco, attributes=ao)


def web(draco=True, ao_samples=512):
    """Fresh build -> merged exterior GLB."""
    import time
    t = time.time()
    sys.modules.pop("build_zx", None)
    import build_zx
    out = build_zx.main(reset=True, scene=False)
    build_wheel_options(out["lib"])
    print("build tris:", out["tris"], "%.0f s" % (time.time() - t))
    res = main(draco=draco, ao_samples=ao_samples)
    print("export_zx.web: %.0f s" % (time.time() - t))
    return res


# ------------------------------------------------------------------ cabin
DEST_INTERIOR = os.path.join(MODELS, "zeekr-7x-interior.glb")
DEST_PROBE = os.path.join(MODELS, "zeekr-7x-cabin.hdr")
DEST_OUTSIDE = os.path.join(MODELS, "zeekr-7x-outside.jpg")
DEST_OUTSIDE_LIGHT = os.path.join(MODELS, "zeekr-7x-outside-light.hdr")

# The world the car stands in and the cabin looks out on: the Shanghai riverside (Poly Haven
# "Shanghai Riverside", CC0), as the SU7's - the sun measured off it is the SU7's
# (xiaomi-su7-ultra.ts: exteriorTurnDeg 147.6, sun 20.4 deg up, #ffdfae, 1.96).
OUTSIDE = dict(
    path=os.path.join(_HERE, "..", "textures", "hdri", "shanghai_riverside_4k.hdr"),
    strength=1.0, rotation=153.6, clamp=8.0)
WEB_EXPOSURE = 0.92          # the viewer's toneMappingExposure
RIG_FILL = 0.8               # the cabin rig as a fill under the daylight (0.5 left the dash's face under its visor dim)
# The cream cabin is lit by what the HDRI sends through the glass, a fraction of a uniform
# white studio's light (the photographs' cream reads ~210 sRGB): the baked light is stored
# times this and the viewer, which divides by the fixed carkit.bake.STORE_SCALE, shows it
# that much brighter. Tuned against the photographs in the web viewer.
CABIN_GAIN = 1.0
PROTECTED = {"screen_main", "int_door_L", "int_door_R", "int_rdoor_L", "int_rdoor_R",
             # the hatch's liner swings with it
             "int_tailgate",
             # the X-ray tab takes the headliner away
             "int_headliner",
             # the rear pillar trims, whose ragged rear edges show from the open boot
             "int_cpillar", "int_cpillar_flange", "int_qtr_lower"}
INTERIOR_GROUPS = [("Zeekr7X_Cabin", "ZX_Interior")]
# between the front seats at head height
PROBE_AT = (0.10, 0.0, 1.15)
PROBE_LIGHT_MIX = 0.3


def cabin_lighting():
    """The OUTSIDE world, the cabin rig at RIG_FILL, the generated cluster on its display,
    and the blackout layer and lookdev floor hidden so daylight comes in through the glass.
    Wrap bakes in carkit.bake.thin_glass()."""
    import zx_interior as ZI
    from carkit import scene as SC
    from carkit.qa import hmi_capture as HC
    SC.hdri_world(**OUTSIDE)
    col = bpy.data.collections.get("ZX_Interior")
    for o in (col.objects if col else ()):
        if o.type == 'LIGHT':
            base = o.data.get("base_energy", o.data.energy)
            o.data["base_energy"] = base
            o.data.energy = base * RIG_FILL
    ob = bpy.data.objects.get("screen_cluster")
    if ob is not None and not ob.get("plain_material"):
        HC.apply(ob, ZI.cluster_image(), 1.2)
    hidden = []
    for n in BLACKOUT + ("Zeekr7X_Blackout", "Ground"):
        ob = bpy.data.objects.get(n)
        if ob and not ob.hide_render:
            ob.hide_render = True
            hidden.append(ob)
    return hidden


def bake_cabin(samples=256, probe_samples=384, probe=True):
    """Vertex lighting on every cabin mesh + the reflection probe (probe=False keeps the one
    on disk, for a rebuild that only touched the cabin's geometry)."""
    from carkit import bake as BK
    col = bpy.data.collections["ZX_Interior"]
    hidden = cabin_lighting()
    # a mesh without faces stops the bake ("No faces found in the object ..."): drop and name them
    for o in [o for o in col.objects if o.type == 'MESH' and not len(o.data.polygons)]:
        print("cabin: removed empty mesh", o.name)
        bpy.data.objects.remove(o, do_unlink=True)
    import time
    t = time.time()
    try:
        with BK.thin_glass():
            objs = BK.prepare(col)
            print("  cabin bake: prepared %d meshes, %.0f s" % (len(objs), time.time() - t))
            stats = BK.vertex_lighting(objs, samples=samples, scale=BK.STORE_SCALE * CABIN_GAIN)
            print("  cabin bake: vertex light, %.0f s" % (time.time() - t))
            BK.smooth(objs)
            BK.to_generic(objs)
            if probe:
                lights = [o for o in col.objects if o.type == 'LIGHT' and o.visible_glossy]
                BK.probe_mix(PROBE_AT, DEST_PROBE, lights, mix=PROBE_LIGHT_MIX, samples=probe_samples)
                print("  cabin bake: probe, %.0f s" % (time.time() - t))
    finally:
        for ob in hidden:
            ob.hide_render = False
    return stats


def join_doors(collection="ZX_Interior"):
    """Each door card's parts (front and rear) -> one object, origin on the hinge
    (zx_openings)."""
    import zx_openings as OP
    OP.join_cards(collection)


def join_headliner(collection="ZX_Interior"):
    """The headliner's pieces -> one object, so the X-ray tab can take it away."""
    col = bpy.data.collections[collection]
    names = [o.name for o in col.objects if o.type == 'MESH' and o.name.startswith("int_headliner")
             and o.name != "int_headliner"]
    return _X.join("int_headliner", names) if names else None


def bake_cabin_open(samples=256):
    """The same vertex lighting with every door and the tailgate open: the second set of light
    the viewer blends in as a part swings open (the cabin is lit by the doorways, the boot by
    the sky). Needs prepare_exterior() first, so the parts are split and hinged."""
    from carkit import bake as BK
    import zx_openings as OP
    import zx_gate as RG
    col = bpy.data.collections["ZX_Interior"]
    OP.join_cards()
    for key, d in OP.DOORS.items():
        OP.set_angle(key, d["deg"])
    RG.set_hatch(RG.OPEN_DEG)
    hidden = cabin_lighting()
    try:
        with BK.thin_glass():
            objs = BK.prepare(col, attr=BK.ATTR_OPEN)
            stats = BK.vertex_lighting(objs, samples=samples, attr=BK.ATTR_OPEN,
                                       scale=BK.STORE_SCALE * CABIN_GAIN)
            BK.smooth(objs, attr=BK.ATTR_OPEN)
            BK.to_generic(objs, BK.ATTR_OPEN, BK.EXPORT_ATTR_OPEN)
    finally:
        for ob in hidden:
            ob.hide_render = False
        for key in OP.DOORS:
            OP.set_angle(key, 0.0)
        RG.set_hatch(0.0)
    return stats


def export_outside():
    """The view out (JPEG, tone mapped as the viewer does) and its light (HDR)."""
    from carkit import bake as BK
    o = OUTSIDE
    view = BK.backdrop(o["path"], DEST_OUTSIDE, rotation=o["rotation"], strength=o["strength"],
                       exposure=WEB_EXPOSURE)
    light = BK.backdrop_light(o["path"], DEST_OUTSIDE_LIGHT, rotation=o["rotation"],
                              strength=o["strength"], clamp=o["clamp"], width=1024)
    return view, light


def export_interior(draco=True):
    from carkit import build as B
    from carkit.qa import hmi_capture as HC
    col = bpy.data.collections["ZX_Interior"]
    # the app draws the live HMI over screen_main: ship the plain screen
    HC.restore_plain(bpy.data.objects["screen_main"])
    B.ensure_uvs([col], force=tuple(
        m.name for m in bpy.data.materials if m.name.startswith("INT_")
        and m.name != "INT_Screen" and not m.name.startswith("INT_Display")))
    for o in [o for o in col.objects if o.type == 'LIGHT']:
        bpy.data.objects.remove(o, do_unlink=True)
    join_doors()
    join_headliner()
    merged = _X.merge_for_export(INTERIOR_GROUPS, PROTECTED)
    clean_degenerate(merged)
    return _X.export(DEST_INTERIOR, INTERIOR_GROUPS, "Zeekr7X_Cabin", draco=draco, attributes=True)


def web_full(samples=256, probe_samples=384, draco=True, ao_samples=512):
    """Fresh build of body and cabin -> baked cabin -> both GLBs, the probe and the outside
    world. In a background Blender (module docstring), ~10 min."""
    import time
    t = time.time()
    for m in [m for m in sys.modules if m.startswith("zx_") or m == "build_zx"]:
        sys.modules.pop(m, None)
    import build_zx
    out = build_zx.main(reset=True, scene=True)
    build_wheel_options(out["lib"])
    import zx_interior_shell as SH
    SH.main()
    print("build: %d exterior tris, %.0f s" % (out["tris"], time.time() - t))
    # the parts are split (and the materials made export-safe) before BOTH bakes, so the closed
    # and the open set are lit from the same car and a door swinging open does not shift a colour
    prepare_exterior()
    stats = bake_cabin(samples, probe_samples)
    print("bake: %.0f s" % (time.time() - t))
    stats_open = bake_cabin_open(samples)
    print("bake open: %.0f s" % (time.time() - t))
    res = {"bake": stats, "bake_open": stats_open, "interior": export_interior(draco=draco)}
    res["exterior"] = main(draco=draco, ao_samples=ao_samples)
    res["outside"] = export_outside()
    print("web_full: %.0f s" % (time.time() - t))
    return res


def web_cabin(samples=256, draco=True):
    """The cabin alone: fresh build -> baked cabin (closed and open) -> the interior GLB, with
    the exterior, the probe and the outside world left as they are. ~8 min in a background
    Blender; use it after a change that touches only the cabin's own geometry."""
    import time
    t = time.time()
    for m in [m for m in sys.modules if m.startswith("zx_") or m == "build_zx"]:
        sys.modules.pop(m, None)
    import build_zx
    build_zx.main(reset=True, scene=True)
    import zx_interior_shell as SH
    SH.main()
    prepare_exterior()
    stats = bake_cabin(samples, probe=False)
    print("bake: %.0f s" % (time.time() - t))
    stats_open = bake_cabin_open(samples)
    print("bake open: %.0f s" % (time.time() - t))
    res = {"bake": stats, "bake_open": stats_open, "interior": export_interior(draco=draco)}
    print("web_cabin: %.0f s" % (time.time() - t))
    return res


# ------------------------------------------------------------------ HMI art
DEST_HMI = os.path.normpath(os.path.join(MODELS, "..", "hmi", "zeekr-7x"))


def hmi_art(res=(1800, 900), samples=256):
    """The car as a cut-out for the infotainment's home scene and 360 page
    (public/hmi/zeekr-7x/car34.webp, car-top.webp): the studio rig on the car alone, front
    three-quarter, the floor lights it but is not drawn, transparent. Fresh build, exterior only:

        blender -b --factory-startup --python-expr "import sys;
            sys.path.append(r'<repo>/blender/scripts'); import export_zx; export_zx.hmi_art()"
    """
    sys.modules.pop("build_zx", None)
    import build_zx
    from carkit import rig, studio
    build_zx.main(reset=True, scene=False)
    prepare_exterior()
    open_all(False)
    rig.drop_lookdev()
    rig.build_studio()
    # the floor lights the car's lower body but is not in the picture
    bpy.data.objects["StudioFloor"].visible_camera = False
    os.makedirs(rig.RENDER_DIR, exist_ok=True)
    os.makedirs(DEST_HMI, exist_ok=True)
    # the screen's own picture of the car is seen from well round the side (the wheelbase is 52 %
    # of the overall length in c10_0016, an azimuth of ~65 degrees), lower and longer than the
    # studio's "card" shot
    rig.SHOTS["hmi"] = dict(az=62.0, el=6.0, fov=20.0, margin=1.04, lift=0.0)
    png = rig.still("hmi", os.path.join(rig.RENDER_DIR, "zeekr-7x_card.png"), dims=DIMS, res=res,
                    samples=samples, transparent=True)
    out = os.path.join(DEST_HMI, "car34.webp")
    studio.to_webp(png, out, quality=88, trim=True, width=1100)
    top = rig.top_view(os.path.join(rig.RENDER_DIR, "zeekr-7x_top.png"), dims=DIMS, samples=samples)
    studio.to_webp(top, os.path.join(DEST_HMI, "car-top.webp"), quality=88, trim=True, width=420)
    return out


def hmi_side_art(res=(1800, 700), samples=192, az=88.0):
    """The car from the side, for the car screen's Quick settings page (the page draws the car
    side-on with the suspension heights beside it, c10_0033): public/hmi/zeekr-7x/car-side.webp.
    Same rig as hmi_art, one shot. Fresh build, exterior only."""
    sys.modules.pop("build_zx", None)
    import build_zx
    from carkit import rig, studio
    build_zx.main(reset=True, scene=False)
    prepare_exterior()
    open_all(False)
    rig.drop_lookdev()
    rig.build_studio()
    bpy.data.objects["StudioFloor"].visible_camera = False
    os.makedirs(rig.RENDER_DIR, exist_ok=True)
    os.makedirs(DEST_HMI, exist_ok=True)
    rig.SHOTS["hmi_side"] = dict(az=az, el=2.0, fov=16.0, margin=1.04, lift=0.0)
    png = rig.still("hmi_side", os.path.join(rig.RENDER_DIR, "zeekr-7x_side.png"), dims=DIMS, res=res,
                    samples=samples, transparent=True)
    out = os.path.join(DEST_HMI, "car-side.webp")
    studio.to_webp(png, out, quality=88, trim=True, width=1100)
    return out


# the clay drawings' cameras, in the car's axes (x forward, y left, z up): position, aim, lens
# (mm on a 36 mm sensor), render size, and what is out of the picture. The climate page's is a wide
# view from behind the front seats (c10_0027), the seat page's a high view from the driver's side
# with the front of the car at the left (c10_0018).
HMI_CABIN_SHOTS = {
    "climate": dict(pos=(-0.30, 0.0, 1.24), aim=(1.10, 0.0, 0.74), lens=17.0, res=(1800, 585),
                    hide=("seat", "headrest", "pillow", "headliner", "pillar", "roof", "qtr_lower",
                          "parcel", "boot", "tailgate", "int_rdoor", "sill", "visor", "rvmirror")),
    # nearly straight down from above the middle of the cabin, a little to the driver's side so
    # the picture's up is the passenger's side, wide enough to take in the wheel (c10_0018 has
    # the front pair at 0.31 of the width, the rear pair at 0.68, the rows at 0.31 and 0.72)
    "seats": dict(pos=(-0.40, 0.60, 3.70), aim=(-0.40, 0.0, 0.92), lens=30.0, res=(1360, 800),
                  hide=("headliner", "pillar", "roof", "int_door_l", "int_rdoor_l", "qtr_lower",
                        "parcel", "boot", "tailgate", "sill", "visor", "rvmirror", "overhead",
                        "head_speaker", "roofrail", "tweeter")),
}
# the chips on the seat page sit on each seat's backrest: its centre, in the car's axes
HMI_SEAT_POINTS = {"FL": (0.05, 0.37, 0.92), "FR": (0.05, -0.37, 0.92),
                   "RL": (-1.05, 0.39, 0.92), "RR": (-1.05, -0.39, 0.92),
                   "wheel": (0.85, 0.404, 1.0)}
# the cabin's parts without the boot: it reads the exterior's tail cap, and the drawings leave the
# boot out anyway, so the cabin builds in seconds without the car
HMI_CABIN_PARTS = ("dash", "screens", "wheel", "seats", "console", "doors", "shell", "pedals")


def hmi_cabin(samples=160, shots=("climate", "seats"), tones=("light", "dark"), shot_overrides=None):
    """Clay renders of the cabin for the infotainment's climate and seat pages
    (public/hmi/zeekr-7x/cabin-<shot>-<light|dark>.webp): every surface one matte colour under a
    uniform white sky, the centre screen black, on a transparent ground, so the picture is all
    form, as the car's own are. Cabin only, no exterior (half a minute plus the renders):

        blender -b --factory-startup --python-expr "import sys;
            sys.path.append(r'<repo>/blender/scripts'); import export_zx; export_zx.hmi_cabin()"

    Prints HMI_SEATS {shot: {seat: [x, y]}}: where each seat's chips go on the seat drawing, as
    fractions of the picture (zeekros/Seats.tsx SEATS)."""
    import json
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    from carkit import rig, scene as SC, studio
    bpy.ops.wm.read_homefile(use_empty=True)
    import zx_interior_shell as SH
    SH.main(lights=False, parts=list(HMI_CABIN_PARTS))
    scn = bpy.context.scene
    objs = [o for o in bpy.data.collections["ZX_Interior"].all_objects if o.type == 'MESH']

    def flat(name, rgb, rough=0.9):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        b.inputs["Base Color"].default_value = rgb + (1.0,)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = 0.0
        return m, b

    clay, clay_bsdf = flat("M_Clay", (0.8, 0.8, 0.8))
    black, _ = flat("M_ScreenBlack", (0.004, 0.004, 0.005), 0.25)
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(black if o.name.startswith("screen_") else clay)

    w = bpy.data.worlds.new("W_Clay")
    scn.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    os.makedirs(rig.RENDER_DIR, exist_ok=True)
    os.makedirs(DEST_HMI, exist_ok=True)
    out, seats = [], {}
    for name in shots:
        shot = dict(HMI_CABIN_SHOTS[name], **(shot_overrides or {}).get(name, {}))
        for o in objs:
            n = o.name.lower()
            hidden = any(k in n for k in shot["hide"])
            # anything wholly above the seats: the header trims, the visors, the mirror
            if not hidden and name == "climate":
                hidden = min((o.matrix_world @ Vector(c)).z for c in o.bound_box) > 1.22
            o.hide_render = hidden
        cd = bpy.data.cameras.new("CAM_" + name)
        cd.lens = shot["lens"]
        cd.clip_start = 0.02
        cam = bpy.data.objects.new("CAM_" + name, cd)
        scn.collection.objects.link(cam)
        cam.location = Vector(shot["pos"])
        cam.rotation_euler = (Vector(shot["aim"]) - Vector(shot["pos"])).to_track_quat('-Z', 'Y').to_euler()
        scn.camera = cam
        scn.render.resolution_x, scn.render.resolution_y = shot["res"]
        scn.render.resolution_percentage = 100
        bpy.context.view_layer.update()
        if name == "seats":
            seats[name] = {}
            for k, pt in HMI_SEAT_POINTS.items():
                c = world_to_camera_view(scn, cam, Vector(pt))
                seats[name][k] = [round(c.x, 4), round(1.0 - c.y, 4)]
        for tone, albedo, sky in (("light", 0.80, 1.05), ("dark", 0.040, 2.4)):
            if tone not in tones:
                continue
            clay_bsdf.inputs["Base Color"].default_value = (albedo, albedo, albedo * 1.02, 1.0)
            bg.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
            bg.inputs["Strength"].default_value = sky
            SC.use_cycles(samples)
            scn.view_settings.view_transform = 'Standard'
            # the sky lights the cabin but is not in the picture: the page behind it shows
            scn.render.film_transparent = True
            scn.render.image_settings.file_format = 'PNG'
            scn.render.image_settings.color_mode = 'RGBA'
            png = os.path.join(rig.RENDER_DIR, "zeekr-7x_cabin_%s_%s.png" % (name, tone))
            scn.render.filepath = png
            bpy.ops.render.render(write_still=True)
            webp = os.path.join(DEST_HMI, "cabin-%s-%s.webp" % (name, tone))
            studio.to_webp(png, webp, quality=80, width=shot["res"][0])
            out.append(webp)
        bpy.data.objects.remove(cam, do_unlink=True)
    print("HMI_SEATS", json.dumps(seats))
    return out


if __name__ == "__main__":
    web()
