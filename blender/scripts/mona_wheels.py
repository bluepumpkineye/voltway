"""XPeng Mona L05 (小鹏MONA L05) wheels: the 20-inch five-V blade wheel on 245/45 R20 tyres.

The studio turnaround car (Autohome series 8662, c1_0003 purple, left side, nose left) wears a 20 in
diamond-cut wheel: five V-shaped pairs of silver spoke faces on a gloss-black dish, five lug covers on a
130 mm circle round an X cap, lime-yellow calipers (front ahead of the axle, rear behind it).

The face was traced from c1_0003's front wheel automatically (2026-11-17): the rim lip's ellipse (fit_rim,
centre (918.5, 2036.9), semi-axes 186 / 183 px) unrolled to (angle, radius) strips, the silver faces thresholded
(luminance > 0.42, chroma < 0.16), the five repeats folded at 72.4 deg, and the free (non-silver) regions between
the arms read per radius row: a narrow slot inside each U (centre 12.2 deg, 18 deg wide at the rim, closing at
r 0.44) and a wide window between neighbouring U's (centre 48.4 deg, 34 deg wide at the rim, 57 deg at r 0.36).
Angles are degrees CCW from 3 o'clock seen from outside in the left-side photo (as the donor's); radius / lip.

In carkit.parts.wheels, local 0 deg maps to world +X (forward of the axle). Left wheels have
Rx(-90) so local -deg (360 - deg) tilts UP; right wheels have Rx(+90) so local +deg tilts UP.
"""
import math

from carkit.geom import Curve
from carkit.parts import wheels as W

LIP_20 = 0.2775          # rim lip radius: 184.8 px / 664.2 px per m

CALIPER = dict(span_deg=40.0, span_rear=36.0, r_inner=0.128, d_out=0.032, steps=16, groove=True)

DISH_20 = Curve([
    (0.000, 0.0640), (0.086, 0.0640), (0.102, 0.0580), (0.128, 0.0430),
    (0.158, 0.0280), (0.190, 0.0160), (0.222, 0.0075), (0.252, 0.0025),
    (LIP_20, 0.0),
], mode="pchip")

BLADE_TAB = 0.968
BLADE_WINDOWS = [
    # wide window between neighbouring V's (the brake shows through)
    [(28.4, 0.945), (45.4, 0.949), (62.4, 0.945), (62.9, 0.900), (62.9, 0.820), (63.7, 0.740), (67.4, 0.660), (72.2, 0.580), (73.6, 0.500), (74.9, 0.420), (76.9, 0.360), (48.4, 0.335), (19.9, 0.360), (21.9, 0.420), (23.2, 0.500), (24.6, 0.580), (25.4, 0.660), (26.2, 0.740), (26.9, 0.820), (27.4, 0.900)],
    # narrow slot inside each V
    [(1.7, 0.945), (10.9, 0.949), (20.2, 0.945), (20.0, 0.880), (19.2, 0.800), (18.4, 0.720), (17.2, 0.650), (15.9, 0.580), (14.4, 0.520), (12.7, 0.470), (10.4, 0.435), (8.2, 0.470), (6.9, 0.520), (5.9, 0.580), (4.7, 0.650), (4.0, 0.720), (3.2, 0.800), (2.4, 0.880)],
]

SPEC_BLADE = W.preset(
    "blade_5", rim_d=2.0 * LIP_20, dish=DISH_20, pinstripe=False,
    flange_face=(1.0 - BLADE_TAB) * LIP_20, roll_left=math.pi,
    tyre=dict(bulge=1.050, shoulder=0.018),
    hub=dict(depth=0.0640, setback=0.008, cap_rise=0.0055),
    lugs=dict(count=5, pcd_r=0.0658, r=0.0140, deg=44.0, rise=0.004),
    disc=dict(style="plain", inner_r=0.112, thickness=0.032),
    caliper=CALIPER,
    mats=dict(rim="obsidian", lip="wheel_silver", lugs="black_gloss", cap="gunmetal", disc="iron"),
)
SPEC_BLADE["spokes"] = dict(
    style="traced", count=5, phase=0.0, depth=0.018, bevel=0.0020, mat="wheel_silver",
    r_in=0.034, r_out=BLADE_TAB * LIP_20, nr=16, seg=60, step_deg=2.4, step_r=0.03,
    windows=BLADE_WINDOWS,
    lug_holes=dict(deg=44.0, pcd=0.0658, r=0.0185, count=5),
)

DESIGNS = {
    "blade20": ("MONA_", SPEC_BLADE),
}
DEFAULT = "blade20"


def corners(surface):
    # 1640 mm front track, 1658 mm rear track, 245/45 R20 tyres (loaded radius 0.354 m); calipers ahead of the front
    # axle and behind the rear one, a little above horizontal (c1_0003)
    return [
        ("FL", surface.FRONT_AXLE, 1, 0.245, surface.WHEEL_R, 0.160, 350.0, 0.9425),
        ("FR", surface.FRONT_AXLE, -1, 0.245, surface.WHEEL_R, 0.160, 10.0, 0.9425),
        ("RL", surface.REAR_AXLE, 1, 0.245, surface.WHEEL_R, 0.154, 190.0, 0.9515),
        ("RR", surface.REAR_AXLE, -1, 0.245, surface.WHEEL_R, 0.154, 170.0, 0.9515),
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
