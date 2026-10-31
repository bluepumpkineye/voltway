"""Avatr 06T seats, read from the Misty Purple / Cotton White cabin (blender/reference/avatr-06t/interior):
c3_0001 / c3_0002 / c3_0040 / c3_0041 (the front seats through the open doors), c3_0012 / c3_0013 (the cushion's
front and the leg rest folded out of it), c10_0001 (the cushions from behind, through the solved camera), c3_0019
(the rear bench).

Front: the "zero-gravity" seat. A long, high cushion whose thick rounded front lip houses the leg rest; a near
upright backrest with moderate bolsters; Cotton White Nappa on the cushion and the lower backrest (a perforated
centre panel, smooth bolsters, a seam across the centre where cushion and backrest panels meet); Misty Purple Nappa on
the backrest's top (a yoke over the shoulders) and on a tall headrest standing close above it. A white moulded side
shield carries the dark oval switch panel low on the outboard side.

Rear: three places, all Cotton White, the outer two shaped like the fronts but flatter; purple headrests; a
fold-down armrest panel in the middle place.

The geometry is carkit.interior.seat's sweep (a spine in the seat's x-z plane, a section across it), as seal_seats.
"""
import copy
import math

from mathutils import Matrix, Vector

import cabin_parts as CP
from carkit.geom import Curve
from carkit.interior import fittings as F
from carkit.interior.sweep import Sweep, stitches, grid_mesh, _orient_to

# seat-local metres, origin at the bight (cushion meets backrest), x forward, z up
CUSHION = dict(
    # a long cushion rising to a crest 0.43 m ahead of the bight, then a deep rounded front that hides the leg rest
    spine=[(0.00, 0.00), (0.10, 0.034), (0.24, 0.062), (0.36, 0.080), (0.430, 0.079), (0.463, 0.052),
           (0.478, 0.000), (0.478, -0.085), (0.470, -0.170)],
    half_w=Curve([(0.0, 0.252), (0.5, 0.260), (1.0, 0.252)]),
    bolster=Curve([(0.0, 0.30), (0.25, 0.75), (0.55, 0.80), (0.74, 0.40), (0.84, 0.0), (1.0, 0.0)], mode="pchip"),
    bolster_h=0.034, centre_half=Curve([(0.0, 0.165), (0.6, 0.160), (1.0, 0.150)], mode="pchip"),
    depth=0.130, ns=46)
# the backrest, 15-18 degrees off upright (c3_0001), ending at the shoulders: the headrest is a separate pillow
BACKREST = dict(
    spine=[(0.00, 0.00), (-0.022, 0.090), (-0.068, 0.255), (-0.112, 0.400), (-0.140, 0.480), (-0.154, 0.522)],
    half_w=Curve([(0.0, 0.252), (0.40, 0.262), (0.78, 0.258), (1.0, 0.240)], mode="pchip"),
    bolster=Curve([(0.0, 0.50), (0.30, 0.90), (0.62, 0.80), (0.86, 0.45), (1.0, 0.25)], mode="pchip"),
    bolster_h=0.068,
    centre_half=Curve([(0.0, 0.160), (0.55, 0.155), (1.0, 0.140)], mode="pchip"),
    depth=0.090, ns=46)
YOKE_FROM = 0.74          # backrest spine fraction where the purple top begins (c3_0002: the upper quarter)
REAR_CUSHION = dict(
    spine=[(0.00, 0.00), (0.10, 0.020), (0.24, 0.036), (0.36, 0.044), (0.43, 0.036), (0.46, 0.000),
           (0.468, -0.050), (0.46, -0.110)],
    half_w=Curve([(0.0, 0.232), (0.5, 0.236), (1.0, 0.226)]),
    bolster=Curve([(0.0, 0.2), (0.3, 0.5), (0.6, 0.6), (0.85, 0.3), (1.0, 0.0)], mode="pchip"),
    bolster_h=0.026, centre_half=Curve([(0.0, 0.170), (0.6, 0.160), (1.0, 0.140)], mode="pchip"),
    depth=0.100, ns=36)
