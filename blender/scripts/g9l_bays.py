"""XPeng G9L bays: the frunk under the bonnet, from the opening photographs (Autohome series 8659,
cat 12: c12_0001-6 on the purple car, c12_0068-73 on the grey one; blender/reference/xpeng-g9l/openings).

What the photographs show, from the cowl forward: a black wiper well under the windscreen's foot with a
ribbed vent strip and the two wipers parked along the glass; a black moulded tray the whole width of the hood
with a thick seal round its rim; a deep rounded-rectangle storage tub in the middle; the blue washer-fluid cap
at the right rear (the passenger side); a rounded slot at each front corner; two gas struts at the cowl's
corners; the bonnet's underside lined with a black pad inside its painted frame.

    import g9l_bays as BY
    BY.build_frunk()      # the static bay (G9L_Details)
    BY.split_bonnet()     # G9L_Bonnet: hood + liner, origin on the hinge
    BY.open_hull()        # the hull's roof under the bonnet

Car axes +x forward, +y left, z up.
"""
import math

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from carkit.bay import (smooth, inset_poly, radial, finish as _finish, prism as _prism,
                        rrect as _rrect, disc as _disc, is_cw as _cw)

# plan half-width of the hood by x, measured on the built panel (G9L_Hood)
HOOD_HALF = [(1.20, 0.919), (1.25, 0.951), (1.5, 0.942), (1.9, 0.912), (2.15, 0.862),
             (2.20, 0.866), (2.25, 0.706), (2.30, 0.212), (2.312, 0.0)]
HOOD_HINGE = (1.215, 1.247)    # (x, z) of the hinge axis, along y, under the rear edge
HOOD_DEG = 62.0
APRON_DROP = 0.080             # the tray's height under the hood's top surface
TUB_DEPTH = 0.225
# the tub's outline, half-width by x from its rear edge round the front (the +y half; mirrored): a wide
# rounded rectangle, about 1.0 m across and 0.5 m deep (c12_0002, c12_0070)
TUB = [(1.560, 0.0), (1.560, 0.400), (1.572, 0.465), (1.615, 0.505), (1.760, 0.520),
       (1.900, 0.500), (1.980, 0.460), (2.020, 0.385), (2.032, 0.220), (2.032, 0.0)]
# the tub wall's offsets (inward, down) from the rim
WALL = [(0.0, 0.0), (0.004, -0.006), (0.010, -0.018), (0.016, -0.065), (0.022, -0.140),
        (0.032, -0.200), (0.048, -0.225)]


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
        ob = bpy.data.objects.get("G9L_Hood") or bpy.data.objects["G9L_Bonnet"]
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        # the bonnet node is built about its hinge: back to the closed pose
        mw = ob.matrix_world.copy()
        self.tree = BVHTree.FromPolygons([mw @ v.co for v in me.vertices],
                                         [list(p.vertices) for p in me.polygons])
        ev.to_mesh_clear()

    def z(self, x, y):
        h = self.tree.ray_cast(Vector((x, y, 2.0)), Vector((0.0, 0.0, -1.0)), 3.0)[0]
        return h.z if h is not None else None

    def zc(self, x, y):
        """Top height, from the nearest point toward the centreline that has one."""
        sgn = 1.0 if y >= 0 else -1.0
        for dy in (0.0, 0.03, 0.06, 0.10, 0.20, 0.40):
            v = self.z(x, y - sgn * min(abs(y), dy))
            if v is not None:
                return v
        return self.z(x, 0.0)


def rim_outline(inset=0.040, n=64):
    """The tray's outer edge: the hood's plan inset by `inset`, from the cowl to a rounded
    front. A closed polygon of (x, y)."""
    x0, x1 = 1.236, 2.185
    xs = [x0 + (x1 - x0) * k / n for k in range(n + 1)]
    right = [(x, -max(0.05, hood_half(x) - inset)) for x in xs]
    h = max(0.05, hood_half(x1) - inset)
    arc = [(x1 + 0.060 * math.sqrt(max(0.0, 1.0 - (y / h) ** 2)), y)
           for y in [-h + 2.0 * h * k / 14 for k in range(1, 14)]]
    left = [(x, max(0.05, hood_half(x) - inset)) for x in reversed(xs)]
    return right + arc + left


def tub_outline(n=10):
    """The tub's closed outline (x, y): the TUB half-widths mirrored."""
    left = smooth([(x, y) for (x, y) in TUB], n)
    right = [(x, -y) for (x, y) in reversed(left)]
    return left + right[1:-1]


def _mat(name):
    return bpy.data.materials[name]


def _plastic():
    """The bay's moulded plastic: black, but a lit photograph of it (c12_0002) reads sRGB ~45,
    well above the satin black the rest of the car uses; baked ambient occlusion darkens it
    further, so its albedo is a dark grey."""
    from carkit import materials as MB
    m = bpy.data.materials.get("M_Frunk_Plastic")
    if m is None:
        m, nt, b = MB.mat("M_Frunk_Plastic")
        MB.set_inputs(b, base=(0.058, 0.059, 0.064), metallic=0.0, roughness=0.72, specular=0.35)
    return m


