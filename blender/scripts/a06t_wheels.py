"""Avatr 06T wheels: the 20 in "five twin-spoke" of the production car, traced
from the Autohome side views (c1_0004.jpg) and design-list_02.jpg.

    twin5      20 in: five spokes each split into two fingers by a thin slot,
               a diamond-cut machined face over gloss black pockets; 255/45 R20

The face is described, as for the other cars, by polygons of (angle in degrees
counter-clockwise from 3 o'clock as seen from outside, radius as a fraction of
the lip radius) - one repeat of the five. carkit.parts.wheels cuts them from a
dished face. A spoke pair is centred at 90 deg, the big window between two
pairs at 126 deg.

Sizes: the lip is the rim's J flange, 17.3 mm above the bead seat: 0.2713 m on
a 20 in rim; the overall diameter is 738 mm (loaded radius 0.369 m).
"""
import math

from carkit.geom import Curve
from carkit.parts import wheels as W

LIP_20 = 0.2713

CALIPER = dict(span_deg=43.0, span_rear=39.0, r_inner=0.14, d_out=0.034, steps=16)

DISH = Curve([(0.000, 0.0720), (0.090, 0.0720), (0.105, 0.0660), (0.130, 0.0500),
              (0.160, 0.0330), (0.190, 0.0200), (0.220, 0.0110), (0.250, 0.0045),
              (0.2713, 0.0)], mode="pchip")
TAB = 0.965

# the big window between two spoke pairs, centred at 126 deg: widest at the
# rim, narrowing toward the hub (c1_0004.jpg)
WIN_BIG = [
    (106.5, 0.26), (105.5, 0.44), (104.5, 0.65), (105.5, 0.84), (109.0, 0.92), (126.0, 0.93),
    (143.0, 0.92), (146.5, 0.84), (147.5, 0.65), (146.5, 0.44), (145.5, 0.26), (126.0, 0.24),
]
# the thin slot that splits one spoke into twin fingers, centred at 90 deg
WIN_SLOT = [
    (88.0, 0.30), (88.2, 0.55), (88.5, 0.78), (88.8, 0.92),
    (91.2, 0.92), (91.5, 0.78), (91.8, 0.55), (92.0, 0.30),
    (90.0, 0.26),
]
# diamond-cut machined inlays along each spoke finger
INLAY_L = [(77.5, 0.96), (77.5, 0.32), (86.5, 0.32), (86.5, 0.96)]
INLAY_R = [(93.5, 0.96), (93.5, 0.32), (102.5, 0.32), (102.5, 0.96)]

SPEC_TWIN5 = W.preset(
    "blade_5", rim_d=2.0 * LIP_20, dish=DISH, pinstripe=False, flange_face=0.0057,
    roll_left=math.pi,
    hub=dict(depth=0.0720, setback=0.008, cap_rise=0.0055),
    lugs=dict(count=5, pcd_r=0.05715, r=0.0118, deg=90.0, rise=0.004),
    disc=dict(style="plain", inner_r=0.120, thickness=0.032),
    caliper=CALIPER,
    mats=dict(rim="black_gloss", lip="machined", lugs="black_gloss", cap="black_gloss",
              disc="iron"))
SPEC_TWIN5["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.018, bevel=0.0020, mat="black_gloss",
    r_in=0.034, r_out=TAB * LIP_20, nr=16, seg=60, step_deg=2.5, step_r=0.03,
    windows=[WIN_BIG, WIN_SLOT],
    inlay=dict(mat="machined", polys=[INLAY_L, INLAY_R], lift=0.0004))

DESIGNS = {"twin5": ("A06T_", SPEC_TWIN5)}
DEFAULT = "twin5"


def corners(surface):
    # tag, axle x, sign, tyre width, rolling radius, disc radius, caliper deg,
    # outer sidewall y (track/2 + tyre width/2: 1676/1680 mm track, 255 mm tyres)
    return [
        ("FL", surface.FRONT_AXLE, 1, 0.255, 0.369, 0.190, 176.0, 0.9655),
        ("FR", surface.FRONT_AXLE, -1, 0.255, 0.369, 0.190, 184.0, 0.9655),
        ("RL", surface.REAR_AXLE, 1, 0.255, 0.369, 0.180, 176.0, 0.9675),
        ("RR", surface.REAR_AXLE, -1, 0.255, 0.369, 0.180, 184.0, 0.9675),
    ]


def build_design(collection, surface, lib, name):
    prefix, spec = DESIGNS[name]
    return W.build_set(collection, prefix, lib, spec, corners(surface))


def build_all(collection, surface, lib):
    """The car's own wheels: the default design."""
    return build_design(collection, surface, lib, DEFAULT)


def build_options(collection, surface, lib):
    made = []
    for name in DESIGNS:
        if name != DEFAULT:
            made += build_design(collection, surface, lib, name)
    return made