REAR_BACKREST = dict(
    spine=[(0.00, 0.00), (-0.030, 0.090), (-0.080, 0.250), (-0.126, 0.390), (-0.160, 0.490), (-0.176, 0.545)],
    half_w=Curve([(0.0, 0.232), (0.5, 0.238), (1.0, 0.228)], mode="pchip"),
    bolster=Curve([(0.0, 0.4), (0.4, 0.8), (0.8, 0.5), (1.0, 0.1)], mode="pchip"),
    bolster_h=0.045, centre_half=Curve([(0.0, 0.175), (0.6, 0.165), (1.0, 0.150)], mode="pchip"),
    depth=0.085, ns=36)

FRONT_COUNTS = [5, 4, 3, 4, 2, 4, 4, 4, 2, 4, 3, 4, 5]     # 14 front points: 13 segments
BACK_COUNTS = [3, 5, 4, 4, 5, 3]


def _section(w, k, bh, c, depth):
    """Front points (13): side foot, side top, crown, crown inner, inner slope, SEAM, centre dish ..., and the back
    (5). The centre panel is columns 5..8."""
    dish = lambda u: 0.004 - 0.010 * (1.0 - (u / max(c, 1e-6)) ** 2)
    front = [(w, -0.10), (w, -0.012), (w - 0.022, 0.050 * k + 0.004), (w - 0.056, bh * k + 0.002),
             (c + 0.030, 0.034 * k + 0.004), (c, 0.004), (0.40 * c, dish(0.40 * c)), (-0.40 * c, dish(0.40 * c)),
             (-c, 0.004), (-(c + 0.030), 0.034 * k + 0.004), (-(w - 0.056), bh * k + 0.002),
             (-(w - 0.022), 0.050 * k + 0.004), (-w, -0.012), (-w, -0.10)]
    back = [(-w + 0.020, -depth), (-0.5 * w, -depth - 0.012), (0.0, -depth - 0.016), (0.5 * w, -depth - 0.012),
            (w - 0.020, -depth)]
    return front + back


