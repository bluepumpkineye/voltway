"""SU7 Ultra cabin - hardpoints from the camera-matched press render, built
with carkit.interior.

The reference is Xiaomi's Ultra cabin render (reference/su7-ultra/interior/
ultra_cabin_front.png), solved as camera "cabin_front" in ref_match.py. Read
through that camera (refmatch.on_plane), the key hardpoints are:

    centre screen   centre (0.47, 0.00, 0.985), 16.1" (347 x 217 mm)
    steering wheel  centre (0.39, 0.39, 0.95), 370 mm across the grips
    cluster         (0.63, 0.37, 0.975), a wide slim display on the dash
    dash            lip at (0.60, 0.95); vent slot z 0.89; yellow Nappa band
                    z 0.86 -> 0.77, running door to door
    console         top at z 0.72, carbon panel x 0.23 -> 0.55
    seats           cushion front edge ~(0.20, 0.40, 0.63)

Trim, from the reference photographs: black Alcantara (dash top, door uppers,
headliner, pillars, seat centres), yellow Nappa (dash band, door inserts, seat
bolsters), black Nappa (armrest, dash face), carbon (console panel, wheel top
and bottom), brushed aluminium (switches, lower wheel spoke), chrome piping.

Axes: +X forward, +Y left (the driver's side - China is LHD), +Z up.
"""
import math

import bpy
from mathutils import Vector, Matrix

import su7_surface as S
import su7_panels as PN
from carkit import geom
from carkit import mesh as M
from carkit.interior import cabin as CB
from carkit.interior import materials as IM
from carkit.interior.sweep import Sweep, grid_mesh, tube, ellipse, stitches, piping, smooth_path

COLLECTION = "SU7_Interior"

# ------------------------------------------------------------- hardpoints
FLOOR_Z = 0.320
DRIVER_Y = 0.395
PASS_Y = -0.395

SCREEN_C = (0.470, 0.000, 0.985)
SCREEN_W, SCREEN_H = 0.347, 0.217          # 16.1" 16:10 active area
SCREEN_TILT = math.radians(8.0)            # top leans away from the occupants

WHEEL_C = (0.390, DRIVER_Y, 0.950)
WHEEL_TILT = math.radians(22.0)            # rim plane back from vertical
WHEEL_R = 0.172                            # rim centreline radius

CLUSTER_C = (0.630, 0.370, 0.975)
CLUSTER_W, CLUSTER_H = 0.200, 0.070

DASH_HALF = 0.800                           # dash runs door to door


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


# ------------------------------------------------------------------ dash
# Section in (x, z), top-front at the windscreen, round the lip, down the face
# and forward under it to the firewall. The indices below are the panel
# boundaries: top pad 0-3, face 3-5, vent 5-7, accent band 8-10, lower 10-13.
#
# The first point runs up under the windscreen's base: 17 mm lower it left a
# slot between the pad and the glass, and from the seat you looked through it
# under the hood's rear edge into the cowl.
DASH_SECTION = [
    (0.938, 0.972), (0.760, 0.958), (0.632, 0.956), (0.602, 0.946),
    (0.591, 0.926), (0.588, 0.899), (0.603, 0.890), (0.588, 0.881),
    (0.585, 0.866), (0.571, 0.820), (0.580, 0.774), (0.612, 0.720),
    (0.700, 0.620), (1.000, 0.590),
]
DASH_COUNTS = [10, 7, 3, 3, 4, 2, 2, 2, 6, 6, 4, 5, 5]
DASH_PANELS = [("TopPad", 0, 3, "alcantara"), ("Face", 3, 5, "leather_black"),
               ("Vent", 5, 7, "satin"), ("Band", 8, 10, "leather_accent"),
               ("Lower", 10, 13, "leather_black")]


def dash_section(i, s):
    """The section at spine fraction s (0 = left door, 1 = right door)."""
    y = DASH_HALF * (1.0 - 2.0 * s)
    ay = abs(y)
    # at the ends the face sweeps forward into the doors
    wrap = _smooth((ay - 0.60) / 0.20)
    out = []
    for k, (x, z) in enumerate(DASH_SECTION):
        if k >= 3:
            x += 0.16 * wrap * (1.0 - 0.4 * (k - 3) / 10.0)
        if k == 7 and ay > 0.72:              # the vent slot ends before the doors
            x -= 0.012 * _smooth((ay - 0.72) / 0.05)
        out.append((x, z))
    return out


def build_dash(col, lib):
    made = []
    spine = [(0.0, DASH_HALF - 2 * DASH_HALF * k / 8.0, 0.0) for k in range(9)]
    sw = Sweep(spine, dash_section, 96, DASH_COUNTS, lateral=(1.0, 0.0, 0.0), outward=-1.0)
    for nm, c0, c1, role in DASH_PANELS:
        ob = sw.mesh("int_dash_" + nm, col, lib[role], j0=sw.col(c0), j1=sw.col(c1))
        made.append(ob)
    # chrome piping along the top of the yellow band, grey stitching on the lip
    j = sw.col(8)
    p, n = sw.iso_col(j, lift=0.0012)
    made.append(piping("int_dash_Piping", p, col, lib["chrome"], r=0.0016,
                       lateral=(1.0, 0.0, 0.0)))
    j = sw.col(4)
    p, n = sw.iso_col(j, lift=0.0)
    made.append(stitches("int_dash_Stitch", p, n, col, lib["thread_grey"], side=0.0))
    # ambient light guide, recessed in the vent slot door to door
    p, n = sw.iso_col(sw.col(6), lift=0.0015)
    made.append(piping("int_dash_Ambient", p, col, lib["ambient"], r=0.0017,
                       lateral=(1.0, 0.0, 0.0)))
    return made, sw


