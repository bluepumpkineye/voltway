"""Luxeed RX reference cameras: the photo measurements and the solves behind
rx_ref_match.py.

Every number here was read off a zoomed, gridded crop of the reference
(blender/reference/luxeed-rx). Coordinates are photo pixels (u right, v
down) and model metres with the FRONT AXLE AT x = 0 ("axle coordinates"):
the overhangs are not published, so the solves are done relative to the
wheels and the overhangs come out of them. rx_ref_match shifts the result
into model coordinates.

Known geometry (MIIT filing, 2026): wheelbase 3000; track 1710/1713 front,
1715/1725 rear; 255/45 R21 front, 275/45 R21 rear (the grey show car carries
"255/45 R21" on its sidewall). Loaded hub height = tyre radius less ~12 mm.
Rim lip: 21 in bead seat (266.7 mm) + ~18 mm flange.

    import rx_camsolve as CS
    CS.solve_all()          # prints each camera; paste into rx_ref_match
"""
import math

from carkit.qa import refmatch as R

WB = 3.000
RF, RR = 0.369, 0.378          # loaded hub heights
RL = 0.285                     # rim lip radius
YF, YR = 0.965, 0.985          # rim lip planes: track/2 + half rim width
# NEV plate holder, 480 x 140: in the blue front 3/4 a 440 mm plate left
# every corner ~4 px inside the photo's.
PLATE_W, PLATE_H = 0.480, 0.140

CF = R.circle((0.0, YF, RF), RL)
CR = R.circle((-WB, YR, RR), RL)


def _plate(sy, sz, W=PLATE_W / 2):
    """Plate corner (sy = +/-1 for +/-y, sz = +/-1 top/bottom); extras
    e0 x, e1 z of the plate centre, e2 tilt (deg, top leaning back)."""
    def f(e):
        t = math.radians(e[2])
        return (e[0] - sz * PLATE_H / 2 * math.sin(t), sy * W,
                e[1] + sz * PLATE_H / 2 * math.cos(t))
    return f


# ------------------------------------------------------------ side_left.jpg
# 1023 x 682, the grey RX Ultra on the Luxeed stand, left side. The rear rim
# is 11 % smaller than the front one: the camera is yawed ~7 deg, so
# solve_side_camera (square-on) does not apply.
SIDE_SIZE = (1023, 682)


def _wheel(xa, rz, yl, hub, left, right, top, bot, tyre_bot):
    return [(hub, (xa, yl - 0.045, rz)),
            ((left, hub[1]), (xa + RL, yl, rz)), ((right, hub[1]), (xa - RL, yl, rz)),
            ((hub[0], top), (xa, yl, rz + RL)), ((hub[0], bot), (xa, yl, rz - RL)),
            ((hub[0], tyre_bot), (xa, yl - 0.01, 0.0))]


SIDE_PAIRS = (_wheel(0.0, RF, YF, (250.6, 421.0), 195, 306, 364, 478, 488)
              + _wheel(-WB, RR, YR, (809.4, 418.0), 760, 858, 367, 468, 480))


# Roof top on the centreline, at the published 1585 mm (x free): the wheel
# features are all in one plane and leave f loose (1030-1110 px); without
# this the roof came out at 1.633 m.
SIDE_ROOF = ((620.0, 200.5), 1.585)


def solve_side():
    (uv, z) = SIDE_ROOF
    pairs = SIDE_PAIRS + [(uv, lambda e: (e[0], 0.0, z))]
    return R.solve_camera(SIDE_SIZE, pairs, (-0.51, 7.23, 1.16), (86.6, -0.7, 172.4), 1200.0,
                          extra=(-2.1,))


# --------------------------------------------------------- front34_blue.jpg
# 1200 x 900, Autohome studio, the blue/purple show car from ahead-left.
# Long lens (~150 mm equivalent). Rim lips are machined silver: points on
# their clean stretches only (spokes hide the rest).
F34_SIZE = (1200, 900)
F34_FW = [(675, 445), (688.3, 453.3), (698.3, 468.3), (704.2, 483.3), (707, 500),
          (706.7, 523.3), (704.2, 536.7), (699.2, 551.7), (690, 565), (680, 575)]
F34_RW = [(980, 425.8), (955.8, 465), (954.2, 490), (956.7, 515), (965, 540),
          (980, 553.3), (1004.2, 531.7), (1006.7, 498.3), (1004.2, 461.7), (995, 435)]
