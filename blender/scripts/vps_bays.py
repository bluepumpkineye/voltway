"""Voyah Passion S (岚图追光S) front bay (frunk) and hinged bonnet.

Models the satin-black under-bonnet apron, weathersealed storage tub with ribbed
floor mat, service access covers (washer fluid, 12V battery, latch slot), rubber
stops, sound-insulator hood liner, and hinged `VoyahPassionS_Bonnet` node.
"""
import math

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from carkit.bay import (smooth, inset_poly, radial, finish as _finish, prism as _prism,
                        rrect as _rrect, disc as _disc, is_cw as _cw)

HOOD_HALF = [
    (1.040, 0.835), (1.180, 0.818), (1.420, 0.790), (1.680, 0.758),
    (1.900, 0.718), (2.060, 0.665), (2.200, 0.585), (2.300, 0.460),
    (2.350, 0.260), (2.360, 0.000),
]
HOOD_HINGE = (1.075, 1.132)
HOOD_DEG = 62.0
APRON_DROP = 0.052
TUB_DEPTH = 0.255

SEAL = [
    (1.240, 0.000), (1.240, 0.405), (1.260, 0.450), (1.310, 0.465),
    (1.480, 0.462), (1.650, 0.442), (1.750, 0.402), (1.805, 0.325),
    (1.832, 0.195), (1.840, 0.000),
]
WALL = [
    (0.0, 0.0), (0.004, -0.007), (0.010, -0.022), (0.018, -0.075),
    (0.028, -0.168), (0.042, -0.228), (0.062, -0.255),
]


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
        ob = bpy.data.objects["VPS_Hood"] if "VPS_Hood" in bpy.data.objects else \
            bpy.data.objects["VPS_Bonnet"]
        self.tree = BVHTree.FromObject(ob.evaluated_get(dg), dg)

    def z(self, x, y):
        h = self.tree.ray_cast(Vector((x, y, 2.0)), Vector((0.0, 0.0, -1.0)), 3.0)[0]
        return h.z if h is not None else None

    def zc(self, x, y):
        sgn = 1.0 if y >= 0 else -1.0
        for dy in (0.0, 0.03, 0.06, 0.10, 0.20, 0.40):
            v = self.z(x, y - sgn * min(abs(y), dy))
            if v is not None:
                return v
        return self.z(x, 0.0)


def rim_outline(inset=0.050, n=64):
    x0, x1 = 1.11, 2.24
    xs = [x0 + (x1 - x0) * k / n for k in range(n + 1)]
    right = [(x, -max(0.05, hood_half(x) - inset)) for x in xs]
    h = max(0.05, hood_half(x1) - inset)
    arc = [(x1 + 0.055 * math.sqrt(max(0.0, 1.0 - (y / h) ** 2)), y)
           for y in [-h + 2.0 * h * k / 14 for k in range(1, 14)]]
    left = [(x, max(0.05, hood_half(x) - inset)) for x in reversed(xs)]
    return right + arc + left


def seal_outline(n=14):
    pts = [(x, y) for (x, y) in SEAL]
    left = smooth([(x, y) for (x, y) in pts], n)
    right = [(x, -y) for (x, y) in reversed(left)]
    return left + right[1:-1]


def _mat(name):
    return bpy.data.materials[name]


