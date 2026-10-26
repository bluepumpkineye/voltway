"""BYD Seal seats, read from c0086 / c0095 / c0121 (the open door), d0126 (down the cabin), c0198 / c0199 (rear).

Front: a bucket with a near-upright backrest to shoulder height and an ordinary headrest on two posts above it.
ORANGE leather over the centre and the bolster crowns, BLACK leather on the sides, shells and the cushion's side
faces. The centre is pressed into five pleats that fan out toward the seat's front and bottom (they converge
up the backrest and fade out at its top), each seam stitched tone-on-tone; the pleat crowns carry a
field of fine perforations. The oval adjuster panel sits low on the outboard side of the cushion.
(The first build ran the backrest into an integrated headrest with an oval window; the owner asked for a
standard headrest instead, 2026-10-26.)

Rear: a three-place bench, all orange, the outer places pleated and perforated like the fronts', a fold-down
armrest panel in the middle, three separate headrests.

The geometry is carkit.interior.seat's sweep (a spine in the seat's x-z plane and a section across it), with a
pleated centre in the section.
"""
import copy
import math

from mathutils import Matrix, Vector

import seal_interior as ZI
import cabin_parts as CP
from carkit import mesh as M
from carkit.geom import Curve
from carkit.interior import fittings as F
from carkit.interior.sweep import Sweep, stitches, grid_mesh, _orient_to, tube, ellipse, smooth_path

N_PLEAT = 5

CUSHION = dict(
    spine=[(0.00, 0.00), (0.09, 0.028), (0.23, 0.054), (0.33, 0.068), (0.385, 0.060), (0.408, 0.022),
           (0.414, -0.045), (0.408, -0.115)],
    half_w=Curve([(0.0, 0.222), (0.5, 0.226), (1.0, 0.216)]),
    bolster=Curve([(0.0, 0.35), (0.25, 0.85), (0.55, 1.0), (0.78, 0.55), (0.88, 0.0), (1.0, 0.0)], mode="pchip"),
    bolster_h=0.046, centre_half=Curve([(0.0, 0.150), (0.6, 0.140), (1.0, 0.125)], mode="pchip"),
    depth=0.125, ns=40)
# the backrest, nearly upright (the photographs show it at 5 to 10 degrees), ending at the shoulders: the
# headrest is a separate pillow on two posts (build_front)
BACKREST = dict(
    spine=[(0.00, 0.00), (-0.020, 0.090), (-0.050, 0.265), (-0.076, 0.420), (-0.0895, 0.520)],
    half_w=Curve([(0.0, 0.226), (0.42, 0.236), (0.80, 0.226), (1.0, 0.212)], mode="pchip"),
    bolster=Curve([(0.0, 0.55), (0.30, 1.0), (0.62, 0.72), (0.88, 0.30), (1.0, 0.12)], mode="pchip"),
    bolster_h=0.075,
    centre_half=Curve([(0.0, 0.150), (0.55, 0.145), (1.0, 0.130)], mode="pchip"),
    depth=0.080, ns=40)
# the rear bench's outer places: a deeper, more reclined back, a longer flatter cushion
REAR_CUSHION = dict(
    spine=[(0.00, 0.00), (0.10, 0.020), (0.24, 0.036), (0.36, 0.044), (0.43, 0.036), (0.46, 0.000),
           (0.468, -0.050), (0.46, -0.110)],
    half_w=Curve([(0.0, 0.232), (0.5, 0.236), (1.0, 0.226)]),
    bolster=Curve([(0.0, 0.2), (0.3, 0.5), (0.6, 0.6), (0.85, 0.3), (1.0, 0.0)], mode="pchip"),
    bolster_h=0.030, centre_half=Curve([(0.0, 0.170), (0.6, 0.160), (1.0, 0.140)], mode="pchip"),
    depth=0.100, ns=36)
REAR_BACKREST = dict(
    spine=[(0.00, 0.00), (-0.030, 0.090), (-0.080, 0.250), (-0.126, 0.390), (-0.160, 0.490), (-0.184, 0.570),
           (-0.196, 0.615)],
    half_w=Curve([(0.0, 0.232), (0.5, 0.238), (1.0, 0.230)], mode="pchip"),
    bolster=Curve([(0.0, 0.4), (0.4, 0.8), (0.8, 0.5), (1.0, 0.1)], mode="pchip"),
    bolster_h=0.050, centre_half=Curve([(0.0, 0.175), (0.6, 0.165), (1.0, 0.150)], mode="pchip"),
    depth=0.085, ns=36)


