"""Avatr 06T bays: the frunk under the bonnet and the boot behind the hatch.

    import a06t_bays as BY
    BY.build_frunk()      # the static bay (A06T_Details)
    BY.split_bonnet()     # A06T_Bonnet: hood + liner, origin on the hinge
    BY.open_hull()        # the hull's roof under the bonnet
"""
import math

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from carkit.bay import (smooth, inset_poly, radial, finish as _finish, prism as _prism,
                        rrect as _rrect, disc as _disc, is_cw as _cw)

HOOD_HALF = [(0.802, 0.833), (1.0, 0.810), (1.3, 0.770), (1.6, 0.731), (1.9, 0.661),
             (2.07, 0.607), (2.14, 0.440), (2.205, 0.0)]
HOOD_HINGE = (0.84, 1.06)      # (x, z) of the hinge axis, along y, under the rear edge
HOOD_DEG = 62.0
APRON_DROP = 0.050             # the apron's height under the hood's top surface
TUB_DEPTH = 0.250
SEAL = [(0.995, 0.0), (0.995, 0.405), (1.012, 0.450), (1.060, 0.466), (1.20, 0.462),
        (1.35, 0.442), (1.44, 0.405), (1.495, 0.330), (1.52, 0.200), (1.525, 0.0)]
WALL = [(0.0, 0.0), (0.004, -0.007), (0.010, -0.022), (0.018, -0.075), (0.028, -0.165),
        (0.042, -0.225), (0.062, -0.250)]


