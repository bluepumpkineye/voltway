"""Luxeed RX wheels: the three designs of the configuration page, built from
the Autohome photographs (blender/reference/luxeed-rx/wheels, owner approved).

    fengying   22 in "five-spoke": a gloss black face of five broad paddles, a
               machined wedge between each pair at the lip, a slot by the hub;
               255/40 R22 front, 275/40 R22 rear - the blue show car
    yufeng     21 in "double five-spoke": a graphite star of five spikes, each with a
               swept fin, over a machined ring that shows as a crescent between the
               shoulders of the star; 255/45 R21, 275/45 R21 (MIIT)
    sport      21 in gloss black "double five-spoke": five Y spokes whose legs
               run out to a thin lip; the same tyres. One variant paints the
               legs' edge bands and the lip blue (the accent material)

Build only the default (build_all) for the car; the other two are built for
the export (build_options) and swapped in the viewer.

The three faces are TRACED: the photographs are unwarped face-on
(the lip ellipse fitted and turned to a circle), unrolled into polar
coordinates, and the windows' outlines read off as polygons of (angle in
degrees counter-clockwise from 3 o'clock as seen from outside, radius as a
fraction of the lip radius) - one repeat of the five. carkit.parts.wheels
cuts them from a dished face. All photographs show the car's left side, so
the left wheels are built as photographed and the right wheels as the same
wheel (not mirrored: no right-side photograph was found).

Second pass (2026-10-30). The Fengying and the Sport were laid over their photographs
(scripts/wheel-trace maskedge) and match; the Yufeng did not (its windows were fat
pentagons where the photograph has two long open pockets round a swept fin, and its
ring was a separate surface that poked through the star), so it was traced again from
the blue car's rear wheel (Autohome 13524057, ellipse ratio 0.989, lugs at 25 deg).
All three gained the hub cap's emblem, domed locking nuts, the tyre's rim-protector rib
and the caliper's split line, and the Sport's blue now sits in a band down each leg's
edge, as in the photographs, not on their tops.

Sizes: the lip is the rim's J flange, 17.3 mm above the bead seat: 0.2840 m
on a 21 in rim, 0.2967 m on a 22 in; the overall diameter (0.763 m) is the
same. The photographs agree: the hub cap measures 0.103 of the Yufeng's lip
radius and 0.098 of the Fengying's, a ratio of 1.05 (1.045 from the sizes).
"""
import math

from carkit.geom import Curve
from carkit.parts import wheels as W

# ------------------------------------------------------------------ sizes
LIP_21 = 0.2840
LIP_22 = 0.2967

# The red, orange and yellow calipers of the photographs (the Yufeng's silver car, front and
# rear, the Fengying's blue one): a monobloc about 80 degrees round the disc on the front axle
# and 78 on the rear, centred a few degrees below the horizontal, stretching from 0.47 of the
# lip radius out to the rim. The model's block is a sector, with a bulge; `groove` is the split
# between its two halves.
CALIPER = dict(span_deg=43.0, span_rear=39.0, r_inner=0.14, d_out=0.034, steps=16, groove=True)


# ------------------------------------------------------------------ helpers
def _xy(poly, big_r):
    return [(big_r * r * math.cos(math.radians(a)), big_r * r * math.sin(math.radians(a))) for (a, r) in poly]


