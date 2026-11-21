"""Avatr 06T centre console (c10_0015, c10_0047, c10_0050, c10_0051, c3_0001, c3_0014, c3_0028).

A floating Cotton White bridge from the dash to the rear seats, open underneath down to a tray on the floor:

    arch        a thick white frame rising from the bridge's front, the 15.6 in screen standing on its top
                (the screen's lower edge at z 0.945); inside its mouth a black vent across the top and a black
                glossy plate with the AVATR wordmark sloping back to the pad
    pad         a flat white top behind the arch, a satin-silver phone guide down its middle (wireless charging)
    cup block   a raised white block with two cupholders, satin rims, dark rubber mats
    armrest     a long padded white lid to the rear seats
    rear face   the rear passengers' vent: a dark louvred slot in a rounded white face

Axes: +X forward, +Y left, +Z up.
"""
import math

import bmesh
import bpy
from mathutils import Vector

import a06t_interior as RI
from carkit import mesh as M
from carkit.geom import Curve
from carkit.interior import fittings as F
from carkit.interior.sweep import grid_mesh, tube, ellipse, smooth_path, _orient_to

X_FRONT, X_REAR = 0.750, -0.560
HW = 0.128                                  # half width
# the pad behind the arch meets the cupholders, aligned with the forward-moved front seats and door armrest (z ~0.745)
TOP = Curve([
    (X_REAR, 0.720), (-0.545, 0.730), (-0.520, 0.735), (0.310, 0.735), (0.325, 0.728), (0.340, 0.720),
    (0.500, 0.720), (0.515, 0.715), (0.528, 0.718), (0.542, 0.722), (0.605, 0.735), (0.660, 0.748),
    (X_FRONT, 0.755),
], mode="pchip")
CUPS = [(0.420, 0.057, 0.041), (0.420, -0.057, 0.041)]         # (x, y, r)


def _under(x):
    """The console's base: solid all the way down to the carpeted floor (eliminates open hole)."""
    return RI.FLOOR_Z + 0.004


def _stations():
    xs, x = [], X_REAR
    while x < X_FRONT:
        xs.append(x)
        dense = (-0.56 < x < -0.50) or (0.30 < x < 0.35) or (0.49 < x < 0.55)
        x += 0.004 if dense else 0.012
    xs.append(X_FRONT)
    return xs


def _section(x, n_arc=6, ny=28):
    zt, zb = TOP(x), _under(x)
    r = 0.022
    pts = [(-HW + 0.004, zb), (-HW, zb + 0.012), (-HW, zt - r)]
    for k in range(1, n_arc):
        a = math.pi - 0.5 * math.pi * k / n_arc
        pts.append((-HW + r + r * math.cos(a), zt - r + r * math.sin(a)))
    for k in range(ny + 1):
        y = -HW + r + 2 * (HW - r) * k / ny
        pts.append((y, zt + 0.0015 * (1.0 - (y / (HW - r)) ** 2)))
    for k in range(1, n_arc):
        a = 0.5 * math.pi - 0.5 * math.pi * k / n_arc
        pts.append((HW - r + r * math.cos(a), zt - r + r * math.sin(a)))
    pts += [(HW, zt - r), (HW, zb + 0.012), (HW - 0.004, zb)]
    return pts


def build_body(col, lib):
    xs = _stations()
    rows = [[(x, y, z) for (y, z) in _section(x)] for x in xs]
    ob = grid_mesh("int_console_body", rows, col, lib["plastic_white"])
    # open the cupholders
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    kill = [f for f in bm.faces if f.calc_center_median().z > 0.65 and
            any((f.calc_center_median().x - cx) ** 2 + (f.calc_center_median().y - cy) ** 2 < (r - 0.002) ** 2
                for (cx, cy, r) in CUPS)]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    bm.to_mesh(ob.data)
    bm.free()
    M.orient(ob.data, lambda c: (0.0, c[1], max(0.0, c[2] - 0.60)))
    made = [ob]
    for x, s, tag in ((X_REAR, -1.0, "rear"), (X_FRONT, 1.0, "front")):
        made.append(F.ngon_cap(col, "int_console_" + tag, [(x + s * 0.0005, y, z) for (y, z) in _section(x)],
                               lib["plastic_white"], (s, 0.0, 0.0)))
    return made


