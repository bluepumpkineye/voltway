"""BYD Seal EV bays: the front frunk under the bonnet, calibrated from the
Autohome Series 6394 opening photographs and official technical specs.

Features:
- Complete moulded surround tray apron with weatherstrip D-seal bead
- Deep storage frunk tub with ribbed base and perimeter seal
- Blue windshield washer fluid filler cap at left rear corner
- Cowl wiper well with parked wipers along the windscreen base
- Under-bonnet acoustic insulator liner pad
- Origin on the bonnet hinge axis (x = 1.075, z = 0.950) opening to 74 deg.
"""
import math

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from carkit import mesh as M
from carkit.bay import (smooth, inset_poly, radial, finish as _finish, prism as _prism,
                        rrect as _rrect, disc as _disc, is_cw as _cw)

# Plan half-width of the hood by x, scaled to BYD Seal (4800 x 1875 mm)
# (the windscreen's base is at x 1.07 on this body; the bonnet's leading edge at x 2.29 on the centreline)
HOOD_HALF = [
    (1.07, 0.720), (1.15, 0.745), (1.30, 0.758), (1.52, 0.760), (1.72, 0.752),
    (1.88, 0.742), (2.00, 0.720), (2.10, 0.640), (2.18, 0.500), (2.25, 0.280),
    (2.29, 0.0),
]
HOOD_HINGE = (1.075, 0.950)    # (x, z) of the hinge axis, along y, under the rear edge
HOOD_DEG = 74.0
APRON_DROP = 0.055
TUB_DEPTH = 0.150

TUB = [
    (1.270, 0.0), (1.270, 0.350), (1.300, 0.430), (1.380, 0.480), (1.520, 0.490),
    (1.700, 0.470), (1.780, 0.410), (1.830, 0.300), (1.850, 0.150), (1.850, 0.0),
]
WALL = [
    (0.0, 0.0), (0.005, -0.008), (0.012, -0.025), (0.022, -0.065),
    (0.032, -0.110), (0.044, -0.140), (0.056, -0.150),
]


