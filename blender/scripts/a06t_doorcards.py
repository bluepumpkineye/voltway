"""Avatr 06T door cards (c3_0003 front card square on, c3_0020 rear card, c3_0023 switch pack, c3_0026 speaker).

Measured as fractions of the card's length (rear edge 0 .. front edge 1) and of its height on the square-on photos:

    frame       Misty Purple soft-touch all round: the belt rail, the leading edge, a broad purple field under the
                armrest and a purple wing at the upper front
    upper panel Cotton White, from the rear edge to ~0.70 of the length (its leading edge leaning forward toward the
                top, the top-front corner rounded), armrest to just under the rail
    light slot  a long black slot across the white panel (0.09 .. 0.50, z ~0.915) with the ambient strip in it
    armrest     a white padded bar the full length of the white panel, the switch pack at its rear end (driver) and
                a satin-silver pull grip at its front end
    pocket      a white D-shaped insert under the armrest (0.22 .. 0.60), its bottom curving down to z ~0.53
    speaker     the round silver Meridian grille at the lower front (front card r 0.064 at 0.79; the rear card adds a
                tweeter and a mid-range at the upper front)

The cards' outlines are a06t_interior.front_card / rear_card (the openings' door frames are built to them). Every part
is named int_door_<L/R>_* or int_rdoor_<L/R>_* so a06t_openings.join_cards hangs it on its door's hinge.
"""
import math

from mathutils import Vector

import a06t_interior as RI
import a06t_panels as PN
from carkit.interior import fittings as F
from carkit.interior.sweep import grid_mesh, tube, ellipse, smooth_path, stitches, cr_segments
from carkit import mesh as M


def _belt(x):
    return RI._belt_z(x)


def _armrest(dc, name, col, lib, side, x0, x1, z, width=0.062, height=0.052, n=44):
    """A white padded bar along the card, its ends tapering into it, tone-on-tone stitching along its top edge."""
    rows, edge = [], []
    for k in range(n + 1):
        s = k / float(n)
        x = x0 + (x1 - x0) * s
        e = min(1.0, min(s, 1.0 - s) * 9.0)
        e = e * e * (3 - 2 * e)
        w = 0.006 + (width - 0.006) * e
        y0 = dc.skin_y(x, z) - dc.th(z)
        prof = [(0.0, -height), (w * 0.55, -height * 0.94), (w * 0.96, -height * 0.55), (w, -0.012),
                (w * 0.9, -0.002), (w * 0.55, 0.0), (0.0, -0.003)]
        sec = cr_segments(prof, 4)
        rows.append([(x, side * (y0 - a), z + b) for (a, b) in sec])
        edge.append((x, side * (y0 - w * 0.78), z + 0.0004))
    ob = grid_mesh(name, rows, col, lib["leather_white"])
    M.orient(ob.data, lambda c: (0.0, -side, 0.4))
    st = stitches(name + "Stitch", edge[4:-4], [(0.0, 0.0, 1.0)] * len(edge[4:-4]), col, lib["thread_white"])
    return [ob, st]


def _speaker(dc, name, col, lib, x, z, r, side, proud=0.003):
    """A round silver grille in a satin ring, flush in the card."""
    c = Vector(dc.point(x, z, proud))
    n = Vector((0.0, -side, 0.0))
    return F.disc(col, name, tuple(c), tuple(n), r, lib["speaker_silver"], dome=0.002, rim=0.0030,
                  rim_mat=lib["satin_metal"])


