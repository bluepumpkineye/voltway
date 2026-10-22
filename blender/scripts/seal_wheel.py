"""BYD Seal steering wheel, traced from the driver's-view photographs (d0127, d0069, d0127 crops).

Frame (carkit.interior.steering.WheelFrame): u to the driver's right, v up the rim plane, w toward the
driver. Measured off d0127 at 3.76 px per mm, centred on the rim's circle:

    rim      orange leather, a 375 mm wide circle with a flat bottom (outer radius 187 mm, flat at
             v -162 mm), about 29 mm thick, tone-on-tone stitching on the inner edge
    hub      a shield-shaped orange airbag pad, 149 mm across its middle and 133 mm tall (full at the
             top, 64 mm wide at the bottom), the silver BYD wordmark across its upper third
    plate    a graphite plate behind the pad: an arm to each side of the pad carrying a roller and
             five keys, two kite-shaped windows (silver chamfer) below the arms, a bar under the pad
             and a bottom opening onto the dash
    column   a short shroud, a lights stalk on the left and a wiper stalk on the right
"""
import math

import bpy
from mathutils import Vector

import seal_interior as ZI
from carkit import mesh as M
from carkit.interior import fittings as F
from carkit.interior import steering as ST
from carkit.interior.sweep import cr_segments, grid_mesh, tube, ellipse, smooth_path

R_CTR = 0.171            # rim centreline radius
V_FLAT = -0.146          # centreline of the flat bottom
R_CORNER = 0.055         # fillet between the circle and the flat
SECTION = (0.0145, 0.0165)
PAD_DV = -0.007          # the pad's centre, below the rim's

# pad outline about its own centre (u, v)
PAD = [(0.050, 0.066), (0.000, 0.0685), (-0.050, 0.066), (-0.064, 0.058), (-0.072, 0.040),
       (-0.0745, 0.000), (-0.070, -0.030), (-0.056, -0.053), (-0.034, -0.066), (0.000, -0.068),
       (0.034, -0.066), (0.056, -0.053), (0.070, -0.030), (0.0745, 0.000), (0.072, 0.040),
       (0.064, 0.058)]

# the left window (kite) in frame coordinates; the right one is its mirror
WINDOW_L = [(-0.1604, -0.0189), (-0.0829, -0.0414), (-0.0637, -0.0720), (-0.0802, -0.0932),
            (-0.1068, -0.1087), (-0.1248, -0.1065), (-0.1413, -0.0720)]
BOTTOM = [(-0.040, -0.090), (0.040, -0.090), (0.062, -0.105), (0.085, -0.130), (-0.085, -0.130),
          (-0.062, -0.105)]
ARM_L = [(-0.0738, 0.0252), (-0.1038, 0.0189), (-0.1339, 0.0085), (-0.1565, -0.0013)]
PLATE_W0, PLATE_W1 = -0.004, 0.012


def d_loop(n=96):
    """The rim's centreline: a circle with a flat bottom and filleted corners, counter-clockwise from
    the right-hand fillet over the top, as dense (u, v) points."""
    rc = R_CORNER
    cy = V_FLAT + rc
    cx = math.sqrt((R_CTR - rc) ** 2 - cy ** 2)
    a1 = math.atan2(cy, cx)                       # direction of the right fillet's centre (about -52 deg)
    a_end = math.pi - a1                          # the left one, the long way round
    pts = []
    for k in range(n + 1):
        t = a1 + (a_end - a1) * k / n
        pts.append((R_CTR * math.cos(t), R_CTR * math.sin(t)))
    ang0 = math.atan2(pts[-1][1] - cy, pts[-1][0] + cx)
    for k in range(1, 13):                        # left fillet down to the flat
        t = ang0 + (-0.5 * math.pi - ang0) * k / 12.0
        pts.append((-cx + rc * math.cos(t), cy + rc * math.sin(t)))
    for k in range(1, 12):                        # the flat
        pts.append((-cx + 2 * cx * k / 12.0, V_FLAT))
    ang1 = math.atan2(pts[0][1] - cy, pts[0][0] - cx)
    for k in range(0, 12):                        # right fillet back up to the start
        t = -0.5 * math.pi + (ang1 + 0.5 * math.pi) * k / 12.0
        pts.append((cx + rc * math.cos(t), cy + rc * math.sin(t)))
    return pts