# plate corners TL TR BL BR (image left = the car's right, -y)
F34_PLATE = [(264.2, 455.3), (371.7, 457.5), (264.2, 491.7), (370.8, 494.7)]
# headlamp inner (lower) tips, right lamp then left lamp: a mirror pair
F34_LAMP_TIPS = [(224.2, 426.3), (452.5, 425.5)]


def f34_pairs():
    pairs = [(p, CF) for p in F34_FW] + [(p, CR) for p in F34_RW]
    pairs += [(F34_PLATE[0], _plate(-1, 1)), (F34_PLATE[1], _plate(1, 1)),
              (F34_PLATE[2], _plate(-1, -1)), (F34_PLATE[3], _plate(1, -1))]
    pairs += [(F34_LAMP_TIPS[0], lambda e: (e[3], -e[4], e[5])),
              (F34_LAMP_TIPS[1], lambda e: (e[3], e[4], e[5]))]
    return pairs


def solve_f34():
    best = None
    for f0 in (1500, 2500, 4000):
        s = R.solve_camera(F34_SIZE, f34_pairs(), (16.0, 9.5, 1.0), (88.8, 0.1, 119.2), f0,
                           extra=(1.0, 0.45, 10.0, 0.85, 0.55, 0.62))
        if best is None or s["rms"] < best["rms"]:
            best = s
    return best


# ---------------------------------------------------------------- rear.jpg
# 2277 x 1280, the grey car square from behind. Solved in MODEL coordinates
# (the rear axle's x from rx_surface). Tyre contacts and outer walls at the
# 1720 mm track; the roof crest at the side photo's (-0.9, 1.585); the
# mirror tips (u 507.3 / 1731.7, v 380) at y +/-1.10, x 0.42. A head-on
# photo cannot fix its focal length from the tyres alone (1800-10000 px all
# fit); the mirrors, 2 m deeper, do.
REAR_SIZE = (2277, 1280)


def solve_rear(mirror_y=1.10):
    import rx_surface as S
    RA = S.REAR_AXLE
    pairs = [((559.0, 1163.0), (RA, 0.860, 0.0)), ((1693.5, 1163.0), (RA, -0.860, 0.0)),
             ((458.0, 1000.0), (RA, 1.003, 0.25)), ((1795.0, 1000.0), (RA, -1.003, 0.25)),
             ((458.0, 1080.0), (RA, 1.000, 0.12)), ((1795.0, 1080.0), (RA, -1.000, 0.12)),
             ((1126.0, 138.0), (-0.9, 0.0, 1.585)),
             ((507.3, 380.0), lambda e: (0.42, mirror_y, e[0])),
             ((1731.7, 380.0), lambda e: (0.42, -mirror_y, e[0]))]
    return R.solve_camera(REAR_SIZE, pairs, (RA - 6.5, 0.0, 1.1), (86.0, 0.0, -90.0), 4300.0,
                          extra=(1.12,))


# -------------------------------------------------- rear34_right_forest.webp
# 2000 x 1125, the silver car's RIGHT side from behind (the nose points right
# in the frame - solved as the left side it fell into a mirror image, f < 0).
# Solved in MODEL coordinates: rim lips (rim/tyre boundary) round both
# right-hand wheels, the hub badges, the door handles' centres and the tail
# lamp's tip on the flank.
FOREST_SIZE = (2000, 1125)
FOREST_RIM_R = [(915, 599), (777.5, 745), (905, 902.5), (1040, 735), (815, 645), (810, 850),
                (1012.5, 635), (1020, 850)]
FOREST_RIM_F = [(1850, 528.3), (1785, 630), (1840, 735), (1913.3, 620), (1803.3, 556.7),
                (1800, 706.7), (1891.7, 550), (1896.7, 706.7)]


def solve_forest():
    import rx_surface as S
    cr = R.circle((S.REAR_AXLE, -YR, RR), RL)
    cf = R.circle((S.FRONT_AXLE, -YF, RF), RL)
    pairs = [(p, cr) for p in FOREST_RIM_R] + [(p, cf) for p in FOREST_RIM_F]
    pairs += [((904, 742.5), (S.REAR_AXLE, -(YR - 0.045), RR)),
              ((1838.3, 626.7), (S.FRONT_AXLE, -(YF - 0.045), RF)),
              ((1070, 432), (-1.175, -0.928, 0.997)), ((1423, 442), (-0.15, -0.929, 0.941)),
              ((605, 408), (-2.14, -0.836, 1.104))]
    w = [1.0] * 18 + [1.5, 1.5, 1.0]
    return R.solve_camera(FOREST_SIZE, pairs, (-6.3, -3.95, 1.0), (87.0, 0.0, -45.0), 2400.0,
                          weights=w)