def counts(npl):
    return [5, 4, 3, 4, 2] + [2, 2] * npl + [2, 4, 3, 4, 5], [3, 5, 4, 4, 5, 3]


def _dish(u, c):
    """The centre panel's base height: a shallow dish, 0.004 at the seams, -0.007 on the centreline."""
    return 0.004 - 0.011 * (1.0 - (u / max(c, 1e-6)) ** 2)


def _section(w, k, bh, c, depth, pa=0.0085, npl=N_PLEAT):
    pts = [(w, -0.10), (w, -0.012), (w - 0.020, 0.050 * k + 0.004), (w - 0.052, bh * k),
           (c + 0.030, 0.035 * k + 0.004), (c, 0.004)]
    for p in range(npl):
        u0 = c - 2.0 * c * p / npl
        u1 = c - 2.0 * c * (p + 1) / npl
        um = 0.5 * (u0 + u1)
        pts.append((um, _dish(um, c) + pa))
        pts.append((u1, _dish(u1, c) - 0.0035 * (pa / 0.0085) if p < npl - 1 else 0.004))
    pts += [(-(c + 0.030), 0.035 * k + 0.004), (-(w - 0.052), bh * k), (-(w - 0.020), 0.050 * k + 0.004),
            (-w, -0.012), (-w, -0.10)]
    back = [(-w + 0.020, -depth), (-0.5 * w, -depth - 0.012), (0.0, -depth - 0.016), (0.5 * w, -depth - 0.012),
            (w - 0.020, -depth)]
    return pts + back