# --------------------------------------------------------------- screens
def _slab(name, centre, w, h, depth, r, tilt, col, mat, nseg=6):
    """A rounded-rectangle slab facing -X (toward the occupants), leaning
    back by `tilt` (top further forward)."""
    loop = []
    for cx, cz, a0 in ((w / 2 - r, h / 2 - r, 0.0), (-w / 2 + r, h / 2 - r, 0.5 * math.pi),
                       (-w / 2 + r, -h / 2 + r, math.pi), (w / 2 - r, -h / 2 + r, 1.5 * math.pi)):
        for k in range(nseg + 1):
            a = a0 + 0.5 * math.pi * k / nseg
            loop.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    n = len(loop)
    ct, st = math.cos(tilt), math.sin(tilt)

    def P(u, v, d):
        # u across (world -Y is to the viewer's right), v up the screen, d forward
        x = d * ct + v * st
        z = -d * st + v * ct
        return (centre[0] + x, centre[1] - u, centre[2] + z)
    verts = [P(u, v, 0.0) for (u, v) in loop] + [P(u, v, depth) for (u, v) in loop]
    faces = [list(range(n)), list(range(2 * n - 1, n - 1, -1))]
    faces += [[k, (k + 1) % n, n + (k + 1) % n, n + k] for k in range(n)]
    ob = M.obj(name, verts, faces, col, mat, smooth=False)
    M.orient(ob.data, lambda c: (c[0] - centre[0] - 0.5 * depth, 0.0, 0.0))
    M.bevel(ob, min(0.003, depth * 0.3), 3, 30)
    return ob


def screen_quad(name, centre, w, h, tilt, col, lift=0.0006):
    """`screen_main`: ONE flat quad with a planar UV, facing the occupants.
    The web app mounts the live HMI on it; name, size and facing are a
    contract."""
    ct, st = math.cos(tilt), math.sin(tilt)

    def P(u, v):
        x = -lift * ct + v * st
        z = lift * st + v * ct
        return (centre[0] + x, centre[1] - u, centre[2] + z)
    verts = [P(-w / 2, -h / 2), P(w / 2, -h / 2), P(w / 2, h / 2), P(-w / 2, h / 2)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [[0, 1, 2, 3]])
    me.validate()
    uv = me.uv_layers.new(name="UVMap")
    for i, co in enumerate([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]):
        uv.data[i].uv = co
    me.update()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    M.orient(ob.data, lambda c: (-1.0, 0.0, 0.0))
    return ob


def screen_material():
    m = bpy.data.materials.get("INT_Screen") or bpy.data.materials.new("INT_Screen")
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs["Base Color"].default_value = (0.004, 0.006, 0.010, 1.0)
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["Emission Color"].default_value = (0.10, 0.16, 0.30, 1.0)
    b.inputs["Emission Strength"].default_value = 0.6
    return m


def cluster_image(path=None, w=640, h=224):
    """The 7.1" cluster's resting display, as in the press render: black,
    a yellow ring gauge on the right, a gear and range block on the left.
    Generated pixels (no third-party UI is copied)."""
    import numpy as np
    from carkit.textures import TEX_DIR
    import os
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    img = np.zeros((h, w, 3), np.float32)
    img[..., :] = 0.012 + 0.010 * (1.0 - yy / h)[..., None]
    yellow = np.array([1.0, 0.72, 0.10])
    # ring gauge: a 270 degree arc, open at the bottom
    cx, cy, r = w * 0.66, h * 0.52, h * 0.34
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    ang = np.degrees(np.arctan2(yy - cy, xx - cx)) % 360.0
    arc = (np.abs(d - r) < 3.2) & ~((ang > 45) & (ang < 135))      # image y is down
    img[arc] = yellow
    ticks = (np.abs(d - (r - 11)) < 5) & ~((ang > 45) & (ang < 135)) & ((ang % 22.5) < 1.6)
    img[ticks] = yellow * 0.7
    # needle at rest (lower left), glowing hub
    t = np.clip(((xx - cx) * np.cos(np.radians(135)) + (yy - cy) * np.sin(np.radians(135))) / r, 0, 1)
    px = cx + t * r * np.cos(np.radians(135))
    py = cy + t * r * np.sin(np.radians(135))
    needle = (np.sqrt((xx - px) ** 2 + (yy - py) ** 2) < 2.2) & (t > 0.05) & (t < 0.95)
    img[needle] = np.array([1.0, 0.35, 0.08])
    img[d < 7] = yellow * 0.8
    # left block: a gear box and two bars
    img[(xx > w * 0.14) & (xx < w * 0.20) & (yy > h * 0.40) & (yy < h * 0.60)] = (0.85, 0.85, 0.85)
    img[(xx > w * 0.24) & (xx < w * 0.40) & (np.abs(yy - h * 0.45) < 2.5)] = (0.5, 0.5, 0.5)
    img[(xx > w * 0.24) & (xx < w * 0.34) & (np.abs(yy - h * 0.56) < 2.5)] = yellow * 0.8
    out = path or os.path.join(TEX_DIR, "cluster_su7.png")
    im = bpy.data.images.get("T_Cluster") or bpy.data.images.new("T_Cluster", w, h)
    if tuple(im.size) != (w, h):
        im.scale(w, h)
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = img[::-1]
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = out
    im.file_format = 'PNG'
    im.save()
    return out


def build_screens(col, lib):
    made = []
    bez = 0.0075
    made.append(_slab("int_screen_body", SCREEN_C, SCREEN_W + 2 * bez, SCREEN_H + 2 * bez,
                      0.016, 0.010, SCREEN_TILT, col, lib["piano"]))
    made.append(screen_quad("screen_main", SCREEN_C, SCREEN_W, SCREEN_H, SCREEN_TILT, col))
    made[-1].data.materials.append(screen_material())
    # the mount: a short dark stalk from the screen's back to the dash face
    ct, st = math.cos(SCREEN_TILT), math.sin(SCREEN_TILT)
    top = Vector((SCREEN_C[0] + 0.016 * ct - 0.06 * st, 0.0, SCREEN_C[2] - 0.016 * st - 0.06 * ct))
    base = Vector((0.600, 0.0, 0.905))
    path = smooth_path([tuple(top), tuple(top.lerp(base, 0.5) + Vector((0, 0, -0.01))),
                        tuple(base)], 10)
    made.append(tube("int_screen_stalk", path, [(a * 0.030, b * 0.016) for (a, b) in
                                                ellipse(1.0, 1.0, 12)],
                     col, lib["satin"], lateral=(0.0, 1.0, 0.0)))
    # cluster: a wide slim display in a black housing on the dash top
    tilt = math.radians(24.0)
    made.append(_slab("int_cluster_body", CLUSTER_C, CLUSTER_W + 0.030, CLUSTER_H + 0.026,
                      0.050, 0.010, tilt, col, lib["satin"]))
    cq = screen_quad("screen_cluster", (CLUSTER_C[0] - 0.0015, CLUSTER_C[1], CLUSTER_C[2]),
                     CLUSTER_W, CLUSTER_H, tilt, col)
    cq.data.materials.append(screen_material())
    made.append(cq)
    return made