# ---------------------------------------------------------------- the cabin
# interior/cabin_front_black.jpg, 1600 x 900, the straight-on press render.
# Known in 3D: the windscreen's side edge (20 mm inboard of V_A, the trim
# covers the rest) and the door glass's front edge up each A-pillar, and the
# door belts (the card top ~75 mm inboard of the skin). The centre screen's
# outer glass corners (631, 276) - (959, 499) with its size from the spec
# (16.1 in 16:10 + a 6 mm border, 359 x 229 mm) fix the depth; its centre
# and tilt are solved with the camera: (0.446, 0, 1.077), 9.9 deg back.
# 7.9 px rms: a camera between the front seats at head height.
CABIN_SIZE = (1600, 900)
CABIN_A_IN_L = [(50, 85), (80, 120), (105, 150), (150, 200), (190, 248)]
CABIN_A_IN_R = [(1552, 100), (1505, 150), (1450, 200), (1402, 250)]
CABIN_A_OUT_L = [(0, 180), (50, 250)]
CABIN_A_OUT_R = [(1600, 177), (1563, 238)]
CABIN_BELT_L = [(0, 352), (100, 344), (200, 337)]
CABIN_BELT_R = [(1390, 337), (1500, 356), (1600, 375)]
CABIN_SCREEN = [((631, 276), 1, 1), ((959, 276), -1, 1), ((631, 499), 1, -1), ((959, 499), -1, -1)]


class _Path(R.Circle):
    """An open 3D polyline for solve_camera's curve matching (out and back,
    so the loop's closing segment is degenerate)."""

    def __init__(self, pts):
        from mathutils import Vector
        self.pts = [Vector(p) for p in pts]

    def points(self):
        return self.pts + self.pts[::-1]


def _cabin_curves():
    import rx_panels as PN
    import rx_surface as S
    from carkit.interior import cabin as CB

    def edge(side, v_fn, x0, x1, d_in, depth=0.015):
        out = []
        for k in range(31):
            x = x0 + (x1 - x0) * k / 30.0
            p = S.surface_offset(x, S.v_along(x, v_fn(x), d_in), -depth)
            out.append((p[0], side * p[1], p[2]))
        return _Path(out)

    def belt(side, th=0.075):
        out = []
        for k in range(31):
            x = -0.30 + 0.92 * k / 30.0
            z = PN.BELT_Z(x) - 0.004
            out.append((x, side * CB.skin_offset_y(S.BODY, x, z, th, S.V_SHOULDER + 0.25), z))
        return _Path(out)
    return dict(a_in=[edge(s, PN.V_A, 0.03, 0.70, 0.020) for s in (1.0, -1.0)],
                a_out=[edge(s, PN.V_GT, 0.03, 0.62, -0.015) for s in (1.0, -1.0)],
                belt=[belt(1.0), belt(-1.0)])


def solve_cabin():
    """cabin_front: the camera and, as extras, the screen's (x, z, tilt)."""
    c = _cabin_curves()
    W, H = 0.359, 0.229

    def corner(cu, cv):
        def f(e):
            t = math.radians(e[2])
            return (e[0] + cv * H / 2 * math.sin(t), cu * W / 2, e[1] + cv * H / 2 * math.cos(t))
        return f
    pairs = ([(p, c["a_in"][0]) for p in CABIN_A_IN_L] + [(p, c["a_in"][1]) for p in CABIN_A_IN_R]
             + [(p, c["a_out"][0]) for p in CABIN_A_OUT_L]
             + [(p, c["a_out"][1]) for p in CABIN_A_OUT_R]
             + [(uv, corner(cu, cv)) for (uv, cu, cv) in CABIN_SCREEN]
             + [(p, c["belt"][0]) for p in CABIN_BELT_L] + [(p, c["belt"][1]) for p in CABIN_BELT_R])
    return R.solve_camera(CABIN_SIZE, pairs, (-0.7, 0.0, 1.2), (78.0, 0.0, -90.0), 650.0,
                          fix=("ry",), extra=(0.45, 0.98, 10.0), iters=300)


def show(name, s):
    print("%s: loc %s rot %s f %.1f (%.0f mm) rms %.2f px" % (
        name, tuple(round(c, 4) for c in s["loc"]), tuple(round(c, 3) for c in s["rot"]),
        s["f_px"], s["lens_mm"], s["rms"]))
    if s.get("extra"):
        print("   extra:", tuple(round(c, 4) for c in s["extra"]))


def solve_all():
    out = {}
    for name, fn in (("side_left", solve_side), ("front34_blue", solve_f34)):
        out[name] = fn()
        show(name, out[name])
    return out
