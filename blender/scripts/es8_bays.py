"""Nio ES8 bays: the 230L electric front trunk (frunk) under the clamshell bonnet
(blender/reference/nio-es8/official/space_frunk.jpg).
"""
import math

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from carkit.bay import (smooth, inset_poly, radial, finish as _finish, prism as _prism,
                        rrect as _rrect, disc as _disc, is_cw as _cw)

# (2026-10-30: the cowl moved back to 1.20 and the nose in by the squeeze es8_surface.fx; the frunk follows)
HOOD_HALF = [(1.20, 0.805), (1.60, 0.835), (1.95, 0.840), (2.169, 0.815), (2.246, 0.770),
             (2.323, 0.550)]
HOOD_HINGE = (1.215, 1.213)
HOOD_DEG = 62.0
APRON_DROP = 0.060
TUB_DEPTH = 0.245     # Nio ES8 230L ultra-wide deep frunk tub
TUB = [(1.360, 0.0), (1.360, 0.360), (1.380, 0.440), (1.435, 0.485), (1.620, 0.495),
       (1.850, 0.485), (2.000, 0.455), (2.070, 0.395), (2.110, 0.295), (2.130, 0.150),
       (2.130, 0.0)]
WALL = [(0.0, 0.0), (0.004, -0.008), (0.010, -0.022), (0.018, -0.075), (0.026, -0.155),
        (0.036, -0.220), (0.052, -0.245)]