def _part(spec, lateral, name, collection, lib, xf, quality=1.0, sc=1.0, npl=N_PLEAT, roles=None, fade=False):
    roles = roles or ("leather_black", "leather_seat", "leather_perf", "leather_black")
    spine = [xf @ Vector((x, 0.0, z)) for (x, z) in spec["spine"]]
    hw, bol, ch = spec["half_w"], spec["bolster"], spec["centre_half"]

    def section(i, s):
        pa = 0.0085 * (1.0 - 0.85 * CP.smooth((s - fade) / 0.10)) if fade else 0.0085
        return _section(hw(s) * sc, bol(s), spec["bolster_h"], ch(s) * sc, spec["depth"], pa, npl)
    cf, cb = counts(npl)
    ns = max(18, int(spec["ns"] * quality))
    sw = Sweep([tuple(p) for p in spine], section, ns, cf + cb, lateral=lateral, closed_section=True, outward=-1.0)
    col = sw.col
    made = []
    nf = len(cf)
    c_a, c_b = 5, 5 + 2 * npl                    # SEAM_L .. SEAM_R (control-point indices)
    last = nf                                   # the last front control point (the side foot)
    r_face, r_crown, r_centre, r_shell = roles
    for nm, j0, j1, role in (("_FaceL", 0, 2, r_face), ("_CrownL", 2, c_a, r_crown),
                             ("_Centre", c_a, c_b, r_centre), ("_CrownR", c_b, c_b + 3, r_crown),
                             ("_FaceR", c_b + 3, last, r_face)):
        made.append(sw.mesh(name + nm, collection, lib[role], j0=col(j0), j1=col(j1)))
    rows = sw.rows(j0=col(last), j1=sw.nt - 1)
    rows = [r + [sw.pts[i][0]] for i, r in enumerate(rows)]
    sh = grid_mesh(name + "_Shell", rows, collection, lib[r_shell])
    ic = len(rows) // 2
    _orient_to(sh, Vector(rows[ic][len(rows[0]) // 2]), -sw.normal(ic, col(c_a + npl)))
    made.append(sh)
    # tone-on-tone stitching on every pleat seam, light grey stitching on the orange/black boundary
    n_s = len(sw.pts)
    i0, i1 = int(n_s * 0.06), int(n_s * 0.86)
    for q in range(1, npl):
        p, nrm = sw.iso_col(col(c_a + 2 * q), i0, i1)
        made.append(stitches("%s_Seam%d" % (name, q), p, nrm, collection, lib["thread"]))
    if roles[0] != roles[1]:
        for k, tag in ((2, "L"), (c_b + 3, "R")):         # the black / orange boundary on each crown
            p, nrm = sw.iso_col(col(k), i0, i1)
            made.append(stitches("%s_Edge%s" % (name, tag), p, nrm, collection, lib["thread_light"],
                                 side=0.0035))
    return made, sw


def seat_spec():
    return dict(cushion=copy.deepcopy(CUSHION), backrest=copy.deepcopy(BACKREST))


def seat(collection, lib, origin, name, yaw=0.0, back_k=1.0, quality=1.0, sc=1.0, cushion=None, backrest=None,
         npl=N_PLEAT, roles=None, fade=False):
    xf = Matrix.Translation(Vector(origin)) @ Matrix.Rotation(yaw, 4, 'Z')
    cu, bk = copy.deepcopy(cushion or CUSHION), copy.deepcopy(backrest or BACKREST)
    bk["spine"] = [(x, z * back_k) for (x, z) in bk["spine"]]
    made = []
    parts, cush = _part(cu, (0.0, 1.0, 0.0), name + "_Cushion", collection, lib, xf, quality, sc, npl, roles)
    made += parts
    parts, back = _part(bk, (0.0, -1.0, 0.0), name + "_Back", collection, lib, xf, quality, sc, npl, roles, fade)
    made += parts
    return made, cush, back, bk


def _end_cap(collection, lib, sw, name, spine_end, spine_prev, mat):
    """The backrest's open top, closed with a shallow dome (the section's last ring pulled to its centre)."""
    ring = [Vector(p) for p in sw.pts[-1]]
    c0 = sum(ring, Vector()) / len(ring)
    t_end = (Vector(spine_end) - Vector(spine_prev)).normalized()
    rows = []
    for sc, lift in ((1.0, 0.0), (0.85, 0.010), (0.62, 0.018), (0.36, 0.023), (0.12, 0.025), (0.0, 0.0255)):
        rows.append([tuple(c0 + (p - c0) * sc + t_end * lift) for p in ring])
    top = grid_mesh(name + "_Top", rows, collection, mat, wrap_t=True)
    _orient_to(top, c0 + t_end * 0.0255, t_end)
    return top


# -------------------------------------------------------- front-seat extras
def _frame(n, a):
    z = Vector((0.0, 0.0, 1.0))
    return n, a, z


def _blk(col, lib, name, centre, size, role, n, a, r=0.0012):
    """A bevelled block, local x along n (out of the surface), y along a, z up."""
    ob = F.box(col, name, (0.0, 0.0, 0.0), size, lib[role], r=r)
    z = n.cross(a).normalized() if abs(n.cross(a).length) > 1e-6 else Vector((0.0, 0.0, 1.0))
    ob.matrix_world = Matrix.Translation(centre) @ Matrix((tuple(n), tuple(a), tuple(z))).transposed().to_4x4()
    return ob


def build_adjuster(col, lib, name, origin, side):
    """The oval switch panel on the cushion's outboard side (c0095): a dark panel with a diamond key and two
    oval rockers, set into the black side shell."""
    made = []
    x0, y0, z0 = origin
    n = Vector((0.0, side, 0.0))
    a = Vector((-side, 0.0, 0.0))             # (n, a, up) right-handed: a = up x n
    y_out = y0 + side * 0.2205
    c = Vector((x0 + 0.205, y_out, z0 - 0.085))
    made.append(_blk(col, lib, name + "_Plate", c, (0.006, 0.150, 0.052), "plastic", n, a, 0.020))
    for k, (dx, dz, w, h, role) in enumerate(((-0.048, 0.000, 0.030, 0.030, "key"),
                                              (-0.005, -0.004, 0.036, 0.020, "key"),
                                              (0.040, -0.008, 0.030, 0.019, "key"))):
        cc = c + Vector((dx, 0.0, dz)) + n * 0.0050
        made.append(_blk(col, lib, "%s_Key%d" % (name, k), cc, (0.007, w, h), role, n, a, 0.0030))
    return made


def build_buckle(col, lib, name, origin, side):
    """The seat-belt buckle stalk at the cushion's inboard rear corner, with its red release button."""
    made = []
    x0, y0, z0 = origin
    n = Vector((0.0, -side, 0.0))
    a = Vector((side, 0.0, 0.0))
    c = Vector((x0 + 0.030, y0 - side * 0.214, z0 + 0.095))
    made.append(_blk(col, lib, name + "_Stalk", c - Vector((0.0, 0.0, 0.030)), (0.014, 0.020, 0.090), "key", n, a,
                     0.004))
    made.append(_blk(col, lib, name + "_Head", c + Vector((0.0, 0.0, 0.032)), (0.016, 0.034, 0.052), "key", n, a,
                     0.006))
    made.append(_blk(col, lib, name + "_Button", c + Vector((0.0, 0.0, 0.032)) + n * 0.0085, (0.003, 0.016, 0.026),
                     "button_red", n, a, 0.0012))
    return made


# ---------------------------------------------------------- the seats
FRONT_BACK_K = 1.0
# the front headrest: a plain pillow on two posts, a hand's width above the shoulders (seat-local metres)
HEAD_W, HEAD_H, HEAD_T, HEAD_R = 0.235, 0.170, 0.092, 0.038
HEAD_GAP, HEAD_POST_Y = 0.032, 0.066


def build_front_headrest(col, lib, name, top, lean):
    """The headrest above the backrest's top point `top` (world), the backrest leaning by `lean` (negative: the top
    is further back, -x): a pillow tilted a little forward of the back, two posts into guide sleeves on the dome."""
    k = Vector((math.sin(lean), 0.0, math.cos(lean)))          # up the backrest
    nrm = Vector((math.cos(lean), 0.0, -math.sin(lean)))       # out of its front face
    centre = top + k * (0.0255 + HEAD_GAP + 0.5 * HEAD_H) - nrm * (0.5 * HEAD_T - 0.018)
    made = [CP.pillow(col, name, tuple(centre), HEAD_W, HEAD_H, HEAD_T, HEAD_R, lib["leather_perf"], 0.7 * lean)]
    p0 = top - k * 0.020 - nrm * (0.5 * HEAD_T - 0.018)         # post foot, inside the backrest
    n_len = (centre - p0).length
    mid = 0.5 * (centre + p0)
    for i, sy in enumerate((-1.0, 1.0)):
        made.append(F.box(col, "%s_Post%d" % (name, i), (mid.x, top.y + sy * HEAD_POST_Y, mid.z),
                          (0.013, 0.013, n_len), lib["piano"], r=0.003, pitch=lean))
        sl = top + k * 0.014 - nrm * (0.5 * HEAD_T - 0.018)
        made.append(F.box(col, "%s_Sleeve%d" % (name, i), (sl.x, top.y + sy * HEAD_POST_Y, sl.z),
                          (0.030, 0.030, 0.022), lib["leather_black"], r=0.006, pitch=lean))
    return made


def build_front(col, lib):
    made = []
    for tag, y in (("FL", ZI.DRIVER_Y), ("FR", ZI.PASS_Y)):
        side = 1.0 if y > 0 else -1.0
        org = (ZI.FRONT_BIGHT_X, y, ZI.FRONT_BIGHT_Z)
        parts, cush, back, spec = seat(col, lib, org, "int_seat_" + tag, back_k=FRONT_BACK_K, fade=0.86)
        made += parts
        sp = spec["spine"]
        made.append(_end_cap(col, lib, back, "int_seat_%s_Back" % tag,
                             (org[0] + sp[-1][0], y, org[2] + sp[-1][1]),
                             (org[0] + sp[-2][0], y, org[2] + sp[-2][1]), lib["leather_seat"]))
        lean = math.atan2(sp[-1][0] - sp[-2][0], sp[-1][1] - sp[-2][1])
        made += build_front_headrest(col, lib, "int_seat_%s_Head" % tag,
                                     Vector((org[0] + sp[-1][0], y, org[2] + sp[-1][1])), lean)
        made.append(F.box(col, "int_seat_%s_base" % tag, (org[0] + 0.22, y, 0.5 * (ZI.FLOOR_Z + org[2] - 0.07)),
                          (0.50, 0.42, org[2] - 0.07 - ZI.FLOOR_Z), lib["leather_black"], r=0.04))
        made += build_adjuster(col, lib, "int_seat_%s_adj" % tag, org, side)
        made += build_buckle(col, lib, "int_seat_%s_buckle" % tag, org, side)
    return made


# ------------------------------------------------------------- rear bench
REAR_Y_OUT = 0.430            # centre of the outer places
REAR_ROLES = ("leather_seat", "leather_seat", "leather_perf", "leather_seat")
REAR_BACK_K = 1.0


def _headrest(col, lib, name, c, w, h, t, tilt):
    made = [CP.pillow(col, name, c, w, h, t, 0.034, lib["leather_seat"], tilt)]
    for k, sy in enumerate((-1.0, 1.0)):
        q = (c[0] + 0.018, c[1] + sy * 0.050, c[2] - 0.5 * h - 0.018)
        made.append(F.box(col, "%s_Post%d" % (name, k), q, (0.012, 0.012, 0.050), lib["piano"], r=0.003))
    return made


def build_rear(col, lib):
    made = []
    bx, bz = ZI.REAR_BIGHT_X, ZI.REAR_BIGHT_Z
    for tag, y in (("RL", REAR_Y_OUT), ("RR", -REAR_Y_OUT)):
        org = (bx, y, bz)
        parts, cush, back, spec = seat(col, lib, org, "int_seat_" + tag, back_k=REAR_BACK_K, cushion=REAR_CUSHION,
                                       backrest=REAR_BACKREST, npl=3, roles=REAR_ROLES, sc=1.0)
        made += parts
        sp = spec["spine"]
        made.append(_end_cap(col, lib, back, "int_seat_%s_Back" % tag,
                             (bx + sp[-1][0], y, bz + sp[-1][1]), (bx + sp[-2][0], y, bz + sp[-2][1]),
                             lib["leather_seat"]))
        # a separate headrest above each outer place
        top = (bx + sp[-1][0], y, bz + sp[-1][1])
        made += _headrest(col, lib, "int_seat_%s_Head" % tag, (top[0] - 0.040, y, top[2] + 0.085), 0.200, 0.140,
                          0.082, -math.radians(14.0))
    # the centre place: a plain cushion block and a back carrying the fold-down armrest panel
    xc = bx + 0.230
    made.append(F.box(col, "int_seat_RC_Cushion", (xc, 0.0, bz + 0.012), (0.470, 0.392, 0.066), lib["leather_seat"],
                      r=0.030))
    sp = REAR_BACKREST["spine"]
    top = (bx + sp[-1][0], 0.0, bz + sp[-1][1])
    mid = (bx + sp[3][0], 0.0, bz + sp[3][1])
    lean = math.atan2(sp[-1][0] - sp[0][0], sp[-1][1] - sp[0][1])          # negative: the top leans back (-x)
    made.append(F.box(col, "int_seat_RC_Back", (bx + 0.5 * sp[-1][0] - 0.020, 0.0, bz + 0.5 * sp[-1][1]),
                      (0.130, 0.390, sp[-1][1] + 0.040), lib["leather_seat"], r=0.030, pitch=lean))
    made.append(F.box(col, "int_seat_RC_Arm", (bx + 0.5 * sp[-1][0] + 0.006 - 0.020, 0.0, bz + 0.40),
                      (0.020, 0.250, 0.300), lib["leather_perf"], r=0.010, pitch=lean))
    made += _headrest(col, lib, "int_seat_RC_Head", (top[0] - 0.040, 0.0, top[2] + 0.085), 0.180, 0.130, 0.078,
                      -math.radians(14.0))
    # the bench's base and the ISOFIX covers on the hinge line
    made.append(F.box(col, "int_rear_bench_base", (bx + 0.19, 0.0, 0.5 * (ZI.FLOOR_Z + bz - 0.07)),
                      (0.58, 1.26, bz - 0.07 - ZI.FLOOR_Z), lib["leather_black"], r=0.020))
    for k, y in enumerate((-0.43, 0.43, 0.0)):
        made.append(F.box(col, "int_rear_isofix%d" % k, (bx - 0.040, y, bz + 0.060), (0.016, 0.040, 0.030),
                          lib["soft"], r=0.006))
    return made


def build(col, lib):
    return build_front(col, lib) + build_rear(col, lib)
