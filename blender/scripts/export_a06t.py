"""Export pipeline for the Avatr 06T web app assets.

    avatr-06t.glb               exterior, ~360k tris, Draco
    avatr-06t-interior.glb      the cabin (a06t_interior), Cycles light baked per vertex
    avatr-06t-cabin.hdr         the cabin reflection probe
    avatr-06t-outside.jpg/.hdr  outside world backdrop
    avatr-06t-shadow.webp       ground contact shadow
    public/hmi/avatr-06t/*.webp HMI artwork cut-outs and clay renders

Run in background Blender:

    blender -b --factory-startup --python-expr
        "import sys; sys.path.append(r'<repo>/blender/scripts');
         import export_a06t; export_a06t.web()"          # exterior only

    ... export_a06t.web_full()                         # body + cabin, baked
    ... export_a06t.hmi_art()                          # HMI car34 and car-top
    ... export_a06t.hmi_cabin()                        # HMI cabin clay shots
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.append(_HERE)

from carkit import export as _X

MODELS = os.path.normpath(os.path.join(_HERE, "..", "..", "public", "models"))
DEST = os.path.join(MODELS, "avatr-06t.glb")
DEST_INTERIOR = os.path.join(MODELS, "avatr-06t-interior.glb")
DEST_PROBE = os.path.join(MODELS, "avatr-06t-cabin.hdr")
DEST_OUTSIDE = os.path.join(MODELS, "avatr-06t-outside.jpg")
DEST_OUTSIDE_LIGHT = os.path.join(MODELS, "avatr-06t-outside-light.hdr")
DEST_SHADOW = os.path.join(MODELS, "avatr-06t-shadow.webp")
HMI_DIR = os.path.normpath(os.path.join(_HERE, "..", "..", "public", "hmi", "avatr-06t"))

OUTSIDE = dict(
    path=os.path.join(_HERE, "..", "textures", "hdri", "zhengyang_gate_4k.hdr"),
    strength=1.0, rotation=189.0, clamp=8.0)
WEB_EXPOSURE = 0.92
RIG_FILL = 0.5

PROTECTED = {"screen_main", "screen_cluster", "screen_mirror_L", "screen_mirror_R",
             "int_door_L", "int_door_R", "int_rdoor_L", "int_rdoor_R",
             "int_tailgate", "int_parcel_shelf", "int_rear_sill",
             "int_headliner", "int_cpillar", "int_cpillar_flange", "int_qtr_lower"}
INTERIOR_GROUPS = [("Avatr06T_Cabin", "A06T_Interior")]
PROBE_AT = (-0.40, 0.0, 1.15)
PROBE_LIGHT_MIX = 0.3

BLACKOUT = ("A06T_Shell_Shadow", "A06T_Greenhouse_Black", "A06T_Roof_Rear_Black", "A06T_Glass_RearBack")
AO_DISTANCE = 1.0
BONNET_DEG = 62.0
DIMS = (4.940, 1.960, 1.455)

GROUPS = [
    ("Avatr06T_Body", "A06T_Body"),
    ("Avatr06T_Wheels", "A06T_Wheels"),
    ("Avatr06T_Details", "A06T_Details"),
    ("Avatr06T_Blackout", "A06T_Blackout"),
]
WHEEL_GROUPS = [
    ("Avatr06T_Aero_Wheels", "A06T_Wheels_Aero"),
    ("Avatr06T_Cyclone_Wheels", "A06T_Wheels_Cyclone"),
    ("Avatr06T_Multi_Wheels", "A06T_Wheels_Multi"),
]

CORNERS = ("FL", "FR", "RL", "RR")


def build_wheel_options(lib):
    """The other wheel designs (a06t_wheels), one collection each."""
    if not WHEEL_GROUPS or bpy.data.collections.get(WHEEL_GROUPS[0][1]) is not None:
        return
    import a06t_surface as S
    import a06t_wheels as AW
    from carkit import build as B
    cols = []
    for (_, cname), name in zip(WHEEL_GROUPS, [n for n in AW.DESIGNS if n != AW.DEFAULT]):
        col = B.fresh_collection(cname)
        AW.build_design(col, S, lib, name)
        cols.append(col)
    B.ensure_uvs(cols)


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
    col = bpy.data.collections.get("A06T_Blackout") or bpy.data.collections.new("A06T_Blackout")
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for n in BLACKOUT:
        ob = bpy.data.objects.get(n)
        if ob is None:
            continue
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        col.objects.link(ob)
    return col


def check_transmission():
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
    if bpy.data.objects.get("A06T_Tailgate") is not None:
        return
    from carkit import materials as MB
    MB.export_safe()
    split_blackout()
    check_transmission()
    import a06t_openings as OP
    import a06t_bays as BY
    import a06t_gate as RG
    BY.build_frunk()
    BY.split_bonnet()
    BY.open_hull()
    OP.build_sill()
    OP.cut_underlay()
    RG.cut_underlay()
    RG.build_seal()
    OP.split_doors()
    OP.open_hull()
    RG.split_tail()
    RG.open_hull()
    RG.split_greenhouse()


def exterior_groups(options=True):
    import a06t_openings as OP
    import a06t_bays as BY
    import a06t_gate as RG
    if wheels_split():
        core = [g for g in GROUPS if g != GROUPS[1]]
        return (core + wheel_corner_groups(options) + OP.door_groups() + BY.bonnet_groups()
                + [RG.GROUP, RG.GREENHOUSE_GROUP])
    return (GROUPS + OP.door_groups() + BY.bonnet_groups() + [RG.GROUP, RG.GREENHOUSE_GROUP])


def open_all(on=True):
    import a06t_openings as OP
    import a06t_bays as BY
    import a06t_gate as RG
    for key, d in OP.DOORS.items():
        OP.set_angle(key, d["deg"] if on else 0.0)
    BY.set_bonnet(BONNET_DEG if on else 0.0)
    RG.set_hatch(RG.OPEN_DEG if on else 0.0)


def bake_exterior_ao(samples=512):
    from carkit import bake as BK
    prepare_exterior()

    def meshes(groups):
        return [o for _, cname in groups for o in
                (bpy.data.collections[cname].objects if cname in bpy.data.collections else ())
                if o.type == 'MESH']

    objs = meshes(exterior_groups(options=False))
    extra = [(cname, meshes([(n, cname)])) for n, cname in WHEEL_GROUPS if cname in bpy.data.collections]
    hide = [o for cname in ("A06T_Interior",)
            for o in (bpy.data.collections[cname].all_objects if cname in bpy.data.collections else ())]
    ground = bpy.data.objects.get("Ground")
    if ground is not None:
        hide.append(ground)
    open_all(True)
    try:
        stats = BK.ambient_occlusion(objs, samples=samples, distance=AO_DISTANCE,
                                     hide=hide + [o for _, ms in extra for o in ms])
        own = meshes([GROUPS[1]])
        for cname, ms in extra:
            gone = own + [o for c, other in extra if c != cname for o in other]
            BK.ambient_occlusion(ms, samples=samples, distance=AO_DISTANCE, hide=hide + gone)
        return stats
    finally:
        open_all(False)


def bake_ground_shadow(samples=192):
    from carkit import studio
    car = []
    for _, cname in exterior_groups():
        col = bpy.data.collections.get(cname)
        if col is not None:
            car.extend([o for o in col.objects if o.type == 'MESH'])
    os.makedirs(os.path.dirname(DEST_SHADOW), exist_ok=True)
    png = os.path.splitext(DEST_SHADOW)[0] + ".png"
    info = studio.ground_shadow(png, car, samples=samples)
    studio.to_webp(png, DEST_SHADOW, quality=85)
    return info


def main(draco=True, ao=True, ao_samples=512, shadow=True):
    prepare_exterior()
    open_all(False)
    if ao:
        bake_exterior_ao(ao_samples)
    split_wheels()
    groups = exterior_groups()
    _X.merge_for_export(groups)
    if shadow:
        bake_ground_shadow()
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    return _X.export(DEST, groups, "Avatr06T_Body", draco=draco, attributes=ao)


def web(draco=True):
    sys.modules.pop("build_a06t", None)
    import build_a06t
    out = build_a06t.main(reset=True, scene=False)
    print("build tris:", out["tris"])
    return main(draco=draco, ao=False, shadow=True)


def exterior(draco=True, ao=True, ao_samples=256):
    for m in [m for m in sys.modules if m.startswith("a06t_") or m == "build_a06t"]:
        sys.modules.pop(m, None)
    import build_a06t
    out = build_a06t.main(reset=True, scene=False)
    build_wheel_options(out["lib"])
    print("build tris:", out["tris"])
    res = {}
    res["exterior"] = main(draco=draco, ao=ao, ao_samples=ao_samples, shadow=True)
    res["outside"] = export_outside()
    return res


def hmi_art(res=(1800, 900), samples=160):
    """Infotainment car cut-out cards: car34.webp and car-top.webp."""
    sys.modules.pop("build_a06t", None)
    import build_a06t
    from carkit import rig, studio
    build_a06t.main(reset=True, scene=False)
    prepare_exterior()
    open_all(False)
    rig.drop_lookdev()
    rig.build_studio()
    bpy.data.objects["StudioFloor"].visible_camera = False
    os.makedirs(rig.RENDER_DIR, exist_ok=True)
    os.makedirs(HMI_DIR, exist_ok=True)
    png = rig.still("card", os.path.join(rig.RENDER_DIR, "a06t_card.png"), dims=DIMS, res=res,
                    samples=samples, transparent=True)
    out = os.path.join(HMI_DIR, "car34.webp")
    studio.to_webp(png, out, quality=88, trim=True, width=1100)
    top = rig.top_view(os.path.join(rig.RENDER_DIR, "a06t_top.png"), dims=DIMS, samples=samples)
    studio.to_webp(top, os.path.join(HMI_DIR, "car-top.webp"), quality=88, trim=True, width=420)
    print("HMI art exported:", out)
    return out


def hmi_cabin(res=(1500, 940), samples=120, shots=("climate", "seats")):
    """Clay renders of the cabin for climate and seat pages."""
    from carkit import rig, scene as SC, studio
    bpy.ops.wm.read_homefile(use_empty=True)
    import a06t_interior as RI
    RI.main(lights=False)
    scn = bpy.context.scene
    objs = [o for o in bpy.data.collections["A06T_Interior"].all_objects if o.type == 'MESH']

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

    CAMS = {
        "climate": ((-1.05, 0.0, 1.52), (1.10, 0.0, 0.70), 17.0),
        "seats": ((-1.45, -0.55, 1.78), (0.25, 0.22, 0.52), 19.0),
    }
    for o in objs:
        n = o.name.lower()
        if any(k in n for k in ("headliner", "pillar", "roof", "int_door_r", "int_rdoor_r", "qtr_lower", "parcel")):
            o.hide_render = True
        elif min((o.matrix_world @ Vector(c)).z for c in o.bound_box) > 1.22:
            o.hide_render = True
    out = []
    os.makedirs(HMI_DIR, exist_ok=True)
    for tone, albedo, sky in (("light", 0.80, 1.05), ("dark", 0.040, 2.4)):
        clay_bsdf.inputs["Base Color"].default_value = (albedo, albedo, albedo * 1.02, 1.0)
        bg.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
        bg.inputs["Strength"].default_value = sky
        for name in shots:
            pos, aim, lens = CAMS[name]
            cd = bpy.data.cameras.new("CAM_" + name)
            cd.lens = lens
            cd.clip_start = 0.02
            cam = bpy.data.objects.new("CAM_" + name, cd)
            scn.collection.objects.link(cam)
            cam.location = Vector(pos)
            cam.rotation_euler = (Vector(aim) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
            scn.camera = cam
            scn.render.resolution_x, scn.render.resolution_y = res
            scn.render.resolution_percentage = 100
            SC.use_cycles(samples)
            scn.view_settings.view_transform = 'Standard'
            scn.render.film_transparent = True
            scn.render.image_settings.file_format = 'PNG'
            scn.render.image_settings.color_mode = 'RGBA'
            png = os.path.join(rig.RENDER_DIR, "a06t_cabin_%s_%s.png" % (name, tone))
            os.makedirs(rig.RENDER_DIR, exist_ok=True)
            scn.render.filepath = png
            bpy.ops.render.render(write_still=True)
            webp = os.path.join(HMI_DIR, "cabin-%s-%s.webp" % (name, tone))
            studio.to_webp(png, webp, quality=80, width=res[0])
            out.append(webp)
            bpy.data.objects.remove(cam, do_unlink=True)
    print("HMI cabin exported:", out)
    return out


def cabin_lighting():
    import a06t_interior as RI
    from carkit import scene as SC
    from carkit.qa import hmi_capture as HC
    SC.hdri_world(**OUTSIDE)
    col = bpy.data.collections.get("A06T_Interior")
    for o in (col.objects if col else ()):
        if o.type == 'LIGHT':
            base = o.data.get("base_energy", o.data.energy)
            o.data["base_energy"] = base
            o.data.energy = base * RIG_FILL
    ob = bpy.data.objects.get("screen_cluster")
    if ob is not None and not ob.get("plain_material"):
        HC.apply(ob, RI.cluster_image(), 1.2)
    hidden = []
    for n in BLACKOUT + ("Avatr06T_Blackout", "Ground"):
        ob = bpy.data.objects.get(n)
        if ob and not ob.hide_render:
            ob.hide_render = True
            hidden.append(ob)
    return hidden


def join_doors(collection="A06T_Interior"):
    import a06t_openings as OP
    OP.join_cards(collection)


def bake_cabin(samples=160, probe_samples=256):
    from carkit import bake as BK
    col = bpy.data.collections["A06T_Interior"]
    hidden = cabin_lighting()
    try:
        with BK.thin_glass():
            objs = BK.prepare(col)
            stats = BK.vertex_lighting(objs, samples=samples)
            BK.smooth(objs)
            BK.to_generic(objs)
            lights = [o for o in col.objects if o.type == 'LIGHT' and o.visible_glossy]
            os.makedirs(os.path.dirname(DEST_PROBE), exist_ok=True)
            BK.probe_mix(PROBE_AT, DEST_PROBE, lights, mix=PROBE_LIGHT_MIX,
                         samples=probe_samples)
    finally:
        for ob in hidden:
            ob.hide_render = False
    return stats


def bake_cabin_open(samples=160):
    from carkit import bake as BK
    import a06t_openings as OP
    import a06t_gate as RG
    col = bpy.data.collections["A06T_Interior"]
    OP.join_cards()
    for key, d in OP.DOORS.items():
        OP.set_angle(key, d["deg"])
    RG.set_hatch(RG.OPEN_DEG)
    hidden = cabin_lighting()
    try:
        with BK.thin_glass():
            objs = BK.prepare(col, attr=BK.ATTR_OPEN)
            stats = BK.vertex_lighting(objs, samples=samples, attr=BK.ATTR_OPEN)
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
    from carkit import bake as BK
    o = OUTSIDE
    os.makedirs(os.path.dirname(DEST_OUTSIDE), exist_ok=True)
    view = BK.backdrop(o["path"], DEST_OUTSIDE, rotation=o["rotation"],
                       strength=o["strength"], exposure=WEB_EXPOSURE)
    light = BK.backdrop_light(o["path"], DEST_OUTSIDE_LIGHT, rotation=o["rotation"],
                              strength=o["strength"], clamp=o["clamp"], width=1024)
    return view, light


def export_interior(draco=True):
    from carkit import build as B
    from carkit.qa import hmi_capture as HC
    col = bpy.data.collections["A06T_Interior"]
    HC.restore_plain(bpy.data.objects["screen_main"])
    B.ensure_uvs([col], force=tuple(
        m.name for m in bpy.data.materials if m.name.startswith("INT_")
        and m.name != "INT_Screen" and not m.name.startswith("INT_Display")))
    for o in [o for o in col.objects if o.type == 'LIGHT']:
        bpy.data.objects.remove(o, do_unlink=True)
    join_doors()
    _X.merge_for_export(INTERIOR_GROUPS, PROTECTED)
    os.makedirs(os.path.dirname(DEST_INTERIOR), exist_ok=True)
    return _X.export(DEST_INTERIOR, INTERIOR_GROUPS, "Avatr06T_Cabin", draco=draco,
                     attributes=True)


def web_full(samples=160, probe_samples=256, draco=True):
    """Full pipeline export for Avatr 06T."""
    import time
    t = time.time()
    for m in [m for m in sys.modules if m.startswith("a06t_") or m == "build_a06t"]:
        sys.modules.pop(m, None)
    import build_a06t
    out = build_a06t.main(reset=True, scene=True)
    build_wheel_options(out["lib"])
    import a06t_interior as RI
    RI.main()
    import a06t_gate as RG
    RG.build_boot()
    RG.build_boot_details()
    RG.build_liner()
    print("build: %d exterior tris, %.0f s" % (out["tris"], time.time() - t))
    stats = bake_cabin(samples, probe_samples)
    print("bake: %.0f s" % (time.time() - t))
    prepare_exterior()
    stats_open = bake_cabin_open(samples)
    print("bake open: %.0f s" % (time.time() - t))
    res = {"bake": stats, "bake_open": stats_open, "interior": export_interior(draco=draco)}
    res["exterior"] = main(draco=draco, ao=True, shadow=True)
    res["outside"] = export_outside()
    print("web_full completed in %.0f s" % (time.time() - t))
    return res


if __name__ == "__main__":
    web()
