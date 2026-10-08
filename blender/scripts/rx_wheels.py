"""Luxeed RX wheels: the three designs of the configuration page, built from
the Autohome photographs (blender/reference/luxeed-rx/wheels, owner approved).

    fengying   22 in "five-spoke": a gloss black face of five broad paddles, a
               machined wedge between each pair at the lip, a slot by the hub;
               255/40 R22 front, 275/40 R22 rear - the blue show car
    yufeng     21 in "double five-spoke": a graphite star of five spokes, each
               joined at the rim to a swept branch of its neighbour, inside a
               wide machined ring; 255/45 R21, 275/45 R21 (MIIT)
    sport      21 in gloss black "double five-spoke": five Y spokes whose legs
               run out to a thin lip; the same tyres. One variant paints the
               legs' tops and the lip blue (the accent material)

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
# lip radius out to the rim. The model's block is a sector, with a bulge.
CALIPER = dict(span_deg=43.0, span_rear=39.0, r_inner=0.14, d_out=0.034, steps=16)

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
    tyre=dict(bulge=1.045, shoulder=0.016),
    hub=dict(depth=0.0720, setback=0.008, cap_rise=0.0055),
    lugs=dict(count=5, pcd_r=0.05715, r=0.0120, deg=22.0, rise=0.004),
    disc=dict(style="plain", inner_r=0.120, thickness=0.032),
    caliper=CALIPER,
    mats=dict(rim="black_gloss", lip="machined", lugs="black_gloss", cap="black_gloss", disc="iron"))
SPEC_FENGYING["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.018, bevel=0.0020, mat="black_gloss",
    r_in=0.034, r_out=FENG_TAB * LIP_22, nr=16, seg=60, step_deg=2.5, step_r=0.03,
    windows=[FENG_WINDOW, FENG_SLOT],
    lug_holes=dict(deg=22.0, pcd=0.05715, r=0.0150, count=5),
    inlay=dict(mat="machined", polys=[FENG_WEDGE], lift=0.0004))

# ------------------------------------------------------------------ yufeng
# depth of the face below the flange plane, by radius (m)
DISH_STAR = Curve([(0.000, 0.0720), (0.090, 0.0720), (0.105, 0.0660), (0.130, 0.0500),
                   (0.160, 0.0330), (0.190, 0.0200), (0.220, 0.0105), (0.250, 0.0035),
                   (0.285, 0.0)], mode="pchip")
# the machined ring under the star's tabs: a few mm lower than they are
DISH_RING = Curve([(0.200, 0.0225), (0.240, 0.0125), (0.2783, 0.0045)], mode="pchip")

# the edge of the dark star: a tab at the rim, a slope, the floor of the
# notch and a steep rise (rear wheel, rear_uw polar strip, 5 repeats of 72 deg)
YUFENG_TAB = 0.965                  # the radius of the tab's flat top, the face's own edge
YUFENG_NOTCH = [
    (48.5, YUFENG_TAB), (54.0, 0.940), (58.0, 0.890), (63.0, 0.850), (68.0, 0.815),
    (73.0, 0.800), (80.0, 0.797), (90.0, 0.797), (94.0, 0.825), (96.7, 0.884),
    (98.0, 0.935), (99.0, 0.958), (99.5, YUFENG_TAB),
    # and back along a circle outside the face: what lies beyond the outline is cut away
    (99.5, 1.12), (48.5, 1.12)]
YUFENG_WINDOWS = [
    # between a spoke and the swept branch that comes back to it
    [(34.5, 0.745), (51.7, 0.743), (54.2, 0.656), (57.5, 0.593), (61.7, 0.547), (68.3, 0.493),
     (73.3, 0.440), (68.0, 0.400), (66.7, 0.325), (39.2, 0.325), (37.0, 0.384), (35.5, 0.500),
     (34.5, 0.620)],
    # between the branch and the next spoke, down to the root of the branch
    [(64.2, 0.738), (97.4, 0.743), (97.2, 0.630), (96.2, 0.565), (95.0, 0.490), (93.3, 0.478),
     (88.3, 0.481), (81.7, 0.499), (75.0, 0.536), (68.3, 0.597), (64.5, 0.640), (62.5, 0.690)],
]

SPEC_YUFENG = W.preset(
    "blade_5", rim_d=2.0 * LIP_21, dish=DISH_STAR, pinstripe=False, flange_face=0.0057,
    roll_left=math.pi,
    hub=dict(depth=0.0720, setback=0.008, cap_rise=0.0055),
    lugs=dict(count=5, pcd_r=0.05715, r=0.0118, deg=45.5, rise=0.004),
    disc=dict(style="plain", inner_r=0.120, thickness=0.032),
    caliper=CALIPER,
    mats=dict(rim="graphite", lip="machined", lugs="black_gloss", cap="black_gloss", disc="iron"))
SPEC_YUFENG["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.018, bevel=0.0020, mat="graphite",
    r_in=0.034, r_out=YUFENG_TAB * LIP_21, nr=16, seg=60, step_deg=2.5, step_r=0.03,
    windows=YUFENG_WINDOWS, notches=[YUFENG_NOTCH],
    lug_holes=dict(deg=45.5, pcd=0.05715, r=0.0175, count=5),
    ring=dict(r_in=0.215, dish=DISH_RING, depth=0.0, rings=6, mat="machined"))

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

SPEC_SPORT = W.preset(
    "blade_5", rim_d=2.0 * LIP_21, dish=DISH_SPORT, pinstripe=False, flange_face=0.0057,
    roll_left=math.pi,
    hub=dict(depth=0.0720, setback=0.008, cap_rise=0.0055),
    lugs=dict(count=5, pcd_r=0.05715, r=0.0118, deg=84.8, rise=0.004),
    disc=dict(style="plain", inner_r=0.120, thickness=0.032),
    caliper=CALIPER,
    mats=dict(rim="black_gloss", lip="accent", accent="accent", lugs="black_gloss",
              cap="black_gloss", disc="iron"))
SPEC_SPORT["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.020, bevel=0.0022, mat="black_gloss",
    r_in=0.034, r_out=0.2805, nr=16, seg=60, step_deg=2.5, step_r=0.03, rings=(0.395,), accent_r=0.395,
    windows=SPORT_WINDOWS,
    lug_holes=dict(deg=84.8, pcd=0.05715, r=0.0175, count=5))

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