# -------------------------------------------------------------- the shell
def build_shell(col, lib):
    made = []
    # past both glass headers by 3 cm: with the black glass underlay hidden
    # (the web view from inside), a short headliner showed the painted roof
    made.append(CB.headliner(S.BODY, col, lib["headliner"], PN.X_ROOF_F + 0.030,
                             PN.X_ROOF_R - 0.030, lambda x: S.v_along(x, S.v_rail(x), 0.010),
                             inset=0.040))
    # A-pillars: across from the door glass's front edge to the windscreen's
    # side edge, overlapping each glass by ~1 cm
    # run 2 cm past the header, under the roof rail's front: stopping at the
    # header left a crescent of painted roof at the corner (web capture)
    xs = [PN.X_COWL - 0.03 - (PN.X_COWL - 0.03 - (PN.X_ROOF_F - 0.02)) * k / 24.0
          for k in range(25)]
    made.append(CB.edge_band(
        S.BODY, col, lib["alcantara"], xs,
        lambda x: (x, S.v_along(x, min(PN.V_A(x) - 0.020, PN.V_GT(x)), -0.024)),
        lambda x: (x, S.v_along(x, PN.V_A(x) + 0.020, 0.016)),
        depth=0.010, bulge=0.030, name="int_apillar"))
    # roof rails above the side glass, from the A-pillar top back to the C-pillar
    xs = [PN.X_ROOF_F + 0.05 - (PN.X_ROOF_F + 0.05 - PN.X_QTR_R) * k / 40.0 for k in range(41)]
    made.append(CB.edge_band(
        S.BODY, col, lib["headliner"], xs,
        lambda x: (x, S.v_along(x, PN.V_GLASS_TOP(x), -0.010)),
        lambda x: (x, S.v_along(x, S.v_rail(x), 0.022)),
        depth=0.012, bulge=0.018, name="int_roofrail"))
    # B-pillar: between the two door glasses, belt to rail
    vs = [PN.V_BELT - 0.004 + (PN.V_GT(-0.25) + 0.012 - PN.V_BELT) * k / 20.0 for k in range(21)]
    made.append(CB.edge_band(
        S.BODY, col, lib["alcantara"], vs,
        lambda v: (PN.GB_F(v) + 0.012, v), lambda v: (PN.GB_R(v) - 0.012, v),
        depth=0.012, bulge=0.030, name="int_bpillar"))
    # C-pillar: behind the quarter light, from below the belt to the backlight.
    # An OFFSET of the sail, not a chord: the sail is broad (no fold risk,
    # unlike the A-pillar), and a straight chord cut the corner so far inside
    # that its open front end showed the painted sail from the rear seats.
    xs = [PN.X_QTR_R + 0.02 - (PN.X_QTR_R + 0.02 - (PN.X_BACKLIGHT + 0.03)) * k / 16.0
          for k in range(17)]
    made.append(CB.pillar_trim(
        S.BODY, col, lib["alcantara"], xs, lambda x: PN.V_BELT - 0.05,
        lambda x: PN.V_REARGLASS + 0.012, inset=0.028, bulge=0.018, nt=16,
        name="int_cpillar", overlap=0.010))
    # under the quarter light: from the belt up to the glass's lower edge
    xs = [PN.X_QTR_F + 0.02 - (PN.X_QTR_F + 0.02 - (PN.X_QTR_R + 0.01)) * k / 12.0
          for k in range(13)]
    made.append(CB.edge_band(
        S.BODY, col, lib["alcantara"], xs,
        lambda x: (x, PN.V_BELT - 0.05), lambda x: (x, PN.V_QTR_LOW(x) - 0.004),
        depth=0.030, bulge=0.020, name="int_qtr_lower"))
    # the sail: behind the headliner's rear end, between the roof rail trim and
    # the backlight's side edge, forward of the C-pillar trim
    xs = [PN.X_ROOF_R + 0.040 - (0.040 + PN.X_ROOF_R - PN.X_QTR_R + 0.050) * k / 12.0
          for k in range(13)]
    made.append(CB.edge_band(
        S.BODY, col, lib["headliner"], xs,
        lambda x: (x, S.v_along(x, S.v_rail(x), 0.004)),
        lambda x: (x, S.v_along(x, PN.V_REARGLASS, 0.014)),
        depth=0.030, bulge=0.012, name="int_sail"))
    made += build_roof_fittings(col, lib)
    # floor and sills
    # out to the kick panels (|y| 0.735) forward of the door openings, and up
    # the toe board under the dash's lower edge
    made.append(CB.floor(col, lib["carpet"], -1.55, 0.80, 1.12, FLOOR_Z, 0.62,
                         lambda x: 0.70 + 0.04 * _smooth((x - 0.80) / 0.12), name="int_floor"))
    made.append(CB.sill(col, lib["satin"], -1.28, 0.95, 0.70, 0.86, FLOOR_Z, 0.40,
                        name="int_sill"))
    return made


# ---------------------------------------------------------- steering wheel
def build_wheel(col, lib):
    from carkit.interior import steering as ST
    made, fr = ST.wheel(col, lib, ST.SU7_ULTRA, WHEEL_C, WHEEL_TILT)
    return made


# ----------------------------------------------------------------- seats
FRONT_BIGHT_X, FRONT_BIGHT_Z = -0.240, 0.530
REAR_BIGHT_X, REAR_BIGHT_Z, REAR_Y = -1.130, 0.480, 0.370


def _rear_spec():
    """The rear buckets: the front seat, its backrest 15 % shorter so the
    integrated headrest clears the falling roofline."""
    import copy
    from carkit.interior import seat as SE
    sp = copy.deepcopy(SE.SU7_ULTRA_FRONT)
    sp["backrest"]["spine"] = [(x * 0.95, z * 0.84) for (x, z) in sp["backrest"]["spine"]]
    return sp