def build_plate(fr, col, lib):
    from mathutils.geometry import tessellate_polygon
    outer, holes = _plate_loops()
    loops = [outer] + holes

    def pv(p, w):
        return Vector(fr.p(p[0], p[1], w))
    verts, faces = [], []
    off = []
    for lp in loops:
        off.append(len(verts))
        verts += [tuple(pv(p, PLATE_W1)) for p in lp]
    back0 = len(verts)
    for lp in loops:
        verts += [tuple(pv(p, PLATE_W0)) for p in lp]
    tess = tessellate_polygon([[Vector((p[0], p[1], 0.0)) for p in lp] for lp in loops])
    for (a, b, c) in tess:
        faces.append([a, b, c])
    # back face
    for (a, b, c) in tess:
        faces.append([back0 + c, back0 + b, back0 + a])
    # walls
    for k, lp in enumerate(loops):
        n = len(lp)
        for i in range(n):
            j = (i + 1) % n
            a, b = off[k] + i, off[k] + j
            faces.append([a, b, back0 + b, back0 + a])
    ob = M.obj("int_wheel_plate", verts, faces, col, lib["graphite"], smooth=False)
    M.orient(ob.data, lambda c: tuple(fr.A))
    return ob


def _plate_loops():
    """The outer outline and the three holes, as (u, v) lists."""
    loop = d_loop(96)

    def ang(p):
        a = math.degrees(math.atan2(p[1], p[0]))
        return a + 360.0 if a < 0 else a
    lower = sorted([p for p in loop if p[1] < -0.012 and 183.0 < ang(p) < 357.0], key=ang)
    outer = ([(-0.1706, -0.012)] + lower + [(0.1706, -0.012)]
             + [(-u, v) for (u, v) in ARM_L[::-1]] + [(0.0, 0.026)] + list(ARM_L))
    outer = _dedupe(outer)

    def smooth(pts):
        return [(p[0], p[1]) for p in cr_segments(pts, 4, closed=True, alpha=0.5)]
    wl = smooth(WINDOW_L)
    wr = smooth([(-u, v) for (u, v) in WINDOW_L][::-1])
    bt = smooth(BOTTOM)
    return outer, [wl, wr, bt]


def _dedupe(pts, eps=1e-5):
    out = []
    for p in pts:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > eps:
            out.append(p)
    if math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) < eps:
        out.pop()
    return out


def build_chamfer(fr, col, lib):
    """A silver chamfer round each window and the bottom opening."""
    made = []
    outer, holes = _plate_loops()
    for k, h in enumerate(holes):
        path = [fr.p(p[0], p[1], PLATE_W1 + 0.0006) for p in h]
        path.append(path[0])
        made.append(tube("int_wheel_chamfer%d" % k, path, ellipse(0.0017, 0.0010, 6), col,
                         lib["brushed"] if k < 2 else lib["gunmetal"], lateral=tuple(fr.A)))
    return made


# ----------------------------------------------------------------- keys
LEFT_KEYS = [(-0.1446, -0.0077), (-0.1103, -0.0077), (-0.0824, -0.0077)]
LEFT_SMALL = [(-0.1293, 0.0066), (-0.0846, 0.0066)]
ROLLER = (-0.1115, 0.0058)


def build_keys(fr, col, lib):
    made = []
    w = PLATE_W1
    for side, tag in ((1.0, "R"), (-1.0, "L")):
        for j, (u, v) in enumerate(LEFT_KEYS):
            made.append(_key(fr, col, lib, "int_wheel_key%s%d" % (tag, j), -u if side > 0 else u, v, w,
                             0.030, 0.0165))
        for j, (u, v) in enumerate(LEFT_SMALL):
            made.append(_key(fr, col, lib, "int_wheel_small%s%d" % (tag, j), -u if side > 0 else u, v, w,
                             0.014, 0.011))
        made.append(_key(fr, col, lib, "int_wheel_roller%s" % tag, -ROLLER[0] if side > 0 else ROLLER[0],
                         ROLLER[1], w, 0.021, 0.0125, mat="knurl", h=0.0055))
    return made


def _key(fr, col, lib, name, u, v, w, wu, hv, mat="key", h=0.0040):
    """A key cap: a bevelled block standing on the plate (depth h toward the driver, wu across, hv up)."""
    from mathutils import Matrix
    c = Vector(fr.p(u, v, w + 0.5 * h))
    ob = F.box(col, name, (0.0, 0.0, 0.0), (h, wu, hv), lib[mat], r=min(0.0012, 0.3 * h))
    rot = Matrix((tuple(fr.A), tuple(fr.U), tuple(fr.V))).transposed()      # (A, U, V) is right-handed
    ob.matrix_world = Matrix.Translation(c) @ rot.to_4x4()
    return ob


# ------------------------------------------------------------- the logo
def _stroke(fr, col, lib, name, pts, w, r=0.0011):
    path = [fr.p(u, v, w) for (u, v) in pts]
    return tube(name, path, ellipse(r, r * 0.55, 6), col, lib["logo_chrome"], lateral=tuple(fr.A), cap=True)