def hood_half(x):
    if x <= HOOD_HALF[0][0]:
        return HOOD_HALF[0][1]
    for (x0, y0), (x1, y1) in zip(HOOD_HALF, HOOD_HALF[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return 0.0


class Hood:
    """The built hood's top surface, for heights under and along it."""

    def __init__(self):
        dg = bpy.context.evaluated_depsgraph_get()
        ob = bpy.data.objects["A06T_Hood"] if "A06T_Hood" in bpy.data.objects else \
            bpy.data.objects["A06T_Bonnet"]
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
    x0, x1 = 0.87, 2.10
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


def build_frunk(collection="A06T_Details"):
    from carkit.interior.sweep import grid_mesh, tube, ellipse
    col = bpy.data.collections[collection]
    hood = Hood()
    satin = _mat("M_Black_Satin")
    shadow = _mat("M_Shadow") if "M_Shadow" in bpy.data.materials else satin
    grey = _mat("M_Radar_Grey")

    def zA(x, y):
        return hood.zc(x, y) - APRON_DROP

    def zF(x, y=0.0):
        return hood.zc(x, 0.0) - APRON_DROP - TUB_DEPTH

    made = []
    rim = rim_outline(inset=0.030)
    seal = seal_outline()
    if _cw(rim) != _cw(seal):
        seal = seal[::-1]
    ctr = (1.26, 0.0)
    ro, so = radial(rim, ctr), radial(seal, ctr)
    bm = bmesh.new()
    vo = [bm.verts.new((x, y, zA(x, y))) for (x, y) in ro]
    vi = [bm.verts.new((x, y, zA(x, y))) for (x, y) in so]
    for i in range(len(vo)):
        j = (i + 1) % len(vo)
        bm.faces.new((vo[i], vo[j], vi[j], vi[i]))
    made.append(_finish(bm, "A06T_Frunk_Apron", col, satin))
    made.append(tube("A06T_Frunk_HoodSeal", [(x, y, zA(x, y) + 0.008) for (x, y) in ro],
                     ellipse(0.0130, 0.0100, 8), col, satin, closed=True, lateral=(0.0, 0.0, 1.0)))
    rings = []
    for (d, e) in WALL:
        poly = inset_poly(seal, d)
        rings.append([(x, y, zA(sx, sy) + e) for (x, y), (sx, sy) in zip(poly, seal)])
    tub = grid_mesh("A06T_Frunk_Tub", rings, col, satin, wrap_t=True)
    made.append(tub)
    bm = bmesh.new()
    floor = [bm.verts.new(p) for p in rings[-1]]
    bm.faces.new(floor)
    made.append(_finish(bm, "A06T_Frunk_Floor", col, satin, smooth_shade=False))
    path = [(x, y, zA(x, y) + 0.005) for (x, y) in seal]
    made.append(tube("A06T_Frunk_Seal", path, ellipse(0.0085, 0.0075, 8), col, satin, closed=True,
                     lateral=(0.0, 0.0, 1.0)))
    X0, X1, HY = 1.17, 1.45, 0.215
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
    made.append(grid_mesh("A06T_Frunk_Mat", rows, col, satin))
    for k, sy in enumerate((-1, 1)):
        made.append(_disc("A06T_Frunk_Pad%d" % k, 1.31, sy * 0.115, 0.045,
                          lambda x, y: zF(x) + 0.0115, 0.004, col, satin))
    made.append(_prism("A06T_Frunk_CoverWasher", _rrect(1.35, -0.346, 0.043, 0.045, 0.012), zA, 0.008, col, satin, 0.0045))
    made.append(_prism("A06T_Frunk_CoverBattery", _rrect(1.33, 0.360, 0.058, 0.060, 0.016), zA, 0.008, col, satin, 0.0045))
    for k, sy in enumerate((-1, 1)):
        made.append(_prism("A06T_Frunk_CoverLip%d" % k, _rrect(1.95, sy * 0.24, 0.026, 0.020, 0.006), zA, 0.006, col, satin, 0.003))
    for k, (x, y) in enumerate(((1.19, -0.48), (1.18, 0.45), (1.50, -0.47), (1.49, 0.47))):
        made.append(_disc("A06T_Frunk_Stop%d" % k, x, y, 0.022, zA, 0.012, col, satin))
    made.append(_prism("A06T_Frunk_Vent", _rrect(0.935, -0.28, 0.026, 0.120, 0.004), zA, 0.006, col, grey, 0.004))
    made.append(_prism("A06T_Frunk_Latch", _rrect(1.95, 0.0, 0.034, 0.020, 0.018), zA, 0.004, col, shadow, 0.0025))
    return made


def build_hood_liner(col, inset=0.14):
    from carkit.interior.sweep import grid_mesh
    hood = Hood()
    xa, xb = 0.98, 2.05
    xm, hl = 0.5 * (xa + xb), 0.5 * (xb - xa)
    rows = []
    for i in range(29):
        x = xa + (xb - xa) * i / 28.0
        t = (x - xm) / hl
        end = max(0.0, 1.0 - abs(t) ** 6) ** (1.0 / 6.0)
        h = max(0.04, (hood_half(x) - inset) * end)
        rows.append([(x, -h + 2 * h * j / 26.0,
                      hood.zc(x, -h + 2 * h * j / 26.0) - 0.0028 - 0.008) for j in range(27)])
    ob = grid_mesh("A06T_HoodLiner", rows, col, _mat("M_Black_Satin"))
    return ob


def bonnet_hinge():
    return Vector((HOOD_HINGE[0], 0.0, HOOD_HINGE[1]))


def split_bonnet():
    from carkit import export as X
    col = bpy.data.collections.get("A06T_BonnetGrp") or bpy.data.collections.new("A06T_BonnetGrp")
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    liner = build_hood_liner(col)
    hood = bpy.data.objects["A06T_Hood"]
    for c in list(hood.users_collection):
        c.objects.unlink(hood)
    col.objects.link(hood)
    bonnet = X.join("A06T_Bonnet", [hood.name, liner.name])
    h = bonnet_hinge()
    bonnet.data.transform(Matrix.Translation(-h))
    bonnet.matrix_world = Matrix.Translation(h)
    bonnet["hinge"] = tuple(h)
    return bonnet


def bonnet_groups():
    return [("Avatr06T_Bonnet", "A06T_BonnetGrp")]


def set_bonnet(deg):
    ob = bpy.data.objects.get("A06T_Bonnet")
    if ob is not None:
        h = bonnet_hinge()
        ob.matrix_world = Matrix.Translation(h) @ Matrix.Rotation(-math.radians(deg), 4, 'Y')


def open_hull(hull="A06T_Shell_Shadow"):
    from carkit import cut as C
    ob = bpy.data.objects[hull]
    sheet = C.sheet_bvh(ob)
    cutter = C.prism_dir("_bay", [(x, y, 1.30) for (x, y) in rim_outline(inset=0.045)],
                         (0.0, 0.0, 1.0), back=0.55, front=0.0)
    before, after = C.difference(ob, [cutter], "bay_")
    removed = C.prune_off_sheet(ob, sheet)
    return before, after, removed