def build_seats(col, lib):
    from carkit.interior import seat as SE
    made = []
    for tag, y in (("FL", DRIVER_Y), ("FR", PASS_Y)):
        parts, cush, back = SE.seat(col, lib, SE.SU7_ULTRA_FRONT,
                                    (FRONT_BIGHT_X, y, FRONT_BIGHT_Z), name="int_seat_" + tag)
        made += parts
        made.append(SE.base(col, lib, (FRONT_BIGHT_X, y, FRONT_BIGHT_Z), FLOOR_Z,
                            name="int_seat_%s_base" % tag))
    rear = _rear_spec()
    for tag, y in (("RL", REAR_Y), ("RR", -REAR_Y)):
        parts, cush, back = SE.seat(col, lib, rear, (REAR_BIGHT_X, y, REAR_BIGHT_Z),
                                    name="int_seat_" + tag)
        made += parts
    # the rear centre section between the two buckets, and the bench base
    made.append(_box(col, "int_rear_centre", (REAR_BIGHT_X + 0.20, 0.0, REAR_BIGHT_Z - 0.03),
                     (0.46, 0.20, 0.12), lib["alcantara"], r=0.03))
    made.append(_box(col, "int_rear_centre_back",
                     (REAR_BIGHT_X - 0.16, 0.0, REAR_BIGHT_Z + 0.28), (0.12, 0.20, 0.52),
                     lib["alcantara"], r=0.03, pitch=math.radians(-18)))
    made.append(_box(col, "int_rear_bench_base", (REAR_BIGHT_X + 0.15, 0.0,
                                                  0.5 * (FLOOR_Z + REAR_BIGHT_Z - 0.08)),
                     (0.56, 1.30, REAR_BIGHT_Z - 0.08 - FLOOR_Z), lib["satin"], r=0.02))
    return made