def _part(spec, lateral, name, collection, lib, xf, roles, cap_from=None, quality=1.0):
    """roles = (face, crown, centre, shell[, cap]): cap (the purple yoke) covers every panel past cap_from."""
    spine = [xf @ Vector((x, 0.0, z)) for (x, z) in spec["spine"]]
    hw, bol, ch = spec["half_w"], spec["bolster"], spec["centre_half"]

    def section(i, s):
        return _section(hw(s), bol(s), spec["bolster_h"], ch(s), spec["depth"])
    ns = max(18, int(spec["ns"] * quality))
    sw = Sweep([tuple(p) for p in spine], section, ns, FRONT_COUNTS + BACK_COUNTS, lateral=lateral,
               closed_section=True, outward=-1.0)
    col = sw.col
    n_s = len(sw.pts)
    i_cap = None if cap_from is None else int(round((n_s - 1) * cap_from))
    r_face, r_crown, r_centre, r_shell = roles[:4]
    made = []
    for nm, j0, j1, role in (("_FaceL", 0, 2, r_face), ("_CrownL", 2, 5, r_crown), ("_Centre", 5, 8, r_centre),
                             ("_CrownR", 8, 11, r_crown), ("_FaceR", 11, 13, r_face)):
        if i_cap is None:
            made.append(sw.mesh(name + nm, collection, lib[role], j0=col(j0), j1=col(j1)))
        else:
            made.append(sw.mesh(name + nm, collection, lib[role], i1=i_cap, j0=col(j0), j1=col(j1)))
            made.append(sw.mesh(name + nm + "Yoke", collection, lib[roles[4]], i0=i_cap, j0=col(j0), j1=col(j1)))
    for (i0, i1, role, tag) in ((0, i_cap if i_cap is not None else n_s - 1, r_shell, ""),
                                ) + (((i_cap, n_s - 1, roles[4], "Yoke"),) if i_cap is not None else ()):
        rows = sw.rows(j0=col(13), j1=sw.nt - 1)[i0:i1 + 1]
        rows = [r + [sw.pts[i0 + k][0]] for k, r in enumerate(rows)]
        sh = grid_mesh(name + "_Shell" + tag, rows, collection, lib[role])
        ic = len(rows) // 2
        _orient_to(sh, Vector(rows[ic][len(rows[0]) // 2]), -sw.normal(i0 + ic, col(6)))
        made.append(sh)
    # tone-on-tone stitching beside the centre panel's seams and along the crowns
    i0, i1 = int(n_s * 0.05), int(n_s * (0.86 if cap_from is None else cap_from - 0.02))
    for k, tag in ((5, "L"), (8, "R")):
        p, nrm = sw.iso_col(col(k), i0, i1)
        made.append(stitches("%s_Seam%s" % (name, tag), p, nrm, collection, lib["thread_white"],
                             side=(0.0045 if k == 5 else -0.0045)))
    for k, tag in ((2, "L"), (11, "R")):
        p, nrm = sw.iso_col(col(k), i0, i1)
        made.append(stitches("%s_Crown%s" % (name, tag), p, nrm, collection, lib["thread_white"]))
    return made, sw


def _end_cap(collection, mat, sw, name, spine_end, spine_prev):
    """The backrest's open top, closed with a shallow dome."""
    ring = [Vector(p) for p in sw.pts[-1]]
    c0 = sum(ring, Vector()) / len(ring)
    t_end = (Vector(spine_end) - Vector(spine_prev)).normalized()
    rows = []
    for sc, lift in ((1.0, 0.0), (0.85, 0.012), (0.62, 0.021), (0.36, 0.027), (0.12, 0.029), (0.0, 0.0295)):
        rows.append([tuple(c0 + (p - c0) * sc + t_end * lift) for p in ring])
    top = grid_mesh(name + "_Top", rows, collection, mat, wrap_t=True)
    _orient_to(top, c0 + t_end * 0.0295, t_end)
    return top


def seat(collection, lib, origin, name, roles, cushion=None, backrest=None, yaw=0.0, back_k=1.0, cap_from=None,
         quality=1.0):
    xf = Matrix.Translation(Vector(origin)) @ Matrix.Rotation(yaw, 4, 'Z')
    cu, bk = copy.deepcopy(cushion or CUSHION), copy.deepcopy(backrest or BACKREST)
    bk["spine"] = [(x, z * back_k) for (x, z) in bk["spine"]]
    made = []
    parts, cush = _part(cu, (0.0, 1.0, 0.0), name + "_Cushion", collection, lib, xf, roles[:4], quality=quality)
    made += parts
    parts, back = _part(bk, (0.0, -1.0, 0.0), name + "_Back", collection, lib, xf, roles, cap_from=cap_from,
                        quality=quality)
    made += parts
    sp = bk["spine"]
    ox, oy, oz = origin
    made.append(_end_cap(collection, lib[roles[4] if cap_from is not None else roles[1]], back, name + "_Back",
                         (ox + sp[-1][0], oy, oz + sp[-1][1]), (ox + sp[-2][0], oy, oz + sp[-2][1])))
    top = Vector((ox + sp[-1][0], oy, oz + sp[-1][1]))
    lean = math.atan2(sp[-1][0] - sp[-2][0], sp[-1][1] - sp[-2][1])
    return made, top, lean


# ------------------------------------------------------------- front extras
def _blk(col, lib, name, centre, size, role, n, a, r=0.0012):
    """A bevelled block, local x along n (out of the surface), y along a, z = n x a."""
    ob = F.box(col, name, (0.0, 0.0, 0.0), size, lib[role], r=r)
    z = n.cross(a).normalized()
    ob.matrix_world = Matrix.Translation(centre) @ Matrix((tuple(n), tuple(a), tuple(z))).transposed().to_4x4()
    return ob


HEAD_W, HEAD_H, HEAD_T, HEAD_R = 0.272, 0.200, 0.112, 0.060
HEAD_GAP, HEAD_POST_Y = 0.012, 0.070


def build_headrest(col, lib, name, top, lean, w=HEAD_W, h=HEAD_H, t=HEAD_T, r=HEAD_R, gap=HEAD_GAP):
    """The tall purple headrest close above the backrest's dome (c3_0001: a squarish pillow with a soft rim, tilted
    a little forward of the back), on two short posts."""
    k = Vector((math.sin(lean), 0.0, math.cos(lean)))
    nrm = Vector((math.cos(lean), 0.0, -math.sin(lean)))
    centre = top + k * (0.0295 + gap + 0.5 * h) - nrm * (0.5 * t - 0.030)
    made = [CP.pillow(col, name, tuple(centre), w, h, t, r, lib["leather_purple"], 0.75 * lean)]
    p0 = top - k * 0.010 - nrm * (0.5 * t - 0.030)
    mid = 0.5 * (centre + p0)
    n_len = (centre - p0).length
    for i, sy in enumerate((-1.0, 1.0)):
        made.append(F.box(col, "%s_Post%d" % (name, i), (mid.x, top.y + sy * HEAD_POST_Y, mid.z), (0.012, 0.012, n_len),
                          lib["satin_metal"], r=0.003, pitch=lean))
    return made, centre + k * 0.5 * h


def build_side_shield(col, lib, name, origin, side):
    """The white moulded shield along the cushion's outboard side, down to the rails, with the dark oval switch
    panel (c3_0010: a rounded slot, a long seat-base rocker, a backrest rocker and two round keys)."""
    made = []
    x0, y0, z0 = origin
    y_out = y0 + side * 0.262
    rows = []
    for i in range(13):
        x = x0 + 0.02 + 0.44 * i / 12.0
        z_top = z0 + 0.010 + 0.050 * math.sin(math.pi * min(1.0, (x - x0) / 0.46)) ** 0.6
        rows.append([(x, y_out + side * 0.010 * math.sin(math.pi * j / 6.0), z_top - (z_top - (z0 - 0.200)) * j / 6.0)
                     for j in range(7)])
    sh = grid_mesh(name + "_Shield", rows, col, lib["plastic_white"])
    _orient_to(sh, Vector(rows[6][3]), Vector((0.0, side, 0.0)))
    made.append(sh)
    n = Vector((0.0, side, 0.0))
    a = Vector((-side, 0.0, 0.0))
    c = Vector((x0 + 0.215, y_out + side * 0.012, z0 - 0.085))
    made.append(_blk(col, lib, name + "_Panel", c, (0.008, 0.190, 0.056), "piano", n, a, 0.026))
    for kk, (dx, dz, w, h) in enumerate(((-0.060, 0.000, 0.064, 0.012), (-0.002, 0.006, 0.010, 0.032),
                                         (0.032, 0.000, 0.012, 0.022), (0.060, 0.000, 0.012, 0.012))):
        made.append(_blk(col, lib, "%s_Key%d" % (name, kk), c + Vector((dx * -side, 0.0, dz)) + n * 0.0055,
                         (0.006, w, h), "satin_metal", n, a, 0.0035))
    return made


def build_buckle(col, lib, name, origin, side):
    """The belt buckle at the cushion's inboard rear corner: a white stalk, a dark head, a red release."""
    made = []
    x0, y0, z0 = origin
    n = Vector((0.0, -side, 0.0))
    a = Vector((side, 0.0, 0.0))
    c = Vector((x0 + 0.040, y0 - side * 0.252, z0 + 0.090))
    made.append(_blk(col, lib, name + "_Stalk", c - Vector((0.0, 0.0, 0.040)), (0.016, 0.026, 0.100), "plastic_white",
                     n, a, 0.005))
    made.append(_blk(col, lib, name + "_Head", c + Vector((0.0, 0.0, 0.032)), (0.018, 0.034, 0.056), "piano", n, a,
                     0.006))
    made.append(_blk(col, lib, name + "_Button", c + Vector((0.0, 0.0, 0.040)) + n * 0.0095, (0.003, 0.018, 0.022),
                     "button_red", n, a, 0.0012))
    return made


# ---------------------------------------------------------------- the seats
REAR_BACK_K = 0.93
FRONT_ROLES = ("leather_white", "leather_white", "leather_white_perf", "leather_white", "leather_purple")
REAR_ROLES = ("leather_white", "leather_white", "leather_white_perf", "leather_white", "leather_white")


def build_front(col, lib, bight_x, bight_z, ys, floor_z):
    made, tops = [], {}
    for tag, y in (("FL", ys[0]), ("FR", ys[1])):
        side = 1.0 if y > 0 else -1.0
        org = (bight_x, y, bight_z)
        parts, top, lean = seat(col, lib, org, "int_seat_" + tag, FRONT_ROLES, cap_from=YOKE_FROM)
        made += parts
        parts, head_top = build_headrest(col, lib, "int_seat_%s_Head" % tag, top, lean)
        made += parts
        tops[tag] = head_top
        # the pedestal under the cushion: the leg-rest housing hides most of it; dark rails on the floor
        made.append(F.box(col, "int_seat_%s_base" % tag, (bight_x + 0.20, y, 0.5 * (floor_z + bight_z - 0.12)),
                          (0.44, 0.40, bight_z - 0.12 - floor_z), lib["satin"], r=0.03))
        for sy in (-0.17, 0.17):
            made.append(F.box(col, "int_seat_%s_rail%s" % (tag, "L" if sy > 0 else "R"),
                              (bight_x + 0.10, y + sy, floor_z + 0.012), (0.70, 0.032, 0.024), lib["satin"], r=0.006))
        made += build_side_shield(col, lib, "int_seat_%s_side" % tag, org, side)
        made += build_buckle(col, lib, "int_seat_%s_buckle" % tag, org, side)
    return made, tops


def build_rear(col, lib, bight_x, bight_z, y_out, floor_z):
    made = []
    for tag, y in (("RL", y_out), ("RR", -y_out)):
        org = (bight_x, y, bight_z)
        # the backrest 7 % shorter and a low headrest: the roof falls over the rear row (headliner z 1.36 at x -1.43; the
        # first build's headrests came within 1 cm of it)
        parts, top, lean = seat(col, lib, org, "int_seat_" + tag, REAR_ROLES, cushion=REAR_CUSHION,
                                backrest=REAR_BACKREST, back_k=REAR_BACK_K)
        made += parts
        parts, _ = build_headrest(col, lib, "int_seat_%s_Head" % tag, top, lean, w=0.230, h=0.128, t=0.088, r=0.042,
                                  gap=0.010)
        made += parts
    # the centre place: a cushion block and a back carrying the fold-down armrest panel
    xc = bight_x + 0.230
    made.append(F.box(col, "int_seat_RC_Cushion", (xc, 0.0, bight_z + 0.012), (0.470, 0.420, 0.064),
                      lib["leather_white"], r=0.030))
    sp = [(x, z * REAR_BACK_K) for (x, z) in REAR_BACKREST["spine"]]
    top = (bight_x + sp[-1][0], 0.0, bight_z + sp[-1][1])
    lean = math.atan2(sp[-1][0] - sp[0][0], sp[-1][1] - sp[0][1])
    made.append(F.box(col, "int_seat_RC_Back", (bight_x + 0.5 * sp[-1][0] - 0.020, 0.0, bight_z + 0.5 * sp[-1][1]),
                      (0.130, 0.420, sp[-1][1] + 0.030), lib["leather_white"], r=0.030, pitch=lean))
    made.append(F.box(col, "int_seat_RC_Arm", (bight_x + 0.5 * sp[-1][0] + 0.008 - 0.020, 0.0, bight_z + 0.40),
                      (0.020, 0.250, 0.300), lib["leather_white_perf"], r=0.010, pitch=lean))
    made += build_headrest(col, lib, "int_seat_RC_Head", Vector(top), lean, w=0.200, h=0.115, t=0.080, r=0.038,
                           gap=0.010)[0]
    made.append(F.box(col, "int_rear_bench_base", (bight_x + 0.19, 0.0, 0.5 * (floor_z + bight_z - 0.07)),
                      (0.58, 1.26, bight_z - 0.07 - floor_z), lib["leather_white"], r=0.020))
    return made
