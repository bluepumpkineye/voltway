"""Merge the XPeng G9L build for the draw-call budget and export it to the web app.

    xpeng-g9l.glb              exterior, ~300k tris, Draco
    xpeng-g9l-shadow.webp      ground shadow on the studio floor

Nodes:
    XpengG9L_Body        the painted shell, glass, lamp surrounds
    XpengG9L_Details     fascia, lamps, trim, mirrors, badges, lettering
    XpengG9L_Wheels_<corner>, XpengG9L_Wheels_Caliper_<corner>     the 22-inch Aero five-spoke, one node per corner
    XpengG9L_Turbine_Wheels_<corner> (and _Caliper_)               the 21-inch turbine option, the same
    XpengG9L_Blackout    inner shadow shell and greenhouse underlay
    XpengG9L_Door_<corner>, XpengG9L_DoorFrame_<corner>, XpengG9L_Bonnet, XpengG9L_Tailgate
                         the hinged parts, each a node with its origin on its hinge (g9l_openings,
                         g9l_bays, g9l_gate)
"""
import os
import sys
import time
import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

from carkit import export as _X

MODELS = os.path.normpath(os.path.join(_HERE, "..", "..", "public", "models"))
DEST = os.path.join(MODELS, "xpeng-g9l.glb")
DEST_SHADOW = os.path.join(MODELS, "xpeng-g9l-shadow.webp")

BLACKOUT = ("G9L_Shell_Shadow", "G9L_Greenhouse_Black", "G9L_Roof_Rear_Black", "G9L_Cowl_Black")
AO_DISTANCE = 1.0
DIMS = (5.120, 1.999, 1.782)

GROUPS = [
    ("XpengG9L_Body", "G9L_Body"),
    ("XpengG9L_Wheels", "G9L_Wheels"),
    ("XpengG9L_Details", "G9L_Details"),
    ("XpengG9L_Blackout", "G9L_Blackout"),
]
# the other wheel design (g9l_wheels.DESIGNS): built beside the default for the export only, a node of its own per corner; the
# viewer shows one design at a time (configurator.wheels)
WHEEL_GROUPS = [
    ("XpengG9L_Turbine_Wheels", "G9L_Wheels_Turbine"),
]

CORNERS = ("FL", "FR", "RL", "RR")


def _corner_col(cname, kind, tag):
    return "%s_%s_%s" % (cname, kind, tag)


def wheels_split():
    return bpy.data.collections.get(_corner_col(GROUPS[1][1], "W", "FL")) is not None


def split_wheels():
    if wheels_split():
        return
    for _, cname in [GROUPS[1]] + WHEEL_GROUPS:
        src = bpy.data.collections.get(cname)
        if src is None:
            continue
        for ob in list(src.objects):
            if ob.type != 'MESH':
                continue
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
    out = []
    for node, cname in [GROUPS[1]] + (WHEEL_GROUPS if options else []):
        for tag in CORNERS:
            out.append(("%s_%s" % (node, tag), _corner_col(cname, "W", tag)))
            out.append(("%s_Caliper_%s" % (node, tag), _corner_col(cname, "C", tag)))
    return out


def split_blackout():
    col = bpy.data.collections.get("G9L_Blackout") or bpy.data.collections.new("G9L_Blackout")
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for n in BLACKOUT:
        ob = bpy.data.objects.get(n)
        if ob is None:
            print("warning: blackout object %s missing" % n)
            continue
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        col.objects.link(ob)
    return col


def check_transmission():
    for _, cname in GROUPS:
        col = bpy.data.collections.get(cname)
        for o in (col.objects if col else ()):
            for m in (o.data.materials if o.type == 'MESH' else ()):
                if m is None or not m.use_nodes:
                    continue
                b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                t = b.inputs.get("Transmission Weight") if b else None
                if t is not None and (t.is_linked or t.default_value > 0.0):
                    t.default_value = 0.0


def build_wheel_options(lib):
    """The other wheel design (g9l_wheels), one collection, on the car's own material library - before prepare_exterior():
    rebuilding the library after it would undo export_safe()."""
    if bpy.data.collections.get(WHEEL_GROUPS[0][1]) is not None:
        return
    import g9l_surface as S
    import g9l_wheels as ZW
    from carkit import build as B
    cols = []
    for (_, cname), name in zip(WHEEL_GROUPS, [n for n in ZW.DESIGNS if n != ZW.DEFAULT]):
        col = B.fresh_collection(cname)
        ZW.build_design(col, S, lib, name)
        cols.append(col)
    B.ensure_uvs(cols)
    return cols


