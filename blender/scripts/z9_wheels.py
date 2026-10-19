"""Denza Z9 wheels: the 21-inch machined multi-spoke (255/40 R21 front, 275/40 R21 rear), traced from the black
car's side photograph (blender/reference/denza-z9/exterior/c1_0036.jpg; rear wheel, ellipse ratio 0.98 at
(2940.5, 2043.4) px, the axle corrected -9, -1 px: scripts/wheel-trace, memory wheel-tracing-method).

What the wheel is: five repeats of a face of silver blades with twenty open slots between them (the brake disc and
caliper show through): in each 72 degrees two V-shaped slots either side of a slender spoke (they narrow from the
rim to the hub), a wide blade, two straight slots either side of a second slender spoke, and a second wide blade;
a plain machined ring is the rim's flange, and a white roundel cap sits in the hub. The slots' outlines are read
off the voted mean picture of the five repeats (z9_wheels.WINDOWS: degrees counter-clockwise from 3 o'clock seen
from outside, radius / the lip radius of the photograph's own fitted circle).
"""
import math
from carkit.geom import Curve
from carkit.parts import wheels as W

LIP_21 = 0.2785     # 21-inch rim lip radius (m): the photograph's fitted circle
TAB = 0.953         # the face's edge: outside it the machined flange ring

CALIPER = dict(
    span_deg=40.0, span_rear=34.0, r_inner=0.135, d_out=0.032, steps=16
)

DISH = Curve([
    (0.000, 0.052), (0.080, 0.052), (0.110, 0.042), (0.150, 0.028),
    (0.200, 0.016), (0.245, 0.009), (0.278, 0.000),
], mode="pchip")

# the twenty slots, four per repeat: the V-shaped pair (narrowing toward the hub) and the straight pair; each
# slot's lower corners run on as a thin gap toward the hub boss (the dark lines that outline the blades)
WINDOWS = [
    # V pair
    [(2.5, 0.945), (3.25, 0.85), (4.0, 0.80), (4.9, 0.70), (5.6, 0.62), (6.1, 0.56), (6.7, 0.515), (7.6, 0.498),
     (8.4, 0.502), (8.9, 0.45), (8.6, 0.38), (8.3, 0.30), (9.3, 0.30), (9.7, 0.34), (10.2, 0.40), (10.6, 0.47),
     (10.4, 0.60), (11.1, 0.70), (11.75, 0.80), (12.25, 0.945)],
    [(14.25, 0.945), (14.5, 0.80), (15.0, 0.70), (15.6, 0.60), (15.9, 0.47), (16.3, 0.40), (16.8, 0.34), (17.2, 0.30),
     (18.2, 0.30), (17.9, 0.38), (17.9, 0.45), (18.25, 0.50), (19.0, 0.55), (19.75, 0.60), (21.0, 0.70),
     (22.0, 0.80), (23.5, 0.945)],
    # straight pair
    [(39.0, 0.945), (39.4, 0.80), (39.75, 0.60), (39.9, 0.52), (41.5, 0.41), (43.2, 0.30), (44.2, 0.30),
     (40.9, 0.505), (45.8, 0.505), (45.5, 0.30), (46.4, 0.30), (46.75, 0.52), (47.1, 0.60), (47.5, 0.80),
     (47.75, 0.945)],
    [(50.25, 0.945), (50.5, 0.80), (51.25, 0.60), (51.5, 0.52), (51.6, 0.30), (52.5, 0.30), (52.2, 0.505),
     (57.1, 0.505), (53.8, 0.30), (54.8, 0.30), (57.5, 0.41), (58.0, 0.60), (58.5, 0.80), (58.75, 0.945)],
]
WINDOWS = [[(a, min(r, TAB - 0.004)) for (a, r) in poly] for poly in WINDOWS]

SPEC_LUXURY = W.preset(
    "blade_5",
    rim_d=2.0 * LIP_21,
    dish=DISH,
    pinstripe=False,
    flange_face=(1.0 - TAB) * LIP_21,
    roll_left=math.pi,
    tyre=dict(bulge=1.042, shoulder=0.015),
    hub=dict(depth=0.052, setback=0.008, cap_rise=0.005, cap_r=0.034),
    lugs=dict(count=5, pcd_r=0.0540, r=0.0100, deg=18.0, rise=0.004),
    disc=dict(style="plain", inner_r=0.118, thickness=0.032),
    caliper=CALIPER,
    mats=dict(
        rim="wheel_silver",
        lip="machined",
        lugs="wheel_silver",
        cap="wheel_cap",
        disc="iron",
        barrel="black_gloss",
        accent="black_gloss",
    ),
)
SPEC_LUXURY["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.016, bevel=0.0018, mat="wheel_silver",
    r_in=0.040, r_out=TAB * LIP_21, nr=16, seg=60, step_deg=2.0, step_r=0.025,
    windows=WINDOWS,
)

DESIGNS = {
    "luxury": ("DenzaZ9_", SPEC_LUXURY),
}
DEFAULT = "luxury"


def corners(surface):
    """The 4 staggered corners of the Denza Z9: 255 mm front, 275 mm rear."""
    r = surface.WHEEL_R
    return [
        ("FL", surface.FRONT_AXLE,  1, 0.255, r, 0.195, 176.0, surface.TRACK_F / 2.0 + 0.118),
        ("FR", surface.FRONT_AXLE, -1, 0.255, r, 0.195, 184.0, surface.TRACK_F / 2.0 + 0.118),
        ("RL", surface.REAR_AXLE,   1, 0.275, r, 0.185, 176.0, surface.TRACK_R / 2.0 + 0.125),
        ("RR", surface.REAR_AXLE,  -1, 0.275, r, 0.185, 184.0, surface.TRACK_R / 2.0 + 0.125),
    ]


def build_design(collection, surface, lib, name):
    prefix, spec = DESIGNS[name]
    return W.build_set(collection, prefix, lib, spec, corners(surface))


def build_all(collection, surface, lib):
    return build_design(collection, surface, lib, DEFAULT)


def build_options(collection, surface, lib):
    made = []
    for name in DESIGNS:
        if name != DEFAULT:
            made += build_design(collection, surface, lib, name)
    return made