def _round(poly, big_r, rad, min_turn=25.0, n=4):
    """A traced outline (angle, radius / big_r) with its sharp corners rounded to a radius of `rad`
    metres (a quadratic curve per corner, at most 45 % of either edge): a window's corner in a
    photograph is never a point."""
    pts = _xy(poly, big_r)
    m = len(pts)
    out = []
    for i in range(m):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % m]
        v1 = (p0[0] - p1[0], p0[1] - p1[1])
        v2 = (p2[0] - p1[0], p2[1] - p1[1])
        l1, l2 = math.hypot(*v1), math.hypot(*v2)
        if l1 < 1e-9 or l2 < 1e-9:
            out.append(p1)
            continue
        c = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))
        if 180.0 - math.degrees(math.acos(c)) < min_turn:
            out.append(p1)
            continue
        d = min(rad, 0.45 * l1, 0.45 * l2)
        a = (p1[0] + v1[0] / l1 * d, p1[1] + v1[1] / l1 * d)
        b = (p1[0] + v2[0] / l2 * d, p1[1] + v2[1] / l2 * d)
        for k in range(n + 1):
            t = k / float(n)
            out.append(((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * p1[0] + t * t * b[0],
                        (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * p1[1] + t * t * b[1]))
    res, prev = [], poly[0][0]
    for (x, y) in out:
        ang = math.degrees(math.atan2(y, x))
        ang += 360.0 * round((prev - ang) / 360.0)
        res.append((ang, math.hypot(x, y) / big_r))
        prev = ang
    return res


def _emblem(angle_deg, w=0.0010, mm=0.001):
    """The Luxeed mark, white lines on the black cap (hub cap crops of the Sport's rear and the Yufeng's rear
    photographs): a hexagon 49 mm long and 21 across, a vertical band in the middle (where "LUXEED" is
    written, not modelled) and a chevron either side of it. `angle_deg`: the hexagon's long axis, counter-
    clockwise from 3 o'clock as seen from outside (it differs wheel to wheel: the cap is not clocked)."""
    hexa = [(-24.4, 0.0), (-13.2, 10.3), (13.2, 10.3), (24.4, 0.0), (13.2, -10.3), (-13.2, -10.3)]
    lines = [(hexa[i], hexa[(i + 1) % 6]) for i in range(6)]
    for sx in (-2.8, 2.8):
        lines.append(((sx, 10.3), (sx, -10.3)))
    for sg in (-1.0, 1.0):
        lines.append(((sg * 12.2, 10.3), (sg * 2.8, 0.0)))
        lines.append(((sg * 2.8, 0.0), (sg * 12.2, -10.3)))
    ca, sa = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
    quads = []
    for (p, q) in lines:
        dx, dy = q[0] - p[0], q[1] - p[1]
        ln = math.hypot(dx, dy)
        nx, ny = -dy / ln * 0.5 * w / mm, dx / ln * 0.5 * w / mm
        quad = [(p[0] + nx, p[1] + ny), (q[0] + nx, q[1] + ny), (q[0] - nx, q[1] - ny), (p[0] - nx, p[1] - ny)]
        quads.append([((x * ca - y * sa) * mm, (x * sa + y * ca) * mm) for (x, y) in quad])
    return dict(mat="machined", h=0.0117, quads=quads)


# ------------------------------------------------------------------ fengying
# Traced from the blue car's front wheel (ellipse ratio 0.994). The face is dark and
# runs out to the machined lip band, where five silver wedges - their points at 0.52 of
# the lip radius - break it; five big windows show the disc and caliper, and five long
# slots (the teardrops) lie between the spoke roots at the hub. The angles are the
# photograph's own, as for the other two designs (one lug sits at 22 deg).
DISH_FENG = Curve([(0.000, 0.0720), (0.090, 0.0720), (0.105, 0.0660), (0.130, 0.0500),
                   (0.160, 0.0330), (0.190, 0.0200), (0.220, 0.0110), (0.250, 0.0050),
                   (0.2863, 0.0006), (0.2967, 0.0)], mode="pchip")
FENG_TAB = 0.965                    # where the dark face ends and the lip's machined band begins
# the window between two wedges (this one is centred at 92 deg): the top edge is a circle
# at 0.80, the sides follow the spokes' flanks, the bottom stops short of the lug at 94 deg
FENG_WINDOW = [
    (70.6, 0.788), (72.6, 0.800), (74.0, 0.800), (80.0, 0.800), (90.0, 0.800), (100.0, 0.800),
    (110.0, 0.800), (112.6, 0.796), (114.4, 0.775), (114.9, 0.745), (114.7, 0.700), (113.8, 0.650),
    (112.2, 0.600), (110.2, 0.550), (108.3, 0.510), (106.0, 0.460), (103.5, 0.400), (101.0, 0.330),
    (98.5, 0.285), (96.0, 0.266), (91.0, 0.262), (86.0, 0.266), (82.0, 0.262), (77.0, 0.265),
    (72.0, 0.290), (67.5, 0.330), (63.8, 0.385), (62.0, 0.440), (62.8, 0.490), (64.0, 0.540),
    (65.5, 0.620), (66.6, 0.687), (68.2, 0.753), (68.9, 0.770)]
# the slot between two spoke roots: a point at 0.46, widening down to the hub
FENG_SLOT = [(a + 72.0, r) for (a, r) in [
    (48.5, 0.460), (44.9, 0.461), (42.7, 0.445), (40.8, 0.419), (39.2, 0.388), (37.7, 0.350),
    (35.6, 0.306), (33.0, 0.272), (31.5, 0.255), (33.5, 0.245), (38.0, 0.235), (44.0, 0.225),
    (48.0, 0.230), (50.4, 0.2465), (51.4, 0.284), (52.0, 0.327), (52.0, 0.372), (51.3, 0.417),
    (50.1, 0.444)]]
# the machined wedge: a straight left edge, a slanting right one, a rounded point; it runs
# out past the face's edge (r > FENG_TAB), into the lip's own machined band
FENG_WEDGE = [
    (55.0, 1.000), (55.1, 0.960), (54.9, 0.820), (54.1, 0.720), (53.9, 0.647), (54.6, 0.587),
    (56.1, 0.540), (57.1, 0.525), (58.2, 0.523), (59.3, 0.533), (60.7, 0.567), (62.1, 0.620),
    (63.2, 0.687), (64.3, 0.753), (65.4, 0.820), (66.1, 0.887), (67.1, 0.960), (67.2, 1.000)]

SPEC_FENGYING = W.preset(
    "blade_5", rim_d=2.0 * LIP_22, dish=DISH_FENG, pinstripe=False,
    flange_face=(1.0 - FENG_TAB) * LIP_22, roll_left=math.pi,
    tyre=dict(bulge=1.045, shoulder=0.016, ridge=True),
    hub=dict(depth=0.0720, setback=0.008, cap_rise=0.0055, cap_logo=_emblem(48.7)),
    lugs=dict(count=5, pcd_r=0.05715, r=0.0120, deg=22.0, rise=0.004, dome=0.0070),
    disc=dict(style="plain", inner_r=0.120, thickness=0.032),
    caliper=CALIPER,
    mats=dict(rim="wheel_black", lip="machined", lugs="wheel_black", cap="wheel_black", disc="iron"))
SPEC_FENGYING["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.018, bevel=0.0028, bevel_segs=2, mat="wheel_black",
    r_in=0.034, r_out=FENG_TAB * LIP_22, nr=16, seg=60, step_deg=2.5, step_r=0.03,
    windows=[FENG_WINDOW, FENG_SLOT],
    lug_holes=dict(deg=22.0, pcd=0.05715, r=0.0150, count=5),
    inlay=dict(mat="machined", polys=[FENG_WEDGE], lift=0.0004))

# ------------------------------------------------------------------ yufeng
# Traced again (see the module docstring) from the blue car's rear wheel: Autohome 13524057,
# unwarped (ellipse ratio 0.989), the axle found by centrefit, one repeat read off a gamma 2.2
# polar strip (the bottom one, free of the caliper) and laid over it until the outlines sat on
# the edges. What it shows, per repeat of 72 deg (angles below are that repeat's, the spike at 7):
#   a spike (a straight radial blade, 3-5 deg wide) at 7 deg, whose shoulder spreads over the
#   rim from 4 to 30 deg; a fin that leaves the next spike's root (r 0.45) and sweeps back to
#   end in the shoulder's far side at 29 deg, r 0.82; so two open pockets per repeat, one each
#   side of the fin, floored by the hub web at r 0.30-0.45; and a crescent of machined ring
#   between the shoulders (36-75 deg), bounded inside by a graphite hoop that keeps r 0.82-0.87.
# The star is a graphite face, the ring a machined face 3.5 mm below it that shows in the
# crescents and 4 mm round the shoulders (a `layers` entry): the first build had the ring as a
# separate surface and the notches cut through the star, which came out chewed.
# depth of the face below the flange plane, by radius (m)
DISH_STAR = Curve([(0.000, 0.0720), (0.090, 0.0720), (0.105, 0.0660), (0.130, 0.0500),
                   (0.160, 0.0330), (0.190, 0.0200), (0.220, 0.0105), (0.250, 0.0035),
                   (0.285, 0.0)], mode="pchip")

YUFENG_TAB = 0.965                  # the radius of the shoulders' flat top, the face's own edge
# pocket between a spike and the fin (the caliper and the disc show in it)
YUF_POCKET_A = [
    (9.25, 0.812), (28.75, 0.815), (30.17, 0.795), (31.17, 0.772), (32.67, 0.739), (34.08, 0.704),
    (36.33, 0.659), (38.67, 0.617), (41.17, 0.583), (43.67, 0.552), (46.17, 0.513), (49.5, 0.478),
    (53.67, 0.461), (58.67, 0.454), (63.5, 0.457), (63.67, 0.435), (62.83, 0.391), (60.33, 0.348),
    (56.17, 0.313), (50.33, 0.300), (25.33, 0.304), (15.33, 0.313), (12.0, 0.374), (10.5, 0.443),
    (9.5, 0.513), (9.08, 0.565)]
# pocket between the fin and the next spike, under the ring's hoop
YUF_POCKET_B = [
    (41.58, 0.815), (77.83, 0.815), (77.83, 0.713), (77.17, 0.626), (76.0, 0.570), (73.25, 0.539),
    (68.67, 0.546), (62.42, 0.565), (56.17, 0.591), (51.17, 0.630), (45.75, 0.691), (42.42, 0.783)]
# the crescent of machined ring: the star is cut away outside the hoop (which holds r 0.87), out
# past the face's edge (r > YUFENG_TAB) so the cut is clean
YUF_CRESCENT = [
    (35.75, 1.12), (35.75, 1.000), (38.67, 0.967), (42.0, 0.923), (45.33, 0.899), (50.33, 0.878),
    (55.33, 0.870), (62.0, 0.868), (67.0, 0.873), (70.33, 0.889), (72.42, 0.915), (74.08, 0.957),
    (74.92, 1.000), (74.92, 1.12)]
_YUF_A = _round(YUF_POCKET_A, LIP_21, 0.0035)
_YUF_B = _round(YUF_POCKET_B, LIP_21, 0.0035)

SPEC_YUFENG = W.preset(
    "blade_5", rim_d=2.0 * LIP_21, dish=DISH_STAR, pinstripe=False, flange_face=0.0057,
    roll_left=math.pi,
    tyre=dict(ridge=True),
    hub=dict(depth=0.0720, setback=0.008, cap_rise=0.0055, cap_logo=_emblem(128.6)),
    lugs=dict(count=5, pcd_r=0.05715, r=0.0118, deg=25.0, rise=0.004, dome=0.0070),
    disc=dict(style="plain", inner_r=0.120, thickness=0.032),
    caliper=CALIPER,
    mats=dict(rim="graphite", lip="machined", lugs="wheel_black", cap="wheel_black", disc="iron"))
SPEC_YUFENG["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.018, bevel=0.0024, bevel_segs=2, mat="graphite",
    r_in=0.034, r_out=YUFENG_TAB * LIP_21, nr=16, seg=60, step_deg=2.5, step_r=0.03,
    windows=[_YUF_A, _YUF_B], notches=[YUF_CRESCENT],
    lug_holes=dict(deg=25.0, pcd=0.05715, r=0.0175, count=5),
    # the machined ring under the star: a plain annulus from just inside the hoop's inner edge (r 0.815) to the
    # lip, no windows (the pockets end under the hoop, so none of it shows inside them)
    layers=[dict(dz=-0.0035, mat="machined", bevel=0.0008, r_in=0.83 * LIP_21, r_out=0.9795 * LIP_21, nr=4,
                 windows=[], notches=[], lug_holes=None)])

# ------------------------------------------------------------------ sport
DISH_SPORT = Curve([(0.000, 0.0720), (0.090, 0.0720), (0.105, 0.0660), (0.130, 0.0500),
                    (0.160, 0.0330), (0.190, 0.0200), (0.220, 0.0105), (0.250, 0.0035),
                    (0.285, 0.0)], mode="pchip")

SPORT_WINDOWS = [
    # the V between a Y's two legs (this Y's axis is at 269.25 deg)
    [(247.0, 0.980), (248.2, 0.900), (251.0, 0.780), (253.8, 0.700), (256.5, 0.620), (260.5, 0.540),
     (261.5, 0.508), (265.0, 0.484), (269.25, 0.472), (273.5, 0.484), (277.0, 0.508), (278.0, 0.540),
     (282.0, 0.620), (284.7, 0.700), (287.5, 0.780), (290.3, 0.900), (291.5, 0.980)],
    # between two Y's (centred at 305.25): narrow at the rim, wide at the stems
    [(278.5, 0.310), (279.0, 0.380), (279.5, 0.424), (283.0, 0.476), (286.0, 0.540), (288.3, 0.620),
     (290.3, 0.700), (292.0, 0.780), (293.7, 0.900), (294.3, 0.980), (316.2, 0.980), (316.8, 0.900),
     (318.5, 0.780), (320.2, 0.700), (322.2, 0.620), (324.5, 0.540), (327.5, 0.476), (331.0, 0.424),
     (331.5, 0.380), (332.0, 0.310)],
]

# the legs run into a lip ring about 9 mm wide (the blue band of the blue car's photographs)
SPORT_FLANGE = 0.0095
# The blue car's legs are black on top with a blue band down each edge (the painted chamfer), from about 0.4 of the
# lip radius out. The bevel modifier cannot make it (it clamps to 0.5 mm along the traced polylines): the top face's
# windows are grown by the band's width, which fades in between 0.38 and 0.44 of the radius, and a second face 3 mm
# lower in the accent material, with the windows as traced (a hair smaller, so its walls stay clear), shows as the
# ledge. Black cars paint the accent black, so the ledge is then just a shadow line.
SPORT_BAND = 0.0050


def _band(r):
    t = max(0.0, min(1.0, (r - 0.38) / 0.06))
    return SPORT_BAND * t * t * (3.0 - 2.0 * t)

SPEC_SPORT = W.preset(
    "blade_5", rim_d=2.0 * LIP_21, dish=DISH_SPORT, pinstripe=False, flange_face=SPORT_FLANGE,
    roll_left=math.pi,
    tyre=dict(ridge=True),
    hub=dict(depth=0.0720, setback=0.008, cap_rise=0.0055, cap_logo=_emblem(0.0)),
    lugs=dict(count=5, pcd_r=0.05715, r=0.0118, deg=84.8, rise=0.004, dome=0.0070),
    disc=dict(style="plain", inner_r=0.120, thickness=0.032),
    caliper=CALIPER,
    mats=dict(rim="wheel_black", lip="accent", accent="accent", lugs="wheel_black",
              cap="wheel_black", disc="iron"))
SPEC_SPORT["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.020, bevel=0.0016, bevel_segs=2, mat="wheel_black",
    r_in=0.034, r_out=LIP_21 - SPORT_FLANGE + 0.001, nr=16, seg=60, step_deg=2.5, step_r=0.03,
    windows=[W.grow(w, _band, LIP_21) for w in SPORT_WINDOWS],
    lug_holes=dict(deg=84.8, pcd=0.05715, r=0.0175, count=5),
    layers=[dict(dz=-0.003, mat="accent", bevel=0.0005, r_in=0.36 * LIP_21, nr=10,
                 windows=[W.grow(w, -0.0006, LIP_21) for w in SPORT_WINDOWS], lug_holes=None)])

# ------------------------------------------------------------------ the set
# name -> (object prefix, spec). The default keeps the build's own "RX_" names.
DESIGNS = {
    "fengying": ("RX_", SPEC_FENGYING),
    "yufeng": ("RX_Yufeng_", SPEC_YUFENG),
    "sport": ("RX_Sport_", SPEC_SPORT),
}
DEFAULT = "fengying"


def corners(surface):
    # tag, axle x, sign, tyre width, rolling radius, disc radius,
    # caliper deg (local: 180 is straight back; the left wheel's +Y is down, the right's up,
    # so 176 and 184 are both 4 degrees below the horizontal), outer sidewall y (track/2 +
    # tyre width/2). The overall diameter is the same for every design, so is the table.
    return [
        ("FL", surface.FRONT_AXLE, 1, 0.255, 0.369, 0.190, 176.0, 0.9825),
        ("FR", surface.FRONT_AXLE, -1, 0.255, 0.369, 0.190, 184.0, 0.9825),
        ("RL", surface.REAR_AXLE, 1, 0.275, 0.378, 0.180, 176.0, 0.9975),
        ("RR", surface.REAR_AXLE, -1, 0.275, 0.378, 0.180, 184.0, 0.9975),
    ]


def build_design(collection, surface, lib, name):
    prefix, spec = DESIGNS[name]
    return W.build_set(collection, prefix, lib, spec, corners(surface))


def build_all(collection, surface, lib):
    """The car's own wheels: the default design."""
    return build_design(collection, surface, lib, DEFAULT)


def build_options(collection, surface, lib):
    """The other designs, on top of the first: for the export (they are split
    into a node of their own), never for a render."""
    made = []
    for name in DESIGNS:
        if name != DEFAULT:
            made += build_design(collection, surface, lib, name)
    return made
