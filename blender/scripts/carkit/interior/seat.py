"""Bucket seats.

A seat is two sweeps in seat-local coordinates (origin at the BIGHT - where
cushion meets backrest - on the seat centreline; X forward, Y left, Z up):

    cushion    spine from the bight forward along the cushion and down its
               front face; closed section across it: side face, bolster
               crown, seam, centre panel ... and back underneath
    backrest   spine from the bight up the back, over the integrated
               headrest and down its rear; closed section: bolsters forward,
               the rear shell behind

The section's control points are the panel lines. Front side, left to right:

    0 side foot   1 side top   2 bolster crown   3 crown inner   4 inner slope
    5 SEAM        6 centre     7 CENTRELINE      8 centre        9 SEAM
    10 inner slope 11 crown inner 12 bolster crown 13 side top   14 side foot
    15.. the underside / rear shell (closed section)

so the centre panel is columns 5..9, the bolsters 0..5 and 9..14, and piping
and stitch lines run along those columns. Bolster height, seat width and the
centre panel's width vary along the spine with the curves in the spec.

    parts = seat(collection, lib, spec, origin=(x, y, z), name="int_seat_FL")
"""
import math

from mathutils import Matrix, Vector

from .. import mesh as M
from ..geom import Curve
from .sweep import Sweep, stitches, piping

# Ultra front bucket: black Alcantara centre and crowns, yellow Nappa bolster
# faces, yellow piping on the crowns, a yellow double stitch down the middle.
SU7_ULTRA_FRONT = dict(
    cushion=dict(
        spine=[(0.00, 0.00), (0.10, 0.030), (0.28, 0.058), (0.43, 0.074), (0.49, 0.062),
               (0.515, 0.020), (0.52, -0.05), (0.51, -0.12)],
        half_w=Curve([(0.0, 0.265), (0.5, 0.272), (1.0, 0.262)]),
        bolster=Curve([(0.0, 0.35), (0.25, 0.85), (0.55, 1.0), (0.78, 0.55), (0.88, 0.0),
                       (1.0, 0.0)], mode="pchip"),
        bolster_h=0.048, centre_half=0.140, depth=0.125),
    backrest=dict(
        spine=[(0.00, 0.00), (-0.045, 0.092), (-0.13, 0.275), (-0.20, 0.440), (-0.240, 0.535),
               (-0.275, 0.630), (-0.302, 0.705), (-0.330, 0.736), (-0.368, 0.729)],
        half_w=Curve([(0.0, 0.262), (0.45, 0.272), (0.62, 0.258), (0.72, 0.165),
                      (0.80, 0.150), (1.0, 0.140)], mode="pchip"),
        bolster=Curve([(0.0, 0.55), (0.30, 1.0), (0.55, 0.75), (0.68, 0.20), (0.78, 0.40),
                       (0.90, 0.25), (1.0, 0.0)], mode="pchip"),
        bolster_h=0.095, centre_half=Curve([(0.0, 0.135), (0.62, 0.130), (0.72, 0.085),
                                            (1.0, 0.080)], mode="pchip"),
        depth=0.085),
    mats=dict(centre="alcantara", crown="alcantara", face="leather_accent",
              shell="leather_black", piping="leather_accent", stitch="thread_accent",
              base="satin"),
    stitch_half_gap=0.006,
)


# Luxeed RX front seat (the white-and-red trim, interior photographs):
# white perforated Nappa all over the front, a ~38 mm red band down the
# middle of cushion and backrest, red piping on the bolster crowns, and a
# dark top (headrest and shoulder wings, piped red) - the SU7 bucket's
# shape with the RX's trim.
LUXEED_RX_FRONT = dict(
    cushion=dict(SU7_ULTRA_FRONT["cushion"], bolster_h=0.040),
    backrest=dict(SU7_ULTRA_FRONT["backrest"], bolster_h=0.075),
    mats=dict(centre="leather_white", crown="leather_white", face="leather_white",
              shell="leather_black", piping="leather_accent", stitch="thread_accent",
              base="satin", cap="leather_black"),
    stitch_half_gap=0.024,
    stripe=dict(half_w=0.019, role="leather_accent", i0=0.05, i1=0.93),
    cap_from=0.64,
)


def _section(half_w, bolster, bh, centre_half, depth, closed=True):
    """Front section points (15) + underside/rear (5), as (a, b)."""
    w = half_w
    c = centre_half
    k = bolster
    front = [
        (w, -0.10), (w, -0.012), (w - 0.020, 0.050 * k + 0.004),
        (w - 0.052, bh * k), (c + 0.030, 0.035 * k + 0.004), (c, 0.004),
        (c * 0.5, -0.005), (0.0, -0.007),
        (-c * 0.5, -0.005), (-c, 0.004), (-(c + 0.030), 0.035 * k + 0.004),
        (-(w - 0.052), bh * k), (-(w - 0.020), 0.050 * k + 0.004), (-w, -0.012), (-w, -0.10),
    ]
    back = [(-w + 0.020, -depth), (-0.5 * w, -depth - 0.012), (0.0, -depth - 0.016),
            (0.5 * w, -depth - 0.012), (w - 0.020, -depth)]
    return front + (back if closed else [])


FRONT_COUNTS = [5, 4, 3, 4, 2, 3, 2, 2, 3, 2, 4, 3, 4, 5]
BACK_COUNTS = [3, 5, 4, 4, 5, 3]            # 14 -> 15 -> ... -> 19 -> 0 (closed)