def _mat(name, base, rough, **kw):
    from carkit import materials as MB
    m = bpy.data.materials.get(name)
    if m is None:
        m, nt, b = MB.mat(name)
        MB.set_inputs(b, base=base, metallic=kw.pop("metallic", 0.0), roughness=rough, **kw)
    return m


# the U-shaped padded surround under the screen (c10_0015 / c10_0047, the owner's photo 1): a rim open toward the seats
SUR_X0, SUR_X1, SUR_Y = 0.575, 0.734, 0.112      # centre-line: open end, front wall, half width
SUR_HV, SUR_HH = 0.028, 0.022                    # the rim's section: vertical and horizontal half sizes
TRAY_HW = 0.090


def build_surround(col, lib):
    """A U-shaped padded surround housing a recessed dark tray with the AVATR wordmark; the screen floats above it
    (2026-11-21: the old arch, its louvred vent, glossy black plate and the bar the screen stood on are gone)."""
    made = []
    ctrl = [(SUR_X0, SUR_Y), (0.640, SUR_Y), (0.703, SUR_Y - 0.004), (0.728, SUR_Y - 0.030), (SUR_X1, 0.0),
            (0.728, -SUR_Y + 0.030), (0.703, -SUR_Y + 0.004), (0.640, -SUR_Y), (SUR_X0, -SUR_Y)]
    xy = smooth_path([(x, y, 0.0) for (x, y) in ctrl], 80)
    path = [(x, y, TOP(x) + 0.021) for (x, y, _) in xy]
    e = 2.0 / 2.8
    prof = []
    for k in range(24):
        t = 2 * math.pi * k / 24
        c, s = math.cos(t), math.sin(t)
        prof.append((SUR_HV * math.copysign(abs(c) ** e, c), SUR_HH * math.copysign(abs(s) ** e, s)))

    def fade(s):
        f = RI._smooth(min(s, 1.0 - s) / 0.07)
        k = 0.55 + 0.45 * f
        return (k, k)
    made.append(tube("int_console_surround", path, prof, col, lib["leather_white"], lateral=(0.0, 0.0, 1.0), scale=fade))
    # the recessed tray: a dark matte floor lower than the rim, dished toward the middle
    tray = _mat("INT_Console_Tray", (0.012, 0.012, 0.014), 0.85, specular=0.2)
    x0, x1 = SUR_X0 + 0.004, SUR_X1 - SUR_HH - 0.004
    rows = []
    for i in range(15):
        x = x0 + (x1 - x0) * i / 14.0
        rows.append([(x, TRAY_HW * (1.0 - 2.0 * j / 10.0),
                      TOP(x) + 0.0075 - 0.0025 * (1.0 - (1.0 - 2.0 * j / 10.0) ** 2)) for j in range(11)])
    tr = grid_mesh("int_console_tray", rows, col, tray)
    M.orient(tr.data, lambda c: (0.0, 0.0, 1.0))
    made.append(tr)
    # the wordmark, reading from the seats, on the tray's front part
    t = M.text_mesh("int_console_logo", "AVATR", 0.0135, col, lib["satin_metal"], extrude=0.0004, resolution=4)
    U, V = Vector((0.0, -1.0, 0.0)), Vector((1.0, 0.0, 0.0))
    from mathutils import Matrix
    Mx = Matrix((tuple(U), tuple(V), tuple(U.cross(V)))).transposed().to_4x4()
    xl = x1 - 0.026
    Mx.translation = Vector((xl, 0.0, TOP(xl) + 0.0068)) - U * 0.034
    t.matrix_world = Mx
    made.append(t)
    return made


def build_pads(col, lib):
    """The dual wireless charging pad behind the surround: two matte dark pads, each with a raised border and a row of
    small horizontal grip ridges across its front (c10_0050 / c10_0051)."""
    made = []
    pad = _mat("INT_Charge_Pad", (0.030, 0.030, 0.034), 0.92, specular=0.15)
    x0, x1, hw, y_mid = 0.470, 0.552, 0.049, 0.054
    zp = 0.7258
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        yc = side * y_mid
        outline = [(x0 + a + 0.5 * (x1 - x0), yc + b) for (a, b) in
                   F.round_rect_xy(-(x1 - x0) / 2, (x1 - x0) / 2, -hw, hw, 0.014, 5)]
        made.append(F.ngon_cap(col, "int_console_pad" + tag, [(x, y, zp) for (x, y) in outline], pad, (0.0, 0.0, 1.0)))
        ring = [(x, y, zp + 0.0006) for (x, y) in outline]
        made.append(tube("int_console_padrim" + tag, ring + [ring[0]], ellipse(0.0016, 0.0009, 6), col, lib["satin"],
                         lateral=(0.0, 0.0, 1.0)))
        for k in range(5):
            xr = x1 - 0.016 - 0.0085 * k
            made.append(F.box(col, "int_console_padridge%s%d" % (tag, k), (xr, yc, zp + 0.0010),
                              (0.0034, 2 * hw - 0.030, 0.0022), pad, r=0.0007))
    return made