def build_logo(fr, col, lib, w):
    """The silver BYD wordmark, 74 mm wide and 15 mm tall, three open letters made of stroked paths."""
    made = []
    H = 0.0145
    x0 = -0.034
    sc = H
    # B (reads as a 3): upper and lower bowls open to the left
    def P(pts, dx):
        return [(x0 + dx + a * sc, 0.0116 - 0.5 * H + b * sc) for (a, b) in pts]
    B0 = smooth_path([(0.0, 0.0, 0.0), (0.0, 0.5, 0.0), (0.0, 1.0, 0.0)], 6)
    B1 = smooth_path([(0.0, 1.0, 0.0), (0.55, 1.0, 0.0), (0.82, 0.85, 0.0), (0.82, 0.66, 0.0),
                      (0.55, 0.51, 0.0), (0.0, 0.51, 0.0)], 12)
    B2 = smooth_path([(0.0, 0.51, 0.0), (0.62, 0.49, 0.0), (0.88, 0.34, 0.0), (0.88, 0.15, 0.0),
                      (0.62, 0.0, 0.0), (0.0, 0.0, 0.0)], 12)
    Y1 = smooth_path([(0.0, 1.0, 0.0), (0.22, 0.74, 0.0), (0.43, 0.48, 0.0)], 8)
    Y2 = smooth_path([(0.86, 1.0, 0.0), (0.64, 0.74, 0.0), (0.43, 0.48, 0.0)], 8)
    Y3 = smooth_path([(0.43, 0.48, 0.0), (0.43, 0.24, 0.0), (0.43, 0.0, 0.0)], 6)
    D0 = smooth_path([(0.0, 0.0, 0.0), (0.0, 0.5, 0.0), (0.0, 1.0, 0.0)], 6)
    D1 = smooth_path([(0.0, 1.0, 0.0), (0.45, 1.0, 0.0), (0.82, 0.78, 0.0), (0.88, 0.5, 0.0),
                      (0.82, 0.22, 0.0), (0.45, 0.0, 0.0), (0.0, 0.0, 0.0)], 14)
    dxs = (0.0, 0.0255, 0.0510)
    SX = 1.30
    for nm, strokes, dx in (("B", (B0, B1, B2), dxs[0]), ("Y", (Y1, Y2, Y3), dxs[1]), ("D", (D0, D1), dxs[2])):
        for k, st in enumerate(strokes):
            pts2 = [(x0 + dx + p[0] * sc * SX, 0.0116 - 0.5 * H + p[1] * sc) for p in st]
            made.append(_stroke(fr, col, lib, "int_wheel_byd_%s%d" % (nm, k), pts2, w))
    return made


# ------------------------------------------------------------- stalks
def build_stalks(fr, col, lib):
    made = []
    for side, tag, tip in ((-1.0, "L", 0.012), (1.0, "R", 0.016)):
        path = smooth_path([fr.p(side * 0.040, 0.018, -0.050), fr.p(side * 0.080, 0.034, -0.044),
                            fr.p(side * 0.116, 0.044, -0.036)], 10)
        made.append(tube("int_wheel_stalk" + tag, path, ellipse(0.0092, 0.0074, 10), col, lib["key"],
                         lateral=tuple(fr.V), scale=lambda s: (1.0 - 0.12 * s, 1.0 - 0.12 * s)))
        end = Vector(path[-1])
        made += F.disc(col, "int_wheel_stalkcap" + tag, tuple(end + Vector(fr.U) * side * 0.001),
                       tuple(Vector(fr.U) * side), 0.0072, lib["gunmetal"], dome=0.002, rim=None)
    return made


# --------------------------------------------------------------- build
def build(col, lib):
    fr = ST.WheelFrame(ZI.WHEEL_C, ZI.WHEEL_TILT)
    made = []
    spec = dict(radius=R_CTR, loop=dict(pts=d_loop(72)), flat_bottom=None, flat_top=None,
                section=SECTION, grip_swell=0.05,
                segments=[(0.0, 180.0, "leather_door"), (180.0, 360.0, "leather_door")], marker=None)
    made += ST.rim(fr, spec, col, lib)
    frh = ST.WheelFrame(tuple(Vector(ZI.WHEEL_C) + fr.V * PAD_DV), ZI.WHEEL_TILT)
    pad = dict(hub=dict(w=0.15, h=0.135, sides=16, r_corner=0.0, dome=0.011, depth=0.050,
                        outline=[(p[0], p[1]) for p in cr_segments(PAD, 3, closed=True, alpha=0.5)],
                        pad_role="leather_door", housing_role="graphite"))
    made += ST.hub(frh, pad, col, lib)
    made.append(build_plate(fr, col, lib))
    made += build_chamfer(fr, col, lib)
    made += build_keys(fr, col, lib)
    made += build_logo(frh, col, lib, 0.0330)
    made += ST.column(fr, col, lib)
    made += build_stalks(fr, col, lib)
    return made
