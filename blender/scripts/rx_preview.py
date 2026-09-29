"""Fast surface preview of the Luxeed RX for camera-matched overlays.

A full build takes minutes; while the profile curves are being fitted to
the photographs all that matters is the skin, the wheels and a few layout
lines. This builds the CarBody as one closed skin (the shadow shell with no
inset), simple tyres and rims, and overlays them through every registered
camera.

    import rx_preview as P
    P.check("v01")      # rebuild the preview and write every overlay
"""
import math
import sys

import bpy

MODS = ("rx_surface", "rx_nose", "rx_ref_match")


def _reload():
    for m in MODS:
        sys.modules.pop(m, None)
    for name in [m for m in sys.modules if m == "carkit" or m.startswith("carkit.")]:
        sys.modules.pop(name, None)


def build(reload=True):
    if reload:
        _reload()
    from carkit import build as B
    from carkit import mesh as M
    from carkit.body import panels as BP
    import rx_surface as S
    import rx_nose as N

    col = B.fresh_collection("RX_Preview")
    lib = {"shadow": _mat("M_Prev_Skin", (0.6, 0.6, 0.62)),
           "tyre": _mat("M_Prev_Tyre", (0.02, 0.02, 0.02))}
    skin = BP.shadow_shell(N.BODY, col, lib, "RX_Skin", nx=120, nv=60,
                           shrink=1.0, inset=0.0, end_offset=0.0, end_w=1.0,
                           mat="shadow")
    made = [skin]
    # the shell's own end caps stop at the crowns; these run to the centreline
    for cap in (N.NOSE, N.TAIL):
        old = bpy.data.objects.get("RX_Skin" + ("_F" if cap.front else "_R"))
        if old:
            bpy.data.objects.remove(old)
        rows, _ = BP.cap_rows(cap, cap.Z_LO + 0.002, cap.Z_HI - 0.002, 0.0, 1.0, 30, 30,
                           top_to_centre=True)
        c = M.mesh_from_rows("RX_Cap" + ("F" if cap.front else "R"), rows, col)
        c.data.materials.append(lib["shadow"])
        M.mirror_y(c)
        made.append(c)
    corners = (("FL", S.FRONT_AXLE, 1, 0.381, 0.255, 0.855),
               ("FR", S.FRONT_AXLE, -1, 0.381, 0.255, 0.855),
               ("RL", S.REAR_AXLE, 1, 0.390, 0.275, 0.860),
               ("RR", S.REAR_AXLE, -1, 0.390, 0.275, 0.860))
    import bmesh
    from mathutils import Matrix
    for tag, ax, sgn, r, wdt, yc in corners:
        z = r - 0.012                     # loaded
        me = bpy.data.meshes.new("RX_Tyre_" + tag)
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=r, radius2=r,
                              depth=wdt,
                              matrix=Matrix.Translation((ax, sgn * yc, z))
                              @ Matrix.Rotation(math.pi / 2, 4, 'X'))
        bm.to_mesh(me)
        bm.free()
        t = bpy.data.objects.new(me.name, me)
        col.objects.link(t)
        t.data.materials.append(lib["tyre"])
        made.append(t)
    print("preview: %d objects, dims %s" % (len(made), N.BODY.dims_report()))
    return made


def _mat(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = rgb + (1.0,)
    return m


def show(on):
    """Include / exclude the preview collection. Keep it EXCLUDED otherwise:
    left in the view layer it renders through every gap in the real panels
    (it was the 'grey A-pillar' in the first close-ups)."""
    lc = bpy.context.view_layer.layer_collection.children.get("RX_Preview")
    if lc:
        lc.exclude = not on


def check(tag, cams=None):
    build()
    import rx_ref_match as RM
    scn = bpy.context.scene
    try:
        scn.render.engine = 'CYCLES'
    except TypeError:
        pass
    out = []
    for name in (cams or list(RM.CAMERAS)):
        out.append(RM.overlay(name, tag, hide=("Glass",)))
    return out