def _part(spec, lateral, name, collection, lib, mats, xf, stitch_gap, ns=44, stripe=None,
          cap_from=None):
    spine = [xf @ Vector((x, 0.0, z)) for (x, z) in spec["spine"]]
    hw, bol = spec["half_w"], spec["bolster"]
    ch = spec["centre_half"]

    def section(i, s):
        c = ch(s) if callable(ch) else ch
        return _section(hw(s), bol(s), spec["bolster_h"], c, spec["depth"])
    counts = FRONT_COUNTS + BACK_COUNTS
    sw = Sweep([tuple(p) for p in spine], section, ns, counts, lateral=lateral,
               closed_section=True, outward=-1.0)
    col = sw.col
    made = []
    n_s = len(sw.pts)
    # cap_from: rows past this spine fraction (a backrest's top: headrest and
    # shoulders) are a separate panel in mats["cap"]
    i_cap = None if cap_from is None else int(round((n_s - 1) * cap_from))
    # panels: faces (yellow) 0..2 and 12..14, crowns 2..5 / 9..12, centre 5..9,
    # shell 14..20(=0)
    for nm, j0, j1, role in (("_FaceL", 0, 2, "face"), ("_CrownL", 2, 5, "crown"),
                             ("_Centre", 5, 9, "centre"), ("_CrownR", 9, 12, "crown"),
                             ("_FaceR", 12, 14, "face")):
        if i_cap is None:
            made.append(sw.mesh(name + nm, collection, lib[mats[role]], j0=col(j0), j1=col(j1)))
        else:
            made.append(sw.mesh(name + nm, collection, lib[mats[role]], i1=i_cap,
                                j0=col(j0), j1=col(j1)))
            made.append(sw.mesh(name + nm + "Cap", collection, lib[mats["cap"]], i0=i_cap,
                                j0=col(j0), j1=col(j1)))
    rows = sw.rows(j0=col(14), j1=sw.nt - 1)
    rows = [r + [sw.pts[i][0]] for i, r in enumerate(rows)]      # close back to column 0
    from .sweep import grid_mesh, _orient_to
    sh = grid_mesh(name + "_Shell", rows, collection, lib[mats["shell"]])
    ic = len(rows) // 2
    _orient_to(sh, Vector(rows[ic][len(rows[0]) // 2]), -sw.normal(ic, col(7)))
    made.append(sh)
    if stripe:
        # a flat band down the centreline, just proud of the centre panel
        i0, i1 = int(n_s * stripe["i0"]), int(n_s * stripe["i1"])
        p, nrm = sw.iso_col(col(7), i0, i1, lift=0.0014)
        rows = []
        for k, (q, nn) in enumerate(zip(p, nrm)):
            B = sw.frames[i0 + k][1]
            Q, Nn = Vector(q), Vector(nn)
            w = stripe["half_w"]
            rows.append([tuple(Q + B * w * t - Nn * (0.0010 * abs(t) ** 4)) for t in
                         (-1.0, -0.5, 0.0, 0.5, 1.0)])
        st = grid_mesh(name + "_Stripe", rows, collection, lib[stripe["role"]])
        _orient_to(st, Vector(rows[len(rows) // 2][2]), Vector(nrm[len(nrm) // 2]))
        made.append(st)
    # piping on the crowns, a double stitch down the middle of the centre panel
    i_end = int(n_s * 0.86)
    for k in (2, 12):
        p, _ = sw.iso_col(col(k), 0, i_end, lift=0.0010)
        made.append(piping("%s_Piping%d" % (name, k), p, collection, lib[mats["piping"]],
                           r=0.0024, lateral=lateral))
    p, nrm = sw.iso_col(col(7), int(n_s * 0.08), int(n_s * 0.84))
    for side in (1.0, -1.0):
        made.append(stitches("%s_Stitch%s" % (name, "L" if side > 0 else "R"), p, nrm,
                             collection, lib[mats["stitch"]], side=side * stitch_gap))
    return made, sw


def seat(collection, lib, spec, origin, name="int_seat", yaw=0.0):
    """A bucket seat at `origin` (the bight, on the seat centreline)."""
    xf = Matrix.Translation(Vector(origin)) @ Matrix.Rotation(yaw, 4, 'Z')
    mats = spec["mats"]
    made = []
    parts, cush = _part(spec["cushion"], (0.0, 1.0, 0.0), name + "_Cushion", collection,
                        lib, mats, xf, spec["stitch_half_gap"], stripe=spec.get("stripe"))
    made += parts
    parts, back = _part(spec["backrest"], (0.0, -1.0, 0.0), name + "_Back", collection,
                        lib, mats, xf, spec["stitch_half_gap"], stripe=spec.get("stripe"),
                        cap_from=spec.get("cap_from"))
    made += parts
    # the base: a dark frame from under the cushion down to the floor rails
    return made, cush, back


def base(collection, lib, origin, floor_z, length=0.46, half_w=0.22, name="int_seat_base"):
    """Seat pedestal and rails: a dark block under the cushion."""
    x0, y0, z0 = origin
    verts, faces = [], []
    top = z0 - 0.09
    for (dx, dz) in ((0.02, top), (length, top + 0.05)):
        pass
    pts = [(x0 + 0.02, -half_w, floor_z), (x0 + length, -half_w, floor_z),
           (x0 + length, half_w, floor_z), (x0 + 0.02, half_w, floor_z),
           (x0 + 0.04, -half_w * 0.9, top), (x0 + length - 0.05, -half_w * 0.9, top + 0.04),
           (x0 + length - 0.05, half_w * 0.9, top + 0.04), (x0 + 0.04, half_w * 0.9, top)]
    verts = [(p[0], y0 + p[1], p[2]) for p in pts]
    faces = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    ob = M.obj(name, verts, faces, collection, lib["satin"], smooth=False)
    M.bevel(ob, 0.012, 2)
    return ob
