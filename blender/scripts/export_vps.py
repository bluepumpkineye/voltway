"""Export pipeline for the Voyah Passion S (岚图追光S) web app assets.

    voyah-passion-s.glb               exterior, Draco + vertex AO
    voyah-passion-s-interior.glb      cabin + boot + door cards + 2048 AO atlas (hall look)
    voyah-passion-s-outside.jpg/.hdr  outside world backdrop & light
    voyah-passion-s-shadow.webp       ground contact shadow
    public/hmi/voyah-passion-s/*.webp HMI artwork cut-outs and clay cabin renders

Run in background Blender:
    blender -b --factory-startup --python-expr "import sys; sys.path.append(r'<repo>/blender/scripts'); import export_vps; export_vps.export_all()"
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
DEST = os.path.join(MODELS, "voyah-passion-s.glb")
DEST_INTERIOR = os.path.join(MODELS, "voyah-passion-s-interior.glb")
DEST_PROBE = os.path.join(MODELS, "voyah-passion-s-cabin.hdr")
DEST_OUTSIDE = os.path.join(MODELS, "voyah-passion-s-outside.jpg")
DEST_OUTSIDE_LIGHT = os.path.join(MODELS, "voyah-passion-s-outside-light.hdr")
DEST_SHADOW = os.path.join(MODELS, "voyah-passion-s-shadow.webp")
HMI_DIR = os.path.normpath(os.path.join(_HERE, "..", "..", "public", "hmi", "voyah-passion-s"))

OUTSIDE = dict(
    path=os.path.join(_HERE, "..", "textures", "hdri", "zhengyang_gate_4k.hdr"),
    strength=1.0, rotation=189.0, clamp=8.0)
WEB_EXPOSURE = 0.92
RIG_FILL = 0.5

PROTECTED = {
    "screen_main", "screen_cluster", "screen_passenger",
    "int_door_L", "int_door_R", "int_rdoor_L", "int_rdoor_R",
    "int_tailgate", "int_parcel_shelf", "int_rear_sill",
    "int_headliner", "int_cpillar", "int_cpillar_flange", "int_qtr_lower",
}
INTERIOR_GROUPS = [("VoyahPassionS_Cabin", "VPS_Interior")]
PROBE_AT = (-0.42, 0.0, 1.24)
PROBE_LIGHT_MIX = 0.3

BLACKOUT = (
    "VPS_Shell_Shadow", "VPS_Shell_Shadow_R",
    "VPS_Greenhouse_Black", "VPS_Roof_Rear_Black", "VPS_Glass_RearBack",
)
AO_DISTANCE = 1.0
BONNET_DEG = 62.0
DIMS = (5.050, 1.998, 1.636)

GROUPS = [
    ("VoyahPassionS_Body", "VPS_Body"),
    ("VoyahPassionS_Feichi_Wheels", "VPS_Wheels"),
    ("VoyahPassionS_Details", "VPS_Details"),
    ("VoyahPassionS_Blackout", "VPS_Blackout"),
]
WHEEL_GROUPS = [
    ("VoyahPassionS_Starlight_Wheels", "VPS_Wheels_Starlight"),
]

CORNERS = ("FL", "FR", "RL", "RR")


def build_wheel_options(lib):
    if not WHEEL_GROUPS or bpy.data.collections.get(WHEEL_GROUPS[0][1]) is not None:
        return
    import vps_surface as S
    import vps_wheels as VW
    from carkit import build as B
    cols = []
    for (_, cname), name in zip(WHEEL_GROUPS, [n for n in VW.DESIGNS if n != VW.DEFAULT]):
        col = B.fresh_collection(cname)
        VW.build_design(col, S, lib, name)
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
    col = bpy.data.collections.get("VPS_Blackout") or bpy.data.collections.new("VPS_Blackout")
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
    if bpy.data.objects.get("VPS_Tailgate") is not None:
        return
    from carkit import materials as MB
    MB.export_safe()
    split_blackout()
    check_transmission()
    import vps_openings as OP
    import vps_bays as BY
    import vps_gate as RG
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
    import vps_openings as OP
    import vps_bays as BY
    import vps_gate as RG
    if wheels_split():
        core = [g for g in GROUPS if g != GROUPS[1]]
        return (core + wheel_corner_groups(options) + OP.door_groups() + BY.bonnet_groups()
                + [RG.GROUP, RG.GREENHOUSE_GROUP])
    return (GROUPS + OP.door_groups() + BY.bonnet_groups() + [RG.GROUP, RG.GREENHOUSE_GROUP])


def open_all(on=True):
    import vps_openings as OP
    import vps_bays as BY
    import vps_gate as RG
    for key, d in OP.DOORS.items():
        OP.set_angle(key, d["deg"] if on else 0.0)
    BY.set_bonnet(BONNET_DEG if on else 0.0)
    RG.set_hatch(RG.OPEN_DEG if on else 0.0)


def bake_exterior_ao(samples=256):
    from carkit import bake as BK
    prepare_exterior()

    def meshes(groups):
        return [o for _, cname in groups for o in
                (bpy.data.collections[cname].objects if cname in bpy.data.collections else ())
                if o.type == 'MESH']

    objs = meshes(exterior_groups(options=False))
    extra = [(cname, meshes([(n, cname)])) for n, cname in WHEEL_GROUPS if cname in bpy.data.collections]
    hide = [o for cname in ("VPS_Interior",)
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
    for _, cname in exterior_groups(options=False):
        col = bpy.data.collections.get(cname)
        if col is not None:
            car.extend([o for o in col.objects if o.type == 'MESH'])
    os.makedirs(os.path.dirname(DEST_SHADOW), exist_ok=True)
    png = os.path.splitext(DEST_SHADOW)[0] + ".png"
    info = studio.ground_shadow(png, car, samples=samples)
    studio.to_webp(png, DEST_SHADOW, quality=85)
    print("SHADOW INFO:", info)
    return info


def main(draco=True, ao=True, ao_samples=256, shadow=True):
    prepare_exterior()
    open_all(False)
    if ao:
        bake_exterior_ao(ao_samples)
    split_wheels()
    groups = exterior_groups()
    _X.merge_for_export(groups)
    sh_info = None
    if shadow:
        sh_info = bake_ground_shadow()
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    res = _X.export(DEST, groups, "VoyahPassionS_Body", draco=draco, attributes=ao)
    return {"export": res, "shadow": sh_info}


def web(draco=True):
    sys.modules.pop("build_vps", None)
    import build_vps
    out = build_vps.main(reset=True, scene=False)
    build_wheel_options(out["lib"])
    print("build tris:", out["tris"])
    return main(draco=draco, ao=False, shadow=True)


def exterior(draco=True, ao=True, ao_samples=256):
    for m in [m for m in sys.modules if m.startswith("vps_") or m == "build_vps"]:
        sys.modules.pop(m, None)
    import build_vps
    out = build_vps.main(reset=True, scene=False)
    build_wheel_options(out["lib"])
    print("build tris:", out["tris"])
    res = {}
    res["exterior"] = main(draco=draco, ao=ao, ao_samples=ao_samples, shadow=True)
    res["outside"] = export_outside()
    return res


def hmi_art(res=(1800, 900), samples=128):
    sys.modules.pop("build_vps", None)
    import build_vps
    from carkit import rig, studio
    build_vps.main(reset=True, scene=False)
    prepare_exterior()
    open_all(False)
    rig.drop_lookdev()
    rig.build_studio()
    bpy.data.objects["StudioFloor"].visible_camera = False
    os.makedirs(rig.RENDER_DIR, exist_ok=True)
    os.makedirs(HMI_DIR, exist_ok=True)
    png = rig.still("card", os.path.join(rig.RENDER_DIR, "vps_card.png"), dims=DIMS, res=res,
                    samples=samples, transparent=True)
    out = os.path.join(HMI_DIR, "car34.webp")
    studio.to_webp(png, out, quality=88, trim=True, width=1100)
    top = rig.top_view(os.path.join(rig.RENDER_DIR, "vps_top.png"), dims=DIMS, samples=samples)
    studio.to_webp(top, os.path.join(HMI_DIR, "car-top.webp"), quality=88, trim=True, width=420)
    print("HMI art exported:", out)
    return out


def hmi_cabin(res=(1500, 940), samples=96, shots=("climate", "seats")):
    from carkit import rig, scene as SC, studio
    bpy.ops.wm.read_homefile(use_empty=True)
    import vps_interior as RI
    RI.main(lights=False)
    scn = bpy.context.scene
    objs = [o for o in bpy.data.collections["VPS_Interior"].all_objects if o.type == 'MESH']

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
        "climate": ((-1.05, 0.0, 1.56), (1.10, 0.0, 0.74), 17.0),
        "seats": ((-1.45, -0.55, 1.82), (0.25, 0.22, 0.56), 19.0),
    }
    for o in objs:
        n = o.name.lower()
        if any(k in n for k in ("headliner", "pillar", "roof", "int_door_r", "int_rdoor_r", "qtr_lower", "parcel")):
            o.hide_render = True
        elif min((o.matrix_world @ Vector(c)).z for c in o.bound_box) > 1.28:
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
            png = os.path.join(rig.RENDER_DIR, "vps_cabin_%s_%s.png" % (name, tone))
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
    import vps_interior as RI
    from carkit import scene as SC
    from carkit.qa import hmi_capture as HC
    SC.hdri_world(**OUTSIDE)
    col = bpy.data.collections.get("VPS_Interior")
    for o in (col.objects if col else ()):
        if o.type == 'LIGHT':
            base = o.data.get("base_energy", o.data.energy)
            o.data["base_energy"] = base
            o.data.energy = base * RIG_FILL
    ob = bpy.data.objects.get("screen_cluster")
    if ob is not None and not ob.get("plain_material"):
        HC.apply(ob, RI.cluster_image(), 1.2)
    hidden = []
    for n in BLACKOUT + ("VoyahPassionS_Blackout", "Ground"):
        ob = bpy.data.objects.get(n)
        if ob and not ob.hide_render:
            ob.hide_render = True
            hidden.append(ob)
    return hidden


def join_doors(collection="VPS_Interior"):
    import vps_openings as OP
    OP.join_cards(collection)


def export_outside():
    from carkit import bake as BK
    o = OUTSIDE
    os.makedirs(os.path.dirname(DEST_OUTSIDE), exist_ok=True)
    view = BK.backdrop(o["path"], DEST_OUTSIDE, rotation=o["rotation"],
                       strength=o["strength"], exposure=WEB_EXPOSURE)
    light = BK.backdrop_light(o["path"], DEST_OUTSIDE_LIGHT, rotation=o["rotation"],
                              strength=o["strength"], clamp=o["clamp"], width=1024)
    return view, light


def cabin_screens():
    import vps_interior as RI
    from carkit.qa import hmi_capture as HC
    ob = bpy.data.objects.get("screen_cluster")
    if ob is not None and not ob.get("plain_material"):
        HC.apply(ob, RI.cluster_image(), 1.2)


def atlas_cabin(samples=384):
    from carkit import aoatlas as AA
    return AA.atlas_for("VPS_Interior", samples=samples)


def export_interior(draco=True, look="hall"):
    from carkit import build as B
    from carkit.qa import hmi_capture as HC
    col = bpy.data.collections["VPS_Interior"]
    HC.restore_plain(bpy.data.objects["screen_main"])
    B.ensure_uvs([col], force=tuple(
        m.name for m in bpy.data.materials if m.name.startswith("INT_")
        and m.name != "INT_Screen" and not m.name.startswith("INT_Display")))
    for o in [o for o in col.objects if o.type == 'LIGHT']:
        bpy.data.objects.remove(o, do_unlink=True)
    join_doors()
    _X.merge_for_export(INTERIOR_GROUPS, PROTECTED)
    if look == "hall":
        atlas_cabin()
    os.makedirs(os.path.dirname(DEST_INTERIOR), exist_ok=True)
    return _X.export(DEST_INTERIOR, INTERIOR_GROUPS, "VoyahPassionS_Cabin", draco=draco,
                     attributes=True, image_format='WEBP' if look == "hall" else 'AUTO')


def web_cabin(draco=True, look="hall"):
    import time
    t = time.time()
    for m in [m for m in sys.modules if m.startswith("vps_") or m == "build_vps"]:
        sys.modules.pop(m, None)
    import build_vps
    build_vps.main(reset=True, scene=True)
    import vps_interior as RI
    RI.main()
    import vps_gate as RG
    RG.build_boot()
    RG.build_boot_details()
    RG.build_liner()
    prepare_exterior()
    cabin_screens()
    res = {"interior": export_interior(draco=draco, look=look)}
    print("web_cabin (%s): %.0f s" % (look, time.time() - t))
    return res


def export_all():
    """Export exterior GLB + shadow + outside HDR/JPG + hall-lit interior GLB + HMI art & clay renders."""
    res = {}
    res["exterior"] = exterior(draco=True, ao=True, ao_samples=256)
    res["cabin"] = web_cabin(draco=True, look="hall")
    res["hmi_art"] = hmi_art()
    res["hmi_cabin"] = hmi_cabin()
    print("EXPORT_ALL COMPLETE!")
    return res


if __name__ == "__main__":
    web()