def _tub_plastic():
    """The storage tub's moulded liner: nearly black in the photographs (c12_0002, c12_0003)."""
    from carkit import materials as MB
    m = bpy.data.materials.get("M_Frunk_Tub")
    if m is None:
        m, nt, b = MB.mat("M_Frunk_Tub")
        MB.set_inputs(b, base=(0.020, 0.020, 0.022), metallic=0.0, roughness=0.78, specular=0.30)
    return m


def _cap_material():
    from carkit import materials as MB
    m = bpy.data.materials.get("M_Cap_Blue")
    if m is None:
        m, nt, b = MB.mat("M_Cap_Blue")
        MB.set_inputs(b, base=(0.020, 0.075, 0.42), metallic=0.0, roughness=0.42, specular=0.45)
    return m


# ------------------------------------------------------------------ the bay
def build_frunk(collection="G9L_Details"):
    """The static bay: wiper well, tray, tub with its divider, the rim seal, the corner pockets,
    the cap, the wipers. Needs G9L_Hood (for the heights under it)."""
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
    # the tray: from the rim in to the tub's lip, paired along rays from the tub's centre
    ctr = (1.80, 0.0)
    ro, so = radial(rim, ctr), radial(tub, ctr)
    bm = bmesh.new()
    vo = [bm.verts.new((x, y, zA(x, y))) for (x, y) in ro]
    vi = [bm.verts.new((x, y, zA(x, y))) for (x, y) in so]
    for i in range(len(vo)):
        j = (i + 1) % len(vo)
        bm.faces.new((vo[i], vo[j], vi[j], vi[i]))
    made.append(_finish(bm, "G9L_Frunk_Tray", col, satin))
    # the hood's own seal round the tray's outer edge (c12_0001: a thick black bead)
    made.append(tube("G9L_Frunk_HoodSeal", [(x, y, zA(x, y) + 0.009) for (x, y) in ro],
                     ellipse(0.0150, 0.0110, 8), col, rubber, closed=True, lateral=(0.0, 0.0, 1.0)))
    # the tub: rings inward and down from its lip, then the floor
    rings = []
    for (d, e) in WALL:
        poly = inset_poly(tub, d)
        rings.append([(x, y, zA(sx, sy) + e) for (x, y), (sx, sy) in zip(poly, tub)])
    made.append(grid_mesh("G9L_Frunk_Tub", rings, col, _tub_plastic(), wrap_t=True))
    bm = bmesh.new()
    floor = [bm.verts.new(p) for p in rings[-1]]
    bm.faces.new(floor)
    made.append(_finish(bm, "G9L_Frunk_Floor", col, _tub_plastic(), smooth_shade=False))
    # the tub's lip: a slim rubber bead
    made.append(tube("G9L_Frunk_TubSeal", [(x, y, zA(x, y) + 0.004) for (x, y) in tub],
                     ellipse(0.0070, 0.0060, 8), col, rubber, closed=True, lateral=(0.0, 0.0, 1.0)))
    # the washer cap, right rear of the tray (c12_0002: a blue screw cap in a round well)
    cx, cy = 1.500, -0.775
    made.append(_disc("G9L_Frunk_CapWell", cx, cy, 0.036, zA, 0.012, col, shadow))
    made.append(_disc("G9L_Frunk_Cap", cx, cy, 0.026, zA, 0.040, col, _cap_material(), lift=0.016))
    # a rounded slot at each front corner of the tray (c12_0002: no pocket round it)
    for k, sy in enumerate((-1, 1)):
        made.append(_prism("G9L_Frunk_Slot%d" % k, _rrect(1.99, sy * 0.600, 0.030, 0.012, 0.010),
                           zA, 0.020, col, gloss, 0.0045))
    # the tray's small clip holes along its rim (the four dots in the photographs)
    for k, (x, y) in enumerate(((1.60, -0.860), (1.60, 0.860), (2.04, -0.300), (2.04, 0.300))):
        made.append(_disc("G9L_Frunk_Stop%d" % k, x, y, 0.018, zA, 0.010, col, shadow))
    # the wiper well: a ribbed vent strip across the cowl and the seal at the tray's back
    made += _build_cowl(col, hood, zA, satin, rubber, shadow)
    return made