def hood_half(x):
    if x <= HOOD_HALF[0][0]:
        return HOOD_HALF[0][1]
    for (x0, y0), (x1, y1) in zip(HOOD_HALF, HOOD_HALF[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return 0.0


class Hood:
    def __init__(self):
        dg = bpy.context.evaluated_depsgraph_get()
        ob = bpy.data.objects.get("ES8_Hood") or bpy.data.objects["ES8_Bonnet"]
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        mw = ob.matrix_world.copy()
        self.tree = BVHTree.FromPolygons([mw @ v.co for v in me.vertices],
                                         [list(p.vertices) for p in me.polygons])
        ev.to_mesh_clear()

    def z(self, x, y):
        h = self.tree.ray_cast(Vector((x, y, 2.0)), Vector((0.0, 0.0, -1.0)), 3.0)[0]
        return h.z if h is not None else None

    def zc(self, x, y):
        sgn = 1.0 if y >= 0 else -1.0
        for dy in (0.0, 0.03, 0.06, 0.10, 0.20, 0.40):
            v = self.z(x, y - sgn * min(abs(y), dy))
            if v is not None:
                return v
        return self.z(x, 0.0) or 1.05


def rim_outline(inset=0.040, n=64):
    x0, x1 = 1.240, 2.200
    xs = [x0 + (x1 - x0) * k / n for k in range(n + 1)]
    right = [(x, -max(0.05, hood_half(x) - inset)) for x in xs]
    h = max(0.05, hood_half(x1) - inset)
    arc = [(x1 + 0.060 * math.sqrt(max(0.0, 1.0 - (y / h) ** 2)), y)
           for y in [-h + 2.0 * h * k / 14 for k in range(1, 14)]]
    left = [(x, max(0.05, hood_half(x) - inset)) for x in reversed(xs)]
    return right + arc + left


def tub_outline(n=10):
    left = smooth([(x, y) for (x, y) in TUB], n)
    right = [(x, -y) for (x, y) in reversed(left)]
    return left + right[1:-1]


def _mat(name):
    return bpy.data.materials[name]


def _plastic():
    from carkit import materials as MB
    m = bpy.data.materials.get("M_Frunk_Plastic")
    if m is None:
        m, nt, b = MB.mat("M_Frunk_Plastic")
        MB.set_inputs(b, base=(0.058, 0.059, 0.064), metallic=0.0, roughness=0.72, specular=0.35)
    return m


def _cap_material():
    from carkit import materials as MB
    m = bpy.data.materials.get("M_Cap_Blue")
    if m is None:
        m, nt, b = MB.mat("M_Cap_Blue")
        MB.set_inputs(b, base=(0.020, 0.075, 0.42), metallic=0.0, roughness=0.42, specular=0.45)
    return m


def build_frunk(collection="ES8_Details"):
    from carkit.interior.sweep import grid_mesh, tube, ellipse
    col = bpy.data.collections[collection]
    hood = Hood()
    satin, shadow = _plastic(), _mat("M_Shadow")
    rubber = _mat("M_Cladding")
    gloss = _mat("M_Black_Gloss")

    def zA(x, y):
        return hood.zc(x, y) - APRON_DROP

    def zF(x, y=0.0):
        return hood.zc(x, 0.0) - APRON_DROP - TUB_DEPTH

    made = []
    rim = rim_outline(inset=0.040)
    tub = tub_outline()
    if _cw(rim) != _cw(tub):
        tub = tub[::-1]
    ctr = (1.84, 0.0)
    ro, so = radial(rim, ctr), radial(tub, ctr)
    bm = bmesh.new()
    vo = [bm.verts.new((x, y, zA(x, y))) for (x, y) in ro]
    vi = [bm.verts.new((x, y, zA(x, y))) for (x, y) in so]
    for i in range(len(vo)):
        j = (i + 1) % len(vo)
        bm.faces.new((vo[i], vo[j], vi[j], vi[i]))
    made.append(_finish(bm, "ES8_Frunk_Tray", col, satin))
    made.append(tube("ES8_Frunk_HoodSeal", [(x, y, zA(x, y) + 0.009) for (x, y) in ro],
                     ellipse(0.0150, 0.0110, 8), col, rubber, closed=True, lateral=(0.0, 0.0, 1.0)))
    rings = []
    for (d, e) in WALL:
        poly = inset_poly(tub, d)
        rings.append([(x, y, zA(sx, sy) + e) for (x, y), (sx, sy) in zip(poly, tub)])
    made.append(grid_mesh("ES8_Frunk_Tub", rings, col, satin, wrap_t=True))
    bm = bmesh.new()
    floor = [bm.verts.new(p) for p in rings[-1]]
    bm.faces.new(floor)
    made.append(_finish(bm, "ES8_Frunk_Floor", col, satin, smooth_shade=False))
    made.append(tube("ES8_Frunk_TubSeal", [(x, y, zA(x, y) + 0.004) for (x, y) in tub],
                     ellipse(0.0070, 0.0060, 8), col, rubber, closed=True, lateral=(0.0, 0.0, 1.0)))
    cx, cy = 1.550, -0.585
    made.append(_disc("ES8_Frunk_CapWell", cx, cy, 0.036, zA, 0.012, col, shadow))
    made.append(_disc("ES8_Frunk_Cap", cx, cy, 0.026, zA, 0.040, col, _cap_material(), lift=0.016))
    for k, sy in enumerate((-1, 1)):
        made.append(_prism("ES8_Frunk_Pocket%d" % k, _rrect(2.04, sy * 0.610, 0.100, 0.130, 0.040),
                           zA, 0.006, col, shadow, 0.0030))
        made.append(_prism("ES8_Frunk_Slot%d" % k, _rrect(2.05, sy * 0.610, 0.030, 0.012, 0.010),
                           zA, 0.020, col, gloss, 0.0045))
    for k, (x, y) in enumerate(((1.30, -0.710), (1.30, 0.710), (1.98, -0.745), (1.98, 0.745))):
        made.append(_disc("ES8_Frunk_Stop%d" % k, x, y, 0.018, zA, 0.010, col, shadow))
    made += _build_cowl(col, hood, zA, satin, rubber, shadow)
    return made


def _build_cowl(col, hood, zA, satin, rubber, shadow):
    from carkit.interior.sweep import grid_mesh, tube, ellipse
    made = []
    hw = 0.765
    rows = []
    for i in range(7):
        t = i / 6.0
        x = 1.312 + 0.046 * t
        z = 1.115 + (zA(1.358, 0.0) - 1.115) * (t ** 1.3)
        rows.append([(x, -hw + 2 * hw * j / 36.0, z) for j in range(37)])
    well = grid_mesh("ES8_Frunk_Cowl", rows, col, satin)
    from carkit import mesh as M
    M.orient(well.data, lambda c: (1.0, 0.0, 1.0))
    made.append(well)
    for k in range(7):
        x = 1.324 + 0.006 * k
        z = 1.115 + (zA(1.358, 0.0) - 1.115) * (((x - 1.312) / 0.046) ** 1.3) + 0.0035
        made.append(tube("ES8_Frunk_Rib%d" % k, [(x, -0.62 + 1.24 * j / 12.0, z) for j in range(13)],
                         ellipse(0.0022, 0.0022, 6), col, shadow, lateral=(1.0, 0.0, 0.0)))
    made.append(tube("ES8_Frunk_CowlSeal", [(1.364, -hw + 2 * hw * j / 36.0, zA(1.364, 0.0) + 0.006)
                                            for j in range(37)],
                     ellipse(0.0100, 0.0080, 8), col, rubber, lateral=(1.0, 0.0, 0.0)))
    for nm, y0, y1, yp in (("L", 0.640, 0.210, 0.660), ("R", 0.090, -0.580, -0.610)):
        z = 1.122
        made.append(tube("ES8_Wiper_Blade" + nm, [(1.292, y0 + (y1 - y0) * j / 8.0, z) for j in range(9)],
                         [(a * 0.0035, b * 0.011) for (a, b) in ellipse(1, 1, 8)], col, satin,
                         lateral=(1.0, 0.0, 0.0)))
        made.append(tube("ES8_Wiper_Arm" + nm, [(1.288, y1 + (y0 - y1) * 0.18 + 0.0 * j, z + 0.006)
                                                for j in range(2)] + [(1.290, yp, z + 0.004)],
                         ellipse(0.0050, 0.0050, 6), col, satin, lateral=(1.0, 0.0, 0.0)))
    return made


def build_hood_liner(col, inset=0.150):
    from carkit.interior.sweep import grid_mesh
    hood = Hood()
    xa, xb = 1.290, 2.170
    xm, hl = 0.5 * (xa + xb), 0.5 * (xb - xa)
    rows = []
    for i in range(29):
        x = xa + (xb - xa) * i / 28.0
        t = (x - xm) / hl
        end = max(0.0, 1.0 - abs(t) ** 6) ** (1.0 / 6.0)
        h = max(0.04, (hood_half(x) - inset) * end)
        rows.append([(x, -h + 2 * h * j / 26.0,
                      hood.zc(x, -h + 2 * h * j / 26.0) - 0.0128) for j in range(27)])
    return grid_mesh("ES8_HoodLiner", rows, col, _mat("M_Black_Satin"))


def bonnet_hinge():
    return Vector((HOOD_HINGE[0], 0.0, HOOD_HINGE[1]))


def split_bonnet():
    from carkit import export as X
    col = bpy.data.collections.get("ES8_BonnetGrp") or bpy.data.collections.new("ES8_BonnetGrp")
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    liner = build_hood_liner(col)
    hood = bpy.data.objects["ES8_Hood"]
    for c in list(hood.users_collection):
        c.objects.unlink(hood)
    col.objects.link(hood)
    bonnet = X.join("ES8_Bonnet", [hood.name, liner.name])
    h = bonnet_hinge()
    bonnet.data.transform(Matrix.Translation(-h))
    bonnet.matrix_world = Matrix.Translation(h)
    bonnet["hinge"] = tuple(h)
    return bonnet


def bonnet_groups():
    return [("NioES8_Bonnet", "ES8_BonnetGrp")]


def set_bonnet(deg):
    ob = bpy.data.objects.get("ES8_Bonnet")
    if ob is not None:
        h = bonnet_hinge()
        ob.matrix_world = Matrix.Translation(h) @ Matrix.Rotation(-math.radians(deg), 4, 'Y')


def open_hull(hull="ES8_Shell_Shadow"):
    from carkit import cut as C
    ob = bpy.data.objects[hull]
    sheet = C.sheet_bvh(ob)
    cutter = C.prism_dir("_bay", [(x, y, 1.35) for (x, y) in rim_outline(inset=0.050)],
                         (0.0, 0.0, 1.0), back=0.65, front=0.0)
    before, after = C.difference(ob, [cutter], "bay_")
    removed = C.prune_off_sheet(ob, sheet)
    return before, after, removed