def _card(dc, pre, col, lib, side, x_of, feats):
    """One card. x_of(f) maps a length fraction (rear 0 .. front 1) to x; feats holds the card's measurements."""
    made = []
    xr, xf = dc.xr, dc.xf
    rail_bot = lambda x: _belt(x) - 0.034
    made.append(dc.belt_cap(pre + "Belt", col, lib["trim_purple"], xr(0.95) + 0.003, xf(1.0), _belt, mirror=False))
    made.append(dc.carrier(pre + "Carrier", col, lib["trim_purple"], lambda x: 0.40, lambda x: _belt(x) - 0.002,
                           x0=xr, x1=xf, mirror=False))
    made.append(dc.band(pre + "Field", col, lib["trim_purple"], lambda x: 0.40, rail_bot, x0=xr, x1=xf, nx=64, nz=26,
                        mirror=False))
    made.append(dc.band(pre + "Rail", col, lib["trim_purple"], rail_bot, lambda x: _belt(x) - 0.002, proud=-0.003,
                        x0=xr, x1=xf, nz=6, edge_round=0.006, mirror=False))
    # the white upper panel: armrest to under the rail; its leading edge leans forward toward the top and rounds into
    # the top edge
    za, zt = feats["arm_z"] - 0.004, None
    f_lo, f_hi = feats["panel_front"]
    top = lambda x: rail_bot(x) - 0.010

    def lead(z):
        zt_ = top(x_of(f_hi))
        t = max(0.0, min(1.0, (z - za) / max(1e-3, zt_ - za)))
        x = x_of(f_lo + (f_hi - f_lo) * t)
        u = max(0.0, (t - 0.72) / 0.28)
        return x - 0.050 * (1.0 - math.sqrt(max(0.0, 1.0 - u * u)))
    rear = (lambda z: x_of(0.0) + 0.012) if feats["front_is_x_hi"] else (lambda z: x_of(0.0) - 0.012)
    x0, x1 = (rear, lead) if feats["front_is_x_hi"] else (lead, rear)
    made.append(dc.band(pre + "Panel", col, lib["leather_white"], lambda x: za, top, proud=0.006, x0=x0, x1=x1,
                        nx=56, nz=14, edge_round=0.006, mirror=False))
    # the light slot
    s0, s1 = feats["slot"]
    zs = feats["slot_z"]
    xa, xb = sorted((x_of(s0), x_of(s1)))
    made.append(dc.band(pre + "Slot", col, lib["piano"], lambda x: zs - 0.008, lambda x: zs + 0.008, proud=0.0075,
                        x0=lambda z: xa, x1=lambda z: xb, nx=40, nz=4, edge_round=0.003, mirror=False))
    made.append(tube(pre + "Ambient", dc.curve([(xa + 0.012, zs - 0.004), (xb - 0.012, zs - 0.004)], proud=0.0085, n=30),
                     ellipse(0.0016, 0.0016, 6), col, lib["ambient"], lateral=(0.0, 0.0, 1.0)))
    # the armrest, the pocket under it, the speaker
    a0, a1 = sorted((x_of(feats["arm"][0]), x_of(feats["arm"][1])))
    made += _armrest(dc, pre + "Armrest", col, lib, side, a0, a1, feats["arm_z"])
    p0, p1 = sorted((x_of(feats["pocket"][0]), x_of(feats["pocket"][1])))
    zp = feats["arm_z"] - 0.058

    def pocket_bot(x):
        t = (x - p0) / (p1 - p0)
        return zp - (zp - feats["pocket_low"]) * math.sin(math.pi * max(0.0, min(1.0, t))) ** 0.55
    made.append(dc.band(pre + "Pocket", col, lib["leather_white"], pocket_bot, lambda x: zp, proud=0.003,
                        x0=lambda z: p0, x1=lambda z: p1, nx=40, nz=10, edge_round=0.005, mirror=False))
    for k, (f, z, r) in enumerate(feats["speakers"]):
        made += _speaker(dc, pre + "Speaker%d" % k, col, lib, x_of(f), z, r, side)
    # the pull grip at the armrest's front end: a satin C
    xg = a1 if feats["front_is_x_hi"] else a0
    sg = 1.0 if feats["front_is_x_hi"] else -1.0
    zg = feats["arm_z"] - 0.022
    y0 = dc.skin_y(xg, zg) - dc.th(zg)
    path = [(xg - sg * 0.030 + sg * 0.030 * math.sin(math.pi * t / 12.0), side * (y0 - 0.004 - 0.045 * math.sin(
        math.pi * t / 12.0)), zg + 0.020 - 0.040 * t / 12.0) for t in range(13)]
    made.append(tube(pre + "Grip", path, ellipse(0.0060, 0.0090, 10), col, lib["satin_metal"],
                     lateral=(0.0, 0.0, 1.0)))
    if feats.get("sail"):
        # the e-mirror's black sail in the card's upper front corner (c3_0003), its slanted edge down and forward
        f0, z0 = feats["sail"]
        f1 = 0.985

        def sail_rear(z):
            """The slanted edge: a point at the front at z0, back to f0 by 0.20 m higher."""
            t = max(0.0, min(1.0, (z - z0) / 0.20))
            return x_of(f1 - (f1 - f0) * t)
        made.append(dc.band(pre + "Sail", col, lib["piano"], lambda x: z0, lambda x: rail_bot(x) - 0.002, proud=0.004,
                            x0=sail_rear, x1=lambda z: x_of(f1), nx=20, nz=8, edge_round=0.003, mirror=False))
    if feats.get("switches"):
        # the window/mirror switch pack at the armrest's rear end (c3_0023: a white plate with four keys)
        xs = (a0 + 0.030) if feats["front_is_x_hi"] else (a1 - 0.030)
        for k in range(4):
            xk = xs + (0.030 * k if feats["front_is_x_hi"] else -0.030 * k)
            yk = side * (dc.skin_y(xk, feats["arm_z"]) - dc.th(feats["arm_z"]) - 0.034)
            made.append(F.box(col, pre + "Switch%d" % k, (xk, yk, feats["arm_z"] + 0.004), (0.022, 0.030, 0.008),
                              lib["plastic_white"], r=0.003))
    return made


FRONT = dict(front_is_x_hi=True, panel_front=(0.70, 0.73), slot=(0.09, 0.50), slot_z=0.915, arm=(0.03, 0.66),
             arm_z=0.745, pocket=(0.22, 0.60), pocket_low=0.535, speakers=[(0.79, 0.560, 0.064)], switches=True,
             sail=(0.80, 0.800))
REAR = dict(front_is_x_hi=True, panel_front=(0.68, 0.70), slot=(0.10, 0.50), slot_z=0.925, arm=(0.04, 0.78),
            arm_z=0.735, pocket=(0.25, 0.62), pocket_low=0.540,
            speakers=[(0.84, 0.555, 0.058), (0.74, 0.905, 0.020), (0.81, 0.902, 0.032)], switches=False)


def build(col, lib):
    made = []
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        dc = RI.front_card(side)
        x_r, x_f = dc.xr(0.70), dc.xf(0.70)
        feats = dict(FRONT, switches=(side > 0))
        made += _card(dc, "int_door_%s_" % tag, col, lib, side, lambda f, a=x_r, b=x_f: a + (b - a) * f, feats)
        dc = RI.rear_card(side)
        x_r, x_f = dc.xr(0.70), dc.xf(0.70)
        made += _card(dc, "int_rdoor_%s_" % tag, col, lib, side, lambda f, a=x_r, b=x_f: a + (b - a) * f, REAR)
    return made