def build_top(col, lib):
    made = []
    # cupholders: wells, satin rims, dark mats
    for k, (cx, cy, r) in enumerate(CUPS):
        z0 = TOP(cx)
        rings = []
        for dz, s in ((0.0, 1.0), (0.005, 0.985), (0.068, 0.95), (0.080, 0.88), (0.082, 0.0)):
            rings.append([(cx + r * s * math.cos(2 * math.pi * j / 40), cy + r * s * math.sin(2 * math.pi * j / 40),
                           z0 - dz) for j in range(40)])
        well = grid_mesh("int_console_cup%d" % k, rings[:-2], col, lib["piano"], wrap_t=True)
        M.orient(well.data, lambda c, cx=cx, cy=cy: (cx - c[0], cy - c[1], 0.3))
        made.append(well)
        mat = grid_mesh("int_console_cupmat%d" % k, rings[-2:], col, lib["rubber"], wrap_t=True)
        M.orient(mat.data, lambda c: (0.0, 0.0, 1.0))
        made.append(mat)
        ring = [(cx + r * math.cos(2 * math.pi * j / 48), cy + r * math.sin(2 * math.pi * j / 48), z0 + 0.0012)
                for j in range(49)]
        made.append(tube("int_console_cuprim%d" % k, ring, ellipse(0.0032, 0.0022, 8), col, lib["satin_metal"],
                         lateral=(0.0, 0.0, 1.0)))
    # the armrest's lid: a padded leather top with a seam round it
    x0, x1, w = 0.320, -0.535, HW - 0.012
    rows = []
    for i in range(25):
        x = x0 + (x1 - x0) * i / 24.0
        ex = math.sin(math.pi * i / 24.0) ** 0.25
        rows.append([(x, w * (1 - 2 * j / 16.0), TOP(x) + 0.004 + 0.016 * ex *
                      (1.0 - abs(1 - 2 * j / 16.0) ** 3)) for j in range(17)])
    lid = grid_mesh("int_console_lid", rows, col, lib["leather_white"])
    M.orient(lid.data, lambda c: (0.0, 0.0, 1.0))
    made.append(lid)
    return made


def build_rear_face(col, lib):
    """The rear passengers' vent (c3_0028): a dark slot with vanes in the rounded rear face."""
    made = []
    x = X_REAR - 0.004
    zv = 0.635
    made.append(F.box(col, "int_console_rvent", (x, 0.0, zv), (0.010, 0.170, 0.034), lib["piano"], r=0.008))
    for k in range(9):
        y = -0.070 + 0.140 * k / 8.0
        made.append(F.box(col, "int_console_rvane%d" % k, (x - 0.004, y, zv), (0.004, 0.0025, 0.026),
                          lib["satin"], r=0.0008))
    rim = [(x - 0.0055, a, b) for (a, b) in F.round_rect_xy(-0.088, 0.088, zv - 0.020, zv + 0.020, 0.016, 6)]
    made.append(tube("int_console_rvent_rim", rim + [rim[0]], ellipse(0.0022, 0.0022, 6), col, lib["satin_metal"],
                     lateral=(1.0, 0.0, 0.0)))
    return made


def build_ambient(col, lib):
    """Ambient lighting strip along the upper console shoulder below the armrest and pad."""
    made = []
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        path = [(-0.520 + 1.150 * k / 24.0, s * (HW + 0.002), TOP(-0.520 + 1.150 * k / 24.0) - 0.012) for k in range(25)]
        made.append(tube("int_console_ambient" + tag, path, ellipse(0.0018, 0.0018, 6), col, lib["ambient"],
                         lateral=(0.0, 0.0, 1.0)))
    return made


def build(col, lib):
    # no ambient strips on the console (the owner, 2026-11-21: "replace the neon pink console strips")
    return build_body(col, lib) + build_surround(col, lib) + build_pads(col, lib) + build_top(col, lib) +         build_rear_face(col, lib)