def build_frunk(collection="VPS_Details"):
    from carkit.interior.sweep import grid_mesh, tube, ellipse
    col = bpy.data.collections[collection]
    hood = Hood()
    satin, shadow = _mat("M_Black_Satin"), _mat("M_Shadow")
    grey = _mat("M_Radar_Grey")

    def zA(x, y):
        return hood.zc(x, y) - APRON_DROP

    def zF(x, y=0.0):
        return hood.zc(x, 0.0) - APRON_DROP - TUB_DEPTH

    made = []
    rim = rim_outline(inset=0.032)
    seal = seal_outline()
    if _cw(rim) != _cw(seal):
        seal = seal[::-1]
    ctr = (1.54, 0.0)
    ro, so = radial(rim, ctr), radial(seal, ctr)
    bm = bmesh.new()
    vo = [bm.verts.new((x, y, zA(x, y))) for (x, y) in ro]
    vi = [bm.verts.new((x, y, zA(x, y))) for (x, y) in so]
    for i in range(len(vo)):
        j = (i + 1) % len(vo)
        bm.faces.new((vo[i], vo[j], vi[j], vi[i]))
    made.append(_finish(bm, "VPS_Frunk_Apron", col, satin))
    made.append(tube("VPS_Frunk_HoodSeal", [(x, y, zA(x, y) + 0.008) for (x, y) in ro],
                     ellipse(0.0130, 0.0100, 8), col, satin, closed=True, lateral=(0.0, 0.0, 1.0)))

    rings = []
    for (d, e) in WALL:
        poly = inset_poly(seal, d)
        rings.append([(x, y, zA(sx, sy) + e) for (x, y), (sx, sy) in zip(poly, seal)])
    tub = grid_mesh("VPS_Frunk_Tub", rings, col, satin, wrap_t=True)
    made.append(tub)
    bm = bmesh.new()
    floor = [bm.verts.new(p) for p in rings[-1]]
    bm.faces.new(floor)
    made.append(_finish(bm, "VPS_Frunk_Floor", col, satin, smooth_shade=False))
    path = [(x, y, zA(x, y) + 0.005) for (x, y) in seal]
    made.append(tube("VPS_Frunk_Seal", path, ellipse(0.0085, 0.0075, 8), col, satin, closed=True,
                     lateral=(0.0, 0.0, 1.0)))

    X0, X1, HY = 1.40, 1.70, 0.220
    rows = []
    for i in range(25):
        x = X0 + (X1 - X0) * i / 24.0
        row = []
        for j in range(73):
            y = -HY + 2 * HY * j / 72.0
            edge = min(x - X0, X1 - x, HY - abs(y))
            f = min(1.0, max(0.0, edge / 0.014))
            f = f * f * (3 - 2 * f)
            rib = 0.5 * (1.0 + math.cos(2 * math.pi * y / 0.044))
            row.append((x, y, zF(x) + 0.0025 + f * (0.0075 + 0.0035 * rib)))
        rows.append(row)
    made.append(grid_mesh("VPS_Frunk_Mat", rows, col, satin))
    for k, sy in enumerate((-1, 1)):
        made.append(_disc("VPS_Frunk_Pad%d" % k, 1.55, sy * 0.115, 0.045,
                          lambda x, y: zF(x) + 0.0115, 0.004, col, satin))

    made.append(_prism("VPS_Frunk_CoverWasher", _rrect(1.58, -0.560, 0.043, 0.045, 0.012), zA, 0.008, col, satin, 0.0045))
    made.append(_prism("VPS_Frunk_CoverBattery", _rrect(1.56, 0.565, 0.058, 0.060, 0.016), zA, 0.008, col, satin, 0.0045))
    for k, sy in enumerate((-1, 1)):
        made.append(_prism("VPS_Frunk_CoverLip%d" % k, _rrect(2.10, sy * 0.24, 0.026, 0.020, 0.006), zA, 0.006, col, satin, 0.003))
    for k, (x, y) in enumerate(((1.38, -0.52), (1.38, 0.52), (1.76, -0.50), (1.76, 0.50))):
        made.append(_disc("VPS_Frunk_Stop%d" % k, x, y, 0.022, zA, 0.012, col, satin))
    made.append(_prism("VPS_Frunk_Vent", _rrect(1.16, -0.28, 0.026, 0.120, 0.004), zA, 0.006, col, grey, 0.004))
    made.append(_prism("VPS_Frunk_Latch", _rrect(2.12, 0.0, 0.034, 0.020, 0.018), zA, 0.004, col, shadow, 0.0025))
    return made


def build_hood_liner(col, inset=0.14):
    from carkit.interior.sweep import grid_mesh
    hood = Hood()
    xa, xb = 1.18, 2.20
    xm, hl = 0.5 * (xa + xb), 0.5 * (xb - xa)
    rows = []
    for i in range(29):
        x = xa + (xb - xa) * i / 28.0
        t = (x - xm) / hl
        end = max(0.0, 1.0 - abs(t) ** 6) ** (1.0 / 6.0)
        h = max(0.04, (hood_half(x) - inset) * end)
        rows.append([(x, -h + 2 * h * j / 26.0,
                      hood.zc(x, -h + 2 * h * j / 26.0) - 0.0028 - 0.008) for j in range(27)])
    return grid_mesh("VPS_HoodLiner", rows, col, _mat("M_Black_Satin"))


def bonnet_hinge():
    return Vector((HOOD_HINGE[0], 0.0, HOOD_HINGE[1]))


def split_bonnet():
    from carkit import export as X
    col = bpy.data.collections.get("VPS_BonnetGrp") or bpy.data.collections.new("VPS_BonnetGrp")
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    liner = build_hood_liner(col)
    hood = bpy.data.objects["VPS_Hood"]
    for c in list(hood.users_collection):
        c.objects.unlink(hood)
    col.objects.link(hood)
    bonnet = X.join("VPS_Bonnet", [hood.name, liner.name])
    h = bonnet_hinge()
    bonnet.data.transform(Matrix.Translation(-h))
    bonnet.matrix_world = Matrix.Translation(h)
    bonnet["hinge"] = tuple(h)
    return bonnet


def bonnet_groups():
    return [("VoyahPassionS_Bonnet", "VPS_BonnetGrp")]


def set_bonnet(deg):
    ob = bpy.data.objects.get("VPS_Bonnet")
    if ob is not None:
        h = bonnet_hinge()
        ob.matrix_world = Matrix.Translation(h) @ Matrix.Rotation(-math.radians(deg), 4, 'Y')


def open_hull(hull="VPS_Shell_Shadow"):
    from carkit import cut as C
    ob = bpy.data.objects[hull]
    sheet = C.sheet_bvh(ob)
    cutter = C.prism_dir("_bay", [(x, y, 1.35) for (x, y) in rim_outline(inset=0.045)],
                         (0.0, 0.0, 1.0), back=0.58, front=0.0)
    before, after = C.difference(ob, [cutter], "bay_")
    removed = C.prune_off_sheet(ob, sheet)
    return before, after, removed
