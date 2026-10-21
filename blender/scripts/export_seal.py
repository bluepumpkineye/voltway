"""Merge the BYD Seal 07 EV build for the draw-call budget and export it to the web app.

    byd-seal.glb              exterior, ~300k tris, Draco
    byd-seal-shadow.webp      ground shadow on the studio floor

Nodes:
    BYDSeal_Body        the painted shell, glass, lamp surrounds
    BYDSeal_Details     fascia, lamps, trim, mirrors, badges, lettering, roof LiDAR
    BYDSeal_Wheels      the four wheels (18-inch 5-petal aero alloy); split into FL/FR/RL/RR
    BYDSeal_Blackout    inner shadow shell and greenhouse underlay
    BYDSeal_Door_<corner>, BYDSeal_DoorFrame_<corner>, BYDSeal_Bonnet, BYDSeal_Tailgate
                        the hinged parts, each a node with its origin on its hinge (seal_openings,
                        seal_bays, seal_gate)
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
DEST = os.path.join(MODELS, "byd-seal.glb")
DEST_SHADOW = os.path.join(MODELS, "byd-seal-shadow.webp")

BLACKOUT = ("Seal_Shell_Shadow", "Seal_Greenhouse_Black", "Seal_Roof_Rear_Black", "Seal_Cowl_Black")
AO_DISTANCE = 1.0
DIMS = (4.800, 1.875, 1.460)

GROUPS = [
    ("BYDSeal_Body", "Seal_Body"),
    ("BYDSeal_Wheels", "Seal_Wheels"),
    ("BYDSeal_Details", "Seal_Details"),
    ("BYDSeal_Blackout", "Seal_Blackout"),
]
WHEEL_GROUPS = []

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


def wheel_corner_groups():
    out = []
    for node, cname in [GROUPS[1]] + WHEEL_GROUPS:
        for tag in CORNERS:
            out.append(("%s_%s" % (node, tag), _corner_col(cname, "W", tag)))
            out.append(("%s_Caliper_%s" % (node, tag), _corner_col(cname, "C", tag)))
    return out


def split_blackout():
    col = bpy.data.collections.get("Seal_Blackout") or bpy.data.collections.new("Seal_Blackout")
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


def prepare_exterior():
    """Everything the exterior needs before it is merged and exported."""
    if bpy.data.objects.get("Seal_Tailgate_Node") is not None:
        return
    import seal_materials as MB
    MB.export_safe()
    split_blackout()
    check_transmission()
    import seal_openings as OP
    import seal_bays as BY
    import seal_gate as RG
    BY.build_frunk()
    BY.split_bonnet()
    BY.open_hull()
    OP.cut_underlay()
    RG.build_seal()
    OP.split_trim()
    OP.split_doors()
    OP.open_hull()
    RG.split_tail()
    RG.open_hull()


def open_all(on=True):
    """Every door, the bonnet and the lid swung open (or shut again)."""
    import seal_openings as OP
    import seal_bays as BY
    import seal_gate as RG
    for key, d in OP.DOORS.items():
        OP.set_angle(key, d["deg"] if on else 0.0, card=False)
    BY.set_bonnet(BY.HOOD_DEG if on else 0.0)
    RG.set_hatch(RG.OPEN_DEG if on else 0.0, card=False)


def exterior_groups():
    import seal_openings as OP
    import seal_bays as BY
    import seal_gate as RG
    if wheels_split():
        core = [g for g in GROUPS if g != GROUPS[1]]
        return core + wheel_corner_groups() + OP.door_groups() + BY.bonnet_groups() + [RG.GROUP]
    return GROUPS + OP.door_groups() + BY.bonnet_groups() + [RG.GROUP]


def exterior_meshes():
    return [o for _, cname in exterior_groups() for o in
            (bpy.data.collections[cname].objects if cname in bpy.data.collections else ())
            if o.type == 'MESH']


def bake_ground_shadow():
    from carkit import studio
    png = os.path.normpath(os.path.join(os.path.dirname(DEST_SHADOW), "..", "..", "blender",
                                        "renders", "byd-seal-shadow.png"))
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


def main(draco=True, shadow=True):
    prepare_exterior()
    open_all(False)
    split_wheels()
    groups = exterior_groups()
    merged = _X.merge_for_export(groups)
    clean_degenerate(merged)
    shadow_info = None
    if shadow:
        try:
            shadow_info = bake_ground_shadow()
        except Exception as e:
            print("Shadow notice:", e)
    res = _X.export(DEST, groups, "BYDSeal_Body", draco=draco, attributes=False)
    print("Exported to:", DEST)
    return res, shadow_info


def web(draco=True):
    t = time.time()
    sys.modules.pop("build_seal", None)
    import build_seal
    out = build_seal.main(reset=True, scene=False)
    print("build tris:", out["tris"], "%.0f s" % (time.time() - t))
    res = main(draco=draco)
    print("export_seal.web: %.0f s" % (time.time() - t))
    return res


# ------------------------------------------------------------------ cabin
def web_cabin(samples=256, probe_samples=384, draco=True, probe=True, outside=True, look="baked"):
    """The BYD Seal's cabin export entry point."""
    t = time.time()
    for m in [m for m in sys.modules if m.startswith("seal_") or m in ("build_seal", "cabin_tools", "cabin_parts")]:
        sys.modules.pop(m, None)
    import build_seal
    import seal_cabin as C
    import cabin_tools as CT
    build_seal.main(reset=True, scene=True)
    import seal_interior_shell as SH
    SH.main()
    print("build: %.0f s" % (time.time() - t))
    prepare_exterior()
    if look == "hall":
        CT.cabin_screens(C.CFG)
        res = {"interior": CT.export_interior(C.CFG, draco=draco, look="hall")}
        if outside:
            res["outside"] = CT.export_outside(C.CFG)
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