def _box(col, name, c, size, mat, r=0.01, pitch=0.0):
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    pts = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
           (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    cp, sp = math.cos(pitch), math.sin(pitch)
    verts = [(c[0] + x * cp + z * sp, c[1] + y, c[2] - x * sp + z * cp) for (x, y, z) in pts]
    faces = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    ob = M.obj(name, verts, faces, col, mat, smooth=False)
    M.bevel(ob, r, 3, 40)
    return ob


# --------------------------------------------------------------- console
CONSOLE_TOP = 0.722
CONSOLE_HALF = 0.118


def build_console(col, lib):
    made = []

    # the bridge: from the dash back to the armrest, open underneath
    def bridge(i, s):
        h = CONSOLE_HALF
        top = CONSOLE_TOP
        return [(-h, top - 0.135), (-h - 0.003, top - 0.06), (-h + 0.006, top - 0.010),
                (-h + 0.030, top), (0.0, top + 0.002), (h - 0.030, top), (h - 0.006, top - 0.010),
                (h + 0.003, top - 0.06), (h, top - 0.135), (0.06, top - 0.145),
                (-0.06, top - 0.145)]
    sp = [(0.655, 0.0, 0.0), (0.44, 0.0, 0.0), (0.205, 0.0, 0.0)]
    sw = Sweep(sp, bridge, 30, [4, 3, 3, 6, 6, 3, 3, 4, 3, 4, 3], lateral=(0.0, -1.0, 0.0),
               closed_section=True)
    ob = sw.mesh("int_console_bridge", col, lib["leather_black"], full_wrap=True)
    M.orient(ob.data, lambda c: (0.0, c[1], c[2] - (CONSOLE_TOP - 0.07)))
    made.append(ob)

    # the carbon panel with its chrome frame, inset in the bridge top
    x0, x1, hw, r = 0.232, 0.548, 0.100, 0.018
    z = CONSOLE_TOP + 0.0035
    outline = _round_rect_xy(x0, x1, -hw, hw, r)
    cup = _round_rect_xy(0.318, 0.418, -0.092, -0.008, 0.020)
    made.append(_plate_with_hole("int_console_carbon", outline, cup, z, col, lib["carbon"]))
    made.append(tube("int_console_frame", [(x, y, z + 0.0005) for (x, y) in outline] +
                     [(outline[0][0], outline[0][1], z + 0.0005)],
                     ellipse(0.0032, 0.0032, 8), col, lib["chrome"], lateral=(0.0, 0.0, 1.0)))
    made.append(tube("int_console_cup_rim", [(x, y, z + 0.0012) for (x, y) in cup] +
                     [(cup[0][0], cup[0][1], z + 0.0012)],
                     ellipse(0.0030, 0.0030, 8), col, lib["chrome"], lateral=(0.0, 0.0, 1.0)))
    # the cup well
    rings = [[(x, y, z - d) for (x, y) in _shrink(cup, k)] for (d, k) in
             ((0.0, 1.0), (0.012, 0.99), (0.060, 0.95), (0.075, 0.90), (0.078, 0.0))]
    well = grid_mesh("int_console_cup", rings, col, lib["satin"], wrap_t=True)
    M.orient(well.data, lambda c: (0.0, 0.0, 1.0))
    made.append(well)
    # four brushed toggles and a start button down the left side of the panel
    for k in range(4):
        xc = 0.338 + 0.032 * k
        made.append(_box(col, "int_toggle_%d" % k, (xc, 0.052, z + 0.004), (0.012, 0.030, 0.006),
                         lib["brushed"], r=0.002))
        made.append(_box(col, "int_toggle_bezel_%d" % k, (xc, 0.052, z + 0.0012),
                         (0.022, 0.040, 0.003), lib["piano"], r=0.0015))
    made.append(_box(col, "int_start", (0.462, 0.052, z + 0.004), (0.022, 0.034, 0.007),
                     lib["brushed"], r=0.004))
    # the phone tray in front of the panel
    made.append(_box(col, "int_console_tray", (0.600, 0.0, CONSOLE_TOP - 0.004),
                     (0.090, 0.190, 0.012), lib["satin"], r=0.004))

    # the armrest: black Nappa, a split lid, down to the floor
    def arm(i, s):
        h, top = 0.126, CONSOLE_TOP + 0.014
        return [(-h, FLOOR_Z + 0.01), (-h - 0.004, top - 0.14), (-h, top - 0.035),
                (-h + 0.020, top - 0.004), (-0.004, top + 0.004), (0.004, top + 0.004),
                (h - 0.020, top - 0.004), (h, top - 0.035), (h + 0.004, top - 0.14),
                (h, FLOOR_Z + 0.01)]
    sp = [(0.215, 0.0, 0.0), (-0.08, 0.0, 0.0), (-0.375, 0.0, 0.0)]
    sw = Sweep(sp, arm, 36, [8, 8, 4, 6, 1, 6, 4, 8, 8], lateral=(0.0, -1.0, 0.0))
    made.append(sw.mesh("int_armrest_side", col, lib["leather_black"], j0=0, j1=sw.col(3)))
    made.append(sw.mesh("int_armrest_lidL", col, lib["leather_black"], j0=sw.col(3),
                        j1=sw.col(4)))
    made.append(sw.mesh("int_armrest_lidR", col, lib["leather_black"], j0=sw.col(5),
                        j1=sw.col(6)))
    made.append(sw.mesh("int_armrest_sideR", col, lib["leather_black"], j0=sw.col(6),
                        j1=sw.nt - 1))
    # end caps
    for k, i in ((0, 0), (1, len(sw.pts) - 1)):
        ring = sw.pts[i]
        c = tuple(sum(p[q] for p in ring) / len(ring) for q in range(3))
        verts = [c] + list(ring)
        faces = [[0, 1 + j, 2 + j] for j in range(len(ring) - 1)]
        cap = M.obj("int_armrest_cap%d" % k, verts, faces, col, lib["leather_black"])
        M.orient(cap.data, (lambda d: (lambda cc: d))((1.0, 0, 0) if k == 0 else (-1.0, 0, 0)))
        made.append(cap)
    return made


def _round_rect_xy(x0, x1, y0, y1, r, n=6):
    pts = []
    for cx, cy, a0 in ((x1 - r, y1 - r, 0.0), (x0 + r, y1 - r, 0.5 * math.pi),
                       (x0 + r, y0 + r, math.pi), (x1 - r, y0 + r, 1.5 * math.pi)):
        for k in range(n + 1):
            a = a0 + 0.5 * math.pi * k / n
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _shrink(loop, k):
    cx = sum(p[0] for p in loop) / len(loop)
    cy = sum(p[1] for p in loop) / len(loop)
    return [(cx + (x - cx) * k, cy + (y - cy) * k) for (x, y) in loop]


def _inside(p, loop):
    """Point-in-polygon (even-odd) for a 2D loop."""
    x, y = p
    c = False
    n = len(loop)
    for i in range(n):
        (x1, y1), (x2, y2) = loop[i], loop[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def _plate_with_hole(name, outer, hole, z, col, mat, nx=120, ny=64):
    """A flat plate inside `outer` with `hole` removed: a fine grid keeping the
    faces whose centre is inside the outline and outside the hole. The ragged
    edges (< 3 mm) sit under the chrome frame and rim tubes."""
    xs = [p[0] for p in outer]
    ys = [p[1] for p in outer]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    verts = [(x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny, z)
             for i in range(nx + 1) for j in range(ny + 1)]
    faces = []
    for i in range(nx):
        for j in range(ny):
            cx = x0 + (x1 - x0) * (i + 0.5) / nx
            cy = y0 + (y1 - y0) * (j + 0.5) / ny
            if _inside((cx, cy), outer) and not _inside((cx, cy), hole):
                a = i * (ny + 1) + j
                faces.append([a, a + ny + 1, a + ny + 2, a + 1])
    ob = M.obj(name, verts, faces, col, mat, smooth=False)
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(ob.data)
    bm.free()
    M.orient(ob.data, lambda c: (0.0, 0.0, 1.0))
    return ob


# ------------------------------------------------------------ door cards
def _belt_z(x, v=None):
    return S.section_v(x, PN.V_BELT if v is None else v)[1]


def build_doors(col, lib):
    from carkit.geom import Curve
    from carkit.interior.door import DoorCard
    made = []
    th = Curve([(0.38, 0.095), (0.55, 0.125), (0.70, 0.150), (0.80, 0.132), (0.88, 0.098),
                (0.96, 0.070)], mode="pchip")
    # The yellow insert continues the dash band into the door and DESCENDS
    # toward the rear into the armrest; the black Alcantara upper door grows
    # taller behind it.
    ins_top = Curve([(-0.14, 0.742), (0.05, 0.748), (0.25, 0.776), (0.45, 0.815),
                     (0.65, 0.848), (0.97, 0.866)], mode="pchip")
    ins_bot = Curve([(-0.14, 0.640), (0.05, 0.625), (0.25, 0.630), (0.45, 0.665),
                     (0.70, 0.725), (0.97, 0.772)], mode="pchip")
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        # the rear edge runs to within 6 mm of the B-pillar shut line; a seal
        # strip (build_closures) fills the slot between front and rear cards
        dc = DoorCard(S.BODY, lambda z: PN._DOOR_F_EDGE(z) - 0.022,
                      lambda z: PN.X_BPILLAR_F + 0.006, 0.40, _belt_z, th,
                      v_top=PN.V_BELT, side=side)
        pre = "int_door_%s_" % tag
        xr = lambda z: PN.X_BPILLAR_F + 0.006
        xf = lambda z: PN._DOOR_F_EDGE(z) - 0.022
        made.append(dc.belt_cap(pre + "Belt", col, lib["satin"], xr(0.95), xf(0.95), _belt_z,
                                mirror=False))
        made.append(dc.carrier(pre + "Carrier", col, lib["satin"], lambda x: 0.40,
                               lambda x: _belt_z(x) - 0.002, x0=xr, x1=xf, mirror=False))
        made.append(dc.band(pre + "Lower", col, lib["leather_black"], lambda x: 0.40,
                            ins_bot, x0=xr, x1=xf, mirror=False))
        made.append(dc.band(pre + "Insert", col, lib["leather_accent"], ins_bot, ins_top,
                            proud=0.008, x0=xr, x1=xf, nz=14, mirror=False))
        made.append(dc.band(pre + "Upper", col, lib["alcantara"], ins_top,
                            lambda x: _belt_z(x) - 0.032, x0=xr, x1=xf, mirror=False))
        made.append(dc.band(pre + "Rail", col, lib["leather_black"],
                            lambda x: _belt_z(x) - 0.032, lambda x: _belt_z(x) - 0.002,
                            proud=-0.004, x0=xr, x1=xf, nz=6, edge_round=0.006, mirror=False))
        # chrome piping on the insert's top edge
        pts = dc.curve([(x, ins_top(x)) for x in [0.95 - 1.07 * k / 20.0 for k in range(21)]],
                       proud=0.0095)
        made.append(piping(pre + "Piping", pts, col, lib["chrome"], r=0.0016,
                           lateral=(0.0, 0.0, 1.0)))
        # ambient light guide in the seam under the rail, continuing the dash's
        pts = dc.curve([(x, _belt_z(x) - 0.032) for x in [0.90 - 1.03 * k / 24.0
                                                          for k in range(25)]], proud=0.002)
        made.append(piping(pre + "Ambient", pts, col, lib["ambient"], r=0.0017,
                           lateral=(0.0, 0.0, 1.0)))
        made.append(dc.armrest(pre + "Armrest", col, lib["leather_accent"], -0.10, 0.46, 0.735,
                               width=0.066, height=0.052, mirror=False))
        # the grab handle rising from the armrest front to the insert top
        a = Vector(dc.point(0.40, 0.735, 0.030))
        b = Vector(dc.point(0.55, 0.842, 0.012))
        mid = a.lerp(b, 0.5) + Vector((0.0, -side * 0.028, 0.012))
        path = smooth_path([tuple(a), tuple(mid), tuple(b)], 16)
        made.append(tube(pre + "Handle", path, [(p[0] * 0.013, p[1] * 0.011) for p in
                                                 ellipse(1.0, 1.0, 12)],
                         col, lib["leather_accent"], lateral=(0.0, 1.0, 0.0)))
        # switch pod lying on the armrest top, carbon strip and speaker
        yc = dc.skin_y(0.30, 0.735) - th(0.735) - 0.034      # over the armrest's middle
        made.append(_box(col, pre + "Switches", (0.300, side * yc, 0.7385),
                         (0.150, 0.046, 0.008), lib["piano"], r=0.003))
        for k in range(4):
            made.append(_box(col, pre + "Switch%d" % k, (0.245 + 0.036 * k, side * yc, 0.7435),
                             (0.024, 0.020, 0.004), lib["satin"], r=0.0015))
        made.append(dc.band(pre + "Carbon", col, lib["carbon"],
                            lambda x: 0.872 + 0.014 * (x - 0.40) / 0.48,
                            lambda x: 0.890 + 0.014 * (x - 0.40) / 0.48, proud=0.002,
                            x0=lambda z: 0.40, x1=lambda z: 0.88, nx=24, nz=3, mirror=False))
        made.append(dc.band(pre + "Speaker", col, lib["speaker"], lambda x: 0.47,
                            lambda x: 0.58, proud=0.003, x0=lambda z: 0.46,
                            x1=lambda z: 0.72, nx=16, nz=6, mirror=False))
    made += build_rear_doors(col, lib)
    return made


# Rear doors, from the collage's rear-seat photograph: black cards, a yellow
# Nappa armrest with a thin yellow line above it, black Alcantara between.
def _rear_top_z(x):
    return S.section_v(x, PN.V_DOOR_R_TOP(x))[1]


def rear_card(side):
    from carkit.geom import Curve
    from carkit.interior.door import DoorCard
    th = Curve([(0.38, 0.075), (0.55, 0.090), (0.70, 0.100), (0.82, 0.092), (0.92, 0.076),
                (1.06, 0.060)], mode="pchip")
    return DoorCard(S.BODY, lambda z: PN.X_BPILLAR_F - 0.006,
                    lambda z: PN._DOOR_R_EDGE(z) + 0.006, 0.40, _rear_top_z, th,
                    v_top=PN.V_BELT + 0.10, side=side)


def build_rear_doors(col, lib):
    made = []
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        dc = rear_card(side)
        pre = "int_rdoor_%s_" % tag
        xr, xf = dc.xr, dc.xf
        line = lambda x: 0.838 + 0.010 * (x + 0.16) / -1.0
        made.append(dc.band(pre + "Lower", col, lib["leather_black"], lambda x: 0.40,
                            lambda x: 0.645, x0=xr, x1=xf, mirror=False))
        made.append(dc.band(pre + "Insert", col, lib["alcantara"], lambda x: 0.645, line,
                            proud=0.006, x0=xr, x1=xf, nz=12, mirror=False))
        made.append(dc.band(pre + "Upper", col, lib["leather_black"], line,
                            lambda x: _rear_top_z(x) - 0.032, x0=xr, x1=xf, nz=6,
                            mirror=False))
        made.append(dc.band(pre + "Rail", col, lib["leather_black"],
                            lambda x: _rear_top_z(x) - 0.032, lambda x: _rear_top_z(x) - 0.002,
                            proud=-0.004, x0=xr, x1=xf, nz=6, edge_round=0.006, mirror=False))
        made.append(dc.belt_cap(pre + "Belt", col, lib["satin"], xr(0.95) + 0.004,
                                xf(0.95), _rear_top_z, mirror=False))
        made.append(dc.carrier(pre + "Carrier", col, lib["satin"], lambda x: 0.40,
                               lambda x: _rear_top_z(x) - 0.002, x0=xr, x1=xf, mirror=False))
        pts = dc.curve([(x, line(x)) for x in [-0.20 - 0.94 * k / 20.0 for k in range(21)]],
                       proud=0.0075)
        made.append(piping(pre + "Line", pts, col, lib["leather_accent"], r=0.0022,
                           lateral=(0.0, 0.0, 1.0)))
        pts = dc.curve([(x, _rear_top_z(x) - 0.032) for x in [-0.20 - 0.96 * k / 24.0
                                                              for k in range(25)]], proud=0.002)
        made.append(piping(pre + "Ambient", pts, col, lib["ambient"], r=0.0017,
                           lateral=(0.0, 0.0, 1.0)))
        made.append(dc.armrest(pre + "Armrest", col, lib["leather_accent"], -1.02, -0.36, 0.708,
                               width=0.060, height=0.046, mirror=False))
        made.append(dc.band(pre + "Speaker", col, lib["speaker"], lambda x: 0.47,
                            lambda x: 0.57, proud=0.003, x0=lambda z: -0.56,
                            x1=lambda z: -0.30, nx=14, nz=6, mirror=False))
        # pull cup under the armrest's front end
        a = Vector(dc.point(-0.46, 0.708, 0.024))
        b = Vector(dc.point(-0.34, 0.760, 0.006))
        mid = a.lerp(b, 0.5) + Vector((0.0, -side * 0.020, 0.006))
        made.append(tube(pre + "Handle", smooth_path([tuple(a), tuple(mid), tuple(b)], 12),
                         [(p[0] * 0.011, p[1] * 0.010) for p in ellipse(1.0, 1.0, 12)],
                         col, lib["leather_accent"], lateral=(0.0, 1.0, 0.0)))
    return made


# ------------------------------------------------------ closing trims
def build_closures(col, lib):
    """Everything that stops the painted body showing from inside: B-pillar
    seals, footwell kick panels, the rear wheelhouse trims and the parcel
    shelf. Found with the magenta leak render (docs/3d-pipeline.md)."""
    made = []
    vh = PN.V_BELT + 0.10
    # B-pillar: a black seal behind the 12 mm slot between the door cards
    xs = [PN.X_BPILLAR_F - 0.030 + 0.060 * k / 6.0 for k in range(7)]
    rows = []
    for x in xs:
        rows.append([(x, CB.skin_offset_y(S.BODY, x, z, 0.030, vh), z)
                     for z in [0.40 + (_belt_z(x) - 0.40) * k / 12.0 for k in range(13)]])
    sealx = grid_mesh("int_bpillar_seal", rows, col, lib["satin"])
    M.orient(sealx.data, lambda c: (0.0, -1.0, 0.0))
    M.mirror_y(sealx)
    made.append(sealx)

    # footwell kick panels: the side walls forward of the door opening, from
    # the floor up into the dash, and the face closing the door opening's
    # front edge
    yk = 0.735
    made.append(CB.wall(col, lib["leather_black"],
                        [(0.962 + (1.26 - 0.962) * k / 12.0, yk) for k in range(13)],
                        lambda x, y: FLOOR_Z, lambda x, y: 0.80, name="int_kick",
                        facing=(0.0, -1.0, 0.0)))
    # outboard of the dash's end it rises to the belt, closing the slot in
    # front of the door card; inboard it stops inside the dash
    made.append(CB.wall(col, lib["leather_black"],
                        [(0.962, yk + (0.875 - yk) * k / 10.0) for k in range(11)],
                        lambda x, y: FLOOR_Z,
                        lambda x, y: 0.84 + 0.15 * _smooth((y - 0.795) / 0.025),
                        name="int_kick_front", facing=(-1.0, 0.0, 0.0)))

    # rear wheelhouse and quarter trims, closing out to the rear door card
    rc = rear_card(1.0)
    made += CB.wheelhouse_trim(
        S.BODY, col, lib["leather_black"], lambda z: PN._DOOR_R_EDGE(z) - 0.002, -1.62,
        FLOOR_Z + 0.02, 0.700, 0.800, 0.975, 0.062, vh, name="int_quarter",
        close_to=lambda z: rc.skin_y(PN._DOOR_R_EDGE(z), z) - rc.th(z) + 0.010)

    # parcel shelf: from behind the rear seat backs to the backlight's base
    pts = []
    for k in range(13):
        x = -1.38 - 0.545 * k / 12.0
        pts.append((x, min(1.028 + 0.066 * (k / 12.0) ** 1.4, S.Z_ROOF(x) - 0.007)))
    made.append(CB.bulkhead(col, lib["alcantara"], pts,
                            lambda x, z: CB.skin_offset_y(S.BODY, x, z, 0.075, 0.99),
                            name="int_parcel_shelf", facing=(0.0, 0.0, 1.0)))
    # the wall behind the rear seat backs, floor to shelf (the boot is behind it)
    made.append(CB.bulkhead(col, lib["satin"],
                            [(-1.525, FLOOR_Z + (1.034 - FLOOR_Z) * k / 10.0) for k in range(11)],
                            lambda x, z: 0.705 if z < 0.80 else
                            CB.skin_offset_y(S.BODY, x, z, 0.075, vh),
                            name="int_rear_bulkhead", facing=(1.0, 0.0, 0.0)))
    return made


# ----------------------------------------------------------------- pedals
def build_pedals(col, lib):
    """Brushed pedals with rubber strips: brake (wide) and accelerator, on the
    toe board - both visible under the wheel in the press render."""
    made = []
    # the toe board rises forward at ~52 degrees; a pad lying along it has its
    # long axis a = (sin 38, 0, cos 38) and faces the driver along n
    p = math.radians(38.0)
    a = Vector((math.sin(p), 0.0, math.cos(p)))
    n = Vector((-math.cos(p), 0.0, math.sin(p)))
    for name, y, x, z, w, h in (("brake", DRIVER_Y + 0.02, 0.850, 0.470, 0.100, 0.075),
                                ("accel", DRIVER_Y - 0.140, 0.870, 0.430, 0.058, 0.190)):
        c = Vector((x, y, z))
        made.append(_box(col, "int_pedal_" + name, tuple(c), (0.010, w, h), lib["brushed"],
                         r=0.003, pitch=p))
        for k in range(3):
            q = c + n * 0.006 + a * ((k - 1) * h * 0.28)
            made.append(_box(col, "int_pedal_%s_strip%d" % (name, k), tuple(q),
                             (0.004, w * 0.82, 0.008), lib["rubber"], r=0.0015, pitch=p))
    return made


# ---------------------------------------------------------- roof fittings
MIRROR_C = (0.330, 0.0, 1.298)        # frameless rear-view mirror, from the photo


def build_roof_fittings(col, lib):
    made = []
    # the frameless mirror: a thin rounded slab, glass toward the driver,
    # hung from the header on a short stem
    w, h, t = 0.252, 0.066, 0.016
    slab = _round_slab(col, "int_rvmirror", MIRROR_C, w, h, t, 0.024, lib["piano"],
                       tilt=math.radians(8.0))
    made.append(slab)
    # a mirror, but a dim one: at full chrome it showed the overhead softbox
    # as a white card, where the press render's mirror reads dark
    mg = bpy.data.materials.get("INT_Mirror") or bpy.data.materials.new("INT_Mirror")
    mg.use_nodes = True
    bm = next(n for n in mg.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bm.inputs["Base Color"].default_value = (0.30, 0.31, 0.32, 1.0)
    bm.inputs["Metallic"].default_value = 1.0
    bm.inputs["Roughness"].default_value = 0.05
    made.append(_round_slab(col, "int_rvmirror_glass",
                            (MIRROR_C[0] - t * 0.5 - 0.0008, 0.0, MIRROR_C[2]), w - 0.006,
                            h - 0.006, 0.0008, 0.021, mg, tilt=math.radians(8.0)))
    zr = S.Z_ROOF(MIRROR_C[0] + 0.03) - 0.045
    stem = smooth_path([(MIRROR_C[0] + 0.02, 0.0, MIRROR_C[2] + 0.02),
                        (MIRROR_C[0] + 0.035, 0.0, 0.5 * (MIRROR_C[2] + zr) + 0.01),
                        (MIRROR_C[0] + 0.04, 0.0, zr)], 8)
    made.append(tube("int_rvmirror_stem", stem, ellipse(0.011, 0.008, 10), col, lib["satin"],
                     lateral=(0.0, 1.0, 0.0)))
    # overhead console just behind the windscreen header - small and shallow:
    # the camera sits at headliner height, so anything hanging from the roof
    # near it looms huge
    xs = [0.225 - 0.15 * k / 10.0 for k in range(11)]
    rows = []
    for x in xs:
        zr = S.Z_ROOF(x) - 0.041
        rows.append([(x, 0.12 * (1 - 2 * j / 10.0), zr - 0.014 * math.sin(math.pi * j / 10.0) ** 0.5)
                     for j in range(11)])
    oc = grid_mesh("int_overhead", rows, col, lib["satin"])
    M.orient(oc.data, lambda c: (0.0, 0.0, -1.0))
    made.append(oc)
    for k, yy in enumerate((0.05, 0.0, -0.05)):
        made.append(_box(col, "int_overhead_btn%d" % k, (0.15, yy, S.Z_ROOF(0.15) - 0.056),
                         (0.016, 0.024, 0.003), lib["chrome"], r=0.0012))
    # sun visors, folded flat against the headliner either side
    for side in (1.0, -1.0):
        rows = []
        for i in range(9):
            x = 0.222 - 0.165 * i / 8.0
            zr = S.Z_ROOF(x) + S.Z_CREST(x) * 0.3 - 0.044
            rows.append([(x, side * (0.150 + 0.40 * j / 8.0), zr - 0.002 * math.sin(math.pi * j / 8))
                         for j in range(9)])
        vz = grid_mesh("int_visor_%s" % ("L" if side > 0 else "R"), rows, col, lib["headliner"])
        M.orient(vz.data, lambda c: (0.0, 0.0, -1.0))
        M.solidify(vz, 0.010, 1.0)
        M.bevel(vz, 0.004, 2, 40)
        made.append(vz)
    return made


def _round_slab(col, name, c, w, h, t, r, mat, tilt=0.0):
    loop = _round_rect_xy(-w / 2, w / 2, -h / 2, h / 2, r)
    ct, st = math.cos(tilt), math.sin(tilt)
    verts = []
    for d in (-t / 2, t / 2):
        for (u, v) in loop:
            verts.append((c[0] + d * ct + v * st, c[1] - u, c[2] - d * st + v * ct))
    n = len(loop)
    faces = [list(range(n)), list(range(2 * n - 1, n - 1, -1))]
    faces += [[k, (k + 1) % n, n + (k + 1) % n, n + k] for k in range(n)]
    ob = M.obj(name, verts, faces, col, mat, smooth=False)
    M.orient(ob.data, lambda q: (q[0] - c[0], 0.0, 0.0))
    return ob


# ------------------------------------------------------------- lighting
def cabin_lights(col):
    """The cabin rig for renders: a soft overhead box just under the
    headliner and a front fill over the dash, both invisible to the camera
    but seen in reflections, plus faint cool light through the side glass.

    Measured against the press render: its "blacks" are lifted cool greys
    (dash face sRGB 54/57/66, carpet 44/48/54), which is soft light from
    above, not light through the windows - windows alone left the lower cabin
    at 5/3/1 and put a hard stripe on the dash lip.
    """
    made = []
    # Powers calibrated against the press render's patch values (a first rig
    # at 10x these read as a white clay render: linear ratio 0.09).
    specs = [
        # name, location, aim, size, power, colour
        ("int_L_Roof", (-0.15, 0.0, 1.30), (-0.15, 0.0, 0.40), (1.7, 1.25), 10.0,
         (0.90, 0.94, 1.00)),
        # from behind and above the viewer: the dash face and console top in
        # the press render are lit from the camera's side
        ("int_L_Back", (-1.05, 0.0, 1.22), (0.60, 0.0, 0.80), (1.3, 0.5), 7.0,
         (0.95, 0.97, 1.00)),
        ("int_L_Left", (0.05, 1.45, 1.20), (0.05, 0.0, 0.75), (2.2, 0.6), 2.5,
         (0.85, 0.90, 1.00)),
        ("int_L_Right", (0.05, -1.45, 1.20), (0.05, 0.0, 0.75), (2.2, 0.6), 2.5,
         (0.85, 0.90, 1.00)),
    ]
    for name, loc, aim, size, power, colour in specs:
        d = bpy.data.lights.new(name, 'AREA')
        d.shape = 'RECTANGLE'
        d.size, d.size_y = size
        d.energy = power
        d.color = colour
        ob = bpy.data.objects.new(name, d)
        col.objects.link(ob)
        ob.location = loc
        v = Vector(aim) - Vector(loc)
        ob.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
        ob.visible_camera = False
        # The light behind the viewer must not show in the rear-view mirror
        # and the screens, which face the camera: it read as a white card.
        if name == "int_L_Back":
            ob.visible_glossy = False
        made.append(ob)
    return made


def main(lights=True):
    col = bpy.data.collections.get(COLLECTION)
    if col:
        for o in list(col.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(col)
    col = bpy.data.collections.new(COLLECTION)
    bpy.context.scene.collection.children.link(col)
    carbon = bpy.data.materials.get("M_Carbon")
    lib = IM.build_library(carbon=carbon)
    build_shell(col, lib)
    dash, _ = build_dash(col, lib)
    build_screens(col, lib)
    build_wheel(col, lib)
    build_seats(col, lib)
    build_console(col, lib)
    build_doors(col, lib)
    build_closures(col, lib)
    build_pedals(col, lib)
    if lights:
        cabin_lights(col)
    assert bpy.data.objects.get("screen_main"), "screen_main is the HMI anchor"
    n = len([o for o in col.objects if o.type == 'MESH'])
    print("interior: %d meshes" % n)
    return col