def prepare_exterior():
    """Everything the exterior needs before it is merged and exported: the blackout layer split off,
    the windows cut out of its underlay and the doors made hinged nodes with the hull opened behind
    them, the tailgate with its seal. Once per build (G9L_Tailgate_Node marks it done); the cabin's open-state
    bake wants the parts split, so web_cabin() calls it before that bake. The cabin's hatch liner must be
    built first (it reads the backlight's outline)."""
    if bpy.data.objects.get("G9L_Tailgate_Node") is not None:
        return
    import g9l_materials as MB
    MB.export_safe()
    split_blackout()
    check_transmission()
    import g9l_openings as OP
    import g9l_bays as BY
    import g9l_gate as RG
    BY.build_frunk()          # the bay under the bonnet, then the bonnet as a hinged node
    BY.split_bonnet()
    BY.open_hull()
    OP.cut_underlay()         # the door windows out of the black underlay: it must not stay behind
    RG.cut_underlay()         # the backlight's underlay goes with the hatch
    RG.build_seal()           # a black bead behind the hatch's shut line
    OP.split_doors()          # a hinged node per door (the cabin's cards: join_cards)
    OP.open_hull()            # the hull behind them, so the cabin shows when one is open
    RG.split_tail()           # the hatch: backlight, spoiler, lamp bar's middle, gate, lettering - one node
    RG.open_hull()            # the hull behind it


def open_all(on=True):
    """Every door, the bonnet and the hatch swung open (or shut again)."""
    import g9l_openings as OP
    import g9l_bays as BY
    import g9l_gate as RG
    for key, d in OP.DOORS.items():
        OP.set_angle(key, d["deg"] if on else 0.0, card=False)
    BY.set_bonnet(BY.HOOD_DEG if on else 0.0)
    RG.set_hatch(RG.OPEN_DEG if on else 0.0, card=False)


def exterior_groups(options=True):
    """Every exterior group; options=False leaves out the extra wheel design."""
    import g9l_openings as OP
    import g9l_bays as BY
    import g9l_gate as RG
    if wheels_split():
        core = [g for g in GROUPS if g != GROUPS[1]]
        return core + wheel_corner_groups(options) + OP.door_groups() + BY.bonnet_groups() + [RG.GROUP]
    return GROUPS + OP.door_groups() + BY.bonnet_groups() + [RG.GROUP] + (WHEEL_GROUPS if options else [])


def exterior_meshes(options=False):
    """The car's meshes; the extra wheel design stands where the default wheels do, so the car's shadow leaves it out."""
    return [o for _, cname in exterior_groups(options) for o in
            (bpy.data.collections[cname].objects if cname in bpy.data.collections else ())
            if o.type == 'MESH']


def bake_ground_shadow():
    from carkit import studio
    png = os.path.normpath(os.path.join(os.path.dirname(DEST_SHADOW), "..", "..", "blender",
                                        "renders", "xpeng-g9l-shadow.png"))
    os.makedirs(os.path.dirname(png), exist_ok=True)
    os.makedirs(os.path.dirname(DEST_SHADOW), exist_ok=True)
    info = studio.ground_shadow(png, exterior_meshes())
    studio.to_webp(png, DEST_SHADOW)
    print("studioShadow:", info)
    return info


def clean_degenerate(objs, dist=1e-7, area=1e-12):
    import bmesh
    n = 0
    for o in objs:
        if o.type != 'MESH':
            continue
        _X.bake_modifiers(o)
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
    print("degenerate faces removed:", n)
    return n


def fix_rim_normals(objs, angle_deg=60.0):
    """Keep a panel's thickness out of its outer surface's normals.

    Every paint panel is Solidify'd, and its rim (the wall at each cut edge) shares vertices with the outer face. The WeightedNormal
    pass that follows has no sharp edges to respect, so at a cut edge it averaged the rim's sideways normals into the outer surface's:
    a band a vertex wide along the G9L's smile edge, the chin line and the openings whose normals were tilted ~7 degrees from the
    surface's own, which a clearcoat showed as stair steps in every reflection (c1_0026's nose, 2026-10-26). Here the edges between
    faces more than `angle_deg` apart are marked sharp and the normals are made again, around them. Returns the number of edges marked."""
    import bmesh
    import math
    total = 0
    lim = math.radians(angle_deg)
    for o in objs:
        if o.type != 'MESH' or not len(o.data.polygons):
            continue
        me = o.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.normal_update()
        n = 0
        for e in bm.edges:
            if len(e.link_faces) == 2 and e.smooth:
                if e.link_faces[0].normal.angle(e.link_faces[1].normal, 0.0) > lim:
                    e.smooth = False
                    n += 1
        bm.to_mesh(me)
        bm.free()
        me.update()
        total += n
        bpy.context.view_layer.objects.active = o
        for ob in bpy.context.view_layer.objects:
            ob.select_set(ob == o)
        try:
            with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
                bpy.ops.mesh.customdata_custom_splitnormals_clear()
        except Exception as e:                                     # a mesh with no custom normals has nothing to clear
            print("rim normals: %s: %s" % (o.name, str(e).strip()[:80]))
        wn = o.modifiers.new("WN_rim", 'WEIGHTED_NORMAL')
        wn.mode = 'FACE_AREA_WITH_ANGLE'
        wn.weight = 50
        wn.keep_sharp = True
        wn.thresh = 0.01
        _X.bake_modifiers(o)
    return total