def _build_cowl(col, hood, zA, satin, rubber, shadow):
    from carkit.interior.sweep import grid_mesh, tube, ellipse
    made = []
    hw = 0.880
    # the well's sloping back wall, from the windscreen's foot down to the tray
    rows = []
    for i in range(7):
        t = i / 6.0
        x = 1.192 + 0.046 * t
        z = 1.255 + (zA(1.238, 0.0) - 1.255) * (t ** 1.3)
        rows.append([(x, -hw + 2 * hw * j / 36.0, z) for j in range(37)])
    well = grid_mesh("G9L_Frunk_Cowl", rows, col, satin)
    from carkit import mesh as M
    M.orient(well.data, lambda c: (1.0, 0.0, 1.0))
    made.append(well)
    # ribs of the vent strip: thin bars across the well
    for k in range(7):
        x = 1.204 + 0.006 * k
        z = 1.255 + (zA(1.238, 0.0) - 1.255) * (((x - 1.192) / 0.046) ** 1.3) + 0.0035
        made.append(tube("G9L_Frunk_Rib%d" % k, [(x, -0.74 + 1.48 * j / 12.0, z) for j in range(13)],
                         ellipse(0.0022, 0.0022, 6), col, shadow, lateral=(1.0, 0.0, 0.0)))
    # the rubber seal along the tray's rear edge
    made.append(tube("G9L_Frunk_CowlSeal", [(1.244, -hw + 2 * hw * j / 36.0, zA(1.244, 0.0) + 0.006)
                                           for j in range(37)],
                     ellipse(0.0100, 0.0080, 8), col, rubber, lateral=(1.0, 0.0, 0.0)))
    # the two wipers parked along the glass (c12_0002): an arm and a blade each
    for nm, y0, y1, yp in (("L", 0.800, 0.260, 0.820), ("R", 0.110, -0.740, -0.770)):
        z = 1.262
        made.append(tube("G9L_Wiper_Blade" + nm, [(1.172, y0 + (y1 - y0) * j / 8.0, z) for j in range(9)],
                         [(a * 0.0035, b * 0.011) for (a, b) in ellipse(1, 1, 8)], col, satin,
                         lateral=(1.0, 0.0, 0.0)))
        made.append(tube("G9L_Wiper_Arm" + nm, [(1.168, y1 + (y0 - y1) * 0.18 + 0.0 * j, z + 0.006 + 0.0)
                                               for j in range(2)] + [(1.17, yp, z + 0.004)],
                         ellipse(0.0050, 0.0050, 6), col, satin, lateral=(1.0, 0.0, 0.0)))
    return made


# ---------------------------------------------------------------- the bonnet
def build_hood_liner(col, inset=0.150):
    """The black insulator pad under the bonnet, inside its painted frame (c12_0001): a sheet
    9 mm under the skin, with rounded ends."""
    from carkit.interior.sweep import grid_mesh
    hood = Hood()
    xa, xb = 1.290, 2.150
    xm, hl = 0.5 * (xa + xb), 0.5 * (xb - xa)
    rows = []
    for i in range(29):
        x = xa + (xb - xa) * i / 28.0
        t = (x - xm) / hl
        end = max(0.0, 1.0 - abs(t) ** 6) ** (1.0 / 6.0)
        h = max(0.04, (hood_half(x) - inset) * end)
        rows.append([(x, -h + 2 * h * j / 26.0,
                      hood.zc(x, -h + 2 * h * j / 26.0) - 0.0028 - 0.010) for j in range(27)])
    ob = grid_mesh("G9L_HoodLiner", rows, col, _mat("M_Black_Satin"))
    return ob


def bonnet_hinge():
    return Vector((HOOD_HINGE[0], 0.0, HOOD_HINGE[1]))


def split_bonnet():
    """G9L_Bonnet: the hood and its liner as a node of its own, origin on the hinge axis (which
    runs along y)."""
    from carkit import export as X
    col = bpy.data.collections.get("G9L_BonnetGrp") or bpy.data.collections.new("G9L_BonnetGrp")
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    liner = build_hood_liner(col)
    hood = bpy.data.objects["G9L_Hood"]
    for c in list(hood.users_collection):
        c.objects.unlink(hood)
    col.objects.link(hood)
    bonnet = X.join("G9L_Bonnet", [hood.name, liner.name])
    h = bonnet_hinge()
    bonnet.data.transform(Matrix.Translation(-h))
    bonnet.matrix_world = Matrix.Translation(h)
    bonnet["hinge"] = tuple(h)
    return bonnet


def bonnet_groups():
    return [("XpengG9L_Bonnet", "G9L_BonnetGrp")]


def set_bonnet(deg):
    """Preview: swing the bonnet `deg` open (nose up)."""
    ob = bpy.data.objects.get("G9L_Bonnet")
    if ob is not None:
        h = bonnet_hinge()
        ob.matrix_world = Matrix.Translation(h) @ Matrix.Rotation(-math.radians(deg), 4, 'Y')


def open_hull(hull="G9L_Shell_Shadow"):
    """Cut the hull's roof away under the bonnet's opening (an exact boolean with a prism of
    the rim, like the other hull cuts), so the tub has room."""
    from carkit import cut as C
    ob = bpy.data.objects[hull]
    sheet = C.sheet_bvh(ob)
    cutter = C.prism_dir("_bay", [(x, y, 1.45) for (x, y) in rim_outline(inset=0.050)],
                         (0.0, 0.0, 1.0), back=0.85, front=0.0)
    before, after = C.difference(ob, [cutter], "bay_")
    removed = C.prune_off_sheet(ob, sheet)
    return before, after, removed