def hood_half(x):
    if x <= HOOD_HALF[0][0]:
        return HOOD_HALF[0][1]
    for (x0, y0), (x1, y1) in zip(HOOD_HALF, HOOD_HALF[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return 0.0


class Hood:
    """The built hood's top surface (the closed pose), for heights under and along it."""

    def __init__(self):
        dg = bpy.context.evaluated_depsgraph_get()
        ob = bpy.data.objects.get("Seal_Hood") or bpy.data.objects.get("BYDSeal_Bonnet")
        if ob is None:
            self.tree = None
            return
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        mw = ob.matrix_world.copy()
        self.tree = BVHTree.FromPolygons([mw @ v.co for v in me.vertices],
                                         [list(p.vertices) for p in me.polygons])
        ev.to_mesh_clear()

    def z(self, x, y):
        if self.tree is None:
            return 0.72
        h = self.tree.ray_cast(Vector((x, y, 2.0)), Vector((0.0, 0.0, -1.0)), 3.0)[0]
        return h.z if h is not None else 0.72

    def zc(self, x, y):
        sgn = 1.0 if y >= 0 else -1.0
        for dy in (0.0, 0.03, 0.06, 0.10, 0.20, 0.40):
            v = self.z(x, y - sgn * min(abs(y), dy))
            if v is not None:
                return v
        return self.z(x, 0.0)


def rim_outline(inset=0.040, n=48):
    """The tray's outer edge: the hood's plan inset by `inset`."""
    x0, x1 = 1.100, 2.260
    xs = [x0 + (x1 - x0) * k / n for k in range(n + 1)]
    right = [(x, -max(0.04, hood_half(x) - inset)) for x in xs]
    h = max(0.04, hood_half(x1) - inset)
    arc = [(x1 + 0.050 * math.sqrt(max(0.0, 1.0 - (y / h) ** 2)), y)
           for y in [-h + 2.0 * h * k / 12 for k in range(1, 12)]]
    left = [(x, max(0.04, hood_half(x) - inset)) for x in reversed(xs)]
    return right + arc + left


def tub_outline(n=8):
    left = smooth([(x, y) for (x, y) in TUB], n)
    right = [(x, -y) for (x, y) in reversed(left)]
    return left + right[1:-1]


def build_frunk(collection=None, lib=None):
    """The complete frunk bay under the bonnet."""
    from carkit.interior.sweep import grid_mesh, tube, ellipse
    if collection is None:
        collection = bpy.data.collections.get("Seal_Details") or bpy.context.scene.collection
    if lib is None:
        import seal_materials as MT
        lib = MT.build_library()

    hd = Hood()
    satin = lib.get("black_trim") or lib.get("piano")
    rubber = lib.get("black_trim")
    shadow = lib.get("shadow")
    gloss = lib.get("black_gloss")

    def zA(x, y):
        return hd.zc(x, y) - APRON_DROP

    made = []
    rim = rim_outline(inset=0.040)
    tub = tub_outline()
    if _cw(rim) != _cw(tub):
        tub = tub[::-1]

    # 1. Full-width surround apron tray from rim to tub lip
    ctr = (1.57, 0.0)
    ro, so = radial(rim, ctr), radial(tub, ctr)
    bm = bmesh.new()
    vo = [bm.verts.new((x, y, zA(x, y))) for (x, y) in ro]
    vi = [bm.verts.new((x, y, zA(x, y))) for (x, y) in so]
    for i in range(len(vo)):
        j = (i + 1) % len(vo)
        bm.faces.new((vo[i], vo[j], vi[j], vi[i]))
    made.append(_finish(bm, "Seal_Frunk_Tray", collection, satin))

    # Hood rim weatherstrip seal
    made.append(tube("Seal_Frunk_HoodSeal", [(x, y, zA(x, y) + 0.008) for (x, y) in ro],
                     ellipse(0.014, 0.010, 8), collection, rubber, closed=True, lateral=(0.0, 0.0, 1.0)))

    # 2. Deep storage tub with walls and bottom
    rings = []
    for (d, e) in WALL:
        poly = inset_poly(tub, d)
        rings.append([(x, y, zA(sx, sy) + e) for (x, y), (sx, sy) in zip(poly, tub)])
    made.append(grid_mesh("Seal_Frunk_Tub", rings, collection, satin, wrap_t=True))

    bm_flr = bmesh.new()
    floor = [bm_flr.verts.new(p) for p in rings[-1]]
    bm_flr.faces.new(floor)
    made.append(_finish(bm_flr, "Seal_Frunk_Floor", collection, satin, smooth_shade=False))

    # Tub lip rubber bead
    made.append(tube("Seal_Frunk_TubSeal", [(x, y, zA(x, y) + 0.004) for (x, y) in tub],
                     ellipse(0.006, 0.005, 8), collection, rubber, closed=True, lateral=(0.0, 0.0, 1.0)))

    # 3. Washer fluid blue cap at left rear
    cx, cy = 1.200, 0.520
    made.append(_disc("Seal_Frunk_CapWell", cx, cy, 0.034, zA, 0.010, collection, shadow))
    made.append(_disc("Seal_Frunk_Cap", cx, cy, 0.024, zA, 0.035, collection, lib["glass"], lift=0.014))

    # 4. Cowl wiper well with parked wipers
    hw = 0.650
    rows = []
    for i in range(7):
        t = i / 6.0
        x = 1.085 + 0.045 * t
        z = 0.985 + (zA(1.130, 0.0) - 0.985) * (t ** 1.3)
        rows.append([(x, -hw + 2 * hw * j / 32.0, z) for j in range(33)])
    well = grid_mesh("Seal_Frunk_Cowl", rows, collection, satin)
    M.orient(well.data, lambda c: (1.0, 0.0, 1.0))
    made.append(well)

    z_w = hd.zc(1.095, 0.0) - 0.005
    for nm, y0, y1 in (("L", 0.500, 0.160), ("R", 0.060, -0.400)):
        made.append(tube("Seal_Wiper_Blade" + nm,
                         [(1.095, y0 + (y1 - y0) * j / 8.0, z_w) for j in range(9)],
                         [(a * 0.0035, b * 0.010) for (a, b) in ellipse(1, 1, 8)],
                         collection, gloss, lateral=(1.0, 0.0, 0.0)))

    return made


def build_hood_liner(col, inset=0.140):
    """The black acoustic insulator liner pad under the bonnet."""
    from carkit.interior.sweep import grid_mesh
    hood = Hood()
    xa, xb = 1.350, 2.180
    xm, hl = 0.5 * (xa + xb), 0.5 * (xb - xa)
    rows = []
    for i in range(25):
        x = xa + (xb - xa) * i / 24.0
        t = (x - xm) / hl
        end = max(0.0, 1.0 - abs(t) ** 6) ** (1.0 / 6.0)
        h = max(0.04, (hood_half(x) - inset) * end)
        rows.append([(x, -h + 2 * h * j / 22.0,
                      hood.zc(x, -h + 2 * h * j / 22.0) - 0.012) for j in range(23)])
    ob = grid_mesh("Seal_HoodLiner", rows, col, bpy.data.materials.get("M_Black_Satin") or bpy.data.materials["M_Black_Trim"])
    return ob


def split_bonnet():
    """Hinges Seal_Hood + liner as BYDSeal_Bonnet in Seal_BonnetGrp with origin on hinge axis."""
    from carkit import export as X
    col = bpy.data.collections.get("Seal_BonnetGrp") or bpy.data.collections.new("Seal_BonnetGrp")
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)

    hood = bpy.data.objects.get("Seal_Hood")
    if hood is None:
        return bpy.data.objects.get("BYDSeal_Bonnet")

    liner = build_hood_liner(col)
    for c in list(hood.users_collection):
        c.objects.unlink(hood)
    col.objects.link(hood)

    hx, hz = HOOD_HINGE
    origin = Vector((hx, 0.0, hz))
    join_names = [hood.name, liner.name]
    for extra in ("Seal_Hood_Center_Crease", "Seal_Hood_Ridge"):
        crease = bpy.data.objects.get(extra)
        if crease is not None:
            for c in list(crease.users_collection):
                c.objects.unlink(crease)
            col.objects.link(crease)
            join_names.append(crease.name)
    bonnet = X.join("BYDSeal_Bonnet", join_names)
    bonnet.name = "BYDSeal_Bonnet"
    bonnet.data.transform(Matrix.Translation(-origin))
    bonnet.matrix_world = Matrix.Translation(origin)
    bonnet["hinge"] = tuple(origin)
    return bonnet


def bonnet_groups():
    return [("BYDSeal_Bonnet", "Seal_BonnetGrp")]


def open_hull(hull="Seal_Shell_Shadow"):
    """Cuts exact opening in shadow shell under frunk tray rim."""
    from carkit import cut as C
    ob = bpy.data.objects.get(hull)
    if ob is None:
        return
    sheet = C.sheet_bvh(ob)
    cutter = C.prism_dir("_bay", [(x, y, 1.10) for (x, y) in rim_outline(inset=0.045)],
                         (0.0, 0.0, 1.0), back=0.70, front=0.0)
    C.difference(ob, [cutter], "bay_")
    C.prune_off_sheet(ob, sheet)


def set_bonnet(deg):
    """Preview: swing the bonnet `deg` open (nose up)."""
    ob = bpy.data.objects.get("BYDSeal_Bonnet")
    if ob is not None:
        hx, hz = HOOD_HINGE
        h = Vector((hx, 0.0, hz))
        ob.matrix_world = Matrix.Translation(h) @ Matrix.Rotation(-math.radians(deg), 4, 'Y')