def main(draco=True, shadow=True):
    prepare_exterior()
    open_all(False)           # every part at its hinge, as the closed car
    split_wheels()
    groups = exterior_groups()
    merged = _X.merge_for_export(groups)
    clean_degenerate(merged)
    if not os.environ.get("G9L_NO_RIMFIX"):
        paintlike = [o for o in merged if not o.name.startswith(("XpengG9L_Wheels", "XpengG9L_Turbine"))]
        print("rim edges marked sharp:", fix_rim_normals(paintlike))
    # the tail cap and the quarter panels are built apart and meet at the corner (x -2.36) at ~35 degrees: one normal across
    # the seam, or the corner reads as a crease that breaks every reflection
    print("seam normals welded:", _X.weld_normals(merged, ((-2.46, -2.28), (0.55, 1.00), (0.55, 1.40)), only_materials=("M_Paint",)))
    # and the nose: the fascia (Details), the fender (Body) and the bonnet meet round the lamp bar's ends at the cap's join ring, each
    # with the normals of its own faces: the stepped reflections along the corner in the viewer. Paint-bearing parts only (the
    # hull behind them is coarser, and its normals would be averaged in)
    paint = [o for o in merged if o.name in ("XpengG9L_Body", "XpengG9L_Details", "XpengG9L_Bonnet")]
    print("nose seam normals welded:", _X.weld_normals(paint, ((2.0, 2.65), (0.0, 1.06), (0.25, 1.30)), only_materials=("M_Paint",)))
    shadow_info = None
    if shadow:
        try:
            shadow_info = bake_ground_shadow()
        except Exception as e:
            print("Shadow notice:", e)
    res = _X.export(DEST, groups, "XpengG9L_Body", draco=draco, attributes=False, draco_normal_bits=14)
    print("Exported to:", DEST)
    return res, shadow_info


def web(draco=True):
    t = time.time()
    sys.modules.pop("build_g9l", None)
    import build_g9l
    out = build_g9l.main(reset=True, scene=False)
    build_wheel_options(out["lib"])
    print("build tris:", out["tris"], "%.0f s" % (time.time() - t))
    res = main(draco=draco)
    print("export_g9l.web: %.0f s" % (time.time() - t))
    return res


# ------------------------------------------------------------------ cabin
def web_cabin(samples=256, probe_samples=384, draco=True, probe=True, outside=True, look="baked"):
    """The G9L's cabin: fresh build of body and cabin -> two baked light sets (every part shut, then every door
    and the tailgate open) -> public/models/xpeng-g9l-interior.glb, the reflection probe
    (xpeng-g9l-cabin.hdr) and the world seen through the glass. The exterior GLB is left as it is.

    look="hall" (about 4 min): no vertex light, no second (doors open) set, no probe and no outside world; the cabin
    ships with its occlusion atlas and the viewer lights it from public/models/cabin-hall.hdr (probe and outside are
    ignored).
    In a background Blender (never the open session):

        blender -b --factory-startup --python-expr "import sys; sys.path.append(r'<repo>/blender/scripts'); \
            import export_g9l; export_g9l.web_cabin()"
    """
    t = time.time()
    for m in [m for m in sys.modules if m.startswith("g9l_") or m in ("build_g9l", "cabin_tools", "cabin_parts")]:
        sys.modules.pop(m, None)
    import build_g9l
    import g9l_cabin as C
    import cabin_tools as CT
    build_g9l.main(reset=True, scene=True)
    import g9l_interior_shell as SH
    SH.main()
    print("build: %.0f s" % (time.time() - t))
    prepare_exterior()
    if look == "hall":
        CT.cabin_screens(C.CFG)
        res = {"interior": CT.export_interior(C.CFG, draco=draco, look="hall")}
        print("web_cabin (hall): %.0f s" % (time.time() - t))
        return res
    stats = CT.bake_cabin(C.CFG, samples, probe_samples, probe=probe)
    print("bake: %.0f s" % (time.time() - t))
    stats_open = CT.bake_cabin_open(C.CFG, samples)
    print("bake open: %.0f s" % (time.time() - t))
    res = {"bake": stats, "bake_open": stats_open, "interior": CT.export_interior(C.CFG, draco=draco)}
    if outside:
        res["outside"] = CT.export_outside(C.CFG)
    print("web_cabin: %.0f s" % (time.time() - t))
    return res
